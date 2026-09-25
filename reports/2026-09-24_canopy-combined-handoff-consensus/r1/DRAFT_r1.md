# Thread handoff — canopy combined: the E2E arc's queue, Y2 wave 2's fix pass and merge, and the selection arc's owner calls

**Written**: 2026-09-24, by session "canopy combined" (juniper-ml worktree
`.claude/worktrees/bubbly-meandering-pie`, branch `worktree-bubbly-meandering-pie` at `6c23fdde`, which was
`origin/main` at writing). The drafted state was re-probed between 20:25Z and 20:45Z; "at writing" means that
window. It **supersedes three handoffs, one per lane**. Two of them are not on `main`:

| lane | predecessor | where it lives at writing |
|---|---|---|
| A | `HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md` | branch `docs/canopy-e2e-handoff-2026-09-24` (`dd4413e5`, no PR), and the worktree `.claude/worktrees/graceful-sprouting-panda`. Written about 11:00Z, amended 19:21–19:41Z. |
| B | `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md` | untracked, ONLY in `.claude/worktrees/idempotent-jumping-sparkle`. Written 06:11Z. |
| C | `HANDOFF_2026-09-24_canopy-selection-cleanup-done-item-19-closed-y7-grounded-owner-calls-remain.md` | `main`, juniper-ml#2087 (`c32e5f2a`, 19:42:45Z) |

All three live in `prompts/thread-handoff_automated-prompts/` wherever they exist. Items below are numbered
A1…, B1…, C1… and X1… (cross-lane) so they cannot collide with the numbering inside the source documents: "ledger
item N" means the E2E ledger's Phase 9 "Still owed" list, and "R15A m1" means round 15's report A, finding m1.

**Merge approval: none is carried.** B's predecessor recorded "ONLY this session's four PRs (2b, 2a, 2c,
addendum), plus the closing PR. No deploys, images, PyPI or GitHub Releases". C's recorded "granted by the owner
for this arc in this session (2026-09-24)". A's recorded none. A per-session grant does not survive a handoff;
B's own closing draft (`S/main/handoff_v4.md`) says so. Ask the owner before the first merge.

## Goal statement (paste this as the new thread's first prompt)

Continue three canopy-related arcs from one combined handoff: juniper-ml
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`.
Read it in full. Each lane section carries its own context, so the lanes can be split across sessions.

- **Lane A: canopy E2E validation.** The ledger of record is juniper-ml
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, and its Phase 9 "Still owed after this
  phase" list (items 0–17) is the queue. Next: F-CANOPY-059's fix (P0, ledger item 16), then a Phase 10 that
  files the findings two peer arcs handed over.
- **Lane B: Y2 wave 2.** Four prepared, unopened PRs: juniper-deploy 2b, juniper-recurrence 2a, juniper-ml 2c,
  and the addendum to the 09-08 handoff. They have been through fifteen consensus rounds. Next: round 15's fix
  pass, round 16, then open and merge per `S/main/PLAN.md`. **It must run from the worktree
  `.claude/worktrees/idempotent-jumping-sparkle`.**
- **Lane C: canopy selection arc.** Nothing is left to implement. What remains: owner decisions, worktree
  removals only the owner can run, a primary fast-forward that a live stack blocks, and the date
  2026-09-29T00:00Z.

Before anything else:

1. Run the verification block below.
2. Put the owner questions to the owner in one message:
   - **Merge approval for this session:** which PRs? Candidates: B's four plus its closing PR, and A's Phase 10
     and F-059 PRs.
   - **B only, the sweeper against Y2's merge order (X1):** exclude the four Y2 PRs from the owner's sweeper, or
     approve making 2b's preflight warn until 2a ships, or accept fix-forward.
   - **A6, urgent:** push a provenance ref for the ledger's local-only commits, or accept their loss. Three are
     already unreachable.
   - The standing calls: C2 (Y7), C3 (the X8 release), A3 (ledger item 17), and the rest of A6 (the ratings and
     the account's later actions).
3. Choose lanes per "Session layout".

Rules that bind every lane:

- **Validate BEFORE opening a PR.** The owner's sweeper readies and arms open PRs, drafts included, and its
  merges are intended ("Mine: fix forward", 2026-09-24 07:32:48Z).
- Follow `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` for every review
  round.
- **Never touch the trio** (`:8101` data, `:8202` cascor, `:8051` canopy).
- **Never print secrets or environment values.**
- **The final summary names every document it references or changes.**

### Session layout

- **Lane B cannot move.** Three of its tools hard-code its worktree:
  `ML = J / "juniper-ml/.claude/worktrees/idempotent-jumping-sparkle"`. The sites are `2026-09-23_freeze_round.py:48`,
  `2026-09-23_open_pinned_pr.py:73` and `2026-09-23_placeholder_census.py:38`, all in that worktree's
  `util/ad-hoc/`.
- **An isolated session reaches no sibling worktree.** A worktree-isolated session refuses git against any other
  worktree of its own repo. So:
  - Lane B runs in a session started in `idempotent-jumping-sparkle`.
  - Lane A's juniper-ml ledger work runs in a session on a fresh juniper-ml worktree cut from current `main`.
  - canopy and cascor work goes in their own worktrees under
    `/home/pcalnon/Development/python/Juniper/worktrees/`. The guard does not stop a session reaching other
    repos.
  - Lane C's items are owner-facing and fit either session.
- **Never do Lane A's juniper-ml edits in `idempotent-jumping-sparkle`.** That tree is based on `5ea8e273`, which is
  older than `main`, and it carries B's uncommitted state. `util/open_signed_pr.py` uploads whole files, so an
  edit made there would revert `main`.

---

## Lane A — canopy E2E validation

**Done before this handoff** (from A's predecessor; the merges, the counts and the branch are re-probed):

- **Phase 9 landed.** It merged as juniper-ml#2083 (`48fc09e5`, 10:52:55Z) after ten consensus rounds.
  - The corrections are replayable: `util/ad-hoc/2026-09-24_phase9_ledger_round{1..10}_corrections.py`.
  - The lane reports and briefs are in `reports/e2e-canopy-2026-09-02/{consensus,drafts}/`.
- **The canopy follow-up to #676 merged.** canopy#684 (`f2147403`, 11:10:28Z) carries round 3's fixes.
  - It was reviewed in rounds C..C8; C8 returned MERGE. The reports are in
    `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`.
  - #676's description was refreshed at 10:54:54Z.
- **Triage** (`python3 -B util/ad-hoc/e2e_finding_triage.py`): 70 findings, 48 fixed, 1 accepted, 2 withdrawn and
  19 open. The open ones are 1 P0 (F-CANOPY-059), 6 P1 (F-CANOPY-055, -056, -057, -058, F-CASCOR-001, -002) and
  12 P2.
- **The owner answered the sweeper question.** Session `bc31e993` asked at 03:34:45Z; the owner answered at
  07:32:48Z: "Mine: fix forward".
- **Secret-shape tooling was hardened** during the review. The launch scan, the answer extractor and both
  archivers share one set of shapes. `util/ad-hoc/2026-09-24_secret_shape_check.py` tests all four.

**A1. F-CANOPY-059's fix (ledger item 16; P0).** The replay player has been dead against cascor since
canopy#532.

- **The change.** Convert cascor's `range` dict to `[start, end]` wherever canopy reads it:
  - `render_session`'s readout: `src/frontend/components/replay_player_panel.py`, `:532` in the ledger's
    citation;
  - the range slider's value.

  A list, or no range at all, must keep working.
- **The regression test uses the payload Phase 1 measured** (segment 7), not a typed list.
  - Correct `test_p2_wave_batch_a.py:179-190`. Its fixture says it is "the exact shape measured off the running
    service", and it is not.
  - Sweep the other fixtures that make the same claim.
- **Then two follow-ons, in order:** F-CANOPY-015's live re-drive, then F-CANOPY-056's fix, which needs a
  reachable control.
- **Every one of these drives starts a replay.** A replay REPLACES cascor's live network (ledger item 17), so
  each drive needs a cascor that may be written: not the trio's.
  - `util/isolated_stack.bash` defaults to the trio's ports, so a bare `--down` kills it. Use a wrapper that
    refuses the defaults, such as `util/ad-hoc/2026-09-23_a_n2_stack.bash`.
  - End each replay, with the sidebar's Reset Training or cascor's `/replay/control` stop.
  - Check that Start and Apply work afterwards.
  - Read `/api/status`'s `fsm_status` and the Network Editor badge. The status bar reads Stopped both during and
    after a replay, so it cannot tell them apart.

**A2. Phase 10: file what two peer arcs handed over.**

- **Method.** File through the consensus procedure. Re-derive each finding first, and decline or withdraw with a
  reason.
- **Mechanics.** The ledger file is about 791 KB.
  - Push it in its own signed commit (`util/push_signed_commit.py`).
  - A 499 or 502 response can still land, so re-read the ref before retrying.
  - `open_signed_pr.py` uploads whole files, so rebase onto the live `main` immediately before it runs.
- **Archive A's predecessor** (the branch `docs/canopy-e2e-handoff-2026-09-24`) in this PR, unless this combined
  handoff's own PR already carried it.

(a) **From the defect-register arc (round 42).** **F-CANOPY-060 to -062 are RESERVED**, and the ids were given to
that arc to cite. Use them, or mark one WITHDRAWN if re-derivation refutes it.

- **F-CANOPY-060** (NIT/LOW, pre-existing): the dataset-shortfall prompt drops juniper-data's
  truncation-permanence sentence.
  - `_producer_detail_from_refusal` (`src/frontend/dashboard_manager.py:8404`, canopy `7ab994e5`) cuts the
    detail at `" To accept it,"` and at `" The resulting dataset"` (`:8410`).
  - So "The resulting dataset will be permanently annotated as truncated." never shows. It comes from juniper-data
    `juniper_data/core/limits.py`, `InputTooLargeError`.
  - Proposed fix: cut only at `" To accept it,"`.
  - Also check that the prompt's three options (`:8442-8444`: "broken rows", "placeholder values") fit a cap
    refusal, if cascor routes one through it.
- **F-CANOPY-061** (LOW; LOW 3 of canopy#683's validation): `_docs_enabled` is pinned by a single sample
  (`src/main.py:517`).
- **F-CANOPY-062** (LOW; LOW 4): the padded-key WARNING names `CANOPY_API_KEY` even when the value came from the
  `_FILE` variant. The comment at `security.py:350` is wrong.
- **061 and 062 are to be FIXED-BY a canopy PR from branch `fix/secret-leaks-683-validation`.**
  - That branch belongs to session `bc31e993`, which ListAgents shows as `defect reg [042116]`. Address it by that
    name WITH the `[042116]` ref: a second session is also named "defect reg".
  - Its precondition has fired: canopy#683 merged at 19:10:20Z (`7ab994e5`).
  - At writing the PR does not exist and the branch is not on origin. Its worktree is
    `worktrees/juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac`.
  - Get the number from `bc31e993`, and record it once the PR exists.
- **A fourth item, no id reserved** (NIT, pre-existing, no owner). The defect-register arc handed it over at about
  20:40Z; `defect reg [042116]` found it while building juniper-cascor#690.
  - **The upstream change.** #690 (OPEN, head `78e99414`, not yet validated) removes #687's refusal sentence
    "Nothing was loaded…" from `_refuse_dataset_wider_than_network`. The sentence was false when the start's
    inline tensors had been bound.
  - **canopy keeps two copies of the old sentence** (at canopy `7ab994e5`):
    - `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42` defines `CASCOR_SENTENCE`; the
      comment at `:41` calls it verbatim;
    - `src/frontend/dashboard_manager.py:8381`, inside `_start_fresh_required_alert` (`:8359`), reads "Nothing was
      loaded: the dataset is still staged, and the results shown are still the previous run's."
  - **Nothing breaks.** canopy parses only the marker and the first sentence, but its alert repeats a claim cascor
    is withdrawing.
  - **It becomes true only once #690 merges.** Re-derive it against cascor `main` then.
  - If it earns an id, assign one in filing order and send the id to the defect-register session. The register
    wants nothing else.

(b) **From the canopy selection arc: O2–O5 and O9.** Its O1 is F-CANOPY-055. Ids run from F-CANOPY-063, in filing
order. The source is `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`, § "Observations (not
A-N2 failures)", lines 188–226 on `main`.

- **O2**: both metric charts plot `metric["epoch"]`, a per-phase counter, as x (`metrics_panel.py`,
  `_parse_metrics` / `_create_accuracy_plot`). So accuracy sits in a sliver at x ≤ 51 on a ~10k axis for every
  CasCor case. It is likely the most user-visible of the five.
- **O3**: `/api/set_params`'s `applied` list omits the keys routed over `/ws/control`, and `epochs_max`'s
  `not-updatable` skip, though the values land.
- **O4**: `/v1/health`'s `version` comes from installed metadata (0.6.0, from `JuniperCanopy1`'s stale editable
  install), while the source is 0.8.1. Related history: OBS-1, canopy#526. It may be an environment artifact
  rather than a code defect.
- **O5**: 80 "Network stats API returned 503" warnings under the recurrence backend: `/api/network/stats` has no
  recurrence branch. It is log noise; decide whether the recurrence backend is in scope.
- **O9**: after a refused Start, the sidebar's "Current Dataset" shows the staged dataset, while the routes are
  honest. The selection arc calls it a pre-existing U-6 design question. If it survives as a design question, it
  goes to the owner (C4).

**A3. Ledger item 17 — the owner's call.** A replay replaces cascor's live network:

- `start_replay` calls `_load_snapshot_to_network` (`manager.py:5977`), which sets `self.model` (`:5734`).
- Neither `reset()` nor `stop_replay()` restores the earlier network.
- `_auto_snap_best` is off by default (`:1472`).

canopy's Replay modal nevertheless promises "a read-only playback session" (`hdf5_snapshots_panel.py:533`), and so
does the proxy route's docstring (`main.py:2985`). The fix is canopy's wording, cascor's design, or both.

**A4. F-CANOPY-058's census (ledger item 0, first half).**

- **The first census was refuted before its first run.** `util/ad-hoc/2026-09-24_f058_trigger_census.py` scores
  every answer without props as EVICTED, and cannot count a watchdog fire.
- **Fix the instrument first:**
  - Record the executed transition itself: wrap `window.store.dispatch` and log `addExecutedCallbacks` by
    `executionPromise`, or install a shim with `add_init_script` before the renderer builds its store.
  - Detect a fire from the lane's state before the reset.
  - Score T-apply only with a request in flight, and check "still in flight" in `took()`.
  - Pass a synthetic check on a scratch dash app, with and without `no_update` answers, before any live run.
- **Count EVICTIONS, not applies.** On the idle trio the feeder answers `no_update`, an HTTP 200 that applies
  nothing.
- **Five triggers:** a gate write, a tab switch, an Apply clamp and release, a display-mode change, and 10 idle
  minutes. Simulate the Apply through the clamp Store, because a real Apply PATCHes the trio's cascor.
- **Size the window, and any verdict floor, to the lane's cadence** (about 7.5–8 s self-clocked), fixed before
  the run (ledger item 14).
- **The leg:** `util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <canopy worktree on main>/src <port>`, with
  `JUNIPER_E2E_CANOPY_URL` exported for the drivers. It reads the trio's `:8101` and `:8202` and must not write
  them.

**A5. The F-CANOPY-055 / F-CANOPY-058 redesign (ledger item 0, second half).**

- **One design for both lanes.** The candidate is Lane B's handshake pacer: request/ack tokens, with no
  `disabled`-prop and no `running=` guard. It must also cover a non-Interval Input, because #613's feeder has one.
- **The partial alternatives** (from the 2026-09-23 E2E handoff): a progress-based watchdog (reset on an
  `n_intervals` change), or a gate that returns `no_update` for global lanes on a tab-only change.
- **Real-renderer tests of every trigger:**
  - a tab switch mid-request;
  - the end of an Apply spanning a request;
  - a second-Input change mid-request;
  - 10 idle minutes with the watchdog.
- **Live verification, before consensus, PR and merge:**
  - the census and its triggers on the fix's leg;
  - F-CANOPY-025's allow arm, re-driven on a leg where the old code fails and whose training may be started.
- **Correct the canopy text F-058 contradicts:**
  - `dashboard_manager.py:467-472` ("the harmless window");
  - `:4698-4701` ("Self-healing, bounded to one cycle");
  - `test_poll_gating.py:312-313` ("the apply clamp alone").
- **KEEP** the canopy worktree `…fix--f055-status-bar-running-guard--20260923-1425--ce78e0de`. It holds the refuted
  first fix (`884d22fb`, `cf6fb1dc`, `7a4a2e33`) as provenance.

**A6. Owner questions (ledger item 15).**

- **The account's later actions**, none made by a Claude Code session on this host:
  - the update-branches on ml#2066 and data#434 (23:16–23:17Z);
  - ml#2045's disarm and re-arm (23:48Z);
  - cascor-worker#196's merge (01:21:37Z);
  - #676's CI re-run (01:22:32Z);
  - ml#2045's draft and ready (03:04–03:05Z).
- **The ratings**, on plan §6.3's rule (`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`):
  F-CANOPY-056 and -057 P1, and F-CANOPY-059 P0, against F-CANOPY-014's P1 precedent.
- **Provenance refs for the local-only commits the ledger cites. Now urgent.**
  - Measured at writing with `util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py` (new, read-only).
  - **canopy `78c057e2` (item 15), `26bf27b3` and `96e7b105` (item 13's follow-up commits) are already
    UNREACHABLE.** They are still in the object store, but no branch holds them, so a `git gc` prune can delete
    them.
  - Every other cited commit is held by ONE local branch only (table below). Until the owner answers, delete none
    of these branches.

| repo | local branch (worktree) | cited commits it alone holds |
|---|---|---|
| canopy | `fix/f055-status-bar-running-guard` (KEEP, A5) | `ce78e0de`, `884d22fb`, `cf6fb1dc`, `7a4a2e33` |
| canopy | `perf/idle-dispatch-cuts-v2` | `8990f65c`, `5310b81a`, `c360fb53`, `040dc5c1` |
| canopy | `perf/idle-dispatch-cuts` | `668380ec`; also `723ee812`, which is on the next row too |
| canopy | `fix/f054-replay-block-clientside` | `723ee812` (shared with the row above) |
| juniper-ml | `docs/canopy-e2e-phase9` (`graceful-sprouting-panda`) | `f6861234`, the rebased copy of `b54e3b3f` |
| juniper-ml | `worktree-squishy-dancing-moth` | `b54e3b3f` |
| juniper-ml | `worktree-partitioned-twirling-stream` (another arc's worktree) | `ada8e50c` |

**A7. The rest of the Phase 9 "Still owed" list, carried unchanged.** The ledger text is authoritative.

- **0**: A4 + A5.
- **1**: hunt the F-053 regression. With the drain parked, L sat at 3.9–5.4 s on the cuts leg under load.
- **2**: the timestamp-only store rewrite. It needs a design that keeps the phase-duration clock.
- **3**: owner: F-CANOPY-004's contract.
- **4**: `FULL_HISTORY_POLL_TICK_MODULUS` → 1.
- **5**: canopy#613's guard. Superseded by item 0.
- **6**: F-CANOPY-049 and cascor#674's follow-ups.
- **7**: CAN-015's replay-player loop, joined by F-056 and F-057, behind F-059.
- **8**: M-CANDIDATES-10/-11, now re-drivable.
- **9**: M-DATASET-17..26 (the owner's question), the M-TOPOLOGY-16 fade half, and F-038's browser-level test gap.
- **10**: owner question: the metrics replay drives no chart.
- **11**: the starvation mechanism, re-derived under FIFO. Unstarted. The `_GATED_POLL_INTERVALS` comment in
  `dashboard_manager.py` still says "the lowest-priority callbacks".
- **12**: F1 and Phase 8's round-1 minors.
- **13**: two parts still open:
  - the stale refresh-rate config: `conf/app_config.yaml:170,181` and `docs/USER_MANUAL.md:1344` promise
    intervals no code reads. #684 changed `docs/USER_MANUAL.md` for other claims, but not `conf/app_config.yaml`,
    so re-locate the manual's line before editing;
  - the live-check instrument's gaps. Fix them before `2026-09-23_idle_cuts_live_check.py` runs again.

  The item's round-3 follow-up (canopy#684) and #676's description are done.
- **14**: a standing rule: a verification census must be able to fail.
- **15**: A6.
- **16**: A1.
- **17**: A3.

**A8. MEMORY.md is within about 38 characters of its load limit.**

- **Measured at 20:28Z:** 24,962 characters by `wc -m` (25,158 bytes). The load limit is about 25,000
  CHARACTERS, not bytes; the owner's operating target is 20 KB (memory `feedback_memory_index_target_is_20kb.md`).
- **How to compact:**
  - Retire entries; never strip hooks.
  - Snapshot the link set first (`util/ad-hoc/2026-09-12_memory_index_linkset.py snapshot`, then `compare`).
  - Re-read the file right before each write, because other sessions edit it.
- The three ACTIVE status lines belong to their arcs. The canopy E2E one is this lane's.

**A9. Worktree cleanup: gated on A6.** Follow each repo's `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (juniper-ml's
is `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`). Never run
`util/remove_stale_worktrees.bash`.

- **canopy, now eligible except where A6's table holds a branch:**
  - `…fix--idle-cuts-round3-wording--20260923-2238--e9053227`: #684 merged. Local head `135c2782`, clean.
  - `…control--main--20260923-1423--3a6dea95`: detached.
  - `…perf--idle-dispatch-cuts-v2--20260923-1418--3a6dea95`: #676 merged. Its branch is in A6's table.
  - `…perf--idle-dispatch-cuts--20260923-0830--723ee812`: superseded. Its branch is in A6's table.
  - `…fix--f054-replay-block-clientside--20260923-0036--2f973ca2`: #670 merged. Its branch is in A6's table.
- **juniper-ml: the owner runs these (C1).**
  - `graceful-sprouting-panda`: branch `docs/canopy-e2e-phase9`, squash-merged as #2083; it holds `f6861234`.
  - `squishy-dancing-moth`: the 09-23 WIP; it holds `b54e3b3f`.

**Traps specific to Lane A:**

- **canopy's `addopts` already has `-q`.** Another `-q` suppresses pytest's summary line. Use
  `conda run --no-capture-output -n JuniperCanopy1`.
- **Refactor PRs need the full canopy unit lane.** Source-window tests read `dashboard_manager.py` text.
- **A census can pass a fix whose failure its window cannot contain.** Put every trigger inside the window, or
  name the ones it cannot see.
- **Lanes must never print a secret.** Build fake secrets by concatenation and print booleans only.
- **Archive with `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`.** Allow a quoted literal per agent
  only after reviewing it.
- **Earlier lanes printed the owner's email address.** Lanes C5, R4-A, A1 and B2 did so in their own local tool
  output. Nothing was sent.

---

## Lane B — Y2 wave 2 and the 09-08 addendum

**Claims.** Session `idempotent-jumping-sparkle`, which the selection arc calls "peer session `canopy`", claimed Y2
waves 2 and 3 and X10. These are items 4 and 20 of
`HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` § B, and whoever runs this
lane inherits the claims. **§ B's terms:**

- The claims hold until 2026-09-29T00:00Z.
- From then on, anyone may start the work unless an open PR or a pushed branch carries it. A document asserting
  the claim stops counting at that point.
- **At writing, none of the four Y2 branches is on origin, and no PR is open.**

**The original request**, verbatim from B's predecessor: "evaluate the current state of the juniper project with
respect to the following handoff prompt:
juniper-ml/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md
determine if any outstanding work remains update the handoff document accordingly begin performing the
outstanding tasks validation by consensus should be performed where appropriate merge approval granted". It was
followed by "continue as planned" several times.

**Short names:**

- `S` = `reports/2026-09-23_y2-wave2-consensus/session-state/` in the `idempotent-jumping-sparkle` worktree. It is
  untracked: the persistent copy of the old tmpfs scratchpad, with the same layout. Pass it as the freeze tool's
  `--scratch`.
- `…PERSISTENCE-DESIGN.md` = `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`. "Wave N" is
  its §11.4 step N.
- Y2 is defined in `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` §6.

**Done** (carried from B's predecessor; the freeze digest, the file count and the worktree status are
re-probed):

- **The four PRs are prepared, unopened, in three worktrees:**
  - **2b**, juniper-deploy: bind-mount the LMU snapshot root, with a preflight on every bring-up path.
  - **2a**, juniper-recurrence: track `recurrence-snapshots/.gitkeep`, and correct #172's unreleased claims.
  - **2c**, juniper-ml: both launchers declare the root. It adds a shared static tripwire,
    `tests/snapshot_root_tripwire.py`, and two mutation harnesses.
  - **The addendum**, juniper-ml: status addendum v13, spliced into the 09-08 handoff, with the probe, splice
    and extract tools.
- **The PR bodies, commit bodies and titles are frozen** in `S/main/` (`pr_*.md`, `commit_*.md`, `titles.json`).
  **`S/main/PLAN.md` v5 is the open-and-merge procedure. Read all of it before opening**; this section does not
  restate it.
- **Round 15 is frozen at `S/r15/`:** 140 files, `SHA256SUMS` digest
  `66742624b1533cd11506c7597af458c27abd3aeb6392f1439f49794bfa4a3171`.
  - Its reports are `S/r15_reports/R15{A,B,C,D}.md`.
  - Earlier rounds are in `S/r14_reports/`, `S/r13_reports/` and so on; rounds 1–4 are in `S/archive_early/`.
- **Evidence at the freeze:**
  - launcher suites 193 OK; launcher harness 103/103;
  - 33 of 37 fired sweeps caught without the tripwire;
  - deploy preflight 76 tests; full deploy suite 360 passed, 42 skipped; deploy harness 111/111;
  - re-probe 46/46 at the pins, and exactly the five documented BROKEN rows at `main`.
- **The bases at the freeze:** juniper-ml `f9c81d80`, juniper-recurrence `ca9609f0`, juniper-deploy `d589dd95`.
  - juniper-ml#2061 was merged three-way into 2c; the freeze accepted it through `--merged 2c_ml.diff`.
  - juniper-recurrence#183 and #184 are filed. Both are OPEN; #184's body was PATCHed at 03:36Z.

**What moved since B's predecessor was written (06:11Z)**, re-probed at writing:

1. **2a must take the delta route (PLAN.md step 2).** juniper-recurrence `main` is `db41e77e` (#186, 08:02:09Z).
   It changed `juniper-recurrence/CHANGELOG.md`, one of 2a's four upload paths.
2. **2b must take the delta route.** juniper-deploy `main` is `7ff6ff32`, after #230 (`b972ae8c`, 18:58:50Z), #231
   (`2bde07b2`, 19:26:17Z) and #232 (19:56:16Z).
   - They changed `CHANGELOG.md` and `docker-compose.yml`, both 2b upload paths.
   - They also changed `k8s/helm/juniper/values.yaml`. B's predecessor said the worktree's copy "equals deploy
     main"; that is no longer true. The file is not uploaded.
   - Both moved sets include a CHANGELOG, so **R15D MINOR 1 is now on the critical path.** That is the fix making
     `--merged` compare a CHANGELOG as a multiset of lines.
3. **2c and the addendum have no moved paths.** juniper-ml `main` moved 18 commits past `f9c81d80` (to
   `6c23fdde`), and none touches their upload paths: `git log f9c81d80..origin/main -- <paths>` is empty.
4. **canopy `main` moved six merges past the round-15 freeze** (`S/r15/SHA256SUMS` was written at 04:43:49Z):
   - #679 (`6c4ad9a9`, 08:14Z);
   - #680 (`5907713b`, 09:08Z), X11 shipped;
   - #681 (`f0401830`, 09:53Z), F1/F2;
   - #682 (`14a0e4c7`, 10:09Z), X8's canopy half;
   - #684 (`f2147403`, 11:10Z);
   - #683 (`7ab994e5`, 19:10:19Z).

   #676 (01:38Z), #677 and #678 predate the freeze, where a merge that changes no row gets no bullet. R15C M1 asked
   for "Since the pins" bullets for canopy#674, #675 and juniper-ml#2058 only. **Re-run the probe with
   `--fetch --at-main`, and bullet every merge that changes a row.** Expect rows beyond the five documented ones
   to read BROKEN.
5. **The live work list moved three times after R15C named `…queue-drained.md`:** #2069 (07:54:40Z), #2082
   (10:36:21Z) and #2087 (19:42:45Z). This combined handoff now supersedes #2087's.
   - R15C M1's own last step ("add a PLAN step that lists the canopy-selection handoffs on main before opening")
     catches this.
   - **Point the addendum at the newest one at open time.**
6. **X11 is no longer an open ruling.** R15C M1 describes it as `…queue-drained.md`'s owner ruling 2. It was ruled,
   and shipped as canopy#680 at 09:08Z.
7. **juniper-data 0.16.0 is released and contains #421.** GitHub published it at 08:52:14Z and PyPI at 18:35Z.
   The probe's `6 packaging (release)` row reads the shared juniper-data checkout's tags. Its docstring says the
   pinned run prints 45/46 once a fetched release tag contains #421 (R14C n4).
8. **The owner answered the sweeper question after R15D.** That changes B3 (X1).

**B1. The round-15 fix pass.** Apply the fix list below, and also:

- merge main's changes three-way into 2a's CHANGELOG, and into 2b's CHANGELOG and `docker-compose.yml`;
- bring the addendum current (moves 4–7 above).

**B2. Round 16.**

- **Re-freeze:**
  `python3 util/ad-hoc/2026-09-23_freeze_round.py --scratch S --round 16 --prior r15 --addendum addendum_v14.md --logs S/fix16/logs16 --reports S/r15_reports`.
  - Add `--merged 2a_recurrence.diff --merged 2b_deploy.diff` once their worktrees carry main's changes. The flag
    names "a diff … whose worktree already merged main's change to its moved paths".
  - Widen the tool's `TOOLS` glob (`2026-09-23_*`) if you create `2026-09-24_*` tools.
- **Run four lanes,** from `S/main/lane_common_r15.md` and `lane_R15{A..D}.md`, with their contexts updated.
  Archive each report at once: `util/ad-hoc/2026-09-22_extract_lane_reports.py --require-heading "## Housekeeping" S/r16_reports NAME=<transcript>`.
- **Tell R16B** that `.env.secrets.enc` is tracked in juniper-deploy and must be deleted from every clone before
  a suite runs.
- While a round runs, touch no uploaded file.
- Repeat until no MAJOR and no unresolved MINOR remains. Then record `APPROVED_FREEZE` in `PLAN.md`.

**B3. Open, then merge, per `S/main/PLAN.md`, after X1 is settled.**

- **The two orders run in opposite directions.**
  - Opening order is 2b → 2a → 2c → addendum, because each PR cites the numbers of the PRs that merge after it.
  - Merge order is 2c → 2a → 2b → addendum. After 2a, `git pull --ff-only` the shared
    `/home/pcalnon/Development/python/Juniper/juniper-recurrence` checkout.
- **Merge with `util/safe_merge.py --pr N --repo <name> --execute --no-auto-fallback`.**
  - Extract it from `origin/main`'s copies, together with `wait_for_checks.py`, `push_signed_commit.py` and
    `open_signed_pr.py` (`git show origin/main:util/<name>`).
  - Read MERGED back: exit 0 is not a merge.

**B4. Closing work.**

- **The closing handoff,** from `S/main/handoff_v4.md`. Fill its `PR_2C` / `PR_2A` / `PR_2B` / `PR_ADD`,
  `GIT_STATUS_BLOCK` and `HANDOFF_VALIDATION_BLOCK`, and point it at the newest selection-arc handoff, not
  `…queue-drained.md`.
- **The consensus archive** `reports/2026-09-23_y2-wave2-consensus/`: rounds 1–16, plus a README meeting §7 of the
  consensus procedure.
- **A closing PR** with the `util/ad-hoc/2026-09-23_*` tools.
- **Worktree cleanup,** only on an explicit merge signal.

**B5. The final summary** names every changed file. It repeats the reminder to rotate the leaked
`JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` tokens: a lane leaked them earlier, and the owner was told.

**B6. The claimed follow-ons: wave 3 and X10, both canopy, both unstarted.** From `S/main/handoff_v4.md`:

- **Wave 3.** Give each of the FIVE in-scope snapshot sites in `src/main.py` a recurrence branch. Locate them by
  symbol, not line:
  - `_backend_snapshot_inventory` and `_backend_snapshot_detail`, both written `!= "service"`;
  - `create_snapshot`;
  - the lookup and the load in `restore_snapshot`.
- **`_require_service_adapter` keeps its 501.** It gates replay, replay/control, resume, retrain and three
  network-editing routes.
- **The adapter.** Add save / list / get / restore to `src/backend/recurrence_service_adapter.py`, over raw
  `httpx`, under §8's names (`save_snapshot`, `load_snapshot`, `list_snapshots`).
  - The service side is juniper-recurrence#172.
  - List through the service: canopy's local listing admits only `.h5` / `.hdf5`, and recurrence writes `.npz`.
- **The gating mechanism is contested.**
  - §8 item 3 and §11.4 step 3 say to widen the gates to a capability test.
  - 09-22 item 4 says to add a third branch and never widen a predicate.
  - Record the choice in `…PERSISTENCE-DESIGN.md`. If the capability test is wanted, the ruling is the owner's.
- **X10.** `RecurrenceBackend.initialize()` returns `True` without probing the service, and `selection_is_live`
  (`src/model_registry.py`) reads configuration only. Locate both by symbol.
- **Owner-gated, not this lane's:**
  - a juniper-recurrence Release carrying #172 and wave 2, cut after 2a;
  - a juniper-canopy Release after wave 3;
  - after each, a juniper-deploy pin bump.

  A recurrence 0.6.0 also needs juniper-ml's `recurrence` extra raised: it is capped at
  `juniper-recurrence>=0.5.0,<0.6.0`. Y2 closes only after all of that.

### The round-15 fix list (verbatim from B's predecessor; sources `S/r15_reports/R15{A,B,C,D}.md`)

**2c, from `S/r15_reports/R15A.md` (0 MAJOR):**
- **m1, the tripwire.**
  - Extend it: quoted `$(…)` values; one-line arrays; `mapfile`/`readarray` options that take arguments; `printf -v`; `${x:=…}`; `while read … done < <(find ROOT)` loops (track loop frames); joins past comment and blank lines; `|&`; odd trailing backslashes; `$'…'`; `${…}` and multi-line quotes in comment stripping; `: >` after `{`, `if` and `!`; `${X:-rm}`; rm-named variables; a bare `>` into a root; `rsync --delete`; `touch -d/-t/-r`; snapshot-name globs.
  - Then state its recognized forms exhaustively, in its docstring and in `pr_wave2c_ml.md`.
  - Add each form to the suites' planted-spelling lists, and E1–E6 to the harness.
- **m2, the fixtures.**
  - Plant a 40-day-old snapshot, a 3 MiB sparse one, a backdated isolated root and a dead-pid pidfile in both `--status` tests.
  - Check the mtimes of the dated files.
  - List the classes that remain in the body: world-writable, "no snapshot newer than a week", run-dir age after a write, the number of runs, routes at `--up`, and `--dry-run`-only sweeps.
- **n1–n6:**
  - the body still says "83 of 83" once (n1);
  - run the pinned black on the harness (n2);
  - the history claims are off: "nine", not "eight", and 2 of the 19 spellings were seen by round 14 (n3);
  - `~root/…` goes through the override (n4);
  - the harness should name `(module.Class.method)` (n5);
  - fix the false positives: narrow the isolated stack's `SNAPSHOTS?_DIR` to the service variables, and use `[*/]snapshots(?![\w-])` in the experiment stack (n6).

**2b, from `S/r15_reports/R15B.md` (0 MAJOR).** R15B validated its fixes on patched copies (`S/r15b/fix_matrix.py`).
- **m1:** add `"--workdir"` to `_COMPOSE_VALUE_OPTIONS`.
- **m2:** add `cd "$SCRIPT_DIR/.."` in both bring-up scripts; record and compare `os.getcwd()` in the shim; correct the texts that claim the render reads what the bring-up reads.
- **m3:** fail if a process still carries the run's `SHIM_LOG` after make returns; name `systemd-run` and `at` as limits.
- **m4:** `commit_2b_deploy.md` should say Docker refuses a missing recurrence root only, and name the six targets (`make restart` has no preflight).
- **n1–n6:**
  - the `make -n` texts (n1);
  - exactly one snapshot render per target (n2);
  - the shim's `DOCKER_HOST` should point at a nonexistent socket (n3);
  - untested exits X25–X27, and the body's claim that every row "really does something when run behind a recording shim", which row [108] contradicts (n4);
  - name the gated starts, `.env` and the secrets file (n5);
  - the harness should flush its output and delete its tree copies (n6).
- Add harness rows for X10, X18–X21 and the gated starts.

**The addendum, from `S/r15_reports/R15C.md`:**
- **M1:** re-point the live work list to `…queue-drained.md`, in v13 lines 7, 9, 39–40 and 155, the merge-approval sentence, and X11, which is `…queue-drained.md`'s owner ruling 2. Also:
  - row 1: §12.4's A-N2 loop ran; 7 of 8 seeds pass, and `equities`' Start is refused;
  - "Since the pins" bullets for canopy#674 (19:47:32Z), canopy#675 (20:06Z) and juniper-ml#2058 (21:53:07Z);
  - raise the splice tool's `SINCE_NOW_FLOOR` to the latest merge named;
  - add a PLAN step that lists the canopy-selection handoffs on `main` before opening.
- **M2:** canopy#674 extended the `nn_model` mirror to the live swap and the restart modal; canopy#368 is still OPEN.
- **m1, probe 2.5.0.**
  - A statement that contains a call or `:=` is code.
  - For G7, fix or list as gaps: `ui`-lane tests, `slow` / `requires_*` marks, unittest naming, nested classes, a parametrize `pytestmark`, and helper or `pytest.raises` assertions.
  - Pin the fixed cases in `util/ad-hoc/2026-09-23_check_probe_helpers.py`.
- **m2:** use `ls-tree -z`; honour `route`'s positional methods.
- **NITs:**
  - the probe still misreads an annotated `router: APIRouter = …`, `HTTPMethod.GET.value`, and routes that only share a prefix (`/api/selection/history`, `/v2/api/selection`, `/api/selection.json`);
  - the G7 path still crashes on a latin-1 test file and on a syntax error;
  - the splice tool's VALIDATION_LINE claims and its time bounds;
  - the extractor should warn on id-less split records;
  - v13 line 178 still says "CURRENT tags".

**Machinery, from `S/r15_reports/R15D.md`:**
- **MAJOR 1:** use drafts; `gh pr view` all four PRs before each merge; run the post-merge checks and blob-compare the squash commit at once if one merged out of order.
- **MINOR 1:** `--merged` should compare a CHANGELOG as a multiset of lines.
- **MINOR 2:**
  - comment the splice tool's seven `except Refused: pass` handlers (CodeQL "Empty except"; resolving review threads is required);
  - add "a review finding that needs code" to the delta route;
  - re-tie the head's blobs before each merge, and compare the squash commit's blobs after it.
- **NITs:**
  - write `.base` only after a verified open (NIT 1);
  - reuse the splice tool's placeholder census, and cross-check fill numbers against the record directory (NIT 2);
  - give post-merge follow-ups a route (NIT 3);
  - #184 must add the addendum's "Wave 2 is …" sentence (NIT 4);
  - `commit_2c_ml.md` must qualify the symlink loop as uutils-only (NIT 5);
  - GitHub appends ` (#N)` and rewrites the co-author trailer, so the message is not "verbatim" (NIT 6);
  - give `APPROVED_FREEZE` a value slot that the opener reads, and have the opener compare the live tools with the freeze's (NIT 7).
- **PLAN.md:** also document `--merged` in the delta route.

**Two items in that list are overtaken and must not be applied as written:**

- **R15C M1's target, `…queue-drained.md`, is stale** (move 5 above).
- **R15D MAJOR 1's "use drafts" is not R15D's fix, and drafts do not hold** (X1).

**Traps specific to Lane B:**

- **Security.**
  - Never print environment variable values.
  - Never read or decrypt a secret.
  - Run `make` only with `-o prepare-secrets` and a docker shim.
- **Tool claims must equal the implementation.** Rounds 14 and 15 kept finding overclaims. State an exhaustive
  list of the recognized forms, and put everything else explicitly out of scope, so later rounds score the gaps
  as admitted.
- **Verify against a pulled image, never a local build.** The compose service has both `build:` and
  `image: …:0.5.0`, so `make build` tags unreleased source as `0.5.0`.

---

## Lane C — canopy selection-reachability arc

**Done before this handoff** (from C's predecessor):

- **W5, the cleanup.** 26 worktrees were removed and 20 local branches deleted, in canopy, cascor and data, behind
  a content gate (`util/ad-hoc/2026-09-24_canopy_arc_worktree_cleanup.py`). The harvest is 174 MB in 25
  directories, at `/home/pcalnon/Development/python/Juniper/backups/worktree-harvest-2026-09-24-canopy-selection-arc/`.
- **Item 19 is closed.** juniper-data 0.16.0 contains #421, and it is published: GitHub Release at 08:52:14Z,
  GHCR, and PyPI (wheel 18:35:40Z, sdist 18:35:42Z).
- **X8's CHANGELOG entry reached juniper-data `main`'s `[Unreleased]`** through juniper-data#438 (`0f0f7e0e`,
  18:51:59Z).
- **Y7's dropdown half is grounded** in a dated note in §4.3 of
  `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`:
  - dash 4.2.0 renders `<label role="option" aria-selected>` around `<input disabled>`, with no `aria-disabled`;
  - an option is `{label, value, disabled, title, search}`, so no canopy prop reaches that element;
  - the note ends with four options for the owner.

**C1. The owner removes juniper-ml's worktrees.** An isolated session cannot, so these are the owner's to run.

- **Already verified by C's predecessor:**
  - `jazzy-soaring-minsky` and `bright-crunching-alpaca` hold only superseded drafts;
  - `tender-wibbling-flask` holds nothing that is not on `main`.
- **Also eligible now: `enumerated-marinating-puddle`,** C's predecessor's own worktree. Its PR #2087 merged at
  19:42:45Z. **Its content has not been compared with `main`.** Run
  `util/ad-hoc/2026-09-24_same_repo_worktree_content_probe.py` on it first.
- **At writing, all four read free** (`util/ad-hoc/2026-09-02_worktree_inuse_probe.py`).
- **`--force` is needed,** because each tree is dirty with untracked copies of what merged. It also deletes
  caches, and jazzy's three empty or near-empty `logs/*.log`.
- A9's two juniper-ml worktrees join this list once A6 is answered.

```bash
python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/{jazzy-soaring-minsky,bright-crunching-alpaca,tender-wibbling-flask,enumerated-marinating-puddle}
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jazzy-soaring-minsky
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bright-crunching-alpaca
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/tender-wibbling-flask
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree prune
git -C /home/pcalnon/Development/python/Juniper/juniper-ml branch -D worktree-jazzy-soaring-minsky worktree-bright-crunching-alpaca worktree-tender-wibbling-flask
```

**C2. Y7.** The owner picks one of the four options in the §4.3 note, or accepts the gap.

**C3. X8's release.** The next juniper-data release after 0.16.0 carries #437 and #438. At writing, the latest
release is still v0.16.0. Cutting the next one is the owner's call.

**C4. O9 / U-6.** It is triaged in A2(b). If it comes back as a design question, it is the owner's.

**C5. 2026-09-29T00:00Z.** The claims on Y2 waves 2 and 3 and X10 lapse, on § B's terms. See Lane B.

**C6. Phase 7: fast-forward the canopy, cascor and data primaries once nothing holds them.**

- **At writing, `util/ad-hoc/cascor_freeze_tell.py` exits 1** (FREEZE IN FORCE), with five holders:
  - the trio's cascor, uvicorn pid 2857489 on `:8202`;
  - its multiprocessing helpers, pids 2904570 and 2904571;
  - the trio's canopy, pid 2858037 on `:8051`;
  - a bash shell, pid 2964731, started 2026-09-19, with its cwd in the cascor primary.
- The trio's data leg is pid 2856834 on `:8101`.
- **Nothing here may stop the trio.** See X4.
- **A clean holder scan is not proof.** An import through an editable finder leaves no trace in `/proc` once the
  file is closed. That is why the cleanup script has `--no-primary-ff`.

**C7. A-N9 needs no action.** No `ModelSpec` accepts `structured`, and `arc_agi` stays unseeded.

**A trap specific to Lane C: an ignored path can still be committed.** The A-N2 report's 92 files under
`**/logs/` were force-added past that rule. Compare with `main` before calling anything "ignored".

---

## Cross-lane facts

**X1. The sweeper against Y2's merge order.**

- **What B's predecessor said:** "Open 2b, 2a and the addendum as drafts (R15D MAJOR 1)".
- **What R15D's fix actually says** (`S/r15_reports/R15D.md`):
  - "Before opening, ask the owner whether the sweeper is his, and record that these four PRs are excluded";
  - `gh pr view` all four before each merge;
  - blob-compare at once if one merged out of order;
  - "Alternatively, let 2b's preflight warn rather than refuse until 2a is released."
- **Drafts do not hold.** On 2026-09-23 drafted PRs were readied and armed 4–7 s apart (memory
  `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`). The owner has since answered: "Mine: fix
  forward".
- **The stake, per R15D:** if 2b lands before 2a is merged and pulled, every bring-up of deploy `main` refuses. The
  recurrence service is in profiles full / demo / dev / test, with `create_host_path: false`.
- **So the owner chooses one:**
  - exclude the four PRs from the sweeper;
  - approve the preflight-warns change, which is a code change and so takes the delta route;
  - accept a fix-forward.

**X2. The claims.** B's claims, and C5's date, are the same fact: whoever runs Lane B holds them until
2026-09-29T00:00Z. After that, only an open PR or a pushed branch keeps one alive. Opening PRs requires round 16
first. **A pushed branch with no PR keeps a claim alive without exposing it to the sweeper**; A's predecessor used
exactly that for its own handoff.

**X3. O9 flows from A2(b) to C4.**

**X4. The trio is Lane A's fixture.**

- Its processes started 2026-09-22 19:37–19:38Z, which matches the ledger's Phase 7 relaunch (2026-09-22).
- A4 reads it. C6's fast-forward waits on it. C's predecessor calls it "the peer's isolated stack".
- Stop it only by an explicit decision, never as a side effect.

**X5. Worktree cleanup across lanes is gated on A6.** Keep B's three worktrees until B closes:

- `.claude/worktrees/idempotent-jumping-sparkle`;
- `worktrees/juniper-recurrence--feature--y2-recurrence-snapshot-root--20260922-1512--749e7a35`;
- `worktrees/juniper-deploy--feature--y2-recurrence-snapshot-bind-mount--20260922-1520--13ee87aa`.

Their uncommitted state is the only copy.

## Shared traps (all lanes)

- **The session guard's refusals** (seen across the three predecessors and this session):
  - `git -C` into a sibling worktree of the same repo, even inside `$(…)`;
  - `for` loops;
  - `python3 - <<EOF` heredocs, or any heredoc with git words in it;
  - commands whose arguments are computed from variables, such as `find $W …` or `gh … $repo`;
  - a `jq` string containing `#`.

  Put the logic in a script under `util/ad-hoc/`, and use literal paths.
- **Signed commits.** Only GraphQL `createCommitOnBranch` signs (`util/push_signed_commit.py`,
  `util/open_signed_pr.py`). The owner's sweeper arms with the repo's default squash body, so a waiver trailer
  must be in a COMMIT body.
- **A whole-file upload against a moving `CHANGELOG.md`.** Repair with `git merge-file <yours> <base> <main>`. When
  both sides inserted at the same point, `util/ad-hoc/2026-09-24_resolve_changelog_conflict_theirs_then_ours.py`
  puts main's entry verbatim with yours below.
- **Mutation scripts edit the worktree in place.** Never upload while one runs.
- **gh 2.46.0:** `gh pr edit` fails, so use `gh api -X PATCH`; `gh pr checks` has no `--json`. Wait on checks
  with `util/wait_for_checks.py`.
- **Do not verify a squash waiver with `git log --format='%(trailers:key=Allow-Symbol-Loss)'`.** GitHub re-wraps
  the trailer block. The post-merge screen, which enforces the waiver, is the authority.

## Verification (run first; literal paths, no variables)

```bash
# From a juniper-ml checkout (any lane)
gh api repos/pcalnon/juniper-ml/commits/main --jq .sha              # 6c23fdde… at writing; it moves often
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -8              # 70 / 48 / 1 / 2 / 19; P0 1; P1 6; P2 12
gh pr view 2083 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '{state, merge: .mergeCommit.oid}'    # MERGED 48fc09e5…
gh pr view 684 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '{state, merge: .mergeCommit.oid}'  # MERGED f2147403…
python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py | tail -1    # 0 failed
python3 util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py   # at writing: 78c057e2, 26bf27b3, 96e7b105 UNREACHABLE
gh pr list --repo pcalnon/juniper-canopy --head fix/secret-leaks-683-validation --state all --json number,state   # [] at writing
gh release list --repo pcalnon/juniper-data --limit 2                # v0.16.0 Latest at writing
python3 util/ad-hoc/cascor_freeze_tell.py; echo "exit=$?"            # exit=1 (FREEZE IN FORCE) at writing
ss -ltnp | grep -E ':(8101|8202|8051) '                              # the trio; do not touch
wc -m /home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md   # 24,962 at writing
gh api repos/pcalnon/juniper-recurrence/compare/ca9609f0...main --jq '[.files[].filename]'   # has juniper-recurrence/CHANGELOG.md: 2a takes the delta route
gh api repos/pcalnon/juniper-deploy/compare/d589dd95...main --jq '[.files[].filename]'       # has CHANGELOG.md, docker-compose.yml: 2b takes the delta route
gh issue view 184 --repo pcalnon/juniper-recurrence --json state,updatedAt                   # OPEN, 2026-09-24T03:36:08Z

# Lane B only, in a session started in the idempotent-jumping-sparkle worktree
git status --short | head -40
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle/reports/2026-09-23_y2-wave2-consensus/session-state/r15 && sha256sum -c --quiet SHA256SUMS && sha256sum SHA256SUMS   # 66742624…4a3171
env -u JUNIPER_E2E_RECURRENCE_SNAPSHOT_DIR -u JUNIPER_RECURRENCE_SNAPSHOTS_DIR python3 -m unittest tests.test_isolated_stack_script tests.test_experiment_stack_script   # 193 OK (run from the worktree root)
python3 util/ad-hoc/2026-09-23_placeholder_census.py                  # 2c 6/4, 2a 4/0, 2b 0/0, addendum 3 (self-test)
python3 util/ad-hoc/2026-09-23_check_open_pinned_pr.py reports/2026-09-23_y2-wave2-consensus/session-state/r15   # bad=[] (live worktrees tie to r15)
```

## Git state at handoff

- **This session:** worktree `bubbly-meandering-pie`, branch `worktree-bubbly-meandering-pie` at `6c23fdde`.
  - New and untracked: this file, `util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py`, and the consensus
    record under `reports/2026-09-24_canopy-combined-handoff-consensus/`.
  - No PR has been opened. The owner decides whether to open one, and whether it also archives the two off-`main`
    predecessors.
- **Lane A:**
  - `graceful-sprouting-panda`: branch `docs/canopy-e2e-phase9`, local head `808b74df`. Its remote was
    squash-merged as #2083 and no longer exists.
  - The branch `docs/canopy-e2e-handoff-2026-09-24` (`dd4413e5`) is on origin, with no PR.
  - canopy `fix/idle-cuts-round3-wording`: local at `135c2782`, clean. Its remote is gone; #684 merged.
- **Lane B:**
  - `idempotent-jumping-sparkle`: per B's predecessor, branch `docs/canopy-selection-0908-handoff-status-2026-09-22`
    at `5ea8e273`, with 2c, the addendum and the tools uncommitted. This session could not run git there.
  - The recurrence worktree has 2a's four files staged and modified.
  - The deploy worktree has 2b's eight files staged and modified, plus `k8s/helm/juniper/values.yaml` modified.
  - No remote branch and no PR exists for any of the four.
- **Lane C:** only `enumerated-marinating-puddle` remains, and its PR (#2087) has merged.

## Documents

- **Referenced:**
  - the three predecessors (the table at the top);
  - `HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`;
  - `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md`;
  - `HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md`;
  - `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md`;
  - `HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md` (all in
    `prompts/thread-handoff_automated-prompts/`);
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`;
  - `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`;
  - `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`;
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`;
  - `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md`;
  - `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`;
  - `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`;
  - `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`;
  - Lane B's `S/main/PLAN.md`, `S/main/handoff_v4.md` and `S/r15_reports/R15{A,B,C,D}.md`.
- **Created:**
  - this file;
  - `util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py`;
  - `reports/2026-09-24_canopy-combined-handoff-consensus/`.
- **Changed:** none.

## Validation record

VALIDATION_RECORD_PENDING
