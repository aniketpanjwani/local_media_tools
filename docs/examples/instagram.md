# Instagram Setup

Scrape event announcements from Instagram profiles using the ScrapeCreators API.

## Prerequisites

- [ScrapeCreators API key](https://scrapecreators.com) (paid service)
- Public Instagram profiles (private accounts cannot be scraped)

## API Key Setup

1. Sign up at [scrapecreators.com](https://scrapecreators.com)
2. Get your API key from the dashboard
3. Add to your environment file:

```bash
echo "SCRAPECREATORS_API_KEY=sk_live_xxxxx" >> ~/.config/local-media-tools/.env
```

## Configuration

Add Instagram accounts to `~/.config/local-media-tools/sources.yaml`:

```yaml
sources:
  instagram:
    enabled: true
    accounts:
      - handle: "local_venue"
        name: "Local Venue"
        type: "music_venue"
        location: "Kingston, NY"
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `handle` | Yes | Instagram username (without @) |
| `name` | No | Display name in newsletters |
| `type` | No | Venue type for categorization |
| `location` | No | City/region (helps with deduplication) |
| `notes` | No | Personal notes (not used in output) |

### Account Types

| Type | Use For |
|------|---------|
| `music_venue` | Bars, clubs, concert halls |
| `restaurant` | Restaurants, cafes with events |
| `gallery` | Art galleries, museums |
| `theater` | Theaters, performance spaces |
| `promoter` | Event promoters (posts about various venues) |
| `aggregator` | Accounts that share events from multiple sources |

## Finding Instagram Handles

1. Go to the profile on instagram.com
2. The handle is in the URL: `instagram.com/{handle}`
3. Or shown at the top of the profile page (without @)

## Common Mistakes

| Mistake | Correct Format |
|---------|----------------|
| `@venue_name` | `venue_name` |
| `https://instagram.com/venue` | `venue` |
| `venue-name` | Check actual handle (dashes vs underscores) |
| Using display name | Use the actual handle |

## How Scraping Works

1. **Fetch posts** - ScrapeCreators retrieves recent posts from the profile
2. **Download images** - Images are saved locally (Instagram CDN blocks external requests)
3. **Extract events** - Claude analyzes post content and images to identify events
4. **Store results** - Events are saved to SQLite with source tracking

### Image Download

Instagram's CDN blocks direct image access from external tools. Local Media Tools downloads images to `~/.config/local-media-tools/data/images/` so Claude can analyze them.

If image download fails:
- Event is still stored (without image data)
- Check network connectivity
- Some older posts may have expired image URLs

## Rate Limits

ScrapeCreators has rate limits based on your plan:
- Check your dashboard for current usage
- Spread sources across multiple research runs if hitting limits
- The plugin handles rate limit errors gracefully

## Priority Handles

Prioritize certain accounts to appear first in newsletters:

```yaml
sources:
  instagram:
    accounts:
      - handle: "venue_a"
        name: "Venue A"
      - handle: "venue_b"
        name: "Venue B"
    priority_handles:
      - "venue_a"  # Appears first in output
```

## Multi-Event Posts

Some accounts post multiple events in a single Instagram post (e.g., weekly schedules). Claude extracts individual events from these posts and links them back to the source post for traceability.

## Troubleshooting

### No Posts Returned

- Verify the handle exists and is public
- Check API key is valid
- Some profiles may have no recent posts

### Wrong Events Extracted

- Add `notes` field with context about the account
- Check if account posts non-event content mixed with events

### Images Missing

- Normal if CDN URLs expired
- Events are still usable without images
- Check network/firewall settings

---

[Back to Configuration](../configuration.md) | [Back to Documentation](../README.md)
