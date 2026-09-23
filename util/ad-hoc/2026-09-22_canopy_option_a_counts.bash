#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_option_a_counts.bash
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
#    Two questions the Option A install probe left open.
#
#    1. PARITY. Does the pyproject-extras lane collect the SAME tests as today's
#       conf/requirements_ci.txt lane? "Collection exits 0" is not the check -- a lane that
#       silently collects 400 fewer tests also exits 0. The unit that matters is the test COUNT,
#       compared against the current lane built the same way.
#
#    2. IS `itsdangerous` LOAD-BEARING? The probe declared it and then observed it present, which
#       proves nothing about whether it was needed -- starlette does NOT depend on it (it ships in
#       the `starlette[full]` extra), so today it reaches canopy only via Flask in the flattened
#       snapshot. This uninstalls it and asserts that src/main.py STOPS importing, which is what
#       makes the new declaration a fix rather than cargo cult.
#
#    Read-only with respect to the canopy repository: works on COPIES.
#
#    Usage:  bash util/ad-hoc/2026-09-22_canopy_option_a_counts.bash
#####################################################################################################################################################################################################

set -uo pipefail

CANOPY="/home/pcalnon/Development/python/Juniper/juniper-canopy"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

unset LD_LIBRARY_PATH LIBTORCH

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Option A -- collection parity + itsdangerous necessity    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "scratch: ${WORK}"

collect_count () {   # $1 = venv python, $2 = repo dir
  # Count the collected test IDs directly rather than scraping pytest's summary line. An earlier
  # revision grepped for "tests collected|error" and matched `test_error_response.py: 3` from the
  # warnings summary -- the filename contains "error" -- so BOTH lanes returned the same wrong
  # string and the parity check passed vacuously. Node IDs contain "::" and nothing else in
  # `-q --collect-only` output does.
  ( cd "$2" && "$1" -m pytest src/tests --collect-only -q -p no:randomly 2>/dev/null \
      | grep -cE '^[^ ].*::' )
}

collect_status () {  # $1 = venv python, $2 = repo dir -- pytest's own summary line, for cross-check
  ( cd "$2" && "$1" -m pytest src/tests --collect-only -q -p no:randomly 2>/dev/null \
      | grep -E '^[0-9]+ (test|error)' | tail -1 )
}

# -- Lane 1: TODAY (requirements_ci.txt from main) -----------------------------------------------
echo
echo "-- lane 1: today's shape (pip install -r conf/requirements_ci.txt) --"
cp -a "${CANOPY}" "${WORK}/c_today"; rm -rf "${WORK}/c_today/.git"
python3 -m venv "${WORK}/ve_today"
T="${WORK}/ve_today/bin/python"
"${T}" -m pip install --quiet --upgrade "pip>=26.1.1"
"${T}" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
( cd "${WORK}/c_today" && "${T}" -m pip install --quiet -r conf/requirements_ci.txt )
( cd "${WORK}/c_today" && "${T}" -m pip install --quiet -e ".[juniper-cascor]" )
"${T}" -m pip install --quiet "h5py>=3.0"
TODAY="$(collect_count "${T}" "${WORK}/c_today")"
TODAY_S="$(collect_status "${T}" "${WORK}/c_today")"
echo "  collected node-ids: ${TODAY}   (pytest says: ${TODAY_S})"

# -- Lane 2: PROPOSED (pyproject extras) ---------------------------------------------------------
echo
echo "-- lane 2: proposed shape (pip install -e .[test,juniper-cascor]) --"
cp -a "${CANOPY}" "${WORK}/c_new"; rm -rf "${WORK}/c_new/.git"
python3 - "${WORK}/c_new/pyproject.toml" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1]); t = p.read_text()
a = '    "prometheus-client>=0.20.0",\n]'
assert t.count(a) == 1
t = t.replace(a, '''    "prometheus-client>=0.20.0",
    "starlette>=0.40",
    "itsdangerous>=2.0",
]''')
b = '[project.optional-dependencies]\n'
assert t.count(b) == 1
t = t.replace(b, '''[project.optional-dependencies]
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
PY
python3 -m venv "${WORK}/ve_new"
N="${WORK}/ve_new/bin/python"
"${N}" -m pip install --quiet --upgrade "pip>=26.1.1"
"${N}" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
( cd "${WORK}/c_new" && "${N}" -m pip install --quiet -e ".[test,juniper-cascor]" )
"${N}" -m pip install --quiet "h5py>=3.0"
NEW="$(collect_count "${N}" "${WORK}/c_new")"
NEW_S="$(collect_status "${N}" "${WORK}/c_new")"
echo "  collected node-ids: ${NEW}   (pytest says: ${NEW_S})"

echo
echo "-- PARITY --"
echo "  today:    ${TODAY} node-ids  | ${TODAY_S}"
echo "  proposed: ${NEW} node-ids  | ${NEW_S}"
if [ "${TODAY}" = "${NEW}" ] && [ "${TODAY}" -gt 1000 ] 2>/dev/null; then
  echo "  => IDENTICAL (${TODAY} node-ids, a plausible magnitude)"
else
  echo "  => NOT ESTABLISHED -- counts differ, or are implausibly small (a broken extractor reads as 0)"
fi

echo
echo "-- installed-distribution count (the pruning this buys) --"
echo "  today:    $("${T}" -m pip list --format=freeze | wc -l) distributions"
echo "  proposed: $("${N}" -m pip list --format=freeze | wc -l) distributions"

# -- Is itsdangerous load-bearing? ---------------------------------------------------------------
echo
echo "-- necessity check: remove itsdangerous from the PROPOSED env --"
"${N}" -m pip uninstall --quiet -y itsdangerous >/dev/null 2>&1
( cd "${WORK}/c_new/src" && "${N}" -c "import main" ) >/dev/null 2>"${WORK}/no_itsd.err"
RC=$?
if [ "${RC}" -ne 0 ]; then
  echo "  WITHOUT itsdangerous, 'import main' FAILS (rc=${RC}) -- the declaration is load-bearing:"
  tail -2 "${WORK}/no_itsd.err" | sed 's/^/      /'
else
  echo "  WITHOUT itsdangerous, 'import main' still succeeds -- the declaration is NOT required;"
  echo "  drop it from the proposed pyproject rather than shipping an unjustified dependency."
fi
