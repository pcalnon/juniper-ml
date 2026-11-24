#!/usr/bin/env bash
# Swap the isolated stack's cascor leg for one launched from a worktree, by pid.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-08
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    canopy E2E arc; F-CASCOR-003 (resume-from-snapshot seed TypeError);
#             notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
#
# WHY THIS EXISTS. `util/isolated_stack.bash` brings the trio up from the PRIMARY
# checkouts and tears all three down together. Verifying a cascor fix live means
# running cascor from a worktree while data (:8101) and canopy (:8051/:8052) stay
# up -- and the stack's own `--down` must still find the leg afterwards, so the
# new pid goes into the SAME pid file (`${RUN_DIR}/juniper-cascor.pid`), which is
# also what keeps it inside the orphan reaper's protected root.
#
# THE FIXTURE DOES NOT SURVIVE THIS. cascor's network lives in the process; a swap
# is a restart. Re-resume it from its snapshot afterwards:
#     POST /v1/snapshots/<id>/resume ; POST /v1/training/dataset {...} ; PATCH /v1/training/params
#
# CONTROL-WS ALLOWLIST. The stack launches cascor admitting only the :8051 canopy
# origin, which is why every verify leg on :8052 ran with its control stream down
# (2026-09-08). Pass every canopy origin that will talk to this leg in
# CASCOR_WS_ORIGINS (comma-separated; the settings validator splits on commas).
#
# SERVING COMMIT. cascor's /v1/health reports `git_sha` from JUNIPER_CASCOR_GIT_SHA
# when stamped; this script stamps it from the worktree it launches, and also
# writes `${RUN_DIR}/cascor-<port>.sha`, for the same reason the canopy verify
# leg does ("a checkout is not a deployment").
#
# Usage:
#   2026-09-08_cascor_leg_swap.bash up   <worktree-src-dir containing api/> [port]
#   2026-09-08_cascor_leg_swap.bash down [port]
#
set -euo pipefail

ACTION="${1:-}"
RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"
LOG_DIR="${RUN_DIR}/logs"
PIDFILE="${RUN_DIR}/juniper-cascor.pid"
DATA_PORT="${JUNIPER_E2E_DATA_PORT:-8101}"
CONDA_PY="${JUNIPER_E2E_CASCOR_PYTHON:-/opt/miniforge3/envs/JuniperCascor1/bin/python}"

stop_by_pidfile() {
    if [[ ! -f "$PIDFILE" ]]; then
        echo "no pid file at $PIDFILE — nothing to stop" >&2
        return 0
    fi
    local pid
    pid="$(cat "$PIDFILE")"
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        for _ in $(seq 1 30); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 1
        done
        kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true
        echo "stopped cascor pid $pid"
    else
        echo "pid $pid not running"
    fi
    rm -f "$PIDFILE"
}

case "$ACTION" in
up)
    SRC_DIR="${2:-}"
    PORT="${3:-${JUNIPER_E2E_CASCOR_PORT:-8202}}"
    if [[ -z "$SRC_DIR" || ! -d "$SRC_DIR/api" ]]; then
        echo "usage: $0 up <worktree-src-dir containing api/> [port]" >&2
        exit 2
    fi
    mkdir -p "$LOG_DIR"
    stop_by_pidfile
    # The port must actually be free before we launch onto it.
    for _ in $(seq 1 20); do
        if ! ss -ltn 2>/dev/null | grep -qE "127\.0\.0\.1:${PORT}\b"; then break; fi
        sleep 1
    done

    SHA="$(git -C "$SRC_DIR" rev-parse HEAD 2>/dev/null || true)"
    ORIGINS="${CASCOR_WS_ORIGINS:-http://127.0.0.1:8051}"
    LOG="${LOG_DIR}/juniper-cascor.log"
    SHAFILE="${RUN_DIR}/cascor-${PORT}.sha"
    # SNAPSHOT ROOT. cascor resolves its default root RELATIVE TO ITS OWN TREE
    # (`manager.py:5065`: `<repo>/cascor-snapshots`), so a worktree-run leg looks in
    # `<worktree>/cascor-snapshots`, which does not exist, lists zero snapshots, and
    # 404s every resume. The arc's snapshots live under the PRIMARY checkout (the
    # storage-convention root shared by CLI, service and container); point the
    # leg there unless told otherwise.
    SNAPSHOTS_DIR="${JUNIPER_CASCOR_SNAPSHOTS_DIR:-/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots}"

    (
        cd "$SRC_DIR"
        LD_LIBRARY_PATH='' \
            JUNIPER_DATA_URL="http://127.0.0.1:${DATA_PORT}" \
            JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS="${ORIGINS}" \
            JUNIPER_CASCOR_SNAPSHOTS_DIR="${SNAPSHOTS_DIR}" \
            JUNIPER_CASCOR_GIT_SHA="${SHA}" \
            JUNIPER_CASCOR_BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            nohup "$CONDA_PY" -m uvicorn api.app:create_app --factory --host 127.0.0.1 --port "$PORT" >>"$LOG" 2>&1 &
        echo "$!" >"$PIDFILE"
    )
    printf '%s\n' "${SHA:-<none>}" >"$SHAFILE"
    echo "launched cascor pid $(cat "$PIDFILE") on port $PORT"
    echo "  src     : $SRC_DIR"
    echo "  sha     : ${SHA:-<none>}  (also in $SHAFILE)"
    echo "  origins : $ORIGINS"
    echo "  snaps   : $SNAPSHOTS_DIR"
    echo "  log     : $LOG (appended)"
    echo "  pid     : $PIDFILE"
    for _ in $(seq 1 90); do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:$PORT/v1/health" || true)
        if [[ "$code" == "200" ]]; then
            echo "healthy after $SECONDS s"
            exit 0
        fi
        sleep 1
    done
    echo "did NOT become healthy within 90 s — see $LOG" >&2
    exit 1
    ;;
down)
    stop_by_pidfile
    ;;
*)
    echo "usage: $0 {up <worktree-src-dir> [port] | down [port]}" >&2
    exit 2
    ;;
esac
