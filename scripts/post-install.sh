#!/bin/bash
# Post-install hook for local-media-tools plugin
# Purpose: Filesystem setup ONLY (directories, config templates)
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

cd "$PLUGIN_DIR"

# Create working directories
mkdir -p tmp/extraction/raw tmp/extraction/images tmp/output

# Copy config templates (only if destination doesn't exist)
if [ ! -e ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    chmod 600 .env
fi

if [ ! -e "config/sources.yaml" ] && [ -f "config/sources.example.yaml" ]; then
    cp config/sources.example.yaml config/sources.yaml
fi

echo '{"status": "success", "message": "Local Media Tools installed. Run /setup to configure."}'
