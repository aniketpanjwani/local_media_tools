---
name: newsletter-events:write
description: Generate a markdown newsletter from stored events
---

# Write Newsletter

Generate a markdown newsletter from stored events.

## Configuration Location

- Configuration: `~/.config/local-media-tools/sources.yaml`
- Events database: `~/.config/local-media-tools/data/events.db`
- Output: Current working directory (e.g., `./newsletter_YYYY-MM-DD.md`)

## Instructions

1. Load the configuration from `~/.config/local-media-tools/sources.yaml`
   - Get `newsletter.name` and `newsletter.region`
   - Get `newsletter.formatting_preferences` for formatting instructions

2. Query events from SQLite database at `~/.config/local-media-tools/data/events.db`
   - Default: next 7 days from today
   - Use `SqliteStorage.query(date_from, date_to)` method

3. Generate markdown following the user's formatting preferences
   - Read `formatting_preferences` as plain English instructions
   - Apply those instructions to format the newsletter
   - Include event data: title, venue, date, time, price, description, links

4. Save output to current working directory: `./newsletter_YYYY-MM-DD.md`

5. Display preview (first ~50 lines) in terminal

## Usage

```
/newsletter-events:write                      # Generate with defaults (next 7 days)
/newsletter-events:write --days 14            # Next 14 days
/newsletter-events:write --from 2025-01-20    # Custom start date
```

## Prerequisites

- Events must be in database (run `/newsletter-events:research` first)
- `~/.config/local-media-tools/sources.yaml` should have `formatting_preferences` set

## Expected Output

- File: `./newsletter_YYYY-MM-DD.md` (in current working directory)
- Preview shown in terminal
- Summary: event count, date range, output path
