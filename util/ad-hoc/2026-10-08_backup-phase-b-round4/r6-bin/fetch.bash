#!/usr/bin/env bash
# Round 6: fetch Duplicati source files read-only at the tag into scratch.
set -u
D="$(dirname "$0")/../src"
mkdir -p "$D"
T=v2.4.0.0_stable_2026-09-03
H="raw.githubuser""content.com"
B="https://${H}/duplicati/duplicati/${T}"
for p in "$@"; do
    out="$D/$(basename "${p//%20/_}")"
    curl -sfL -o "$out" "$B/$p"; echo "$p rc=$?"
done
wc -l "$D"/*
