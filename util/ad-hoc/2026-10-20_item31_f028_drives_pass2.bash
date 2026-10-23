#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- item 31 (F-CANOPY-028), second pass: the ``forced`` arm at the settled timing
# Author      : Paul Calnon
# Created     : 2026-10-20
# Status      : ad-hoc -- investigation
# Retire when : RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : util/ad-hoc/2026-10-20_item31_f028_drives.bash (pass 1: the forced arm at the EARLY timing, now
#               ``forcedearly``; it lost nothing on the parent, every click landing after the second render);
#               util/ad-hoc/2026-10-20_item30_fixwave_redrive.py (``forced`` pins at the settled timing). Neither
#               timing stages early#2's order: the renderer holds the render a params-store write requests behind
#               the click's writer, and early#2's stale render was requested before it (ledger Phase 15, round 2).
# License     : MIT License
# ---------------------------------------------------------------------------
# Pass 2, one leg at a time: the parent leg (canopy main 571743db, dash 4.4.1, port 8062) up, ``forced`` x6, down;
# the F-CANOPY-028 fix tree (port 8066) up, ``forced`` x6, down. Records and logs are named *_forced_settled so
# pass 1's *_forced records (the early timing) stay.
#
# Usage:  bash util/ad-hoc/2026-10-20_item31_f028_drives_pass2.bash
# ---------------------------------------------------------------------------
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"
E2="${HOME}/.local/state/juniper/turing-e2"
PY="${E2}/venvs/JuniperCanopy1-dash44/bin/python"
DRIVER="${HERE}/2026-10-20_item30_fixwave_redrive.py"
LEG="${HERE}/2026-10-20_turing_canopy_leg.bash"
FIXLEG="${HERE}/2026-10-20_f069_fix_leg.bash"
FIX_SRC="${E2}/trees/juniper-canopy-f028/src"
OUT="${ROOT}/reports/e2e-canopy-2026-09-02/item31-turing"
mkdir -p "${OUT}/logs"

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

echo "$(stamp) 1/2 parent leg up (port 8062); forced (settled timing) x6"
bash "$LEG" up 8062 demo http://127.0.0.1:9 "$PY" || { echo "parent leg did not come up"; exit 1; }
"$PY" -I "$DRIVER" --base http://127.0.0.1:8062 --step f028 --f028-arms forced --f028-repeat 6 \
    --out "${OUT}/parent_8062_dash441_forced_settled.json" > "${OUT}/logs/parent_8062_dash441_forced_settled.log" 2>&1
echo "$(stamp)   exit $?"
bash "$LEG" down 8062

echo "$(stamp) 2/2 fix leg up (port 8066); forced (settled timing) x6"
bash "$FIXLEG" up 8066 "$PY" "$FIX_SRC" "+f069+f028-fix-unlanded" || { echo "fix leg did not come up"; exit 1; }
"$PY" -I "$DRIVER" --base http://127.0.0.1:8066 --step f028 --f028-arms forced --f028-repeat 6 \
    --out "${OUT}/fix_8066_dash441_forced_settled.json" > "${OUT}/logs/fix_8066_dash441_forced_settled.log" 2>&1
echo "$(stamp)   exit $?"
bash "$FIXLEG" down 8066
echo "$(stamp) done"
