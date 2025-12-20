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

from schemas.event import (
    Event,
    EventCategory,
    EventCollection,
    EventSource,
    InstagramPost,
    InstagramProfile,
    PostImage,
    Venue,
)


CURRENT_SCHEMA_VERSION = "2.1.0"

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Instagram profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instagram_id TEXT UNIQUE NOT NULL,
    handle TEXT NOT NULL,
    full_name TEXT,
    bio TEXT,
    followers_count INTEGER,
    following_count INTEGER,
    post_count INTEGER,
    profile_pic_url TEXT,
    is_verified INTEGER DEFAULT 0 CHECK(is_verified IN (0, 1)),
    external_url TEXT,
    last_scraped_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_profiles_handle ON profiles(handle);
CREATE INDEX IF NOT EXISTS idx_profiles_instagram_id ON profiles(instagram_id);

-- Instagram posts table
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    instagram_post_id TEXT UNIQUE NOT NULL,
    shortcode TEXT,
    post_url TEXT NOT NULL,
    caption TEXT,
    media_type TEXT CHECK(media_type IN ('photo', 'video', 'carousel', 'reel')),
    display_url TEXT,
    image_count INTEGER DEFAULT 1,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    posted_at TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    classification TEXT CHECK(classification IN ('event', 'not_event', 'ambiguous')),
    classification_reason TEXT,
    needs_image_analysis INTEGER DEFAULT 1 CHECK(needs_image_analysis IN (0, 1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_posts_profile_id ON posts(profile_id);
CREATE INDEX IF NOT EXISTS idx_posts_instagram_post_id ON posts(instagram_post_id);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_posts_shortcode ON posts(shortcode);

-- Post images table (for carousel images)
CREATE TABLE IF NOT EXISTS post_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    image_index INTEGER NOT NULL DEFAULT 0,
    file_path TEXT,
    downloaded_at TEXT,
    analyzed_at TEXT,
    is_event_flyer INTEGER DEFAULT 0 CHECK(is_event_flyer IN (0, 1)),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, image_index)
);

CREATE INDEX IF NOT EXISTS idx_post_images_post_id ON post_images(post_id);

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

-- Events table with foreign key to venues and posts
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_key TEXT UNIQUE NOT NULL,
    venue_id INTEGER NOT NULL,
    post_id INTEGER,

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

    FOREIGN KEY (venue_id) REFERENCES venues(id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE SET NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_venue_id ON events(venue_id);
CREATE INDEX IF NOT EXISTS idx_events_post_id ON events(post_id);
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
        """Run schema migrations."""
        if from_version == "1.0.0":
            self._migrate_1_0_0_to_2_0_0(conn)
            from_version = "2.0.0"

        if from_version == "2.0.0":
            self._migrate_2_0_0_to_2_1_0(conn)

        conn.execute(
            "UPDATE schema_metadata SET value = ? WHERE key = 'version'",
            (CURRENT_SCHEMA_VERSION,),
        )

    def _migrate_1_0_0_to_2_0_0(self, conn: sqlite3.Connection) -> None:
        """Migrate from 1.0.0 to 2.0.0: Add profiles, posts tables, and post_id FK."""
        # Create profiles table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instagram_id TEXT UNIQUE NOT NULL,
                handle TEXT NOT NULL,
                full_name TEXT,
                bio TEXT,
                followers_count INTEGER,
                following_count INTEGER,
                post_count INTEGER,
                profile_pic_url TEXT,
                is_verified INTEGER DEFAULT 0 CHECK(is_verified IN (0, 1)),
                external_url TEXT,
                last_scraped_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_profiles_handle ON profiles(handle)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_profiles_instagram_id ON profiles(instagram_id)")

        # Create posts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                instagram_post_id TEXT UNIQUE NOT NULL,
                shortcode TEXT,
                post_url TEXT NOT NULL,
                caption TEXT,
                media_type TEXT CHECK(media_type IN ('photo', 'video', 'carousel', 'reel')),
                display_url TEXT,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                posted_at TEXT NOT NULL,
                scraped_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_profile_id ON posts(profile_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_instagram_post_id ON posts(instagram_post_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_shortcode ON posts(shortcode)")

        # Add post_id column to events table
        conn.execute("ALTER TABLE events ADD COLUMN post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_post_id ON events(post_id)")

    def _migrate_2_0_0_to_2_1_0(self, conn: sqlite3.Connection) -> None:
        """Migrate from 2.0.0 to 2.1.0: Add post_images table and classification fields."""
        # Add new columns to posts table
        conn.execute("ALTER TABLE posts ADD COLUMN image_count INTEGER DEFAULT 1")
        conn.execute("ALTER TABLE posts ADD COLUMN classification TEXT CHECK(classification IN ('event', 'not_event', 'ambiguous'))")
        conn.execute("ALTER TABLE posts ADD COLUMN classification_reason TEXT")
        conn.execute("ALTER TABLE posts ADD COLUMN needs_image_analysis INTEGER DEFAULT 1 CHECK(needs_image_analysis IN (0, 1))")

        # Create post_images table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS post_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                image_index INTEGER NOT NULL DEFAULT 0,
                file_path TEXT,
                downloaded_at TEXT,
                analyzed_at TEXT,
                is_event_flyer INTEGER DEFAULT 0 CHECK(is_event_flyer IN (0, 1)),
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                UNIQUE(post_id, image_index)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_post_images_post_id ON post_images(post_id)")

        # Migrate existing display_url to post_images for existing posts
        conn.execute("""
            INSERT INTO post_images (post_id, image_url, image_index)
            SELECT id, display_url, 0 FROM posts WHERE display_url IS NOT NULL
        """)

    def _find_or_create_profile(
        self, conn: sqlite3.Connection, profile: InstagramProfile
    ) -> int:
        """Find existing profile by instagram_id or create new one."""
        existing = conn.execute(
            "SELECT id FROM profiles WHERE instagram_id = ?",
            (profile.instagram_id,),
        ).fetchone()

        if existing:
            self._update_profile(conn, existing["id"], profile)
            return existing["id"]

        return self._insert_profile(conn, profile)

    def _update_profile(
        self, conn: sqlite3.Connection, profile_id: int, profile: InstagramProfile
    ) -> None:
        """Update profile with any new non-null fields."""
        conn.execute(
            """
            UPDATE profiles SET
                handle = ?,
                full_name = COALESCE(?, full_name),
                bio = COALESCE(?, bio),
                followers_count = COALESCE(?, followers_count),
                following_count = COALESCE(?, following_count),
                post_count = COALESCE(?, post_count),
                profile_pic_url = COALESCE(?, profile_pic_url),
                is_verified = ?,
                external_url = COALESCE(?, external_url),
                last_scraped_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                profile.handle,
                profile.full_name,
                profile.bio,
                profile.followers_count,
                profile.following_count,
                profile.post_count,
                profile.profile_pic_url,
                1 if profile.is_verified else 0,
                profile.external_url,
                profile_id,
            ),
        )

    def _insert_profile(self, conn: sqlite3.Connection, profile: InstagramProfile) -> int:
        """Insert new profile and return its ID."""
        cursor = conn.execute(
            """
            INSERT INTO profiles (
                instagram_id, handle, full_name, bio, followers_count,
                following_count, post_count, profile_pic_url, is_verified,
                external_url, last_scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                profile.instagram_id,
                profile.handle,
                profile.full_name,
                profile.bio,
                profile.followers_count,
                profile.following_count,
                profile.post_count,
                profile.profile_pic_url,
                1 if profile.is_verified else 0,
                profile.external_url,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def _find_or_create_post(
        self, conn: sqlite3.Connection, post: InstagramPost, profile_id: int
    ) -> int:
        """Find existing post by instagram_post_id or create new one."""
        existing = conn.execute(
            "SELECT id FROM posts WHERE instagram_post_id = ?",
            (post.instagram_post_id,),
        ).fetchone()

        if existing:
            self._update_post(conn, existing["id"], post)
            return existing["id"]

        return self._insert_post(conn, post, profile_id)

    def _update_post(
        self, conn: sqlite3.Connection, post_id: int, post: InstagramPost
    ) -> None:
        """Update post with latest data."""
        conn.execute(
            """
            UPDATE posts SET
                shortcode = COALESCE(?, shortcode),
                post_url = ?,
                caption = ?,
                media_type = ?,
                display_url = COALESCE(?, display_url),
                image_count = ?,
                like_count = ?,
                comment_count = ?,
                classification = COALESCE(?, classification),
                classification_reason = COALESCE(?, classification_reason),
                needs_image_analysis = ?,
                scraped_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                post.shortcode,
                post.post_url,
                post.caption,
                post.media_type,
                post.display_url,
                post.image_count,
                post.like_count,
                post.comment_count,
                post.classification,
                post.classification_reason,
                1 if post.needs_image_analysis else 0,
                post_id,
            ),
        )
        # Update post_images for this post
        self._save_post_images(conn, post_id, post.image_urls)

    def _insert_post(
        self, conn: sqlite3.Connection, post: InstagramPost, profile_id: int
    ) -> int:
        """Insert new post and return its ID."""
        cursor = conn.execute(
            """
            INSERT INTO posts (
                profile_id, instagram_post_id, shortcode, post_url, caption,
                media_type, display_url, image_count, like_count, comment_count,
                classification, classification_reason, needs_image_analysis,
                posted_at, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                profile_id,
                post.instagram_post_id,
                post.shortcode,
                post.post_url,
                post.caption,
                post.media_type,
                post.display_url,
                post.image_count,
                post.like_count,
                post.comment_count,
                post.classification,
                post.classification_reason,
                1 if post.needs_image_analysis else 0,
                post.posted_at.isoformat(),
            ),
        )
        post_id = cursor.lastrowid
        # Save post_images for this post
        self._save_post_images(conn, post_id, post.image_urls)  # type: ignore[arg-type]
        return post_id  # type: ignore[return-value]

    def _save_post_images(
        self, conn: sqlite3.Connection, post_id: int, image_urls: list[str]
    ) -> None:
        """Save or update post images for a post."""
        # Delete existing images for this post (to handle updates)
        conn.execute("DELETE FROM post_images WHERE post_id = ?", (post_id,))

        # Insert new images
        for index, url in enumerate(image_urls):
            if url:
                conn.execute(
                    """
                    INSERT INTO post_images (post_id, image_url, image_index)
                    VALUES (?, ?, ?)
                    """,
                    (post_id, url, index),
                )

    def save_instagram_scrape(
        self,
        profile: InstagramProfile,
        posts: list[InstagramPost],
        events_by_post: dict[str, list[Event]],
    ) -> SaveResult:
        """
        Save profile, posts, and extracted events atomically.

        Args:
            profile: Instagram profile data
            posts: List of posts from the profile
            events_by_post: Dict mapping instagram_post_id -> list of extracted events

        Returns:
            SaveResult with counts of saved/updated records
        """
        saved = 0
        updated = 0
        errors: list[tuple[str, str]] = []

        with self._connection() as conn:
            # 1. Save/update profile
            profile_id = self._find_or_create_profile(conn, profile)

            # 2. Save/update posts and link events
            for post in posts:
                try:
                    post_db_id = self._find_or_create_post(conn, post, profile_id)

                    # Link events to this post
                    for event in events_by_post.get(post.instagram_post_id, []):
                        event.post_id = post_db_id
                        venue_id = self._find_or_create_venue(conn, event.venue)
                        result = self._upsert_event(conn, event, venue_id)
                        if result == "saved":
                            saved += 1
                        else:
                            updated += 1
                except Exception as e:
                    errors.append((post.instagram_post_id, str(e)))

        return SaveResult(saved=saved, updated=updated, errors=errors if errors else None)

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
            event.post_id,
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
                    venue_id = ?, post_id = ?, updated_at = CURRENT_TIMESTAMP
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
                    venue_id, post_id, unique_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            post_id=row["post_id"] if "post_id" in row.keys() else None,
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
