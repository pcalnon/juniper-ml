#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-23_decision4_pre_switch_markers.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:   Decision 4, step 2 (juniper-ml#2034): insert a one-line marker at every published
#                location of a pre-decision-11 result that is still quoted as current, recording the
#                semantics that produced it. The originals are retained, not corrected.
#
#    Two marker classes, from #2034's inventory:
#      * SELECTED-ON -- scores from a two-way artifact whose X_test fed patience and early stopping
#        in-loop and was then reported: the T6 re-baseline, E-C at cap 64, and the P3 acceptance
#        rule and roll-up.
#      * INSTANCE -- counts scored against the generator-1.x dataset instance: the attribution
#        corpus. They are not selected-on, but a rebuild at generator >= 3.0.0 does not reproduce
#        them. "spiral keeps the exact instance every prior analysis used" is stated in five places
#        and became false across the generator bump, so all five are marked.
#
#    Every edit is an exact, counted replacement: the script refuses to write anything unless each
#    anchor occurs exactly once, so a moved or concurrently-edited anchor fails loudly instead of
#    landing a marker in the wrong place. Re-running after a successful run refuses too, because
#    the anchors now carry their markers.
#
#    Usage: python util/ad-hoc/2026-09-23_decision4_pre_switch_markers.py [--check]
#####################################################################################################################################################################################################

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

SELECTED_ON = (
    "**Pre-decision-11, selected-on (annotated 2026-09-23, juniper-ml#2034).** Measured before juniper-data 0.13.0 / "
    "juniper-cascor 0.11.0, on a two-way artifact whose `X_test` fed patience and early stopping in-loop and was then "
    "reported, so these scores are **selected-on, not held-out**. Retained as measured, and not comparable with a later "
    "result (`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §7)."
)

INSTANCE_NOTE = (
    "That instance is generator 1.x's. Since decision 11 every generator is at 3.0.0 or later, and V-1 found that each "
    "one's rows changed, so a rebuild now scores a different instance and does not reproduce these counts (juniper-ml#2034)."
)

P4 = "notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P4-STUDIES-EVIDENCE.md"
R3 = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-R3-EA-RERUN-EVIDENCE.md"
EI = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-E-I-CAP-CEILING-EVIDENCE.md"
PLAN = "notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md"
ROLLUP = "notes/JUNIPER_2026-08-08_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P3-ACCEPTANCE-ROLLUP.md"
FINDINGS = "notes/JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md"
REFERENCE = "docs/REFERENCE.md"
ATTRIBUTE = "util/snapshot_attribute.py"

POINTS_TO_T6 = (
    "**Pre-decision-11, selected-on (annotated 2026-09-23, juniper-ml#2034).** This page's figures and the T6 table it "
    "points to as current were both measured before juniper-data 0.13.0 / juniper-cascor 0.11.0, and their val scores "
    "are selected-on, not held-out. Neither is comparable with a later result."
)

EDITS: list[tuple[str, str, str]] = [
    # (file, anchor, replacement) -- the anchor must occur exactly once.
    (
        P4,
        "### E-C — noise robustness on spiral + moon (8 cells) — RE-MEASURED AT CAP 64, 2026-08-29\n\n",
        "### E-C — noise robustness on spiral + moon (8 cells) — RE-MEASURED AT CAP 64, 2026-08-29\n\n" + SELECTED_ON + "\n\n",
    ),
    (
        P4,
        "### E-A / E-I re-baselined (2026-08-26, cascor `67d7ea3`) — T6\n\n",
        "### E-A / E-I re-baselined (2026-08-26, cascor `67d7ea3`) — T6\n\n" + SELECTED_ON + "\n\n",
    ),
    (
        R3,
        "**Last Updated**: 2026-08-26\n\n> **RE-BASELINED 2026-08-26 (T6).** This grid predates cascor#514",
        "**Last Updated**: 2026-08-26\n\n" + POINTS_TO_T6 + "\n\n> **RE-BASELINED 2026-08-26 (T6).** This grid predates cascor#514",
    ),
    (
        EI,
        "**Last Updated**: 2026-08-26\n\n> **RE-BASELINED 2026-08-26 (T6).** This ladder predates cascor#514",
        "**Last Updated**: 2026-08-26\n\n" + POINTS_TO_T6 + "\n\n> **RE-BASELINED 2026-08-26 (T6).** This ladder predates cascor#514",
    ),
    (
        PLAN,
        "| **Correctness (cascor)** | Spiral baseline reaches test accuracy ≥ the value recorded in the P1 reference run, within tolerance;",
        "| **Correctness (cascor)** | Spiral baseline reaches test accuracy ≥ the value recorded in the P1 reference run, within tolerance (**pre-decision-11**: that reference and the P3 roll-up's scores are `metrics_final.json` val accuracy on a two-way artifact whose `X_test` fed early stopping in-loop -- selected-on; a re-evaluation compares held-out `test` accuracy against a re-measured reference, juniper-ml#2034);",
    ),
    (
        ROLLUP,
        "**Prior evidence**: [P0](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md)",
        SELECTED_ON + "\n\n**Prior evidence**: [P0](JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md)",
    ),
    (
        FINDINGS,
        "leave a declared seed alone. spiral therefore keeps the exact instance every analysis above used,\nso nothing here needs re-deriving for spiral; the other five become reproducible for the first\ntime.",
        "leave a declared seed alone. spiral therefore keeps the exact instance every analysis above used,\nso nothing here needs re-deriving for spiral; the other five become reproducible for the first\ntime. " + INSTANCE_NOTE,
    ),
    (
        REFERENCE,
        "| **Not `None`** | keep it. This is spiral: it stays on the exact instance every prior analysis used. |",
        "| **Not `None`** | keep it. This is spiral: it stays on the exact instance every prior analysis used -- generator 1.x's; a rebuild at generator 3.0.0 or later does not reproduce it (juniper-ml#2034). |",
    ),
    (
        REFERENCE,
        "### Counts you may quote\n\n",
        "### Counts you may quote\n\n**Pre-decision-11 dataset instance (annotated 2026-09-23, juniper-ml#2034).** The counts below were scored on 2026-08-24 against the generator-1.x instances. "
        + INSTANCE_NOTE.split(". ", 1)[1]
        + " They are retained as measured.\n\n",
    ),
    (
        REFERENCE,
        "so spiral keeps the exact instance every prior analysis used; `--dataset-seed` overrides",
        "so spiral keeps the exact instance every prior analysis used (generator 1.x's, which a rebuild at 3.0.0 or later does not reproduce: juniper-ml#2034); `--dataset-seed` overrides",
    ),
    (
        ATTRIBUTE,
        "       generator declaring none, and leaves a declared seed alone so spiral keeps the exact\n       instance every prior analysis used.\n",
        "       generator declaring none, and leaves a declared seed alone so spiral keeps the exact\n       instance every prior analysis used. That instance is generator 1.x's: since decision 11\n       every generator is at 3.0.0 or later and each one's rows changed (V-1), so a rebuild now\n       scores a different instance and does not reproduce the 2026-08-24 counts (juniper-ml#2034).\n",
    ),
    (
        ATTRIBUTE,
        "    to: spiral keeps the exact instance every prior analysis used, and the other five become\n    reproducible without silently redefining the one that already was.\n",
        "    to: spiral keeps the exact instance every prior analysis used, and the other five become\n    reproducible without silently redefining the one that already was. (Within one generator\n    version. The instance every prior analysis used is generator 1.x's, and a rebuild at 3.0.0\n    or later draws different rows: juniper-ml#2034.)\n",
    ),
]


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    texts: dict[str, str] = {}
    problems = []
    for rel, anchor, _ in EDITS:
        text = texts.setdefault(rel, (REPO / rel).read_text(encoding="utf-8"))
        count = text.count(anchor)
        if count != 1:
            problems.append(f"{rel}: anchor occurs {count} times: {anchor[:70]!r}")
    if problems:
        print("REFUSED -- nothing written:", *problems, sep="\n  ")
        return 1
    for rel, anchor, replacement in EDITS:
        texts[rel] = texts[rel].replace(anchor, replacement)
    if check_only:
        print(f"OK: {len(EDITS)} anchors found exactly once across {len(texts)} files (--check, nothing written)")
        return 0
    for rel, text in texts.items():
        (REPO / rel).write_text(text, encoding="utf-8")
    print(f"wrote {len(EDITS)} markers across {len(texts)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
