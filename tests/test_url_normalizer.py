import pytest
from unittest.mock import patch, Mock
from douyin_download.url_normalizer import extract_video_id, validate_video_id, VideoUnavailableError


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
        mock_client.return_value.__enter__.return_value.head.return_value = mock_response
        result = validate_video_id("7385822337847635259")
        assert result is True


def test_validate_video_id_not_found():
    """不存在的影片拋出 VideoUnavailableError"""
    with patch('httpx.Client') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.return_value.__enter__.return_value.head.return_value = mock_response
        with pytest.raises(VideoUnavailableError):
            validate_video_id("0000000000000000000")
