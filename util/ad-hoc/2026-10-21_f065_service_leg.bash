#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- item 20 (F-CANOPY-065: the WS leg's partition never reaches the toast)
# Author      : Paul Calnon
# Created     : 2026-10-21
# Status      : ad-hoc -- investigation
# Retire when : RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : util/ad-hoc/2026-10-20_turing_canopy_leg.bash (the launcher this wraps);
#               util/ad-hoc/2026-10-20_f069_fix_leg.bash (the demo-mode wrapper this mirrors);
#               util/ad-hoc/2026-10-20_turing_cascor_leg.bash (the cascor leg a service leg points at);
#               notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 10 item 20, F-CANOPY-065)
# License     : MIT License
# ---------------------------------------------------------------------------
# Bring up ONE service-mode canopy leg on turing from a given tree, pointed at a throwaway
# cascor leg, so an Apply's two legs (hot keys over /ws/control, cold keys over REST) reach a
# real cascor. The worktree guard refuses environment prefixes on a command line, so the
# variables the launcher reads are set here, as 2026-10-20_f069_fix_leg.bash does for demo legs.
#
# The /v1/health git_sha is stamped "<base sha><suffix>": a tree is NOT a commit, so a leg of an
# unlanded fix must never read as its base.
#
# Usage:
#   bash util/ad-hoc/2026-10-21_f065_service_leg.bash up   <port> <python> <tree-src> <cascor-url> <stamp-suffix> <base-sha>
#   bash util/ad-hoc/2026-10-21_f065_service_leg.bash down <port>
# ---------------------------------------------------------------------------
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="${HERE}/2026-10-20_turing_canopy_leg.bash"
ACTION="${1:-}"
PORT="${2:-}"

case "$ACTION" in
up)
    PY="${3:-}"
    SRC="${4:-}"
    CASCOR_URL="${5:-}"
    SUFFIX="${6:-}"
    BASE_SHA="${7:-}"
    if [[ -z "$PORT" || -z "$PY" || ! -x "$PY" || ! -f "$SRC/main.py" || ! "$CASCOR_URL" =~ ^http://127\.0\.0\.1:[0-9]+$ || ! "$BASE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
        echo "usage: $0 up <port> <python> <tree-src> <cascor-url (http://127.0.0.1:N)> <stamp-suffix> <base-sha, 40 hex>" >&2
        exit 2
    fi
    export CANOPY_LEG_SRC="$SRC"
    export CANOPY_LEG_GIT_SHA="${BASE_SHA}${SUFFIX}"
    exec bash "$LAUNCHER" up "$PORT" service "$CASCOR_URL" "$PY"
    ;;
down)
    exec bash "$LAUNCHER" down "$PORT"
    ;;
*)
    echo "usage: $0 {up <port> <python> <tree-src> <cascor-url> <stamp-suffix> <base-sha> | down <port>}" >&2
    exit 2
    ;;
esac
