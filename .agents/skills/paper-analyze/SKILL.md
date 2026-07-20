---
name: paper-analyze
description: Analyze the top paper selected by Research Radar and write evidence-bounded findings into the same daily brief. Use this whenever the user asks to deep-read, analyze, interpret, or explain a selected radar paper, its method, findings, limitations, or relevance to a research track.
compatibility: Requires an existing Research Radar candidates file and daily brief. Full-text analysis additionally requires lawful access to the actual paper text.
---

# Paper Analyze

Analyze at most the first selected paper from an existing Research Radar run. Keep the analysis inside that day's brief so the recommendation ledger and evidence trail remain aligned.

## Inputs

Locate the repository and read:

1. `90-system/runs/YYYY-MM-DD-candidates.json`
2. the `brief_path` from `90-system/runs/YYYY-MM-DD-run.json`
3. `.agents/skills/research-radar/references/evidence-and-failure-rules.md`

If the candidates file has no item, stop and report that there is no selected paper to analyze. Do not substitute an unselected paper.

## Choose evidence depth

- If only metadata exists, describe bibliographic relevance and missing evidence.
- If an abstract exists, label the section `摘要级分析`.
- If a lawful open full text can be retrieved, actually read it before labeling the section `全文精读`.
- If retrieval fails, fall back once to abstract-level analysis and state the limitation.

An accessible link is not proof of reading. Do not bypass login or paywalls.

## Analysis structure

Append or replace a single section in the daily brief:

```markdown
## 首篇分析

### 证据等级

### 研究问题与方法

### 来源明确报告的结果

### 与当前研究方向的关系

### 局限与待核验事项

### 建议下一步
```

Separate source-reported findings from your inference. Keep DOI, original URL, title, and evidence level unchanged.

## Completion

Report the updated brief path, evidence depth, and any unavailable source or full-text limitation. Do not create a separate paper note unless the user explicitly requests one.
