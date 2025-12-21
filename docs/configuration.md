# Configuration Guide

All configuration is stored in `~/.config/local-media-tools/`. This location persists across plugin upgrades.

## Directory Structure

```
~/.config/local-media-tools/
├── .env                    # API keys
├── sources.yaml            # Event source configuration
└── data/
    ├── events.db           # SQLite database of scraped events
    ├── raw/                # Raw API responses
    └── images/             # Downloaded event images
```

## Environment Variables (.env)

Create or edit `~/.config/local-media-tools/.env`:

```bash
# Required for Instagram scraping
SCRAPECREATORS_API_KEY=your_key_here

# Required for web aggregator scraping
FIRECRAWL_API_KEY=your_key_here
```

**Get API keys:**
- ScrapeCreators: [scrapecreators.com](https://scrapecreators.com)
- Firecrawl: [firecrawl.dev](https://firecrawl.dev)

## Sources Configuration (sources.yaml)

The primary configuration file. Use `/newsletter-events:add-source` to add sources interactively, or edit directly.

### Newsletter Settings

```yaml
newsletter:
  name: "My Local Events"      # Project name
  region: "Hudson Valley, NY"  # Target region
  formatting_preferences: |
    Organize events by date with each day as a section header.
    Format dates like "Saturday, January 20".
    Use emojis for categories: music, art, food.
```

### Formatting Preferences

The `formatting_preferences` field accepts natural language instructions. Claude interprets these when generating newsletters with `/newsletter-events:write`.

**Example styles:**

```yaml
# Minimal
formatting_preferences: |
  Organize by date. Simple formatting, no emojis.
  Just event name, venue, and time.

# Detailed with links
formatting_preferences: |
  Format: **Title** @ Venue | Time | Price
  Include [Get Tickets](ticket_url) links when available.
  Include [Source](source_url) for attribution.
  Use emojis for categories.

# By category
formatting_preferences: |
  Organize by category (Music, Art, Food, Community).
  Within each category, sort by date.
  Use bullet points with essentials only.
```

### Available Fields for Formatting

When writing `formatting_preferences`, you can reference these fields:

| Field | Description | Example Value |
|-------|-------------|---------------|
| `title` | Event name | "Jazz Night" |
| `venue` | Venue name | "The Blue Note" |
| `venue_city` | Venue city | "Kingston" |
| `date` | ISO date | "2025-01-20" |
| `day_of_week` | Full day name | "Saturday" |
| `formatted_date` | Human-readable | "January 20" |
| `time` | Start time | "8:00 PM" |
| `description` | Event description | "Live jazz trio..." |
| `category` | Category | "music", "art", "food_drink" |
| `price` | Price or "Free" | "$15" |
| `ticket_url` | Buy tickets link | URL or empty |
| `event_url` | Event page link | URL or empty |
| `source_url` | Original source | Instagram post, Facebook event, or web page URL |

**About `source_url`:** This is where the event was originally found:
- **Instagram** → the Instagram post URL
- **Facebook** → the Facebook event page URL
- **Web aggregators** → the scraped page URL

Use it for attribution: `Include [Source](source_url) for each event.`

### Adding Sources

Sources are organized by platform under the `sources` key:

```yaml
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

  web_aggregators:
    enabled: true
    sources:
      - url: "https://localevents.com"
        name: "Local Events"
        source_type: "listing"
```

See platform-specific guides for detailed configuration:
- [Instagram Setup](examples/instagram.md)
- [Facebook Setup](examples/facebook.md)
- [Web Aggregators](examples/web-aggregator.md)

### Filters

Control which events are included:

```yaml
filters:
  date_range:
    start: "today"     # Start date (today, tomorrow, or YYYY-MM-DD)
    end: "+7days"      # End date (relative or absolute)
  categories: []       # Empty = all categories
  exclude_keywords:
    - "cancelled"
    - "postponed"
```

### Storage Settings

```yaml
storage:
  backend: sqlite      # sqlite (default) or json (legacy)
  auto_backup: true    # Backup before migrations
```

## Complete Example

See [config/sources.example.yaml](../config/sources.example.yaml) for a fully documented configuration template with all available options.

## Validating Configuration

After editing `sources.yaml`, run:

```
/newsletter-events:list-sources
```

This displays your configured sources and highlights any issues.

---

[Back to Documentation](README.md)
