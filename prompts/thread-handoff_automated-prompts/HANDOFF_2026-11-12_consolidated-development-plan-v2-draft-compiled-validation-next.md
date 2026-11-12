# Thread handoff: consolidated development plan — the v2 re-plan is drafted and NOT validated; validate it, reconcile, then take its rulings to the owner

**Written**: 2026-11-12 about 02:25Z (2026-11-11 in America/Chicago) by session `64ddc378` (named "consolidated development project"), in juniper-ml worktree `.claude/worktrees/vectorized-wandering-planet` on the Linux host. The owner asked to pause the arc; nothing below was cut short by a limit.
**Continues**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md`, which session `560c1ec5` consumed (v1.14.0 landed as juniper-ml#2318 on 2026-10-24). No handoff of this arc lies between that one and this.
**Merge approval**: none was given in this session. It opened one PR and merged nothing.

## Goal statement (paste as the new thread's first prompt)

```text
Continue the consolidated-development-plan arc from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-12_consolidated-development-plan-v2-draft-compiled-validation-next.md. Read it in full, then
notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md ("v2"). Run the verification
block first. Ask the owner for this session's merge approval before any merge: none carries over.

Completed so far:
- Status established. The plan of record, notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md
  ("v1", v1.15.15), was validated in 14 rounds and landed (ml#2214, ml#2318). Since 2026-10-24 no session has owned
  it: its fifteen v1.15.x records cover P12 and R-OBS-SC-2 only, its other ten paths are stale since 2026-10-10,
  and the re-plan it prescribes after Wave 1 never ran.
- A paged, read-only probe: util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py (self-test 24 of 24), and
  its two outputs of 2026-11-12T02:09Z under reports/2026-11-12_consolidated-development-plan-v2/.
- v2, a DRAFT re-plan: state of 17 paths with sources, v1's Waves 0-1 item by item, what decayed, the order of
  work, the release train and one owner packet. Its header and Validation record say it is not validated.
- One PR carrying v2, the probe, the two outputs and this handoff, on branch
  docs/consolidated-plan-v2-draft-2026-11-12. Not merged.

Remaining work, in order:
1. Find the PR's state (verification block). If the owner's sweeper merged it, every later edit is a new PR.
2. Re-run the probe; where a number moved, update v2's rows and the files under reports/.
3. Validate v2 with two independent reviewers, per notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-
   CONSENSUS-PROCEDURE.md: Lane A re-derives a stated sample of v2's [P] and [H] rows from their sources; Lane B
   attacks section 4's order and section 6's packet. Check ListAgents first; launch nothing while another arc
   runs a round. Give each lane a hard sample size and have it write findings to disk as it goes.
4. Re-derive every finding at its source before applying it. Record the reconciliation in v2's Validation
   record and in a round1-reconciliation.md beside the probe outputs. Flip v2's Status only then.
5. Confirm section 3's "no record" rows with each path's live session before anyone acts on them: they are
   title searches. The losses of section 3.5 (v1's XC-PRESERVE rows j, k, l and g) need the same check.
6. Put section 6.4's six items to the owner (who takes the unowned P3 gates; whether v2 becomes the planning
   surface; resume or park P5 to P10; the four losses; the cleanup signal; juniper-harcot in the sweeps), and
   section 6.1's and 6.2's lists only as a map: each of those is its own arc's to ask.
7. Archive the next handoff, and give this one a CONSUMED banner in that PR.

Key context:
- Do not edit v1. Session 6e3bdef0 (R-OBS-SC-2's follow-ups) owes v1.15.16 in that file.
- Four arcs had live sessions on 2026-11-12: backup Phase D, canopy Phase 16, flood 4 and R-OBS-SC-2's
  follow-ups. v2 is a map of them, not an instruction to them.
- What v2 found that the owner has not been told elsewhere: the XC-LEAKS repository settings are unchanged
  after 39 days and juniper-recurrence still runs no gitleaks; three sets of transcripts v1 wanted archived
  have expired, and one scratchpad's files are gone; eight P3 gate items (P3-01, -02, -03, -05, -06, -08, -09,
  -11) have no PR and no session, and they gate juniper-data 0.18.0 and the next cascor release; P5 to P10 have
  been idle five to seven weeks; canopy's Phase 16 exists in one local unsigned commit.
- The account's weekly usage limit stopped at least seven agents on 2026-11-09; its reset was 2026-11-12 03:00Z.
```

## Traps met in this session

- **The juniper-ml primary checkout sits on juniper-ml#2360's branch.** Its `notes/` and `util/` are that branch's, not `main`'s: `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md` and `util/tmp_path_literal_check.py` exist there and not on `main`. Read `origin/main` from your own worktree.
- **v1's census reads one page of 50 commits per repository**, and prints "a full page of 50: more may have merged" when it fills. Over a month juniper-ml and juniper-canopy fill it; use the new probe.
- **A probe line like `cursor[bot](draft)=40` fails the doc-link hook**, which reads it as a link. The probe now prints `/draft`.
- **`pre-commit run --files` skips `notes/` and `util/ad-hoc/` for markdownlint, Black, Flake8 and MyPy** (out of those hooks' scope), so its green there proves nothing. Check the 512-character limit with `awk 'length($0) > 512'`.
- **The isolation guard** refuses `git -C` into another checkout and any loop or `$(…)` around git. Run one plain git command per call, or put the logic in a script. A `cd` inside a call persists to the next call.
- **Write and Edit refuse the primary checkout's `tmp/`**, where the scratchpad lives; use the worktree's `tmp/`.
- **`util/open_signed_pr.py` opens a ready PR**, and the owner's sweeper may arm it. v2's header says DRAFT, NOT VALIDATED so that a merge of it stays honest.

## Verification commands (one per call)

```bash
git fetch origin
git log -1 --format='%h %s' origin/main
gh pr list --repo pcalnon/juniper-ml --head docs/consolidated-plan-v2-draft-2026-11-12 --state all --json number,state,mergedAt,autoMergeRequest
python3 -B util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py --self-test                      # 24 of 24 pass
python3 -B util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py --since 2026-10-10T21:30:00Z      # exit 0; compare with the saved output
command grep -c 'DRAFT, NOT VALIDATED' notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md   # 1 until validated
command grep -c 'Version\*\*: 1.15.1[56]' notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md  # 1
awk 'length($0) > 512' notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md                 # prints nothing
```

If the PR is not merged, the files are on its branch and in this session's worktree, not on `main`: read them with `git show origin/docs/consolidated-plan-v2-draft-2026-11-12:<path>`.

## Git state

- **Worktree** `.claude/worktrees/vectorized-wandering-planet`, branch `worktree-vectorized-wandering-planet`, fast-forwarded to `348777f4` (`origin/main` at 2026-11-12T01:36Z). No local commit. The five files below are untracked there and identical to the PR's.
- **The PR** was opened from `origin/main` through `util/open_signed_pr.py` (one signed API commit). Its number is in the verification block's third command.
- **Scratch**, kept under the retention rule: the worktree's ignored `tmp/cdp-v2/` (the PR body, the commit body, the gate's scan copies), and this session's scratchpad `census/` (v1's census output and juniper-ml's merge list for the window). `git worktree remove` deletes the first.
- **Host**: nothing was changed. The session read GitHub and PyPI, listed directories, and counted transcript files by date.

## Documents referenced / changed

- **Referenced**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.15) and `reports/2026-10-04_consolidated-development-plan/`;
  - `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`;
  - `util/ad-hoc/2026-10-05_ecosystem_live_census.py`;
  - the handoffs v2 reads, each also named in v2's "Documents referenced" table:
    - `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`;
    - `HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md`;
    - `HANDOFF_2026-10-30_turing-check-wording-fixed-owner-steps.md`;
    - `HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md`;
    - `HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md`;
    - `HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md`;
    - `HANDOFF_2026-11-12_canopy-phase16-round33-frozen-round34-relaunch-next.md`;
    - `HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md`.
- **Created** (all in the PR):
  - `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md`;
  - `util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py`;
  - `reports/2026-11-12_consolidated-development-plan-v2/state-probe.txt` and `state-probe-with-merges.txt`;
  - this file.
- **Modified**: nothing. No auto-memory file was written.
