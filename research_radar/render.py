from __future__ import annotations

from typing import Any

from .config import DEFAULT_REPORT_ITEM_FIELDS
from .models import PaperCandidate, SourceResult


def _safe(value: str) -> str:
    return value.replace("|", "\\|").strip()


def render_brief(
    *,
    date: str,
    title: str,
    focus_name: str,
    selected: list[PaperCandidate],
    source_results: list[SourceResult],
    deep_threshold: float,
    report: dict[str, Any] | None = None,
) -> str:
    report = report or {}
    item_fields = report.get("item_fields", list(DEFAULT_REPORT_ITEM_FIELDS))
    abstract_limit = int(report.get("abstract_limit", 900))
    requirements = report.get("writing_requirements", [])
    style = report.get("style", {})
    intro = style.get("intro", "")
    requirements_heading = style.get("requirements_heading", "撰写要求")
    selection_heading = style.get("selection_heading", "今日入选")
    analysis_heading = style.get("analysis_heading", "首篇分析边界")
    partial = any(result.status in {"failed", "limited", "partial", "misconfigured"} for result in source_results)
    lines = [
        "---",
        f'date: "{date}"',
        'authorship: "ai-generated"',
        'status: "draft"',
        f'source_status: "{"partial" if partial else "complete"}"',
        "---",
        "",
        f"# {date} {title}",
        "",
        f"**今日方向：** {focus_name}",
        "",
        "> 本简报由公开元数据与配置规则自动生成。摘要级内容不代表已阅读全文；来源失败只表示覆盖不完整。",
        "",
        intro,
        "" if intro else None,
        "## 来源覆盖",
        "",
        "| 来源 | 状态 | 候选数 | 说明 |",
        "| --- | --- | ---: | --- |",
    ]
    lines = [line for line in lines if line is not None]
    for result in source_results:
        lines.append(f"| {_safe(result.source)} | {result.status} | {len(result.items)} | {_safe(result.detail or '-')} |")
    if requirements:
        lines.extend(["", f"## {requirements_heading}", ""])
        lines.extend(f"- {_safe(requirement)}" for requirement in requirements)
    lines.extend(["", f"## {selection_heading}", ""])
    if not selected:
        lines.extend(["**今日无高置信新增。**", "", "这不等同于没有相关研究，请结合上面的来源状态判断覆盖范围。"])
        return "\n".join(lines).rstrip() + "\n"
    for index, item in enumerate(selected, start=1):
        values = {
            "evidence": ("类型", f"{item.source_type} / {item.evidence_level}"),
            "authors": ("作者", "、".join(item.authors[:5]) or "未提供"),
            "published_date": ("日期", item.published_date or str(item.year or "未提供")),
            "venue": ("期刊/渠道", item.venue or "未提供"),
            "matched_track": ("匹配方向", item.matched_track or "跨方向"),
            "score": ("评分", f"{item.score:.1f}"),
            "sources": ("来源", ", ".join(item.sources)),
            "doi": ("DOI", item.doi or "未提供"),
            "url": ("原始链接", item.url or item.full_text_url or "未提供"),
            "full_text_url": ("开放全文链接", item.full_text_url or "未提供"),
        }
        lines.extend([f"### {index}. {item.title}", ""])
        for field in item_fields:
            if field == "abstract":
                if abstract_limit:
                    abstract = item.abstract[:abstract_limit]
                    lines.extend(["", f"**摘要级信息：** {abstract or '来源未提供摘要，需打开原始链接核验。'}"])
            else:
                label, value = values[field]
                lines.append(f"- **{label}：** {value}")
        lines.append("")
    first = selected[0]
    lines.extend([f"## {analysis_heading}", ""])
    if first.score >= deep_threshold:
        lines.append("首篇达到深入分析阈值，但当前自动输出仍仅使用可见摘要和元数据；只有实际读取开放全文后才能标记为“全文精读”。")
    else:
        lines.append("首篇未达到深入分析阈值，本次只保留摘要级事实，不扩展方法或结论。")
    return "\n".join(lines).rstrip() + "\n"
