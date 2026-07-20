from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

from ..http import HttpFailure
from ..models import PaperCandidate, SourceResult, clean_text
from .base import AdapterContext


class ArxivAdapter:
    id = "arxiv"
    base_url = "https://export.arxiv.org/api/query"
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    def collect(self, context: AdapterContext) -> SourceResult:
        settings = context.config["sources"].get(self.id, {})
        if not settings.get("enabled", False):
            return SourceResult(self.id, "disabled", detail="Disabled in config.")
        before = context.http.request_count
        items: list[PaperCandidate] = []
        try:
            for query in context.queries[:3]:
                terms = " AND ".join(f'all:"{term}"' for term in query.split()[:8])
                categories = [str(value) for value in settings.get("categories", []) if str(value)]
                if categories:
                    category_filter = " OR ".join(f"cat:{value}" for value in categories)
                    terms = f"({terms}) AND ({category_filter})"
                params = {"search_query": terms, "start": 0, "max_results": 10, "sortBy": "submittedDate", "sortOrder": "descending"}
                response = context.http.request(f"{self.base_url}?{urllib.parse.urlencode(params)}", headers={"Accept": "application/atom+xml"})
                try:
                    root = ET.fromstring(response.body)
                except ET.ParseError as exc:
                    raise HttpFailure("Invalid Atom XML from arXiv") from exc
                for entry in root.findall("atom:entry", self.ns):
                    entry_id = clean_text(entry.findtext("atom:id", default="", namespaces=self.ns))
                    published = clean_text(entry.findtext("atom:published", default="", namespaces=self.ns))[:10]
                    links = [node.attrib for node in entry.findall("atom:link", self.ns)]
                    pdf = next((link.get("href", "") for link in links if link.get("type") == "application/pdf"), "")
                    candidate = PaperCandidate(
                        source=self.id,
                        title=clean_text(entry.findtext("atom:title", default="", namespaces=self.ns)),
                        authors=[clean_text(node.findtext("atom:name", default="", namespaces=self.ns)) for node in entry.findall("atom:author", self.ns)],
                        abstract=clean_text(entry.findtext("atom:summary", default="", namespaces=self.ns)),
                        published_date=published,
                        year=int(published[:4]) if published[:4].isdigit() else None,
                        doi=clean_text(entry.findtext("arxiv:doi", default="", namespaces=self.ns)),
                        venue="arXiv",
                        url=entry_id,
                        full_text_url=pdf,
                        arxiv_id=entry_id.rsplit("/", 1)[-1],
                        evidence_level="abstract",
                    )
                    if candidate.title and (not published or published >= context.since.isoformat()):
                        items.append(candidate)
        except HttpFailure as exc:
            status = "limited" if exc.status == 429 else "failed"
            return SourceResult(self.id, status, items, str(exc), context.http.request_count - before)
        return SourceResult(self.id, "success", items, requests=context.http.request_count - before)
