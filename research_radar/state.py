from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .config import ConfigError
from .models import PaperCandidate


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON state file: {path}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"State file must contain an object: {path}")
    return value


def atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_ledger(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Corrupted ledger {path} at line {line_number}.") from exc
        canonical_id = str(row.get("canonical_id", ""))
        if canonical_id:
            result[canonical_id] = str(row.get("content_version", row.get("published_date", "")))
    return result


def append_ledger(path: Path, items: list[PaperCandidate], date: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_pairs: set[tuple[str, str]] = set()
    if path.exists():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ConfigError(f"Corrupted ledger {path} at line {line_number}.") from exc
            existing_pairs.add((str(row.get("date", "")), str(row.get("canonical_id", ""))))
    with path.open("a", encoding="utf-8") as handle:
        for item in items:
            if (date, item.canonical_id) in existing_pairs:
                continue
            row = {
                "date": date,
                "canonical_id": item.canonical_id,
                "title": item.title,
                "published_date": item.published_date,
                "content_version": item.published_date or str(item.year or ""),
                "sources": item.sources,
                "score": item.score,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            existing_pairs.add((date, item.canonical_id))
