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

1. `app.map()` - Discovers all URLs on the site
2. Filter - Removes non-event URLs (about, contact, assets)
3. `app.scrape()` - Gets markdown content from each page
4. **Claude** - Extracts events from the markdown

## Error Handling

- `FirecrawlError` - Base exception for all Firecrawl errors
- Partial failures are logged; scraping continues with other pages
- Failed pages have an `error` key instead of `markdown`

## Rate Limits

Firecrawl has built-in rate limiting. The SDK handles this automatically.

## JavaScript-Heavy Sites

Firecrawl includes "smart wait" by default, but some sites (like Eventbrite) need extra time for JavaScript to render.

### The `wait_for` Parameter

Add extra delay before scraping:

```python
# For scraping with link discovery
result = app.scrape(url,
    formats=["links"],
    wait_for=3000  # Wait 3 seconds for JS
)

# For crawling
result = app.crawl(url, scrape_options={"wait_for": 3000})
```

**When to use:**
- Site loads content via JavaScript/AJAX
- Initial `map()` returns 0 or very few URLs
- Sites like Eventbrite, modern SPAs, React/Vue apps

### Link Discovery Pattern

For JS-heavy sites, use `scrape()` with `formats=["links"]` instead of `map()`:

```python
# map() often fails on JS sites
map_result = app.map(url)  # Returns 0 links for Eventbrite

# scrape with wait_for + links format works
scrape_result = app.scrape(url,
    formats=["links"],
    wait_for=3000
)
links = scrape_result.links  # Returns 60+ links for Eventbrite
```

### Actions for Complex Interactions

For sites requiring user interaction (infinite scroll, click to load):

```python
from firecrawl.v2.types import WaitAction, ScrollAction

result = app.scrape(url,
    actions=[
        WaitAction(type="wait", milliseconds=2000),
        ScrollAction(type="scroll", direction="down"),
        WaitAction(type="wait", milliseconds=1000),
    ],
    formats=["links"]
)
```

**Supported actions:** `wait`, `click`, `scroll`, `write`, `press`, `executeJavascript`
