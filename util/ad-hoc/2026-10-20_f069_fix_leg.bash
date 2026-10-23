#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- item 32 (F-CANOPY-069: dash 3.x renders canopy's dashboard inert)
# Author      : Paul Calnon
# Created     : 2026-10-20
# Status      : ad-hoc -- investigation
# Retire when : RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : util/ad-hoc/2026-10-20_turing_canopy_leg.bash (the launcher this wraps);
#               util/ad-hoc/2026-10-20_f069_apply_fix.py (builds the fix tree this serves);
#               notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 14, F-CANOPY-069)
# License     : MIT License
# ---------------------------------------------------------------------------
# Bring up ONE demo leg on turing from the F-CANOPY-069 FIX tree (a copy of the E2 tree at
# canopy main 571743db with 2026-10-20_f069_apply_fix.py applied), on the interpreter given,
# so the fix can be probed under a chosen dash. The worktree guard refuses environment
# prefixes on a command line, so the two variables the launcher reads are set here.
#
# The /v1/health git_sha is stamped "<serving commit>+f069-fix-unlanded": the tree is NOT a
# commit, and a leg of it must never read as 571743db.
#
# Usage:
#   bash util/ad-hoc/2026-10-20_f069_fix_leg.bash up   <port> <python> [fix-tree-src] [stamp-suffix] [base-sha]
#   bash util/ad-hoc/2026-10-20_f069_fix_leg.bash down <port>
# ---------------------------------------------------------------------------
set -euo pipefail

E2="${HOME}/.local/state/juniper/turing-e2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="${HERE}/2026-10-20_turing_canopy_leg.bash"
ACTION="${1:-}"
PORT="${2:-}"

case "$ACTION" in
up)
    PY="${3:-}"
    SRC="${4:-${E2}/trees/juniper-canopy-f069/src}"
    # Optional 5th arg: the stamp's suffix, e.g. "+f069+f028-fix-unlanded" for the item 31 tree.
    SUFFIX="${5:-+f069-fix-unlanded}"
    # Optional 6th arg: the base commit the stamp names (default: canopy main 571743db, the fix trees' parent).
    # A tree proved equal to a later canopy main passes that sha, so /v1/health names the code it serves
    # (ledger Phase 15, round 2: item 27's leg).
    BASE_SHA="${6:-571743dba37fa39ac70dbd94fa5822d0822d5e68}"
    if [[ -z "$PORT" || -z "$PY" || ! -x "$PY" || ! -f "$SRC/main.py" || ! "$BASE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
        echo "usage: $0 up <port> <python> [fix-tree-src] [stamp-suffix] [base-sha, 40 hex]   (src: $SRC)" >&2
        exit 2
    fi
    export CANOPY_LEG_SRC="$SRC"
    export CANOPY_LEG_GIT_SHA="${BASE_SHA}${SUFFIX}"
    exec bash "$LAUNCHER" up "$PORT" demo http://127.0.0.1:9 "$PY"
    ;;
down)
    exec bash "$LAUNCHER" down "$PORT"
    ;;
*)
    echo "usage: $0 {up <port> <python> [fix-tree-src] | down <port>}" >&2
    exit 2
    ;;
esac
