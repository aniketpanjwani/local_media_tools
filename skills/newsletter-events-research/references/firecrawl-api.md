# Firecrawl Python SDK Reference

This plugin uses `firecrawl-py` for web scraping. Firecrawl handles the hard parts
(JavaScript rendering, anti-bot, rate limiting). Claude does the event extraction.

## Why This Approach

| Component | Responsibility |
|-----------|---------------|
| Firecrawl | URL discovery, page scraping, markdown conversion |
| Claude | Event extraction from markdown (same as Instagram image analysis) |

We don't use Firecrawl's `extract` endpoint because:
- We're already paying for Claude
- Claude is better at nuanced extraction
- Consistent with other source workflows

## Installation

Installed automatically via `uv sync` during `/setup`.

Requires `FIRECRAWL_API_KEY` in `.env` (only if web aggregators are configured).

## Client Usage

```python
from scripts.scrape_firecrawl import FirecrawlClient

client = FirecrawlClient()

# Option 1: Full workflow (discover + scrape)
pages = client.scrape_aggregator(
    url="https://example.com/events",
    max_pages=50,
    event_url_pattern="/events/*",  # Optional
)

# Option 2: Step by step
urls = client.discover_event_urls(url, max_urls=50)
pages = client.scrape_pages(urls)

# Each page has: url, markdown, metadata
for page in pages:
    print(page["markdown"])  # Claude extracts events from this
```

## How It Works

1. `app.map_url()` - Discovers all URLs on the site
2. Filter - Removes non-event URLs (about, contact, assets)
3. `app.scrape_url()` - Gets markdown content from each page
4. **Claude** - Extracts events from the markdown

## Error Handling

- `FirecrawlError` - Base exception for all Firecrawl errors
- Partial failures are logged; scraping continues with other pages
- Failed pages have an `error` key instead of `markdown`

## Rate Limits

Firecrawl has built-in rate limiting. The SDK handles this automatically.
