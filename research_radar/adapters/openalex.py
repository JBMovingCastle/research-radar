from __future__ import annotations

import os
import urllib.parse
from typing import Any

from ..http import HttpFailure
from ..models import PaperCandidate, SourceResult, clean_text
from .base import AdapterContext


def _abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        words.extend((int(position), word) for position in positions)
    return " ".join(word for _, word in sorted(words))


class OpenAlexAdapter:
    id = "openalex"
    base_url = "https://api.openalex.org/works"

    @staticmethod
    def _candidate(item: dict[str, Any]) -> PaperCandidate:
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        ids = item.get("ids") or {}
        best_oa = item.get("best_oa_location") or {}
        published = clean_text(item.get("publication_date"))
        return PaperCandidate(
            source="openalex",
            title=clean_text(item.get("display_name")),
            authors=[clean_text(entry.get("author", {}).get("display_name")) for entry in item.get("authorships", [])],
            abstract=_abstract(item.get("abstract_inverted_index")),
            published_date=published,
            year=int(item.get("publication_year")) if str(item.get("publication_year", "")).isdigit() else None,
            doi=clean_text(ids.get("doi")),
            venue=clean_text(source.get("display_name")),
            issn=[clean_text(value) for value in source.get("issn", [])],
            url=clean_text(primary.get("landing_page_url") or item.get("doi") or item.get("id")),
            full_text_url=clean_text(best_oa.get("pdf_url")),
            openalex_id=clean_text(item.get("id")).rsplit("/", 1)[-1],
            citation_count=int(item.get("cited_by_count", 0) or 0),
            evidence_level="abstract" if item.get("abstract_inverted_index") else "metadata",
        )

    def collect(self, context: AdapterContext) -> SourceResult:
        settings = context.config["sources"].get(self.id, {})
        if not settings.get("enabled", False):
            return SourceResult(self.id, "disabled", detail="Disabled in config.")
        env_name = settings.get("api_key_env", "OPENALEX_API_KEY")
        key = os.getenv(env_name, "")
        if not key:
            return SourceResult(self.id, "misconfigured", detail=f"Missing required {env_name}.")
        before = context.http.request_count
        items: list[PaperCandidate] = []
        targets = context.config.get("target_sources", [])
        venue_mode = context.config["selection"].get("venue_mode", "prefer")
        source_ids = [str(target.get("openalex_id", "")).rsplit("/", 1)[-1] for target in targets if target.get("openalex_id")]
        requests_to_make: list[tuple[str, list[str]]] = []
        for query in context.queries[:3]:
            filters = [f"from_publication_date:{context.since.isoformat()}", "type:article"]
            if venue_mode == "only" and source_ids:
                filters.append(f"primary_location.source.id:{'|'.join(source_ids[:100])}")
            requests_to_make.append((query, filters))
        for author in context.config.get("authors", [])[:5]:
            author_id = clean_text(author.get("openalex_id")).rsplit("/", 1)[-1]
            if author_id:
                requests_to_make.append(
                    (
                        "",
                        [
                            f"from_publication_date:{context.since.isoformat()}",
                            "type:article",
                            f"authorships.author.id:{author_id}",
                        ],
                    )
                )
        try:
            for query, filters in requests_to_make:
                params = {
                    "api_key": key,
                    "filter": ",".join(filters),
                    "sort": "publication_date:desc",
                    "per_page": 10,
                    "select": "id,ids,display_name,authorships,abstract_inverted_index,publication_date,publication_year,primary_location,best_oa_location,cited_by_count,doi",
                }
                if query:
                    params["search"] = query
                payload = context.http.get_json(f"{self.base_url}?{urllib.parse.urlencode(params)}")
                items.extend(self._candidate(raw) for raw in payload.get("results", []) if raw.get("display_name"))
        except HttpFailure as exc:
            status = "limited" if exc.status == 429 else "failed"
            return SourceResult(self.id, status, items, str(exc), context.http.request_count - before)
        return SourceResult(self.id, "success", items, requests=context.http.request_count - before)
