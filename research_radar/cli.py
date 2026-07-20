from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import CONFIG_NAME, ConfigError, doctor, initialize, load_config
from .delivery import deliver
from .pipeline import run_daily


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-radar", description="Configurable daily research radar for Codex and Obsidian.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a safe local configuration and output folders.")
    init.add_argument("--destination", default=".")
    init.add_argument("--preset", choices=("ci3", "blank"), default="ci3")
    init.add_argument("--interactive", action="store_true")
    init.add_argument("--force", action="store_true")

    check = sub.add_parser("doctor", help="Validate Python, configuration, paths, optional keys, and Feishu readiness.")
    check.add_argument("--config", default=CONFIG_NAME)
    check.add_argument("--json", action="store_true")

    validate = sub.add_parser("validate", help="Validate the configuration without collecting sources.")
    validate.add_argument("--config", default=CONFIG_NAME)

    show = sub.add_parser("show-config", help="Print the effective public configuration; environment secrets are never included.")
    show.add_argument("--config", default=CONFIG_NAME)

    run = sub.add_parser("run", help="Collect, select, and write one daily Markdown brief.")
    run.add_argument("--config", default=CONFIG_NAME)
    run.add_argument("--date", help="YYYY-MM-DD; defaults to configured local date.")
    run.add_argument("--force", action="store_true", help="Replace today's brief; existing same-day ledger entries are kept unique.")
    run.add_argument("--json", action="store_true")

    send = sub.add_parser("deliver", help="Deliver an existing brief through local, stdout, or optional Feishu.")
    send.add_argument("--config", default=CONFIG_NAME)
    send.add_argument("--date", required=True)
    send.add_argument("--channel", choices=("local", "stdout", "feishu"), default="local")
    send.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            path = initialize(Path(args.destination), preset=args.preset, force=args.force, interactive=args.interactive)
            print(f"Created {path}")
            print("Next: python3 -m research_radar doctor --config research-radar.config.json")
            return 0
        if args.command == "doctor":
            ok, checks = doctor(args.config)
            if args.json:
                print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
            else:
                for item in checks:
                    print(f"[{item['status'].upper():5}] {item['check']}: {item['detail']}")
            return 0 if ok else 1
        if args.command == "validate":
            _, path = load_config(args.config)
            print(f"Valid: {path}")
            return 0
        if args.command == "show-config":
            config, _ = load_config(args.config)
            print(json.dumps(config, ensure_ascii=False, indent=2))
            return 0
        if args.command == "run":
            result = run_daily(args.config, date=args.date, force=args.force)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Brief: {result.get('brief_path', '')}")
                print(f"Selected: {result.get('selected_count', 0)} | Coverage: {result.get('coverage', 'unknown')}")
                if result.get("idempotent_skip"):
                    print("Skipped: today's brief already exists. Use --force only for an intentional rebuild.")
            return 0
        if args.command == "deliver":
            result = deliver(args.config, args.date, args.channel, force=args.force)
            print(json.dumps({key: result.get(key) for key in ("date", "delivery_channel", "delivery_status", "delivery_detail", "idempotent_skip")}, ensure_ascii=False))
            return 0 if result.get("delivery_status", "success") == "success" else 1
    except (ConfigError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 2
