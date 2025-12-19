"""
Migrate events from JSON to SQLite storage.

Usage:
    python -m scripts.migrate_json_to_sqlite [--dry-run] [--no-backup]
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from schemas.event import EventCollection
from schemas.sqlite_storage import MigrationResult, SqliteStorage
from schemas.storage import EventStorage


def migrate_json_to_sqlite(
    json_path: Path,
    db_path: Path,
    backup: bool = True,
    dry_run: bool = False,
) -> MigrationResult:
    """
    Migrate events.json to events.db.

    Args:
        json_path: Path to existing JSON file
        db_path: Path where SQLite database will be created
        backup: Whether to backup JSON file before migration
        dry_run: If True, only report what would happen

    Returns:
        MigrationResult with status and details
    """
    # 1. Check if JSON exists
    json_storage = EventStorage(json_path)
    if not json_storage.exists():
        return MigrationResult(status="skipped", error="No JSON file found")

    # 2. Load and validate
    try:
        collection = json_storage.load(EventCollection)
    except Exception as e:
        return MigrationResult(status="failed", error=f"Failed to load JSON: {e}")

    # 3. Dry run - just report what would happen
    if dry_run:
        return MigrationResult(
            status="skipped",
            events_migrated=len(collection.events),
            error=f"Dry run: would migrate {len(collection.events)} events",
        )

    # 4. Backup JSON
    backup_path = None
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = json_path.with_suffix(f".json.{timestamp}.backup")
        shutil.copy(json_path, backup_path)

    # 5. Initialize SQLite and import
    sqlite_storage = SqliteStorage(db_path)
    result = sqlite_storage.save(collection)

    if result.errors:
        return MigrationResult(
            status="failed",
            events_migrated=result.saved + result.updated,
            backup_path=backup_path,
            error=f"Migration errors: {result.errors}",
        )

    # 6. Verify migration
    loaded = sqlite_storage.load()
    if len(loaded.events) != len(collection.events):
        return MigrationResult(
            status="failed",
            events_migrated=len(loaded.events),
            backup_path=backup_path,
            error=f"Event count mismatch: {len(loaded.events)} vs {len(collection.events)}",
        )

    return MigrationResult(
        status="success",
        events_migrated=len(collection.events),
        backup_path=backup_path,
    )


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate JSON events to SQLite")
    parser.add_argument(
        "--json-path",
        type=Path,
        default=Path("tmp/extraction/events.json"),
        help="Path to JSON file (default: tmp/extraction/events.json)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("tmp/extraction/events.db"),
        help="Path to SQLite database (default: tmp/extraction/events.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen without migrating",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of JSON file",
    )

    args = parser.parse_args()

    print(f"Migrating {args.json_path} -> {args.db_path}")

    result = migrate_json_to_sqlite(
        json_path=args.json_path,
        db_path=args.db_path,
        backup=not args.no_backup,
        dry_run=args.dry_run,
    )

    if result.status == "success":
        print(f"Success: Migrated {result.events_migrated} events")
        if result.backup_path:
            print(f"Backup: {result.backup_path}")
    elif result.status == "skipped":
        print(f"Skipped: {result.error}")
    else:
        print(f"Failed: {result.error}")
        exit(1)


if __name__ == "__main__":
    main()
