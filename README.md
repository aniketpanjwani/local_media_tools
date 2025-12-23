# Local Media Tools

![Research output showing scraped events](assets/research-output.png)

A Claude Code plugin for scraping local events from Instagram and web sources, with support for ad-hoc Facebook event URLs.

**Created by [Aniket Panjwani](https://www.youtube.com/@aniketapanjwani)**

> 💡 **Non-technical?** [Book a consultation](https://tidycal.com/aniketpanjwani/local-media-tools-consultation) for guided setup. You'll leave ready to scrape events from any Instagram profile or webpage yourself.

## What It Does

Create hyper-local event newsletters by aggregating events from:
- **Instagram** - Public profiles via ScrapeCreators API
- **Facebook** - Direct event URLs (pass to `/research` command)
- **Web Aggregators** - Event listing websites via Firecrawl

Events are deduplicated, stored in SQLite, and formatted according to your preferences.

## Quick Start

```
/plugin marketplace add aniketpanjwani/local_media_tools
/plugin install newsletter-events
/newsletter-events:setup
```

Then:
1. Add API keys to `~/.config/local-media-tools/.env`
2. Add sources: `/newsletter-events:add-source`
3. Scrape events: `/newsletter-events:research`
4. Generate newsletter: `/newsletter-events:write`

**[Full Getting Started Guide](docs/getting-started.md)**

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | First newsletter in 10 minutes |
| [Configuration](docs/configuration.md) | Source setup and API keys |
| [Commands](docs/commands.md) | Complete command reference |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |

### Platform Guides

| [Instagram](docs/examples/instagram.md) | [Facebook](docs/examples/facebook.md) | [Web Aggregators](docs/examples/web-aggregator.md) |
|----------------------------------------|---------------------------------------|---------------------------------------------------|

### For Developers

| [Architecture](docs/architecture.md) | [Development](docs/development.md) | [Changelog](CHANGELOG.md) |
|-------------------------------------|-----------------------------------|---------------------------|

## Requirements

- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- [bun](https://bun.sh/) (for Facebook event scraping)
- [Claude Code](https://claude.com/claude-code)
- API keys: [ScrapeCreators](https://scrapecreators.com) (Instagram) or [Firecrawl](https://firecrawl.dev) (web)

## Output

- **Database:** `~/.config/local-media-tools/data/events.db`
- **Newsletters:** `newsletter_YYYY-MM-DD.md` in current directory

## Maintenance

Old plugin versions accumulate in `~/.claude/plugins/cache/` (~30-40MB each). To clean up:

```bash
# Remove all old versions, keep only current (check version in plugin.json first)
ls ~/.claude/plugins/cache/local-media-tools/newsletter-events/ | grep -v "CURRENT_VERSION" | xargs -I {} rm -rf ~/.claude/plugins/cache/local-media-tools/newsletter-events/{}
```

## Support

- **Issues:** [GitHub Issues](https://github.com/aniketpanjwani/local_media_tools/issues)
- **Email:** [aniket@contentquant.io](mailto:aniket@contentquant.io)
- **YouTube:** [@aniketapanjwani](https://www.youtube.com/@aniketapanjwani)
- **Consultation:** [Book a guided setup session](https://tidycal.com/aniketpanjwani/local-media-tools-consultation)

## Author

**Aniket Panjwani, PhD** - Building AI solutions for small businesses. [Schedule a Growth Mapping Call](https://tidycal.com/aniketpanjwani/growth-mapping-call).

## License

MIT
