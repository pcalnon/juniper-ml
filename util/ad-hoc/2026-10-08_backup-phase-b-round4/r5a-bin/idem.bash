#!/usr/bin/env bash
# r5-A: idempotence of the staging + clearing scripts on a scratch copy of 9ce2f602
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/097ae87b-7a4c-4970-9f46-d052521e17c7/scratchpad/r5-A
rm -rf "$S/idem"; cp -a "$S/head" "$S/idem"; cd "$S/idem" || exit 2
D=notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
sha256sum "$D"
export PYTHONDONTWRITEBYTECODE=1
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check 2>&1 | tail -3
python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py 2>&1 | tail -3
sha256sum "$D"
cmp "$D" "$S/head/$D" && echo "D unchanged"
