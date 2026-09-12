#!/usr/bin/env bash
# Verify revision 2's CORRECTED gate commands, hermetically.
#
# Project:     Juniper
# Sub-Project: juniper-ml
# Application: util/ad-hoc
# Author:      Paul Calnon
# License:     MIT License
# Created:     2026-09-12
# Status:      ad-hoc -- investigation
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:     notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md
#
# Why
# ---
# Round 2 of consensus found six defects in revision 2's respecified gate commands, including a
# grep character class that refused 100% of trees. The corrections must themselves be verified
# rather than asserted -- that is the whole lesson of this arc.
#
# Operates ONLY on a throwaway repo it creates under a caller-supplied scratch dir. Touches no
# real repository, no worktree, no branch, no stash.

set -uo pipefail

SCRATCH="${1:?usage: verify_respecified_gates.bash <scratch-dir>}"
R="${SCRATCH}/r"
rm -rf "${SCRATCH}"
mkdir -p "${R}"

git init -q "${R}"
git -C "${R}" config user.email t@example.invalid
git -C "${R}" config user.name  t

echo "a" > "${R}/a.txt"
git -C "${R}" add a.txt
git -C "${R}" commit -qm c1
SHA1="$(git -C "${R}" rev-parse HEAD)"

echo "=== 1. update-ref create-only precondition ==="
git -C "${R}" update-ref refs/salvage/20260912/wt/HEAD "${SHA1}" ''
echo "  first write rc=$?  (expect 0)"

echo "b" > "${R}/b.txt"
git -C "${R}" add b.txt
git -C "${R}" commit -qm c2
SHA2="$(git -C "${R}" rev-parse HEAD)"

git -C "${R}" update-ref refs/salvage/20260912/wt/HEAD "${SHA2}" '' 2>/dev/null
echo "  second write (different sha) rc=$?  (expect NON-ZERO)"

NOW="$(git -C "${R}" rev-parse refs/salvage/20260912/wt/HEAD)"
if [[ "${NOW}" == "${SHA1}" ]]; then
    echo "  ANCHOR PRESERVED -- create-only works"
else
    echo "  CLOBBERED -- precondition does NOT work"
fi

echo "=== 1b. control: WITHOUT the precondition it clobbers (the round-2 finding) ==="
git -C "${R}" update-ref refs/salvage/nopre/wt/HEAD "${SHA1}"
git -C "${R}" update-ref refs/salvage/nopre/wt/HEAD "${SHA2}"
echo "  unguarded second write rc=$?  (expect 0 == silent overwrite)"
NOW2="$(git -C "${R}" rev-parse refs/salvage/nopre/wt/HEAD)"
[[ "${NOW2}" == "${SHA2}" ]] && echo "  CLOBBERED as predicted" || echo "  unexpectedly preserved"

echo "=== 2. ls-files -v character class ==="
git -C "${R}" update-index --skip-worktree a.txt
echo "  full ls-files -v:"
git -C "${R}" ls-files -v | sed 's/^/    /'
N_WRONG="$(git -C "${R}" ls-files -v | grep -c '^[SsHh]')"
N_RIGHT="$(git -C "${R}" ls-files -v | grep -c '^[Ssh]')"
TOTAL="$(git -C "${R}" ls-files | wc -l)"
echo "  tracked=${TOTAL}  wrong-class [SsHh]=${N_WRONG}  corrected-class [Ssh]=${N_RIGHT}"
echo "  (expect wrong==tracked, corrected==1 -- only the skip-worktree file)"
git -C "${R}" update-index --no-skip-worktree a.txt

echo "=== 3. rev-parse --git-path resolves per-worktree state ==="
git -C "${R}" worktree add -q "${SCRATCH}/wt_a" -b wta
echo "  from the linked worktree: $(git -C "${SCRATCH}/wt_a" rev-parse --git-path rebase-merge)"
echo "  from the main repo:       $(git -C "${R}" rev-parse --git-path rebase-merge)"
echo "  (expect the first under .git/worktrees/<n>/, the second under .git/)"

echo "=== 4. ABSENT vs PRESENT-BUT-UNREADABLE ==="
git -C "${R}" rev-parse --verify --quiet MERGE_HEAD >/dev/null 2>&1
echo "  absent MERGE_HEAD rev-parse rc=$?  (expect non-zero)"
echo "  its --git-path exists? $( [ -e "$(git -C "${R}" rev-parse --git-path MERGE_HEAD)" ] && echo YES || echo NO )  (expect NO => benign, continue)"

git -C "${R}" worktree remove --force "${SCRATCH}/wt_a" 2>/dev/null
echo "=== done; scratch repo left at ${SCRATCH} ==="
