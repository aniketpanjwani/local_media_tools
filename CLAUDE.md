# Newsletter Events Plugin

A Claude Code plugin that automates local newsletter event curation by scraping Instagram and Facebook.

## Quick Start

```bash
# Setup environment
./scripts/setup.sh

# Configure sources
cp config/sources.example.yaml config/sources.yaml
# Edit config/sources.yaml with your accounts

# Add API keys
# Edit .env with your SCRAPECREATORS_API_KEY
```

## Skills

- **newsletter-events-setup** - Environment setup and verification
- **newsletter-events-research** - Scrape events from configured sources
- **newsletter-events-write** - Generate newsletter markdown from events

## Commands

- `/setup-newsletter` - Set up or verify environment
- `/research-events` - Scrape all configured sources
- `/write-newsletter` - Generate newsletter from cached events
- `/newsletter` - Run complete pipeline (research + write)

## Architecture

This plugin uses two runtimes:
- **Python** (primary) - ScrapeCreators API, deduplication, templating
- **Node.js** (via subprocess) - Facebook event scraping

## Project Structure

```
scripts/           # Scrapers and utilities
config/            # Configuration files
schemas/           # Pydantic data models
templates/         # Jinja2 newsletter templates
tmp/               # Working directory (gitignored)
  extraction/      # Raw scraped data
  output/          # Generated newsletters
tests/             # Pytest test suite
```

## Development

```bash
# Run tests
uv run pytest

# Type check
uv run mypy .

# Format
uv run ruff format .
```

## Configuration

Edit `config/sources.yaml`:

```yaml
newsletter:
  name: "My Local Events"
  region: "Hudson Valley, NY"

sources:
  instagram:
    accounts:
      - handle: "local_venue"
        name: "Local Venue"
        type: "music_venue"
```
