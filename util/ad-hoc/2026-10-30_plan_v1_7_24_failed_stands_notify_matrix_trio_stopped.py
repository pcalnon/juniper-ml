#!/usr/bin/env python3
"""Plan v1.7.24: the owner's rulings of 2026-10-29/30 -- `failed` stands, juniper-canopy joins the notify matrix, the trio is stopped.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-30
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.23 -> v1.7.24);
         util/ad-hoc/2026-10-27_plan_v1_7_23_client_0_3_1_published_followups_closed.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py (the consolidated plan's matching revision)

Why
---
v1.7.23's **Next** left two questions with the owner: whether juniper-data's notify matrix should take juniper-canopy, and
whether the ``index.jsonl`` correction row should say ``failed`` rather than ``degraded``. The owner answered both in
session ``904851c9`` on 2026-10-29 at 23:10:11Z, with "let's stop the :8202 stack", and on 2026-10-30 at 08:20:32Z chose the
stop's scope: the canopy E2E trio, via ``--down`` (the transcript's own timestamps). That session acted on every answer on
2026-10-30. One independent reviewer of the first draft found that it dated all of it 2026-10-30, as index line 483's own
text does; this revision dates each answer. That session's handoff,
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled.md``
(landed by juniper-ml#2390), left both plans unrevised. Re-probed here: juniper-data#501 and its three runs (``gh pr view``,
``gh run view``), ``index.jsonl`` lines 482-484 (and the correction script's ``--check``), the listening ports, which
processes run from ``JuniperCascor1`` (``/proc``), ``util/recurrence_env_preflight.bash`` (still 2 findings), juniper-canopy#778,
and the ``test_accuracy`` run's ``metrics_final.json``, ``stats.json`` and ``aggregate.csv``, plus the test pin the canopy#777
diff missed, at juniper-data#501's parent and on ``main``. The canopy session's no-hold reply is that session's record, as
marked.

The Status line takes a summary (``STATUS_RECORD``); the Progress bullet and the revision row take the whole record
(``RECORD``). The v1.7.23 Progress bullet and revision row each get a pointer after the ``failed`` sentence, in the style of
v1.7.21's correction of the v1.7.17 row, and W0.1's status row gets its closure appended. Nothing already written is
rewritten except **Next**, as in v1.7.23.

Usage
-----
    python3 util/ad-hoc/2026-10-30_plan_v1_7_24_failed_stands_notify_matrix_trio_stopped.py [--plan PATH] [--check]

``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Every anchor must match exactly as
often as stated (once, or twice for the ``failed`` pointer), or the script refuses and writes nothing. ``--check`` reports
what is applied / pending without writing, and exits 1 while an edit is owed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_HEADLINE = "`failed` stands, juniper-canopy joins the notify matrix, and the trio is stopped"

_RULINGS = (
    "**The owner answered** the questions session `904851c9` (`ListAgents` ref `6f4d37`) put on 2026-10-29: the work to do, "
    "`failed` and the pull at 23:10Z that day, and the stop's scope at 2026-10-30 08:20Z. That session acted on every answer on "
    "2026-10-30 (its handoff landed as juniper-ml#2390). "
)
_INDEX = (
    "**`failed` stands.** Line 483 of `~/.local/state/juniper-experiments/index.jsonl`, appended at 2026-10-30 08:25:05Z by "
    "`util/ad-hoc/2026-10-30_index_correction_row_failed.py`, corrects line 482 with outcome `failed` for run "
    "`20261003T091414Z-4ba6`. Its text dates the ruling 2026-10-30, the day it was appended; the answer came on 2026-10-29. "
    "Lines 1-482 are byte-identical to the copy taken before the append (re-compared here), and the script's `--check` passes. "
)
_NOTIFY = (
    "**juniper-canopy joins the notify matrix.** juniper-data#501 (merged as `95163c47`, 2026-10-30 08:37:14Z) makes "
    "`notify-consumers.yml`'s matrix `[juniper-recurrence, juniper-canopy]`. The diff in juniper-canopy#777's body missed a test "
    "pin: `juniper_data/tests/unit/test_notify_consumers_dispatch.py:438` asserted `[REPO_NAME]`, and the merged test asserts "
    "`CONSUMERS` (`:441`), which is `[REPO_NAME, \"juniper-canopy\"]`. The `workflow_dispatch` with version `0.17.1` (run "
    "41027844552) succeeded, and so did both "
    "`repository_dispatch` runs it fired: canopy's `juniper-data Schema Drift` (run 41027857909) and recurrence's "
    "`CI — bench harness` (run 41027858881). So `CROSS_REPO_DISPATCH_TOKEN` covers canopy, and juniper-data's next release "
    "dispatches canopy's drift job. "
)
_TRIO = (
    "**The trio is stopped.** On the owner's word, `util/isolated_stack.bash --down` stopped the canopy E2E arc's trio (data "
    "`:8101`, cascor `:8202`, canopy `:8051`) at 2026-10-30 08:25:52Z. The canopy session was told first; its no-hold reply had "
    "arrived, and was read only after the stop (that session's record). The logs are kept in "
    "`juniper-ml/tmp/2026-10-30-trio-stop/`. The `:8202` cascor ran from `JuniperCascor1`, and no listening service runs from "
    "that environment now, though short-lived processes do: it is this host's `python3` and the experiment stack's default "
    "cascor environment. `util/recurrence_env_preflight.bash` still "
    "refuses it with 2 findings, both `juniper-service-core` 0.5.0 against juniper-recurrence 0.5.0's `>=0.6.0,<0.8.0` "
    "(re-run 2026-10-30). "
)
_OUTSIDE = (
    "**Also landed, outside this arc**: APD-ML-002's `test_accuracy` fills. "
    "`util/ad-hoc/2026-10-30_test_accuracy_731_smoke_suite.yaml`, one spiral-smoke cell on the cascor primary's `src/` (which "
    "carries juniper-cascor#731), ran as `20261030T084056Z-0ac7`: its final evaluation is on `test` with `accuracy` 0.575, which "
    "the suite's `aggregate.csv` carries as `test_accuracy`. The register row's close condition is met by a run, and the close "
    "is the owner's. juniper-deploy#266 (merged as `3070bd7e`) pins cascor 0.13.0, which carries #731. "
)
_CONSOLIDATED = (
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` records the rulings and what followed (v1.15.9)"
)

RECORD = _RULINGS + _INDEX + _NOTIFY + _TRIO + _OUTSIDE + _CONSOLIDATED

STATUS_RECORD = (
    "the owner answered on 2026-10-29 and 2026-10-30: `index.jsonl` line 483 records `failed` for run `20261003T091414Z-4ba6`, correcting line "
    "482; juniper-data#501 adds juniper-canopy to the notify matrix, and the 0.17.1 dispatch shows `CROSS_REPO_DISPATCH_TOKEN` "
    "covers canopy; the canopy E2E trio, whose cascor ran from `JuniperCascor1`, is stopped, and the preflight still refuses "
    "that environment (2 findings); outside this arc, a run fills APD-ML-002's `test_accuracy`, and juniper-deploy pins cascor "
    "0.13.0. `JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` records them (v1.15.9)"
)

_STATUS_ANCHOR = "records the publish, the follow-ups, the rulings and the erratum (v1.15.5)). The v1.4.0 plan edits follow that record"

NEXT_OLD = (
    "  - **Next**: juniper-data's next release carries W5.7 (the owner's cut; R-DATA-2 in "
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` §5, which names 0.17.2); W5.7 changes a default, so "
    "whether a patch release may carry it is the owner's call too. That release turns juniper-canopy#777's drift job red, "
    "because juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`: re-capture both "
    "snapshots then (the job prints the commands). Adding juniper-canopy to juniper-data's `notify-consumers.yml` matrix is the "
    "owner's (the diff is in juniper-canopy#777's body; only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers "
    "canopy), and once that change merges, a `workflow_dispatch` with version `0.17.1` settles it. Whether the `index.jsonl` "
    "correction row should say `failed` rather than `degraded` is the owner's to say. A juniper-config-tools 0.2.0 cut (the "
    "owner's call) needs its `[Unreleased]` backfilled first. The W0.1 service-core half stays open, and the next real "
    "recurrence run with `save_model` enabled is the snapshot path's first live exercise; it waits on W0.1, since "
    "`util/recurrence_env_preflight.bash` still refuses `JuniperCascor1` (2 findings, re-run 2026-10-27). Left out of "
    "juniper-canopy#776: the restart modal still shows Noise for `mnist`, which does not declare it, and its training fields "
    "are still cascor-only and shown under recurrence."
)
NEXT_NEW = (
    "  - **Next**: juniper-data's next release carries W5.7 (the owner's cut; R-DATA-2 in "
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` §5, which names 0.17.2); W5.7 changes a default, so "
    "whether a patch release may carry it is the owner's call too. That release turns juniper-canopy#777's drift job red, "
    "because juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`: re-capture both "
    "snapshots then (the job prints the commands). Since juniper-data#501 the release's own dispatch runs that job. A "
    "juniper-config-tools 0.2.0 cut (the owner's call) needs its `[Unreleased]` backfilled first. The W0.1 service-core half "
    "stays open, and the next real recurrence run with `save_model` enabled is the snapshot path's first live exercise; it "
    "waits on W0.1, since `util/recurrence_env_preflight.bash` still refuses `JuniperCascor1` (2 findings, re-run 2026-10-30). "
    "The `:8202` cascor that ran from that environment stopped with the trio on 2026-10-30, though the experiment stack still "
    "launches its cascor from it by default, and W0.1's half was ruled for the next cascor restart (2026-10-18). Left out of "
    "juniper-canopy#776: the restart modal still shows Noise for `mnist`, which does not declare it (juniper-canopy#778, opened "
    "2026-10-29, proposes the change for a canopy session), and its training "
    "fields are still cascor-only and shown under recurrence (out of #778's scope too)."
)

FAILED_OLD = "where the owner's option, as that session records, named `failed`."
FAILED_NEW = (
    "where the owner's option, as that session records, named `failed`. "
    "*(Answered in v1.7.24: the owner ruled `failed` on 2026-10-29, and line 483, appended 2026-10-30, corrects line 482.)*"
)
#: The sentence stands in the v1.7.23 Progress bullet and in its revision row, which repeats the bullet's record.
FAILED_COUNT = 2

W01_OLD = "service-core half deferred (live cascor on `:8202` imports from the env)"
W01_NEW = "service-core half deferred (live cascor on `:8202` imports from the env; that cascor stopped with the canopy E2E trio on 2026-10-30, v1.7.24)"

_ROW_ANCHOR_START = "| 2026-10-27 | 1.7.23 | **juniper-recurrence-client 0.3.1 published; the arc's follow-ups closed**:"
_ROW_START = "| 2026-10-30 | 1.7.24 | "
_ROW_UPDATED = (
    "Updated: Status line (a summary of this record), the Progress block (a session bullet before **Next**, and **Next** "
    "rewritten), W0.1's status row (its closure appended), and the v1.7.23 Progress bullet and revision row (a pointer after "
    "the `failed` sentence in each). | Paul Calnon |"
)


def edits() -> list[tuple[str, str, int]]:
    bullet = f"  - **{_HEADLINE} (Linux host, 2026-10-30)**: {RECORD}.\n"
    status_new = _STATUS_ANCHOR.replace("(v1.15.5)). The v1.4.0", f"(v1.15.5)); **{_HEADLINE}** (v1.7.24: {STATUS_RECORD}). The v1.4.0")
    return [
        ("- **Version**: 1.7.23", "- **Version**: 1.7.24", 1),
        (_STATUS_ANCHOR, status_new, 1),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (NEXT_OLD, bullet + NEXT_NEW, 1),
        (FAILED_OLD, FAILED_NEW, FAILED_COUNT),
        (W01_OLD, W01_NEW, 1),
    ]


def row() -> str:
    return f"{_ROW_START}**{_HEADLINE}**: {RECORD}. {_ROW_UPDATED}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's own copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()

    for text_piece in (RECORD, STATUS_RECORD, NEXT_NEW, FAILED_NEW, W01_NEW):
        if "|" in text_piece or "\n" in text_piece:
            raise SystemExit(f"ERROR: a record text carries a table pipe or a newline: {text_piece[:90]!r}")

    text = args.plan.read_text(encoding="utf-8")
    original = text
    owed = 0
    for old, new, count in edits():
        # ``new`` contains ``old`` for the appended edits, so applied means every ``old`` sits inside a ``new``.
        if text.count(new) == count and text.count(old) <= text.count(new):
            print(f"  = already applied: {new[:80]!r}")
            continue
        if text.count(old) != count:
            raise SystemExit(f"ERROR: expected {count} occurrence(s) of {old[:90]!r}, found {text.count(old)}")
        owed += 1
        print(f"  {'~ WOULD apply' if args.check else '+ applied'} (x{count}): {old[:80]!r}")
        text = text.replace(old, new, count)

    if _ROW_START in text:
        print("  = revision row already present")
    else:
        starts = [m.start() for m in re.finditer(re.escape(_ROW_ANCHOR_START), text)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.23 revision row, found {len(starts)}")
        end = text.find("\n", starts[0])
        end = len(text) if end < 0 else end
        owed += 1
        text = text[:end] + "\n" + row() + text[end:]
        print(f"  {'~ WOULD add' if args.check else '+ added'} the revision row after v1.7.23")

    if args.check:
        print(f"--check: {owed} edit(s) owed; nothing written")
        return 1 if owed else 0
    if text != original:
        args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
