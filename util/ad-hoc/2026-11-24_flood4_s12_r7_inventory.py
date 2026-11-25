#!/usr/bin/env python3
"""Build ruling 7's worktree inventory: identify the flood-4 arc's worktrees, map each to its PR, flag and batch them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 7), §6 (the rename pass);
    prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md
    (the five); tmp/flood4/session12/briefs/R7_inventory.txt; util/ad-hoc/2026-11-24_flood4_s12_r7_{scan,live,measure,
    mentions_index,context}.py (its inputs)

Identification, strongest first (every candidate records which rule matched, with file:line where there is one):
  name      the name carries "flood4" (worktrees/)
  five      one of the five worktrees the 11-06 handoff owed (its lines 18-22)
  curated   named by the arc's handoffs or logs and checked by hand (CURATED below, each with its evidence)
  log       a strong mention: an arc handoff, a running log (STATE*), a brief, or the record
  report    the name carries one of the arc's item codes (ITEM_RULES), it was born inside the arc's window, and an arc
            agent's own report, log or script names it (the mention classes "work"/"copy" in the arc's tmp trees)
  item-code the same, but no file names it (flag ITEM-CODE-ONLY: identified by its name alone)
  inferred  provenance inferred, not stated (INFERRED below); always batch B
Anything else is REJECTED, with the reason. PRs: ``own`` = PRs whose head branch is the worktree's branch, in its repo;
``rel`` = the PR(s) the worktree built, validated, landed or simulated, from the item code in its name (ITEM_RULES) or
the curated mapping. Batches: C = excluded or live; B = needs the Overtoad (any PR not merged, no PR, inferred
provenance); A = the rest (every PR merged, not live, not excluded).

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_inventory.py --dir tmp/flood4/session12/r7 [--measure FILE] --now ISO8601Z
Pass 1 (no --measure) writes <dir>/candidate_paths.txt for the measure step; pass 2 writes inventory.json,
inventory.tsv, rejected.tsv, batches.txt and local_branches.tsv. It reads files only (no git) and writes only <dir>.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
REPOS = ["juniper-ml", "juniper-data", "juniper-cascor", "juniper-canopy", "juniper-data-client", "juniper-cascor-client",
         "juniper-cascor-worker", "juniper-deploy", "juniper-recurrence", "juniper-harcot"]
HANDOFF_1106 = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md"
H1 = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md"

EXCLUDED = {
    "curious-plotting-hummingbird": "EXCLUDED-DO-NOT-SWEEP (owner ruling; not this arc's: branch fix/handoff-passphrase-resolved)",
    "hidden-scribbling-toast": "EXCLUDED-ORCHESTRATOR (sessions 10-12's orchestrator, in use; also session 10's launch worktree)",
    "playful-scribbling-kite": "EXCLUDED-LAUNCH (session 12's launch worktree)",
}

FIVE = {
    "juniper-ml--fix--wake-the-claude-followups--20261104-0331--b22126a4": f"{HANDOFF_1106}:19",
    "juniper-ml--fix--wake-the-claude-prompt-guard--20261104-0550--b7382bfa": f"{HANDOFF_1106}:19",
    "juniper-ml--docs--handoff-2026-11-04-launcher-arc--20261104-1532--1c18106d": f"{HANDOFF_1106}:19",
    "juniper-ml--feat--launcher-v-follows-claude-claudey-file--20261106-0348--8d553b41": f"{HANDOFF_1106}:21",
    "juniper-ml--fix--predict-merge-scratch-alternates--20261106-0707--87181fed": f"{HANDOFF_1106}:22",
}

S = "humming-stargazing-papert/tmp/flood4/"
ML = "juniper-ml"
# name -> (evidence, [(repo, pr)], role). Agents: the log line that names the agent and its job.
CURATED: dict[str, tuple[str, list[tuple[str, int]], str]] = {
    "humming-stargazing-papert": (f"{H1}:11", [(ML, 2530), (ML, 2635)], "orchestrator, sessions 1-9 (session 1's launch worktree); holds sessions 1-9's logs and round 2's triage"),
    "joyful-dancing-kahan": ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md:5", [], "session 2's launch worktree"),
    "binary-seeking-frog": ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md:5", [], "session 3's launch worktree"),
    "polymorphic-knitting-pie": ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md:5", [], "session 4's launch worktree"),
    "agile-wondering-lollipop": ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session5-seven-more-landed-queue-and-decisions-pending.md:5", [], "session 5's launch worktree"),
    "resilient-tinkering-thimble": ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session6-four-landed-rulings-19-29-fable-limit-five-agents-dead.md:5", [], "session 6's launch worktree"),
    "curious-seeking-locket": ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_flood4-session7-data-fix-landed-rulings-30-32-fable-limit-three-agents-dead.md:5", [], "session 7's launch worktree"),
    "scalable-wondering-minsky": (f"{S}session8/STATE_S8.txt:4", [], "session 8's launch worktree"),
    "linked-skipping-parrot": (f"{S}session9/STATE_S9.txt:5", [], "session 9's launch worktree"),
    "juniper-ml--val-fidelity-clean-main--20261107-1800--303ccc0b": (f"{H1}:23", [(ML, 2517), (ML, 2519)], "round 1 validators' clean main"),
    # session 1 (round 1)
    "agent-a7674bdaf3240b78b": (f"{H1}:17", [(ML, 2517)], "round 1 ml tests builder"),
    "agent-ab56f3c71e4f75377": (f"{H1}:17", [(ML, 2519)], "round 1 ml docs builder"),
    "agent-a3c73385122d55e37": (f"{H1}:18", [(ML, 2517)], "round 1 validator (ml-tests/val-round2)"),
    "agent-a80754b707aae7b98": (f"{H1}:18", [(ML, 2517)], "round 1 validator (ml-tests/val-tests-dir)"),
    "agent-aa05f5bd8126623da": (f"{H1}:18", [(ML, 2517)], "round 1 validator (ml-tests/val-subpkg)"),
    "agent-adfe0777292754a5c": (f"{H1}:18", [(ML, 2517)], "round 1 validator (ml-tests/val-fidelity)"),
    "agent-a4d5218b39ee8273c": (f"{H1}:18", [(ML, 2519)], "round 1 validator (ml-docs/val-fidelity)"),
    "agent-af5444824ef90bc24": (f"{H1}:18", [(ML, 2519)], "round 1 validator (ml-docs/val-round3)"),
    # sessions 2-3
    "agent-a2a3d94543b707549": (f"{S}STATE.txt:128", [(ML, 2531)], "M-3 builder (paused-fit wedge)"),
    "agent-a552a50a3a9e32041": (f"{S}STATE.txt:154", [(ML, 2534)], "M-4/M-7 builder (resume continuity)"),
    "agent-a046a9b4b79c0d922": (f"{S}STATE.txt:254", [(ML, 2531)], "M-3 fix-up"),
    "agent-aba7a82eb8f1730ca": (f"{S}STATE.txt:261", [(ML, 2534)], "M-4/M-7 fix-up"),
    "agent-a54fb70fa14aac288": (f"{S}STATE.txt:268", [("juniper-canopy", 807), ("juniper-canopy", 808)], "round 2 canopy builder"),
    "agent-a38bba7307d124c58": (f"{S}STATE.txt:272", [("juniper-data", 534), ("juniper-data", 535), ("juniper-data", 537)], "round 2 data builder"),
    "agent-a89a45162cee4b2e8": (f"{S}STATE.txt:280", [(ML, 2579)], "ml-propose builder"),
    "agent-a675564a3fa0194a8": (f"{S}STATE.txt:410", [(ML, 2554)], "ml-code builder (ruling 15)"),
    "agent-a6c5f687d43e132a5": (f"{S}STATE.txt:468", [(ML, 2554)], "ml-code claims lens"),
    "agent-a0aed7b83f2dc1d30": ("humming-stargazing-papert/tmp/flood4r2-val/ml-code-port-lens/findings.json:4", [(ML, 2554)], "ml-code port lens (its own findings name the worktree)"),
    # session 4
    "agent-a67685d30bfa19727": (f"{S}STATE.txt:511", [(ML, 2581)], "ml-tests builder"),
    "agent-ab006c2d3dc68fe8c": (f"{S}STATE.txt:560", [(ML, 2547)], "N-4 builder"),
    "agent-a001ff6d68bf06099": (f"{S}STATE.txt:574", [(ML, 2557)], "N-2 builder"),
    "agent-a69d8c2809c3b4840": (f"{S}STATE.txt:595", [(ML, 2557)], "N-2 code lens (limit-killed)"),
    "agent-af6b55f5ab45c409b": (f"{S}STATE.txt:595", [(ML, 2557)], "N-2 claims lens (limit-killed)"),
    "agent-ad9caecdbf851e588": (f"{S}STATE.txt:596", [(ML, 2547)], "N-4 code lens (limit-killed)"),
    "agent-a82c2300eca19f450": (f"{S}STATE.txt:596", [(ML, 2554)], "ml-code r3 fix-up (limit-killed)"),
    "agent-a44c2f3feb8589d05": ("humming-stargazing-papert/tmp/flood4r2-val/n4-claims-lens/findings.json:9", [(ML, 2547)], "N-4 claims lens (its own findings name the worktree)"),
    # session 5
    "agent-a6e0be00279ab446e": (f"{S}session5/STATE_S5.txt:77", [(ML, 2557)], "N-2 claims lens, session 5"),
    "agent-afad991b60b22df1b": (f"{S}session5/STATE_S5.txt:101", [(ML, 2557)], "N-2 code lens, session 5"),
    "agent-a134eb76c2019fdd2": (f"{S}session5/STATE_S5.txt:122", [(ML, 2547)], "N-4 code lens, session 5"),
    "agent-a9ff96b8a7d3346e7": (f"{S}session5/STATE_S5.txt:315", [(ML, 2557)], "N-2 round 2"),
    "agent-a7f807098f4f5df1a": (f"{S}session5/STATE_S5.txt:350", [(ML, 2547)], "N-4 round 2"),
    "agent-abc4673d5f7701209": (f"{S}session5/STATE_S5.txt:369", [(ML, 2554)], "ml-code round 3 carrier"),
    "agent-afbefb91618438425": ("humming-stargazing-papert/tmp/flood4r2-val/ml-code-final-s5/PROGRESS.txt:1", [(ML, 2554)], "ml-code final check, session 5 (its own log names the worktree)"),
    "agent-a76e29cb722ffff18": (f"{S}session6/prev_prompts/028_ml-propose-round-3-fix-up-s5.txt:13", [(ML, 2579)], "ml-propose round 2 assembly (validator)"),
    "agent-a316b11a248b6f8fe": (f"{S}session6/STATE_S6.txt:23", [(ML, 2579)], "ml-propose round 3 fix-up"),
    # session 6
    "agent-a211deee35ec85ad3": (f"{S}session6/STATE_S6.txt:212", [(ML, 2579)], "ml-propose round 3b carrier"),
    "agent-a29e21f88df874394": (f"{S}session6/STATE_S6.txt:277", [(ML, 2557)], "N-2 landing prep"),
    "agent-abd21f5554a19c89f": (f"{S}session6/STATE_S6.txt:315", [(ML, 2581)], "ml-tests round 2 (limit-killed)"),
    "agent-a1e6389f6c2d68753": (f"{S}session6/STATE_S6.txt:318", [(ML, 2584)], "ml-docs builder (limit-killed)"),
    "agent-a949c0b9e199389bf": (f"{S}session6/STATE_S6.txt:321", [(ML, 2625)], "ruling 18 guard builder J (limit-killed)"),
    "agent-a80ef4dd2caed2c10": (f"{S}session6/STATE_S6.txt:322", [(ML, 2579)], "ml-propose r3b quick check K (limit-killed)"),
    # session 7
    "agent-a4cd1de89c2b57ea3": (f"{S}session7/STATE_S7.txt:53", [(ML, 2581)], "ml-tests round 2 carrier H2"),
    "agent-a61564fc0ee03e2a2": (f"{S}session7/STATE_S7.txt:55", [(ML, 2579)], "ml-propose r3b quick check K2"),
    "agent-a5303a15bb4329057": (f"{S}session7/STATE_S7.txt:120", [(ML, 2625)], "ruling 18 guard builder J2 (limit-killed; HALF-WRITTEN guard, sha 7b5ee677)"),
    "agent-afa2d849b67f0bfb0": (f"{S}session7/STATE_S7.txt:192", [(ML, 2581)], "ml-tests round 2 tests lens L1"),
    # session 8
    "agent-a89a668e6d43bcee2": (f"{S}session8/STATE_S8.txt:53", [(ML, 2581)], "ml-tests round 2 fix-up carrier H3"),
    "agent-a9898bd52fb78c449": (f"{S}session8/STATE_S8.txt:181", [(ML, 2584)], "ml-docs carrier"),
    "agent-a600fa9c3ad0c1b9e": (f"{S}session8/STATE_S8.txt:190", [(ML, 2581)], "ml-tests round 2 tests lens L1b"),
    # session 9
    "agent-aa1160aea3f9c907d": (f"{S}session9/STATE_S9.txt:86", [(ML, 2618)], "D-14 builder M (stale per the session 9 handoff)"),
    "agent-a0f16311d9dabda6f": (f"{S}session9/STATE_S9.txt:256", [(ML, 2625)], "guard 1.4.0 carrier J4"),
    "agent-a7aa0806f2312b786": (f"{S}session9/STATE_S9.txt:361", [(ML, 2618)], "D-14 juniper-ml carrier M2"),
    "juniper-cascor--detached-origin-main--20261109-1004--96cf891b": ("", [], "UNKNOWN"),
}

INFERRED = {
    "vectorized-crunching-ritchie": "probably session 11's launch worktree: born 2026-11-24T12:19:38Z, 2 min before session 11's START "
                                     "(hidden-scribbling-toast tmp/flood4/session11/STATE_S11.txt:4, 12:21:30Z), and session 11's V26-code "
                                     "lens strace logs show its processes probing vectorized-crunching-ritchie/tmp "
                                     "(tmp/flood4/session11/r26/val_code/strace/juniper-cascor-worker.txt:3825); no log names it",
    "juniper-cascor--detached-origin-main--20261109-1004--96cf891b": "no file names it; detached at cascor#753's merge commit 96cf891b, made "
                                     "21 min after #753 merged, 20 min after the arc's ruling-17 builder worktree "
                                     "(juniper-cascor--fix--stop-then-start-race--20261109-0944--96cf891b) at the same commit",
}

# (regex on the name, [(repo, pr)], item). First match wins; applied to names without a CURATED entry.
ITEM_RULES: list[tuple[str, list[tuple[str, int]], str]] = [
    (r"^juniper-canopy--test--flood4-consolidated-tests", [("juniper-canopy", 797)], "round 1 canopy tests carrier"),
    (r"^juniper-canopy--docs--flood4-consolidated-docs", [("juniper-canopy", 802)], "round 1 canopy docs carrier"),
    (r"^juniper-data--test--flood4-consolidated-tests", [("juniper-data", 518)], "round 1 data tests carrier"),
    (r"^juniper-data--docs--flood4-consolidated-docs", [("juniper-data", 519)], "round 1 data docs carrier"),
    (r"^juniper-canopy--(test|val)--flood4r2-canopy-tests", [("juniper-canopy", 807)], "round 2 canopy tests carrier"),
    (r"^juniper-canopy--docs--flood4r2-canopy-docs", [("juniper-canopy", 808)], "round 2 canopy docs carrier"),
    (r"^juniper-canopy--val--flood4r2-canopy-claims", [("juniper-canopy", 807), ("juniper-canopy", 808)], "round 2 canopy claims lens"),
    (r"^juniper-data--land--flood4r2-m0-control", [("juniper-data", 534), ("juniper-data", 535), ("juniper-data", 537)], "session 5 data landing control (M0)"),
    (r"^juniper-data--(test--flood4r2-consolidated-tests|land--flood4r2-stage1-data-tests|val--flood4r2-data-tests)", [("juniper-data", 534)], "round 2 data tests carrier"),
    (r"^juniper-data--(docs--flood4r2-consolidated-docs|land--flood4r2-stage2-data-docs)", [("juniper-data", 535)], "round 2 data docs carrier"),
    (r"^juniper-data--(fix--flood4r2-retry-after|land--flood4r2-(stage3-data-code|s6-control|s6-mutation-twin)|val--flood4r2-data-code)", [("juniper-data", 537)], "data code carrier (ruling 9, Retry-After)"),
    (r"^juniper-data--(val--flood4r2-m1|fix--gitleaks-pr-commit-pagination)", [("juniper-data", 530)], "M-1, gitleaks commit pagination"),
    (r"^juniper-data--(land--flood4r2-unrun-tests|val--flood4r2-d2-unrun-tests|test--run-the-unrun-tests)", [("juniper-data", 539)], "ruling 25, the unrun tests"),
    (r"^juniper-data--(fix--test-security-unit-marks|val--r17-unit-marks)", [("juniper-data", 529)], "ruling 17, the 44 unmarked tests"),
    (r"^juniper-data--test--gitleaks-pr-scan-blocking-wiring-pins", [("juniper-data", 542)], "ruling 35, blocking-wiring pins"),
    (r"^juniper-data--ci--scheduled-benchmark-smoke-run", [("juniper-data", 540)], "ruling 33, benchmark smoke run"),
    (r"^juniper-cascor--((check|val)--flood4r2-n1|fix--paused-fit-wedge|validate--paused-fit-wedge-n1)", [("juniper-cascor", 753)], "N-1, cascor paused-fit wedge"),
    (r"^juniper-cascor--(val--flood4r2-n3|fix--ws-resume-losses|validate--ws-resume-losses-n3|build--ws-resume-losses-n3|val--n3-r3)", [("juniper-cascor", 754)], "N-3, cascor resume losses"),
    (r"^juniper-cascor--(check--flood4r2-r17|fix--stop-then-start-race|val--r17-stop-start)", [("juniper-cascor", 756)], "ruling 17, cascor stop-then-start"),
    (r"^juniper-cascor--((check|val)--flood4r2-r32|fix--pause-check-then-act)", [("juniper-cascor", 769)], "ruling 32, cascor pause fix"),
    (r"^juniper-cascor--docs--pause-stop-start-overlap", [("juniper-cascor", 764)], "ruling 32, known-not-fixed doc"),
    (r"^juniper-cascor--val--flood4r2-d14-resume", [("juniper-cascor", 776), (ML, 2618)], "D-14 resume answers (rulings 30-31)"),
    (r"^juniper-cascor--(val--flood4r2-d14|test--ws-resume-(shared-answer-table|answer-table-land)|(check|mut)--d14)", [("juniper-cascor", 776)], "D-14 shared table, cascor"),
    (r"^juniper-ml--val--flood4r2-d14", [(ML, 2618)], "D-14 shared table, juniper-ml"),
    (r"^juniper-canopy--(test--unit-lane-network-guard|val--r17-network-guard|probe--r17-guard-r2)", [("juniper-canopy", 815)], "ruling 17, canopy unit-lane network guard"),
    (r"^juniper-canopy--(ci--lockfile-graphql-failure-print|val--r17-lockfile)", [("juniper-canopy", 814)], "ruling 17, canopy lockfile print"),
    (r"^juniper-data-client--(ci--gitleaks-pr-commit-scan|val--r10-port)", [("juniper-data-client", 260)], "ruling 10 pilot port"),
    (r"^juniper-cascor-client--ci--gitleaks-pr-commit-scan", [("juniper-cascor-client", 196)], "ruling 10 port"),
    (r"^juniper-cascor-worker--ci--gitleaks-pr-commit-scan", [("juniper-cascor-worker", 230)], "ruling 10 port"),
    (r"^juniper-cascor--ci--gitleaks-pr-commit-scan", [("juniper-cascor", 761)], "ruling 10 port"),
    (r"^juniper-canopy--ci--gitleaks-pr-commit-scan", [("juniper-canopy", 822)], "ruling 10 port"),
    (r"^juniper-deploy--(ci--gitleaks-pr-commit-scan|r10-port-mainbase)", [("juniper-deploy", 277)], "ruling 10 port"),
    (r"^juniper-ml--ci--gitleaks-pr-commit-scan", [(ML, 2587)], "ruling 10 port"),
    (r"--fix--register-slow-marker-for-scheduled-lane--", [], "ruling 37: built, never pushed; overtaken by worker#231, data-client#263, cascor-client#198"),
    (r"^juniper-ml--((val|land)--)?flood4r2-ml-propose|^juniper-ml--sims--flood4r2-ml-propose", [(ML, 2579)], "ml-propose (ruling 14)"),
    (r"^juniper-ml--((val|land)--)?flood4r2-ml-tests", [(ML, 2581)], "ml-tests, round 2"),
    (r"^juniper-ml--((val|land|fix)--)?flood4r2-ml-docs", [(ML, 2584)], "ml-docs, round 2"),
    (r"^juniper-ml--(land|val)--flood4r2-ml-code", [(ML, 2554)], "ml-code (guard 1.3.0)"),
    (r"^juniper-ml--clean--flood4r2-s8", [(ML, 2579), (ML, 2581), (ML, 2584)], "session 8 clean-main snapshots for its landings"),
    (r"^juniper-ml--val--flood4r2-n4", [(ML, 2547)], "N-4, broadcast drop close"),
    (r"^juniper-ml--val--flood4r2-r18-guard", [(ML, 2625)], "ruling 18, guard 1.4.0"),
]

REJECT_NOTES = {
    "happy-crafting-pebble": "the harcot arc's session 72668aea (its own Overtoad dialog, tmp/flood4/session11/record/dialogs_all_since_1108.json:2041)",
    "agent-a54a0a279acc3a863": "the one-artifact arc's (tmp/cascor-publish-artifact/; tmp/flood4/session11/consolidated_plan_main.md:1195)",
    "immutable-exploring-russell": "R-OBS-SC-2's session worktree (HANDOFF_2026-11-24_r-obs-sc-2-group-d-r45-done-r50-r51-ml-2637-r53-and-owner-items-next.md:5)",
    "declarative-jumping-wreath": "R-OBS-SC-2's session worktree (HANDOFF_2026-11-24_r-obs-sc-2-group-d-r45-r49-r52-prs-gating-canopy-r45-r50-r51-next.md:5)",
    "modular-gathering-squirrel": "the backup arc's session worktree (HANDOFF_2026-11-24_backup-ac5-not-passed-runs-slowed-io-class-ruled-host-steps-and-probe-fixes-next.md:4)",
    "radiant-marinating-seahorse": "the backup arc's session worktree (HANDOFF_2026-11-24_backup-probe-1-4-0-and-watchdog-allow-list-landed-host-steps-and-four-rulings-pending.md:4)",
    "docs_r-obs-sc-2-0-11-5-quick-start-and-cut-tools": "R-OBS-SC-2's (named for it)",
    "juniper-ml--docs--notes-naming-harcot-token--20261109-2200--b47b07d1": "the notes-naming convention's harcot token (another arc); named in no flood-4 file",
}
OTHER_ARC_PATTERNS = [
    (r"--fix--b914-merge-literals--", "the 2026-11-23 B914 merge-literals arc (six repos); named in no flood-4 file"),
    (r"--fix--overtoad-rename-repair--", "the 2026-11-23 rename-repair arc (ml#2606's siblings); named in no flood-4 file"),
    (r"--fix--(rate-limit-retry-after-round-up|fastapi-telemetry-opt-out)--", "R-OBS-SC-2's (disowned by the session 5 handoff, line 108)"),
]

CLASS_ORDER = ["state", "handoff-flood4", "handoff-1106", "brief", "record"]


def iso(t: float) -> str:
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_refs(repo: str) -> dict[str, str]:
    """Local branch -> sha, from loose refs and packed-refs (file reads)."""
    gitdir = JUNIPER / repo / ".git"
    refs: dict[str, str] = {}
    packed = gitdir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(("#", "^")) or " " not in line:
                continue
            sha, ref = line.split(" ", 1)
            if ref.startswith("refs/heads/"):
                refs[ref[len("refs/heads/"):]] = sha
    heads = gitdir / "refs" / "heads"
    if heads.is_dir():
        for p in heads.rglob("*"):
            if p.is_file():
                refs[str(p.relative_to(heads))] = p.read_text(encoding="utf-8", errors="replace").strip()
    return refs


def count_flood4_refs(repo: str) -> int:
    gitdir = JUNIPER / repo / ".git"
    n = 0
    packed = gitdir / "packed-refs"
    if packed.is_file():
        n += sum(1 for line in packed.read_text(encoding="utf-8", errors="replace").splitlines() if " refs/flood4/" in line)
    loose = gitdir / "refs" / "flood4"
    if loose.is_dir():
        n += sum(1 for p in loose.rglob("*") if p.is_file())
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--measure", type=Path)
    ap.add_argument("--now", required=True)
    a = ap.parse_args()
    d = a.dir
    now = datetime.datetime.strptime(a.now, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()
    wts = json.loads((d / "scan_worktrees.json").read_text(encoding="utf-8"))
    idx = json.loads((d / "mentions_index.json").read_text(encoding="utf-8"))
    prs: dict[tuple[str, str], list[dict]] = {}
    prnum: dict[tuple[str, int], dict] = {}
    for r in REPOS:
        for p in json.loads((d / "prs" / f"{r}.json").read_text(encoding="utf-8")):
            p["repo"] = r
            prs.setdefault((r, p["headRefName"]), []).append(p)
            prnum[(r, p["number"])] = p
    remote: dict[str, set[str]] = {}
    for r in REPOS:
        remote[r] = {ln.split("\t", 1)[0] for ln in (d / "branches" / f"{r}.tsv").read_text(encoding="utf-8").splitlines() if ln}
    births: dict[str, int] = {}
    for f in ("births_worktrees.tsv", "births_claude.tsv"):
        for ln in (d / f).read_text(encoding="utf-8").splitlines():
            t, p = ln.split("\t", 1)
            births[p] = int(t)
    holders: dict[str, list[str]] = {}
    for ln in (d / "proc_cwds.tsv").read_text(encoding="utf-8").splitlines():
        if ln.startswith(("#", "pid\t")):
            continue
        pid, wt, _, cmd = (ln.split("\t") + ["", "", "", ""])[:4]
        holders.setdefault(wt, []).append(f"pid {pid} ({cmd[:60]})")
    measure = {}
    if a.measure:
        measure = {r["path"]: r for r in json.loads(a.measure.read_text(encoding="utf-8"))["rows"]}
    refs = {r: read_refs(r) for r in REPOS}

    inv, rej = [], []
    for w in wts:
        name, path = w["name"], w["path"]
        repo = w.get("repo") or (name.split("--", 1)[0] if name.startswith("juniper-") else "juniper-ml")
        c = (idx.get(name) or {})
        counts, first = c.get("counts", {}), c.get("first", {})
        how, evidence = None, ""
        if name in EXCLUDED:
            how, evidence = "excluded", EXCLUDED[name]
        elif w["location"] == "worktrees/" and "flood4" in name:
            how, evidence = "name", "name carries 'flood4'"
        elif name in FIVE:
            how, evidence = "five", FIVE[name]
        elif name in INFERRED:
            how, evidence = "inferred", INFERRED[name]
        elif name in CURATED:
            how, evidence = "curated", CURATED[name][0]
        else:
            strong = next((first[k] for k in CLASS_ORDER if k in first), None)
            if strong:
                how, evidence = "log", strong.replace(str(JUNIPER) + "/juniper-ml/.claude/worktrees/", "")
        if how is None and name not in REJECT_NOTES:
            rule = next(((pat, label) for pat, _lst, label in ITEM_RULES if re.search(pat, name)), None)
            born = births.get(path, 0)
            in_window = datetime.datetime(2026, 11, 7, 22, 46, tzinfo=datetime.timezone.utc).timestamp() <= born <= now
            if rule and in_window:
                report = first.get("work") or first.get("copy")
                if report:
                    # an arc agent's own report, log or script naming the worktree (checked by reading: r7 context helper)
                    how, evidence = "report", report.replace(str(JUNIPER) + "/juniper-ml/.claude/worktrees/", "")
                else:
                    how, evidence = "item-code", f"name carries the arc's item code ({rule[1]}); born {iso(born)}; no file names it"
        if how is None or (how == "log" and name in REJECT_NOTES):
            reason = REJECT_NOTES.get(name)
            if reason is None:
                reason = next((why for pat, why in OTHER_ARC_PATTERNS if re.search(pat, name)), None)
            if reason is None:
                b = births.get(path, 0)
                prof = ",".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no mention"
                arc_start = datetime.datetime(2026, 11, 7, 22, 46, tzinfo=datetime.timezone.utc).timestamp()
                when = "born before the arc (session 1 began 2026-11-07T22:46Z)" if b and b < arc_start else f"born {iso(b) if b else '?'}"
                reason = f"no flood-4 evidence: {when}; mentions: {prof}"
                if counts and set(counts) <= {"work", "copy", "handoff-other"}:
                    reason += " (only in another arc's handoff, a copied repository file, or the 2026-11-07 worktree-list dump)"
            rej.append({"name": name, "location": w["location"], "repo": repo, "branch": w.get("branch") or "", "detached": (w.get("detached_sha") or "")[:12],
                        "kind": w.get("kind"), "reason": reason})
            continue
        # PRs
        branch = w.get("branch")
        own = prs.get((repo, branch), []) if branch else []
        rel_list: list[tuple[str, int]] = []
        item = ""
        if name in CURATED:
            rel_list, item = CURATED[name][1], CURATED[name][2]
        else:
            for pat, lst, label in ITEM_RULES:
                if re.search(pat, name):
                    rel_list, item = lst, label
                    break
        # a tree that combined two carriers (e.g. "-r2-plus-ml-propose", "-pr2558-ml-propose") also served ml-propose
        if name.startswith("juniper-ml--") and "ml-propose" in name and (ML, 2579) not in rel_list:
            rel_list = rel_list + [(ML, 2579)]
        if name.endswith("-mltests") and (ML, 2581) not in rel_list:
            rel_list = rel_list + [(ML, 2581)]
        rel = [prnum[k] for k in rel_list if k in prnum]
        ownr = list(own)
        # head and name sha
        head_sha = w.get("detached_sha") or (refs.get(repo, {}).get(branch) if branch else None)
        m = re.search(r"--([0-9a-f]{7,8})(-[A-Za-z0-9]+)?$", name)
        name_sha = m.group(1) if m else None
        head_moved = bool(name_sha and head_sha and not head_sha.startswith(name_sha))
        flags = []
        if how == "excluded":
            flags.append(EXCLUDED[name].split(" ", 1)[0])
        hs = holders.get(path, [])
        meas = measure.get(path, {})
        recent = meas.get("recent_files", 0)
        if hs:
            flags.append("LIVE")
        if recent:
            flags.append("LIVE")
        if name == "humming-stargazing-papert":
            flags.append("ARCHIVE-LAST")
        if w.get("kind") != "linked-worktree":
            flags.append("PLAIN-DIR")
        if w.get("locked"):
            flags.append("LOCKED")
        considered = rel if rel else ownr
        if name == "humming-stargazing-papert":
            considered = rel  # its branch's PR (#2606) is the rename arc's, not this arc's
        if not considered:
            flags.append("NO-PR")
        elif any(p["state"] != "MERGED" for p in considered):
            flags.append("UNMERGED")
        if how == "inferred":
            flags.append("PROVENANCE-INFERRED")
        if how == "item-code":
            flags.append("ITEM-CODE-ONLY")
        if head_moved:
            # HEAD is not the commit the worktree was created at (the sha in its name). The arc made no local commits
            # (every PR went up as signed API commits), so this is a merge/rebase/reset made for a simulation or a
            # landing check, or someone else's commits. On a detached HEAD no branch holds them: removing the worktree
            # leaves them unreachable. The executing script must test HEAD against origin/main and bundle what is not on it.
            flags.append("HEAD-MOVED")
        rename_log = name in ("agent-a7aa0806f2312b786", "agent-a0f16311d9dabda6f")
        rwin = meas.get("rename_window_files", 0)
        if rename_log or rwin:
            flags.append("RENAME-TOUCHED")
        if "EXCLUDED" in " ".join(flags) or "LIVE" in flags:
            batch = "C"
        elif any(f in flags for f in ("NO-PR", "UNMERGED", "PROVENANCE-INFERRED", "LOCKED")):
            batch = "B"
        else:
            batch = "A"
        b = births.get(path, 0)
        row = {
            "name": name, "path": path, "location": w["location"], "repo": repo, "kind": w.get("kind"),
            "branch": branch or "", "detached_sha": (w.get("detached_sha") or "")[:12], "head_sha": (head_sha or "")[:12],
            "name_sha": name_sha or "", "registered": bool(w.get("registered")), "locked": bool(w.get("locked")),
            "born_utc": iso(b) if b else "", "identified_by": how, "evidence": evidence, "item": item,
            "remote_branch_exists": bool(branch and branch in remote.get(repo, set())),
            "own_prs": [f"{p['repo']}#{p['number']} {p['state']} {p['mergedAt'] or ''} head={p.get('headRefOid', '')[:8]}".strip() for p in ownr],
            "related_prs": [f"{p['repo']}#{p['number']} {p['state']} {p['mergedAt'] or ''}".strip() for p in rel],
            "holders": hs, "flags": sorted(set(flags), key=flags.index), "batch": batch,
            "mention_counts": counts,
        }
        for k in ("total_bytes", "files", "newest_mtime", "tmp_exists", "tmp_is_symlink", "tmp_bytes", "tmp_files", "tmp_newest_mtime",
                  "recent_files", "recent_newest", "rename_window_files"):
            row[k] = meas.get(k)
        inv.append(row)

    (d / "candidate_paths.txt").write_text("\n".join(r["path"] for r in inv) + "\n", encoding="utf-8")
    if not a.measure:
        print(f"pass 1: {len(inv)} candidates, {len(rej)} rejected; wrote candidate_paths.txt")
        return 0
    order = {"C": 2, "B": 1, "A": 0}
    inv.sort(key=lambda r: (order[r["batch"]], r["location"], r["name"]))
    (d / "inventory.json").write_text(json.dumps({"generated_utc": a.now, "count": len(inv), "rows": inv}, indent=1) + "\n", encoding="utf-8")
    cols = ["batch", "flags", "name", "location", "repo", "kind", "branch", "detached_sha", "head_sha", "name_sha", "registered", "locked",
            "born_utc", "identified_by", "evidence", "item", "own_prs", "related_prs", "remote_branch_exists", "tmp_exists", "tmp_bytes",
            "tmp_files", "tmp_newest_mtime", "total_bytes", "files", "newest_mtime", "recent_files", "rename_window_files", "holders", "path"]
    with (d / "inventory.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in inv:
            fh.write("\t".join(";".join(map(str, r[c])) if isinstance(r[c], list) else str(r[c] if r[c] is not None else "") for c in cols) + "\n")
    with (d / "rejected.tsv").open("w", encoding="utf-8") as fh:
        fh.write("name\tlocation\trepo\tkind\tbranch\tdetached\treason\n")
        for r in sorted(rej, key=lambda r: (r["location"], r["name"])):
            fh.write(f"{r['name']}\t{r['location']}\t{r['repo']}\t{r['kind']}\t{r['branch']}\t{r['detached']}\t{r['reason']}\n")
    # batches summary
    lines = [f"generated {a.now}; candidates {len(inv)}; rejected {len(rej)}"]
    for bt in ("A", "B", "C"):
        rows = [r for r in inv if r["batch"] == bt]
        tot = sum(r["total_bytes"] or 0 for r in rows)
        tmpb = sum(r["tmp_bytes"] or 0 for r in rows)
        lines.append(f"\nBATCH {bt}: {len(rows)} entries, total {tot} bytes ({tot / 1e9:.2f} GB), of which tmp/ {tmpb} bytes ({tmpb / 1e9:.2f} GB)")
        by: dict[str, list[dict]] = {}
        for r in rows:
            by.setdefault(f"{r['location']}{r['repo']}" if r["location"] == "worktrees/" else r["location"], []).append(r)
        for k, rs in sorted(by.items()):
            lines.append(f"  {k}: {len(rs)} entries, {sum(x['total_bytes'] or 0 for x in rs)} bytes")
        if bt != "A":
            for r in rows:
                lines.append(f"    - {r['name']}  [{','.join(r['flags'])}]  {r['item'] or ''}  related={';'.join(r['related_prs']) or '-'} own={';'.join(r['own_prs']) or '-'}")
    # local branches of the arc's merged PRs, in the primaries (file reads)
    lb = ["repo\tbranch\tlocal_sha\tremote_exists\tchecked_out_in\tprs"]
    arc_heads: dict[tuple[str, str], list[dict]] = {}
    for r in inv:
        for p in [prnum.get((x.split("#")[0], int(x.split("#")[1].split()[0]))) for x in r["related_prs"] + r["own_prs"]]:
            if p:
                arc_heads.setdefault((p["repo"], p["headRefName"]), []).append(p)
    checked = {(r["repo"], r["branch"]): r["name"] for r in inv if r["branch"]}
    for w in wts:
        if w.get("branch"):
            checked.setdefault((w.get("repo") or "", w["branch"]), w["name"])
    for (repo, br), ps in sorted(arc_heads.items()):
        sha = refs.get(repo, {}).get(br)
        if sha is None:
            continue
        states = sorted({f"#{p['number']}:{p['state']}" for p in ps})
        lb.append(f"{repo}\t{br}\t{sha[:12]}\t{br in remote.get(repo, set())}\t{checked.get((repo, br), '')}\t{','.join(states)}")
    (d / "local_branches.tsv").write_text("\n".join(lb) + "\n", encoding="utf-8")
    lines.append("\nrefs/flood4/* local refs per primary: " + ", ".join(f"{r}={count_flood4_refs(r)}" for r in REPOS))
    (d / "batches.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
