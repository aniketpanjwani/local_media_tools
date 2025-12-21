# Architecture

Technical overview of Local Media Tools for contributors and curious users.

## Design Philosophy

Local Media Tools is designed as a **Claude Code plugin** that augments Claude's capabilities with local event scraping. The architecture prioritizes:

1. **Simplicity** - Minimal dependencies, straightforward data flow
2. **Reliability** - SQLite for persistence, graceful error handling
3. **Extensibility** - Easy to add new source types
4. **Separation** - User config persists across plugin upgrades

## Dual Runtime Design

The plugin uses two runtimes:

| Runtime | Purpose | Components |
|---------|---------|------------|
| **Python** | Primary | ScrapeCreators API, Firecrawl, SQLite, deduplication |
| **Node.js** | Secondary | Facebook event scraping (via subprocess) |

**Why two runtimes?**
- Python has better data processing libraries (Pydantic, SQLite)
- The facebook-event-scraper npm package is the most reliable Facebook scraper
- Python calls Node.js via subprocess when needed

## Data Flow

```
Sources (Instagram, Web) + Ad-hoc URLs (Facebook)
         ↓
    Scrapers (Python/Node.js)
         ↓
    Event Extraction (Claude vision for images)
         ↓
    Deduplication (fuzzy venue matching)
         ↓
    SQLite Storage (events.db)
         ↓
    Newsletter Generation (Claude formatting)
         ↓
    Markdown Output
```

## Directory Structure

### Plugin Directory (managed by Claude Code)

```
~/.claude/plugins/cache/local-media-tools/newsletter-events/{version}/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── commands/               # Slash command definitions
├── skills/                 # Skill workflows
├── scripts/                # Python/JS scrapers
├── schemas/                # Pydantic models
└── config/                 # Default configuration templates
```

### User Config Directory (persists across upgrades)

```
~/.config/local-media-tools/
├── .env                    # API keys
├── sources.yaml            # Event source configuration
└── data/
    ├── events.db           # SQLite database
    ├── raw/                # Raw API responses (for debugging)
    └── images/             # Downloaded event images
```

## Database Schema

SQLite database with four main tables:

```sql
-- Profiles: Instagram accounts, Facebook pages
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE,
    platform TEXT,  -- instagram, facebook
    name TEXT,
    type TEXT,      -- music_venue, promoter, aggregator
    location TEXT
);

-- Venues: Deduplicated event locations
CREATE TABLE venues (
    id INTEGER PRIMARY KEY,
    name TEXT,
    normalized_name TEXT,  -- for fuzzy matching
    address TEXT,
    instagram_handle TEXT,
    facebook_url TEXT
);

-- Events: Individual events
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER REFERENCES venues(id),
    title TEXT,
    date DATE,
    time TEXT,
    description TEXT,
    price TEXT,
    ticket_url TEXT,
    source TEXT,      -- instagram, facebook, web
    source_post_id TEXT,
    created_at TIMESTAMP
);

-- Posts: Instagram posts that may contain multiple events
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id),
    post_id TEXT UNIQUE,
    content TEXT,
    image_paths TEXT,  -- JSON array
    scraped_at TIMESTAMP
);
```

## Key Components

### scripts/paths.py

Centralized path resolver. All file paths go through this module:

```python
from scripts.paths import get_config_path, get_data_path

config = get_config_path("sources.yaml")
db = get_data_path("events.db")
```

### scripts/scrape_instagram.py

ScrapeCreators API client:
- Fetches recent posts for configured profiles
- Downloads images locally (Instagram CDN blocks external requests)
- Returns structured post data for Claude to extract events

### scripts/facebook_bridge.py

Python-to-Node.js subprocess bridge:
- Calls `scripts/scrape_facebook.js` via bun/node
- Scrapes individual Facebook event URLs (ad-hoc, not configured)
- Parses JSON output from Node.js
- Handles subprocess errors gracefully

### schemas/sqlite_storage.py

SQLite backend:
- Schema migrations on startup
- Venue deduplication (85% fuzzy match threshold)
- Upsert logic for events and venues
- Query methods for newsletter generation

### schemas/event.py

Pydantic models for type safety:

```python
class Event(BaseModel):
    title: str
    venue: str
    date: date
    time: Optional[str]
    description: Optional[str]
    price: Optional[str]
    ticket_url: Optional[str]
    source: Literal["instagram", "facebook", "web"]
```

## Plugin Structure

### Commands (commands/*.md)

Slash command definitions that map to skills:

```markdown
---
name: newsletter-events:research
description: Scrape events from configured sources
---
# Research Events
Run the newsletter-events-research skill.
```

### Skills (skills/*/SKILL.md)

Workflow definitions with routing logic:

```markdown
# newsletter-events-research

<routing>
| Condition | Workflow |
|-----------|----------|
| Instagram sources exist | workflows/instagram.md |
| Facebook sources exist | workflows/facebook.md |
</routing>
```

### Agents (agents/*.yaml)

Proactive agents that run automatically:

```yaml
name: config-validator
trigger: before_research
description: Validate configuration before scraping
```

## Extending the Plugin

### Adding a New Source Type

1. Create scraper in `scripts/scrape_{source}.py`
2. Add source config schema in `config/config_schema.py`
3. Update research skill routing in `skills/newsletter-events-research/SKILL.md`
4. Add example config in `config/sources.example.yaml`

### Adding a New Command

1. Create `commands/{command}.md` with frontmatter
2. Create or update skill in `skills/`
3. Update docs in `docs/commands.md`

---

[Back to Documentation](README.md)
