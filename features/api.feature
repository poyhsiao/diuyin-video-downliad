Feature: FastAPI 預留端點

  Scenario: 根路徑回應
    Given FastAPI 客戶端
    When 發送 GET 請求至 "/"
    Then 回應狀態應為 200
    And 回應內容應為 {"status": "coming_soon"}

  Scenario: 下載端點預留
    Given FastAPI 客戶端
    When 發送 GET 請求至 "/download?url=https://www.douyin.com/video/7637075230132849971"
    Then 回應狀態應為 200
    And 回應內容應包含 "coming_soon"