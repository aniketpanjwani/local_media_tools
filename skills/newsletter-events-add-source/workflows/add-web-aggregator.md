# Workflow: Add Web Aggregator

<stop>
YOU MUST FOLLOW THIS WORKFLOW EXACTLY.

DO NOT:
- Skip directly to editing sources.yaml
- Add a source without profiling
- Take shortcuts

The profiling step uses Firecrawl to probe the site. This is NOT optional.
</stop>

Add a web aggregator source WITH mandatory profiling.

<critical>
## PROFILING IS MANDATORY

This workflow discovers the optimal scraping strategy for each site.
DO NOT skip profiling. DO NOT save without a profile.

The profile determines:
- Whether to use `map` or `crawl` for URL discovery
- What regex pattern matches event URLs
- Sample URLs for validation
</critical>

## Input

A single web URL to add as a source.

**Process one URL at a time** - each requires interactive profiling.

---

## Step 1: Load Config & Check Duplicate

```python
from pathlib import Path
import yaml

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"

if not config_path.exists():
    print("ERROR: sources.yaml not found. Run /newsletter-events:setup first.")
    # STOP

with open(config_path) as f:
    config = yaml.safe_load(f)

existing_urls = {s["url"].lower() for s in config["sources"]["web_aggregators"]["sources"]}

if url.lower() in existing_urls:
    return {"type": "Web", "source": url, "name": "", "status": "Already exists"}
```

## Step 2: Build Base Entry

```python
from urllib.parse import urlparse

domain = urlparse(url).netloc.replace("www.", "")
name = domain.split(".")[0].replace("-", " ").title()

new_source = {
    "url": url,
    "name": name,
    "source_type": "listing",
    "max_pages": 50,
    # profile will be added in Step 3
}
```

---

## Step 3: Profile Site (MANDATORY)

<critical>
DO NOT SKIP THIS STEP.
Every web aggregator MUST be profiled before saving.
</critical>

### 3a: Probe with Map (Fast)

```python
from scripts.scrape_firecrawl import FirecrawlClient
import re

client = FirecrawlClient()

print(f"Profiling {url}...")
print("  Trying map_url (fast discovery)...")

map_result = client.app.map_url(url)
all_urls = map_result.get("links", [])

# Filter to likely event URLs
event_patterns = r"/events?/|/calendar/|/shows?/|/event/|/performances?/"
event_urls = [u for u in all_urls if re.search(event_patterns, u, re.I)]

discovery_method = "map"
print(f"  Map found {len(event_urls)} event URLs")
```

### 3b: Crawl Fallback (If Map Fails)

```python
MIN_URLS_THRESHOLD = 5

if len(event_urls) < MIN_URLS_THRESHOLD:
    print(f"  Map found too few URLs, trying crawl...")

    crawl_result = client.app.crawl_url(
        url,
        limit=30,
        max_discovery_depth=2,
        scrape_options={"formats": ["links"]}
    )

    all_links = []
    for page in crawl_result.get("data", []):
        all_links.extend(page.get("links", []))

    event_urls = [u for u in all_links if re.search(event_patterns, u, re.I)]
    discovery_method = "crawl"

    print(f"  Crawl found {len(event_urls)} event URLs")
```

### 3c: Learn URL Pattern

Analyze discovered URLs to find the common pattern:

```python
from urllib.parse import urlparse

# Extract paths from discovered URLs
paths = [urlparse(u).path for u in event_urls[:20]]

# Claude analyzes paths and generates appropriate regex
# Examples:
#   /events/jazz-night           → r"/events/[^/]+$"
#   /event/a-frosty-fest/76214   → r"/event/[^/]+/\d+/?$"
#   /calendar/2025/01/15/show    → r"/calendar/\d{4}/\d{2}/\d{2}/[^/]+$"
```

### 3d: Present Profile for Confirmation

Display the discovered profile to the user:

```
📊 Source Profile: {name}
   URL: {url}

   Discovery Method: {discovery_method}
   {f"(map found {len(map_urls)} URLs)" if discovery_method == "map" else f"(map found <5, crawl found {len(event_urls)})"}

   Learned Pattern: {human_readable_pattern}
   Regex: {learned_regex}

   Sample Event URLs ({len(event_urls)} total):
     • {event_urls[0]}
     • {event_urls[1]}
     • {event_urls[2]}

   Save this profile? (Y/n)
```

Wait for user confirmation.

### 3e: Handle Profiling Failures

If BOTH map and crawl find zero event URLs:

```
⚠️  Could not discover event URLs on {url}

Possible reasons:
- Site requires JavaScript that Firecrawl couldn't render
- Events are loaded via API/AJAX
- Non-standard URL structure

Options:
1. Add anyway (you can manually set event_url_pattern later)
2. Skip this source
3. Provide a custom event_url_pattern now

Choose (1-3):
```

If user chooses 1: Save with `profile: null` and `needs_manual_config: true`
If user chooses 2: Skip and return status "Skipped - profiling failed"
If user chooses 3: Prompt for pattern, validate it, then continue

---

## Step 4: Build Complete Entry with Profile

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

# Enable web aggregators if not already
config["sources"]["web_aggregators"]["enabled"] = True
config["sources"]["web_aggregators"]["sources"].append(new_source)
```

---

## Step 5: Backup & Save

```python
import shutil

backup_path = config_path.with_suffix(f".yaml.{datetime.now():%Y%m%d%H%M%S}.backup")
shutil.copy2(config_path, backup_path)

with open(config_path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

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

## Output

Return result for the dispatcher:

```python
return {
    "type": "Web",
    "source": domain,
    "name": name,
    "status": f"Added (profiled: {discovery_method})",
}
```
