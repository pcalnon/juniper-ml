#!/usr/bin/env python3
"""Apply the owner's rulings of 2026-11-06 to the consolidated plan (v1.15.12) and the partition-provenance spec (v0.2.2).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-06
Status: ad-hoc -- one-off (P12 session ff40b833)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Usage: python3 <this> PLAN_IN PLAN_OUT SPEC_IN SPEC_OUT

Each edit names an anchor that must occur exactly once in its input; the script refuses (exit 1) otherwise, so a
moved anchor is a loud failure and never a silent skip. Inputs are main's copies, fetched with `gh api`.
"""

import sys
from pathlib import Path

RULINGS_0611 = (
    "\n**The owner's rulings of 2026-11-06** (v1.15.12; session `ff40b833`), with what followed the 2026-11-03 rulings:\n\n"
    "- **The data-client cap width: `<0.8.0`.** Before P5's W5 Release (data-client 0.7.0), canopy's `juniper-data` extra and recurrence's dependency widen from `<0.7.0` to `<0.8.0`, which admits W5 (0.7.0) and W11 (0.7.1) and nothing later (`…PARTITION-PROVENANCE-SPEC.md` §11.2 and §16, its v0.2.2). Until this ruling the width was an agent's inference (v1.15.11).\n"
    "- **R-DATA-2's lock gate stands**: data's second image lock PR follows R-OBS-SC-2, so 0.18.0 waits for observability 0.4.2 and service-core 0.7.2 on PyPI (§5).\n"
    "- **P3 D-07: a retro-note.** #437 (`equities_seq` 6.0.0, `task_type` `regression`) shipped unmarked in 0.17.0. 0.18.0's release notes carry a correction naming it a contract break, and juniper-data's `CHANGELOG.md` `[0.17.0]` entry gains a BREAKING tag. Neither the 0.17.0 Release body nor its artifacts change (§5).\n"
    "- **P3 D-12: answered** by the 2026-11-03 ruling. A session cuts 0.18.0 once its gates clear, and the owner approves the `pypi` gate as for every release (§5).\n"
    "- **W0.1 ran on 2026-11-04** (~14:40Z, at the owner's word), no listening service or live process importing `JuniperCascor1`: six editable `--no-deps` reinstalls, preflight and `pip check` clean. The recurrence bench then failed 4 of 41: the env held juniper-model-core **0.2.0**, and recurrence 0.8.0's `_folds.py` passes `walk_forward_folds(groups=)`, which model-core has only from **0.3.0**, so every `POST /v1/crossval` answered 500. 0.8.0's floor (`>=0.2.0`) admitted it and `pip check` could not see it. On the owner's word, model-core 0.3.2 went into the env (bench 41 of 41).\n"
    "- **juniper-recurrence 0.8.1** carries the floor fix: recurrence#229 (`2a467adb`) floors `juniper-model-core[crossval]>=0.3.0,<0.4.0`, with a test that the range admits neither 0.1.0 nor 0.2.0. The owner approved the patch; Release `juniper-recurrence-v0.8.1` was cut, its notes are ml#2454 (`8d553b41`), its image run 41935261283 succeeded, and its PyPI run 41935261358 passed the owner's gate. PyPI serves 0.8.1 with that floor (probed 2026-11-06). Owed: juniper-ml's `[recurrence]` floor to `>=0.8.1`, at the owner's word, and the stale smoke pin `juniper-model-core>=0.1.0,<0.2.0` at recurrence's `.github/workflows/publish-recurrence-model.yml:173`.\n"
    "- **The P12 worktree cleanup is done** (2026-11-04): the six trees are removed, five of them with `--force` on the owner's word after `util/ad-hoc/2026-11-04_dirty_worktree_files_landed_check.py` showed every dirty file already on `main` or in a commit of its merged PR (canopy#776, #777); `util/ad-hoc/2026-11-04_p12_force_remove_landed_worktrees.bash` refused any tree without its archive.\n"
)

PLAN_EDITS = [
    ("- **Version**: 1.15.11\n", "- **Version**: 1.15.12\n"),
    ("the W0.1 simulation 2026-11-04)", "the W0.1 simulation 2026-11-04; W0.1's run and juniper-recurrence 0.8.1's publish probed 2026-11-06)"),
    (
        "  - Planning only: this plan changes no code,",
        "  - v1.15.12 (2026-11-06) records the owner's four rulings of 2026-11-06 (the data-client caps widen to `<0.8.0`; R-DATA-2's lock gate stands; P3 D-07 is a retro-note in 0.18.0; P3 D-12 is answered), W0.1's run of 2026-11-04 and the model-core floor bug it exposed, juniper-recurrence 0.8.1's publish, which fixes that floor, and the P12 worktree cleanup's completion (XC-P12; §5; §6). Like v1.15.0, no round checks it.\n"
        "  - Planning only: this plan changes no code,",
    ),
    (
        "\n\n**Actions:**\n",
        "\n" + RULINGS_0611 + "\n**Actions:**\n",
    ),
    (
        "so both are asked at the mid-wave sitting.\n5. Data's image lock PR",
        "so both are asked at the mid-wave sitting. **Ruled 2026-11-06** (v1.15.12): D-07 is a retro-note (0.18.0's release notes name #437 a contract break, and `[0.17.0]` gains a BREAKING tag); D-12 is answered by the 2026-11-03 ruling.\n5. Data's image lock PR",
    ),
    (
        "the second follows R-OBS-SC-2 (Security step 4).\n",
        "the second follows R-OBS-SC-2 (Security step 4), and gates R-DATA-2 (owner ruling 2026-11-06).\n",
    ),
    (
        "Whether the owner counts D-12 or D-07 as answered by 0.17.0's cut on the instruction of 2026-10-08 is not recorded, so both are asked.\n",
        "Whether the owner counts D-12 or D-07 as answered by 0.17.0's cut on the instruction of 2026-10-08 is not recorded, so both are asked. **Ruled 2026-11-06**: D-07 is a retro-note in 0.18.0's release notes; D-12 is answered by the 2026-11-03 ruling (XC-P12).\n",
    ),
    (
        "`…PARTITION-PROVENANCE-SPEC.md` §11 carries the new numbers (its v0.2.1).\n",
        "`…PARTITION-PROVENANCE-SPEC.md` §11 carries the new numbers (its v0.2.1). **Ruled 2026-11-06**: both caps widen to `<0.8.0`, admitting 0.7.0 and 0.7.1 (that spec's v0.2.2).\n",
    ),
]

SPEC_EDITS = [
    ("**Version**: 0.2.1\n", "**Version**: 0.2.2\n"),
    ("**Last Updated**: 2026-11-04\n", "**Last Updated**: 2026-11-06\n"),
    (
        "left unedited except for one change: v0.2.1 (2026-11-04) renumbers the data-client releases, W5 to 0.7.0 and W11 to 0.7.1, by the owner's ruling of 2026-11-03 (§11.2, §16), and §14 and §15 still quote the numbers as reviewed.",
        "left unedited except for two changes: v0.2.1 (2026-11-04) renumbers the data-client releases, W5 to 0.7.0 and W11 to 0.7.1, by the owner's ruling of 2026-11-03 (§11.2, §16), and §14 and §15 still quote the numbers as reviewed; v0.2.2 (2026-11-06) records the owner's ruling that the consumer caps widen to `<0.8.0` (§11.2, §16).",
    ),
    (
        "  - Both are widened to `<0.8.0` **before** the Release.",
        "  - Both are widened to `<0.8.0` **before** the Release (owner ruling 2026-11-06; until then this width was an inference).",
    ),
    (
        "| 2026-11-03 | `JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A9 |\n",
        "| 2026-11-03 | `JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A9 |\n"
        "| The consumer cap width (not an OQ) | canopy's and recurrence's data-client caps widen `<0.7.0` → `<0.8.0` before W5's Release (§11.2) | 2026-11-06 | `JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A9 (its v1.15.12) |\n",
    ),
]


def apply(src: Path, dst: Path, edits) -> None:
    text = src.read_text(encoding="utf-8")
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            sys.exit(f"REFUSED {src.name}: anchor occurs {n} times: {old[:90]!r}")
        text = text.replace(old, new)
    dst.write_text(text, encoding="utf-8")
    print(f"OK {dst} ({len(edits)} edits)")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    apply(Path(sys.argv[1]), Path(sys.argv[2]), PLAN_EDITS)
    apply(Path(sys.argv[3]), Path(sys.argv[4]), SPEC_EDITS)
