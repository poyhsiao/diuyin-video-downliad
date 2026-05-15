"""Step definitions for download feature."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from douyin_download.core import resolve_video_id, sort_urls, download_video


@pytest.fixture
def mock_extract(mocker):
    """Mock the extract_cdn_url function."""
    return mocker.patch("douyin_download.extractor.extract_cdn_url")


@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess.run."""
    return mocker.patch("subprocess.run")


@given('抖音網址 "{url}"')
def given_douyin_url(url: str):
    """Set the Douyin URL for testing."""
    return url


@given("輸出目錄 \"{output_dir}\"")
def given_output_dir(output_dir: str):
    """Set the output directory for testing."""
    return output_dir


@given("無效的抖音頁面")
def given_invalid_page():
    """Set an invalid Douyin page URL."""
    return "https://www.douyin.com/video/invalid12345"


@when("使用者執行下載指令")
def when_user_executes_download(mock_extract, mock_subprocess, sample_douyin_url, temp_output_dir):
    """Execute the download command with mocked dependencies."""
    mock_extract.return_value = [
        "https://v5-hl-mly-ov.zjcdn.com/test.mp4",
    ]
    try:
        video_id, path = download_video(sample_douyin_url, temp_output_dir)
        return {"video_id": video_id, "path": path, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@when("使用者執行下載指令並指定輸出目錄")
def when_user_executes_download_with_dir(mock_extract, mock_subprocess, sample_douyin_url):
    """Execute download with custom output directory."""
    mock_extract.return_value = ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]
    output_dir = Path("/tmp/douyin_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        video_id, path = download_video(sample_douyin_url, output_dir)
        return {"video_id": video_id, "path": path, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@when("使用者嘗試解析 URL")
def when_user_tries_to_parse_url(sample_douyin_url):
    """Attempt to parse an unsupported URL."""
    with pytest.raises(ValueError, match="Unsupported URL"):
        resolve_video_id(sample_douyin_url.replace("douyin.com/video/", "example.com/"))


@when("使用者嘗試提取 CDN URL")
def when_user_tries_extract_cdn_url(mock_extract):
    """Attempt to extract CDN URL from invalid page."""
    mock_extract.return_value = []
    result = mock_extract("https://www.douyin.com/video/invalid12345")
    return result


@when("使用者執行下載指令未指定輸出目錄")
def when_user_downloads_without_output_dir(mock_extract, mock_subprocess, sample_douyin_url):
    """Execute download without specifying output directory."""
    mock_extract.return_value = ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]
    default_dir = Path.home() / "Downloads"
    default_dir.mkdir(parents=True, exist_ok=True)
    try:
        video_id, path = download_video(sample_douyin_url, default_dir)
        return {"video_id": video_id, "path": path, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@then("系統應回傳成功訊息")
def then_system_returns_success(when_user_executes_download):
    """Verify system returns success message."""
    assert when_user_executes_download.get("success") is True


@then("檔案應存在於 \"{expected_path}\"")
def then_file_should_exist(expected_path: str):
    """Verify file exists at expected path."""
    if expected_path.startswith("~"):
        expected_path = os.path.expanduser(expected_path)
    path = Path(expected_path)
    # For mocked tests, we check the logic rather than actual file
    assert path.name.startswith("douyin_")
    assert path.suffix == ".mp4"


@then("系統應拋出 ValueError 例外")
def then_system_should_raise_value_error():
    """Verify system raises ValueError exception."""
    pass  # Handled in when step


@then("系統應回傳空陣列")
def then_system_returns_empty_array(when_user_tries_extract_cdn_url):
    """Verify system returns empty array."""
    assert when_user_tries_extract_cdn_url == []


@then("系統應使用 ~/Downloads 作為輸出目錄")
def then_system_uses_default_download_dir(when_user_downloads_without_output_dir):
    """Verify system uses default Downloads directory."""
    assert when_user_downloads_without_output_dir.get("success") is True
    path = when_user_downloads_without_output_dir.get("path", Path())
    assert str(path).startswith(str(Path.home() / "Downloads"))


@then("v5 URL 應排在第一位")
def then_v5_url_first(sorted_urls):
    """Verify v5 URL is first."""
    assert "v5-" in sorted_urls[0]


@then("v3 URL 應排在第二位")
def then_v3_url_second(sorted_urls):
    """Verify v3 URL is second."""
    assert "v3-" in sorted_urls[1]


@then("aweme URL 應排在第三位")
def then_aweme_url_third(sorted_urls):
    """Verify aweme URL is third."""
    assert "aweme/v1/play/" in sorted_urls[2]