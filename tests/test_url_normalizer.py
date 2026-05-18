import pytest
from unittest.mock import patch, Mock
from httpx import TimeoutException

from douyin_download.url_normalizer import extract_url_from_text, resolve_short_url, InvalidURLError


def test_extract_url_from_clean_text():
    """乾淨 URL 原樣回傳"""
    url = extract_url_from_text("https://www.douyin.com/video/7385822337847635259")
    assert url == "https://www.douyin.com/video/7385822337847635259"

def test_extract_url_from_share_text():
    """從複雜分享文字取出 URL"""
    text = "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/ NWZ:/"
    url = extract_url_from_text(text)
    assert url == "https://v.douyin.com/NdvdvNIN50I"

def test_extract_url_from_multiple_takes_first():
    """多個 URL 只取第一個"""
    text = "第一個 https://example.com/a 第二個 https://example.com/b"
    url = extract_url_from_text(text)
    assert url == "https://example.com/a"

def test_extract_url_returns_none_when_no_url():
    """無 URL 的文字回傳 None"""
    text = "這只是普通文字，沒有網址"
    url = extract_url_from_text(text)
    assert url is None


def test_resolve_short_url_success():
    """成功解析短網址"""
    with patch('httpx.Client') as mock_client:
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.url = "https://www.douyin.com/video/7385822337847635259"
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = resolve_short_url("https://v.douyin.com/abc123")
        assert result == "https://www.douyin.com/video/7385822337847635259"


def test_resolve_short_url_http_error():
    """HTTP 錯誤拋出 InvalidURLError"""
    with patch('httpx.Client') as mock_client:
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        with pytest.raises(InvalidURLError):
            resolve_short_url("https://v.douyin.com/notfound")