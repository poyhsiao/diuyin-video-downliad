Feature: CLI 指令

  Scenario: download 子指令存在
    Given 已安裝 douyin CLI
    When 執行 "douyin download --help"
    Then 輸出應包含 "Download a Douyin video"

  Scenario: CLI 指令顯示正確用法
    Given 已安裝 douyin CLI
    When 執行 "douyin download --help"
    Then 輸出應包含 "URL [OUTPUT_DIR]"