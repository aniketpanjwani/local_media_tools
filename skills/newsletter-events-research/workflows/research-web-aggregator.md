# Workflow: Research Web Aggregators

<required_reading>
Read before proceeding:
- `references/event-detection.md`
</required_reading>

<critical>
USE THE CLI TOOLS - DO NOT import Python modules directly.

The CLI handles:
- Firecrawl API calls (`cli_web.py`)
- URL tracking and deduplication (`cli_web.py`)
- Event saving with validation (`cli_events.py`)

Claude's job is to extract events from the returned markdown.
</critical>

<process>

## Step 0: Get Plugin Directory

```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save the output path as `PLUGIN_DIR`.

## Step 1: Discover URLs (Optional Preview)

To see what URLs will be scraped without scraping:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py discover --all
```

Or for a specific source:
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py discover --source "Source Name"
```

This shows how many URLs are found and how many are new (not yet scraped).

## Step 2: Scrape New Pages

Run the scraper to get markdown content from new URLs:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py scrape --source "Source Name"
```

Or scrape all sources:
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py scrape --all --limit 20
```

**Output:** JSON array of scraped pages, each with:
- `source_name`: Name of the web aggregator
- `original_url`: The page URL
- `normalized_url`: Canonical URL for tracking
- `title`: Page title
- `markdown`: Full page content as markdown
- `scraped_at`: Timestamp

## Step 3: Extract Events from Markdown (Claude)

For each page in the JSON output, analyze the markdown and extract events.

**For each page:**

1. Read the markdown content carefully
2. Identify all events mentioned on the page
3. For each event, extract:
   - **Title**: Event name
   - **Date**: Parse to YYYY-MM-DD format
   - **Time**: See time extraction guide below
   - **Venue**: Name and city
   - **Description**: 1-2 sentence summary
   - **Category**: music, art, food_drink, community, outdoor, market, workshop, or other
   - **Price**: Ticket price, "Free", or null
   - **Ticket URL**: Where to buy tickets
   - **Source URL**: The page URL (from `original_url`)

4. Skip pages that don't contain event information (navigation pages, category listings)

### Time Extraction Guide

Look for time patterns in the markdown and convert to 24-hour "HH:MM" format:

| Pattern | Example | Convert To |
|---------|---------|------------|
| 12-hour with AM/PM | "7:30 PM", "7pm", "7 PM" | "19:30" |
| 24-hour | "19:30", "19:00" | "19:30" |
| Doors/Show times | "Doors 6pm, Show 8pm" | "20:00" (use show time) |
| Range | "7pm - 10pm" | "19:00" (use start) |
| All day | "All day event" | null |
| No time found | - | null |

**Common patterns to look for:**
- "Saturday at 7:30 PM"
- "Starts at 8pm"
- "7:00 PM - 10:00 PM"
- "Doors open 6pm"
- Times in event cards or tables

## Step 4: Save Events to Database

Use the `cli_events.py` tool to save extracted events:

**Single event:**
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py save --json '{
  "title": "Jazz Night",
  "venue_name": "The Blue Note",
  "venue_city": "Kingston",
  "event_date": "2025-01-20",
  "start_time": "19:30",
  "source": "web_aggregator",
  "source_url": "https://example.com/events/jazz-night",
  "description": "Live jazz trio performing classic standards",
  "category": "music",
  "price": "$15"
}'
```

**Multiple events (batch):**

Write events to a temp file, then save:
```bash
# Write JSON file with events array
cat > /tmp/events.json << 'EOF'
[
  {"title": "Event 1", "venue_name": "Venue 1", "event_date": "2025-01-20", ...},
  {"title": "Event 2", "venue_name": "Venue 2", "event_date": "2025-01-21", ...}
]
EOF

# Save all events
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py save-batch --file /tmp/events.json
```

**Required fields:**
- `title`
- `venue_name`
- `event_date` (YYYY-MM-DD format)

**Optional fields:**
- `venue_city`, `venue_address`
- `start_time` (HH:MM 24-hour format)
- `source` (defaults to "web_aggregator")
- `source_url`, `ticket_url`, `event_url`
- `description`, `category`, `price`

## Step 5: Mark URLs as Scraped

**CRITICAL**: Only mark URLs as scraped AFTER successfully saving events.

For each page that was processed:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py mark-scraped \
  --source "Source Name" \
  --url "https://example.com/events/event-page" \
  --events-count 1
```

This prevents re-scraping the same URLs on future runs.

## Step 6: Show Statistics

After processing, show summary:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py stats
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py show-stats
```

</process>

<success_criteria>
Web aggregator research complete when:
- [ ] CLI scrape command executed and returned pages JSON
- [ ] Events extracted from each page's markdown (including times when available)
- [ ] Events saved using `cli_events.py` (not inline Python)
- [ ] Each processed URL marked as scraped via `mark-scraped`
- [ ] Statistics show updated page and event counts
</success_criteria>
