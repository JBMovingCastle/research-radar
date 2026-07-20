from __future__ import annotations

import email.utils
import xml.etree.ElementTree as ET

from ..http import HttpFailure
from ..models import PaperCandidate, SourceResult, clean_text
from .base import AdapterContext


def _first_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in node.iter():
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in names and clean_text(child.text):
            return clean_text(child.text)
    return ""


def _link(node: ET.Element) -> str:
    for child in node.iter():
        if child.tag.rsplit("}", 1)[-1].lower() == "link":
            if child.attrib.get("href"):
                return clean_text(child.attrib["href"])
            if clean_text(child.text):
                return clean_text(child.text)
    return ""


def _date(value: str) -> str:
    value = clean_text(value)
    if len(value) >= 10 and value[4:5] == "-":
        return value[:10]
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


class FeedAdapter:
    id = "feeds"

    def collect(self, context: AdapterContext) -> SourceResult:
        feeds = context.config["sources"].get("feeds", [])
        if not feeds:
            return SourceResult(self.id, "skipped", detail="No RSS/Atom feeds configured.")
        before = context.http.request_count
        items: list[PaperCandidate] = []
        errors: list[str] = []
        for feed in feeds:
            try:
                response = context.http.request(feed["url"], headers={"Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml"})
                root = ET.fromstring(response.body)
                entries = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}]
                for entry in entries[: int(feed.get("max_items", 20))]:
                    published = _date(_first_text(entry, ("published", "updated", "pubdate", "date")))
                    candidate = PaperCandidate(
                        source=f"feed:{feed['name']}",
                        source_type="feed",
                        title=_first_text(entry, ("title",)),
                        authors=[_first_text(entry, ("author", "creator"))],
                        abstract=_first_text(entry, ("summary", "description", "content")),
                        published_date=published,
                        year=int(published[:4]) if published[:4].isdigit() else None,
                        doi=_first_text(entry, ("doi",)),
                        venue=feed["name"],
                        url=_link(entry),
                        evidence_level="feed-summary",
                    )
                    if candidate.title and (not published or published >= context.since.isoformat()):
                        items.append(candidate)
            except (HttpFailure, ET.ParseError) as exc:
                errors.append(f"{feed['name']}: {exc}")
        status = "partial" if errors and items else "failed" if errors else "success"
        return SourceResult(self.id, status, items, "; ".join(errors), context.http.request_count - before)
