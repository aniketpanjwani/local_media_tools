# Write Newsletter

Generate a formatted newsletter from collected event data.

## Prerequisites

Run `/research` first to collect events.

## Instructions

1. Load events from `tmp/extraction/events.json`
2. Filter to events in the next 7 days
3. Generate newsletter using `newsletter-events-write` skill
4. Save to `output/newsletter_YYYY-MM-DD.md`
5. Report summary

## Arguments

- `$ARGUMENTS` - Optional: Custom title for the newsletter

## Example Usage

```
/write
/write Hudson Valley Weekend Guide
```

## Expected Output

- Newsletter saved to `output/` directory
- Summary showing:
  - Total events included
  - Events by day
  - Flagged items for review
