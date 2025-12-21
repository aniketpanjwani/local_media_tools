"""
Configuration schema with Pydantic validation.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


# Default database path in stable config directory
DEFAULT_DB_PATH = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    backend: Literal["sqlite", "json"] = "sqlite"
    path: Path = Field(default=DEFAULT_DB_PATH)
    auto_backup: bool = True

    @field_validator("path")
    @classmethod
    def ensure_parent_exists(cls, v: Path) -> Path:
        """Ensure parent directory exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


class InstagramAccount(BaseModel):
    """Configuration for a single Instagram account."""

    handle: str = Field(..., description="Instagram username without @")
    name: str
    type: str  # music_venue, promoter, aggregator, etc.
    location: str | None = None
    notes: str | None = None

    @field_validator("handle")
    @classmethod
    def strip_at_symbol(cls, v: str) -> str:
        return v.lstrip("@").strip()


class InstagramConfig(BaseModel):
    """Instagram source configuration."""

    enabled: bool = True
    accounts: list[InstagramAccount] = Field(default_factory=list)
    priority_handles: list[str] = Field(default_factory=list)


class EventbriteConfig(BaseModel):
    """Eventbrite source configuration (future)."""

    enabled: bool = False
    organizers: list[dict[str, Any]] = Field(default_factory=list)


class WebAggregatorSource(BaseModel):
    """Configuration for a web aggregator source."""

    url: str = Field(..., description="Base URL of the event aggregator")
    name: str = Field(..., description="Human-readable name for this source")
    source_type: Literal["calendar", "listing", "venue"] = "listing"
    event_url_pattern: str | None = Field(
        None,
        description="Glob pattern to filter event URLs (e.g., '/events/*')",
    )
    max_pages: int = Field(50, ge=1, le=200)
    extraction_hints: str | None = Field(
        None,
        description="Hints for LLM extraction (e.g., 'Events are in cards with .event-item class')",
    )


class WebAggregatorConfig(BaseModel):
    """Web aggregator source configuration."""

    enabled: bool = True
    sources: list[WebAggregatorSource] = Field(default_factory=list)


class SourcesConfig(BaseModel):
    """All event sources configuration."""

    instagram: InstagramConfig = Field(default_factory=InstagramConfig)
    eventbrite: EventbriteConfig = Field(default_factory=EventbriteConfig)
    web_aggregators: WebAggregatorConfig = Field(default_factory=WebAggregatorConfig)

    model_config = {"extra": "ignore"}  # Ignore deprecated facebook config


class FiltersConfig(BaseModel):
    """Event filtering configuration."""

    date_range: dict[str, str] = Field(
        default_factory=lambda: {"start": "today", "end": "+7days"}
    )
    categories: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class NewsletterConfig(BaseModel):
    """Newsletter project configuration with formatting preferences."""

    name: str
    region: str
    formatting_preferences: str = Field(
        default="Organize events chronologically by date. Use section headers for each day. Include event title, venue, time, and price. Keep formatting simple and readable.",
        description="Natural language instructions for how Claude should format the newsletter markdown",
    )


class AppConfig(BaseModel):
    """Complete application configuration."""

    newsletter: NewsletterConfig
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """Load and validate configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
