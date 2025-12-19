"""
Configuration schema with Pydantic validation.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


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


class SourcesConfig(BaseModel):
    """All event sources configuration."""

    instagram: InstagramConfig = Field(default_factory=InstagramConfig)
    facebook: FacebookConfig = Field(default_factory=FacebookConfig)
    eventbrite: EventbriteConfig = Field(default_factory=EventbriteConfig)


class OutputConfig(BaseModel):
    """Output configuration."""

    template: str = "templates/newsletter.md.j2"
    path: str = "tmp/output/"
    include_images: bool = True


class FiltersConfig(BaseModel):
    """Event filtering configuration."""

    date_range: dict[str, str] = Field(
        default_factory=lambda: {"start": "today", "end": "+7days"}
    )
    categories: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class NewsletterConfig(BaseModel):
    """Top-level newsletter configuration."""

    name: str
    region: str
    week_start: str = "tuesday"


class AppConfig(BaseModel):
    """Complete application configuration."""

    newsletter: NewsletterConfig
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """Load and validate configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
