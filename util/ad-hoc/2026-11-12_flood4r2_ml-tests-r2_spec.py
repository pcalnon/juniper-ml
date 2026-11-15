#!/usr/bin/env python3
"""
Derive round 2's wiring spec for the flood-4 "ml-tests" carrier from round 1's, for the main it now lands on.

Round 1 registered its fifteen suites on a main that did not hold the code carrier (juniper-ml#2554). That
carrier registered five suites after the same anchors, so each list would now interleave the two carriers. The
rule taken from round 1's own landing note: the code carrier's suites stay first, this carrier's follow them. So
four anchors move to the code carrier's suite that now sits after the old anchor; the other anchors, and every
comment and description, are round 1's.

The output is the `--spec` of `2026-11-09_flood4r2_ml-tests_wire.py`, which re-derives the registrations in
ci.yml, main-verify.yml and docs/REFERENCE.md. This script refuses when an anchor it names is not a suite of the
tree it runs in, or when round 1's spec does not hold a suite it overrides.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_spec.py --round1-spec <json> --out <json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_wire.py; juniper-ml#2554
"""

import argparse
import json
import sys
from pathlib import Path

# suite -> the keys of round 1's entry that change, and why.
OVERRIDES = {
    "tests/test_claude_agent_guard_nest_depth.py": {
        "after": "tests/test_claude_agent_guard_push_signed_abbrev.py",  # was test_claude_agent_guard_brace_cap.py; #2554's two abbreviation suites follow it
    },
    "tests/test_launcher_empty_version_output.py": {
        "after": "tests/test_prompt_file_later_flag.py",  # was test_wake_the_claude.py; #2554's suite follows it
        "mv_after": "tests/test_prompt_file_later_flag.py",
    },
    "tests/test_launcher_prompt_and_version_edges.py": {
        "after": "tests/test_claudey_empty_prompt_file_env.py",  # was test_claude_interactive.py; #2554's suite follows it
    },
    "tests/test_predict_merge_scratch_edges.py": {
        "after": "tests/test_predict_merge_inherited_git_env.py",  # was test_predict_merge.py; #2554's suite follows it
    },
}
ANCHOR_KEYS = ("after", "desc_after", "mv_after")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--round1-spec", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.round1_spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    by_test = {entry["test"]: entry for entry in spec}
    missing = sorted(set(OVERRIDES) - set(by_test))
    if missing:
        print(f"round 1's spec lacks {missing}", file=sys.stderr)
        return 1
    changed = []
    for suite, keys in OVERRIDES.items():
        for key, value in keys.items():
            changed.append(f"{suite}: {key} {by_test[suite].get(key)} -> {value}")
            by_test[suite][key] = value
    carried = {entry["test"] for entry in spec}
    bad = []
    for entry in spec:
        if not Path(entry["test"]).is_file():
            bad.append(f"{entry['test']} is not in this tree")
        for key in ANCHOR_KEYS:
            anchor = entry.get(key)
            if anchor and anchor not in carried and not Path(anchor).is_file():
                bad.append(f"{entry['test']}: {key} {anchor} is not in this tree")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
        fh.write("\n")
    print(f"{len(spec)} suites; {len(changed)} anchors moved:")
    print("\n".join("  " + line for line in changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
