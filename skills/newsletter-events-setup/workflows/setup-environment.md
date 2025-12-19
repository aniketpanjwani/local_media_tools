# Workflow: Setup Environment

<process>
## Step 1: Run Bootstrap Script

```bash
./scripts/setup.sh
```

This will:
- Install `uv` if missing
- Install `bun` if missing
- Run `uv sync` for Python dependencies
- Run `bun install` for Node.js dependencies
- Create tmp directories
- Copy `.env.example` to `.env` if needed

## Step 2: Configure API Keys

Edit `.env` and add your ScrapeCreators API key:

```
SCRAPECREATORS_API_KEY=your_key_here
```

Get a key at https://scrapecreators.com

## Step 3: Configure Sources

Copy the example config:

```bash
cp config/sources.example.yaml config/sources.yaml
```

Edit `config/sources.yaml` to add your Instagram accounts and Facebook pages.

## Step 4: Verify Installation

Run verification checks:

```bash
# Check uv
uv --version

# Check bun
bun --version

# Check Python imports
uv run python -c "import rapidfuzz; import pydantic; import structlog; print('OK')"

# Check Node.js
bun run scripts/scrape_facebook.js --help
```
</process>

<success_criteria>
Setup is complete when:
- [ ] All verification commands pass
- [ ] `.env` contains valid API key
- [ ] `config/sources.yaml` exists with at least one source
</success_criteria>
