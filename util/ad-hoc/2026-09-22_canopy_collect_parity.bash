#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_collect_parity.bash
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
#    Collection parity for juniper-canopy#650: does installing the declared surface from pyproject
#    extras collect the SAME tests as installing conf/requirements_ci.txt?
#
#    Third revision. The first scraped pytest's summary with a grep that also matched
#    `test_error_response.py: 3` from the warnings block -- the filename contains "error" -- so both
#    lanes returned the same wrong string and parity "passed" vacuously. The second counted node-ids
#    but discarded stderr, and reported 0 for both lanes with no way to see why.
#
#    This revision:
#      * KEEPS the working tree (no cleanup trap) so the extractor can be fixed without paying for
#        two torch installs again;
#      * captures each lane's collection output to a FILE, stdout and stderr both, so a failure is
#        legible rather than an empty string;
#      * writes the sorted node-id SETS and diffs them -- a count alone cannot tell "5 added, 0
#        dropped" from "K dropped, 5+K added";
#      * refuses to call parity established unless both lanes collected a plausible number.
#
#    Usage:  bash util/ad-hoc/2026-09-22_canopy_collect_parity.bash [workdir]
#####################################################################################################################################################################################################

set -uo pipefail

CANOPY="/home/pcalnon/Development/python/Juniper/juniper-canopy"
WORK="${1:-/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/b71ebef9-0742-4ce0-b72d-110ca6a9dbbf/scratchpad/parity}"

unset LD_LIBRARY_PATH LIBTORCH
rm -rf "${WORK}"; mkdir -p "${WORK}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  canopy#650 -- collection parity (kept workdir)            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "workdir: ${WORK}  (deliberately NOT cleaned up)"

build_repo () {   # $1 = dest, $2 = "today" | "new"
  cp -a "${CANOPY}" "$1"
  rm -rf "$1/.git"
  if [ "$2" = "new" ]; then
    python3 "$(dirname "$0")/2026-09-22_canopy_option_a_build.py" "${WORK}/built" >/dev/null
    cp "${WORK}/built/pyproject.toml" "$1/pyproject.toml"
  fi
}

run_lane () {     # $1 = tag, $2 = repo dir, $3 = venv dir, $4 = "today" | "new"
  local tag="$1" repo="$2" ve="$3" mode="$4"
  python3 -m venv "${ve}"
  local PY="${ve}/bin/python"
  "${PY}" -m pip install --quiet --upgrade "pip>=26.1.1"
  "${PY}" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
  if [ "${mode}" = "today" ]; then
    ( cd "${repo}" && "${PY}" -m pip install --quiet -r conf/requirements_ci.txt )
    ( cd "${repo}" && "${PY}" -m pip install --quiet -e ".[juniper-cascor]" )
  else
    ( cd "${repo}" && "${PY}" -m pip install --quiet -e ".[test,juniper-cascor]" )
  fi
  "${PY}" -m pip install --quiet "h5py>=3.0"
  "${PY}" -m pip list --format=freeze > "${WORK}/${tag}.dists"

  # Both streams to the file: an empty result must be explainable.
  ( cd "${repo}" && "${PY}" -m pytest src/tests --collect-only -q -p no:randomly ) \
      > "${WORK}/${tag}.collect" 2>&1
  echo "$?" > "${WORK}/${tag}.rc"

  # pytest 9's `-q --collect-only` prints one `<file>: <count>` line per file, NOT node ids.
  # An earlier revision grepped for '::' and found nothing in either lane, reporting 0 == 0 --
  # which the plausibility guard below correctly refused to call parity. Keep BOTH the file set
  # and the per-file counts: a file that silently loses tests keeps its line.
  grep -E '^[^ ].*\.py: [0-9]+$' "${WORK}/${tag}.collect" \
      | sed 's/[[:space:]]*$//' | sort -u > "${WORK}/${tag}.ids"
}

echo
echo "-- lane 1: today (pip install -r conf/requirements_ci.txt) --"
build_repo "${WORK}/c_today" today
run_lane today "${WORK}/c_today" "${WORK}/ve_today" today
echo "   pytest rc=$(cat "${WORK}/today.rc")  node-ids=$(wc -l < "${WORK}/today.ids")  dists=$(wc -l < "${WORK}/today.dists")"

echo
echo "-- lane 2: proposed (pip install -e .[test,juniper-cascor]) --"
build_repo "${WORK}/c_new" new
run_lane new "${WORK}/c_new" "${WORK}/ve_new" new
echo "   pytest rc=$(cat "${WORK}/new.rc")  node-ids=$(wc -l < "${WORK}/new.ids")  dists=$(wc -l < "${WORK}/new.dists")"

T=$(wc -l < "${WORK}/today.ids"); N=$(wc -l < "${WORK}/new.ids")

echo
echo "-- PARITY (set comparison, not a count) --"
# Floor is in FILES (canopy collects ~345), not node-ids -- the 1000 here was a node-id-era
# figure left over from the revision whose extractor matched nothing.
if [ "${T}" -lt 100 ] || [ "${N}" -lt 100 ]; then
  echo "  NOT ESTABLISHED -- a lane collected implausibly few files (today=${T} new=${N})."
  echo "  Last lines of each collection log:"
  echo "  --- today ---"; tail -6 "${WORK}/today.collect" | sed 's/^/     /'
  echo "  --- new   ---"; tail -6 "${WORK}/new.collect"   | sed 's/^/     /'
  exit 1
fi

echo "  today=${T}  proposed=${N}"
echo "  DROPPED (in today, not in proposed):"
comm -23 "${WORK}/today.ids" "${WORK}/new.ids" | head -20 | sed 's/^/     - /'
DROP=$(comm -23 "${WORK}/today.ids" "${WORK}/new.ids" | wc -l)
echo "  GAINED (in proposed, not in today):"
comm -13 "${WORK}/today.ids" "${WORK}/new.ids" | head -20 | sed 's/^/     + /'
GAIN=$(comm -13 "${WORK}/today.ids" "${WORK}/new.ids" | wc -l)
echo
echo "  dropped=${DROP}  gained=${GAIN}"
if [ "${DROP}" -eq 0 ] && [ "${GAIN}" -eq 0 ]; then
  echo "  => IDENTICAL SETS (${T} node-ids)"
else
  echo "  => SETS DIFFER -- resolve before merging"
  exit 1
fi
