# Newsletter Events

A Claude Code plugin for automated local newsletter generation. Scrapes events from Instagram and Facebook, deduplicates across sources, and generates formatted markdown newsletters.

## Purpose

This tool automates the full lifecycle of creating a local events newsletter:

1. **Discover** - Find Instagram and Facebook event sources for any city
2. **Research** - Scrape configured sources for upcoming events
3. **Deduplicate** - Use fuzzy matching to merge duplicate events
4. **Write** - Generate a formatted markdown newsletter grouped by day

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [bun](https://bun.sh/) - JavaScript runtime (for Facebook scraping)
- [Claude Code](https://claude.com/claude-code) - CLI tool

## Setup

1. **Clone and install dependencies:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your SCRAPECREATORS_API_KEY
   ```

   Get a ScrapeCreators API key at [scrapecreators.com](https://scrapecreators.com). See their [API docs](https://scrapecreators.com/docs) for pricing and usage limits.

3. **Configure sources:**
   ```bash
   cp config/sources.example.yaml config/sources.yaml
   # Edit sources.yaml with your venues and accounts
   ```

## Usage

Run commands via Claude Code:

```bash
# Discover sources for a new city
claude /discover Winnipeg, Manitoba, Canada

# Full workflow: research + write
claude /full-run

# Or run phases separately:
claude /research    # Scrape all sources
claude /write       # Generate newsletter from collected events

# With custom title:
claude /full-run "Hudson Valley Weekend Events"
```

### Starting a New Newsletter

1. **Discover sources** for your city:
   ```bash
   claude /discover "Portland, Oregon, USA"
   ```
   This searches for local venues, promoters, and event aggregators, then generates a YAML config snippet.

2. **Add sources** to `config/sources.yaml`

3. **Research and write**:
   ```bash
   claude /full-run
   ```

## Project Structure

```
├── .claude/
│   ├── commands/           # Slash commands (/discover, /research, /write, etc.)
│   └── skills/             # Claude Code skills
│       ├── newsletter-events-discover/   # Source discovery for new cities
│       ├── newsletter-events-research/   # Event scraping workflows
│       ├── newsletter-events-setup/      # Environment setup
│       └── newsletter-events-write/      # Newsletter generation
├── config/
│   ├── config_schema.py    # Pydantic config models
│   └── sources.example.yaml
├── schemas/
│   ├── event.py            # Event/Venue Pydantic models
│   └── storage.py          # Atomic file I/O
├── scripts/
│   ├── scrape_instagram.py # ScrapeCreators API client
│   ├── scrape_facebook.js  # Facebook scraper (bun/Node.js)
│   ├── facebook_bridge.py  # Python-to-JS subprocess bridge
│   ├── deduplicate.py      # Fuzzy matching deduplication
│   └── generate_newsletter.py
├── templates/
│   └── newsletter.md.j2    # Jinja2 newsletter template
├── tests/
└── tmp/                    # Working directory (gitignored)
    └── extraction/         # Raw data, images, events.json
```

## Configuration

Edit `config/sources.yaml`:

```yaml
newsletter:
  name: "My Local Events"
  region: "Hudson Valley, NY"

sources:
  instagram:
    enabled: true
    accounts:
      - handle: "venue_instagram"
        name: "The Venue"
        type: "venue"

  facebook:
    enabled: true
    pages:
      - url: "https://facebook.com/venue/events"
        name: "The Venue"
```

## Output

Generated newsletters are saved to `output/newsletter_YYYY-MM-DD.md` with:

- Events grouped by day
- Venue, time, and ticket information
- Links to original sources
- Flagged items needing manual review

## Limitations

**Facebook scraper:** Uses [facebook-event-scraper](https://github.com/francescov1/facebook-event-scraper) which scrapes public pages without an official API. This can be unreliable:
- Only works for public events
- May break when Facebook changes their HTML structure
- Rate limiting and bot detection may block requests
- Some pages may require proxy configuration for heavy use

**Instagram scraper:** Requires a paid ScrapeCreators API key. Rate limits apply per your plan.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Install dependencies manually
uv sync
bun install
```

## License

MIT
