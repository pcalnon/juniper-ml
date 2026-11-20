#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       The outside-reader corrections to the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 CHANGELOG sections
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-11-15_cascor_canopy_release_notes_corrections.py
# File Path:     juniper-ml/util/ad-hoc/
#
# Date:          2026-11-15
# Last Modified: 2026-11-15
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     A Release body cannot be re-cut, and the ceremony renders it from the CHANGELOG section verbatim. An
#     independent reviewer read both rendered bodies as an outside reader on publication day (2026-11-15) and found
#     statements that were true when each PR merged and false at the release head, because later PRs in the same
#     release changed what they describe (the class juniper-ml 0.11.5's cut recorded). Every finding below was
#     re-checked at the release head (cascor 668f88e9, canopy 1c2dbd01) before it was applied. This tool makes the
#     corrections, inside each release's own section only, as the proposal's fourth commit.
#
#     Two kinds of edit:
#       * text: a span matched whitespace-insensitively (the sections mix wrapped paragraphs and one-line
#         sub-bullets) is replaced by new text; it must match exactly once. Nothing is re-wrapped: markdownlint
#         excludes CHANGELOG.md in both repositories, whose lines already run past 2,000 characters, and a wrap
#         inside a code span would only change how the source reads.
#       * item: a whole bullet, found by the start of its first line, is replaced together with its continuation
#         lines and sub-bullets.
#     Each is "already at target" when its new text is present and its old text is not.
#
# Usage:
#     python3 util/ad-hoc/2026-11-15_cascor_canopy_release_notes_corrections.py --repo juniper-cascor --tree DIR [--check]
#
#     Exit 0: written, or (--check) every edit at target. Exit 1: --check found an edit still to make.
#     Exit 2: an anchor is missing or ambiguous; nothing is written.
#
#####################################################################################################################################################################################################
"""The outside-reader corrections to the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 CHANGELOG sections."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass

VERSIONS = {"juniper-cascor": "0.14.0", "juniper-canopy": "0.10.0"}


@dataclass(frozen=True)
class Fix:
    """One correction. kind is "text" (old is an unwrapped span) or "item" (old is the start of a bullet's first line)."""

    finding: str
    kind: str
    old: str
    new: str


CASCOR = [
    Fix(
        "B1",
        "item",
        "  - **Left alone.** The same census found two other sets that no lane runs:",
        "  - **Left alone here, and given a lane later in this release** (the nightly-lanes entry below). The same census found two other sets that no lane ran:\n"
        "    - the 153 `performance`-marked tests in `src/tests/performance/`, which the new nightly `performance-smoke` job runs;\n"
        "    - five unmarked tests in `src/tests/integration/test_comprehensive_serialization.py`, now marked `integration` and run in the required integration jobs.\n",
    ),
    Fix(
        "B2",
        "text",
        "Five other live documents still name the file (`docs/REFERENCE.md`, `docs/testing/MANUAL.md`, `docs/ci_cd/MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `src/tests/README.md`); they are left for a later pass.",
        "Five other live documents named the file too (`docs/REFERENCE.md`, `docs/testing/MANUAL.md`, `docs/ci_cd/MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `src/tests/README.md`); "
        '"Five documents no longer name the nonexistent `src/tests/pytest.ini`" above corrects them in this release.',
    ),
    Fix(
        "M3",
        "item",
        "  - **Not fixed here: the stop-then-start race.**",
        "  - **Reported here, fixed later in this release: the stop-then-start race.** A start sent after a stop, before the old fit reached its next checkpoint, cleared the shared `_stop_event`, so the old "
        "fit was never interrupted: it trained on to its natural end while the FSM read `STOPPED` and, still owning the lifecycle, wrote `training_state` `Completed` and counted a successful session for a "
        "run the operator had stopped. `swap_dataset_live` cleared the event the same way after its 10 s join timed out. The Overtoadship check above could not help, because cascor's queue keeps the new run "
        "from starting until the old fit returns. This change shipped `util/ad-hoc/2026-11-08_stop_then_start_race_repro.py`, which reproduced it (exit 1). The Overtoad's ruling 17 (2026-11-09), "
        '"cascor: stop-then-start", gave it a fix of its own: see "A start sent after a stop no longer cancels it" below, whose per-run stop signal the Overtoad ruled on 2026-11-12 to keep, and with which '
        "the reproducer exits 0.\n",
    ),
    Fix("M3b", "text", '("Reported, not fixed here: the stop-then-start race")', "(the stop-then-start item of the paused-fit entry above)"),
    Fix(
        "M4",
        "item",
        "  - **The job caps pytest below 9.2 (Overtoad ruling 2026-10-29).**",
        "  - **The job capped pytest below 9.2 (Overtoad ruling 2026-10-29); the cap is gone in this release** (the pytest 9.2 entry above). pytest 9.2.0 (PyPI 2026-10-27) broke pytest-benchmark 5.3.0, "
        "then the latest release, at fixture setup: `AttributeError: 'Function' object has no attribute '_nodeid'` (`pytest_benchmark/fixture.py:88`). Every benchmark test errored, and run 40970853599 "
        "logged `5 errors` and stopped at `--maxfail=5`. The job therefore installed `pytest<9.2` (9.1.1) after the project until pytest-benchmark 5.3.1 supported 9.2. The required lanes kept pytest 9.2. "
        "Locally, on 9.1.1 with pytest-benchmark 5.3.0, all 153 passed.\n",
    ),
    Fix(
        "M5",
        "text",
        "It also catches a failure the exit status hides. `src/tests/conftest.py`'s `pytest_unconfigure` calls `os._exit(0)` whenever a non-daemon thread outlives the session, so a failing lane can exit 0 (measured: `1 failed`, exit status 0).",
        "It also catches a failure the exit status hid: `src/tests/conftest.py`'s `pytest_unconfigure` called `os._exit(0)` whenever a non-daemon thread outlived the session, so a failing lane could exit 0 "
        '(measured: `1 failed`, exit status 0). "A failing test session no longer exits 0 when a thread outlives it" below removes that mask in this release.',
    ),
    Fix(
        "M6",
        "text",
        "165 of 165 uploads had succeeded over 200 runs (`util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`).",
        "The survey (`util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`) counted 165 of 165 upload steps succeeding over 200 runs; a step masked by `continue-on-error` reads `success` there, so the "
        "count does not show that every upload succeeded (the Bandit SARIF comment entry above).",
    ),
    Fix(
        "M6b",
        "text",
        'The 2026-10-29 entry below keeps its "165 of 165" as written.',
        'The nightly-lanes entry below (juniper-cascor#735) qualifies its "165 of 165" accordingly.',
    ),
    Fix(
        "m8",
        "text",
        "**The image picks up R-OBS-SC-2's two security patches.** Both locks move `juniper-observability` 0.4.1 -> 0.4.2 and `juniper-service-core` 0.7.1 -> 0.7.2, and nothing else: `requirements.lock` "
        "holds 73 pins and `requirements-cpu.lock` 54, and each reproduces under its constraint-mode freshness resolution.",
        "**The image picks up juniper-observability 0.4.2, the security patch, and juniper-service-core 0.7.2, a plain patch released with it.** #748 moved both locks from 0.4.1 and 0.7.1 to them, and "
        "nothing else (the release's other lock moves are under Changed): `requirements.lock` holds 73 pins and `requirements-cpu.lock` 54, and each reproduces under its constraint-mode freshness "
        "resolution.",
    ),
    Fix(
        "m9",
        "text",
        "juniper-ml's flood-4 record (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`) adds the ruling to its §8 in its next update.",
        "As of this release, juniper-ml's flood-4 record (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`) lists rulings 1 to 14 in its §8 and not this one.",
    ),
    Fix(
        "m10a",
        "text",
        "The unit lane now selects 5,836 of 5,851 collected tests, up from 5,796 of 5,811.",
        "At this change the unit lane selected 5,836 of 5,851 collected tests, up from 5,796 of 5,811.",
    ),
    Fix("m10b", "text", "The unit lane selects 5,860 of 5,875 tests, up from 5,836 of 5,851.", "At this change the unit lane selected 5,860 of 5,875 tests, up from 5,836 of 5,851."),
]

CANOPY = [
    Fix(
        "B2",
        "text",
        "**The image picks up R-OBS-SC-2's two security patches.** `requirements.lock` moves `juniper-observability` 0.4.1 -> 0.4.2 and `juniper-service-core` 0.7.1 -> 0.7.2, and nothing else: 60 pins, "
        "which CI's constraint-mode freshness resolution reproduces. The image installs that lock (`Dockerfile:40`).",
        "**The image picks up juniper-observability 0.4.2, the security patch, and juniper-service-core 0.7.2, a plain patch released with it.** #806 moved `requirements.lock` from 0.4.1 and 0.7.1 to "
        "them, and nothing else; #810 later added `lazy-importer` (the release's other lock moves are under Changed), so the lock this release installs holds 61 pins, which CI's constraint-mode "
        "freshness resolution reproduces. The image installs that lock (`Dockerfile:40`).",
    ),
    Fix(
        "B3",
        "text",
        "A Dependabot PR reads the Dependabot secret store, which does not hold the token, so its upload stays tokenless.",
        "A Dependabot PR reads the Dependabot secret store, which did not hold the token then, so its upload stayed tokenless until the Overtoad added the token there on 2026-11-04.",
    ),
    Fix(
        "B4",
        "text",
        "(the event juniper-recurrence's bench lane receives; it reaches canopy once juniper-data's notify-consumers matrix lists it)",
        "(the event juniper-recurrence's bench lane receives; juniper-data's notify-consumers matrix has listed canopy since juniper-data#501, 2026-10-30, so juniper-data's next release sends it here)",
    ),
    Fix(
        "B5",
        "text",
        "the conda file was the one environment on 3.x, and it was the one nobody drove.",
        "the two conda files (`conf/conda_environment.yaml` and `conf/conda_environment_cpu.yaml`, both `dash=3.3.0`) were the environments on 3.x, and nobody drove them. This release moves only "
        "`conf/conda_environment.yaml`: `conf/conda_environment_cpu.yaml` still pins `dash=3.3.0`, below the new floor.",
    ),
    Fix(
        "m6",
        "text",
        "**Still open**: the `?api_key=` WebSocket query parameter reaches Sentry under the default `send_pii=False`. Query strings are juniper-observability 0.4.3's follow-up, so this lock does not close that path.",
        "**Still open**: 0.4.2's notes leave query strings, Sentry Logs, request bodies, breadcrumbs and exception values for juniper-observability 0.4.3, so this lock does not close them. The query "
        "strings include canopy's `?api_key=` WebSocket parameter, which reaches Sentry under the default `send_pii=False`.",
    ),
    Fix(
        "m8a",
        "text",
        "no trigger, step, pin or job name changed. Same record, §4.",
        "no trigger, step, pin or job name changed. Found by the Cursor flood-3 evaluation: juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4.",
    ),
    Fix("m8b", "text", "(a row in the same record)", "(a row in that flood-3 record)"),
    Fix(
        "m9",
        "text",
        "(the Overtoad's ruling 17 of 2026-11-09 in juniper-ml's Cursor flood-4 arc, which that record's next update adds to §8 of `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`)",
        "(the Overtoad's ruling 17 of 2026-11-09 in juniper-ml's Cursor flood-4 arc; as of this release its record, `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, lists "
        "rulings 1 to 14 in §8 and not this one)",
    ),
    Fix(
        # Second round: the first wording named the files the old `paths` entry DID cover, so it contradicted the
        # sentence after it; the reviewer's replacement covers the whole "Why" text.
        "m10",
        "text",
        "Every conda-env refresh rewrites the `<package>=<version>=<build>` lines under a new commit. No commit-scoped entry can name that commit in advance, so the next refresh of "
        "`conf/requirements-conda.txt` would have failed the PR scan and then the push scan of `main`. Meanwhile the old global `conf/conda_environment.*\\.ya?ml` path entry skipped EVERY rule in "
        "those files.",
        "Every conda-env refresh rewrites the `<package>=<version>=<build>` lines under a new commit, and no commit-scoped entry can name that commit in advance. The old global "
        "`conf/conda_environment.*\\.ya?ml` path entry kept such a refresh from failing only by skipping EVERY rule in those files; without it, the next refresh of a conda environment file would fail "
        "the PR scan and then the push scan of `main`. (`conf/requirements-conda.txt`, which the new allowlist also names, has not been in the tree since before 0.9.0; its four findings are in history "
        "only.)",
    ),
    Fix(
        "m11",
        "text",
        "The unit lane now selects 8,224 of 8,228 collected tests, up from 8,182 of 8,186",
        "At this change the unit lane selected 8,224 of 8,228 collected tests, up from 8,182 of 8,186",
    ),
    Fix("n12", "text", "`.github/workflows/lockfile-update.yml` banner 0.1.2.", "`.github/workflows/lockfile-update.yml` banner 0.1.2 (0.1.3 after the next entry's change)."),
    Fix(
        "n13",
        "text",
        "so a sibling capture such as flat `equities` is covered from the commit that adds it",
        "so a sibling capture is covered from the commit that adds it, as flat `equities` and `mnist` are in this release",
    ),
]

FIXES = {"juniper-cascor": CASCOR, "juniper-canopy": CANOPY}


class Refused(Exception):
    """An anchor is missing or ambiguous."""


def _ws(s: str) -> re.Pattern:
    return re.compile(r"\s+".join(re.escape(t) for t in s.split()))


def section_bounds(text: str, version: str) -> tuple[int, int]:
    """The first ``## [`` heading after ``## [Unreleased]`` must be ``## [<version>] - ``; return its section's span."""
    u = text.find("## [Unreleased]\n")
    first = text.find("\n## [", u + 1)
    if u == -1 or first == -1 or not text.startswith(f"## [{version}] - ", first + 1):
        raise Refused(f"the first release heading after [Unreleased] is not '## [{version}] - '")
    nxt = text.find("\n## [", first + 1)
    return first + 1, (len(text) if nxt == -1 else nxt + 1)


def apply_fix(sec: str, fix: Fix) -> tuple[str, str]:
    if fix.kind == "text":
        n_new = len(_ws(fix.new).findall(sec))
        old_hits = list(_ws(fix.old).finditer(sec))
        if n_new == 1 and not old_hits:
            return sec, "already at target"
        if n_new == 0 and len(old_hits) == 1:
            m = old_hits[0]
            return sec[: m.start()] + fix.new + sec[m.end() :], "applied"
        raise Refused(f"{fix.finding}: old text x{len(old_hits)}, new text x{n_new}")
    lines = sec.split("\n")
    new_first = fix.new.split("\n", 1)[0]
    new_prefix = new_first[: new_first.index("**", new_first.index("**") + 2) + 2]
    starts = [i for i, ln in enumerate(lines) if ln.startswith(fix.old)]
    have_new = [i for i, ln in enumerate(lines) if ln.startswith(new_prefix)]
    if not starts and len(have_new) == 1:
        return sec, "already at target"
    if len(starts) != 1 or have_new:
        raise Refused(f"{fix.finding}: item start x{len(starts)}, new item x{len(have_new)}")
    i = starts[0]
    indent = len(lines[i]) - len(lines[i].lstrip(" "))
    j = i + 1
    while j < len(lines):
        ln = lines[j]
        if not ln.strip() or ln.startswith("#"):
            break
        if ln.lstrip(" ").startswith("- ") and (len(ln) - len(ln.lstrip(" "))) <= indent:
            break
        j += 1
    replacement = fix.new.rstrip("\n").split("\n")
    return "\n".join(lines[:i] + replacement + lines[j:]), "applied"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, choices=sorted(FIXES))
    ap.add_argument("--tree", required=True, type=pathlib.Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    path = args.tree / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    try:
        lo, hi = section_bounds(text, VERSIONS[args.repo])
        sec = text[lo:hi]
        pending = 0
        for fix in FIXES[args.repo]:
            sec, status = apply_fix(sec, fix)
            pending += status == "applied"
            print(f"{args.repo} {fix.finding}: {status}")
    except Refused as exc:
        print(f"REFUSED: {exc}; nothing written", file=sys.stderr)
        return 2
    if args.check:
        print(f"--check: {pending} edit(s) still to make" if pending else "--check: every edit is at target")
        return 1 if pending else 0
    path.write_text(text[:lo] + sec + text[hi:], encoding="utf-8")
    print(f"wrote {path}: {pending} edit(s) applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
