# Workflow: Research Facebook

<required_reading>
Read before proceeding:
- `references/facebook-scraper-api.md`
- `references/event-detection.md`
</required_reading>

<process>
## Step 1: Load Configuration

```python
from config.config_schema import AppConfig

config = AppConfig.from_yaml("config/sources.yaml")
pages = config.sources.facebook.pages
```

## Step 2: Scrape Each Facebook Page

For each Facebook page in the config:

```python
from scripts.facebook_bridge import FacebookBridge

bridge = FacebookBridge(timeout=120)

for page in pages:
    try:
        events = bridge.scrape_page_events(page.url)

        # Save raw data
        save_to = f"tmp/extraction/raw/facebook_{page.name}_{date.today()}.json"

    except FacebookScraperError as e:
        # Log error but continue with other pages
        logger.error("facebook_scrape_failed", page=page.name, error=str(e))
        continue
```

## Step 3: Normalize Events

Convert Facebook data to Event objects:

```python
from schemas.event import Event, Venue, EventSource
from datetime import date, time

for fb_event in events:
    venue = Venue(
        name=fb_event.get("venue", {}).get("name", page.name),
        city=fb_event.get("venue", {}).get("city"),
        address=fb_event.get("venue", {}).get("address"),
    )

    event = Event(
        title=fb_event["title"],
        venue=venue,
        event_date=parse_date(fb_event["event_date"]),
        start_time=parse_time(fb_event.get("start_time")),
        source=EventSource.FACEBOOK,
        source_url=fb_event.get("source_url"),
        ticket_url=fb_event.get("ticket_url"),
        image_url=fb_event.get("image_url"),
        description=fb_event.get("description"),
    )
```

## Step 4: Download Event Images

```python
from scripts.scrape_instagram import download_image

for event in events:
    if event.image_url:
        download_image(
            url=event.image_url,
            output_dir=f"tmp/extraction/images/facebook",
            filename=f"{event.source_id}.jpg"
        )
```

## Step 5: Save Results

```python
from schemas.storage import EventStorage
from schemas.event import EventCollection

collection = EventCollection(events=all_events)
storage = EventStorage("tmp/extraction/events.json")
storage.save(collection)
```
</process>

<success_criteria>
Facebook research complete when:
- [ ] All configured pages scraped
- [ ] Event images downloaded
- [ ] Raw data saved to `tmp/extraction/raw/`
- [ ] Events saved to `tmp/extraction/events.json`
</success_criteria>
