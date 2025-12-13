# Workflow: Research All Sources

<required_reading>
Read before proceeding:
- `references/scrapecreators-api.md`
- `references/facebook-scraper-api.md`
- `references/event-detection.md`
</required_reading>

<process>
## Step 1: Load Configuration

```python
from config.config_schema import AppConfig

config = AppConfig.from_yaml("config/sources.yaml")
```

## Step 2: Run Instagram Research

If Instagram is enabled:

```python
if config.sources.instagram.enabled:
    # Follow research-instagram.md workflow
    # Collect all Instagram events
```

## Step 3: Run Facebook Research

If Facebook is enabled:

```python
if config.sources.facebook.enabled:
    # Follow research-facebook.md workflow
    # Collect all Facebook events
```

## Step 4: Combine and Deduplicate

```python
from scripts.deduplicate import deduplicate_events

all_events = instagram_events + facebook_events
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

storage = EventStorage("tmp/extraction/events.json")
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
- [ ] Facebook research complete (if enabled)
- [ ] Events deduplicated across sources
- [ ] Combined events saved to `tmp/extraction/events.json`
- [ ] Summary reported to user
</success_criteria>
