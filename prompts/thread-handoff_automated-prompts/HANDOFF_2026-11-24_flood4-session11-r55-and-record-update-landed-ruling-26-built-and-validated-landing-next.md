# Handoff: flood-4 session 11 -- R55 (juniper-ml#2631) and the record update (rulings 15-48, R54; juniper-ml#2635) landed; ruling 26's six ports built and validated, their landing next

**Date**: 2026-11-24 (written ~15:00Z UTC; finished after juniper-ml#2635 merged at 14:51:35Z)

**Arc**: the Cursor flood-4 disposition, session 11, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (ListAgents name
`flood4-session10-d14-pair-landed-guard-1-4-0-landing-record-next` [17d26a]). It continues
`HANDOFF_2026-11-24_flood4-session10-d14-pair-landed-guard-1-4-0-landing-record-next.md` (on main via #2626).

**The running log is the detail**: `tmp/flood4/session11/STATE_S11.txt` in the orchestrator worktree (UTC from `date -u`;
the Overtoad's words verbatim). Briefs: `tmp/flood4/session11/briefs/` (R1 drafter, V1/V2 record lenses, B26 builder, V26
port lenses).

**Merge approval**: the Overtoad's first message of session 11: "merge approval granted for this session and work arc".
The arc's convention is that each session asks again; ask whether "and work arc" carries over. **Agent load**: "Opus, 2 at
a time" (the Overtoad's ruling of 2026-11-14). **No agent is running.**

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_flood4-session11-r55-and-record-update-landed-ruling-26-built-and-validated-landing-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session11/STATE_S11.txt. Ask the Overtoad for this session's
merge approval (session 11's was "for this session and work arc"). Before any Overtoad dialog, start what can run.

Done in session 11 (verified on GitHub):
- R55 = flood-4 ruling 48: juniper-ml#2631 MERGED 13:06:28Z as 9a9ef3fb (the compatibility paragraph states the rule
  ReferenceCompatibilityMatrixTest enforces; one test pins it; mutation-checked). [007878] (R-OBS-SC-2) told.
- The owed Dependabot reads: done from the scan logs (ml#2598, data-client#265, cascor-client#200, data#546/#549; data#544's
  Dependabot run was cancelled by a lockfile commit). All eight ported repos read on a Dependabot event.
- Cheatsheet item: no change (docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:1297's "1.3.0" is still true of guard 1.4.0, probed).
- Provenance: sessions 5-9's 383 helpers and 10 handoffs are on main; session 10's 16 ride #2635.
- R54, the record update: juniper-ml#2635 (branch docs/flood4-record-rulings-15-48): notes/JUNIPER_2026-11-06_JUNIPER-
  ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 gains rulings 15-48 (ruling 17 one ruling over four fixes), rulings
  1-14's outcomes, Still open; + CHANGELOG + 30 helpers. Drafted, then two lenses (claims 1/10/3, document 2/9/24), all
  merged. CodeQL alert 1131 (py/overly-permissive-file, a session-10 helper's chmod 0o644) fixed in b53131a7.
  MERGED 2026-11-24T14:51:35Z as 0a7c602c. [007878] (R-OBS-SC-2: inventory :170 stale) and [ffffd3] (one-artifact
  line, keeps the consolidated plan: :120 and :1159 stale) told. OWED READ: main's push-time Symbol & Docs Screen on
  0a7c602c (in progress at 14:55Z).
- Ruling 26 (port juniper-canopy#814's lockfile-print fix to juniper-data, juniper-cascor, juniper-data-client,
  juniper-cascor-client, juniper-cascor-worker + canopy's CICD_MANUAL.md:796 line): all six BUILT (B26) and VALIDATED
  (V26-code: all SHIP-WITH-FIXES, 0/0/2; V26-claims: all SHIP-WITH-FIXES, 0/2/8). Nothing pushed. tmp/flood4/session11/r26/.

Remaining, in order:
1. Read main's push-time 'Symbol & Docs Screen' on 0a7c602c (#2635's merge); a red one needs a fix PR.
2. Land ruling 26's six PRs. Fix pass first, on each repo's frozen set (tmp/flood4/session11/r26/<repo>/final/):
   - val_code/fixes.json T1a-T1g (pre-commit 4.6.0, not 4.5.1) and val_claims/fixes.json T1-T10 (T1-* only once #2635
     merged: "lists it as ruling 26 in its section 8"; T2 option (a), recommended: add juniper-data's
     docs/ci_cd/CICD_REFERENCE.md row v0.1.1 + its stamp 0.4.8 -> 0.4.9; T9 optional);
   - C1 (val_code/code_fixes_proposed.json): two ::error:: assertions per repo, proven; recommended: adopt, re-run
     util/ad-hoc/2026-11-24_flood4_s11_r26_proof.py, refresh final.sha256.
   Then per repo: re-check main = base.txt (rebuild if moved), secret scan, util/open_signed_pr.py (or the s10
   open_pr_from_paths helper, --repo juniper-<x>), verify blobs, util/safe_merge.py --execute; read MERGED.
3. A juniper-ml provenance PR for ruling 26's helpers: util/ad-hoc/2026-11-24_flood4_s11_{r26_proof,v26_code_*,
   v26_claims_*}.py. FIRST change the 0o755 chmod in v26_code_{bash32,steprun}.py to 0o700 (CodeQL, as #2635 showed).
4. Ruling 7's cleanup ("All, after record merges"; the record merged, so it may start): 151 flood4 worktrees under Juniper/worktrees/
   plus carriers/agents under .claude/worktrees/. Archive each tmp/ first, as R-OBS-SC-2 did
   (juniper-ml/tmp/worktree-archive-2026-11-23/: README, per-worktree MANIFEST.txt, tmp/ moved, saved/ for files not on
   main). Inventory and plan first; scale suggests showing the Overtoad the plan. humming-stargazing-papert holds round 2's
   triage + sessions 1-9's logs: archive it last.
5. The other 2026-11-12 follow-ups (transcript f2b4e7c3, STATE_S6.txt:51-90): ruling 23's two service-core PRs ("WebSocket
   gaps beside N-4": an unserialisable broadcast closes every socket, /ws/control's post-close crash, the per-IP slot
   freed early; "Lifecycle races beside N-2": stop-then-LOAD, a leftover replay session's stop resets a running run);
   ruling 27 (canopy: 124 unit tests in 38 files connect to :8100; mock the data client at startup, add 8100 to the
   guard); ruling 28 (canopy's load-sensitive test_relay_cascade_add_does_not_block_the_loop). Build, two lenses, land.
6. The next record update: ruling 26's PRs and session 11-12's outcomes.
```

## Key context (traps met in session 11)

- **The worktree screen refuses a Bash command whose text holds "git" in a complex form**: a heredoc that says GitHub or
  names the secret-scan engine, or `$(cat list)` beside the engine's path. Split commands; keep log text free of them.
- **main moves under a frozen set**: #2633 landed a CHANGELOG entry between the freeze and the upload, and the whole-file
  CHANGELOG would have reverted it. Rebuild on the new main; for a fix commit on a PR branch after update-branch, edit the
  BRANCH's copies (`git show FETCH_HEAD:<path>`), never the local ones.
- **The CodeQL prescreen cannot see py/overly-permissive-file** (a literal 0o644 / 0o755 in chmod). Grep helpers for
  chmod literals before upload.
- **safe_merge**: its thread probe failed open from #2606 until #2632 (c93914a7); `--timeout` above 3300 s is clamped.
- **Subagents cannot write a findings .md** (the harness refuses): ask for findings.txt + fixes.json.
- `STATE.txt:308`'s "~03:00Z" for rulings 15-17 is local time labelled Z (the transcript has 09:15:39Z).

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -30 tmp/flood4/session11/STATE_S11.txt
gh pr view 2631 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 9a9ef3fb
gh pr view 2635 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 0a7c602c
gh api "repos/pcalnon/juniper-ml/commits/0a7c602c/check-runs?per_page=100" --jq '.check_runs[] | select(.name|test("Symbol")) | .name + " " + (.conclusion//"-")'
ls tmp/flood4/session11/r26/   # REVERIFY.txt REPORT.txt, six repo dirs, val_code/ val_claims/
```

## Git status

- Orchestrator worktree: branch `worktree-hidden-scribbling-toast`, HEAD `0a7c602c` (= main after #2635; reset there after
  checking the tracked files equalled main). No tracked edits. Untracked: this handoff (until its own PR lands), ruling
  26's 13 helpers (item 3), and the ignored `tmp/flood4/session11/`.
- Ruling 26's clones live under `tmp/flood4/session11/r26/clones/` and the validators' under `r26/val_*/`; nothing pushed.
- `curious-plotting-hummingbird` is DO NOT SWEEP; never run `util/remove_stale_worktrees.bash`; never touch a primary.

## Documents created or modified in session 11

- **Merged**: juniper-ml#2631 (`docs/REFERENCE.md` 0.6.82, `tests/test_pyproject_extras.py`, `CHANGELOG.md`,
  `util/ad-hoc/2026-11-24_flood4_s11_{r55_mutation_check,land_prep}.py`).
- **Merged**: juniper-ml#2635 (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, `CHANGELOG.md`,
  session 10's 16 and session 11's 14 helpers: `util/ad-hoc/2026-11-23_flood4_s10_*`,
  `util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_*`, `util/ad-hoc/2026-11-24_flood4_s11_*`).
- **Memory** (`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`): appended to
  `reference_codeql_unused_global_cascor.md` and `reference_worktree_isolated_session_command_refusals.md`; new
  `reference_subagent_findings_md_write_refused.md` (with its `MEMORY.md` line).
- **This handoff**, on its own pull request.
- **Uncommitted**: `tmp/flood4/session11/` (log, briefs, deliverables, evidence) and ruling 26's helpers (item 3).
