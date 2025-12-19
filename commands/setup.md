---
name: setup
description: Set up or verify Local Media Tools environment (runtimes, dependencies, config)
---

# Setup Local Media Tools

Interactive setup wizard that verifies and configures everything needed to use the plugin.

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
> Then restart your terminal and run `/setup` again.

**If bun missing:**
> bun (JavaScript runtime) is not installed.
>
> Install with: `curl -fsSL https://bun.sh/install | bash`
>
> Then restart your terminal and run `/setup` again.

**STOP HERE if runtimes missing.** User must install them first.

### Step 2: Install Dependencies

```bash
cd ${CLAUDE_PLUGIN_ROOT}
uv sync
bun install
```

Report success/failure clearly. If failure, show the error and suggest fixes.

### Step 3: Check Configuration Files

**Check .env and API key:**
```bash
[ -f .env ] && echo "EXISTS" || echo "MISSING"
grep -q "SCRAPECREATORS_API_KEY=." .env 2>/dev/null && \
  ! grep -q "SCRAPECREATORS_API_KEY=your_api_key_here" .env 2>/dev/null && \
  echo "KEY_SET" || echo "KEY_MISSING"
```

**If API key not set:**
> API key required for Instagram scraping.
>
> 1. Sign up at https://scrapecreators.com
> 2. Get your API key from the dashboard
> 3. Edit `.env` and replace the placeholder:
>    ```
>    SCRAPECREATORS_API_KEY=your_actual_key_here
>    ```
>
> Note: Use an editor, not command line, to avoid saving the key in shell history.

**Check sources.yaml:**
```bash
[ -f config/sources.yaml ] && echo "EXISTS" || echo "MISSING"
```

**If sources.yaml is still template:**
> No event sources configured yet.
>
> Run `/discover [your city]` to find Instagram and Facebook event sources.
> Example: `/discover Portland, Oregon`

### Step 4: Summary

**Human-readable output:**
```
Local Media Tools Setup Status
==============================
✅ uv installed (v0.5.x)
✅ bun installed (v1.x.x)
✅ Python dependencies installed
✅ Node dependencies installed
⚠️  API key not configured - Instagram scraping won't work
⚠️  No sources configured - run /discover [city]

Next steps:
1. Add API key to .env
2. Run /discover [city] to find event sources
3. Run /research to start scraping
```

**JSON output (with --json flag):**

For machine-readable output, run `scripts/validate_setup.py`:

```bash
python scripts/validate_setup.py
```

This returns structured JSON:
```json
{
  "status": "partial",
  "checks": {
    "uv_installed": {"passed": true, "version": "0.5.1"},
    "bun_installed": {"passed": true, "version": "1.1.34"},
    "python_deps": {"passed": true},
    "node_deps": {"passed": true},
    "api_key_set": {"passed": false, "action": "Add SCRAPECREATORS_API_KEY to .env"},
    "sources_configured": {"passed": false, "action": "Run /discover [city]"}
  },
  "ready": false,
  "next_steps": [
    "Add API key to .env",
    "Run /discover [city] to find event sources"
  ]
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
| sources.yaml missing | Copy from template, guide to /discover |
