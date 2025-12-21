#!/usr/bin/env python
"""
Migration script to recompute all event unique_keys after normalization change.

This script should be run ONCE after upgrading to version 2.2.0 to ensure
existing events use the new normalize_title() function for their unique_keys.

Usage:
    uv run python scripts/migrate_unique_keys.py

What it does:
1. Loads all events from the database
2. Recomputes unique_key for each event using the new normalization
3. Updates the database with new unique_keys
4. Reports duplicates that were created (events that now have same key)
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

from schemas.event import normalize_title


def compute_new_unique_key(title: str, event_date: str, venue_name: str) -> str:
    """Compute unique key using new normalization."""
    import hashlib

    normalized = normalize_title(title)
    normalized_venue = venue_name.lower().strip()
    key_string = f"{normalized}|{event_date}|{normalized_venue}"
    return hashlib.md5(key_string.encode()).hexdigest()[:16]


def migrate_unique_keys(db_path: Path, dry_run: bool = False) -> dict:
    """
    Migrate all event unique_keys to use new normalization.

    Args:
        db_path: Path to SQLite database
        dry_run: If True, don't write changes, just report what would happen

    Returns:
        Dict with migration statistics
    """
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return {"status": "skipped", "reason": "database not found"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get all events with their current unique_key
    rows = conn.execute("""
        SELECT e.id, e.unique_key, e.title, e.event_date, v.name as venue_name
        FROM events e
        JOIN venues v ON e.venue_id = v.id
    """).fetchall()

    if not rows:
        print("No events found in database")
        conn.close()
        return {"status": "skipped", "reason": "no events"}

    print(f"Found {len(rows)} events to migrate")

    # Track changes and duplicates
    updates = []
    unchanged = 0
    new_keys: dict[str, list[int]] = defaultdict(list)

    for row in rows:
        old_key = row["unique_key"]
        new_key = compute_new_unique_key(
            row["title"], row["event_date"], row["venue_name"]
        )

        new_keys[new_key].append(row["id"])

        if old_key != new_key:
            updates.append((row["id"], old_key, new_key, row["title"]))
        else:
            unchanged += 1

    # Find duplicates (events with same new key)
    duplicates = {k: ids for k, ids in new_keys.items() if len(ids) > 1}

    print(f"\nMigration summary:")
    print(f"  - Unchanged: {unchanged}")
    print(f"  - To update: {len(updates)}")
    print(f"  - Duplicate groups: {len(duplicates)}")

    if duplicates:
        print(f"\nDuplicate events (will have same unique_key):")
        for key, ids in list(duplicates.items())[:10]:  # Show first 10
            print(f"  Key {key}: event IDs {ids}")
        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more groups")

    if dry_run:
        print("\nDRY RUN - no changes made")
        conn.close()
        return {
            "status": "dry_run",
            "unchanged": unchanged,
            "updates": len(updates),
            "duplicates": len(duplicates),
        }

    # Apply updates
    if updates:
        print(f"\nUpdating {len(updates)} unique_keys...")
        for event_id, old_key, new_key, title in updates:
            try:
                conn.execute(
                    "UPDATE events SET unique_key = ? WHERE id = ?",
                    (new_key, event_id),
                )
            except sqlite3.IntegrityError as e:
                # Duplicate key - this means two events now have the same key
                # Keep the existing one, mark this one for review
                print(f"  Duplicate found for event {event_id}: {title[:50]}")
                conn.execute(
                    "UPDATE events SET needs_review = 1, review_notes = ? WHERE id = ?",
                    (f"Duplicate after migration: {old_key} -> {new_key}", event_id),
                )

        conn.commit()
        print("Migration complete!")

    conn.close()

    return {
        "status": "success",
        "unchanged": unchanged,
        "updates": len(updates),
        "duplicates": len(duplicates),
    }


if __name__ == "__main__":
    import sys

    db_path = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"

    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN MODE - no changes will be made\n")

    result = migrate_unique_keys(db_path, dry_run=dry_run)
    print(f"\nResult: {result}")
