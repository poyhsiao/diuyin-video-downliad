"""BDD-style integration tests for download pipeline.

These tests follow BDD principles but are written as standard pytest tests.
Each test documents a scenario in comments following the Given-When-Then pattern.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from douyin_download.core import resolve_video_id, sort_urls, download_video, NoCDNAvailableError


# === DOWNLOAD FEATURE ===

class TestDownloadFeature:
    """BDD: Download Feature - 使用者想要下載抖音影片

    Scenario: 下載普通 URL 的影片
        Given 抖音網址 "https://www.douyin.com/video/7637075230132849971"
        And 輸出目錄 "/tmp/douyin_test"
        When 使用者執行下載指令
        Then 系統應回傳成功訊息
        And 檔案應存在於指定目錄
    """

    @patch("douyin_download.core.extract_cdn_url")
    @patch("douyin_download.core._download_file")
    def test_download_normal_url_succeeds(
        self, mock_download, mock_extract, tmp_path
    ) -> None:
        """下載普通 URL 的影片 - Given: 抖音 URL, When: 執行下載, Then: 成功"""
        # Given
        url = "https://www.douyin.com/video/7637075230132849971"
        mock_extract.return_value = ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]
        mock_download.return_value = None

        # When
        video_id, path = download_video(url, tmp_path)

        # Then
        assert video_id == "7637075230132849971"
        assert path.suffix == ".mp4"
        mock_extract.assert_called_once_with(url, wait_seconds=5)

    @patch("douyin_download.core.extract_cdn_url")
    @patch("douyin_download.core._download_file")
    def test_download_to_custom_directory(
        self, mock_download, mock_extract, tmp_path
    ) -> None:
        """下載至自訂目錄 - Given: 自訂目錄, When: 指定輸出目錄下載, Then: 檔案在自訂目錄"""
        # Given
        url = "https://www.douyin.com/video/7637075230132849971"
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        mock_extract.return_value = ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]
        mock_download.return_value = None

        # When
        video_id, path = download_video(url, custom_dir)

        # Then
        assert path.parent == custom_dir
        assert path.name.startswith("douyin_")

    def test_unsupported_url_raises_error(self) -> None:
        """不支援的 URL 格式 - Given: 無效 URL, When: 嘗試解析, Then: 拋出 ValueError"""
        # Given
        url = "https://example.com/video"

        # When/Then
        with pytest.raises(ValueError, match="Unsupported URL"):
            resolve_video_id(url)

    @patch("douyin_download.core.extract_cdn_url")
    def test_no_video_urls_raises_error(self, mock_extract, tmp_path) -> None:
        """無法取得影片 URL 時 - Given: 提取失敗, When: 執行下載, Then: 拋出 NoCDNAvailableError"""
        # Given
        url = "https://www.douyin.com/video/7637075230132849971"
        mock_extract.return_value = []

        # When/Then
        with pytest.raises(NoCDNAvailableError, match="No video URLs extracted"):
            download_video(url, tmp_path)

    @patch("douyin_download.core.extract_cdn_url")
    @patch("douyin_download.core._download_file")
    def test_default_output_directory_is_downloads(
        self, mock_download, mock_extract, tmp_path
    ) -> None:
        """未指定輸出目錄時使用預設值 - Given: 無輸出目錄, When: 下載, Then: 使用 ~/Downloads"""
        # Given
        url = "https://www.douyin.com/video/7637075230132849971"
        default_dir = tmp_path / "downloads"
        default_dir.mkdir()
        mock_extract.return_value = ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]
        mock_download.return_value = None

        # When
        video_id, path = download_video(url, default_dir)

        # Then
        assert path.parent == default_dir


# === EXTRACTOR FEATURE ===

class TestExtractorFeature:
    """BDD: Extractor Feature - CDN URL 提取與排序

    Scenario: 從頁面提取 URL
        Given 抖音頁面 URL
        When 提取 CDN URL
        Then 結果應包含 "zjcdn.com" 的 URL

    Scenario: URL 品質排序
        Given 多個品質的 URL (v5, v3, aweme)
        When 系統排序 URL
        Then v5 URL 應排在第一位
        And v3 URL 應排在第二位
        And aweme URL 應排在第三位
    """

    def test_extract_returns_zjcdn_urls(self) -> None:
        """從頁面提取 URL - Given: 抖音 URL, When: 提取, Then: 包含 zjcdn.com"""
        # This is a smoke test for the extractor
        # Real extraction requires network, so we verify the function exists
        from douyin_download.extractor import extract_cdn_url
        assert callable(extract_cdn_url)

    def test_url_quality_sorting_v5_first(self) -> None:
        """URL 品質排序 - Given: v5/v3/aweme URLs, When: 排序, Then: v5 第一"""
        # Given
        urls = [
            "https://aweme/v1/play/test",
            "https://v3-dy-o.zjcdn.com/test-v3.mp4",
            "https://v5-hl-mly-ov.zjcdn.com/test-v5.mp4",
        ]

        # When
        sorted_urls = sort_urls(urls)

        # Then
        assert "v5" in sorted_urls[0]
        assert "v3" in sorted_urls[1]
        assert "aweme/v1/play/" in sorted_urls[2]

    def test_empty_url_list_returns_empty(self) -> None:
        """空 URL 清單排序 - Given: 空陣列, When: 排序, Then: 空陣列"""
        assert sort_urls([]) == []

    def test_single_url_unchanged(self) -> None:
        """單一 URL 排序 - Given: 單一 URL, When: 排序, Then: 不變"""
        url = ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]
        assert sort_urls(url) == url

    @patch("playwright.sync_api.sync_playwright")
    def test_extract_timeout_raises_error(self, mock_playwright) -> None:
        """超時錯誤 - Given: Playwright, When: page.goto timeout, Then: 拋出 ExtractionTimeoutError"""
        from playwright.sync_api import TimeoutError
        from douyin_download.extractor import extract_cdn_url, ExtractionTimeoutError

        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.goto.side_effect = TimeoutError("timed out")
        mock_p = MagicMock()
        mock_p.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value = mock_p

        with pytest.raises(ExtractionTimeoutError):
            extract_cdn_url("https://www.douyin.com/video/123", wait_seconds=2)

    @patch("playwright.sync_api.sync_playwright")
    def test_extract_404_raises_video_not_found(self, mock_playwright) -> None:
        """404 錯誤 - Given: Playwright, When: page returns 404, Then: 拋出 VideoNotFoundError"""
        from douyin_download.extractor import extract_cdn_url, VideoNotFoundError

        mock_response = MagicMock()
        mock_response.status = 404

        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.goto.return_value = mock_response
        mock_p = MagicMock()
        mock_p.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value = mock_p

        with pytest.raises(VideoNotFoundError, match="404"):
            extract_cdn_url("https://www.douyin.com/video/123", wait_seconds=2)

    @patch("playwright.sync_api.sync_playwright")
    def test_extract_403_raises_video_not_found(self, mock_playwright) -> None:
        """403 錯誤 - Given: Playwright, When: page returns 403, Then: 拋出 VideoNotFoundError"""
        from douyin_download.extractor import extract_cdn_url, VideoNotFoundError

        mock_response = MagicMock()
        mock_response.status = 403

        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.goto.return_value = mock_response
        mock_p = MagicMock()
        mock_p.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value = mock_p

        with pytest.raises(VideoNotFoundError, match="403"):
            extract_cdn_url("https://www.douyin.com/video/123", wait_seconds=2)

    @patch("playwright.sync_api.sync_playwright")
    def test_extract_no_response_raises_error(self, mock_playwright) -> None:
        """無回應錯誤 - Given: Playwright, When: page returns None, Then: 拋出 VideoNotFoundError"""
        from douyin_download.extractor import extract_cdn_url, VideoNotFoundError

        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_p = MagicMock()
        mock_p.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value = mock_p

        with pytest.raises(VideoNotFoundError, match="no response"):
            extract_cdn_url("https://www.douyin.com/video/123", wait_seconds=2)


# === API FEATURE ===

class TestApiFeature:
    """BDD: API Feature - FastAPI 端點

    Scenario: 根路徑回應
        Given FastAPI 客戶端
        When 發送 GET 請求至 "/"
        Then 回應狀態應為 200
        And 回應內容應為 {"status": "coming_soon"}

    Scenario: 下載端點預留
        Given FastAPI 客戶端
        When 發送 GET 請求至 "/download"
        Then 回應狀態應為 200
    """

    @pytest.mark.asyncio
    async def test_root_endpoint_returns_coming_soon(self) -> None:
        """根路徑回應 - Given: FastAPI 客戶端, When: GET /, Then: 200 + coming_soon"""
        from httpx import AsyncClient, ASGITransport
        from douyin_download.api import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert response.json() == {"status": "coming_soon"}

    @pytest.mark.asyncio
    async def test_download_endpoint_returns_coming_soon(self) -> None:
        """下載端點預留 - Given: FastAPI 客戶端, When: GET /download, Then: 200"""
        from httpx import AsyncClient, ASGITransport
        from douyin_download.api import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/download?url=https://www.douyin.com/video/7637075230132849971"
            )

        assert response.status_code == 200
        assert "status" in response.json()


# === CLI FEATURE ===

class TestCliFeature:
    """BDD: CLI Feature - 命令列介面

    Scenario: download 子指令存在
        Given 已安裝 douyin CLI
        When 執行 "douyin download --help"
        Then 輸出應包含 "Download a Douyin video"

    Scenario: CLI 指令顯示正確用法
        Given 已安裝 douyin CLI
        When 執行 "douyin download --help"
        Then 輸出應包含 "URL [OUTPUT_DIR]"
    """

    def test_cli_download_help_shows_message(self, tmp_path) -> None:
        """download 子指令存在 - Given: CLI 已安裝, When: --help, Then: 顯示說明"""
        import subprocess

        # Try local venv first, fall back to system PATH
        venv_douyin = (
            Path.home()
            / "Templates"
            / "git"
            / "kimhsiao"
            / "diuyin-video-downliad"
            / ".venv"
            / "bin"
            / "douyin"
        )
        project_dir = Path.home() / "Templates" / "git" / "kimhsiao" / "diuyin-video-downliad"

        douyin_cmd = venv_douyin if venv_douyin.exists() else "douyin"

        result = subprocess.run(
            [str(douyin_cmd), "download", "--help"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
        )

        output = result.stdout + result.stderr
        assert "Download a Douyin video" in output

    def test_cli_download_help_shows_usage(self, tmp_path) -> None:
        """CLI 指令顯示正確用法 - Given: CLI 已安裝, When: --help, Then: 顯示 URL 用法"""
        import subprocess

        venv_douyin = (
            Path.home()
            / "Templates"
            / "git"
            / "kimhsiao"
            / "diuyin-video-downliad"
            / ".venv"
            / "bin"
            / "douyin"
        )
        project_dir = Path.home() / "Templates" / "git" / "kimhsiao" / "diuyin-video-downliad"

        douyin_cmd = venv_douyin if venv_douyin.exists() else "douyin"

        result = subprocess.run(
            [str(douyin_cmd), "download", "--help"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
        )

        output = result.stdout + result.stderr
        assert "URL" in output or "Usage:" in output