from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .checker import build_report
from .report import render
from .templates import CONFIG_TEMPLATE


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orgchat",
        description="Check production readiness of an organization chatbot project.",
    )
    parser.add_argument("--version", action="version", version=f"orgchat-check {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    check = subparsers.add_parser("check", help="Run the seven organization-chatbot readiness checks.")
    check.add_argument("--path", default=".", help="Project root to inspect. Default: current directory")
    check.add_argument("--config", help="Path to an orgchat.toml file")
    check.add_argument("--format", choices=["terminal", "json", "markdown"], default="terminal")
    check.add_argument("--output", help="Write the rendered report to this file")
    check.add_argument("--no-heuristics", action="store_true", help="Only use explicit orgchat.toml values")
    check.add_argument("--strict", action="store_true", help="Return exit code 1 for WARN as well as FAIL")

    init = subparsers.add_parser("init", help="Create a starter orgchat.toml file.")
    init.add_argument("--path", default=".", help="Project root. Default: current directory")
    init.add_argument("--force", action="store_true", help="Overwrite an existing orgchat.toml")
    return parser


def _write_report(content: str, output: str) -> None:
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def _run_init(path: str, force: bool) -> int:
    root = Path(path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "orgchat.toml"
    if destination.exists() and not force:
        print(f"File already exists: {destination}. Use --force to overwrite.", file=sys.stderr)
        return 1
    destination.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    print(f"Created {destination}")
    print("Run `orgchat check` after filling the values.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _run_init(args.path, args.force)

    if args.command != "check":
        parser.print_help()
        return 2

    try:
        report = build_report(
            root=args.path,
            config_path=args.config,
            use_heuristics=not args.no_heuristics,
        )
        content = render(report, args.format)
        if args.output:
            _write_report(content, args.output)
            print(f"Report written to {Path(args.output).expanduser().resolve()}")
        else:
            print(content, end="")
    except (OSError, ValueError) as exc:
        print(f"orgchat check failed: {exc}", file=sys.stderr)
        return 2

    if report.overall_status == "FAIL":
        return 1
    if args.strict and report.overall_status == "WARN":
        return 1
    return 0
