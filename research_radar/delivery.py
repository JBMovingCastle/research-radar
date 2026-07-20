from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import ConfigError, load_config, safe_path
from .state import atomic_json_write, read_json


def deliver(config_path: str | Path, date: str, channel: str, *, force: bool = False) -> dict[str, Any]:
    config, resolved = load_config(config_path)
    root = resolved.parent
    run_path = safe_path(root, config["paths"]["runs_dir"]) / f"{date}-run.json"
    state = read_json(run_path)
    if not state.get("brief_written"):
        raise ConfigError(f"No completed brief for {date}. Run the radar first.")
    if state.get("delivery_attempted") and not force:
        return {**state, "idempotent_skip": True}
    brief_path = safe_path(root, state["brief_path"], file_path=True)
    message = brief_path.read_text(encoding="utf-8").strip()
    if not message:
        raise ConfigError("Refusing to deliver an empty brief.")
    outcome = "success"
    detail = ""
    if channel == "local":
        detail = state["brief_path"]
    elif channel == "stdout":
        print(message)
        detail = "Printed to stdout."
    elif channel == "feishu":
        feishu = config.get("delivery", {}).get("feishu", {})
        env_name = feishu.get("user_id_env", "FEISHU_USER_ID")
        user_id = os.getenv(env_name, "")
        command = feishu.get("command", "lark-cli")
        if not user_id:
            raise ConfigError(f"Missing Feishu recipient environment variable: {env_name}")
        if not shutil.which(command):
            raise ConfigError(f"Feishu command not found: {command}")
        if len(message) > 12000:
            raise ConfigError("Feishu message exceeds the 12,000-character safety limit.")
        completed = subprocess.run(
            [command, "im", "+messages-send", "--as", "bot", "--user-id", user_id, "--markdown", message, "--idempotency-key", f"research-radar-{date}"],
            capture_output=True,
            text=True,
            check=False,
        )
        outcome = "success" if completed.returncode == 0 else "failed"
        detail = (completed.stdout if completed.returncode == 0 else completed.stderr or completed.stdout).strip()[:1000]
    else:
        raise ConfigError("channel must be local, stdout, or feishu.")
    state.update({"delivery_attempted": True, "delivery_sent": outcome == "success", "delivery_channel": channel, "delivery_status": outcome, "delivery_detail": detail})
    atomic_json_write(run_path, state)
    return state
