# 配置手册

配置文件是仓库根目录的 `research-radar.config.json`。JSON 不支持注释；修改后用 `python3 -m research_radar validate` 检查。

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
