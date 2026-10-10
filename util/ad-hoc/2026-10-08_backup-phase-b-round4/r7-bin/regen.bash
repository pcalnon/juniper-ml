#!/usr/bin/env bash
# Round 7: regenerate D in a scratch tree from origin/main's D.
set -u
R7="$(cd "$(dirname "$0")/.." && pwd)"
T="$R7/tree"
D=notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
rm -rf "$T"; mkdir -p "$T"; tar -xf "$R7/head.tar" -C "$T"
sha256sum "$T/$D"
cp "$R7/D.main.md" "$T/$D"
cd "$T" || exit 1
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo 2>&1 | tail -4
python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py 2>&1 | tail -3
sha256sum "$D"
python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py 2>&1 | tail -2
python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py --check 2>&1 | tail -2
