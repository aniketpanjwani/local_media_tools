"""Tests for Instagram CLI tool."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.cli_instagram import (
    cmd_list_posts,
    cmd_scrape,
    cmd_show_stats,
    get_config,
    get_storage,
    scrape_account,
    save_raw_response,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory with sources.yaml."""
    config_dir = tmp_path / ".config" / "local-media-tools"
    config_dir.mkdir(parents=True)

    sources_yaml = config_dir / "sources.yaml"
    sources_yaml.write_text("""
newsletter:
  name: "Test Newsletter"
  region: "Test Region"

sources:
  instagram:
    enabled: true
    accounts:
      - handle: "testhandle"
        name: "Test Account"
        type: "venue"
""")

    # Create .env file
    env_file = config_dir / ".env"
    env_file.write_text("SCRAPECREATORS_API_KEY=test_key\n")

    return config_dir


@pytest.fixture
def mock_api_response() -> dict:
    """Mock ScrapeCreators API response."""
    return {
        "posts": [
            {
                "node": {
                    "id": "123456789",
                    "shortcode": "ABC123",
                    "url": "https://www.instagram.com/p/ABC123/",
                    "__typename": "GraphImage",
                    "display_url": "https://example.com/image.jpg",
                    "owner": {
                        "id": "987654321",
                        "username": "testhandle",
                    },
                    "edge_media_to_caption": {
                        "edges": [{"node": {"text": "Test caption"}}]
                    },
                    "edge_liked_by": {"count": 100},
                    "edge_media_to_comment": {"count": 10},
                    "taken_at_timestamp": int(datetime.now().timestamp()),
                }
            }
        ],
        "next_max_id": None,
    }


class TestScrapeAccount:
    """Tests for scrape_account function."""

    def test_scrape_account_returns_posts(self, mock_api_response: dict) -> None:
        """Scrape account returns parsed posts."""
        mock_client = MagicMock()
        mock_client.get_instagram_user_posts.return_value = mock_api_response

        result = scrape_account(mock_client, "testhandle", limit=10)

        assert result["handle"] == "testhandle"
        assert result["profile"] is not None
        assert result["profile"].handle == "testhandle"
        assert len(result["posts"]) == 1
        assert result["posts"][0].instagram_post_id == "123456789"
        assert result["error"] is None

    def test_scrape_account_handles_empty_response(self) -> None:
        """Scrape account handles empty API response."""
        mock_client = MagicMock()
        mock_client.get_instagram_user_posts.return_value = {"posts": []}

        result = scrape_account(mock_client, "testhandle", limit=10)

        assert result["handle"] == "testhandle"
        assert result["profile"] is None
        assert len(result["posts"]) == 0

    def test_scrape_account_strips_at_symbol(self, mock_api_response: dict) -> None:
        """Handle is normalized by stripping @ symbol."""
        mock_client = MagicMock()
        mock_client.get_instagram_user_posts.return_value = mock_api_response

        result = scrape_account(mock_client, "@testhandle", limit=10)

        assert result["handle"] == "testhandle"
        mock_client.get_instagram_user_posts.assert_called_with("testhandle", limit=10)


class TestSaveRawResponse:
    """Tests for save_raw_response function."""

    def test_save_raw_response_creates_file(self, tmp_path: Path) -> None:
        """Raw response is saved to JSON file."""
        raw_dir = tmp_path / "raw"
        scrape_result = {
            "handle": "testhandle",
            "raw_response": {"posts": [{"node": {"id": "123"}}]},
        }

        with patch("scripts.cli_instagram.Path.home", return_value=tmp_path / "fake_home"):
            # Create the expected directory structure
            (tmp_path / "fake_home" / ".config" / "local-media-tools" / "data" / "raw").mkdir(
                parents=True
            )

            output_path = save_raw_response("testhandle", scrape_result)

            assert output_path.exists()
            with open(output_path) as f:
                saved_data = json.load(f)
            assert saved_data == {"posts": [{"node": {"id": "123"}}]}


class TestCmdShowStats:
    """Tests for show-stats command."""

    def test_show_stats_empty_database(self, tmp_path: Path, capsys) -> None:
        """Show stats with empty database."""
        from schemas.sqlite_storage import SqliteStorage

        db_path = tmp_path / "test.db"
        storage = SqliteStorage(db_path)

        with patch("scripts.cli_instagram.get_storage", return_value=storage):
            args = MagicMock()
            args.json = False
            result = cmd_show_stats(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Profiles:     0" in captured.out
        assert "Events:       0" in captured.out


class TestCmdListPosts:
    """Tests for list-posts command."""

    def test_list_posts_no_posts_found(self, tmp_path: Path, capsys) -> None:
        """List posts shows message when no posts found."""
        from schemas.sqlite_storage import SqliteStorage

        db_path = tmp_path / "test.db"
        storage = SqliteStorage(db_path)

        with patch("scripts.cli_instagram.get_storage", return_value=storage):
            args = MagicMock()
            args.handle = "nonexistent"
            args.classified_only = False
            args.json = False
            result = cmd_list_posts(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No posts found" in captured.out
