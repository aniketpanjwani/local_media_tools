#!/bin/bash
# scripts/setup.sh - Bootstrap script for consistent environments

set -e

echo "Setting up newsletter-events environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies with uv...${NC}"
uv sync
echo -e "${GREEN}Python dependencies installed${NC}"

# Install Node.js dependencies
echo -e "${YELLOW}Installing Node.js dependencies with bun...${NC}"
bun install
echo -e "${GREEN}Node.js dependencies installed${NC}"

# Create tmp directories
mkdir -p tmp/extraction/raw tmp/extraction/images tmp/output
echo -e "${GREEN}Created tmp directories${NC}"

# Check for .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Created .env from .env.example - please add your API keys${NC}"
    else
        echo -e "${RED}No .env file found - create one with SCRAPECREATORS_API_KEY${NC}"
    fi
else
    echo -e "${GREEN}.env file exists${NC}"
fi

# Verify API key
if [ -z "$SCRAPECREATORS_API_KEY" ] && ! grep -q "SCRAPECREATORS_API_KEY=." .env 2>/dev/null; then
    echo -e "${RED}Warning: SCRAPECREATORS_API_KEY not set${NC}"
    echo "   Add to your .env file: SCRAPECREATORS_API_KEY=your_key_here"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Add your API keys to .env"
echo "  2. Copy config/sources.example.yaml to config/sources.yaml"
echo "  3. Configure your event sources"
echo "  4. Run /research-events to start scraping"
