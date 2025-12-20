---
name: newsletter-events:research
description: Research and collect events from all configured sources (Instagram and Facebook)
---

# Research Events

Research and collect events from all configured sources (Instagram and Facebook).

## Configuration Location

Configuration is loaded from `~/.config/local-media-tools/sources.yaml`.
Scraped data is saved to `~/.config/local-media-tools/data/events.db`.

## Critical: Use CLI Tools Only

**NEVER use Firecrawl, Chrome MCP, curl, or raw API calls for Instagram.**

Instagram scraping MUST use the CLI tool:

```bash
# Scrape all configured Instagram accounts
uv run python scripts/cli_instagram.py scrape --all

# Check results
uv run python scripts/cli_instagram.py show-stats
```

The CLI tool handles:
- Correct ScrapeCreators API parameters
- Rate limiting and retries
- Database storage with proper relationships

## Instructions

1. Read config from `~/.config/local-media-tools/sources.yaml`
2. **Instagram:** Run `uv run python scripts/cli_instagram.py scrape --all`
3. **Facebook:** Use Chrome MCP with facebook-event-scraper (Node.js subprocess)
4. Classify posts and extract events from scraped data
5. Report summary with `uv run python scripts/cli_instagram.py show-stats`

## Expected Output

- Raw data saved to `~/.config/local-media-tools/data/raw/`
- Event images saved to `~/.config/local-media-tools/data/images/`
- Events saved to SQLite database
- Summary printed showing:
  - Events found per source
  - Duplicates removed
  - Events flagged for review
