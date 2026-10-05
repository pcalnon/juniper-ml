#!/usr/bin/env bash
# Lane C round 3: build a fresh tree, put origin/main's D in it, run --from-repo, save the STAGED D
# (the clearing script's input) for the gate attacks.
set -euo pipefail
S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C
W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sorted-stargazing-garden
D=notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
export PYTHONDONTWRITEBYTECODE=1
rm -rf "$S/staged_tree"; mkdir -p "$S/staged_tree"
git -C "$W" archive c3d0e890 | tar -x -C "$S/staged_tree"
git -C "$W" show "origin/main:$D" > "$S/staged_tree/$D"
cd "$S/staged_tree"
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo > /dev/null
cp "$D" "$S/staged_D.md"
sha256sum "$S/staged_D.md"
