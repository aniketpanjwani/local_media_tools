# Development Guide

How to set up a development environment and contribute to Local Media Tools.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [bun](https://bun.sh/) - JavaScript runtime
- [Claude Code](https://claude.com/claude-code) - for testing plugin behavior

## Setup

### Clone the Repository

```bash
git clone https://github.com/aniketpanjwani/local_media_tools
cd local_media_tools
```

### Install Dependencies

```bash
# Python dependencies
uv sync

# Node.js dependencies
bun install
```

### Create Test Configuration

```bash
# Copy example config
mkdir -p ~/.config/local-media-tools
cp config/sources.example.yaml ~/.config/local-media-tools/sources.yaml

# Add API keys for testing
echo "SCRAPECREATORS_API_KEY=your_test_key" >> ~/.config/local-media-tools/.env
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_storage.py -v

# Run with coverage
uv run pytest tests/ --cov=scripts --cov=schemas
```

## Code Style

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Format code
uv run ruff format .

# Check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix
```

## Project Structure

```
├── .claude-plugin/         # Plugin manifest
│   └── plugin.json
├── commands/               # Slash command definitions (.md)
├── skills/                 # Skill workflows
│   └── */
│       ├── SKILL.md       # Skill entry point
│       ├── workflows/     # Step-by-step procedures
│       └── references/    # API documentation
├── agents/                 # Proactive agent definitions
├── scripts/                # Python/JS implementation
│   ├── paths.py           # Path resolver
│   ├── scrape_*.py        # Scrapers
│   └── *.js               # Node.js scrapers
├── schemas/                # Pydantic models
├── config/                 # Configuration schemas and examples
├── tests/                  # Pytest test suite
└── docs/                   # User documentation
```

## Making Changes

### Adding a New Scraper

1. Create `scripts/scrape_{source}.py`:
   ```python
   def scrape(config: dict) -> list[dict]:
       """Scrape events from source."""
       # Implementation
       return events
   ```

2. Add config schema in `config/config_schema.py`:
   ```python
   class NewSourceConfig(BaseModel):
       enabled: bool = True
       # source-specific fields
   ```

3. Update research skill routing in `skills/newsletter-events-research/SKILL.md`

4. Add tests in `tests/test_scrape_{source}.py`

### Modifying Database Schema

1. Add migration logic in `schemas/sqlite_storage.py`:
   ```python
   def _migrate_to_v{N}(self):
       """Migration from v{N-1} to v{N}."""
       # ALTER TABLE statements
   ```

2. Update schema version constant

3. Test migration with existing database

### Updating Commands

1. Edit command definition in `commands/{name}.md`
2. Update skill if workflow changes
3. Update `docs/commands.md`

## Testing Locally

### Test Plugin Installation

```bash
# From the plugin directory
claude /plugin install newsletter-events

# Verify installation
claude /newsletter-events:setup
```

### Test Individual Scrapers

```bash
# Instagram
uv run python scripts/scrape_instagram.py --handle "test_handle"

# Facebook
bun run scripts/scrape_facebook.js "https://facebook.com/venue/events"

# Firecrawl
uv run python scripts/scrape_firecrawl.py --url "https://example.com/events"
```

### Test Database Operations

```python
from schemas.sqlite_storage import SQLiteStorage

storage = SQLiteStorage()
events = storage.get_events(days=7)
```

## Pull Request Guidelines

1. **Branch from main:** `git checkout -b feature/your-feature`

2. **Write tests:** New features should have test coverage

3. **Follow code style:** Run `uv run ruff format .` before committing

4. **Update docs:** If changing user-facing behavior, update relevant docs

5. **Describe changes:** PR description should explain what and why

### Commit Message Format

```
type(scope): description

Examples:
feat(instagram): add rate limit handling
fix(facebook): handle missing event dates
docs: update troubleshooting guide
test: add storage migration tests
```

## Releasing

1. Update version in `.claude-plugin/plugin.json`
2. Update CHANGELOG (if exists)
3. Create PR to main
4. After merge, tag release: `git tag v0.9.6`
5. Push tag: `git push origin v0.9.6`

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/aniketpanjwani/local_media_tools/issues)
- **Email:** [aniket@contentquant.io](mailto:aniket@contentquant.io)

---

[Back to Documentation](README.md)
