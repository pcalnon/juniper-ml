#!/usr/bin/env bash
# r5-A: run named suites in a tree with a minimal environment; print counts and failing ids
cd "$1" || exit 2
shift
for t in "$@"; do
  printf '%s ' "$t"
  env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 HOME="$PWD" timeout 900 python3 -m unittest "$t" 2>&1 | grep -E '^(Ran|OK|FAILED|FAIL:|ERROR:)' | tr '\n' ' '
  echo
done
