"""Unit tests for extractor helper methods."""

import pytest
from unittest.mock import MagicMock

from douyin_download.extractor import _extract_from_video_tag


class TestExtractFromVideoTag:
    """Tests for _extract_from_video_tag function."""

    def test_video_tag_found(self) -> None:
        """Should return URL when video tag has src."""
        mock_page = MagicMock()
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = "https://v5.video.mp4"
        mock_page.query_selector.return_value = mock_video

        result = _extract_from_video_tag(mock_page)
        assert result == ["https://v5.video.mp4"]

    def test_video_tag_not_found(self) -> None:
        """Should return empty list when no video tag."""
        mock_page = MagicMock()
        mock_page.query_selector.return_value = None

        result = _extract_from_video_tag(mock_page)
        assert result == []