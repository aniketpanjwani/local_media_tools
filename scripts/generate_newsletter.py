"""
Newsletter Generator

Generates markdown newsletters from event collections using Jinja2 templates.
"""

from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from schemas.event import Event, EventCollection

logger = structlog.get_logger()


def group_events_by_day(events: list[Event]) -> dict[str, list[Event]]:
    """
    Group events by their day of week and date.

    Returns:
        Dict mapping display string (e.g., "Friday, Dec 15") to list of events
    """
    by_day: dict[str, list[Event]] = defaultdict(list)

    for event in events:
        if event.event_date:
            day_key = event.formatted_date  # e.g., "Friday, Dec 15"
            by_day[day_key].append(event)

    # Sort events within each day by start time
    for day in by_day:
        by_day[day].sort(
            key=lambda e: (e.start_time.hour, e.start_time.minute)
            if e.start_time
            else (23, 59)
        )

    return dict(by_day)


def find_flagged_events(events: list[Event]) -> list[dict]:
    """
    Find events that need manual review.

    Returns events with:
    - Missing critical info (date, venue)
    - Low confidence scores
    - Potential data issues
    """
    flagged = []

    for event in events:
        reasons = []

        if not event.event_date:
            reasons.append("missing date")

        if not event.venue or not event.venue.name:
            reasons.append("missing venue")

        if not event.start_time:
            reasons.append("missing start time")

        if event.confidence_score and event.confidence_score < 0.7:
            reasons.append(f"low confidence ({event.confidence_score:.0%})")

        if reasons:
            flagged.append(
                {
                    "title": event.title,
                    "event_date": event.event_date,
                    "review_reason": ", ".join(reasons),
                }
            )

    return flagged


def generate_newsletter(
    collection: EventCollection,
    template_name: str = "newsletter.md.j2",
    title: str | None = None,
    subtitle: str | None = None,
) -> str:
    """
    Generate a markdown newsletter from an event collection.

    Args:
        collection: EventCollection with events to include
        template_name: Name of the Jinja2 template file
        title: Newsletter title (defaults to "This Week's Events")
        subtitle: Newsletter subtitle (defaults to date range)

    Returns:
        Rendered markdown string
    """
    # Set up Jinja2 environment
    template_dir = Path(__file__).parent.parent / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template(template_name)

    # Filter to events within the week range
    events = [
        e
        for e in collection.events
        if e.event_date
        and collection.week_start <= e.event_date <= collection.week_end
    ]

    # Sort by date
    events.sort(key=lambda e: (e.event_date, e.start_time or datetime.min.time()))

    # Group by day
    events_by_day = group_events_by_day(events)

    # Find flagged events
    flagged = find_flagged_events(events)

    # Default title/subtitle
    if not title:
        title = "This Week's Events"

    if not subtitle:
        start = collection.week_start.strftime("%B %d")
        end = collection.week_end.strftime("%B %d, %Y")
        subtitle = f"{start} - {end}"

    # Count unique sources
    sources = set(e.source.value for e in events)

    # Render template
    content = template.render(
        title=title,
        subtitle=subtitle,
        events_by_day=events_by_day,
        flagged_events=flagged,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source_count=len(sources),
        total_events=len(events),
    )

    logger.info(
        "newsletter_generated",
        event_count=len(events),
        flagged_count=len(flagged),
        day_count=len(events_by_day),
    )

    return content


def save_newsletter(
    content: str,
    output_path: str | Path,
) -> Path:
    """
    Save newsletter content to a file.

    Args:
        content: Markdown content to save
        output_path: Path to save the newsletter

    Returns:
        Path to the saved file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("newsletter_saved", path=str(path))
    return path
