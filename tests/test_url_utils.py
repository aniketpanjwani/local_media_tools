"""Tests for URL normalization utilities."""

import pytest

from scripts.url_utils import normalize_url


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_basic_url_unchanged(self) -> None:
        """Simple URL without query params stays the same."""
        url = "https://example.com/events/123"
        assert normalize_url(url) == "https://example.com/events/123"

    def test_lowercases_scheme_and_host(self) -> None:
        """Scheme and host are lowercased."""
        url = "HTTPS://EXAMPLE.COM/Events/123"
        assert normalize_url(url) == "https://example.com/Events/123"

    def test_removes_trailing_slash(self) -> None:
        """Trailing slash is removed."""
        url = "https://example.com/events/"
        assert normalize_url(url) == "https://example.com/events"

    def test_preserves_root_path(self) -> None:
        """Root path is preserved as /."""
        url = "https://example.com/"
        assert normalize_url(url) == "https://example.com/"

    def test_sorts_query_params(self) -> None:
        """Query parameters are sorted alphabetically."""
        url = "https://example.com/events?z=1&a=2&m=3"
        assert normalize_url(url) == "https://example.com/events?a=2&m=3&z=1"

    def test_removes_utm_params(self) -> None:
        """UTM tracking parameters are stripped."""
        url = "https://example.com/events?utm_source=fb&utm_medium=social&id=123"
        assert normalize_url(url) == "https://example.com/events?id=123"

    def test_removes_fbclid(self) -> None:
        """Facebook click ID is stripped."""
        url = "https://example.com/events?fbclid=abc123&id=456"
        assert normalize_url(url) == "https://example.com/events?id=456"

    def test_removes_gclid(self) -> None:
        """Google click ID is stripped."""
        url = "https://example.com/events?gclid=xyz789&id=456"
        assert normalize_url(url) == "https://example.com/events?id=456"

    def test_removes_fragment(self) -> None:
        """URL fragments are removed."""
        url = "https://example.com/events#section-1"
        assert normalize_url(url) == "https://example.com/events"

    def test_handles_no_query_params(self) -> None:
        """URL without query params returns without query string."""
        url = "https://example.com/events/123"
        result = normalize_url(url)
        assert "?" not in result

    def test_handles_only_tracking_params(self) -> None:
        """URL with only tracking params returns without query string."""
        url = "https://example.com/events?utm_source=fb&fbclid=abc"
        result = normalize_url(url)
        assert "?" not in result

    def test_complex_normalization(self) -> None:
        """Multiple normalizations applied together."""
        url = "HTTPS://HVmag.COM/Events/jazz-night/?utm_source=fb&id=123&fbclid=x#tickets"
        expected = "https://hvmag.com/Events/jazz-night?id=123"
        assert normalize_url(url) == expected

    def test_preserves_path_case(self) -> None:
        """Path case is preserved (only host is lowercased)."""
        url = "https://example.com/Events/Jazz-Night"
        assert normalize_url(url) == "https://example.com/Events/Jazz-Night"
