from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

from ..http import HttpFailure
from ..models import PaperCandidate, SourceResult, clean_text
from .base import AdapterContext


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_href = ""
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href") or ""
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.current_href:
            title = clean_text(" ".join(self.current_text))
            if title:
                self.links.append((self.current_href, title))
            self.current_href = ""
            self.current_text = []


class WebPageAdapter:
    id = "web_pages"

    def collect(self, context: AdapterContext) -> SourceResult:
        pages = context.config["sources"].get("web_pages", [])
        if not pages:
            return SourceResult(self.id, "skipped", detail="No official pages configured.")
        before = context.http.request_count
        items: list[PaperCandidate] = []
        errors: list[str] = []
        for page in pages:
            try:
                response = context.http.request(page["url"], headers={"Accept": "text/html"})
                parser = LinkParser()
                parser.feed(response.body.decode("utf-8", errors="replace"))
                seen: set[str] = set()
                for href, title in parser.links:
                    url = urljoin(page["url"], href)
                    if url in seen or not url.startswith(("https://", "http://")):
                        continue
                    seen.add(url)
                    items.append(
                        PaperCandidate(
                            source=f"web:{page['name']}",
                            source_type="industry",
                            title=title,
                            venue=page["name"],
                            url=url,
                            evidence_level="webpage-link",
                        )
                    )
                    if len(seen) >= int(page.get("max_items", 10)):
                        break
            except HttpFailure as exc:
                errors.append(f"{page['name']}: {exc}")
        status = "partial" if errors and items else "failed" if errors else "success"
        return SourceResult(self.id, status, items, "; ".join(errors), context.http.request_count - before)
