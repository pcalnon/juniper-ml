#!/usr/bin/env bash
# Lane C round 3, task 1b: second clearing run (must be a no-op) and stage --check (must print 0 staged).
set -uo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
D=notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
export PYTHONDONTWRITEBYTECODE=1
unset FIXFWD_PR
cd "$S/repro" || exit 9
H1=$(sha256sum "$D" | cut -c1-64)
python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py > "$S/repro_clear_run2.txt" 2>&1
echo "clear run2 exit=$?"
tail -n 3 "$S/repro_clear_run2.txt"
echo "OK lines: $(grep -c '  OK  ' "$S/repro_clear_run2.txt")  ALREADY lines: $(grep -c 'ALREADY' "$S/repro_clear_run2.txt")  FAIL lines: $(grep -c 'FAIL' "$S/repro_clear_run2.txt")"
H2=$(sha256sum "$D" | cut -c1-64)
[ "$H1" = "$H2" ] && echo "hash unchanged by run2: $H2" || echo "HASH CHANGED by run2: $H1 -> $H2"
rm -rf "$S/repro_check_workdir"; mkdir -p "$S/repro_check_workdir"
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check --workdir "$S/repro_check_workdir" > "$S/repro_stage_check.txt" 2>&1
echo "check exit=$?"
tail -n 4 "$S/repro_stage_check.txt"
H3=$(sha256sum "$D" | cut -c1-64)
[ "$H1" = "$H3" ] && echo "hash unchanged by --check" || echo "HASH CHANGED by --check"
# and --from-repo a second time must also be a no-op on the cleared design
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo > "$S/repro_stage_from_repo_run2.txt" 2>&1
echo "from-repo run2 exit=$?"
tail -n 1 "$S/repro_stage_from_repo_run2.txt"
H4=$(sha256sum "$D" | cut -c1-64)
[ "$H1" = "$H4" ] && echo "hash unchanged by from-repo run2" || echo "HASH CHANGED by from-repo run2"
