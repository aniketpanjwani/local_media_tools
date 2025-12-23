#!/usr/bin/env python3
"""
CLI tool for web aggregator research that Claude can invoke directly.

Usage:
    uv run python scripts/cli_web.py discover --all
    uv run python scripts/cli_web.py discover --source "Great Northern Catskills"
    uv run python scripts/cli_web.py scrape --source "Great Northern Catskills"
    uv run python scripts/cli_web.py show-stats

This ensures:
- Correct Firecrawl API usage (map vs crawl per profile)
- URL tracking (only scrape new URLs)
- Proper database storage
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_schema import AppConfig, WebAggregatorSource
from schemas.sqlite_storage import SqliteStorage
from scripts.paths import get_sources_path, get_database_path, TEMP_RAW_DIR
from scripts.scrape_firecrawl import FirecrawlClient, FirecrawlError
from scripts.url_utils import normalize_url


def get_config() -> AppConfig:
    """Load configuration from user config directory."""
    config_path = get_sources_path()
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}", file=sys.stderr)
        print("Run /newsletter-events:setup to create configuration.", file=sys.stderr)
        sys.exit(1)
    return AppConfig.from_yaml(config_path)


def get_storage() -> SqliteStorage:
    """Get SQLite storage instance."""
    return SqliteStorage(get_database_path())


def discover_urls(client: FirecrawlClient, source: WebAggregatorSource) -> list[str]:
    """
    Discover event URLs from a web aggregator using its stored profile.

    Returns list of discovered event page URLs.
    """
    profile = source.profile
    pattern = source.event_url_pattern or (profile.event_url_regex if profile else None)
    discovery_method = profile.discovery_method if profile else "map"

    if discovery_method == "crawl":
        # Use crawl (profile says map and scrape failed for this site)
        print(f"  Using crawl (per profile)...", file=sys.stderr)
        crawl_result = client.app.crawl(
            source.url,
            limit=source.max_pages,
        )

        all_links = []
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

        # Filter using learned regex
        if pattern:
            discovered_urls = [u for u in all_links if re.search(pattern, u)]
        else:
            discovered_urls = client._filter_event_urls(all_links, None)

    elif discovery_method == "scrape_wait_for":
        # Use scrape with wait_for (JS-heavy site like Eventbrite)
        print(f"  Using scrape with wait_for (per profile)...", file=sys.stderr)
        scrape_result = client.app.scrape(
            source.url,
            formats=["links"],
            wait_for=3000,  # Wait 3 seconds for JS to render
        )

        all_links = []
        if hasattr(scrape_result, "links"):
            all_links = scrape_result.links or []
        elif isinstance(scrape_result, dict):
            all_links = scrape_result.get("links", [])

        # Filter using learned regex
        if pattern:
            discovered_urls = [u for u in all_links if re.search(pattern, u)]
        else:
            discovered_urls = client._filter_event_urls(all_links, None)

    else:
        # Default: use map (fast path, works for most sites)
        discovered_urls = client.discover_event_urls(
            url=source.url,
            max_urls=source.max_pages,
            event_url_pattern=pattern,
        )

    return discovered_urls


def cmd_discover(args: argparse.Namespace) -> int:
    """Discover event URLs from web aggregators (without scraping)."""
    config = get_config()
    storage = get_storage()

    sources = config.sources.web_aggregators.sources
    if not sources:
        print("No web aggregator sources configured.", file=sys.stderr)
        print("Add sources with /newsletter-events:add-source", file=sys.stderr)
        return 1

    # Filter to specific source if provided
    if args.source:
        sources = [s for s in sources if s.name.lower() == args.source.lower()]
        if not sources:
            print(f"Error: Source '{args.source}' not found.", file=sys.stderr)
            return 1

    try:
        client = FirecrawlClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    results = []

    for source in sources:
        print(f"\n{source.name}:", file=sys.stderr)
        print(f"  URL: {source.url}", file=sys.stderr)

        try:
            discovered_urls = discover_urls(client, source)

            # Normalize and check existing
            normalized_map = {normalize_url(u): u for u in discovered_urls}
            existing_urls = storage.get_scraped_urls_for_source(source.name)
            new_urls = [(norm, orig) for norm, orig in normalized_map.items()
                        if norm not in existing_urls]

            print(f"  Found: {len(discovered_urls)} URLs, {len(new_urls)} new", file=sys.stderr)

            results.append({
                "source": source.name,
                "url": source.url,
                "discovered": len(discovered_urls),
                "new": len(new_urls),
                "already_scraped": len(discovered_urls) - len(new_urls),
                "sample_urls": discovered_urls[:5],
                "error": None,
            })

        except FirecrawlError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            results.append({
                "source": source.name,
                "url": source.url,
                "discovered": 0,
                "new": 0,
                "already_scraped": 0,
                "sample_urls": [],
                "error": str(e),
            })

    # Print summary
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"{'Source':<30} {'Found':>10} {'New':>10} {'Scraped':>10}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    for r in results:
        if r.get("error"):
            print(f"{r['source']:<30} {'ERROR':>10} {'-':>10} {'-':>10}", file=sys.stderr)
        else:
            print(f"{r['source']:<30} {r['discovered']:>10} {r['new']:>10} {r['already_scraped']:>10}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, indent=2))

    return 0


def cmd_scrape(args: argparse.Namespace) -> int:
    """Scrape new URLs from web aggregators and return markdown for event extraction."""
    config = get_config()
    storage = get_storage()

    sources = config.sources.web_aggregators.sources
    if not sources:
        print("No web aggregator sources configured.", file=sys.stderr)
        return 1

    # Filter to specific source if provided
    if args.source:
        sources = [s for s in sources if s.name.lower() == args.source.lower()]
        if not sources:
            print(f"Error: Source '{args.source}' not found.", file=sys.stderr)
            return 1

    try:
        client = FirecrawlClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    all_pages = []

    for source in sources:
        print(f"\n{source.name}:", file=sys.stderr)

        try:
            # Discover URLs
            discovered_urls = discover_urls(client, source)

            # Filter to new URLs only
            normalized_map = {normalize_url(u): u for u in discovered_urls}
            existing_urls = storage.get_scraped_urls_for_source(source.name)
            new_urls = [(norm, orig) for norm, orig in normalized_map.items()
                        if norm not in existing_urls]

            print(f"  Found {len(discovered_urls)} URLs, {len(new_urls)} new", file=sys.stderr)

            if not new_urls:
                print(f"  No new URLs to scrape", file=sys.stderr)
                continue

            # Limit URLs if specified
            if args.limit and len(new_urls) > args.limit:
                print(f"  Limiting to {args.limit} URLs", file=sys.stderr)
                new_urls = new_urls[:args.limit]

            # Scrape each new URL
            pages_scraped = []
            for i, (normalized_url, original_url) in enumerate(new_urls):
                print(f"  [{i+1}/{len(new_urls)}] Scraping {original_url[:60]}...", file=sys.stderr)
                try:
                    page = client.app.scrape(original_url, formats=["markdown"])

                    # Handle ScrapeData object or dict response
                    if hasattr(page, "markdown"):
                        markdown = page.markdown or ""
                        title = page.metadata.title if hasattr(page, "metadata") and hasattr(page.metadata, "title") else ""
                    else:
                        markdown = page.get("markdown", "")
                        title = page.get("metadata", {}).get("title", "")

                    page_data = {
                        "source_name": source.name,
                        "normalized_url": normalized_url,
                        "original_url": original_url,
                        "title": title,
                        "markdown": markdown,
                        "scraped_at": datetime.now().isoformat(),
                    }
                    pages_scraped.append(page_data)
                    all_pages.append(page_data)

                except Exception as e:
                    print(f"    ERROR: {e}", file=sys.stderr)

            # Save raw data
            if pages_scraped:
                TEMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
                raw_path = TEMP_RAW_DIR / f"web_{source.name.replace(' ', '_')}_{datetime.now():%Y%m%d_%H%M%S}.json"
                with open(raw_path, "w") as f:
                    json.dump(pages_scraped, f, indent=2)
                print(f"  Saved raw data to {raw_path}", file=sys.stderr)

            print(f"  Scraped {len(pages_scraped)} pages", file=sys.stderr)

        except FirecrawlError as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    # Output all scraped pages as JSON for Claude to process
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Total: {len(all_pages)} pages scraped", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    # Output JSON to stdout for Claude to read
    print(json.dumps(all_pages, indent=2))

    return 0


def cmd_mark_scraped(args: argparse.Namespace) -> int:
    """Mark a URL as scraped (called after Claude extracts events)."""
    storage = get_storage()

    storage.save_scraped_page(
        source_name=args.source,
        url=normalize_url(args.url),
        events_count=args.events_count,
    )

    print(f"Marked as scraped: {args.url} ({args.events_count} events)")
    return 0


def cmd_list_pages(args: argparse.Namespace) -> int:
    """List scraped pages from the most recent scrape run."""
    # Find most recent raw files
    if not TEMP_RAW_DIR.exists():
        print("No scraped data found. Run 'scrape' first.", file=sys.stderr)
        return 1

    raw_files = sorted(TEMP_RAW_DIR.glob("web_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not raw_files:
        print("No scraped data found. Run 'scrape' first.", file=sys.stderr)
        return 1

    # Filter by source if specified
    if args.source:
        source_pattern = args.source.replace(" ", "_")
        raw_files = [f for f in raw_files if source_pattern in f.name]
        if not raw_files:
            print(f"No scraped data for source '{args.source}'", file=sys.stderr)
            return 1

    # Collect pages from files (most recent per source)
    seen_sources = set()
    all_pages = []

    for raw_file in raw_files:
        # Extract source name from filename: web_Source_Name_20251222_221709.json
        parts = raw_file.stem.split("_")
        if len(parts) >= 4:
            # Source name is between "web_" and the timestamp
            source_name = " ".join(parts[1:-2])  # Skip "web" and last 2 (date, time)
        else:
            source_name = "Unknown"

        # Only use most recent file per source
        if source_name in seen_sources:
            continue
        seen_sources.add(source_name)

        try:
            with open(raw_file) as f:
                pages = json.load(f)

            for i, page in enumerate(pages):
                all_pages.append({
                    "index": i,
                    "source": page.get("source_name", source_name),
                    "title": page.get("title", "")[:60],
                    "url": page.get("original_url", ""),
                    "scraped_at": page.get("scraped_at", ""),
                    "file": str(raw_file),
                })
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {raw_file}: {e}", file=sys.stderr)

    if not all_pages:
        print("No pages found in scraped data.", file=sys.stderr)
        return 1

    # Output
    if args.json:
        print(json.dumps(all_pages, indent=2))
    else:
        print(f"\n{'Idx':>4} {'Source':<25} {'Title':<40}")
        print("-" * 75)
        for p in all_pages:
            print(f"{p['index']:>4} {p['source']:<25} {p['title']:<40}")
        print(f"\nTotal: {len(all_pages)} pages")
        print(f"\nUse 'read-page --source \"Name\" --index N' to read a page's content")

    return 0


def cmd_read_page(args: argparse.Namespace) -> int:
    """Read a single page's markdown content from scraped data."""
    if not TEMP_RAW_DIR.exists():
        print("No scraped data found. Run 'scrape' first.", file=sys.stderr)
        return 1

    # Find the file for this source
    source_pattern = args.source.replace(" ", "_")
    raw_files = sorted(
        [f for f in TEMP_RAW_DIR.glob("web_*.json") if source_pattern in f.name],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not raw_files:
        print(f"No scraped data for source '{args.source}'", file=sys.stderr)
        return 1

    # Use most recent file
    raw_file = raw_files[0]

    try:
        with open(raw_file) as f:
            pages = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {raw_file}: {e}", file=sys.stderr)
        return 1

    if args.index >= len(pages):
        print(f"Index {args.index} out of range. Source has {len(pages)} pages (0-{len(pages)-1}).", file=sys.stderr)
        return 1

    page = pages[args.index]

    if args.json:
        # Output full page data
        print(json.dumps(page, indent=2))
    else:
        # Output just the markdown for easy processing
        print(f"# Page {args.index}: {page.get('title', 'Untitled')}")
        print(f"# URL: {page.get('original_url', '')}")
        print(f"# Source: {page.get('source_name', args.source)}")
        print()
        print(page.get("markdown", ""))

    return 0


def cmd_show_stats(args: argparse.Namespace) -> int:
    """Show statistics about web aggregator scraping."""
    storage = get_storage()
    config = get_config()

    sources = config.sources.web_aggregators.sources

    print("WEB AGGREGATOR STATISTICS")
    print("=" * 60)

    with storage._connection() as conn:
        # Get scraped page counts per source
        stats = conn.execute("""
            SELECT source_name, COUNT(*) as pages, SUM(events_extracted) as events
            FROM scraped_pages
            GROUP BY source_name
        """).fetchall()

        stats_dict = {row[0]: {"pages": row[1], "events": row[2] or 0} for row in stats}

    print(f"\n{'Source':<30} {'Pages':>10} {'Events':>10} {'Profile':>10}")
    print("-" * 60)

    for source in sources:
        s = stats_dict.get(source.name, {"pages": 0, "events": 0})
        profile_method = source.profile.discovery_method if source.profile else "none"
        print(f"{source.name:<30} {s['pages']:>10} {s['events']:>10} {profile_method:>10}")

    # Totals
    total_pages = sum(s["pages"] for s in stats_dict.values())
    total_events = sum(s["events"] for s in stats_dict.values())
    print("-" * 60)
    print(f"{'TOTAL':<30} {total_pages:>10} {total_events:>10}")

    if args.json:
        result = {
            "sources": [
                {
                    "name": source.name,
                    "url": source.url,
                    "pages_scraped": stats_dict.get(source.name, {}).get("pages", 0),
                    "events_extracted": stats_dict.get(source.name, {}).get("events", 0),
                    "profile": source.profile.discovery_method if source.profile else None,
                }
                for source in sources
            ],
            "totals": {
                "pages": total_pages,
                "events": total_events,
            },
        }
        print("\n" + json.dumps(result, indent=2))

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Web aggregator research CLI for newsletter events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python scripts/cli_web.py discover --all
  uv run python scripts/cli_web.py discover --source "Great Northern Catskills"
  uv run python scripts/cli_web.py scrape --source "Great Northern Catskills"
  uv run python scripts/cli_web.py scrape --all --limit 10
  uv run python scripts/cli_web.py mark-scraped --source "Name" --url "https://..." --events-count 2
  uv run python scripts/cli_web.py show-stats
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover command
    discover_parser = subparsers.add_parser("discover", help="Discover event URLs (no scraping)")
    discover_group = discover_parser.add_mutually_exclusive_group(required=True)
    discover_group.add_argument("--all", action="store_true", help="Discover from all sources")
    discover_group.add_argument("--source", type=str, help="Discover from specific source")
    discover_parser.add_argument("--json", action="store_true", help="Output JSON results")
    discover_parser.set_defaults(func=cmd_discover)

    # scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape new URLs and output markdown")
    scrape_group = scrape_parser.add_mutually_exclusive_group(required=True)
    scrape_group.add_argument("--all", action="store_true", help="Scrape all sources")
    scrape_group.add_argument("--source", type=str, help="Scrape specific source")
    scrape_parser.add_argument("--limit", type=int, help="Max URLs to scrape per source")
    scrape_parser.set_defaults(func=cmd_scrape)

    # mark-scraped command
    mark_parser = subparsers.add_parser("mark-scraped", help="Mark URL as scraped after event extraction")
    mark_parser.add_argument("--source", type=str, required=True, help="Source name")
    mark_parser.add_argument("--url", type=str, required=True, help="URL that was scraped")
    mark_parser.add_argument("--events-count", type=int, default=0, help="Number of events extracted")
    mark_parser.set_defaults(func=cmd_mark_scraped)

    # list-pages command
    list_parser = subparsers.add_parser("list-pages", help="List scraped pages from most recent run")
    list_parser.add_argument("--source", type=str, help="Filter to specific source")
    list_parser.add_argument("--json", action="store_true", help="Output JSON")
    list_parser.set_defaults(func=cmd_list_pages)

    # read-page command
    read_parser = subparsers.add_parser("read-page", help="Read a single page's markdown content")
    read_parser.add_argument("--source", type=str, required=True, help="Source name")
    read_parser.add_argument("--index", type=int, required=True, help="Page index (from list-pages)")
    read_parser.add_argument("--json", action="store_true", help="Output full JSON (not just markdown)")
    read_parser.set_defaults(func=cmd_read_page)

    # show-stats command
    stats_parser = subparsers.add_parser("show-stats", help="Show scraping statistics")
    stats_parser.add_argument("--json", action="store_true", help="Output JSON")
    stats_parser.set_defaults(func=cmd_show_stats)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
