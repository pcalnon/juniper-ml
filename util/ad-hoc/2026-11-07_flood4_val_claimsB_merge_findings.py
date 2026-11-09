"""
Merge the claims-lens slice-B validator's own findings with its four forks' findings into one findings.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 docs carrier validation (claims lens, slice B); notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
  python3 <this file> <val-claims-B scratch dir>

Reads own_findings.json and fork_{workers,ws,control,registry_replay}/findings.json in that dir,
applies the lead validator's severity decisions (each recorded in the finding as 'severity_note'),
folds C2+S3 into one ordering finding and R7 into B-own-4, and writes findings.json there.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FORKS = ("fork_workers", "fork_ws", "fork_control", "fork_registry_replay")

# The lead validator re-read the code for each of these and set the final severity.
OVERRIDES = {
    "C1": ("BLOCKER", "Lead re-read control_security.py:171-175 and control_stream.py:139-149: the cooldown-trigger WARNING fires on the Nth failed-key/Origin attempt, which closes 4001/4003. The rewrite's 'a failed key (4001) logs nothing' is a false universal introduced by the builder's #2446 fix."),
    "W1": ("BLOCKER", "Lead re-read coordinator.py:337-362 (submit_tasks clears _completed_task_ids, keeps _pending_tasks) and :405-466 (accept keeps assigned_worker_id); only cancel_round clears _pending_tasks. The rewrite's 'the other is rejected as a Duplicate result' is false once a round boundary intervenes; introduced by the builder's #2464 fix."),
    "W2": ("BLOCKER", "Lead re-read audit.py: AuditLogger (:46) has log (:61); on_anomaly (:123) is WorkerMetrics'. A wrong API name on main, carried verbatim from draft #2442."),
    "S2": ("MAJOR", "Lead re-read manager.py:451-452 (broadcast returns before sequencing with no active socket). Seq continuity is literally true; the consequence the text invites ('caught up', 'continuous') is false for a sole client. Arguably BLOCKER where one dashboard is the only client."),
}

DROP = {"C2", "S3", "R7"}

DEP1 = {
    "id": "DEP1",
    "severity": "MAJOR",
    "severity_note": "BLOCKER if the docs PR merges before the ml tests carrier, or if the tests carrier drops or renames a named file. Folds fork findings C2 and S3 (and the 'pinned by' half of R7).",
    "where": "docs/REFERENCE.md:8905 (#2456: test_request_body_limit_boundary.py), docs/REFERENCE.md:9061 (#2462: test_ws_frame_exact_cap.py), docs/REFERENCE.md:2114 (#2460: test_replay_speed_range_edges.py, test_lifecycle_paused_terminal.py)",
    "claim": "Three sections name test files that are not on main (303ccc0b). They exist only in the ml TESTS carrier (worktree agent-a7674bdaf3240b78b), byte-identical to drafts #2451, #2458 and #2445. Each sentence is true only once that carrier has merged with those paths. The forks checked the content: each sentence's description matches what its file pins, and both body-cap '>=' mutants survive main's tests but are killed by the boundary file.",
    "evidence": "ls juniper-service-core/tests on main: none of the four files; agent-a7674bdaf3240b78b/tmp/flood4/ml-tests/changed_paths_final.txt lists all four; diff of `git show refs/flood4/pr/{2451,2458,2445}:<path>` vs the tests-carrier copies: identical (fork_control, fork_ws, fork_registry_replay findings).",
    "fix": "Open and merge the tests carrier first, and make the docs PR depend on it. Re-check the four paths against the merged tests PR before opening the docs PR (D-ml-docs-2). No text change is needed once it has landed.",
}


def load(path: Path) -> dict:
    """Load one findings file."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    scratch = Path(argv[1])
    own = load(scratch / "own_findings.json")
    checked = ["[lead] " + c for c in own.get("checked", [])]
    not_checked: list[str] = []
    findings: list[dict] = []
    r7_evidence = ""
    for fork in FORKS:
        data = load(scratch / fork / "findings.json")
        checked += ["[%s] %s" % (fork, c) for c in data.get("checked", [])]
        not_checked += ["[%s] %s" % (fork, c) for c in data.get("not_checked", [])]
        for item in data.get("findings", []):
            fid = item.get("id")
            if fid == "R7":
                r7_evidence = item.get("evidence", "")
            if fid in DROP:
                continue
            item = dict(item)
            if fid in OVERRIDES:
                sev, note = OVERRIDES[fid]
                if sev != item.get("severity"):
                    note = "Fork rated %s. %s" % (item.get("severity"), note)
                item["severity"] = sev
                item["severity_note"] = note
            item["source"] = fork
            findings.append(item)
    for item in own.get("findings", []):
        item = dict(item)
        item["source"] = "lead"
        if item.get("id") == "B-own-4" and r7_evidence:
            item["evidence"] = item.get("evidence", "") + " Fork R7 (folded here): " + r7_evidence
        findings.append(item)
    findings.append(dict(DEP1, source="lead (merge of fork C2, S3, R7)"))
    order = {"BLOCKER": 0, "MAJOR": 1, "MINOR": 2}
    findings.sort(key=lambda f: (order.get(f.get("severity"), 3), f.get("id", "")))
    not_checked += [
        "[lead] Drafts outside slice B (validator A's slice); markdownlint / doc-link / anchor resolution (other lenses; the builder's pinned pre-commit log reports pass)",
        "[lead] Running the ml tests carrier's suites or mutating them (tests lens); forks ran only the paired draft tests they cite",
        "[lead] Whether juniper-cascor's own /ws/training uses service-core's manager (bears on how common S2's sole-client case is)",
    ]
    out = {
        "carrier": "juniper-ml docs carrier (uncommitted worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-ab56f3c71e4f75377, base origin/main 303ccc0b4613dadcbe5ef16985a862beccec7a1a)",  # home-path-literal: allow (recorded findings text, not a path this script uses)
        "lens": "claims, slice B (#2442, #2444, #2446, #2449, #2456, #2457, #2460, #2462, #2464, #2465)",
        "checked": checked,
        "not_checked": not_checked,
        "findings": findings,
    }
    with (scratch / "findings.json").open("w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1)
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    print("findings=%d %s checked=%d not_checked=%d" % (len(findings), counts, len(checked), len(not_checked)))
    for f in findings:
        if f["severity"] != "MINOR":
            print(f["severity"], f["id"], f["where"][:110])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
