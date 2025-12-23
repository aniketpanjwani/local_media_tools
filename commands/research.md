---
name: newsletter-events:research
description: Research and collect events from all configured sources (Instagram, web aggregators, Facebook)
---

# Research Events

Research and collect events from all configured sources (Instagram, web aggregators, and ad-hoc Facebook URLs).

## Configuration Location

Configuration is loaded from `~/.config/local-media-tools/sources.yaml`.
Scraped data is saved to `~/.config/local-media-tools/data/events.db`.

## Critical: Use CLI Tools Only

**NEVER use Firecrawl, Chrome MCP, curl, or raw API calls for Instagram.**

### Step 1: Get the plugin directory

Run this command to get the plugin path:
```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save the output path and use it as `PLUGIN_DIR` in subsequent commands.

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

1. Get plugin directory by running: `cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'` and save output as PLUGIN_DIR
2. Read config from `~/.config/local-media-tools/sources.yaml`
3. **Instagram:** Run `cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py scrape --all`
4. **Web Aggregators:** Run `cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py scrape --all --limit 20`
5. **Facebook:** Pass event URLs directly (e.g., `/research https://facebook.com/events/123`)
6. **Classify posts:** Read and follow `$PLUGIN_DIR/skills/newsletter-events-research/workflows/research-instagram.md` Steps 3-7 to classify posts and extract events
7. **Extract web events:** Use `cli_web.py list-pages` and `read-page` to process pages one at a time (see below)
8. Report summary with `cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py show-stats`

## Classification (Step 6 Details)

After scraping, you MUST classify each unclassified post:

1. **List unclassified posts:** `cd "$PLUGIN_DIR" && uv run python scripts/cli_instagram.py list-posts --handle <handle>`
2. **For each unclassified post, analyze the caption:**
   - **CLEARLY_NOT_EVENT:** Thank you posts, past recaps, food photos, memes → skip
   - **CLEARLY_EVENT:** Has future date, time, venue, event keywords → extract event
   - **AMBIGUOUS:** Need to check images for details
3. **For posts needing image analysis:** Download and analyze flyer images for event details
4. **Extract events:** Create Event objects with title, date, time, venue, price
5. **Save to database:** Update post classification and save extracted events

## Web Aggregator Event Extraction (Step 7 Details)

**CRITICAL: Do NOT read raw JSON files from `data/raw/`. Use CLI commands instead.**

After scraping, process pages one at a time:

### 7a. List all scraped pages
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py list-pages
```

### 7b. Read each page individually
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py read-page --source "Source Name" --index 0
```

### 7c. Extract event details from the markdown output
Look for: title, date (YYYY-MM-DD), time (HH:MM 24hr), venue, description, price

### 7d. Save each event
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py save --json '{
  "title": "Event Name",
  "venue_name": "Venue",
  "event_date": "2025-01-20",
  "start_time": "19:30",
  "source": "web_aggregator",
  "source_url": "https://..."
}'
```

### 7e. Mark source as scraped when done
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py mark-scraped --source "Name" --url "URL" --events-count N
```

Skip pages that are navigation/category listings without specific event details.

## Expected Output

- Raw data saved to `~/.config/local-media-tools/data/raw/`
- Event images saved to `~/.config/local-media-tools/data/images/`
- Events saved to SQLite database
- Summary printed showing:
  - Events found per source
  - Duplicates removed
  - Events flagged for review
