#!/usr/bin/env bash
# A-N2 (item 18): run several driver cases in order, screenshotting canopy's dashboard right after each.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-23
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    util/ad-hoc/2026-09-23_a_n2_drive.py, util/ad-hoc/2026-09-23_a_n2_screenshot.py;
#             evidence in reports/2026-09-23_canopy-a-n2-generate-stage-train-render/
#
# The dashboard shows only the LATEST run, so each screenshot has to be taken before the next case
# starts; this keeps that ordering mechanical. A case whose driver run exits non-zero stops the batch.
#
# Usage: bash util/ad-hoc/2026-09-23_a_n2_run_batch.bash <timeout-seconds> <case> [<case> ...]
set -euo pipefail

HERE="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
DRIVE="${HERE}/2026-09-23_a_n2_drive.py"
SHOT="${HERE}/2026-09-23_a_n2_screenshot.py"
CANOPY_PY="/opt/miniforge3/envs/JuniperCanopy1/bin/python"

timeout_s="$1"
shift
for case_name in "$@"; do
    echo "=================== ${case_name} ==================="
    python3 "${DRIVE}" run "${case_name}" --timeout "${timeout_s}"
    LIBTORCH='' LD_LIBRARY_PATH='' "${CANOPY_PY}" "${SHOT}" "${case_name}" --settle 45 | tail -12
done
