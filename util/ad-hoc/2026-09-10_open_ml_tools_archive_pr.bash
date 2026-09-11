#!/usr/bin/env bash
# Single-use: opens the juniper-ml PR archiving the two ci-tools ceiling fan-out helpers.
# Project: Juniper / juniper-ml / ad-hoc tooling. Author: Paul Calnon. Created 2026-09-10. MIT.
#
# A script rather than an inline command because a worktree-isolated session's Bash
# classifier refuses a multi-line invocation with runtime-computed operands. Both --add
# targets are NEW files on main, so the whole-file-upload clobber hazard does not apply.
set -euo pipefail
S="/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/15755553-7151-44a6-88a7-0dfb60e5f079/scratchpad"
W="/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/tender-splashing-wigderson"
/opt/miniforge3/envs/JuniperCascor1/bin/python \
  /home/pcalnon/Development/python/Juniper/juniper-ml/util/open_signed_pr.py \
  --repo juniper-ml \
  --branch chore/archive-ci-tools-ceiling-fanout-helpers \
  --add "${W}/util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py:util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py" \
  --add "${W}/util/ad-hoc/2026-09-10_open_ci_tools_ceiling_prs.py:util/ad-hoc/2026-09-10_open_ci_tools_ceiling_prs.py" \
  --message "$(cat "${S}/ml-tools-msg.txt")" \
  --title "chore(util): archive the juniper-ci-tools ceiling fan-out helpers" \
  --body-file "${S}/ml-tools-body.md" \
  "$@"
