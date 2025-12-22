#!/usr/bin/env python3
"""
CLI tool for event database operations.

This CLI handles the FRAGILE parts of event management:
- Correct path resolution
- Schema validation via Pydantic
- Database operations with proper types

Usage:
    uv run python scripts/cli_events.py save --json '{"title": "...", ...}'
    uv run python scripts/cli_events.py save-batch --file events.json
    uv run python scripts/cli_events.py query --from 2025-01-01 --to 2025-01-07
    uv run python scripts/cli_events.py stats
"""

import argparse
import json
import re
import sys
from datetime import date, time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.paths import get_database_path
from schemas.sqlite_storage import SqliteStorage
from schemas.event import Event, Venue, EventSource, EventCategory, EventCollection


def parse_time(time_str: str | None) -> time | None:
    """
    Parse time string to time object.

    Handles various formats:
    - "19:00", "19:30" (24-hour)
    - "7:00 PM", "7:30 pm" (12-hour with space)
    - "7pm", "7:30pm" (12-hour compact)
    - "7 PM", "7 pm" (hour only)

    Returns None for invalid/empty strings.
    """
    if not time_str:
        return None

    time_str = time_str.strip().upper()

    # Try 24-hour format first: "19:00", "19:30"
    match = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)

    # Try 12-hour format: "7:00 PM", "7:30pm", "7 PM", "7pm"
    match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$", time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        is_pm = match.group(3) == "PM"

        if hour == 12:
            hour = 0 if not is_pm else 12
        elif is_pm:
            hour += 12

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)

    return None


def parse_category(category_str: str | None) -> EventCategory:
    """Parse category string to EventCategory enum."""
    if not category_str:
        return EventCategory.OTHER

    category_str = category_str.lower().strip()
    category_map = {
        "music": EventCategory.MUSIC,
        "food_drink": EventCategory.FOOD_DRINK,
        "food": EventCategory.FOOD_DRINK,
        "drink": EventCategory.FOOD_DRINK,
        "art": EventCategory.ART,
        "community": EventCategory.COMMUNITY,
        "outdoor": EventCategory.OUTDOOR,
        "market": EventCategory.MARKET,
        "workshop": EventCategory.WORKSHOP,
        "other": EventCategory.OTHER,
    }
    return category_map.get(category_str, EventCategory.OTHER)


def cmd_save(args: argparse.Namespace) -> int:
    """Save a single event from JSON."""
    try:
        data = json.loads(args.json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "invalid_json", "message": str(e)}), file=sys.stdout)
        return 1

    # Validate required fields
    required = ["title", "venue_name", "event_date"]
    missing = [f for f in required if f not in data or not data[f]]
    if missing:
        print(
            json.dumps({"error": "missing_fields", "fields": missing}),
            file=sys.stdout,
        )
        return 1

    try:
        storage = SqliteStorage(get_database_path())

        event = Event(
            title=data["title"],
            venue=Venue(
                name=data["venue_name"],
                city=data.get("venue_city"),
                address=data.get("venue_address"),
            ),
            event_date=date.fromisoformat(data["event_date"]),
            start_time=parse_time(data.get("start_time")),
            end_time=parse_time(data.get("end_time")),
            source=EventSource(data.get("source", "web_aggregator")),
            source_url=data.get("source_url"),
            description=data.get("description"),
            short_description=data.get("short_description"),
            category=parse_category(data.get("category")),
            price=data.get("price"),
            is_free=data.get("is_free", False),
            ticket_url=data.get("ticket_url"),
            event_url=data.get("event_url"),
            image_url=data.get("image_url"),
            confidence=data.get("confidence", 0.8),
            needs_review=data.get("needs_review", True),
            review_notes=data.get("review_notes"),
        )

        result = storage.save(EventCollection(events=[event]))
        print(
            json.dumps(
                {
                    "success": True,
                    "saved": result.saved,
                    "updated": result.updated,
                    "unique_key": event.unique_key,
                    "title": event.title,
                }
            )
        )
        return 0

    except Exception as e:
        print(json.dumps({"error": "save_failed", "message": str(e)}), file=sys.stdout)
        return 1


def cmd_save_batch(args: argparse.Namespace) -> int:
    """Save multiple events from JSON file."""
    try:
        with open(args.file) as f:
            events_data = json.load(f)
    except FileNotFoundError:
        print(
            json.dumps({"error": "file_not_found", "path": args.file}), file=sys.stdout
        )
        return 1
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "invalid_json", "message": str(e)}), file=sys.stdout)
        return 1

    if not isinstance(events_data, list):
        print(
            json.dumps({"error": "invalid_format", "message": "Expected JSON array"}),
            file=sys.stdout,
        )
        return 1

    storage = SqliteStorage(get_database_path())
    events = []
    errors = []

    for i, data in enumerate(events_data):
        try:
            # Validate required fields
            required = ["title", "venue_name", "event_date"]
            missing = [f for f in required if f not in data or not data[f]]
            if missing:
                errors.append({"index": i, "error": "missing_fields", "fields": missing})
                continue

            event = Event(
                title=data["title"],
                venue=Venue(
                    name=data["venue_name"],
                    city=data.get("venue_city"),
                    address=data.get("venue_address"),
                ),
                event_date=date.fromisoformat(data["event_date"]),
                start_time=parse_time(data.get("start_time")),
                end_time=parse_time(data.get("end_time")),
                source=EventSource(data.get("source", "web_aggregator")),
                source_url=data.get("source_url"),
                description=data.get("description"),
                category=parse_category(data.get("category")),
                price=data.get("price"),
                ticket_url=data.get("ticket_url"),
                confidence=data.get("confidence", 0.8),
                needs_review=data.get("needs_review", True),
            )
            events.append(event)

        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    if events:
        result = storage.save(EventCollection(events=events))
        print(
            json.dumps(
                {
                    "success": True,
                    "saved": result.saved,
                    "updated": result.updated,
                    "total_input": len(events_data),
                    "total_processed": len(events),
                    "errors": errors if errors else None,
                }
            )
        )
    else:
        print(
            json.dumps(
                {
                    "success": False,
                    "message": "No valid events to save",
                    "errors": errors,
                }
            )
        )
        return 1

    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Query events by date range."""
    storage = SqliteStorage(get_database_path())

    try:
        date_from = date.fromisoformat(args.date_from) if args.date_from else None
        date_to = date.fromisoformat(args.date_to) if args.date_to else None
    except ValueError as e:
        print(json.dumps({"error": "invalid_date", "message": str(e)}), file=sys.stdout)
        return 1

    events = storage.query(date_from=date_from, date_to=date_to)

    output = []
    for event in events:
        output.append(
            {
                "title": event.title,
                "venue": event.venue.name,
                "venue_city": event.venue.city,
                "date": event.event_date.isoformat(),
                "day_of_week": event.event_date.strftime("%A"),
                "formatted_date": event.event_date.strftime("%B %d"),
                "time": event.start_time.strftime("%H:%M") if event.start_time else None,
                "description": event.description,
                "category": event.category.value if event.category else None,
                "price": event.price,
                "ticket_url": event.ticket_url,
                "event_url": event.event_url,
                "source_url": event.source_url,
                "unique_key": event.unique_key,
            }
        )

    print(json.dumps({"count": len(output), "events": output}, indent=2))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show event database statistics."""
    storage = SqliteStorage(get_database_path())

    with storage._connection() as conn:
        # Total events
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        # Events by source
        by_source = conn.execute(
            "SELECT source, COUNT(*) FROM events GROUP BY source ORDER BY COUNT(*) DESC"
        ).fetchall()

        # Events by category
        by_category = conn.execute(
            "SELECT category, COUNT(*) FROM events GROUP BY category ORDER BY COUNT(*) DESC"
        ).fetchall()

        # Events needing review
        needs_review = conn.execute(
            "SELECT COUNT(*) FROM events WHERE needs_review = 1"
        ).fetchone()[0]

        # Date range
        date_range = conn.execute(
            "SELECT MIN(event_date), MAX(event_date) FROM events"
        ).fetchone()

        # Unique venues
        venue_count = conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0]

    stats = {
        "total_events": total,
        "needs_review": needs_review,
        "unique_venues": venue_count,
        "date_range": {
            "earliest": date_range[0],
            "latest": date_range[1],
        },
        "by_source": {row[0]: row[1] for row in by_source},
        "by_category": {row[0]: row[1] for row in by_category},
    }

    print(json.dumps(stats, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Event database operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Save a single event
    uv run python scripts/cli_events.py save --json '{"title": "Jazz Night", "venue_name": "Blue Note", "event_date": "2025-01-20", "start_time": "7pm"}'

    # Save multiple events from file
    uv run python scripts/cli_events.py save-batch --file /tmp/events.json

    # Query events in date range
    uv run python scripts/cli_events.py query --from 2025-01-01 --to 2025-01-31

    # Show statistics
    uv run python scripts/cli_events.py stats
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # save command
    save_parser = subparsers.add_parser("save", help="Save single event from JSON")
    save_parser.add_argument(
        "--json", required=True, help="Event data as JSON string"
    )
    save_parser.set_defaults(func=cmd_save)

    # save-batch command
    batch_parser = subparsers.add_parser(
        "save-batch", help="Save events from JSON file"
    )
    batch_parser.add_argument(
        "--file", required=True, help="Path to JSON file with events array"
    )
    batch_parser.set_defaults(func=cmd_save_batch)

    # query command
    query_parser = subparsers.add_parser("query", help="Query events by date range")
    query_parser.add_argument(
        "--from", dest="date_from", help="Start date (YYYY-MM-DD)"
    )
    query_parser.add_argument("--to", dest="date_to", help="End date (YYYY-MM-DD)")
    query_parser.set_defaults(func=cmd_query)

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
