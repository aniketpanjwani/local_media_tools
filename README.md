# Local Media Tools

A Claude Code plugin providing AI-powered skills for local media publications. Automate event curation, content research, and newsletter generation for hyperlocal journalism.

**Created by [Aniket Panjwani](https://www.youtube.com/@aniketapanjwani)**

## About

Local Media Tools is a collection of Claude Code skills designed specifically for local media publications—community newsletters, hyperlocal news sites, and regional event guides. The plugin automates tedious research and curation tasks so publishers can focus on storytelling.

### Current Skills

**Newsletter Events** - Automated local events newsletter generation:
1. **Discover** - Find Instagram and Facebook event sources for any city
2. **Research** - Scrape configured sources for upcoming events (including location-based Facebook discovery)
3. **Deduplicate** - Use fuzzy matching to merge duplicate events
4. **Write** - Generate a formatted markdown newsletter grouped by day

*More skills coming soon.*

## Quick Start

### Installation

```bash
/plugin marketplace add https://github.com/aniketpanjwani/local_media_tools
/plugin install local-media-tools
/setup
```

The `/setup` command will guide you through:
1. Installing runtime dependencies (uv, bun)
2. Installing Python and Node packages
3. Configuring your API key
4. Finding event sources for your city

### After Setup

1. **Get API key** at [scrapecreators.com](https://scrapecreators.com) (required for Instagram)
2. **Add key** to `.env`: `SCRAPECREATORS_API_KEY=your_key`
3. **Discover sources** for your city: `/discover Portland, Oregon`
4. **Start researching**: `/research`

### Manual Installation (Advanced)

For development or offline use:

```bash
git clone https://github.com/aniketpanjwani/local_media_tools
cd local_media_tools
./scripts/setup.sh
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [bun](https://bun.sh/) - JavaScript runtime (for Facebook page scraping)
- [Claude Code](https://claude.com/claude-code) - CLI tool
- [Chrome MCP Server](https://github.com/anthropics/anthropic-quickstarts/tree/main/mcp-servers/chrome) - For Facebook location-based discovery (optional)

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

This is a Claude Code plugin with the following structure:

```
├── .claude-plugin/
│   ├── plugin.json         # Plugin manifest
│   ├── marketplace.json    # Marketplace catalog for /plugin install
│   └── hooks.json          # Post-install automation hooks
├── commands/               # Slash commands
│   ├── discover.md         # /discover - Find sources for a city
│   ├── research.md         # /research - Scrape all sources
│   ├── write.md            # /write - Generate newsletter
│   ├── full-run.md         # /full-run - Research + write
│   ├── setup.md            # /setup - Environment setup
│   └── setup-location.md   # /setup-location - Configure Facebook location_id
├── skills/                 # Claude Code skills
│   ├── newsletter-events-discover/   # Source discovery for new cities
│   ├── newsletter-events-research/   # Event scraping workflows
│   ├── newsletter-events-setup/      # Environment setup
│   └── newsletter-events-write/      # Newsletter generation
├── agents/                 # Proactive agents
│   └── config-validator.md # Validates config before research
├── config/
│   ├── config_schema.py    # Pydantic config models
│   └── sources.example.yaml
├── schemas/
│   ├── event.py            # Event/Venue Pydantic models
│   └── storage.py          # Atomic file I/O
├── scripts/
│   ├── post-install.sh     # Post-install hook (creates dirs, copies templates)
│   ├── validate_setup.py   # Machine-readable setup validation
│   ├── scrape_instagram.py # ScrapeCreators API client
│   ├── scrape_facebook.js  # Facebook page scraper (bun/Node.js)
│   ├── facebook_bridge.py  # Python-to-JS subprocess bridge
│   ├── facebook_discover.py # Facebook location-based discovery utilities
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
    # Scrape specific Facebook pages
    pages:
      - url: "https://facebook.com/venue/events"
        name: "The Venue"
    # Location-based discovery (requires Chrome MCP + Facebook login)
    locations:
      - location_id: "111841478834264"
        location_name: "Medellín, Antioquia"
        date_filter: "THIS_WEEK"  # or THIS_WEEKEND, THIS_MONTH
```

### Setting Up Facebook Location Discovery

Facebook location-based discovery uses Chrome MCP to scrape Facebook's events page while logged in. To configure:

1. **Install Chrome MCP Server** and ensure it's running
2. **Log into Facebook** in Chrome
3. **Run the setup command**:
   ```bash
   claude /setup-location
   ```
   This will guide you through finding your city's `location_id` and save it to config.

## Output

Generated newsletters are saved to `output/newsletter_YYYY-MM-DD.md` with:

- Events grouped by day
- Venue, time, and ticket information
- Links to original sources
- Flagged items needing manual review

## Limitations

**Facebook page scraper:** Uses [facebook-event-scraper](https://github.com/francescov1/facebook-event-scraper) which scrapes public pages without an official API. This can be unreliable:
- Only works for public events
- May break when Facebook changes their HTML structure
- Rate limiting and bot detection may block requests
- Some pages may require proxy configuration for heavy use

**Facebook location discovery:** Uses Chrome MCP to scrape while logged in:
- Requires Chrome browser with active Facebook session
- Requires Chrome MCP Server to be running
- `location_id` must be configured manually (one-time setup per city)
- Events discovered have sparse data (title, date, venue) and are marked for review

**Instagram scraper:** Requires a paid ScrapeCreators API key. Rate limits apply per your plan.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Install dependencies manually
uv sync
bun install
```

## Support & Contact

Need help using this plugin or want to request new features?

- **Email:** [aniket@contentquant.io](mailto:aniket@contentquant.io)
- **YouTube:** [@aniketapanjwani](https://www.youtube.com/@aniketapanjwani)

## Author

**Aniket Panjwani** - Building tools for local media and hyperlocal journalism.

## License

MIT
