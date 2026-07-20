from __future__ import annotations

import urllib.parse
from typing import Any

from ..http import HttpFailure
from ..models import PaperCandidate, SourceResult, clean_text
from .base import AdapterContext


class CrossrefAdapter:
    id = "crossref"
    base_url = "https://api.crossref.org"

    @staticmethod
    def _date(parts: Any) -> str:
        if not isinstance(parts, list) or not parts or not isinstance(parts[0], list):
            return ""
        values = parts[0]
        if not values:
            return ""
        return "-".join(str(value).zfill(2) for value in values[:3])

    @classmethod
    def _candidate(cls, item: dict[str, Any]) -> PaperCandidate:
        date_parts = item.get("published-print", item.get("published-online", item.get("issued", {}))).get("date-parts", [])
        published = cls._date(date_parts)
        authors = [
            clean_text(" ".join((author.get("given", ""), author.get("family", ""))))
            for author in item.get("author", [])
        ]
        links = item.get("link", [])
        full_text = next((clean_text(link.get("URL")) for link in links if "pdf" in clean_text(link.get("content-type")).lower()), "")
        return PaperCandidate(
            source=cls.id,
            title=clean_text(item.get("title")),
            authors=authors,
            abstract=clean_text(item.get("abstract")),
            published_date=published,
            year=int(published[:4]) if published[:4].isdigit() else None,
            doi=clean_text(item.get("DOI")),
            venue=clean_text(item.get("container-title")),
            issn=[clean_text(value) for value in item.get("ISSN", [])],
            url=clean_text(item.get("URL")),
            full_text_url=full_text,
            citation_count=int(item.get("is-referenced-by-count", 0) or 0),
            evidence_level="abstract" if item.get("abstract") else "metadata",
        )

    def collect(self, context: AdapterContext) -> SourceResult:
        settings = context.config["sources"].get(self.id, {})
        if not settings.get("enabled", False):
            return SourceResult(self.id, "disabled", detail="Disabled in config.")
        before = context.http.request_count
        items: list[PaperCandidate] = []
        venue_mode = context.config["selection"].get("venue_mode", "prefer")
        targets = [entry for entry in context.config.get("target_sources", []) if entry.get("issn")]
        requests_to_make: list[tuple[str, dict[str, str]]] = []
        for query in context.queries[:3]:
            if venue_mode != "only" or not targets:
                requests_to_make.append((f"{self.base_url}/works", {"query.bibliographic": query}))
        if targets and context.queries:
            for target in targets[:4]:
                requests_to_make.append(
                    (
                        f"{self.base_url}/journals/{urllib.parse.quote(target['issn'])}/works",
                        {"query.bibliographic": context.queries[0]},
                    )
                )
        for author in context.config.get("authors", [])[:5]:
            author_params: dict[str, str] = {}
            if clean_text(author.get("name")):
                author_params["query.author"] = clean_text(author["name"])
            if clean_text(author.get("orcid")):
                author_params["filter"] = f"orcid:{clean_text(author['orcid'])}"
            if author_params:
                requests_to_make.append((f"{self.base_url}/works", author_params))
        try:
            for endpoint, request_params in requests_to_make:
                params = {
                    "filter": f"from-pub-date:{context.since.isoformat()},type:journal-article",
                    "sort": "published",
                    "order": "desc",
                    "rows": "10",
                    "select": "DOI,title,author,abstract,published-print,published-online,issued,container-title,ISSN,URL,link,is-referenced-by-count",
                }
                if request_params.get("filter"):
                    params["filter"] = f"{params['filter']},{request_params['filter']}"
                params.update({key: value for key, value in request_params.items() if key != "filter"})
                mailto = clean_text(settings.get("mailto"))
                if mailto:
                    params["mailto"] = mailto
                payload = context.http.get_json(f"{endpoint}?{urllib.parse.urlencode(params)}")
                for raw in payload.get("message", {}).get("items", []):
                    candidate = self._candidate(raw)
                    if candidate.title:
                        items.append(candidate)
        except HttpFailure as exc:
            status = "limited" if exc.status == 429 else "failed"
            return SourceResult(self.id, status, items, str(exc), context.http.request_count - before)
        return SourceResult(self.id, "success", items, requests=context.http.request_count - before)
