# YouTube Recipes CLI - just commands
# Install just: https://github.com/casey/just

# Show all available commands
default:
    @just --list

# Install dependencies and setup project
setup:
    @echo "Setting up YouTube Recipes CLI..."
    @if [ ! -f .env ]; then \
        cp .env.example .env && \
        echo "✓ Created .env file (please edit with your credentials)"; \
    else \
        echo "✓ .env file already exists"; \
    fi
    uv sync
    @echo "✓ Setup complete! Run 'just test-install' to verify."

# Sync dependencies
sync:
    uv sync

# Test that installation works
test-install:
    @echo "Testing installation..."
    uv run yt-recipes version

# Test Docmost login
test-docmost:
    @echo "Testing Docmost login..."
    uv run python test_docmost_login.py

# Run the CLI with a URL (usage: just run "https://youtube.com/...")
run URL:
    uv run yt-recipes process "{{URL}}"

# Run with preview mode
preview URL:
    uv run yt-recipes process "{{URL}}" --preview

# Run in verbose mode
verbose URL:
    uv run yt-recipes process "{{URL}}" --verbose

# Process batch URLs from file
batch FILE:
    uv run yt-recipes batch "{{FILE}}"
