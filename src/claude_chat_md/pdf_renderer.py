"""Render Markdown to a clean, minimalistic PDF using Playwright + Chromium."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from rich.console import Console

console = Console(stderr=True)

_CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;

    @bottom-center {
        content: counter(page);
        font-size: 9px;
        color: #999;
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    }
}

:root {
    --text: #1a1a1a;
    --text-secondary: #555;
    --text-muted: #888;
    --border: #e0e0e0;
    --bg-code: #f6f8fa;
    --bg-quote: #f9f9f9;
    --accent: #5a67d8;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', 'Helvetica Neue', 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
    line-height: 1.7;
    color: var(--text);
    -webkit-font-smoothing: antialiased;
    padding: 40px 50px;
}

h1 {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
    color: var(--text);
    letter-spacing: -0.3px;
}

h2 {
    font-size: 14px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 8px;
    color: var(--text);
}

h3 {
    font-size: 12px;
    font-weight: 600;
    margin-top: 16px;
    margin-bottom: 6px;
    color: var(--text-secondary);
}

h4 {
    font-size: 11px;
    font-weight: 600;
    margin-top: 10px;
    margin-bottom: 4px;
    color: var(--text-secondary);
}

p {
    margin-bottom: 8px;
}

/* Conversation structure */
hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 16px 0;
}

strong {
    font-weight: 600;
}

em {
    font-style: italic;
    color: var(--text-secondary);
}

/* Role labels */
p > strong:first-child {
    font-size: 12px;
}

/* Blockquotes — used for search results and tool use */
blockquote {
    border-left: 3px solid var(--border);
    padding: 6px 12px;
    margin: 8px 0;
    background: var(--bg-quote);
    border-radius: 0 4px 4px 0;
    font-size: 10px;
    color: var(--text-secondary);
    page-break-inside: avoid;
}

blockquote p {
    margin-bottom: 4px;
}

blockquote strong {
    color: var(--text);
}

/* Code blocks — artifacts and inline code */
pre {
    background: var(--bg-code);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 14px;
    margin: 10px 0;
    overflow-x: auto;
    font-size: 9px;
    line-height: 1.5;
    page-break-inside: auto;
}

code {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 9.5px;
}

p code, li code {
    background: var(--bg-code);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 10px;
}

pre code {
    background: none;
    padding: 0;
    font-size: inherit;
}

/* Lists */
ul, ol {
    margin: 6px 0 8px 20px;
}

li {
    margin-bottom: 3px;
}

/* Links */
a {
    color: var(--accent);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    font-size: 10px;
}

th, td {
    border: 1px solid var(--border);
    padding: 6px 10px;
    text-align: left;
}

th {
    background: var(--bg-code);
    font-weight: 600;
}

/* Subtitle / shared by */
h1 + p > em {
    font-size: 11px;
    color: var(--text-muted);
}

/* Artifact headings */
h3 code {
    font-weight: 500;
}

/* Images */
img {
    max-width: 100%;
    border-radius: 4px;
}
"""


def _md_to_html(md: str) -> str:
    """Convert markdown text to HTML using Python's markdown library."""
    import markdown

    html_body = markdown.markdown(
        md,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
        },
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{_CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""


async def _render_pdf(html: str, output_path: Path) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "2cm", "right": "2.5cm", "bottom": "2cm", "left": "2.5cm"},
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template='<div style="width:100%;text-align:center;font-size:9px;color:#999;font-family:Arial,sans-serif;"><span class="pageNumber"></span></div>',
        )
        await browser.close()


def render_pdf(md_content: str, output_path: Path) -> None:
    """Convert a Markdown string to a styled PDF file."""
    console.print("[dim]  Rendering PDF …[/dim]")
    html = _md_to_html(md_content)
    asyncio.run(_render_pdf(html, output_path))
