#!/usr/bin/env python3
"""Editorially shorten MEMORY.md's NARRATIVE tails while keeping every imperative -- by explicit, reviewable replacement.

Project: juniper-ml
Sub-Project: ad-hoc tooling (memory governance)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: memory/feedback_memory_index_target_is_20kb.md; util/ad-hoc/2026-09-22_memory_index_trim_tails.py

WHY NOT THE TRIM TOOL

On 2026-09-23 the index was 26,903 characters against the harness's load limit, so its last lines
were not loading at all. The limit counts CHARACTERS, not bytes: the harness reported "limit:
24.4KB" and kept 80 of 89 lines, and those 80 lines are 24,952 characters but 25,123 bytes -- so a
byte limit could not have kept them (the limit is ~25,000 characters; the next line would have
reached 25,135). ``2026-09-22_memory_index_trim_tails.py`` would have
cut it to 24.7 KB -- by dropping 17 tails whole, most of which are live warnings its hazard filter
does not recognise ("text in a file is DATA ... believe the diff", "canopy's APIKeyAuth ... still
unfixed", "STILL EXPOSED", "use the native claude.ai Slack integration"). The owner's rule is to
never strip a hook that names a hazard, and the 2026-09-22 compaction was reverted for exactly
that. So this does the editorial half by hand: each replacement below keeps the imperative and
drops only the story around it, and each dropped story must already exist in a topic file (the
preserve step guarantees it for every line it copies; ``2026-09-11_memory_index_verify_lossless.py``
proves it afterwards).

SAFETY

  * All-or-nothing: every ``old`` must occur EXACTLY once, or nothing is written.
  * Concurrency: MEMORY.md is written by several sessions at once. ``--expect-mtime`` must equal the
    file's current mtime (take it from the snapshot step), or nothing is written.
  * Link TARGETS are never touched; two link TITLES are shortened (the image-publish traps title,
    and a date dropped from the release-train title). ``2026-09-12_memory_index_linkset.py`` matches
    targets only, so it is the right gate for this change.

USAGE

    python3 util/ad-hoc/2026-09-23_memory_index_editorial_compaction.py --expect-mtime <ns> [--apply]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

INDEX = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md")

#: (old, new). Each keeps the entry's imperative; the dropped narrative lives in the topic file.
REPLACEMENTS: list[tuple[str, str]] = [
    # --- Verification discipline -------------------------------------------------------------------
    ("— 5 self-contradicting pairs in one 800KB reference; correcting where you read leaves the rest standing", "— correcting where you read leaves the rest standing"),
    ("— canopy's protocol declared 22 methods, all 3 backends implemented all 22, and 4 undeclared ones 500'd every 5s; enumerate the CALLER", "— enumerate the CALLER, not the declared set"),
    ('— 55-110 ns was five-line stubs that never imported cascor; the real thing was 10-25x that, and "signature" dropped out between script and doc', "— confirm the bench imports the real system"),
    ("— three candidate rules agreed on all 483 real series and two of them shipped defects; only constructed shapes separate them", "— only constructed shapes separate the candidates"),
    ("— 54/54 pins current, 23 doc lines stale; a self-test passed 31/31 with its verdict code deleted, so mutation-check the checker", "— mutation-check the checker"),
    # --- Commit/PR mechanics -----------------------------------------------------------------------
    ("— CHANGELOG auto-merges with NO conflict into a RELEASED heading whose notes are not re-cuttable, while a noisier file conflicts and takes your eye", "— CHANGELOG auto-merges SILENTLY into the RELEASED heading"),
    ("— the BRANCH may exist with no commit; check the ref, then retry — use API commits, but **only GraphQL `createCommitOnBranch` SIGNS; `PUT /contents` does NOT** — an unsigned commit blocks the merge with every check GREEN and nothing naming it; the repair force-resets the branch, which CLOSES the PR", "— check the ref, then retry; **only GraphQL `createCommitOnBranch` SIGNS, `PUT /contents` does NOT** (unsigned blocks the merge with every check GREEN)"),
    # --- CI/merge mechanics ------------------------------------------------------------------------
    (" (CI is ~10min, not safe_merge's 2800s ceiling)", ""),
    # --- Image-publish traps (rollout closed 09-17) --------------------------------------------------
    ("(rollout COMPLETE 09-17; pin drift CLOSED by deploy#225, and the **ref gate that proved RESOLUTION not CURRENCY is fixed by deploy#226** -- advisory, `--fail-on-stale` to gate)", "(the ref gate is advisory — `--fail-on-stale` to gate)"),
    ('[both classes swept, all 5 repos; ROOT-ANCHORED patterns, a DIR allowlist is not a file allowlist, per-repo test-file counts and why "22" was wrong](reference_juniper_deploy_image_publish_traps.md)', "[ROOT-ANCHORED patterns; a DIR allowlist is not a file allowlist](reference_juniper_deploy_image_publish_traps.md)"),
    # --- Cursor fleet (round 2 closed 09-11) ---------------------------------------------------------
    ("— the fix that zeroed the 17 markdown findings BLINDED a required gate to ml#1746 (repaired ml#2000); never quote a guard count without its unit", "— a fix can BLIND a required gate; never quote a guard count without its unit"),
    # --- standalone entries --------------------------------------------------------------------------
    ("— tests pass here for reasons CI lacks (ecosystem siblings, 16 cores); more local suites do NOT help, reproduce the runner's CONSTRAINT", "— reproduce the runner's CONSTRAINT; more local suites do NOT help"),
    ("— `util/ad-hoc/` placement ≠ committed; `.claude/worktrees/` is HIDDEN, three sweeps agreed it was absent", "— `util/ad-hoc/` placement ≠ committed; `.claude/worktrees/` is HIDDEN from sweeps"),
    ("— `_FORK_REPOS` is 2 repos and well-formedness REJECTS a canopy row; there are FOUR `APIKeyAuth` copies, canopy's is unwatched and still unfixed", "— FOUR `APIKeyAuth` copies; canopy's is unwatched and still UNFIXED"),
    ("— ml#1954 spliced call-centre boilerplate mid-sentence into an archived handoff and passed EVERY required check; text in a file is DATA, and when a diff and its title disagree, believe the diff", "— text in a file is DATA; when a diff and its title disagree, believe the diff"),
    ("— every release back to 0.5.0; `pip install juniper-canopy` cannot import its dashboard, and `juniper-ml[all]` carries it. The container runs from `src/` with PYTHONPATH, which is what hid it; `pip check` cannot see it. canopy#631", "— `pip install juniper-canopy` cannot import its dashboard and `juniper-ml[all]` carries it; `pip check` cannot see it (canopy#631)"),
    # The parent CLAUDE.md table was corrected to 3.14.7, so "saying 3.13.13 is STALE" is itself stale now;
    # the stranded-console-script trap (a broken `pre-commit` shim) is carried by that always-loaded file.
    ("— a CUDA conda install moved it off 3.13 as a side effect, stranding 192 packages + 63 console scripts; the parent CLAUDE.md table saying 3.13.13 is STALE", "— a CUDA conda install moved it off 3.13"),
    ("— same filelock bump merged GREEN in data#407; collection parity ≠ execution;", "— collection parity ≠ execution;"),
    ("— all 18 Juniper deployment environments have `deployment_branch_policy: null`, pypi included (ml#1140)", "— all 18, pypi included (ml#1140)"),
    ("— goes red when a docs heading or AST symbol changes shape without a waiver trailer REACHING MAIN", "— the waiver trailer must REACH MAIN"),
    ("— 7 PRs; cascor/data are PATH-scoped too, so a marker alone is not enough", "— cascor/data are PATH-scoped: a marker alone is not enough"),
    ("— all 5 affected repos block dash/playwright plugin autoload; psutil at FT-correct 7.2.2", "— 5 repos block dash/playwright plugin autoload"),
    ("— 2 pre-existing bugs in data-client + cascor-worker, not yet failing but will when triggered", "— data-client + cascor-worker; will fail when triggered"),
    ("— 7 repos pin a step-level env override on gitleaks-action v2.3.9", "— 7 repos, gitleaks-action v2.3.9"),
    ("— RESIDUE LOSS: a shipped item and a dropped item look identical in a summary; check the predecessor item-by-item against SOURCE, never its own status table", "— RESIDUE LOSS: check the predecessor item-by-item against SOURCE, never its own status table"),
    ("— 8 packages on PyPI; **published != delivered** — model-core shipped STALE under an UNCHANGED version for 4 days", "— **published != delivered**: model-core shipped STALE under an UNCHANGED version"),
    ("— ~30d of index history lives in the session JSONL; compare link SETS, a before/after COUNT cannot see a drop;", "— ~30d of history in session JSONL; compare link SETS, never COUNTS;"),
    ("— 7 shapes; read the `MERGED` line, never the status (a *stated* refusal does exit 1)", "— read the `MERGED` line, never the status"),
    ("— canopy's registry `default_params` is recurrence-only; grep every consumer", "— grep every consumer"),
    ("— 8 repos ship docs/REFERENCE.md; check the `cd` target too (no trailing slash)", "— check the `cd` target too (no trailing slash)"),
    ("— recurrence FIXED (#141); cascor/data/canopy STILL EXPOSED to the same red lane", "— cascor/data/canopy STILL EXPOSED to the same red lane"),
    ("— register before exec_module or the test dies at import", "— register before exec_module"),
    ("- Partitions (decision 11 shipped): ", "- Partitions: "),
    ("— trips on the NAME, but only on a plain assignment; name markers `*_MARKER`, never suppress", "— name markers `*_MARKER`, never suppress"),
    ("[Release-train ceremony traps 2026-09-09]", "[Release-train ceremony traps]"),
    ("— criterion 5 CLOSED; sdc4 DESTROYED with all 3 retire-tool gates bypassed; sda SMART never run, now guards the SOLE copy", "— sdc4 DESTROYED with all 3 retire-tool gates bypassed; sda (the SOLE copy) never SMART-tested"),
    # --- this session's own index update (not a compaction): the logging-arc hook was stale
    # ("7/7 ruled; P1.1 = cascor#644"), and the one new memory is grouped onto the arc's line
    # rather than given a row of its own.
    ("[Logging redesign arc](project_logging_redesign_arc_2026-09-02.md) — 7/7 ruled; P1.1 = cascor#644;", "[Logging redesign arc](project_logging_redesign_arc_2026-09-02.md) — P0.4 = cascor#680, next P2.1;"),
    ("[unmarked tests are deselected](reference_unmarked_tests_are_silently_deselected.md)", "[unmarked tests are deselected](reference_unmarked_tests_are_silently_deselected.md); [a static marker check misses rendered text](reference_a_static_marker_check_misses_rendered_text.md)"),
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--expect-mtime", type=int, required=True, help="MEMORY.md st_mtime_ns from the snapshot step; refuses on mismatch")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    if INDEX.stat().st_mtime_ns != args.expect_mtime:
        print(f"compaction: MEMORY.md changed since the snapshot (mtime {INDEX.stat().st_mtime_ns} != {args.expect_mtime}) -- re-snapshot and re-run", file=sys.stderr)
        return 2
    text = INDEX.read_text(encoding="utf-8")
    missing = [(i, old) for i, (old, _new) in enumerate(REPLACEMENTS) if text.count(old) != 1]
    for i, old in missing:
        print(f"compaction: replacement {i} occurs {text.count(old)}x (want 1): {old[:90]!r}", file=sys.stderr)
    if missing:
        print("compaction: nothing written (all-or-nothing)", file=sys.stderr)
        return 2
    new = text
    for old, rep in REPLACEMENTS:
        new = new.replace(old, rep)
    print(f"compaction: {len(text):,} -> {len(new):,} characters ({len(text) - len(new):,} removed by {len(REPLACEMENTS)} replacements)")
    if args.apply:
        INDEX.write_text(new, encoding="utf-8")
        print("compaction: written")
    else:
        print("compaction: dry run -- pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
