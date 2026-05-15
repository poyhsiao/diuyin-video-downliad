Feature: 抖音影片下載功能

  Scenario: 下載普通 URL 的影片
    Given 抖音網址 "https://www.douyin.com/video/7637075230132849971"
    When 使用者執行下載指令
    Then 系統應回傳成功訊息
    And 檔案應存在於 ~/Downloads/douyin_7637075230132849971.mp4

  Scenario: 下載至自訂目錄
    Given 抖音網址 "https://www.douyin.com/video/7637075230132849971"
    And 輸出目錄 "/tmp/douyin_test"
    When 使用者執行下載指令並指定輸出目錄
    Then 檔案應存在於 /tmp/douyin_test/douyin_7637075230132849971.mp4

  Scenario: 不支援的 URL 格式
    Given 抖音網址 "https://example.com/video"
    When 使用者嘗試解析 URL
    Then 系統應拋出 ValueError 例外

  Scenario: 無法取得影片 URL 時
    Given 無效的抖音頁面
    When 使用者嘗試提取 CDN URL
    Then 系統應回傳空陣列

  Scenario: 使用者未指定輸出目錄時使用預設值
    Given 抖音網址 "https://www.douyin.com/video/7637075230132849971"
    When 使用者執行下載指令未指定輸出目錄
    Then 系統應使用 ~/Downloads 作為輸出目錄