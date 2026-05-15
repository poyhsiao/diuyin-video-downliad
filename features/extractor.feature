Feature: CDN URL 多層 Fallback 提取功能

  Scenario: 從 <video> 標籤提取 URL
    Given 抖音頁面包含 "<video src='https://v5.video.mp4'></video>"
    When 提取 CDN URL
    Then 結果應包含 "https://v5.video.mp4"
    And 結果應至少有 1 個 URL

  Scenario: Fallback 到 <source> 標籤
    Given 抖音頁面無 <video> 但有 "<source src='https://v3.source.mp4'>"
    When 提取 CDN URL
    Then 結果應包含 "https://v3.source.mp4"

  Scenario: Fallback 到 __pace_f
    Given 抖音頁面無 DOM 標籤但有 __pace_f 数据 '{"video": "https://v5.pace.mp4"}'
    When 提取 CDN URL
    Then 結果應包含 "https://v5.pace.mp4"

  Scenario: __pace_f 返回 list 時不崩潰
    Given __pace_f 返回列表 "[1, 2, 3]"
    When 提取 CDN URL
    Then 結果應為空陣列

  Scenario: 所有方法都失敗
    Given 抖音頁面無任何視頻 URL
    When 提取 CDN URL
    Then 結果應為空陣列

  Scenario: URL 品質排序
    Given 一組 URL ["https://aweme/v1/play/test", "https://aweme/v3-test", "https://aweme/v5-test"]
    When 系統排序 URL
    Then v5 URL 應排在第一位
    And v3 URL 應排在第二位
    And aweme URL 應排在第三位