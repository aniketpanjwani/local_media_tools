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

RUN THE PROFILER CLI FROM THE PLUGIN DIRECTORY.
DO NOT try to import Python modules directly.
</critical>

### 3a: Run the Profiler CLI

The plugin includes a CLI tool for profiling. First get the plugin path, then run the profiler.

**Step 1: Get plugin directory:**
```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save the output path as `PLUGIN_DIR`.

**Step 2: Run the profiler:**
```bash
cd "$PLUGIN_DIR" && uv run python scripts/profile_source.py "{url}"
```

This will:
1. Try `map_url()` first (fast sitemap/link discovery)
2. Fall back to `crawl_url()` if map finds < 5 event URLs
3. Filter URLs matching `/events?/`, `/calendar/`, `/shows?/`, etc.
4. Suggest a regex pattern based on discovered URLs
5. Output JSON with the profile data

Example output:
```json
{
  "success": true,
  "url": "https://example.com",
  "discovery_method": "map",
  "event_urls_count": 25,
  "event_urls": ["https://example.com/events/jazz-night", ...],
  "suggested_regex": "/events/[^/]+/?$",
  "notes": "Discovered 25 event URLs using map."
}
```

### 3b: Parse Profiler Output

Extract the key fields from the JSON output:
- `discovery_method`: "map" or "crawl"
- `event_urls`: Sample URLs for validation
- `suggested_regex`: Pattern to match event URLs
- `event_urls_count`: Total found

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

The profiler now automatically tries multiple strategies:
1. `map()` - Fast sitemap/link discovery
2. `scrape_url()` with `waitFor: 3000` and `formats: ["links"]` - For JavaScript-heavy sites
3. `crawl()` - Thorough multi-page crawl

If ALL strategies find zero event URLs:

```
⚠️  Could not discover event URLs on {url}

The profiler tried:
- map() → 0 URLs
- scrape with waitFor (3s) → 0 URLs
- crawl → 0 URLs

Possible reasons:
- Site requires login or has bot protection
- Events are loaded via authenticated API
- Non-standard URL structure

Options:
1. Study the page manually to find URL patterns
2. Add anyway without a profile (configure later)
3. Skip this source

Choose (1-3):
```

**Option 1 - Manual Pattern Discovery:**
1. Use WebFetch to analyze the page structure
2. Look for event detail links in the HTML
3. Derive a regex pattern from observed URLs
4. **CRITICAL:** Set `discovery_method: "map"` - the schema only allows "map" or "crawl"
5. Set `notes: "Manually profiled - [description]"` to document manual discovery

**Option 2:** Save with `profile: null`

**Option 3:** Skip and return status "Skipped - profiling failed"

<critical>
**Schema Constraint:** `discovery_method` must be `"map"` or `"crawl"`.
Do NOT use values like `"manual"` or `"scrape"` - they will cause Pydantic validation errors.
When manually profiling, use `"map"` and document in the `notes` field.
</critical>

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
