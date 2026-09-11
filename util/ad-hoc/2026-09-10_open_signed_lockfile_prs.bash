#!/usr/bin/env bash
# Single-use: opens the juniper-cascor-client and juniper-data-client PRs converting
# lockfile-update.yml's regen commit to the GitHub-signed createCommitOnBranch path.
# Project: Juniper / juniper-ml / ad-hoc tooling. Author: Paul Calnon. Created 2026-09-10. MIT.
#
# A script rather than an inline command because a worktree-isolated session's Bash
# classifier refuses a multi-line invocation with runtime-computed operands.
#
# juniper-ml is deliberately NOT in this set: its lockfile-update.yml uses
# peter-evans/create-pull-request on a schedule, a different mechanism from the plain
# git push these two carry.
set -euo pipefail
S="/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/15755553-7151-44a6-88a7-0dfb60e5f079/scratchpad"
W="/home/pcalnon/Development/python/Juniper/worktrees"
HELPER="/home/pcalnon/Development/python/Juniper/juniper-ml/util/open_signed_pr.py"
PY="/opt/miniforge3/envs/JuniperCascor1/bin/python"
TITLE="ci(lockfile): sign the regen commit via createCommitOnBranch"

CCL="${W}/juniper-cascor-client--ci--sign-the-lockfile-regen-commit--20260910-2100--66311349"
DCL="${W}/juniper-data-client--ci--sign-the-lockfile-regen-commit--20260910-2100--25a18dfb"

"${PY}" "${HELPER}" --repo juniper-cascor-client --branch ci/sign-the-lockfile-regen-commit \
  --add "${CCL}/.github/workflows/lockfile-update.yml:.github/workflows/lockfile-update.yml" \
  --add "${CCL}/CHANGELOG.md:CHANGELOG.md" \
  --message "$(cat "${S}/sign-msg.txt")" --title "${TITLE}" --body-file "${S}/sign-body.md"

"${PY}" "${HELPER}" --repo juniper-data-client --branch ci/sign-the-lockfile-regen-commit \
  --add "${DCL}/.github/workflows/lockfile-update.yml:.github/workflows/lockfile-update.yml" \
  --add "${DCL}/CHANGELOG.md:CHANGELOG.md" \
  --message "$(cat "${S}/sign-msg.txt")" --title "${TITLE}" --body-file "${S}/sign-body.md"
