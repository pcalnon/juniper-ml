#!/usr/bin/env python3
"""
Write the edits file for the ml-propose PR body at its landing on juniper-ml main 16f2512b.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, landing)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: landing the ml-propose carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-propose-r3b-quick-s7/text_fixes.json (session 7's six fixes, K2);
         util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py (applies the file this writes, all or nothing)

K2's fixes 1, 3, 4 and 6 are taken verbatim. Fix 2 is rewritten from session 8's measurements on the landing tree at
16f2512b (tmp/flood4/session8/land/ml-propose/: land.stdout, check5.stdout, sim.stdout, seqsafety.stdout,
precommit.log, ci_list_D.txt, fail4_vs_clean_main.json). Fix 5 is reworded for juniper-ml#2558 merged: its squash's
docs/REFERENCE.md diff is d4dcefbc's exactly (blobs 789a982d..40dabb91), and 8764f5cf changes no line of that file.

Usage: python3 <this> [--landing-dir <dir>] [--main <sha8> --commits N --movers '#A, #B and #C' --mover-count N
       --removed '<what the landing removes>' --docs-warnings N --ci-suites N --ci-pass N --gate-sha <sha8>]
Without arguments it writes the 16f2512b edits of 2026-11-15 00:20Z (tmp/flood4/session8/land/ml-propose/). With
--landing-dir it copies <dir>/land/texts/ to <dir>/texts_s8/ and writes <dir>/body_edits.json for that landing.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
K2 = ROOT / "tmp/flood4r2-val/ml-propose-r3b-quick-s7/text_fixes.json"

FIX2_TEMPLATE = (
    "and every check below except the full mutation run was made again there. Since then `main` has gained {commits} commits, to `{main}`; "
    "{mover_count_word} of them change `CHANGELOG.md` or `docs/REFERENCE.md`: {movers}. "
    "The 22 files were landed on `{main}` with the landing command: both documents rebuilt three-way with no conflict, the runbook's stamp "
    "re-dated, the other 19 files byte for byte. The three-way filed the CHANGELOG entry under the released `## [0.11.5]` heading, so the entry "
    "was moved to the end of `## [Unreleased]`'s `### Fixed`; the rest of `CHANGELOG.md` is `main`'s, byte for byte. Measured on that tree: "
    "the propose suite, 188 tests OK on Python 3.12.11 and 3.14.7 (`propose.py` and its test file are unchanged on `main` since `15b5d9bb`); "
    "the pristine, patch (0.11.5 -> 0.11.6) and minor (0.11.5 -> 0.12.0) rows of the table below, with the tests carrier's gate file "
    "(sha256 `{gate_sha}`): the unextended script's patch proposal fails 3 of the 8 and its minor proposal 4, and with this PR the 8, the 20 "
    "and the 188 pass after both; no line that any of those {mover_count_word} commits added is removed, except {removed}; the pinned "
    "pre-commit on the 22 files (17 hooks pass, 9 are skipped, no file is modified); CI's two "
    "sequence-safety screens, which pass with no waiver (the symbol screen finds nothing in 19 files; the docs screen gives {docs_warnings_word} "
    "small-deletion warnings in 2 files); and CI's regression list, {ci_suites} suites there: {ci_pass} pass, and the four that fail "
    "(`tests/test_a0_restore_scripts.py`, `tests/test_e2e_f037_render_census.py`, `tests/test_replay_redrive_stack_refusal.py`, "
    "`tests/test_workflow_script_paths.py`) fail the same tests in a clean `{main}` worktree on this host."
)
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
DEFAULTS_16F2512B = {
    "main": "16f2512b", "commits": 18, "movers": "juniper-ml#2554, #2555, #2557, #2558 (the 0.11.5 release proposal) and #2548",
    "mover_count": 5, "removed": "`docs/REFERENCE.md`'s `**Version:**` and `**Last Updated:**` stamp lines", "docs_warnings": 4,
    "ci_suites": 242, "ci_pass": 238, "gate_sha": "1ee53200",
}

FIX5_NEW = (
    "and the REVIEW line does not name them: it asks about the history in general and names the renamed clause. juniper-ml#2558, the 0.11.5 "
    "release proposal (merged on 2026-11-13 as `48b66130`), was built by the unextended script. Its generated commit (`8764f5cf`) changes no "
    "line of `docs/REFERENCE.md`. Its second commit (`d4dcefbc`), whose two `docs/REFERENCE.md` lines are exactly what the merge carried, sets "
    "by hand the Version cell that this PR's propose.py writes, byte for byte, and makes the same two renames in the paragraph; it also rewords "
    "the raise's words and the words after the clause's pins, which the script never writes."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--landing-dir", type=Path)
    for name in ("main", "movers", "removed", "gate_sha"):
        parser.add_argument("--" + name.replace("_", "-"), dest=name)
    for name in ("commits", "mover_count", "docs_warnings", "ci_suites", "ci_pass"):
        parser.add_argument("--" + name.replace("_", "-"), dest=name, type=int)
    args = parser.parse_args()
    values = dict(DEFAULTS_16F2512B)
    if args.landing_dir:
        missing = [k for k in values if getattr(args, k) is None]
        if missing:
            print("REFUSED: --landing-dir needs every figure; missing: " + ", ".join(missing))
            return 1
        values = {k: getattr(args, k) for k in values}
        landing = args.landing_dir.resolve()
        texts = landing / "texts_s8"
        if texts.exists():
            print(f"REFUSED: {texts} exists; remove it to rebuild from {landing / 'land/texts'}")
            return 1
        shutil.copytree(landing / "land" / "texts", texts)
        body = str((texts / "pr_body.txt").relative_to(ROOT))
        out = landing / "body_edits.json"
    else:
        body = "tmp/flood4/session8/land/ml-propose/texts_s8/pr_body.txt"
        out = ROOT / "tmp/flood4/session8/land/ml-propose/body_edits.json"
    values["mover_count_word"] = WORDS[values["mover_count"]]
    values["docs_warnings_word"] = WORDS.get(values["docs_warnings"], str(values["docs_warnings"]))
    fix2_new = FIX2_TEMPLATE.format(**values)
    k2 = json.loads(K2.read_text(encoding="utf-8"))
    BODY = body
    OUT = out
    edits = [
        {"id": "K2-fix1-F3", "file": BODY, "old": k2[0]["old"], "new": k2[0]["new"]},
        {"id": f"S8-fix2-F4-on-{values['main']}", "file": BODY, "old": "and every check below except the full mutation run was made again there.", "new": fix2_new},
        {"id": "K2-fix3-F5", "file": BODY, "old": k2[2]["old"], "new": k2[2]["new"]},
        {"id": "K2-fix4-F6", "file": BODY, "old": k2[3]["old"], "new": k2[3]["new"]},
        {"id": "S8-fix5-F6-merged", "file": BODY, "old": k2[4]["old"], "new": FIX5_NEW},
        {"id": "K2-fix6-F7", "file": BODY, "old": k2[5]["old"], "new": k2[5]["new"]},
    ]
    doc = {
        "worktree": str(ROOT),
        "why": "flood-4 session 8: the ml-propose PR body at its landing on main 16f2512b (K2's six fixes; fix 2 rewritten from session 8's measurements, fix 5 reworded for #2558 merged).",
        "edits": edits,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(edits)} edits -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
