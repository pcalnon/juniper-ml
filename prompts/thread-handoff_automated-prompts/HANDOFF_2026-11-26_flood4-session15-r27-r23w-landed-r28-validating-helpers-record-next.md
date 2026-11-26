# Handoff: flood-4 session 15 -- r27 (juniper-canopy#843) and r23w (juniper-ml#2671) landed; r28 built, its two lenses running; r28's landing, the helpers PR and the record next

**Date**: 2026-11-26 (written ~03:25Z UTC; session 15 ran from 2026-11-26 01:50Z)

**Arc**: the Cursor flood-4 disposition, session 15, in the orchestrator worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast` (launched in
`swirling-swimming-horizon`, then EnterWorktree'd here; ListAgents name `swirling-swimming-horizon-27` [de69b3]).
It continues `HANDOFF_2026-11-26_flood4-session14-r23l-landed-r27-r23w-validating-r28-next.md` (on main via #2665).

**The running log is the detail**: `tmp/flood4/session15/STATE_S15.txt` (UTC from `date -u`). Session 14's directories
stay in use: `tmp/flood4/session14/` (briefs/, the carriers r23w/, r27/, r28/, the lenses' `*-val-*` dirs, land/).

**Merge approval**: the Overtoad chose "Merge approval granted" in session 15's dialog. Ask again in session 16.
**Agent load**: "Opus, 2 at a time" (2026-11-14).

---

## Goal for the next session

```text
Continue the Cursor flood-4 disposition from
prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_flood4-session15-r27-r23w-landed-r28-validating-helpers-record-next.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast).
Run the Verification block; read the tail of tmp/flood4/session15/STATE_S15.txt. Ask the Overtoad for this session's
merge approval; before that dialog, start what can run.

Done in session 15 (verified on GitHub):
- juniper-canopy#843 (r27, ruling 27) MERGED 2026-11-26T03:01:13Z as 2cec71fe. Three commits: 48954b7d (the PR, 16
  validator fixes applied + a comment-only allow_service_ports sentence), f7de38e2 (canopy's Update Lockfile workflow:
  requirements.lock sentry-sdk 3.0.0 -> 3.0.1, kept: CI installs from pyproject and every lane venv had 3.0.1),
  879fb9bc (macOS fix: the unanswered_port fixture returns 9; a bound-but-unlistened port TIMES OUT on the macOS runner).
- juniper-ml#2671 (r23w, ruling 23 "WebSocket gaps beside N-4") MERGED 2026-11-26T03:27:03Z as 06783316: 66
  validator fixes, 28 files, on fcbc5d3c, plus a CodeQL fix-up ee244c39 (4 alerts in two helpers; threads resolved).
  Both of ruling 23's PRs are on main (#2664, #2671). Its 20 helper copies in S were proven equal to main's blobs and
  removed; S fast-forwarded 966cdb13 -> 06783316.
- r28 (ruling 28, canopy relay test) BUILT: tmp/flood4/session14/r28/final/ (2 files: src/tests/regression/
  test_x7_sites_outside_main_gate.py, CHANGELOG.md; base 60880efc). Artefact, not a real stall (gen-2 GC passes);
  the 4 site tests now assert WHERE the call runs.

In flight when session 15 ended (they write to disk; they die if session 15's process is closed):
- r28 CODE LENS -> tmp/flood4/session14/r28-val-code/ ; r28 CLAIMS LENS -> tmp/flood4/session14/r28-val-claims/
  (both launched ~03:20Z). Done = findings.txt + fixes.json + REPORT.txt. No file newer than ~20 min and no REPORT:
  launch a replacement that finishes from its files (model: tmp/flood4/session14/briefs/R27_VAL_CODE2_replacement_prompt.txt).

Remaining, in order:
1. Land r28 (model: tmp/flood4/session14/land/r27/ and STATE_S15.txt 01:55-03:01Z). land/r28/work = r28/final +
   texts/; apply both lenses' fixes.json with util/ad-hoc/2026-11-25_flood4_s14_fixpass.py (dry run; overlaps by hand);
   CHANGELOG.md three-way onto canopy main (2cec71fe or later; keep both entries: r28/evidence/
   CHANGELOG.merged_onto_2cec71fe.txt); fresh clone; the changed file + the unit lane on 3.12 in a CI-like env
   (util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py + its census; venv r27-val-code2/venvs/py312); flakes;
   pinned pre-commit (/opt/miniforge3/bin/pre-commit); CodeQL prescreen; gitleaks; the seqsafety probe WITH the
   Allow-Symbol-Loss trailer (r28/texts/symbol_loss_waiver.txt, 8 symbols) as the commit body's LAST paragraph, before
   the Co-Authored-By/Claude-Session lines only if the workflow reads it there -- check; unwrap the PR body
   (util/ad-hoc/2026-11-26_flood4_s15_unwrap_pr_body.py) + attribution; util/open_signed_pr.py --repo juniper-canopy;
   whole-tree blob check; safe_merge (python3 -u). Watch the macOS leg and CodeQL threads.
2. One juniper-ml PR for the canopy carriers' helpers: r27's 26 and r28's 9 builder helpers (+ its lenses') untracked
   in S (git status). For each: README header, prescreen, and BY HAND the two queries the prescreen misses
   (py/import-and-import-from: a module imported as `import X as y` and `from X import z`; py/catch-base-exception),
   G-TMP, pre-commit.
3. The record update (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md): session 13's list
   (its handoff item 4) + #2664, #843, #2671, r28's PR, the helpers PR; section 8's "Still open" bullets for rulings
   23, 27, 28 and ruling 7; ruling 23's open question answered (below).
4. Ruling 7's run stays the Overtoad's (commands in session 13's handoff; pid 39566 still sits in humming).
5. After each PR lands: prove S's untracked copies equal to main's blobs (`git ls-tree origin/main -- <paths>` +
   a local blob hash), remove them, fast-forward S (session 15 did this for #2671's 20).
```

## Key context (traps met in session 15)

- **macOS runner**: a connect to a port that is BOUND but not listening times out (`httpx.ConnectTimeout`); Linux
  refuses. canopy's `test_x7_client_budget.py` already uses `127.0.0.1:9`. A lens's "macOS: analysis only" missed it.
  Memory: `reference_macos_bound_unlistened_port_times_out.md`.
- **CodeQL prescreen is blind** to `py/import-and-import-from` and `py/catch-base-exception`: #2671's four threads.
  Fix the code; when the alerts read `fixed` on `refs/pull/N/merge`
  (`gh api repos/O/R/code-scanning/alerts/N/instances?ref=refs/pull/N/merge`), resolve each thread with GraphQL
  `resolveReviewThread`, then re-run safe_merge.
- **canopy's Update Lockfile workflow** pushes a signed regen commit to any PR that touches `pyproject.toml`; read what
  it changed before merging.
- **`verify_pr_blobs` is per-commit**: after a fix-up commit, check the whole tree through the contents API (session
  15's inline checks: `land/r27/verify_tree_v2.log`, `land/r23w/verify_tree_v2.log`).
- **GitHub shows single newlines** in a PR body as line breaks: unwrap texts with the s15 helper.
- **Isolation refusals**: a `gh api` path with `/git/` in it, `xargs ... git`, and complex chains naming `gitleaks`.
- **Ruling 23's open question, answered by the claims lens**: the r23w slot hold is a STATED COST of the ruled fix,
  not a new defect (it lasts as long as N-4's unbounded drain, which already held the socket open; under uvicorn's
  default implementation no server-side bound). No ruling needed; the Overtoad was told on 2026-11-26.
- **MEMORY.md is 22.5 KB**, over the 20 KB target: a compaction by retiring entries is due (not done; another
  session's job).

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-scribbling-toast
date -u; git fetch origin main --quiet; git log --oneline -3 origin/main
tail -30 tmp/flood4/session15/STATE_S15.txt
gh pr view 2671 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + ((.mergeCommit.oid // "-")[0:8])'
gh pr view 843 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + ((.mergeCommit.oid // "-")[0:8])'
ls tmp/flood4/session14/r28-val-code/ tmp/flood4/session14/r28-val-claims/   # findings.txt / fixes.json / REPORT.txt?
(cd tmp/flood4/session14/r28/final && sha256sum -c --quiet ../final.sha256) && echo "r28 carrier intact"
ls ~/Development/python/Juniper/juniper-ml/tmp/worktree-archive-2026-11-24-flood4/ 2>/dev/null | head   # ruling 7 run?
```

## Git status

- Orchestrator worktree: branch `worktree-hidden-scribbling-toast`, HEAD `06783316` (fast-forwarded); no tracked
  edits. Untracked: this handoff (until its PR lands), r27's 26 and r28's 9 builder helpers (item 2; r28's lenses may
  add more), and the ignored `tmp/flood4/`.
- `curious-plotting-hummingbird` is DO NOT SWEEP; never run `util/remove_stale_worktrees.bash`; never touch a primary.

## Documents created or modified in session 15

- **juniper-canopy#843 (MERGED, 2cec71fe)**: `CHANGELOG.md`, `docs/testing/TESTING_REFERENCE.md` (v0.26.5),
  `pyproject.toml`, `requirements.lock` (the workflow's regen), `src/tests/conftest.py`,
  `src/tests/unit/test_health.py`, `src/tests/unit/test_unit_lane_juniper_data_fake.py` (new),
  `src/tests/unit/test_unit_lane_network_guard.py`.
- **juniper-ml#2671**: `juniper-service-core/juniper_service_core/websocket/{manager,control_stream}.py`,
  `juniper-service-core/tests/test_websocket_unsendable_late_frame_and_slot.py` (new),
  `juniper-service-core/tests/test_websocket_broadcast_drop_close.py`, `juniper-service-core/CHANGELOG.md`,
  `CHANGELOG.md`, `docs/REFERENCE.md` (0.6.85), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.74), and 20
  `util/ad-hoc/` helpers: `2026-11-25_flood4_s14_r23w_{probe,probe_summary,mutants,manifest}.py`,
  `2026-11-25_flood4_s14_r23w-val-code_{apply_fixes,assemble,consumers,fixes_build,inproc,mutants,numpy_scalars,progress,pytest_where,wire,wire_matrix,wire_summary}.py`,
  `2026-11-25_flood4_s14_r23w-val-claims_{fixes_build,probe,sweep}.py`, `2026-11-26_flood4_s15_unwrap_pr_body.py`.
- **This handoff**, on its own pull request.
- **Outside the repositories**: memory `reference_macos_bound_unlistened_port_times_out.md` (new) and its pointer in
  `MEMORY.md`.
- **Uncommitted**: `tmp/flood4/session15/` (STATE_S15.txt, ci843/, attribution files) and, under
  `tmp/flood4/session14/`, land/r27/, land/r23w/ and the r23w-val-claims, r28, r28-val-* directories.
