# Workflow: Research Instagram

<required_reading>
Read before proceeding:
- `references/scrapecreators-api.md`
- `references/event-detection.md`
</required_reading>

<critical>
**NOT EVERY POST IS AN EVENT.** You must classify each post first. Only posts that announce specific upcoming events should become Event objects. Skip posts that are:
- Food/drink photos
- Staff/team photos
- Venue interior shots
- Memes or reposts
- General announcements without event details
- Throwback/recap posts of past events
</critical>

<process>
## Step 1: Load Configuration

```python
from config.config_schema import AppConfig
from pathlib import Path

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"
config = AppConfig.from_yaml(config_path)
accounts = config.sources.instagram.accounts
```

## Step 2: Scrape Each Account

For each Instagram account in the config:

```python
from scripts.scrape_instagram import ScrapeCreatorsClient

client = ScrapeCreatorsClient()

for account in accounts:
    result = client.get_instagram_user_posts(account.handle, limit=20)

    # Save raw data
    data_dir = Path.home() / ".config" / "local-media-tools" / "data"
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
```

## Step 3: Classify Each Post (CRITICAL)

**For EACH post, you must determine: Is this an event announcement?**

Analyze the post caption AND image. Ask yourself:

1. **Does it announce a FUTURE event?** (not a recap of past event)
2. **Does it have event details?** (date, time, performer, ticket info)
3. **Is there an event flyer image?** (designed graphic, not just a photo)

**Classification prompt for each post:**
```
Look at this Instagram post (caption + image).

Is this announcing a specific upcoming event?

ANSWER ONLY: "EVENT" or "NOT_EVENT"

If EVENT, briefly note: title, date (if visible), venue
If NOT_EVENT, briefly note why (e.g., "food photo", "past event recap", "general announcement")
```

**Only proceed to Step 4 for posts classified as "EVENT".**

## Step 4: Extract Event Details (Events Only)

For posts classified as EVENT:

1. Use Claude's vision to analyze the flyer image
2. Extract: title, date, time, venue, price, ticket URL
3. If date is unclear from image, check caption
4. Score confidence (0-1) based on clarity

**Extraction prompt:**
```
Extract event details from this flyer:
- Event title
- Date (format: YYYY-MM-DD if possible)
- Time (format: HH:MM)
- Venue name
- Price/admission (or "Free" or "Unknown")
- Ticket URL (if visible)

Rate confidence for each field: high/medium/low
```

## Step 5: Create Event Objects

**Only for classified events with extractable details:**

```python
from schemas.event import Event, Venue, EventSource

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

## Step 6: Save Results

```python
from schemas.sqlite_storage import SqliteStorage
from schemas.event import EventCollection

db_path = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"
collection = EventCollection(events=events)
storage = SqliteStorage(db_path)
storage.save(collection)
```

## Step 7: Report Summary

Report:
- Total posts scraped per account
- Posts classified as events vs not-events
- Events successfully extracted
- Any posts needing review (low confidence)

Example:
```
@elmamm: 12 posts → 3 events, 9 skipped (6 food photos, 2 past recaps, 1 meme)
@cineplexcol: 12 posts → 8 events, 4 skipped (movie stills, not event announcements)
```
</process>

<success_criteria>
Instagram research complete when:
- [ ] All configured accounts scraped
- [ ] Each post classified as EVENT or NOT_EVENT
- [ ] Only actual events saved to database (not all posts!)
- [ ] Summary shows posts scraped vs events extracted
- [ ] Raw data saved to `~/.config/local-media-tools/data/raw/`
</success_criteria>
