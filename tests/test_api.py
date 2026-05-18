"""Tests for API endpoints."""

import pytest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from douyin_download.api import app
from douyin_download.url_normalizer import InvalidURLError, VideoUnavailableError


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_download_with_share_text_normalizes_url(client):
    """分享文字格式的 URL 會被正規化"""
    with patch('douyin_download.api.normalize') as mock_normal:
        mock_normal.return_value = "https://www.douyin.com/video/7385822337847635259"
        with patch('douyin_download.api.download_video') as mock_download:
            test_file = Path("/tmp/test.mp4")
            test_file.touch()
            mock_download.return_value = ("7385822337847635259", test_file)
            response = client.post(
                "/api/v1/download",
                data={"url": "7.61 复制打开抖音... https://v.douyin.com/xxx/ ..."}
            )
            mock_normal.assert_called_once()
            assert response.status_code == 200


def test_download_invalid_url_returns_400(client):
    """無效 URL 回傳 HTTP 400"""
    with patch('douyin_download.api.normalize') as mock_normal:
        mock_normal.side_effect = InvalidURLError("No URL found")
        response = client.post(
            "/api/v1/download",
            data={"url": "這只是普通文字"}
        )
        assert response.status_code == 400
        detail = response.json().get("detail", {})
        assert detail.get("code") == "URL_RESOLVE_FAILED"


def test_download_video_not_available_returns_400(client):
    """影片不存在回傳 HTTP 400"""
    with patch('douyin_download.api.normalize') as mock_normal:
        mock_normal.side_effect = VideoUnavailableError("Video not available")
        response = client.post(
            "/api/v1/download",
            data={"url": "https://v.douyin.com/invalid"}
        )
        assert response.status_code == 400
        detail = response.json().get("detail", {})
        assert detail.get("code") == "VIDEO_NOT_AVAILABLE"


def test_download_sync_mode(client):
    """Test synchronous download returns video file."""
    test_file = Path("/tmp/test_sync.mp4")
    test_file.touch()
    mock_result = ("vid_123", test_file)

    with patch("douyin_download.api.normalize", return_value="https://www.douyin.com/video/123"):
        with patch("douyin_download.api.download_video", return_value=mock_result):
            response = client.post(
                "/api/v1/download",
                data={
                    "url": "https://www.douyin.com/video/123",
                    "quality": "720p",
                },
            )

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"


def test_download_with_callback(client):
    """Test async download with callback."""
    with patch("douyin_download.api.normalize", return_value="https://www.douyin.com/video/123"):
        response = client.post(
            "/api/v1/download",
            data={
                "url": "https://www.douyin.com/video/123",
                "callback_url": "https://example.com/webhook",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "task_id" in data


def test_get_task(client):
    """Test get task status."""
    # First create a task
    with patch("douyin_download.api.normalize", return_value="https://www.douyin.com/video/123"):
        create_response = client.post(
            "/api/v1/download",
            data={
                "url": "https://www.douyin.com/video/123",
                "callback_url": "https://example.com/webhook",
            },
        )
    task_id = create_response.json()["task_id"]

    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id


def test_get_task_not_found(client):
    """Test get task not found."""
    response = client.get("/api/v1/tasks/nonexistent")
    assert response.status_code == 404


def test_list_tasks(client):
    """Test list all tasks."""
    # Create a task first
    with patch("douyin_download.api.normalize", return_value="https://www.douyin.com/video/123"):
        client.post(
            "/api/v1/download",
            data={
                "url": "https://www.douyin.com/video/123",
                "callback_url": "https://example.com/webhook",
            },
        )

    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_cancel_task(client):
    """Test cancel task."""
    # Create a task
    with patch("douyin_download.api.normalize", return_value="https://www.douyin.com/video/123"):
        create_response = client.post(
            "/api/v1/download",
            data={
                "url": "https://www.douyin.com/video/123",
                "callback_url": "https://example.com/webhook",
            },
        )
    task_id = create_response.json()["task_id"]

    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"