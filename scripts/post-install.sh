#!/bin/bash
# Post-install hook for newsletter-events plugin
# Purpose: Create stable config directory and copy templates
# All runtime/dependency checks happen in /setup command

set -e

PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-}"

# Validate PLUGIN_DIR
if [ -z "$PLUGIN_DIR" ]; then
    echo '{"status": "error", "message": "CLAUDE_PLUGIN_ROOT not set"}'
    exit 1
fi

if [ ! -d "$PLUGIN_DIR" ]; then
    echo '{"status": "error", "message": "Plugin directory does not exist"}'
    exit 1
fi

# Resolve to absolute path
PLUGIN_DIR=$(cd "$PLUGIN_DIR" && pwd -P)

# Verify this is a valid plugin directory
if [ ! -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ]; then
    echo '{"status": "error", "message": "Not a valid plugin directory"}'
    exit 1
fi

# Stable config directory (persists across plugin upgrades)
CONFIG_DIR="$HOME/.config/local-media-tools"
DATA_DIR="$CONFIG_DIR/data"

# Create stable config directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/raw"
mkdir -p "$DATA_DIR/images"

# Copy .env template (only if destination doesn't exist)
if [ ! -e "$CONFIG_DIR/.env" ] && [ -f "$PLUGIN_DIR/.env.example" ]; then
    cp "$PLUGIN_DIR/.env.example" "$CONFIG_DIR/.env"
    chmod 600 "$CONFIG_DIR/.env"
fi

# Copy sources.yaml template (only if destination doesn't exist)
if [ ! -e "$CONFIG_DIR/sources.yaml" ] && [ -f "$PLUGIN_DIR/config/sources.example.yaml" ]; then
    cp "$PLUGIN_DIR/config/sources.example.yaml" "$CONFIG_DIR/sources.yaml"
fi

echo '{"status": "success", "message": "Newsletter Events installed. Config at ~/.config/local-media-tools/. Run /newsletter-events:setup to configure."}'
