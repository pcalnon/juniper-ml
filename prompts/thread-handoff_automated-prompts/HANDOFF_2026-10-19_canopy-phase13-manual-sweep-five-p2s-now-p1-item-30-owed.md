# HANDOFF 2026-10-19 — P2 canopy Lane A: Phase 13 recorded. Item 26's first step is done: every open finding checked against canopy's manual; F-CANOPY-012, -013, -018, -028 and -032 are P1 by it (9 open P1, 11 open P2); four are fixed in code since canopy 0.7.0 and owed their live re-drive (item 30). Next are items 25, 27, 28 and 30.

**Written**: 2026-10-19 by the session in juniper-ml worktree `.claude/worktrees/federated-stargazing-blanket` on host
turing (macOS, no Juniper service, no reach to the trio), at a phase boundary, as its PR was opened.
**Consensus**: four rounds on 2026-10-19 (three lanes, then two on each correction pass); round 4 changed no number,
disposition or action, so the review ended there (ledger Phase 13, Consensus record).
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its item 4 is DONE; its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`.
**Merge approval**: the owner granted it in this session for this session's PR. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Items 25 and 28 need a canopy verify leg
against the trio (the Linux host, not turing); item 27 needs a demo leg that trains, never the trio; item 30's Network
Editor and Workers rows need a service leg with a writable or stoppable cascor (never the trio), and its Parameters
rows a demo leg; item 26's second step waits on the owner's ruling (O17).

**Completed:**

- **juniper-ml#2263 merged** on 2026-10-19T08:49:20Z: the ledger's Phase 12 and the previous handoff.
- **The ledger's Phase 13** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, 2026-10-19) does
  item 26's first step: every one of the 20 open findings checked against canopy's `docs/USER_MANUAL.md` at canopy
  `main` `571743db` (2026-10-17, the head after the v0.9.0 release), under §6.3 of
  `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (P1 = "breaks a documented behaviour")
  and the ledger's own precedents (F-CANOPY-056, F-CANOPY-057, F-CANOPY-064).
  - **Five re-ratings, P2 to P1**, each with a dated RE-RATED blockquote in its entry: F-CANOPY-012 (Patch Weights
    lists `output_weights`, entered as separated floats), F-CANOPY-013 (workflow step 6, confirm the edit from the
    status alert), F-CANOPY-018 (Apply "enables only when a value differs from the last applied set"), F-CANOPY-028
    (the pin set "survives a reload"; the narrowest, counter-reading recorded) and F-CANOPY-032 (the "Worker data
    degraded" alert "when the upstream call fails").
  - **Four are fixed in code**: canopy#532 (F-013), #533 (F-018, F-028) and #535 (F-012), merged 2026-08-28 and
    ancestors of v0.7.0 (published 2026-09-09); the CHANGELOG names none of them. Their entries stay OPEN until their
    rows are re-driven (item 30). **F-CANOPY-032 has no fix in code** (canopy#533 pinned its path only; Phase 4 found the
    source correct and suspected F-CANOPY-027's class, since FIXED); its re-drive closes or re-diagnoses it.
  - **The other fifteen stand**: ten not reached (F-CANOPY-001, -033, -034, -049, -051, -057, -060, -063, -066,
    F-ML-002); F-CASCOR-001/-002 P1 already; F-CANOPY-064 P1 on the manual already; F-CANOPY-065 not reached (its rating
    stays with the owner's first limb, which now decides it alone among the findings Phase 11 named); F-CANOPY-067
    "P2 pending a live drive", unchanged. One round-1 lane dissents on F-CANOPY-028 (P2) and on F-CANOPY-067 (P1 by
    source); both are recorded in the ledger's consensus record.
  - **Counts**: 79 findings, 56 fixed, 1 accepted, 2 withdrawn, **20 open**: 0 P0, **9 P1** (F-CANOPY-012, -013, -018,
    -028, -032, -064, -065, F-CASCOR-001, -002), **11 P2**. By the first limb's ruling: 9/11 or 8/12; the two recorded
    dissents would make it one P1 fewer (F-CANOPY-028) or one more (F-CANOPY-067).
  - **The CAN-015g/h design note** (`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`)
    carries the dated correction item 26 required: g-3 never reached cascor `main` (cascor#187 into
    `feature/can-015g-2-replay-weight-cache`; #190 into `…-v2`, 13 minutes after #189 had landed that branch on `main`;
    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s. The V7 roadmap's
    §28.1 (`notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`) and the 2026-05-05 audit's §5.2
    (`notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`), whose own §11.4 had confirmed only g-1 and g-6 on cascor `main`, carry the same dated
    correction (rounds 1 and 2), and the roadmap's CAN-015 row and the audit's §5.2 Status delta, §8.1 and §11.7
    rows point at it (rounds 2 and 3). canopy#535's residue is recorded in F-CANOPY-012's entry: by source the manual's
    semicolon and newline forms for `output_weights` are read as rows and rejected on any network with more than one
    output.
  - **New item 30**: the Phase 4 fix wave's live re-drive, owed since 2026-08-28 and carried by no Still-owed list
    from Phase 5's on.
- **This session's PR** carries the ledger, this file, the design note's, the V7 roadmap's and the audit's corrections, the parent's
  item 4 and O17, the INDEX's P2 row, the SUPERSEDED banner on the Phase 12 handoff, Phase 13's consensus records
  (briefs, verbatim reports, replayable passes) and the apply script `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`.
  Find it with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase13 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py`, query
   `reviewThreads(isResolved:false)` (a CodeQL thread blocks the merge while every check is green), ask the owner,
   then `python3 util/safe_merge.py --execute` and read its `MERGED` line. Afterwards re-check `origin/main` for the
   five headers (`grep -c 'P1 since 2026-10-19' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`
   should print 5): a concurrent whole-file upload of a shared file can revert merged lines.
2. **Item 30: the fix wave's live re-drive**, now at P1 for four findings, on a leg serving canopy 0.9.0 or later:
   - M-NETWORK-EDITOR-17 (F-CANOPY-012: all four targets; `output_weights` in the manual's three forms, as rows, and as
     a wrong-count flat list; by source the semicolon and newline forms are read as rows and rejected on a network
     with more than one output) and
     M-NETWORK-EDITOR-09/-13 (F-CANOPY-013: the alert's index and count on a successful append and remove) need a
     service leg whose cascor can be restored into `Investigating`: a writable cascor, never the trio.
   - C2.9-05 (F-CANOPY-018: the toast, and as an added expectation scored separately, Apply disabled and `params-status`
     clean after a successful apply) and M-PARAMETERS-04/-05/-06 (F-CANOPY-028: pin, reload, pin again): the Apply
     controls work in both modes by the manual, the pins by source; a demo leg is expected to reach them.
   - M-WORKERS-02 (F-CANOPY-032): cascor stopped, canopy up, the Workers tab open 60 s, on a leg whose cascor may be
     stopped; then segment 16's `degraded` induction, where no alert is correct. Its result closes or re-diagnoses.
   - At P2: C2.1-01/02 (F-CANOPY-001); M-METRICS-03 (F-CANOPY-026's row, still FAIL in
     `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`). F-CANOPY-034 has no row.
   Each header's token changes only on its own row's result; record the drives as a ledger phase with consensus rounds.
3. **Item 25: census triggers fired from the page**, on the merged code (canopy 0.9.0 or later, a verify leg on the
   Linux host). Schedule each trigger as its own task when the shim sees `AddWatched` (`setTimeout(…, 0)`), timestamp
   it in the page, validate on the synthetic check first. Under the pacer every TOOK predicate reads NO-EFFECT by
   construction, so the evictions are the score. **T-apply needs its own design** (Phase 12, Instruments).
4. **Item 26's second step**, once the owner rules (O17): every open finding not yet rated against canopy's
   `CHANGELOG.md` and the design plans for a promise, or, if the ruling counts it, a description of an internal
   mechanism, of the behaviour it breaks. Of the findings Phase 11 named, F-CANOPY-065's rating is the one the ruling
   moves (every site that recorded F-CANOPY-057's stream as shipped is corrected or points at the correction); leads
   from round 1:
   `CHANGELOG.md:1436-1437` (`[0.8.0]`) for F-CANOPY-060 and `:2909` (`[0.6.0]`) for F-CANOPY-051 (ledger Phase 13,
   Still owed). Others may be reached by entries nobody has read for them yet.
5. **Item 27: F-CANOPY-055's Live Dataset Switch allow arm**, on a demo leg serving 0.9.0 or later whose training may
   be started (never the trio), with the experimental-functions toggle on (ledger Phase 12, item 27). Record in
   F-CANOPY-025's and F-CANOPY-055's entries.
6. **Item 28: the first live run on the shipped pacer**, when the trio's canopy is restarted on 0.9.0 (owner, O13) or
   on any leg serving the merged tree (ledger Phase 12, item 28).
7. **Item 29**: worktree housekeeping on the Linux host (ledger Phase 12, item 29).
8. Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb decides F-CANOPY-065 alone among the
   findings Phase 11 named, every site that recorded F-CANOPY-057's stream as shipped corrected or pointed at the
   correction: 9/11 or 8/12).

**Traps learned:**

- **The triage reads the first severity token anywhere in a header and only the last 170 characters for a
  disposition.** A re-rating must put `P1` before any `P2` in the header, and the word "fixed" must stay out of the
  tail: "fixed in code" would flip an OPEN entry to FIXED. Phase 13's headers say "code change canopy#NNN".
- **The manual's line numbers move between releases.** F-CANOPY-064 cites `:266`, `:271`, `:293`; at `571743db` the
  same sentences are `:311`, `:316`, `:338`. Cite the commit with every line.
- **canopy's CHANGELOG does not name the Phase 4 fix wave.** canopy#532/#533/#535 are in v0.7.0 (the `compare` API
  says `behind`, 0 ahead) but no fix entry names them or their findings (canopy#532 appears only inside the 0.9.0
  entry for F-CANOPY-059); do not infer "unshipped" from the CHANGELOG.
- **On turing the worktree guard refuses** `awk` with a program, `sed` with a shell variable, loops over variables,
  `$(…)` inside commands, and heredocs that mention `git`. Spell paths and line numbers out; multi-step logic goes in
  a scratchpad or `util/ad-hoc/` script run with `python3 -I`/`-B`.
- **turing has no signing**: land through `util/open_signed_pr.py` (small files) and
  `util/ad-hoc/2026-10-17_push_signed_with_retry.py` (the ~980 KB ledger as its own commit). Run
  `util/ad-hoc/2026-10-17_turing_network_probe.bash` first; on 2026-10-19 the link was healthy (0% loss to the
  gateway, 12.6 Mbps up).
- **Shared files land as whole-file uploads.** Build each from a fresh `origin/main` copy at upload time and re-apply
  with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`, then the four correction passes
  (`util/ad-hoc/2026-10-19_phase13_ledger_round{1,2,3,4}_corrections.py --root <copy>`), in that order, on a
  whole-tree copy (each pass reads several files under `--root`); re-check `origin/main` an hour after the merge.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase13 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -7   # 79 / 56 / 1 / 2 / 20; P1 9; P2 11
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 9
grep -c 'P1 since 2026-10-19' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md   # 5
grep -n '^## Phase 13' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
grep -c 'Correction 2026-10-19' notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md   # 2
grep -c 'Correction 2026-10-19' notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md   # 1
grep -c 'Correction 2026-10-19' notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md   # 1
gh api repos/pcalnon/juniper-canopy/compare/v0.7.0...28da69f8 --jq .status   # behind (canopy#535 is in 0.7.0)
gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/docs/USER_MANUAL.md?ref=571743db" | grep -n 'Use the API response'   # :510
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase13`, landed from turing through the API as signed commits
  (`util/open_signed_pr.py`; the ledger by `util/ad-hoc/2026-10-17_push_signed_with_retry.py`). Worktree
  `federated-stargazing-blanket` holds the same files as local, unsigned commits that never leave the host (the
  frozen drafts the consensus rounds reviewed).
- **juniper-canopy, cascor, data:** no branches from this session; read through the GitHub API only (canopy `main`
  `571743db`, cascor `main` `4c26919f`).
- **Services:** none on this host. The trio on the Linux host was not touched or reached.

## Changed by this session

- **Created:** this file; `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`;
  `reports/e2e-canopy-2026-09-02/drafts/lane13*_phase13_ledger_brief.md`;
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round*.md`;
  `util/ad-hoc/2026-10-19_phase13_ledger_round*_corrections.py`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 13; the headers of F-CANOPY-012,
    -013, -018, -028 and -032 and a RE-RATED blockquote in each; Status bullets on F-CANOPY-057 and F-CANOPY-065;
  - `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`: the header's Status and
    Last updated, the dated correction under the status block, the two g-3 rows;
  - `notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`: §28.1's dated correction and its g-3 row (round 1); its CAN-015 row (round 2);
  - `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`: §5.2's dated correction and its g-3 row (round 2); pointers on its §5.2 Status delta and
    its §8.1 and §11.7 rows (round 3);
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: item 4; O17;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md`:
    the SUPERSEDED banner.
- **Outside the repo**, in auto-memory: `MEMORY.md` and `canopy-e2e-arc-state.md`.
