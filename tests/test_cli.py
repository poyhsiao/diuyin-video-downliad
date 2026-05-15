"""Unit tests for CLI commands."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from douyin_download.cli import main, download, info, session
from douyin_download.models import VideoNotFoundError


class TestDownloadCommand:
    """Tests for download command."""

    def test_download_command_success(self, tmp_path: Path) -> None:
        """Test successful video download."""
        runner = CliRunner()
        with patch("douyin_download.cli.download_video") as mock_download:
            mock_download.return_value = ("7637075230132849971", tmp_path / "test.mp4")
            result = runner.invoke(download, ["https://v.douyin.com/test123"])
            assert result.exit_code == 0
            assert "Downloaded:" in result.output

    def test_download_command_with_quality(self, tmp_path: Path) -> None:
        """Test download with quality option."""
        runner = CliRunner()
        with patch("douyin_download.cli.download_video") as mock_download:
            mock_download.return_value = ("7637075230132849971", tmp_path / "test.mp4")
            result = runner.invoke(download, ["--quality", "720p", "https://v.douyin.com/test123"])
            assert result.exit_code == 0
            mock_download.assert_called_once()
            call_kwargs = mock_download.call_args[1]
            assert call_kwargs.get("quality") == "720p"

    def test_download_command_with_output_dir(self, tmp_path: Path) -> None:
        """Test download with output directory option."""
        runner = CliRunner()
        with patch("douyin_download.cli.download_video") as mock_download:
            mock_download.return_value = ("7637075230132849971", tmp_path / "test.mp4")
            result = runner.invoke(download, ["--output", str(tmp_path), "https://v.douyin.com/test123"])
            assert result.exit_code == 0

    def test_download_command_video_not_found_error(self) -> None:
        """Test download handles VideoNotFoundError."""
        runner = CliRunner()
        with patch("douyin_download.cli.download_video") as mock_download:
            mock_download.side_effect = VideoNotFoundError("Video not found")
            result = runner.invoke(download, ["https://v.douyin.com/test123"])
            assert result.exit_code == 1
            assert "Error: Video not found" in result.output

    def test_download_command_no_cdn_available_error(self) -> None:
        """Test download handles NoCDNAvailableError."""
        runner = CliRunner()
        with patch("douyin_download.cli.download_video") as mock_download:
            from douyin_download.core import NoCDNAvailableError
            mock_download.side_effect = NoCDNAvailableError("No CDN available")
            result = runner.invoke(download, ["https://v.douyin.com/test123"])
            assert result.exit_code == 1
            assert "Error: No CDN available" in result.output


class TestInfoCommand:
    """Tests for info command."""

    def test_info_command_success(self) -> None:
        """Test successful info extraction."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve, \
             patch("douyin_download.cli.extract_cdn_url") as mock_extract, \
             patch("douyin_download.cli.sort_urls") as mock_sort:
            mock_resolve.return_value = "7637075230132849971"
            mock_extract.return_value = ["https://v5-dy-o.test.com/video.mp4"]
            mock_sort.return_value = ["https://v5-dy-o.test.com/video.mp4"]

            result = runner.invoke(info, ["https://v.douyin.com/test123"])
            assert result.exit_code == 0
            assert "Video ID: 7637075230132849971" in result.output
            assert "Available URLs: 1" in result.output
            assert "Best quality URL:" in result.output

    def test_info_command_no_urls_extracted(self) -> None:
        """Test info when no URLs are extracted."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve, \
             patch("douyin_download.cli.extract_cdn_url") as mock_extract, \
             patch("douyin_download.cli.sort_urls") as mock_sort:
            mock_resolve.return_value = "7637075230132849971"
            mock_extract.return_value = []
            mock_sort.return_value = []

            result = runner.invoke(info, ["https://v.douyin.com/test123"])
            assert result.exit_code == 0
            assert "No URLs extracted" in result.output

    def test_info_command_video_not_found_error(self) -> None:
        """Test info handles VideoNotFoundError."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve:
            mock_resolve.side_effect = VideoNotFoundError("Video not found")

            result = runner.invoke(info, ["https://v.douyin.com/test123"])
            assert result.exit_code == 1
            assert "Error: Video not found" in result.output

    def test_info_command_no_cdn_available_error(self) -> None:
        """Test info handles NoCDNAvailableError."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve, \
             patch("douyin_download.cli.extract_cdn_url") as mock_extract:
            from douyin_download.core import NoCDNAvailableError
            mock_resolve.return_value = "7637075230132849971"
            mock_extract.side_effect = NoCDNAvailableError("No CDN available")

            result = runner.invoke(info, ["https://v.douyin.com/test123"])
            assert result.exit_code == 1
            assert "Error: No CDN available" in result.output


class TestSessionCommand:
    """Tests for session command."""

    def test_session_command_success(self) -> None:
        """Test successful session resolution."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve:
            mock_resolve.return_value = "7637075230132849971"

            result = runner.invoke(session, ["https://v.douyin.com/test123"])
            assert result.exit_code == 0
            assert "Video ID: 7637075230132849971" in result.output
            assert "URL format: valid" in result.output

    def test_session_command_invalid_url(self) -> None:
        """Test session handles invalid URL."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve:
            mock_resolve.side_effect = ValueError("Unsupported URL format")

            result = runner.invoke(session, ["https://invalid.com/test"])
            assert result.exit_code == 1
            assert "Error: Unsupported URL format" in result.output

    def test_session_command_video_not_found(self) -> None:
        """Test session handles VideoNotFoundError."""
        runner = CliRunner()
        with patch("douyin_download.cli.resolve_video_id") as mock_resolve:
            mock_resolve.side_effect = VideoNotFoundError("Video not found")

            result = runner.invoke(session, ["https://v.douyin.com/test123"])
            assert result.exit_code == 1
            assert "Error: Video not found" in result.output


class TestMainCommand:
    """Tests for main CLI group."""

    def test_main_command_version(self) -> None:
        """Test main command shows version."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_main_command_help(self) -> None:
        """Test main command shows help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Douyin video downloader CLI" in result.output

    def test_main_command_list_commands(self) -> None:
        """Test main command lists all subcommands."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "download" in result.output
        assert "info" in result.output
        assert "session" in result.output