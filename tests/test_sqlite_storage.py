"""Tests for SQLite storage backend."""

from datetime import date, time
from pathlib import Path

import pytest

from schemas.event import Event, EventCategory, EventCollection, EventSource, Venue
from schemas.sqlite_storage import CURRENT_SCHEMA_VERSION, SqliteStorage, SaveResult


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Temporary database path."""
    return tmp_path / "test_events.db"


@pytest.fixture
def sample_venue() -> Venue:
    """Sample venue for testing."""
    return Venue(
        name="Test Venue",
        city="Kingston",
        state="NY",
        address="123 Main St",
        instagram_handle="testvenue",
    )


@pytest.fixture
def sample_event(sample_venue: Venue) -> Event:
    """Sample event for testing."""
    return Event(
        title="Test Concert",
        venue=sample_venue,
        event_date=date(2025, 1, 20),
        source=EventSource.INSTAGRAM,
        start_time=time(20, 0),
        description="A test concert",
        category=EventCategory.MUSIC,
    )


class TestSqliteStorageInit:
    """Tests for database initialization."""

    def test_create_database(self, temp_db: Path) -> None:
        """Database file created with schema."""
        storage = SqliteStorage(temp_db)
        assert temp_db.exists()

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        """Parent directory created if missing."""
        db_path = tmp_path / "nested" / "dir" / "test.db"
        storage = SqliteStorage(db_path)
        assert db_path.exists()

    def test_schema_version_set(self, temp_db: Path) -> None:
        """Schema version stored in metadata table."""
        storage = SqliteStorage(temp_db)
        with storage._connection() as conn:
            result = conn.execute(
                "SELECT value FROM schema_metadata WHERE key = 'version'"
            ).fetchone()
            assert result is not None
            assert result[0] == CURRENT_SCHEMA_VERSION


class TestSaveAndLoad:
    """Tests for save and load operations."""

    def test_save_and_load_single_event(
        self, temp_db: Path, sample_event: Event
    ) -> None:
        """Single event saved and loaded correctly."""
        storage = SqliteStorage(temp_db)
        collection = EventCollection(events=[sample_event])

        result = storage.save(collection)
        assert result.saved == 1
        assert result.updated == 0
        assert result.errors is None

        loaded = storage.load()
        assert len(loaded.events) == 1
        assert loaded.events[0].title == sample_event.title
        assert loaded.events[0].event_date == sample_event.event_date
        assert loaded.events[0].venue.name == sample_event.venue.name

    def test_save_multiple_events(self, temp_db: Path, sample_venue: Venue) -> None:
        """Multiple events saved correctly."""
        storage = SqliteStorage(temp_db)

        events = [
            Event(
                title=f"Event {i}",
                venue=sample_venue,
                event_date=date(2025, 1, 20 + i),
                source=EventSource.INSTAGRAM,
            )
            for i in range(3)
        ]
        collection = EventCollection(events=events)

        result = storage.save(collection)
        assert result.saved == 3

        loaded = storage.load()
        assert len(loaded.events) == 3

    def test_upsert_duplicate_updates(
        self, temp_db: Path, sample_event: Event
    ) -> None:
        """Duplicate unique_key updates instead of inserting."""
        storage = SqliteStorage(temp_db)

        # First save
        storage.save(EventCollection(events=[sample_event]))

        # Modify and save again (same unique_key)
        sample_event.description = "Updated description"
        result = storage.save(EventCollection(events=[sample_event]))

        assert result.saved == 0
        assert result.updated == 1

        loaded = storage.load()
        assert len(loaded.events) == 1
        assert loaded.events[0].description == "Updated description"

    def test_load_empty_database(self, temp_db: Path) -> None:
        """Loading empty database returns empty collection."""
        storage = SqliteStorage(temp_db)
        loaded = storage.load()
        assert len(loaded.events) == 0


class TestVenueDeduplication:
    """Tests for venue matching and deduplication."""

    def test_same_venue_creates_single_record(self, temp_db: Path) -> None:
        """Multiple events at same venue share one venue record."""
        storage = SqliteStorage(temp_db)
        venue = Venue(name="Shared Venue", city="Kingston", state="NY")

        event1 = Event(
            title="Event 1",
            venue=venue,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Event 2",
            venue=venue,
            event_date=date(2025, 1, 21),
            source=EventSource.FACEBOOK,
        )

        storage.save(EventCollection(events=[event1, event2]))

        assert storage.count_venues() == 1
        assert storage.count_events() == 2

    def test_instagram_handle_match(self, temp_db: Path) -> None:
        """Venues matched by instagram handle regardless of name."""
        storage = SqliteStorage(temp_db)

        venue1 = Venue(
            name="The Falcon",
            city="Marlboro",
            state="NY",
            instagram_handle="thefalcon",
        )
        venue2 = Venue(
            name="The Falcon Music Venue",  # Different name
            city="Marlboro",
            state="NY",
            instagram_handle="thefalcon",  # Same handle
        )

        event1 = Event(
            title="Event 1",
            venue=venue1,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Event 2",
            venue=venue2,
            event_date=date(2025, 1, 21),
            source=EventSource.FACEBOOK,
        )

        storage.save(EventCollection(events=[event1, event2]))

        # Should deduplicate to single venue
        assert storage.count_venues() == 1

    def test_fuzzy_name_match(self, temp_db: Path) -> None:
        """Venues with similar names (85%+ match) are deduplicated."""
        storage = SqliteStorage(temp_db)

        # "The Falcon Bar" vs "The Falcon Bar & Grill" = ~85% similar
        venue1 = Venue(name="The Falcon Bar", city="Marlboro", state="NY")
        venue2 = Venue(name="The Falcon Bars", city="Marlboro", state="NY")  # ~93% similar

        event1 = Event(
            title="Event 1",
            venue=venue1,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Event 2",
            venue=venue2,
            event_date=date(2025, 1, 21),
            source=EventSource.FACEBOOK,
        )

        storage.save(EventCollection(events=[event1, event2]))

        # Fuzzy match should deduplicate
        assert storage.count_venues() == 1

    def test_fuzzy_name_no_match_below_threshold(self, temp_db: Path) -> None:
        """Venues with names below 85% threshold are not deduplicated."""
        storage = SqliteStorage(temp_db)

        # "The Falcon" vs "The Falcon Venue" = ~77% similar (below threshold)
        venue1 = Venue(name="The Falcon", city="Marlboro", state="NY")
        venue2 = Venue(name="The Falcon Venue", city="Marlboro", state="NY")

        event1 = Event(
            title="Event 1",
            venue=venue1,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Event 2",
            venue=venue2,
            event_date=date(2025, 1, 21),
            source=EventSource.FACEBOOK,
        )

        storage.save(EventCollection(events=[event1, event2]))

        # Below threshold = separate venues
        assert storage.count_venues() == 2

    def test_different_city_no_match(self, temp_db: Path) -> None:
        """Same venue name in different cities creates separate records."""
        storage = SqliteStorage(temp_db)

        venue1 = Venue(name="Main Street Bar", city="Kingston", state="NY")
        venue2 = Venue(name="Main Street Bar", city="Poughkeepsie", state="NY")

        event1 = Event(
            title="Event 1",
            venue=venue1,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Event 2",
            venue=venue2,
            event_date=date(2025, 1, 21),
            source=EventSource.FACEBOOK,
        )

        storage.save(EventCollection(events=[event1, event2]))

        # Different cities = different venues
        assert storage.count_venues() == 2

    def test_venue_fields_updated(self, temp_db: Path) -> None:
        """New venue info updates existing record."""
        storage = SqliteStorage(temp_db)

        venue1 = Venue(name="Test Venue", city="Kingston", state="NY")
        venue2 = Venue(
            name="Test Venue",
            city="Kingston",
            state="NY",
            website="https://testvenue.com",
            instagram_handle="testvenue",
        )

        event1 = Event(
            title="Event 1",
            venue=venue1,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Event 2",
            venue=venue2,
            event_date=date(2025, 1, 21),
            source=EventSource.FACEBOOK,
        )

        storage.save(EventCollection(events=[event1]))
        storage.save(EventCollection(events=[event2]))

        # Venue should be updated with new fields
        loaded = storage.load()
        assert loaded.events[0].venue.website == "https://testvenue.com"


class TestQuery:
    """Tests for query functionality."""

    def test_query_by_date_range(self, temp_db: Path) -> None:
        """Filter events by date range."""
        storage = SqliteStorage(temp_db)

        events = [
            Event(
                title="Past",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 10),
                source=EventSource.INSTAGRAM,
            ),
            Event(
                title="Current",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.INSTAGRAM,
            ),
            Event(
                title="Future",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 30),
                source=EventSource.INSTAGRAM,
            ),
        ]
        storage.save(EventCollection(events=events))

        results = storage.query(date_from=date(2025, 1, 15), date_to=date(2025, 1, 25))
        assert len(results) == 1
        assert results[0].title == "Current"

    def test_query_by_source(self, temp_db: Path) -> None:
        """Filter events by source platform."""
        storage = SqliteStorage(temp_db)

        events = [
            Event(
                title="IG Event",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.INSTAGRAM,
            ),
            Event(
                title="FB Event",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.FACEBOOK,
            ),
        ]
        storage.save(EventCollection(events=events))

        results = storage.query(sources=[EventSource.INSTAGRAM])
        assert len(results) == 1
        assert results[0].title == "IG Event"

    def test_query_by_category(self, temp_db: Path) -> None:
        """Filter events by category."""
        storage = SqliteStorage(temp_db)

        events = [
            Event(
                title="Music Event",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.INSTAGRAM,
                category=EventCategory.MUSIC,
            ),
            Event(
                title="Food Event",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.INSTAGRAM,
                category=EventCategory.FOOD_DRINK,
            ),
        ]
        storage.save(EventCollection(events=events))

        results = storage.query(categories=[EventCategory.MUSIC])
        assert len(results) == 1
        assert results[0].title == "Music Event"

    def test_query_multiple_filters(self, temp_db: Path) -> None:
        """Combine multiple filters."""
        storage = SqliteStorage(temp_db)

        events = [
            Event(
                title="Match",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.INSTAGRAM,
                category=EventCategory.MUSIC,
            ),
            Event(
                title="Wrong Source",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.FACEBOOK,
                category=EventCategory.MUSIC,
            ),
            Event(
                title="Wrong Category",
                venue=Venue(name="V", city="C"),
                event_date=date(2025, 1, 20),
                source=EventSource.INSTAGRAM,
                category=EventCategory.FOOD_DRINK,
            ),
        ]
        storage.save(EventCollection(events=events))

        results = storage.query(
            sources=[EventSource.INSTAGRAM], categories=[EventCategory.MUSIC]
        )
        assert len(results) == 1
        assert results[0].title == "Match"

    def test_query_empty_filters_returns_all(
        self, temp_db: Path, sample_event: Event
    ) -> None:
        """Query with no filters returns all events."""
        storage = SqliteStorage(temp_db)
        storage.save(EventCollection(events=[sample_event]))

        results = storage.query()
        assert len(results) == 1


class TestEventFields:
    """Tests for event field preservation."""

    def test_all_fields_preserved(self, temp_db: Path) -> None:
        """All event fields saved and loaded correctly."""
        storage = SqliteStorage(temp_db)

        venue = Venue(
            name="Full Venue",
            city="Kingston",
            state="NY",
            address="123 Main St",
            instagram_handle="fullvenue",
            website="https://venue.com",
            coordinates=(41.9, -74.0),
        )

        event = Event(
            title="Full Event",
            venue=venue,
            event_date=date(2025, 1, 20),
            source=EventSource.INSTAGRAM,
            start_time=time(20, 0),
            end_time=time(23, 0),
            description="Full description",
            short_description="Short desc",
            category=EventCategory.MUSIC,
            price="$20",
            is_free=False,
            ticket_url="https://tickets.com",
            event_url="https://event.com",
            image_url="https://img.com/event.jpg",
            source_url="https://instagram.com/p/123",
            source_id="123",
            confidence=0.95,
            needs_review=True,
            review_notes="Check date",
        )

        storage.save(EventCollection(events=[event]))
        loaded = storage.load()

        assert len(loaded.events) == 1
        e = loaded.events[0]

        # Venue fields
        assert e.venue.name == venue.name
        assert e.venue.city == venue.city
        assert e.venue.state == venue.state
        assert e.venue.address == venue.address
        assert e.venue.instagram_handle == venue.instagram_handle
        assert e.venue.website == venue.website
        assert e.venue.coordinates == venue.coordinates

        # Event fields
        assert e.title == event.title
        assert e.event_date == event.event_date
        assert e.source == event.source
        assert e.start_time == event.start_time
        assert e.end_time == event.end_time
        assert e.description == event.description
        assert e.short_description == event.short_description
        assert e.category == event.category
        assert e.price == event.price
        assert e.is_free == event.is_free
        assert e.ticket_url == event.ticket_url
        assert e.event_url == event.event_url
        assert e.image_url == event.image_url
        assert e.source_url == event.source_url
        assert e.source_id == event.source_id
        assert e.confidence == event.confidence
        assert e.needs_review == event.needs_review
        assert e.review_notes == event.review_notes


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_exists(self, temp_db: Path) -> None:
        """Exists returns True after init."""
        storage = SqliteStorage(temp_db)
        assert storage.exists()

    def test_count_events(self, temp_db: Path, sample_event: Event) -> None:
        """Count events returns correct count."""
        storage = SqliteStorage(temp_db)
        assert storage.count_events() == 0

        storage.save(EventCollection(events=[sample_event]))
        assert storage.count_events() == 1

    def test_count_venues(self, temp_db: Path, sample_event: Event) -> None:
        """Count venues returns correct count."""
        storage = SqliteStorage(temp_db)
        assert storage.count_venues() == 0

        storage.save(EventCollection(events=[sample_event]))
        assert storage.count_venues() == 1


class TestProfileAndPostQueries:
    """Tests for profile and post query methods used for deduplication."""

    @pytest.fixture
    def sample_profile(self):
        """Sample Instagram profile."""
        from schemas.event import InstagramProfile

        return InstagramProfile(
            instagram_id="123456789",
            handle="testvenue",
            full_name="Test Venue",
            bio="A test venue bio",
            followers_count=1000,
            post_count=50,
        )

    @pytest.fixture
    def sample_posts(self):
        """Sample Instagram posts with classifications."""
        from datetime import datetime

        from schemas.event import InstagramPost

        return [
            InstagramPost(
                instagram_post_id="post_001",
                shortcode="ABC123",
                post_url="https://instagram.com/p/ABC123",
                caption="Jazz night this Friday!",
                media_type="photo",
                posted_at=datetime(2025, 1, 15, 12, 0),
                classification="event",
                classification_reason="Has future date",
                needs_image_analysis=False,
            ),
            InstagramPost(
                instagram_post_id="post_002",
                shortcode="DEF456",
                post_url="https://instagram.com/p/DEF456",
                caption="Thanks for coming last night!",
                media_type="photo",
                posted_at=datetime(2025, 1, 14, 12, 0),
                classification="not_event",
                classification_reason="Past event recap",
                needs_image_analysis=False,
            ),
            InstagramPost(
                instagram_post_id="post_003",
                shortcode="GHI789",
                post_url="https://instagram.com/p/GHI789",
                caption="",  # No caption - needs image analysis
                media_type="carousel",
                posted_at=datetime(2025, 1, 13, 12, 0),
                classification=None,  # Not yet classified
                classification_reason=None,
                needs_image_analysis=True,
            ),
        ]

    def test_get_profile_by_handle_returns_profile(
        self, temp_db: Path, sample_profile, sample_posts
    ) -> None:
        """get_profile_by_handle returns profile data when it exists."""
        storage = SqliteStorage(temp_db)

        # Save profile and posts
        storage.save_instagram_scrape(
            profile=sample_profile,
            posts=sample_posts[:2],  # Only classified posts
            events_by_post={},
        )

        result = storage.get_profile_by_handle("testvenue")
        assert result is not None
        assert result["handle"] == "testvenue"
        assert result["instagram_id"] == "123456789"
        assert result["full_name"] == "Test Venue"

    def test_get_profile_by_handle_strips_at_symbol(
        self, temp_db: Path, sample_profile, sample_posts
    ) -> None:
        """get_profile_by_handle works with @ prefix."""
        storage = SqliteStorage(temp_db)
        storage.save_instagram_scrape(
            profile=sample_profile,
            posts=sample_posts[:1],
            events_by_post={},
        )

        result = storage.get_profile_by_handle("@testvenue")
        assert result is not None
        assert result["handle"] == "testvenue"

    def test_get_profile_by_handle_returns_none_when_not_found(
        self, temp_db: Path
    ) -> None:
        """get_profile_by_handle returns None for unknown handle."""
        storage = SqliteStorage(temp_db)
        result = storage.get_profile_by_handle("nonexistent")
        assert result is None

    def test_get_posts_for_profile_returns_all_posts(
        self, temp_db: Path, sample_profile, sample_posts
    ) -> None:
        """get_posts_for_profile returns all posts for profile."""
        storage = SqliteStorage(temp_db)
        storage.save_instagram_scrape(
            profile=sample_profile,
            posts=sample_posts,
            events_by_post={},
        )

        result = storage.get_posts_for_profile("testvenue")
        assert len(result) == 3
        assert "post_001" in result
        assert "post_002" in result
        assert "post_003" in result

    def test_get_posts_for_profile_only_classified(
        self, temp_db: Path, sample_profile, sample_posts
    ) -> None:
        """get_posts_for_profile with only_classified=True filters unclassified posts."""
        storage = SqliteStorage(temp_db)
        storage.save_instagram_scrape(
            profile=sample_profile,
            posts=sample_posts,
            events_by_post={},
        )

        result = storage.get_posts_for_profile("testvenue", only_classified=True)
        assert len(result) == 2  # Only post_001 and post_002 have classification
        assert "post_001" in result
        assert "post_002" in result
        assert "post_003" not in result  # classification is None

    def test_get_posts_for_profile_contains_classification_data(
        self, temp_db: Path, sample_profile, sample_posts
    ) -> None:
        """get_posts_for_profile returns classification fields."""
        storage = SqliteStorage(temp_db)
        storage.save_instagram_scrape(
            profile=sample_profile,
            posts=sample_posts,
            events_by_post={},
        )

        result = storage.get_posts_for_profile("testvenue", only_classified=True)

        post_001 = result["post_001"]
        assert post_001["classification"] == "event"
        assert post_001["classification_reason"] == "Has future date"

        post_002 = result["post_002"]
        assert post_002["classification"] == "not_event"
        assert post_002["classification_reason"] == "Past event recap"

    def test_get_posts_for_profile_empty_for_unknown_handle(
        self, temp_db: Path
    ) -> None:
        """get_posts_for_profile returns empty dict for unknown handle."""
        storage = SqliteStorage(temp_db)
        result = storage.get_posts_for_profile("nonexistent")
        assert result == {}


class TestScrapedPages:
    """Tests for scraped_pages URL tracking."""

    def test_get_scraped_urls_empty(self, temp_db: Path) -> None:
        """get_scraped_urls_for_source returns empty set for new source."""
        storage = SqliteStorage(temp_db)
        result = storage.get_scraped_urls_for_source("New Source")
        assert result == set()

    def test_save_and_get_scraped_url(self, temp_db: Path) -> None:
        """save_scraped_page stores URL, get_scraped_urls_for_source retrieves it."""
        storage = SqliteStorage(temp_db)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/123", 2)

        result = storage.get_scraped_urls_for_source("HV Magazine")
        assert "https://hvmag.com/events/123" in result

    def test_save_multiple_urls_same_source(self, temp_db: Path) -> None:
        """Multiple URLs for same source are all retrieved."""
        storage = SqliteStorage(temp_db)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/1", 1)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/2", 2)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/3", 0)

        result = storage.get_scraped_urls_for_source("HV Magazine")
        assert len(result) == 3
        assert "https://hvmag.com/events/1" in result
        assert "https://hvmag.com/events/2" in result
        assert "https://hvmag.com/events/3" in result

    def test_urls_isolated_by_source(self, temp_db: Path) -> None:
        """URLs are isolated per source name."""
        storage = SqliteStorage(temp_db)
        storage.save_scraped_page("Source A", "https://a.com/1", 1)
        storage.save_scraped_page("Source B", "https://b.com/1", 1)

        result_a = storage.get_scraped_urls_for_source("Source A")
        result_b = storage.get_scraped_urls_for_source("Source B")

        assert "https://a.com/1" in result_a
        assert "https://b.com/1" not in result_a
        assert "https://b.com/1" in result_b
        assert "https://a.com/1" not in result_b

    def test_save_scraped_page_upserts(self, temp_db: Path) -> None:
        """Saving same URL twice updates instead of duplicating."""
        storage = SqliteStorage(temp_db)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/1", 1)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/1", 3)

        result = storage.get_scraped_urls_for_source("HV Magazine")
        assert len(result) == 1

        # Check events_extracted was updated
        page = storage.get_scraped_page("HV Magazine", "https://hvmag.com/events/1")
        assert page is not None
        assert page["events_extracted"] == 3

    def test_get_scraped_page_returns_details(self, temp_db: Path) -> None:
        """get_scraped_page returns full record details."""
        storage = SqliteStorage(temp_db)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/1", 5)

        page = storage.get_scraped_page("HV Magazine", "https://hvmag.com/events/1")
        assert page is not None
        assert page["source_name"] == "HV Magazine"
        assert page["url"] == "https://hvmag.com/events/1"
        assert page["events_extracted"] == 5
        assert "scraped_at" in page

    def test_get_scraped_page_returns_none_not_found(self, temp_db: Path) -> None:
        """get_scraped_page returns None for unknown URL."""
        storage = SqliteStorage(temp_db)
        result = storage.get_scraped_page("HV Magazine", "https://unknown.com/1")
        assert result is None

    def test_update_scraped_page_updates_record(self, temp_db: Path) -> None:
        """update_scraped_page updates existing record."""
        storage = SqliteStorage(temp_db)
        storage.save_scraped_page("HV Magazine", "https://hvmag.com/events/1", 2)

        result = storage.update_scraped_page("HV Magazine", "https://hvmag.com/events/1", 4)
        assert result is True

        page = storage.get_scraped_page("HV Magazine", "https://hvmag.com/events/1")
        assert page is not None
        assert page["events_extracted"] == 4

    def test_update_scraped_page_returns_false_not_found(self, temp_db: Path) -> None:
        """update_scraped_page returns False for unknown URL."""
        storage = SqliteStorage(temp_db)
        result = storage.update_scraped_page("HV Magazine", "https://unknown.com/1", 4)
        assert result is False
