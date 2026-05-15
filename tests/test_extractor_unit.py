"""Unit tests for extractor helper methods."""

import pytest
from unittest.mock import MagicMock

from douyin_download.extractor import _extract_from_data_attributes, _extract_from_video_tag, extract_cdn_url


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


class TestExtractFromPaceF:
    """Tests for _extract_from_pace_f behavior via extract_cdn_url."""

    def test_pace_f_returns_list_not_dict(self) -> None:
        """Should return empty list when __pace_f returns a list, not dict.

        When __pace_f is a JSON list instead of dict, we skip the values()
        iteration and fall through to source element extraction. Since no
        source elements exist in this mock, we get an empty list.
        """
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_page.evaluate.return_value = '[1, 2, 3]'  # JSON list, not dict
        mock_page.query_selector_all.return_value = []

        result = extract_cdn_url("https://example.com", wait_seconds=1)

        assert result == []


class TestExtractFromDataAttributes:
    """Tests for _extract_from_data_attributes function."""

    def test_data_attributes_found(self) -> None:
        """Should extract URLs from data-* and href attributes."""
        mock_page = MagicMock()
        mock_page.content.return_value = '<a href="https://v5.data.mp4">video</a>'
        mock_page.evaluate.return_value = '{"videoUrl": "https://v5.data.mp4"}'

        result = _extract_from_data_attributes(mock_page)
        assert result == ["https://v5.data.mp4"]

    def test_data_attributes_not_found(self) -> None:
        """Should return empty list when no mp4/play in attributes."""
        mock_page = MagicMock()
        mock_page.content.return_value = '<a href="https://example.com">link</a>'
        mock_page.evaluate.return_value = '{"other": "not-a-video-url"}'

        result = _extract_from_data_attributes(mock_page)
        assert result == []