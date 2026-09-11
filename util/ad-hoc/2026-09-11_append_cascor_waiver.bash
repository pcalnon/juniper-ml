#!/usr/bin/env bash
# Single-use: appends the Allow-Symbol-Loss waiver commit to juniper-cascor#645's branch.
# Project: Juniper / juniper-ml / ad-hoc tooling. Author: Paul Calnon. Created 2026-09-11. MIT.
#
# The trailer must live in a COMMIT message (never PR-body prose) so it survives squash-merge,
# its value is a whitespace-separated list of SYMBOL NAMES (prose there matches nothing and the
# screen still FAILS), and the trailer block must be the last paragraph.
set -euo pipefail
S="/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/15755553-7151-44a6-88a7-0dfb60e5f079/scratchpad"
C="/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--chore--widen-ci-tools-ceiling--20260910-2021--a51b7c58"
REL="src/tests/unit/test_sequence_safety_retired.py"

/opt/miniforge3/envs/JuniperCascor1/bin/python \
  /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/2026-09-08_append_signed_commit.py \
  --repo juniper-cascor \
  --branch chore/raise-ci-tools-floor \
  --add "${C}/${REL}:${REL}" \
  --message "$(cat "${S}/cascor-waiver-msg.txt")" \
  "$@"
