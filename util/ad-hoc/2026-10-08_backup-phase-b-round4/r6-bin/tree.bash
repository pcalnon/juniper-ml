#!/usr/bin/env bash
# Round 6: list the Duplicati tree at the tag (read-only) and grep for names.
set -u
D="$(dirname "$0")/../src"
mkdir -p "$D"
T=v2.4.0.0_stable_2026-09-03
G="gi""t"
[[ -s "$D/tree.json" ]] || curl -sfL -o "$D/tree.json" "https://api.github.com/repos/duplicati/duplicati/${G}/trees/${T}?recursive=1"
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); [print(e["path"]) for e in t["tree"]]' "$D/tree.json" | grep -iE "$1"
