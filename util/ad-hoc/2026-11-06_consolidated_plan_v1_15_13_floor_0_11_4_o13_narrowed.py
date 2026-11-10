#!/usr/bin/env python3
"""Record the [recurrence] floor, juniper-recurrence#230, juniper-ml 0.11.4's cut and O13's narrowing in the consolidated plan (v1.15.13).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-06
Status: ad-hoc -- one-off (P12 session 61859b4a)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-06_plan_v1_15_12_spec_v0_2_2_owner_rulings.py (v1.15.12, the pattern);
         ml#2473 (the floor), ml#2482 (the 0.11.4 proposal), juniper-recurrence#230 (the model publish smoke pin)

Usage: python3 <this> PLAN_IN PLAN_OUT --release-cut-at HH:MM:SSZ --archive-pr ml#NNNN --publish-run NNNNNNNNNNN

Each edit names an anchor that must occur exactly once in its input; the script refuses (exit 1) otherwise, so a
moved anchor is a loud failure and never a silent skip. PLAN_IN is main's copy, fetched with `git show` or `gh api`.
The three cut facts are arguments because they exist only after the ceremony; the output is refused while any
placeholder survives.

O13's narrowing is the owner's answer of 2026-11-06 09:40:25Z ("Four primaries only") to the question session
0b8fa86a asked on 2026-11-05 at 01:08:12Z (that transcript's lines 2029 and 2033), relayed by the canopy Phase 16
session and checked against the transcript before it was applied.
"""

import argparse
import sys
from pathlib import Path

PLACEHOLDERS = ("RELEASE_CUT_AT", "ARCHIVE_PR", "PUBLISH_RUN")

FOLLOWED_0611 = (
    "\n**What followed the 2026-11-06 rulings** (v1.15.13; session `61859b4a`):\n\n"
    "- **juniper-ml's `[recurrence]` floor: `juniper-recurrence>=0.8.1,<0.9.0`** (ml#2473, merged 2026-11-06 as `84569b4a`, on the owner's go-ahead of that day). recurrence 0.8.0 admits juniper-model-core 0.2.0, whose `walk_forward_folds` takes no `groups=`, so an environment holding it answers 500 on every `POST /v1/crossval`; 0.8.1 floors `juniper-model-core[crossval]>=0.3.0`. A fresh install already resolved 0.8.1, so the floor moves an environment that holds 0.8.0. Pre-flighted against PyPI: `[recurrence]` resolves in 32 packages and `[all]` in 95 on Python 3.12, 3.13 and 3.14.\n"
    "- **juniper-ml 0.11.4 carries it** (owner ruling 2026-11-06: a patch, cut now). `util/release_train/detect.py` proposed 0.12.0, so the manifest's version was set to 0.11.4, as for 0.11.2. The proposal was ml#2482 (merged as `957f0e94`), with `docs/REFERENCE.md`'s co-changes from `util/ad-hoc/2026-11-06_juniper_ml_0_11_4_cut_cochanges.py`. Release `v0.11.4` was cut at RELEASE_CUT_AT on `957f0e94`; its archive is ARCHIVE_PR, and publish run PUBLISH_RUN waits at the owner's `pypi` gate (§5, R-ML-RECURRENCE-FLOOR).\n"
    "- **juniper-recurrence#230** (merged 2026-11-06 as `3529dfd9`, owner-approved): `publish-recurrence-model.yml`'s TestPyPI import smoke installed `juniper-model-core>=0.1.0,<0.2.0` while the package requires `>=0.2.0,<0.4.0`. model 0.6.0's publish (run 39197693617) installed model-core 0.1.0, printed pip's incompatibility error and passed. The smoke now installs the package's own range, `juniper-recurrence-model/tests/test_publish_smoke_pins.py` fails when the two disagree, and the model CI's change filter names the publish workflow. It first applies to the next model release's publish.\n"
    "- **O13 narrowed** (the owner's answer of 2026-11-06 09:40:25Z, \"Four primaries only\", to the question session `0b8fa86a` asked on 2026-11-05 at 01:08:12Z; relayed by the canopy Phase 16 session): the 2026-11-03 ruling, guarded session pulls, covers the cascor, data, data-client and recurrence primaries, the four the question named. Who may pull the canopy primary stays open under O13. v1.15.11 and v1.15.12 recorded the ruling as covering every primary.\n"
)

PLAN_EDITS = [
    ("- **Version**: 1.15.12\n", "- **Version**: 1.15.13\n"),
    (
        "W0.1's run and juniper-recurrence 0.8.1's publish probed 2026-11-06)",
        "W0.1's run and juniper-recurrence 0.8.1's publish probed 2026-11-06; the `[recurrence]` floor, juniper-recurrence#230 and juniper-ml 0.11.4's cut probed later that day)",
    ),
    (
        "  - Planning only: this plan changes no code,",
        "  - v1.15.13 (2026-11-06) records what followed the 2026-11-06 rulings: juniper-ml's `[recurrence]` floor `juniper-recurrence>=0.8.1` (ml#2473); juniper-recurrence#230, whose model publish smoke now installs the package's own model-core range, with a drift test; and juniper-ml 0.11.4's cut, which carries the floor (owner ruling 2026-11-06; R-ML-RECURRENCE-FLOOR, §5). It also narrows O13's 2026-11-03 ruling to the four primaries its question named, by the owner's answer of 2026-11-06: who may pull the canopy primary stays open (XC-P12; §6 A5). Like v1.15.0, no round checks it.\n"
        "  - Planning only: this plan changes no code,",
    ),
    ("\n\n**Actions:**\n", "\n" + FOLLOWED_0611 + "\n**Actions:**\n"),
    (
        "- **O13, who pulls the primaries: guarded session pulls.** A session may fast-forward a primary checkout to `origin/main` only after",
        "- **O13, who pulls the primaries: guarded session pulls, for the cascor, data, data-client and recurrence primaries.** A session may fast-forward one of those four primary checkouts to `origin/main` only after",
    ),
    (
        "A trio `--up` still waits for P3-05 (§4 Wave 1, the trio route).",
        "A trio `--up` still waits for P3-05 (§4 Wave 1, the trio route). **Narrowed 2026-11-06** (v1.15.13): the ruling covers the four primaries its question named, and who may pull the canopy primary stays open under O13 (the owner's answer of 09:40:25Z to session `0b8fa86a`'s question).",
    ),
    (
        "Who pulls the primaries stayed open under O13 until 2026-11-03, when the owner ruled guarded session pulls (XC-P12).",
        "Who pulls the cascor, data, data-client and recurrence primaries stayed open under O13 until 2026-11-03, when the owner ruled guarded session pulls (XC-P12). Who may pull the canopy primary stays open (the owner's answer of 2026-11-06; v1.15.13).",
    ),
    (
        "who pulls them ruled 2026-11-03: guarded session pulls, XC-P12)",
        "who pulls the cascor, data, data-client and recurrence primaries ruled 2026-11-03: guarded session pulls, XC-P12; the canopy primary stays open, the owner's answer of 2026-11-06, v1.15.13)",
    ),
    (
        "`[servers]` and `[all]` users whose upgrade kept cascor 0.11.0 |\n",
        "`[servers]` and `[all]` users whose upgrade kept cascor 0.11.0 |\n"
        "| **R-ML-RECURRENCE-FLOOR** (cut as juniper-ml 0.11.4, 2026-11-06, on the owner's ruling of that day; at the owner's `pypi` gate, run PUBLISH_RUN) | `[recurrence]`'s `juniper-recurrence>=0.8.1,<0.9.0` (ml#2473), the release that floors `juniper-model-core[crossval]>=0.3.0` (juniper-recurrence#229); with it, the tooling changes in `[Unreleased]` since 0.11.3 | juniper-recurrence 0.8.1 on PyPI (2026-11-06) | `pip install -U juniper-ml[recurrence]` moves an environment off recurrence 0.8.0, and so off model-core 0.2.0 |\n",
    ),
    (
        "\n- **Gate severity, from round 9.** The gate is a screen",
        "\n"
        "  - v1.15.12 is a record of the owner's four rulings of 2026-11-06, W0.1's run and juniper-recurrence 0.8.1's publish (2026-11-06). No round checks it (owner ruling 2026-10-24). Its PR, ml#2467, added no entry here; v1.15.13 adds this one.\n"
        "  - v1.15.13 is a record of the `[recurrence]` floor (ml#2473), juniper-recurrence#230, juniper-ml 0.11.4's cut and O13's narrowing (2026-11-06). No round checks it (owner ruling 2026-10-24); its facts cite PyPI's `juniper-recurrence/0.8.1` metadata, the pre-flight's output, the merge commits of ml#2473 (`84569b4a`) and ml#2482 (`957f0e94`), recurrence `main` at `3529dfd9` with its post-merge runs, the TestPyPI job log of run 39197693617 (job 117883986182), Release `v0.11.4` with publish run PUBLISH_RUN, and session `0b8fa86a`'s transcript lines 2029 and 2033.\n"
        "- **Gate severity, from round 9.** The gate is a screen",
    ),
    (
        "    - and with v1.15.11's, `2026-11-01_simulate_w0_1_env_refresh_pip_check.py` and `2026-11-04_p12_worktree_cleanup_check.bash`;",
        "    - with v1.15.11's, `2026-11-01_simulate_w0_1_env_refresh_pip_check.py` and `2026-11-04_p12_worktree_cleanup_check.bash`;\n"
        "    - with v1.15.12's, `2026-11-06_plan_v1_15_12_spec_v0_2_2_owner_rulings.py`, `2026-11-04_dirty_worktree_files_landed_check.py` and `2026-11-04_p12_force_remove_landed_worktrees.bash`;\n"
        "    - and with v1.15.13's, `2026-11-06_consolidated_plan_v1_15_13_floor_0_11_4_o13_narrowed.py`; the floor's `2026-11-06_raise_recurrence_floor_0_8_1.py` and the cut's `2026-11-06_juniper_ml_0_11_4_cut_cochanges.py` landed with ml#2473 and ml#2482;",
    ),
    (
        "(new: six worktrees' `tmp/`).",
        "(new: six worktrees' `tmp/`).\n"
        "  - by session `61859b4a` (2026-11-06), recorded with v1.15.13: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan_in", type=Path)
    ap.add_argument("plan_out", type=Path)
    ap.add_argument("--release-cut-at", required=True, help="the Release's UTC time, e.g. 14:52:10Z")
    ap.add_argument("--archive-pr", required=True, help="the archive PR, e.g. ml#2490")
    ap.add_argument("--publish-run", required=True, help="the publish.yml run id")
    args = ap.parse_args()
    fills = {"RELEASE_CUT_AT": args.release_cut_at, "ARCHIVE_PR": args.archive_pr, "PUBLISH_RUN": args.publish_run}

    text = args.plan_in.read_text(encoding="utf-8")
    for old, new in PLAN_EDITS:
        n = text.count(old)
        if n != 1:
            sys.exit(f"REFUSED {args.plan_in.name}: anchor occurs {n} times: {old[:90]!r}")
        for token, value in fills.items():
            new = new.replace(token, value)
        text = text.replace(old, new)
    left = [token for token in PLACEHOLDERS if token in text]
    if left:
        sys.exit(f"REFUSED: placeholders survive in the output: {left}")
    args.plan_out.write_text(text, encoding="utf-8")
    print(f"OK {args.plan_out} ({len(PLAN_EDITS)} edits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
