#!/usr/bin/env bash
# Round 7: fresh extraction of 19ae4aa9; suites normal + ci-sim; home-absent; r6 mutants.
set -u
R7="$(cd "$(dirname "$0")/.." && pwd)"
SRC=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/golden-floating-willow/util/ad-hoc/2026-10-08_backup-phase-b-round4/r6-bin
cp "$SRC"/run_suites.bash "$SRC"/ci_home_absent.bash "$SRC"/r6_mutants.py "$R7/bin/"
T="$R7/t1"; rm -rf "$T"; mkdir -p "$T"; tar -xf "$R7/head.tar" -C "$T"
echo "== normal"; bash "$R7/bin/run_suites.bash" "$T" normal
echo "== cisim";  bash "$R7/bin/run_suites.bash" "$T" cisim
echo "== home-absent"; bash "$R7/bin/ci_home_absent.bash" "$T" "$R7/ha"
echo "== home-absent whole A0 suite"
( cd "$R7/ha" && env -i PATH=/usr/bin:/bin HOME="$R7/ha" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_a0_restore_scripts 2>&1 | tail -3 )
echo "== r6 mutants (plain PATH)"; python3 "$R7/bin/r6_mutants.py" "$T"
echo "== git-status-like check of tree vs tar"; T2="$R7/t2"; rm -rf "$T2"; mkdir -p "$T2"; tar -xf "$R7/head.tar" -C "$T2"; diff -rq "$T" "$T2" | grep -v -E '__pycache__' | head
