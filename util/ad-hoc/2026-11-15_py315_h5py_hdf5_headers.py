#!/usr/bin/env python3
"""Let h5py build from its sdist on the informational Python 3.15 leg (canopy and cascor `unit-tests`; one worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- migration (phase 2 of the ecosystem's Python 3.15 migration)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_py315_informational_green_legs.py (the green-legs fix whose warnings named this);
         prompts/thread-handoff_automated-prompts/
         HANDOFF_2026-11-15_python-3-15-phase-2-approved-deploy-precommit-matrix.md (Task 2, item 1)

Why this exists
---------------
Phase 2 of the Python 3.15 migration (approved by the owner on 2026-11-15) works through the problems the
informational 3.15 legs found. The first stops three repos' legs before any test runs: h5py publishes no CPython
3.15 wheel. Re-probed on PyPI 2026-11-15: 3.16.0 (2026-03-06) is the newest release, and its wheels are
cp310-cp314. So pip builds h5py from the sdist on 3.15, and that build needs libhdf5's headers and pkg-config,
which the runner image lacks. juniper-canopy's and juniper-cascor's `unit-tests` 3.15 legs fail at
`Install dependencies` (`Unable to load dependency HDF5`), and canopy's then fails 5 snapshot tests for want of h5py.

The fix installs `libhdf5-dev` and `pkg-config` on the 3.15 leg only (`if: matrix.experimental == true`, Linux),
right before `Install dependencies`, so the sdist builds. The step carries an `id` and the leg's
`continue-on-error` expression like every other step of the job (the green-legs rule), so the
`Report the informational Python 3.15 result` step lists it too. The blocking legs skip it and are unchanged.
Drop the step once h5py ships a cp315 wheel.

juniper-ml's own `Regression Tests` leg (its `tests` job) has the same failure, and `--repo juniper-ml` applies the
same step there, before `Install test dependencies`. It also corrects that step's comment, which said h5py never
builds from source. There the failed h5py install also skipped setuptools, wheel and cryptography, which the step
installs after it.

Every edit is an exact-substring replacement that must match exactly once, so the set can be re-applied onto a moved
`origin/main` from a fresh worktree (re-run, never re-type) and a drifted base fails loudly instead of being
half-edited. Nothing is written unless every edit matches, and each written file is read back.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_h5py_hdf5_headers.py --repo juniper-canopy --worktree <canopy worktree>
    python3 util/ad-hoc/2026-11-15_py315_h5py_hdf5_headers.py --repo juniper-cascor --worktree <cascor worktree> --check

Bases: juniper-canopy origin/main bab3ec8d (juniper-canopy#820); juniper-cascor origin/main f5ffefb7
(juniper-cascor#761); juniper-ml origin/main 725c6343 (juniper-ml#2584). All 2026-11-15.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

CI = ".github/workflows/ci.yml"
CHANGELOG = "CHANGELOG.md"


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str


INSTALL_ANCHOR = """\
      - name: Install dependencies
        id: install-dependencies
        continue-on-error: ${{ matrix.experimental == true }}
"""


def hdf5_step(how_h5py_arrives: str) -> str:
    return f"""\
      - name: Install the HDF5 headers h5py builds against (Python 3.15 only)
        # Phase 2 of the ecosystem's Python 3.15 migration. h5py publishes no CPython 3.15 wheel
        # (3.16.0, 2026-03-06, the newest release, ships cp310-cp314), so on the 3.15 leg pip builds
        # it from the sdist, and that build needs libhdf5's headers and pkg-config, which the runner
        # image lacks. {how_h5py_arrives}
        # The blocking legs install h5py's wheel and skip this step. Drop it once h5py ships a cp315
        # wheel.
        id: install-the-hdf5-headers-h5py-builds-against
        if: matrix.experimental == true && runner.os == 'Linux'
        continue-on-error: ${{{{ matrix.experimental == true }}}}
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends libhdf5-dev pkg-config

"""


FIXED_ANCHOR = "### Fixed\n\n- **The informational Python 3.15 legs no longer show as failed checks**"


def changelog_entry(repo_effect: str, job: str = "unit-tests", install_step: str = "Install dependencies") -> str:
    return f"""\
### Fixed

- **h5py installs on the informational Python 3.15 leg.** Phase 2 of the ecosystem's Python 3.15 migration (approved
  by the owner on 2026-11-15) works through what the 3.15 legs found, and this is the first item: h5py publishes no
  CPython 3.15 wheel (3.16.0, 2026-03-06, the newest release on PyPI when re-probed on 2026-11-15, ships
  cp310-cp314), so pip builds it from the sdist there, and the runner image lacks the libhdf5 headers and
  pkg-config that build needs. {repo_effect}
  - `ci.yml`'s `{job}` gains `Install the HDF5 headers h5py builds against (Python 3.15 only)`, which installs
    `libhdf5-dev` and `pkg-config` before `{install_step}`, on the 3.15 leg alone
    (`if: matrix.experimental == true && runner.os == 'Linux'`). Like the job's other steps it carries an `id` and
    the leg's `continue-on-error` expression, so the 3.15 report step lists it.
  - The blocking legs skip the step and still install h5py's wheel. The 3.15 leg stays informational.
  - Drop the step once h5py ships a cp315 wheel. Applied by juniper-ml's
    `util/ad-hoc/2026-11-15_py315_h5py_hdf5_headers.py`.

- **The informational Python 3.15 legs no longer show as failed checks**"""


ML_INSTALL_ANCHOR = """\
      - name: Install test dependencies
        id: install-test-dependencies
        continue-on-error: ${{ matrix.experimental == true }}
"""

ML_COMMENT_OLD = """\
          # without it the suites cannot even be collected. Wheels exist for the
          # whole 3.12/3.13/3.14 matrix, so this never builds from source.
"""

ML_COMMENT_NEW = """\
          # without it the suites cannot even be collected. Wheels exist for 3.12,
          # 3.13 and 3.14. 3.15 has none yet, so on the informational 3.15 leg pip
          # builds it from the sdist, against the HDF5 headers the step above
          # installs.
"""

EDITS: dict[str, list[Edit]] = {
    "juniper-ml": [
        Edit(
            CI,
            ML_INSTALL_ANCHOR,
            hdf5_step(
                "Without them `Install test dependencies` stops at\n"
                "        # `pip install \"h5py>=3.11\"`, so the packages it installs after h5py (setuptools, wheel,\n"
                "        # cryptography) are never installed either."
            )
            + ML_INSTALL_ANCHOR,
        ),
        Edit(CI, ML_COMMENT_OLD, ML_COMMENT_NEW),
        Edit(
            CHANGELOG,
            FIXED_ANCHOR,
            changelog_entry(
                "On `main`'s 3.15 leg (run 43681267307) h5py's wheel build stopped at `Unable to load dependency\n"
                "  HDF5`. That ended `Install test dependencies` at `pip install \"h5py>=3.11\"`, before it installed\n"
                "  setuptools, wheel and cryptography, so `Run Python regression tests` then failed 6 tests on `No module named\n"
                "  'setuptools'`. The step's comment, which said h5py never builds from source, now names the 3.15 exception.",
                job="tests",
                install_step="Install test dependencies",
            ),
        ),
    ],
    "juniper-canopy": [
        Edit(
            CI,
            INSTALL_ANCHOR,
            hdf5_step("Without them `Install dependencies` fails at\n        # `pip install \"h5py>=3.0\"`, and the snapshot tests that need h5py then fail.")
            + INSTALL_ANCHOR,
        ),
        Edit(
            CHANGELOG,
            FIXED_ANCHOR,
            changelog_entry(
                "On `main`'s 3.15 leg (run 43675560841) h5py's wheel build stopped at `Unable to load dependency\n"
                "  HDF5`, and 5 of `src/tests/unit/test_main_gate_coverage_snapshots.py`'s tests then failed for want of it: 4\n"
                "  on `No module named 'h5py'`, 1 on the route's `500: h5py not available` (5120 passed)."
            ),
        ),
    ],
    "juniper-cascor": [
        Edit(
            CI,
            INSTALL_ANCHOR,
            hdf5_step("Without them `Install dependencies` fails at `pip install -e \".[all]\"`\n        # (h5py is in the `ml` extra), and the leg runs no test.")
            + INSTALL_ANCHOR,
        ),
        Edit(
            CHANGELOG,
            FIXED_ANCHOR,
            changelog_entry(
                "On `main`'s 3.15 leg (run 43678353051) h5py's wheel build stopped at `Unable to load dependency\n"
                "  HDF5`, which failed `pip install -e \".[all]\"` (h5py is in the `ml` extra), so pytest and coverage were never\n"
                "  installed and the leg ran no test."
            ),
        ),
    ],
}


def apply(repo: str, worktree: Path, check_only: bool) -> int:
    edits = EDITS[repo]
    contents: dict[str, str] = {}
    bad = 0
    for e in edits:
        path = worktree / e.path
        if e.path not in contents:
            contents[e.path] = path.read_text(encoding="utf-8")
        text = contents[e.path]
        n = text.count(e.old)
        label = f"{e.path}: {e.old.strip().splitlines()[0][:90]!r}"
        if n != 1:
            print(f"MISMATCH ({n} occurrences, want 1): {label}")
            bad += 1
            continue
        print(f"ok: {label}")
        contents[e.path] = text.replace(e.old, e.new, 1)
    if bad:
        print(f"{bad} edit(s) did not match exactly once; nothing written", file=sys.stderr)
        return 1
    if check_only:
        print(f"check: all {len(edits)} edit(s) match exactly once")
        return 0
    for rel, text in contents.items():
        path = worktree / rel
        path.write_text(text, encoding="utf-8")
        if path.read_text(encoding="utf-8") != text:  # read back our own write
            print(f"READ-BACK MISMATCH: {rel}", file=sys.stderr)
            return 1
    print(f"wrote {len(contents)} file(s), {len(edits)} edit(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, choices=sorted(EDITS))
    ap.add_argument("--worktree", required=True, type=Path, help="a checkout of --repo (never a primary)")
    ap.add_argument("--check", action="store_true", help="report matches only; write nothing")
    args = ap.parse_args()
    return apply(args.repo, args.worktree, args.check)


if __name__ == "__main__":
    sys.exit(main())
