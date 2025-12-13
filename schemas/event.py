"""
Event data models with Pydantic validation.

These schemas standardize event data from various sources (Instagram, Facebook, etc.)
into a common format for newsletter generation.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Any
import hashlib

from pydantic import BaseModel, Field, field_validator


class EventSource(str, Enum):
    """Source platform for event data."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    EVENTBRITE = "eventbrite"
    MANUAL = "manual"


class EventCategory(str, Enum):
    """Category for newsletter organization."""

    MUSIC = "music"
    FOOD_DRINK = "food_drink"
    ART = "art"
    COMMUNITY = "community"
    OUTDOOR = "outdoor"
    MARKET = "market"
    WORKSHOP = "workshop"
    OTHER = "other"


class Venue(BaseModel):
    """Venue information with validation."""

    name: str = Field(..., min_length=1, description="Venue name")
    city: str | None = None
    address: str | None = None
    state: str = "NY"
    instagram_handle: str | None = None
    website: str | None = None
    coordinates: tuple[float, float] | None = None  # (lat, lon)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("instagram_handle")
    @classmethod
    def strip_at_symbol(cls, v: str | None) -> str | None:
        if v:
            return v.lstrip("@").strip()
        return v


class Event(BaseModel):
    """
    Normalized event data from any source.

    The unique_key is computed automatically based on title, date, and venue
    to enable cross-source deduplication.
    """

    # Required fields
    title: str = Field(..., min_length=1, description="Event title")
    venue: Venue
    event_date: date
    source: EventSource

    # Optional fields
    start_time: time | None = None
    end_time: time | None = None
    description: str | None = None
    short_description: str | None = None
    category: EventCategory = EventCategory.OTHER
    price: str | None = None
    is_free: bool = False
    ticket_url: str | None = None
    event_url: str | None = None
    image_url: str | None = None
    source_url: str | None = None
    source_id: str | None = None

    # Metadata
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    needs_review: bool = False
    review_notes: str | None = None
    scraped_at: datetime | None = None

    # Computed (set in model_post_init)
    unique_key: str = ""

    def model_post_init(self, __context: Any) -> None:
        """Compute unique_key after initialization."""
        if not self.unique_key:
            object.__setattr__(self, "unique_key", self._compute_unique_key())

    def _compute_unique_key(self) -> str:
        """Generate stable hash for deduplication."""
        normalized_title = self.title.lower().strip()
        normalized_venue = self.venue.name.lower().strip()
        key_string = f"{normalized_title}|{self.event_date.isoformat()}|{normalized_venue}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]

    @property
    def day_of_week(self) -> str:
        """Return day of week for newsletter grouping."""
        return self.event_date.strftime("%A").upper()

    @property
    def formatted_date(self) -> str:
        """Return formatted date string."""
        return self.event_date.strftime("%B %d")

    @property
    def formatted_time(self) -> str:
        """Return formatted time string."""
        if not self.start_time:
            return ""
        start = self.start_time.strftime("%-I:%M%p").lower()
        if self.end_time:
            end = self.end_time.strftime("%-I:%M%p").lower()
            return f"{start}-{end}"
        return start


class EventCollection(BaseModel):
    """Collection of events with deduplication support."""

    events: list[Event] = Field(default_factory=list)
    week_start: date | None = None
    week_end: date | None = None
    schema_version: str = "1.0.0"

    def add_event(self, event: Event) -> bool:
        """Add event if not duplicate. Returns True if added."""
        existing_keys = {e.unique_key for e in self.events}
        if event.unique_key in existing_keys:
            return False
        self.events.append(event)
        return True

    def get_events_by_day(self) -> dict[str, list[Event]]:
        """Group events by day of week."""
        by_day: dict[str, list[Event]] = {}
        for event in sorted(self.events, key=lambda e: e.event_date):
            day = event.day_of_week
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(event)
        return by_day
