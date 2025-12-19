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

**For EACH post, determine: Does this announce any upcoming events?**

Analyze the post caption AND image. Ask yourself:

1. **Does it announce FUTURE event(s)?** (not a recap of past events)
2. **Does it have event details?** (date, time, performer, ticket info)
3. **How many distinct events are announced?** (could be 0, 1, or multiple)

**Classification prompt for each post:**
```
Look at this Instagram post (caption + image).

Does this announce upcoming event(s)?

ANSWER ONE OF:
- "NO_EVENTS" - Not an event announcement (food photo, past recap, etc.)
- "ONE_EVENT" - Announces exactly one upcoming event
- "MULTIPLE_EVENTS" - Announces 2+ distinct events (e.g., weekly schedule, series)

If ONE_EVENT: note title, date, venue
If MULTIPLE_EVENTS: list each event briefly (title + date for each)
If NO_EVENTS: note why (e.g., "food photo", "past event recap")
```

**Only proceed to Step 4 for posts with events.**

## Step 4: Extract Event Details

For each event in the post (may be 1 or multiple):

**For ONE_EVENT posts:**
1. Use Claude's vision to analyze the flyer image
2. Extract: title, date, time, venue, price, ticket URL
3. Create ONE Event object

**For MULTIPLE_EVENTS posts:**
1. Identify each distinct event in the post
2. For EACH event, extract: title, date, time, venue, price
3. Create SEPARATE Event objects for each
4. All events share the same source_url (the post URL)

**Extraction prompt:**
```
Extract ALL events from this post.

For EACH event, provide:
- Event title
- Date (format: YYYY-MM-DD)
- Time (format: HH:MM)
- Venue name
- Price/admission (or "Free" or "Unknown")

If this is a multi-event post (e.g., weekly schedule), list each event separately.
Example output for weekly schedule:
1. Jazz Night | 2025-01-20 | 20:00 | MAMM | Free
2. Open Mic | 2025-01-22 | 19:00 | MAMM | Free
3. Live Band | 2025-01-24 | 21:00 | MAMM | $10
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
- Posts with events vs posts skipped
- Total events extracted (may be > posts with events if multi-event posts)
- Any events needing review (low confidence)

Example:
```
@elmamm: 12 posts scraped
  - 2 posts with single events → 2 events
  - 1 post with weekly schedule → 5 events
  - 9 posts skipped (6 food photos, 2 past recaps, 1 meme)
  - Total: 7 events extracted

@cineplexcol: 12 posts scraped
  - 4 posts with single events → 4 events
  - 8 posts skipped (movie stills, not event announcements)
  - Total: 4 events extracted
```
</process>

<success_criteria>
Instagram research complete when:
- [ ] All configured accounts scraped
- [ ] Each post classified as NO_EVENTS, ONE_EVENT, or MULTIPLE_EVENTS
- [ ] All events from multi-event posts extracted separately
- [ ] Only actual events saved to database (not all posts!)
- [ ] Summary shows posts scraped → events extracted breakdown
- [ ] Raw data saved to `~/.config/local-media-tools/data/raw/`
</success_criteria>
