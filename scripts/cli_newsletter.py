#!/usr/bin/env python3
"""
CLI tool for newsletter data loading.

This CLI handles the FRAGILE parts of newsletter generation:
- Correct path resolution
- Database queries with proper types
- Loading formatting preferences from config

Claude handles the CREATIVE parts:
- Interpreting natural language preferences
- Adapting descriptions to user style
- Generating formatted markdown

Usage:
    uv run python scripts/cli_newsletter.py load --days 7
    uv run python scripts/cli_newsletter.py load --from 2025-01-01 --to 2025-01-14
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.paths import get_database_path, get_sources_path
from schemas.sqlite_storage import SqliteStorage
from config.config_schema import AppConfig


def cmd_load(args: argparse.Namespace) -> int:
    """
    Load events and preferences for newsletter generation.

    Returns JSON that Claude uses to generate the newsletter.
    Claude interprets the formatting_preferences and applies them creatively.
    """
    # Load config
    sources_path = get_sources_path()
    if not sources_path.exists():
        print(
            json.dumps(
                {
                    "error": "config_not_found",
                    "message": f"Config file not found at {sources_path}",
                    "suggestion": "Run /newsletter-events:setup to create configuration",
                }
            ),
            file=sys.stdout,
        )
        return 1

    try:
        config = AppConfig.from_yaml(sources_path)
    except Exception as e:
        print(
            json.dumps({"error": "config_invalid", "message": str(e)}),
            file=sys.stdout,
        )
        return 1

    # Load storage
    db_path = get_database_path()
    if not db_path.exists():
        print(
            json.dumps(
                {
                    "error": "database_not_found",
                    "message": f"Database not found at {db_path}",
                    "suggestion": "Run /newsletter-events:research to scrape events first",
                }
            ),
            file=sys.stdout,
        )
        return 1

    storage = SqliteStorage(db_path)

    # Parse date range
    try:
        if args.date_from:
            start_date = date.fromisoformat(args.date_from)
        else:
            start_date = date.today()

        if args.date_to:
            end_date = date.fromisoformat(args.date_to)
        else:
            end_date = start_date + timedelta(days=args.days)
    except ValueError as e:
        print(
            json.dumps({"error": "invalid_date", "message": str(e)}),
            file=sys.stdout,
        )
        return 1

    # Query events
    events = storage.query(date_from=start_date, date_to=end_date)

    if not events:
        print(
            json.dumps(
                {
                    "error": "no_events",
                    "message": f"No events found from {start_date} to {end_date}",
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "suggestion": "Run /newsletter-events:research to scrape new events, or try a wider date range with --days 14",
                }
            ),
            file=sys.stdout,
        )
        return 1

    # Prepare event data - Claude will format this according to preferences
    events_data = []
    for event in events:
        events_data.append(
            {
                "title": event.title,
                "venue": event.venue.name,
                "venue_city": event.venue.city,
                "date": event.event_date.isoformat(),
                "day_of_week": event.event_date.strftime("%A"),
                "formatted_date": event.event_date.strftime("%B %d"),
                "time": (
                    event.start_time.strftime("%-I:%M %p")
                    if event.start_time
                    else None
                ),
                "description": event.description,  # Raw description - Claude adapts this
                "category": event.category.value if event.category else "other",
                "price": event.price,
                "is_free": event.is_free,
                "ticket_url": event.ticket_url,
                "event_url": event.event_url,
                "source_url": event.source_url,
            }
        )

    # Sort by date, then by time (events without time come first)
    events_data.sort(key=lambda e: (e["date"], e["time"] or ""))

    # Build output with all context Claude needs
    output = {
        "newsletter_name": config.newsletter.name,
        "region": config.newsletter.region,
        # Claude interprets this natural language to format the newsletter
        "formatting_preferences": config.newsletter.formatting_preferences,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "start_formatted": start_date.strftime("%B %d, %Y"),
            "end_formatted": end_date.strftime("%B %d, %Y"),
        },
        "event_count": len(events_data),
        "events": events_data,
    }

    print(json.dumps(output, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Load newsletter data (Claude generates the markdown)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Load events for next 7 days (default)
    uv run python scripts/cli_newsletter.py load

    # Load events for next 14 days
    uv run python scripts/cli_newsletter.py load --days 14

    # Load events for specific date range
    uv run python scripts/cli_newsletter.py load --from 2025-01-01 --to 2025-01-14

The output is JSON containing:
- newsletter_name, region: From config
- formatting_preferences: Natural language instructions for Claude
- events: Array of event objects with all fields
- date_range: Start and end dates

Claude then interprets the formatting_preferences and generates markdown.
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # load command
    load_parser = subparsers.add_parser(
        "load", help="Load events + preferences for Claude to format"
    )
    load_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days from today to include (default: 7)",
    )
    load_parser.add_argument(
        "--from",
        dest="date_from",
        help="Start date (YYYY-MM-DD), overrides --days",
    )
    load_parser.add_argument(
        "--to",
        dest="date_to",
        help="End date (YYYY-MM-DD)",
    )
    load_parser.set_defaults(func=cmd_load)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
