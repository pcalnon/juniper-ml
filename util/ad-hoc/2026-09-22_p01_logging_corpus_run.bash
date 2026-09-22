#!/usr/bin/env bash
# P0.1 -- the post-merge worker-profile corpus for the logging arc (cascor#573).
#
# Project:     juniper-ml
# Sub-Project: ad-hoc tooling
# Author:      Paul Calnon
# Created:     2026-09-22
# Status:      ad-hoc -- one-off (ROADMAP P0.1, which gates P2 and P3)
# Related:     util/ad-hoc/2026-08-26_census_post588_run.bash  (the two-leg census this is cut down from)
#              util/ad-hoc/2026-08-14_r5_stack_up.bash          (data stack up; prints RUN_ID + DATA_URL)
#              util/ad-hoc/2026-08-17_h2h_thread_probe.bash     (drives one CLI cell)
#              util/ad-hoc/2026-08-29_format_caller_attribution.py (P0.2 reads what this writes)
#
# WHY THIS EXISTS RATHER THAN RE-RUNNING THE 08-26 CENSUS
# That script runs TWO legs. Leg 1 arms cascor#570's import auditor and pre-flights on
# `cascor_diag_import_audit.py` plus a Sentry DSN by value -- both of which live only on the
# abandoned `diag/census-at67d7ea35-0339` worktree, so on merged `main` it exits 2 before doing any
# work. P0.1 needs only leg 2, the `JUNIPER_CASCOR_WORKER_PROFILE` leg. This is that leg alone.
#
# WHAT P0.1 ASKS FOR (ROADMAP section 3):
#   (a) run the 32-profile cap-4 cell on merged main with JUNIPER_CASCOR_WORKER_PROFILE
#   (b) archive under juniper-ml/reports/
#   (c) record the CELL IDENTITY -- suite path, max_hidden_units, dataset seed, experiment seed,
#       base config, arm
# (c) is why provenance.json below copies the cell verbatim rather than naming it: the 08-26
# corpus recorded only a PATH, and that path points into ~/.local/state, which is not version
# controlled and whose suite dir can be reaped. A path is not an identity.
#
# HAZARDS RESPECTED
#   * Teardown is BY OUR OWN RUN_ID, never --all-mine (a shared run root; other sessions run here).
#   * The orphan reaper (util/reap_pytest_orphans.bash) treats reparenting to `systemd --user` as
#     the orphan predicate, and this stack launches under nohup. Protection is automatic here --
#     experiment_stack.bash writes run-dir pidfiles and the cmdlines reference the run root -- but
#     do NOT run the reaper against this while it is live.
#   * CASCOR_SRC must be a WORKTREE, not the shared juniper-cascor checkout, which other sessions
#     move between branches mid-run. Pinning is the whole point.
#
# Usage: 2026-09-22_p01_logging_corpus_run.bash <CASCOR_SRC> <CELL_YAML> <OUT_ROOT> [BOUND_SECONDS]
# Terminal markers: `p01: done ->` on completion; `p01: FAIL` on any pre-flight failure.
# Exit: 0 the leg was attempted and the stack torn down; 2 pre-flight failure.
set -uo pipefail

CASCOR_SRC="${1:?usage: $0 <CASCOR_SRC> <CELL_YAML> <OUT_ROOT> [BOUND_SECONDS]}"
CELL="${2:?usage: see header}"
OUT_ROOT="${3:?usage: see header}"
BOUND="${4:-360}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ML_ROOT="$(cd "${HERE}/../.." && pwd)"

[[ -d "${CASCOR_SRC}" ]] || { echo "p01: FAIL cascor src not found: ${CASCOR_SRC}"; exit 2; }
[[ -f "${CELL}" ]] || { echo "p01: FAIL cell not found: ${CELL}"; exit 2; }
[[ -e "${OUT_ROOT}/cli-01" ]] && { echo "p01: FAIL ${OUT_ROOT}/cli-01 exists -- a NEW OUT_ROOT every time, or the trainer log doubles every count"; exit 2; }

# The whole point of P0.1 is that the corpus postdates the Phase 1 merges. Refuse to produce one
# that does not, rather than archiving a corpus that silently answers the wrong question.
if ! git -C "${CASCOR_SRC}" merge-base --is-ancestor 8065ca0 HEAD 2>/dev/null; then
    echo "p01: FAIL ${CASCOR_SRC} does not contain 8065ca0 (P1.4, cascor#670)."
    echo "p01:      A corpus taken before the Phase 1 merges cannot measure the post-merge share."
    exit 2
fi

mkdir -p "${OUT_ROOT}/prof" || { echo "p01: FAIL cannot create ${OUT_ROOT}"; exit 2; }

SHA="$(git -C "${CASCOR_SRC}" rev-parse HEAD)"
echo "p01: cascor ${SHA} | cell ${CELL} | out=${OUT_ROOT} | bound=${BOUND}s"

# --- provenance, written BEFORE the run so a crash still leaves the identity ---------------------
{
    printf '{\n'
    printf '  "step": "P0.1",\n'
    printf '  "arc": "cascor#573 logging redesign",\n'
    printf '  "arm": "direct CLI (forked workers), single leg, worker cProfile armed",\n'
    printf '  "cascor_sha": "%s",\n' "${SHA}"
    printf '  "cascor_src": "%s",\n' "${CASCOR_SRC}"
    printf '  "cell_path": "%s",\n' "${CELL}"
    printf '  "bound_seconds": %s,\n' "${BOUND}"
    printf '  "started_utc": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '  "phase1_prs": ["644", "647", "648", "652", "653", "667", "670"],\n'
    printf '  "cell_verbatim": '
    python3 -c 'import json,sys; print(json.dumps(open(sys.argv[1]).read()))' "${CELL}"
    printf '\n}\n'
} >"${OUT_ROOT}/provenance.json"
cp "${CELL}" "${OUT_ROOT}/cell.yaml"

# --- one throwaway data stack --------------------------------------------------------------------
stack_out="$(bash "${HERE}/2026-08-14_r5_stack_up.bash" 2>"${OUT_ROOT}/stack_up.log")" || {
    echo "p01: FAIL stack bring-up failed; see ${OUT_ROOT}/stack_up.log"
    exit 2
}
RUN_ID="$(sed -n 's/^RUN_ID=//p' <<<"${stack_out}")"
DATA_URL="$(sed -n 's/^DATA_URL=//p' <<<"${stack_out}")"
[[ -n "${RUN_ID}" && -n "${DATA_URL}" ]] || { echo "p01: FAIL could not parse RUN_ID/DATA_URL from: ${stack_out}"; exit 2; }
echo "${RUN_ID}" >"${OUT_ROOT}/stack_run_id"
echo "p01: stack ${RUN_ID} DATA_URL=${DATA_URL}"

# --- the one leg: worker cProfile ------------------------------------------------------------------
echo "p01: leg (worker profile) -> ${OUT_ROOT}/cli-01  load1=$(cut -d' ' -f1 /proc/loadavg)"
env -u JUNIPER_DIAG_IMPORT_LOG JUNIPER_CASCOR_WORKER_PROFILE="${OUT_ROOT}/prof" \
    bash "${HERE}/2026-08-17_h2h_thread_probe.bash" "${CASCOR_SRC}" "${CELL}" "${OUT_ROOT}/cli-01" "${DATA_URL}" "${BOUND}" default
rc=$?
echo "p01: leg rc=${rc}"

# --- teardown by our OWN run id --------------------------------------------------------------------
bash "${ML_ROOT}/util/experiment_stack.bash" --down "${RUN_ID}" >"${OUT_ROOT}/stack_down.log" 2>&1
echo "p01: stack ${RUN_ID} down rc=$?"

# --- controls, PRINTED not judged -------------------------------------------------------------------
n_prof=$(find "${OUT_ROOT}/prof" -name '*.prof' 2>/dev/null | wc -l)
echo "p01: control 1 (profiles): ${n_prof} .prof in ${OUT_ROOT}/prof  (expect 32 = 4 rounds x 8 candidates at cap 4/pool 8)"
if [[ "${n_prof}" -eq 0 ]]; then
    echo "p01:   ZERO profiles is a HOLLOW result, not a measurement -- JUNIPER_CASCOR_WORKER_PROFILE"
    echo "p01:   must reach the FORKSERVER PARENT's environment, and cascor#567 is inert without it."
fi
n_log=$(cat "${OUT_ROOT}"/cli-01/logs/juniper_cascor.log* 2>/dev/null | wc -l)
echo "p01: control 2 (trainer log lines): ${n_log}  (zero here means the run never trained)"
echo "p01: control 3 (unique worker pids in profile names): $(find "${OUT_ROOT}/prof" -name '*.prof' -printf '%f\n' 2>/dev/null | cut -d- -f2 | sort -u | wc -l)"
echo "p01: done -> ${OUT_ROOT}"
