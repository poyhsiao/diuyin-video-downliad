Feature: CDN URL 提取功能

  Scenario: 從頁面提取 URL
    Given 抖音頁面 URL "https://www.douyin.com/video/7637075230132849971"
    When 提取 CDN URL
    Then 結果應包含 "zjcdn.com" 的 URL
    And 結果應至少有 1 個 URL

  Scenario: URL 品質排序
    Given 一組 URL ["https://aweme/v1/play/test", "https://aweme/v3-test", "https://aweme/v5-test"]
    When 系統排序 URL
    Then v5 URL 應排在第一位
    And v3 URL 應排在第二位
    And aweme URL 應排在第三位

  Scenario: 空 URL 清單排序
    Given 空 URL 清單
    When 系統排序 URL
    Then 結果應為空陣列

  Scenario: 單一 URL 排序
    Given 單一 URL "https://v5-hl-mly-ov.zjcdn.com/test.mp4"
    When 系統排序 URL
    Then 結果應只有一個 URL