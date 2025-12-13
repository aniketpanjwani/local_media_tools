"""
Event Deduplication

Fuzzy matching and deduplication logic for events from multiple sources.
Uses rapidfuzz for efficient string similarity matching.
"""

from datetime import date

import structlog
from rapidfuzz import fuzz

from schemas.event import Event

logger = structlog.get_logger()


def normalize_title(title: str) -> str:
    """
    Normalize a title for comparison.

    Removes common prefixes, lowercases, and strips punctuation.
    """
    title = title.lower().strip()

    # Remove common prefixes
    prefixes = ["live:", "tonight:", "this weekend:", "show:", "event:"]
    for prefix in prefixes:
        if title.startswith(prefix):
            title = title[len(prefix) :].strip()

    # Remove common suffixes
    suffixes = ["- live", "live!", "!!!", "!"]
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()

    return title


def normalize_venue(venue_name: str) -> str:
    """
    Normalize a venue name for comparison.
    """
    venue = venue_name.lower().strip()

    # Remove common venue suffixes
    suffixes = [
        "bar",
        "lounge",
        "club",
        "venue",
        "theater",
        "theatre",
        "hall",
        "room",
        "stage",
        "the",
    ]

    words = venue.split()
    if words and words[-1] in suffixes:
        words = words[:-1]
    if words and words[0] == "the":
        words = words[1:]

    return " ".join(words)


def calculate_similarity(event1: Event, event2: Event) -> float:
    """
    Calculate similarity score between two events.

    Returns a score from 0.0 (completely different) to 1.0 (identical).
    """
    # Must be on the same date to be duplicates
    if event1.event_date != event2.event_date:
        return 0.0

    # Title similarity (weighted heavily)
    title1 = normalize_title(event1.title)
    title2 = normalize_title(event2.title)
    title_score = fuzz.ratio(title1, title2) / 100.0

    # Venue similarity
    venue_score = 0.0
    if event1.venue and event2.venue:
        venue1 = normalize_venue(event1.venue.name)
        venue2 = normalize_venue(event2.venue.name)
        venue_score = fuzz.ratio(venue1, venue2) / 100.0

    # Time similarity
    time_score = 0.0
    if event1.start_time and event2.start_time:
        time_diff = abs(
            (event1.start_time.hour * 60 + event1.start_time.minute)
            - (event2.start_time.hour * 60 + event2.start_time.minute)
        )
        # Within 30 minutes = full match, degrades after
        time_score = max(0.0, 1.0 - (time_diff / 60.0))

    # Weighted combination
    # Title is most important, then venue, then time
    combined_score = (title_score * 0.5) + (venue_score * 0.35) + (time_score * 0.15)

    return combined_score


def merge_events(primary: Event, secondary: Event) -> Event:
    """
    Merge two duplicate events, preferring data from the primary.

    Facebook events are preferred as primary because they have
    more structured data.
    """
    # Start with the primary event's data
    merged_data = primary.model_dump()

    # Fill in missing fields from secondary
    if not merged_data.get("description") and secondary.description:
        merged_data["description"] = secondary.description

    if not merged_data.get("ticket_url") and secondary.ticket_url:
        merged_data["ticket_url"] = secondary.ticket_url

    if not merged_data.get("image_url") and secondary.image_url:
        merged_data["image_url"] = secondary.image_url

    if not merged_data.get("start_time") and secondary.start_time:
        merged_data["start_time"] = secondary.start_time

    if not merged_data.get("end_time") and secondary.end_time:
        merged_data["end_time"] = secondary.end_time

    # Keep both source URLs
    if secondary.source_url and secondary.source_url != primary.source_url:
        merged_data["alternate_source_urls"] = [secondary.source_url]

    return Event(**merged_data)


def deduplicate_events(
    events: list[Event],
    threshold: float = 0.75,
    prefer_source: str = "facebook",
) -> list[Event]:
    """
    Deduplicate a list of events using fuzzy matching.

    Args:
        events: List of events to deduplicate
        threshold: Similarity threshold (0.0-1.0) for considering events duplicates
        prefer_source: Preferred source when merging duplicates ("facebook" or "instagram")

    Returns:
        Deduplicated list of events
    """
    if not events:
        return []

    logger.info("deduplication_start", event_count=len(events), threshold=threshold)

    # Sort events to ensure preferred source comes first
    def source_priority(event: Event) -> int:
        if event.source.value == prefer_source:
            return 0
        return 1

    sorted_events = sorted(events, key=source_priority)

    # Track which events have been merged
    merged_indices: set[int] = set()
    result: list[Event] = []

    for i, event1 in enumerate(sorted_events):
        if i in merged_indices:
            continue

        # Find all duplicates of this event
        duplicates = [event1]

        for j in range(i + 1, len(sorted_events)):
            if j in merged_indices:
                continue

            event2 = sorted_events[j]
            similarity = calculate_similarity(event1, event2)

            if similarity >= threshold:
                logger.debug(
                    "duplicate_found",
                    event1=event1.title,
                    event2=event2.title,
                    similarity=f"{similarity:.2f}",
                )
                duplicates.append(event2)
                merged_indices.add(j)

        # Merge all duplicates
        if len(duplicates) > 1:
            merged = duplicates[0]
            for dup in duplicates[1:]:
                merged = merge_events(merged, dup)
            result.append(merged)
        else:
            result.append(event1)

    # Sort by date
    result.sort(key=lambda e: (e.event_date or date.max, e.start_time or ""))

    logger.info(
        "deduplication_complete",
        original_count=len(events),
        deduplicated_count=len(result),
        duplicates_removed=len(events) - len(result),
    )

    return result


def find_duplicates(
    events: list[Event], threshold: float = 0.75
) -> list[tuple[Event, Event, float]]:
    """
    Find all duplicate pairs in a list of events.

    Useful for debugging and manual review.

    Returns:
        List of tuples: (event1, event2, similarity_score)
    """
    duplicates = []

    for i, event1 in enumerate(events):
        for j in range(i + 1, len(events)):
            event2 = events[j]
            similarity = calculate_similarity(event1, event2)

            if similarity >= threshold:
                duplicates.append((event1, event2, similarity))

    return duplicates
