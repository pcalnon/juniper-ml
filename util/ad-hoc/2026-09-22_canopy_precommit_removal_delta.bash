#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_precommit_removal_delta.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#646, juniper-canopy#650
#
# Description:
#    What is LOST from the installed set when `pre_commit>=4.6.2` is removed from juniper-canopy's
#    conf/requirements_ci.txt.
#
#    The resolution probe showed the pre_commit-free variant resolves to 90 pins against main's 95.
#    A fix that greens CI by quietly dropping five distributions is only safe if none of the lanes
#    that install this file actually need them. This names the five and reports, for each, whether
#    the requirements file still declares it directly and whether canopy imports it.
#
#    Usage:  bash util/ad-hoc/2026-09-22_canopy_precommit_removal_delta.bash
#####################################################################################################################################################################################################

set -uo pipefail

CANOPY="/home/pcalnon/Development/python/Juniper/juniper-canopy"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

gh api "repos/pcalnon/juniper-canopy/contents/conf/requirements_ci.txt?ref=dependabot/pip/filelock-4.0.0" \
  --jq '.content' | base64 -d > "${WORK}/pr_head.txt"
grep -v '^pre_commit' "${WORK}/pr_head.txt" > "${WORK}/no_precommit.txt"

uv pip compile "${CANOPY}/conf/requirements_ci.txt" --index-strategy unsafe-best-match --quiet -o "${WORK}/main.lock"
uv pip compile "${WORK}/no_precommit.txt"           --index-strategy unsafe-best-match --quiet -o "${WORK}/nopc.lock"

grep -oiE '^[a-z0-9._-]+' "${WORK}/main.lock" | tr '[:upper:]' '[:lower:]' | sort -u > "${WORK}/main.names"
grep -oiE '^[a-z0-9._-]+' "${WORK}/nopc.lock" | tr '[:upper:]' '[:lower:]' | sort -u > "${WORK}/nopc.names"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Removing pre_commit: what leaves the installed set        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "main pins: $(wc -l < "${WORK}/main.names")    without pre_commit: $(wc -l < "${WORK}/nopc.names")"
echo
echo "LOST (in main, not in the pre_commit-free resolution):"
comm -23 "${WORK}/main.names" "${WORK}/nopc.names" > "${WORK}/lost"
sed 's/^/  - /' "${WORK}/lost"
echo
echo "GAINED:"
comm -13 "${WORK}/main.names" "${WORK}/nopc.names" | sed 's/^/  + /'
echo
echo "For each LOST package -- still declared directly in the file? imported by canopy?"
while read -r pkg; do
  decl=$(grep -icE "^${pkg}[><=~!]" "${WORK}/no_precommit.txt")
  mod=${pkg//-/_}
  imp=$(grep -rlE "^[[:space:]]*(import|from)[[:space:]]+${mod}\b" "${CANOPY}/src" --include='*.py' 2>/dev/null | wc -l)
  printf '  %-16s declared-direct=%s  importing-files=%s\n' "${pkg}" "${decl}" "${imp}"
done < "${WORK}/lost"
