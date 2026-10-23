#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- item 31 (F-CANOPY-028: a pin made just before a table rebuild is discarded)
# Author      : Paul Calnon
# Created     : 2026-10-20
# Status      : ad-hoc -- investigation
# Retire when : RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : util/ad-hoc/2026-10-20_item30_fixwave_redrive.py (``--step f028``; the ``delay<N>`` and ``forced`` arms);
#               util/ad-hoc/2026-10-20_turing_canopy_leg.bash and 2026-10-20_f069_fix_leg.bash (the legs);
#               util/ad-hoc/2026-10-20_f028_apply_fix.py (the tree the fix legs serve);
#               notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 14, item 31; Phase 15)
# License     : MIT License
# ---------------------------------------------------------------------------
# The item 31 drives, in order, one leg at a time (turing has 16 GiB):
#   1. the early-timing forced arm x6 on the PARENT leg (canopy main 571743db, dash 4.4.1, port 8062, already up);
#   2. that leg down; the F-CANOPY-028 fix tree up on port 8066 (dash 4.4.1);
#   3. on the fix: the early-timing forced arm x6, then ``early,mid`` x3 (item 31's own ask), then the delays 2..14 s x1;
#   4. the fix leg down.
# The early-timing forced arm was named ``forced`` when this pass ran (2026-10-20), so its records' arm labels read
# ``forced#N``; the driver now names it ``forcedearly`` and gives ``forced`` the settled timing (pass 2), and this
# script calls ``forcedearly`` so it reproduces what it recorded (ledger Phase 15, round 2, Lane 15-B's MINOR 12).
# Every run has its OWN --out (a later run overwrites a step's key in a shared record). Logs go next to the records.
#
# Usage:  bash util/ad-hoc/2026-10-20_item31_f028_drives.bash
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

echo "$(stamp) 1/4 parent, forcedearly x6 (port 8062)"
"$PY" -I "$DRIVER" --base http://127.0.0.1:8062 --step f028 --f028-arms forcedearly --f028-repeat 6 \
    --out "${OUT}/parent_8062_dash441_forced.json" > "${OUT}/logs/parent_8062_dash441_forced.log" 2>&1
echo "$(stamp)   exit $?"

echo "$(stamp) 2/4 parent leg down; fix leg up (port 8066)"
bash "$LEG" down 8062
bash "$FIXLEG" up 8066 "$PY" "$FIX_SRC" "+f069+f028-fix-unlanded" || { echo "fix leg did not come up"; exit 1; }

echo "$(stamp) 3/4 fix, forcedearly x6"
"$PY" -I "$DRIVER" --base http://127.0.0.1:8066 --step f028 --f028-arms forcedearly --f028-repeat 6 \
    --out "${OUT}/fix_8066_dash441_forced.json" > "${OUT}/logs/fix_8066_dash441_forced.log" 2>&1
echo "$(stamp)   exit $?"
echo "$(stamp) 3/4 fix, early,mid x3"
"$PY" -I "$DRIVER" --base http://127.0.0.1:8066 --step f028 --f028-arms early,mid --f028-repeat 3 \
    --out "${OUT}/fix_8066_dash441_early_mid.json" > "${OUT}/logs/fix_8066_dash441_early_mid.log" 2>&1
echo "$(stamp)   exit $?"
echo "$(stamp) 3/4 fix, fixed delays 2..14 s x1"
"$PY" -I "$DRIVER" --base http://127.0.0.1:8066 --step f028 --f028-arms delay2,delay4,delay6,delay8,delay10,delay12,delay14 --f028-repeat 1 \
    --out "${OUT}/fix_8066_dash441_delay_sweep.json" > "${OUT}/logs/fix_8066_dash441_delay_sweep.log" 2>&1
echo "$(stamp)   exit $?"

echo "$(stamp) 4/4 fix leg down"
bash "$FIXLEG" down 8066
echo "$(stamp) done"
