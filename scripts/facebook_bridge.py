"""
Facebook Bridge

Python subprocess bridge to the Node.js Facebook event scraper.
Uses JSON stdin/stdout for communication.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class FacebookScraperError(Exception):
    """Base exception for Facebook scraper errors."""

    pass


class FacebookBridge:
    """Bridge to the Node.js Facebook event scraper."""

    def __init__(self, timeout: int = 120):
        """
        Initialize the Facebook bridge.

        Args:
            timeout: Timeout in seconds for scraper operations
        """
        self.timeout = timeout
        self._script_path = Path(__file__).parent / "scrape_facebook.js"

        if not self._script_path.exists():
            raise FacebookScraperError(
                f"Facebook scraper script not found at {self._script_path}"
            )

    def _call_scraper(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Call the Node.js scraper with a JSON request.

        Args:
            request: Request object with action, url, and options

        Returns:
            Response object with success and data/error

        Raises:
            FacebookScraperError: If the scraper fails
        """
        try:
            result = subprocess.run(
                ["bun", "run", str(self._script_path)],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self._script_path.parent.parent,  # Project root
            )

            if result.returncode != 0 and not result.stdout:
                error_msg = result.stderr or "Unknown error"
                logger.error(
                    "facebook_scraper_failed",
                    returncode=result.returncode,
                    stderr=error_msg,
                )
                raise FacebookScraperError(f"Scraper process failed: {error_msg}")

            try:
                response = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(
                    "facebook_scraper_invalid_json",
                    stdout=result.stdout[:500],
                    error=str(e),
                )
                raise FacebookScraperError(f"Invalid JSON response: {e}")

            if not response.get("success"):
                error = response.get("error", "Unknown error")
                logger.warning("facebook_scraper_error", error=error)
                raise FacebookScraperError(error)

            return response

        except subprocess.TimeoutExpired:
            logger.error("facebook_scraper_timeout", timeout=self.timeout)
            raise FacebookScraperError(
                f"Scraper timed out after {self.timeout} seconds"
            )
        except FileNotFoundError:
            raise FacebookScraperError(
                "bun not found. Please install bun: https://bun.sh"
            )

    def scrape_page_events(
        self, url: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Scrape all events from a Facebook page.

        Args:
            url: Facebook page events URL (e.g., https://facebook.com/venue/events)
            limit: Maximum number of events to scrape

        Returns:
            List of event dictionaries matching the Event schema

        Raises:
            FacebookScraperError: If scraping fails
        """
        logger.info("facebook_scrape_page_start", url=url, limit=limit)

        response = self._call_scraper(
            {
                "action": "scrape_page_events",
                "url": url,
                "options": {"limit": limit},
            }
        )

        events = response.get("data", [])
        logger.info("facebook_scrape_page_complete", url=url, event_count=len(events))

        return events

    def scrape_single_event(self, url: str) -> dict[str, Any]:
        """
        Scrape a single Facebook event.

        Args:
            url: Facebook event URL (e.g., https://facebook.com/events/123456)

        Returns:
            Event dictionary matching the Event schema

        Raises:
            FacebookScraperError: If scraping fails
        """
        logger.info("facebook_scrape_event_start", url=url)

        response = self._call_scraper(
            {
                "action": "scrape_single_event",
                "url": url,
            }
        )

        event = response.get("data")
        logger.info("facebook_scrape_event_complete", url=url, title=event.get("title"))

        return event


def download_image(url: str, output_dir: str, filename: str) -> Path | None:
    """
    Download an image from a URL.

    Args:
        url: Image URL
        output_dir: Directory to save the image
        filename: Filename for the saved image

    Returns:
        Path to the saved image, or None if download failed
    """
    import requests

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename

    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.debug("image_downloaded", path=str(file_path))
        return file_path

    except requests.RequestException as e:
        logger.warning("image_download_failed", url=url, error=str(e))
        return None
