from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from .adapters import ADAPTERS
from .adapters.base import AdapterContext
from .config import ConfigError, load_config, safe_path
from .http import HttpClient
from .models import PaperCandidate, SourceResult, clean_text
from .render import render_brief
from .state import append_ledger, atomic_json_write, load_ledger, read_json


SOURCE_QUALITY = {
    "openalex": 0.9,
    "crossref": 0.85,
    "semantic_scholar": 0.85,
    "semantic_scholar_recommendations": 0.8,
    "arxiv": 0.75,
    "feed": 0.65,
    "industry": 0.6,
}


def parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def focus_for(config: dict[str, Any], day: dt.date) -> str:
    key = day.strftime("%A").lower()
    configured = str(config.get("rotation", {}).get(key, ""))
    track_ids = {str(track["id"]) for track in config["tracks"]}
    return configured if configured in track_ids else str(config["tracks"][day.weekday() % len(config["tracks"])]["id"])


def queries_for(config: dict[str, Any], focus: str) -> list[str]:
    tracks = config["tracks"]
    if focus in {"cross_cutting", "weekly_balance", "industry_evidence"}:
        queries = [query for track in tracks for query in track.get("queries", [])[:1]]
    else:
        chosen = next((track for track in tracks if track["id"] == focus), tracks[0])
        queries = list(chosen.get("queries", []))
    return [clean_text(value) for value in queries if clean_text(value)]


def keyword_hits(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [str(keyword) for keyword in keywords if str(keyword).strip() and str(keyword).lower() in lowered]


def target_venue_match(candidate: PaperCandidate, config: dict[str, Any]) -> bool:
    venue = candidate.venue.lower()
    issn = {value.upper() for value in candidate.issn}
    for target in config.get("target_sources", []):
        if target.get("issn") and str(target["issn"]).upper() in issn:
            return True
        if target.get("name") and str(target["name"]).lower() in venue:
            return True
        if target.get("openalex_id") and str(target["openalex_id"]).rsplit("/", 1)[-1].lower() == candidate.openalex_id.lower():
            return True
    return False


def annotate_and_filter(candidate: PaperCandidate, config: dict[str, Any]) -> bool:
    text = candidate.searchable_text
    if keyword_hits(text, config.get("exclusion_keywords", [])):
        return False
    candidate.track_hits = {
        str(track["id"]): keyword_hits(text, track.get("keywords", []))
        for track in config["tracks"]
    }
    candidate.track_hits = {key: value for key, value in candidate.track_hits.items() if value}
    context_hits = keyword_hits(text, config.get("context_keywords", []))
    venue_hit = target_venue_match(candidate, config)
    if config["selection"].get("venue_mode") == "only" and config.get("target_sources") and not venue_hit:
        return False
    if candidate.source_type == "industry":
        return bool(context_hits or candidate.track_hits)
    return bool((context_hits and candidate.track_hits) or venue_hit)


def merge_duplicates(candidates: Iterable[PaperCandidate]) -> list[PaperCandidate]:
    merged: dict[str, PaperCandidate] = {}
    for item in candidates:
        key = item.canonical_id
        current = merged.get(key)
        if current is None:
            merged[key] = item
            continue
        current.sources = sorted(set(current.sources + item.sources))
        if len(item.abstract) > len(current.abstract):
            current.abstract = item.abstract
            current.evidence_level = item.evidence_level
        for field in ("doi", "url", "full_text_url", "arxiv_id", "semantic_scholar_id", "openalex_id", "venue", "published_date"):
            if not getattr(current, field) and getattr(item, field):
                setattr(current, field, getattr(item, field))
        current.authors = current.authors or item.authors
        current.issn = sorted(set(current.issn + item.issn))
        current.citation_count = max(current.citation_count, item.citation_count)
    return list(merged.values())


def score_candidate(candidate: PaperCandidate, config: dict[str, Any], focus: str, today: dt.date, ledger: dict[str, str]) -> None:
    weights = config["score_weights"]
    all_hits = sum((values for values in candidate.track_hits.values()), [])
    context_hits = keyword_hits(candidate.searchable_text, config.get("context_keywords", []))
    relevance_ratio = min(1.0, (len(set(all_hits)) + len(set(context_hits))) / 4)
    if target_venue_match(candidate, config):
        relevance_ratio = min(1.0, relevance_ratio + 0.2)
    source_key = candidate.source if candidate.source in SOURCE_QUALITY else candidate.source_type
    quality_ratio = SOURCE_QUALITY.get(source_key, 0.55)
    if len(candidate.sources) > 1:
        quality_ratio = min(1.0, quality_ratio + 0.1)
    published = parse_date(candidate.published_date)
    if published:
        age = max(0, (today - published).days)
        recency_ratio = max(0.0, 1 - age / max(1, int(config["windows"]["influence_days"])))
    else:
        recency_ratio = 0.25
    impact_ratio = min(1.0, math.log1p(max(0, candidate.citation_count)) / math.log(101))
    previous = ledger.get(candidate.canonical_id)
    current_version = candidate.published_date or str(candidate.year or "")
    candidate.previously_seen = previous == current_version
    novelty_ratio = 0.0 if candidate.previously_seen else 1.0
    candidate.matched_track = focus if focus in candidate.track_hits else max(candidate.track_hits, key=lambda key: len(candidate.track_hits[key]), default="")
    breakdown = {
        "relevance": weights["relevance"] * relevance_ratio,
        "source_quality": weights["source_quality"] * quality_ratio,
        "recency": weights["recency"] * recency_ratio,
        "impact": weights["impact"] * impact_ratio,
        "novelty": weights["novelty"] * novelty_ratio,
    }
    candidate.score_breakdown = {key: round(value, 2) for key, value in breakdown.items()}
    candidate.score = round(sum(breakdown.values()), 2)


def choose(candidates: list[PaperCandidate], config: dict[str, Any], focus: str, *, include_seen: bool = False) -> list[PaperCandidate]:
    minimum = float(config["selection"]["minimum_score"])
    eligible = sorted(
        (item for item in candidates if item.score >= minimum and (include_seen or not item.previously_seen)),
        key=lambda item: (-item.score, item.title.lower()),
    )
    limit = int(config["selection"]["daily_limit"])
    focus_quota = min(limit, int(config["selection"].get("focus_quota", limit)))
    focus_items = [item for item in eligible if item.matched_track == focus][:focus_quota]
    selected = list(focus_items)
    for item in eligible:
        if item not in selected:
            selected.append(item)
        if len(selected) >= limit:
            break
    return selected[:limit]


def run_daily(
    config_path: str | Path,
    *,
    date: str | None = None,
    force: bool = False,
    adapters: tuple[type, ...] = ADAPTERS,
    http: HttpClient | None = None,
) -> dict[str, Any]:
    config, resolved_config = load_config(config_path)
    root = resolved_config.parent
    timezone = ZoneInfo(config["project"].get("timezone", "Asia/Shanghai"))
    today = dt.date.fromisoformat(date) if date else dt.datetime.now(timezone).date()
    runs_dir = safe_path(root, config["paths"]["runs_dir"])
    run_path = runs_dir / f"{today.isoformat()}-run.json"
    existing = read_json(run_path)
    if existing.get("brief_written") and not force:
        return {**existing, "idempotent_skip": True}
    focus = focus_for(config, today)
    queries = queries_for(config, focus)
    since = today - dt.timedelta(days=int(config["windows"]["new_days"]))
    network = config["network"]
    client = http or HttpClient(int(network["timeout_seconds"]), int(network["max_retries"]), str(network["user_agent"]))
    results: list[SourceResult] = []
    for adapter_type in adapters:
        adapter = adapter_type()
        try:
            result = adapter.collect(AdapterContext(config, today, since, focus, queries, client))
        except Exception as exc:  # Provider isolation is deliberate; state keeps the exact class and message.
            result = SourceResult(getattr(adapter, "id", adapter_type.__name__), "failed", detail=f"{type(exc).__name__}: {exc}")
        results.append(result)
    merged = merge_duplicates(item for result in results for item in result.items)
    filtered = [item for item in merged if annotate_and_filter(item, config)]
    ledger_path = safe_path(root, config["paths"]["ledger_file"], file_path=True)
    ledger = load_ledger(ledger_path)
    for item in filtered:
        score_candidate(item, config, focus, today, ledger)
    selected = choose(filtered, config, focus, include_seen=force)
    runs_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = runs_dir / f"{today.isoformat()}-candidates.json"
    atomic_json_write(
        candidates_path,
        {
            "date": today.isoformat(),
            "focus_track": focus,
            "queries": queries,
            "source_status": [result.to_status_dict() for result in results],
            "items": [item.to_dict() for item in selected],
            "candidate_count": len(merged),
            "eligible_count": len(filtered),
        },
    )
    brief_dir = safe_path(root, config["paths"]["briefs_dir"]) / today.strftime("%Y") / today.strftime("%m")
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brief_dir / f"{today.isoformat()} {config['project']['brief_title']}.md"
    focus_name = next((track["name"] for track in config["tracks"] if track["id"] == focus), focus)
    brief_path.write_text(
        render_brief(
            date=today.isoformat(),
            title=config["project"]["brief_title"],
            focus_name=focus_name,
            selected=selected,
            source_results=results,
            deep_threshold=float(config["selection"]["deep_analysis_threshold"]),
            report=config.get("report", {}),
        ),
        encoding="utf-8",
    )
    append_ledger(ledger_path, selected, today.isoformat())
    state = {
        "date": today.isoformat(),
        "brief_written": True,
        "brief_path": brief_path.relative_to(root).as_posix(),
        "candidates_path": candidates_path.relative_to(root).as_posix(),
        "selected_count": len(selected),
        "candidate_count": len(merged),
        "focus_track": focus,
        "source_status": [result.to_status_dict() for result in results],
        "coverage": "partial" if any(result.status in {"failed", "limited", "partial", "misconfigured"} for result in results) else "complete",
        "delivery_attempted": False,
        "delivery_sent": False,
    }
    atomic_json_write(run_path, state)
    return state
