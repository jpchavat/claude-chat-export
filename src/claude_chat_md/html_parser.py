"""Parse saved Claude.ai HTML conversation exports."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag


@dataclass
class Artifact:
    tool_use_id: str
    tool_name: str
    iframe_url: str
    # Populated later by Playwright fetcher
    source_html: str = ""


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content_html: str  # raw inner HTML of message body
    timestamp: str = ""
    artifacts: list[Artifact] = field(default_factory=list)
    tool_uses: list[str] = field(default_factory=list)  # e.g. ["Searched the web"]


@dataclass
class Conversation:
    title: str
    messages: list[Message]


def _get_text(el: Tag) -> str:
    return el.get_text(separator="\n", strip=True)


def _extract_title(soup: BeautifulSoup) -> str:
    # The conversation title appears in the header
    for sel in [
        ".truncate.text-text-300.cursor-pointer",
        "header .truncate",
        "title",
    ]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            if text and text.lower() not in {"claude", ""}:
                return text
    return "Claude Conversation"


def _extract_timestamp(turn: Tag) -> str:
    ts = turn.select_one(".text-text-500.text-xs")
    return ts.get_text(strip=True) if ts else ""


def _extract_tool_uses(turn: Tag) -> list[str]:
    """Extract tool use labels like 'Searched the web'."""
    labels = []
    for btn in turn.select("button.group\\/status, [class*='group/status']"):
        text = btn.get_text(strip=True)
        if text:
            labels.append(text)
    # Also catch by looking for inline status text
    for el in turn.select(".inline-flex.items-center.gap-1 .truncate"):
        text = el.get_text(strip=True)
        if text and len(text) < 80:
            labels.append(text)
    return list(dict.fromkeys(labels))  # deduplicate, preserve order


def _extract_artifacts(turn: Tag) -> list[Artifact]:
    artifacts = []
    for iframe in turn.select("iframe[src*='claudemcpcontent.com']"):
        src = iframe.get("src", "")
        # Container id encodes the tool_use_id: mcp-app-container-{tool_use_id}
        container = iframe.find_parent(id=re.compile(r"^mcp-app-container-"))
        tool_use_id = ""
        if container:
            tool_use_id = container["id"].replace("mcp-app-container-", "")

        # Tool name is shown in the modal header
        modal_id = f"mcp-app-modal-{tool_use_id}" if tool_use_id else ""
        tool_name = "artifact"
        if modal_id:
            modal = turn.find_parent().find(id=modal_id) if turn.find_parent() else None  # type: ignore[union-attr]
            if not modal:
                # Search whole soup for it
                modal = iframe.find_parent(id=re.compile(r"^mcp-app-modal-"))
            if modal:
                name_el = modal.select_one("span.font-base")
                if name_el:
                    tool_name = name_el.get_text(strip=True)

        artifacts.append(Artifact(
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            iframe_url=src,
        ))
    return artifacts


def _extract_assistant_content_html(turn: Tag) -> str:
    """Return the combined inner HTML of all .standard-markdown divs in a turn."""
    parts = []
    for md_div in turn.select(".standard-markdown"):
        parts.append(str(md_div))
    # Also look for progressive-markdown (streaming responses)
    for md_div in turn.select(".progressive-markdown"):
        parts.append(str(md_div))
    return "\n".join(parts)


def parse_html(html_path: Path) -> Conversation:
    """Parse a saved Claude HTML export and return a Conversation."""
    with open(html_path, encoding="utf-8") as f:
        raw = f.read()
    soup = BeautifulSoup(raw, "html.parser")

    title = _extract_title(soup)
    messages: list[Message] = []

    # Each [data-test-render-count] is a conversation turn
    turns = soup.select("[data-test-render-count]")

    for turn in turns:
        # --- User message ---
        user_msg_el = turn.select_one("[data-testid='user-message']")
        if user_msg_el:
            # Grab plain text (user messages are plain text)
            content = _get_text(user_msg_el)
            timestamp = _extract_timestamp(turn)
            messages.append(Message(
                role="user",
                content_html=content,
                timestamp=timestamp,
            ))
            continue

        # --- Assistant message ---
        content_html = _extract_assistant_content_html(turn)
        artifacts = _extract_artifacts(turn)
        tool_uses = _extract_tool_uses(turn)

        if content_html or artifacts:
            messages.append(Message(
                role="assistant",
                content_html=content_html,
                artifacts=artifacts,
                tool_uses=tool_uses,
            ))

    return Conversation(title=title, messages=messages)
