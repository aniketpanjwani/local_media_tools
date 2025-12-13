"""Pytest configuration and fixtures."""

import sys
from datetime import date, time
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.event import Event, EventCategory, EventSource, Venue


@pytest.fixture
def sample_venue() -> Venue:
    """Create a sample venue for testing."""
    return Venue(
        name="The Avalon Lounge",
        city="Catskill",
        state="NY",
        instagram_handle="theavalonlounge",
    )


@pytest.fixture
def sample_event(sample_venue: Venue) -> Event:
    """Create a sample event for testing."""
    return Event(
        title="Live Music: Blue Ranger Jake",
        venue=sample_venue,
        event_date=date(2025, 12, 15),
        source=EventSource.INSTAGRAM,
        start_time=time(20, 0),
        category=EventCategory.MUSIC,
        description="Great local act performing originals and covers.",
    )


@pytest.fixture
def tmp_path_factory_session(tmp_path_factory):
    """Session-scoped temporary directory."""
    return tmp_path_factory.mktemp("newsletter_events")
