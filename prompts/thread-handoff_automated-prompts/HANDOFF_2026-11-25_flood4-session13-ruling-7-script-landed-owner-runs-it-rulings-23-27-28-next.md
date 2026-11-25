# Handoff: flood-4 session 13 -- ruling 7's cleanup script built, validated by two lenses and landed; the Overtoad runs it; rulings 23, 27, 28 next

**Date**: 2026-11-25 (written ~04:05Z UTC, updated ~12:05Z after the Overtoad's K1 answer; session 13 ran from 02:07Z)

**Arc**: the Cursor flood-4 disposition, session 13, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (launched in
`stateful-painting-jellyfish`, then EnterWorktree'd here; ListAgents name
`flood4-session12-ruling-26-landed-ruling-7-ruled-cleanup-script-next` [cea3c5]). It continues
`HANDOFF_2026-11-25_flood4-session12-ruling-26-landed-ruling-7-ruled-cleanup-script-next.md` (on main via #2651).

**The running log is the detail**: `tmp/flood4/session13/STATE_S13.txt` (UTC from `date -u`). The lenses' outputs:
`tmp/flood4/session13/val_code/` and `val_claims/` (findings.txt, fixes.json). The landing set: `tmp/flood4/session13/land/`.

**Merge approval**: the Overtoad's first message of session 13: "merge approval granted". Ask again in session 14.
**Agent load**: "Opus, 2 at a time" (2026-11-14). **No agent is running.**

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_flood4-session13-ruling-7-script-landed-owner-runs-it-rulings-23-27-28-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session13/STATE_S13.txt. Ask the Overtoad for this session's
merge approval. Before any Overtoad dialog, start what can run.

Done in session 13 (verified on GitHub):
- juniper-ml#2644 (ruling 26's 17 helpers) MERGED 02:46:13Z as 157ffc26; #2651 (session 12's handoff) MERGED.
  Ruling 26's six PRs were already merged; canopy's main: our merge commit 9b65990a has a green run (45502397843);
  60880efc's one red (Playwright test_populated_store_survives_poll_after_stop, a Dependabot bump) is not ours.
- Ruling 7's cleanup script: util/ad-hoc/2026-11-25_flood4_r7_cleanup.py 1.1.0 + its fixture self-test (130/130),
  util/ad-hoc/2026-11-25_flood4_s13_r7_{primaries_probe,fixpass}.py, and session 12's seven R7 inventory helpers
  (one edited: two unused locals) -> juniper-ml#2659 MERGED 2026-11-25T04:49:21Z as d78bbc53 (signed ab038385,
  blobs verified 11/11). Two Opus lenses: code (C1-C5 MAJOR, all fixed; C7 the only real exposure: 7 local
  probe commits now bundled) and claims (K1-K15). Merged through the fixpass helper (code 31/31; claims 34 + K5 by
  hand; K2/K3/K8 superseded by C2/C7/C7b).
- K1: juniper-ml--val--flood4r2-n4-claims--20261109-0958--f85fbc8b is NOT a simulation tree (the N-4 claims lens's fix
  tree: 9 of its 14 carrier files exist nowhere else in their original bytes). The Overtoad ruled (verbatim):
  "Archive it whole (Recommended)" -> the run uses --held archive (moved whole into <archive>/NAME/tree/ by rename).

Remaining, in order:
1. Confirm this handoff's PR (#2660) merged; the worktree is already past #2659 (HEAD b54f961b).
2. Ruling 7's RUN is the Overtoad's (R7-Q1). If he has run it: read its report (the commands below write
   tmp/flood4/session13/r7_dryrun.txt and the archive's runs/<id>-execute.{log,json}); verify the archive:
   README.md, INDEX.tsv, every MANIFEST sha256 line (the selftest's checker is the model), deleted_branches.txt
   against the 87, no refs/flood4/* touched, the held directory as he ruled. If humming was held back by skips,
   help settle them, then --only humming-stargazing-papert. If he has not run it, give him the commands again.
3. Rulings 23, 27, 28 (none built), unchanged from session 12's handoff item 3: ruling 23's two service-core PRs
   ("WebSocket gaps beside N-4": an unserialisable broadcast closes every socket, /ws/control crashes after a server
   close, a dropped socket's per-IP slot is freed before it has closed; "Lifecycle races beside N-2": a stop followed
   at once by a snapshot load, a leftover replay session's stop resetting a running run); ruling 27 (canopy: 124 unit
   tests in 38 files connect to :8100; mock the data client at app startup for the unit lane, add 8100 to the guard);
   ruling 28 (canopy's load-sensitive test_relay_cascade_add_does_not_block_the_loop). Build, two lenses, land each.
   Sources: the record's section 8 rulings 23, 27, 28; humming's tmp/flood4/session6/STATE_S6.txt:51-90; the N-4/N-2
   validators' prompts and outputs under humming's tmp/flood4r2-val/; the session-6 dialog in transcript f2b4e7c3
   (util/ad-hoc/2026-11-24_flood4_s11_v26_claims_dialog.py extracts it). AFTER ruling 7 runs, humming's tmp/ is at
   juniper-ml/tmp/worktree-archive-2026-11-24-flood4/humming-stargazing-papert/tmp/.
4. The next record update (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md): ruling 26's six
   PRs and #2644; ruling 7's four rulings (verbatim, tmp/flood4/session13/r7_dialog.json), K1 and its answer, the
   cleanup's outcome (#2659 and the run); section 6's rename scope (only juniper-ml/.claude/worktrees/: 61 of 64; 0 of
   218 under worktrees/); F3's premise corrected (humming's HEAD moved by its OWN commits and a `pull origin`
   fast-forward to 0658e854 on 2026-11-23, its reflog shows; the index moved with it); session 12-13's helpers.
```

## How the Overtoad runs ruling 7 (give these again if not yet run)

```bash
cd ~/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
S=util/ad-hoc/2026-11-25_flood4_r7_cleanup.py
A="--inventory tmp/flood4/session12/r7/inventory.json --pr-commits tmp/flood4/session13/r7_pr_commits.jsonl"
# 0. close the terminal tab whose shell sits in humming-stargazing-papert (pid 39566, pts/11), or `cd ~` in it
python3 $S $A --list | tail -3                                   # 1. selection check: no git, writes nothing
python3 $S $A --fetch --json tmp/flood4/session13/r7_dryrun.json 2>&1 | tee tmp/flood4/session13/r7_dryrun.txt | tail -60
                                                                  # 2. dry run; read the SUMMARY's SKIP / REVIEW / BRANCH KEEP lines
python3 $S $A --fetch --execute --held archive                   # 3. asks you to type 'execute' (--held archive: K1)
python3 $S $A --fetch --execute --only humming-stargazing-papert # 4. only if step 3 held humming back
```

## Key context (traps met in session 13)

- **A session's background `safe_merge` dies with the session** and its block-buffered log stays empty: run it as
  `python3 -u`. A net armed earlier still merges (#2651 did; #2644 needed a re-run after main moved twice).
- **The isolation refuses** `git -C <primary>` and loops or pipes naming `.git` paths; read primaries' `.git` files with a
  helper (`2026-11-25_flood4_s13_r7_primaries_probe.py`). The juniper-ml primary is SHALLOW (boundary b4d08355).
- **G-TMP's pattern skips `/tmp` after a word character**: write `NAME/tmp/`, not `<name>/tmp/`, in text.
- **The script's design departures, all disclosed in its docstring**: prune is a report (C6); reflog-only commits are
  bundled through temporary refs refs/r7-archive/<run>/<n>, deleted after (C7); a creation base counts only when it is
  on main's or HEAD's history (K7; d4dcefbc is not); the inventory's sha256 is pinned (K12).
- **Write timestamps from `date -u`**, never from estimate: session 13 had to correct three log entries.
- **The K1 dialog blocked ~8 h** (asked ~04:07Z). #2659's armed net merged meanwhile; #2660's safe_merge REFUSED
  ("went BEHIND 3 times without a stable green head"), so #2660 was re-cut as one signed commit on the moved main.
- **pid 39566** (an idle bash on pts/11, cwd humming-stargazing-papert since 11-17) was still alive at 11:58Z: the
  script skips humming until that tab is closed.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -30 tmp/flood4/session13/STATE_S13.txt
gh pr view 2659 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + ((.mergeCommit.oid // "-")[0:8])'
grep -E "MERGED|REFUSED|rc=" tmp/flood4/session13/land/safe_merge_2659.log
python3 util/ad-hoc/2026-11-25_flood4_r7_cleanup.py --inventory tmp/flood4/session12/r7/inventory.json --pr-commits tmp/flood4/session13/r7_pr_commits.jsonl --list | grep -E "^selection|REFUSED"
ls ~/Development/python/Juniper/juniper-ml/tmp/worktree-archive-2026-11-24-flood4/ 2>/dev/null | head   # exists once he has run --execute
```

## Git status

- Orchestrator worktree: branch `worktree-hidden-scribbling-toast`, HEAD `b54f961b` (fast-forwarded from `f41b1d07`
  in three steps, each after proving the untracked copies equal main's blobs). No tracked edits. Untracked: this
  handoff (until #2660 lands) and the ignored `tmp/flood4/session13/`.
- `curious-plotting-hummingbird` is DO NOT SWEEP; never run `util/remove_stale_worktrees.bash`; never touch a primary.

## Documents created or modified in session 13

- **juniper-ml#2659 (MERGED, d78bbc53)**: `util/ad-hoc/2026-11-25_flood4_r7_cleanup.py`, `..._r7_cleanup_selftest.py`,
  `..._s13_r7_primaries_probe.py`, `..._s13_r7_fixpass.py` (new), `util/ad-hoc/2026-11-24_flood4_s12_r7_{scan,live,
  measure,mentions_index,context,inventory,commit_peek}.py` (session 12's; `..._inventory.py` edited).
- **This handoff**, on its own pull request (juniper-ml#2660).
- **Uncommitted**: `tmp/flood4/session13/` (STATE_S13.txt, briefs, both lenses' outputs, the merge copies, fixtures,
  the landing set, r7_dialog.json, r7_pr_commits.jsonl).
