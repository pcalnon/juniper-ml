# Handoff: R-OBS-SC-2 follow-ups -- juniper-ml 0.11.5 at the owner's `pypi` gate; the guard + register PR, two consumer cuts, the 0.4.3 design prompt and plan v1.15.16 remain

**Written**: 2026-11-13 10:40Z by session `218ff61e` (listed in `ListAgents` as
`r-obs-sc-2-follow-ups-five-prs-validated-opening-next`, ref `13c125`), which ends with this file.
**Predecessors** (both on `main`; this file points into them instead of repeating them):

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-five-prs-validated-opening-next.md`
  (below, "the five-PRs handoff");
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md`
  (below, "the four-ruled handoff": round 1's four rulings verbatim, "How to change a fork", "Traps").

**Working records** (gitignored; keep both until plan v1.15.16 has merged): `tmp/fsf/WORKING_RECORD.md` in worktree
`.claude/worktrees/foamy-squishing-floyd`, and `tmp/lps/fixpass_r1.md` in worktree
`.claude/worktrees/logical-percolating-sparkle`.

**How far to trust this file.** Each state fact below was read from git, `gh`, PyPI or the disk on 2026-11-13: between
10:11Z and 10:40Z unless its line gives another time. `tmp/fsf/handoff_claims_check.py` (in the first worktree above)
re-derives 75 of them, and all held at 10:40Z. Five of the 75, marked `[moves]`, describe state that the owner's
approval or a later merge changes. `tmp/fsf/handoff_text_check.py` compared each quoted ruling with the transcript,
and each named path with the disk. One independent fact-checker then re-derived what those two do not cover; its
findings are applied. A time is given only where a tool printed it. What this session was told by another, and did
not re-derive, is marked "reported". Not checked by anyone but this session: that both review rounds ran on Opus.

## Goal

Finish the R-OBS-SC-2 follow-ups. In order: see juniper-ml 0.11.5 through its gate and its two post-publish edits;
open the guard and register PR for `APD-ECO-016`, which is now unblocked; prepare the juniper-cascor and
juniper-canopy releases the owner ruled on 2026-11-13; write the start prompt for the juniper-observability 0.4.3
design session; and record all of it in plan v1.15.16.

**First turn**: ask the owner for merge approval for a named group (the guard + register PR, the post-publish docs
PR, the two consumer release PRs and their archive PRs, the plan v1.15.16 PR). Approvals are per-session. This
session's ("merge approval granted", 2026-11-13) does not carry.

## Owner rulings of 2026-11-13 (session `218ff61e`; label and option text verbatim; answer times from the transcript)

1. **0.11.5** (01:57:00Z): "Yes, as patch 0.11.5 (Recommended)" -- "This session writes the co-change tool, opens and
   merges the proposal PR (removing the two interim clauses the floor PR added to docs/REFERENCE.md), cuts the GitHub
   Release, opens the archive PR, and stops at the pypi gate, which you approve."
2. **Worktrees** (01:57:00Z): "Remove after checks (Recommended)" -- "For each: confirm the PR is MERGED through the
   API, confirm its edits equal main's files, check its tmp/ against the retention rule, then git worktree remove and
   prune. The never-opened juniper-data worktree and the two juniper-ml session worktrees stay."
3. **How to re-ask round 2** (01:57:00Z): "One at a time, with background" -- "Each question comes on its own, opened
   by a short plain-language account of what it decides, what waits on it, and what each option would set in motion."
4. **Round 2 Q1, the 0.4.3 design** (02:14:33Z): "Now, in its own thread (Recommended)" -- "I write a start prompt
   for a fresh session. That session writes the design to notes/, runs its validation rounds, and brings you the
   design to rule on. Implementation, the 0.4.3 release and the third lock round follow that ruling. Cost: one design
   plus review rounds, on whichever model has quota (the flood-4 session reports the weekly Fable limit was reached
   today)."
5. **Round 2 Q2, lock cuts** (02:28:23Z): "cascor + canopy now (Recommended)" -- "This arc's fixes are merged in both.
   A session prepares a cascor release and a canopy release from main, each raising its floors in the release PR; you
   approve each pypi gate; then juniper-deploy pins the two images and the stack restarts. cascor is cut ahead of
   P3-05 and P3-08 again. data waits for 0.18.0, recurrence for its next release."
6. **Round 2 Q3, the restart gate** (02:40:52Z): "Probe per environment" -- "After you upgrade the three environments,
   a session re-runs the probe in each and records the result. The restart then proceeds on that record, on P3-05, and
   with blank Sentry DSNs. The F-S10 relays stay untested until the relay tests exist."
7. **Round 2 Q4, the juniper-ml primary** (asked 02:41:20Z, answered 10:10:51Z): "Guarded session pulls
   (Recommended)" -- "O13's rule extended to juniper-ml: a session may fast-forward it to origin/main only when it is
   on main and clean, after checking listening ports, process working directories and the run directories' pid files
   show no live stack imports it, and it records the pull (time, from and to commits). Sessions never switch its
   branch. Your own moves stay free."

Two notes on reading them. Ruling 7 replaces, for the juniper-ml primary only, the four-ruled handoff's trap "Never
pull or switch a primary checkout"; the juniper-canopy primary is still unruled (below). Ruling 6 names only what
stands in for the relay tests. Nothing in it touches the rest of security step 5, which includes that the session
records the commit the editable installs run, not pip's version (the four-ruled handoff, Q3, "New since").

Round 2 is complete: nothing of it is left to ask. Each question's full text, with the background the owner read,
prints with `python3 util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py 218ff61e --full`. Until plan v1.15.16 they are
recorded only here, in that transcript and in `tmp/fsf/WORKING_RECORD.md`.

## Completed this session

- **juniper-ml#2558 merged** (10:08:14Z, `main` `48b66130`): the 0.11.5 proposal (`8764f5cf`) and one co-change commit
  (`d4dcefbc`), made by `util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py`.
  - `docs/REFERENCE.md`: the Version cell and line 184; the two interim clauses of juniper-ml#2555 are gone.
  - `CHANGELOG.md`: juniper-ml#2360's Fixed bullet re-homed from the released `[0.11.4]` to `[0.11.5]`; five entries
    that merge had moved from Added to Changed put back; six sentences reworded.
  - Two independent review rounds (Opus) came first. Two update-branch merges (09:54:44Z, 09:55:16Z) and an auto-merge
    armed at 09:55:09Z by `pcalnon` landed it while this session sat in the Q4 dialog; none was this session's.
- **Release `v0.11.5` cut** at 10:24:18Z on `48b66130` (`ceremony.py --target-sha`). `releases/latest` is `v0.11.5`.
  Its body equals the notes with the security header filled by
  `util/ad-hoc/2026-11-13_juniper_ml_0_11_5_security_notes_header.py`, and holds no placeholder.
- **Publish run 43408809021** (created 10:24:20Z): Build and Validate and Publish to TestPyPI succeeded, and Publish to
  PyPI waits at the `pypi` gate. **The owner approves it; no session does.** The working deadline is 2026-12-13 (day
  30) and the run is cancelled by 2026-12-18 (day 35).
- **Archive PR juniper-ml#2561 merged** at 10:38:29Z as `main` `7ae846b6`. `notes/releases/RELEASE_NOTES_v0.11.5.md`
  on `main` is byte-identical to the Release body.
- **Four merged fork worktrees removed** (juniper-cascor#755 and #757, juniper-canopy#816 and #817) after
  `tmp/fsf/fork_worktree_check.py` showed each edited file's blob equal to its PR's signed commit.
- **Two peer sessions were messaged that the tag exists**: the flood-4 arc
  (`flood4-session6-four-landed-rulings-19-29-fable-limit-five-agents-dead`) and the backup arc
  (`backup-phase-d-sitting-steps-11-13-done-ac4-drill-next`). This session had asked both to hold their juniper-ml
  merges until the tag existed, and that message released them. Each files its CHANGELOG entries under the now-empty
  `[Unreleased]`.

## Remaining work

1. **0.11.5 after the gate.** Once `https://pypi.org/pypi/juniper-ml/0.11.5/json` answers 200 and its `requires_dist`
   holds `juniper-observability>=0.4.2; extra == "tools"`:
   - open one docs PR: `docs/QUICK_START.md` lines 85 and 102 still show the 0.11.4 sample `pip list` (precedent
     juniper-ml#2510);
   - the parent `Juniper/AGENTS.md` paragraph that names the latest juniper-ml on PyPI still says 0.11.4. That file is
     unversioned, and the owner approves the edit, as for 0.11.4.
2. **Guard and register PR, `APD-ECO-016`.** Unblocked: juniper-data#537 merged at 02:54:07Z as `3cf8867c`. Follow
   "Remaining work" item 1 of the five-PRs handoff. What it needs from here:
   - The guard (`retry-after-rounds-up`; register ids `APD-ECO-016` and `APD-SVCCORE-004`) is still uncommitted in
     `.claude/worktrees/logical-percolating-sparkle`, whose session has ended:
     `tests/test_service_fork_drift.py` (sha256 `98ead3169bcc1fbe…`; 78 changed lines against `main`, whose copy has not
     changed since `9238be21`) and `util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py` (sha256
     `6cf393ce32bf9d76…`). Check both hashes, then copy the files into your own worktree.
   - The mutation check's pre-fix commits are the parents of the three fixes:
     `--main-ref main --prefix juniper-cascor=44b60af28d1741d828f66375e58f333862c8fa29 --prefix juniper-canopy=b9417b2f29ba059b645d96c405625be0a5399027 --prefix juniper-data=c68e6b4c8e17be71be1bef1d0dcb6ac213505d6e`.
   - No independent reviewer has read the guard. Have it reviewed before the PR opens.
   - On `main`: the register has no `APD-ECO-016`; `docs/REFERENCE.md` line 3733 says "all eight guards are `ENFORCED`"
     and its document version is 0.6.69 (take the next free number at freeze). The CHANGELOG entry goes under
     `[Unreleased]`.
   - Reported by flood-4, not re-derived: `util/ad-hoc/2026-11-12_fork_retry_after_round_up_mutation_check.py` kills
     all 25 mutants on juniper-data, but its pre-fix case reads SURVIVED there, because juniper-data's helper-floor
     test is named `test_the_helper_floors_a_zero_remainder_at_one`.
3. **The juniper-cascor and juniper-canopy releases** (ruling 5). Not started.
   - Each is cut from its `main`. Its release PR raises `juniper-observability>=0.4.2` and
     `juniper-service-core>=0.7.2` (round 1's ruling 1, in the four-ruled handoff). The owner approves each `pypi`
     gate. Then juniper-deploy pins the two images, and the owner restarts the stack.
   - Ask the owner each version first. The detector's proposal does not bind: for juniper-ml 0.11.5 it proposed
     0.12.0, and the manifest was set to the patch by hand.
   - Section 11.7 of `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` is the procedure
     (`--cross-repo`, `--target-sha`, the tag-window and released-section checks). The four-ruled handoff's "Traps"
     says which branches a consumer's lockfile workflow skips.
   - Measured on 2026-11-13 between 02:14Z and 02:24Z, so re-measure: juniper-cascor `main` was 27 commits past
     `v0.13.0`, and juniper-canopy 58 past `v0.9.0`.
4. **The start prompt for the juniper-observability 0.4.3 design session** (ruling 4; the plan's R-OBS-SC-3). Not
   written. Its sources: the plan's section 5 row "R-OBS-SC-3" and its XC-SENTRY mitigations (a) and (b), and "Still
   open, for 0.4.3" in `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`.
5. **Plan v1.15.16**, written into v1 (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`,
   at 1.15.15). The v2 draft (`notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md`) says so
   itself, in its header and in item 20 of its section 6.4 (the header cites that item as "§7.4"). The method is item
   3 of the five-PRs handoff. Record:
   - round 1's four rulings and the five PRs (the five-PRs handoff's table);
   - the seven rulings above. Ruling 7 extends O13 to the juniper-ml primary, ruling 6 changes security step 5's
     condition, and ruling 5 bears on P4 D-4 (canopy's second cut) and D-5 (cascor's cut timing): it cuts cascor
     ahead of P3-05 and P3-08;
   - 0.11.5: juniper-ml#2555, #2558, Release `v0.11.5`, run 43408809021, #2561 (`7ae846b6`);
   - `APD-ECO-016`, once filed;
   - the eight findings listed under item 3 of the five-PRs handoff. Before recording its fifth (the WebSocket
     `retry_after` reading 0.0) as open, read flood-4's owner answer of 2026-11-12 23:34:04Z in session `f2b4e7c3`
     ("WebSocket gaps beside N-4, Lifecycle races beside N-2, Match cascor's resume answers");
   - new this session: juniper-ml#2360's merge misfiled CHANGELOG entries in two ways (one bullet under a released
     heading; five entries under the wrong category), and `util/ad-hoc/2026-09-23_released_section_drift.py` sees only
     the first kind.
6. **Housekeeping.** Removing a worktree needs the owner's word, worktree by worktree.
   - `Juniper/worktrees/juniper-data--fix--rate-limit-retry-after-round-up--20261111-1855--399eeffb` was never opened.
   - `.claude/worktrees/logical-percolating-sparkle` and `.claude/worktrees/foamy-squishing-floyd` hold the `tmp/`
     evidence named at the top.
   - The juniper-cascor and juniper-canopy primaries each keep the local branches `fix/fastapi-telemetry-opt-out` and
     `fix/rate-limit-retry-after-round-up`, left by the removed worktrees.

**Still open with the owner, and not asked this session**: who may pull the juniper-canopy primary (O13; the
four-ruled handoff, Q4, "New since"); whether a fix-forward is owed for juniper-cascor 0.12.0; A1's open limbs (the
data-client and cascor F-S10 fixes); and the trio's environment upgrade, an owner action
(`JuniperData` and `JuniperCanopy1` hold juniper-observability 0.4.0 and juniper-service-core 0.5.0, read from their
dist-info on 2026-11-13).

## Key context

- **The five-PRs handoff's "Key context" still holds in full**: bases move often, and its two upload tools guard
  against it; a mutation check writes over the real source file; the `Verify AGENTS.md Last Updated` date check.
- **Blank the six Sentry DSN variables for every test run**: `util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py`.
- **An owner dialog blocks the session until it is answered.** One held this session from 02:41:20Z to 10:10:51Z
  while two peer sessions waited on a message from it. Before asking the owner anything, give each waiting peer
  a condition it can check without you.
- **`origin/*` refs are shared by every worktree of the repository**, so another session's fetch moves your
  `origin/main`. Read `git rev-parse origin/main` immediately before a whole-file upload.
- **A session's `ListAgents` name can change mid-session.** This one's did. Give peers the `[ref]` as well.
- **Agents**: both reviewers ran with `model: opus`. Reported by flood-4 before 01:50Z: the account's weekly Fable
  limit had killed five of its agents at about 01:40Z. A sub-agent cannot write a report file here: have it return
  the report as its final message.
- **A cut needs both checks on the previous section**: the drift tool, and a read of the category headings against
  the parent of any long-lived PR's merge (`git show <merge>^:CHANGELOG.md`).
- This session's clock estimates, made without a tool, were hours off. Cite only a time a tool printed.

## Verification commands (one per call)

```bash
git fetch origin
git log -1 --format='%h %s' origin/main                 # 7ae846b6 at 10:39Z; later merges are expected
gh api repos/pcalnon/juniper-ml/releases/tags/v0.11.5 --jq '[.target_commitish, .published_at] | @tsv'
gh api repos/pcalnon/juniper-ml/actions/runs/43408809021/pending_deployments --jq '.[].environment.name'   # pypi, until the owner approves
gh pr view 2561 --repo pcalnon/juniper-ml --json state,mergedAt               # MERGED, 2026-11-13T10:38:29Z
python3 util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py --check     # exit 0; eleven lines "already at target"
python3 util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py 218ff61e           # five calls; the seven rulings
sha256sum /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/logical-percolating-sparkle/tests/test_service_fork_drift.py   # 98ead3169bcc1fbe...
gh pr view 537 --repo pcalnon/juniper-data --json state,mergedAt,mergeCommit
git show origin/main:notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md | command grep -c 'APD-ECO-016'   # 0 until filed
```

The cut-script check passes on any checkout that holds `48b66130`'s `CHANGELOG.md` and `docs/REFERENCE.md`. Once a
later merge adds an entry under `[Unreleased]`, it refuses (exit 2) by design, which is not a defect of the release.

## Git status (2026-11-13 10:39Z)

- Worktree `.claude/worktrees/foamy-squishing-floyd`, branch `worktree-foamy-squishing-floyd`, at `7ae846b6`, which
  was `origin/main`. No tracked change apart from this file, and nothing staged. This file lands through its own PR,
  which the owner merges.
- Open PRs of this arc: this file's only.
- juniper-ml#2548 (the backup arc's) is open and is not this arc's.

## Documents referenced / changed

- **Referenced**: the two predecessor handoffs named at the top;
  `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`;
  `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md`;
  `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (section 11.7);
  `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`;
  `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`; `docs/REFERENCE.md`; `docs/QUICK_START.md`; the
  parent `Juniper/AGENTS.md`.
- **Changed by this session**: through juniper-ml#2558, `pyproject.toml`, `CHANGELOG.md`, `README.md`, `AGENTS.md`,
  `docs/REFERENCE.md`, `util/ad-hoc/2026-11-13_juniper_ml_0_11_5_cut_cochanges.py` and
  `util/ad-hoc/2026-11-13_juniper_ml_0_11_5_security_notes_header.py`; through juniper-ml#2561,
  `notes/releases/RELEASE_NOTES_v0.11.5.md`; and this file.
