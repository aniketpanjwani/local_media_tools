---
name: newsletter-events-add-source
description: Add Instagram accounts, Facebook pages, or web aggregators to sources.yaml configuration
---

<essential_principles>
## Configuration Location

All sources are stored in `~/.config/local-media-tools/sources.yaml`.

## Source Types

| Type | Identifier | Example |
|------|------------|---------|
| Instagram | @handle or handle | @localvenue, elmamm |
| Facebook | URL with /events | https://facebook.com/venue/events |
| Web Aggregator | Any other URL | https://localevents.com |

## Schema Quick Reference

**Instagram Account:**
```yaml
- handle: "localvenue"      # Required (@ stripped automatically)
  name: "Local Venue"       # Auto-generated from handle if omitted
  type: "music_venue"       # music_venue, bar, restaurant, gallery, promoter, aggregator
  location: "Kingston, NY"  # Optional
  notes: "Live jazz"        # Optional
```

**Facebook Page:**
```yaml
- url: "https://facebook.com/venue/events"  # Required
  name: "The Venue"                          # Auto-extracted from URL if omitted
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
- `https://facebook.com/thevenue/events` - Add Facebook page
- `https://hudsonvalleyevents.com` - Add web aggregator
- `@venue1, @venue2 and https://events.com` - Mix of sources

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
- Contains `facebook.com` → Facebook page
- If URL doesn't end with `/events`, append it

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

# Facebook
existing_fb_urls = {p["url"].lower() for p in config["sources"]["facebook"]["pages"]}

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

**Facebook:**
```python
# Extract name from URL path
path = url.split("facebook.com/")[1].split("/")[0]
new_page = {
    "url": url if url.endswith("/events") else f"{url.rstrip('/')}/events",
    "name": path.replace("_", " ").replace("-", " ").title(),
}
config["sources"]["facebook"]["pages"].append(new_page)
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
| Facebook | facebook.com/thevenue/events | The Venue | Added |

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
