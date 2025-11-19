# YouTube Recipes CLI

Extract recipes from YouTube cooking videos using AI and upload them to Docmost.

Built with modern Python tools: **uv**, **Typer**, and **Rich** for a beautiful CLI experience.


## Features

- 🎥 **Smart YouTube URL parsing** - All YouTube URL formats supported
- 🤖 **AI-powered extraction** - Uses Groq AI (Llama 3.3 70B) for detailed recipe extraction
- 🌍 **Multi-language support** - Spanish, English, French, German, Italian, Portuguese
- ✨ **Beautiful CLI** - Rich terminal output with progress bars
- 📦 **Batch processing** - Process multiple videos from a file
- 👀 **Preview mode** - Review recipes before uploading
- 💾 **Local export** - Save recipes as markdown files
- 🔄 **Flexible upload** - Upload to Docmost or export locally

## Installation

### Prerequisites

Install [uv](https://github.com/astral-sh/uv) (fast Python package manager):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Optional but recommended - install [just](https://github.com/casey/just) (command runner):

```bash
# macOS
brew install just

# Linux
cargo install just
# or use your package manager

# Windows
cargo install just
# or: scoop install just
```

### Setup

```bash
# 1. Navigate to project
cd yt-recipes

# 2. Install dependencies (creates .venv and installs package)
uv sync

# 3. Setup environment
cp .env.example .env
# Edit .env with your API keys
```

**Or use just:**

```bash
just setup
```

### Configure Credentials

Edit `.env` with your API keys:

```env
# RapidAPI (for YouTube transcripts)
RAPIDAPI_KEY=your_rapidapi_key_here

# Groq API (for AI recipe extraction)
GROQ_API_KEY=your_groq_api_key_here

# Docmost (for uploading recipes)
DOCMOST_URL=https://your-docmost.com
DOCMOST_EMAIL=your_email@example.com
DOCMOST_PASSWORD=your_password
DOCMOST_SPACE_ID=your_space_id
DOCMOST_PARENT_PAGE_ID=your_parent_page_id
```

**Where to get API keys:**
- **RapidAPI**: https://rapidapi.com/h0p3rwe/api/youtube-transcript3
- **Groq**: https://console.groq.com/

## Usage

### Basic Usage

```bash
# Process a single video
uv run yt-recipes process "https://www.youtube.com/watch?v=VIDEO_ID"

# With preview
uv run yt-recipes process "URL" --preview

# In a specific language
uv run yt-recipes process "URL" --language en

# Save locally without uploading
uv run yt-recipes process "URL" --no-upload --export-dir ./my-recipes
```

### Using `just` (easier!)

```bash
# Show all commands
just

# Process with preview
just preview "https://youtube.com/..."

# Export locally
just export "URL" ./recipes

# Verbose logging
just verbose "URL"
```

### Batch Processing

Create a file with URLs (one per line):

```text
# urls.txt
https://www.youtube.com/watch?v=VIDEO_ID_1
https://youtu.be/VIDEO_ID_2
https://www.youtube.com/watch?v=VIDEO_ID_3
```

Process all:

```bash
uv run yt-recipes batch urls.txt

# Or with just
just batch urls.txt
```

## Commands

### `yt-recipes process`

Process a single YouTube URL.

```bash
uv run yt-recipes process URL [OPTIONS]
```

**Options:**
- `--language, -l` - Target language (es, en, fr, de, it, pt) [default: es]
- `--preview, -p` - Preview recipes before uploading
- `--export-dir, -e` - Export to local directory
- `--no-upload` - Skip Docmost upload
- `--verbose, -v` - Verbose logging

**Examples:**
```bash
# Basic
uv run yt-recipes process "https://youtu.be/VIDEO_ID"

# English with preview
uv run yt-recipes process "URL" -l en -p

# Export only
uv run yt-recipes process "URL" --no-upload -e ./recipes
```

### `yt-recipes batch`

Process multiple URLs from a file.

```bash
uv run yt-recipes batch FILE [OPTIONS]
```

Same options as `process` command.

### `yt-recipes version`

Show version information.

```bash
uv run yt-recipes version
```

## How It Works

1. **Extract Video ID** - Parses YouTube URL
2. **Fetch Transcript** - Gets transcript via RapidAPI
3. **Extract Recipes** - AI identifies and extracts recipes with details
4. **Format** - Converts to markdown with all recipe information
5. **Export/Upload** - Saves locally and/or uploads to Docmost

## Recipe Output Format

Extracted recipes include:

- Name (translated to target language)
- Icon (appropriate emoji)
- Servings, prep time, cook time, total time
- Difficulty level
- Complete ingredients list with quantities
- Step-by-step instructions
- Tips, variations, and notes
- YouTube link back to original video

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync

# Or with just
just setup
```

### Common Tasks

```bash
# Run tests
just test

# Lint code
just lint

# Format code
just format

# Check everything
just check

# Add dependency
just add httpx

# Add dev dependency
just add-dev pytest
```

### Manual Commands

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Add dependency
uv add package-name

# Add dev dependency
uv add --group dev package-name
```

### Alternative Running Methods

```bash
# 1. Via uv run (recommended)
uv run yt-recipes process "URL"

# 2. After activating venv
source .venv/bin/activate
yt-recipes process "URL"

# 3. As Python module
uv run python -m yt_recipes.cli process "URL"
```

## Troubleshooting

### "Failed to spawn: `yt_recipes`"

**Problem:** Package not installed in environment.

**Solution:**
```bash
uv sync  # This installs the package with entry points
```

### "ImportError: attempted relative import with no known parent package"

**Problem:** Running the module file directly.

**Solution:** Use one of these methods:
```bash
uv run yt-recipes process "URL"     # ✓ Correct
python -m yt_recipes.cli process    # ✓ Correct
python yt_recipes/cli.py            # ✗ Wrong
```

### "Error loading settings"

**Problem:** Missing or incomplete `.env` file.

**Solution:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

### "Failed to fetch transcript"

**Causes:**
- Invalid RapidAPI key
- Video has no captions/subtitles
- RapidAPI subscription expired

**Solution:**
- Verify API key in `.env`
- Check video has captions
- Verify RapidAPI subscription is active

### "Groq API request failed"

**Causes:**
- Invalid Groq API key
- Rate limit exceeded
- Network issues

**Solution:**
- Verify API key in `.env`
- Wait if rate-limited
- Check internet connection

## Project Structure

```
yt_recipes/
├── __init__.py          # Package initialization
├── cli.py               # Main CLI application (Typer)
├── config.py            # Settings management (Pydantic)
├── youtube.py           # Video ID extraction & transcripts
├── ai.py                # Groq AI recipe extraction
├── docmost.py           # Docmost API client
├── formatter.py         # Recipe markdown formatting
└── utils.py             # Utilities and logging
```

## Tech Stack

- **uv** - Fast Python package manager
- **hatchling** - Modern build backend (flat layout compatible)
- **just** - Modern command runner
- **Typer** - CLI framework
- **Rich** - Beautiful terminal output
- **httpx** - Modern HTTP client
- **Pydantic** - Data validation & settings
- **Groq AI** - LLM inference (Llama 3.3 70B)

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `just check` to lint and test
5. Submit a pull request

## Credits

Built by [PatillaCode](https://github.com/patillacode)

Powered by:
- [uv](https://github.com/astral-sh/uv) - Package management
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Groq](https://groq.com/) - AI inference
- [RapidAPI](https://rapidapi.com/) - YouTube transcripts

---

**Enjoy extracting recipes!** 🍽️

Found a bug? [Open an issue](https://github.com/patillacode/yt-recipes-cli/issues)
