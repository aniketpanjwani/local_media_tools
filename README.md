# Local Media Tools

A Claude Code plugin for scraping local events from Instagram, Facebook, and web sources. Get structured JSON data for your own workflows.

**Created by [Aniket Panjwani](https://www.youtube.com/@aniketapanjwani)**

## About

Local Media Tools scrapes event data from configured sources and outputs structured JSON. You configure your sources (Instagram accounts, Facebook pages, web aggregators), run `/research`, and get deduplicated event data.

### What It Does

1. **Scrape Instagram** - Public profiles via ScrapeCreators API
2. **Scrape Facebook** - Event pages and location-based discovery
3. **Scrape Web Aggregators** - Event listing websites via Firecrawl
4. **Deduplicate** - Fuzzy matching to merge duplicate events
5. **Output JSON** - Structured event data at `tmp/extraction/events.json`

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
3. Configuring your API keys

### After Setup

1. **Get API key** at [scrapecreators.com](https://scrapecreators.com) (required for Instagram)
2. **Add key** to `.env`: `SCRAPECREATORS_API_KEY=your_key`
3. **Configure sources** in `config/sources.yaml` (copy from `sources.example.yaml`)
4. **Run scraping**: `/research`

### Manual Installation (Advanced)

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

```bash
# Scrape all configured sources
claude /research

# Setup environment
claude /setup

# Configure Facebook location discovery
claude /setup-location
```

## Configuration

Edit `config/sources.yaml` (see `sources.example.yaml` for full documentation):

```yaml
newsletter:
  name: "My Local Events"
  region: "Hudson Valley, NY"

sources:
  instagram:
    enabled: true
    accounts:
      - handle: "local_venue"
        name: "Local Venue"
        type: "music_venue"
        location: "Kingston, NY"

  facebook:
    enabled: true
    pages:
      - url: "https://facebook.com/venue/events"
        name: "The Venue"
    # Location-based discovery (requires Chrome MCP + Facebook login)
    locations:
      - location_id: "111841478834264"
        location_name: "Medellín, Antioquia"
        date_filter: "THIS_WEEK"

  web_aggregators:
    enabled: true
    sources:
      - url: "https://localevents.com"
        name: "Local Events"
        source_type: "listing"
```

### Setting Up Facebook Location Discovery

Facebook location-based discovery uses Chrome MCP to scrape Facebook's events page while logged in:

1. **Install Chrome MCP Server** and ensure it's running
2. **Log into Facebook** in Chrome
3. **Run the setup command**: `/setup-location`

## Output

Scraped events are saved to `tmp/extraction/events.json`:

```json
{
  "events": [
    {
      "title": "Live Music Night",
      "venue": {"name": "Local Venue", "city": "Kingston"},
      "event_date": "2024-01-15",
      "start_time": "20:00",
      "source": "instagram",
      "confidence": 0.9
    }
  ],
  "schema_version": "1.0.0",
  "scraped_at": "2024-01-10T12:00:00Z"
}
```

## Project Structure

```
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── commands/
│   ├── research.md         # /research - Scrape all sources
│   ├── setup.md            # /setup - Environment setup
│   └── setup-location.md   # /setup-location - Facebook location setup
├── skills/
│   ├── newsletter-events-research/   # Event scraping workflows
│   └── newsletter-events-setup/      # Environment setup
├── config/
│   ├── config_schema.py    # Pydantic config models
│   └── sources.example.yaml
├── schemas/
│   ├── event.py            # Event/Venue Pydantic models
│   └── storage.py          # Atomic file I/O
├── scripts/
│   ├── scrape_instagram.py # ScrapeCreators API client
│   ├── scrape_facebook.js  # Facebook page scraper (bun/Node.js)
│   ├── scrape_firecrawl.py # Web aggregator scraper
│   ├── facebook_bridge.py  # Python-to-JS subprocess bridge
│   ├── facebook_discover.py # Facebook location-based utilities
│   └── deduplicate.py      # Fuzzy matching deduplication
├── tests/
└── tmp/                    # Working directory (gitignored)
    └── extraction/         # Raw data, images, events.json
```

## Limitations

**Facebook page scraper:** Uses [facebook-event-scraper](https://github.com/francescov1/facebook-event-scraper) which scrapes public pages without an official API. This can be unreliable:
- Only works for public events
- May break when Facebook changes their HTML structure
- Rate limiting and bot detection may block requests

**Facebook location discovery:** Uses Chrome MCP to scrape while logged in:
- Requires Chrome browser with active Facebook session
- Requires Chrome MCP Server to be running
- Events discovered have sparse data and are marked for review

**Instagram scraper:** Requires a paid ScrapeCreators API key. Rate limits apply per your plan.

**Web aggregators:** Requires a Firecrawl API key. Only needed if using web aggregator sources.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Install dependencies manually
uv sync
bun install
```

## Support & Contact

- **Email:** [aniket@contentquant.io](mailto:aniket@contentquant.io)
- **YouTube:** [@aniketapanjwani](https://www.youtube.com/@aniketapanjwani)

## Author

**Aniket Panjwani** - Building tools for local media and hyperlocal journalism.

## License

MIT
