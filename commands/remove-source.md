---
name: newsletter-events:remove-source
description: Remove Instagram accounts, Facebook pages, or web aggregators from sources.yaml
---

# Remove Event Sources

Remove existing event sources from your configuration without editing YAML manually.

## Configuration Location

Sources are stored in `~/.config/local-media-tools/sources.yaml`.

## Usage Examples

```bash
# Remove Instagram account
/newsletter-events:remove-source @localvenue

# Remove multiple Instagram accounts
/newsletter-events:remove-source @venue1 @venue2 @venue3

# Remove Facebook page
/newsletter-events:remove-source https://facebook.com/thevenue/events

# Remove web aggregator
/newsletter-events:remove-source https://oldsite.com

# Remove by name
/newsletter-events:remove-source "Local Venue"

# Mix of sources
/newsletter-events:remove-source @oldvenue https://facebook.com/closedbar/events
```

## Identifier Matching

| Input Pattern | Matches |
|---------------|---------|
| `@handle` | Instagram account by handle |
| `handle` | Instagram account by handle |
| `facebook.com/*/events` | Facebook page by URL |
| HTTP/HTTPS URL | Web aggregator by URL |
| `"Name"` | Any source by name |

### Match Priority

1. Exact Instagram handle (case-insensitive)
2. Exact Facebook URL (normalized)
3. Exact Web URL (normalized)
4. Exact name match (any type)

## Workflow

### Step 1: Parse Identifiers

The skill parses your input to detect what to remove:

- **Instagram:** `@` prefix or alphanumeric handles
- **Facebook:** URLs containing `facebook.com`
- **Web:** Any other HTTP/HTTPS URL
- **Name:** Quoted strings search by name

### Step 2: Find Matches

Each identifier is matched against existing sources.

If **no match found**:
```
Source not found: @unknownhandle
```

If **ambiguous match** (name matches multiple types):
```
Multiple sources match 'venue':
1. @venue (Instagram) - Local Venue
2. facebook.com/venue/events (Facebook) - The Venue

Which one(s) to remove? (Enter numbers or 'all'):
```

### Step 3: Confirm Large Batches

If removing 4+ sources, confirmation is requested:

```
About to remove 5 sources. Continue? (y/n)
```

### Step 4: Backup & Remove

1. Current config backed up to `sources.yaml.YYYYMMDDHHMMSS.backup`
2. Sources removed from appropriate sections
3. Orphaned references cleaned up (e.g., `priority_handles`)
4. Config validated with Pydantic schema
5. If validation fails, backup is restored

### Step 5: Report

A summary shows what was removed:

```
Removing sources...

✓ Removed @localvenue (Local Venue) from Instagram accounts
✓ Removed @oldbar (Old Bar) from Instagram accounts
  Also removed from priority_handles
✗ Not found: @unknownhandle

Summary: 2 removed, 1 not found

Config backup: sources.yaml.20250120143022.backup
To undo: cp ~/.config/local-media-tools/sources.yaml.20250120143022.backup ~/.config/local-media-tools/sources.yaml

Remaining sources: 4 (run /list-sources to view)
```

## Safety Features

| Feature | Description |
|---------|-------------|
| Automatic backup | Config saved before any changes |
| Validation | Config validated after removal |
| Auto-rollback | Backup restored if validation fails |
| Orphan cleanup | Related references (priority_handles) cleaned up |

## Error Handling

| Error | Response |
|-------|----------|
| sources.yaml missing | "Run /newsletter-events:setup first" |
| No sources configured | "No sources configured. Nothing to remove." |
| Source not found | "Source not found: @handle" |
| Invalid YAML after removal | Restore backup, show error |

## Undo

If you remove the wrong source, restore from backup:

```bash
cp ~/.config/local-media-tools/sources.yaml.TIMESTAMP.backup ~/.config/local-media-tools/sources.yaml
```

## Related Commands

| Command | Description |
|---------|-------------|
| `/newsletter-events:list-sources` | View all configured sources |
| `/newsletter-events:add-source` | Add new sources |
| `/newsletter-events:research` | Scrape configured sources |
