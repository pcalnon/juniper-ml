#!/usr/bin/env bash
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-22_wait_for_main_pipeline.bash
# Author:        Paul Calnon
#
# Date Created:  2026-09-22
# Last Modified: 2026-09-22
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
# Status:        ad-hoc -- one-off
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       juniper-canopy#646, juniper-canopy#650
#
# Description:
#    Block until every push-triggered workflow run for a given SHA on a repo's default branch has
#    finished, then print each run's conclusion.
#
#    A PR merging green says the PR was green; it does not say main is. The post-merge lane runs
#    different jobs against a different tree, and this session's whole point was a change to how
#    four CI lanes install their dependencies -- so main's own pipeline is the confirmation that
#    matters, not the PR's.
#
#    Usage:  bash util/ad-hoc/2026-09-22_wait_for_main_pipeline.bash <owner/repo> <sha> [timeout-s]
#####################################################################################################################################################################################################

set -uo pipefail

REPO="${1:?usage: $0 <owner/repo> <sha> [timeout-s]}"
SHA="${2:?sha required}"
TIMEOUT="${3:-2400}"

# `gh run list --commit` matches on the FULL sha and silently returns nothing for an abbreviated
# one. The first revision of this script took that empty list as "0 pending, 0 failed" and printed
# "main is GREEN" while the pipeline was still running -- a vacuous pass of exactly the kind this
# session kept producing. Resolve to the full sha, and refuse to conclude anything from an empty
# list (see the TOTAL guard below).
SHA="$(gh api "repos/${REPO}/commits/${SHA}" --jq '.sha' 2>/dev/null || echo "${SHA}")"

runs () {
  gh run list --repo "${REPO}" --commit "${SHA}" --limit 30 --json name,status,conclusion,event 2>/dev/null
}

START=$(date +%s)
echo "waiting on push runs for ${REPO} @ ${SHA:0:8} (timeout ${TIMEOUT}s)"

while true; do
  SNAP="$(runs)"
  TOTAL="$(printf '%s' "${SNAP}" | jq '[.[] | select(.event == "push")] | length' 2>/dev/null)"
  PENDING="$(printf '%s' "${SNAP}" | jq '[.[] | select(.event == "push") | select(.status != "completed")] | length' 2>/dev/null)"

  if [ "${TOTAL:-0}" -gt 0 ] && [ "${PENDING:-1}" -eq 0 ]; then
    break
  fi

  NOW=$(date +%s)
  if [ $((NOW - START)) -ge "${TIMEOUT}" ]; then
    echo "timed out with ${PENDING:-?} run(s) still going"
    break
  fi
  sleep 30
done

SNAP="$(runs)"
TOTAL="$(printf '%s' "${SNAP}" | jq '[.[] | select(.event == "push")] | length' 2>/dev/null)"
FAILED="$(printf '%s' "${SNAP}" | jq '[.[] | select(.event == "push") | select(.conclusion == "failure")] | length' 2>/dev/null)"

echo
printf '%s' "${SNAP}" | jq -r '.[] | select(.event == "push") | "  \(.conclusion // .status)\t\(.name)"'
echo

# An EMPTY list is not a green one. Without this, a mistyped or abbreviated sha yields zero runs,
# zero failures, and a confident "GREEN" -- which is what the first revision reported while the
# pipeline was still in progress.
if [ "${TOTAL:-0}" -eq 0 ]; then
  echo "NOT ESTABLISHED -- no push runs found for ${SHA:0:8}; nothing was measured"
  exit 2
fi
if [ "${FAILED:-1}" -eq 0 ]; then
  echo "main is GREEN at ${SHA:0:8} (${TOTAL} push run(s), 0 failed)"
else
  echo "main has ${FAILED} FAILED run(s) of ${TOTAL} at ${SHA:0:8}"
  exit 1
fi
