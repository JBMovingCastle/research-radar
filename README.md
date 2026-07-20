# Research Radar

一个面向 Codex + Obsidian 的可配置每日研究雷达。它把多个公开学术渠道、RSS/Atom 与机构网页的候选内容统一整理为一份可追溯的 Markdown **日报**，而不是把“搜到几条链接”当成研究判断。

它的默认模板服务于 CI3（建筑工业化、施工信息学、模块化建造、人机协作等）方向，但研究方向、关键词、期刊、作者、订阅源、保存位置和交付方式都可由使用者在本地配置。

> 事实边界：v0.1.0 生成的是“每日研究简报”，不是自动周报。它不会声称已经阅读全文，也不会把接口失败、限流或未配置解释为“今天没有论文”。

## 它具体做什么

- 按研究方向、关键词和日期窗口从多个来源收集论文或网页级线索。
- 用 DOI 优先、平台 ID 其次、标题与年份最后的规则去重。
- 用研究语境、研究方向命中、目标期刊、来源质量、时效、引用数和历史记录评分。
- 每日最多选取 5 项，保留标题、作者、日期、期刊/渠道、DOI、原始链接、摘要级信息和评分。
- 为每一个来源记录 `success`、`limited`、`failed`、`misconfigured`、`skipped` 等状态，避免“静默失败”。
- 用本地推荐账本跨日去重；同一天重复运行会跳过，不重复抓取或写入日报。
- 先写本地 Markdown 日报；可选输出到终端或发送到飞书。发送失败不删除本地日报，也不会无限重发。

## 一份日报如何生成

```text
配置研究方向与来源
        ↓
按当天轮换方向生成检索式
        ↓
并行采集公开 API、RSS/Atom、官方网页
        ↓
字段标准化 → DOI/平台ID/标题去重 → 研究语境过滤
        ↓
评分与每日限额选择（最多 5 项）
        ↓
生成 Markdown 日报 + 候选快照 + 来源状态 + 跨日账本
        ↓
本地保存；按需 stdout 或飞书交付
```

生成的日报包含：

- 当天的研究方向与 `source_status: complete/partial`。
- 每个渠道的状态、候选数和失败/限流原因。
- 入选内容的题目、作者、发布日期、期刊/渠道、来源、DOI、原始链接、评分和最多 900 字的可见摘要。
- 首篇的分析边界：即使分数达到深入分析阈值，自动输出仍只基于元数据和可见摘要；只有实际读取开放全文后，才应标记为全文精读。

默认输出位置：

```text
10-daily-briefs/YYYY/MM/YYYY-MM-DD CI3研究简报.md
90-system/runs/YYYY-MM-DD-run.json
90-system/runs/YYYY-MM-DD-candidates.json
90-system/index/recommendation-ledger.jsonl
```

`run.json` 是本次运行和交付状态，`candidates.json` 是已入选候选的结构化快照，`recommendation-ledger.jsonl` 用于跨日去重。它们都应保留在本地，不要提交到公共仓库。

## 可以检索哪些论文与信息来源

| 来源 | 默认状态 | 可检索内容 | 主要限制 |
| --- | --- | --- | --- |
| Crossref | 开启、无密钥 | 关键词、日期、期刊、ISSN、DOI、作者姓名/ORCID | 元数据摘要不完整；不保证全文开放 |
| arXiv | 开启、无密钥 | 关键词、分类、近期预印本、摘要与 PDF 链接 | 对建筑管理等传统期刊覆盖有限 |
| Semantic Scholar Search | 开启、可无密钥 | 跨学科论文、引用数、摘要、开放链接 | 无密钥为共享限流，可能返回 429 |
| Semantic Scholar Recommendations | 开启、可无密钥 | 基于正向/负向种子论文的推荐 | 没有正向种子时自动跳过 |
| OpenAlex | 默认关闭、需要 API key | 关键词、作者 OpenAlex ID、期刊/Source ID、开放获取链接 | 需要免费 API key，受额度限制 |
| RSS/Atom | 添加后启用、无密钥 | 期刊、出版社、实验室或机构订阅 | 取决于订阅源本身的质量与更新频率 |
| Official Web Page | CI3 模板已配置、无密钥 | 大学、政府和行业机构网页中的链接级线索 | 是网页级证据，不冒充论文全文或摘要 |

CI3 模板默认关注四本期刊：`Automation in Construction`、`Advanced Engineering Informatics`、`Journal of Construction Engineering and Management` 与 `Journal of Management in Engineering`。它们在 `prefer` 模式下获得加权；切换到 `only` 后，最终结果只保留匹配期刊名、ISSN 或 OpenAlex Source ID 的内容。

你也可以自行添加任何合法的 ISSN、RSS/Atom 地址、官方网页、关注作者 ORCID/OpenAlex ID，以及 Semantic Scholar 正负种子论文。详细字段与示例见[配置手册](docs/CONFIGURATION.md)，各来源的适配器行为见[适配器说明](docs/ADAPTERS.md)。

## 五分钟开始

要求 Python 3.11 或更高版本。克隆仓库后，在仓库根目录执行：

```bash
python3 -m research_radar init --preset ci3
python3 -m research_radar doctor
python3 -m research_radar run
```

如果不使用 CI3 模板：

```bash
python3 -m research_radar init --preset blank --interactive
```

然后用任意文本编辑器打开 `research-radar.config.json`。首次运行不需要 API key：Crossref、arXiv 和配置的 RSS/官方网页可以组成真实采集基线。OpenAlex 和更稳定的 Semantic Scholar 使用体验可按需补充密钥。

## 如何按自己的研究方向配置

你可以在 `research-radar.config.json` 中修改：

- 实验室名称、日报标题、语言和时区。
- 每个研究方向的关键词与检索式，以及排除词。
- 关注作者、ORCID、OpenAlex Author ID 和正/负种子论文。
- 目标期刊名称、ISSN、OpenAlex Source ID，以及 `prefer` / `only` 期刊策略。
- RSS/Atom、大学、政府和行业机构网页渠道。
- 每日数量、评分权重、时间窗口、深入分析阈值和保存目录。

修改后先运行：

```bash
python3 -m research_radar validate
python3 -m research_radar doctor
```

配置只接受仓库内相对路径；密钥只从环境变量读取，不会写入配置或 Git。

## 在 Codex、Obsidian 与飞书中使用

仓库包含两个 Codex Skills：

- `research-radar`：初始化、修改配置、生成日报和安装本地每日任务。
- `paper-analyze`：对当日首篇内容进行证据受限的摘要级或全文分析。

可以把仓库作为 Obsidian vault 打开，或把输出目录改为现有 vault 内的相对目录。每日自动化应在同学自己的电脑上运行，不应把个人配置、日报、账本或密钥提交回公共 GitHub。

日报默认已完成本地交付；也可以：

```bash
python3 -m research_radar deliver --date 2026-07-21 --channel stdout
```

飞书是可选增强，需要安装并登录 `lark-cli`，并在运行时显式提供收件人：

```bash
export FEISHU_USER_ID="运行时收件人ID"
python3 -m research_radar deliver --date 2026-07-21 --channel feishu
```

## 不做什么

- 不抓取 Google Scholar，不包含 Sci-Hub。
- 不绕过登录、付费墙或机构授权。
- 不自动下载付费全文，也不把 PDF 链接等同于读过全文。
- 不把 Scopus、Web of Science、IEEE Xplore 伪装成零配置来源；它们需要个人或机构授权。
- 不承诺“检索所有论文”。第三方接口异常会明确记录为部分覆盖。

如果你需要周报，可基于每天的 Markdown 日报再做人工汇总或另行实现周度汇总规则；当前版本未提供自动周报命令。

[MIT](LICENSE) © 2026 JBMovingCastle
