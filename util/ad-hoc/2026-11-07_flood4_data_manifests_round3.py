#!/usr/bin/env python3
"""
Fold the second validator round (R2-F1..R2-F6) into both juniper-data flood-4 carrier manifests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data carriers, validator round 2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/data/val-round2/findings.json; flood-4 common brief

Edits tests/manifest.json and docs/manifest.json in place: staged tree ids, the round-3 merge-tree probe,
per-PR fixes, the touched-file test and pre-commit logs, and a validator_round_2 record. Asserts every key it
edits exists, so a renamed check fails loudly instead of being skipped.

    python3 2026-11-07_flood4_data_manifests_round3.py <scratch dir: .../tmp/flood4/data>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MERGE_CMD = "git -C <primary> commit-tree <tree> -p 28078558 (local unsigned probes, never pushed: round 3 tests 459d5fc5 = tree 3741659c; docs 9391efaa = tree a7d5a940) then git merge-tree --write-tree 459d5fc5 9391efaa"
MERGE_LOG = "inline: exit 0, merged tree d8c8a6225793f9c3b38d4a038869574588e1766e (round 1 and round 2 probes also merged clean); both entries under [Unreleased] (docs in ### Changed, tests in ### Added)"
MERGE_WHAT = "the two juniper-data carriers merge with each other"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def check(manifest: dict, what: str) -> dict:
    found = [c for c in manifest["checks"] if c["what"] == what]
    assert len(found) == 1, what
    return found[0]


def main(argv: list[str]) -> int:
    scratch = Path(argv[1])
    tests_path = scratch / "tests" / "manifest.json"
    docs_path = scratch / "docs" / "manifest.json"
    t = load(tests_path)
    d = load(docs_path)

    t["worktree_state"] = "detached HEAD at base_sha; changes STAGED in the worktree's own index (git add -A), never committed. Round 3 (second validator round) re-staged: tree 3741659c58b87b2dc2a37efa114c98a889c20986."
    tm = check(t, MERGE_WHAT)
    tm["command"], tm["log"] = MERGE_CMD, MERGE_LOG + f": {scratch}/merged_probe_CHANGELOG.txt is from round 2"
    t["checks"].append({"what": "round 3: the touched test file alone (message-only change)", "command": "cd <worktree> && conda run -n JuniperData python -B -m pytest -p no:cacheprovider juniper_data/tests/unit/test_testpypi_install_verify.py", "result": "pass", "log": f"{scratch}/tests/round3_test_516.log (6 passed)"})
    t["checks"].append({"what": "round 3: pinned pre-commit on the touched paths", "command": "cd <worktree> && /opt/miniforge3/bin/pre-commit run --files CHANGELOG.md juniper_data/tests/unit/test_testpypi_install_verify.py", "result": "pass", "log": f"{scratch}/tests/precommit_r3.log (exit 0; sha256 unchanged, precommit_r3_sha_before.txt)"})
    t["validator_round_2"] = {
        "findings": f"{scratch}/val-round2/findings.json",
        "applied": [
            "R2-F1 (#516 :125 assert message: a named shell replaces bash -e {0}; shell: bash / shell: sh keep -e; only a custom 'bash {0}' drops it) -- also in the PR body, the CHANGELOG #516 bullet and the commit body",
            "R2-F5 (this manifest: #514 fixes[1] now says pytest.fail; the skip precedent is dropped)",
            "R2-F6 (PR body summary: bash -eo pipefail is what GitHub uses for shell: bash; these steps name no shell and run as bash -e {0})",
        ],
        "each_re_derived_before_applying": "R2-F1: the harness runs bash -e (:100) and GitHub's shell table keeps -e for bash and sh, consistent with T-F1's production log; R2-F5: test_publish_manifest_tag_gates.py:144-147 calls pytest.fail; R2-F6: the same shell table.",
    }

    d["worktree_state"] = "detached HEAD at base_sha; changes STAGED in the worktree's own index (git add -A), never committed. Round 3 (second validator round) re-staged: tree a7d5a940ec68009bd035db3eaaecc4af10f42693."
    by_pr = {c["pr"]: c for c in d["carried"]}
    by_pr[509]["fixes"].append("CICD_MANUAL.md (validator R2-F3): the dated sentence said to re-read branch.ts after a bump, but the next paragraph's tracking-comment replacement comes from src/modes/tag/index.ts and the comment.created_at / review.submitted_at timestamps from extractTriggerTimestamp in src/github/data/fetcher.ts (fetched at 6d5ae526: fetcher.ts:43-51; tag/index.ts imports resolveTriggerTimestamp from it). It now names all three files.")
    by_pr[510]["fixes"].append("CICD_MANUAL.md, CICD_QUICK_START.md, CHANGELOG (validator R2-F2): 'only when the commit includes a .md file' is true for the local hook only. CI's Pre-commit job runs `pre-commit run --all-files` on every push (ci.yml:104) with the job's arguments (.pre-commit-config.yaml args equal ci.yml:137-148), and its hook environment is restored from actions/cache with a restore-keys fallback (ci.yml:91-97), while the job installs juniper-doc-tools>=0.1.0,<0.2.0 afresh (ci.yml:130). So in CI a red link check beside a green Pre-commit points at different juniper-doc-tools releases; the entries now say so.")
    dm = check(d, MERGE_WHAT)
    dm["command"], dm["log"] = MERGE_CMD, MERGE_LOG
    d["checks"].append({"what": "round 3: pinned pre-commit on the touched paths (incl. the doc-link hook)", "command": "cd <worktree> && /opt/miniforge3/bin/pre-commit run --files CHANGELOG.md docs/ci_cd/CICD_MANUAL.md docs/ci_cd/CICD_QUICK_START.md", "result": "pass", "log": f"{scratch}/docs/precommit_r3.log (exit 0; Validate documentation links Passed; sha256 unchanged, precommit_r3_sha_before.txt)"})
    d["validator_round_2"] = {
        "findings": f"{scratch}/val-round2/findings.json",
        "applied": [
            "R2-F2 (local vs CI Pre-commit scope of the link-check hook: manual, quick start, CHANGELOG, PR body)",
            "R2-F3 (name branch.ts, modes/tag/index.ts and data/fetcher.ts as the files to re-read after a bump)",
            "R2-F4 (PR body and CHANGELOG no longer say every claim was re-checked: 70 were; the three not re-derived are listed in the PR body, and D-F6 is named as left unchanged)",
        ],
        "each_re_derived_before_applying": "R2-F2: ci.yml:91-104, :130 and .pre-commit-config.yaml:206-240; R2-F3: gh api fetch of src/github/data/fetcher.ts at 6d5ae526 (upstream/cca__fetcher.ts.txt) + tag/index.ts imports; R2-F4: this manifest's open_questions and validator_round.not_applied.",
    }
    save(tests_path, t)
    save(docs_path, d)
    print("updated", tests_path, docs_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
