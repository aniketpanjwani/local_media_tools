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

## Agents

| Agent | Description |
|-------|-------------|
| `config-validator` | Validates plugin configuration before research |

---

[Back to Documentation](README.md)
