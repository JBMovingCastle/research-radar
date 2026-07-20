from __future__ import annotations

import os
import urllib.parse
from typing import Any

from ..http import HttpFailure
from ..models import PaperCandidate, SourceResult, clean_text
from .base import AdapterContext


FIELDS = "paperId,title,abstract,authors,year,publicationDate,venue,externalIds,url,openAccessPdf,citationCount"


def _candidate(item: dict[str, Any], source: str) -> PaperCandidate:
    external = item.get("externalIds") or {}
    published = clean_text(item.get("publicationDate"))
    year = item.get("year")
    return PaperCandidate(
        source=source,
        title=clean_text(item.get("title")),
        authors=[clean_text(author.get("name")) for author in item.get("authors", [])],
        abstract=clean_text(item.get("abstract")),
        published_date=published,
        year=int(year) if isinstance(year, int) or str(year).isdigit() else None,
        doi=clean_text(external.get("DOI")),
        venue=clean_text(item.get("venue")),
        url=clean_text(item.get("url")),
        full_text_url=clean_text((item.get("openAccessPdf") or {}).get("url")),
        arxiv_id=clean_text(external.get("ArXiv")),
        semantic_scholar_id=clean_text(item.get("paperId")),
        citation_count=int(item.get("citationCount", 0) or 0),
        evidence_level="abstract" if item.get("abstract") else "metadata",
    )


class SemanticScholarSearchAdapter:
    id = "semantic_scholar"
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def collect(self, context: AdapterContext) -> SourceResult:
        settings = context.config["sources"].get("semantic_scholar", {})
        if not settings.get("enabled", False):
            return SourceResult(self.id, "disabled", detail="Disabled in config.")
        env_name = settings.get("api_key_env", "S2_API_KEY")
        key = os.getenv(env_name, "")
        headers = {"x-api-key": key} if key else {}
        before = context.http.request_count
        items: list[PaperCandidate] = []
        try:
            for query in context.queries[:3]:
                params = {"query": query, "limit": 10, "fields": FIELDS, "publicationDateOrYear": f"{context.since.isoformat()}:"}
                payload = context.http.get_json(f"{self.base_url}?{urllib.parse.urlencode(params)}", headers=headers)
                items.extend(_candidate(raw, self.id) for raw in payload.get("data", []) if raw.get("title"))
        except HttpFailure as exc:
            status = "limited" if exc.status == 429 else "failed"
            return SourceResult(self.id, status, items, str(exc), context.http.request_count - before)
        detail = "Authenticated." if key else "Unauthenticated shared rate limit."
        return SourceResult(self.id, "success", items, detail, context.http.request_count - before)


class SemanticScholarRecommendationsAdapter:
    id = "semantic_scholar_recommendations"
    base_url = "https://api.semanticscholar.org/recommendations/v1/papers"

    def collect(self, context: AdapterContext) -> SourceResult:
        settings = context.config["sources"].get("semantic_scholar", {})
        if not settings.get("enabled", False) or not settings.get("recommendations_enabled", False):
            return SourceResult(self.id, "disabled", detail="Recommendations disabled in config.")
        seeds = context.config.get("seed_papers", {})
        positive = [str(value).strip() for value in seeds.get("positive", []) if str(value).strip()]
        negative = [str(value).strip() for value in seeds.get("negative", []) if str(value).strip()]
        if not positive:
            return SourceResult(self.id, "skipped", detail="No positive seed papers configured.")
        env_name = settings.get("api_key_env", "S2_API_KEY")
        key = os.getenv(env_name, "")
        headers = {"x-api-key": key} if key else {}
        before = context.http.request_count
        params = {"limit": 20, "fields": FIELDS}
        try:
            payload = context.http.post_json(
                f"{self.base_url}?{urllib.parse.urlencode(params)}",
                {"positivePaperIds": positive[:100], "negativePaperIds": negative[:100]},
                headers=headers,
            )
            items = []
            for raw in payload.get("recommendedPapers", []):
                if not raw.get("title"):
                    continue
                candidate = _candidate(raw, self.id)
                if not candidate.published_date or candidate.published_date >= context.since.isoformat():
                    items.append(candidate)
        except HttpFailure as exc:
            status = "limited" if exc.status == 429 else "failed"
            return SourceResult(self.id, status, detail=str(exc), requests=context.http.request_count - before)
        return SourceResult(self.id, "success", items, requests=context.http.request_count - before)
