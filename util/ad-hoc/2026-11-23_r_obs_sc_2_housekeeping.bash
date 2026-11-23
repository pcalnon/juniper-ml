#!/usr/bin/env bash
# =====================================================================================================================
# Project:       juniper-ml
# Sub-Project:   ad-hoc tooling (R-OBS-SC-2 follow-ups: worktree housekeeping on the Overtoad's word)
# Author:        Paul Calnon
# Created:       2026-11-23
# Status:        ad-hoc -- one-off (removes the worktrees and branches the Overtoad approved on 2026-11-23)
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related:       prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md (item 6),
#                prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md (item 7),
#                prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next.md (item 6)
#
# Why: the Overtoad approved, on 2026-11-23 ("Six finished worktrees, data worktree + 4 branches"), removing:
#   * six finished juniper-ml worktrees, whose work is on main (checked file by file, normalized for the blind
#     "owner -> Overtoad" pass of 2026-11-20..22 that rewrote ~2,450 tracked files in each);
#   * the never-opened juniper-data worktree (its uncommitted Retry-After fix is superseded by juniper-data#537);
#   * the juniper-cascor and juniper-canopy primaries' local fix/* branches (PRs #755, #757, #816, #817 merged).
# Nothing is deleted that is not on main or saved first: each worktree's tmp/ is MOVED (same filesystem, a rename)
# into juniper-ml/tmp/worktree-archive-2026-11-23/<name>/, its non-landed files are copied beside it, and its
# ignored files outside tmp/ are listed (and moved too unless they are caches). `git worktree remove` deletes ignored
# files, which is why tmp/ goes first.
#
# Every precondition is re-read at run time; an item whose state moved since the 2026-11-23 probes is SKIPPED.
#
# Usage:  bash util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash            # dry run: prints the plan, changes nothing
#         bash util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash --execute  # does it
# =====================================================================================================================
set -u
# The run of 2026-11-23T20:45:52Z (tmp/housekeeping/execute_2026-11-23.txt in worktree curried-frolicking-boot) spelled
# this path as a literal; it is derived from $HOME here for gate G5 (decision D12). The value is the same on that host.
J="$HOME/Development/python/Juniper"
ML=$J/juniper-ml
ARCH=$ML/tmp/worktree-archive-2026-11-23
EXEC=0
[[ "${1:-}" == "--execute" ]] && EXEC=1
run() {  # echo, and run only under --execute
  echo "    + $*"
  if [[ $EXEC -eq 1 ]]; then "$@" || { echo "    !! FAILED: $*"; return 1; }; fi
}
holders() {
  local d=$1 out="" p c
  for p in /proc/[0-9]*; do
    c=$(readlink "$p/cwd" 2>/dev/null) || continue
    case "$c" in "$d"|"$d"/*) out+="${p#/proc/} ";; esac
  done
  printf '%s' "$out"
}
is_registered() {  # $1 repo, $2 worktree path
  git -C "$1" worktree list --porcelain | command grep -qx "worktree $2"
}
is_locked() {
  git -C "$1" worktree list --porcelain | awk -v w="worktree $2" '$0==w{f=1;next} /^worktree /{f=0} f && /^locked/{print "locked"}' | command grep -q locked
}
CACHE_RE='(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.hypothesis|.*\.egg-info|\.coverage.*|htmlcov)/?$'

# name | expected HEAD (8) | expected untracked count | files to save (tracked non-residue + differing drafts), ';'-separated
WTS=(
  "logical-percolating-sparkle|9238be21|1|tests/test_service_fork_drift.py;util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py"
  "foamy-squishing-floyd|7ae846b6|1|prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md"
  "toasty-prancing-karp|4a786c81|1|tests/test_service_fork_drift.py;util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py;prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md"
  "agent-a4c8d9de35bfc0d67|0578d2ec|1|.github/workflows/ci.yml;CHANGELOG.md;docs/REFERENCE.md"
  "buzzing-growing-whale|a949d504|6|docs/QUICK_START.md"
  "humble-humming-flask|91e16a50|25|"
)
echo "mode: $([[ $EXEC -eq 1 ]] && echo EXECUTE || echo DRY-RUN)   archive: ${ARCH}   $(date -u +%FT%TZ)"
[[ $EXEC -eq 1 ]] && mkdir -p "$ARCH"
summary=()
for spec in "${WTS[@]}"; do
  IFS='|' read -r name head_exp unt_exp saves <<< "$spec"
  wt=$ML/.claude/worktrees/$name
  echo "== $name"
  if [[ ! -d "$wt" ]]; then echo "  SKIP: absent"; summary+=("$name: absent"); continue; fi
  if ! is_registered "$ML" "$wt"; then echo "  SKIP: not a registered juniper-ml worktree"; summary+=("$name: SKIP unregistered"); continue; fi
  if is_locked "$ML" "$wt"; then echo "  SKIP: locked"; summary+=("$name: SKIP locked"); continue; fi
  h=$(holders "$wt"); if [[ -n "$h" ]]; then echo "  SKIP: processes inside: $h"; summary+=("$name: SKIP in use"); continue; fi
  head=$(git -C "$wt" rev-parse --short=8 HEAD)
  if [[ "$head" != "$head_exp" ]]; then echo "  SKIP: HEAD moved ($head, probed $head_exp)"; summary+=("$name: SKIP head moved"); continue; fi
  unt=$(git -C "$wt" status --porcelain --untracked-files=all | command grep -c '^??')
  if [[ "$unt" != "$unt_exp" ]]; then echo "  SKIP: untracked count $unt, probed $unt_exp"; summary+=("$name: SKIP untracked moved"); continue; fi
  branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD)
  remote=$(git -C "$ML" ls-remote --heads origin "$branch" | cut -c1-8)
  dest=$ARCH/$name
  echo "  branch=$branch head=$head untracked=$unt remote-branch=${remote:-none}"
  # ignored entries outside tmp/
  ign=$(git -C "$wt" ls-files --others --ignored --exclude-standard --directory | command grep -v -E '^tmp/?$')
  keep_ign=$(printf '%s\n' "$ign" | command grep -v -E "$CACHE_RE" | command grep -v '^$' || true)
  echo "  ignored outside tmp/: $(printf '%s\n' "$ign" | command grep -c . ) entries; non-cache: $(printf '%s\n' "$keep_ign" | command grep -c . )"
  printf '%s\n' "$keep_ign" | command grep . | sed 's/^/      keep: /' | head -20
  [[ $EXEC -eq 1 ]] && mkdir -p "$dest/saved" "$dest/ignored"
  if [[ $EXEC -eq 1 ]]; then
    {
      echo "worktree: .claude/worktrees/$name"; echo "branch: $branch"; echo "head: $(git -C "$wt" rev-parse HEAD)"
      echo "remote branch: ${remote:-none}"; echo "archived: $(date -u +%FT%TZ) by util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash"
      echo "note: this worktree's tracked files, untracked files and tmp/ were rewritten by the blind owner->Overtoad pass"
      echo "      of 2026-11-20..22; tmp/ and saved/ hold that rewritten text, not the original. The original text of"
      echo "      landed files is on juniper-ml main; session transcripts hold the rest."
      echo "tracked diff stat vs HEAD: $(git -C "$wt" diff HEAD --shortstat)"
    } > "$dest/MANIFEST.txt"
  fi
  IFS=';' read -r -a files <<< "$saves"
  for f in "${files[@]}"; do
    [[ -z "$f" ]] && continue
    echo "  save: $f"
    if [[ $EXEC -eq 1 ]]; then mkdir -p "$dest/saved/$(dirname "$f")" && cp -a "$wt/$f" "$dest/saved/$f" && sha256sum "$dest/saved/$f" | sed "s#$dest/##" >> "$dest/MANIFEST.txt"; fi
  done
  while IFS= read -r e; do
    [[ -z "$e" ]] && continue
    e=${e%/}
    if [[ $EXEC -eq 1 ]]; then mkdir -p "$dest/ignored/$(dirname "$e")"; fi
    run mv "$wt/$e" "$dest/ignored/$e"
  done <<< "$keep_ign"
  if [[ -d "$wt/tmp" ]]; then
    echo "  tmp/: $(du -sh "$wt/tmp" | cut -f1)"
    run mv "$wt/tmp" "$dest/tmp" || { summary+=("$name: FAILED moving tmp"); continue; }
  fi
  run git -C "$ML" worktree remove --force "$wt" || { summary+=("$name: FAILED worktree remove"); continue; }
  if [[ -z "$remote" ]]; then
    run git -C "$ML" branch -D "$branch" || summary+=("$name: branch delete failed")
  else
    echo "  remote branch exists: local branch kept"
  fi
  summary+=("$name: $([[ $EXEC -eq 1 ]] && echo removed || echo would remove)")
done

echo "== juniper-data never-opened worktree"
JD=$J/juniper-data
DW=$J/worktrees/juniper-data--fix--rate-limit-retry-after-round-up--20261111-1855--399eeffb
DB=fix/rate-limit-retry-after-round-up
if [[ -d "$DW" ]] && is_registered "$JD" "$DW" && [[ -z "$(holders "$DW")" ]] && [[ "$(git -C "$DW" rev-parse --short=8 HEAD)" == 399eeffb ]] \
   && [[ "$(git -C "$DW" status --porcelain --untracked-files=all | wc -l)" == 4 ]] && ! is_locked "$JD" "$DW"; then
  ddest=$ARCH/$(basename "$DW")
  echo "  save: the uncommitted diff (3 files) as a patch and the untracked test, to ${ddest#"$ML"/}"
  echo "  ignored entries: $(git -C "$DW" ls-files --others --ignored --exclude-standard --directory | command grep -c .)"
  if [[ $EXEC -eq 1 ]]; then
    mkdir -p "$ddest/saved"
    git -C "$DW" diff HEAD > "$ddest/saved/uncommitted.patch"
    git -C "$DW" ls-files --others --exclude-standard -z | while IFS= read -r -d '' u; do mkdir -p "$ddest/saved/$(dirname "$u")"; cp -a "$DW/$u" "$ddest/saved/$u"; done
    { echo "worktree: $DW"; echo "branch: $DB at $(git -C "$DW" rev-parse HEAD)"; echo "superseded by juniper-data#537 (merged 2026-11-13T02:54:07Z)"
      echo "archived: $(date -u +%FT%TZ)"; (cd "$ddest" && find saved -type f -exec sha256sum {} +); } > "$ddest/MANIFEST.txt"
  fi
  run git -C "$JD" worktree remove --force "$DW" && run git -C "$JD" branch -D "$DB"
  summary+=("juniper-data worktree: $([[ $EXEC -eq 1 ]] && echo removed || echo would remove)")
else
  echo "  SKIP: state moved since the probe (absent, unregistered, in use, locked, HEAD or status changed)"
  summary+=("juniper-data worktree: SKIP")
fi

echo "== primaries' merged local branches"
declare -A BR=(
  ["juniper-cascor fix/fastapi-telemetry-opt-out"]=b9167bdc ["juniper-cascor fix/rate-limit-retry-after-round-up"]=5834709a
  ["juniper-canopy fix/fastapi-telemetry-opt-out"]=ee265fde ["juniper-canopy fix/rate-limit-retry-after-round-up"]=b9417b2f
)
for key in "${!BR[@]}"; do
  read -r repo b <<< "$key"
  sha=$(git -C "$J/$repo" rev-parse --short=8 "refs/heads/$b" 2>/dev/null || echo absent)
  inwt=$(git -C "$J/$repo" worktree list --porcelain | command grep -c "^branch refs/heads/$b$")
  if [[ "$sha" == "${BR[$key]}" && "$inwt" == 0 ]]; then
    echo "  $repo $b at $sha (full $(git -C "$J/$repo" rev-parse "refs/heads/$b"))"
    if [[ $EXEC -eq 1 ]]; then echo "$repo $b $(git -C "$J/$repo" rev-parse "refs/heads/$b")" >> "$ARCH/deleted_branches.txt"; fi
    run git -C "$J/$repo" branch -D "$b"
    summary+=("$repo $b: $([[ $EXEC -eq 1 ]] && echo deleted || echo would delete)")
  else
    echo "  SKIP $repo $b: sha=$sha (probed ${BR[$key]}), checked out in $inwt worktree(s)"
    summary+=("$repo $b: SKIP")
  fi
done
if [[ $EXEC -eq 1 ]]; then
  run git -C "$ML" worktree prune
  run git -C "$JD" worktree prune
fi
echo "== summary"
printf '  %s\n' "${summary[@]}"
