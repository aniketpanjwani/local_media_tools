# Workflow: Research Instagram

<required_reading>
Read before proceeding:
- `references/scrapecreators-api.md`
- `references/event-detection.md`
</required_reading>

<process>
## Step 1: Load Configuration

```python
from config.config_schema import AppConfig

config = AppConfig.from_yaml("config/sources.yaml")
accounts = config.sources.instagram.accounts
priority = config.sources.instagram.priority_handles
```

## Step 2: Scrape Each Account

For each Instagram account in the config:

```python
from scripts.scrape_instagram import ScrapeCreatorsClient, download_image

client = ScrapeCreatorsClient()

for account in accounts:
    # Fetch recent posts
    result = client.get_instagram_user_posts(account.handle, limit=20)

    # Save raw data
    save_to = f"tmp/extraction/raw/instagram_{account.handle}_{date.today()}.json"

    # Download images from posts
    for post in result.get("posts", []):
        for image in post.get("images", []):
            download_image(
                url=image["url"],
                output_dir=f"tmp/extraction/images/{account.handle}",
                filename=f"{post['id']}.jpg"
            )
```

## Step 3: Analyze Images with Vision

For each downloaded image:

1. Use Claude's vision to analyze the flyer
2. Extract: title, date, time, venue, price, ticket URL
3. Score confidence (0-1) based on clarity

**Vision prompt:**
```
Analyze this event flyer image. Extract:
- Event title
- Date (if visible)
- Time (if visible)
- Venue name
- Price/admission (if visible)
- Any ticket URL or QR code

If information is unclear, indicate uncertainty.
```

## Step 4: Create Event Candidates

Convert extracted data to Event objects:

```python
from schemas.event import Event, Venue, EventSource, EventCategory

event = Event(
    title=extracted_title,
    venue=Venue(name=venue_name, instagram_handle=account.handle),
    event_date=parsed_date,
    source=EventSource.INSTAGRAM,
    source_url=post_url,
    image_url=image_url,
    confidence=calculated_confidence,
)
```

## Step 5: Save Results

```python
from schemas.storage import EventStorage
from schemas.event import EventCollection

collection = EventCollection(events=events)
storage = EventStorage("tmp/extraction/events.json")
storage.save(collection)
```
</process>

<success_criteria>
Instagram research complete when:
- [ ] All configured accounts scraped
- [ ] Images downloaded to `tmp/extraction/images/`
- [ ] Raw data saved to `tmp/extraction/raw/`
- [ ] Events extracted and saved to `tmp/extraction/events.json`
</success_criteria>
