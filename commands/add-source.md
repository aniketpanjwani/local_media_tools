---
name: newsletter-events:add-source
description: Add Instagram accounts, Facebook pages, or web aggregators to sources.yaml
---

# Add Event Sources

Quickly add new event sources to your configuration without editing YAML manually.

## Configuration Location

Sources are stored in `~/.config/local-media-tools/sources.yaml`.

## Usage Examples

```bash
# Add Instagram accounts
/newsletter-events:add-source @localvenue @musicbar

# Add Facebook page
/newsletter-events:add-source https://facebook.com/thevenue/events

# Add web aggregator
/newsletter-events:add-source https://hudsonvalleyevents.com

# Mix of sources
/newsletter-events:add-source @venue1 @venue2 https://facebook.com/bar/events https://events.com
```

## Source Types

| Input Pattern | Detected As | Example |
|--------------|-------------|---------|
| `@handle` | Instagram | @localvenue |
| `handle` (after "instagram") | Instagram | "add instagram localvenue" |
| `facebook.com/*/events` | Facebook Page | https://facebook.com/venue/events |
| Other URLs | Web Aggregator | https://localevents.com |

## Workflow

### Step 1: Parse Sources

The skill parses your input to detect source types:

- **Instagram:** `@` prefix or alphanumeric handles
- **Facebook:** URLs containing `facebook.com`
- **Web:** Any other HTTP/HTTPS URL

### Step 2: Check Duplicates

Each source is checked against existing entries. Duplicates are skipped with a warning.

### Step 3: Generate Defaults

For each new source, reasonable defaults are generated:

| Field | Auto-Generated Value |
|-------|---------------------|
| `name` | Extracted from handle/URL (e.g., "local_venue" → "Local Venue") |
| `type` | "venue" for Instagram |
| `source_type` | "listing" for web aggregators |
| `max_pages` | 50 for web aggregators |

### Step 4: Backup & Save

1. Current config backed up to `sources.yaml.YYYYMMDDHHMMSS.backup`
2. New sources appended to appropriate sections
3. Config validated with Pydantic schema
4. If validation fails, backup is restored

### Step 5: Report

A summary table shows what was added:

```
| Type      | Source                          | Name        | Status        |
|-----------|--------------------------------|-------------|---------------|
| Instagram | @localvenue                    | Local Venue | Added         |
| Instagram | @musicbar                      | Music Bar   | Already exists|
| Facebook  | facebook.com/thevenue/events   | The Venue   | Added         |

Config saved. Backup at sources.yaml.20250120123456.backup
```

## Error Handling

| Error | Response |
|-------|----------|
| sources.yaml missing | "Run /newsletter-events:setup first" |
| Invalid YAML after save | Restore backup, show error |
| No sources detected in input | "No valid sources found. Use @handle for Instagram, URLs for Facebook/web" |

## Notes

- Instagram handles have `@` stripped automatically
- Facebook URLs without `/events` get it appended
- Web aggregator URLs are normalized (trailing slash handling)
- All changes create a timestamped backup
