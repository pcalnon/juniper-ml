#!/usr/bin/env python3
"""Consolidated development plan v1.15.8 -> v1.15.9: the deploy pin, a filled ``test_accuracy``, the trio stopped.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-30
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-30_plan_v1_7_24_failed_stands_notify_matrix_trio_stopped.py (the recurrence plan's matching revision);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_recurrence-equities-trio-stopped-notify-matrix-deploy-0-13-0-test-accuracy-filled.md
         (the handoff whose item 2 this carries out)

Why
---
Session ``904851c9`` (``ListAgents`` ref ``6f4d37``) put two question sets to the owner. The first was asked 2026-10-29
22:48Z and answered 23:10:11Z the same day: the work to do (the ``test_accuracy`` run, the deploy pin, the notify matrix),
``failed`` for the index row, and the pull ("i don't think the PR was mine. let's stop the :8202 stack"). The second, the
stop's scope, was answered 2026-10-30 08:20:32Z: "Trio via --down". The session acted on every answer on 2026-10-30, and
its handoff (landed by juniper-ml#2390) records the actions. Those times are the transcript's own timestamps. v1.15.8 says
none of it:

- **The deploy pin.** The option the owner chose reads: "Choosing it rules that 0.13.0, which has no F-S10 fix, counts for
  the consolidated plan's R-CASCOR pin route." juniper-deploy#266 (``3070bd7e``, 2026-10-30 08:41:07Z) moves
  ``docker-compose.yml:233`` / ``:427`` and helm ``values.yaml:120`` to 0.13.0. GHCR's index for the tag is
  ``sha256:721417527c4f…`` (re-read here through the registry API), and cascor's ``requirements-cpu.lock`` at ``v0.13.0``
  pins observability 0.4.1, service-core 0.7.1 and data-client 0.6.0.
- **``test_accuracy`` fills.** Run ``20261030T084056Z-0ac7`` (suite ``test-accuracy-731-smoke-20261030T084056Z``, one
  spiral-smoke cell on the cascor primary's ``src/`` at ``e8e8bf4d``) wrote ``eval_metrics.final`` on ``test`` with
  ``accuracy`` 0.575. ``stats.json``'s ``cascor.eval_scalars`` carries it (``held_out`` true; schema
  ``juniper-experiment-stats/2``), and the suite's ``aggregate.csv`` has ``test_accuracy`` 0.575 (all re-read here). So
  APD-ML-002's close condition is met by a run. The close itself is the owner's, and this revision does not make it.
- **The trio is stopped.** ``util/isolated_stack.bash --down`` stopped data ``:8101``, cascor ``:8202`` and canopy ``:8051``
  at 2026-10-30 08:25:52Z. ``ss`` here shows only the four canopy legs of 2026-10-10 among the trio's ports, and none of the
  host's TCP listeners runs from ``JuniperCascor1``. Short-lived processes do: ``python3`` on this host is that environment's
  interpreter, and ``util/experiment_stack.bash:200`` makes it the default cascor environment (the 08:40Z run's cascor ran
  from it). So W0.1's "A live cascor on ``:8202`` imports from that environment" is stale, and "nothing uses it" would be false.
- **The notify matrix.** juniper-data#501 (``95163c47``) adds juniper-canopy; dispatch run 41027844552, canopy's drift run
  41027857909 and recurrence's bench run 41027858881 all succeeded (re-read here).
- **Index line 483** corrects line 482 with outcome ``failed`` (``util/ad-hoc/2026-10-30_index_correction_row_failed.py
  --check`` exits 0). Its text dates the ruling 2026-10-30, the day it was appended; the answer came on 2026-10-29.
- **The cascor primary moved again**: its ``main`` reflog records ``e8e8bf4d`` -> ``d042de23`` at 2026-10-30 18:18:33Z
  (cascor ``main``: cascor#735 and #736, whose ``src/`` changes are all under ``src/tests/``). The actor is unrecorded.
- **P4-39 and P4-40**, which ride R-CASCOR: #672's version fix (``0d2d826b``) is an ancestor of ``v0.12.0``
  (``compare 0d2d826b...v0.12.0``: behind 0), and cascor's CHANGELOG at ``v0.13.0`` repeats ``### Added`` and ``### Fixed`` in
  its ``[0.12.0]`` section but no heading in ``[0.13.0]``.

Not edited: register row APD-ML-002 (``notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md``), whose five-touch close
is the owner's; the parent ``Juniper/AGENTS.md``, whose "juniper-deploy still pins the 0.12.0 image" is stale but needs the
owner's approval; and the non-P12 paths, which keep v1.14.0's state (v1.15.0's status note). Every line stays within 512
characters, and the script refuses if any line is over.

Validation: one independent read-only reviewer checked the first draft. Its BLOCKER was the ruling dates (three of the four
answers came on 2026-10-29, not 2026-10-30); its MAJORs were a ``/proc`` claim that read as "nothing uses the environment"
and the Overview's "it pins ... cascor 0.12.0"; its MINORs and NITs (the stop's order of events, the trio's tense, action 6's
v1.7.23 pointer, the record's source list, a "Filled" pointer, the owner's own words, the session alias, the changed-file
list and the parent ``AGENTS.md`` item) are applied here.

Usage
-----
    python3 util/ad-hoc/2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py [--root DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found zero times or more than once, or a line
over 512 characters after the edits, refuses the whole run before anything is written. ``--check`` writes nothing and
exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
MAX_LINE = 512

# Multi-line texts are bound to names here rather than written inside the REPLACEMENTS display: adjacent literals inside
# a list or tuple trip CodeQL's py/implicit-string-concatenation-in-list, whose unresolved thread blocks a merge.
_DATE_OLD = "ml#2064's close and juniper-cascor 0.13.0's gate probed 2026-10-28, 0.13.0's publish later that day, and the cascor primary 2026-10-29)\n"
_DATE_NEW = "ml#2064's close and juniper-cascor 0.13.0's gate and publish probed 2026-10-28, the cascor primary 2026-10-29, and deploy's pin and the trio 2026-10-30)\n"

_STATUS_ANCHOR = (
    "  - v1.15.8 (2026-10-29) records that the cascor primary carries cascor#731 from 2026-10-29 20:48:58Z (fast-forwarded to `e8e8bf4d`, cascor `main`), "
    "so the experiment stack's default `src/` serves it for the canonical checkout, while juniper-deploy still pins 0.12.0 (XC-P12; §4; §5). Like v1.15.0, no round checks it.\n"
)
_STATUS_ADD = (
    "  - v1.15.9 (2026-10-30) records the owner's answers of 2026-10-29 and 2026-10-30 and what followed: juniper-deploy pins cascor 0.13.0 (deploy#266), "
    "a run on the cascor primary's `src/` filled `test_accuracy`, so APD-ML-002's close condition is met (the close is the owner's), the trio is stopped, "
    "juniper-data#501 adds juniper-canopy to the notify matrix, and index row 483 says `failed` (Overview; §2; XC-P12; §4; §5; §8; Appendix A). Like v1.15.0, no round checks it.\n"
)

_OVERVIEW_PIN_OLD = "Since deploy#258 (2026-10-23) it pins data 0.17.1 and cascor 0.12.0 (re-probed 2026-10-25).\n"
_OVERVIEW_PIN_NEW = (
    "Since deploy#258 (2026-10-23) it pins data 0.17.1 and cascor 0.12.0 (re-probed 2026-10-25). "
    "deploy#266 pins cascor 0.13.0 from 2026-10-30, whose lock pins the same 0.4.1 and 0.7.1 (v1.15.9; §5).\n"
)

_OVERVIEW_TRIO_OLD = "     - The stack trio runs from conda environments.\n"
_OVERVIEW_TRIO_NEW = "     - The stack trio runs from conda environments. It has been stopped since 2026-10-30 (§4 Wave 1's trio route; v1.15.9).\n"

_S2_OLD = "and its `test_*` columns (ml#2381, 10-28); 003..006 wait on one owner menu."
_S2_NEW = "and its `test_*` columns (ml#2381, 10-28); a run filled `test_accuracy` on 10-30, and the register row's close is the owner's (XC-P12); 003..006 wait on one owner menu."

_NOTIFY_ANCHOR = "  The owner ruled on 2026-10-26 that the release-train archive cap is 1,000,000 B (ml#2364), after a GitHub-hosted runner accepted every GraphQL body it tried, up to 16,777,216 B (run 40410086979).\n"
_NOTIFY_ADD = (
    "  On the owner's word of 2026-10-29 (v1.15.9; that plan's v1.7.24), juniper-data#501 (`95163c47`, merged 2026-10-30) adds juniper-canopy to `notify-consumers.yml`'s matrix, so a data release also dispatches canopy's drift check. "
    "The `workflow_dispatch` with version 0.17.1 (run 41027844552) succeeded, and so did canopy's `juniper-data Schema Drift` run 41027857909 and recurrence's bench run 41027858881: `CROSS_REPO_DISPATCH_TOKEN` covers canopy.\n"
)

_PUBLISHED_OLD = "**Published 2026-10-28** (v1.15.7): PyPI serves 0.13.0 from 11:43:24Z.\n"
_PUBLISHED_NEW = "**Published 2026-10-28** (v1.15.7): PyPI serves 0.13.0 from 11:43:24Z. **Filled 2026-10-30** (v1.15.9): below.\n"

_GATE_OLD = (
    "juniper-deploy pins 0.12.0, but the experiment stack's default (the cascor primary's `src/`, for the canonical checkout) carries cascor#731 from 2026-10-29 20:48:58Z (v1.15.8). "
    "ml#2381 left the register row's close to the owner.\n"
)
_GATE_NEW = (
    "juniper-deploy pins 0.13.0 from 2026-10-30 (deploy#266; v1.15.9), and the experiment stack's default (the cascor primary's `src/`, for the canonical checkout) carries cascor#731 from 2026-10-29 20:48:58Z (v1.15.8). "
    "ml#2381 left the register row's close to the owner.\n"
    "   - **Filled 2026-10-30** (v1.15.9): `util/ad-hoc/2026-10-30_test_accuracy_731_smoke_suite.yaml`, one spiral-smoke cell on the cascor primary's `src/` at `e8e8bf4d`, ran as `20261030T084056Z-0ac7` (index row 484). "
    "Its final evaluation is on `test` with `accuracy` 0.575, and the suite's `aggregate.csv` carries it as `test_accuracy`. "
    'So the register row\'s close condition, "until that column exists", is met by a run. The five-touch close is the owner\'s.\n'
)

_W0_1_OLD = "A live cascor on `:8202` imports from that environment (§8)."
_W0_1_NEW = (
    "The `:8202` cascor that imported from it stopped with the trio on 2026-10-30, and no listening service runs from it, "
    "though short-lived processes do: it is this host's `python3` and the experiment stack's default cascor env (§4 Wave 1; §8; v1.15.9)."
)

_SENTRY_OLD = (
    "   - The trio keeps serving from the environment being changed, so stop it before the upgrade, "
    "or run the session's tests in a clone of each environment and upgrade the live one at the restart (`EX/round12-laneB2-schedule.md` R12B2-06).\n"
)
_SENTRY_NEW = (
    "   - The trio keeps serving from the environment being changed, so stop it before the upgrade, "
    "or run the session's tests in a clone of each environment and upgrade the live one at the restart (`EX/round12-laneB2-schedule.md` R12B2-06). "
    "The trio has been stopped since 2026-10-30 (the trio route below; v1.15.9), so this applies again only if it restarts before the upgrade.\n"
)

_ACTION6_OLD = "Further P12 work follows the **Next** bullet of `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.23)"
_ACTION6_NEW = "Further P12 work follows the **Next** bullet of `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.24)"

_TRIO_ANCHOR = "  - verifies the code, not the version: pip reports 0.5.0 for an editable checkout whatever it holds.\n"
_TRIO_ADD = (
    "  - **Stopped 2026-10-30** (v1.15.9), on the owner's word: `util/isolated_stack.bash --down`, run from the juniper-ml primary with the trio's guard dir as `JUNIPER_E2E_RUN_DIR`, "
    "stopped data `:8101`, cascor `:8202` and canopy `:8051` at 08:25:52Z. The canopy E2E session was told first; its no-hold reply had arrived, and was read only after the stop.\n"
    "    - The logs are kept in `juniper-ml/tmp/2026-10-30-trio-stop/`. Who pulls the primaries stays open under O13.\n"
    "    - The cascor primary is cascor `main` whole (§5), which this route pulls only after P3-05, with #683's deployment note applied, and a later `--up` runs it as it stands.\n"
    "    - The four canopy legs of 2026-10-10 (`:8052`, `:8053`, `:8058`, `:8059`) stay up; `:8052` and `:8053` have no cascor or data behind them now.\n"
)

_P6_OLD = (
    "and fills once a cascor carrying cascor#731 serves a run with a test split: 0.13.0's image is on GHCR, and its wheel on PyPI from 2026-10-28; "
    "juniper-deploy still pins 0.12.0, while the experiment stack's default `src/` carries cascor#731 from 2026-10-29 (§5; XC-P12 action 4).\n"
)
_P6_NEW = (
    "and filled on 2026-10-30, in a run on the experiment stack's default `src/`, which carries cascor#731 from 2026-10-29; "
    "juniper-deploy pins 0.13.0 from 2026-10-30, and the register row's close is the owner's (§5; XC-P12 action 4).\n"
)

_P12ROW_OLD = "is annotated: `index.jsonl` line 482 (owner, 10-26) |"
_P12ROW_NEW = "is annotated: `index.jsonl` lines 482-483 (owner, 10-26 and 10-29) |"

_CASCOR_ANCHOR = "    - The pull landed while a stack on `:8202` runs from that `src/`, and its actor is unrecorded. O13 governs a pull of the trio's primaries (§4 Wave 1), so whether it was intended is the owner's to say.\n"
_CASCOR_ADD = (
    '    - **2026-10-30** (v1.15.9): the owner had answered "i don\'t think the PR was mine" (2026-10-29), so the pull\'s actor is still unknown, and had the trio stopped (2026-10-30 08:25:52Z; §4 Wave 1). '
    "The primary moved again at 18:18:33Z, `e8e8bf4d` → `d042de23` (cascor `main`: cascor#735 and #736, whose changes under `src/` are all in `src/tests/`); that pull's actor is unrecorded too.\n"
    "  - **2026-10-30** (v1.15.9): juniper-deploy pins 0.13.0 (deploy#266, `3070bd7e`, 08:41:07Z; `docker-compose.yml:233` and `:427`, helm `values.yaml:120`), "
    "on the owner's ruling of 2026-10-29 that 0.13.0 counts for R-CASCOR's pin route though it carries no cascor F-S10 fix. The fix-forward question stands.\n"
    "    - GHCR's index for `0.13.0` is `sha256:721417527c4f…`, both architectures labelled revision `61a67c53`; `scripts/verify_published_images.py --fail-on-stale` passes, and its control on the old pins fails. "
    "A run filled `test_accuracy` (0.575, run `20261030T084056Z-0ac7`; XC-P12 action 4).\n"
    "    - The unversioned parent `Juniper/AGENTS.md` still says juniper-deploy pins the 0.12.0 image; its edit needs the owner's approval.\n"
)

_DEPLOY_OLD = "and deploy#258 pins data 0.17.1 and cascor 0.12.0 |"
_DEPLOY_NEW = "and deploy#258 pins data 0.17.1 and cascor 0.12.0; deploy#266 pins cascor 0.13.0 (2026-10-30; §5) |"

_T6_OLD = "P4-39 and P4-40 (ride R-CASCOR)"
_T6_NEW = (
    "P4-39 and P4-40 (ride R-CASCOR: #672's version fix is in 0.12.0, and 0.13.0's CHANGELOG section repeats no category heading, "
    "where 0.12.0's repeats `### Added` and `### Fixed`; deploy#266 pins 0.13.0, v1.15.9)"
)

_T5_OLD = "it fills once a cascor carrying cascor#731 serves a run with a test split, and the register row's close is the owner's"
_T5_NEW = "it filled on 2026-10-30 in run `20261030T084056Z-0ac7` (v1.15.9), and the register row's close is the owner's"

_T2_OLD = "Done 2026-10-26 by the owner's ruling: a correction row (line 482).\n"
_T2_NEW = "Done 2026-10-26 by the owner's ruling: a correction row (line 482). It records `degraded`; the owner ruled `failed` on 2026-10-29, and line 483, appended 2026-10-30, corrects line 482 (v1.15.9).\n"

_VALIDATION_ANCHOR = (
    "  - v1.15.8 is a record of the cascor primary's move onto cascor#731 (2026-10-29). No round checks it (owner ruling 2026-10-24); its facts cite the primary's `main` reflog, the `752a797f...e8e8bf4d` compare, "
    "the primary's `classification_metrics.py` and `manager.py`, juniper-deploy's compose file and helm values, PyPI's juniper-ml 0.11.3 and juniper-cascor 0.12.0 / 0.13.0 metadata, and a `[servers]` pip dry-run.\n"
)
_VALIDATION_ADD = (
    "  - v1.15.9 is a record of P12's state on 2026-10-30. No round checks it (owner ruling 2026-10-24); its facts cite deploy#266 with deploy's compose file and helm values, juniper-data#501, runs 41027844552, 41027857909 and 41027858881, "
    "GHCR's `juniper-cascor:0.13.0` index, cascor's `requirements-cpu.lock` and CHANGELOG at `v0.13.0`, and `index.jsonl` lines 482-484.\n"
    "    - Also run `20261030T084056Z-0ac7`'s results and its suite's `aggregate.csv`, `ss` and `/proc`, `util/experiment_stack.bash`, the trio's stop record, "
    "the cascor primary's reflog with the `e8e8bf4d...d042de23` and `0d2d826b...v0.12.0` compares, and the owner's answers with their timestamps in session `904851c9`'s transcript.\n"
    "    - One independent read-only reviewer checked the first draft: its BLOCKER was the ruling dates (three answers came on 2026-10-29), its MAJORs a `/proc` claim and the Overview's cascor 0.12.0 pin; all are applied.\n"
)

_SCRIPTS_OLD = "    - and with v1.15.8's, `2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py`;\n"
_SCRIPTS_NEW = (
    "    - with v1.15.8's, `2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py`;\n"
    "    - and with v1.15.9's, `2026-10-30_consolidated_plan_v1_15_9_deploy_pin_test_accuracy_trio_stopped.py`, which cites `2026-10-30_index_correction_row_failed.py` and `2026-10-30_test_accuracy_731_smoke_suite.yaml` (both landed by ml#2390);\n"
)

_MEMORY_ANCHOR = (
    "  - by session `3ca2d3e4` (2026-10-29), with v1.15.8: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-cascor 0.13.0), "
    "and `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)
_MEMORY_ADD = (
    "  - by session `904851c9` (`ListAgents` ref `6f4d37`; 2026-10-30), recorded with v1.15.9: `~/.local/state/juniper-experiments/index.jsonl` (lines 483 and 484 appended), the trio guard's three pid files (removed by `--down`), "
    "`juniper-ml/tmp/2026-10-30-trio-stop/` and `juniper-ml/tmp/2026-10-30-recurrence-equities-y2/` (new), and `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block); `MEMORY.md` is unchanged.\n"
    "  - by session `856140dc` (2026-10-30), with v1.15.9: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.8\n", "- **Version**: 1.15.9\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_OVERVIEW_PIN_OLD, _OVERVIEW_PIN_NEW),
    (_OVERVIEW_TRIO_OLD, _OVERVIEW_TRIO_NEW),
    (_S2_OLD, _S2_NEW),
    (_NOTIFY_ANCHOR, _NOTIFY_ANCHOR + _NOTIFY_ADD),
    (_PUBLISHED_OLD, _PUBLISHED_NEW),
    (_GATE_OLD, _GATE_NEW),
    (_W0_1_OLD, _W0_1_NEW),
    (_ACTION6_OLD, _ACTION6_NEW),
    (_SENTRY_OLD, _SENTRY_NEW),
    (_TRIO_ANCHOR, _TRIO_ANCHOR + _TRIO_ADD),
    (_P12ROW_OLD, _P12ROW_NEW),
    (_P6_OLD, _P6_NEW),
    (_CASCOR_ANCHOR, _CASCOR_ANCHOR + _CASCOR_ADD),
    (_DEPLOY_OLD, _DEPLOY_NEW),
    (_T6_OLD, _T6_NEW),
    (_T5_OLD, _T5_NEW),
    (_T2_OLD, _T2_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_ANCHOR + _VALIDATION_ADD),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
    (_MEMORY_ANCHOR, _MEMORY_ANCHOR + _MEMORY_ADD),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    pending = refused = 0
    for old, new in REPLACEMENTS:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new, 1)
        pending += 1
        print(f"  ~ {site}... {'pending' if args.check else 'applied now'}")

    long_lines = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]
    for n, width in long_lines:
        print(f"  ! line {n} is {width} characters, over {MAX_LINE}")
    if refused or long_lines:
        print(f"REFUSED: {refused} anchor(s), {len(long_lines)} long line(s); nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
