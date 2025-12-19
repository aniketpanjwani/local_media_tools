# Local Media Tools

A Claude Code plugin for scraping local events from Instagram, Facebook, and web sources.

## Quick Start

```bash
# Setup environment
./scripts/setup.sh

# Configure sources
# Edit ~/.config/local-media-tools/sources.yaml

# Add API keys to ~/.config/local-media-tools/.env:
# SCRAPECREATORS_API_KEY=your_key (required for Instagram)
# FIRECRAWL_API_KEY=your_key (optional, for web aggregators)
```

## Skills

- **newsletter-events-setup** - Environment setup and verification
- **newsletter-events-research** - Scrape events from configured sources
- **newsletter-events-write** - Generate newsletter markdown from stored events

## Commands

- `/newsletter-events:setup` - Set up or verify environment
- `/newsletter-events:setup-location` - Configure Facebook location-based discovery
- `/newsletter-events:research` - Scrape all configured sources
- `/newsletter-events:write` - Generate newsletter from stored events

## Architecture

This plugin uses two runtimes:
- **Python** (primary) - ScrapeCreators API, Firecrawl, deduplication
- **Node.js** (via subprocess) - Facebook event scraping

## Directory Structure

**Plugin (code/dependencies):** stays in plugin cache, changes on upgrade

**User Config (stable location, persists across upgrades):**
```
~/.config/local-media-tools/
├── .env                    # API keys
├── sources.yaml            # Event source configuration
└── data/
    ├── events.db           # SQLite database
    ├── raw/                # Raw API responses
    └── images/             # Downloaded event images
```

**Output:** Current working directory (newsletters)

## Project Structure

```
.claude-plugin/    # Plugin manifest
  plugin.json
commands/          # Slash commands
skills/            # Skills with workflows and references
agents/            # Proactive agents
scripts/           # Scrapers and utilities
  paths.py         # Centralized path resolver
config/            # Configuration templates
schemas/           # Pydantic data models
tests/             # Pytest test suite
```

## Development

```bash
# Run tests
uv run pytest

# Format
uv run ruff format .
```

## Configuration

Configuration is stored in `~/.config/local-media-tools/sources.yaml`.

See `config/sources.example.yaml` for full documentation:

```yaml
newsletter:
  name: "My Local Events"
  region: "Hudson Valley, NY"
  formatting_preferences: |
    Organize by date with day headers.
    Use emojis for categories.

sources:
  instagram:
    accounts:
      - handle: "local_venue"
        name: "Local Venue"
        type: "music_venue"

  facebook:
    pages:
      - url: "https://facebook.com/venue/events"
        name: "The Venue"

  web_aggregators:
    sources:
      - url: "https://localevents.com"
        name: "Local Events"
        source_type: "listing"
```

## Output

- **Events database**: `~/.config/local-media-tools/data/events.db` (SQLite)
- **Newsletters**: `./newsletter_YYYY-MM-DD.md` (in current directory)
