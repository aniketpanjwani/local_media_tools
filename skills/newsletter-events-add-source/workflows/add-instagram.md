# Workflow: Add Instagram Accounts

Add one or more Instagram accounts to sources.yaml configuration.

<required_reading>
This is a simple workflow - no profiling needed for Instagram accounts.
</required_reading>

## Input

List of Instagram handles (already parsed, @ stripped, lowercase).

## Step 1: Load Current Config

```python
from pathlib import Path
import yaml

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"

if not config_path.exists():
    print("ERROR: sources.yaml not found. Run /newsletter-events:setup first.")
    # STOP - cannot continue

with open(config_path) as f:
    config = yaml.safe_load(f)
```

## Step 2: Check for Duplicates

```python
existing_handles = {
    a["handle"].lower()
    for a in config["sources"]["instagram"]["accounts"]
}

new_handles = []
duplicates = []

for handle in instagram_handles:
    if handle.lower() in existing_handles:
        duplicates.append(handle)
    else:
        new_handles.append(handle)
```

## Step 3: Build New Entries

For each new handle:

```python
new_accounts = []
for handle in new_handles:
    new_account = {
        "handle": handle,
        "name": handle.replace("_", " ").title(),
        "type": "venue",  # Default type
    }
    new_accounts.append(new_account)
    config["sources"]["instagram"]["accounts"].append(new_account)
```

## Step 4: Backup Config

```python
import shutil
from datetime import datetime

backup_path = config_path.with_suffix(f".yaml.{datetime.now():%Y%m%d%H%M%S}.backup")
shutil.copy2(config_path, backup_path)
```

## Step 5: Save Updated Config

```python
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
    # STOP - validation failed
```

## Output

Return results for the dispatcher to display:

```python
results = []
for account in new_accounts:
    results.append({
        "type": "Instagram",
        "source": f"@{account['handle']}",
        "name": account["name"],
        "status": "Added",
    })
for handle in duplicates:
    results.append({
        "type": "Instagram",
        "source": f"@{handle}",
        "name": handle.replace("_", " ").title(),
        "status": "Already exists",
    })
```
