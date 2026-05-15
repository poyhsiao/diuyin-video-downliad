"""Tests for API endpoints."""

import pytest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from douyin_download.api import app


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


def test_download_sync_mode(client):
    """Test synchronous download."""
    mock_result = ("vid_123", Path("/tmp/test.mp4"))
    mock_result[1].touch()

    with patch("douyin_download.api.download_video", return_value=mock_result):
        response = client.post(
            "/api/v1/download",
            json={
                "url": "https://www.douyin.com/video/123",
                "quality": "720p",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["video_id"] == "vid_123"


def test_download_with_callback(client):
    """Test async download with callback."""
    response = client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["task_id"] is not None


def test_get_task(client):
    """Test get task status."""
    # First create a task
    create_response = client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )
    task_id = create_response.json()["task_id"]

    # Get task - status may be "pending" (task created) or "failed" (background exec attempted)
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] in ("pending", "failed")


def test_get_task_not_found(client):
    """Test get non-existent task."""
    response = client.get("/api/v1/tasks/non-existent-id")
    assert response.status_code == 404


def test_list_tasks(client):
    """Test list all tasks."""
    # Create a task first
    client.post(
        "/api/v1/download",
        json={
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
    create_response = client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )
    task_id = create_response.json()["task_id"]

    # Cancel it
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
