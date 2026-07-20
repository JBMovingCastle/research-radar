# Contributing

1. 新建分支并保持改动聚焦。
2. 新适配器必须返回统一 `PaperCandidate` / `SourceResult`，提供离线固定响应测试，并在 `docs/ADAPTERS.md` 写明密钥、限制和证据等级。
3. 不提交密钥、收件人、真实运行记录、付费全文或绕过访问控制的代码。
4. 运行 `python3 -m unittest discover -s tests -v` 后提交 Pull Request。

新增来源时优先官方API、公开RSS和合法开放获取链接。来源数量不是质量指标；不可稳定验证的连接器不应列为默认可用。
