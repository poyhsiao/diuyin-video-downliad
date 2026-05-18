"""BDD tests for URL normalizer feature.

Tests follow BDD principles as standard pytest classes with Given-When-Then in docstrings.
"""

import pytest
from unittest.mock import patch, Mock

from douyin_download.url_normalizer import (
    extract_url_from_text,
    resolve_short_url,
    extract_video_id,
    validate_video_id,
    normalize,
    InvalidURLError,
    VideoUnavailableError,
)


class TestExtractUrlFromText:
    """Feature: URL Extraction from Share Text

    Scenario: 從分享文字正確取出 URL
        Given 用戶分享文字 "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/ NWZ:/"
        When 系統呼叫 extract_url_from_text
        Then 結果應為 "https://v.douyin.com/NdvdvNIN50I"
    """

    def test_extracts_url_from_share_text(self) -> None:
        """從分享文字正確取出 URL - Given: 分享文字含 URL, When: 呼叫 extract_url_from_text, Then: 回傳 URL"""
        text = "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/ NWZ:/"
        result = extract_url_from_text(text)
        assert result == "https://v.douyin.com/NdvdvNIN50I"

    def test_returns_none_for_text_without_url(self) -> None:
        """處理無 URL 的純文字 - Given: 純文字無 URL, When: 呼叫 extract_url_from_text, Then: 回傳 None"""
        text = "這只是普通文字"
        result = extract_url_from_text(text)
        assert result is None

    def test_strips_trailing_slash_from_url(self) -> None:
        """URL 結尾斜線會被移除"""
        text = "看這個影片 https://v.douyin.com/abc123/ "
        result = extract_url_from_text(text)
        assert result == "https://v.douyin.com/abc123"


class TestResolveShortUrl:
    """Feature: Short URL Resolution

    Scenario: 解析短網址為完整 URL
        Given 短網址 "https://v.douyin.com/abc123"
        When 系統呼叫 resolve_short_url
        Then 結果應為 "https://www.douyin.com/video/7385822337847635259"
    """

    def test_resolves_short_url_to_final_url(self) -> None:
        """解析短網址為完整 URL - Given: 短網址, When: 呼叫 resolve_short_url, Then: 回傳完整 URL"""
        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.url = "https://www.douyin.com/video/7385822337847635259"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = resolve_short_url("https://v.douyin.com/abc123")
            assert result == "https://www.douyin.com/video/7385822337847635259"


class TestExtractVideoId:
    """Feature: Video ID Extraction

    Scenario: 從 URL 提取影片 ID
        Given URL "https://www.douyin.com/video/7385822337847635259"
        When 系統呼叫 extract_video_id
        Then 結果應為 "7385822337847635259"
    """

    def test_extracts_video_id_from_standard_url(self) -> None:
        """從標準 URL 提取影片 ID - Given: 標準影片 URL, When: 呼叫 extract_video_id, Then: 回傳 ID"""
        url = "https://www.douyin.com/video/7385822337847635259"
        result = extract_video_id(url)
        assert result == "7385822337847635259"

    def test_extracts_video_id_from_aweme_url(self) -> None:
        """從 aweme URL 提取 ID"""
        url = "https://www.douyin.com/aweme/7385822337847635259"
        result = extract_video_id(url)
        assert result == "7385822337847635259"

    def test_returns_none_for_unsupported_format(self) -> None:
        """不支援格式回傳 None"""
        url = "https://www.douyin.com/user/123"
        result = extract_video_id(url)
        assert result is None


class TestValidateVideoId:
    """Feature: Video ID Validation

    Scenario: 驗證存在的影片
        Given 存在的影片 ID "7385822337847635259"
        When 系統呼叫 validate_video_id
        Then 返回 True

    Scenario: 驗證不存在的影片
        Given 不存在的影片 ID "0000000000000000000"
        When 系統呼叫 validate_video_id
        Then 拋出 VideoUnavailableError
    """

    def test_returns_true_for_existing_video(self) -> None:
        """驗證存在的影片 - Given: 存在的影片 ID, When: 呼叫 validate_video_id, Then: 回傳 True"""
        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = validate_video_id("7385822337847635259")
            assert result is True

    def test_raises_error_for_nonexistent_video(self) -> None:
        """驗證不存在的影片 - Given: 不存在的影片 ID, When: 呼叫 validate_video_id, Then: 拋出 VideoUnavailableError"""
        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            with pytest.raises(VideoUnavailableError, match="not found"):
                validate_video_id("0000000000000000000")

    def test_raises_error_for_access_denied(self) -> None:
        """403 錯誤拋出 VideoUnavailableError"""
        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            with pytest.raises(VideoUnavailableError, match="access denied"):
                validate_video_id("7385822337847635259")


class TestNormalize:
    """Feature: Full Normalization Pipeline

    Scenario: 完整流程 - 分享文字到正規化 URL
        Given 用戶分享文字 "7.61 复制打开抖音... https://v.douyin.com/xxx/ ..."
        When 系統呼叫 normalize
        Then 返回 "https://www.douyin.com/video/7385822337847635259"
    """

    def test_normalize_clean_url(self) -> None:
        """乾淨 URL 直接正規化"""
        with patch("douyin_download.url_normalizer.validate_video_id", return_value=True):
            result = normalize("https://www.douyin.com/video/7385822337847635259")
            assert result == "https://www.douyin.com/video/7385822337847635259"

    def test_normalize_share_text_extracts_url(self) -> None:
        """分享文字自動取出 URL 並解析"""
        with patch("douyin_download.url_normalizer.resolve_short_url") as mock_resolve, \
             patch("douyin_download.url_normalizer.validate_video_id", return_value=True):
            mock_resolve.return_value = "https://www.douyin.com/video/7385822337847635259"
            result = normalize("7.61 复制打开抖音... https://v.douyin.com/abc123/ ...")
            assert "7385822337847635259" in result

    def test_normalize_no_url_raises_error(self) -> None:
        """無 URL 拋出 InvalidURLError"""
        with pytest.raises(InvalidURLError, match="No URL found"):
            normalize("這只是普通文字")