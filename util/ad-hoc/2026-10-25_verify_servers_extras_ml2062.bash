#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────────────────────────
# Project:      juniper-ml
# Sub-Project:  ad-hoc tooling
# Author:       Paul Calnon
# Created:      2026-10-25
# Status:       ad-hoc — verification (juniper-ml#2062)
# Retire when:  RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:      juniper-ml#2062; util/ad-hoc/2026-10-25_servers_own_extras_ml2062.py (the fix);
#               util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py (the instrument, which
#               measured the defect on 2026-09-23)
#
# A DIFFERENTIAL check of juniper-ml#2062: the same wheel-contract probe, run in two clean venvs
# that differ only in what juniper-ml's [servers] installs.
#
#   control  juniper-ml[servers]==<published version>, from PyPI
#   fix      juniper-ml[servers] built from this checkout
#
# Both resolve the same server releases, so a check that SKIPs or FAILs in `control` and PASSes in
# `fix` is the extras change and nothing else. Each venv also gets CPU torch: cascor's modules import
# it, and [servers] deliberately does not carry it. The probe runs with LD_LIBRARY_PATH unset, because
# a foreign libtorch on that path makes the cascor checks SKIP on `undefined symbol` (juniper-ml#2062).
#
# The four checks that bear on #2062:
#   CP-1  canopy's backend imports, including backend.service_backend (needs juniper-cascor-client)
#   CC-2  cascor's spiral_problem.data_provider (needs juniper-data-client)
#   CC-3  the same module, a second contract
#   JD-8  juniper-data's service -> client roundtrip (needs data's [api] runtime and the data client)
#
# Usage:  bash util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash <workdir> [control-version]
#         PYTHON=python3.12 is the default interpreter (the version #2062 was measured on).
# ─────────────────────────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="${1:?usage: $0 <workdir> [control-version]}"
CONTROL_VERSION="${2:-0.11.1}"
PY="${PYTHON:-python3.12}"
PROBE="${REPO}/util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py"
CHECKS='(CP-1|CC-2|CC-3|JD-8) '

mkdir -p "${WORK}"

build_venv() {
    local name="$1"
    shift
    local venv="${WORK}/${name}"
    rm -rf "${venv}"
    "${PY}" -m venv "${venv}"
    "${venv}/bin/python" -m pip install --quiet --upgrade pip
    "${venv}/bin/python" -m pip install --quiet "$@"
    "${venv}/bin/python" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
}

build_venv control "juniper-ml[servers]==${CONTROL_VERSION}"
build_venv fix "${REPO}[servers]"

for name in control fix; do
    echo "== ${name}"
    "${WORK}/${name}/bin/python" -m pip freeze --all >"${WORK}/${name}.freeze.txt"
    awk 'BEGIN { IGNORECASE = 1 } /^(juniper-|fastapi==|starlette==|uvicorn==|pydantic-settings==|torch==)/ { print "   " $0 }' "${WORK}/${name}.freeze.txt"
    # The probe exits with its FAIL count; the per-check lines are the measurement, so keep going.
    (cd "${WORK}" && env -u LD_LIBRARY_PATH "${WORK}/${name}/bin/python" "${PROBE}" --json-out "${WORK}/${name}.json" >"${WORK}/${name}.probe.txt" 2>&1) || true
    awk -v pat="${CHECKS}" '$0 ~ "^ +\\[(PASS|FAIL|SKIP) *\\] " pat { print }' "${WORK}/${name}.probe.txt"
done
