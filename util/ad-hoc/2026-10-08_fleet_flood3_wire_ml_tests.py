#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_wire_ml_tests.py -- register harvested juniper-ml suites in all three hand-maintained lists.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-09-05_wire_harvested_test.py` (round 2's wirer, which predates the 2026-09-10 relocation)

WHY THIS EXISTS

juniper-ml's regression inventory is hand-maintained, and since the 2026-09-10 structure repair it
lives in THREE places, none of which a new test file registers itself in:

    .github/workflows/ci.yml   `Run Python regression tests` -- the authoritative list (a comment + an invocation)
    docs/REFERENCE.md          `### Running every suite` -- the ordered copy of that list, in a ```bash block
    docs/REFERENCE.md          `## Test Suite Reference` -- one `- `tests/...` -- description` entry per suite

Round 2's `2026-09-05_wire_harvested_test.py` still targets `AGENTS.md`, which no longer holds the run
list (it relocated to REFERENCE.md), and it never touches the `Running every suite` block -- so a suite
it wires is invoked by CI and absent from the operator's copy, which is exactly the drift
`util/ad-hoc/2026-09-10_agents_md_test_list_drift.py` reports.

A fleet PR's own versions of these files cannot be taken: each was written against a stale base and
would revert what concurrent sessions added since. The registration is re-derived against the tree
this runs in. Every suite is APPENDED to the end of each list, in input order, so the run-list copy
keeps ci.yml's order.

IDEMPOTENT: a suite already present in a list is left alone there.

Input (`--spec`): a JSON list of objects
    {"test": "tests/test_x.py", "ci_comment": "one line or several, no leading '#'", "desc": "Test Suite Reference text"}

Usage (run from the juniper-ml worktree root):
    2026-10-08_fleet_flood3_wire_ml_tests.py --spec <json> [--check]

Exit: 0 when every suite is present in all three lists afterwards; 1 when an anchor is missing or a
      suite is still absent somewhere (with --check, nothing is written); 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CI = Path(".github/workflows/ci.yml")
REFERENCE = Path("docs/REFERENCE.md")
CI_STEP = "      - name: Run Python regression tests"
CI_INVOKE = "          python3 -m unittest -v "
RUN_HEADING = "### Running every suite"
REF_SECTION = "## Test Suite Reference"


def _ci(text: str, suites: list[dict]) -> tuple[str, list[str]]:
    notes: list[str] = []
    start = text.find(CI_STEP)
    if start < 0:
        return text, ["ci.yml: regression step NOT FOUND"]
    nxt = text.find("\n      - name: ", start + len(CI_STEP))
    end = nxt if nxt >= 0 else len(text)
    block = text[start:end]
    last = block.rfind(CI_INVOKE + "tests/")
    if last < 0:
        return text, ["ci.yml: no unittest invocation in the regression step"]
    insert_at = start + block.index("\n", last) + 1
    add = ""
    for s in suites:
        line = f"{CI_INVOKE}{s['test']}"
        if re.search(rf"^{re.escape(line)}\s*$", block, re.M):
            notes.append(f"ci.yml: {s['test']} already invoked")
            continue
        comment_lines = [ln.rstrip() for ln in s["ci_comment"].strip().splitlines() if ln.strip()]
        if comment_lines and not comment_lines[0].startswith(s["test"]):
            comment_lines[0] = f"{s['test']}: {comment_lines[0]}"
        add += "".join(f"          # {ln}\n" for ln in comment_lines) + line + "\n"
        notes.append(f"ci.yml: {s['test']} wired")
    return text[:insert_at] + add + text[insert_at:], notes


def _run_list(text: str, suites: list[dict]) -> tuple[str, list[str]]:
    h = text.find(RUN_HEADING)
    if h < 0:
        return text, ["REFERENCE.md: `Running every suite` NOT FOUND"]
    fence = text.find("```bash\n", h)
    close = text.find("\n```", fence + 8)
    if fence < 0 or close < 0:
        return text, ["REFERENCE.md: run-list code block NOT FOUND"]
    block = text[fence:close]
    # Append after the LAST unittest line, not before the fence: the block ends with the bash suite
    # and a doc-tools comment, and a suite appended below those reads as part of that comment.
    last = block.rfind("\npython3 -m unittest -v tests/")
    if last < 0:
        return text, ["REFERENCE.md: no unittest line in the run-list block"]
    eol = fence + block.index("\n", last + 1)
    add = ""
    notes = []
    for s in suites:
        line = f"python3 -m unittest -v {s['test']}"
        if re.search(rf"^{re.escape(line)}\s*$", block, re.M):
            notes.append(f"REFERENCE run list: {s['test']} already listed")
            continue
        add += "\n" + line
        notes.append(f"REFERENCE run list: {s['test']} listed")
    return text[:eol] + add + text[eol:], notes


def _descriptions(text: str, suites: list[dict]) -> tuple[str, list[str]]:
    sec = text.find("\n" + REF_SECTION + "\n")
    if sec < 0:
        return text, ["REFERENCE.md: `## Test Suite Reference` NOT FOUND"]
    nxt = text.find("\n## ", sec + 1 + len(REF_SECTION))
    end = nxt if nxt >= 0 else len(text)
    section = text[sec:end]
    last = section.rfind("\n- `tests/")
    if last < 0:
        return text, ["REFERENCE.md: no `- `tests/` entry in the Test Suite Reference"]
    insert_at = sec + section.index("\n", last + 1) + 1
    add = ""
    notes = []
    for s in suites:
        if f"\n- `{s['test']}` " in section:
            notes.append(f"REFERENCE descriptions: {s['test']} already described")
            continue
        desc = " ".join(s["desc"].split())
        add += f"- `{s['test']}` -- {desc}\n"
        notes.append(f"REFERENCE descriptions: {s['test']} described")
    return text[:insert_at] + add + text[insert_at:], notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args(argv)
    try:
        suites = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        assert isinstance(suites, list) and suites
        for s in suites:
            assert isinstance(s, dict) and {"test", "ci_comment", "desc"} <= set(s), s
            assert re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", s["test"]), s["test"]
            assert Path(s["test"]).is_file(), f"{s['test']} is not in this tree"
    except (OSError, ValueError, AssertionError) as exc:
        print(f"bad --spec: {exc}", file=sys.stderr)
        return 2

    ci_text = CI.read_text(encoding="utf-8")
    ref_text = REFERENCE.read_text(encoding="utf-8")
    ci_new, n1 = _ci(ci_text, suites)
    ref_new, n2 = _run_list(ref_text, suites)
    ref_new, n3 = _descriptions(ref_new, suites)
    for note in n1 + n2 + n3:
        print(note)
    # Every success note names its suite; an anchor failure names none, so it cannot be mistaken for one.
    named = {s["test"] for s in suites}
    bad = [n for n in n1 + n2 + n3 if not any(t in n for t in named)]
    if bad:
        return 1
    if not args.check:
        CI.write_text(ci_new, encoding="utf-8")
        REFERENCE.write_text(ref_new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
