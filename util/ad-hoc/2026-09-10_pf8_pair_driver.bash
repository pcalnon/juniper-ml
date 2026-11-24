#!/usr/bin/env bash
# Run the PF-8 two-run concurrency PAIR: N parallel-arm suite runs (two identical PF-1-shape cells
# at once), then M control-arm runs (the same cell shape, sequential) under the SAME four thread
# variables, with the 1/5/15-minute load average logged around every launch.
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-09-10
# Status:      ad-hoc -- investigation (perf lane P2 item 4.2, step 2 of §1.3 of the 2026-09-08
#              re-scope note; run because the step-1 occupancy probe landed inside the ~4-8 band)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:     notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md
#
# WHY A DRIVER
#
# The pair is several launches with settle gaps, and the control arm must carry EXACTLY the
# budget run_suite pins for the parallel arm (thread_budget_env at max_parallel 2 on 16 cores:
# OMP/MKL/OPENBLAS 2, CASCOR_NUM_PROCESSES 4) or the arms differ in budget, not only in
# concurrency, and compare_baseline's thread_budget identity would rightly refuse the comparison.
# Exporting the four variables here makes both arms identical on that axis (run_suite's own export
# for the parallel arm carries the same values) and the driver's manifests record what each cell
# actually ran under. One script, one log, one launch to kill.
#
# The occupancy sampler (2026-09-10_pf8_occupancy_sampler.py) is started SEPARATELY, before this,
# and attaches to every run dir this creates.
#
# Usage:
#   bash util/ad-hoc/2026-09-10_pf8_pair_driver.bash
#   PF8_PARALLEL_REPEATS=3 PF8_CONTROL_REPEATS=1 PF8_SETTLE_SECONDS=15 bash util/ad-hoc/2026-09-10_pf8_pair_driver.bash
set -euo pipefail

ML_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export JUNIPER_EXP_PROJECT_DIR="${JUNIPER_EXP_PROJECT_DIR:-/home/pcalnon/Development/python/Juniper}"
RUN_ROOT="${JUNIPER_EXP_RUN_ROOT:-${HOME}/.local/state/juniper-experiments}"
PARALLEL_SUITE="${ML_DIR}/util/ad-hoc/2026-09-10_pf8_two_run_parallel_suite.yaml"
CONTROL_SUITE="${ML_DIR}/util/ad-hoc/2026-09-10_pf8_occupancy_probe_suite.yaml"
PARALLEL_REPEATS="${PF8_PARALLEL_REPEATS:-3}"
CONTROL_REPEATS="${PF8_CONTROL_REPEATS:-1}"
SETTLE="${PF8_SETTLE_SECONDS:-15}"
LOG="${PF8_LOG:-${RUN_ROOT}/suites/pf8-pair-driver-$(date -u +%Y%m%dT%H%M%SZ).log}"

# The H-11 budget run_suite pins for a cascor suite at max_parallel 2 on this 16-core host.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 CASCOR_NUM_PROCESSES=4

mkdir -p "$(dirname "${LOG}")"

log() {
    printf '%s %s   loadavg=%s\n' "$(date -u +%FT%TZ)" "$*" "$(cut -d' ' -f1-3 /proc/loadavg)" | tee -a "${LOG}"
}

run_suite() {
    # continue_on_failure is set in both suites; a non-zero exit here means a cell failed, which
    # the registry records. Log it and carry on so one bad cell does not lose the rest of the pair.
    if ! python3 "${ML_DIR}/util/experiments/run_suite.py" --suite "$1" 2>&1 | tee -a "${LOG}"; then
        log "run_suite exited non-zero for $1 (continuing; see registry.jsonl)"
    fi
}

log "pair driver start: parallel x${PARALLEL_REPEATS}, control x${CONTROL_REPEATS}, settle ${SETTLE}s, budget OMP/MKL/OPENBLAS=2 CASCOR_NUM_PROCESSES=4"
for i in $(seq 1 "${PARALLEL_REPEATS}"); do
    log "parallel arm run ${i}/${PARALLEL_REPEATS} start"
    run_suite "${PARALLEL_SUITE}"
    log "parallel arm run ${i}/${PARALLEL_REPEATS} done"
    sleep "${SETTLE}"
done
for i in $(seq 1 "${CONTROL_REPEATS}"); do
    log "control arm run ${i}/${CONTROL_REPEATS} start"
    run_suite "${CONTROL_SUITE}"
    log "control arm run ${i}/${CONTROL_REPEATS} done"
    sleep "${SETTLE}"
done
log "pair driver complete"
