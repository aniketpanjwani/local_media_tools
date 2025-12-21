"""URL normalization utilities for consistent URL tracking."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# Query parameters to strip (tracking/analytics params)
TRACKING_PARAMS = frozenset({
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
})


def normalize_url(url: str) -> str:
    """
    Canonicalize URL for consistent tracking.

    - Lowercases scheme and host
    - Removes trailing slash (except for root path)
    - Sorts query parameters alphabetically
    - Removes common tracking parameters (utm_*, fbclid, etc.)
    - Removes fragment

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL string
    """
    parsed = urlparse(url)

    # Filter out tracking params and sort remaining
    params = sorted(
        (k, v) for k, v in parse_qsl(parsed.query) if k.lower() not in TRACKING_PARAMS
    )

    # Remove trailing slash (but keep root path as /)
    path = parsed.path.rstrip("/") or "/"

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",  # params (rarely used)
            urlencode(params) if params else "",
            "",  # fragment removed
        )
    )
