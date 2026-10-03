#!/usr/bin/env python3
"""Archive the backup design's consensus round 4 reports verbatim into a notes/ record.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-24
Status:      ad-hoc -- validation record
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-22_archive_consensus_reports.py (whose extraction and screen this reuses)
             notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md

util/ad-hoc/2026-09-22_archive_consensus_reports.py already does the careful part -- it lifts each
subagent's FINAL assistant message out of the session JSONL rather than retyping it, and refuses to
write a report carrying credential-shaped content, because notes/ is committed to a PUBLIC repository.
It hard-codes the transcript directory of the session that wrote it, so this loads it as a module,
points it at the directory given here, and keeps its extraction and its screen unchanged.

Three deliberate differences. No subagent id is written into the record: an id is session metadata, not
evidence, and it resolves to nothing outside the session that minted it. There is no --allow-shaped: a
credential-shaped hit refuses the archive outright, to be classified by hand before any re-run. And
--header is required, because a record without its disposition table is a pile of reports, not a record.

Usage:
    python3 util/ad-hoc/2026-09-24_archive_round4_reports.py --tasks-dir <session>/subagents \\
        --header <preamble.md> --out notes/<RECORD>.md --report '<Heading>=<agent-id>' [...] [--check]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ARCHIVER = Path(__file__).with_name("2026-09-22_archive_consensus_reports.py")


def load_archiver(tasks_dir: Path):
    spec = importlib.util.spec_from_file_location("archive_consensus_reports", ARCHIVER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ARCHIVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.TASKS = tasks_dir
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", required=True, type=Path)
    ap.add_argument("--header", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report", action="append", required=True, metavar="HEADING=AGENT_ID")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not args.tasks_dir.is_dir():
        raise SystemExit(f"no such transcript directory: {args.tasks_dir}")
    archiver = load_archiver(args.tasks_dir)

    parts = [args.header.read_text(encoding="utf-8").rstrip() + "\n"]
    problems: list[str] = []
    for spec in args.report:
        heading, _, agent_id = spec.partition("=")
        if not heading or not agent_id:
            raise SystemExit(f"--report must be HEADING=AGENT_ID, got {spec!r}")
        body = archiver.final_report(agent_id)
        problems += archiver.screen(heading, body)
        print(f"  {heading}: {len(body):,} characters")
        parts.append(
            f"\n---\n\n## {heading}\n\n"
            f"Archived verbatim ({len(body):,} characters), lifted from the subagent's own transcript.\n\n"
            "<!-- markdownlint-disable -->\n\n"
            f"{body}\n"
            "<!-- markdownlint-enable -->\n"
        )

    if problems:
        for problem in problems:
            print(f"  SHAPED: {problem}", file=sys.stderr)
        print("\nrefusing to archive: classify every hit by hand first", file=sys.stderr)
        return 2

    text = "".join(parts)
    size = f"{len(text):,} characters, {len(text.encode('utf-8')):,} bytes"
    if args.check:
        print(f"\n--check: would write {args.out} ({size}); nothing written")
        return 0
    args.out.write_text(text, encoding="utf-8")
    print(f"\nwrote {args.out} ({size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
