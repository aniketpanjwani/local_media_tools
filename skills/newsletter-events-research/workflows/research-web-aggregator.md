# Workflow: Research Web Aggregators

<required_reading>
Read before proceeding:
- `references/firecrawl-api.md`
- `references/event-detection.md`
</required_reading>

<process>
## Step 1: Load Configuration

```python
from config.config_schema import AppConfig

config = AppConfig.from_yaml("config/sources.yaml")
sources = config.sources.web_aggregators.sources

if not sources:
    print("No web aggregator sources configured in sources.yaml")
    # Exit workflow
```

## Step 2: Scrape Each Aggregator

The Python client discovers URLs and scrapes pages, returning markdown.
Claude then extracts events from the markdown content.

```python
from scripts.scrape_firecrawl import FirecrawlClient, FirecrawlError
from datetime import date
import json

client = FirecrawlClient()

for source in sources:
    try:
        # Get markdown content from pages
        pages = client.scrape_aggregator(
            url=source.url,
            max_pages=source.max_pages,
            event_url_pattern=source.event_url_pattern,
        )

        # Save raw markdown for reference
        raw_path = f"tmp/extraction/raw/web_{source.name}_{date.today()}.json"
        with open(raw_path, "w") as f:
            json.dump(pages, f, indent=2)

        print(f"✓ {source.name}: scraped {len(pages)} pages")

    except FirecrawlError as e:
        print(f"✗ {source.name}: {e}")
        continue
```

## Step 3: Extract Events (Claude)

For each scraped page, Claude analyzes the markdown and extracts events.

**For each page's markdown content:**

1. Read the markdown
2. Identify all events mentioned
3. For each event, extract:
   - Title
   - Date (parse to YYYY-MM-DD)
   - Time (start and end if available)
   - Venue name and address
   - Description
   - Price (or "Free")
   - Ticket URL
   - Event URL (the page it came from)

4. Create Event objects:

```python
from schemas.event import Event, Venue, EventSource

event = Event(
    title=extracted_title,
    venue=Venue(name=venue_name, address=venue_address),
    event_date=parsed_date,
    start_time=parsed_time,
    source=EventSource.WEB_AGGREGATOR,
    source_url=page_url,
    description=description,
    price=price,
    ticket_url=ticket_url,
    confidence=0.8,
    needs_review=True,
    review_notes=f"Extracted from {source.name}",
)
```

## Step 4: Merge with Existing Events

```python
from schemas.storage import EventStorage

storage = EventStorage("tmp/extraction/events.json")
existing = storage.load()

added = 0
for event in extracted_events:
    if existing.add_event(event):
        added += 1

storage.save(existing)
print(f"Added {added} new events (deduplicated)")
```

</process>

<success_criteria>
Web aggregator research complete when:
- [ ] All configured sources scraped
- [ ] Raw markdown saved to `tmp/extraction/raw/web_*.json`
- [ ] Claude extracted events from markdown content
- [ ] Events merged to `tmp/extraction/events.json`
- [ ] Events marked with `needs_review=True` for human verification
</success_criteria>
