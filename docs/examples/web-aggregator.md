# Web Aggregator Setup

Scrape event listings from websites using the Firecrawl API.

## Prerequisites

- [Firecrawl API key](https://firecrawl.dev) (has free tier)
- Website with scrapeable event listings

## API Key Setup

1. Sign up at [firecrawl.dev](https://firecrawl.dev)
2. Get your API key from the dashboard
3. Add to your environment file:

```bash
echo "FIRECRAWL_API_KEY=fc-xxxxx" >> ~/.config/local-media-tools/.env
```

## Configuration

Add web sources to `~/.config/local-media-tools/sources.yaml`:

```yaml
sources:
  web_aggregators:
    enabled: true
    sources:
      - url: "https://hudsonvalleyevents.com"
        name: "Hudson Valley Events"
        source_type: "listing"
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | Website URL to scrape |
| `name` | Yes | Display name for the source |
| `source_type` | No | Type of site (listing, calendar, venue) |
| `max_pages` | No | Maximum pages to crawl (default: 50) |
| `event_url_pattern` | No | Only scrape URLs matching this pattern |
| `extraction_hints` | No | Help Claude understand the page structure |

### Source Types

| Type | Description | Example |
|------|-------------|---------|
| `listing` | Event listing with multiple events per page | Event aggregator sites |
| `calendar` | Calendar-style layout with dates | Community calendars |
| `venue` | Single venue's event schedule | Bar/restaurant websites |

## Examples

### Event Listing Site

```yaml
- url: "https://hudsonvalleyevents.com"
  name: "Hudson Valley Events"
  source_type: "listing"
  max_pages: 50
```

### Calendar Site

```yaml
- url: "https://localcalendar.com/events"
  name: "Local Calendar"
  source_type: "calendar"
  event_url_pattern: "/event/*"
  max_pages: 30
```

### Venue Site

```yaml
- url: "https://thevenue.com/schedule"
  name: "The Venue"
  source_type: "venue"
  extraction_hints: "Events in table rows with date, artist, and time"
```

## Extraction Hints

When Claude has trouble extracting events, add `extraction_hints` to describe the page structure:

```yaml
- url: "https://example.com/events"
  name: "Example Events"
  extraction_hints: |
    Events are listed in cards with class 'event-card'.
    Each card has: title in h3, date in .event-date, venue in .location.
    Some events span multiple days - treat as single event.
```

## Testing Before Adding

1. Visit the site manually to understand structure
2. Test at [firecrawl.dev/playground](https://firecrawl.dev) (if available)
3. Start with low `max_pages` (5-10) to test extraction
4. Adjust `extraction_hints` based on results

## What Works Well

| Site Type | Scraping Success |
|-----------|------------------|
| Static HTML event listings | High |
| Server-rendered pages | High |
| Light JavaScript | Medium |
| Heavy SPAs (React, Vue) | Low |
| Sites with bot protection | Very Low |

## What Doesn't Work

- **Heavy SPAs** - Sites that require JavaScript to render content
- **Login-required sites** - Firecrawl doesn't handle authentication
- **Bot-protected sites** - Cloudflare, reCAPTCHA, etc.
- **Pagination via infinite scroll** - May only get first page

## Troubleshooting

### No Events Extracted

**Symptom:** Scrape succeeds but 0 events

**Solutions:**
1. Add `extraction_hints` describing the page structure
2. Check if site uses JavaScript rendering
3. Verify URL has actual event listings
4. Check raw response in `~/.config/local-media-tools/data/raw/`

### Firecrawl API Error

**Symptom:** 401 or 403 error

**Solutions:**
1. Check API key is correct in `.env`
2. Verify API key is active (check Firecrawl dashboard)
3. Check if you've exceeded rate limits

### Incomplete Data

**Symptom:** Some events missing fields

**Solutions:**
1. Add specific `extraction_hints`
2. Check if data is in images (not text)
3. Some sites simply don't provide full event details

### Slow Scraping

**Symptom:** Takes very long to complete

**Solutions:**
1. Reduce `max_pages`
2. Add `event_url_pattern` to limit scope
3. Some sites are just slow to crawl

---

[Back to Configuration](../configuration.md) | [Back to Documentation](../README.md)
