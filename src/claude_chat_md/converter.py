"""Convert Claude conversation data to Markdown.

Supports two input paths:
  1. API JSON (from chat_snapshots endpoint) — full fidelity including artifact code.
  2. Parsed HTML (BeautifulSoup, from saved .html files) — text only, artifact URLs.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import markdownify

from .html_parser import Conversation, Message

# ---------------------------------------------------------------------------
# HTML → Markdown helper
# ---------------------------------------------------------------------------

def _html_to_md(html: str) -> str:
    if not html:
        return ""
    md = markdownify.markdownify(
        html,
        heading_style="ATX",
        bullets="-",
        code_language_callback=lambda el: (
            (el.get("class") or [""])[0].replace("language-", "")
        ),
    )
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


# ---------------------------------------------------------------------------
# Path 1: Convert from API JSON snapshot
# ---------------------------------------------------------------------------

_SKIP_TOOL_NAMES = {
    "web_fetch",         # raw page fetches — noisy, not useful in MD
}

_SKIP_TOOL_RESULT_NAMES = {
    "web_fetch",
}

_MAX_EXCERPT_CHARS = 150

_WEB_SEARCH_TOOLS = {
    "web_search",
}


def _fmt_timestamp(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%b %d, %Y %H:%M")
    except Exception:
        return iso


def _web_search_result_to_md(block: dict[str, Any], include_sources: bool) -> str:
    """Format a web_search tool_result block."""
    content_items = block.get("content") or []
    if not isinstance(content_items, list):
        return ""

    sources = []
    for item in content_items:
        if item.get("type") != "knowledge":
            continue
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        text = (item.get("text") or "").strip()
        if not text:
            continue
        sources.append({"title": title, "url": url, "text": text})

    if not sources:
        return ""

    if include_sources:
        # Full dump: each source as a subsection with complete text
        parts = []
        for src in sources:
            header = f"#### [{src['title']}]({src['url']})" if src["url"] else f"#### {src['title']}"
            parts.append(header)
            parts.append("")
            parts.append(src["text"])
            parts.append("")
        return "\n".join(parts)
    else:
        # Compact: linked sources with short excerpt
        lines = ["> **Sources:**"]
        for src in sources:
            excerpt = src["text"][:_MAX_EXCERPT_CHARS]
            if len(src["text"]) > _MAX_EXCERPT_CHARS:
                excerpt += " …"
            link = f"[{src['title']}]({src['url']})" if src["url"] else src["title"]
            lines.append(f"> - {link}")
            lines.append(f">   {excerpt}")
        return "\n".join(lines)


def _content_block_to_md(block: dict[str, Any], tool_index: list[int], include_sources: bool = False) -> str:
    """Convert a single content block to Markdown."""
    btype = block.get("type", "")

    # --- plain text (markdown already) ---
    if btype == "text":
        text = block.get("text", "").strip()
        return text if text else ""

    # --- tool use ---
    if btype == "tool_use":
        name = block.get("name", "")
        inp = block.get("input") or {}

        if name in _SKIP_TOOL_NAMES:
            return ""

        if name in _WEB_SEARCH_TOOLS:
            query = inp.get("query", "")
            return f"> 🔍 **Web search:** {query}"

        # Artifact / widget
        if "widget_code" in inp:
            tool_index[0] += 1
            title = inp.get("title") or name
            code = inp.get("widget_code", "").strip()
            lang = "html"
            if "import React" in code or "useState" in code or "jsx" in code.lower():
                lang = "jsx"
            lines = [
                f"### Artifact {tool_index[0]}: {title}",
                "",
                f"```{lang}",
                code,
                "```",
            ]
            return "\n".join(lines)

        # Generic tool use
        tool_index[0] += 1
        inp_str = "\n".join(f"  {k}: {v}" for k, v in inp.items() if k not in ("widget_code",))
        return f"> 🔧 **Tool:** `{name}`\n{inp_str}"

    # --- tool result ---
    if btype == "tool_result":
        name = block.get("name", "")
        if name in _SKIP_TOOL_RESULT_NAMES:
            return ""
        # Web search results get special formatting
        if name == "web_search":
            return _web_search_result_to_md(block, include_sources)
        # Skip boilerplate artifact confirmation messages
        content_items = block.get("content") or []
        if isinstance(content_items, list):
            snippets = []
            for item in content_items:
                text = (item.get("text") or "").strip()
                if not text:
                    continue
                if "Content rendered and shown" in text or "tool call rendered" in text:
                    continue
                snippets.append(f"> {text}")
            return "\n".join(snippets[:2])
        return ""

    return ""


def _message_to_md_from_api(msg: dict[str, Any], include_sources: bool = False) -> str:
    sender = msg.get("sender", "")
    ts = msg.get("created_at", "")
    role_label = "**Human**" if sender == "human" else "**Claude**"
    header = f"{role_label} · *{_fmt_timestamp(ts)}*" if ts else role_label

    parts = [header, ""]
    tool_index = [0]

    for block in msg.get("content") or []:
        md = _content_block_to_md(block, tool_index, include_sources)
        if md:
            parts.append(md)
            parts.append("")

    return "\n".join(parts).rstrip()


def from_api_snapshot(snapshot: dict[str, Any], include_sources: bool = False) -> str:
    """Convert a chat_snapshots API response dict to a Markdown string."""
    title = snapshot.get("snapshot_name") or "Claude Conversation"
    shared_by = snapshot.get("created_by", "")

    lines = [f"# {title}"]
    if shared_by:
        lines.append(f"\n*Shared by {shared_by}*")
    lines += ["", "---", ""]

    for msg in snapshot.get("chat_messages") or []:
        lines.append(_message_to_md_from_api(msg, include_sources))
        lines += ["", "---", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Path 2: Convert from parsed HTML (Conversation dataclass)
# ---------------------------------------------------------------------------

def _html_message_to_md(msg: Message) -> str:
    role_label = "**Human**" if msg.role == "user" else "**Claude**"
    header = f"{role_label} · *{msg.timestamp}*" if msg.timestamp else role_label

    parts = [header, ""]

    for tool in msg.tool_uses:
        parts.append(f"> 🔍 *{tool}*")
        parts.append("")

    if msg.role == "user":
        parts.append(msg.content_html)
    else:
        md = _html_to_md(msg.content_html)
        if md:
            parts.append(md)

    for i, artifact in enumerate(msg.artifacts, start=1):
        parts.append("")
        parts.append(f"### Artifact {i}: `{artifact.tool_name}`")
        if artifact.source_html:
            lang = "html"
            if "import React" in artifact.source_html or "useState" in artifact.source_html:
                lang = "jsx"
            parts += [f"\n```{lang}", artifact.source_html.strip(), "```"]
        else:
            parts.append(
                f"\n> **Interactive artifact** (source not available in static export)  \n"
                f"> View live: <{artifact.iframe_url}>"
            )

    return "\n".join(parts).rstrip()


def from_html_conversation(conv: Conversation) -> str:
    """Convert an HTML-parsed Conversation to a Markdown string."""
    lines = [f"# {conv.title}", "", "---", ""]
    for msg in conv.messages:
        lines.append(_html_message_to_md(msg))
        lines += ["", "---", ""]
    return "\n".join(lines)
