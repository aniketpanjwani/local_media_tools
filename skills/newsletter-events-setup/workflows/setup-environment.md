# Workflow: Setup Environment

<process>
## Step 1: Run Bootstrap Script

```bash
cd ${CLAUDE_PLUGIN_ROOT}
./scripts/setup.sh
```

This will:
- Install `uv` if missing
- Install `bun` if missing
- Run `uv sync` for Python dependencies
- Run `bun install` for Node.js dependencies
- Create stable config directory at `~/.config/local-media-tools/`
- Copy `.env.example` to `~/.config/local-media-tools/.env` if needed
- Copy `sources.example.yaml` to `~/.config/local-media-tools/sources.yaml` if needed

## Step 2: Configure API Keys

Edit `~/.config/local-media-tools/.env` and add your ScrapeCreators API key:

```
SCRAPECREATORS_API_KEY=your_key_here
```

Get a key at https://scrapecreators.com

## Step 3: Configure Sources

Edit `~/.config/local-media-tools/sources.yaml` to add your Instagram accounts and Facebook pages.

See `config/sources.example.yaml` in the plugin directory for detailed examples.

## Step 4: Verify Installation

Run verification checks:

```bash
# Check uv
uv --version

# Check bun
bun --version

# Check Python imports
cd ${CLAUDE_PLUGIN_ROOT}
uv run python -c "import rapidfuzz; import pydantic; import structlog; print('OK')"

# Check Node.js
bun run scripts/scrape_facebook.js --help

# Check config directory
ls -la ~/.config/local-media-tools/
```
</process>

<success_criteria>
Setup is complete when:
- [ ] All verification commands pass
- [ ] `~/.config/local-media-tools/.env` contains valid API key
- [ ] `~/.config/local-media-tools/sources.yaml` exists with at least one source
</success_criteria>
