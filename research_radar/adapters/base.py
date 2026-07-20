from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Protocol

from ..http import HttpClient
from ..models import SourceResult


@dataclass(slots=True)
class AdapterContext:
    config: dict[str, Any]
    today: dt.date
    since: dt.date
    focus_track: str
    queries: list[str]
    http: HttpClient


class SourceAdapter(Protocol):
    id: str

    def collect(self, context: AdapterContext) -> SourceResult: ...
