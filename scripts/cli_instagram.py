#!/usr/bin/env python3
"""
CLI tool for Instagram research that Claude can invoke directly.

Usage:
    uv run python scripts/cli_instagram.py scrape --all
    uv run python scripts/cli_instagram.py scrape --handle wayside_cider
    uv run python scripts/cli_instagram.py list-posts --handle wayside_cider
    uv run python scripts/cli_instagram.py show-stats

This ensures:
- Correct API parameters (handle, not username)
- Rate limiting (2 calls/second)
- Automatic retry on 429/5xx errors
- Proper database storage with FK relationships
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_schema import AppConfig
from schemas.event import InstagramPost, InstagramProfile
from schemas.sqlite_storage import SqliteStorage
from scripts.paths import get_sources_path, get_database_path, TEMP_RAW_DIR
from scripts.scrape_instagram import ScrapeCreatorsClient, ScrapeCreatorsError


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


def scrape_account(client: ScrapeCreatorsClient, handle: str, limit: int = 20) -> dict:
    """
    Scrape posts from a single Instagram account.

    Returns dict with profile, posts, and metadata.
    """
    handle = handle.lstrip("@").strip()
    result = client.get_instagram_user_posts(handle, limit=limit)

    posts_data = result.get("posts", [])
    if not posts_data:
        return {
            "handle": handle,
            "profile": None,
            "posts": [],
            "raw_response": result,
            "error": None,
            "scraped_at": datetime.now().isoformat(),
        }

    # Extract profile from first post's owner data
    # Note: We use the queried handle, not API response, as it may differ
    first_node = posts_data[0].get("node", {})
    owner = first_node.get("owner", {})
    profile = InstagramProfile(
        instagram_id=owner.get("id", ""),
        handle=handle,  # Use queried handle, not API response
        full_name=owner.get("full_name"),
    )

    # Create InstagramPost objects
    posts = []
    for post_data in posts_data:
        node = post_data.get("node", {})
        try:
            post = InstagramPost.from_api_response(node)
            posts.append(post)
        except Exception as e:
            print(f"Warning: Failed to parse post {node.get('id')}: {e}", file=sys.stderr)

    return {
        "handle": handle,
        "profile": profile,
        "posts": posts,
        "raw_response": result,
        "error": None,
        "scraped_at": datetime.now().isoformat(),
    }


def save_raw_response(handle: str, scrape_result: dict) -> Path:
    """Save raw API response to data directory."""
    TEMP_RAW_DIR.mkdir(parents=True, exist_ok=True)

    output_path = TEMP_RAW_DIR / f"instagram_{handle}.json"

    # Save the original API response, not the processed data
    raw_response = scrape_result.get("raw_response", {})
    with open(output_path, "w") as f:
        json.dump(raw_response, f, indent=2, default=str)

    return output_path


def cmd_scrape(args: argparse.Namespace) -> int:
    """Scrape Instagram accounts and save to database."""
    config = get_config()
    storage = get_storage()
    client = ScrapeCreatorsClient()

    accounts = config.sources.instagram.accounts
    if not accounts:
        print("No Instagram accounts configured.", file=sys.stderr)
        print("Add accounts to ~/.config/local-media-tools/sources.yaml", file=sys.stderr)
        return 1

    # Filter to specific handle if provided
    if args.handle:
        handle = args.handle.lstrip("@").strip()
        accounts = [a for a in accounts if a.handle == handle]
        if not accounts:
            print(f"Error: Account @{handle} not found in configuration.", file=sys.stderr)
            return 1

    results = []
    total_posts = 0
    total_new = 0

    print(f"Scraping {len(accounts)} Instagram account(s)...\n")

    for account in accounts:
        try:
            print(f"  @{account.handle}...", end=" ", flush=True)

            # Scrape posts from API
            scrape_result = scrape_account(client, account.handle, limit=args.limit)

            if scrape_result["error"]:
                print(f"ERROR: {scrape_result['error']}")
                results.append({
                    "handle": account.handle,
                    "posts_fetched": 0,
                    "new_posts": 0,
                    "error": scrape_result["error"],
                })
                continue

            posts = scrape_result["posts"]
            profile = scrape_result["profile"]

            # Check which posts are already in database
            existing = storage.get_posts_for_profile(account.handle, only_classified=False)
            existing_ids = set(existing.keys())

            new_posts = [p for p in posts if p.instagram_post_id not in existing_ids]

            # Save profile and posts to database (without events - Claude does extraction)
            if profile and posts:
                storage.save_instagram_scrape(
                    profile=profile,
                    posts=posts,
                    events_by_post={},  # Empty - Claude extracts events
                )

            # Save raw response
            save_raw_response(account.handle, scrape_result)

            print(f"{len(posts)} posts ({len(new_posts)} new)")

            total_posts += len(posts)
            total_new += len(new_posts)

            results.append({
                "handle": account.handle,
                "name": account.name,
                "posts_fetched": len(posts),
                "new_posts": len(new_posts),
                "already_in_db": len(posts) - len(new_posts),
                "error": None,
            })

        except ScrapeCreatorsError as e:
            print(f"ERROR: {e}")
            results.append({
                "handle": account.handle,
                "posts_fetched": 0,
                "new_posts": 0,
                "error": str(e),
            })

    # Print summary
    print(f"\n{'='*50}")
    print(f"SUMMARY: {total_posts} posts fetched, {total_new} new")
    print(f"{'='*50}\n")

    # Print table
    print(f"{'Account':<25} {'Fetched':>10} {'New':>10} {'In DB':>10}")
    print("-" * 55)
    for r in results:
        if r.get("error"):
            print(f"@{r['handle']:<24} {'ERROR':>10} {'-':>10} {'-':>10}")
        else:
            print(f"@{r['handle']:<24} {r['posts_fetched']:>10} {r['new_posts']:>10} {r['already_in_db']:>10}")
    print("-" * 55)
    print(f"{'TOTAL':<25} {total_posts:>10} {total_new:>10} {total_posts - total_new:>10}")

    # Output JSON if requested
    if args.json:
        print("\n" + json.dumps(results, indent=2))

    return 0


def cmd_list_posts(args: argparse.Namespace) -> int:
    """List posts from database for a handle."""
    storage = get_storage()
    handle = args.handle.lstrip("@").strip()

    posts = storage.get_posts_for_profile(handle, only_classified=args.classified_only)

    if not posts:
        print(f"No posts found for @{handle}")
        return 0

    print(f"Posts for @{handle}: {len(posts)} total\n")

    if args.json:
        print(json.dumps(list(posts.values()), indent=2, default=str))
    else:
        print(f"{'Post ID':<25} {'Classification':<15} {'Posted':<12} {'Reason'}")
        print("-" * 80)
        for post_id, post in sorted(posts.items(), key=lambda x: x[1].get("posted_at", ""), reverse=True):
            classification = post.get("classification") or "unclassified"
            posted_at = post.get("posted_at", "")[:10]
            reason = (post.get("classification_reason") or "")[:30]
            print(f"{post_id:<25} {classification:<15} {posted_at:<12} {reason}")

    return 0


def cmd_show_stats(args: argparse.Namespace) -> int:
    """Show statistics about scraped data."""
    storage = get_storage()

    with storage._connection() as conn:
        # Get profile counts
        profile_count = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]

        # Get post counts by classification
        post_stats = conn.execute("""
            SELECT
                COALESCE(classification, 'unclassified') as classification,
                COUNT(*) as count
            FROM posts
            GROUP BY classification
            ORDER BY count DESC
        """).fetchall()

        # Get event counts
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        # Get venue counts
        venue_count = conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0]

        # Get posts per profile
        posts_per_profile = conn.execute("""
            SELECT pr.handle, COUNT(p.id) as post_count
            FROM profiles pr
            LEFT JOIN posts p ON pr.id = p.profile_id
            GROUP BY pr.id
            ORDER BY post_count DESC
        """).fetchall()

    print("DATABASE STATISTICS")
    print("=" * 40)
    print(f"Profiles:     {profile_count}")
    print(f"Venues:       {venue_count}")
    print(f"Events:       {event_count}")
    print()

    print("POSTS BY CLASSIFICATION")
    print("-" * 40)
    total_posts = 0
    for row in post_stats:
        print(f"  {row[0]:<20} {row[1]:>6}")
        total_posts += row[1]
    print("-" * 40)
    print(f"  {'Total':<20} {total_posts:>6}")
    print()

    print("POSTS PER PROFILE")
    print("-" * 40)
    for row in posts_per_profile:
        print(f"  @{row[0]:<22} {row[1]:>6}")

    if args.json:
        stats = {
            "profiles": profile_count,
            "venues": venue_count,
            "events": event_count,
            "posts_by_classification": {row[0]: row[1] for row in post_stats},
            "posts_per_profile": {row[0]: row[1] for row in posts_per_profile},
        }
        print("\n" + json.dumps(stats, indent=2))

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Instagram research CLI for newsletter events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python scripts/cli_instagram.py scrape --all
  uv run python scripts/cli_instagram.py scrape --handle wayside_cider
  uv run python scripts/cli_instagram.py list-posts --handle wayside_cider
  uv run python scripts/cli_instagram.py show-stats
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape Instagram accounts")
    scrape_group = scrape_parser.add_mutually_exclusive_group(required=True)
    scrape_group.add_argument("--all", action="store_true", help="Scrape all configured accounts")
    scrape_group.add_argument("--handle", type=str, help="Scrape specific handle")
    scrape_parser.add_argument("--limit", type=int, default=20, help="Max posts per account (default: 20)")
    scrape_parser.add_argument("--json", action="store_true", help="Output JSON results")
    scrape_parser.set_defaults(func=cmd_scrape)

    # list-posts command
    list_parser = subparsers.add_parser("list-posts", help="List posts from database")
    list_parser.add_argument("--handle", type=str, required=True, help="Instagram handle")
    list_parser.add_argument("--classified-only", action="store_true", help="Only show classified posts")
    list_parser.add_argument("--json", action="store_true", help="Output JSON")
    list_parser.set_defaults(func=cmd_list_posts)

    # show-stats command
    stats_parser = subparsers.add_parser("show-stats", help="Show database statistics")
    stats_parser.add_argument("--json", action="store_true", help="Output JSON")
    stats_parser.set_defaults(func=cmd_show_stats)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
