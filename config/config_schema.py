"""
Configuration schema with Pydantic validation.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    backend: Literal["sqlite", "json"] = "sqlite"
    path: Path = Field(default=Path("tmp/extraction/events.db"))
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


class FacebookPage(BaseModel):
    """Configuration for a Facebook page."""

    url: str
    name: str


class FacebookLocation(BaseModel):
    """A single Facebook location for event discovery via Chrome MCP."""

    location_id: str = Field(..., description="Facebook location ID (e.g., '111841478834264')")
    location_name: str = Field(..., description="Human-readable name (e.g., 'Medellín, Antioquia')")
    date_filter: Literal["THIS_WEEK", "THIS_WEEKEND", "THIS_MONTH"] = "THIS_WEEK"
    max_events: int = Field(100, ge=1, le=500)
    scroll_count: int = Field(3, ge=1, le=10, description="Conservative default; each scroll ~10 events")
    scroll_delay_seconds: float = Field(5.0, ge=1.0, le=15.0, description="Delay to avoid rate limits")


class FacebookConfig(BaseModel):
    """Facebook source configuration."""

    enabled: bool = True
    pages: list[FacebookPage] = Field(default_factory=list)
    groups: list[FacebookPage] = Field(default_factory=list)
    locations: list[FacebookLocation] = Field(
        default_factory=list,
        description="Location-based discovery via Chrome MCP (supports multiple cities)",
    )


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
    facebook: FacebookConfig = Field(default_factory=FacebookConfig)
    eventbrite: EventbriteConfig = Field(default_factory=EventbriteConfig)
    web_aggregators: WebAggregatorConfig = Field(default_factory=WebAggregatorConfig)


class FiltersConfig(BaseModel):
    """Event filtering configuration."""

    date_range: dict[str, str] = Field(
        default_factory=lambda: {"start": "today", "end": "+7days"}
    )
    categories: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """Top-level project configuration."""

    name: str
    region: str


class AppConfig(BaseModel):
    """Complete application configuration."""

    newsletter: ProjectConfig  # Keep 'newsletter' key for backwards compatibility
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """Load and validate configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
