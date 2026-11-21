#!/usr/bin/env bash
# Reproduce cascor's silent WebSocket drop, swap the leg onto the fixed loader, prove the
# drop is gone, then grow the fixture one more window with the relay alive.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-08
# Status:     ad-hoc — investigation
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    F-CASCOR-003 / F-CASCOR-004 / F-CANOPY-049 / F-CANOPY-036 / F-CANOPY-026 / M-TOPOLOGY-16;
#             juniper-cascor#632; notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
#
# ORDER IS THE POINT. (A) the raw-client drop probe against the leg as it runs NOW -- the
# first #632 commit only, so the config tunables are still NumPy scalars in memory and the
# first state broadcast should fail to serialise and drop us. (B) swap the leg onto the
# worktree with the extended fix, `resume` the 48-unit snapshot so the leg holds a network,
# then the SAME probe: the drop should be gone. (C) with the relays reconnected to the new
# process (the TCP reset makes their recv() raise, so they reconnect on their own), stage the
# dataset, raise the cap to 52 and watch the growth from three tabs -- the run that can
# finally verify F-036 (cards), F-026 (mid-run pairs) and M-TOPOLOGY-16 (glow). (D) snapshot.
#
# Usage:
#   bash util/ad-hoc/2026-09-08_relay_repair_sequence.bash
set -uo pipefail

RUN_DIR="${JUNIPER_E2E_RUN_DIR:-${TMPDIR:-/tmp}/juniper-e2e}"
export JUNIPER_E2E_CANOPY_URL="${JUNIPER_E2E_CANOPY_URL:-http://127.0.0.1:8052}"
export LIBTORCH=
export LD_LIBRARY_PATH=
PY=/opt/miniforge3/envs/JuniperCanopy1/bin/python
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASCOR=http://127.0.0.1:8202
SNAP="${FIXTURE_SNAPSHOT:-snapshot_20260908T123427Z}"
FIX_SRC="${CASCOR_FIX_SRC:-/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--snapshot-restore-seed-numpy-scalar--20260908-0725--d39d5370/src}"
SUMMARY="${RUN_DIR}/relay_repair_sequence.txt"

say() { echo "$*" | tee -a "$SUMMARY"; }
cascor_state() { curl -s --max-time 8 "$CASCOR/v1/training/status" | "$PY" -c 'import sys,json; d=json.load(sys.stdin)["data"]; print(d["state_machine"]["status"], "hidden", d["monitor"]["current_hidden_units"], "epoch", d["training_state"]["current_epoch"], "metrics", d["monitor"]["total_metrics"])' 2>/dev/null; }
ws_summary() { grep 'WS emission summary' "${RUN_DIR}/logs/juniper-cascor.log" | tail -1 | cut -c1-140; }

mkdir -p "$RUN_DIR"
say "relay repair sequence start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "cascor before: $(cascor_state)"

say "=== (A) drop probe against the running leg (first #632 commit only) ==="
WS_DROP_RESULTS="${RUN_DIR}/ws_drop_A.json" "$PY" "${HERE}/2026-09-08_cascor_ws_drop_probe.py" --snapshot "$SNAP" >"${RUN_DIR}/ws_drop_A.log" 2>&1
say "    rc=$? $(grep -E '=> VERDICT' "${RUN_DIR}/ws_drop_A.log" | tail -1)"
say "    cascor: $(cascor_state)   $(ws_summary)"

say "=== (B) swap the cascor leg onto the extended fix, resume, probe again ==="
JUNIPER_CASCOR_SNAPSHOTS_DIR=/home/pcalnon/Development/python/Juniper/juniper-cascor/cascor-snapshots \
CASCOR_WS_ORIGINS="http://127.0.0.1:8051,http://127.0.0.1:8052" \
    bash "${HERE}/2026-09-08_cascor_leg_swap.bash" up "$FIX_SRC" 8202 >"${RUN_DIR}/leg_swap_B.log" 2>&1
say "    swap rc=$? $(grep -E 'healthy|sha' "${RUN_DIR}/leg_swap_B.log" | tr '\n' ' ' | cut -c1-200)"
sleep 25   # let both canopy relays reconnect and be promoted (5 s resume handshake)
curl -s --max-time 60 -X POST "$CASCOR/v1/snapshots/$SNAP/resume" | cut -c1-160 | tee -a "$SUMMARY"; echo | tee -a "$SUMMARY"
sleep 8
say "    cascor after resume: $(cascor_state)   $(ws_summary)"
WS_DROP_RESULTS="${RUN_DIR}/ws_drop_B.json" "$PY" "${HERE}/2026-09-08_cascor_ws_drop_probe.py" --snapshot "$SNAP" >"${RUN_DIR}/ws_drop_B.log" 2>&1
say "    rc=$? $(grep -E '=> VERDICT' "${RUN_DIR}/ws_drop_B.log" | tail -1)"
say "    cascor: $(cascor_state)   $(ws_summary)"

say "=== (C) grow 48 -> 52 with the relay alive, three tabs open ==="
curl -s --max-time 30 -X POST -H 'Content-Type: application/json' -d '{"dataset_type":"spirals","n_samples":1000,"noise":0.25,"rotations":1.5,"n_spirals":2}' "$CASCOR/v1/training/dataset" | cut -c1-120 | tee -a "$SUMMARY"; echo | tee -a "$SUMMARY"
curl -s --max-time 10 -X PATCH -H 'Content-Type: application/json' -d '{"max_hidden_units": 52, "candidate_patience": 2000}' "$CASCOR/v1/training/params" | cut -c1-120 | tee -a "$SUMMARY"; echo | tee -a "$SUMMARY"
say "    cascor before start: $(cascor_state)"
LIVE_RUN_RESULTS="${RUN_DIR}/live_run_52.json" JUNIPER_E2E_SHOTS_DIR="${RUN_DIR}/shots/live52" \
    "$PY" "${HERE}/2026-09-08_live_run_probe.py" --start --budget 1500 --grace 60 >"${RUN_DIR}/live_run_52.log" 2>&1
say "    rc=$?"
grep -vE 'CONSOLE\[' "${RUN_DIR}/live_run_52.log" | grep -E '=> |server growth|cards  |glow  |F-026 samples|metrics store' | sed 's/^/    /' | tee -a "$SUMMARY"
say "    cascor after: $(cascor_state)   $(ws_summary)"
curl -s --max-time 10 -X PATCH -H 'Content-Type: application/json' -d '{"candidate_patience": 50}' "$CASCOR/v1/training/params" >/dev/null

say "=== (D) snapshot ==="
curl -s --max-time 120 -X POST -H 'Content-Type: application/json' -d '{"description": "canopy E2E fixture 2/52/2 COMPLETED, grown 2026-09-08 on cascor#632 (extended) with the relay alive"}' "$CASCOR/v1/snapshots" | cut -c1-200 | tee -a "$SUMMARY"; echo | tee -a "$SUMMARY"
say "relay repair sequence end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
