#!/usr/bin/env bash
# A-N2 (item 18) isolated-stack wrapper: pins ports / run dir / synthetic ecosystem root, then execs util/isolated_stack.bash.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-23
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    item 18 (A-N2) of prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_canopy-selection-six-prs-queued-live-swap-mirror-staged.md;
#             §12.4 of notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md;
#             evidence in reports/2026-09-23_canopy-a-n2-generate-stage-train-render/
#
# WHY THIS EXISTS. util/isolated_stack.bash DEFAULTS to 8101 / 8202 / 8051 (+8211 for recurrence),
# and on 2026-09-23 another session's isolated stack was live on exactly 8101 / 8202 / 8051. Its
# --down kills whatever listens on those ports, so a bare --down or --status from this session would
# have targeted THAT stack. This wrapper hard-sets every override, refuses (exit 2) if any is empty
# or names a port another stack uses, and adds two guards the underlying script does not have:
#
#   --up   refuses if any of this wrapper's four ports already has a listener. do_up tears a failed
#          bring-up down BY PORT, so a port someone else took in the meantime would be killed.
#   --down refuses if a listener on one of the four ports is not a pid this run recorded in
#          ${JUNIPER_E2E_RUN_DIR}/*.pid -- it never stops a process it did not start.
#
# The legs run from DETACHED worktrees at each repo's origin/main (never the primary checkouts,
# which the other stack imports), reached through a synthetic ecosystem root of symlinks, because
# isolated_stack.bash derives every leg's path from JUNIPER_E2E_PROJECT_DIR.
#
# Usage (only these; everything else is passed through verbatim):
#   bash util/ad-hoc/2026-09-23_a_n2_stack.bash --dry-run --up --with-recurrence
#   bash util/ad-hoc/2026-09-23_a_n2_stack.bash --up --with-recurrence
#   bash util/ad-hoc/2026-09-23_a_n2_stack.bash --status
#   bash util/ad-hoc/2026-09-23_a_n2_stack.bash --down
set -euo pipefail

WRAPPER_NAME="$(basename "${BASH_SOURCE[0]}")"
ML_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
STACK_SCRIPT="${ML_ROOT}/util/isolated_stack.bash"

ECOSYSTEM_ROOT="/home/pcalnon/Development/python/Juniper"
WORKTREES_ROOT="${ECOSYSTEM_ROOT}/worktrees"
SCRATCH="/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/317c1df2-5970-4312-96f5-ab61df517bb2/scratchpad"

# --- the overrides (hard-set: a caller's exported value must never move a leg onto a live port) ---
export JUNIPER_E2E_DATA_PORT=8111
export JUNIPER_E2E_CASCOR_PORT=8212
export JUNIPER_E2E_CANOPY_PORT=8061
export JUNIPER_E2E_RECURRENCE_PORT=8221
export JUNIPER_E2E_RUN_DIR="${SCRATCH}/a-n2-run"
export JUNIPER_E2E_PROJECT_DIR="${SCRATCH}/a-n2-eco"
# juniper-data pyproject.toml [project.optional-dependencies]: api (uvicorn + service tier),
# mnist (datasets[vision]), equities (yfinance + pandas). equities is what the `equities` seed needs.
export JUNIPER_E2E_DATA_EXTRAS="api,mnist,equities"
# Snapshots: cascor's train_output_layer writes an .h5 on every output pass. Unset, a linked
# worktree gets its own <worktree>/cascor-snapshots; point cascor AND canopy at the run dir instead
# so nothing lands in a checkout and canopy lists what cascor wrote.
export JUNIPER_CASCOR_SNAPSHOTS_DIR="${JUNIPER_E2E_RUN_DIR}/cascor-snapshots"
export JUNIPER_E2E_CANOPY_SNAPSHOT_DIR="${JUNIPER_E2E_RUN_DIR}/cascor-snapshots"

# Ports that are NEVER acceptable: isolated_stack.bash's own defaults (8101/8202/8051/8211 -- the
# other session's stack holds the first three), the operator stack (8100/8201/8050), and the two
# other canopy instances seen listening at 2026-09-23T19:14Z (8055/8056).
FORBIDDEN_PORTS=(8101 8202 8051 8211 8100 8201 8050 8055 8056)
# The other session's stack, recorded 2026-09-23T19:14Z. Never a target.
PROTECTED_PIDS=(2856834 2857489 2858037)

refuse() {
    echo "[${WRAPPER_NAME}] REFUSING: $*" >&2
    exit 2
}

log() { echo "[${WRAPPER_NAME}] $*"; }

# --- validation of the overrides ---
for var in JUNIPER_E2E_DATA_PORT JUNIPER_E2E_CASCOR_PORT JUNIPER_E2E_CANOPY_PORT JUNIPER_E2E_RECURRENCE_PORT; do
    value="${!var:-}"
    [[ -n "${value}" ]] || refuse "${var} is empty"
    [[ "${value}" =~ ^[0-9]+$ ]] || refuse "${var}='${value}' is not a port number"
    for bad in "${FORBIDDEN_PORTS[@]}"; do
        [[ "${value}" != "${bad}" ]] || refuse "${var}=${value} is a default / another stack's port"
    done
done
for var in JUNIPER_E2E_RUN_DIR JUNIPER_E2E_PROJECT_DIR JUNIPER_E2E_DATA_EXTRAS JUNIPER_CASCOR_SNAPSHOTS_DIR JUNIPER_E2E_CANOPY_SNAPSHOT_DIR; do
    [[ -n "${!var:-}" ]] || refuse "${var} is empty"
done
[[ "$(realpath -m "${JUNIPER_E2E_PROJECT_DIR}")" != "${ECOSYSTEM_ROOT}" ]] || refuse "JUNIPER_E2E_PROJECT_DIR is the real ecosystem root (the primaries)"
for leg in juniper-data juniper-cascor juniper-canopy; do
    target="$(realpath -e "${JUNIPER_E2E_PROJECT_DIR}/${leg}" 2>/dev/null || true)"
    [[ -n "${target}" ]] || refuse "${JUNIPER_E2E_PROJECT_DIR}/${leg} does not resolve"
    [[ "${target}" == "${WORKTREES_ROOT}/"* ]] || refuse "${leg} resolves to ${target}, which is not under ${WORKTREES_ROOT} (a primary checkout?)"
done
[[ -x "${STACK_SCRIPT}" || -f "${STACK_SCRIPT}" ]] || refuse "stack script not found at ${STACK_SCRIPT}"

# Data-leg provenance: isolated_stack.bash stamps cascor/canopy but not juniper-data, whose /v1/health
# reads JUNIPER_DATA_GIT_SHA. Stamp it from the worktree the data venv installs (-e) from. It is a
# stamp, not a proof: the driver separately records the venv's juniper_data.__file__.
JUNIPER_DATA_GIT_SHA="$(git -C "${JUNIPER_E2E_PROJECT_DIR}/juniper-data" rev-parse HEAD)"
JUNIPER_DATA_BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export JUNIPER_DATA_GIT_SHA JUNIPER_DATA_BUILD_DATE

MY_PORTS=("${JUNIPER_E2E_DATA_PORT}" "${JUNIPER_E2E_CASCOR_PORT}" "${JUNIPER_E2E_CANOPY_PORT}" "${JUNIPER_E2E_RECURRENCE_PORT}")

listener_pid() {
    ss -tlnpH "sport = :$1" 2>/dev/null | grep -oE 'pid=[0-9]+' | head -n1 | cut -d= -f2 || true
}

listener_any() {
    [[ -n "$(ss -tlnH "sport = :$1" 2>/dev/null)" ]]
}

recorded_pids() {
    local f
    for f in "${JUNIPER_E2E_RUN_DIR}"/*.pid; do
        [[ -f "${f}" ]] && tr -d '[:space:]' <"${f}" && echo
    done
}

is_dry=0
action=""
for arg in "$@"; do
    case "${arg}" in
        --dry-run) is_dry=1 ;;
        --up) action="up" ;;
        --down) action="down" ;;
        --status) action="status" ;;
        *) ;;
    esac
done

log "ports: data=${JUNIPER_E2E_DATA_PORT} cascor=${JUNIPER_E2E_CASCOR_PORT} canopy=${JUNIPER_E2E_CANOPY_PORT} recurrence=${JUNIPER_E2E_RECURRENCE_PORT}"
log "run dir: ${JUNIPER_E2E_RUN_DIR}"
log "project dir: ${JUNIPER_E2E_PROJECT_DIR}"
for leg in juniper-data juniper-cascor juniper-canopy; do
    log "  ${leg} -> $(realpath -e "${JUNIPER_E2E_PROJECT_DIR}/${leg}") @ $(git -C "${JUNIPER_E2E_PROJECT_DIR}/${leg}" rev-parse HEAD)"
done
log "data extras: ${JUNIPER_E2E_DATA_EXTRAS}"
log "snapshots: cascor=${JUNIPER_CASCOR_SNAPSHOTS_DIR} canopy=${JUNIPER_E2E_CANOPY_SNAPSHOT_DIR}"

if (( is_dry == 0 )); then
    if [[ "${action}" == "up" ]]; then
        for port in "${MY_PORTS[@]}"; do
            if listener_any "${port}"; then
                refuse "--up: port ${port} already has a listener (pid $(listener_pid "${port}")); a failed bring-up would kill it by port"
            fi
        done
        mkdir -p "${JUNIPER_CASCOR_SNAPSHOTS_DIR}"
    elif [[ "${action}" == "down" ]]; then
        mapfile -t mine < <(recorded_pids)
        for port in "${MY_PORTS[@]}"; do
            pid="$(listener_pid "${port}")"
            if [[ -z "${pid}" ]]; then
                if listener_any "${port}"; then
                    refuse "--down: port ${port} has a listener whose pid is not visible to this user; not ours"
                fi
                continue
            fi
            for protected in "${PROTECTED_PIDS[@]}"; do
                [[ "${pid}" != "${protected}" ]] || refuse "--down: port ${port} is held by protected pid ${pid}"
            done
            ours=0
            for m in "${mine[@]}"; do
                [[ "${pid}" == "${m}" ]] && ours=1
            done
            (( ours == 1 )) || refuse "--down: port ${port} is held by pid ${pid}, which this run did not record in ${JUNIPER_E2E_RUN_DIR}/*.pid"
        done
    fi
fi

exec bash "${STACK_SCRIPT}" "$@"
