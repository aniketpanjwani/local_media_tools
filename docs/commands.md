# Commands Reference

All commands use the `/newsletter-events:` prefix.

## Core Commands

### /newsletter-events:setup

Set up or verify the plugin environment.

```
/newsletter-events:setup
```

**What it does:**
- Installs runtime dependencies (uv, bun)
- Installs Python and Node packages
- Creates config directory at `~/.config/local-media-tools/`
- Validates API keys in `.env`

**When to use:** First-time setup or after plugin updates.

---

### /newsletter-events:research

Scrape events from all configured sources, plus any ad-hoc Facebook event URLs.

```
/newsletter-events:research
```

Or with Facebook event URLs:

```
/newsletter-events:research https://facebook.com/events/123456789
```

**What it does:**
- Reads sources from `~/.config/local-media-tools/sources.yaml`
- Scrapes Instagram profiles via ScrapeCreators API
- Scrapes web aggregators via Firecrawl
- Scrapes any Facebook event URLs passed directly
- Deduplicates venues using fuzzy matching
- Stores results in SQLite database

**Output:** Events stored in `~/.config/local-media-tools/data/events.db`

**Duration:** 1-5 minutes depending on source count.

---

### /newsletter-events:write

Generate a newsletter from scraped events.

```
/newsletter-events:write
```

**What it does:**
- Reads events from SQLite database
- Filters by date range (configurable)
- Formats according to `formatting_preferences` in sources.yaml
- Outputs markdown newsletter

**Output:** `newsletter_YYYY-MM-DD.md` in current directory.

---

## Source Management

### /newsletter-events:add-source

Add a new event source interactively.

```
/newsletter-events:add-source
```

**What it does:**
- Prompts for source type (Instagram or Web)
- Collects required information
- Adds to `sources.yaml`
- Validates configuration

**Note:** Facebook events are not configured here. Pass Facebook event URLs directly to `/research` instead.

---

### /newsletter-events:list-sources

View all configured sources.

```
/newsletter-events:list-sources
```

**Output:** Table of configured sources with type, name, and status.

---

### /newsletter-events:remove-source

Remove a source from configuration.

```
/newsletter-events:remove-source
```

**What it does:**
- Shows list of configured sources
- Prompts for source to remove
- Updates `sources.yaml`

---

### /newsletter-events:update-event

Refresh specific event page(s) to update event data.

```
/newsletter-events:update-event https://example.com/events/jazz-night
```

**What it does:**
- Re-scrapes the specified URL(s)
- Extracts events from the page content
- Updates existing events in database (or creates new ones)
- Updates the scraped timestamp

**When to use:**
- Event details have changed (date, time, venue)
- You want to verify event data is current
- Events weren't extracted correctly on first scrape

**Note:** Web aggregator URLs are tracked to avoid re-scraping. This command
bypasses that to force a refresh.

---

## Skills

Skills are workflows that can be triggered by Claude when relevant.

| Skill | Description |
|-------|-------------|
| `newsletter-events-setup` | Environment setup and verification |
| `newsletter-events-research` | Event scraping from all sources |
| `newsletter-events-write` | Newsletter generation |
| `newsletter-events-add-source` | Add sources interactively |
| `newsletter-events-list-sources` | Display configured sources |
| `newsletter-events-remove-source` | Remove sources |
| `newsletter-events-update-event` | Refresh specific event pages |

## Agents

| Agent | Description |
|-------|-------------|
| `config-validator` | Validates plugin configuration before research |

---

## CLI Tools

These Python CLI tools are used internally by the plugin. They can be run manually for debugging or advanced usage.

All commands are run from the plugin directory:
```bash
PLUGIN_DIR=$(cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath')
cd "$PLUGIN_DIR" && uv run python scripts/<script>.py <command>
```

### cli_web.py

Web aggregator scraping and page management.

| Command | Description |
|---------|-------------|
| `discover --all` | Preview URLs that would be scraped (no scraping) |
| `scrape --all --limit N` | Scrape all web sources, save to raw files |
| `list-pages` | List scraped pages with index numbers |
| `read-page --source "Name" --index N` | Read one page's markdown content |
| `mark-scraped --source "Name" --url "URL" --events-count N` | Mark URL as processed |
| `show-stats` | Show scraping statistics |

**Why page-by-page?** Large scrapes (40+ pages) can exceed Claude's token limits when read all at once. The `list-pages` → `read-page` pattern processes one page at a time to avoid this.

### cli_instagram.py

Instagram scraping and post management.

| Command | Description |
|---------|-------------|
| `scrape --all` | Scrape all configured Instagram accounts |
| `scrape --handle <handle>` | Scrape specific account |
| `list-posts --handle <handle>` | List posts from database |
| `classify --post-id <id> --classification <type>` | Classify a post |
| `show-stats` | Show Instagram statistics |

### cli_events.py

Event database management.

| Command | Description |
|---------|-------------|
| `save --json '{...}'` | Save a single event to database |
| `save-batch --file events.json` | Save multiple events from JSON file |
| `query --days N` | Query events by date range |
| `stats` | Show event database statistics |

---

[Back to Documentation](README.md)
