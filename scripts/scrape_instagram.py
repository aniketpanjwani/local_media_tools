"""
ScrapeCreators client for Instagram scraping with retry logic and rate limiting.
"""

import os
import time
from pathlib import Path
from typing import Any

import requests
import structlog
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = structlog.get_logger()

# Load environment variables from stable config directory
_env_path = Path.home() / ".config" / "local-media-tools" / ".env"
load_dotenv(_env_path)


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, calls_per_second: float = 2.0) -> None:
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait_if_needed(self) -> None:
        """Block if we need to throttle."""
        elapsed = time.time() - self.last_call
        wait_time = self.min_interval - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_call = time.time()


class ScrapeCreatorsError(Exception):
    """Base exception for ScrapeCreators API errors."""

    pass


class ScrapeCreatorsRateLimitError(ScrapeCreatorsError):
    """Raised when rate limit is hit."""

    pass


class ScrapeCreatorsClient:
    """
    Client for ScrapeCreators Instagram API with retry logic and rate limiting.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.scrapecreators.com",
        timeout: int = 30,
        max_retries: int = 3,
        calls_per_second: float = 2.0,
    ) -> None:
        self.api_key = api_key or os.getenv("SCRAPECREATORS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set SCRAPECREATORS_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limiter = RateLimiter(calls_per_second)

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with rate limiting and error handling."""
        self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"x-api-key": self.api_key}

        logger.info("api_request", method=method, endpoint=endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )

            if response.status_code == 429:
                raise ScrapeCreatorsRateLimitError("Rate limit exceeded")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as e:
            logger.error("api_timeout", endpoint=endpoint, timeout=self.timeout)
            raise ScrapeCreatorsError(f"Request timeout after {self.timeout}s") from e
        except requests.exceptions.RequestException as e:
            logger.error("api_error", endpoint=endpoint, error=str(e))
            raise ScrapeCreatorsError(f"API request failed: {e}") from e

    def get_instagram_profile(self, handle: str) -> dict[str, Any]:
        """Fetch Instagram profile info."""
        handle = handle.lstrip("@").strip()
        return self._make_request("GET", f"/v1/instagram/profile/{handle}")

    def get_instagram_user_posts(
        self,
        handle: str,
        next_max_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Fetch paginated Instagram posts."""
        handle = handle.lstrip("@").strip()
        params: dict[str, Any] = {"handle": handle, "limit": limit}
        if next_max_id:
            params["next_max_id"] = next_max_id
        return self._make_request("GET", "/v1/instagram/user/posts", params=params)

def download_image(url: str, output_dir: Path, filename: str) -> Path | None:
    """
    Download an image to the specified directory.

    Returns the path to the downloaded file, or None if download failed.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("image_downloaded", path=str(output_path))
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error("image_download_failed", url=url, error=str(e))
        return None


def get_image_storage_path(
    handle: str,
    post_id: str,
    index: int,
    posted_at: Any | None = None,
) -> Path:
    """
    Generate storage path for an Instagram image.

    Directory structure:
    ~/.config/local-media-tools/data/images/instagram/{handle}/{date}_{post_id}_{index}.jpg

    Args:
        handle: Instagram handle (with or without @)
        post_id: Instagram post ID
        index: Image index within the post (0-indexed)
        posted_at: Optional datetime when posted (for date prefix)

    Returns:
        Path to where the image should be stored
    """
    import re
    from datetime import datetime

    # Sanitize handle
    safe_handle = re.sub(r"[^\w\-]", "_", handle.lower().lstrip("@"))

    # Format date prefix if available
    date_prefix = ""
    if posted_at:
        if isinstance(posted_at, datetime):
            date_prefix = posted_at.strftime("%Y-%m-%d") + "_"
        elif hasattr(posted_at, "isoformat"):
            date_prefix = str(posted_at)[:10] + "_"

    # Truncate post_id if too long
    safe_post_id = post_id[:50]

    base_dir = (
        Path.home()
        / ".config"
        / "local-media-tools"
        / "data"
        / "images"
        / "instagram"
    )
    return base_dir / safe_handle / f"{date_prefix}{safe_post_id}_{index}.jpg"


def download_post_images(
    post: Any,  # InstagramPost - using Any to avoid circular import
    handle: str,
) -> list[tuple[int, Path | None]]:
    """
    Download all images for an Instagram post.

    Args:
        post: InstagramPost object with image_urls list
        handle: Instagram handle of the account

    Returns:
        List of (index, path) tuples. Path is None if download failed.
    """
    results: list[tuple[int, Path | None]] = []

    # Skip videos/reels - no static images to download
    if post.media_type in ("video", "reel"):
        logger.info(
            "skipping_video_download",
            post_id=post.instagram_post_id,
            media_type=post.media_type,
        )
        return results

    for index, url in enumerate(post.image_urls):
        if not url:
            results.append((index, None))
            continue

        path = get_image_storage_path(
            handle=handle,
            post_id=post.instagram_post_id,
            index=index,
            posted_at=post.posted_at,
        )

        try:
            downloaded = download_image(url, path.parent, path.name)
            results.append((index, downloaded))
        except Exception as e:
            logger.error(
                "image_download_failed",
                url=url,
                post_id=post.instagram_post_id,
                index=index,
                error=str(e),
            )
            results.append((index, None))

    return results


if __name__ == "__main__":
    # Simple test
    import json

    client = ScrapeCreatorsClient()

    handle = "theavalonlounge"
    print(f"Fetching posts for @{handle}...")

    try:
        result = client.get_instagram_user_posts(handle, limit=5)
        print(json.dumps(result, indent=2))
    except ScrapeCreatorsError as e:
        print(f"Error: {e}")
