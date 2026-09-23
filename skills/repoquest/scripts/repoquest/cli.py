"""Command-line interface; verification is the only code-executing command."""

import argparse
from pathlib import Path
import sys

from .core import QuestError, load_case, verify
from .importer import import_git
from .render import render


def main(argv=None):
    parser = argparse.ArgumentParser(prog="repoquest", description="Build a debugging mystery from a curated Python bug.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Validate case structure and evidence without executing code")
    check.add_argument("case", type=Path)
    run = commands.add_parser("verify", help="Run a trusted contract against both snapshots; not a sandbox")
    run.add_argument("case", type=Path)
    run.add_argument("--trust-code", action="store_true", help="Acknowledge that the selected Python code will execute locally")
    run.add_argument("--timeout", type=float, default=10)
    build = commands.add_parser("build", help="Build standalone HTML from current verified evidence; never executes case code")
    build.add_argument("case", type=Path)
    build.add_argument("--output", type=Path, required=True)
    imp = commands.add_parser("import-git", help="Read selected files from two local commits into a draft case; never executes code")
    imp.add_argument("repo", type=Path)
    imp.add_argument("--before", required=True)
    imp.add_argument("--after", required=True)
    imp.add_argument("--file", action="append", dest="files", required=True)
    imp.add_argument("--contract", type=Path, required=True)
    imp.add_argument("--license-file", required=True)
    imp.add_argument("--license-name", required=True)
    imp.add_argument("--origin", required=True)
    imp.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            case, _ = load_case(args.case)
            print(f"Valid case: {case['id']} (no code executed)")
        elif args.command == "verify":
            report = verify(args.case, args.trust_code, args.timeout)
            print(f"Verified: before {len(report['before']['failures'])} failing / after {report['after']['tests']} passing; same contract")
        elif args.command == "build":
            if args.output.suffix.lower() != ".html":
                raise QuestError("Output must be an .html file")
            page = render(args.case)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(page, encoding="utf-8")
            print(f"Built {args.output.resolve()} (no code executed)")
        else:
            path = import_git(args.repo, args.before, args.after, args.files, args.contract,
                              args.license_file, args.license_name, args.origin, args.output)
            print(f"Imported {path}; curate narrative, evidence, hints, and solution before check/verify/build. No code executed.")
    except (QuestError, OSError, UnicodeError) as exc:
        print(f"repoquest: {exc}", file=sys.stderr)
        return 2
    return 0
