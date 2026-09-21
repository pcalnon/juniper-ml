#!/usr/bin/env bash
# Project:     Juniper
# Sub-Project: juniper-ml (cascor#573 logging redesign, P1.4)
# Application: ad-hoc verification
# Author:      Paul Calnon
# Version:     0.1.0
# License:     MIT License
#
# Re-derives the "~872 live suppressed Path-A sites" figure that §11 of
# notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md uses to size the per-call
# cost of Option D, and that the 2026-09-17 handoff repeats.
#
# The method is the one published in
# notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md: count
# `Logger.<method>(` occurrences under src/, then subtract three populations --
#   src/tests/                      (not production)
#   src/cascade_correlation/backups/ (dead tree, RECON N-6)
#   src/api/                        (stdlib-bound, does not use cascor's Logger)
# -- and take trace + verbose + debug as the set suppressed at the default INFO level.
#
# WHY THIS EXISTS: the consensus procedure
# (notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md §1) holds
# that accepting an agent's number without re-deriving it is the same error merely outsourced.
#
# TRAP, and the reason a naive re-derivation disagrees by ~30%: `git grep` walks the TRACKED tree.
# `src/backups/check.py` is UNTRACKED and carries ~68 more debug sites, and the dead tree is
# `src/cascade_correlation/backups/`, NOT `src/backups/`. A plain `grep -r` over the working tree
# counts both and lands near 1,144 instead of ~872.
#
# Usage: 2026-09-21_p14_suppressed_site_census.bash [<rev>]
set -uo pipefail

CASCOR="${P14_CASCOR:-/home/pcalnon/Development/python/Juniper/juniper-cascor}"
REV="${1:-main}"
PAT='\b[Ll]ogger\.(trace|verbose|debug|info|warning|error|critical|fatal)\('

# git grep prefixes each hit with "<rev>:<path>:", so path filtering happens on that prefix --
# which is why -h is NOT passed: the path must survive into the exclusion filter.
tally() { # tally <path-exclude-regex|""> <method-alternation>
    local exclude="$1" methods="$2"
    git -C "$CASCOR" grep -o -E "$PAT" "$REV" -- src \
        | { [ -n "$exclude" ] && grep -vE "$exclude" || cat; } \
        | grep -cE "[Ll]ogger\.($methods)\(" || true
}

ALLM='trace|verbose|debug|info|warning|error|critical|fatal'
TV='trace|verbose'
DBG='debug'
SUPPRESSED='trace|verbose|debug'

echo "cascor rev: $REV  ($(git -C "$CASCOR" rev-parse --short=8 "$REV"))"
echo
printf '%-42s %7s %7s %7s\n' 'population' 'all' 'trace+v' 'debug'
printf '%-42s %7s %7s %7s\n' '------------------------------------------' '-------' '-------' '-------'

E1=''
E2=':src/tests/'
E3=':src/tests/|:src/cascade_correlation/backups/'
E4=':src/tests/|:src/cascade_correlation/backups/|:src/api/'

printf '%-42s %7s %7s %7s\n' 'all tracked src/'                "$(tally "$E1" "$ALLM")" "$(tally "$E1" "$TV")" "$(tally "$E1" "$DBG")"
printf '%-42s %7s %7s %7s\n' 'less src/tests/'                 "$(tally "$E2" "$ALLM")" "$(tally "$E2" "$TV")" "$(tally "$E2" "$DBG")"
printf '%-42s %7s %7s %7s\n' 'less cascade_correlation/backups/' "$(tally "$E3" "$ALLM")" "$(tally "$E3" "$TV")" "$(tally "$E3" "$DBG")"
printf '%-42s %7s %7s %7s\n' 'less src/api/  (= Path A)'       "$(tally "$E4" "$ALLM")" "$(tally "$E4" "$TV")" "$(tally "$E4" "$DBG")"
echo
echo "SUPPRESSED Path-A sites (trace+verbose+debug): $(tally "$E4" "$SUPPRESSED")"
echo
echo "Roadmap §11 / handoff figure: ~872 (census commit 70edfc4)."
