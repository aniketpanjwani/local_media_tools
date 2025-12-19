"""
SQLite storage backend with type constraints and query support.

Provides normalized schema with separate venues and events tables,
venue deduplication via fuzzy matching, and parameterized queries.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Generator, Literal

from rapidfuzz import fuzz

from schemas.event import Event, EventCategory, EventCollection, EventSource, Venue


CURRENT_SCHEMA_VERSION = "1.0.0"

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Venues table (normalized)
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT,
    state TEXT DEFAULT 'NY',
    address TEXT,
    instagram_handle TEXT,
    website TEXT,
    lat REAL,
    lon REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, city, state)
);

-- Events table with foreign key to venues
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_key TEXT UNIQUE NOT NULL,
    venue_id INTEGER NOT NULL,

    -- Core fields
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    description TEXT,
    short_description TEXT,

    -- Categorization
    source TEXT NOT NULL CHECK(source IN ('instagram', 'facebook', 'eventbrite', 'manual', 'web_aggregator')),
    category TEXT DEFAULT 'other',

    -- Pricing
    price TEXT,
    is_free INTEGER DEFAULT 0 CHECK(is_free IN (0, 1)),
    ticket_url TEXT,
    event_url TEXT,

    -- Media
    image_url TEXT,
    source_url TEXT,
    source_id TEXT,

    -- Metadata
    confidence REAL DEFAULT 1.0,
    needs_review INTEGER DEFAULT 0 CHECK(needs_review IN (0, 1)),
    review_notes TEXT,
    scraped_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (venue_id) REFERENCES venues(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_venue_id ON events(venue_id);
CREATE INDEX IF NOT EXISTS idx_venues_instagram ON venues(instagram_handle);
"""


# Fuzzy match threshold for venue deduplication
VENUE_MATCH_THRESHOLD = 85


@dataclass
class SaveResult:
    """Result of save operation."""

    saved: int = 0
    updated: int = 0
    errors: list[tuple[str, str]] | None = None


@dataclass
class MigrationResult:
    """Result of JSON to SQLite migration."""

    status: Literal["success", "skipped", "failed"]
    events_migrated: int = 0
    backup_path: Path | None = None
    error: str | None = None


class SqliteStorage:
    """SQLite storage with type constraints and query support."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for safe connection handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create tables if not exist, run migrations."""
        with self._connection() as conn:
            conn.executescript(SCHEMA_SQL)
            self._ensure_schema_version(conn)

    def _ensure_schema_version(self, conn: sqlite3.Connection) -> None:
        """Check schema version and run migrations if needed."""
        result = conn.execute(
            "SELECT value FROM schema_metadata WHERE key = 'version'"
        ).fetchone()

        if result is None:
            conn.execute(
                "INSERT INTO schema_metadata (key, value) VALUES ('version', ?)",
                (CURRENT_SCHEMA_VERSION,),
            )
        elif result[0] != CURRENT_SCHEMA_VERSION:
            self._migrate_schema(conn, from_version=result[0])

    def _migrate_schema(self, conn: sqlite3.Connection, from_version: str) -> None:
        """Run schema migrations. Placeholder for future versions."""
        # Will be implemented when schema evolves
        pass

    def _find_or_create_venue(self, conn: sqlite3.Connection, venue: Venue) -> int:
        """Find existing venue (fuzzy match) or create new one."""
        # 1. Try instagram handle first (most reliable identifier)
        if venue.instagram_handle:
            existing = conn.execute(
                "SELECT id FROM venues WHERE instagram_handle = ?",
                (venue.instagram_handle,),
            ).fetchone()
            if existing:
                self._update_venue_fields(conn, existing["id"], venue)
                return existing["id"]

        # 2. Fuzzy name match within same city/state
        candidates = conn.execute(
            "SELECT id, name FROM venues WHERE city = ? AND state = ?",
            (venue.city, venue.state),
        ).fetchall()

        for candidate in candidates:
            similarity = fuzz.ratio(venue.name.lower(), candidate["name"].lower())
            if similarity >= VENUE_MATCH_THRESHOLD:
                self._update_venue_fields(conn, candidate["id"], venue)
                return candidate["id"]

        # 3. No match - create new venue
        return self._insert_venue(conn, venue)

    def _update_venue_fields(
        self, conn: sqlite3.Connection, venue_id: int, venue: Venue
    ) -> None:
        """Update venue with any new non-null fields."""
        conn.execute(
            """
            UPDATE venues SET
                instagram_handle = COALESCE(?, instagram_handle),
                website = COALESCE(?, website),
                address = COALESCE(?, address),
                lat = COALESCE(?, lat),
                lon = COALESCE(?, lon)
            WHERE id = ?
            """,
            (
                venue.instagram_handle,
                venue.website,
                venue.address,
                venue.coordinates[0] if venue.coordinates else None,
                venue.coordinates[1] if venue.coordinates else None,
                venue_id,
            ),
        )

    def _insert_venue(self, conn: sqlite3.Connection, venue: Venue) -> int:
        """Insert new venue and return its ID."""
        lat = venue.coordinates[0] if venue.coordinates else None
        lon = venue.coordinates[1] if venue.coordinates else None
        cursor = conn.execute(
            """
            INSERT INTO venues (name, city, state, address, instagram_handle, website, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                venue.name,
                venue.city,
                venue.state,
                venue.address,
                venue.instagram_handle,
                venue.website,
                lat,
                lon,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def _upsert_event(
        self, conn: sqlite3.Connection, event: Event, venue_id: int
    ) -> Literal["saved", "updated"]:
        """Insert or update event."""
        existing = conn.execute(
            "SELECT id FROM events WHERE unique_key = ?",
            (event.unique_key,),
        ).fetchone()

        event_data = (
            event.title,
            event.event_date.isoformat(),
            event.start_time.isoformat() if event.start_time else None,
            event.end_time.isoformat() if event.end_time else None,
            event.description,
            event.short_description,
            event.source.value,
            event.category.value if event.category else "other",
            event.price,
            1 if event.is_free else 0,
            event.ticket_url,
            event.event_url,
            event.image_url,
            event.source_url,
            event.source_id,
            event.confidence,
            1 if event.needs_review else 0,
            event.review_notes,
            event.scraped_at.isoformat() if event.scraped_at else None,
            venue_id,
        )

        if existing:
            conn.execute(
                """
                UPDATE events SET
                    title = ?, event_date = ?, start_time = ?, end_time = ?,
                    description = ?, short_description = ?, source = ?, category = ?,
                    price = ?, is_free = ?, ticket_url = ?, event_url = ?,
                    image_url = ?, source_url = ?, source_id = ?,
                    confidence = ?, needs_review = ?, review_notes = ?, scraped_at = ?,
                    venue_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE unique_key = ?
                """,
                (*event_data, event.unique_key),
            )
            return "updated"
        else:
            conn.execute(
                """
                INSERT INTO events (
                    title, event_date, start_time, end_time,
                    description, short_description, source, category,
                    price, is_free, ticket_url, event_url,
                    image_url, source_url, source_id,
                    confidence, needs_review, review_notes, scraped_at,
                    venue_id, unique_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*event_data, event.unique_key),
            )
            return "saved"

    def save(self, collection: EventCollection) -> SaveResult:
        """Save event collection with upsert semantics."""
        saved = 0
        updated = 0
        errors: list[tuple[str, str]] = []

        with self._connection() as conn:
            for event in collection.events:
                try:
                    venue_id = self._find_or_create_venue(conn, event.venue)
                    result = self._upsert_event(conn, event, venue_id)
                    if result == "saved":
                        saved += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append((event.unique_key, str(e)))

        return SaveResult(saved=saved, updated=updated, errors=errors if errors else None)

    def load(self) -> EventCollection:
        """Load all events from database."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT e.*, v.name as venue_name, v.city as venue_city,
                       v.state as venue_state, v.address as venue_address,
                       v.instagram_handle as venue_instagram_handle,
                       v.website as venue_website, v.lat as venue_lat, v.lon as venue_lon
                FROM events e
                JOIN venues v ON e.venue_id = v.id
                ORDER BY e.event_date
                """
            ).fetchall()

            events = [self._row_to_event(row) for row in rows]
            return EventCollection(events=events)

    def query(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        sources: list[EventSource] | None = None,
        categories: list[EventCategory] | None = None,
    ) -> list[Event]:
        """Query events with parameterized filters."""
        where_clauses: list[str] = []
        params: dict[str, str | int] = {}

        if date_from:
            where_clauses.append("e.event_date >= :date_from")
            params["date_from"] = date_from.isoformat()

        if date_to:
            where_clauses.append("e.event_date <= :date_to")
            params["date_to"] = date_to.isoformat()

        if sources:
            placeholders = ",".join(f":source_{i}" for i in range(len(sources)))
            where_clauses.append(f"e.source IN ({placeholders})")
            params.update({f"source_{i}": s.value for i, s in enumerate(sources)})

        if categories:
            placeholders = ",".join(f":cat_{i}" for i in range(len(categories)))
            where_clauses.append(f"e.category IN ({placeholders})")
            params.update({f"cat_{i}": c.value for i, c in enumerate(categories)})

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        query = f"""
            SELECT e.*, v.name as venue_name, v.city as venue_city,
                   v.state as venue_state, v.address as venue_address,
                   v.instagram_handle as venue_instagram_handle,
                   v.website as venue_website, v.lat as venue_lat, v.lon as venue_lon
            FROM events e
            JOIN venues v ON e.venue_id = v.id
            WHERE {where_sql}
            ORDER BY e.event_date
        """

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """Convert SQLite row to Event instance."""
        # Reconstruct Venue
        coordinates = None
        if row["venue_lat"] is not None and row["venue_lon"] is not None:
            coordinates = (row["venue_lat"], row["venue_lon"])

        venue = Venue(
            name=row["venue_name"],
            city=row["venue_city"],
            state=row["venue_state"],
            address=row["venue_address"],
            instagram_handle=row["venue_instagram_handle"],
            website=row["venue_website"],
            coordinates=coordinates,
        )

        # Convert types
        event_date = date.fromisoformat(row["event_date"])
        start_time = time.fromisoformat(row["start_time"]) if row["start_time"] else None
        end_time = time.fromisoformat(row["end_time"]) if row["end_time"] else None
        scraped_at = (
            datetime.fromisoformat(row["scraped_at"]) if row["scraped_at"] else None
        )

        return Event(
            title=row["title"],
            venue=venue,
            event_date=event_date,
            source=EventSource(row["source"]),
            start_time=start_time,
            end_time=end_time,
            description=row["description"],
            short_description=row["short_description"],
            category=EventCategory(row["category"]) if row["category"] else EventCategory.OTHER,
            price=row["price"],
            is_free=bool(row["is_free"]),
            ticket_url=row["ticket_url"],
            event_url=row["event_url"],
            image_url=row["image_url"],
            source_url=row["source_url"],
            source_id=row["source_id"],
            confidence=row["confidence"],
            needs_review=bool(row["needs_review"]),
            review_notes=row["review_notes"],
            scraped_at=scraped_at,
            unique_key=row["unique_key"],
        )

    def exists(self) -> bool:
        """Check if database file exists."""
        return self.db_path.exists()

    def count_events(self) -> int:
        """Return total number of events in database."""
        with self._connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
            return result[0] if result else 0

    def count_venues(self) -> int:
        """Return total number of venues in database."""
        with self._connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM venues").fetchone()
            return result[0] if result else 0
