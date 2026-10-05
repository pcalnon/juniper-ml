# HANDOFF 2026-10-04 — P2 canopy Lane A: Phase 10 drafted through three consensus rounds (round 3's fix pass owed, NOT pushed); F-058 census v2 built and synthetic-checked

> **SUPERSEDED 2026-10-05** by `HANDOFF_2026-10-05_canopy-phase10-five-rounds-pr-open-census-ran-live-phase11-owed.md`,
> which the same session wrote after finishing this file's steps 1–3.

**Written**: 2026-10-04, late, by the session in juniper-ml worktree `.claude/worktrees/clever-juggling-spring`
(branch `docs/canopy-e2e-phase10`). It was cut off by the usage limit. **Not consensus-validated.**
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md` (authoritative for
P2). Also read `HANDOFF_2026-10-04_canopy-replay-player-fixed-and-live-verified-p2-items-2-to-7-next.md`.
**Merge approval**: the owner granted it for THIS session's PRs ("merge approval granted"). It is not carried, so
ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_canopy-phase10-round3-fix-pass-owed-then-land-census-v2-ready.md`
(juniper-ml). Start a session IN worktree `.claude/worktrees/clever-juggling-spring`: the work is local commits on
branch `docs/canopy-e2e-phase10`, and nothing is pushed. Finish Phase 10 (round 3's fix pass, then round 4 if it
changes a number, disposition or action), land it as one PR, then run the F-058 census live. Ask for merge approval
before the first merge.

**Completed (local commits on `docs/canopy-e2e-phase10`, base `cf711cf4`):**

- `0737d573`: the ledger's Phase 10 (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) files
  F-CANOPY-060 to -066 and declines O4 and O9. Predecessor A is archived as
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`.
  Three instruments ship with it: `util/ad-hoc/2026-10-04_phase10_{f060,o2,o3}_rederive.py`.
- `2134ca2a`: round 1, four lanes. It added F-CANOPY-067 (P2), re-rated F-CANOPY-065 to P1, and corrected
  W1-09's Phase 1 PASS to FAIL.
- `0d3c337b`: round 2, two lanes. It re-rated F-CANOPY-057 to P2 (canopy#684 had corrected its basis), made
  F-CANOPY-065's P1 conditional, fixed F-CANOPY-067's triggers, and scoped M-METRICS-32.
- Counts at `0d3c337b` (`util/ad-hoc/e2e_finding_triage.py`): 78 findings, 53 fixed, 1 accepted, 2 withdrawn,
  22 open (0 P0, 6 P1, 16 P2).
- Uncommitted when this was written, and committed with this file: `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`
  (the P2 row) and `HANDOFF_2026-10-03_canopy-consolidated.md` (item 2 marked DONE).
- MEMORY.md is at 24,769 characters (it was 24,993). One resolved entry was retired; its two latent CI risks
  were checked fixed on main. The gitleaks Node24 cleanup is still owed: the trigger is met, yet the override
  remains in canopy, cascor and deploy.

**Remaining, in order:**

1. **Round 3.** Lane 10-R3A returned SOUND-WITH-FIXES with one MAJOR that changes an action, so round 4 is
   owed after the fixes. Its report is the final message of agent `acbfa54f3ee566bcc`. Lane 10-R3B (agent
   `a09866a22515100dc`) was still running at the cut-off.
   - Check
     `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-clever-juggling-spring/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/subagents/agent-a09866a22515100dc.jsonl`
     for its final report. If it has none, re-run R3B from `reports/e2e-canopy-2026-09-02/drafts/lane10R3_phase10_ledger_brief.md`.
   - Archive both reports with `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`, under `--marker
     "Round 4 of the Phase 10 ledger validation"`, to
     `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round3.md`.
   - R3A's fixes. Re-derive each first.
     - **(MAJOR)** F-CANOPY-067's P2 basis covers only an idle cascor. Mid-run, the store keeps the burst's
       flat rows until a 5 s gap in `metrics` frames or until window-size newer rows arrive (`:7833-7834`).
       W8 step 13 always lands on an idle cascor, because canopy refuses a model switch while training
       (`main.py:4092-4097`). Reword the basis, and add a mid-run burst to item 18 and to both fix directions
       (e.g. restart canopy mid-run with the tab reconnecting inside 5 s).
     - Phase 1's cluster DOES hold a mostly hidden Accuracy marker: two junction pixels are about 70% `#28a745`,
       at about 98.6%. Rewrite the header ("one Accuracy point after the run in both archived captures, mostly
       hidden in Phase 1's") and the body's pixel sentence. The exact-colour counts are 0/7/7; within a colour
       distance of 20 they are 0/11/8. W1-09 stays FAIL.
     - Round 2's record says "(both lanes)" for "could not have failed". Only Lane 10-R2B said so, about a W14
       cascor restart; Lane 10-R2A disagreed.
     - F-CANOPY-057's Severity bullet: "still promises" becomes "promised (until canopy#684)".
   - **Lane 10-R3B DID finish** (SOUND-WITH-FIXES). Its report is the final message in that transcript, so do
     NOT re-run it. Re-derive its points, which agree with R3A's and extend them:
     - **(MAJOR)** F-067's zeros persist in the Full History and Between Hidden Units views. `extendTraces` has no
       display-mode check (`metrics_panel.py:1015-1142`, `:1037`), and in those views nothing redraws the store
       while cascor is idle. Hold a second page in Full History through the deciding drive.
     - Run the rating drive on UNFIXED `main` before item 18's fix, since a fixed build cannot show P1.
     - W8 step 13 is a no-op unless the recurrence leg is up (`--with-recurrence`; `settings.py:262`,
       `main.py:4086-4089`).
     - Phase 1's Accuracy point is hidden under the ROC-AUC and Recall markers. Its exact-colour counts are
       0/7/7.
     - F-057 is still called P1 as current state in its Severity bullet and in Phase 9's item 15.
     - F-065's condition was not carried into 4 places (:9794, :9814, :9834, :10343).
     - Round 2's "both lanes" attribution is wrong.
   - Script the pass as `util/ad-hoc/2026-10-04_phase10_ledger_round3_corrections.py`, in the same style as rounds
     1 and 2. Replace `ROUND3_PENDING` with round 3's record, then freeze and run round 4, narrow, on that diff.
2. **Land Phase 10.**
   - `git fetch origin main` and `git rebase origin/main`. main had one unrelated commit, `bba22f4a`.
   - `gh api -X POST repos/pcalnon/juniper-ml/git/refs -f ref=refs/heads/docs/canopy-e2e-phase10 -f sha=<main full sha>`.
   - `python3 util/ad-hoc/2026-09-24_push_phase9_signed_groups.py --base <main full sha> --branch docs/canopy-e2e-phase10`.
     It refuses a dirty tree, including untracked files.
   - `gh pr create --base main --head docs/canopy-e2e-phase10` with the body
     `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/pr_body_phase10.md`,
     which is tmpfs. If that file is gone, rebuild the body from the ledger's Summary.
   - `util/wait_for_checks.py`, then `util/safe_merge.py --execute`; read the `MERGED` line, not the exit code.
3. **F-058 census v2 (item 3).** The drafts are in `/home/pcalnon/Development/python/Juniper/backups/2026-10-04_f058_census_v2_drafts/`:
   `shim.py`, `synth_app.py`, `synth_check.py` and `census_live.py`.
   - The shim wraps `window.store.dispatch` through an init-script trap on `window.store`. It scores A (taken),
     X (pruned: an eviction) and R (re-added), and records each watchdog fire at its write, with the lane's
     state before it.
   - `synth_check.py`: 6 of 6 known-answer cases pass. Data and `no_update` controls give 0 evicted, with 13
     store changes counted independently. A second-Input change mid-request evicts every later request. The
     watchdog's fires are caught.
   - **New lead, from the synthetic app only:** with canopy's own wiring, the gate's MOUNT write re-enables the
     lane while a 3 s first request is in flight, and the cascade starts at page load.
   - Move the drafts to `util/ad-hoc/2026-10-04_f058_census_v2_*` on a branch from main. `census_live.py`'s
     T-tab should reuse `e2e_f027_redrive.open_tab`.
   - Run against a verify leg: `util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <canopy tree at main>/src <port>`,
     pass `JUNIPER_CANOPY_GIT_SHA` for a tarball tree, and export `JUNIPER_E2E_CANOPY_URL`. It reads the trio
     read-only. Never use `:8051`.
4. Then items 4, 5 and 7, and the owner batch O2–O16, from the parent. New owner question: is a CHANGELOG or
   design-plan promise "documented" under plan §6.3? If not, F-CANOPY-065 is P2.

**Traps learned:**

- The worktree guard refuses `$(…)`, loops, computed paths after `sed`, and long heredocs. Use plain commands or
  scripts.
- `pre-commit` fixes land in the worktree: re-`git add`. Plain `pre-commit run` checks only staged files.
- Lanes printed the owner's e-mail with `git show --stat`; forbid author fields in every brief.
- The link-set tool's `unreachable` view is blind to `[[name-slug]]` links. That caveat is now in
  `feedback_memory_index_target_is_20kb.md`.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-juggling-spring
git status --short; git log --oneline -6        # docs/canopy-e2e-phase10, clean, on 0d3c337b + this commit
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 78 / 53 / 1 / 2 / 22; P1 6; P2 16
gh api repos/pcalnon/juniper-ml/commits/main --jq .sha
ss -ltnH | grep -E ':(8101|8202|8051) '         # the trio: never touch
ls /home/pcalnon/Development/python/Juniper/backups/2026-10-04_f058_census_v2_drafts/
wc -m ~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md
```

## Git state

- juniper-ml: branch `docs/canopy-e2e-phase10` in worktree `clever-juggling-spring`, local only, nothing pushed.
  No PR is open from this session.
- canopy, cascor and data: no branches; read-only pins `1b2dd438`, `95cdc562` and `29be6d35`.
- Lane 10-R2B saw `juniper-canopy/.git/config` change at 17:13:33 during its run. The cause is unknown.

## Changed by this session

- **New:**
  - this handoff;
  - the archived predecessor A;
  - `util/ad-hoc/2026-10-04_phase10_{f060,o2,o3}_rederive.py`;
  - `util/ad-hoc/2026-10-04_phase10_ledger_round{1,2}_corrections.py`;
  - `util/ad-hoc/2026-10-04_archive_phase10_lane_probes.py`;
  - `util/ad-hoc/2026-10-04_phase10_r1_*` (25 files);
  - `reports/e2e-canopy-2026-09-02/drafts/lane10{A1,A2,B1,B2,R2A,R3}_*.md` and `lane10R2B_*.md`;
  - `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round{1,2}.md`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`.
- **Auto-memory, outside the repo:**
  - `MEMORY.md`;
  - `feedback_memory_index_target_is_20kb.md`;
  - `project_gitleaks_node24_override_followup.md`;
  - `project_ecosystem_ci_latent_risks_2026-04-10.md`, moved to `memory/retired/`.
