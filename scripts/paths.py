"""
Centralized path resolver for stable user configuration.

All user data (config, API keys, database) lives in ~/.config/local-media-tools/
to persist across plugin version upgrades.

Plugin code/dependencies remain in the version-specific CLAUDE_PLUGIN_ROOT.
"""

from pathlib import Path

# Stable user config directory (persists across plugin upgrades)
CONFIG_DIR = Path.home() / ".config" / "local-media-tools"

# Individual paths within config directory
ENV_PATH = CONFIG_DIR / ".env"
SOURCES_PATH = CONFIG_DIR / "sources.yaml"
DATA_DIR = CONFIG_DIR / "data"
DATABASE_PATH = DATA_DIR / "events.db"

# Temporary working files (can be in plugin root, ephemeral)
# These are used during scraping but don't need to persist
TEMP_RAW_DIR = CONFIG_DIR / "data" / "raw"
TEMP_IMAGES_DIR = CONFIG_DIR / "data" / "images"


def get_config_dir() -> Path:
    """Get the stable config directory path."""
    return CONFIG_DIR


def get_env_path() -> Path:
    """Get path to .env file with API keys."""
    return ENV_PATH


def get_sources_path() -> Path:
    """Get path to sources.yaml config file."""
    return SOURCES_PATH


def get_database_path() -> Path:
    """Get path to SQLite events database."""
    return DATABASE_PATH


def get_output_dir() -> Path:
    """Get output directory for newsletters (current working directory)."""
    return Path.cwd()


def ensure_directories() -> None:
    """Create all necessary directories if they don't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def get_plugin_root() -> Path:
    """Get the plugin installation root (for scripts, dependencies)."""
    import os
    return Path(os.environ.get("CLAUDE_PLUGIN_ROOT", ".")).resolve()
