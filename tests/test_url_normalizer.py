import pytest
from douyin_download.url_normalizer import extract_url_from_text

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