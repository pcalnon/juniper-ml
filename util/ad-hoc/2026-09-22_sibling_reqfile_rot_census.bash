#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_sibling_reqfile_rot_census.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-ml#1994
#
# Description:
#    Which Juniper repos carry a conf/requirements_ci.txt that no longer RESOLVES, and which of
#    them still install it in CI?
#
#    Context: the filelock 3.32.6 -> 4.0.0 dependabot bump merged GREEN in juniper-data#407 and
#    juniper-data-client#207 on 2026-09-21, because nothing in those repos installs the file. The
#    same bump is red in juniper-canopy#646, which is the only repo that does install it. A file
#    that nothing installs is documentation, and documentation that cannot resolve is a lie that
#    dependabot keeps editing.
#
#    Prints, per repo: whether the file exists, whether any workflow installs it, and whether it
#    resolves. A repo that does NOT install it but does NOT resolve is rot -- harmless today,
#    misleading to anyone who trusts it, and a trap for a local consumer that does install it.
#
#    Usage:  bash util/ad-hoc/2026-09-22_sibling_reqfile_rot_census.bash
#####################################################################################################################################################################################################

set -uo pipefail

JUNIPER="/home/pcalnon/Development/python/Juniper"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

REPOS="juniper-canopy juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-recurrence"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  conf/requirements_ci.txt -- installed? resolvable?        ║"
echo "╚════════════════════════════════════════════════════════════╝"
printf '%-24s %-8s %-12s %-12s %s\n' REPO FILE INSTALLED-IN-CI RESOLVES DETAIL
echo "-------------------------------------------------------------------------------------------"

for repo in ${REPOS}; do
  root="${JUNIPER}/${repo}"
  req="${root}/conf/requirements_ci.txt"

  if [ ! -d "${root}" ]; then
    printf '%-24s %-8s %-12s %-12s %s\n' "${repo}" "-" "-" "-" "repo not present locally"
    continue
  fi
  if [ ! -f "${req}" ]; then
    printf '%-24s %-8s %-12s %-12s %s\n' "${repo}" "no" "-" "-" "no conf/requirements_ci.txt"
    continue
  fi

  # Does any workflow actually pip-install it?
  hits=$(grep -rlE "pip install .*-r .*requirements_ci\.txt" "${root}/.github/workflows" 2>/dev/null | wc -l)
  if [ "${hits}" -gt 0 ]; then installed="YES"; else installed="no"; fi

  # Does it resolve? unsafe-best-match reproduces pip's cross-index view for the pytorch extra index.
  out="${WORK}/${repo}.out"
  if uv pip compile "${req}" --index-strategy unsafe-best-match --quiet \
        -o "${WORK}/${repo}.lock" > "${out}" 2>&1; then
    resolves="YES"
    detail=""
  else
    resolves="NO"
    detail=$(grep -iE "depends on|unsatisfiable|no solution" "${out}" | tail -1 | cut -c1-70)
  fi

  printf '%-24s %-8s %-12s %-12s %s\n' "${repo}" "yes" "${installed}" "${resolves}" "${detail}"
done

echo
echo "Legend: INSTALLED-IN-CI=YES + RESOLVES=NO  => actively breaks CI (the canopy#646 shape)"
echo "        INSTALLED-IN-CI=no  + RESOLVES=NO  => rot: a file dependabot edits that cannot be used"
