#!/usr/bin/env python3
"""
CLI tool for profiling web aggregator sources.

Discovers optimal scraping strategy (map vs crawl) and suggests URL patterns.
Used by the add-source command to profile new web sources.

Usage:
    uv run python scripts/profile_source.py <url>

Output:
    JSON with profile data including discovery_method, event_urls, and regex pattern.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.paths import get_env_path

# Load environment variables from stable config directory
load_dotenv(get_env_path())

# Patterns to exclude (navigation, static files, etc.)
# We intentionally do NOT pre-filter by "event-like" patterns because:
# - Every site has different URL structures
# - Pre-filtering misses valid events (e.g., /display,event/ vs /events/)
# - The per-source event_url_regex in sources.yaml handles real filtering
EXCLUDE_PATTERNS = [
    r"^https?://[^/]+/?$",  # Homepage only
    r"/about",
    r"/contact",
    r"/privacy",
    r"/terms",
    r"/login",
    r"/signup",
    r"/cart",
    r"/checkout",
    r"/account",
    r"/search",
    r"/faq",
    r"/help",
    r"\.(css|js|png|jpg|gif|svg|ico|pdf|xml|json)$",
    r"\?.*page=",  # Pagination params (keep /page:X style)
]

MIN_URLS_THRESHOLD = 5
DEFAULT_WAIT_FOR_MS = 3000  # Wait 3 seconds for JavaScript to render


def filter_urls(urls: list[str]) -> list[str]:
    """Filter out navigation/static URLs, keep everything else for inspection."""
    filtered = []
    for url in urls:
        if any(re.search(p, url, re.I) for p in EXCLUDE_PATTERNS):
            continue
        filtered.append(url)
    return filtered


def suggest_regex_pattern(urls: list[str]) -> str | None:
    """Analyze URLs and suggest a regex pattern."""
    if not urls:
        return None

    # Extract paths
    paths = [urlparse(u).path for u in urls]

    # Find common patterns
    # Look for patterns like /events/slug, /event/slug/id, /calendar/date/slug
    pattern_templates = []

    for path in paths[:20]:  # Sample first 20
        # Replace specific slugs/IDs with regex patterns
        # e.g., /events/jazz-night -> /events/[^/]+
        # e.g., /event/frosty-fest/76214 -> /event/[^/]+/\d+

        parts = path.strip("/").split("/")
        regex_parts = []

        for part in parts:
            if re.match(r"^\d+$", part):
                regex_parts.append(r"\d+")
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", part):
                regex_parts.append(r"\d{4}-\d{2}-\d{2}")
            elif re.match(r"^[a-z0-9-]+$", part, re.I):
                regex_parts.append("[^/]+")
            else:
                regex_parts.append(re.escape(part))

        if regex_parts:
            pattern_templates.append("/" + "/".join(regex_parts) + "/?$")

    # Find most common pattern structure
    if pattern_templates:
        counter = Counter(pattern_templates)
        most_common = counter.most_common(1)[0][0]
        return most_common

    return None


def profile_source(url: str) -> dict:
    """
    Profile a web source to discover optimal scraping strategy.

    Returns:
        dict with discovery_method, event_urls, suggested_regex, notes
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "FIRECRAWL_API_KEY not set in ~/.config/local-media-tools/.env",
        }

    app = FirecrawlApp(api_key=api_key)

    # Try map first (fast)
    print(f"Profiling {url}...", file=sys.stderr)
    print("  Trying map (fast discovery)...", file=sys.stderr)

    try:
        map_result = app.map(url)
        # map returns a MapData object with 'links' attribute containing LinkResult objects
        all_urls = []
        if hasattr(map_result, "links"):
            for link in map_result.links:
                if hasattr(link, "url"):
                    all_urls.append(link.url)
                elif isinstance(link, str):
                    all_urls.append(link)
        elif isinstance(map_result, list):
            all_urls = [u.url if hasattr(u, "url") else u for u in map_result]

        event_urls = filter_urls(all_urls)
        discovery_method = "map"
        print(f"  Map found {len(all_urls)} total, {len(event_urls)} content URLs", file=sys.stderr)
    except Exception as e:
        print(f"  Map failed: {e}", file=sys.stderr)
        all_urls = []
        event_urls = []
        discovery_method = "map"

    # Fallback 1: Try scrape with wait_for for JavaScript-heavy sites
    if len(event_urls) < MIN_URLS_THRESHOLD:
        print(
            f"  Map found too few URLs ({len(event_urls)}), trying scrape with wait_for...",
            file=sys.stderr,
        )

        try:
            # Use scrape with wait_for and links format for JS-heavy sites
            scrape_result = app.scrape(
                url,
                formats=["links"],
                wait_for=DEFAULT_WAIT_FOR_MS,
            )

            # Extract links from scrape result
            all_links = []
            if hasattr(scrape_result, "links"):
                all_links = scrape_result.links or []
            elif isinstance(scrape_result, dict):
                all_links = scrape_result.get("links", [])

            event_urls = filter_urls(all_links)
            discovery_method = "scrape_wait_for"  # JS-heavy site needs wait_for
            print(
                f"  Scrape with wait_for found {len(all_links)} total, {len(event_urls)} content URLs",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"  Scrape with wait_for failed: {e}", file=sys.stderr)

    # Fallback 2: Try crawl if scrape also found too few
    if len(event_urls) < MIN_URLS_THRESHOLD:
        print(
            f"  Still too few URLs ({len(event_urls)}), trying crawl...",
            file=sys.stderr,
        )

        try:
            # crawl() returns a list of CrawlData objects
            crawl_result = app.crawl(url, limit=30)

            all_links = []
            # Iterate through crawl results
            if isinstance(crawl_result, list):
                for page in crawl_result:
                    if hasattr(page, "links"):
                        all_links.extend(page.links)
                    elif isinstance(page, dict):
                        all_links.extend(page.get("links", []))
            elif hasattr(crawl_result, "data"):
                for page in crawl_result.data:
                    if hasattr(page, "links"):
                        all_links.extend(page.links)

            event_urls = filter_urls(all_links)
            discovery_method = "crawl"
            print(f"  Crawl found {len(all_links)} total, {len(event_urls)} content URLs", file=sys.stderr)
        except Exception as e:
            print(f"  Crawl failed: {e}", file=sys.stderr)

    # Suggest regex pattern
    suggested_regex = suggest_regex_pattern(event_urls)

    # Build notes based on what worked
    if discovery_method == "crawl":
        notes = f"Discovered {len(event_urls)} URLs using crawl (map and scrape found too few)."
    elif len(event_urls) >= MIN_URLS_THRESHOLD:
        notes = f"Discovered {len(event_urls)} URLs using map/scrape with wait_for."
    else:
        notes = f"Found only {len(event_urls)} URLs. May need manual profiling."

    return {
        "success": True,
        "url": url,
        "discovery_method": discovery_method,
        "event_urls_count": len(event_urls),
        "event_urls": event_urls[:10],  # Sample
        "suggested_regex": suggested_regex,
        "notes": notes,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Profile a web source for event scraping"
    )
    parser.add_argument("url", help="URL of the web aggregator to profile")
    parser.add_argument(
        "--format",
        choices=["json", "human"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    result = profile_source(args.url)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            print(f"\n📊 Source Profile: {args.url}")
            print(f"   Discovery Method: {result['discovery_method']}")
            print(f"   URLs Found: {result['event_urls_count']}")
            if result.get("suggested_regex"):
                print(f"   Suggested Pattern: {result['suggested_regex']}")
            print("\n   Sample URLs:")
            for url in result.get("event_urls", [])[:5]:
                print(f"     • {url}")
        else:
            print(f"\n❌ Error: {result.get('error')}")

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
