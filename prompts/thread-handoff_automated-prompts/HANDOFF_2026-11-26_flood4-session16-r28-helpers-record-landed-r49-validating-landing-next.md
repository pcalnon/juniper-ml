# Handoff: flood-4 session 16 -- r28 (juniper-canopy#845), the helpers (#2675) and the record (#2677) landed; ruling 49 built and validated, one question for the Overtoad; r49's landing next

**Date**: 2026-11-26 (written 13:58Z UTC; session 16 ran from 2026-11-26 11:35Z)

**Arc**: the Cursor flood-4 disposition, session 16, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (EnterWorktree'd from
`rippling-dazzling-owl`; session b5d6f8ae). It continues
`HANDOFF_2026-11-26_flood4-session15-r27-r23w-landed-r28-validating-helpers-record-next.md` (on main via #2672).

**The running log is the detail**: `tmp/flood4/session16/STATE_S16.txt` (UTC from `date -u`). Session 16's carrier,
lenses and briefs are under `tmp/flood4/session16/` (briefs/, r49/, r49-val-code/, r49-val-claims/, rec/, rec_land/,
helpers_pr/); r28's landing files are under `tmp/flood4/session14/land/r28/`.

**Merge approval**: session 16's dialog: "Merge approval granted"; then the Overtoad typed "merge approval granted for
this work arc" (2026-11-26 11:49Z). Ask again in session 17 if unsure; the typed approval names the whole arc.
**Agent load**: "Opus, 2 at a time" (2026-11-14).

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_flood4-session16-r28-helpers-record-landed-r49-validating-landing-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session16/STATE_S16.txt.

Done in session 16 (verified on GitHub):
- juniper-canopy#845 (r28, ruling 28) MERGED 2026-11-26T12:35:32Z as 374c0fb9 (armed net); the Allow-Symbol-Loss line
  reached main's squash message and canopy's Post-Merge Main Verification passed on 374c0fb9. 35 lens fixes applied
  (2 overlaps hand-merged); CI's 3.12 lane on aa9ac734 + r28: 8540 passed, 0 failed, 96.86%, gate PASS; the final file
  300/300 x2 on 3.13 (with/without GC load), 60/60 3.12 (load), 60/60 3.14 (no load); M1 50/50 FAIL both ways.
- juniper-ml#2675 (rulings 27 + 28's 53 helpers) MERGED 13:26:32Z as bac6848e, after a fix-up (22ec2f74) for two
  CodeQL threads (alerts 1142 py/overly-permissive-file, 1143 py/file-not-closed) on r27-val-code2_census.py:67.
- juniper-ml#2677 (the record update, notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md: rulings
  7's answers, 23, 26-28's PRs, new RULING 49, session 16's approvals, Still open) MERGED 2026-11-26T13:58:08Z as
  89e876d2 (armed net).
- RULING 49 (Overtoad, 2026-11-26 11:49Z, "Separate follow-up PR (Recommended)"): canopy's
  test_health_stays_fast_while_upstream_is_slow (src/tests/regression/test_x7_loop_responsiveness.py) gets ruling 28's
  kind of fix in its own canopy PR, with its own builder and two lenses. BUILT: tmp/flood4/session16/r49/final/
  (CHANGELOG.md, docs/AGENTS_REFERENCE.md, the test file; base aa9ac734; texts/ incl. symbol_loss_waiver.txt).
  Claims lens DONE: 0/0/5 MINOR/6 NIT, fixes.json 16 (r49-val-claims/). Code lens DONE 13:40Z: SHIP-WITH-FIXES,
  0/0/1 MINOR/3 NIT, fixes.json 3 (C1-C3) + C4 (the waiver line into the commit body); lane 8540 passed on
  3.12/3.13/3.14, flakes 0/1200, old failure reproduced on main and gone. No agent of session 16 is running.

Remaining, in order:
0. ASK THE OVERTOAD before landing r49 (start the fix pass, clone and lane first; a dialog blocks the session). The
   code lens found the new test kills 8 of 12 mutants where main's wall-clock test killed 12. Survivors: a time.sleep
   in the health route, one in /api/status before it offloads, one in the middleware, a 0.5 s timeout around the
   offload; the whole unit lane with the first two applied still passes 8540/8540. Its C1 corrects the docstring's
   false claim that the structural gate covers them (the gate reads main.py only and ignores time.sleep). An optional
   prototype, tmp/flood4/session16/r49-val-code/proto_loop_only_watchdog.diff, kills those stalls without failing on
   whole-process stops but brings back a time limit, against ruling 49's "no 1 s wall-clock bound". Put: land as
   ruled with C1's honest docstring (the gap stated), or adopt the watchdog (then a lens round on it), or other.
1. Land r49 exactly as r28 was landed (STATE_S16.txt 11:37-12:36Z; files under tmp/flood4/session14/land/r28/):
   land dir tmp/flood4/session16/land/r49/; work = r49/final + texts/; fixes: code lens first, then claims
   (util/ad-hoc/2026-11-25_flood4_s14_fixpass.py; overlaps by hand; util/ad-hoc/2026-11-26_flood4_s16_show_fixes.py
   prints fixes by id); CHANGELOG three-way onto canopy main (374c0fb9 or later) with r49's entry ABOVE #845's;
   fresh clone; CI's 3.12 unit lane (r27v2 runner + census) and the changed file x50 with and without
   util/ad-hoc/2026-11-25_flood4_s14_r28_load_plugin.py; M1 x50; pinned pre-commit; prescreen + helpers_check;
   gitleaks (util/ad-hoc/2026-11-09_flood4r2_land_gitleaks.py, canopy's .gitleaks.toml, main baseline); seqsafety
   probe WITH the waiver in the commit message (trailer block, before Co-Authored-By); unwrap the PR body
   (util/ad-hoc/2026-11-26_flood4_s15_unwrap_pr_body.py) + attribution; util/open_signed_pr.py --repo juniper-canopy;
   verify_pr_blobs; safe_merge (python3 -u; read the MERGED line); main-verify on the merge commit.
2. One juniper-ml PR for r49's helpers: the builder's 10 + both lenses' (util/ad-hoc/2026-11-26_flood4_s16_r49*), with
   helpers_check, prescreen, G-TMP, pinned pre-commit, gitleaks; and BY HAND: no os.open/chmod with a mode wider than
   0o600, no fd kept open (the two rules #2675 met that no tool here models).
3. A small record update: ruling 49's PR and the r49 helpers PR (§8 ruling 49, Still open, §7, §9).
4. S cleanup after each PR lands: prove S's untracked copies equal main's blobs (git ls-tree origin/main + a local
   blob hash), remove them, fast-forward S. #2675's 53 were done in session 16 (53/53 == main's blobs; S
   fast-forwarded bceac63c -> bac6848e), and #2677's helper too (== main's blob d225923f; S -> 89e876d2). Pending:
   this handoff's file once its PR lands, then r49's helpers after item 2.
5. Ruling 7's run stays the Overtoad's (commands in session 13's handoff; pid 39566 still holds humming).
```

## Key context (traps met in session 16)

- **A live Juniper stack** has run from the PRIMARY checkouts since 2026-11-26 11:53Z (canopy :8050 from
  JuniperCanopy1, juniper-data :8100, cascor :8201, a cascor worker :8210; parent systemd --user). Not this arc's: never
  touch it. `util/ad-hoc/2026-11-25_flood4_s14_r28_run_lane.py` REFUSES to start while a Juniper port listens (no
  switch); run canopy tests through `util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py` with its census,
  which refuses every Juniper-port connect in pytest and its children. canopy's own guard arms unit/ regression/
  contract/ performance/.
- **CodeQL rules nothing here predicts**: py/overly-permissive-file (os.open mode 0o644) and py/file-not-closed for an
  os.open fd kept open; and the prescreen misses py/import-and-import-from and py/catch-base-exception
  (`util/ad-hoc/2026-11-26_flood4_s16_helpers_check.py` covers those two). After fixing, wait for the alert to read
  `fixed` on refs/pull/N/merge, resolve each thread (GraphQL resolveReviewThread), re-run safe_merge.
- **safe_merge exits 0 on a REFUSAL** (unresolved threads): read its last line. A busy main re-syncs the branch
  (GitHub-signed merge commits); three BEHIND cycles refuse.
- **py312/py314 venvs lack pytest-repeat**: repeat with the runner's `--count` (separate processes). On 3.14 the
  synthetic GC load pushes the first FastAPI/pydantic import past pytest-timeout's 60 s: a load limit, not a result.
- **The isolation guard** refuses compound commands, inline Python with dict comprehensions, `git merge-file -L`
  labels (read as paths) and a gh api path with /git/. A juniper-ml clone fails on a git-lfs smudge: finish with
  `GIT_LFS_SKIP_SMUDGE=1 git -C <clone> reset --hard HEAD`.
- **Stamps from `date -u` only**: session 16 wrote two estimated stamps and corrected them.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -30 tmp/flood4/session16/STATE_S16.txt
gh pr view 845 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'
gh pr view 2675 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'
gh pr view 2677 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + ((.mergeCommit.oid // "-")[0:8])'
ls tmp/flood4/session16/r49-val-code/ tmp/flood4/session16/r49-val-claims/   # findings.txt / fixes.json / REPORT.txt?
(cd tmp/flood4/session16/r49/final && sha256sum -c --quiet ../final.sha256) && echo "r49 carrier intact"
ss -ltnp | grep -E ':(805[0-9]|8100|820[0-9]|821[01])\b'   # the live stack: still up?
```

## Git status

- Orchestrator worktree: branch `worktree-hidden-scribbling-toast`, HEAD `89e876d2` (#2677; no tracked edits).
  Untracked: r49's helpers (`util/ad-hoc/2026-11-26_flood4_s16_r49*`: the builder's 10 and both
  lenses'), this handoff (until its PR lands), and the ignored `tmp/flood4/`.
- `curious-plotting-hummingbird` is DO NOT SWEEP; never run `util/remove_stale_worktrees.bash`; never touch a primary.

## Documents created or modified in session 16

- **juniper-canopy#845 (MERGED, 374c0fb9)**: `CHANGELOG.md`, `src/tests/regression/test_x7_sites_outside_main_gate.py`.
- **juniper-ml#2675 (MERGED, bac6848e)**: 53 `util/ad-hoc/` helpers (r27's 25, r28's 26, and
  `2026-11-26_flood4_s16_{show_fixes,helpers_check}.py`); four r27 lens helpers edited before landing
  (`2026-11-25_flood4_s14_r27-val-code2_{bypass_probe,census,junit}.py`, `2026-11-25_flood4_s14_r27-val-code_fence.py`)
  and the census again in fix-up 22ec2f74.
- **juniper-ml#2677**: `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, `CHANGELOG.md`,
  `util/ad-hoc/2026-11-26_flood4_s16_rec_build_fixes.py`.
- **This handoff**, on its own pull request.
- **Outside the repositories**: memory `reference_codeql_unused_global_cascor.md` (a 2026-11-26 paragraph).
- **Uncommitted**: `tmp/flood4/session16/` (STATE_S16.txt, briefs/, r49*, rec*, helpers_pr/, attribution files) and
  `tmp/flood4/session14/land/r28/`.
