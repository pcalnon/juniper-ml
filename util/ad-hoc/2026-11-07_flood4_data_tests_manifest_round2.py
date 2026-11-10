#!/usr/bin/env python3
"""
Fold the validator round (T-F1..T-F4) into the juniper-data flood-4 tests carrier's manifest.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier, validator round)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/data/val-tests/findings.json; flood-4 common brief

Edits the manifest in place: per-PR fixes and outcomes for #513/#514/#516, the round-2 check results,
the validator_round record, and the T-F2 note on #512. Asserts the keys it edits exist.

    python3 2026-11-07_flood4_data_tests_manifest_round2.py <manifest.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRATCH = str(Path.home() / "Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert/tmp/flood4/data")
SHELL_FIX = (
    "Validator T-F1: the harness ran the step under `bash -eo pipefail` and its docstring called that GitHub's default. "
    "A run: step that names no shell runs as `bash -e {0}` (GitHub's workflow-syntax shell table; the v0.17.1 Publish manifest job log "
    "shows `shell: /usr/bin/bash -e {0}` for all four rehearsed steps, val-tests/ci_publish_manifest_v0.17.1_job_114308353499.log:646,715,760,836; "
    "publish-image.yml has no defaults:/shell:). `shell: bash` is what adds pipefail. The harness now runs `bash -e -c`, and the docstring/comment say so "
    "(a named shell would stop the rehearsal matching the runner)."
)


def main(argv: list[str]) -> int:
    path = Path(argv[1])
    with path.open(encoding="utf-8") as fh:
        m = json.load(fh)
    by_pr = {c["pr"]: c for c in m["carried"]}
    assert set(by_pr) == {512, 513, 514, 516, 517}
    m["worktree_state"] = "detached HEAD at base_sha; changes STAGED in the worktree's own index (git add -A), never committed. Round 2 (validator fixes) re-staged: tree d0fd0040c8b8b4d76ce172f419f1960f37430984."
    by_pr[512]["reason"] += " Validator T-F2 (kept as drafted, per the orchestrator): 6 of the 7 parametrize rows add nothing -- every row runs the same two workflow-binding asserts, and the other two restate the table itself. Padding, not vacuity."
    by_pr[513]["fixes"] = [SHELL_FIX + " test_publish_image_manifest_identity.py:127 argv; :138 docstring."]
    by_pr[513]["outcome"] = "carried-with-fix"
    by_pr[513]["reason"] = "Required checks green incl. macOS (triage); content TRUE; 8 pass alone under `bash -e`; mutant M4 killed. Carrier differs from the head blob only by the T-F1 fix."
    by_pr[514]["fixes"].append(SHELL_FIX + " test_publish_manifest_tag_gates.py:15-17 docstring, :74-75 comment, :161 argv.")
    by_pr[514]["fixes"].append("Validator T-F4: the bash lookup now calls pytest.fail, not pytest.skip, when /usr/bin:/bin has no bash. A skip would let 10 of its 12 tests skip on a required lane while the lane read green; bash is present on every runner.")
    by_pr[514]["reason"] = "Content TRUE on main (12 pass under `bash -e`; mutant M5 killed after the fixes). Carrier differs from the head blob only by the bash-path, shell-semantics and fail-not-skip fixes (blob_compare.log)."
    by_pr[516]["fixes"] = [
        "Validator T-F3: the docstrings said the step checks the installed version against the tag (:4 'checks the installed version'; :167 'A publish whose installed version does not match the tag is not a success'). publish.yml:48 only prints m.version('juniper-data') -- the workflow's own comment calls it a 'Version-only check' -- and the tag match is pip's `juniper-data==${VERSION}` (:45). Both docstrings now say that; no assertion changed."
    ]
    by_pr[516]["outcome"] = "carried-with-fix"
    by_pr[516]["reason"] = "Required checks green (triage); 6 pass alone; mutant M6 (add --extra-index-url pypi.org) killed, 4 failed. Carrier differs from the head blob only by the T-F3 docstrings."
    checks = {c["what"]: c for c in m["checks"]}
    checks["full suite on the carrier tree"]["log"] = f"{SCRATCH}/tests/pytest_full_r2.log (round 2: 2563 passed, 7 skipped, 14 subtests passed, 0 failed, 161s, pytest exit 0; round 1: {SCRATCH}/tests/pytest_full.log, same counts)"
    checks["each carried file alone, unmutated (baselines)"]["log"] = f"{SCRATCH}/tests/mutation_r2/baseline_{{512,513,514,516,517}}.log (round 2: #512 22 passed, #513 8, #514 12, #516 6, #517 3)"
    checks["mutation check, every carried test file (brief rule 11)"]["log"] = f"{SCRATCH}/tests/mutation_r2/mutation_results.json (round 2, after the fixes: 8/8 killed, 5/5 baselines green, 0 arms errored, sha256 restored; round 1 in {SCRATCH}/tests/mutation/)"
    checks["carried files vs draft head blobs"]["log"] = f"{SCRATCH}/tests/blob_compare.log (round 2: 4/7 byte-identical -- #512 x3, #517; #513, #514, #516 differ only by their recorded fixes)"
    pre = checks["pinned pre-commit on every changed file (ruff, ruff-format, mypy tests, check-ast, doc-links, ...)"]
    pre["log"] = f"{SCRATCH}/tests/precommit_r2.log (round 2: exit 0; sha256 of all 8 files unchanged, precommit_r2_sha_before.txt)"
    cq = checks["CodeQL prescreen on the 7 test files"]
    cq["log"] += f" Round 2 on the 3 touched files: only the same pytestmark predictions ({SCRATCH}/tests/codeql_prescreen_r2.log). The validator independently found no pytestmark alert in juniper-data's 60-alert history, and CodeQL already analysed the five draft heads with no new alerts."
    mt = checks["the two juniper-data carriers merge with each other"]
    mt["command"] = "git -C <primary> commit-tree <tree> -p 28078558 (local unsigned probes, never pushed: round 2 tests 459c901e = tree d0fd0040; docs f8475ee2 = tree 988a5094) then git merge-tree --write-tree 459c901e f8475ee2"
    mt["log"] = f"inline: exit 0, merged tree 3777f09a2f1439652688abd62069d04239861725 (round 1 probes also merged clean); merged CHANGELOG keeps both entries under [Unreleased] (docs in ### Changed, tests in ### Added): {SCRATCH}/merged_probe_CHANGELOG.txt"
    m["validator_round"] = {
        "findings": f"{SCRATCH}/val-tests/findings.json",
        "applied": ["T-F1 (#513, #514: bash -e, docstrings)", "T-F3 (#516 docstrings)", "T-F4 (#514 fail, not skip)"],
        "noted_not_changed": ["T-F2 (#512 parametrize padding), per the orchestrator"],
        "each_re_derived_before_applying": "T-F1 production log lines 646/715/760/836 + no defaults:/shell: in publish-image.yml or publish.yml; T-F3 publish.yml:45-48; T-F4 read of _run(): 10 of 12 tests go through it.",
    }
    m["open_questions"] = [q for q in m["open_questions"] if not q.startswith("The CodeQL prescreen predicts")]
    m["open_questions"].insert(
        1,
        "With -o pipefail removed, the rehearsal matches production: a pipeline later added to one of these steps fails open on the runner, and now fails open in the test too. That is the intent (the test pins what the runner does), not lost strictness to restore.",
    )
    with path.open("w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=2)
        fh.write("\n")
    print("updated", path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
