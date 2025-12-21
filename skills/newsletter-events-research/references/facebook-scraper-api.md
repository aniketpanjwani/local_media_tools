# Facebook Event Scraper API Reference

## Overview

We use the `facebook-event-scraper` npm package via a Python subprocess bridge. This allows us to scrape public Facebook events without needing the Facebook API.

GitHub: https://github.com/francescov1/facebook-event-scraper

## Architecture

```
Python code
    ↓
facebook_bridge.py
    ↓ (subprocess with JSON stdin/stdout)
scrape_facebook.js
    ↓
facebook-event-scraper npm
    ↓
Facebook.com
```

## Python Usage

```python
from scripts.facebook_bridge import FacebookBridge, FacebookScraperError

bridge = FacebookBridge(timeout=120)

# Scrape a single event by URL
event = bridge.scrape_single_event("https://facebook.com/events/123456")
```

## Response Structure

Events are normalized to match our Event schema:

```json
{
  "title": "Jazz Night",
  "description": "Weekly jazz with...",
  "event_date": "2025-01-15",
  "start_time": "19:00",
  "end_time": "22:00",
  "venue": {
    "name": "Colony Woodstock",
    "address": "123 Main St",
    "city": "Woodstock",
    "coordinates": [42.0, -74.0]
  },
  "ticket_url": "https://...",
  "image_url": "https://...",
  "source": "facebook",
  "source_url": "https://facebook.com/events/...",
  "source_id": "123456789"
}
```

## Error Handling

```python
try:
    event = bridge.scrape_single_event(url)
except FacebookScraperError as e:
    if "timeout" in str(e).lower():
        # Page took too long to load
    elif "not found" in str(e).lower():
        # Event doesn't exist or is private
    else:
        # Other error
```

## Limitations

- Only works for public events
- May be rate limited by Facebook
- Some events may have incomplete data
- Requires bun to be installed
