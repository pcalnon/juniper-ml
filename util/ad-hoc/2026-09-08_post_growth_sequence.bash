#!/usr/bin/env bash
# Run the arc's COMPLETED-state instruments against one canopy leg, one at a time.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-08
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    canopy E2E arc, F-CANOPY-035/-038, M-DATASET-17..26, M-CANDIDATES-09..11;
#             notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
#
# WHY SEQUENTIAL. Every one of these opens its own headless browser against the same
# leg. Two at once share the fast lane and the renderer's slots, which is the very
# contention F-CANOPY-035 and F-CANOPY-038 are about -- a storm count or a store
# read taken beside another driver measures the pair, not the app. And all of them
# want the fixture COMPLETED with history rows, which the WebSocket-drop probe's
# `/resume` destroys (the monitor's metrics are cleared), so they run BEFORE it.
#
# Each step writes its own results file (the instrument's env var) and a log under
# ${RUN_DIR}; a step that exits non-zero is recorded and the sequence continues.
#
# Usage:
#   JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 bash util/ad-hoc/2026-09-08_post_growth_sequence.bash
set -uo pipefail

RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"
export JUNIPER_E2E_CANOPY_URL="${JUNIPER_E2E_CANOPY_URL:-http://127.0.0.1:8052}"
export LIBTORCH=
export LD_LIBRARY_PATH=
PY=/opt/miniforge3/envs/JuniperCanopy1/bin/python
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUMMARY="${RUN_DIR}/post_growth_sequence.txt"

run_step() {
    local name="$1"; shift
    local log="${RUN_DIR}/${name}.log"
    local t0=$SECONDS
    echo "=== ${name}  ($(date -u +%H:%M:%SZ)) ===" | tee -a "$SUMMARY"
    "$@" >"$log" 2>&1
    local rc=$?
    echo "    rc=${rc} in $((SECONDS - t0))s -> ${log}" | tee -a "$SUMMARY"
    grep -E '=> |VERDICT|verdicts|results ->' "$log" | grep -vE 'CONSOLE\[' | tail -12 | sed 's/^/    /' | tee -a "$SUMMARY"
}

mkdir -p "$RUN_DIR"
echo "post-growth sequence start $(date -u +%Y-%m-%dT%H:%M:%SZ) against ${JUNIPER_E2E_CANOPY_URL}" | tee -a "$SUMMARY"

# F-CANOPY-038: the one-command re-measure named in the ledger's still-owed list.
JUNIPER_E2E_SEG17_RESULTS="${RUN_DIR}/seg17_storestorm.json" \
    run_step storestorm "$PY" "${HERE}/e2e_seg17_topology_driver.py" --step storestorm

# M-DATASET-17..26: the sequence (3-D) controls, drivable now that the data leg carries [equities].
run_step dataset_seq "$PY" "${HERE}/e2e_seg16_dataset_driver.py" --step seq

# M-CANDIDATES-10/-11: the constructive fallback (a real card, then the click) on the calm page.
run_step cardsprobe "$PY" "${HERE}/e2e_f027_redrive.py" --step cardsprobe

# F-CANOPY-035, the symptom on THIS leg and fixture (writes on the wire vs the store).
F035_RESULTS="${RUN_DIR}/f035_redrive_2026-09-08.json" \
    run_step f035_redrive "$PY" "${HERE}/2026-09-04_f035_candidate_loss_redrive.py"

# F-CANOPY-035, the dispatch probe's positive control under the dict-aware rule.
F035_RENDERER_RESULTS="${RUN_DIR}/f035_renderer_CONTROL_topology-store_v2.json" \
    run_step dispatch_control "$PY" "${HERE}/2026-09-07_f035_renderer_dispatch_probe.py" --store network-visualizer-topology-store --tab "Network Topology" --window 60

# F-CANOPY-035, the lifecycle probe on its subject, for continuity with the 09-07 runs.
F035_LIFECYCLE_RESULTS="${RUN_DIR}/f035_lifecycle_subject_2026-09-08.json" \
    run_step lifecycle_subject "$PY" "${HERE}/2026-09-07_f035_callback_lifecycle_probe.py" --window 90

# F-CANOPY-035, the discriminating test, second replicate.
F035_SUPERSESSION_RESULTS="${RUN_DIR}/f035_supersession_run2.json" \
    run_step supersession_run2 "$PY" "${HERE}/2026-09-08_f035_supersession_test.py" --baseline 30 --settle 20 --watch 60

echo "post-growth sequence end $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$SUMMARY"
