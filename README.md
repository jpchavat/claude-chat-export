<div align="center">

# claude-chat-export

**Convert Claude.ai conversations to Markdown and PDF**

*Artifacts, web search sources, and full message history — all in one command.*

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agent_skills-compatible-5a67d8?style=flat-square)](https://agentskills.io)

</div>

---

## Example output

<p align="center">
  <img src="assets/example_page1.png" width="32%" alt="Page 1" />
  <img src="assets/example_page2.png" width="32%" alt="Page 2" />
  <img src="assets/example_page3.png" width="32%" alt="Page 3" />
</p>

## Features

| | Feature | Description |
|---|---|---|
| **🔗** | **URL mode** | Fetch directly from a Claude share URL — full conversation with artifact source code |
| **📄** | **HTML mode** | Parse a saved Claude HTML page — extracts text content |
| **📑** | **PDF export** | Clean, minimalistic styled PDF via `--pdf` |
| **🧩** | **Artifacts** | Interactive widgets, charts, and code included as fenced code blocks |
| **🔍** | **Web sources** | Compact linked excerpts by default, or full content with `--include-sources` |

## Quick start

```bash
# Install
git clone https://github.com/jpchavat/claude-chat-export.git
cd claude-chat-export
uv sync
uv run playwright install chromium   # one-time setup

# Export a conversation
uv run claude-chat-export https://claude.ai/share/<uuid>

# Export with PDF
uv run claude-chat-export https://claude.ai/share/<uuid> --pdf
```

## Usage

```bash
# From a share URL (recommended — includes artifacts)
uv run claude-chat-export https://claude.ai/share/<uuid>

# From a saved HTML file
uv run claude-chat-export conversation.html

# Generate PDF alongside Markdown
uv run claude-chat-export https://claude.ai/share/<uuid> --pdf

# Include full web search source content
uv run claude-chat-export https://claude.ai/share/<uuid> --include-sources

# Custom output path
uv run claude-chat-export https://claude.ai/share/<uuid> -o notes.md
```

## Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output file path (default: `<uuid>.md` or `<file>.md`) |
| `--pdf` | Also generate a styled PDF alongside the Markdown output |
| `--include-sources` | Include full web search source content instead of compact excerpts |
| `--no-artifacts` | Skip artifact code extraction |

## Agent Skill

<a href="https://agentskills.io"><img src="https://img.shields.io/badge/agent_skills-open_standard-5a67d8?style=for-the-badge" alt="Agent Skills" /></a>

This repo includes an [Agent Skill](https://agentskills.io) — the open standard supported by **30+ AI tools**. Install it once and use `/claude-chat-export` from your favorite agent.

**Compatible with:** Claude Code · Claude.ai · OpenAI Codex · Gemini CLI · Cursor · VS Code / GitHub Copilot · Roo Code · Goose · Junie (JetBrains) · [and more](https://agentskills.io/home)

### Install the skill

Each tool has its own skills directory. Copy the skill folder to the right location:

| Tool | Skills path |
|------|-------------|
| **Claude Code** | `~/.claude/skills/` |
| **OpenAI Codex** | `~/.codex/skills/` |
| **Gemini CLI** | `~/.gemini/skills/` |
| **Cursor** | `.cursor/skills/` (project) |
| **VS Code / Copilot** | `.github/skills/` (project) |
| **Any project** | `.claude/skills/` or `.agent/skills/` (committed to repo) |

```bash
# Claude Code (personal — available in all projects)
mkdir -p ~/.claude/skills && cp -r .claude/skills/claude-chat-export ~/.claude/skills/

# OpenAI Codex
mkdir -p ~/.codex/skills && cp -r .claude/skills/claude-chat-export ~/.codex/skills/

# Gemini CLI
mkdir -p ~/.gemini/skills && cp -r .claude/skills/claude-chat-export ~/.gemini/skills/

# Or one-liner without cloning the repo (Claude Code example):
git clone https://github.com/jpchavat/claude-chat-export.git /tmp/cce \
  && mkdir -p ~/.claude/skills \
  && cp -r /tmp/cce/.claude/skills/claude-chat-export ~/.claude/skills/ \
  && rm -rf /tmp/cce
```

Then invoke it from your agent:

```
/claude-chat-export https://claude.ai/share/<uuid> --pdf
```

## How it works

| Mode | Approach |
|------|----------|
| **URL** | Uses Playwright to load the share page and intercepts the `chat_snapshots` API response, which contains the full conversation data including artifact widget code |
| **HTML** | Parses the saved HTML with BeautifulSoup to extract rendered messages. Artifact source code is not available in static exports (delivered via postMessage at runtime) |
| **PDF** | Converts Markdown to styled HTML with a clean, minimalistic CSS theme, then uses Chromium's built-in PDF printing via Playwright |

## License

MIT
