"""API steps for BDD tests."""

from pytest_bdd import given, when, then
from fastapi.testclient import TestClient


# Store client globally for step access
_client: TestClient = None
_created_task_id: str | None = None


@given("FastAPI client")
def fastapi_client():
    """Create FastAPI test client."""
    global _client
    from douyin_download.api import app
    _client = TestClient(app)
    return _client


@when("I send GET request to {path}")
def send_get_request(path: str):
    """Send GET request."""
    global _client
    return _client.get(path)


@when("I send POST request to {path} with:")
def send_post_request(path: str, table):
    """Send POST request with form data."""
    global _client
    data = {row["field"]: row["value"] for row in table}
    return _client.post(path, json=data)


@when("I send DELETE request to {path}")
def send_delete_request(path: str):
    """Send DELETE request."""
    global _client
    return _client.delete(path)


@then("response status should be {status}")
def check_status(response, status: int):
    """Check response status code."""
    assert response.status_code == status


@then("response should contain {key}")
def check_response_contains(response, key: str):
    """Check response JSON contains key."""
    data = response.json()
    assert key in data, f"Expected '{key}' in response: {data}"


@then("response should be a list")
def check_response_is_list(response):
    """Check response is a list."""
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"


@given("I create a download task with callback")
def create_download_task():
    """Create a download task with callback URL."""
    global _client, _created_task_id
    response = _client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )
    _created_task_id = response.json().get("task_id")


@when("I send GET request to {path}")
def send_get_request_with_task_id(path: str):
    """Send GET request with task_id substituted."""
    global _client, _created_task_id
    actual_path = path.replace("{task_id}", _created_task_id)
    return _client.get(actual_path)


@when("I send DELETE request to {path}")
def send_delete_request_with_task_id(path: str):
    """Send DELETE request with task_id substituted."""
    global _client, _created_task_id
    actual_path = path.replace("{task_id}", _created_task_id)
    return _client.delete(actual_path)


@then("response should contain task details")
def check_task_details(response):
    """Check response contains task fields."""
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert "video_url" in data