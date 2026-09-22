#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_wait_for_dependabot_rebase.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- one-off
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#646
#
# Description:
#    Block until a dependabot PR's head SHA changes away from a known value, i.e. until dependabot
#    has acted on an `@dependabot rebase` comment, then print the new head and the resulting file
#    list.
#
#    Used for juniper-canopy#646: it edits three files that juniper-canopy#650 deleted, so the PR
#    went DIRTY on merge and a branch update would only produce modify/delete conflicts. A rebase
#    regenerates the diff against current main; the file list afterwards is how you confirm the
#    deleted files actually left the PR rather than assuming they did.
#
#    Usage:  bash util/ad-hoc/2026-09-22_wait_for_dependabot_rebase.bash <repo> <pr> <old-sha> [timeout-s]
#####################################################################################################################################################################################################

set -uo pipefail

REPO="${1:?usage: $0 <owner/repo> <pr> <old-sha> [timeout-s]}"
PR="${2:?pr number required}"
OLD="${3:?old head sha required}"
TIMEOUT="${4:-900}"

START=$(date +%s)
echo "watching ${REPO}#${PR}; head is ${OLD:0:8}, waiting for it to move (timeout ${TIMEOUT}s)"

while true; do
  CUR="$(gh api "repos/${REPO}/pulls/${PR}" --jq '.head.sha' 2>/dev/null)"
  STATE="$(gh api "repos/${REPO}/pulls/${PR}" --jq '.state' 2>/dev/null)"

  if [ "${STATE}" != "open" ]; then
    echo "PR is now ${STATE} (head ${CUR:0:8}) -- dependabot may have closed and superseded it"
    break
  fi
  if [ -n "${CUR}" ] && [ "${CUR}" != "${OLD}" ]; then
    echo "head moved: ${OLD:0:8} -> ${CUR:0:8}"
    break
  fi

  NOW=$(date +%s)
  if [ $((NOW - START)) -ge "${TIMEOUT}" ]; then
    echo "timed out after ${TIMEOUT}s with head still ${OLD:0:8}"
    exit 1
  fi
  sleep 20
done

echo
echo "files in the PR now:"
gh api "repos/${REPO}/pulls/${PR}/files" --jq '.[].filename' | sed 's/^/  /'
echo
echo "mergeStateStatus: $(gh pr view "${PR}" --repo "${REPO}" --json mergeStateStatus --jq '.mergeStateStatus')"
