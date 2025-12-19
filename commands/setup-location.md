---
name: newsletter-events:setup-location
description: Interactively set up a Facebook location_id for event discovery using Chrome MCP
---

# Setup Facebook Location

Interactive command to help users configure a Facebook `location_id` for event discovery.

## Overview

This command guides you through finding your city's `location_id` by:
1. Opening Facebook Events in Chrome
2. Helping you select the correct city
3. Extracting the `location_id` from the URL
4. Saving it to your configuration

## Prerequisites

- **Chrome MCP Server** must be running
- Chrome browser must be open
- You should be **logged into Facebook** in Chrome

## Workflow

### Step 1: Verify Chrome MCP is available

Before starting, verify Chrome MCP is responding:

```
chrome_get_windows_and_tabs()
```

If this fails, inform the user: "Chrome MCP is not responding. Please ensure the Chrome extension is installed and Chrome is open."

### Step 2: Navigate to Facebook Events

```
chrome_navigate(url: "https://www.facebook.com/events/")
```

Wait 3 seconds for page load.

### Step 3: Check authentication

```
chrome_get_web_content(textContent: true)
```

Look for login indicators. If not logged in:
- "Please log into Facebook in Chrome first, then run this command again."
- STOP

### Step 4: Prompt user for city name

Ask the user:

> What city do you want to find events for? (e.g., "Medellín", "Brooklyn", "San José")

Store their response as `target_city`.

### Step 5: Guide user to location picker

Instruct the user:

> I'll now help you find the location_id for **{target_city}**.
>
> 1. Look at the Facebook Events page in Chrome
> 2. Click on the location filter (usually shows "Nearby" or your current location near the top)
> 3. Type "**{target_city}**" in the search box
> 4. **Important**: Select the correct city from the dropdown (watch for disambiguation!)
>
> Let me know when you've selected your city.

Wait for user confirmation.

### Step 6: Extract location_id from URL

After user confirms city selection:

```
chrome_get_web_content(htmlContent: false, textContent: false)
```

This returns the current URL. Parse it to extract `location_id`:

```python
import re
from urllib.parse import urlparse, parse_qs

# Get current URL from Chrome
current_url = chrome_response.get("url", "")

# Extract location_id parameter
parsed = urlparse(current_url)
params = parse_qs(parsed.query)
location_id = params.get("location_id", [None])[0]
```

If `location_id` not found:
- "I couldn't find a location_id in the URL. Did you select a city from the location picker?"
- Offer to retry

### Step 7: Confirm with user

Show the user what was extracted:

> I found:
> - **Location ID**: `{location_id}`
> - **City**: {target_city}
>
> Is this correct? (yes/no)

If no, go back to Step 5.

### Step 8: Read current config

```python
from pathlib import Path
import yaml

config_path = Path("config/sources.yaml")
if config_path.exists():
    config = yaml.safe_load(config_path.read_text())
else:
    config = {"sources": {"facebook": {"enabled": True, "pages": [], "locations": []}}}
```

### Step 9: Add or update location

Check if this location_id already exists:

```python
existing_locations = config.get("sources", {}).get("facebook", {}).get("locations", [])
existing_ids = [loc.get("location_id") for loc in existing_locations]

if location_id in existing_ids:
    # Update existing
    print(f"Updating existing location: {target_city}")
    for loc in existing_locations:
        if loc.get("location_id") == location_id:
            loc["location_name"] = target_city
else:
    # Add new
    new_location = {
        "location_id": location_id,
        "location_name": target_city,
        "date_filter": "THIS_WEEK",
        "scroll_count": 3,
        "scroll_delay_seconds": 5.0,
    }
    existing_locations.append(new_location)

config["sources"]["facebook"]["locations"] = existing_locations
```

### Step 10: Save configuration

```python
config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
```

### Step 11: Confirm success

> Location saved to `config/sources.yaml`:
>
> ```yaml
> locations:
>   - location_id: "{location_id}"
>     location_name: "{target_city}"
>     date_filter: "THIS_WEEK"
>     scroll_count: 3
>     scroll_delay_seconds: 5.0
> ```
>
> You can now run `/research` and select "Facebook Discover" to scrape events from this location.
>
> **Tip**: Adjust `date_filter` to `THIS_MONTH` for more events, or increase `scroll_count` to load more results.

## Error Handling

| Error | Response |
|-------|----------|
| Chrome MCP not available | "Chrome MCP is not responding. Please ensure Chrome is open and the extension is installed." |
| Not logged into Facebook | "Please log into Facebook in Chrome first, then run this command again." |
| No location_id in URL | "I couldn't extract a location_id. Please make sure you selected a city from the dropdown (not just typed it)." |
| Config file write error | "Failed to save config. Please check file permissions for config/sources.yaml" |

## Example Session

```
User: /setup-location
Claude: I'll help you set up a Facebook location for event discovery.

First, let me verify Chrome MCP is available... OK!

What city do you want to find events for? (e.g., "Medellín", "Brooklyn", "San José")

User: Medellín, Colombia

Claude: I'll now help you find the location_id for **Medellín, Colombia**.

I've opened Facebook Events in Chrome. Now:
1. Click on the location filter (shows "Nearby" near the top)
2. Type "Medellín" in the search box
3. **Important**: Select "Medellín, Antioquia" from the dropdown (not Medellín, Philippines!)

Let me know when you've selected your city.

User: done

Claude: I found:
- **Location ID**: `111841478834264`
- **City**: Medellín, Colombia

Is this correct? (yes/no)

User: yes

Claude: Location saved to `config/sources.yaml`:

```yaml
locations:
  - location_id: "111841478834264"
    location_name: "Medellín, Colombia"
    date_filter: "THIS_WEEK"
```

You can now run `/research` and select "Facebook Discover" to scrape events!
```
