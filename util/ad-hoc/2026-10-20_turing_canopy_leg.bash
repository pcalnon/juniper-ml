#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- item 30 (the Phase 4 fix wave's live re-drive)
# Author      : Paul Calnon
# Created     : 2026-10-20
# Status      : ad-hoc -- investigation
# Retire when : RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : util/ad-hoc/2026-09-04_canopy_verify_instance.bash (the Linux-host launcher this mirrors);
#               notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 13, item 30)
# License     : MIT License
# ---------------------------------------------------------------------------
# Bring up ONE canopy leg on turing (macOS) from the E2 tree, in demo or service mode.
#
# WHY A SEPARATE LAUNCHER. 2026-09-04_canopy_verify_instance.bash is written for the
# Linux host: it hardcodes /opt/miniforge3, a /home/... snapshot dir, and stamps the
# serving commit with `git -C`, which the worktree guard refuses here. turing's E2 tree
# (~/.local/state/juniper/turing-e2/trees/juniper-canopy) is an rsync of the primary
# checkout with .git excluded, so the serving commit is passed in explicitly
# (CANOPY_LEG_GIT_SHA) after 2026-10-20_e2_tree_blob_sha_check.py has proved the
# fix-touched files byte-identical to that commit. Everything else mirrors the Linux
# launcher's env, nested SERVER__ names included (plan §4.2 trap T-1).
#
# The trio is NOT on this host (nothing listens on 8101/8202/8051); every leg here is
# a throwaway. Demo legs point cascor and juniper-data at a closed port so no upstream
# is ever reached. Service legs take the cascor URL as an argument.
#
# Usage:
#   bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up   <port> demo
#   bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up   <port> service <cascor-url>
#   bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash down <port>
#
# Env (optional): CANOPY_LEG_SRC (default: the E2 tree's src), CANOPY_LEG_PY (default: the
# E2 venv's python, the one that has playwright), CANOPY_LEG_RUN_DIR (default:
# ~/.local/state/juniper/turing-e2/legs -- persistent, outside any reaper root),
# CANOPY_LEG_GIT_SHA (stamped onto /v1/health as git_sha).
# ---------------------------------------------------------------------------
set -euo pipefail

E2="${HOME}/.local/state/juniper/turing-e2"
SRC_DIR="${CANOPY_LEG_SRC:-${E2}/trees/juniper-canopy/src}"
PY="${CANOPY_LEG_PY:-${E2}/venvs/JuniperCanopy1/bin/python}"
RUN_DIR="${CANOPY_LEG_RUN_DIR:-${E2}/legs}"
ACTION="${1:-}"

case "$ACTION" in
up)
    PORT="${2:-}"
    MODE="${3:-}"
    CASCOR_URL="${4:-http://127.0.0.1:9}"
    # Optional 5th arg: the interpreter (a venv over the same tree with a different dash, say).
    PY="${5:-$PY}"
    if [[ -z "$PORT" || ! -f "$SRC_DIR/main.py" ]]; then
        echo "usage: $0 up <port> demo|service [cascor-url] [python]   (src: $SRC_DIR)" >&2
        exit 2
    fi
    case "$MODE" in
    demo) DEMO=1 ;;
    service) DEMO=0 ;;
    *) echo "mode must be demo or service" >&2; exit 2 ;;
    esac
    mkdir -p "$RUN_DIR/snapshots-$PORT"
    LOG="$RUN_DIR/canopy-$PORT.log"
    PIDFILE="$RUN_DIR/canopy-$PORT.pid"
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "already up: pid $(cat "$PIDFILE") on port $PORT" >&2
        exit 0
    fi
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "port $PORT already has a listener -- refusing to double-start" >&2
        exit 1
    fi

    export JUNIPER_CANOPY_SERVER__HOST=127.0.0.1
    export JUNIPER_CANOPY_SERVER__PORT="$PORT"
    export JUNIPER_CANOPY_CASCOR_SERVICE_URL="$CASCOR_URL"
    export JUNIPER_CANOPY_JUNIPER_DATA_URL="${CANOPY_LEG_DATA_URL:-http://127.0.0.1:9}"
    export JUNIPER_CANOPY_CASCOR_WS_ORIGIN="http://127.0.0.1:$PORT"
    export JUNIPER_CANOPY_WEBSOCKET__ALLOWED_ORIGINS="[\"http://127.0.0.1:$PORT\",\"http://localhost:$PORT\"]"
    export JUNIPER_CANOPY_DEMO_MODE="$DEMO"
    export JUNIPER_CANOPY_SNAPSHOT_DIR="$RUN_DIR/snapshots-$PORT"
    # The serving commit: CANOPY_LEG_GIT_SHA, else $RUN_DIR/serving-commit, which is written
    # only after 2026-10-20_e2_tree_blob_sha_check.py has printed ALL MATCH for that commit.
    if [[ -z "${CANOPY_LEG_GIT_SHA:-}" && -f "$RUN_DIR/serving-commit" ]]; then
        CANOPY_LEG_GIT_SHA="$(head -1 "$RUN_DIR/serving-commit")"
    fi
    export JUNIPER_CANOPY_GIT_SHA="${CANOPY_LEG_GIT_SHA:-}"
    BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    export JUNIPER_CANOPY_BUILD_DATE="$BUILD_DATE"
    export LIBTORCH=
    export LD_LIBRARY_PATH=
    unset PYTHONPATH

    cd "$SRC_DIR"
    nohup "$PY" main.py >"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
    printf '%s\n' "${JUNIPER_CANOPY_GIT_SHA:-<none>}" >"$RUN_DIR/canopy-$PORT.sha"
    echo "launched pid $(cat "$PIDFILE") on port $PORT (mode=$MODE cascor=$CASCOR_URL)"
    echo "  src : $SRC_DIR"
    echo "  py  : $PY (dash $("$PY" -c 'import dash; print(dash.__version__)' 2>/dev/null))"
    echo "  sha : ${JUNIPER_CANOPY_GIT_SHA:-<none>}"
    echo "  log : $LOG"
    for _ in $(seq 1 90); do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:$PORT/v1/health" || true)
        if [[ "$code" == "200" ]]; then
            echo "healthy after $SECONDS s"
            curl -sS --max-time 3 "http://127.0.0.1:$PORT/v1/health"
            echo
            exit 0
        fi
        sleep 1
    done
    echo "did NOT become healthy within 90 s -- see $LOG" >&2
    exit 1
    ;;
down)
    PORT="${2:-}"
    PIDFILE="$RUN_DIR/canopy-$PORT.pid"
    if [[ -z "$PORT" || ! -f "$PIDFILE" ]]; then
        echo "no pid file at $PIDFILE -- nothing to stop" >&2
        exit 0
    fi
    PID=$(cat "$PIDFILE")
    # Teardown BY PID, never by port.
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
    echo "usage: $0 {up <port> demo|service [cascor-url] | down <port>}" >&2
    exit 2
    ;;
esac
