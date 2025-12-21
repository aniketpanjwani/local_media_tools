---
name: newsletter-events-write
description: Generate markdown newsletters from stored events. Use when the user wants to create, write, or generate a newsletter from scraped events.
---

<essential_principles>
## How This Skill Works

This skill generates markdown newsletters from events stored in SQLite. The user's **natural language formatting preferences** are read from the config file and applied during generation.

### Key Concept: Natural Language Formatting

Users describe how they want newsletters formatted in plain English. You interpret these instructions directly - no templates or structured syntax needed.

Example preference from config:
```yaml
formatting_preferences: |
  Organize by date with each day as a section header.
  Use emojis: 🎵 music, 🎨 art, 🍴 food.
  Format: **Title** @ Venue | Time | Price
```

### Data Source

Events are stored in SQLite at `tmp/extraction/events.db` (or path from config).

### Output

Generated markdown saved to `tmp/output/newsletter_YYYY-MM-DD.md`.
</essential_principles>

<workflow>
## Step 1: Load Configuration

Read `config/sources.yaml` to get:
- `newsletter.name` - Newsletter title
- `newsletter.region` - Geographic region
- `newsletter.formatting_preferences` - User's formatting instructions

```python
from config import AppConfig

config = AppConfig.from_yaml("config/sources.yaml")
name = config.newsletter.name
region = config.newsletter.region
formatting_prefs = config.newsletter.formatting_preferences
```

## Step 2: Query Events from SQLite

```python
from datetime import date, timedelta
from schemas.sqlite_storage import SqliteStorage

storage = SqliteStorage(config.storage.path)

# Default: next 7 days
start_date = date.today()
end_date = start_date + timedelta(days=7)

events = storage.query(date_from=start_date, date_to=end_date)
```

If no events found, report this to user with helpful suggestions:
- Run `/research` to scrape new events
- Adjust date range
- Check that sources are configured

## Step 3: Prepare Event Data

For each event, extract the relevant fields:

```python
events_data = []
for event in events:
    events_data.append({
        "title": event.title,
        "venue": event.venue.name,
        "venue_city": event.venue.city,
        "date": event.event_date.strftime("%Y-%m-%d"),
        "day_of_week": event.event_date.strftime("%A"),
        "formatted_date": event.event_date.strftime("%B %d"),
        "time": event.start_time.strftime("%-I:%M %p") if event.start_time else None,
        "description": event.description or event.short_description,
        "category": event.category.value if event.category else "other",
        "price": event.price or ("Free" if event.is_free else None),
        "ticket_url": event.ticket_url,
        "event_url": event.event_url,
        "source_url": event.source_url,
    })
```

### Available Fields Reference

When generating the newsletter, these fields are available for each event:

| Field | Description | Example |
|-------|-------------|---------|
| `title` | Event name | "Jazz Night" |
| `venue` | Venue name | "The Blue Note" |
| `venue_city` | Venue city | "Kingston" |
| `date` | ISO date | "2025-01-20" |
| `day_of_week` | Full day name | "Saturday" |
| `formatted_date` | Human-readable date | "January 20" |
| `time` | Start time | "8:00 PM" |
| `description` | Event description | "Live jazz trio..." |
| `category` | Event category | "music", "art", "food_drink" |
| `price` | Price or "Free" | "$15" or "Free" |
| `ticket_url` | Link to buy tickets | URL or null |
| `event_url` | Link to event page | URL or null |
| `source_url` | Where event was found | Instagram post, Facebook event, or web page URL |

**Note:** `source_url` is the original source where the event was discovered:
- Instagram events → the Instagram post URL
- Facebook events → the Facebook event page URL
- Web aggregator events → the scraped page URL

Users can request source attribution in their `formatting_preferences`, e.g.:
```yaml
formatting_preferences: |
  Include [Source](source_url) link for each event.
```

## Step 4: Generate Markdown

Apply the user's formatting preferences to generate the newsletter.

**Your task:** Read the `formatting_preferences` string and generate markdown that follows those instructions exactly.

Include:
- Newsletter header with name and date range
- Events organized per user's preference (by date, by category, etc.)
- Formatting per user's preference (emojis, separators, structure)
- Only include fields that are available (skip nulls gracefully)

## Step 5: Save Output

```python
from pathlib import Path
from datetime import date

output_dir = Path("tmp/output")
output_dir.mkdir(parents=True, exist_ok=True)

filename = f"newsletter_{date.today().isoformat()}.md"
output_path = output_dir / filename

output_path.write_text(markdown_content)
```

## Step 6: Display Preview

Show the first ~50 lines of generated markdown in terminal so user can review.

Report:
- Output file path
- Number of events included
- Date range covered
</workflow>

<error_handling>
### No Events Found

```
No events found for {start_date} to {end_date}.

Suggestions:
- Run /research to scrape new events
- Check your date range (default: next 7 days)
- Verify sources are configured in config/sources.yaml
```

### No Formatting Preferences

Use sensible defaults:
```
Organize events chronologically by date.
Use section headers for each day (e.g., "## Saturday, January 20").
Include event title, venue, time, and price.
Keep formatting simple and readable.
```

### Database Not Found

```
Events database not found at {path}.
Run /research first to scrape events.
```
</error_handling>

<success_criteria>
Newsletter generation is complete when:
- [ ] Config loaded (name, region, preferences)
- [ ] Events queried from SQLite
- [ ] Markdown generated following user's preferences
- [ ] Output saved to `tmp/output/newsletter_YYYY-MM-DD.md`
- [ ] Preview displayed to user
</success_criteria>
