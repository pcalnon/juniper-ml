#!/usr/bin/env python3
"""Match each saved validation-report file to the subagent final message it was copied from.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-10-05
Status:      ad-hoc -- provenance check for the Phase B consensus record
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py (writes each report's origin line)
             util/ad-hoc/2026-09-22_archive_consensus_reports.py (final_report(), reused here)

The Phase B record says where each report came from. That line has to be checked, not assumed: the
2026-10-05 validation of the round-3 handoff found it false for five sections. This compares every
--file, after the archiver's own normalisation (rstrip plus one newline), with two things in every
subagent transcript under each --tasks-dir: the FINAL assistant message, and the content of every Write
call (round 2's lanes wrote their reports as files, so their final messages are not the report). A file
that matches neither is reported with any blank-line-insensitive match to a final message, which
separates "not a lane's report" from "a lane's report with its blank lines rewritten"; --diagnose also
names the closest final message and prints the lines that differ. Read-only: it opens transcripts and
files, and writes nothing.

It replays Write and Edit calls only, never Bash. Over the Phase B record's sources it therefore confirms
all but four by content, and exits 1 on those four, all of them true origins:

- round 2's lane B, ml#2114 and ml#2115 lanes finished their own report files in place with a Python
  .replace or `sed -i`;
- the coordinating session did the same to round 3's brief, with a `sed -i` between its Write and two Edits.

Those four rest on the other criterion: the file's last writer is its own lane (for the brief, the
coordinator), and its mtime falls inside that writer's window, before the next reader starts. The round-3
handoff's re-validation established both, with its own instruments, for the first 14 sources (its "Not
refuted"), and its third validation re-derived the same four failures over 15.

Usage:
    python3 util/ad-hoc/2026-10-05_match_reports_to_final_messages.py \\
        --tasks-dir <session>/subagents [--tasks-dir ...] --file <report.md> [--file ...] [--diagnose]
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import sys
from pathlib import Path

ARCHIVER = Path(__file__).with_name("2026-09-22_archive_consensus_reports.py")


def load_archiver():
    spec = importlib.util.spec_from_file_location("archive_consensus_reports", ARCHIVER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ARCHIVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def without_blank_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if line.strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", action="append", required=True, type=Path)
    ap.add_argument("--file", action="append", required=True, type=Path)
    ap.add_argument("--diagnose", action="store_true", help="for an unmatched file, show the closest final message and the differing lines")
    args = ap.parse_args()

    archiver = load_archiver()
    finals: dict[tuple[str, str], str] = {}
    for tasks_dir in args.tasks_dir:
        if not tasks_dir.is_dir():
            raise SystemExit(f"no such transcript directory: {tasks_dir}")
        archiver.TASKS = tasks_dir
        session = tasks_dir.parent.name[:8]
        for transcript in sorted(tasks_dir.glob("agent-*.jsonl")):
            agent = transcript.name[len("agent-") : -len(".jsonl")]
            try:
                finals[(session, agent)] = archiver.final_report(agent).rstrip() + "\n"
            except SystemExit:
                continue
    print(f"{len(finals)} final messages read")
    writes = written_files(args.tasks_dir)
    print(f"{len(writes)} written files reconstructed")

    unmatched = 0
    for path in args.file:
        body = path.read_text(encoding="utf-8").rstrip() + "\n"
        exact = [f"{s}/{a}" for (s, a), text in finals.items() if text == body]
        wrote = [f"{s}/{a} wrote {name}" for (s, a, name), text in writes if text.rstrip() + "\n" == body]
        print(f"{path.name}: {len(body):,} characters; final message: {exact or 'NONE'}; written file: {wrote or 'NONE'}")
        if not exact and not wrote:
            unmatched += 1
            loose = [f"{s}/{a}" for (s, a), text in finals.items() if without_blank_lines(text) == without_blank_lines(body)]
            print(f"  blank-line-insensitive: {loose or 'NONE'}")
            if args.diagnose:
                diagnose(body, finals)
                same_name = {f"{s}/{a} wrote {name}": text.rstrip() + "\n" for (s, a, name), text in writes if name == path.name}
                diagnose(body, same_name)
    return 1 if unmatched else 0


def written_files(tasks_dirs: list[Path]) -> list[tuple[tuple[str, str, str], str]]:
    """Each file a transcript wrote, as its Write and then its own Edit calls left it, keyed by
    (session, agent, file name). A lane that wrote its own report file is the report's origin, whatever
    its final message says. An Edit whose old_string is absent is skipped (it failed in the session too)."""
    found = []
    for tasks_dir in tasks_dirs:
        session = tasks_dir.parent.name[:8]
        # The session's own transcript sits beside its directory: a brief the parent wrote is found there.
        parent = tasks_dir.parent.with_suffix(".jsonl")
        transcripts = [(agent_file.name[len("agent-") : -len(".jsonl")], agent_file) for agent_file in sorted(tasks_dir.glob("agent-*.jsonl"))]
        if parent.is_file():
            transcripts.append(("main", parent))
        for agent, transcript in transcripts:
            files: dict[str, str] = {}
            with transcript.open(encoding="utf-8") as fh:
                for line in fh:
                    try:
                        content = (json.loads(line).get("message") or {}).get("content")
                    except json.JSONDecodeError:
                        continue
                    for block in content if isinstance(content, list) else []:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        given = block.get("input") or {}
                        path = str(given.get("file_path", ""))
                        if block.get("name") == "Write" and isinstance(given.get("content"), str):
                            files[path] = given["content"]
                        elif block.get("name") == "Edit" and path in files and given.get("old_string", "") in files[path]:
                            count = -1 if given.get("replace_all") else 1
                            files[path] = files[path].replace(given["old_string"], given.get("new_string", ""), count)
            found += [((session, agent, Path(path).name), text) for path, text in files.items()]
    return found


def diagnose(body: str, candidates: dict) -> None:
    """Name the candidate with the fewest differing lines and show how the file departs from it."""
    if not candidates:
        print("  no candidate to compare")
        return

    def delta(text: str) -> list[str]:
        return [line for line in difflib.unified_diff(text.splitlines(), body.splitlines(), n=0, lineterm="") if line[:1] in "+-" and line[:3] not in ("+++", "---")]

    label, text = min(candidates.items(), key=lambda item: len(delta(item[1])))
    lines = delta(text)
    print(f"  closest: {label} ({len(text):,} characters); {len(lines)} differing lines (- candidate, + file); first 12:")
    for line in lines[:12]:
        print(f"    {line[:160]}")


if __name__ == "__main__":
    raise SystemExit(main())
