#!/usr/bin/env python3
"""Machine-readable setup validation for agents."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


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


def check_api_key(plugin_root: Path) -> dict:
    """Check if API key is configured."""
    env_file = plugin_root / ".env"
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


def validate_setup(plugin_root: Path) -> dict:
    """Return complete setup status as JSON."""
    return {
        "plugin_root": str(plugin_root),
        "runtimes": {
            "uv": check_command("uv"),
            "bun": check_command("bun"),
        },
        "config": {
            "env_exists": (plugin_root / ".env").exists(),
            "api_key": check_api_key(plugin_root),
            "sources_yaml_exists": (plugin_root / "config/sources.yaml").exists(),
        },
        "directories": {
            "tmp_extraction": (plugin_root / "tmp/extraction").exists(),
            "tmp_output": (plugin_root / "tmp/output").exists(),
        },
        "ready": False,  # Will be set below
    }


def main():
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", ".")).resolve()
    status = validate_setup(plugin_root)

    # Determine if fully ready
    status["ready"] = all([
        status["runtimes"]["uv"]["installed"],
        status["runtimes"]["bun"]["installed"],
        status["config"]["api_key"]["configured"],
        status["config"]["sources_yaml_exists"],
    ])

    print(json.dumps(status, indent=2))
    sys.exit(0 if status["ready"] else 1)


if __name__ == "__main__":
    main()
