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

### Profile Response

```json
{
  "username": "theavalonlounge",
  "full_name": "The Avalon Lounge",
  "biography": "Live music venue...",
  "follower_count": 5000,
  "is_verified": false
}
```

### Posts Response

```json
{
  "posts": [
    {
      "id": "3123456789",
      "caption": "Tonight! Live music with...",
      "taken_at": "2025-01-15T18:00:00Z",
      "media_type": "image",
      "images": [
        {"url": "https://..."}
      ],
      "like_count": 50,
      "comment_count": 5
    }
  ],
  "next_max_id": "abc123"
}
```

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
