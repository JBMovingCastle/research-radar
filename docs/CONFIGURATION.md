# 配置手册

配置文件是仓库根目录的 `research-radar.config.json`。JSON 不支持注释；修改后用 `python3 -m research_radar validate` 检查。

个人使用时应修改初始化生成的 `research-radar.config.json`，不要直接修改 `configs/ci3.json` 或 `configs/blank.json`。后两者是内置模板，供首次初始化和版本发布使用。

## 从需求找到配置字段

| 想修改的内容 | 配置字段 |
| --- | --- |
| 项目名称、日报标题 | `project.name`、`project.brief_title` |
| 总体研究语境 | `context_keywords` |
| 研究方向 | `tracks` |
| 方向关键词 | `tracks[].keywords` |
| 实际检索式 | `tracks[].queries` |
| 每日推荐数量 | `selection.daily_limit` |
| 入选门槛 | `selection.minimum_score` |
| 重点期刊 | `target_sources` |
| 只看目标期刊 | `selection.venue_mode: "only"` |
| 优先目标期刊但保留其他结果 | `selection.venue_mode: "prefer"` |
| 关注作者 | `authors` |
| RSS/Atom 订阅 | `sources.feeds` |
| 机构网页 | `sources.web_pages` |
| 摘要长度、日报字段和章节写法 | `report` |
| 日报、运行记录和账本位置 | `paths` |

最有效的配置需求通常包含四件事：研究什么、每天需要几条、重点关注或排除什么、日报给谁看。只说“优化一下关键词”通常不足以形成稳定检索式。

## 每日数量与报告写法

默认每天最多选取 5 项；`selection.daily_limit` 可由使用者设置为 1 到 20。报告的展示顺序、摘要长度、章节标题、开场说明和写作要求可直接通过 `report` 修改：

```json
{
  "selection": {"daily_limit": 8},
  "report": {
    "writing_requirements": [
      "优先面向项目组决策，保留事实与来源。",
      "不把摘要级信息扩写为已验证结论。"
    ],
    "item_fields": ["authors", "venue", "doi", "url", "abstract"],
    "abstract_limit": 500,
    "style": {
      "intro": "面向项目例会的速览，重点保留可行动线索。",
      "requirements_heading": "编辑要求",
      "selection_heading": "本期重点",
      "analysis_heading": "阅读边界"
    }
  }
}
```

- `writing_requirements`：会显示在日报的“撰写要求”区，供使用者直接编辑并保留在输出中。
- `item_fields`：控制每项内容的字段和顺序；可用值为 `evidence`、`authors`、`published_date`、`venue`、`matched_track`、`score`、`sources`、`doi`、`url`、`full_text_url`、`abstract`。
- `abstract_limit`：每项可见摘要最多保留 0 到 1500 个字符；设为 `0` 时不输出摘要正文。
- `style`：控制开场说明和三个章节标题；不设置时使用默认中文标题。

这部分只能控制模板和表达要求，不会让系统自动获得付费全文或把摘要级内容升级为全文结论。若把每日数量调大，也应同时考虑阅读负担和飞书消息长度。

## 研究方向与关键词

```json
{
  "context_keywords": ["modular construction", "建筑工业化"],
  "tracks": [
    {
      "id": "robotics",
      "name": "建筑机器人",
      "keywords": ["human-robot collaboration", "建筑机器人"],
      "queries": ["modular construction human robot collaboration"]
    }
  ]
}
```

候选内容需要命中研究方向，同时命中研究语境；目标期刊文章可作为例外进入评分。这能减少“只含AI、机器人或区块链，但与本组研究无关”的噪声。

例如增加“工程教育与生成式 AI”方向，可在 `tracks` 数组中加入：

```json
{
  "id": "engineering_education_ai",
  "name": "工程教育与生成式 AI",
  "keywords": [
    "engineering education",
    "generative AI",
    "large language model",
    "AI-assisted learning",
    "工程教育",
    "生成式人工智能"
  ],
  "queries": [
    "engineering education generative AI",
    "engineering education large language model",
    "AI-assisted learning engineering education"
  ]
}
```

不要只使用 `AI`、`robot`、`blockchain` 等过宽的单词。应在 `context_keywords` 和 `queries` 中同时说明所属学科、应用对象或研究场景，否则噪声会明显增加。

## 期刊和渠道

```json
{
  "selection": {"venue_mode": "prefer"},
  "target_sources": [
    {
      "name": "Automation in Construction",
      "issn": "0926-5805",
      "openalex_id": "S126507392"
    }
  ]
}
```

- `prefer`：目标期刊获得加权，但其他高相关内容仍可入选。
- `only`：最终结果必须匹配期刊名、ISSN或OpenAlex Source ID。

Crossref 使用 ISSN 端点真实检索该期刊；OpenAlex 在配置 ID 后使用来源过滤。

## 作者与种子论文

```json
{
  "authors": [
    {"name": "Example Author", "orcid": "0000-0000-0000-0000", "openalex_id": "A123456"}
  ],
  "seed_papers": {
    "positive": ["DOI:10.1234/example", "CorpusId:123456"],
    "negative": []
  }
}
```

Crossref会使用作者姓名和ORCID检索，OpenAlex会使用已配置的Author ID。种子论文由 Semantic Scholar Recommendations 使用；没有正向种子时该适配器显示 `skipped`，不会发出空请求。

## RSS/Atom

```json
{
  "sources": {
    "feeds": [
      {
        "name": "Example Journal Feed",
        "url": "https://example.org/feed.xml",
        "max_items": 20
      }
    ]
  }
}
```

## 官方网页

```json
{
  "sources": {
    "web_pages": [
      {
        "name": "Government Innovation",
        "url": "https://example.gov/innovation/",
        "authority": "government",
        "max_items": 10
      }
    ]
  }
}
```

网页适配器只把页面中的链接作为网页级线索，不把链接标题解释为论文摘要。

## 保存位置

```json
{
  "paths": {
    "briefs_dir": "10-daily-briefs",
    "topics_dir": "20-topics",
    "runs_dir": "90-system/runs",
    "ledger_file": "90-system/index/recommendation-ledger.jsonl"
  }
}
```

所有路径必须是仓库内相对路径，不能使用 `/Users/...`、`C:\\...` 或 `..`。

## 密钥

```bash
export S2_API_KEY="..."
export OPENALEX_API_KEY="..."
```

配置中只保存环境变量名称，例如 `"api_key_env": "OPENALEX_API_KEY"`，不得保存真实密钥。

## 修改时的安全规则

- JSON 必须使用英文双引号，不支持注释或尾随逗号。
- 不要把 API Key、飞书收件人 ID 或其他个人身份信息写入配置。
- `paths` 只接受项目内部的相对路径，不接受绝对路径或 `..`。
- `selection.daily_limit` 支持 1 到 20；提高数量也会增加阅读负担和消息长度。
- `selection.venue_mode: "only"` 可能导致结果明显减少，通常先使用 `"prefer"`。
- 修改后先执行 `python3 -m research_radar validate` 和 `python3 -m research_radar doctor`，再决定是否运行检索。

如果使用 Codex，可以直接让它先读取本手册、只修改相关字段，并明确要求“修改后不要运行检索”。完整对话示例见[快速开始](QUICKSTART.md#方式一直接让-codex-帮你操作)。
