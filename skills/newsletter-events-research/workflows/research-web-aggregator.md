# Workflow: Research Web Aggregators

<required_reading>
Read before proceeding:
- `references/event-detection.md`
</required_reading>

<critical>
USE THE CLI TOOL - DO NOT import Python modules directly.

The CLI handles Firecrawl API calls and URL tracking. Claude's job is to extract events from the returned markdown.
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

1. Read the markdown content
2. Identify all events mentioned on the page
3. For each event, extract:
   - **Title**: Event name
   - **Date**: Parse to YYYY-MM-DD format
   - **Time**: Start and end times if available
   - **Venue**: Name and address
   - **Description**: Brief description
   - **Price**: Ticket price or "Free"
   - **Ticket URL**: Where to buy tickets
   - **Source URL**: The page URL (from `original_url`)

4. Skip pages that don't contain event information (navigation pages, category listings without dates)

## Step 4: Save Events to Database

For each extracted event, save to the database:

```bash
cd "$PLUGIN_DIR" && uv run python -c "
from pathlib import Path
from schemas.sqlite_storage import SqliteStorage
from schemas.event import Event, Venue, EventSource

storage = SqliteStorage(Path.home() / '.config/local-media-tools/data/events.db')

event = Event(
    title='EVENT_TITLE',
    venue=Venue(name='VENUE_NAME', address='VENUE_ADDRESS'),
    event_date='YYYY-MM-DD',
    start_time='HH:MM',
    source=EventSource.WEB_AGGREGATOR,
    source_url='ORIGINAL_URL',
    description='DESCRIPTION',
    price='PRICE',
    ticket_url='TICKET_URL',
    confidence=0.8,
    needs_review=True,
    review_notes='Extracted from SOURCE_NAME',
)

from schemas.event import EventCollection
result = storage.save(EventCollection(events=[event]))
print(f'Saved: {result.saved} new, {result.updated} updated')
"
```

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
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py show-stats
```

</process>

<success_criteria>
Web aggregator research complete when:
- [ ] CLI scrape command executed and returned pages JSON
- [ ] Events extracted from each page's markdown
- [ ] Events saved to database with `needs_review=True`
- [ ] Each processed URL marked as scraped via `mark-scraped`
- [ ] Statistics show updated page and event counts
</success_criteria>
