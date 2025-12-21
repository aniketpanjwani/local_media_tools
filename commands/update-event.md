---
name: newsletter-events:update-event
description: Refresh specific event pages to update event data
---

# Update Event

Re-scrape specific event page URLs to refresh event data in the database.

## When to Use

- Event details have changed (date, time, venue)
- You want to verify event data is current
- Events weren't extracted correctly on first scrape

## Usage

```
/newsletter-events:update-event <url> [<url2> ...]
```

**Examples:**
```
/newsletter-events:update-event https://hvmag.com/events/jazz-night
/newsletter-events:update-event https://example.com/event/1 https://example.com/event/2
```

## Instructions

1. Get plugin directory: `cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'`
2. Read skill: `$PLUGIN_DIR/skills/newsletter-events-update-event/SKILL.md`
3. Follow the workflow to:
   - Parse and normalize URLs
   - Re-scrape pages via Firecrawl
   - Extract events from markdown
   - Update database (events FIRST, then scraped_pages)

## Expected Output

- Events updated in SQLite database
- scraped_pages timestamp updated
- Summary of events updated vs created
