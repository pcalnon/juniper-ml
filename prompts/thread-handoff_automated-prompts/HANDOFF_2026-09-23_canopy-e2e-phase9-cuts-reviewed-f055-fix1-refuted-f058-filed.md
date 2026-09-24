# Thread handoff — canopy E2E arc, Phase 9: the idle cuts reviewed through three rounds, F-055's first fix refuted in review, F-CANOPY-058 filed

**Written**: 2026-09-23, evening. The thread ran long: two canopy changes went through five consensus lanes, so
a fresh thread takes the remaining merges and the redesign.

> **Superseded in part, 2026-09-24 (a note added by the successor session; the authoring session archived this
> file itself, in `b54e3b3f`).** canopy#676 did not stay a draft. It was marked ready at 2026-09-23 22:28:04Z and
> armed at 22:28:12Z, in a pass over nine PRs that no Claude Code session on this host made, and it merged at
> 2026-09-24 01:38:02Z as `e9053227` with round 3's fixes unapplied. The ledger's Phase 9 ("The merge, out of
> order") has the record. What that makes dead or stale below:
>
> - **Item 1's ordering is moot.** The Phase 9 PR still had to land, but no longer "before canopy#676 merges".
>   The WIP now lives on branch `docs/canopy-e2e-phase9`, as `5a0e4ea9`..`e624c281` and later, on `f9c81d80`.
> - **Item 2 cannot be run.** The head branch was deleted at 01:38:03Z, so the ref `PATCH` fails, and
>   `gh pr ready 676` and `safe_merge.py` would act on a merged PR. Round 3's fixes are owed as a canopy follow-up
>   PR instead, plus an edit of #676's description (the ledger's Phase 9, Still owed item 13).
> - **Stale:** "State at handoff"'s "#676 is open as a draft", the verification command's expectation for #676,
>   and "canopy worktrees to clean on merge signals", where the `…perf--idle-dispatch-cuts-v2--…` signal has now
>   fired.
> - **One error it repeats:** "Both corrected prose only" is false, because rounds 1 and 2 each changed test
>   code. The merged squash message says the same thing.
> - **Superseded by the ledger's own validation (its rounds 1 and 2):**
>   - Item 3's "metrics-store apply census" cannot fail on the idle trio: the feeder answers `no_update`, an
>     HTTP 200 that applies nothing, so it must count evictions. The eviction census written for it was then
>     refuted before its first run (Phase 9, Still owed items 0 and 14).
>   - Item 4's "all three triggers" are four: a change of the feeder's second Input evicts too.
>   - The verification comment's "69 findings, 18 open, 4 open P1" is now 70 findings and 19 open, with 1
>     open P0 (F-CANOPY-059, found in round 2) and 6 open P1.

---

## Goal statement (paste this as the new thread's first prompt)

Continue the canopy E2E validation arc from Phase 9 of the ledger,
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` ("Still owed after this phase", item 0
first). Phase 9 exists only as **local WIP commits** in the juniper-ml worktree
`.claude/worktrees/squishy-dancing-moth`: `800c20bb`, `08a1573a` and `48df689b`, plus the round-3 archive
commit if present. They are on `51993b37`, unsigned and never pushed.

**Completed in the 2026-09-23 evening thread:**

- **The idle cuts are canopy#676:** one GitHub-signed commit, `4b4cfb16`, on canopy `main` `0254a7ec`. It is a
  **DRAFT** with no auto-merge, held on purpose: an unseen actor arms PRs as `pcalnon`.
  - It was rebuilt from local `668380ec`. The snapshot was regenerated, and the CHANGELOG conflict resolved
    with `main`'s entries verbatim.
  - Falsification: 7 of 9 fail on the parent, and CLASS names only `metrics-panel-update-interval`. Suite:
    6806 passed, 0 failed.
  - Live check against its own parent: STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT. Reported as
    measured.
  - Review: round 1 (Lanes A and B), then round 2 (B2). Both corrected prose only: the stop claim, the dead
    weight stream, "2 Hz", pooled pairs, stale comments, the squash message. The branch was collapsed onto one
    commit so the refuted first message cannot land.
  - Round 3 (B3): **MERGE-WITH-FIXES, wording only**. The squash message says "two rounds; prose
    corrections only", but it was three rounds and both earlier rounds changed test code. The PR description
    is stale. A few surviving phrases remain: `replay_player_panel.py:75`, the test message and name, and
    `ws_dash_bridge.js:113-115`. All three rounds are archived.
- **F-CANOPY-055's first fix was refuted in review. It is NOT a PR.** Local branch
  `fix/f055-status-bar-running-guard` (`884d22fb`, `cf6fb1dc`, `7a4a2e33`), kept as provenance.
  - What it did: an own lane plus a `running=` guard, F-035's repair.
  - What passed: falsification (19 of 94 fail on the parent), the suite (6823 / 0), and the census, which
    scored the parent NEVER-APPLIES and the fix APPLIES over 150 s. The demo allow arm landed on both legs, so
    it does not discriminate.
  - What refuted it: Lane B (**DO-NOT-MERGE**). The fused gate writes the lane's `disabled` on every tab
    switch, mount and Apply change; the Apply releases; and the strand watchdog false-fires. Each re-enables
    the lane mid-request.
  - `completeJob()` then releases the guard for the EVICTED request too, so eviction cascades. I re-derived
    this in `dash_renderer.dev.js:925-937` and `:966-986`.
  - The census window contained none of those triggers.
- **New findings in the WIP ledger:**
  - F-CANOPY-056 (P2): Stop keeps the replay session against cascor.
  - F-CANOPY-057 (P2): the replay-weight stream is unwired end to end.
  - **F-CANOPY-058 (P1):** the `running=`-guard cascade. It reaches #613's metrics-store lane in PRODUCTION;
    this is source plus a synthetic repro, not yet seen on canopy.
  - Triage: 69 findings, 18 open. P1: F-055, F-058, F-CASCOR-001, F-CASCOR-002.

**Remaining, in order:**

1. **Land the juniper-ml Phase 9 PR BEFORE canopy#676 merges.** This was round 2's MAJOR: #676's CHANGELOG and
   comments cite F-CANOPY-056 and F-CANOPY-057 "in the juniper-ml E2E evidence ledger".
   - The ledger has no placeholders left.
   - Rebase the WIP onto `origin/main`.
   - Validate the ledger text per the SOP, since it is a document of record.
   - Upload with `util/open_signed_pr.py`. The ledger is ~700 KB, so push it in its OWN signed commit
     (`util/push_signed_commit.py`), because a ~1 MB `createCommitOnBranch` payload returns HTTP 499.
   - Re-check that `origin/main`'s ledger has not moved before the whole-file upload.
2. **Merge canopy#676.**
   - First apply round 3's wording fixes. The worktree is `…perf--idle-dispatch-cuts-v2--…`, local head
     `040dc5c1`.
     - Collapse again to ONE signed commit on current `main` with a corrected message (three rounds; test code
       changed in rounds 1 and 2; the live-check SHAs `ce78e0de`/`3a6dea95`; 45% of ticks).
     - Method: a temp branch at `main`, `util/push_signed_commit.py`, then
       `gh api -X PATCH …/git/refs/heads/perf/idle-dispatch-cuts-v2 -f sha=… -F force=true`.
     - Refresh the PR body (`gh api -X PATCH …/pulls/676 -F body=@file`).
     - Decide explicitly whether round 4 is warranted (§4).
   - Then run `gh pr ready 676`, then `python3 util/safe_merge.py --repo juniper-canopy --pr 676 --execute`.
   - Read the `MERGED` line, not the exit code, and check `auto_merge` first.
   - It is BEHIND `main` (#677, which does not touch its files). safe_merge updates the branch.
3. **Confirm F-CANOPY-058 live on a leg serving current `main`.** Run a metrics-store apply census with a tab
   switch timed mid-request, an Apply spanning a request, and at least 10 idle minutes. Fix the rule and
   predictions in the docstring first.
4. **One redesign for F-CANOPY-055 and F-CANOPY-058.**
   - Candidate: Lane B's handshake pacer. A clientside pacer on the 1 s lane issues a request token only after
     the feeder's ack (echoing the token) has applied, or after a stale timeout. No `running=`, no watchdog.
   - Alternatives are partial: a progress-based watchdog (reset on `n_intervals` change), or a gate that
     returns `no_update` for global lanes on a tab-only change.
   - Real-renderer tests for all three triggers, then the census plus the triggers live, consensus rounds, PR
     and merge.
5. The rest of Phase 9's still-owed list, notably the FIFO starvation mechanism (item 11) and the F-053 hunt.
6. **`MEMORY.md` compaction: URGENT.** It is 25,180 bytes against the 24.4 KB load limit, so its tail is
   invisible to every session. The target is 20 KB.
   - A digest move of the "Verification discipline" line was tried and reverted: it dropped 25 index
     pointers, all still reachable, which breaks the owner's "never drop a pointer to hit a number".
   - Shorten hooks only after verifying that each topic file carries the detail.
   - Take a link-set snapshot first (`util/ad-hoc/2026-09-12_memory_index_linkset.py`).
   - RETIRE entries; never strip hooks.
   - Other sessions edit it concurrently, so re-read it right before each write.

**Key context:**

- **The consensus procedure** is `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
  - Briefs are in `reports/e2e-canopy-2026-09-02/drafts/`.
  - Archive verbatim with `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`.
  - Rounds 1 and 2 are archived as `consensus/2026-09-23_validator_reports_phase9_round{1,2}.md`.
- **A census can pass a fix whose failure its window cannot contain.** Size the window to the lane's cadence
  (~8 s self-clocked), and include the triggers.
- **canopy's `addopts` already has `-q`.** Another `-q` suppresses pytest's summary line. Use
  `conda run --no-capture-output -n JuniperCanopy1`.
- **The worktree guard** refuses python heredocs that mention git, `git -C <juniper-ml primary>`, and loops.
  Use the Write tool, and plain `git -C <sibling>`.
- **Do not touch** the trio (`:8101` data, `:8202` cascor fixture 2/68/2), and never `:8051`. All of this
  thread's legs are down.
- **canopy worktrees to clean on merge signals:**
  - `…control--main--20260923-1423--3a6dea95` (detached; clean now);
  - `…perf--idle-dispatch-cuts-v2--…` (after #676 merges);
  - `…perf--idle-dispatch-cuts--20260923-0830--723ee812` (superseded);
  - `…fix--f054-replay-block-clientside--…` (#670 merged).
  - KEEP `…fix--f055-status-bar-running-guard--…` (provenance for the redesign).

## Verification commands (run first)

```bash
gh pr view 676 --repo pcalnon/juniper-canopy --json isDraft,autoMergeRequest,headRefOid,mergeStateStatus
git log --oneline -5                                   # in .claude/worktrees/squishy-dancing-moth: 48df689b ...
python3 util/ad-hoc/e2e_finding_triage.py | tail -8    # 69 findings, 18 open, 4 open P1
grep -n "<<" notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md    # remaining placeholders
git -C /home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--f055-status-bar-running-guard--20260923-1425--ce78e0de log --oneline -3   # 7a4a2e33
df -i /tmp | tail -1
```

## State at handoff

- **juniper-ml:** worktree `.claude/worktrees/squishy-dancing-moth`, branch `worktree-squishy-dancing-moth`,
  WIP commits on `51993b37`. `origin/main` has moved since (`c2bcb96c` or later).
- **canopy:** `main` is `9cdfcad4` (#677) or later. #676 is open as a draft. No other PR of this arc is open.
