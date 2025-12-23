# Workflow: Extract Events from Scraped Pages

<purpose>
Given JSON from the scrape workflow, extract events and save them using the CLI.
</purpose>

<critical>
YOU MUST USE cli_events.py TO SAVE EVENTS.

DO NOT:
- Import Python modules
- Read source code files
- Read files from data/raw/
- Write inline Python scripts
- Use SqliteStorage or EventCollection directly

THE ONLY WAY TO SAVE EVENTS:
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py save --json '{...}'
```
</critical>

<input>
JSON array of scraped pages from `research-web-scrape.md`.
Each page has `markdown` content to analyze.
</input>

<process>

## Step 1: Get Plugin Directory

```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save as `PLUGIN_DIR`.

## Step 2: Extract Events from Each Page

For each page in the JSON:

1. Read the `markdown` field
2. Look for event details:
   - **Title**: Event name
   - **Date**: Convert to YYYY-MM-DD
   - **Time**: Convert to HH:MM (24-hour) or null
   - **Venue**: Name and city
   - **Description**: 1-2 sentences
   - **Category**: music, art, food_drink, community, outdoor, market, workshop, other
   - **Price**: Ticket price, "Free", or null

3. Skip pages without event information (navigation, category listings)

### Time Conversion

| Input | Output |
|-------|--------|
| "7:30 PM" | "19:30" |
| "7pm" | "19:00" |
| "Doors 6pm, Show 8pm" | "20:00" (use show time) |
| "All day" | null |
| Not found | null |

## Step 3: Save Each Event with CLI

For EACH extracted event, run:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py save --json '{
  "title": "Event Name",
  "venue_name": "Venue Name",
  "venue_city": "City",
  "event_date": "2025-01-20",
  "start_time": "19:30",
  "source": "web_aggregator",
  "source_url": "https://example.com/events/page",
  "description": "Brief description",
  "category": "music",
  "price": "$15"
}'
```

**Required fields:** title, venue_name, event_date
**Optional fields:** venue_city, start_time, source, source_url, description, category, price

## Step 4: Mark URLs as Scraped

After saving events from a page:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py mark-scraped \
  --source "Source Name" \
  --url "https://example.com/events/page" \
  --events-count 1
```

## Step 5: Show Statistics

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py stats
```

</process>

<success_criteria>
- [ ] Events extracted from markdown (not source code)
- [ ] Each event saved with `cli_events.py save --json`
- [ ] URLs marked as scraped with `cli_web.py mark-scraped`
- [ ] Statistics shown
</success_criteria>
