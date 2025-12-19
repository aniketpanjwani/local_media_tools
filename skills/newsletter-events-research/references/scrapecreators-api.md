# ScrapeCreators API Reference

## Overview

ScrapeCreators provides an API for scraping Instagram data. We use it to fetch posts from venue and promoter accounts.

API Documentation: https://scrapecreators.com/docs

## Authentication

Set `SCRAPECREATORS_API_KEY` in your `.env` file.

## Client Usage

```python
from scripts.scrape_instagram import ScrapeCreatorsClient

client = ScrapeCreatorsClient()

# Fetch profile info
profile = client.get_instagram_profile("theavalonlounge")

# Fetch recent posts
posts = client.get_instagram_user_posts("theavalonlounge", limit=20)
```

## Response Structure

### Posts Response

The posts endpoint returns a nested structure with profile owner info embedded in each post:

```json
{
  "posts": [
    {
      "node": {
        "id": "3791185451521504245",
        "shortcode": "DSc_xTjkXP1",
        "__typename": "GraphImage",
        "display_url": "https://instagram.com/...",
        "owner": {
          "id": "11425683273",
          "username": "theavalonlounge"
        },
        "is_video": false,
        "edge_media_to_caption": {
          "edges": [{"node": {"text": "Tonight! Live music..."}}]
        },
        "edge_liked_by": {"count": 99},
        "edge_media_to_comment": {"count": 5},
        "taken_at_timestamp": 1766164545,
        "url": "https://www.instagram.com/p/DSc_xTjkXP1/"
      }
    }
  ],
  "next_max_id": "abc123"
}
```

**Key fields:**
- `node.id` - Post ID (numeric string)
- `node.shortcode` - URL shortcode
- `node.__typename` - Media type: `GraphImage`, `GraphVideo`, `GraphSidecar` (carousel)
- `node.owner.id` - Profile's Instagram ID
- `node.owner.username` - Profile handle
- `node.edge_media_to_caption.edges[0].node.text` - Caption text
- `node.taken_at_timestamp` - Unix timestamp when posted
- `node.url` - Full post URL

### Profile Endpoint

**Note:** The `/v1/instagram/profile/{handle}` endpoint may return 404. Extract profile info from post owner data instead.

## Rate Limiting

- Built-in rate limiter: 2 calls/second
- API returns 429 on rate limit
- Automatic retry with backoff

## Error Handling

```python
try:
    posts = client.get_instagram_user_posts(handle)
except ScrapeCreatorsRateLimitError:
    # Wait and retry
except ScrapeCreatorsError as e:
    # Log and continue with other accounts
```
