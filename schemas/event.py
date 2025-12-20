"""
Event data models with Pydantic validation.

These schemas standardize event data from various sources (Instagram, Facebook, etc.)
into a common format for newsletter generation.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Any, Literal
import hashlib

from pydantic import BaseModel, Field, field_validator


class EventSource(str, Enum):
    """Source platform for event data."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    EVENTBRITE = "eventbrite"
    MANUAL = "manual"
    WEB_AGGREGATOR = "web_aggregator"


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


class InstagramProfile(BaseModel):
    """Instagram profile/account data."""

    instagram_id: str = Field(..., description="Instagram's numeric account ID")
    handle: str = Field(..., description="Username without @")
    full_name: str | None = None
    bio: str | None = None
    followers_count: int | None = None
    following_count: int | None = None
    post_count: int | None = None
    profile_pic_url: str | None = None
    is_verified: bool = False
    external_url: str | None = None

    @field_validator("handle")
    @classmethod
    def strip_at_symbol(cls, v: str) -> str:
        return v.lstrip("@").strip()


class InstagramPost(BaseModel):
    """Instagram post data from ScrapeCreators API."""

    instagram_post_id: str = Field(..., description="Instagram's post ID (numeric string)")
    shortcode: str | None = Field(None, description="Post shortcode used in URLs")
    post_url: str
    caption: str | None = None
    media_type: Literal["photo", "video", "carousel", "reel"] = "photo"
    display_url: str | None = None
    image_urls: list[str] = Field(default_factory=list, description="All images (carousel or single)")
    image_count: int = Field(default=1, description="Number of images in post")
    like_count: int = 0
    comment_count: int = 0
    posted_at: datetime

    # Classification fields (set during workflow processing)
    classification: Literal["event", "not_event", "ambiguous"] | None = Field(
        default=None, description="Post classification result"
    )
    classification_reason: str | None = Field(
        default=None, description="Why the post was classified this way"
    )
    needs_image_analysis: bool = Field(
        default=True, description="Whether image analysis is needed for this post"
    )

    @classmethod
    def from_api_response(cls, node: dict[str, Any], scraped_at: datetime | None = None) -> "InstagramPost":
        """Create InstagramPost from ScrapeCreators API response node."""
        # Extract caption from nested structure
        caption = None
        if edges := node.get("edge_media_to_caption", {}).get("edges", []):
            caption = edges[0].get("node", {}).get("text")

        # Map __typename to media_type
        typename = node.get("__typename", "GraphImage")
        media_type_map = {
            "GraphImage": "photo",
            "GraphVideo": "video",
            "GraphSidecar": "carousel",
        }
        media_type = media_type_map.get(typename, "photo")

        # Extract all carousel images (or single image for non-carousel posts)
        image_urls: list[str] = []
        if typename == "GraphSidecar":
            # Carousel post - extract all images from edge_sidecar_to_children
            children = node.get("edge_sidecar_to_children", {}).get("edges", [])
            for child in children:
                child_node = child.get("node", {})
                if child_url := child_node.get("display_url"):
                    image_urls.append(child_url)
        else:
            # Single image/video post
            if display_url := node.get("display_url"):
                image_urls.append(display_url)

        # Determine if image analysis is needed (videos/reels have no static images)
        needs_image_analysis = media_type not in ("video", "reel")

        # Convert Unix timestamp to datetime
        posted_at = datetime.fromtimestamp(node.get("taken_at_timestamp", 0))

        return cls(
            instagram_post_id=node.get("id", ""),
            shortcode=node.get("shortcode"),
            post_url=node.get("url", ""),
            caption=caption,
            media_type=media_type,
            display_url=node.get("display_url"),
            image_urls=image_urls,
            image_count=len(image_urls) if image_urls else 1,
            like_count=node.get("edge_liked_by", {}).get("count", 0),
            comment_count=node.get("edge_media_to_comment", {}).get("count", 0),
            posted_at=posted_at,
            needs_image_analysis=needs_image_analysis,
        )


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

    # Instagram source (optional - only set for Instagram events)
    post_id: int | None = Field(default=None, description="FK to posts table (nullable for non-Instagram events)")

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
    schema_version: str = "1.0.0"
    scraped_at: datetime | None = None

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


class PostImage(BaseModel):
    """Individual image from an Instagram post (for carousel storage)."""

    post_id: int = Field(..., description="FK to posts table")
    image_url: str = Field(..., description="URL of the image")
    image_index: int = Field(default=0, description="Position in carousel (0-indexed)")
    file_path: str | None = Field(default=None, description="Local file path after download")
    downloaded_at: datetime | None = Field(default=None, description="When image was downloaded")
    analyzed_at: datetime | None = Field(default=None, description="When image was analyzed by vision")
    is_event_flyer: bool = Field(default=False, description="Whether this image contains event details")
