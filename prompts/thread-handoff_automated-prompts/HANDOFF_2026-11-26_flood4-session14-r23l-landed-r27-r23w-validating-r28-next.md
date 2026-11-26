# Handoff: flood-4 session 14 -- ruling 23's lifecycle races landed (#2664); r27 and r23w built and in validation; r28 next

**Date**: 2026-11-26 (written ~00:50Z UTC; session 14 ran from 2026-11-25 20:11Z)

**Arc**: the Cursor flood-4 disposition, session 14, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (launched in
`structured-foraging-origami`, then EnterWorktree'd here; ListAgents name `structured-foraging-origami-4d` [ffffe5]).
It continues `HANDOFF_2026-11-25_flood4-session13-ruling-7-script-landed-owner-runs-it-rulings-23-27-28-next.md`
(on main via #2660).

**The running log is the detail**: `tmp/flood4/session14/STATE_S14.txt` (UTC from `date -u`). Briefs:
`tmp/flood4/session14/briefs/` (`COMMON_S14.txt` binds every agent; `B23L`, `B23W`, `B27`, `B28` builders;
`V_CODE_S14.txt`, `V_CLAIMS_S14.txt` lens templates). Sources copied out of humming: `tmp/flood4/session14/sources/`.

**Merge approval**: the Overtoad's message in session 14: "merge approval granted". Ask again in session 15.
**Agent load**: "Opus, 2 at a time" (2026-11-14).

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_flood4-session14-r23l-landed-r27-r23w-validating-r28-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session14/STATE_S14.txt. Ask the Overtoad for this session's
merge approval. Before any Overtoad dialog, start what can run.

Done in session 14 (verified on GitHub):
- #2659 and #2660 confirmed merged. Ruling 7's run NOT done yet (no archive dir; pid 39566 still sits in humming).
- Ruling 23 "Lifecycle races beside N-2" = juniper-ml#2664, MERGED 2026-11-25T23:44:03Z as 82ccd7c5 (signed
  e5261c1c, blobs 24/24): one helper _refuse_while_a_stopped_fit_runs (start_training, all four loads, attach_model);
  a load ends a leftover replay session; stop_replay resets/relabels only from REPLAYING. Code lens SHIP-WITH-FIXES
  (0/0/2/3), claims lens 0/0/3/14; 26 of 29 fixes applied. 17 helpers rode it.
- r27 (canopy :8100, ruling 27) BUILT: tmp/flood4/session14/r27/final/ (7 files; base canopy 60880efc); claims lens
  DONE (0 BLOCKER, 0 MAJOR, 4 MINOR, 8 NIT; 13 fixes, dry run WOULD 13/13 on tmp/flood4/session14/land/r27/work).
- r23w (WebSocket gaps beside N-4, ruling 23) BUILT on 82ccd7c5: tmp/flood4/session14/r23w/final/.

In flight when session 14 ended (they write to disk; they die if session 14's process is closed):
- r23w CODE LENS -> tmp/flood4/session14/r23w-val-code/ (launched ~00:23Z).
- r27 CODE LENS #2 -> tmp/flood4/session14/r27-val-code2/ (launched 00:45Z; replaces r27-val-code/, which stalled).
FIRST check each: findings.txt + fixes.json + REPORT.txt present = done. If not, and no file in it is newer than
~20 min, launch a replacement that finishes from its files (model: tmp/flood4/session14/briefs/R27_VAL_CODE2_replacement_prompt.txt).

Remaining, in order:
1. Land r27: apply tmp/flood4/session14/r27-val-claims/fixes.json + r27-val-code2/fixes.json to land/r27/work with
   util/ad-hoc/2026-11-25_flood4_s14_fixpass.py (dry run first; resolve overlaps by hand); re-run the changed canopy
   tests and the unit lane once on 3.12 in a fresh clone (CI-like child env, below); if canopy main moved past
   60880efc, three-way CHANGELOG.md and re-derive TESTING_REFERENCE.md's stamp (v0.26.5 now); freeze; pinned pre-commit;
   CodeQL prescreen; gitleaks dir with main's baseline; util/open_signed_pr.py --repo juniper-canopy; verify blobs
   (util/ad-hoc/2026-11-23_flood4_s10_verify_pr_blobs.py --repo juniper-canopy); safe_merge (python3 -u). Model:
   tmp/flood4/session14/land/r23l/ and STATE_S14.txt 23:00-23:28Z.
2. r23w: CLAIMS lens (V_CLAIMS_S14.txt + a header like r23l's in STATE_S14.txt), then land like r23l (three-way the
   three shared documents and re-derive REFERENCE's stamp if main moved past 82ccd7c5; its lens helpers ride it).
   Open question it carries: under uvicorn's default websockets-sansio and wsproto a stalled dropped client now holds
   its per-IP slot as long as its connection lasts (>45 s); bounding it is outside ruling 23 -- say so in the texts,
   and ask the Overtoad only if a lens calls it a defect of this PR.
3. r28 (canopy relay test, ruling 28): builder from briefs/B28_canopy_relay_test_builder.txt (if r27 has landed, tell
   it to build on that main), two lenses, land.
4. One juniper-ml PR for the canopy carriers' juniper-ml helpers (r27's 16 untracked in S now, r28's later; each
   checked against its carrier first).
5. The record update (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md): session 13's list
   (its handoff item 4) plus #2664, r27, r23w, r28 and the helpers PR; section 8's "Still open" bullets for rulings 23,
   27, 28 and ruling 7.
6. Ruling 7's run stays the Overtoad's (commands in session 13's handoff; --held archive).
```

## Key context (traps met in session 14)

- **A DNS outage (`EAI_AGAIN`) killed both builders at ~21:00Z**; SendMessage to each agent id resumed it from its own
  transcript, told to `ps` for its own processes first. Both then finished.
- **A lens can stall silently**: r27-val-code wrote nothing for 2.5 h (no process alive, no findings, ListAgents still
  "running"). Watch file mtimes; TaskStop it and launch a replacement that finishes from its files, read-only.
- **git-lfs smudge fails** on a fresh juniper-ml clone ("batch response: Bad credentials"): check out with
  `GIT_LFS_SKIP_SMUDGE=1 git -C <ABSOLUTE path> reset --hard HEAD`.
- **The isolation refuses** `git -C <relative path>`, and any command whose text contains "git" (also "gitleaks",
  ".github") with a chain, pipe, loop or `$(...)`: use absolute paths and one plain git command per call.
- **This shell's LD_LIBRARY_PATH names a foreign libtorch**: canopy's pytest dies at collection (undefined symbol
  _PyCode_SetExtra) unless the child env drops LD_LIBRARY_PATH/PYTHONPATH (r27-val-code's runner does).
- **The s13 fixpass helper keys by basename** (cannot tell two CHANGELOG.md apart): use
  `util/ad-hoc/2026-11-25_flood4_s14_fixpass.py` (repo-relative; `--dry-run`; `--skip ID`).
- **safe_merge clamps `--timeout` to 3300 s**; the armed auto-merge net completed #2664 anyway.
- **The seqsafety probe** is `git commit-tree --no-gpg-sign` (commit.gpgsign=true here): dangling, never pushed. CI's
  symbol-loss scopes are `tests/*.py`, `util/**/*.py`, `util/**/*.bash`.
- **Write timestamps from `date -u`**: session 14 had to correct eight estimated log stamps.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -30 tmp/flood4/session14/STATE_S14.txt
gh pr view 2664 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + ((.mergeCommit.oid // "-")[0:8])'
ls tmp/flood4/session14/r23w-val-code/ tmp/flood4/session14/r27-val-code2/      # findings.txt / fixes.json / REPORT.txt?
(cd tmp/flood4/session14/r27/final && sha256sum -c --quiet ../final.sha256) && echo "r27 carrier intact"
ls ~/Development/python/Juniper/juniper-ml/tmp/worktree-archive-2026-11-24-flood4/ 2>/dev/null | head   # ruling 7 run?
```

## Git status

- Orchestrator worktree: branch `worktree-hidden-scribbling-toast`, HEAD `82ccd7c5` (fast-forwarded from `3b99d974`
  after the 17 helper copies were proven equal to main's blobs and removed; one, the pre-K5 mutation helper, is kept in
  `tmp/flood4/session14/r23l/final/`). No tracked edits. Untracked: this handoff (until its PR lands), r23w's 2 and
  r27's 16 helpers under `util/ad-hoc/` (plus whatever the running lenses add), and the ignored `tmp/flood4/session14/`.
- `curious-plotting-hummingbird` is DO NOT SWEEP; never run `util/remove_stale_worktrees.bash`; never touch a primary.

## Documents created or modified in session 14

- **juniper-ml#2664 (MERGED, 82ccd7c5)**: `juniper-service-core/juniper_service_core/lifecycle/manager.py`,
  `juniper-service-core/tests/test_lifecycle_{stop_then_start,stop_then_load,leftover_replay_session}.py`,
  `juniper-service-core/CHANGELOG.md`, `CHANGELOG.md`, `docs/REFERENCE.md` (0.6.84), and 17 `util/ad-hoc/` helpers:
  `2026-11-25_flood4_s14_r23l_{probe,probe_summary,mutation_check,flake,coverage_diff,reader_suites,prfilter,manifest}.py`,
  `2026-11-25_flood4_s14_r23l-val-code_{probe,mutants,flake,fixes_check}.py`,
  `2026-11-25_flood4_s14_r23l-val-claims_{http_answers,http_compare,method_diff,fixes_check}.py`,
  `2026-11-25_flood4_s14_fixpass.py`.
- **This handoff**, on its own pull request.
- **Uncommitted**: `tmp/flood4/session14/` (STATE_S14.txt, runenv.bash, briefs/, sources/, dialog extracts, the four
  carriers, the lenses' outputs, land/r23l/ and land/r27/), and the untracked helpers listed under Git status.
