#!/usr/bin/env python3
"""
Re-prove the docs carrier's file:line citations on today's main: each cited window must contain what the claim says.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier finish, session 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2);
         util/ad-hoc/2026-11-12_flood4r2_ml-docs_manifest.py (the claims table these windows come from)

Each fact names a file, an inclusive line window (the citation the claims table gives) and a regular expression
the window must match. A miss prints the window, so a wrong citation is corrected rather than kept. Existence facts
check that a path is (or is not) a file. The results go to one JSON report.

Usage: 2026-11-14_flood4r2_ml-docs_cite_check.py --repo <tree> --out <json>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WAKE = "scripts/wake_the_claude.bash"
CLAUDEY = "scripts/claude_interactive.bash"
SESSION = "scripts/default_interactive_session_claude_code.bash"
SLC = "juniper-ci-tools/juniper_ci_tools/symbol_loss_check.py"
DAC = "juniper-ci-tools/juniper_ci_tools/docs_additions_check.py"
PM = "util/fleet_triage/predict_merge.py"
GUARD = "util/claude_agent_guard.py"
RERUN = "util/ad-hoc/2026-10-05_rerun_after_actions_outage.py"
LANE = "util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py"
MATRIX = "util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py"

FACTS = [
    ("claudey-booleans", CLAUDEY, 43, 44, r'TRUE="0"[\s\S]*FALSE="1"'),
    ("wake-booleans", WAKE, 104, 105, r'TRUE="0"[\s\S]*FALSE="1"'),
    ("claudey-version", CLAUDEY, 49, 49, r"0\.2\.0"),
    ("claudey-default-model-opus", CLAUDEY, 95, 111, r'(?m)MODEL_OPUS_ALIAS="opus"[\s\S]*^export DEFAULT_MODEL="\$\{MODEL_OPUS_ALIAS\}"'),
    ("claudey-default-effort-max", CLAUDEY, 100, 116, r'(?m)MAX="max"[\s\S]*^export DEFAULT_EFFORT="\$\{MAX\}"'),
    ("claudey-remote-control-aliases", CLAUDEY, 218, 219, r"--remote-control-session"),
    ("wake-version", WAKE, 121, 123, r"1\.1\.0"),
    ("wake-effort-default-max", WAKE, 255, 262, r'(?m)^EFFORT_MAX="max"[\s\S]*^EFFORT_DEFAULT="\$\{EFFORT_MAX\}"'),
    ("wake-effort-no-auto-comment", WAKE, 255, 262, r"(?i)auto"),
    ("wake-effort-aliases", WAKE, 361, 361, r"--effort-type[\s\S]*--effort-level|--effort-level[\s\S]*--effort-type"),
    ("wake-tmp-error", WAKE, 1849, 1851, r"cannot create juniper-ml's tmp/"),
    ("wake-nohup-error", WAKE, 1888, 1889, r"Failed to open nohup log file"),
    ("session-effort-high", SESSION, 22, 31, r"--effort[ =\"']+high|high"),
    ("session-skip-permissions", SESSION, 22, 31, r"CLAUDE_SKIP_PERMISSIONS"),
    ("slc-constants", SLC, 72, 73, r"WEAKEN_RATIO\s*=\s*0\.6[\s\S]*WEAKEN_MIN_DELTA\s*=\s*4"),
    ("slc-both-arms-inclusive", SLC, 368, 372, r"<=[\s\S]*>=|>=[\s\S]*<="),
    ("slc-bash-line-count", SLC, 304, 311, r"len\(|max\(1|- start|end"),
    ("slc-waives-kind-prefix", SLC, 436, 446, r"partition\(\":\"\)|split\(\":\", 1\)|\":\""),
    ("slc-tests-three-names", "juniper-ci-tools/tests/test_symbol_loss_check.py", 170, 212, r"test_weakened_shrink_past_threshold_fails[\s\S]*test_small_shrink_below_threshold_is_not_flagged|test_small_shrink_below_threshold_is_not_flagged[\s\S]*test_weakened_shrink_past_threshold_fails"),
    ("slc-test-same-length", "juniper-ci-tools/tests/test_symbol_loss_check.py", 170, 212, r"test_same_length_gutting_is_invisible_blind_spot"),
    ("dac-min-run-default-5", DAC, 1, 80, r"min[-_]run[\s\S]{0,120}\b5\b|\b5\b[\s\S]{0,120}min[-_]run"),
    ("lane-version", LANE, 8, 8, r"0\.3\.1"),
    ("lane-min-nonzero-none", LANE, 249, 254, r"none \(no column has a std > 0\)[\s\S]*min-nonzero=\{min_nonzero_text\}"),
    ("lane-min-nonzero-null", LANE, 205, 215, r"X_last_step_std_min_nonzero\"\] = .* else None"),
    ("matrix-e-h-cv", MATRIX, 74, 74, r"E_H_CV"),
    ("rerun-version", RERUN, 8, 8, r"0\.3\.0"),
    ("rerun-actions-exact", RERUN, 40, 80, r"\"Actions\""),
    ("rerun-operational-degraded", RERUN, 60, 100, r"operational[\s\S]*degraded_performance|degraded_performance[\s\S]*operational"),
    ("rerun-status-url", RERUN, 45, 45, r"githubstatus\.com/api/v2/components\.json"),
    ("rerun-defaults-and-exclusive", RERUN, 90, 102, r"default=120[\s\S]*default=4 \* 3600[\s\S]*mutually_exclusive_group\(required=True\)"),
    ("pm-hooks-ruff", PM, 95, 99, r"ruff-format"),
    ("pm-nine-vars", PM, 133, 148, r"GIT_SHALLOW_FILE[\s\S]*GIT_GRAFT_FILE|GIT_GRAFT_FILE[\s\S]*GIT_SHALLOW_FILE"),
    ("pm-lfs-skip-smudge", PM, 145, 160, r"GIT_LFS_SKIP_SMUDGE"),
    ("pm-errors-replace", PM, 145, 160, r"errors=\"replace\""),
    ("pm-docs-screen-cli", PM, 240, 282, r"juniper-docs-additions-check"),
    ("pm-docs-screen-files", PM, 240, 282, r"--files"),
    ("pm-scratch-dir", PM, 350, 360, r"fleet-triage-"),
    ("pm-filter-attributes", PM, 362, 370, r"\* -filter"),
    ("pm-shallow-copy", PM, 366, 375, r"shallow"),
    ("pm-merge-exit-error", PM, 424, 432, r"PredictMergeError"),
    ("pm-is-heal-branch-prefixes", PM, 528, 556, re.escape('_HEAL_BRANCH_RE = re.compile(r"^(?:fix|heal|hotfix)/", re.IGNORECASE)')),
    ("pm-is-heal-title-prefixes", PM, 528, 556, re.escape('_HEAL_TITLE_RE = re.compile(r"^\\s*(?:fix\\(|fix:|heal\\b)", re.IGNORECASE)')),
    ("guard-version-1.3.0", GUARD, 183, 183, re.escape('__version__ = "1.3.0"')),
    ("guard-exact-allowed-export", GUARD, 286, 290, re.escape('GPG_EXACT_ALLOWED = ("export",)')),
    ("guard-min-abbrev-2", GUARD, 286, 291, r"GPG_MIN_ABBREV\s*=\s*2"),
    ("guard-max-brace-64", GUARD, 186, 192, r"MAX_BRACE_ALTERNATIVES\s*=\s*64"),
    ("guard-tests-gpg-cases", "tests/test_claude_agent_guard.py", 346, 406, r'GPG_CASES = \[[\s\S]*"gpg --cl", GPG_SIGN[\s\S]*"gpg --e KEYID", None[\s\S]*"gpg --li", GPG_SECRET'),
    ("pm-tests-heal", "tests/test_predict_merge.py", 668, 702, r"(?i)heal|hotfix"),
    ("main-verify-docs-screen", ".github/workflows/main-verify.yml", 250, 262, r"juniper-docs-additions-check"),
]
EXISTS = [
    ("slc-gate-in-ci-tools", "juniper-ci-tools/tests/test_symbol_loss_check.py", True),
    ("dac-gate-in-ci-tools", "juniper-ci-tools/tests/test_docs_additions_check.py", True),
    ("slc-gate-not-in-tests", "tests/test_symbol_loss_check.py", False),
    ("dac-gate-not-in-tests", "tests/test_docs_additions_check.py", False),
    ("claudey-env-suite", "tests/test_claudey_empty_prompt_file_env.py", True),
    ("later-flag-suite", "tests/test_prompt_file_later_flag.py", True),
    ("inherited-git-env-suite", "tests/test_predict_merge_inherited_git_env.py", True),
]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    rows = []
    for name, path, start, end, pattern in FACTS:
        lines = (args.repo / path).read_text(encoding="utf-8", errors="replace").splitlines()
        window = "\n".join(lines[start - 1:end])
        found = re.search(pattern, window) is not None
        rows.append({"fact": name, "path": path, "lines": f"{start}-{end}", "pattern": pattern, "ok": found, "window": None if found else window})
        print(f"{'ok  ' if found else 'MISS'} {name}: {path}:{start}-{end}")
        if not found:
            print("      " + window.replace("\n", "\n      ")[:1200])
    for name, path, expected in EXISTS:
        found = (args.repo / path).is_file() == expected
        rows.append({"fact": name, "path": path, "expect_file": expected, "ok": found})
        print(f"{'ok  ' if found else 'MISS'} {name}: {path} is_file == {expected}")
    misses = sum(1 for row in rows if not row["ok"])
    args.out.write_text(json.dumps({"repo": str(args.repo), "facts": len(rows), "misses": misses, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} facts, {misses} misses")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
