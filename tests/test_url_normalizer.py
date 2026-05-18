import pytest
from unittest.mock import patch, Mock
from douyin_download.url_normalizer import extract_video_id, validate_video_id, VideoUnavailableError, normalize, InvalidURLError


def test_normalize_clean_url():
    """乾淨 URL 直接正規化"""
    with patch('douyin_download.url_normalizer.validate_video_id', return_value=True):
        result = normalize("https://www.douyin.com/video/7385822337847635259")
        assert result == "https://www.douyin.com/video/7385822337847635259"


def test_normalize_share_text_extracts_url():
    """分享文字自動取出 URL"""
    with patch('douyin_download.url_normalizer.resolve_short_url') as mock_resolve, \
         patch('douyin_download.url_normalizer.validate_video_id', return_value=True):
        mock_resolve.return_value = "https://www.douyin.com/video/7385822337847635259"
        result = normalize("7.61 复制打开抖音... https://v.douyin.com/abc123/ ...")
        assert "7385822337847635259" in result


def test_normalize_no_url_raises_error():
    """無 URL 拋出 InvalidURLError"""
    with pytest.raises(InvalidURLError, match="No URL found"):
        normalize("這只是普通文字")


def test_extract_video_id_from_standard_url():
    """從標準 /video/ URL 提取 ID"""
    url = "https://www.douyin.com/video/7385822337847635259"
    video_id = extract_video_id(url)
    assert video_id == "7385822337847635259"


def test_extract_video_id_from_aweme_url():
    """從 aweme/ URL 提取 ID"""
    url = "https://www.douyin.com/aweme/7385822337847635259"
    video_id = extract_video_id(url)
    assert video_id == "7385822337847635259"


def test_extract_video_id_from_short_url():
    """從已解析的完整 URL 提取 ID"""
    url = "https://www.douyin.com/video/7385822337847635259"
    video_id = extract_video_id(url)
    assert video_id == "7385822337847635259"


def test_extract_video_id_returns_none_for_invalid():
    """不支援格式回傳 None"""
    url = "https://www.douyin.com/user/123"
    video_id = extract_video_id(url)
    assert video_id is None


def test_validate_video_id_exists():
    """存在的影片 ID 回傳 True"""
    with patch('httpx.Client') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = validate_video_id("7385822337847635259")
        assert result is True


def test_validate_video_id_not_found():
    """不存在的影片拋出 VideoUnavailableError"""
    with patch('httpx.Client') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        with pytest.raises(VideoUnavailableError):
            validate_video_id("0000000000000000000")
