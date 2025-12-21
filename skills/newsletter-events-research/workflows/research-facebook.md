# Workflow: Research Facebook Events

Scrape individual Facebook event URLs provided by the user.

<required_reading>
Read before proceeding:
- `references/facebook-scraper-api.md`
</required_reading>

<process>
## Step 1: Extract Facebook Event URLs

Parse the user's input for Facebook event URLs:

```python
import re

# Extract all Facebook event URLs from user input
pattern = r'https?://(?:www\.)?(?:facebook\.com|fb\.com)/events/\d+'
urls = [match.group(0) for match in re.finditer(pattern, user_input, re.IGNORECASE)]

if not urls:
    print("No Facebook event URLs found in your input.")
    print("Please provide URLs like: https://facebook.com/events/123456")
    # STOP HERE
```

## Step 2: Scrape Each Event

```python
from scripts.facebook_bridge import FacebookBridge, FacebookScraperError

bridge = FacebookBridge(timeout=120)
all_events = []
failed_urls = []

for url in urls:
    try:
        event_data = bridge.scrape_single_event(url)
        all_events.append(event_data)
        print(f"Scraped: {event_data.get('title')}")
    except FacebookScraperError as e:
        failed_urls.append((url, str(e)))
        print(f"Failed: {url} - {e}")
        continue
```

## Step 3: Normalize and Save Events

```python
from schemas.event import Event, Venue, EventSource
from schemas.sqlite_storage import SqliteStorage
from pathlib import Path
from datetime import datetime

def parse_date(date_str):
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def parse_time(time_str):
    if not time_str:
        return None
    return datetime.strptime(time_str, "%H:%M").time()

events = []
for fb_event in all_events:
    venue = Venue(
        name=fb_event.get("venue", {}).get("name", "TBD"),
        city=fb_event.get("venue", {}).get("city"),
    )
    event = Event(
        title=fb_event["title"],
        venue=venue,
        event_date=parse_date(fb_event.get("event_date")),
        start_time=parse_time(fb_event.get("start_time")),
        source=EventSource.FACEBOOK,
        source_url=fb_event.get("source_url"),
        description=fb_event.get("description"),
        image_url=fb_event.get("image_url"),
    )
    events.append(event)

# Save to database
db_path = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"
storage = SqliteStorage(db_path)
storage.save_events(events)
```

## Step 4: Report Summary

```
Scraped {len(all_events)} Facebook events.

{if failed_urls}
Failed to scrape:
{for url, error in failed_urls}
  - {url}: {error}
{endfor}
{endif}
```
</process>

<success_criteria>
- [ ] All provided URLs attempted
- [ ] Successful events saved to database
- [ ] Failed URLs reported with clear errors
</success_criteria>
