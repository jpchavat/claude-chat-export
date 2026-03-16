"""Fetch conversation data from Claude's chat_snapshots API via Playwright.

The shared conversation API is public (no auth needed) but requires a real
browser to pass Cloudflare checks.  We piggyback on the request that the
React app already makes when rendering the share page.

Endpoint:
  GET /api/chat_snapshots/{uuid}?rendering_mode=messages&render_all_tools=true
"""

from __future__ import annotations

import re
from typing import Any

from rich.console import Console

console = Console(stderr=True)

SHARE_URL_RE = re.compile(
    r"https?://claude\.ai/share/([0-9a-f-]{36})"
)

# How long to wait after domcontentloaded for the React app to fire its API call
API_WAIT_MS = 8_000


def extract_uuid(url: str) -> str | None:
    """Return the share UUID from a claude.ai/share/... URL, or None."""
    m = SHARE_URL_RE.search(url)
    return m.group(1) if m else None


async def fetch_snapshot(share_url: str) -> dict[str, Any]:
    """
    Visit *share_url* in a headless browser, intercept the chat_snapshots
    API response, and return the parsed JSON dict.

    Raises RuntimeError if the snapshot cannot be captured.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed.  Run: uv run playwright install chromium"
        )

    uuid = extract_uuid(share_url)
    if not uuid:
        raise ValueError(f"Cannot extract share UUID from URL: {share_url!r}")

    snapshot: dict[str, Any] | None = None

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()

        async def on_response(response):
            nonlocal snapshot
            if (
                "chat_snapshots" in response.url
                and uuid in response.url
                and response.status == 200
                and snapshot is None
            ):
                try:
                    snapshot = await response.json()
                    console.print(
                        f"  [green]✓[/green] Captured snapshot API response "
                        f"({len(snapshot.get('chat_messages', []))} messages)"
                    )
                except Exception as exc:
                    console.print(f"  [yellow]Warning parsing snapshot: {exc}[/yellow]")

        page.on("response", on_response)

        console.print(f"[dim]  Loading {share_url} …[/dim]")
        try:
            await page.goto(share_url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as exc:
            console.print(f"  [yellow]Page load warning: {exc}[/yellow]")

        # Wait for the React app to fire its API call
        await page.wait_for_timeout(API_WAIT_MS)
        await browser.close()

    if snapshot is None:
        raise RuntimeError(
            f"Could not capture chat_snapshots API response for {share_url}.\n"
            "Make sure the URL is a valid public Claude share link."
        )

    return snapshot
