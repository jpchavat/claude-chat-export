# claude-chat-export

Convert Claude.ai conversations to Markdown — including artifacts (interactive widgets, charts, code), web search results, and full message history.

## Features

- **URL mode**: Fetch directly from a Claude share URL — gets full conversation with artifact source code
- **HTML mode**: Parse a saved Claude HTML page — extracts text content
- **Artifacts**: Interactive widgets, charts, and code are included as code blocks in the markdown
- **Web search sources**: Compact linked excerpts by default, or full content with `--include-sources`

## Installation

```bash
# Clone and install
git clone https://github.com/jpchavat/claude-chat-export.git
cd claude-chat-export
uv sync

# Install browser for URL mode (one-time)
uv run playwright install chromium
```

## Usage

```bash
# From a share URL (recommended — includes artifacts)
uv run claude-chat-export https://claude.ai/share/<uuid>

# From a saved HTML file
uv run claude-chat-export conversation.html

# Custom output path
uv run claude-chat-export https://claude.ai/share/<uuid> -o notes.md

# Include full web search source content
uv run claude-chat-export https://claude.ai/share/<uuid> --include-sources
```

## Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output file path (default: `<uuid>.md` or `<file>.md`) |
| `--include-sources` | Include full web search source content instead of compact excerpts |
| `--no-artifacts` | Skip artifact code extraction |

## How it works

- **URL mode**: Uses Playwright to load the share page and intercepts the `chat_snapshots` API response, which contains the full conversation data including artifact widget code.
- **HTML mode**: Parses the saved HTML with BeautifulSoup to extract rendered messages. Artifact source code is not available in static HTML exports (the code is delivered via postMessage at runtime).

## License

MIT
