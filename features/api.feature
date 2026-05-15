Feature: FastAPI API Endpoints

  Scenario: Health check returns healthy status
    Given FastAPI client
    When I send GET request to "/health"
    Then response status should be 200
    And response should contain "healthy"

  Scenario: Download video synchronously
    Given FastAPI client
    When I send POST request to "/api/v1/download" with:
      | field    | value                              |
      | url      | https://www.douyin.com/video/123   |
      | quality  | 720p                               |
    Then response status should be 200
    And response should contain "status"

  Scenario: Download with callback creates pending task
    Given FastAPI client
    When I send POST request to "/api/v1/download" with:
      | field        | value                              |
      | url          | https://www.douyin.com/video/123   |
      | callback_url | https://example.com/webhook        |
    Then response status should be 200
    And response should contain "pending"
    And response should contain "task_id"

  Scenario: Get task status
    Given FastAPI client
    And I create a download task with callback
    When I send GET request to "/api/v1/tasks/{task_id}"
    Then response status should be 200
    And response should contain task details

  Scenario: List all tasks
    Given FastAPI client
    And I create a download task with callback
    When I send GET request to "/api/v1/tasks"
    Then response status should be 200
    And response should be a list

  Scenario: Cancel pending task
    Given FastAPI client
    And I create a download task with callback
    When I send DELETE request to "/api/v1/tasks/{task_id}"
    Then response status should be 200
    And response should contain "cancelled"