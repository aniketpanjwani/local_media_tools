---
name: newsletter-events:add-source
description: Add Instagram accounts or web aggregators to sources.yaml (web sources require profiling)
---

# Add Event Sources

Add new event sources to your configuration. Web aggregators require profiling to discover optimal scraping strategy.

## Source Types & Workflows

| Input | Type | Workflow |
|-------|------|----------|
| `@handle` | Instagram | Simple add (no profiling) |
| `http://` or `https://` URL | Web Aggregator | **Requires profiling with Firecrawl** |
| `facebook.com/events/*` | Facebook | Not stored - use `/research` directly |

## Usage

```bash
# Instagram accounts (simple)
/newsletter-events:add-source @localvenue @musicbar

# Web aggregator (will be profiled)
/newsletter-events:add-source https://hudsonvalleyevents.com

# Mix of sources
/newsletter-events:add-source @venue1 https://events.com
```

---

## Step 1: Parse and Classify Input

```python
import re

sources = {"instagram": [], "web": [], "facebook": []}

for token in user_input.replace(",", " ").replace(" and ", " ").split():
    token = token.strip()
    if not token:
        continue

    if "facebook.com/events/" in token:
        sources["facebook"].append(token)
    elif token.startswith("@") or re.match(r"^[a-zA-Z][a-zA-Z0-9_.]+$", token):
        sources["instagram"].append(token.lstrip("@").lower())
    elif token.startswith("http://") or token.startswith("https://"):
        sources["web"].append(token)
```

For Facebook URLs, inform user:
```
Facebook events are not stored in configuration.
Use: /research https://facebook.com/events/123456
```

---

## Step 2: Load Config

```python
from pathlib import Path
import yaml

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"

if not config_path.exists():
    print("ERROR: sources.yaml not found. Run /newsletter-events:setup first.")
    # STOP

with open(config_path) as f:
    config = yaml.safe_load(f)
```

---

## Step 3: Process Instagram Sources (Simple)

For each Instagram handle:

1. Check if already exists:
   ```python
   existing = {a["handle"].lower() for a in config["sources"]["instagram"]["accounts"]}
   ```

2. If new, add with defaults:
   ```python
   new_account = {
       "handle": handle,
       "name": handle.replace("_", " ").title(),
       "type": "venue",
   }
   config["sources"]["instagram"]["accounts"].append(new_account)
   ```

---

## Step 4: Process Web Sources (REQUIRES PROFILING)

<critical>
FOR EACH WEB URL, YOU MUST COMPLETE PROFILING BEFORE SAVING.
DO NOT skip profiling. DO NOT save without a profile.
</critical>

### 4a: Check for Duplicate

```python
existing_urls = {s["url"].lower() for s in config["sources"]["web_aggregators"]["sources"]}
if url.lower() in existing_urls:
    # Skip - already exists
    continue
```

### 4b: Build Base Entry

```python
from urllib.parse import urlparse

domain = urlparse(url).netloc.replace("www.", "")
name = domain.split(".")[0].replace("-", " ").title()

new_source = {
    "url": url,
    "name": name,
    "source_type": "listing",
    "max_pages": 50,
}
```

### 4c: Profile with Firecrawl (MANDATORY)

<critical>
RUN THE PROFILER CLI FROM THE PLUGIN DIRECTORY.

The plugin includes a CLI tool for profiling. Run it using:

```bash
cd $CLAUDE_PLUGIN_ROOT && uv run python scripts/profile_source.py "{url}"
```

This returns JSON with discovery_method, event_urls, and suggested regex pattern.
DO NOT try to import Python modules directly - use the CLI tool.
</critical>

**Run the profiler:**
```bash
cd $CLAUDE_PLUGIN_ROOT && uv run python scripts/profile_source.py "{url}"
```

The profiler will:
1. Try `map_url()` first (fast sitemap/link discovery)
2. Fall back to `crawl_url()` if map finds < 5 event URLs
3. Filter URLs matching `/events?/`, `/calendar/`, `/shows?/`, etc.
4. Suggest a regex pattern based on discovered URLs
5. Output JSON with the profile data

### 4d: Learn URL Pattern

Analyze discovered URLs to generate regex pattern:
```python
# Examples:
# /events/jazz-night         → r"/events/[^/]+$"
# /event/a-frosty-fest/76214 → r"/event/[^/]+/\d+/?$"
```

### 4e: Show Profile & Confirm

```
📊 Source Profile: {name}
   URL: {url}

   Discovery: {discovery_method}
   Found: {len(event_urls)} event URLs
   Pattern: {learned_regex}

   Samples:
     • {event_urls[0]}
     • {event_urls[1]}
     • {event_urls[2]}

Save this profile? (Y/n)
```

**Wait for user confirmation.**

### 4f: Store with Profile

```python
from datetime import datetime

new_source["profile"] = {
    "discovery_method": discovery_method,
    "crawl_depth": 2,
    "event_url_regex": learned_regex,
    "sample_event_urls": event_urls[:5],
    "notes": f"Discovered {len(event_urls)} event URLs.",
    "profiled_at": datetime.now().isoformat(),
}

config["sources"]["web_aggregators"]["enabled"] = True
config["sources"]["web_aggregators"]["sources"].append(new_source)
```

### 4g: Handle Profiling Failures

If both map and crawl find 0 event URLs:
```
⚠️ Could not discover event URLs.

Options:
1. Add anyway (manually configure later)
2. Skip this source
3. Provide custom event_url_pattern

Choose (1-3):
```

---

## Step 5: Backup & Save

```python
import shutil
from datetime import datetime

backup_path = config_path.with_suffix(f".yaml.{datetime.now():%Y%m%d%H%M%S}.backup")
shutil.copy2(config_path, backup_path)

with open(config_path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

---

## Step 6: Validate

```python
from config.config_schema import AppConfig

try:
    AppConfig.from_yaml(config_path)
except Exception as e:
    shutil.copy2(backup_path, config_path)
    print(f"ERROR: Invalid config. Restored backup. Error: {e}")
    # STOP
```

---

## Step 7: Report Results

| Type | Source | Name | Status |
|------|--------|------|--------|
| Instagram | @localvenue | Local Venue | Added |
| Web | greatnortherncatskills.com | Great Northern Catskills | Added (profiled: map) |

```
Config saved to ~/.config/local-media-tools/sources.yaml
Backup at sources.yaml.YYYYMMDDHHMMSS.backup

Run /newsletter-events:research to scrape these sources.
```
