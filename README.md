# Research Radar

一个面向 Codex + Obsidian 的可配置每日研究雷达。它会从公开学术 API、RSS/Atom 和官方网页收集候选内容，统一去重和评分，每天生成一份带来源状态的 Markdown 日报。

它不是“自动证明今天没有论文”的搜索器。任何接口失败、限流或未配置都会明确标成部分覆盖。

## 五分钟开始

要求 Python 3.11 或更高版本。克隆仓库后，在仓库根目录执行：

```bash
python3 -m research_radar init --preset ci3
python3 -m research_radar doctor
python3 -m research_radar run
```

生成内容默认位于：

```text
10-daily-briefs/YYYY/MM/YYYY-MM-DD CI3研究简报.md
90-system/runs/YYYY-MM-DD-run.json
90-system/runs/YYYY-MM-DD-candidates.json
90-system/index/recommendation-ledger.jsonl
```

如果不使用 CI3 模板：

```bash
python3 -m research_radar init --preset blank --interactive
```

然后用任意文本编辑器打开 `research-radar.config.json`。完整字段说明见 [配置手册](docs/CONFIGURATION.md)。

## 开箱可用与可选增强

默认不需要密钥：

- Crossref
- arXiv
- RSS/Atom（添加订阅地址后启用）
- 大学、政府、行业机构官方网页
- Semantic Scholar Search（无密钥共享限流）

可选增强：

```bash
export S2_API_KEY="你的密钥"
export OPENALEX_API_KEY="你的密钥"
```

OpenAlex 必须先在配置中设为 `"enabled": true`。密钥只从环境变量读取，不写进配置。

## 你可以修改什么

- 每个研究方向的关键词和检索式。
- 关注作者、ORCID和推荐种子论文。
- 目标期刊名称、ISSN和OpenAlex Source ID。
- 期刊策略：`prefer` 优先或 `only` 仅限目标期刊。
- 任意RSS/Atom订阅和官方网页。
- 时间窗口、每天数量、阈值、权重和保存目录。
- 本地、终端或可选飞书交付。

修改后先运行：

```bash
python3 -m research_radar validate
python3 -m research_radar doctor
```

## 在 Codex 与 Obsidian 中使用

仓库包含两个 Codex Skills：

- `research-radar`：初始化、配置、生成日报和安装本地每日任务。
- `paper-analyze`：对当日首篇内容做证据受限的摘要级或全文分析。

把仓库作为 Obsidian vault 打开，或把输出目录改为现有 vault 内的相对目录。对 Codex 说：

> 初始化研究雷达，然后每天上午 8:30 生成一份研究日报。

每日自动化应在本机运行，不应把个人配置、日报或密钥提交回公共仓库。

## 交付

日报生成后已完成本地交付。也可以：

```bash
python3 -m research_radar deliver --date 2026-07-21 --channel stdout
```

飞书是可选功能，需要安装并登录 `lark-cli`，且显式提供收件人：

```bash
export FEISHU_USER_ID="运行时收件人ID"
python3 -m research_radar deliver --date 2026-07-21 --channel feishu
```

系统只尝试一次。失败不会删除本地日报，也不会自动无限重发。

## 边界

- 不抓取 Google Scholar，不包含 Sci-Hub。
- 不绕过登录、付费墙或机构授权。
- 不自动声称读过全文；有 PDF 链接也只表示链接存在。
- Scopus、Web of Science、IEEE Xplore 需要个人或机构授权，因此不冒充零配置来源。

适配器原理、来源限制和上游项目见 [ADAPTERS](docs/ADAPTERS.md) 与 [UPSTREAM](docs/UPSTREAM.md)。

分享材料位于 [presentation/Research-Radar-分享版_v0.1.0.pptx](presentation/Research-Radar-分享版_v0.1.0.pptx)，配套讲稿见 [presentation/六页分享讲稿.md](presentation/六页分享讲稿.md)。

## License

[MIT](LICENSE) © 2026 JBMovingCastle
