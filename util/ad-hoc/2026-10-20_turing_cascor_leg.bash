#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- item 30 (the Phase 4 fix wave's live re-drive)
# Author      : Paul Calnon
# Created     : 2026-10-20
# Status      : ad-hoc -- investigation
# Retire when : RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : util/ad-hoc/e2e_cascor_leg_restart.bash (the Linux-host recipe this mirrors);
#               util/ad-hoc/2026-10-20_turing_canopy_leg.bash (the canopy leg that points at this one)
# License     : MIT License
# ---------------------------------------------------------------------------
# Bring up ONE throwaway cascor on turing from the E2 tree: a WRITABLE cascor that item 30's
# Network Editor rows (F-CANOPY-012, -013) can restore into Investigating, and that the
# M-WORKERS-02 cascor-down arm (F-CANOPY-032) can STOP after canopy has attached to it
# (canopy falls back to demo mode when cascor is unreachable at ITS boot, main.py:439-447,
# so the order is cascor up, canopy up, cascor down). The trio is not on this host.
#
# No juniper-data: the data URL points at a closed port and every auto-start is off. The
# in-process spiral fallback on POST /v1/training/start is enough to grow a small network.
#
# Usage:
#   bash util/ad-hoc/2026-10-20_turing_cascor_leg.bash up   <port> <canopy-origin>
#   bash util/ad-hoc/2026-10-20_turing_cascor_leg.bash down <port>
# ---------------------------------------------------------------------------
set -euo pipefail

E2="${HOME}/.local/state/juniper/turing-e2"
SRC_DIR="${CASCOR_LEG_SRC:-${E2}/trees/juniper-cascor/src}"
VENV="${CASCOR_LEG_VENV:-${E2}/venvs/JuniperCascor1}"
RUN_DIR="${CASCOR_LEG_RUN_DIR:-${E2}/legs}"
ACTION="${1:-}"

case "$ACTION" in
up)
    PORT="${2:-}"
    CANOPY_ORIGIN="${3:-}"
    if [[ -z "$PORT" || -z "$CANOPY_ORIGIN" || ! -f "$SRC_DIR/api/app.py" ]]; then
        echo "usage: $0 up <port> <canopy-origin, e.g. http://127.0.0.1:8064>   (src: $SRC_DIR)" >&2
        exit 2
    fi
    mkdir -p "$RUN_DIR/cascor-snapshots-$PORT"
    LOG="$RUN_DIR/cascor-$PORT.log"
    PIDFILE="$RUN_DIR/cascor-$PORT.pid"
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "already up: pid $(cat "$PIDFILE") on port $PORT" >&2
        exit 0
    fi
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "port $PORT already has a listener -- refusing to double-start" >&2
        exit 1
    fi
    export JUNIPER_DATA_URL="http://127.0.0.1:9"
    export JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS="$CANOPY_ORIGIN"
    export JUNIPER_CASCOR_SNAPSHOTS_DIR="$RUN_DIR/cascor-snapshots-$PORT"
    export JUNIPER_CASCOR_AUTO_START=false
    export JUNIPER_CASCOR_AUTO_START_DATA_SERVICE=false
    export JUNIPER_CASCOR_AUTO_START_CANOPY=false
    export LIBTORCH=
    export LD_LIBRARY_PATH=
    unset PYTHONPATH
    cd "$SRC_DIR"
    nohup "$VENV/bin/uvicorn" api.app:create_app --factory --host 127.0.0.1 --port "$PORT" >"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
    echo "launched pid $(cat "$PIDFILE") on port $PORT (ws origin allowlist: $CANOPY_ORIGIN)"
    echo "  src : $SRC_DIR"
    echo "  log : $LOG"
    for _ in $(seq 1 120); do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:$PORT/v1/health" || true)
        if [[ "$code" == "200" ]]; then
            echo "healthy after $SECONDS s"
            curl -sS --max-time 3 "http://127.0.0.1:$PORT/v1/health" | head -c 600
            echo
            exit 0
        fi
        sleep 1
    done
    echo "did NOT become healthy within 120 s -- see $LOG" >&2
    exit 1
    ;;
down)
    PORT="${2:-}"
    PIDFILE="$RUN_DIR/cascor-$PORT.pid"
    if [[ -z "$PORT" || ! -f "$PIDFILE" ]]; then
        echo "no pid file at $PIDFILE -- nothing to stop" >&2
        exit 0
    fi
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        for _ in $(seq 1 20); do
            kill -0 "$PID" 2>/dev/null || break
            sleep 1
        done
        kill -0 "$PID" 2>/dev/null && kill -9 "$PID" || true
        echo "stopped pid $PID"
    else
        echo "pid $PID not running"
    fi
    rm -f "$PIDFILE"
    ;;
*)
    echo "usage: $0 {up <port> <canopy-origin> | down <port>}" >&2
    exit 2
    ;;
esac
