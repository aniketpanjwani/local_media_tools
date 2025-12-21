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
from pathlib import Path

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"
config = AppConfig.from_yaml(config_path)
sources = config.sources.web_aggregators.sources

if not sources:
    print("No web aggregator sources configured in sources.yaml")
    # Exit workflow
```

## Step 2: Discover and Filter URLs

For each aggregator, use its stored profile to discover event page URLs efficiently.

```python
from scripts.scrape_firecrawl import FirecrawlClient, FirecrawlError
from scripts.url_utils import normalize_url
from schemas.sqlite_storage import SqliteStorage
from datetime import date
import json
import re

client = FirecrawlClient()
db_path = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"
storage = SqliteStorage(db_path)

for source in sources:
    try:
        profile = source.profile  # May be None for legacy configs

        # 1. Discover event page URLs using profile-guided strategy
        if profile and profile.discovery_method == "crawl":
            # Use crawl with stored parameters (profile says map failed for this site)
            print(f"ℹ {source.name}: Using crawl (per profile)")
            crawl_result = client.app.crawl_url(
                source.url,
                limit=source.max_pages,
                max_discovery_depth=profile.crawl_depth,
                scrape_options={"formats": ["links"]}
            )
            all_links = []
            for page in crawl_result.get("data", []):
                all_links.extend(page.get("links", []))

            # Filter using learned regex from profile (or user override)
            pattern = source.event_url_pattern or profile.event_url_regex
            if pattern:
                discovered_urls = [u for u in all_links if re.search(pattern, u)]
            else:
                # Fallback to default patterns
                discovered_urls = client._filter_event_urls(all_links, None)
        else:
            # Default: use map (fast path, works for most sites)
            discovered_urls = client.discover_event_urls(
                url=source.url,
                max_pages=source.max_pages,
                event_url_pattern=source.event_url_pattern,
            )

        # 2. Normalize discovered URLs
        # Map normalized -> original for scraping
        normalized_map = {normalize_url(u): u for u in discovered_urls}

        # 3. Get already-scraped URLs for this source
        existing_urls = storage.get_scraped_urls_for_source(source.name)

        # 4. Filter to NEW URLs only
        new_urls = [(norm, orig) for norm, orig in normalized_map.items()
                    if norm not in existing_urls]

        print(f"ℹ {source.name}: Found {len(discovered_urls)} URLs, {len(new_urls)} new")

        if not new_urls:
            print(f"  → No new URLs to scrape")
            continue

        # Continue to scraping...
```

## Step 3: Scrape New URLs Only

```python
        pages_to_process = []
        for normalized_url, original_url in new_urls:
            try:
                # Scrape the page to get markdown
                page = client.scrape_url(original_url)
                pages_to_process.append({
                    "normalized_url": normalized_url,
                    "original_url": original_url,
                    "markdown": page.get("markdown", ""),
                    "title": page.get("title", ""),
                })
            except FirecrawlError as e:
                print(f"  ✗ Failed to scrape {original_url}: {e}")
                continue

        # Save raw markdown for reference
        data_dir = Path.home() / ".config" / "local-media-tools" / "data" / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        raw_path = data_dir / f"web_{source.name}_{date.today()}.json"
        with open(raw_path, "w") as f:
            json.dump(pages_to_process, f, indent=2)

        print(f"✓ {source.name}: scraped {len(pages_to_process)} new pages")

    except FirecrawlError as e:
        print(f"✗ {source.name}: {e}")
        continue
```

## Step 4: Extract Events (Claude)

For each scraped page, Claude analyzes the markdown and extracts events.

**For each page in `pages_to_process`:**

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
    source_url=page["original_url"],
    description=description,
    price=price,
    ticket_url=ticket_url,
    confidence=0.8,
    needs_review=True,
    review_notes=f"Extracted from {source.name}",
)
```

## Step 5: Save Events, Then Mark URLs Scraped

**CRITICAL**: Save events FIRST, then mark URLs as scraped. This prevents data
loss if event saving fails - we don't want to mark a URL as "scraped" when no
events were actually saved.

```python
from schemas.event import EventCollection

# For each page that was processed
for page in pages_to_process:
    events_from_page = events_by_url.get(page["original_url"], [])

    # 1. Save events FIRST
    if events_from_page:
        collection = EventCollection(events=events_from_page)
        result = storage.save(collection)
        print(f"  → {page['original_url']}: {result.saved} new, {result.updated} updated")

    # 2. THEN mark URL as scraped (only after events saved successfully)
    storage.save_scraped_page(
        source_name=source.name,
        url=page["normalized_url"],
        events_count=len(events_from_page),
    )

print(f"✓ {source.name}: Complete")
```

</process>

<success_criteria>
Web aggregator research complete when:
- [ ] All configured sources processed
- [ ] Only NEW URLs scraped (already-scraped URLs skipped)
- [ ] Raw markdown saved to `~/.config/local-media-tools/data/raw/web_*.json`
- [ ] Claude extracted events from markdown content
- [ ] Events saved BEFORE URLs marked as scraped (prevents data loss)
- [ ] Events saved to `~/.config/local-media-tools/data/events.db`
- [ ] URLs recorded in `scraped_pages` table
- [ ] Events marked with `needs_review=True` for human verification
</success_criteria>
