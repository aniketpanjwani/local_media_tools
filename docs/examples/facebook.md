# Facebook Setup

Scrape events from Facebook pages and discover local events by location.

## Two Approaches

| Approach | Best For | Requirements |
|----------|----------|--------------|
| **Page Scraping** | Known venues with /events pages | None (no API key) |
| **Location Discovery** | Finding events in a city | Chrome MCP + Facebook login |

## Page Scraping

Scrape event listings from Facebook pages that have an `/events` section.

### Configuration

```yaml
sources:
  facebook:
    enabled: true
    pages:
      - url: "https://facebook.com/localvenue/events"
        name: "Local Venue"
```

### Finding Event Pages

1. Go to the venue's Facebook page
2. Look for the "Events" tab
3. Copy the URL (should end in `/events`)

**Valid URL formats:**
- `https://facebook.com/venuename/events`
- `https://www.facebook.com/venuename/events`

### Limitations

Facebook page scraping uses the [facebook-event-scraper](https://github.com/francescov1/facebook-event-scraper) library, which scrapes public HTML. This can be unreliable:

- Only works for public events
- May break when Facebook changes their HTML
- Rate limiting and bot detection may block requests
- Some pages have different structures

**If page scraping fails consistently:** Use location-based discovery instead.

---

## Location-Based Discovery

Discover events happening near a specific city by scraping Facebook's events page while logged in.

### Prerequisites

1. **Chrome browser** installed
2. **Chrome MCP Server** configured in Claude Code
3. **Facebook account** logged in via Chrome

### Setup Steps

#### 1. Configure Chrome MCP

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "chrome-mcp-server": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-chrome"]
    }
  }
}
```

#### 2. Log into Facebook

1. Open Chrome
2. Navigate to facebook.com
3. Log in with your account
4. Keep Chrome open

#### 3. Run Setup Command

```
/newsletter-events:setup-location
```

Claude will:
1. Open Facebook's events page in Chrome
2. Help you navigate to your city
3. Extract the location_id from the URL
4. Add it to your configuration

### Configuration

After setup, your sources.yaml will include:

```yaml
sources:
  facebook:
    locations:
      - location_id: "111841478834264"
        location_name: "Medellín, Antioquia"
        date_filter: "THIS_WEEK"
```

### Date Filters

| Filter | Description |
|--------|-------------|
| `THIS_WEEK` | Events in the current week |
| `THIS_WEEKEND` | Friday through Sunday |
| `THIS_MONTH` | Events in the current month |

### How Discovery Works

1. Claude opens facebook.com/events in Chrome via MCP
2. Navigates to your configured location
3. You scroll to load more events (interactive)
4. Claude extracts event data from the page
5. Events are stored with sparse data (marked for review)

### Sparse Data

Location-based discovery captures limited data from the listing page:
- Event title
- Date/time (often incomplete)
- Venue name (sometimes missing)

Events are marked as needing review. When generating newsletters, Claude handles incomplete data gracefully.

---

## Troubleshooting

### Page Scraper Fails

**Symptom:** No events returned from a page

**Solutions:**
1. Verify the page has public events
2. Check the URL ends in `/events`
3. Try visiting the URL manually
4. Use location discovery instead

### Chrome MCP Not Working

**Symptom:** "Could not connect to Chrome"

**Solutions:**
1. Ensure Chrome is open
2. Restart Chrome MCP server
3. Check MCP configuration in Claude Code settings
4. Try running a simple Chrome MCP command first

### Location Discovery Fails

**Symptom:** Can't find location or extract events

**Solutions:**
1. Log into Facebook in Chrome first
2. Navigate to facebook.com/events manually to verify access
3. Check Chrome MCP is responding
4. Try a different browser profile

### Events Missing Details

**Symptom:** Events have no venue or time

**Cause:** Normal for location discovery (limited data available)

**Solution:** Claude will work with available data when generating newsletters

---

[Back to Configuration](../configuration.md) | [Back to Documentation](../README.md)
