"""Command-line adapter for the single Thief SDK entry point."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from thief_agent.sdk import ThiefSdk


def build_parser() -> argparse.ArgumentParser:
    """Build the stable public command surface."""
    parser = argparse.ArgumentParser(prog="thief-agent")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="show safe environment diagnostics")
    validate = commands.add_parser("validate", help="validate shared configuration")
    validate.add_argument("file", nargs="?", default="config/game.json")
    peer = commands.add_parser("peer", help="start the Thief peer")
    peer.add_argument("--config", type=Path, default=Path("config/game.secret.toml"))
    peer.add_argument("--game-config", type=Path, default=Path("config/game.json"))
    replay = commands.add_parser("replay", help="verify a completed log")
    replay.add_argument("log", type=Path)
    replay.add_argument("--config", type=Path, default=Path("config/game.json"))
    report = commands.add_parser("report", help="process an agreed result")
    report.add_argument("result", type=Path)
    report.add_argument("--mode", choices=("validate", "dry-run", "live"), default="validate")
    report.add_argument("--state-dir", type=Path, default=Path("artifacts/reporting/runtime"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one CLI command and return a process exit code."""
    args = build_parser().parse_args(argv)
    sdk = ThiefSdk()
    if args.command == "doctor":
        print(json.dumps(asdict(sdk.doctor()), sort_keys=True))
        return 0
    if args.command == "validate":
        print(json.dumps(asdict(sdk.validate_config(Path(args.file))), sort_keys=True))
        return 0
    if args.command == "replay":
        replay_report = sdk.verify_replay(args.log, args.config)
        print(json.dumps(asdict(replay_report), sort_keys=True))
        return 0 if replay_report.status == "Verified OK" else 1
    if args.command == "report":
        if args.mode != "validate":
            receipt = sdk.deliver_result(args.result, args.mode, args.state_dir)
            print(json.dumps(asdict(receipt), sort_keys=True, default=str))
            return 0
        result_report = sdk.validate_result(args.result)
        print(json.dumps(asdict(result_report), sort_keys=True))
        return 0 if result_report.confirmed else 1
    sdk.run_peer(args.config, args.game_config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
