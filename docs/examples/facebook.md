# Facebook Events

Scrape individual Facebook events by passing their URLs directly to the research command.

## How It Works

Facebook events are scraped ad-hoc rather than configured in `sources.yaml`. Simply pass one or more Facebook event URLs when running research.

## Usage

### Single Event

```
/newsletter-events:research https://facebook.com/events/123456789
```

### Multiple Events

```
/newsletter-events:research https://facebook.com/events/123456789 https://facebook.com/events/987654321
```

### Mixed with Configured Sources

```
/newsletter-events:research https://facebook.com/events/123456789
```

This will:
1. Scrape all configured Instagram and web sources
2. Also scrape the provided Facebook event URL

## Supported URL Formats

| Format | Example |
|--------|---------|
| Standard | `https://facebook.com/events/123456789` |
| With www | `https://www.facebook.com/events/123456789` |
| Short | `https://fb.com/events/123456789` |

## What Gets Scraped

For each Facebook event URL, the scraper extracts:

| Field | Description |
|-------|-------------|
| Title | Event name |
| Description | Full event description |
| Date/Time | Start and end times |
| Venue | Name, address, city, coordinates |
| Image | Event cover photo |
| Ticket URL | Link to buy tickets (if available) |
| Host | Event organizer |
| Going/Interested | Attendance counts |

## Limitations

- Only public events can be scraped
- Private events or login-required events will fail
- The scraper uses HTML parsing which may break if Facebook changes their layout

## Troubleshooting

### Event Not Found

**Symptom:** "Event not found or is private"

**Solutions:**
1. Verify the event is public (viewable without login)
2. Check the URL is correct
3. Try visiting the URL in an incognito browser

### Scraper Timeout

**Symptom:** "Scraper timed out"

**Solutions:**
1. Try again (Facebook may have rate-limited)
2. Check your internet connection
3. The event page may be loading slowly

### Missing Data

**Symptom:** Some fields are empty

**Cause:** The event page doesn't have that information

**Solution:** This is normal - Claude will work with available data when generating newsletters

---

[Back to Configuration](../configuration.md) | [Back to Documentation](../README.md)
