#!/usr/bin/env bash
# A port pull request's pre-merge check, on its head as GitHub holds it: the FINAL checker on the PR's publishers.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling (publish artifact identity)
# Author:     Paul Calnon
# Created:    2026-11-26
# Status:     ad-hoc -- one-off (the one-artifact template sweep's pre-merge check of each port)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:    util/ad-hoc/2026-11-23_publish_port_template_identity.py (the checker, fix pass 11, sha256 a452db3d...);
#             util/ad-hoc/2026-11-24_publish_port_install_pins.json (the canonical pins); util/ad-hoc/2026-11-15_fetch_pr_files.py
#             (the fetch); reports/2026-11-23_one-artifact-template-sweep-reviews/dispositions.md (the arc's record, where
#             each port's "FINAL checker on its head" line comes from this check); plan v1.15.18
#             (notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
#
# Promoted, with plan v1.15.18, from session b71989's check_pr_head.bash (worktree moonlit-percolating-sun, its tmp/s2/).
# The behaviour is the original's, the refusal of any checker but sha256 a452db3d... included. What changed in the
# promotion: it runs from any juniper-ml checkout (the root is found from this script's own location); the checker and
# the fetch are that checkout's own files; the interpreter is ${PYTHON:-python3}; the output goes under the checkout's
# tmp/; and it names no host path.
#
# What it does: read the PR's head commit, fetch the named publishers at that commit (and, for juniper-data, its called
# file notify-consumers.yml) and juniper-cascor main's publish.yml (the template), then run the checker with the given
# pins, all of the repository's publishers on one command line. It prints the head sha, the checker's lines and its
# exit status, and exits with the checker's status (0: every publisher passes); 1 when a fetch fails; 2 when it cannot
# start (a usage error, a checker that is not a452db3d..., no PyYAML, an output directory that exists).
#
#   bash util/ad-hoc/2026-11-26_publish_port_check_pr_head.bash REPO PR_NUMBER PINS_FILE PUBLISHER [PUBLISHER ...]
#   e.g. bash util/ad-hoc/2026-11-26_publish_port_check_pr_head.bash juniper-cascor-client 207 \
#            util/ad-hoc/2026-11-24_publish_port_install_pins.json publish.yml
#
# - PINS_FILE: the canonical pins file, or a port's proposed copy. A relative path is read from the checkout root.
# - PYTHON (environment, default python3) runs the checker and the fetch. It must import PyYAML (the checker parses
#   the workflows); the run refuses at once when it cannot.
# - Network: read-only GitHub API GETs through `gh` (the PR's head, and the files fetched).
# - Each run writes a NEW directory, tmp/publish-port-check-pr-head/<REPO>-<PR_NUMBER>/<UTC stamp>/, under the checkout
#   root, and deletes nothing.
# - `set -u` alone, not `set -euo pipefail`: the checker's exit status is captured and reported, never fatal here.
set -u
repo="${1:?repo}"; pr="${2:?pr}"; pins="${3:?pins}"; shift 3
root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)" || { echo "REFUSED: this script is not inside a git checkout"; exit 2; }
cd "$root" || exit 2
py="${PYTHON:-python3}"
checker="util/ad-hoc/2026-11-23_publish_port_template_identity.py"
want="a452db3d285d70838adb3c6cfc9091c9cf0999996bf6e718c6ef5e49e05cee35"
got="$(sha256sum "$checker" | cut -d' ' -f1)"
[[ "$got" == "$want" ]] || { echo "REFUSED: checker sha256 $got"; exit 2; }
"$py" -I -c 'import yaml' > /dev/null 2>&1 || { echo "REFUSED: ${py} cannot import yaml (PyYAML): set PYTHON to an interpreter that has it"; exit 2; }
wf=".github/workflows"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="tmp/publish-port-check-pr-head/${repo}-${pr}/${stamp}"
mkdir -p "$(dirname "$out")" || exit 2
mkdir "$out" || { echo "REFUSED: $out exists (each run writes a new directory)"; exit 2; }
head="$(gh pr view "$pr" --repo "pcalnon/${repo}" --json headRefOid,headRefName --jq '.headRefOid + " " + .headRefName')"
sha="${head%% *}"; branch="${head#* }"
echo "$(date -u) ${repo}#${pr} head ${sha} (${branch}); output: $out"
paths=()
for f in "$@"; do paths+=("$wf/$f"); done
if [[ "$repo" == "juniper-data" ]]; then paths+=("$wf/notify-consumers.yml"); fi
"$py" -I util/ad-hoc/2026-11-15_fetch_pr_files.py --repo "$repo" --ref "$sha" --out "$out/head" "${paths[@]}" > "$out/fetch.log" 2>&1 || { echo "FETCH FAILED"; cat "$out/fetch.log"; exit 1; }
"$py" -I util/ad-hoc/2026-11-15_fetch_pr_files.py --repo juniper-cascor --ref main --out "$out/cascor" "$wf/publish.yml" >> "$out/fetch.log" 2>&1 || { echo "TEMPLATE FETCH FAILED"; exit 1; }
args=()
for f in "$@"; do args+=("$out/head/$wf/$f"); done
"$py" -I -B "$checker" --repo "$repo" --template "$out/cascor/$wf/publish.yml" --pins "$pins" "${args[@]}" > "$out/check.log" 2>&1
rc=$?
cut -c1-220 "$out/check.log"
echo "checker exit ${rc}; template sha256 $(sha256sum "$out/cascor/$wf/publish.yml" | cut -c1-16); pins sha256 $(sha256sum "$pins" | cut -c1-16)"
exit $rc
