---
description: Validates newsletter plugin configuration before research operations. Use proactively before running Facebook Discover or any research workflow that depends on external services.
capabilities:
  - Validate ~/.config/local-media-tools/sources.yaml exists and is well-formed
  - Check Facebook location configuration for discovery
  - Verify API keys are set for required services
  - Detect common configuration mistakes
  - Suggest fixes for invalid configurations
---

# Config Validator Agent

Proactive agent that validates plugin configuration before research operations.

## When to Use

This agent should run automatically:
- **Before** `/research` command (especially Facebook location-based discovery)
- **Before** any skill workflow that requires external configuration

## Validation Checks

### 1. Config File Exists

```python
from pathlib import Path

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"
if not config_path.exists():
    return {
        "valid": False,
        "error": "~/.config/local-media-tools/sources.yaml not found",
        "fix": "Run /newsletter-events:setup to create config directory and copy templates"
    }
```

### 2. YAML Syntax Valid

```python
import yaml

try:
    config = yaml.safe_load(config_path.read_text())
except yaml.YAMLError as e:
    return {
        "valid": False,
        "error": f"Invalid YAML syntax: {e}",
        "fix": "Check ~/.config/local-media-tools/sources.yaml for YAML syntax errors"
    }
```

### 3. Required Sections Present

```python
required_sections = ["newsletter", "sources"]
missing = [s for s in required_sections if s not in config]
if missing:
    return {
        "valid": False,
        "error": f"Missing required sections: {missing}",
        "fix": "See config/sources.example.yaml in plugin directory for required structure"
    }
```

### 4. Facebook Locations Configured (for Discover)

When validating for Facebook Discover specifically:

```python
facebook = config.get("sources", {}).get("facebook", {})
locations = facebook.get("locations", [])

if not locations:
    return {
        "valid": False,
        "error": "No Facebook locations configured",
        "fix": "Run /newsletter-events:setup-location to add a Facebook location_id, or edit ~/.config/local-media-tools/sources.yaml manually"
    }

# Validate each location
for i, loc in enumerate(locations):
    if not loc.get("location_id"):
        return {
            "valid": False,
            "error": f"Location {i+1} missing location_id",
            "fix": "Each location needs a location_id. Run /setup-location to find your city's ID."
        }
    if not loc.get("location_name"):
        return {
            "valid": False,
            "error": f"Location {i+1} missing location_name",
            "fix": "Add a human-readable location_name for each location"
        }
```

### 5. API Keys Present (for Instagram)

When validating for Instagram research:

```python
import os

if not os.getenv("SCRAPECREATORS_API_KEY"):
    return {
        "valid": False,
        "error": "SCRAPECREATORS_API_KEY not set",
        "fix": "Add SCRAPECREATORS_API_KEY to ~/.config/local-media-tools/.env"
    }
```

### 6. Instagram Accounts Configured

```python
instagram = config.get("sources", {}).get("instagram", {})
accounts = instagram.get("accounts", [])

if instagram.get("enabled", True) and not accounts:
    return {
        "valid": False,
        "warning": "Instagram enabled but no accounts configured",
        "fix": "Add Instagram account handles to ~/.config/local-media-tools/sources.yaml"
    }
```

## Validation Response Format

Return a structured validation result:

```python
{
    "valid": True,  # or False
    "checks": [
        {"name": "config_exists", "passed": True},
        {"name": "yaml_valid", "passed": True},
        {"name": "facebook_locations", "passed": True, "count": 2},
        {"name": "instagram_accounts", "passed": True, "count": 5},
        {"name": "api_keys", "passed": True},
    ],
    "warnings": [
        "Instagram account 'old_venue' hasn't been scraped in 30+ days"
    ],
    "errors": [],  # Empty if valid
    "ready_for": ["facebook_discover", "facebook_pages", "instagram"]
}
```

## Proactive Behavior

When the user invokes a research command:

1. **Detect intent**: Is this Facebook Discover, Instagram, or all sources?
2. **Run relevant checks**: Only validate what's needed
3. **Report issues early**: Before any scraping begins
4. **Suggest fixes**: Provide actionable next steps

### Example Interaction

```
User: /research

[config-validator agent runs proactively]

Agent: Validating configuration for research...

Config Validation Results:
  ~/.config/local-media-tools/sources.yaml   OK
  YAML syntax           OK
  Facebook locations    2 configured (Medellín, Bogotá)
  Instagram accounts    5 configured
  API keys              OK

Ready to proceed with research. Which sources would you like to scrape?
```

### Example with Issues

```
User: /research

[config-validator agent runs proactively]

Agent: Configuration issues found:

  Facebook locations    MISSING

You need to configure at least one Facebook location for discovery.

Run `/newsletter-events:setup-location` to interactively configure your city, or add manually to ~/.config/local-media-tools/sources.yaml:

```yaml
sources:
  facebook:
    locations:
      - location_id: "YOUR_LOCATION_ID"
        location_name: "Your City"
```

Would you like to:
1. Run /newsletter-events:setup-location now
2. Continue with Instagram only
3. Skip research for now
```

## Integration Points

This agent integrates with:
- **`/research` command**: Validates before research begins
- **`/setup-location` command**: Validates after location is added
- **`newsletter-events-research` skill**: Called at workflow start
