# Research Facebook Events (Discover by Location)

Discover events in a geographic area using Chrome MCP to scrape Facebook's events page.

## Prerequisites

1. **Chrome browser** must be open and **logged into Facebook**
2. **Chrome MCP Server** must be running
3. **config/sources.yaml** must have at least one location configured under `facebook.locations`

## Workflow

### Step 1: Load and Validate Configuration

```python
from config.config_schema import AppConfig

config = AppConfig.from_yaml("config/sources.yaml")

if not config.sources.facebook.locations:
    print("No Facebook locations configured. See references/facebook-location-setup.md")
    # STOP HERE
```

If no locations configured, inform user and stop.

### Step 2: For Each Configured Location

Loop through `config.sources.facebook.locations`:

#### 2a. Build the Discover URL

```python
from scripts.facebook_discover import build_discover_url

url = build_discover_url(
    location_id=location.location_id,
    date_filter=location.date_filter,
)
print(f"Scraping events for {location.location_name}: {url}")
```

#### 2b. Navigate to Facebook Events

Use Chrome MCP:
```
chrome_navigate(url: "<url>")
```

Wait 3 seconds for page to load.

#### 2c. Check Authentication Status

```
chrome_get_web_content(textContent: true)
```

```python
from scripts.facebook_discover import is_logged_in

if not is_logged_in(page_content):
    print("Facebook requires authentication.")
    print("Please log into Facebook in Chrome, then run this skill again.")
    # STOP HERE
```

#### 2d. Scroll to Load More Events

Repeat `location.scroll_count` times (default: 3):

```
chrome_keyboard(keys: "PageDown")
```

Wait `location.scroll_delay_seconds` (default: 5.0) between scrolls.

#### 2e. Extract Event Links

```
chrome_get_interactive_elements(selector: "a[href*='/events/']")
```

This returns a list of elements with:
- `href`: Event URL
- `text`: Event card content (date, title, venue)

#### 2f. Parse Events

```python
from scripts.facebook_discover import parse_event_card

events = []
for element in event_elements:
    event = parse_event_card(
        text=element.get("text", ""),
        url=element.get("href", ""),
        location_name=location.location_name,
    )
    if event:
        events.append(event)

print(f"Found {len(events)} events for {location.location_name}")
```

### Step 3: Save Results

Save to `tmp/extraction/facebook_discover_{timestamp}.json`:

```python
import json
from datetime import datetime

output = {
    "source": "facebook_discover",
    "scraped_at": datetime.now().isoformat(),
    "locations": [
        {
            "location_id": location.location_id,
            "location_name": location.location_name,
            "date_filter": location.date_filter,
            "event_count": len(events),
            "events": [event.model_dump() for event in events],
        }
        for location, events in all_results
    ],
}

with open(f"tmp/extraction/facebook_discover_{datetime.now():%Y%m%d_%H%M%S}.json", "w") as f:
    json.dump(output, f, indent=2, default=str)
```

### Step 4: Summary

Print summary:
- Total events discovered across all locations
- Breakdown by location
- Any warnings or issues encountered

## Error Handling

| Error | Detection | Action |
|-------|-----------|--------|
| Not logged in | `is_logged_in()` returns False | Stop with clear instructions |
| Rate limited | Page shows error or no events after successful login | Wait 60s, retry once, then stop |
| No events found | Empty event list for a location | Log warning, continue to next location |
| Navigation timeout | Chrome MCP tool fails | Retry once, then skip location |
| Parse failures | `parse_event_card()` returns None | Log warning, continue (partial results OK) |

## Validation Step (Optional)

Before full scraping, validate a single location:

1. Navigate to the discover URL
2. Check login status
3. Verify events are visible
4. Report success/failure

This helps catch configuration issues before a full run.
