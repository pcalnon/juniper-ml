#!/usr/bin/env bash
# run each named suite in a tree; print counts
cd "$1" || exit 2
shift
for t in "$@"; do
  printf '%s ' "$t"
  PYTHONDONTWRITEBYTECODE=1 timeout 900 python3 -m unittest "$t" 2>&1 | grep -E '^(Ran|OK|FAILED)' | tr '\n' ' '
  echo
done
