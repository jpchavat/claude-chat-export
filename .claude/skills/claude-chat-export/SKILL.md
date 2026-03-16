---
name: claude-chat-export
description: "Use this skill whenever the user wants to export, download, save, or convert a Claude.ai conversation to Markdown or PDF. Triggers include: any mention of 'export chat', 'save conversation', 'download chat', 'convert to markdown', 'convert to PDF', Claude share URLs (claude.ai/share/...), or requests to extract artifacts, code, or web search results from a Claude conversation. Also use when the user provides a saved Claude HTML file and wants it converted. Do NOT use for general markdown conversion or non-Claude content."
---

# Claude Chat Export

Export Claude.ai conversations to Markdown and PDF with full fidelity — artifacts, web search sources, and message history.

## Overview

This skill uses the `claude-chat-export` CLI tool. It accepts either a **Claude share URL** or a **saved HTML file** and produces a clean Markdown file.

- **URL mode** (recommended): Fetches the full conversation via Claude's API, including artifact source code (interactive widgets, charts, visualizations).
- **HTML mode**: Parses a saved HTML page — text content only, artifact source code is not available from static exports.

## Running the tool

Use `uvx` to run without permanent installation:

```bash
uvx --from git+https://github.com/jpchavat/claude-chat-export.git claude-chat-export <source> [options]
```

If Playwright's Chromium browser has not been installed yet (required for URL mode), install it first:

```bash
uv run --with playwright python -m playwright install chromium
```

## Arguments

| Argument | Description |
|----------|-------------|
| `<source>` | A Claude share URL (`https://claude.ai/share/<uuid>`) or a local `.html` file path |
| `-o, --output <path>` | Output file path (default: `<uuid>.md` for URLs, `<file>.md` for HTML files) |
| `--pdf` | Also generate a styled PDF alongside the Markdown output |
| `--include-sources` | Include full web search source content with titles and URLs (default: compact excerpts) |
| `--no-artifacts` | Skip artifact code extraction |

## Examples

```bash
# Export from a share URL — includes artifacts with full source code
uvx --from git+https://github.com/jpchavat/claude-chat-export.git claude-chat-export https://claude.ai/share/179a9020-069d-4203-b018-96bb0e999b33

# Export from a saved HTML file
uvx --from git+https://github.com/jpchavat/claude-chat-export.git claude-chat-export ~/Downloads/conversation.html

# Full web search sources + custom output path
uvx --from git+https://github.com/jpchavat/claude-chat-export.git claude-chat-export https://claude.ai/share/<uuid> --include-sources -o ~/Desktop/notes.md
```

## What gets exported

- Human and Claude messages with timestamps
- Web search queries with source links (compact by default, full text with `--include-sources`)
- Artifact source code (HTML/CSS/JS widgets) as fenced code blocks (URL mode only)
- Claude's analysis text in original markdown
