#!/usr/bin/env python3
"""Consolidated development plan v1.15.7 -> v1.15.8: the cascor primary carries juniper-cascor#731.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py (the revision this follows, and the pattern);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md
         (the handoff that lands with it)

Why
---
v1.15.7 (2026-10-28, juniper-ml#2384, merged 22:19:26Z) recorded juniper-cascor 0.13.0's publish and said neither default
runs cascor#731 yet: juniper-deploy pins ``ghcr.io/pcalnon/juniper-cascor:0.12.0``, and ``util/experiment_stack.bash:171``
launches ``${PROJECT_DIR}/juniper-cascor/src`` (the cascor primary, for the canonical checkout), whose
``classification_metrics.py`` had no ``compute_classification_accuracy``. The second half stopped being true on 2026-10-29 at
20:48:58Z: the primary's ``main`` reflog records ``pull origin: Fast-forward`` from ``5b7d10dc`` to ``e8e8bf4d``, which is
cascor ``main`` and 8 commits past cascor#731's ``752a797f`` (``compare 752a797f...e8e8bf4d``: ahead 8, behind 0). The primary
now defines ``compute_classification_accuracy`` and ``manager.py:2292`` calls it, so a run the experiment stack launches with
its default ``src/`` serves cascor#731. Who pulled is not recorded (the reflog shows only the git identity), and this session
ran no git in juniper-cascor.

This revision flips the two places v1.15.7 says the default ``src/`` lacks cascor#731 (XC-P12 action 4 and §4's P6 line),
extends the Date line's probe list, adds a §5 R-CASCOR sub-bullet (with a note that the pull landed under the live ``:8202``
stack, and that O13 governs a pull of the trio's primaries), and adds the record lines (Version, status, validation, the
scripts list, changed-by). v1.15.7's own status line, the third place, stays as the record of what v1.15.7 said. juniper-deploy still pins 0.12.0
(``docker-compose.yml:233`` and ``:427``; helm ``values.yaml:120``), and §5's sub-bullet also records that a fresh
``juniper-ml[servers]==0.11.3`` install resolves juniper-cascor 0.13.0 (its floor is ``>=0.12.0`` with no cap; a pip dry-run,
``--no-cache-dir --ignore-installed``, on 2026-10-29).

Register row ``APD-ML-002`` (``notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md``) is not edited: juniper-ml#2381
left its close to the owner, and its close condition, "until that column exists", is met by a run, not by a checkout.

Every line stays within 512 characters, and the script refuses if any line is over.

Validation: three independent read-only reviewers checked the first draft of this revision's handoff, and the fact-checker
and the residue auditor each found the primary's move (it happened after the draft) as their BLOCKER; this revision exists
because of it. A round-2 reviewer replayed this script on a pristine copy of ``origin/main``'s plan, and the result was
byte-identical to the worktree's. Its findings here were the "three places" wording (the Date line is extended, not flipped),
the missing ``:8202`` note, and the changed-by line, which omitted this session's parent ``Juniper/AGENTS.md`` edit.

Usage
-----
    python3 util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py [--root DIR] [--check]

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
_DATE_OLD = "ml#2064's close and juniper-cascor 0.13.0's gate probed 2026-10-28, and 0.13.0's publish probed later that day)\n"
_DATE_NEW = "ml#2064's close and juniper-cascor 0.13.0's gate probed 2026-10-28, 0.13.0's publish later that day, and the cascor primary 2026-10-29)\n"

_STATUS_ANCHOR = (
    "  - v1.15.7 (2026-10-28) records juniper-cascor 0.13.0's publish: the owner approved its `pypi` gate, and PyPI serves the wheel, which carries cascor#731's `compute_classification_accuracy`. "
    "juniper-deploy and the experiment stack's default `src/` do not carry cascor#731 yet, so `test_accuracy` is not filled by default (XC-P12; §4; §5). Like v1.15.0, no round checks it.\n"
)
_STATUS_ADD = (
    "  - v1.15.8 (2026-10-29) records that the cascor primary carries cascor#731 from 2026-10-29 20:48:58Z (fast-forwarded to `e8e8bf4d`, cascor `main`), "
    "so the experiment stack's default `src/` serves it for the canonical checkout, while juniper-deploy still pins 0.12.0 (XC-P12; §4; §5). Like v1.15.0, no round checks it.\n"
)

_GATE_OLD = (
    "`test_accuracy` fills once a cascor carrying cascor#731 serves a run with a test split, "
    "and neither default does yet: juniper-deploy pins 0.12.0, and the experiment stack runs the cascor primary's `src/`, which lacks cascor#731, unless `JUNIPER_EXP_CASCOR_SRC_DIR` or `JUNIPER_EXP_PROJECT_DIR` points elsewhere. "
    "ml#2381 left the register row's close to the owner.\n"
)
_GATE_NEW = (
    "`test_accuracy` fills once a cascor carrying cascor#731 serves a run with a test split. "
    "juniper-deploy pins 0.12.0, but the experiment stack's default (the cascor primary's `src/`, for the canonical checkout) carries cascor#731 from 2026-10-29 20:48:58Z (v1.15.8). "
    "ml#2381 left the register row's close to the owner.\n"
)

_W4_OLD = "juniper-deploy still pins 0.12.0, and the experiment stack's default `src/` lacks cascor#731 (§5; XC-P12 action 4).\n"
_W4_NEW = "juniper-deploy still pins 0.12.0, while the experiment stack's default `src/` carries cascor#731 from 2026-10-29 (§5; XC-P12 action 4).\n"

_CASCOR_ANCHOR = (
    "  - `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` parses the PyPI wheel without installing it: the wheel defines `compute_classification_accuracy`, `_compute_final_eval_metrics` (the final evaluation) calls it, and the 0.12.0 control fails. "
    "PyPI's files are a second `python -m build` (`publish.yml` builds in both jobs), so their sha256 differ from TestPyPI's, as 0.12.0's do.\n"
)
_CASCOR_ADD = (
    "  - **2026-10-29** (v1.15.8): the cascor primary was fast-forwarded `5b7d10dc` → `e8e8bf4d` (cascor `main`, 8 commits past cascor#731's `752a797f`) at 20:48:58Z, "
    "so `util/experiment_stack.bash`'s default `src/` serves cascor#731 for the canonical checkout. "
    "A fresh `juniper-ml[servers]==0.11.3` install resolves 0.13.0 too (floor `>=0.12.0`, uncapped; a pip dry-run). juniper-deploy still pins 0.12.0.\n"
    "    - The pull landed while a stack on `:8202` runs from that `src/`, and its actor is unrecorded. O13 governs a pull of the trio's primaries (§4 Wave 1), so whether it was intended is the owner's to say.\n"
)

_VALIDATION_ANCHOR = "    - Also the cascor primary's `classification_metrics.py`, `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` and `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py`.\n"
_VALIDATION_ADD = (
    "  - v1.15.8 is a record of the cascor primary's move onto cascor#731 (2026-10-29). No round checks it (owner ruling 2026-10-24); its facts cite the primary's `main` reflog, the `752a797f...e8e8bf4d` compare, "
    "the primary's `classification_metrics.py` and `manager.py`, juniper-deploy's compose file and helm values, PyPI's juniper-ml 0.11.3 and juniper-cascor 0.12.0 / 0.13.0 metadata, and a `[servers]` pip dry-run.\n"
)

_SCRIPTS_OLD = "    - and with v1.15.7's, `2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py` and `2026-10-28_verify_cascor_0_13_0_published_wheel.py`;\n"
_SCRIPTS_NEW = (
    "    - with v1.15.7's, `2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py` and `2026-10-28_verify_cascor_0_13_0_published_wheel.py`;\n"
    "    - and with v1.15.8's, `2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py`;\n"
)

_MEMORY_ANCHOR = (
    "  - by session `22169b88` (2026-10-28), with v1.15.7: `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description) "
    "and `project_pypi_publish_workflow_dual_gate.md` (cascor's PyPI files are a second build, not TestPyPI's); `MEMORY.md` is unchanged.\n"
)
_MEMORY_ADD = (
    "  - by session `3ca2d3e4` (2026-10-29), with v1.15.8: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-cascor 0.13.0), "
    "and `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description); this session did not change `MEMORY.md`.\n"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.7\n", "- **Version**: 1.15.8\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
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
