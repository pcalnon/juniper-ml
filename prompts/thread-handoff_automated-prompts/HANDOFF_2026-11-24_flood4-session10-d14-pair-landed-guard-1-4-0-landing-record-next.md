# Handoff: flood-4 session 10 -- the D-14 pair LANDED after a sha256-proven recovery from the rename pass; guard 1.4.0 opened as ml#2625 under the owner's rulings 46-47; R55's check and the record update next

**Date**: 2026-11-24 (written 02:20Z UTC, while ml#2625 waited on its checks)

**Arc**: the Cursor flood-4 disposition, session 10, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (ListAgents name
`flood4-session9-paused-pause-fix-landed-guard-and-d14-ready` [f9fa6e]). It continues
`HANDOFF_2026-11-16_flood4-session9-paused-pause-fix-landed-guard-and-d14-ready.md` (on main via #2604; the primary
checkout's untracked `HANDOFF_2026-11-16__flood4-...` copy is the 2026-11-20..22 rename pass's rewrite of it).

**The running log is the detail**: `tmp/flood4/session10/STATE_S10.txt` in the orchestrator worktree (UTC from `date -u`;
the owner's answers verbatim; provisional ruling numbers 46-48). Briefs: `tmp/flood4/session10/briefs/`.

**Merge approval**: granted for session 10 only ("merge approval granted", the owner's second message). A new session
asks again. **Agent load**: "Opus, 2 at a time" (the owner's ruling of 2026-11-14). **No agent is running.**

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_flood4-session10-d14-pair-landed-guard-1-4-0-landing-record-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session10/STATE_S10.txt. Ask the owner for THIS session's
merge approval. Before any owner dialog, start whatever must merge meanwhile in the background (see Key context).

Done in session 10 (verified on GitHub):
- The 2026-11-20..22 blind "owner -> Overtoad" pass had rewritten the carriers' WORKING TREES. Recovered, each proven
  against the sha256 its builder recorded on 2026-11-16: cascor D-14 4/4 verbatim; ml D-14 35/35 (6 verbatim, 26 plain
  inverse, 1 two-step, 2 anchored); guard 16/16 from the INDEX (staged blobs are untouched by a working-tree sed).
- juniper-cascor#776 MERGED 2026-11-23 22:13Z as 36dd6f2d; juniper-ml#2618 MERGED 22:31Z as eeaa191c (D-14 complete:
  one shared /ws/training resume table, service-core answering as cascor does). Both needed a CodeQL fix
  (py/uninitialized-local-variable: `pytest.fail` inside `except` -> `raise AssertionError(...) from exc`).
- Owner rulings 2026-11-24 ~01:45Z (verbatim): 46 "Land 1.4.0, name gaps (Recommended)"; 47 "Keep 3 s
  (Recommended)"; 48 "Add a paragraph check (Recommended)" (R55).
- juniper-ml#2625 (guard 1.4.0) OPENED 02:17:13Z: signed 12bc5a48 on main 9b5d36bc, 16/16 blobs = the validated final
  set; claims lens JL2b's 31 text fixes applied (F1-F11 closed); REFERENCE 0.6.80; waiver trailer
  `Allow-Symbol-Loss: method:BashAnalyzer._path_word` in its commit's last paragraph. safe_merge --execute was running
  (log tmp/flood4/session10/guard/safe_merge.log).

Remaining, in order:
1. If #2625 is not MERGED: finish it (read the log's MERGED line; a CodeQL thread -> fix, re-scan, check whether the
   bot resolved it itself before resolving). Then message `overtoad-rename-repair-2606-rebuilt-validated-upload-after-peer-prs`
   its merge commit: that session HOLDS ml#2606 until it has it (agreed 01:55Z; "slipped past 05:00Z" frees it to go
   first). Then tell the owner: re-run util/install_claude_agent_guard.bash on turing (not installed on the Linux host)
   and confirm turing's Claude Code is >= v2.1.295 (the "onFailure" setting needs it).
2. Ruling 48 (R55): one assertion in tests/test_pyproject_extras.py that the paragraph above docs/REFERENCE.md's
   compatibility table states that the current row tracks pyproject.toml between a floor PR and its release
   (`_DECLARES_RE` at :91-92 already pins the release named there). Small PR; tell [9660dc] when it lands.
3. The record-update PR: rulings 15-48 into notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
   section 8 (it stops at ruling 14, last changed 734aab58 on 11-09), with sessions 9-10's outcomes; R54 (plan v1.15.17
   :1158) wants ruling 17 recorded as ONE ruling over its four fixes. Sources: STATE_S9.txt (rulings 36-45, in session 9's
   orchestrator worktree, untouched by the pass) and STATE_S10.txt (46-48). Keep "owner" unless ml main carries the
   rename by then (ml#2606).
4. docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:1294 calls the guard entry "1.3.0" (where the brace cap arrived; still a true
   description): decide whether it should name 1.4.0 (needs the cheatsheet's stamps).
5. Provenance: session 10's 16 untracked helpers (sha256 below) need a commit; ml#2606 carries sessions 5-9's helpers and
   handoffs (its ruling 6: keep, fix identifiers; ruling 7: restore handoff text): confirm with the rename session before
   committing any of those yourself.
6. Ruling 7 cleanup (archive each tmp/ first, then remove): see Git status.
7. The 2026-11-12 rulings' service-core and canopy items and the owed Dependabot reads (juniper-data, juniper-data-client,
   juniper-cascor-client, juniper-ml), as session 9's handoff lists them.
```

## Key context (traps met in session 10)

- **Rename damage is on disk, not in git**: a juniper-ml worktree that existed 2026-11-20..22 has rewritten tracked files
  (`' M'`, symlinks as `' T'`), untracked files and much of `tmp/`. Never land from a carrier's working tree. Recover
  provably with `util/ad-hoc/2026-11-23_flood4_s10_verify_recover.py` (sha256 manifest required; `--base-ref` enables
  the anchored inverse) or `util/ad-hoc/2026-11-23_flood4_s10_materialize_staged.py` (index blobs). The orchestrator
  worktree `humming-stargazing-papert` is ml#2606's head branch: read its `tmp/` only, never enter or write it.
- **A whole-file upload onto a moved main reverts main's change**: `util/ad-hoc/2026-11-23_flood4_s10_open_pr_from_paths.py`
  refuses unless main is the expected base; when main moved, check the compare's files before passing the new base
  (#2625 went onto 9b5d36bc, a backup-docs commit touching none of its paths). Verify every push with
  `util/ad-hoc/2026-11-23_flood4_s10_verify_pr_blobs.py`.
- **Agent isolation failed 3x** ("Could not read the repository git config to neutralize filter drivers", load ~42):
  builders ran IN the orchestrator worktree with a WHERE YOU WORK brief section; a concurrent reader reads main via
  `git show origin/main:<path>`.
- **Owner dialogs block** (~3.75 h this time): `util/ad-hoc/2026-11-23_flood4_s10_land_d14_pair.py` merged the pair
  during it (resolve a CodeQL thread only when its alert instance on `refs/pull/N/merge` reads `fixed`).
- **`SENTRY_SDK_DSN` is set in session environments**: a cascor unit lane sent 2 Sentry events; run lanes with
  `env -u SENTRY_SDK_DSN -u JUNIPER_CASCOR_LOG_DIR`.
- cascor main carries the rename (#772): new cascor CHANGELOG text says "the Overtoad's ruling" (#776 did). **ml main
  carries it too since ml#2606 MERGED 2026-11-24 05:06:27Z as 5a049144** (after guard 1.4.0; this session held #2626 for
  it, hold lifted at 05:06Z): new living text in juniper-ml follows main (read how #2606 rendered the file you edit);
  records such as handoffs and release notes keep their original text (the owner's ruling 2 of 2026-11-23).

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -25 tmp/flood4/session10/STATE_S10.txt
gh pr view 776 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 36dd6f2d
gh pr view 2618 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'      # MERGED eeaa191c
gh pr view 2625 --repo pcalnon/juniper-ml --json state,mergeCommit,headRefOid --jq '.state + " " + (.mergeCommit.oid // "-")[0:8] + " head " + .headRefOid[0:8]'
tail -4 tmp/flood4/session10/guard/safe_merge.log
sha256sum -c tmp/flood4/session10/s10_untracked_helpers.sha256 | grep -c ': OK$'   # 16
```

## Git status

- Orchestrator worktree `hidden-scribbling-toast`: branch `worktree-hidden-scribbling-toast`, HEAD `ca976240`, the
  guard's 16 files STAGED by builder G1 (the same bytes as #2625; after #2625 merges, `git reset --hard origin/main` is
  safe once `git diff --cached --stat origin/main -- util/claude_agent_guard.py tests/` is empty). Untracked: the 16
  helpers below and `tmp/flood4/session10/`, `tmp/flood4r2-val/s10-guard-claims-lens/` (evidence; keep).
- KEEP until archived (ruling 7): the D-14 carriers `worktrees/juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d`
  and `.claude/worktrees/agent-a7aa0806f2312b786`; the guard carrier `.claude/worktrees/agent-a0f16311d9dabda6f`; the
  cascor test worktree `worktrees/juniper-cascor--test--ws-resume-answer-table-land--20261123-1512--e9c86f83` (branch
  `test/ws-resume-answer-table-land`, local only); plus session 9's list. Their `tmp/` dirs are partly rewritten by the
  pass: archive as-is, noting it. `curious-plotting-hummingbird` is DO NOT SWEEP; never run
  `util/remove_stale_worktrees.bash`; never touch a primary checkout.

Session 10's untracked helpers (sha256, so a later copy is provably the original):

```text
e8fd0d523898fa5bdc49fc915b731cd94489b16e9637a16b1136dad9778fc262  util/ad-hoc/2026-11-23_flood4_s10_compare_manifest.py
0248449b75e1611e5b1a186db6525856d11a44687a0e8bce8351eb30a37d9dac  util/ad-hoc/2026-11-23_flood4_s10_diff_of_diffs.py
97f148ccfd9ca2aff6ee0d09139287ed9394feafce10aa949d5ec99541d583d9  util/ad-hoc/2026-11-23_flood4_s10_land_d14_pair.py
9baf06acee30aa485fb3c655061c92cec69968b7138df37629c6702c9f0ee324  util/ad-hoc/2026-11-23_flood4_s10_materialize_staged.py
a453fadd9c485083bf0dfeef7471806cd5236c8a8ae3192be3eb9497f786a636  util/ad-hoc/2026-11-23_flood4_s10_open_pr_from_paths.py
4cb4947650f143b7bea5c9c0f2fa25ffe65650607bab1d645f403233cb68e310  util/ad-hoc/2026-11-23_flood4_s10_tree_probe.py
563dc5baf5e20a18054133f4051f0072265dc37315457cbe309a57bca81ab61b  util/ad-hoc/2026-11-23_flood4_s10_verify_pr_blobs.py
bfa6e049724d5727b40ab5f37ae3217b5aaed7426ac9aca2f06f88d646decfb5  util/ad-hoc/2026-11-23_flood4_s10_verify_recover.py
85a1ef87b9a65be5141bc4ca0cfc89b3ad265a6a428f831d8812cd9c72432c73  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_bashprint.py
b3747bdb56a8b5a7a3ab1c447cc7cc35f3fd4af83509a7f5039fd6f9914dc894  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_brace_expand_diff.py
7b5f7c471acf69fd3768945b82140e72cddd445e682c320919263a2964f43122  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_findings.py
b099d910acd6933656247c3a502a2e72c8e6bb404157585b87665853293450c5  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_guardprobe.py
7060e01d5faaf323bb48186fb7c4b8fbc38b9d3754db1a4cf95da309eedae683  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_seqsafety.py
771aa8579d3201814ff63bd8b2c770d027afa92b99fc1367e4472a5760f1699b  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_textfixes.py
c2e1baa886b490810945bd26903a5d044ee9fe9341129668c128728f616842a0  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_textscan.py
018c23d8e7d2be17fe08ceb0587a34406bd894985e1b39e62586d56b49590501  util/ad-hoc/2026-11-23_flood4r2_val_s10-guard-claims_threeway.py
```

## Documents created or modified in session 10

- **Merged on GitHub**: juniper-cascor#776 (`CHANGELOG.md`, `docs/api/API_SCHEMAS.md` 0.3.26, new
  `src/tests/fixtures/ws_resume_answers.json`, new `src/tests/unit/api/test_websocket_resume_answer_table.py`);
  juniper-ml#2618 (35 paths: `.github/workflows/{ci,docs-full-check,main-verify}.yml`, `AGENTS.md`, `CHANGELOG.md`,
  `docs/REFERENCE.md` 0.6.79, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` 1.0.72, juniper-service-core's `CHANGELOG.md`,
  `MANIFEST.in`, `pyproject.toml`, `websocket/{manager,training_stream}.py`, `tests/fixtures/ws_resume_answers.json`,
  `tests/test_websocket_resume_{answer_table,continuity}.py`, new `tests/test_ws_resume_answer_table_drift.py`, 19
  `util/ad-hoc/2026-11-1[56]_flood4r2_d14_*.py`).
- **Open**: juniper-ml#2625 (`CHANGELOG.md`, `docs/REFERENCE.md` 0.6.80, `tests/test_claude_agent_guard.py`,
  `tests/test_claude_agent_guard_brace_cap.py`, `util/claude_agent_guard.py` 1.4.0, 11 `util/ad-hoc/2026-11-16_flood4r2_r18-guard_*.py`).
- **This handoff**, on its own pull request.
- **Memory** (`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`): appended to
  `reference_codeql_unused_global_cascor.md`, `reference_owner_dialog_blocks_the_session.md`,
  `reference_blind_substitution_rewrites_untracked_files_in_sibling_worktrees.md`,
  `reference_worktree_isolated_session_command_refusals.md`.
- **Uncommitted, orchestrator worktree**: `tmp/flood4/session10/STATE_S10.txt`, the briefs `R1_d14_ml_rebuild_on_main.txt`,
  `JL2b_guard_claims_lens.txt`, `G1_guard_land_prep.txt`, every deliverable under `tmp/flood4/session10/` and
  `tmp/flood4r2-val/s10-guard-claims-lens/`, and the 16 helpers above.
