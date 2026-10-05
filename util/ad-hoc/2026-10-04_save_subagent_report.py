#!/usr/bin/env python3
"""Save one subagent's final report verbatim to a file, the moment it lands.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-10-04
Status:      ad-hoc -- validation record
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-22_archive_consensus_reports.py (whose extraction and screen this reuses)
             util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py (which assembles the saved files)

A subagent's report lives only in the session's transcript, and a session that ends -- or is cut by a
usage limit -- can take it along. This lifts the FINAL assistant message out of the transcript (never
retyped), runs the same credential-shape screen as the archivers, and writes it to a file under the
repository, so the record can be assembled later from files. A screen hit refuses the save.

Usage:
    python3 util/ad-hoc/2026-10-04_save_subagent_report.py --tasks-dir <session>/subagents \\
        --agent <agent-id> --out util/ad-hoc/<dir>/<lane>.md
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ARCHIVER = Path(__file__).with_name("2026-09-22_archive_consensus_reports.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", required=True, type=Path)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location("archive_consensus_reports", ARCHIVER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ARCHIVER}")
    archiver = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = archiver
    spec.loader.exec_module(archiver)
    archiver.TASKS = args.tasks_dir

    body = archiver.final_report(args.agent)
    problems = archiver.screen(args.out.name, body)
    if problems:
        for problem in problems:
            print(f"  SHAPED: {problem}", file=sys.stderr)
        print("refusing to save: classify every hit by hand first", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body, encoding="utf-8")
    print(f"saved {args.out} ({len(body):,} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
