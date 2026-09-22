#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_option_a_probe.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#650
#
# Description:
#    Does juniper-canopy's unit-test lane still stand up when it STOPS installing
#    conf/requirements_ci.txt and installs pyproject extras instead (Option A)?
#
#    conf/requirements_ci.txt is a 75-line flattened snapshot of which 49 lines are transitives
#    declared as direct. Dropping it removes packages that nothing declares -- which is the point --
#    but some of those transitives are load-bearing by ACCIDENT. The one that matters:
#    src/main.py:533 imports starlette.middleware.sessions.SessionMiddleware, and that module
#    raises at import time unless `itsdangerous` is installed. Today `itsdangerous` arrives only
#    because Flask is listed in the snapshot. Nothing in pyproject declares either.
#
#    This probe builds the lane exactly as the proposed ci.yml would, then checks the accident
#    cases explicitly BEFORE running collection, so a missing transitive is named rather than
#    showing up as an opaque collection error.
#
#    Read-only with respect to the canopy repository: it works on a COPY.
#
#    Usage:  bash util/ad-hoc/2026-09-22_canopy_option_a_probe.bash
#####################################################################################################################################################################################################

set -uo pipefail

CANOPY="/home/pcalnon/Development/python/Juniper/juniper-canopy"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# The host carries a rust_mudgeon LIBTORCH/LD_LIBRARY_PATH that shadows the venv's torch and
# produces `undefined symbol` collection errors unrelated to anything under test.
unset LD_LIBRARY_PATH LIBTORCH

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  canopy Option A -- unit lane without requirements_ci.txt  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "scratch: ${WORK}"
echo

cp -a "${CANOPY}" "${WORK}/canopy"
rm -rf "${WORK}/canopy/.git"
cd "${WORK}/canopy" || exit 2

# Apply the proposed pyproject change: a lean [test] extra plus the three undeclared directs.
python3 - <<'PY'
from pathlib import Path
p = Path("pyproject.toml")
t = p.read_text()

# starlette is imported by production source (src/middleware.py, src/main.py) and declared nowhere.
anchor = '    "prometheus-client>=0.20.0",\n]'
assert t.count(anchor) == 1, "prometheus-client anchor not unique"
t = t.replace(anchor, '''    "prometheus-client>=0.20.0",
    "starlette>=0.40",
    "itsdangerous>=2.0",
]''')

# A lean test extra -- deliberately NOT [dev], which pulls [demo] and ~2GB of torch.
anchor2 = '[project.optional-dependencies]\n'
assert t.count(anchor2) == 1
t = t.replace(anchor2, '''[project.optional-dependencies]
test = [
    "pytest>=9.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "pytest-mock>=3.12",
    "pytest-timeout>=2.4.0",
    "coverage>=7.16.0",
    "anyio>=4.15.1",
    "packaging>=26.3",
]
''')
p.write_text(t)
print("pyproject patched")
PY

python3 -m venv "${WORK}/ve"
PY="${WORK}/ve/bin/python"
"${PY}" -m pip install --quiet --upgrade "pip>=26.1.1"

echo "── install, exactly as the proposed unit lane would ──"
"${PY}" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu; echo "  torch            rc=$?"
"${PY}" -m pip install --quiet -e ".[test,juniper-cascor]";                            echo "  -e .[test,cascor] rc=$?"
"${PY}" -m pip install --quiet "h5py>=3.0";                                            echo "  h5py             rc=$?"
echo

echo "── the ACCIDENT cases: transitives that only requirements_ci.txt supplied ──"
"${PY}" - <<'PY'
import importlib, sys
checks = [
    ("starlette.middleware.sessions", "SessionMiddleware  (src/main.py:533)"),
    ("starlette.middleware.base",     "BaseHTTPMiddleware (src/middleware.py:11)"),
    ("itsdangerous",                  "required by starlette SessionMiddleware"),
    ("anyio",                         "src/tests/conftest.py"),
    ("packaging",                     "src/tests/unit/test_client_version_floors.py"),
    ("pytest_timeout",                "pyproject timeout=60 under --strict-config"),
    ("pytest_mock",                   "4 test modules use the mocker fixture"),
    ("pytest_asyncio",                "async tests"),
]
bad = 0
for mod, why in checks:
    try:
        importlib.import_module(mod)
        print(f"  OK      {mod:32} {why}")
    except Exception as exc:
        bad += 1
        print(f"  MISSING {mod:32} {why}  -> {type(exc).__name__}: {exc}")
sys.exit(1 if bad else 0)
PY
ACC=$?
echo "  accident-case check rc=${ACC}"
echo

echo "── does the app import at all? ──"
cd "${WORK}/canopy/src" && "${PY}" -c "import main; print('  src/main.py imported OK')" 2>&1 | tail -5
cd "${WORK}/canopy" || exit 2

echo
echo "── pytest collection (the real gate) ──"
"${PY}" -m pytest src/tests --collect-only -q -p no:randomly 2>&1 | tail -8
echo "collection rc=${PIPESTATUS[0]}"
