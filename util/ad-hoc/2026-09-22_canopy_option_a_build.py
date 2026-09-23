#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_option_a_build.py
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- migration
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#650
#
# Description:
#    Builds the juniper-canopy "Option A" change set into a scratch directory so the diff can be
#    reviewed before anything is pushed. Writes nothing into the canopy working tree.
#
#    Option A stops four CI lanes installing conf/requirements_ci.txt -- a `pip list --format=freeze`
#    snapshot in which 49 of 75 requirement lines are transitives declared as direct -- and installs
#    pyproject extras instead. canopy's own `security` job (ci.yml:565) already does exactly this,
#    as do all five sibling repos; canopy is the only repo of nine still using the flattened file as
#    an install manifest, which is why juniper-canopy#646 (filelock 4.x) is red here and green in
#    juniper-data#407 / juniper-data-client#207.
#
#    Every edit asserts its anchor is unique before applying, so a drifted file fails loudly rather
#    than silently patching the wrong line.
#
#    Usage:  python3 util/ad-hoc/2026-09-22_canopy_option_a_build.py <out-dir>
#####################################################################################################################################################################################################

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CANOPY = Path("/home/pcalnon/Development/python/Juniper/juniper-canopy")

# Files this change set touches. The three deletions have zero consumers (verified by repo-wide
# grep); dependabot nonetheless edits them on every pip PR, and four canopy PRs (#629, #551, #498,
# #481) exist solely to edit conf/requirements_bak.txt.
DELETIONS = [
    "conf/requirements_bak.txt",
    "conf/requirements_ci_2026-05-11_17-00-18.txt",
    "conf/requirements_ci_2026-05-18_17-19-21.txt",
]

EDITED = [
    "pyproject.toml",
    ".github/workflows/ci.yml",
    ".github/workflows/scheduled-tests.yml",
]


def sub_once(text: str, old: str, new: str, what: str) -> str:
    """Replace `old` with `new`, asserting exactly one occurrence."""
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"ABORT: {what}: expected exactly 1 occurrence, found {n}\n---\n{old}\n---")
    return text.replace(old, new)


def sub_exactly(text: str, old: str, new: str, count: int, what: str) -> str:
    """Replace every occurrence of `old`, asserting there are exactly `count` of them."""
    n = text.count(old)
    if n != count:
        raise SystemExit(f"ABORT: {what}: expected exactly {count} occurrences, found {n}\n---\n{old}\n---")
    return text.replace(old, new)


# ── pyproject.toml ───────────────────────────────────────────────────────────────────────────────

TEST_EXTRA = '''[project.optional-dependencies]
# The test surface, declared rather than inherited from a `pip list --format=freeze` snapshot.
#
# Every CI lane used to get pytest and friends from conf/requirements_ci.txt, which is generator
# output (`juniper-generate-dep-docs`) in which 49 of 75 requirement lines are transitives declared
# as direct. That made dependabot open PRs against packages canopy does not use, and one of them --
# `pre_commit`, which no lane that installs the file ever runs -- dragged in `virtualenv` and its
# `filelock<4` cap, making #646's `filelock>=4.0.0` unsatisfiable. canopy was the only repo of nine
# still installing that file; the `security` job here (ci.yml) and all five sibling repos already
# install from pyproject extras.
#
# Deliberately NOT [dev]: that extra pulls [demo], hence torch, hence ~2GB per lane.
test = [
    "pytest>=9.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    # pyproject's [tool.pytest.ini_options] sets `timeout = 60` under `--strict-config`, so an env
    # without pytest-timeout is a hard collection error, not a degraded run.
    "pytest-mock>=3.12",
    "pytest-timeout>=2.4.0",
    "coverage>=7.16.0",
    # Imported directly by the suite: anyio by src/tests/conftest.py, packaging by
    # src/tests/unit/test_client_version_floors.py. Both previously arrived only as transitives.
    "anyio>=4.15.1",
    "packaging>=26.3",
]
'''

PROD_DEPS = '''    "prometheus-client>=0.20.0",
    # Imported directly by production source and previously undeclared -- they resolved only as
    # transitives of fastapi (starlette) and Flask (itsdangerous), and Flask is in no lane's
    # declared dependency set at all. src/middleware.py imports BaseHTTPMiddleware / JSONResponse /
    # ASGIApp from starlette, and src/main.py imports starlette's SessionMiddleware, whose module
    # raises ImportError at import time unless itsdangerous is installed (starlette ships it in its
    # `full` extra, not its base requirements). Verified by uninstalling itsdangerous from an
    # otherwise-complete env: `import main` then fails.
    "starlette>=0.40",
    "itsdangerous>=2.0",
]'''


def build_pyproject(root: Path) -> None:
    p = root / "pyproject.toml"
    t = p.read_text(encoding="utf-8")
    t = sub_once(t, '    "prometheus-client>=0.20.0",\n]', PROD_DEPS, "pyproject: production deps")
    t = sub_once(t, "[project.optional-dependencies]\n", TEST_EXTRA, "pyproject: test extra")
    p.write_text(t, encoding="utf-8")


# ── .github/workflows/ci.yml ─────────────────────────────────────────────────────────────────────

DROP_NOTE = """          # conf/requirements_ci.txt is NOT installed here. It is generator output
          # (juniper-generate-dep-docs) -- a pip freeze in which most lines are transitives
          # declared as direct -- so installing it pulled packages no lane uses and coupled this
          # job to their version conflicts (juniper-ml#1994). The declared surface lives in
          # pyproject extras, which is what the security job and every sibling repo install."""


def build_ci(root: Path) -> None:
    p = root / ".github/workflows/ci.yml"
    t = p.read_text(encoding="utf-8")

    # 1. unit-tests lane: drop the file, keep the comment that explains what replaced it.
    t = sub_once(
        t,
        "          # Install all other CI dependencies\n          pip install -r conf/requirements_ci.txt\n",
        DROP_NOTE + "\n",
        "ci.yml: unit-tests requirements install",
    )

    # 2. integration + ui + dependency-docs lanes: three bare occurrences remain.
    t = sub_exactly(
        t, "          pip install -r conf/requirements_ci.txt\n", "", 3,
        "ci.yml: remaining requirements installs",
    )

    # 3. Fold the test extra into each lane's existing editable install.
    #
    # `observability` is included because the flattened file carried `sentry-sdk>=2.0.0` and these
    # lanes relied on it. canopy's own source never imports sentry_sdk -- juniper_observability's
    # configure_sentry does, internally -- so no import grep finds it, and collection succeeds
    # without it. Five unit tests then fail at RUN time with ModuleNotFoundError. Measured on
    # canopy#650's first CI round; `observability` is canopy's declared home for that dependency.
    t = sub_exactly(
        t, 'pip install -e ".[juniper-cascor]"',
        'pip install -e ".[test,juniper-cascor,observability]"', 2,
        "ci.yml: unit + integration extras",
    )
    t = sub_once(
        t, 'pip install -e ".[ui-test]"', 'pip install -e ".[test,ui-test,observability]"',
        "ci.yml: ui extras",
    )
    # dependency-docs generates the freeze FROM this env, so it installs the full declared surface
    # rather than the bare project -- the generated documentation then describes what canopy
    # actually declares.
    t = sub_once(
        t, "          pip install -e .\n",
        '          pip install -e ".[test,juniper-data,juniper-cascor,observability]"\n',
        "ci.yml: dependency-docs extras",
    )
    p.write_text(t, encoding="utf-8")


# ── .github/workflows/scheduled-tests.yml ────────────────────────────────────────────────────────


def build_scheduled(root: Path) -> None:
    p = root / ".github/workflows/scheduled-tests.yml"
    t = p.read_text(encoding="utf-8")
    # The existing comment describes a failed attempt to use `.[test]` before the extra existed.
    # It is now wrong in the other direction, so it is replaced rather than left to mislead.
    old_comment_start = "          # Match the main ci.yml unit-tests job: torch from the CPU index"
    i = t.find(old_comment_start)
    if i < 0:
        raise SystemExit("ABORT: scheduled-tests.yml: comment anchor not found")
    j = t.find("          pip install torch --index-url", i)
    if j < 0:
        raise SystemExit("ABORT: scheduled-tests.yml: torch install not found after comment")
    new_comment = (
        "          # Match the main ci.yml unit-tests job: torch from the CPU index (canopy's\n"
        "          # demo_mode.py and demo_backend.py import torch at module load), then the repo\n"
        "          # itself with the [test] extra. An earlier revision tried `.[test]` before that\n"
        "          # extra existed -- pip warned and exit-0'd, so the `||` fallback never fired and\n"
        "          # every scheduled run failed with `No module named pytest`. The extra now exists,\n"
        "          # so this is the shape that comment was reaching for.\n"
    )
    t = t[:i] + new_comment + t[j:]
    t = sub_once(t, "          pip install -r conf/requirements_ci.txt\n", "",
                 "scheduled-tests.yml: requirements install")
    # The scheduled lane runs `-m "slow or integration"` with NO path filter, so it sweeps the whole
    # tree including the observability unit tests. It gets the same extras as the unit lane.
    t = sub_once(t, 'pip install -e ".[juniper-cascor]"',
                 'pip install -e ".[test,juniper-cascor,observability]"',
                 "scheduled-tests.yml: extras")
    p.write_text(t, encoding="utf-8")


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/canopy_option_a")
    if out.exists():
        shutil.rmtree(out)
    # Copy only the three files this change set edits. A full copytree trips over the dangling
    # symlinks in canopy's notes/ tree, and nothing here needs the rest of the repo.
    for rel in EDITED:
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CANOPY / rel, dst)

    build_pyproject(out)
    build_ci(out)
    build_scheduled(out)
    for rel in DELETIONS:
        if not (CANOPY / rel).is_file():
            raise SystemExit(f"ABORT: deletion target missing from canopy: {rel}")

    print(f"built into {out}\n")
    for rel in EDITED:
        print("=" * 100)
        print(f"### {rel}")
        print("=" * 100)
        subprocess.run(["diff", "-u", str(CANOPY / rel), str(out / rel)], check=False)
    print("=" * 100)
    print("### deletions")
    for rel in DELETIONS:
        print(f"  D  {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
