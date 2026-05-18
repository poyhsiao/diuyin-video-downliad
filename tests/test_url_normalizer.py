import pytest
from douyin_download.url_normalizer import extract_video_id


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
