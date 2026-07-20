# 上游项目与设计来源

本仓库采用独立、精简的标准库实现。以下项目用于方案比较和接口设计参考：

- [LucaJiang/DailyPaper](https://github.com/LucaJiang/DailyPaper) — MIT。借鉴“用正负种子调用 Semantic Scholar Recommendations”的思路；未复制其 DeepSeek 摘要、ServerChan 推送或已读文件逻辑。
- [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) — MIT。借鉴统一论文模型、平台连接器和免费来源优先的架构。
- [Eclipse-Cj/paper-distill-mcp](https://github.com/Eclipse-Cj/paper-distill-mcp) — AGPL-3.0。仅参考配置向导和能力说明，没有复制代码。
- [Crossref REST API documentation](https://github.com/CrossRef/rest-api-doc) — 使用官方期刊、ISSN、日期和作品检索接口。
- [OpenAlex Authentication](https://developers.openalex.org/api-reference/authentication) — OpenAlex当前要求免费API key并提供每日免费额度。
- [Semantic Scholar API](https://www.semanticscholar.org/product/api) — 使用Academic Graph与Recommendations官方接口。
- [arXiv API](https://info.arxiv.org/help/api/index.html) — 使用官方Atom API。

这些项目和API各自受其许可证及服务条款约束。MIT许可证只覆盖本仓库代码，不改变第三方服务条款。
