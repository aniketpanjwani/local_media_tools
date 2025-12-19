# Local Media Tools

A Claude Code plugin for scraping local events from Instagram, Facebook, and web sources.

## Quick Start

```bash
# Setup environment
./scripts/setup.sh

# Configure sources
cp config/sources.example.yaml config/sources.yaml
# Edit config/sources.yaml with your accounts

# Add API keys to .env:
# SCRAPECREATORS_API_KEY=your_key (required for Instagram)
# FIRECRAWL_API_KEY=your_key (optional, for web aggregators)
```

## Skills

- **newsletter-events-setup** - Environment setup and verification
- **newsletter-events-research** - Scrape events from configured sources
- **newsletter-events-write** - Generate newsletter markdown from stored events

## Commands

- `/setup` - Set up or verify environment
- `/setup-location` - Configure Facebook location-based discovery
- `/research` - Scrape all configured sources
- `/write` - Generate newsletter from stored events

## Architecture

This plugin uses two runtimes:
- **Python** (primary) - ScrapeCreators API, Firecrawl, deduplication
- **Node.js** (via subprocess) - Facebook event scraping

## Project Structure

```
.claude-plugin/    # Plugin manifest
  plugin.json
commands/          # Slash commands
skills/            # Skills with workflows and references
agents/            # Proactive agents
scripts/           # Scrapers and utilities
config/            # Configuration files
schemas/           # Pydantic data models
tmp/               # Working directory (gitignored)
  extraction/      # Raw scraped data, events.db (SQLite)
  output/          # Generated newsletters
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

Edit `config/sources.yaml` (see `sources.example.yaml` for full documentation):

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

- **Events database**: `tmp/extraction/events.db` (SQLite)
- **Newsletters**: `tmp/output/newsletter_YYYY-MM-DD.md`
