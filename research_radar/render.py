from __future__ import annotations

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
) -> str:
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
        "## 来源覆盖",
        "",
        "| 来源 | 状态 | 候选数 | 说明 |",
        "| --- | --- | ---: | --- |",
    ]
    for result in source_results:
        lines.append(f"| {_safe(result.source)} | {result.status} | {len(result.items)} | {_safe(result.detail or '-')} |")
    lines.extend(["", "## 今日入选", ""])
    if not selected:
        lines.extend(["**今日无高置信新增。**", "", "这不等同于没有相关研究，请结合上面的来源状态判断覆盖范围。"])
        return "\n".join(lines).rstrip() + "\n"
    for index, item in enumerate(selected, start=1):
        authors = "、".join(item.authors[:5]) or "未提供"
        lines.extend(
            [
                f"### {index}. {item.title}",
                "",
                f"- **类型：** {item.source_type} / {item.evidence_level}",
                f"- **作者：** {authors}",
                f"- **日期：** {item.published_date or item.year or '未提供'}",
                f"- **期刊/渠道：** {item.venue or '未提供'}",
                f"- **匹配方向：** {item.matched_track or '跨方向'}",
                f"- **评分：** {item.score:.1f}",
                f"- **来源：** {', '.join(item.sources)}",
                f"- **DOI：** {item.doi or '未提供'}",
                f"- **原始链接：** {item.url or item.full_text_url or '未提供'}",
                "",
                f"**摘要级信息：** {item.abstract[:900] if item.abstract else '来源未提供摘要，需打开原始链接核验。'}",
                "",
            ]
        )
    first = selected[0]
    lines.extend(["## 首篇分析边界", ""])
    if first.score >= deep_threshold:
        lines.append("首篇达到深入分析阈值，但当前自动输出仍仅使用可见摘要和元数据；只有实际读取开放全文后才能标记为“全文精读”。")
    else:
        lines.append("首篇未达到深入分析阈值，本次只保留摘要级事实，不扩展方法或结论。")
    return "\n".join(lines).rstrip() + "\n"
