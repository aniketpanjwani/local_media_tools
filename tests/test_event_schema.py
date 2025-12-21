"""Tests for event schema validation."""

from datetime import date, time

import pytest
from pydantic import ValidationError

from schemas.event import (
    Event,
    EventCategory,
    EventCollection,
    EventSource,
    Venue,
    normalize_title,
)


class TestVenue:
    """Tests for Venue model."""

    def test_valid_venue(self):
        """Test creating a valid venue."""
        venue = Venue(name="Test Venue", city="Kingston", state="NY")
        assert venue.name == "Test Venue"
        assert venue.city == "Kingston"
        assert venue.state == "NY"

    def test_venue_strips_name(self):
        """Test that venue name is stripped of whitespace."""
        venue = Venue(name="  Test Venue  ")
        assert venue.name == "Test Venue"

    def test_venue_strips_at_symbol(self):
        """Test that @ is stripped from instagram handle."""
        venue = Venue(name="Test", instagram_handle="@testhandle")
        assert venue.instagram_handle == "testhandle"

    def test_venue_requires_name(self):
        """Test that venue requires a name."""
        with pytest.raises(ValidationError):
            Venue(name="")


class TestEvent:
    """Tests for Event model."""

    def test_valid_event(self, sample_venue):
        """Test creating a valid event."""
        event = Event(
            title="Test Event",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        assert event.title == "Test Event"
        assert event.venue.name == "The Avalon Lounge"
        assert event.source == EventSource.INSTAGRAM

    def test_event_generates_unique_key(self, sample_venue):
        """Test that unique_key is generated."""
        event = Event(
            title="Test Event",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        assert event.unique_key != ""
        assert len(event.unique_key) == 16

    def test_same_events_have_same_key(self, sample_venue):
        """Test that identical events have the same unique_key."""
        event1 = Event(
            title="Test Event",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Test Event",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.FACEBOOK,  # Different source
        )
        assert event1.unique_key == event2.unique_key

    def test_different_events_have_different_keys(self, sample_venue):
        """Test that different events have different unique_keys."""
        event1 = Event(
            title="Test Event 1",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Test Event 2",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        assert event1.unique_key != event2.unique_key

    def test_day_of_week_property(self, sample_event):
        """Test day_of_week property."""
        assert sample_event.day_of_week == "MONDAY"

    def test_formatted_date_property(self, sample_event):
        """Test formatted_date property."""
        assert sample_event.formatted_date == "December 15"

    def test_formatted_time_property(self, sample_event):
        """Test formatted_time property."""
        assert "8:00pm" in sample_event.formatted_time

    def test_confidence_validation(self, sample_venue):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            Event(
                title="Test",
                venue=sample_venue,
                event_date=date(2025, 12, 15),
                source=EventSource.MANUAL,
                confidence=1.5,
            )


class TestEventCollection:
    """Tests for EventCollection model."""

    def test_add_event(self, sample_event):
        """Test adding an event to collection."""
        collection = EventCollection()
        assert collection.add_event(sample_event) is True
        assert len(collection.events) == 1

    def test_add_duplicate_event(self, sample_event):
        """Test that duplicate events are rejected."""
        collection = EventCollection()
        collection.add_event(sample_event)
        assert collection.add_event(sample_event) is False
        assert len(collection.events) == 1

    def test_get_events_by_day(self, sample_venue):
        """Test grouping events by day."""
        collection = EventCollection()

        # Add events on different days
        event1 = Event(
            title="Monday Event",
            venue=sample_venue,
            event_date=date(2025, 12, 15),  # Monday
            source=EventSource.MANUAL,
        )
        event2 = Event(
            title="Tuesday Event",
            venue=sample_venue,
            event_date=date(2025, 12, 16),  # Tuesday
            source=EventSource.MANUAL,
        )

        collection.add_event(event1)
        collection.add_event(event2)

        by_day = collection.get_events_by_day()
        assert "MONDAY" in by_day
        assert "TUESDAY" in by_day
        assert len(by_day["MONDAY"]) == 1
        assert len(by_day["TUESDAY"]) == 1


class TestNormalizeTitle:
    """Tests for normalize_title function."""

    def test_basic_normalization(self):
        """Test basic lowercase and strip."""
        assert normalize_title("  Jazz Night  ") == "jazz night"

    def test_removes_live_prefix(self):
        """Test removing 'live:' prefix."""
        assert normalize_title("Live: Jazz Night") == "jazz night"

    def test_removes_tonight_prefix(self):
        """Test removing 'tonight:' prefix."""
        assert normalize_title("Tonight: Special Performance") == "special performance"

    def test_removes_presents_prefix(self):
        """Test removing 'presents:' prefix."""
        assert normalize_title("Presents: The Jazz Band") == "the jazz band"

    def test_removes_featuring_prefix(self):
        """Test removing 'featuring:' prefix."""
        assert normalize_title("Featuring: Artist Name") == "artist name"

    def test_removes_feat_prefix(self):
        """Test removing 'feat:' prefix."""
        assert normalize_title("Feat: Special Guest") == "special guest"

    def test_removes_punctuation(self):
        """Test removing punctuation."""
        assert normalize_title("Jazz Night! @ The Venue") == "jazz night the venue"

    def test_collapses_spaces(self):
        """Test collapsing multiple spaces."""
        assert normalize_title("Jazz    Night   at   Venue") == "jazz night at venue"

    def test_only_removes_one_prefix(self):
        """Test that only one prefix is removed."""
        # "live:" should be removed, leaving "presents: something"
        result = normalize_title("Live: Presents: Something")
        assert result == "presents something"

    def test_preserves_words_with_colons(self):
        """Test that colons within titles are handled."""
        assert normalize_title("Time: 8PM Jazz Night") == "time 8pm jazz night"

    def test_complex_normalization(self):
        """Test complex title with multiple transformations."""
        assert normalize_title("  LIVE: Jazz Night!! @ Colony  ") == "jazz night colony"


class TestNormalizedUniqueKey:
    """Tests for unique_key with title normalization."""

    def test_similar_titles_match(self, sample_venue):
        """Test that similar titles produce same unique_key."""
        event1 = Event(
            title="Jazz Night",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="JAZZ NIGHT!",  # Different case and punctuation
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.FACEBOOK,
        )
        assert event1.unique_key == event2.unique_key

    def test_prefix_variants_match(self, sample_venue):
        """Test that title with prefix matches without prefix."""
        event1 = Event(
            title="Jazz Night",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Live: Jazz Night",  # With prefix
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.FACEBOOK,
        )
        assert event1.unique_key == event2.unique_key

    def test_different_titles_dont_match(self, sample_venue):
        """Test that actually different titles have different keys."""
        event1 = Event(
            title="Jazz Night",
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        event2 = Event(
            title="Blues Night",  # Different content
            venue=sample_venue,
            event_date=date(2025, 12, 15),
            source=EventSource.INSTAGRAM,
        )
        assert event1.unique_key != event2.unique_key
