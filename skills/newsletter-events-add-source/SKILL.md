---
name: newsletter-events-add-source
description: Add Instagram accounts or web aggregators to sources.yaml configuration
---

<essential_principles>
## Configuration Location

All sources are stored in `~/.config/local-media-tools/sources.yaml`.

## Source Types

| Type | Identifier | Example |
|------|------------|---------|
| Instagram | @handle or handle | @localvenue, elmamm |
| Web Aggregator | Any URL | https://localevents.com |

**Note:** Facebook events are not stored in configuration. Pass event URLs directly to `/research`.

## Schema Quick Reference

**Instagram Account:**
```yaml
- handle: "localvenue"      # Required (@ stripped automatically)
  name: "Local Venue"       # Auto-generated from handle if omitted
  type: "music_venue"       # music_venue, bar, restaurant, gallery, promoter, aggregator
  location: "Kingston, NY"  # Optional
  notes: "Live jazz"        # Optional
```

**Web Aggregator:**
```yaml
- url: "https://localevents.com"  # Required
  name: "Local Events"            # Auto-extracted from domain if omitted
  source_type: "listing"          # listing, calendar, or venue
  max_pages: 50                   # 1-200
```
</essential_principles>

<intake>
What sources do you want to add?

**Examples:**
- `@localvenue @musicbar @artgallery` - Add Instagram accounts
- `https://hudsonvalleyevents.com` - Add web aggregator
- `@venue1, @venue2 and https://events.com` - Mix of sources

**Note:** For Facebook events, use `/research https://facebook.com/events/123456` instead.

Provide the source(s):
</intake>

<process>
## Step 1: Parse Input

Analyze the user's input to extract sources:

**Instagram detection:**
- Starts with `@` → Instagram handle
- Word after "instagram" → Instagram handle
- Known Instagram handle format (alphanumeric + underscores) → Instagram handle

**Facebook detection:**
- Contains `facebook.com/events/` → Show message:
  "Facebook events are not stored in configuration. Pass the URL directly to /research instead:
   /research https://facebook.com/events/123456"
  Continue processing other sources.

**Web Aggregator detection:**
- Any other URL (http:// or https://) → Web aggregator

**Extract multiple sources:**
- Split on commas, "and", spaces, newlines
- Deduplicate

## Step 2: Load Current Config

```python
from pathlib import Path
import yaml

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"

if not config_path.exists():
    print("ERROR: sources.yaml not found. Run /newsletter-events:setup first.")
    # STOP HERE

with open(config_path) as f:
    config = yaml.safe_load(f)
```

## Step 3: Check for Duplicates

For each source, check if it already exists:

```python
# Instagram
existing_handles = {a["handle"].lower() for a in config["sources"]["instagram"]["accounts"]}

# Web
existing_web_urls = {s["url"].lower() for s in config["sources"]["web_aggregators"]["sources"]}
```

## Step 4: Build New Entries

For each new source that doesn't exist:

**Instagram:**
```python
new_account = {
    "handle": handle.lstrip("@").lower(),
    "name": handle.lstrip("@").replace("_", " ").title(),
    "type": "venue",  # Default
}
config["sources"]["instagram"]["accounts"].append(new_account)
```

**Web Aggregator:**
```python
from urllib.parse import urlparse
domain = urlparse(url).netloc.replace("www.", "")
new_source = {
    "url": url,
    "name": domain.split(".")[0].replace("-", " ").title(),
    "source_type": "listing",
    "max_pages": 50,
}
config["sources"]["web_aggregators"]["sources"].append(new_source)
```

## Step 5: Backup Original Config

```python
import shutil
from datetime import datetime

backup_path = config_path.with_suffix(f".yaml.{datetime.now():%Y%m%d%H%M%S}.backup")
shutil.copy2(config_path, backup_path)
```

## Step 6: Save Updated Config

```python
with open(config_path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

## Step 7: Validate

```python
from config.config_schema import AppConfig

try:
    AppConfig.from_yaml(config_path)
except Exception as e:
    # Restore backup
    shutil.copy2(backup_path, config_path)
    print(f"ERROR: Invalid config. Restored backup. Error: {e}")
    # STOP HERE
```

## Step 8: Report Results

Display a summary table:

| Type | Source | Name | Status |
|------|--------|------|--------|
| Instagram | @localvenue | Local Venue | Added |
| Instagram | @musicbar | Music Bar | Already exists |
| Web | hudsonvalleyevents.com | Hudson Valley Events | Added |

**Footer:**
```
Config saved to ~/.config/local-media-tools/sources.yaml
Backup at sources.yaml.20250120123456.backup

Run /newsletter-events:research to scrape these sources.
```
</process>

<success_criteria>
- [ ] All sources parsed from input
- [ ] Duplicates identified and skipped
- [ ] Config backed up before modification
- [ ] New sources appended to correct sections
- [ ] Config validates after save
- [ ] Clear summary table shown to user
</success_criteria>
