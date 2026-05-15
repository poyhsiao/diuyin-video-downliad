"""Tests for task management."""

import pytest
from pathlib import Path

from douyin_download.models import TaskStatus
from douyin_download.tasks import TaskManager, get_task_manager


def test_create_task():
    """Test task creation."""
    manager = TaskManager()
    task = manager.create_task(
        video_url="https://example.com/video/123",
        quality="720p",
    )
    assert task.task_id is not None
    assert task.video_url == "https://example.com/video/123"
    assert task.quality == "720p"
    assert task.status == TaskStatus.PENDING


def test_get_task():
    """Test getting task by ID."""
    manager = TaskManager()
    task = manager.create_task(video_url="https://example.com/video/123")
    found = manager.get_task(task.task_id)
    assert found is not None
    assert found.task_id == task.task_id


def test_get_task_not_found():
    """Test getting non-existent task."""
    manager = TaskManager()
    found = manager.get_task("non-existent-id")
    assert found is None


def test_list_tasks():
    """Test listing all tasks."""
    manager = TaskManager()
    task1 = manager.create_task(video_url="https://example.com/video/1")
    task2 = manager.create_task(video_url="https://example.com/video/2")
    tasks = manager.list_tasks()
    assert len(tasks) == 2


def test_update_task():
    """Test updating task fields."""
    manager = TaskManager()
    task = manager.create_task(video_url="https://example.com/video/123")
    manager.update_task(
        task.task_id,
        status=TaskStatus.RUNNING,
        video_id="vid_123",
    )
    updated = manager.get_task(task.task_id)
    assert updated.status == TaskStatus.RUNNING
    assert updated.video_id == "vid_123"


def test_get_task_manager_singleton():
    """Test task manager singleton."""
    m1 = get_task_manager()
    m2 = get_task_manager()
    assert m1 is m2