#!/usr/bin/env python3
"""Machine-readable setup validation for agents."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# Import from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from paths import (
    get_config_dir,
    get_env_path,
    get_sources_path,
    get_database_path,
    get_plugin_root,
    DATA_DIR,
)


def check_command(cmd: str) -> dict:
    """Check if a command exists and get its version."""
    path = shutil.which(cmd)
    if not path:
        return {"installed": False, "version": None}

    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip().split("\n")[0]
        return {"installed": True, "version": version}
    except Exception:
        return {"installed": True, "version": "unknown"}


def check_api_key() -> dict:
    """Check if API key is configured."""
    env_file = get_env_path()
    if not env_file.exists():
        return {"configured": False, "reason": ".env file missing"}

    content = env_file.read_text()
    for line in content.splitlines():
        if line.startswith("SCRAPECREATORS_API_KEY="):
            value = line.split("=", 1)[1].strip()
            if value and value != "your_api_key_here":
                return {"configured": True}
            return {"configured": False, "reason": "API key is placeholder"}

    return {"configured": False, "reason": "SCRAPECREATORS_API_KEY not found"}


def check_firecrawl_key() -> dict:
    """Check if Firecrawl API key is configured (optional - only for web aggregators)."""
    sources_file = get_sources_path()
    if sources_file.exists():
        content = sources_file.read_text()
        # Only required if web_aggregators section has actual sources
        if "web_aggregators:" not in content or "sources: []" in content:
            return {"required": False, "configured": True}

    env_file = get_env_path()
    if not env_file.exists():
        return {"required": True, "configured": False, "reason": ".env missing"}

    content = env_file.read_text()
    for line in content.splitlines():
        if line.startswith("FIRECRAWL_API_KEY="):
            value = line.split("=", 1)[1].strip()
            if value and value != "your_firecrawl_api_key_here":
                return {"required": True, "configured": True}
            return {"required": True, "configured": False, "reason": "placeholder"}

    return {"required": True, "configured": False, "reason": "key not found"}


def validate_setup() -> dict:
    """Return complete setup status as JSON."""
    config_dir = get_config_dir()
    plugin_root = get_plugin_root()

    return {
        "config_dir": str(config_dir),
        "plugin_root": str(plugin_root),
        "runtimes": {
            "uv": check_command("uv"),
            "bun": check_command("bun"),
        },
        "config": {
            "config_dir_exists": config_dir.exists(),
            "env_exists": get_env_path().exists(),
            "api_key": check_api_key(),
            "firecrawl_key": check_firecrawl_key(),
            "sources_yaml_exists": get_sources_path().exists(),
        },
        "directories": {
            "data_dir": DATA_DIR.exists(),
        },
        "database": {
            "exists": get_database_path().exists(),
            "path": str(get_database_path()),
        },
        "ready": False,  # Will be set below
    }


def main():
    status = validate_setup()

    # Determine if fully ready
    # Firecrawl key only required if web_aggregators has sources configured
    firecrawl_ok = (
        not status["config"]["firecrawl_key"].get("required", False)
        or status["config"]["firecrawl_key"].get("configured", False)
    )

    status["ready"] = all([
        status["runtimes"]["uv"]["installed"],
        status["runtimes"]["bun"]["installed"],
        status["config"]["api_key"]["configured"],
        status["config"]["sources_yaml_exists"],
        firecrawl_ok,
    ])

    print(json.dumps(status, indent=2))
    sys.exit(0 if status["ready"] else 1)


if __name__ == "__main__":
    main()
