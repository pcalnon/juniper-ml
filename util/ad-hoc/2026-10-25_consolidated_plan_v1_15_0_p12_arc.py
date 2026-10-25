#!/usr/bin/env python3
"""Consolidated plan v1.15.0: a record of the recurrence x equities arc (P12) since the final census of 2026-10-10.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.14.0 -> v1.15.0);
         util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py (the probe whose results the edits state);
         notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md v1.7.16
         (the arc's own record, which the edits cite rather than re-derive)

What it records: W1.13's four releases and W1.14 (2026-10-17), the owner's P12 rulings of 2026-10-17 and 2026-10-18,
P12's W5 items in code and in recurrence 0.7.0 / 0.8.0, juniper-ml 0.11.0 and 0.11.1, and the release state the P12 rows
name (data 0.17.1 and cascor 0.12.0 served; the fix-forwards still owed). It adds R-ML-TOOLS (0.11.1, shipped) and
R-ML-SERVERS (the `[servers]` floors, next) to the release train. Other paths are not touched.

Usage
-----
    python3 util/ad-hoc/2026-10-25_consolidated_plan_v1_15_0_p12_arc.py \
        --census-time 2026-10-25THH:MMZ --probe-time 2026-10-25THH:MM:SSZ [--plan PATH] [--check]

``--census-time`` and ``--probe-time`` are when the live census and the re-probe last ran; both appear in the Snapshot.
``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Each edit applies when its
anchor matches exactly once and its replacement is absent, counts as applied when its replacement is present (for the
Snapshot edit, whose text embeds the two times, when its marker is present), and otherwise refuses. Nothing is written unless every edit applies or is already applied, and no line of the result may
exceed 512 characters (the plan's own limit: its longest line on v1.14.0 is exactly 512). ``--check`` reports without
writing; its exit status is 0 when every edit is applied, 1 when any is pending, 2 on a refusal.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
MAX_LINE = 512

# The Snapshot edit embeds the two times, so a re-run with other values must still see it as applied.
MARKERS = {"snapshot": "  - v1.15.0 takes in P12's drift to 2026-10-25, and the state of every release its rows name"}

HANDOFF = "HO/HANDOFF_2026-10-25_recurrence-equities-juniper-ml-0-11-1-published-servers-floors-next.md"
SHORT = "…0-11-1-published-servers-floors-next.md"
RPLAN = "`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`"
PROBE = "`util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py`"


def edits(census_time: str, probe_time: str) -> list[tuple[str, str, str]]:
    """(label, old, new). An append-style edit's new text starts with its old text."""
    e: list[tuple[str, str, str]] = []

    def add(label: str, old: str, new: str) -> None:
        e.append((label, old, new))

    def append(label: str, anchor: str, extra: str) -> None:
        e.append((label, anchor, anchor + extra))

    # ---- header -------------------------------------------------------------------------------------------------
    add(
        "date",
        "- **Date**: 2026-10-04 (state re-probed 2026-10-05, 2026-10-08 and 2026-10-10; corrected 2026-10-24)",
        "- **Date**: 2026-10-04 (state re-probed 2026-10-05, 2026-10-08 and 2026-10-10; corrected 2026-10-24; P12's rows and the releases they name re-probed 2026-10-25)",
    )
    add("version", "- **Version**: 1.14.0", "- **Version**: 1.15.0")
    append(
        "status",
        "and is then gated, landed and merged (Validation record).\n",
        "  - v1.15.0 (2026-10-25) is a record of the recurrence × equities arc (P12) since the final census: W1.13's four releases and W1.14 (2026-10-17), "
        "the owner's P12 rulings of 2026-10-17 and 2026-10-18, P12's W5 items, and juniper-ml 0.11.0 and 0.11.1 (XC-P12; §5). "
        "It re-probes the release rows those touch, and adds R-ML-TOOLS (shipped) and R-ML-SERVERS (next) to §5.\n"
        "    - It is not a validation round: validation ended by the owner's ruling of 2026-10-24, so no round checks v1.15.0, "
        "and each fact it adds names the probe or the record it came from. Every other path keeps v1.14.0's state and its staleness (Snapshot).\n",
    )
    append(
        "snapshot",
        "    - Every gate, cut and open PR named here as waiting or open may have moved: re-probe it before acting.\n",
        "  - v1.15.0 takes in P12's drift to 2026-10-25, and the state of every release its rows name, from three sources:\n"
        "    - the live census (`util/ad-hoc/2026-10-05_ecosystem_live_census.py`), run with `--since 2026-10-10T21:30:00Z` and re-run at "
        f"{census_time} with `--since 2026-10-25T18:12:00Z` to catch late drift. It found one open PR in the nine repositories, ml#2271, a settings change;\n"
        f"    - {PROBE} ({probe_time}): 22 PyPI versions, 11 requirement lines, 4 publish runs and 16 issues and PRs. "
        "Every one of the 46 rows with an expected state matched it (exit 0); the other 7 are reported only;\n"
        f"    - {RPLAN} v1.7.16 (ml#2317), whose Progress and \"Ruled\" blocks record the arc's work and the owner's rulings. "
        "v1.15.0 cites them rather than re-deriving them.\n"
        "    - It takes in ml#2232, ml#2260, ml#2292, ml#2306 and ml#2314 above, and ml#2319 and ml#2321 (juniper-ml 0.11.1). "
        "The rest of the drift (P1, P2, P3, the turing host plan, flood 3's record) is not taken in, so those rows stay stale.\n",
    )

    # ---- documents referenced ---------------------------------------------------------------------------------------
    add(
        "doc-w113",
        "| `…w1-13-owner-next.md` | `HO/HANDOFF_2026-10-10_recurrence-equities-w1-11-done-w1-13-owner-next.md` (P12's current handoff) |",
        "| `…w1-13-owner-next.md` | `HO/HANDOFF_2026-10-10_recurrence-equities-w1-11-done-w1-13-owner-next.md` (P12's handoff until 2026-10-17; later P12 handoffs supersede it) |\n"
        f"| `{SHORT}` | `{HANDOFF}` (P12's current handoff, landed with v1.15.0) |",
    )

    # ---- overview ---------------------------------------------------------------------------------------------------
    append(
        "ov-sentry-deploy",
        "juniper-deploy still pins data 0.17.0, whose image locks 0.4.0 and 0.7.0, and cascor 0.11.0 (`EX/round14-laneA-reprobe.md` R14A-01).",
        " Since deploy#258 (2026-10-23) it pins data 0.17.1 and cascor 0.12.0 (re-probed 2026-10-25).",
    )
    add(
        "ov-w114",
        f"     - Recurrence's fix, W1.14 (effort S), awaits owner acceptance ({RPLAN} F-S10, W1.14). It closes recurrence's relay only:",
        "     - Recurrence's fix, W1.14, was accepted by the owner on 2026-10-17 and ships from recurrence 0.6.0 (recurrence#203; §5). It closes recurrence's relay only:",
    )
    append(
        "ov-canopy-screen",
        "So the relay is open in canopy 0.8.1 and any canopy before them, juniper-deploy's `ghcr.io/pcalnon/juniper-canopy:0.8.1` among them (`EX/round13-laneB2-schedule.md` R13B2-02).\n",
        "       - canopy 0.9.0 is the first release with that screen: its `[0.9.0]` section names #683 and #685, PyPI serves it since 2026-10-17, "
        "and juniper-deploy pins it since deploy#249 (2026-10-18; re-probed 2026-10-25).\n",
    )
    append(
        "ov-source-fix",
        "only once each consumer runs the patched client (§5). data-client 0.6.0 was cut on 2026-10-10 without it (§5).",
        " PyPI serves 0.6.0 since 2026-10-17, and has no 0.5.1 or 0.6.1 (2026-10-25).",
    )
    append(
        "ov-train",
        "and cascor 0.12.0 were cut on 2026-10-10 and wait at the `pypi` gate. The fix-forwards are owed (owner ruling 2026-10-10; §5).\n",
        "     - By 2026-10-25 the owner had approved all five gates: PyPI serves model 0.4.0 from 2026-10-13, data-client 0.6.0 from 10-17, "
        "ci-tools 0.9.1 from 10-21, data 0.17.1 from 10-23 and cascor 0.12.0 from 10-25 (18:13Z). "
        "The fix-forwards are still owed: PyPI has no observability 0.4.2, service-core 0.7.2 or data 0.17.2.\n"
        "     - The P12 chain then published recurrence 0.6.0 and canopy 0.9.0 (2026-10-17), recurrence 0.6.1, 0.7.0 and 0.8.0 and model 0.5.0 and 0.6.0 "
        "(10-18 to 10-20), and juniper-ml 0.11.0 and 0.11.1 (10-21, 10-25; §5).\n",
    )
    append(
        "ov-canopy-p0",
        "   - Published canopy 0.8.1 still carries the F-CANOPY-059 P0. `main` fixed it and verified the fix live on 2026-10-04.",
        " canopy 0.9.0 is the first release with the fix (canopy#740 merged on 2026-10-16; PyPI since 2026-10-17): its `[0.9.0]` section names F-CANOPY-059.",
    )
    add(
        "ov-p12-head",
        "- **P12 runs ahead of the owner's rulings.**",
        "- **P12 ran ahead of the owner's rulings; the owner took them on 2026-10-17 and 2026-10-18.**",
    )
    add(
        "ov-p12-tail",
        "  - Their rulings are now ratify-or-revert decisions (§6 A1, A9).\n  - P12 continues from `…w1-13-owner-next.md`.",
        "  - **Phase 1 is done** (v1.15.0): W1.13's four releases are served and W1.14 shipped in recurrence 0.6.0 (2026-10-17). "
        "Every pin and floor that follows them is on `main` (XC-P12).\n"
        "  - The owner ruled R1–R8 as shipped, R5's amended band, W1.14 for 0.6.0, the dates and W5.8 (B) (§6 A1, A9). "
        "P6 OD-2, canopy#685 call (a), DC-0.6's two numbers and F-S10's data-client and cascor fixes remain.\n"
        f"  - P12 continues from `{SHORT}`.",
    )
    add(
        "scope-p12",
        '  - **P12**: its own horizon is 2027-01-15, and its dates are "owner to confirm".',
        "  - **P12**: its own horizon is 2027-01-15. The owner confirmed its dates on 2026-10-18: M0 2026-10-24, M1 2026-11-21, M2 and M3 2026-12-12, M4 2027-01-15.",
    )
    add(
        "inputs-p12",
        "and later handoffs have superseded P12's status; the current one is `…w1-13-owner-next.md`.",
        f"and later handoffs have superseded P12's status; the current one is `{SHORT}`.",
    )
    add(
        "metric-leaks",
        "F-S10's route into Sentry, by exception chain and log record) | 0 | §3 XC-SENTRY; XC-P12 |",
        "F-S10's route into Sentry, by exception chain and log record); recurrence's relay is fixed from recurrence 0.6.0 (W1.14), for a service that runs it | 0 | §3 XC-SENTRY; XC-P12 |",
    )

    # ---- §2 state at a glance ---------------------------------------------------------------------------------------
    add(
        "s2-p4",
        "| P4 release | Three releases are served (observability 0.4.1, service-core 0.7.1, data 0.17.0; 10-10), and five wait at the `pypi` gate "
        "(ci-tools 0.9.1, recurrence-model 0.4.0, data-client 0.6.0, data 0.17.1, cascor 0.12.0). canopy#740 proposed canopy 0.9.0 "
        "(open at the final census, 2026-10-10T21:30Z). P4's Wave 4 waits on Docker Hub secrets. | §5 (the fix-forwards; the gates) | T1 |",
        "| P4 release | Served on 10-10: observability 0.4.1, service-core 0.7.1, data 0.17.0. The five then at the `pypi` gate are served "
        "(re-probed 2026-10-25): model 0.4.0, data-client 0.6.0, ci-tools 0.9.1, data 0.17.1 (10-23) and cascor 0.12.0 (10-25). "
        "The P12 chain added canopy 0.9.0, recurrence 0.6.0–0.8.0, model 0.5.0 and 0.6.0, and juniper-ml 0.11.0 and 0.11.1. "
        "R-OBS-SC-2 and R-DATA-2 are owed. P4's Wave 4 waits on Docker Hub secrets (10-10). | §5 (the fix-forwards; R-ML-SERVERS) | T1 |",
    )
    add(
        "s2-p12",
        "| P12 equities | Phase 0 is closed out (ml#2151), except W0.1's service-core half (owner). Phase 1's waves 1 and 2 merged (10-05, 10-09) "
        "pending A9's rulings, R7 among them; its code is done except W1.14 and 2c. W1.11 is done, and W1.13 started on 10-10 (`…w1-13-owner-next.md`). "
        "The review of `…EQUITIES-CV-BLOWUP-INVESTIGATION.md` is done (ml#2168: GO upheld), so R5 can be ruled. "
        "Next: the owner's W1.13 cuts, W1.14, A1 (F-S10's fixes and their vehicle) and A9. | §6 A1, A9; S0.9; S0.11 | T0/T2 |",
        "| P12 equities | 2026-10-25: Phase 1 is done. W1.13's releases are served and W1.14 shipped in recurrence 0.6.0 (10-17), then the pins and floors. "
        "The owner ruled most of A1 and A9 on 10-17/18. P12's W5 items are on `main`; their model and service halves ship in recurrence 0.7.0/0.8.0 "
        "and model 0.5.0/0.6.0, and W5.7 (data#486) waits for a data release. juniper-ml 0.11.0 and 0.11.1 carry the floors. "
        "W0.1's service-core half: owner (XC-P12). | §5 R-ML-SERVERS; client 0.3.1 (owner); §6 A1, A9's rest | T1/T2 |",
    )

    # ---- §3 XC-P12 --------------------------------------------------------------------------------------------------
    append(
        "xc-done",
        "recurrence-model 0.4.0 and data-client 0.6.0 are cut and wait at the `pypi` gate (§5).\n",
        f"\n**W1.13 and W1.14 are done, and P12 went on to its W5 items** (v1.15.0, from {RPLAN} v1.7.16; every release re-probed 2026-10-25):\n\n"
        "- **W1.14** was accepted by the owner on 2026-10-17 and merged as recurrence#203 (`aeccd35f`) before recurrence 0.6.0's cut: vehicle (b). "
        "The published 0.6.0 wheel serves fixed 5xx phrases and refuses a padded key at load; the 0.5.0 control relays the key in its 502 detail.\n"
        "- **W1.13's four releases** are served: model 0.4.0 (2026-10-13), data-client 0.6.0 (10-17 05:16Z), and recurrence 0.6.0 and canopy 0.9.0 "
        "(10-17 22:08Z). The owner delegated the last two cuts and approved every gate (Ruled 2026-10-17).\n"
        "- **recurrence 0.6.0 shipped without the owner's floors ruling of 2026-10-10** (model `>=0.4.0`, data-client `>=0.6.0`), "
        "so an upgrade over 0.5.0 kept the old pair. recurrence#206 raised them, and 0.6.1 serves them (2026-10-18 19:02Z).\n"
        "- **The pins and floors followed.** juniper-deploy#249 pinned recurrence 0.6.0 and canopy 0.9.0 after both deploy smokes passed on its head "
        "(8/8 and 3/3, by GHCR digest); #251, #255 and #257 moved recurrence to 0.6.1, 0.7.0 and 0.8.0. "
        "In juniper-ml, #2232 widened the `[recurrence]` ceilings and floored canopy `>=0.9.0` and recurrence `>=0.6.0`; "
        "#2243, #2260 and #2292 then raised them step by step, to recurrence `>=0.8.0,<0.9.0` and model `>=0.6.0,<0.7.0`.\n"
        "- **2c's name is settled** (owner ruling 2026-10-18): `${RUN_DIR}/snapshots`. juniper-ml's `util/isolated_stack.bash` sets it, "
        "and juniper-canopy#751 (open) has canopy Lane B adopt it.\n"
        "- **P12's W5 items.** W5.10 (recurrence#208), W5.9 and W5.8 (B) (recurrence#209, #212), W5.2 (recurrence#214, #215; the bench row #219), "
        "W5.4 with R5's band (ml#2262), and W5.5 and W5.6 (ml#2273) merged. Their model and service halves were released in model 0.5.0 and 0.6.0 "
        "and recurrence 0.7.0 and 0.8.0 (2026-10-19, 10-20); the juniper-ml items are driver tooling, which no package ships. "
        "W5.7 merged as data#486 and waits for juniper-data's next release (§5).\n"
        "- **juniper-ml 0.11.0 and 0.11.1** carry the meta-package's floors (2026-10-21, 2026-10-25; §5). "
        "The driver follow-ups filed on 2026-10-10 merged: ml#2211 as ml#2316, and ml#2210 as ml#2320.\n",
    )
    append(
        "xc-act1",
        "O7's ruling now also covers what remains of Y2 wave 2 after W1.10 and W1.12 (§6 A5).\n",
        "   - **Ruled 2026-10-18** (" + RPLAN + ", \"Ruled 2026-10-18, turing deploy-smokes session\"): R1–R8 are confirmed as shipped, "
        "R6 stands as applied, and R1's preset is not commissioned. The APD-ML OD-2 and canopy#685 call (a) are not among those rulings, so they stay open (§6 A1).\n",
    )
    append(
        "xc-act2",
        "A fix reaches a running service only through §4 Wave 1's \"F-S10 delivery\" routes.\n",
        "\n   **Ruled 2026-10-17**: W1.14 is accepted, and vehicle (b) carries it: recurrence 0.6.0 and every later release. "
        "Still open: the source fix in the data client and a cascor fix (cascor 0.12.0, served on 2026-10-25, names none).\n",
    )
    add(
        "xc-act3",
        "has had its consensus review: three rounds, GO upheld (ml#2168, 2026-10-05). R5 can now be ruled. It gates only W5.4.",
        "has had its consensus review: three rounds, GO upheld (ml#2168, 2026-10-05). "
        "R5 was ruled on 2026-10-18 (the amended band, re-measured on W5.2's population), and W5.4 encoded it (ml#2262).",
    )
    append(
        "xc-act5",
        "is an OWNER-ACTION. A live cascor on `:8202` imports from that environment (§8).",
        " Ruled 2026-10-18: the owner runs it at the next cascor restart on the original host, and M0 closes on its date (2026-10-24) with it as an owner follow-up.",
    )
    add(
        "xc-act6",
        "6. **Do not dispatch W0.1–W0.9, or Phase 1's waves 1 and 2, again.** Wave 2 and W1.11 are done. Further P12 work follows `…w1-13-owner-next.md`: "
        "W1.13's cuts, in the order data-client 0.6.0, recurrence-model 0.4.0, recurrence 0.6.0 and canopy 0.9.0, and W1.14, which awaits the owner.",
        "6. **Do not dispatch W0.1–W0.9, Phase 1 (W1.1–W1.14) or the done W5 items again.** Further P12 work follows "
        f"`{SHORT}`: R-ML-SERVERS (§5), the recurrence-client 0.3.1 cut, the W1.11 and W1.12 smokes on the 0.8.0 image, "
        "and the owner's open items (§6 A1, A9).",
    )

    # ---- §4 the program ---------------------------------------------------------------------------------------------
    add(
        "sit-a1",
        "   - A1: P12 ratify or revert; F-S10's fixes and their vehicle (time-bound, §6 A1); when to swap W0.1's service-core half;",
        "   - A1's remainder: P6 OD-2, canopy#685 call (a), and F-S10's data-client and cascor fixes (§6 A1). The rest of A1 was ruled on 2026-10-17 and 2026-10-18;",
    )
    add(
        "sit-a9",
        "   - A9, the P12 rulings Phase 1 applied pending, R7 among them;",
        "   - A9's remainder: DC-0.6's two numbers (§6 A9). The rest of A9 was ruled on 2026-10-18;",
    )
    append(
        "s09",
        "so R5 joins Group B's P12 asks.",
        " Overtaken: the owner ruled those asks, R5 among them, in the P12 sessions of 2026-10-17 and 2026-10-18 (XC-P12).",
    )
    append(
        "s09-name",
        "and settle the snapshot-directory name (`…p1-wave1-in-flight.md`).",
        " The name is settled (`${RUN_DIR}/snapshots`, owner ruling 2026-10-18; juniper-canopy#751); the frozen bodies' comparison is not re-probed.",
    )
    append(
        "s011",
        "- **S0.11 — F-S10**, for whatever the owner accepts at §6 A1.",
        " W1.14's part is done: it merged with its tests (recurrence#203) and ships from recurrence 0.6.0. What remains is the data-client and cascor fixes, if A1 accepts them.",
    )
    append(
        "route-rec",
        "so a host leg needs that primary to hold the fix first (`EX/round7-laneB1-safety.md` R7B1-12).\n",
        "  - **Done for PyPI and the image** (v1.15.0): vehicle (b), recurrence 0.6.0 and every later release; juniper-deploy pins 0.8.0 (deploy#257). "
        "Whether the recurrence primary in `JuniperCascor1` holds W1.14 was not re-probed, so host legs follow the bullets below.\n",
    )
    append(
        "after-rdata-mla",
        "- **R-ML-a**: the X8 floor (merged as ml#2190; unreleased), ml#2062's fix (P4 D-1, mid-wave; open), the `[recurrence]` caps (unchanged), and an `[all]` dry-run resolve.",
        " **Shipped as juniper-ml 0.11.0** (2026-10-21), with the floor, the widened caps and an `[all]` pre-flight against real PyPI (ml#2292). "
        "ml#2062's fix did not ride it, and its issue is open (§5).",
    )
    add(
        "exit-vehicle",
        "  - if A1 chose vehicle (a): the recurrence fix released; under either vehicle,",
        "  - if A1 chose vehicle (a) (it chose (b) on 2026-10-17): the recurrence fix released; under either vehicle,",
    )
    add(
        "wave2-p12",
        "| P12 equities | M0 (after W0.1's service-core half) · Phase 1: waves 1–2 merged pending A9 (R7 added); W1.11 done; W1.13 in progress → M1 · "
        "W1.1b (P12-11, optional, after R1) · R5, rulable now; W5.4 in Wave 4 |",
        "| P12 equities | M0 closes on its date (10-24); W0.1's service-core half is an owner follow-up · Phase 1 done (10-17) → M1 (11-21; "
        "the W1.11/W1.12 smokes owed on 0.8.0) · W1.1b not commissioned · W5.4 done · next: R-ML-SERVERS |",
    )
    append(
        "wave4-p12",
        "F-P8 (Major since ml#2168, with a W5.7 guard) and the rest of P12-48.",
        " By 2026-10-25, W5.2, W5.4–W5.6 and W5.8 (B)–W5.10 are done, W5.7 is merged (data#486) and unreleased, and W5.11 was declined (10-18). "
        "W1.14's canopy follow-up is juniper-canopy#738.",
    )

    # ---- §5 release train -------------------------------------------------------------------------------------------
    add(
        "r-canopy-a",
        "| **R-CANOPY-A**: juniper-canopy (PyPI 0.8.1; canopy#740 proposed 0.9.0, open at the final census, 2026-10-10T21:30Z) |",
        "| **R-CANOPY-A** (shipped as canopy 0.9.0 on 2026-10-17, the P12 chain's canopy release; note below) |",
    )
    add(
        "r-data-2",
        "| **R-DATA-2** (owed; owner ruling 2026-10-10): juniper-data 0.17.2, or 0.17.1 only if the owner withdraws the cut 0.17.1, its Release, tag and image with it (note below) | "
        "P3-03 (`d1c66a11` and `94ce8b1f`, rebased) and P3-09, beside data#478's lock and data#479's floors |",
        "| **R-DATA-2** (owed; owner ruling 2026-10-10): juniper-data 0.17.2; 0.17.1 is served since 2026-10-23, which ends the withdrawal option (note below) | "
        "P3-03 (`d1c66a11` and `94ce8b1f`, rebased) and P3-09, beside data#478's lock and data#479's floors; and P12's W5.7, a default change (note below) |",
    )
    add(
        "r-cascor",
        "Bypassed in part: cascor#712 bumped it to 0.12.0 on 2026-10-10 (note below) |",
        "Bypassed in part: cascor#712 bumped it to 0.12.0 on 2026-10-10; served 2026-10-25 (note below) |",
    )
    add(
        "r-fs10",
        "| **F-S10's release vehicle** (owner ruling, §6 A1) | The recurrence relay fix (W1.14) | Either (a) recurrence 0.5.1 from the `juniper-recurrence-v0.5.0` tag "
        "with only the fix (an exception to the `origin/main` rule; CI by hand, §4 Wave 1), or (b) the P12-chain recurrence release with its gates "
        "(after W1.13; R-ML-a's widened `[recurrence]` caps admit 0.6.0) |",
        "| **F-S10's release vehicle** (shipped; owner ruling 2026-10-17: (b)) | The recurrence relay fix (W1.14; recurrence#203) | Either (a) recurrence 0.5.1 "
        "from the `juniper-recurrence-v0.5.0` tag with only the fix, or (b) the P12-chain recurrence release. (b) was taken: recurrence 0.6.0 "
        "(PyPI 2026-10-17) and every later release carry it, and no 0.5.1 exists |",
    )
    add(
        "r-p12-chain",
        "| **The P12 chain**: the first data-client, model, recurrence and canopy releases with P12 W1.x,",
        "| **The P12 chain** (done 2026-10-17; note below): the first data-client, model, recurrence and canopy releases with P12 W1.x,",
    )
    add(
        "r-ml-a",
        "| **R-ML-a**: juniper-ml (PyPI 0.10.0), after R-DATA | The X8 floor (merged as ml#2190); ml#2062's `[servers]` fix (P4 D-1; open); "
        "the `[recurrence]` caps (unchanged), widened before the P12 chain's recurrence and canopy cuts (cap first) | "
        "R-DATA on PyPI (met on 2026-10-10); an `[all]` dry-run resolve |",
        "| **R-ML-a** (shipped with R-ML-b as juniper-ml 0.11.0, 2026-10-21; note below), after R-DATA | The X8 floor (merged as ml#2190); "
        "ml#2062's `[servers]` fix (P4 D-1; open, and not in 0.11.0); the `[recurrence]` caps (unchanged), widened before the P12 chain's recurrence "
        "and canopy cuts (cap first) | R-DATA on PyPI (met on 2026-10-10); an `[all]` dry-run resolve (met, ml#2292) |",
    )
    add(
        "r-ml-b",
        "| **R-ML-b**, after the P12 chain; W10 later | The P12-chain floors; later, W10's floors once W5 and W6 publish | Each floor read from the published wheel | — |",
        "| **R-ML-b** (shipped with R-ML-a as 0.11.0), after the P12 chain; W10 later | The P12-chain floors: `[servers]` canopy `>=0.9.0`; "
        "`[recurrence]` recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`. Later, W10's floors once W5 and W6 publish | "
        "Each floor read from the published wheel; PyPI's 0.11.x metadata carries them (2026-10-25) | — |\n"
        "| **R-ML-TOOLS** (shipped as juniper-ml 0.11.1, 2026-10-25) | The `[tools]` floors on the shared security patches, "
        "`juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0` (ml#2314). Rated Medium, CWE-201, CWE-755 and CWE-770 "
        "(owner, 2026-10-25), as the releases it floors | R-OBS-SC on PyPI (met on 2026-10-10); proposal ml#2319, archive ml#2321; "
        "the owner approved the gate (run 40178692483) | `[tools]` and `[all]` users whose upgrade kept observability 0.4.0 or service-core 0.7.0 |\n"
        "| **R-ML-SERVERS** (next; unblocked on 2026-10-25): a juniper-ml patch | The `[servers]` floors `juniper-data>=0.17.1` and "
        "`juniper-cascor>=0.12.0`, which floor the shared security patches; ml#2062's fix if it is ready | Both on PyPI (met: data 2026-10-23, "
        "cascor 2026-10-25). The floors PR first, pre-flighted for `[servers]` and `[all]` against real PyPI; then the owner's cut, gate and rating | "
        "`[servers]` and `[all]` users whose upgrade keeps data 0.17.0 or cascor 0.11.0 |",
    )
    append(
        "note-dc-patch",
        "but not canopy. R-DC-PATCH's 0.5.1 branch is unchanged; the forward-port targets a 0.6.x patch.\n",
        "- **Re-probed 2026-10-25**: PyPI serves 0.6.0 since 2026-10-17 and has no 0.5.1 or 0.6.1, and canopy 0.9.0 admits 0.6 too (`<0.7.0`). "
        "So R-DC-PATCH-6 is the route for every unpinned consumer, and R-DC-PATCH reaches only installs held below 0.6.\n",
    )
    append(
        "note-data",
        "That choice is time-bound while the gate waits (§6, mid-wave sitting; `EX/round14-laneA-reprobe.md` R14A-06).\n",
        "- **Re-probed 2026-10-25**: the owner approved the gate. PyPI serves 0.17.1 from 2026-10-23T23:49Z (run 38084468369), "
        "and juniper-deploy pins it since deploy#258. So R-DATA-2 is 0.17.2, which PyPI does not have yet.\n"
        "- R-DATA-2 would also carry P12's W5.7 (data#486, merged 2026-10-19, in `[Unreleased]`). W5.7 changes a default: "
        "a multi-symbol request that loses a named symbol gets 422 instead of a silently partial dataset. "
        f"Whether a 0.17.x patch may carry that is the owner's call ({RPLAN}, Progress 2026-10-19).\n",
    )
    append(
        "note-cascor",
        "- So R-CASCOR is being cut ahead of its gates (P3-05's validation of cascor#690, P3-08) and without a cascor F-S10 fix. "
        "Whether a fix-forward is owed for it is the owner's (mid-wave sitting).\n",
        "- **Re-probed 2026-10-25**: the owner approved the gate. PyPI serves 0.12.0 from 18:13:28Z (run 38085392643 green), "
        "and juniper-deploy pins it since deploy#258 (2026-10-23). The fix-forward question stands.\n",
    )
    append(
        "note-p12",
        "- There is no forward-port yet: 0.6.0 carries F-S10 (above), and R-DC-PATCH-6 is the route for consumers on 0.6.x.\n",
        "\n**The P12 chain, at 2026-10-25 (v1.15.0).** Done. PyPI served model 0.4.0 first (2026-10-13), then data-client 0.6.0 (10-17 05:16Z), "
        "then recurrence 0.6.0 and canopy 0.9.0 (10-17 22:08Z). The data-client, model and recurrence wheels were each read on publication "
        f"against a control that fails ({RPLAN}, W1.13's status row).\n\n"
        "- canopy 0.9.0 was also R-CANOPY-A: its `[0.9.0]` section names F-CANOPY-059, #678, #683, #685 and #702. It was cut before R-OBS-SC-2 existed, "
        "so ahead of that row's lock-PR gate; whether P3-06, the O3 wording and A4 were met is not re-probed.\n"
        "- recurrence 0.6.0 shipped without the owner's floors ruling of 2026-10-10, and 0.6.1 carries it (2026-10-18). "
        "P12's W5 items followed in model 0.5.0 and 0.6.0 and recurrence 0.7.0 and 0.8.0 (2026-10-19, 10-20).\n"
        "- R-ML-a and R-ML-b shipped together as juniper-ml 0.11.0 (2026-10-21). Its `[recurrence]` ceilings rose on `main` the day after the cuts "
        "(ml#2232, 2026-10-18), and until 0.11.0 `juniper-ml[recurrence]` resolved recurrence 0.5.x. R-ML-TOOLS followed as 0.11.1 (2026-10-25).\n"
        "- There is still no forward-port: PyPI has no data-client 0.6.1.\n",
    )
    add(
        "order",
        "4. R-ML-a.\n5. The P12 chain (in progress since 2026-10-10).\n6. R-ML-b.\n",
        "4. R-ML-a: shipped as juniper-ml 0.11.0 (2026-10-21), with R-ML-b.\n"
        "5. The P12 chain: done (2026-10-17), and carried on through recurrence 0.8.0 (2026-10-20).\n"
        "6. R-ML-b: shipped with R-ML-a. R-ML-TOOLS followed as 0.11.1 (2026-10-25).\n"
        "7. R-ML-SERVERS, now that data 0.17.1 and cascor 0.12.0 are served. It waits on none of the steps above.\n",
    )
    append(
        "dc06",
        "The §9 edge into P5 W10 depends on that width (`EX/round1-laneA2-residue-P4-P5-P11-P12.md` A2-02).\n",
        "\n**Canopy's width is settled** (v1.15.0): canopy 0.9.0's `juniper-data` extra admits `juniper-data-client>=0.5.0,<0.7.0`, and recurrence 0.8.0 requires "
        "`>=0.6.0,<0.7.0` (PyPI metadata, 2026-10-25). Left for A9: the number P5's W5 takes, and R-DC-PATCH-6's.\n",
    )

    # ---- §6 owner packet --------------------------------------------------------------------------------------------
    add(
        "s6-ruled",
        "**A1 is time-bound.** W1.13 started on 2026-10-10",
        f"**A1 and A9 since the final census** (v1.15.0; {RPLAN}, \"Ruled 2026-10-17\" and \"Ruled 2026-10-18, turing deploy-smokes session\"):\n\n"
        "- **A1, ruled**: R6 stands as applied; W1.14 is accepted, and vehicle (b) carried it (recurrence 0.6.0); "
        "W0.1's swap is the owner's, at the next cascor restart on the original host.\n"
        "- **A1, still open**: P6 OD-2, canopy#685 call (a), the data-client source fix and a cascor fix, and whether host recurrence legs take a port of W1.14.\n"
        "- **A9, ruled**: R1–R8 confirmed as shipped, R1's preset not commissioned; the dates confirmed (M0 2026-10-24, M1 2026-11-21, "
        "M2 and M3 2026-12-12, M4 2027-01-15); W5.8 (B), W5.9 and W5.10 accepted for recurrence 0.7.0 and model 0.5.0; W5.11 declined.\n"
        "- **A9, still open**: DC-0.6's two numbers, the one P5's W5 takes and R-DC-PATCH-6's (§5). Canopy's width is settled by canopy 0.9.0.\n\n"
        "**A1 is time-bound.** W1.13 started on 2026-10-10",
    )
    append(
        "a1-deadline",
        "until R-DC-PATCH-6 ships (`EX/round14-laneB-attack.md` R14B-14).\n",
        "The deadline passed on 2026-10-17 (v1.15.0): W1.14 merged before recurrence 0.6.0's cut, and data-client 0.6.0's gate was approved, "
        "so its unfixed text is served.\n",
    )

    # ---- §7 / §8 / §9 -----------------------------------------------------------------------------------------------
    add(
        "s71-item3",
        "3. F-S10's fixes, as one item (at least two rounds): W1.14, plus",
        "3. F-S10's fixes, as one item (at least two rounds): W1.14 (merged and released on 2026-10-17 without these rounds; v1.15.0), plus",
    )
    add(
        "s8-extras",
        "The floor merged (ml#2190); next, the `[recurrence]` caps |",
        "The floor merged (ml#2190); the `[recurrence]` caps and floors followed (ml#2232, #2243, #2260, #2292), with the `[tools]` floors (ml#2314), "
        "released as 0.11.0 and 0.11.1; next, R-ML-SERVERS (§5) |",
    )
    add(
        "s8-routers",
        "| W1.14 (F-S10), P5-16, P5-26, P12-15, P12-24..30 | W1.14 first |",
        "| W1.14 (F-S10), P5-16, P5-26, P12-15, P12-24..30 | W1.14 first: merged 2026-10-17 (recurrence#203) |",
    )
    add(
        "s8-deploy",
        "P4-14's data pin merged (deploy#243); the recurrence and canopy pins follow W1.13 |",
        "P4-14's data pin merged (deploy#243); the recurrence and canopy pins followed W1.13 (deploy#249; recurrence 0.8.0 since deploy#257), "
        "and deploy#258 pins data 0.17.1 and cascor 0.12.0 |",
    )
    add(
        "s9-vehicle",
        "| F-S10's release vehicle (§5) | W1.14 accepted, merged and validated; the owner's vehicle ruling (§6 A1) | Hard |",
        "| F-S10's release vehicle (§5) | W1.14 accepted, merged and validated; the owner's vehicle ruling (§6 A1) | Hard. Met on 2026-10-17: vehicle (b), recurrence 0.6.0 |",
    )
    add(
        "s9-dc-cut",
        "Bypassed: 0.6.0 was cut on 2026-10-10 without the forward-port and waits at its `pypi` gate.",
        "Bypassed: 0.6.0 was cut on 2026-10-10 without the forward-port and is served since 2026-10-17.",
    )
    add(
        "s9-phase1",
        "applied R7 pending (XC-P12); the owner ratifies or reverts |",
        "applied R7 pending (XC-P12). The owner ratified them on 2026-10-18, with the dates; DC-0.6's numbers remain |",
    )
    add(
        "s9-m1",
        "M1 waits on W1.13, W1.14, 2c and the rulings |",
        "W1.13, W1.14, 2c's name and the Phase 1 rulings were done by 2026-10-18. Every M1 landing is on `main`, and the W1.11 and W1.12 smokes are owed on the 0.8.0 image |",
    )
    add(
        "s9-2c",
        "2c must reconcile the snapshot-directory name with W1.10's |",
        "2c must reconcile the snapshot-directory name with W1.10's: settled as W1.10's on 2026-10-18 (juniper-canopy#751) |",
    )
    add(
        "s9-w10",
        "| Conditional. A narrow cap forces a second recurrence and canopy release |",
        "| Conditional. A narrow cap forces a second recurrence and canopy release. Recurrence 0.8.0 and canopy 0.9.0 both cap data-client at `<0.7.0` |",
    )

    # ---- §11 / §12 --------------------------------------------------------------------------------------------------
    append(
        "h22-canopy",
        "with no outbound-key screen in `src/settings.py` at `v0.8.1`. juniper-deploy pins `ghcr.io/pcalnon/juniper-canopy:0.8.1` (Overview 2; `EX/round13-laneB2-schedule.md` R13B2-02).\n",
        "  - canopy 0.9.0 carries that screen, and juniper-deploy pins 0.9.0 since deploy#249 (2026-10-18). A running canopy closes its own relay only after a restart on it (v1.15.0).\n",
    )
    add(
        "h22-dc",
        "  - data-client 0.6.0, cut on 2026-10-10 and waiting at its `pypi` gate, carries F-S10 unfixed",
        "  - data-client 0.6.0, cut on 2026-10-10 and served since 2026-10-17, carries F-S10 unfixed",
    )
    add(
        "h22-lift-rec",
        "    - recurrence's bodies and logs, once recurrence runs W1.14;",
        "    - recurrence's bodies and logs, once recurrence runs W1.14 (recurrence 0.6.0 and later; juniper-deploy pins 0.8.0);",
    )
    add(
        "h22-lift-canopy",
        "which canopy 0.8.1 lacks;",
        "which canopy 0.8.1 lacks and canopy 0.9.0 has;",
    )
    add(
        "risk-fs10",
        "the owner's `pypi` gates on data-client 0.6.0 and the coming recurrence 0.6.0 |",
        "the owner's `pypi` gates on data-client 0.6.0 and the coming recurrence 0.6.0 (both approved on 2026-10-17; recurrence 0.6.0 carries W1.14) |",
    )

    # ---- appendices -------------------------------------------------------------------------------------------------
    add(
        "appA-head",
        "- **P12** (`EX/extraction-P12-equities.md`; current status in `…w1-13-owner-next.md`):",
        f"- **P12** (`EX/extraction-P12-equities.md`; current status in `{SHORT}`):",
    )
    add(
        "appA-p0",
        "  - **Done, phase 0** (merged; owner ratification pending, §6 A1):",
        "  - **Done, phase 0** (merged; R6 ratified on 2026-10-18, §6 A1):",
    )
    add(
        "appA-w1",
        "(merged on 2026-10-05; owner ratification of R1's default half, R2, data#451's reading of R3 and R8's alternative pending, §6 A9):",
        "(merged on 2026-10-05; R1's default half, R2, data#451's reading of R3 and R8's alternative ratified on 2026-10-18, §6 A9):",
    )
    add(
        "appA-w2",
        "(merged on 2026-10-09; owner ratification of R7 pending, §6 A9): P12-12 (W1.2: canopy#733, R7 pending),",
        "(merged on 2026-10-09; R7 ratified on 2026-10-18, §6 A9): P12-12 (W1.2: canopy#733),",
    )
    append(
        "appA-rest",
        "P12-17's display half (W1.7: canopy#732).\n",
        "  - **Done, the rest of Phase 1** (v1.15.0): P12-21 (W1.11: deploy#243, deploy#245, ml#2190; 2026-10-10), P12-23 (W1.13: the four releases "
        "of 2026-10-17, then the pins and floors; XC-P12) and P12-W1.14 (recurrence#203, in recurrence 0.6.0).\n",
    )
    add(
        "appA-t0",
        "  - **T0**: P12-01's service-core swap (owner); P12-W1.14 (F-S10; added to `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` by ml#2151, "
        "after extraction, so not a validation finding; owner acceptance, then a session fix)",
        "  - **T0**: P12-01's service-core swap (owner, at the next cascor restart; ruled 2026-10-18). P12-W1.14 (F-S10; added to "
        "`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` by ml#2151, after extraction, so not a validation finding) is done (above)",
    )
    add("appA-t1", "P12-23 →the P12 chain\n", "P12-23 →the P12 chain (done)\n")
    add(
        "appA-t2",
        "  - **T2**: Phase 1's rest: P12-11 (W1.1b, optional, after R1).",
        "  - **T2**: Phase 1's rest: P12-11 (W1.1b, optional, after R1), not commissioned (R1, ruled 2026-10-18).",
    )
    append(
        "appA-t5",
        "the R-6/H-9 rows of `…CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`, and P4-Q6.\n",
        "    - By 2026-10-25: W5.2, W5.4, W5.5, W5.6, W5.8 (B), W5.9 and W5.10 are done; W5.7 is merged (data#486) and unreleased; W5.11 was declined (XC-P12).\n",
    )
    add(
        "appB-2",
        "| 2 | R-CANOPY-A / the P12-chain canopy release |",
        "| 2 | R-CANOPY-A / the P12-chain canopy release (one release in the event: canopy 0.9.0) |",
    )
    add(
        "appB-6",
        "| 6 | R-ML-a / R-ML-b |",
        "| 6 | R-ML-a / R-ML-b (one release in the event: juniper-ml 0.11.0, without P4-21's ml#2062) |",
    )

    # ---- validation record / changed by this plan -------------------------------------------------------------------
    append(
        "drift-list",
        "marked stale (Snapshot), and no round checks it (owner ruling 2026-10-24).\n",
        "  - v1.15.0 is a record of P12's drift to 2026-10-25 and of the releases P12's rows name (Snapshot). No round checks it (owner ruling 2026-10-24); "
        f"its facts cite the census, {PROBE} and {RPLAN} v1.7.16.\n",
    )
    add(
        "changed-adhoc",
        "and `2026-10-24_sequence_safety_on_paths.py`;\n",
        "and `2026-10-24_sequence_safety_on_paths.py`; then, with v1.15.0's PR, `2026-10-25_p12_arc_state_reprobe.py` and "
        "`2026-10-25_consolidated_plan_v1_15_0_p12_arc.py`;\n",
    )
    append(
        "changed-handoff",
        "    - `HO/HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md`, by session `560c1ec5`.\n",
        f"  - with v1.15.0's PR, the recurrence × equities arc's handoff `{HANDOFF}` (P12's, not this plan's).\n",
    )
    append(
        "changed-memory",
        "`reference_signed_commit_api_499_on_large_payloads.md` and the index `MEMORY.md`.",
        "\n  - by session `2988c32a` (2026-10-25), with v1.15.0: `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.",
    )
    return e


def apply(text: str, plan: list[tuple[str, str, str]]) -> tuple[str, list[tuple[str, str]]]:
    report = []
    for label, old, new in plan:
        if new in text:
            report.append((label, "already applied"))
            continue
        marker = MARKERS.get(label)
        if marker and marker in text:
            report.append((label, "already applied (with other --census-time/--probe-time values)"))
            continue
        count = text.count(old)
        if count != 1:
            report.append((label, f"REFUSED: anchor matches {count} times"))
            continue
        text = text.replace(old, new, 1)
        report.append((label, "applied"))
    return text, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--census-time", required=True, help="when the live census last ran, e.g. 2026-10-25T19:40Z")
    ap.add_argument("--probe-time", required=True, help="when the re-probe last finished, e.g. 2026-10-25T19:36:41Z")
    ap.add_argument("--plan", type=Path, default=_PLAN)
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args()
    for name, value in (("--census-time", args.census_time), ("--probe-time", args.probe_time)):
        if not re.fullmatch(r"2026-\d\d-\d\dT\d\d:\d\d(:\d\d)?Z", value):
            print(f"{name} must look like 2026-10-25T19:40Z, got {value!r}", file=sys.stderr)
            return 2

    original = args.plan.read_text(encoding="utf-8")
    updated, report = apply(original, edits(args.census_time, args.probe_time))
    for label, state in report:
        print(f"{label:<18} {state}")
    refused = [label for label, state in report if state.startswith("REFUSED")]
    long_lines = [(n, len(line)) for n, line in enumerate(updated.split("\n"), 1) if len(line) > MAX_LINE]
    for n, length in long_lines:
        print(f"line {n}: {length} characters, over the {MAX_LINE} limit")
    if refused or long_lines:
        print("refusing: nothing written", file=sys.stderr)
        return 2
    pending = [label for label, state in report if state == "applied"]
    if args.check:
        return 1 if pending else 0
    if updated != original:
        args.plan.write_text(updated, encoding="utf-8")
        print(f"wrote {args.plan} ({len(pending)} edits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
