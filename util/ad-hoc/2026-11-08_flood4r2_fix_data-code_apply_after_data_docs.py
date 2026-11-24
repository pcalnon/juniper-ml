#!/usr/bin/env python3
"""
Write and verify the edit the data-code carrier must make to data-docs' text once data-docs is on main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: data-claims-lens F1, the landing-order hazard)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/data-claims-lens/findings.json F1 (BLOCKER) and F5

Usage:
  2026-11-08_flood4r2_fix_data-code_apply_after_data_docs.py <data repo or worktree> <main sha>
      <data-tests wt> <data-docs wt> <data-code wt> <out json> <work dir>

data-docs adds docs/REFERENCE.md § Failed-Auth Throttle Retention, whose "When a window ends" paragraph states the
throttle's Retry-After as main computes it: truncated. data-code rounds it up but is built on a main WITHOUT that
section, and the three carriers merge with no conflict, so nothing forces the change. This script writes the exact
old -> new edit into <out json> and checks it two ways:

1. ``old`` occurs exactly once in data-docs' final docs/REFERENCE.md.
2. A simulated landing in the planned order (data-tests, data-docs, data-code), each carrier's REFERENCE.md merged
   over main's with ``git merge-file -p`` (stdout only; no worktree is written), has no conflict, holds ``old``
   exactly once, and after the edit holds no truncated throttle formula in that section.

The optional Pins-table row is checked the same way (its anchor row occurs once). Nothing is written outside
<out json> and <work dir>.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REF = "docs/REFERENCE.md"
OLD = "`Retry-After` is `max(1, int(window_seconds - elapsed))`: truncated, with a floor of 1. A fraction of a second left is still 1 second, and 9.4 seconds left is 9."
NEW = "`Retry-After` is `max(1, math.ceil(window_seconds - elapsed))`: rounded up, with a floor of 1. A fraction of a second left is 1 second, and 9.4 seconds left is 10."
PIN_ANCHOR = "| `test_the_entry_cap_drops_the_oldest_recorded_failures` | same | With `_MAX_ENTRIES` patched to 3, cleanup keeps the three newest rows by `window_start` and the new failure makes four; an evicted address is not blocked, and checking it does not insert it |\n"
PIN_ROW = "| `TestFailedAuthThrottleRoundsUp` | `tests/unit/test_retry_after_rounds_up.py` | With a frozen clock: 9.4 s left is `10`, 6.0 s stays `6`, a sub-second remainder is `1`, a fresh block is the whole window, and the pre-auth 429's `Retry-After` carries the rounded value |\n"


def _merge(current: Path, base: Path, other: Path) -> tuple[str, int]:
    proc = subprocess.run(["git", "merge-file", "-p", str(current), str(base), str(other)], capture_output=True, text=True, check=False)
    return proc.stdout, proc.returncode


def _section(text: str) -> str:
    start = text.index("## Failed-Auth Throttle Retention")
    return text[start : text.index("\n## ", start + 1)]


def main(argv: list[str]) -> int:
    repo, sha = argv[1], argv[2]
    tests_wt, docs_wt, code_wt = Path(argv[3]), Path(argv[4]), Path(argv[5])
    out, work = Path(argv[6]), Path(argv[7])
    work.mkdir(parents=True, exist_ok=True)
    main_text = subprocess.run(["git", "-C", repo, "show", f"{sha}:{REF}"], capture_output=True, text=True, check=True).stdout
    base = work / "REFERENCE.main.md.txt"
    base.write_text(main_text, encoding="utf-8")
    docs_text = (docs_wt / REF).read_text(encoding="utf-8")
    checks: dict = {"old_in_data_docs_final": docs_text.count(OLD), "old_in_data_code_tree": (code_wt / REF).read_text(encoding="utf-8").count(OLD)}
    # Simulated landing: data-tests, then data-docs, then data-code, each merged over main's REFERENCE.md.
    current = work / "REFERENCE.landing.step0.md.txt"
    current.write_text(main_text, encoding="utf-8")
    steps = []
    for index, (label, wt) in enumerate((("data-tests", tests_wt), ("data-docs", docs_wt), ("data-code", code_wt)), start=1):
        merged, conflicts = _merge(current, base, wt / REF)
        current = work / f"REFERENCE.landing.step{index}.{label}.md.txt"
        current.write_text(merged, encoding="utf-8")
        steps.append({"after": label, "merge_file_exit (conflicts)": conflicts, "has_conflict_markers": "<<<<<<<" in merged})
    landed = current.read_text(encoding="utf-8")
    checks["landing_steps"] = steps
    checks["old_in_landed"] = landed.count(OLD)
    checks["pin_anchor_in_landed"] = landed.count(PIN_ANCHOR)
    edited = landed.replace(OLD, NEW, 1)
    section = _section(edited)
    checks["after_edit_new_in_section"] = section.count(NEW)
    checks["after_edit_int_formula_in_section"] = section.count("int(window_seconds")
    checks["after_edit_truncated_in_section"] = section.count("truncated")
    (work / "REFERENCE.landing.after_edit.md.txt").write_text(edited, encoding="utf-8")
    ok = (
        checks["old_in_data_docs_final"] == 1
        and checks["old_in_data_code_tree"] == 0
        and all(step["merge_file_exit (conflicts)"] == 0 and not step["has_conflict_markers"] for step in steps)
        and checks["old_in_landed"] == 1
        and checks["after_edit_new_in_section"] == 1
        and checks["after_edit_int_formula_in_section"] == 0
        and checks["after_edit_truncated_in_section"] == 0
        and checks["pin_anchor_in_landed"] == 1
    )
    record = {
        "purpose": "data-claims-lens F1 (BLOCKER): data-code rounds the failed-auth throttle's Retry-After up, but data-docs (which lands BEFORE data-code) states it truncated in docs/REFERENCE.md § Failed-Auth Throttle Retention > When a window ends, and the three carriers merge with no conflict. When the orchestrator rebuilds data-code on the main that holds data-docs, it applies `edits` (required) to that main's docs/REFERENCE.md. Do NOT add the sentence to data-code before then: data-code's own tree has no such section.",
        "target_repo": "juniper-data",
        "carrier": "data-code",
        "apply_when": "rebuilding data-code on the juniper-data main that already holds the data-docs carrier",
        "edits": [
            {
                "id": "E1-when-a-window-ends-rounds-up",
                "required": True,
                "file": REF,
                "section": "## Failed-Auth Throttle Retention > ### When a window ends",
                "old": OLD,
                "new": NEW,
                "old_must_occur": 1,
                "reason": "security.py's FailedAuthThrottle.check returns max(1, math.ceil(remaining)) in data-code; the sentence data-docs carries describes main's max(1, int(...)).",
            }
        ],
        "optional_edits": [
            {
                "id": "E2-pins-row-for-the-throttle-round-up",
                "required": False,
                "file": REF,
                "section": "## Failed-Auth Throttle Retention > ### Pins (on `main`)",
                "insert_after": PIN_ANCHOR,
                "old": PIN_ANCHOR,
                "new": PIN_ANCHOR + PIN_ROW,
                "old_must_occur": 1,
                "reason": "data-claims-lens F1's optional suggestion: name data-code's TestFailedAuthThrottleRoundsUp in the section's own Pins table (§ Non-ASCII API Keys step 2 already names it).",
            }
        ],
        "also_in_this_carrier": "data-code's CHANGELOG.md and pr_body.txt already list § Failed-Auth Throttle Retention among the sections it changes (claims F1); that is true once E1 is applied.",
        "stamps": "data-claims-lens F5: not re-bumped here; the orchestrator re-derives docs/REFERENCE.md's and docs/DEVELOPER_CHEATSHEET.md's stamps from that main at the rebuild.",
        "verified_against": {
            "main_sha": sha,
            "data_docs_reference_sha256": hashlib.sha256(docs_text.encode("utf-8")).hexdigest(),
            "data_tests_reference_sha256": hashlib.sha256((tests_wt / REF).read_bytes()).hexdigest(),
            "data_code_reference_sha256": hashlib.sha256((code_wt / REF).read_bytes()).hexdigest(),
        },
        "checks": checks,
        "all_checks_pass": ok,
    }
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=1))
    print(f"all_checks_pass={ok} -> {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
