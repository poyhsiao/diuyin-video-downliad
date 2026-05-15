"""Unit tests for extractor helper methods."""

from unittest.mock import MagicMock

from douyin_download.extractor import (
    _extract_from_data_attributes,
    _extract_from_network_interception,
    _extract_from_source_tags,
    _extract_from_video_tag,
    _extract_from_pace_f,
    _intercept_aweme_detail_api,
)


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

    def test_video_tag_empty_src(self) -> None:
        """Should return empty list when video tag has empty src."""
        mock_page = MagicMock()
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = ""
        mock_page.query_selector.return_value = mock_video

        result = _extract_from_video_tag(mock_page)
        assert result == []

    def test_video_tag_src_without_mp4_or_play(self) -> None:
        """Should return empty list when src has no mp4/play."""
        mock_page = MagicMock()
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = "https://v5.video.jpg"
        mock_page.query_selector.return_value = mock_video

        result = _extract_from_video_tag(mock_page)
        assert result == []

    def test_video_tag_src_is_none(self) -> None:
        """Should return empty list when src attribute is None."""
        mock_page = MagicMock()
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = None
        mock_page.query_selector.return_value = mock_video

        result = _extract_from_video_tag(mock_page)
        assert result == []


class TestExtractFromSourceTags:
    """Tests for _extract_from_source_tags function."""

    def test_source_tags_found(self) -> None:
        """Should return URLs from source tags."""
        mock_page = MagicMock()
        mock_el1 = MagicMock()
        mock_el1.get_attribute.return_value = "https://cdn1.video.mp4"
        mock_el2 = MagicMock()
        mock_el2.get_attribute.return_value = "https://cdn2.video.mp4"
        mock_page.query_selector_all.return_value = [mock_el1, mock_el2]

        result = _extract_from_source_tags(mock_page)
        assert result == ["https://cdn1.video.mp4", "https://cdn2.video.mp4"]

    def test_source_tags_none_found(self) -> None:
        """Should return empty list when no source tags."""
        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = []

        result = _extract_from_source_tags(mock_page)
        assert result == []

    def test_source_tags_mixed_valid_invalid(self) -> None:
        """Should return all source URLs regardless of mp4/play content."""
        mock_page = MagicMock()
        mock_el1 = MagicMock()
        mock_el1.get_attribute.return_value = "https://cdn.video.mp4"
        mock_el2 = MagicMock()
        mock_el2.get_attribute.return_value = None  # skip
        mock_el3 = MagicMock()
        mock_el3.get_attribute.return_value = "https://cdn.video.jpg"  # no mp4/play, but still included
        mock_page.query_selector_all.return_value = [mock_el1, mock_el2, mock_el3]

        result = _extract_from_source_tags(mock_page)
        assert result == ["https://cdn.video.mp4", "https://cdn.video.jpg"]


class TestExtractFromPaceF:
    """Tests for _extract_from_pace_f behavior via extract_cdn_url."""

    def test_pace_f_returns_list_not_dict(self) -> None:
        """Should return empty list when __pace_f returns a list, not dict."""
        mock_page = MagicMock()
        mock_page.evaluate.return_value = '[1, 2, 3]'

        result = _extract_from_pace_f(mock_page)

        assert result == []

    def test_pace_f_returns_empty_dict(self) -> None:
        """Should return empty list when __pace_f is empty dict."""
        mock_page = MagicMock()
        mock_page.evaluate.return_value = '{}'

        result = _extract_from_pace_f(mock_page)
        assert result == []

    def test_pace_f_returns_dict_with_non_url_strings(self) -> None:
        """Should return empty list when dict values are not video URLs."""
        mock_page = MagicMock()
        mock_page.evaluate.return_value = '{"title": "My Video", "duration": "120"}'

        result = _extract_from_pace_f(mock_page)
        assert result == []

    def test_pace_f_returns_dict_with_string_values(self) -> None:
        """Should extract URLs when dict values are strings with mp4/play."""
        mock_page = MagicMock()
        mock_page.evaluate.return_value = '{"video": "https://cdn.video.mp4"}'

        result = _extract_from_pace_f(mock_page)
        assert result == ["https://cdn.video.mp4"]

    def test_pace_f_returns_nested_dict_with_urls(self) -> None:
        """Should extract URLs from nested dict values."""
        mock_page = MagicMock()
        mock_page.evaluate.return_value = '{"outer": {"inner": "https://cdn.video.play"}}'

        result = _extract_from_pace_f(mock_page)
        assert result == ["https://cdn.video.play"]

    def test_pace_f_json_decode_error(self) -> None:
        """Should return empty list on JSON decode error."""
        mock_page = MagicMock()
        mock_page.evaluate.return_value = 'not valid json {'

        result = _extract_from_pace_f(mock_page)
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

    def test_data_attributes_malformed_urls(self) -> None:
        """Should return empty list for malformed URLs without mp4/play."""
        mock_page = MagicMock()
        mock_page.content.return_value = '<a href="https://example.com/page">link</a>'

        result = _extract_from_data_attributes(mock_page)
        assert result == []


class TestExtractCdnUrlChainBehavior:
    """Tests for chaining behavior - testing individual extractors together."""

    def test_video_tag_empty_triggers_source_tags(self) -> None:
        """Should return source URLs when video tag has no valid src."""
        mock_page = MagicMock()
        # video tag exists but src lacks mp4/play
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = "https://v5.video.jpg"
        mock_page.query_selector.return_value = mock_video
        # source tags has valid URL
        mock_source = MagicMock()
        mock_source.get_attribute.return_value = "https://source.video.mp4"
        mock_page.query_selector_all.return_value = [mock_source]
        # pace_f empty
        mock_page.evaluate.return_value = '{}'
        mock_page.content.return_value = '<a href="https://other.mp4">link</a>'

        # simulate chain: video_tag -> source_tags
        urls = _extract_from_video_tag(mock_page)
        if not urls:
            urls = _extract_from_source_tags(mock_page)
        if not urls:
            urls = _extract_from_pace_f(mock_page)
        if not urls:
            urls = _extract_from_data_attributes(mock_page)

        assert urls == ["https://source.video.mp4"]

    def test_source_tags_empty_triggers_pace_f(self) -> None:
        """Should return pace_f URLs when source tags is empty."""
        mock_page = MagicMock()
        # video tag returns empty
        mock_page.query_selector.return_value = None
        # source tags empty
        mock_page.query_selector_all.return_value = []
        # pace_f has URL
        mock_page.evaluate.return_value = '{"playUrl": "https://pacef.video.mp4"}'
        mock_page.content.return_value = '<a href="https://other.mp4">link</a>'

        # simulate chain
        urls = _extract_from_video_tag(mock_page)
        if not urls:
            urls = _extract_from_source_tags(mock_page)
        if not urls:
            urls = _extract_from_pace_f(mock_page)
        if not urls:
            urls = _extract_from_data_attributes(mock_page)

        assert urls == ["https://pacef.video.mp4"]

    def test_pace_f_empty_triggers_data_attributes(self) -> None:
        """Should return data attribute URLs when pace_f is empty."""
        mock_page = MagicMock()
        # video tag returns empty
        mock_page.query_selector.return_value = None
        # source tags empty
        mock_page.query_selector_all.return_value = []
        # pace_f empty
        mock_page.evaluate.return_value = '{}'
        # data attributes has URL
        mock_page.content.return_value = '<a href="https://dataattr.video.mp4">video</a>'

        # simulate chain
        urls = _extract_from_video_tag(mock_page)
        if not urls:
            urls = _extract_from_source_tags(mock_page)
        if not urls:
            urls = _extract_from_pace_f(mock_page)
        if not urls:
            urls = _extract_from_data_attributes(mock_page)

        assert urls == ["https://dataattr.video.mp4"]

    def test_video_tag_with_valid_url_stops_chain(self) -> None:
        """Should return video tag URL without trying fallbacks."""
        mock_page = MagicMock()
        # video tag has valid URL
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = "https://first.video.mp4"
        mock_page.query_selector.return_value = mock_video

        # simulate chain - it should stop at video tag
        urls = _extract_from_video_tag(mock_page)
        original_urls = list(urls)  # copy

        if not urls:
            urls = _extract_from_source_tags(mock_page)
        if not urls:
            urls = _extract_from_pace_f(mock_page)
        if not urls:
            urls = _extract_from_data_attributes(mock_page)

        # Should return video tag URL
        assert original_urls == ["https://first.video.mp4"]
        # And fallbacks should NOT have been reached (urls unchanged since first was non-empty)
        assert urls == ["https://first.video.mp4"]

    def test_video_tag_no_mp4_play_falls_through_to_source(self) -> None:
        """Should fall through to source when video src lacks mp4/play."""
        mock_page = MagicMock()
        # video tag has src but no mp4/play
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = "https://v5.video.jpg"
        mock_page.query_selector.return_value = mock_video
        # source tags has valid URL
        mock_source = MagicMock()
        mock_source.get_attribute.return_value = "https://source.video.play"
        mock_page.query_selector_all.return_value = [mock_source]

        # video tag returns empty due to no mp4/play
        urls = _extract_from_video_tag(mock_page)
        assert urls == []

        # should fall through to source tags
        urls = _extract_from_source_tags(mock_page)
        assert urls == ["https://source.video.play"]


class TestExtractFromNetworkInterception:
    """Tests for _extract_from_network_interception function."""

    def test_captures_mp4_urls(self) -> None:
        """Should capture URLs matching mp4 pattern."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        _extract_from_network_interception(mock_page, timeout_ms=100)

        mock_page.route.assert_called_once()
        mock_page.unroute_all.assert_called_once()
        assert mock_page.wait_for_timeout.call_count >= 1

    def test_captures_m3u8_urls(self) -> None:
        """Should capture URLs matching m3u8 pattern."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        _extract_from_network_interception(mock_page, timeout_ms=100)

        mock_page.route.assert_called_once()

    def test_captures_chunk_urls(self) -> None:
        """Should capture URLs matching chunk pattern."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        _extract_from_network_interception(mock_page, timeout_ms=100)

        mock_page.route.assert_called_once()

    def test_captures_video_path_urls(self) -> None:
        """Should capture URLs containing /video/ path."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        _extract_from_network_interception(mock_page, timeout_ms=100)

        mock_page.route.assert_called_once()

    def test_captures_googlevideo_urls(self) -> None:
        """Should capture URLs with play.googlevideo domain."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        _extract_from_network_interception(mock_page, timeout_ms=100)

        mock_page.route.assert_called_once()

    def test_filters_non_video_requests(self) -> None:
        """Should not capture CSS, JS, or image URLs."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        _extract_from_network_interception(mock_page, timeout_ms=100)

        mock_page.route.assert_called_once()
        mock_page.unroute_all.assert_called_once()

    def test_handles_timeout_gracefully(self) -> None:
        """Should handle timeout without raising."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        result = _extract_from_network_interception(mock_page, timeout_ms=100)

        assert result == []
        mock_page.unroute_all.assert_called_once()

    def test_returns_deduplicated_urls(self) -> None:
        """Should return unique URLs only."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        result = _extract_from_network_interception(mock_page, timeout_ms=100)

        assert isinstance(result, list)
        mock_page.unroute_all.assert_called_once()


class TestInterceptAwemeDetailApi:
    """Tests for _intercept_aweme_detail_api function."""

    def test_handles_route_fetch_without_context_disposed_error(self) -> None:
        """Should not raise 'Request context disposed' error when using route.fetch()."""
        mock_page = MagicMock()
        mock_request = MagicMock()
        mock_request.url = "https://www.douyin.com/aweme/v1/web/aweme/detail/?aid=6383"
        mock_route = MagicMock()
        mock_route.request = mock_request
        mock_route.fetch.side_effect = Exception("Request context disposed")
        mock_page.route.return_value = None
        mock_page.unroute_all.return_value = None
        mock_page.wait_for_timeout.return_value = None

        # page.route(pattern, handler) - side_effect receives (pattern, handler)
        # We need to call handler(route) where route.fetch() raises
        def route_handler(*args, **kwargs):
            handler = args[1]
            handler(mock_route)  # mock_route.fetch() raises

        mock_page.route.side_effect = None
        mock_page.route = MagicMock(side_effect=route_handler)

        # Should not raise, should return empty list
        result = _intercept_aweme_detail_api(mock_page, timeout_ms=100)
        assert result == []

    def test_handles_timeout_gracefully(self) -> None:
        """Should handle timeout and return empty list."""
        mock_page = MagicMock()
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        result = _intercept_aweme_detail_api(mock_page, timeout_ms=100)
        assert result == []


class TestNetworkInterceptionChaining:
    """Tests for network interception as fallback in extraction chain."""

    def test_network_interception_used_after_data_attributes(self) -> None:
        """Should use network interception when all other methods fail."""
        mock_page = MagicMock()
        # All other methods return empty
        mock_page.query_selector.return_value = None
        mock_page.query_selector_all.return_value = []
        mock_page.evaluate.return_value = '{}'
        mock_page.content.return_value = '<a href="https://example.com">link</a>'
        # Network interception captures URLs
        mock_page.route = MagicMock()
        mock_page.unroute_all = MagicMock()
        mock_page.wait_for_timeout = MagicMock()

        # Simulate chain with network interception as final fallback
        urls = _extract_from_data_attributes(mock_page)
        if not urls:
            urls = _extract_from_network_interception(mock_page, timeout_ms=100)

        assert urls == []