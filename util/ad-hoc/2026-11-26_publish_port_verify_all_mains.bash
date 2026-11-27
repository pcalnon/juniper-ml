#!/usr/bin/env bash
# The one-artifact template sweep's done check: every port's publishers on each repo's main, judged by the FINAL checker.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling (publish artifact identity)
# Author:     Paul Calnon
# Created:    2026-11-26
# Status:     ad-hoc -- one-off (the sweep's done check, which read "18 of 18 pass" once every port had landed)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-23_publish_port_template_identity.py (the checker, fix pass 11, sha256 a452db3d...);
#             util/ad-hoc/2026-11-24_publish_port_install_pins.json (the canonical pins); util/ad-hoc/2026-11-15_fetch_pr_files.py
#             (the fetch); reports/2026-11-23_one-artifact-template-sweep-reviews/dispositions.md (the arc's record: § "Fix
#             pass 11", "How to run the checker on a port", and "Landed: juniper-ml#2673", the run that read 18 of 18);
#             plan v1.15.18 (notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
#
# Promoted, with plan v1.15.18, from session b71989's verify_all_mains_v3.bash (worktree moonlit-percolating-sun, its
# tmp/s2/), itself an adaptation of session ffffd3's v2: v2 passed no --pins, fetched no called file, and ran the checker
# once per workflow. The behaviour is v3's. What changed in the promotion: it runs from any juniper-ml checkout (the root
# is found from this script's own location); the checker, the pins file and the fetch are that checkout's own files;
# the interpreter is ${PYTHON:-python3}; the output goes under the checkout's tmp/; and it names no host path.
#
# What it does: fetch juniper-cascor main's three publishers (its publish.yml is the template) and every port's
# publishers from each repository's `main` (or REF_<repo> if set, e.g. REF_juniper_data=fix/x), then run the checker
# ONCE per repository with all of its publishers on one command line, --repo and --pins explicit, and juniper-data's
# called file notify-consumers.yml fetched beside its publish.yml, as "How to run the checker on a port" says. Done:
# the last line reads "18 of 18 pass" and the exit status is 0; otherwise it is 1 (2 when it cannot start).
#
#   bash util/ad-hoc/2026-11-26_publish_port_verify_all_mains.bash
#
# - CHECKER and PINS (environment) override the checkout's own checker and pins file, e.g. to check with a port's
#   proposed pins copy before it is merged. A relative path is read from the checkout root.
# - PYTHON (environment, default python3) runs the checker and the fetch. It must import PyYAML (the checker parses
#   the workflows); the run refuses at once when it cannot.
# - Network: read-only GitHub API GETs through `gh` (each repository's ref, and the files fetched).
# - Each run writes a NEW directory, tmp/publish-port-verify-all-mains/<UTC stamp>/, under the checkout root, and
#   deletes nothing.
# - `set -u` alone, not `set -euo pipefail`: a failed fetch or a failing repository is reported and the run goes on to
#   the next, so the summary counts every publisher.
set -u
root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || { echo "REFUSED: this script is not inside a git checkout"; exit 2; }
cd "$root" || exit 2
wf=".github/workflows"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="tmp/publish-port-verify-all-mains/${stamp}"
mkdir -p "$(dirname "$out")" || exit 2
mkdir "$out" || { echo "REFUSED: $out exists (each run writes a new directory)"; exit 2; }
checker="${CHECKER:-util/ad-hoc/2026-11-23_publish_port_template_identity.py}"
pins="${PINS:-util/ad-hoc/2026-11-24_publish_port_install_pins.json}"
fetch="util/ad-hoc/2026-11-15_fetch_pr_files.py"
py="${PYTHON:-python3}"
"$py" -I -c 'import yaml' > /dev/null 2>&1 || { echo "REFUSED: ${py} cannot import yaml (PyYAML): set PYTHON to an interpreter that has it"; exit 2; }
date -u
echo "checkout: $root ($(git rev-parse --short=12 HEAD)); output: $out"
echo "checker: $checker sha256 $(sha256sum "$checker" | cut -c1-16)"
echo "pins:    $pins sha256 $(sha256sum "$pins" | cut -c1-16)"
declare -A files
files[juniper-cascor]="publish.yml publish-cascor-model.yml publish-protocol.yml"
files[juniper-canopy]="publish.yml"
files[juniper-data]="publish.yml"
files[juniper-data-client]="publish.yml"
files[juniper-cascor-client]="publish.yml"
files[juniper-cascor-worker]="publish.yml"
files[juniper-recurrence]="publish-recurrence-app.yml publish-recurrence-client.yml publish-recurrence-model.yml"
files[juniper-ml]="publish.yml publish-ci-tools.yml publish-config-tools.yml publish-doc-tools.yml publish-model-core.yml publish-observability.yml publish-service-core.yml"
order="juniper-cascor juniper-canopy juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-recurrence juniper-ml"
for r in $order; do
    var="REF_${r//-/_}"
    ref="${!var:-main}"
    paths=()
    for f in ${files[$r]}; do paths+=("$wf/$f"); done
    if [[ "$r" == "juniper-data" ]]; then paths+=("$wf/notify-consumers.yml"); fi
    echo "$r @ $ref: $(gh api "repos/pcalnon/$r/commits/$ref" --jq '.sha[0:12] + " " + .commit.committer.date')"
    "$py" -I "$fetch" --repo "$r" --ref "$ref" --out "$out/$r" "${paths[@]}" > "$out/$r.fetch.log" 2>&1 || echo "  FETCH FAILED (see $out/$r.fetch.log)"
done
template="$out/juniper-cascor/$wf/publish.yml"
echo "publishers fetched: $(find "$out" -name 'publish*.yml' | wc -l) (expect 18); called file: $(sha256sum "$out/juniper-data/$wf/notify-consumers.yml" 2>/dev/null | cut -c1-16)"
pass=0
total=0
for r in $order; do
    args=()
    for f in ${files[$r]}; do args+=("$out/$r/$wf/$f"); total=$((total + 1)); done
    "$py" -I -B "$checker" --repo "$r" --template "$template" --pins "$pins" "${args[@]}" > "$out/$r.check.log" 2>&1
    rc=$?
    n=$(grep -c '^PASS ' "$out/$r.check.log")
    pass=$((pass + n))
    grep -E '^(PASS|FAIL) ' "$out/$r.check.log" | cut -c1-160 | sed "s|^|  $r: |"
    echo "  $r: exit $rc; $(tail -1 "$out/$r.check.log")"
done
echo "${pass} of ${total} pass"
[[ ${pass} -eq ${total} ]]
