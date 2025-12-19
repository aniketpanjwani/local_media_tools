"""
Facebook Events discovery utilities.

These functions are called by Claude Code during the skill workflow.
Claude handles browser automation via Chrome MCP; these functions just build URLs and parse data.
"""

from datetime import datetime, date, timedelta
from urllib.parse import urlencode
import re

from dateutil import parser as date_parser
import structlog

from schemas.event import Event, EventSource, Venue

logger = structlog.get_logger()


def build_discover_url(
    location_id: str,
    date_filter: str = "THIS_WEEK",
    now: datetime | None = None,
) -> str:
    """
    Build Facebook Events discover URL with location and date filters.

    Args:
        location_id: Facebook's internal location ID
        date_filter: One of THIS_WEEK, THIS_WEEKEND, THIS_MONTH
        now: Current datetime (for testing; defaults to datetime.now())

    Returns:
        Complete URL for Facebook Events discover page

    Example:
        >>> build_discover_url("111841478834264", "THIS_WEEK")
        'https://web.facebook.com/events/?date_filter_option=THIS_WEEK&...'
    """
    if now is None:
        now = datetime.now()

    # Calculate date range based on filter
    if date_filter == "THIS_WEEK":
        days_until_sunday = 6 - now.weekday()
        end_date = now + timedelta(days=days_until_sunday)
    elif date_filter == "THIS_WEEKEND":
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0 and now.weekday() == 5:
            days_until_saturday = 0  # Already Saturday
        start_override = now + timedelta(days=days_until_saturday)
        end_date = start_override + timedelta(days=1)
        now = start_override  # Start from Saturday
    elif date_filter == "THIS_MONTH":
        next_month = now.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    else:
        raise ValueError(f"Unknown date_filter: {date_filter}")

    params = {
        "date_filter_option": date_filter,
        "discover_tab": "CUSTOM",
        "location_id": location_id,
        "start_date": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }

    return f"https://web.facebook.com/events/?{urlencode(params)}"


def parse_facebook_date(date_str: str, reference_date: date | None = None) -> date | None:
    """
    Parse Facebook's various date formats into a Python date.

    Facebook uses several formats:
    - "Fri, Dec 20 at 8:00 PM" (within current year)
    - "Sat, Jan 4, 2025 at 9:00 PM" (explicit year)
    - "Today at 7:00 PM"
    - "Tomorrow at 8:00 PM"
    - "Saturday at 9:00 PM" (this week)

    Args:
        date_str: The date string from Facebook
        reference_date: Reference date for relative terms (defaults to today)

    Returns:
        Parsed date or None if parsing fails
    """
    if reference_date is None:
        reference_date = date.today()

    date_str = date_str.strip()

    # Handle relative dates
    if date_str.lower().startswith("today"):
        return reference_date

    if date_str.lower().startswith("tomorrow"):
        return reference_date + timedelta(days=1)

    # Handle weekday names (e.g., "Saturday at 9:00 PM")
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(weekdays):
        if date_str.lower().startswith(day):
            # Find next occurrence of this weekday
            days_ahead = i - reference_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return reference_date + timedelta(days=days_ahead)

    # Try dateutil parser for explicit dates
    try:
        # Remove time portion for simpler parsing
        date_part = re.split(r"\s+at\s+", date_str, flags=re.IGNORECASE)[0]
        parsed = date_parser.parse(date_part, fuzzy=True)

        # If no year specified and date is in the past, assume next year
        if parsed.year == reference_date.year and parsed.date() < reference_date:
            parsed = parsed.replace(year=parsed.year + 1)

        return parsed.date()
    except Exception:
        pass

    logger.warning("failed_to_parse_date", date_str=date_str)
    return None


def parse_event_card(
    text: str,
    url: str,
    location_name: str,
    reference_date: date | None = None,
) -> Event | None:
    """
    Parse a single Facebook event card into an Event object.

    Facebook event cards typically contain (in order):
    - Date/time (e.g., "Fri, Dec 20 at 8:00 PM")
    - Event title
    - Location or "Online"
    - Attendance info (e.g., "234 interested · 45 going")

    Args:
        text: The text content of the event card
        url: The event URL (contains event ID)
        location_name: Human-readable location from config
        reference_date: Reference date for parsing relative dates

    Returns:
        Event object or None if parsing fails
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Need at least date and title
    if len(lines) < 2:
        logger.debug("event_card_too_short", line_count=len(lines), text=text[:50])
        return None

    try:
        # Extract event ID from URL
        event_id_match = re.search(r"/events/(\d+)", url)
        event_id = event_id_match.group(1) if event_id_match else url.split("/")[-1].rstrip("/")

        # Parse date (first line)
        event_date = parse_facebook_date(lines[0], reference_date)
        if event_date is None:
            logger.warning("could_not_parse_event_date", date_str=lines[0])
            return None

        # Title (second line)
        title = lines[1]

        # Venue (third line, if present and not "Online" or attendance info)
        venue_name = "TBD"
        if len(lines) > 2:
            potential_venue = lines[2]
            # Skip if it looks like attendance info
            if not re.search(r"\d+\s*(interested|going)", potential_venue, re.IGNORECASE):
                if potential_venue.lower() != "online":
                    venue_name = potential_venue

        return Event(
            title=title,
            venue=Venue(
                name=venue_name,
                city=location_name.split(",")[0] if location_name else None,
            ),
            event_date=event_date,
            source=EventSource.FACEBOOK,
            source_url=f"https://facebook.com/events/{event_id}",
            description=None,  # Would need to click into event for full description
            needs_review=True,  # Mark for human review since discovery data is sparse
        )

    except Exception as e:
        logger.warning("failed_to_parse_event_card", error=str(e), text=text[:100])
        return None


def is_logged_in(page_content: str) -> bool:
    """
    Check if the page content indicates the user is logged into Facebook.

    Args:
        page_content: Text content from chrome_get_web_content

    Returns:
        True if logged in, False if login required
    """
    login_indicators = [
        "Log In",
        "Log in",
        "Create new account",
        "Create New Account",
        "Forgotten password",
    ]

    # Check for login page indicators
    for indicator in login_indicators:
        if indicator in page_content:
            # Could be a false positive if these words appear elsewhere
            # Check if it's prominently featured (near start of content)
            if page_content.find(indicator) < 500:
                return False

    return True
