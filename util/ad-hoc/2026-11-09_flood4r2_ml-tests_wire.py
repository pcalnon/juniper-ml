#!/usr/bin/env python3
"""2026-11-09_flood4r2_ml-tests_wire.py -- register new juniper-ml suites in ci.yml, main-verify.yml and docs/REFERENCE.md.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: `2026-11-07_flood4_wire_ml_tests.py` (round 1's wirer, which this copies)

WHAT CHANGED AGAINST ROUND 1'S WIRER

1. A Test Suite Reference entry placed after a sibling goes after the sibling's WHOLE block: round 1
   inserted after the sibling's first line, which would split an entry from its indented sub-bullets
   (`tests/test_predict_merge.py` has one).
2. `desc_after` may name a different sibling for the description than `after` names for the two
   ordered lists (a suite with no description of its own cannot anchor one).
3. `mv_after` registers the suite in main-verify.yml's `Run Python regression battery` step too, after
   that suite's line, with an optional `mv_comment`. main-verify's battery is a partial mirror of ci.yml
   (no gate compares them), so only suites whose draft registered them there are given an `mv_after`.
   A missing main-verify anchor is an error, never an append.

Everything else is round 1's: ci.yml's `Run Python regression tests` step is the authoritative list
(a comment + an invocation); docs/REFERENCE.md `### Running every suite` is its ordered copy; the
`## Test Suite Reference` gets one `- `tests/...` -- description` entry per suite. IDEMPOTENT: a suite
already present in a list is left alone there.

Input (`--spec`): a JSON list of objects
    {"test": "tests/test_x.py", "ci_comment": "...", "desc": "...", "after": "tests/test_y.py",
     "desc_after": "tests/test_z.py", "mv_after": "tests/test_w.py", "mv_comment": "..."}

Usage (run from the juniper-ml worktree root):
    2026-11-09_flood4r2_ml-tests_wire.py --spec <json> [--check]

Exit: 0 when every suite is present in every list it targets afterwards; 1 when an anchor is missing
      or a suite is still absent somewhere (with --check, nothing is written); 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CI = Path(".github/workflows/ci.yml")
MV = Path(".github/workflows/main-verify.yml")
REFERENCE = Path("docs/REFERENCE.md")
CI_STEP = "      - name: Run Python regression tests"
MV_STEP = "      - name: Run Python regression battery"
INVOKE = "          python3 -m unittest -v "
RUN_HEADING = "### Running every suite"
REF_SECTION = "## Test Suite Reference"
_SUITE = r"tests/test_[A-Za-z0-9_]+\.py"


def _step_block(text: str, step: str) -> tuple[int, int]:
    start = text.find(step)
    if start < 0:
        return -1, -1
    nxt = text.find("\n      - name: ", start + len(step))
    return start, (nxt if nxt >= 0 else len(text))


def _workflow(text: str, suites: list[dict], step: str, after_key: str, comment_key: str, label: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    for s in suites:
        if after_key == "mv_after" and "mv_after" not in s:
            continue
        start, end = _step_block(text, step)
        if start < 0:
            return text, [f"{label}: step {step.strip()!r} NOT FOUND"]
        block = text[start:end]
        line = f"{INVOKE}{s['test']}"
        if re.search(rf"^{re.escape(line)}[ \t]*$", block, re.M):
            notes.append(f"{label}: {s['test']} already invoked")
            continue
        after = s.get(after_key)
        anchor = re.search(rf"^{re.escape(INVOKE + after)}[ \t]*$", block, re.M) if after else None
        if anchor:
            insert_at = start + anchor.end() + 1
        elif after_key == "mv_after":
            notes.append(f"{label}: anchor {after!r} NOT FOUND")
            continue
        else:
            last = block.rfind(INVOKE + "tests/")
            if last < 0:
                return text, [f"{label}: no unittest invocation in the step"]
            insert_at = start + block.index("\n", last) + 1
        comment_lines = [ln.rstrip() for ln in (s.get(comment_key) or "").strip().splitlines() if ln.strip()]
        add = "".join(f"          # {ln}\n" for ln in comment_lines) + line + "\n"
        text = text[:insert_at] + add + text[insert_at:]
        notes.append(f"{label}: {s['test']} wired" + (" after " + after if anchor else " at the end"))
    return text, notes


def _run_list(text: str, suites: list[dict]) -> tuple[str, list[str]]:
    notes: list[str] = []
    for s in suites:
        h = text.find(RUN_HEADING)
        if h < 0:
            return text, ["REFERENCE.md: `Running every suite` NOT FOUND"]
        fence = text.find("```bash\n", h)
        close = text.find("\n```", fence + 8)
        if fence < 0 or close < 0:
            return text, ["REFERENCE.md: run-list code block NOT FOUND"]
        block = text[fence:close]
        line = f"python3 -m unittest -v {s['test']}"
        if re.search(rf"^{re.escape(line)}\s*$", block, re.M):
            notes.append(f"REFERENCE run list: {s['test']} already listed")
            continue
        anchor = re.search(rf"^python3 -m unittest -v {re.escape(s['after'])}[ \t]*$", block, re.M) if s.get("after") else None
        if anchor:
            eol = fence + anchor.end()
        else:
            last = block.rfind("\npython3 -m unittest -v tests/")
            if last < 0:
                return text, ["REFERENCE.md: no unittest line in the run-list block"]
            eol = fence + block.index("\n", last + 1)
        text = text[:eol] + "\n" + line + text[eol:]
        notes.append(f"REFERENCE run list: {s['test']} listed" + (" after " + s["after"] if anchor else " at the end"))
    return text, notes


def _end_of_entry(section: str, start: int) -> int:
    """Index just past the entry that starts at ``start`` (a ``\\n- `` line), including its indented continuation lines."""
    pos = section.index("\n", start + 1) + 1
    while pos < len(section) and section.startswith("  ", pos):
        nl = section.find("\n", pos)
        pos = (nl + 1) if nl >= 0 else len(section)
    return pos


def _descriptions(text: str, suites: list[dict]) -> tuple[str, list[str]]:
    notes: list[str] = []
    for s in suites:
        sec = text.find("\n" + REF_SECTION + "\n")
        if sec < 0:
            return text, ["REFERENCE.md: `## Test Suite Reference` NOT FOUND"]
        nxt = text.find("\n## ", sec + 1 + len(REF_SECTION))
        end = nxt if nxt >= 0 else len(text)
        section = text[sec:end]
        if f"\n- `{s['test']}` " in section:
            notes.append(f"REFERENCE descriptions: {s['test']} already described")
            continue
        sibling = s.get("desc_after") or s.get("after")
        sib = section.find(f"\n- `{sibling}` ") if sibling else -1
        if sib >= 0:
            insert_at = sec + _end_of_entry(section, sib)
        else:
            last = section.rfind("\n- `tests/")
            if last < 0:
                return text, ["REFERENCE.md: no `- `tests/` entry in the Test Suite Reference"]
            insert_at = sec + _end_of_entry(section, last)
        desc = " ".join(s["desc"].split())
        text = text[:insert_at] + f"- `{s['test']}` -- {desc}\n" + text[insert_at:]
        notes.append(f"REFERENCE descriptions: {s['test']} described" + (" after " + sibling if sib >= 0 else " at the end"))
    return text, notes


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
            assert re.fullmatch(_SUITE, s["test"]), s["test"]
            assert Path(s["test"]).is_file(), f"{s['test']} is not in this tree"
            for key in ("after", "desc_after", "mv_after"):
                assert key not in s or re.fullmatch(_SUITE, s[key]), (key, s.get(key))
    except (OSError, ValueError, AssertionError) as exc:
        print(f"bad --spec: {exc}", file=sys.stderr)
        return 2

    ci_new, n1 = _workflow(CI.read_text(encoding="utf-8"), suites, CI_STEP, "after", "ci_comment", "ci.yml")
    mv_new, n2 = _workflow(MV.read_text(encoding="utf-8"), suites, MV_STEP, "mv_after", "mv_comment", "main-verify.yml")
    ref_new, n3 = _run_list(REFERENCE.read_text(encoding="utf-8"), suites)
    ref_new, n4 = _descriptions(ref_new, suites)
    notes = n1 + n2 + n3 + n4
    for note in notes:
        print(note)
    # Every success note names its suite and no failure note does: an anchor failure says NOT FOUND.
    named = {s["test"] for s in suites}
    bad = [n for n in notes if "NOT FOUND" in n or not any(t in n for t in named)]
    if bad:
        return 1
    if not args.check:
        CI.write_text(ci_new, encoding="utf-8")
        MV.write_text(mv_new, encoding="utf-8")
        REFERENCE.write_text(ref_new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
