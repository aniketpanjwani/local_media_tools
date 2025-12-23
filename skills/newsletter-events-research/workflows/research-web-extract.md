# Workflow: Extract Events from Scraped Pages

<purpose>
After Phase 1 scrapes pages, extract events page-by-page using CLI tools.
</purpose>

<critical>
YOU MUST USE CLI TOOLS FOR ALL DATA ACCESS.

DO NOT:
- Read files from data/raw/ directly
- Import Python modules
- Read source code files
- Write inline Python scripts
- Use SqliteStorage or EventCollection directly

THE ONLY WAY TO ACCESS PAGES:
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py list-pages
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py read-page --source "Name" --index N
```

THE ONLY WAY TO SAVE EVENTS:
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py save --json '{...}'
```
</critical>

<process>

## Step 1: Get Plugin Directory

```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save as `PLUGIN_DIR`.

## Step 2: List All Scraped Pages

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py list-pages
```

This shows all pages from the most recent scrape with their index numbers.
Output example:
```
 Idx Source                    Title
---------------------------------------------------------------------------
   0 Tourism Winnipeg          Winter Festival 2025
   1 Tourism Winnipeg          Jazz Night at The Park
   2 Eventbrite Winnipeg       Tech Meetup - December
...
```

## Step 3: Process Pages One at a Time

For EACH page, in order:

### 3a. Read the page content

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py read-page --source "Source Name" --index 0
```

This outputs the page's markdown content.

### 3b. Extract event details from the markdown

Look for:
- **Title**: Event name
- **Date**: Convert to YYYY-MM-DD
- **Time**: Convert to HH:MM (24-hour) or null
- **Venue**: Name and city
- **Description**: 1-2 sentences
- **Category**: music, art, food_drink, community, outdoor, market, workshop, other
- **Price**: Ticket price, "Free", or null

Skip pages without event information (navigation, category listings).

### Time Conversion

| Input | Output |
|-------|--------|
| "7:30 PM" | "19:30" |
| "7pm" | "19:00" |
| "Doors 6pm, Show 8pm" | "20:00" (use show time) |
| "All day" | null |
| Not found | null |

### 3c. Save the event

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

### 3d. Move to next page

Increment index and repeat steps 3a-3c.

## Step 4: Mark Source as Scraped

After processing all pages from a source:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py mark-scraped \
  --source "Source Name" \
  --url "https://example.com" \
  --events-count N
```

## Step 5: Show Statistics

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_events.py stats
```

</process>

<success_criteria>
- [ ] Used `list-pages` to enumerate pages (NOT read raw files)
- [ ] Used `read-page` to read each page (NOT Read tool on data/raw/)
- [ ] Each event saved with `cli_events.py save --json`
- [ ] Sources marked as scraped with `cli_web.py mark-scraped`
- [ ] Statistics shown
</success_criteria>
