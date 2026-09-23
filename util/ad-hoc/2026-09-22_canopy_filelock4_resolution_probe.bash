#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_canopy_filelock4_resolution_probe.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- investigation
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#646
#
# Description:
#    Independent re-derivation of the juniper-canopy#646 falsifier.
#
#    #646 raises `filelock>=3.32.6` -> `>=4.0.0` in conf/requirements_ci.txt. That file also carries
#    `pre_commit>=4.6.2`, and pre-commit requires virtualenv>=20.10.0, every published version of
#    which declares `filelock<4`. The claim under test is that DELETING the pre_commit line -- and
#    changing nothing else, keeping the filelock 4 bump -- makes the file resolve.
#
#    pre_commit is dead weight in that file: canopy's pre-commit CI job installs it itself
#    (.github/workflows/ci.yml:91) and never reads conf/requirements_ci.txt, while the four lanes
#    that DO install that file (ci.yml:164/330/404/616 and scheduled-tests.yml:70) never run
#    pre-commit.
#
#    Prints four resolutions so the result is discriminating rather than a single green tick:
#      A. PR head as-is                       -> expected FAIL (unsatisfiable)
#      B. PR head minus pre_commit            -> expected PASS, with filelock 4.x
#      C. main as-is                          -> expected PASS, with filelock 3.x (control)
#      D. PR head minus filelock              -> expected PASS, with filelock 3.x (the other route)
#
#    Uses `uv pip compile` for speed. uv reaches the same verdict as pip in seconds where pip burns
#    ~51 minutes before `resolution-too-deep`; --index-strategy unsafe-best-match reproduces pip's
#    cross-index behaviour for the pytorch CPU extra index that the file carries.
#
#    Usage:  bash util/ad-hoc/2026-09-22_canopy_filelock4_resolution_probe.bash
#####################################################################################################################################################################################################

set -uo pipefail

CANOPY="/home/pcalnon/Development/python/Juniper/juniper-canopy"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  juniper-canopy#646 -- filelock 4.x resolution probe       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "scratch: ${WORK}"
echo

# The PR head's version of the file, fetched from the PR branch rather than reconstructed.
gh api "repos/pcalnon/juniper-canopy/contents/conf/requirements_ci.txt?ref=dependabot/pip/filelock-4.0.0" \
  --jq '.content' | base64 -d > "${WORK}/A_pr_head.txt"

cp "${CANOPY}/conf/requirements_ci.txt" "${WORK}/C_main.txt"

grep -v '^pre_commit' "${WORK}/A_pr_head.txt" > "${WORK}/B_no_precommit.txt"
grep -v '^filelock'   "${WORK}/A_pr_head.txt" > "${WORK}/D_no_filelock.txt"

echo "line counts: A=$(wc -l < "${WORK}/A_pr_head.txt")  B=$(wc -l < "${WORK}/B_no_precommit.txt")  C=$(wc -l < "${WORK}/C_main.txt")  D=$(wc -l < "${WORK}/D_no_filelock.txt")"
echo "A filelock line : $(grep '^filelock' "${WORK}/A_pr_head.txt")"
echo "C filelock line : $(grep '^filelock' "${WORK}/C_main.txt")"
echo

probe () {
  local tag="$1" file="$2" expect="$3"
  local start end rc out
  start=$(date +%s)
  out="${WORK}/${tag}.out"
  uv pip compile "${file}" \
      --index-strategy unsafe-best-match \
      --quiet -o "${WORK}/${tag}.lock" > "${out}" 2>&1
  rc=$?
  end=$(date +%s)
  echo "── ${tag} (expect ${expect}) ── exit=${rc} elapsed=$((end - start))s"
  if [ "${rc}" -eq 0 ]; then
    echo "     resolved filelock : $(grep -i '^filelock==' "${WORK}/${tag}.lock" || echo '(absent)')"
    echo "     resolved virtualenv: $(grep -i '^virtualenv==' "${WORK}/${tag}.lock" || echo '(absent)')"
    echo "     pins: $(grep -c '^[^[:space:]#]' "${WORK}/${tag}.lock")"
  else
    grep -iE "unsatisfiable|depends on filelock|because|no solution" "${out}" | tail -6 | sed 's/^/     /'
  fi
  echo
}

probe A "${WORK}/A_pr_head.txt"      FAIL
probe B "${WORK}/B_no_precommit.txt" PASS
probe C "${WORK}/C_main.txt"         PASS
probe D "${WORK}/D_no_filelock.txt"  PASS
