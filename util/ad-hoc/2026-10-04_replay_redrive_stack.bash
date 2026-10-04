#!/usr/bin/env bash
# Throwaway data + cascor + canopy stack for the CAN-015 replay player's live re-drive
# (F-CANOPY-015 / -059 / -056 and canopy#697), then execs util/isolated_stack.bash.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-10-04
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    still-owed item 16 of notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md;
#             item 1 of prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md;
#             derived from util/ad-hoc/2026-09-23_a_n2_stack.bash
#
# WHY THIS EXISTS. Every replay drive replaces cascor's live network, so it must not run against
# the shared trio (8101 / 8202 / 8051, util/isolated_stack.bash's defaults). This wrapper hard-sets
# its own ports, refuses any default or other stack's port, refuses --up while one of its ports is
# taken, and refuses --down for any listener whose pid this run did not record.
#
# Unlike the A-N2 wrapper, the legs are NOT git worktrees: they are tarballs of each repo's
# origin/main extracted under JUNIPER_REDRIVE_ECO (a session scratchpad), because the session that
# wrote this could not run git against sibling repos. isolated_stack.bash then reports
# git_sha: null for cascor and canopy, which is honest; the commit each leg was extracted from is
# passed in as JUNIPER_REDRIVE_{DATA,CASCOR,CANOPY}_SHA and recorded by the driver.
#
# Usage:
#   JUNIPER_REDRIVE_ECO=<dir holding juniper-data/ juniper-cascor/ juniper-canopy/> \
#   JUNIPER_REDRIVE_DATA_SHA=<sha> bash util/ad-hoc/2026-10-04_replay_redrive_stack.bash --up|--status|--down [--dry-run]
set -euo pipefail

WRAPPER_NAME="$(basename "${BASH_SOURCE[0]}")"
ML_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.." && pwd)"
STACK_SCRIPT="${ML_ROOT}/util/isolated_stack.bash"
ECOSYSTEM_ROOT="/home/pcalnon/Development/python/Juniper"

refuse() {
    echo "[${WRAPPER_NAME}] REFUSING: $*" >&2
    exit 2
}

log() { echo "[${WRAPPER_NAME}] $*"; }

ECO="${JUNIPER_REDRIVE_ECO:-}"
[[ -n "${ECO}" ]] || refuse "JUNIPER_REDRIVE_ECO is empty"
ECO="$(realpath -e "${ECO}")" || refuse "JUNIPER_REDRIVE_ECO does not exist"
[[ "${ECO}" != "${ECOSYSTEM_ROOT}" && "${ECO}" != "${ECOSYSTEM_ROOT}/"* ]] || refuse "JUNIPER_REDRIVE_ECO is inside the real ecosystem root (the primaries)"
for leg in juniper-data juniper-cascor juniper-canopy; do
    [[ -d "${ECO}/${leg}" ]] || refuse "${ECO}/${leg} is missing"
done

# --- the overrides (hard-set: a caller's exported value must never move a leg onto a live port) ---
export JUNIPER_E2E_DATA_PORT=8113
export JUNIPER_E2E_CASCOR_PORT=8214
export JUNIPER_E2E_CANOPY_PORT=8063
export JUNIPER_E2E_RECURRENCE_PORT=8223
export JUNIPER_E2E_PROJECT_DIR="${ECO}"
export JUNIPER_E2E_RUN_DIR="${ECO}/run"
export JUNIPER_E2E_DATA_EXTRAS="api"
export JUNIPER_CASCOR_SNAPSHOTS_DIR="${JUNIPER_E2E_RUN_DIR}/cascor-snapshots"
export JUNIPER_E2E_CANOPY_SNAPSHOT_DIR="${JUNIPER_E2E_RUN_DIR}/cascor-snapshots"
export JUNIPER_DATA_GIT_SHA="${JUNIPER_REDRIVE_DATA_SHA:-}"
JUNIPER_DATA_BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export JUNIPER_DATA_BUILD_DATE

# isolated_stack.bash's defaults (the shared trio holds the first three), the operator stack, the
# A-N2 wrapper's ports, and the other canopy instances seen on this host.
FORBIDDEN_PORTS=(8101 8202 8051 8211 8100 8201 8050 8111 8212 8061 8221 8055 8056)
MY_PORTS=("${JUNIPER_E2E_DATA_PORT}" "${JUNIPER_E2E_CASCOR_PORT}" "${JUNIPER_E2E_CANOPY_PORT}" "${JUNIPER_E2E_RECURRENCE_PORT}")
for port in "${MY_PORTS[@]}"; do
    for bad in "${FORBIDDEN_PORTS[@]}"; do
        [[ "${port}" != "${bad}" ]] || refuse "port ${port} is a default / another stack's port"
    done
done

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
        --with-recurrence) refuse "--with-recurrence is not needed for the replay re-drive" ;;
        *) ;;
    esac
done
[[ -n "${action}" ]] || refuse "one of --up / --status / --down is required"

log "ports: data=${JUNIPER_E2E_DATA_PORT} cascor=${JUNIPER_E2E_CASCOR_PORT} canopy=${JUNIPER_E2E_CANOPY_PORT}"
log "eco: ${ECO} (data ${JUNIPER_DATA_GIT_SHA:-unknown}, cascor ${JUNIPER_REDRIVE_CASCOR_SHA:-unknown}, canopy ${JUNIPER_REDRIVE_CANOPY_SHA:-unknown})"
log "run dir: ${JUNIPER_E2E_RUN_DIR}"

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
            ours=0
            for m in "${mine[@]}"; do
                [[ "${pid}" == "${m}" ]] && ours=1
            done
            (( ours == 1 )) || refuse "--down: port ${port} is held by pid ${pid}, which this run did not record in ${JUNIPER_E2E_RUN_DIR}/*.pid"
        done
    fi
fi

exec bash "${STACK_SCRIPT}" "$@"
