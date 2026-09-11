#!/usr/bin/env bash
# Single-use: appends the sequence-safety pin-guard fix to juniper-cascor#645's branch.
# Project: Juniper / juniper-ml / ad-hoc tooling. Author: Paul Calnon. Created 2026-09-11. MIT.
#
# Uses append_signed_commit.py rather than open_signed_pr.py: the latter's DUP-GUARD refuses
# once a PR exists for the branch. append_signed_commit.py reads expected_head_oid live and
# verifies its own write by reading every added path back.
set -euo pipefail
S="/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/15755553-7151-44a6-88a7-0dfb60e5f079/scratchpad"
C="/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--chore--widen-ci-tools-ceiling--20260910-2021--a51b7c58"
REL="src/tests/unit/test_sequence_safety_retired.py"

/opt/miniforge3/envs/JuniperCascor1/bin/python \
  /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/2026-09-08_append_signed_commit.py \
  --repo juniper-cascor \
  --branch chore/raise-ci-tools-floor \
  --add "${C}/${REL}:${REL}" \
  --message "$(cat "${S}/cascor-testfix-msg.txt")" \
  "$@"
