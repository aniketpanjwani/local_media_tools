# Workflow: Research All Sources

<required_reading>
Read before proceeding:
- `references/scrapecreators-api.md`
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
```

## Step 2: Run Instagram Research

If Instagram is enabled:

```python
if config.sources.instagram.enabled:
    # Follow research-instagram.md workflow
    # Collect all Instagram events
```

## Step 3: Run Web Aggregator Research

If web aggregators are enabled:

```python
if config.sources.web_aggregators.enabled and config.sources.web_aggregators.sources:
    # Follow research-web-aggregator.md workflow
    # Collect all web aggregator events
```

Note: Facebook events are not configured sources. To scrape Facebook events,
pass URLs directly to the research skill (e.g., `https://facebook.com/events/123456`).

## Step 4: Combine and Deduplicate

```python
from scripts.deduplicate import deduplicate_events

all_events = instagram_events + web_aggregator_events
deduplicated = deduplicate_events(all_events, threshold=0.75)
```

## Step 5: Save Combined Results

```python
from schemas.storage import EventStorage
from schemas.event import EventCollection
from datetime import date, timedelta

# Calculate week range
today = date.today()
week_start = today
week_end = today + timedelta(days=7)

collection = EventCollection(
    events=deduplicated,
    week_start=week_start,
    week_end=week_end,
)

from schemas.sqlite_storage import SqliteStorage

db_path = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"
storage = SqliteStorage(db_path)
storage.save(collection)
```

## Step 6: Report Summary

Print summary of research:
- Total events found per source
- Events after deduplication
- Events flagged for review
- Any errors encountered
</process>

<success_criteria>
Full research complete when:
- [ ] Instagram research complete (if enabled)
- [ ] Web aggregator research complete (if enabled)
- [ ] Events deduplicated across sources
- [ ] Combined events saved to `~/.config/local-media-tools/data/events.db`
- [ ] Summary reported to user
</success_criteria>
