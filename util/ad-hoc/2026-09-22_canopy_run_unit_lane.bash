#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_run_unit_lane.bash
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
#    RUN juniper-canopy's unit lane against the juniper-canopy#650 install shape, using the exact
#    pytest invocation from .github/workflows/ci.yml.
#
#    Why this and not the collection-parity probe: collection parity was IDENTICAL (345 files /
#    7538 tests, same sets) and CI still failed. `sentry_sdk` is reached only at run time -- canopy
#    never imports it, `juniper_observability.configure_sentry` does, and five unit tests drive that
#    path. Collection is not execution, and an import grep cannot see a dependency's own imports.
#    Running the suite is the only check that covers both.
#
#    Expects the venv + repo copy left behind by 2026-09-22_canopy_collect_parity.bash.
#
#    Usage:  bash util/ad-hoc/2026-09-22_canopy_run_unit_lane.bash [parity-workdir]
#####################################################################################################################################################################################################

set -uo pipefail

WORK="${1:-/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/b71ebef9-0742-4ce0-b72d-110ca6a9dbbf/scratchpad/parity}"
REPO="${WORK}/c_new"
PY="${WORK}/ve_new/bin/python"

unset LD_LIBRARY_PATH LIBTORCH

if [ ! -x "${PY}" ]; then
  echo "no venv at ${PY} -- run 2026-09-22_canopy_collect_parity.bash first" >&2
  exit 2
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  canopy#650 -- RUN the unit lane (ci.yml invocation)       ║"
echo "╚════════════════════════════════════════════════════════════╝"
"${PY}" -c "import sentry_sdk, sys; print('sentry_sdk', sentry_sdk.VERSION)" 2>/dev/null || echo "sentry_sdk ABSENT"
echo

cd "${REPO}" || exit 2
mkdir -p reports/junit

# Exactly ci.yml's unit-tests invocation, minus the coverage flags (coverage thresholds are a
# separate gate and would obscure a plain pass/fail here).
"${PY}" -m pytest \
  -m "not requires_cascor and not requires_server and not slow" \
  src/tests/unit/ src/tests/regression/ src/tests/contract/ src/tests/performance/ \
  --timeout=60 \
  -q --no-header -p no:randomly 2>&1 | tail -25

echo
echo "pytest exit: ${PIPESTATUS[0]}"
