# Research Radar v0.1.2

## CI 修复

- 修复 GitHub Actions：现在会先初始化一份新配置，再检查模板与目录。
- CI 只在 `main` 推送和 Pull Request 时运行，不会因发布标签而重复发送失败通知。
- 修正报告模板配置的回归测试数据。

本版本的离线检查包含 23 项测试，以及全新目录中的 `init → validate → doctor` 验证。
