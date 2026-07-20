from __future__ import annotations

import dataclasses
import hashlib
import re
from typing import Any


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_doi(value: str | None) -> str:
    doi = clean_text(value).lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix) :]
    return doi.strip().rstrip(".,;)")


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", clean_text(value).lower())


@dataclasses.dataclass(slots=True)
class PaperCandidate:
    source: str
    source_type: str = "academic"
    title: str = ""
    authors: list[str] = dataclasses.field(default_factory=list)
    abstract: str = ""
    published_date: str = ""
    year: int | None = None
    doi: str = ""
    venue: str = ""
    issn: list[str] = dataclasses.field(default_factory=list)
    url: str = ""
    full_text_url: str = ""
    arxiv_id: str = ""
    semantic_scholar_id: str = ""
    openalex_id: str = ""
    citation_count: int = 0
    evidence_level: str = "metadata"
    sources: list[str] = dataclasses.field(default_factory=list)
    track_hits: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    matched_track: str = ""
    score: float = 0.0
    score_breakdown: dict[str, float] = dataclasses.field(default_factory=dict)
    previously_seen: bool = False

    def __post_init__(self) -> None:
        self.title = clean_text(self.title)
        self.abstract = clean_text(self.abstract)
        self.doi = normalize_doi(self.doi)
        self.authors = [clean_text(item) for item in self.authors if clean_text(item)]
        self.issn = sorted({clean_text(item).upper() for item in self.issn if clean_text(item)})
        self.sources = sorted(set(self.sources or [self.source]))

    @property
    def canonical_id(self) -> str:
        if self.doi:
            return f"doi:{self.doi}"
        for prefix, value in (
            ("arxiv", self.arxiv_id),
            ("s2", self.semantic_scholar_id),
            ("openalex", self.openalex_id),
        ):
            if value:
                return f"{prefix}:{value.lower()}"
        digest = hashlib.sha256(f"{normalize_title(self.title)}|{self.year or ''}".encode()).hexdigest()[:20]
        return f"title:{digest}"

    @property
    def searchable_text(self) -> str:
        return " ".join((self.title, self.abstract, self.venue, " ".join(self.authors))).lower()

    def to_dict(self) -> dict[str, Any]:
        value = dataclasses.asdict(self)
        value["canonical_id"] = self.canonical_id
        return value


@dataclasses.dataclass(slots=True)
class SourceResult:
    source: str
    status: str
    items: list[PaperCandidate] = dataclasses.field(default_factory=list)
    detail: str = ""
    requests: int = 0

    def to_status_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "items": len(self.items),
            "requests": self.requests,
            "detail": self.detail,
        }
