---
name: newsletter-events:setup
description: Set up or verify Local Media Tools environment (runtimes, dependencies, config)
---

# Setup Local Media Tools

Interactive setup wizard that verifies and configures everything needed to use the plugin.

## Configuration Location

All user configuration is stored in `~/.config/local-media-tools/`:
- `.env` - API keys (ScrapeCreators, Firecrawl)
- `sources.yaml` - Event sources configuration
- `data/events.db` - SQLite database of scraped events

This location persists across plugin upgrades.

## Arguments

- `--json` - Output machine-readable JSON instead of human-friendly text

## Workflow

### Step 1: Check Runtime Requirements

```bash
# Check uv
uv --version 2>/dev/null || echo "NOT_INSTALLED"

# Check bun
bun --version 2>/dev/null || echo "NOT_INSTALLED"
```

**If uv missing:**
> uv (Python package manager) is not installed.
>
> Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`
>
> Then restart your terminal and run `/newsletter-events:setup` again.

**If bun missing:**
> bun (JavaScript runtime) is not installed.
>
> Install with: `curl -fsSL https://bun.sh/install | bash`
>
> Then restart your terminal and run `/newsletter-events:setup` again.

**STOP HERE if runtimes missing.** User must install them first.

### Step 2: Get Plugin Directory and Install Dependencies

First, get the plugin installation path:
```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save the output path as `PLUGIN_DIR`, then install dependencies:

```bash
cd "$PLUGIN_DIR"
uv sync
bun install
```

Report success/failure clearly. If failure, show the error and suggest fixes.

### Step 3: Check Configuration Files

**Check .env and API key:**
```bash
CONFIG_DIR="$HOME/.config/local-media-tools"
[ -f "$CONFIG_DIR/.env" ] && echo "EXISTS" || echo "MISSING"
grep -q "SCRAPECREATORS_API_KEY=." "$CONFIG_DIR/.env" 2>/dev/null && \
  ! grep -q "SCRAPECREATORS_API_KEY=your_api_key_here" "$CONFIG_DIR/.env" 2>/dev/null && \
  echo "KEY_SET" || echo "KEY_MISSING"
```

**If API key not set:**
> API key required for Instagram scraping.
>
> 1. Sign up at https://scrapecreators.com
> 2. Get your API key from the dashboard
> 3. Edit `~/.config/local-media-tools/.env` and replace the placeholder:
>    ```
>    SCRAPECREATORS_API_KEY=your_actual_key_here
>    ```
>
> Note: Use an editor, not command line, to avoid saving the key in shell history.

**Check sources.yaml:**
```bash
[ -f "$CONFIG_DIR/sources.yaml" ] && echo "EXISTS" || echo "MISSING"
```

**If sources.yaml is still template:**
> No event sources configured yet.
>
> Edit `~/.config/local-media-tools/sources.yaml` and add your sources.
> See `config/sources.example.yaml` in the plugin directory for examples.

**Check Firecrawl API key (if web aggregators configured):**

If `sources.yaml` includes `web_aggregators:` section with sources:

```bash
grep -q "FIRECRAWL_API_KEY=." "$CONFIG_DIR/.env" 2>/dev/null && \
  ! grep -q "FIRECRAWL_API_KEY=your_firecrawl_api_key_here" "$CONFIG_DIR/.env" 2>/dev/null && \
  echo "KEY_SET" || echo "KEY_MISSING"
```

**If Firecrawl key not set but web aggregators are configured:**
> Firecrawl API key required for web aggregator scraping.
>
> 1. Sign up at https://firecrawl.dev
> 2. Get your API key from the dashboard
> 3. Edit `~/.config/local-media-tools/.env` and add:
>    ```
>    FIRECRAWL_API_KEY=your_actual_key_here
>    ```
>
> Note: This is only needed if you're using web aggregator sources.

### Step 4: Summary

**Human-readable output:**
```
Local Media Tools Setup Status
==============================
Config directory: ~/.config/local-media-tools/

✅ uv installed (v0.5.x)
✅ bun installed (v1.x.x)
✅ Python dependencies installed
✅ Node dependencies installed
⚠️  API key not configured - Instagram scraping won't work
⚠️  Firecrawl key not configured - web aggregator scraping won't work
⚠️  No sources configured

Next steps:
1. Add API key to ~/.config/local-media-tools/.env
2. Add Firecrawl key to .env (if using web aggregators)
3. Configure sources in ~/.config/local-media-tools/sources.yaml
4. Run /newsletter-events:research to start scraping
```

**JSON output (with --json flag):**

For machine-readable output, run `scripts/validate_setup.py`:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/validate_setup.py
```

This returns structured JSON:
```json
{
  "config_dir": "/Users/you/.config/local-media-tools",
  "plugin_root": "/path/to/plugin",
  "runtimes": {
    "uv": {"installed": true, "version": "uv 0.5.1"},
    "bun": {"installed": true, "version": "1.1.34"}
  },
  "config": {
    "config_dir_exists": true,
    "env_exists": true,
    "api_key": {"configured": true},
    "firecrawl_key": {"required": false, "configured": true},
    "sources_yaml_exists": true
  },
  "directories": {
    "data_dir": true
  },
  "database": {
    "exists": true,
    "path": "/Users/you/.config/local-media-tools/data/events.db"
  },
  "ready": true
}
```

## Error Handling

| Error | Response |
|-------|----------|
| uv not installed | Provide install command, STOP |
| bun not installed | Provide install command, STOP |
| uv sync fails | Show error, suggest `rm -rf .venv && uv sync` |
| bun install fails | Show error, suggest `rm -rf node_modules && bun install` |
| .env missing | Copy from .env.example, then continue |
| API key missing | Warn but continue (optional for Facebook-only users) |
| Firecrawl key missing | Warn but continue (only needed for web aggregators) |
| sources.yaml missing | Copy from template, guide to configuration |
