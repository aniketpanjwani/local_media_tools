#!/bin/bash
# scripts/setup.sh - Bootstrap script for consistent environments

set -e

echo "Setting up newsletter-events environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stable config directory (persists across plugin upgrades)
CONFIG_DIR="$HOME/.config/local-media-tools"
DATA_DIR="$CONFIG_DIR/data"

# Plugin root (for dependencies)
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-.}"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv (Python package manager)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo -e "${GREEN}uv installed${NC}"

# Check for bun
if ! command -v bun &> /dev/null; then
    echo -e "${YELLOW}Installing bun (JavaScript runtime)...${NC}"
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
fi
echo -e "${GREEN}bun installed${NC}"

# Install Python dependencies (in plugin directory)
echo -e "${YELLOW}Installing Python dependencies with uv...${NC}"
cd "$PLUGIN_DIR"
uv sync
echo -e "${GREEN}Python dependencies installed${NC}"

# Install Node.js dependencies (in plugin directory)
echo -e "${YELLOW}Installing Node.js dependencies with bun...${NC}"
bun install
echo -e "${GREEN}Node.js dependencies installed${NC}"

# Create stable config directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/raw"
mkdir -p "$DATA_DIR/images"
echo -e "${GREEN}Created config directories at $CONFIG_DIR${NC}"

# Copy .env template if not exists
if [ ! -f "$CONFIG_DIR/.env" ]; then
    if [ -f "$PLUGIN_DIR/.env.example" ]; then
        cp "$PLUGIN_DIR/.env.example" "$CONFIG_DIR/.env"
        chmod 600 "$CONFIG_DIR/.env"
        echo -e "${YELLOW}Created .env from template - please add your API keys${NC}"
    else
        echo -e "${RED}No .env.example found in plugin directory${NC}"
    fi
else
    echo -e "${GREEN}.env file exists${NC}"
fi

# Copy sources.yaml template if not exists
if [ ! -f "$CONFIG_DIR/sources.yaml" ]; then
    if [ -f "$PLUGIN_DIR/config/sources.example.yaml" ]; then
        cp "$PLUGIN_DIR/config/sources.example.yaml" "$CONFIG_DIR/sources.yaml"
        echo -e "${YELLOW}Created sources.yaml from template - please configure your sources${NC}"
    else
        echo -e "${RED}No sources.example.yaml found in plugin directory${NC}"
    fi
else
    echo -e "${GREEN}sources.yaml file exists${NC}"
fi

# Verify API key
if [ -z "$SCRAPECREATORS_API_KEY" ] && ! grep -q "SCRAPECREATORS_API_KEY=." "$CONFIG_DIR/.env" 2>/dev/null; then
    echo -e "${RED}Warning: SCRAPECREATORS_API_KEY not set${NC}"
    echo "   Add to $CONFIG_DIR/.env: SCRAPECREATORS_API_KEY=your_key_here"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Configuration directory: $CONFIG_DIR"
echo ""
echo "Next steps:"
echo "  1. Add your API keys to $CONFIG_DIR/.env"
echo "  2. Configure your event sources in $CONFIG_DIR/sources.yaml"
echo "  3. Run /newsletter-events:research to start scraping"
