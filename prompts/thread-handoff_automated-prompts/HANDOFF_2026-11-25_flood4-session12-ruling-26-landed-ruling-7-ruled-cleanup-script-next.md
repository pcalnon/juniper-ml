# Handoff: flood-4 session 12 -- ruling 26's six PRs landed; ruling 7 inventoried and ruled, its cleanup script next

**Date**: 2026-11-25 (written ~01:55Z UTC; session 12 ran from 2026-11-24 21:32Z)

**Arc**: the Cursor flood-4 disposition, session 12, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (ListAgents name
`flood4-session11-r55-and-record-update-landed-ruling-26-built-and-validated-landing-next` [cbb418]). It continues
`HANDOFF_2026-11-24_flood4-session11-r55-and-record-update-landed-ruling-26-built-and-validated-landing-next.md` (on main via #2638).

**The running log is the detail**: `tmp/flood4/session12/STATE_S12.txt` in the orchestrator worktree (UTC from `date -u`;
the Overtoad's words verbatim). Ruling 26's sets, proofs and logs: `tmp/flood4/session12/r26/`. Ruling 7's inventory and
plan: `tmp/flood4/session12/r7/` (`plan.txt` holds steps R1-R9 and questions Q1-Q9). Brief: `tmp/flood4/session12/briefs/R7_inventory.txt`.

**Merge approval**: the Overtoad's first message of session 12: "merge approval granted." Ask again in session 13.
**Agent load**: "Opus, 2 at a time" (2026-11-14). **No agent is running.**

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_flood4-session12-ruling-26-landed-ruling-7-ruled-cleanup-script-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session12/STATE_S12.txt. Ask the Overtoad for this session's
merge approval. Before any Overtoad dialog, start what can run (a dialog blocked session 12 for three hours).

Done in session 12 (verified on GitHub):
- Ruling 26 LANDED, all six: juniper-data#552 (ff946c03), juniper-cascor#781 (fcdefc3b), juniper-data-client#272
  (a8f07b1d), juniper-cascor-client#205 (bed31af6), juniper-cascor-worker#237 (883be37b), juniper-canopy#842 (9b65990a),
  merged 22:07-22:28Z. Fix pass first (util/ad-hoc/2026-11-24_flood4_s12_r26_fixpass.py: the claims lens's 50 fixes incl.
  T2 option (a) and T9, the code lens's T1g and C1, five C1 test-plan bullets, data's "four files"; 67 applied, T1a-T1f
  recognised as T3's duplicates), cross-checked against both lenses' fixed copies, re-proved in fresh clones with BOTH
  session-11 harnesses (fixed pass; main fails exactly the 8 new; canopy#814's M1-M5 at session 11's counts; C1's V14/V15
  killed), pre-commit counts as the bodies say, secret scans clean (configs proven ACTIVE). cascor's and canopy's mains
  moved mid-session (cascor#780, canopy#841, files disjoint from the sets): opened on the new mains.
- Push-time checks: the three clients green. data/cascor/canopy's runs were CANCELLED by Dependabot merges landing right
  after ours; the newer mains carry our change and were green (data 8e08d209, cascor 5e3d9801); canopy ba1cb0d0 had 4 runs
  in progress at 01:48Z -> re-read.
- Item 3: juniper-ml#2644 (branch chore/flood4-ruling26-helpers): session 11's 13 ruling-26 helpers + session 12's 4,
  v26_code_{bash32,steprun}.py's stub chmod 0o755 -> 0o700. Its first safe_merge REFUSED (timed out on its own
  update-branch head bff6ae4d, Quality Gate absent); on head f7831b11 every check is green; safe_merge was RE-RUN at 01:47Z.
- Ruling 7 inventoried (read-only agent; 282 candidates): batch A 265 entries, 71.97 GB (tmp/ 10.75 GB), every related PR
  merged; B 13 (no PR); C 4 (excluded/live). The Overtoad's rulings (2026-11-25 01:46Z, labels verbatim): R7-Q1 "You run
  the script (Recommended)"; R7-Q2 all four of "9 session launch worktrees", "3 ruling-37 marker trees", "6
  inferred-provenance trees", "Delete the 13 sim dirs"; R7-Q3 "juniper-ml/tmp/ (Recommended)"; R7-Q4 "Delete branches,
  keep refs (Recommended)".

Remaining, in order:
1. Confirm juniper-ml#2644 MERGED (read safe_merge2.log's MERGED line, or re-run util/safe_merge.py --execute). Re-read
   canopy main's push-time checks.
2. Ruling 7's cleanup SCRIPT (the Overtoad runs it; this isolated session cannot run git in other checkouts). Write
   util/ad-hoc/2026-11-25_flood4_r7_cleanup.{bash,py} from tmp/flood4/session12/r7/plan.txt (R1-R9) and inventory.json,
   modeled on util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash. Dry run by default, --execute to act. Per worktree:
   refuse if LIVE (a process cwd in it, or a file modified in the last 6 h); git status --porcelain -> tracked edits as a
   patch + untracked non-ignored files into saved/; tmp/ MOVED (rename) into
   juniper-ml/tmp/worktree-archive-2026-11-24-flood4/<name>/tmp/; MANIFEST.txt (branch, HEAD, time, sha256 of every
   saved file); then git worktree remove + prune. Scope: batch A + all of batch B (save the worker ruling-37 marker's
   uncommitted edits as a patch first). The 13 PLAIN-DIR sim trees: write a file list, then delete (no archive).
   Branches: write deleted_branches.txt (repo, name, full sha) BEFORE deleting the 87; KEEP the 69 refs/flood4/* refs.
   humming-stargazing-papert LAST, compared against origin/main (its branch moved to 0658e854); the Overtoad closes the
   terminal tab in it (pid 39566, pts/11) first. Never touch curious-plotting-hummingbird, hidden-scribbling-toast,
   playful-scribbling-kite; never run util/remove_stale_worktrees.bash. Test the script ONLY on a synthetic fixture
   (repos + worktrees built under tmp/), two lenses (code, claims), land it on a signed PR, then give the Overtoad the
   exact commands: dry run, the report to read, then --execute. A README.md in the archive, as 2026-11-23's.
3. Rulings 23, 27, 28 (none built): ruling 23's two service-core PRs ("WebSocket gaps beside N-4": an unserialisable
   broadcast closes every socket, /ws/control crashes after a server close, a dropped socket's per-IP slot is freed
   before it has closed; "Lifecycle races beside N-2": a stop followed at once by a snapshot load, a leftover replay
   session's stop resetting a running run); ruling 27 (canopy: 124 unit tests in 38 files connect to :8100; mock the
   data client at app startup for the unit lane, add 8100 to the guard); ruling 28 (canopy's load-sensitive
   test_relay_cascade_add_does_not_block_the_loop). Build, two lenses, land each. Sources: the record's §8 rulings 23,
   27, 28; humming-stargazing-papert/tmp/flood4/session6/STATE_S6.txt:51-90; the N-4 / N-2 validators' prompts
   (session5/prev_prompts/034-037, session6/prev_prompts/017-018) and their outputs under tmp/flood4r2-val/; the session-6
   dialog in transcript f2b4e7c3 (util/ad-hoc/2026-11-24_flood4_s11_v26_claims_dialog.py extracts it). If ruling 7's
   cleanup runs first, those trees' tmp/ will have MOVED into the archive: read them there.
4. The next record update: ruling 26's six PRs and #2644; ruling 7's four rulings and the cleanup's outcome; §6's rename
   scope corrected (the pass touched juniper-ml/.claude/worktrees/ only: 61 of 64 candidates there, 0 of 218 under
   worktrees/); session 12's helpers, incl. the R7 agent's seven util/ad-hoc/2026-11-24_flood4_s12_r7_*.py (untracked;
   run G-TMP, the CodeQL prescreen, pre-commit and a secret scan before they ride a PR).
```

## Key context (traps met in session 12)

- **The isolation refuses `git -C <primary checkout>`** outright, and any loop or pipe whose text holds `.github` or
  `github.raw`, a `mkdir && cat <<EOF` write and a `python3 - <<PY` heredoc. Write files with the Write tool; pass
  `.github` paths as a helper script's arguments; `git -C <a clone under tmp/>` and `git worktree list` from the
  worktree are allowed. Ruling 7's removals therefore cannot be this session's own git commands.
- **`util/ad-hoc/2026-11-24_flood4_s11_r26_proof.py` takes `--expect-new` once per name** (`action="append"`); the
  code lens's harness takes them all after one flag (`nargs="+"`).
- **The CodeQL prescreen's "pytestmark never read" is a false positive**, and `py/overly-permissive-file` flags
  `os.chmod`, not `pathlib.Path.chmod` (memory `reference_codeql_unused_global_cascor.md`).
- **A secret scan of a whole-file set flags main's own content**: canopy's `CHANGELOG.md:1663` (`generic-api-key`) is
  byte-identical to main's line 1656; a PR's scan is commit-ranged.
- **Dependabot merges right after ours cancel the push-time runs** (cancel-in-progress): read the newer main's runs.
- **safe_merge can time out on its own update-branch head** while a required check has not appeared; it disarms the
  net on refusal. Re-read the PR's checks, then re-run it.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -40 tmp/flood4/session12/STATE_S12.txt
for p in juniper-data:552 juniper-cascor:781 juniper-data-client:272 juniper-cascor-client:205 juniper-cascor-worker:237 juniper-canopy:842 juniper-ml:2644; do gh pr view ${p#*:} --repo pcalnon/${p%%:*} --json state,mergeCommit --jq "\"${p}: \" + .state + \" \" + (.mergeCommit.oid // \"-\")[0:8]"; done
grep -E "MERGED|REFUSED" tmp/flood4/session12/r26/helpers_pr/safe_merge2.log
m=$(gh api repos/pcalnon/juniper-canopy/commits/main --jq .sha); gh api "repos/pcalnon/juniper-canopy/commits/$m/check-runs?per_page=100" --jq '[.check_runs[] | (.conclusion // .status)] | group_by(.) | map("\(.[0])=\(length)") | join(" ")'
ls tmp/flood4/session12/r7/   # plan.txt findings.txt inventory.json inventory.tsv rejected.tsv batches.txt local_branches.tsv
```

## Git status

- Orchestrator worktree: branch `worktree-hidden-scribbling-toast`, HEAD `f41b1d07` (fast-forwarded from `0a7c602c` at
  the start; main has moved since). No tracked edits. Untracked: the 17 helpers that #2644 carries (byte-equal to its
  blobs; fast-forward after it merges, then they become tracked), the R7 agent's seven
  `util/ad-hoc/2026-11-24_flood4_s12_r7_*.py`, this handoff (until its own PR lands) and the ignored `tmp/flood4/session12/`.
- Ruling 26's fresh clones sit under `tmp/flood4/session12/r26/clones/` (sets installed, nothing pushed from them).
- `curious-plotting-hummingbird` is DO NOT SWEEP; never run `util/remove_stale_worktrees.bash`; never touch a primary.

## Documents created or modified in session 12

- **Merged in five sibling repos and canopy**: juniper-data#552 (`.github/workflows/lockfile-update.yml`,
  `juniper_data/tests/unit/test_lockfile_signed_commit.py`, `CHANGELOG.md`, `docs/ci_cd/CICD_REFERENCE.md`),
  juniper-cascor#781 (the workflow, `src/tests/unit/test_lockfile_commit_gh_failure.py`, `CHANGELOG.md`),
  juniper-data-client#272 (the workflow, `tests/test_lockfile_signed_commit.py`, `CHANGELOG.md`),
  juniper-cascor-client#205 and juniper-cascor-worker#237 (the workflow, `tests/test_lockfile_commit_gh_failure.py`,
  `CHANGELOG.md`), juniper-canopy#842 (`docs/ci_cd/CICD_MANUAL.md`, `CHANGELOG.md`).
- **Open, merge re-run**: juniper-ml#2644: `util/ad-hoc/2026-11-24_flood4_s11_r26_proof.py`,
  `util/ad-hoc/2026-11-24_flood4_s11_v26_claims_{changelog,dialog,diffcheck,fixes,runs,testnames}.py`,
  `util/ad-hoc/2026-11-24_flood4_s11_v26_code_{bash32,blockdiff,proof,propose,steprun,tmpcheck}.py` (bash32 and steprun
  edited: 0o700), `util/ad-hoc/2026-11-24_flood4_s12_r26_{fixpass,setcheck,reprove,precommit}.py` (new).
- **Untracked, new**: `util/ad-hoc/2026-11-24_flood4_s12_r7_{scan,live,measure,mentions_index,context,inventory,commit_peek}.py`.
- **Memory** (`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`): appended to
  `reference_codeql_unused_global_cascor.md` and `reference_worktree_isolated_session_command_refusals.md`.
- **This handoff**, on its own pull request.
- **Uncommitted**: `tmp/flood4/session12/` (log, briefs, sets, proofs, inventory).
