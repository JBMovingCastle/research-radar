# 配置手册

配置文件是仓库根目录的 `research-radar.config.json`。JSON 不支持注释；修改后用 `python3 -m research_radar validate` 检查。

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
