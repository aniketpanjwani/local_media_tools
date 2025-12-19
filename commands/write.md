# Write Newsletter

Generate a markdown newsletter from stored events.

## Instructions

1. Load the configuration from `config/sources.yaml`
   - Get `newsletter.name` and `newsletter.region`
   - Get `newsletter.formatting_preferences` for formatting instructions
   - Get `storage.path` for database location

2. Query events from SQLite database
   - Default: next 7 days from today
   - Use `SqliteStorage.query(date_from, date_to)` method

3. Generate markdown following the user's formatting preferences
   - Read `formatting_preferences` as plain English instructions
   - Apply those instructions to format the newsletter
   - Include event data: title, venue, date, time, price, description, links

4. Save output to `tmp/output/newsletter_YYYY-MM-DD.md`

5. Display preview (first ~50 lines) in terminal

## Usage

```
/write                      # Generate with defaults (next 7 days)
/write --days 14            # Next 14 days
/write --from 2025-01-20    # Custom start date
```

## Prerequisites

- Events must be in database (run `/research` first)
- `config/sources.yaml` should have `formatting_preferences` set

## Expected Output

- File: `tmp/output/newsletter_YYYY-MM-DD.md`
- Preview shown in terminal
- Summary: event count, date range, output path
