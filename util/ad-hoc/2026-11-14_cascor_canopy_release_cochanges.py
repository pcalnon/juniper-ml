#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Purpose:       Co-change edits for the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 release proposals
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-11-14_cascor_canopy_release_cochanges.py
# File Path:     juniper-ml/util/ad-hoc/
#
# Date:          2026-11-14
# Last Modified: 2026-11-14
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     The Overtoad's ruling of 2026-11-13 (R-OBS-SC-2 round 2, Q2: "cascor + canopy now") has a session cut
#     juniper-cascor and juniper-canopy from main, "each raising its floors in the release PR" (round 1's
#     ruling 1, 2026-11-09: juniper-observability>=0.4.2, juniper-service-core>=0.7.2). The Overtoad chose the
#     versions on 2026-11-14: cascor 0.14.0, canopy 0.10.0.
#
#     util/release_train/propose.py opens each proposal with the version bump, the CHANGELOG move and the
#     AGENTS.md header. This tool makes the rest, as the proposal's second commit, on a tree of the release
#     branch's files (fetched from GitHub, never a primary checkout):
#
#       * pyproject.toml: the two floors and the comments that give their reasons;
#       * CHANGELOG.md: in the release's own section only, the Security entry's last sentence ("The
#         `pyproject.toml` floors move in the next release PR.") becomes the statement that they follow in
#         this release (the juniper-cascor 0.12.0 entry is the precedent for its wording);
#       * canopy only: the three fallback version literals (src/__init__.py, juniper_canopy/__init__.py,
#         src/canopy_constants.py), which src/tests/.../test_d8_d11_phase4_truth_up.py pins to pyproject and
#         propose.py does not bump (canopy 0.9.0's 6251cc57 is the precedent).
#
#     Every edit is exact: its old text must occur exactly once (in the CHANGELOG, inside the release's
#     section), or its new text must already be there, which reads "already at target".
#
# Usage:
#     python3 util/ad-hoc/2026-11-14_cascor_canopy_release_cochanges.py --repo juniper-cascor --tree DIR
#     python3 util/ad-hoc/2026-11-14_cascor_canopy_release_cochanges.py --repo juniper-canopy --tree DIR --check
#
#     DIR holds the branch's files at their repository paths. --check changes nothing and exits 0 only when
#     every edit is already at target. Exit 1: an edit is still to make (--check) or its anchor is missing or
#     ambiguous; nothing is written unless every edit applies.
#
#####################################################################################################################################################################################################
"""Co-change edits for the juniper-cascor 0.14.0 and juniper-canopy 0.10.0 release proposals."""

from __future__ import annotations

import argparse
import pathlib
import sys
from dataclasses import dataclass

CASCOR_OBS_OLD = """    # (juniper-ml notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md). 0.4.1
    # (2026-10-10) is the security patch: the shared ``configure_sentry``,
    # which src/api/observability.py delegates to, no longer sends
    # frame-local variables, which could hold the real API key.
    "juniper-observability>=0.4.1",
"""
CASCOR_OBS_NEW = """    # (juniper-ml notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md). 0.4.1
    # (2026-10-10) is the security patch: the shared ``configure_sentry``,
    # which src/api/observability.py delegates to, no longer sends
    # frame-local variables, which could hold the real API key. 0.4.2
    # (PyPI, 2026-11-09) is the second (R-OBS-SC-2): ``configure_sentry``
    # scrubs transactions as well as error events, redacts the parsed
    # cookies, and filters Sec-WebSocket-Protocol, X-CSRF-Token,
    # X-XSRF-Token and Proxy-Authorization. The locks moved in #748.
    "juniper-observability>=0.4.2",
"""

CASCOR_SC_OLD = """    # Floor 0.7.1 (2026-10-10), the security patch (non-ASCII X-API-Key is a
    # 401; bounded FailedAuthThrottle.check()). cascor's own APIKeyAuth and
    # FailedAuthThrottle are its copies in src/api/security.py, fixed by #689
    # and #710, so this floor is consistency with the lock and the siblings.
    "juniper-service-core>=0.7.1,<0.8.0",
"""
CASCOR_SC_NEW = """    # Floor 0.7.1 (2026-10-10), the security patch (non-ASCII X-API-Key is a
    # 401; bounded FailedAuthThrottle.check()). Floor 0.7.2 (PyPI,
    # 2026-11-09): FailedAuthThrottle's Retry-After rounds up instead of
    # truncating. cascor's own APIKeyAuth and FailedAuthThrottle are its
    # copies in src/api/security.py, fixed by #689, #710 and #757, so this
    # floor is consistency with the lock and the siblings.
    "juniper-service-core>=0.7.2,<0.8.0",
"""

CASCOR_CL_OLD = """    (juniper-ml `util/ad-hoc/2026-10-10_targeted_lock_refresh.py`). The `pyproject.toml` floors move in the next release
    PR.
"""
CASCOR_CL_NEW = """    (juniper-ml `util/ad-hoc/2026-10-10_targeted_lock_refresh.py`). The wheel's floors follow in this release:
    `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2,<0.8.0`, so a pip install over an older environment
    upgrades both. The locks moved in #748; the floors ride in the release proposal, because a `pyproject.toml` change on
    any branch but `release/` triggers `lockfile-update.yml`'s full `--upgrade` regen.
"""

CANOPY_OBS_OLD = """    # notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md). 0.4.1 (2026-10-10) is
    # the security patch: ``configure_sentry``, which canopy calls, no longer
    # sends frame-local variables, which could hold the real API key.
    "juniper-observability>=0.4.1,<0.5.0",
"""
CANOPY_OBS_NEW = """    # notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md). 0.4.1 (2026-10-10) is
    # the security patch: ``configure_sentry``, which canopy calls, no longer
    # sends frame-local variables, which could hold the real API key. 0.4.2
    # (PyPI, 2026-11-09) is the second (R-OBS-SC-2): it scrubs transactions
    # as well as error events, redacts the parsed cookies, and filters
    # Sec-WebSocket-Protocol (canopy's WebSocket key when ws_auth_enabled is
    # on), X-CSRF-Token, X-XSRF-Token and Proxy-Authorization. The lock
    # moved in #806. Query strings (the ?api_key= WebSocket parameter) are
    # 0.4.3's follow-up.
    "juniper-observability>=0.4.2,<0.5.0",
"""

CANOPY_SC_OLD = """    # 0.7.1 floor (2026-10-10): the security patch (non-ASCII X-API-Key is a 401;
    # bounded FailedAuthThrottle.check()). canopy's own key compare and throttle
    # live in src/security.py, so this is consistency with the lock and the
    # sibling services rather than a fix to canopy's auth path. The floor check
    # reads the INSTALLED metadata, so an existing editable install keeps
    # booting until it is reinstalled, and the reinstall upgrades the wheel.
    "juniper-service-core>=0.7.1,<0.8.0",
"""
CANOPY_SC_NEW = """    # 0.7.1 floor (2026-10-10): the security patch (non-ASCII X-API-Key is a 401;
    # bounded FailedAuthThrottle.check()). 0.7.2 floor (PyPI, 2026-11-09):
    # FailedAuthThrottle's Retry-After rounds up instead of truncating.
    # canopy's own key compare and throttle live in src/security.py, so this
    # is consistency with the lock and the sibling services rather than a fix
    # to canopy's auth path. The floor check reads the INSTALLED metadata, so
    # an existing editable install keeps booting until it is reinstalled, and
    # the reinstall upgrades the wheel.
    "juniper-service-core>=0.7.2,<0.8.0",
"""

CANOPY_CL_OLD = """    is held (juniper-ml `util/ad-hoc/2026-10-10_targeted_lock_refresh.py`). The `pyproject.toml` floors move in the next
    release PR.
"""
CANOPY_CL_NEW = """    is held (juniper-ml `util/ad-hoc/2026-10-10_targeted_lock_refresh.py`). The wheel's floors follow in this release:
    `juniper-observability>=0.4.2,<0.5.0` and `juniper-service-core>=0.7.2,<0.8.0`, so a pip install over an older
    environment upgrades both. The boot-time `enforce_dependency_floors` reads the **installed** metadata, so an existing
    editable install keeps booting until it is reinstalled; the reinstall upgrades it. The lock moved in #806; the floors
    ride in the release proposal, because a `pyproject.toml` change on any branch but `release/` triggers
    `lockfile-update.yml`'s full `--upgrade` regen.
"""


# The coverage pass (publish procedure §11.7, control 2: diff the tag window against the section), as cascor
# 0.13.0's 037ac8a4 did: the Dependabot lock moves since the last tag are described nowhere, and a Release mints
# the image as well as the wheel. Measured on 2026-11-15 by diffing each lock between the tag and the release
# head (v0.13.0..3c4d1dec, v0.9.0..cb3f1562). Each bullet goes in at the end of its section's Changed list.
CASCOR_FIXED_ANCHOR = "\n### Fixed\n"
CASCOR_LOCKS_BULLET = """- **The dependency locks moved** (`requirements.lock`, and `requirements-cpu.lock`, which the image installs),
  through the Dependabot updates merged since 0.13.0 (#744, #751) and #748's two security pins (Security, below).
  The notable runtime pins in `requirements-cpu.lock`: `fastapi` 0.162.0 -> 0.162.2, `pydantic` 2.14.1 -> 2.14.3
  (with `pydantic-core` 2.50.4 and `pydantic-settings` 2.16.2), `python-dateutil` 3.0.0 -> 4.0.0, `sentry-sdk`
  2.73.0 -> 2.74.0, `websockets` 17.3 -> 17.4, `anyio` 4.15.1 -> 4.16.0 and `cachetools` 7.2.5 -> 8.0.0, plus six
  smaller moves, and `six` leaves both locks. `requirements.lock` also moves the CUDA 13 wheels (`cuda-toolkit`
  13.0.3.0 -> 13.2.2, `triton` 3.8.0 -> 3.9.0 and the `nvidia-*` set). Apart from the two security floors
  (Security, below), the wheel's declared requirements are unchanged.
"""

CANOPY_SECURITY_ANCHOR = "\n### Security\n"
CANOPY_LOCK_BULLET = """- **The dependency lock moved** (`requirements.lock`, which the image installs), through the lock regenerations of
  the Dependabot updates merged since 0.9.0 (#755, #770, #771, #772, #810, #811, #813), F-CANOPY-069's fix (#760)
  and #806's two security pins (Security, below). The notable runtime pins: `fastapi` 0.143.3 -> 0.162.5 with
  `starlette` 1.8.0 -> 1.10.0, `dash` 4.4.1 -> 4.5.0, `pydantic` 2.14.1 -> 2.14.3 (with `pydantic-core` 2.50.4 and
  `pydantic-settings` 2.16.2), `sentry-sdk` 2.72.0 -> 2.74.0, `websockets` 17.2 -> 17.4, `python-multipart`
  0.0.32 -> 0.0.33, `importlib-metadata` 9.0.1 -> 10.2.0, `anyio` 4.15.1 -> 4.16.0 and `certifi` 2026.7.22 ->
  2026.10.23, plus seven smaller moves, and `lazy-importer` 0.1.0 joins it. Apart from the dash floor (above) and the
  two security floors (Security, below), the wheel's declared requirements are unchanged.
"""

CANOPY_DASH_OLD = """dependencies, `comm` and `janus`, at the lock's versions. Everything canopy tests runs dash 4.x (the lock's 4.4.1,
  CI's 4.4.1 pip lane and 4.1.0 conda lane, every live drive in the E2E ledger), and a floor that nothing tests is
"""
CANOPY_DASH_NEW = """dependencies, `comm` and `janus`, at the lock's versions. Everything canopy tested at the fix ran dash 4.x (the
  lock's 4.4.1, which has since moved to 4.5.0, CI's 4.4.1 pip lane and 4.1.0 conda lane, every live drive in the E2E
  ledger), and a floor that nothing tests is
"""


@dataclass(frozen=True)
class Edit:
    """One exact replacement in one file; ``section`` bounds a CHANGELOG edit to ``## [<section>] - ``."""

    path: str
    old: str
    new: str
    section: str | None = None


EDITS: dict[str, tuple[str, list[Edit]]] = {
    "juniper-cascor": (
        "0.14.0",
        [
            Edit("pyproject.toml", CASCOR_OBS_OLD, CASCOR_OBS_NEW),
            Edit("pyproject.toml", CASCOR_SC_OLD, CASCOR_SC_NEW),
            Edit("CHANGELOG.md", CASCOR_CL_OLD, CASCOR_CL_NEW, section="0.14.0"),
            # The coverage pass (the proposal's third commit).
            Edit("CHANGELOG.md", CASCOR_FIXED_ANCHOR, CASCOR_LOCKS_BULLET + CASCOR_FIXED_ANCHOR, section="0.14.0"),
        ],
    ),
    "juniper-canopy": (
        "0.10.0",
        [
            Edit("pyproject.toml", CANOPY_OBS_OLD, CANOPY_OBS_NEW),
            Edit("pyproject.toml", CANOPY_SC_OLD, CANOPY_SC_NEW),
            Edit("CHANGELOG.md", CANOPY_CL_OLD, CANOPY_CL_NEW, section="0.10.0"),
            Edit("src/__init__.py", '    __version__ = "0.9.0"\n', '    __version__ = "0.10.0"\n'),
            Edit("juniper_canopy/__init__.py", '    __version__ = "0.9.0"\n', '    __version__ = "0.10.0"\n'),
            Edit("src/canopy_constants.py", 'def resolve_app_version(fallback: str = "0.9.0") -> str:\n', 'def resolve_app_version(fallback: str = "0.10.0") -> str:\n'),
            # The coverage pass (the proposal's third commit).
            Edit("CHANGELOG.md", CANOPY_SECURITY_ANCHOR, CANOPY_LOCK_BULLET + CANOPY_SECURITY_ANCHOR, section="0.10.0"),
            Edit("CHANGELOG.md", CANOPY_DASH_OLD, CANOPY_DASH_NEW, section="0.10.0"),
        ],
    ),
}


def section_bounds(text: str, version: str) -> tuple[int, int]:
    """Return [start, end) of the release's section: the first ``## [`` heading after ``## [Unreleased]``.

    That heading must be ``## [<version>] - ``. It is required to be the FIRST release heading, not the only
    one: juniper-canopy's CHANGELOG keeps its pre-2026 numbering below (``## [0.10.0] - 2025-12-06``, and old
    0.3.0 to 0.9.0 beside the new ones), and the ceremony's ``changelog_version_section`` reads the topmost
    match, as this does.
    """
    unreleased = "## [Unreleased]\n"
    if not text.startswith(unreleased) and text.count("\n" + unreleased) != 1:
        raise ValueError("expected exactly one '## [Unreleased]' heading")
    first = text.find("\n## [", text.index(unreleased) + len(unreleased) - 1)
    if first == -1 or not text.startswith(f"## [{version}] - ", first + 1):
        found = text[first + 1 : text.find("\n", first + 1)] if first != -1 else "none"
        raise ValueError(f"the first release heading after [Unreleased] is {found!r}, not '## [{version}] - '")
    start = first + 1
    nxt = text.find("\n## [", start + 1)
    return start, (len(text) if nxt == -1 else nxt + 1)


def apply_edit(text: str, edit: Edit) -> tuple[str, str]:
    """Apply one edit; return (new text, status). Status: 'applied' or 'already at target'. Raises on a bad anchor."""
    lo, hi = (0, len(text)) if edit.section is None else section_bounds(text, edit.section)
    region = text[lo:hi]
    n_new = region.count(edit.new)
    # An insertion's new text CONTAINS its anchor, so the anchor is counted outside the new text.
    n_old_outside = region.replace(edit.new, "\0").count(edit.old)
    if n_new == 1 and n_old_outside == 0:
        return text, "already at target"
    if n_new == 0 and region.count(edit.old) == 1:
        return text[:lo] + region.replace(edit.old, edit.new, 1) + text[hi:], "applied"
    where = f" within [{edit.section}]" if edit.section else ""
    raise ValueError(f"{edit.path}{where}: old text occurs {region.count(edit.old)} time(s) and new text {n_new} time(s); expected 1 and 0, or new once with no old outside it")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, choices=sorted(EDITS))
    ap.add_argument("--tree", required=True, type=pathlib.Path, help="directory holding the release branch's files at their repository paths")
    ap.add_argument("--check", action="store_true", help="change nothing; exit 0 only if every edit is already at target")
    args = ap.parse_args(argv)

    version, edits = EDITS[args.repo]
    texts: dict[str, str] = {}
    pending = 0
    try:
        for edit in edits:
            path = args.tree / edit.path
            if edit.path not in texts:
                texts[edit.path] = path.read_text(encoding="utf-8")
            texts[edit.path], status = apply_edit(texts[edit.path], edit)
            pending += status == "applied"
            print(f"{args.repo} {version} {edit.path}: {status}")
    except (OSError, ValueError) as exc:
        print(f"REFUSED: {exc}; nothing written", file=sys.stderr)
        return 1
    if args.check:
        print(f"--check: {pending} edit(s) still to make" if pending else "--check: every edit is at target")
        return 1 if pending else 0
    for rel, text in texts.items():
        (args.tree / rel).write_text(text, encoding="utf-8")
    print(f"wrote {len(texts)} file(s); {pending} edit(s) applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
