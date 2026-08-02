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
    peer.add_argument("--config", default="config/game.toml.example")
    replay = commands.add_parser("replay", help="verify a completed log")
    replay.add_argument("log", type=Path)
    report = commands.add_parser("report", help="process an agreed result")
    report.add_argument("result", type=Path)
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
    print(sdk.foundation_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
