#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc probe
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-15_verify_worktree_content_shipped.bash
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-15
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     Pre-cleanup safety check. A worktree holding UNCOMMITTED changes is about to be
#     removed; `git worktree remove --force` is destructive and also deletes ignored
#     files. This proves every uncommitted file in the worktree is byte-identical to
#     what is on origin/main, so nothing is lost by removing it.
#
#     Exits non-zero if ANY file differs, so it can gate the removal.
#
# Usage:
#     bash util/ad-hoc/2026-09-15_verify_worktree_content_shipped.bash <worktree-path>
#
#####################################################################################################################################################################################################
set -euo pipefail

WT="${1:?usage: $0 <worktree-path>}"
cd "$WT"

git fetch -q origin main

differs=0
same=0
while IFS= read -r f; do
    [ -n "$f" ] || continue
    if git show "origin/main:$f" 2>/dev/null | diff -q - "$f" >/dev/null 2>&1; then
        echo "  SAME as origin/main : $f"
        same=$((same + 1))
    else
        echo "  *** DIFFERS         : $f"
        differs=$((differs + 1))
    fi
done < <(git diff --name-only)

echo
echo "identical: $same   differing: $differs"
if [ "$differs" -ne 0 ]; then
    echo "REFUSING: worktree holds content not on origin/main -- do not remove it."
    exit 1
fi
echo "SAFE: every uncommitted change is already on origin/main."
