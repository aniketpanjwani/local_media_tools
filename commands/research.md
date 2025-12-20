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

### Step 1: Get the plugin directory

```bash
PLUGIN_DIR=$(cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath')
echo "Plugin directory: $PLUGIN_DIR"
```

### Step 2: Run the CLI from the plugin directory

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py scrape --all

# Check results
cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py show-stats
```

The CLI tool handles:
- Correct ScrapeCreators API parameters
- Rate limiting and retries
- Database storage with proper relationships

## Instructions

1. Get plugin directory: `PLUGIN_DIR=$(cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath')`
2. Read config from `~/.config/local-media-tools/sources.yaml`
3. **Instagram:** Run `cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py scrape --all`
4. **Facebook:** Use Chrome MCP with facebook-event-scraper (Node.js subprocess)
5. **Classify posts:** Read and follow `$PLUGIN_DIR/skills/newsletter-events-research/workflows/research-instagram.md` Steps 3-7 to classify posts and extract events
6. Report summary with `cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py show-stats`

## Classification (Step 5 Details)

After scraping, you MUST classify each unclassified post:

1. **List unclassified posts:** `cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py list-posts --handle <handle>`
2. **For each unclassified post, analyze the caption:**
   - **CLEARLY_NOT_EVENT:** Thank you posts, past recaps, food photos, memes → skip
   - **CLEARLY_EVENT:** Has future date, time, venue, event keywords → extract event
   - **AMBIGUOUS:** Need to check images for details
3. **For posts needing image analysis:** Download and analyze flyer images for event details
4. **Extract events:** Create Event objects with title, date, time, venue, price
5. **Save to database:** Update post classification and save extracted events

## Expected Output

- Raw data saved to `~/.config/local-media-tools/data/raw/`
- Event images saved to `~/.config/local-media-tools/data/images/`
- Events saved to SQLite database
- Summary printed showing:
  - Events found per source
  - Duplicates removed
  - Events flagged for review
