"""Step definitions for API feature."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from douyin_download.api import app


@pytest.fixture
async def api_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def extract_result():
    """Mock extraction result."""
    return ["https://v5-hl-mly-ov.zjcdn.com/test.mp4"]


@given("FastAPI 客戶端")
def given_api_client(api_client):
    """Set the FastAPI client for testing."""
    return api_client


@when('發送 GET 請求至 "{path}"')
async def when_send_get_request(api_client, path):
    """Send a GET request to specified path."""
    response = await api_client.get(path)
    return response


@then("回應狀態應為 {status_code}")
def then_response_status(response, status_code):
    """Verify response status code."""
    assert response.status_code == int(status_code)


@then('回應內容應為 {expected}')
def then_response_body_equals(response, expected):
    """Verify response body equals expected JSON."""
    import json
    expected_dict = json.loads(expected)
    assert response.json() == expected_dict


@then("回應內容應包含 \"{text}\"")
def then_response_contains(response, text):
    """Verify response contains specified text."""
    response_data = response.json()
    # Check if text is in any string field
    found = text in str(response_data)
    assert found, f"Expected '{text}' in {response_data}"