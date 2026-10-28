#!/usr/bin/env python3
"""Consolidated development plan v1.15.6 -> v1.15.7: juniper-cascor 0.13.0 published.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-28
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor Release v0.13.0 and publish run 40608671287 (the publish this records);
         util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py (the wheel probe, with its 0.12.0 control);
         util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py (the revision this follows, and the pattern)

Why
---
v1.15.6 (2026-10-28, juniper-ml#2383, merged 10:49:20Z) recorded juniper-cascor 0.13.0 at the owner's ``pypi`` gate. The
owner approved it later that day: the run's ``pypi`` deployment left ``waiting`` at 11:39:02Z, ``Publish to PyPI`` ran
11:42:56Z-11:43:30Z, and PyPI serves the wheel from 11:43:24Z. This revision flips the four places v1.15.6 left waiting (the
Date line, XC-P12 action 4, §4's P6 line, §5's R-CASCOR note) and adds the record lines (Version, status, validation,
changed-by).

What the publish does not change, and the revision says so where it names the column: ``test_accuracy`` fills only once a
cascor carrying juniper-cascor#731 serves a run with a test split (juniper-ml#2381's own condition), and neither default does
yet. juniper-deploy's ``docker-compose.yml`` pins ``ghcr.io/pcalnon/juniper-cascor:0.12.0``, and ``util/experiment_stack.bash``
launches ``${PROJECT_DIR}/juniper-cascor/src`` (the cascor primary, for the canonical checkout) unless
``JUNIPER_EXP_CASCOR_SRC_DIR`` or ``JUNIPER_EXP_PROJECT_DIR`` points elsewhere, and the primary's ``classification_metrics.py``
has no ``compute_classification_accuracy``. Register row ``APD-ML-002``
(``notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md``) is not edited: juniper-ml#2381 left its close to the owner,
and that row's "in no juniper-cascor release yet" (stale since Release v0.13.0, 00:25:28Z) is the owner's to correct with it.

§2's P4 row still has no room under 512 characters, and §5 carries the publish, as v1.15.6 decided for the cut.

Each fact was re-probed here: run 40608671287's jobs (both success), its approvals (``pcalnon`` for ``pypi``, then the
wait timer) and its ``pypi`` deployment's statuses, PyPI's and TestPyPI's ``/juniper-cascor/0.13.0/json`` (the same
``requires_dist``, 33 entries; different sha256 for both files), juniper-cascor's ``publish.yml`` (``python -m build`` in the
``testpypi`` job and again in the ``pypi`` job, as for 0.12.0, whose files also differ), juniper-deploy's
``docker-compose.yml`` on ``main`` (two ``image:`` lines at 0.12.0; no deploy PR open), and the wheel probe (0.13.0 passes all
four checks, the 0.12.0 control fails all four). Every line stays within 512 characters, and the script refuses if any line
is over.

Validation: two independent read-only reviewers checked the first draft. A fact-checker found 0 BLOCKER, 0 MAJOR, 6 MINOR
and 8 NIT; a residue / consistency / executability reviewer found 0 BLOCKER, 0 MAJOR, 6 MINOR and 13 NIT, and no predecessor
item dropped. They converged on five: the wheel probe was credited with a check it did not make (it now parses the call's
enclosing function), this docstring kept a "none does yet" the plan had dropped, a wrong archive path and a wrong "stale
since" time in the handoff, and a stale saved diff. The plan-side fixes are the default ``src/`` named with both variables
(for the canonical checkout; a launcher run from elsewhere derives another ``PROJECT_DIR``), §4's line naming both defaults,
the approval time (the deployment's ``queued`` status, not the upload) and a fuller source list in the validation record. A
round-2 reviewer of the fix pass found 0 BLOCKER, 0 MAJOR, 5 MINOR and 9 NIT, none in the plan, which it replayed
byte-for-byte from this script on a pristine copy.

Usage
-----
    python3 util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py [--root DIR] [--check]

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
_DATE_OLD = "juniper-recurrence-client 0.3.1's publish probed 2026-10-27, and ml#2064's close and juniper-cascor 0.13.0's gate probed 2026-10-28)\n"
_DATE_NEW = "juniper-recurrence-client 0.3.1's publish probed 2026-10-27, ml#2064's close and juniper-cascor 0.13.0's gate probed 2026-10-28, and 0.13.0's publish probed later that day)\n"

_STATUS_ANCHOR = (
    "  - v1.15.6 (2026-10-28) records P5-11's close (ml#2381 closed ml#2064) and juniper-cascor 0.13.0, which carries cascor#731, at the owner's `pypi` gate, so APD-ML-002's `test_accuracy` has its producer and its column on `main` "
    "(§2; XC-P12; §4; §5; §6; §8; §9; Appendices A and B). Like v1.15.0, no round checks it.\n"
)
_STATUS_ADD = (
    "  - v1.15.7 (2026-10-28) records juniper-cascor 0.13.0's publish: the owner approved its `pypi` gate, and PyPI serves the wheel, which carries cascor#731's `compute_classification_accuracy`. "
    "juniper-deploy and the experiment stack's default `src/` do not carry cascor#731 yet, so `test_accuracy` is not filled by default (XC-P12; §4; §5). Like v1.15.0, no round checks it.\n"
)

_MOVED_OLD = "**Moved 2026-10-28** (v1.15.6): ml#2064 is closed, and Release v0.13.0 carries cascor#731, its PyPI leg at the owner's gate.\n"
_MOVED_NEW = "**Moved 2026-10-28** (v1.15.6): ml#2064 is closed, and Release v0.13.0 carries cascor#731, its PyPI leg at the owner's gate. **Published 2026-10-28** (v1.15.7): PyPI serves 0.13.0 from 11:43:24Z.\n"

_GATE_OLD = (
    "   - juniper-cascor 0.13.0 carries cascor#731: its image is on GHCR, and its wheel waits at the owner's `pypi` gate (run 40608671287; §5). `test_accuracy` fills once a cascor carrying cascor#731 serves a run with a test split. "
    "ml#2381 left the register row's close to the owner.\n"
)
_GATE_NEW = (
    "   - juniper-cascor 0.13.0 carries cascor#731: its image is on GHCR, and PyPI serves its wheel from 2026-10-28 11:43:24Z (run 40608671287; §5). `test_accuracy` fills once a cascor carrying cascor#731 serves a run with a test split, "
    "and neither default does yet: juniper-deploy pins 0.12.0, and the experiment stack runs the cascor primary's `src/`, which lacks cascor#731, unless `JUNIPER_EXP_CASCOR_SRC_DIR` or `JUNIPER_EXP_PROJECT_DIR` points elsewhere. "
    "ml#2381 left the register row's close to the owner.\n"
)

_W4_OLD = "0.13.0's image is on GHCR, and its wheel waits at the owner's `pypi` gate (§5).\n"
_W4_NEW = "0.13.0's image is on GHCR, and its wheel on PyPI from 2026-10-28; juniper-deploy still pins 0.12.0, and the experiment stack's default `src/` lacks cascor#731 (§5; XC-P12 action 4).\n"

_CASCOR_ANCHOR = (
    "  - It carries cascor#731, the final evaluation's `accuracy` (XC-P12 action 4). Like 0.12.0, it names no cascor F-S10 fix: its notes list none, and `src/api/secrets.py` is unchanged from `v0.12.0`. "
    "Its locks pin data-client 0.6.0, which carries F-S10 too. The fix-forward question stands.\n"
)
_CASCOR_ADD = (
    "  - **Published 2026-10-28** (v1.15.7): the owner approved the gate (its `pypi` deployment left `waiting` at 11:39:02Z), and `Publish to PyPI` ran 11:42:56Z–11:43:30Z (run 40608671287 green). "
    "PyPI serves the wheel from 11:43:24Z, with TestPyPI's `requires_dist`. juniper-deploy still pins cascor 0.12.0 (`docker-compose.yml`; no deploy PR open).\n"
    "  - `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` parses the PyPI wheel without installing it: the wheel defines `compute_classification_accuracy`, `_compute_final_eval_metrics` (the final evaluation) calls it, and the 0.12.0 control fails. "
    "PyPI's files are a second `python -m build` (`publish.yml` builds in both jobs), so their sha256 differ from TestPyPI's, as 0.12.0's do.\n"
)

_VALIDATION_ANCHOR = (
    "  - v1.15.6 is a record of P5-11's close (2026-10-28) and of juniper-cascor 0.13.0 at its `pypi` gate. No round checks it (owner ruling 2026-10-24); its facts cite ml#2381 and #2379, cascor#731 and #733, "
    "Release v0.13.0, runs 40608671287 and 40608671351, PyPI's, TestPyPI's and GHCR's answers for 0.13.0, the `v0.12.0...v0.13.0` compare, and `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py`.\n"
)
_VALIDATION_ADD = (
    "  - v1.15.7 is a record of juniper-cascor 0.13.0's publish (2026-10-28). No round checks it (owner ruling 2026-10-24); its facts cite run 40608671287's jobs, approvals and `pypi` deployment, PyPI's and TestPyPI's 0.12.0 and 0.13.0 metadata, "
    "juniper-cascor's `publish.yml`, juniper-deploy's `docker-compose.yml` and PR list, and `util/experiment_stack.bash`.\n"
    "    - Also the cascor primary's `classification_metrics.py`, `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` and `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py`.\n"
)

_SCRIPTS_OLD = "    - and with v1.15.6's, `2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py`;\n"
_SCRIPTS_NEW = (
    "    - with v1.15.6's, `2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py`;\n"
    "    - and with v1.15.7's, `2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py` and `2026-10-28_verify_cascor_0_13_0_published_wheel.py`;\n"
)

_MEMORY_ANCHOR = (
    "  - by session `1fc78df5` (2026-10-28), with v1.15.6: `project_recurrence_equities_p0_arc_2026-10-04.md`, `project_pypi_publish_workflow_dual_gate.md` "
    "(a waiting gate's working deadline is day 30) and their lines in `MEMORY.md`.\n"
)
_MEMORY_ADD = (
    "  - by session `22169b88` (2026-10-28), with v1.15.7: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description) "
    "and `project_pypi_publish_workflow_dual_gate.md` (cascor's PyPI files are a second build, not TestPyPI's); `MEMORY.md` is unchanged.\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.6\n", "- **Version**: 1.15.7\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_MOVED_OLD, _MOVED_NEW),
    (_GATE_OLD, _GATE_NEW),
    (_W4_OLD, _W4_NEW),
    (_CASCOR_ANCHOR, _CASCOR_ANCHOR + _CASCOR_ADD),
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
