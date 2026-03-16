"""CLI entry point for claude-chat-export."""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

import click
from rich.console import Console

from .converter import from_api_snapshot, from_html_conversation
from .html_parser import parse_html
from .api_fetcher import extract_uuid

console = Console(stderr=True)

CLAUDE_SHARE_RE = re.compile(r"https?://claude\.ai/share/[0-9a-f-]{36}")


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _output_path(source: str, output: Path | None) -> Path:
    if output:
        return output
    if _is_url(source):
        uuid = extract_uuid(source) or "conversation"
        return Path(f"{uuid}.md")
    return Path(source).with_suffix(".md")


@click.command()
@click.argument("source")
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output .md file (default: <uuid>.md for URLs, <file>.md for HTML).",
)
@click.option(
    "--no-artifacts",
    is_flag=True,
    default=False,
    help="Skip artifact code extraction (faster, text only).",
)
@click.option(
    "--include-sources",
    is_flag=True,
    default=False,
    help="Include full web search source content (default: compact links with excerpts).",
)
def main(source: str, output: Path | None, no_artifacts: bool, include_sources: bool) -> None:
    """Convert a Claude conversation to Markdown.

    SOURCE can be:

    \b
      • A Claude share URL:  https://claude.ai/share/<uuid>
      • A saved HTML file:   /path/to/conversation.html

    When given a URL the full conversation is fetched via the Claude API
    (Playwright required — run `uv run playwright install chromium` once).
    Artifacts (interactive widgets, charts, code) are included as code blocks.

    When given an HTML file the text content is extracted from the saved page.
    Artifact source code is not available from static HTML exports.

    \b
    Examples:
      claude-chat-export https://claude.ai/share/179a9020-069d-4203-b018-96bb0e999b33
      claude-chat-export conversation.html
      claude-chat-export conversation.html -o notes.md
    """
    out_path = _output_path(source, output)

    if _is_url(source):
        # ── URL mode: fetch via API ────────────────────────────────────────
        if not CLAUDE_SHARE_RE.match(source):
            console.print(
                f"[red]Error:[/red] URL must be a Claude share link "
                f"(https://claude.ai/share/<uuid>)"
            )
            sys.exit(1)

        console.print(f"[bold]Fetching[/bold] {source} …")

        from .api_fetcher import fetch_snapshot
        try:
            snapshot = asyncio.run(fetch_snapshot(source))
        except Exception as exc:
            console.print(f"[red]Error:[/red] {exc}")
            sys.exit(1)

        n_msgs = len(snapshot.get("chat_messages") or [])
        title = snapshot.get("snapshot_name", "")
        console.print(
            f"  [green]✓[/green] {n_msgs} messages — [italic]{title}[/italic]"
        )

        if not no_artifacts:
            artifacts_found = sum(
                1
                for m in (snapshot.get("chat_messages") or [])
                for c in (m.get("content") or [])
                if c.get("type") == "tool_use" and "widget_code" in (c.get("input") or {})
            )
            if artifacts_found:
                console.print(
                    f"  [green]✓[/green] {artifacts_found} artifact(s) with full source code"
                )

        md = from_api_snapshot(snapshot, include_sources=include_sources)

    else:
        # ── HTML file mode ─────────────────────────────────────────────────
        html_path = Path(source)
        if not html_path.exists():
            console.print(f"[red]Error:[/red] File not found: {source}")
            sys.exit(1)
        if html_path.suffix.lower() not in {".html", ".htm"}:
            console.print(f"[red]Error:[/red] Expected an HTML file, got: {source}")
            sys.exit(1)

        console.print(f"[bold]Parsing[/bold] {html_path.name} …")
        conv = parse_html(html_path)
        console.print(
            f"  [green]✓[/green] {len(conv.messages)} messages — "
            f"[italic]{conv.title}[/italic]"
        )

        artifact_count = sum(len(m.artifacts) for m in conv.messages)
        if artifact_count:
            console.print(
                f"  [yellow]⚠[/yellow]  {artifact_count} artifact(s) found — "
                f"source not available from static HTML.\n"
                f"  Tip: use the share URL instead to get full artifact code."
            )

        md = from_html_conversation(conv)

    # ── Write output ───────────────────────────────────────────────────────
    out_path.write_text(md, encoding="utf-8")
    console.print(f"\n[bold green]✓ Written:[/bold green] {out_path}")
    console.print(f"  {len(md.splitlines())} lines / {len(md):,} chars")
