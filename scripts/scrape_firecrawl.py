"""
Firecrawl client for web aggregator scraping.

This client handles URL discovery and page scraping only.
Claude does the event extraction from the returned markdown.
"""

import os
import re
from typing import Any

import structlog
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()
logger = structlog.get_logger()


class FirecrawlError(Exception):
    """Base exception for Firecrawl errors."""

    pass


class FirecrawlClient:
    """
    Client for Firecrawl API - scraping only, no LLM extraction.

    Returns markdown content for Claude to process and extract events.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set FIRECRAWL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.app = FirecrawlApp(api_key=self.api_key)

    def discover_event_urls(
        self,
        url: str,
        max_urls: int = 50,
        event_url_pattern: str | None = None,
    ) -> list[str]:
        """
        Map a site and return filtered event URLs.

        Args:
            url: Base URL of the aggregator site
            max_urls: Maximum number of URLs to return
            event_url_pattern: Optional glob pattern to filter URLs

        Returns:
            List of URLs likely to be event pages
        """
        logger.info("mapping_site", url=url)

        try:
            map_result = self.app.map_url(url)
            all_urls = map_result.get("links", [])
            logger.info("mapped_site", url_count=len(all_urls))
        except Exception as e:
            logger.error("map_failed", url=url, error=str(e))
            raise FirecrawlError(f"Failed to map site: {e}") from e

        # Filter to event URLs
        event_urls = self._filter_event_urls(all_urls, event_url_pattern)
        logger.info("filtered_urls", count=len(event_urls))

        return event_urls[:max_urls]

    def scrape_pages(
        self,
        urls: list[str],
    ) -> list[dict[str, Any]]:
        """
        Scrape multiple pages and return markdown content.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of dicts with 'url', 'markdown', 'metadata' keys
        """
        results = []

        for url in urls:
            try:
                logger.info("scraping_page", url=url)
                page = self.app.scrape_url(url, params={"formats": ["markdown"]})
                results.append(
                    {
                        "url": url,
                        "markdown": page.get("markdown", ""),
                        "metadata": page.get("metadata", {}),
                    }
                )
            except Exception as e:
                logger.error("scrape_failed", url=url, error=str(e))
                results.append(
                    {
                        "url": url,
                        "markdown": "",
                        "error": str(e),
                    }
                )

        logger.info(
            "scraping_complete",
            total=len(urls),
            success=len([r for r in results if "error" not in r]),
        )
        return results

    def scrape_aggregator(
        self,
        url: str,
        max_pages: int = 50,
        event_url_pattern: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Full workflow: discover URLs and scrape pages.

        Returns markdown content for Claude to extract events from.
        """
        event_urls = self.discover_event_urls(url, max_pages, event_url_pattern)

        if not event_urls:
            logger.warning("no_event_urls_found", url=url)
            return []

        return self.scrape_pages(event_urls)

    def _filter_event_urls(
        self,
        urls: list[str],
        pattern: str | None = None,
    ) -> list[str]:
        """Filter URLs to likely event pages."""
        # Common event URL patterns
        default_patterns = [
            r"/events?/",
            r"/calendar/",
            r"/shows?/",
            r"/performances?/",
            r"/whats-on/",
            r"/happening/",
            r"/gigs?/",
            r"/concerts?/",
        ]

        # Patterns to exclude
        exclude_patterns = [
            r"/about",
            r"/contact",
            r"/privacy",
            r"/terms",
            r"/login",
            r"/signup",
            r"/cart",
            r"/checkout",
            r"/account",
            r"\.(css|js|png|jpg|gif|svg|ico|pdf)$",
        ]

        filtered = []
        for url in urls:
            # Check exclusions first
            if any(re.search(p, url, re.I) for p in exclude_patterns):
                continue

            # Check if matches event pattern
            if pattern:
                # Convert glob pattern to regex
                regex_pattern = pattern.replace("*", ".*")
                if re.search(regex_pattern, url, re.I):
                    filtered.append(url)
            elif any(re.search(p, url, re.I) for p in default_patterns):
                filtered.append(url)

        return filtered


if __name__ == "__main__":
    # Simple test - returns markdown for Claude to process
    client = FirecrawlClient()

    # Discover URLs
    urls = client.discover_event_urls(
        url="https://example.com/events",
        max_urls=5,
    )
    print(f"Found {len(urls)} event URLs")

    # Scrape pages
    pages = client.scrape_pages(urls)
    for page in pages:
        print(f"\n--- {page['url']} ---")
        print(
            page["markdown"][:500] + "..."
            if len(page["markdown"]) > 500
            else page["markdown"]
        )
