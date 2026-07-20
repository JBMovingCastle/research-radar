from __future__ import annotations

import json
import os
import re
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Any


CONFIG_NAME = "research-radar.config.json"
WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
ISSN_RE = re.compile(r"^\d{4}-[\dXx]{4}$")


class ConfigError(ValueError):
    pass


def load_config(path: str | Path = CONFIG_NAME) -> tuple[dict[str, Any], Path]:
    config_path = Path(path).expanduser().resolve()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config not found: {config_path}. Run `python3 -m research_radar init` first.") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {config_path}: line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config root must be a JSON object.")
    validate_config(data, config_path.parent)
    return data, config_path


def safe_path(root: Path, value: str, *, file_path: bool = False) -> Path:
    relative = Path(value)
    if not value or relative.is_absolute() or ".." in relative.parts:
        raise ConfigError(f"Unsafe repository path: {value!r}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ConfigError(f"Path escapes repository: {value!r}") from exc
    if file_path and not resolved.name:
        raise ConfigError(f"Expected a file path: {value!r}")
    return resolved


def validate_config(config: dict[str, Any], root: Path) -> None:
    if config.get("config_version") != 1:
        raise ConfigError("config_version must be 1.")
    project = config.get("project")
    if not isinstance(project, dict) or not str(project.get("name", "")).strip():
        raise ConfigError("project.name is required.")
    tracks = config.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ConfigError("At least one track is required.")
    ids: set[str] = set()
    query_count = 0
    for track in tracks:
        if not isinstance(track, dict):
            raise ConfigError("Each track must be an object.")
        track_id = str(track.get("id", "")).strip()
        if not track_id or track_id in ids:
            raise ConfigError(f"Track IDs must be non-empty and unique: {track_id!r}")
        ids.add(track_id)
        queries = [str(item).strip() for item in track.get("queries", []) if str(item).strip()]
        keywords = [str(item).strip() for item in track.get("keywords", []) if str(item).strip()]
        if not queries or not keywords:
            raise ConfigError(f"Track {track_id!r} needs at least one query and one keyword.")
        query_count += len(queries)
    if query_count == 0:
        raise ConfigError("At least one non-empty query is required.")
    rotation = config.get("rotation", {})
    invalid_days = set(rotation) - WEEKDAYS
    if invalid_days:
        raise ConfigError(f"Invalid rotation weekdays: {sorted(invalid_days)}")
    selection = config.get("selection", {})
    if selection.get("venue_mode") not in {"prefer", "only"}:
        raise ConfigError("selection.venue_mode must be 'prefer' or 'only'.")
    limit = selection.get("daily_limit")
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ConfigError("selection.daily_limit must be an integer from 1 to 20.")
    weights = config.get("score_weights", {})
    required_weights = {"relevance", "source_quality", "recency", "impact", "novelty"}
    if set(weights) != required_weights or any(not isinstance(weights[key], (int, float)) or weights[key] < 0 for key in required_weights):
        raise ConfigError(f"score_weights must define non-negative values for {sorted(required_weights)}.")
    for source in config.get("target_sources", []):
        issn = str(source.get("issn", "")).strip()
        if issn and not ISSN_RE.match(issn):
            raise ConfigError(f"Invalid ISSN: {issn!r}. Use NNNN-NNNN.")
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise ConfigError("paths is required.")
    for key in ("briefs_dir", "topics_dir", "runs_dir"):
        safe_path(root, str(paths.get(key, "")))
    safe_path(root, str(paths.get("ledger_file", "")), file_path=True)
    sources = config.get("sources")
    if not isinstance(sources, dict):
        raise ConfigError("sources is required.")
    built_in_enabled = any(
        bool(sources.get(name, {}).get("enabled"))
        for name in ("crossref", "arxiv", "semantic_scholar", "openalex")
    )
    if not built_in_enabled and not sources.get("feeds") and not sources.get("web_pages"):
        raise ConfigError("At least one academic source, feed, or official web page must be enabled.")
    names: set[str] = set()
    for group in ("feeds", "web_pages"):
        entries = sources.get(group, [])
        if not isinstance(entries, list):
            raise ConfigError(f"sources.{group} must be a list.")
        for entry in entries:
            name = str(entry.get("name", "")).strip().lower()
            url = str(entry.get("url", "")).strip()
            if not name or name in names:
                raise ConfigError(f"Custom source names must be non-empty and unique: {name!r}")
            if not url.startswith(("https://", "http://")):
                raise ConfigError(f"Custom source URL must use http(s): {url!r}")
            names.add(name)


def initialize(
    destination: Path,
    *,
    preset: str = "ci3",
    force: bool = False,
    interactive: bool = False,
) -> Path:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    config_path = destination / CONFIG_NAME
    if config_path.exists() and not force:
        raise ConfigError(f"Config already exists: {config_path}. Use --force to replace it.")
    template_resource = resources.files("configs").joinpath(f"{preset}.json")
    if not template_resource.is_file():
        raise ConfigError(f"Unknown preset: {preset}")
    data = json.loads(template_resource.read_text(encoding="utf-8"))
    if interactive:
        name = input(f"Research group name [{data['project']['name']}]: ").strip()
        if name:
            data["project"]["name"] = name
            data["project"]["full_name"] = name
        title = input(f"Daily brief title [{data['project']['brief_title']}]: ").strip()
        if title:
            data["project"]["brief_title"] = title
        keywords = input("Extra context keywords, comma separated [none]: ").strip()
        if keywords:
            data["context_keywords"].extend(item.strip() for item in keywords.split(",") if item.strip())
    validate_config(data, destination)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key in ("briefs_dir", "topics_dir", "runs_dir"):
        safe_path(destination, data["paths"][key]).mkdir(parents=True, exist_ok=True)
    safe_path(destination, data["paths"]["ledger_file"], file_path=True).parent.mkdir(parents=True, exist_ok=True)
    return config_path


def doctor(config_path: str | Path = CONFIG_NAME) -> tuple[bool, list[dict[str, str]]]:
    checks: list[dict[str, str]] = []
    if sys.version_info < (3, 11):
        checks.append({"status": "error", "check": "python", "detail": "Python 3.11 or newer is required."})
    else:
        checks.append({"status": "ok", "check": "python", "detail": sys.version.split()[0]})
    try:
        config, path = load_config(config_path)
    except ConfigError as exc:
        checks.append({"status": "error", "check": "config", "detail": str(exc)})
        return False, checks
    checks.append({"status": "ok", "check": "config", "detail": str(path)})
    root = path.parent
    for key, value in config["paths"].items():
        target = safe_path(root, value, file_path=key == "ledger_file")
        parent = target.parent if key == "ledger_file" else target
        writable = os.access(parent, os.W_OK) if parent.exists() else os.access(parent.parent, os.W_OK)
        checks.append({"status": "ok" if writable else "error", "check": f"path:{key}", "detail": value})
    openalex = config["sources"].get("openalex", {})
    if openalex.get("enabled"):
        env_name = openalex.get("api_key_env", "OPENALEX_API_KEY")
        checks.append({"status": "ok" if os.getenv(env_name) else "error", "check": "openalex-key", "detail": f"{env_name} is {'set' if os.getenv(env_name) else 'missing'}"})
    else:
        checks.append({"status": "info", "check": "openalex-key", "detail": "OpenAlex disabled; enable it after setting OPENALEX_API_KEY."})
    semantic = config["sources"].get("semantic_scholar", {})
    s2_env = semantic.get("api_key_env", "S2_API_KEY")
    checks.append({"status": "ok" if os.getenv(s2_env) else "info", "check": "semantic-scholar-key", "detail": f"{s2_env} is {'set' if os.getenv(s2_env) else 'optional and missing'}"})
    command = config.get("delivery", {}).get("feishu", {}).get("command", "lark-cli")
    checks.append({"status": "ok" if shutil.which(command) else "info", "check": "feishu", "detail": f"{command} {'available' if shutil.which(command) else 'not installed; local delivery still works'}"})
    return not any(item["status"] == "error" for item in checks), checks
