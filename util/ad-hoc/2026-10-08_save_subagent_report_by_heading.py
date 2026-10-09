#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File:          2026-10-08_save_subagent_report_by_heading.py
# Author:        Paul Calnon
# Version:       1.0.0
# License:       MIT License
# -----------------------------------------------------------------------------
# Purpose: save a subagent's report when its LAST assistant message is not the
# report. util/ad-hoc/2026-10-04_save_subagent_report.py takes the last text
# message; an agent whose background wait loop fires after it reported ends on a
# one-line "that notice was my wait loop" message, and the helper saves that
# (observed 2026-10-08, Phase B round 4 lane C: 182 characters saved).
#
# This variant takes the LAST assistant text message that starts with --heading,
# and applies the same shape screen as the original before writing.
#
# Usage: 2026-10-08_save_subagent_report_by_heading.py --tasks-dir <dir>
#            --agent <id> --heading "# Phase B round 4" --out <file>
# -----------------------------------------------------------------------------
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ARCHIVER = Path(__file__).with_name("2026-09-22_archive_consensus_reports.py")


def texts(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get("message") or {}
            if rec.get("type") != "assistant" and msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, str):
                yield content
            elif isinstance(content, list):
                yield "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", required=True, type=Path)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--heading", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    path = args.tasks_dir / f"agent-{args.agent}.jsonl"
    if not path.is_file():
        raise SystemExit(f"no transcript for {args.agent} at {path}")
    hits = [t for t in texts(path) if t.lstrip().startswith(args.heading)]
    if not hits:
        raise SystemExit(f"no assistant message starts with {args.heading!r}")
    body = hits[-1].strip() + "\n"

    spec = importlib.util.spec_from_file_location("archive_consensus_reports", ARCHIVER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ARCHIVER}")
    archiver = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = archiver
    spec.loader.exec_module(archiver)
    problems = archiver.screen(args.out.name, body)
    if problems:
        for problem in problems:
            print(f"  SHAPED: {problem}", file=sys.stderr)
        print("refusing to save: classify every hit by hand first", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body, encoding="utf-8")
    print(f"saved {args.out} ({len(body):,} characters; {len(hits)} candidate(s), took the last)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
