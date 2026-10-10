# HANDOFF 2026-10-03 — P2 canopy: E2E validation arc + canopy-selection arc (CONSOLIDATED): F-CANOPY-059 (P0) still unfixed, Phase 10 unfiled, Y2 wave 2 stalled at round 15 with its claim lapsed, selection arc owner-gated only

**Written**: 2026-10-03 by a drafter session of the handoff-consolidation task (juniper-ml worktree
`.claude/worktrees/snappy-strolling-waterfall`, branch `docs/handoff-consolidation-2026-10-03`, cut from
`origin/main` `afb02801`). **This consolidated file was itself written without consensus validation.**

**Live probe window**: 2026-10-03, ~08:15Z–08:38Z UTC (gh, PyPI JSON, local file reads; no git against other repos).

**Consolidated sources** (all in `prompts/thread-handoff_automated-prompts/`):

| source | self-declared validation |
|---|---|
| `HANDOFF_2026-09-22_canopy-e2e-phase7-f053-and-f048-fixed-f054-open.md` | not stated (its review checks were orchestrator-only; re-evaluated item-by-item 09-23 in its own top section) |
| `HANDOFF_2026-09-23_canopy-e2e-phase8-f054-fixed-f055-filed-cuts-pending.md` | not stated |
| `HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md` | not stated (carries a successor's "superseded in part" note) |
| `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md` | **"This handoff is NOT validated"** |

**Also read and carried** (predecessors the combined handoff left unfinished; frozen copies on `main` via juniper-ml#2096 under
`reports/2026-09-24_canopy-combined-handoff-consensus/r1/`):

- the combined DRAFT itself, `HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md` (untracked in
  worktree `bubbly-meandering-pie`; byte-identical to `r1/DRAFT_r1.md`, sha256 `8c2fa290…`), plus its round-1 fix list
  F1–F22 and the five reports `r1/reports/R1{A..E}.md` (four SAFE AFTER FIXES, R1-E FAIL). **All F1–F22 are folded in
  below**, so this file does not repeat round 1's defects;
- predecessor **A** `HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md` (origin branch
  `docs/canopy-e2e-handoff-2026-09-24`, no PR) — not validated;
- predecessor **B** `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md` (untracked, only in worktree `idempotent-jumping-sparkle`) — not validated;
- predecessor **C** `HANDOFF_2026-09-24_canopy-selection-cleanup-done-item-19-closed-y7-grounded-owner-calls-remain.md` (main, #2087), and its chain
  `…canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md`, `…four-rulings-made-x11-f2-f1-x8-to-implement.md`,
  `HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md` (`…queue-drained.md` below).

**Supersedes**: the four sources above, the combined draft, and predecessors A, B and C.

**Documents of record**: the ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (its Phase 9 "Still owed after this
phase", items 0–17, is authoritative for Lane A); the matrix `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`; the
consensus procedure `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`; the selection design
`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`; the persistence design
`notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` ("wave N" = its §11.4 step N); Y2's definition
`notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-DEADLOCK-PROPOSALS.md` §6.

---

## Goal statement (paste as the new thread's first prompt)

Continue the juniper-canopy work from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md` (juniper-ml). Read it
in full. Three lanes, separable across sessions: **A** the E2E validation arc (queue = ledger
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 9 "Still owed", items 0–17); **B** Y2 wave 2 (four prepared,
never-opened PRs: juniper-deploy 2b, juniper-recurrence 2a, juniper-ml 2c, and the addendum to the 09-08 selection handoff); **C** the
canopy-selection arc's residue, which is owner calls only.

**Completed so far (verified 2026-10-03):** Phase 7/8/9 ledger PRs merged (juniper-ml#2030, #2054, #2083 `48fc09e5`); canopy#670 (F-054),
#676 (idle cuts), #684 (#676's round-3 follow-up, `f2147403`) merged; canopy#685 (`dc5ea02e`, 09-24 23:24Z) fixed F-CANOPY-061/062's
substance; cascor#690 merged (`0fbb447a`, 09-25 02:06Z); the selection arc's four rulings shipped (canopy#680/#681/#682, cascor#685/#687,
data#437); juniper-data 0.16.0 is on PyPI; the round-1 handoff, its `r1/` record (including `DRAFT_r1.md`) and the reachability tool merged as juniper-ml#2096 (09-26; the prompts/ draft itself did not). Triage still prints
70 findings / 48 fixed / 1 accepted / 2 withdrawn / 19 open (1 P0, 6 P1, 12 P2); matrix BLOCKED 20. **In canopy nothing has moved since
2026-09-25** except dependabot merges; the primaries were pulled (C6).

**Before anything else:** pick lanes per § Session layout (the verification block is split by checkout); then run § Verification commands
for your lane; then put ONE owner message containing every owner-gated item below (O1–O17). **No merge approval is carried** — ask before the first merge.

**Remaining work, ordered.** (OG = owner-gated; AG = agent-doable.)

Lane A (E2E):

1. **DONE 2026-10-04 — this item is closed.** F-CANOPY-015, F-059 and F-056 are FIXED and were verified live on a throwaway stack: 11 of 11 checks
   passed (evidence `reports/2026-10-04_canopy-replay-redrive/verdicts.json`). Three PRs did it:
   - canopy#694 (F-059), canopy#696 (F-056) and canopy#697.
   - canopy#697 fixed the range-end off-by-one and the window end, and guarded the render-echo loop.
   - Merge commits: `5ff4241c`, `3cc4fdb2` and `1b2dd438`.

   To drive it again, use `util/ad-hoc/2026-10-04_replay_redrive_stack.bash` and `util/ad-hoc/2026-10-04_replay_redrive.py`, and replay an EXPLICIT save
   (`POST /v1/snapshots`). cascor's automatic per-pass snapshots carry no history. The entries below are history.

   **UPDATE 2026-10-03: the code fix is DONE, in canopy#694, merged as `5ff4241c`.** What remains of this item:
   - F-CANOPY-015's live re-drive and F-059's live check, against a writable cascor.
   - ~~F-CANOPY-056's fix, which F-059 no longer masks.~~ **DONE in code 2026-10-03: canopy#696, merged as `3cc4fdb2`.** It still needs the
     live drive. That drive should also watch for a possible feedback loop: `render_session` writes values that are `queue_control`'s Inputs.
     The loop is unverified; see the F-056 status bullet in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`.
   - The range-end off-by-one follow-up: cascor's `end` is exclusive, while the slider sends an inclusive value. `test_replay_player_panel_gate_coverage.py` pins that outbound value.

   The original item follows, for context. **AG — F-CANOPY-059 fix (P0, ledger item 16).** `replay_player_panel.py` still does `range_value = summary.get("range") or [start, end]`
   then indexes `range_value[0]` (canopy `main` `58b467ca`, `:508` and `:534`) [VERIFIED 2026-10-03: source fetched via gh]. Convert cascor's
   `range` dict to `[start, end]` in the readout and the range slider; list or no range must keep working; regression test on Phase 1's measured
   payload (segment 7), correct `test_p2_wave_batch_a.py:179-190` and sweep sibling fixtures claiming "measured" shapes. Then F-CANOPY-015's live
   re-drive, then F-CANOPY-056's fix. **Every drive starts a replay, which replaces cascor's live network** — needs a writable cascor, not the trio.
2. **DONE 2026-10-05 — this item is closed.** The ledger's Phase 10
   (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) files F-CANOPY-060 to -067, declines O4 and O9,
   corrects Phase 1's W1-09 PASS to FAIL and re-rates F-CANOPY-057 to P2, after five consensus rounds (2026-10-04/05; the
   last changed no number, disposition or action). Predecessor A is
   archived with it. The id the defect-register arc should hear about: its unreserved "Nothing was loaded…" item is
   F-CANOPY-063. The original item follows, for context.

   **AG — Phase 10 ledger PR** filing the peer arcs' items (details in § Context A2). F-CANOPY-060 still present [VERIFIED 2026-10-03:
   `dashboard_manager.py:8410` on canopy main]; F-061/062 to be filed as FIXED-BY canopy#685 [VERIFIED 2026-10-03: merged `dc5ea02e`, body
   items 3 and 4]; the "Nothing was loaded…" copies are now a real divergence [VERIFIED 2026-10-03: absent from cascor main `manager.py`,
   present at canopy main `dashboard_manager.py:8381` and `test_start_fresh_refusal_and_modal_text.py:42`]; O2–O5 and O9 from the selection
   arc. Archive predecessor A in this PR (its branch `dd4413e5` still has no PR).
3. **DONE 2026-10-08 — this item is closed.** The ledger's Phase 11
   (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) records the F-058 census v2, run live twice
   (canopy `main` `60ae1870` and `c7876f5a`), after six consensus rounds (2026-10-05 to 10-08; the last changed no
   number, disposition or action). It landed by the PR from branch `docs/canopy-e2e-phase11`
   (`gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase11 --state all`).
   - F-CANOPY-058 is observed live: 29 of 611 requests evicted, in runs of up to 11 and 34.8 s.
   - Its trigger, the strand watchdog's false fires, is filed as F-CANOPY-068: P1 if a CHANGELOG's description of an
     internal mechanism counts as documented, else P2 (owner batch O17).
   - Counts 79/53/1/2/23, 7 P1, 16 P2. New items 24–26: F-CANOPY-068 with item 4's design, census triggers fired from
     the page, and the reach of the §6.3 ruling plus a sweep of canopy's manual.
   - The evidence is in `reports/e2e-canopy-2026-09-02/f058-census-v2/`, and the census in `util/ad-hoc/2026-10-04_f058_census_v2_*`.
   - The original item follows, for context.

   **AG — F-CANOPY-058 census instrument repair, then the census** (ledger item 0, first half). Blocker: none. [NOT RE-PROBED — from ledger Phase 9]
   **Status 2026-10-05: run, not yet recorded.** The repaired census v2 passed its synthetic check (6 of 6) and ran live on
   canopy `main` `60ae1870`. The strand watchdog fired falsely 13 times in ~25 min, each mid-request, and 3 of those fires
   started eviction cascades (2, 11 and 4 lost responses); the scripted triggers landed too late to test the claim. The
   files and a results note are outside the repo, in `/home/pcalnon/Development/python/Juniper/backups/2026-10-05_f058_census_v2_final/`.
   Owed: move them under `util/ad-hoc/2026-10-04_f058_census_v2_*` and record the run as the ledger's Phase 11, with
   its own consensus rounds.
4. **DONE IN CODE 2026-10-08: canopy#731** (branch `fix/f055-f058-f068-request-ack-pacer`, head `65ead946`).
   - It went through three independent review rounds: `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_canopy731_pacer_rounds1-3.md`.
   - Live: 0 of 912 requests evicted across four census runs, and F-055's census APPLIES on `2689a207`
     (`reports/e2e-canopy-2026-09-02/pacer-live/README.md`).
   - Still owed: the merge, if pending, and the ledger's Phase 12 with its own consensus rounds. See
     `HANDOFF_2026-10-08_canopy-pacer-731-landed-phase12-owed.md`.
   - The original item follows, for context.

   **AG — one redesign for F-CANOPY-055 + F-CANOPY-058 + F-CANOPY-068** (ledger item 0, second half, and Phase 11's item
   24): request/ack handshake pacer. **Unblocked 2026-10-08** (item 3 is done).
   - It must answer F-CANOPY-068 too. Lane B's pacer takes the watchdog off the guarded lane. A design that keeps a
     watchdog must base it on progress, not on samples of `disabled`.
   - Phase 11's "Still owed" lists the canopy text to correct, and the CHANGELOG `[0.8.0]` description that needs a
     correcting entry.
   - Phase 11's item 25, census triggers fired from the page, belongs with its tests.
5. **AG — ledger items 1, 2, 6, 7, 8, 9 (test gap / M-TOPOLOGY-16), 11, 12, 13, 14** (§ Context A7).
6. **AG — MEMORY.md compaction** (24,929 chars by `wc -m` against a ~25,000-character load limit [VERIFIED 2026-10-03]) `[ALSO all paths]`.
7. **AG after O2 — worktree cleanup** (canopy and juniper-ml; § Context A9). Never `util/remove_stale_worktrees.bash`.

Lane B (Y2 wave 2):

8. **OG first (O7)** — the claim lapsed 2026-09-29T00:00Z with no open PR or pushed branch [VERIFIED 2026-10-03: no Y2 branch on recurrence or
   deploy origin, no PR]; ask whether Y2 wave 2 continues and who runs it, and settle the sweeper-vs-merge-order question.
9. **AG — re-base the delta**: recurrence `main` is now `be081fae` (+#186, #187, #188), deploy `9403dbf5` (+#230–#238), juniper-ml `afb02801`
   [VERIFIED 2026-10-03: gh commits/main]. Re-run the moved-path checks for all four upload sets.
10. **AG — round-15 fix pass** (never started [VERIFIED 2026-10-03: no file under `S` newer than B's handoff; no `r16`/`fix16`]), then round 16+,
   then open (2b→2a→2c→addendum) and merge (2c→2a→2b→addendum) per `S/main/PLAN.md`, then closing work (§ Context B).

Lane C (selection):

11. **OG** — C1 worktree removals, C2 Y7, C3 X8 release `[ALSO P4]`, C4 O9 if it returns as a design question. C5's date has passed; C6
   changed (§ Context C).

**Key context.** The owner's sweeper readies and arms open PRs (drafts too); its merges are intended ("Mine: fix forward", 2026-09-24
07:32:48Z) — validate BEFORE opening. Never touch the trio (`:8101` data, `:8202` cascor, `:8051` canopy) [VERIFIED 2026-10-03: still
listening, pids 2856834 / 2857489 / 2858037, started 2026-09-22]. Never print secrets, env values or the owner's email. Never merge other
sessions' PRs. Name every referenced or changed document by filename.

---

## Dependencies on other paths

- **P4 (release & distribution)**: C3 — X8 (`equities_seq` 6.0.0, data#437/#438) ships only in the next juniper-data release after 0.16.0
  [VERIFIED 2026-10-03: GitHub Latest and PyPI are still 0.16.0]. Lane B's tail is also P4's: a juniper-recurrence Release after 2a, a
  juniper-canopy Release after wave 3, a juniper-deploy pin bump after each, and raising juniper-ml's `recurrence` extra
  (`pyproject.toml:105`, `juniper-recurrence>=0.5.0,<0.6.0` [VERIFIED 2026-10-03]) for a recurrence 0.6.0.
- **P3 (defect register round 42)**: F-CANOPY-060–062 ids were RESERVED and given to that arc to cite; the "Nothing was loaded" item came from
  its session (`defect reg [042116]`, `bc31e993`). When the Phase 10 PR assigns an id to it, send the id to whichever session now runs P3.
  **Done 2026-10-08:** Phase 10 assigned F-CANOPY-063. No P3 session was running, so the id is recorded under item 11 of
  `HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` and in the INDEX's P2 ↔ P3 row.
  canopy#685 (P3's PR) is merged, so the old "get the PR number" step is closed.
- **P6 (perf lane), possibly**: the trio holds the cascor primary (`util/ad-hoc/cascor_freeze_tell.py` reported FREEZE IN FORCE on 09-24);
  stopping the trio is an explicit owner decision (O13). [UNVERIFIED — freeze tell not re-run; it is a host probe]
- **All paths**: MEMORY.md compaction (item 6) is shared; re-read right before each write.

---

## Context the remaining work needs

### Session layout (F3, F12 applied)

- **Lane B cannot move.** Its tools hard-code `ML = J / "juniper-ml/.claude/worktrees/idempotent-jumping-sparkle"`:
  `2026-09-23_freeze_round.py:48`, `2026-09-23_open_pinned_pr.py:73`, `2026-09-23_placeholder_census.py:38`, and a fourth,
  `2026-09-23_freeze_round14.py:38`, all in that worktree's `util/ad-hoc/`. Run Lane B in a session started in that worktree, and read this
  handoff there by its absolute path (that tree is at `5ea8e273`, older than main).
- **A worktree-isolated session refuses git against any sibling worktree of its own repo**, loops, `$(…)`, computed arguments, heredocs
  naming git, and a `jq` string containing `#`. Put logic in `util/ad-hoc/` scripts with literal paths. The refusal set varies by session.
- Lane A's juniper-ml edits: a fresh worktree from current `main`. canopy/cascor work: worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`.
- **Never do Lane A's juniper-ml edits in `idempotent-jumping-sparkle`**: `open_signed_pr.py` uploads whole files, so they would revert main.
- **Locate every file:line by its quoted text before editing** (F13); line numbers below are measured at the stated commit.

### Lane A — the E2E arc

**A1 (F-CANOPY-059) traps.** `util/isolated_stack.bash` defaults to the trio's ports, so a bare `--down` kills the trio; use a wrapper that
refuses defaults (e.g. `util/ad-hoc/2026-09-23_a_n2_stack.bash`). End each replay (sidebar Reset Training, or cascor `/replay/control` stop);
check Start and Apply afterwards; read `/api/status`'s `fsm_status` and the Network Editor badge, because the status bar reads Stopped both
during and after a replay.

**A2 (Phase 10).** File through the consensus procedure; re-derive each first; decline or withdraw with a reason.
- Mechanics: ledger ~791 KB — push it in its OWN signed commit (`util/push_signed_commit.py`); a 499/502 can still land, re-read the ref
  before retrying; rebase onto live `main` immediately before upload. **To create a branch without opening a PR** (F5):
  `gh api -X POST repos/pcalnon/juniper-ml/git/refs -f ref=refs/heads/<b> -f sha=<main sha>`, then
  `util/ad-hoc/2026-09-24_push_phase9_signed_groups.py --base <sha> --branch <b>` (pushes the ledger alone and last), then open the PR.
- **(a) defect-register items, ids RESERVED:**
  - **F-CANOPY-060** (NIT/LOW, pre-existing): `_producer_detail_from_refusal` (`dashboard_manager.py:8404`; cut list `:8410`) cuts at
    `" To accept it,"` AND `" The resulting dataset"`, so juniper-data's "The resulting dataset will be permanently annotated as truncated."
    (`juniper_data/core/limits.py`, `InputTooLargeError`) never shows. Proposed fix: cut only at `" To accept it,"`. Also check the prompt's
    three options ("broken rows", "placeholder values"; were `:8442-8444` at `7ab994e5`) fit a cap refusal if cascor routes one through it.
  - **F-CANOPY-061** (LOW; LOW 3 of #683's validation): `_docs_enabled` pinned by one sample (`src/main.py:517` at `7ab994e5`). **FIXED-BY
    canopy#685** (`_docs_enabled = not get_api_key_auth().enabled`).
  - **F-CANOPY-062** (LOW; LOW 4): padded-key WARNING named `CANOPY_API_KEY` for the `_FILE` source; comment at `security.py:350` wrong.
    **FIXED-BY canopy#685** (`_PADDED_KEY_FILE_WARNING`). #685 also fixed two HIGHs (padded outbound keys leaking; a non-ASCII key reaching
    Sentry) — mention, do not file as canopy E2E findings unless re-derived as such.
  - **"Nothing was loaded…" (NIT, pre-existing, no id reserved)**: cascor#690 removed #687's sentence from `_refuse_dataset_wider_than_network`
    because it was false once a start's inline tensors were bound. canopy keeps two copies: `CASCOR_SENTENCE` in
    `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42` (comment `:41` calls it verbatim) and the alert text in
    `_start_fresh_required_alert` (`dashboard_manager.py:8381`). Nothing breaks (canopy parses the marker and first sentence only). Assign an id
    in filing order if it survives re-derivation.
- **(b) selection-arc observations, ids from F-CANOPY-063 in filing order** [UNVERIFIED — from predecessor A and the combined draft, not validated; not re-probed] (O1 is already F-CANOPY-055). Source for O2–O5:
  `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md` § "Observations (not A-N2 failures)", lines 188–224 on main; **O9's
  source is `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md:76-81`** (F9).
  - O2: both metric charts plot `metric["epoch"]` (a per-phase counter) as x (`metrics_panel.py` `_parse_metrics` / `_create_accuracy_plot`),
    so accuracy sits at x ≤ 51 on a ~10k axis for every CasCor case. Likely the most user-visible.
  - O3: `/api/set_params`'s `applied` list omits keys routed over `/ws/control` and `epochs_max`'s `not-updatable` skip, though values land.
  - O4: `/v1/health` `version` from installed metadata (0.6.0, `JuniperCanopy1`'s stale editable install) vs source 0.8.1; history OBS-1,
    canopy#526. May be an environment artifact.
  - O5: 80 "Network stats API returned 503" warnings under the recurrence backend (`/api/network/stats` has no recurrence branch). Decide scope.
  - O9: after a refused Start, sidebar "Current Dataset" shows the staged dataset (it follows the selection, which hydrates `pending` first);
    routes are honest. Pre-existing U-6 design question → C4 if it survives.

**A3 (ledger item 17, OG — O3).** A replay replaces cascor's live network: at cascor `main` `b2921712`, `start_replay` (`manager.py:6399`)
calls `_load_snapshot_to_network` (`:6429`), which sets `self.model` (`:6186`); neither `reset()` nor `stop_replay()` restores it;
`_auto_snap_best` defaults False (`:1550`) [VERIFIED 2026-10-03: grep of main]. canopy promises "a read-only playback session"
(`hdf5_snapshots_panel.py`, was `:533`; proxy docstring `main.py:3016` on canopy main). Fix = canopy wording, cascor design, or both.

**A4 (census, ledger item 0 first half)** [NOT RE-PROBED — from ledger Phase 9 item 0]. `util/ad-hoc/2026-09-24_f058_trigger_census.py` was refuted before its first run (scores every
answer without props EVICTED; cannot count a watchdog fire). Fix first: record the executed transition (wrap `window.store.dispatch`, log
`addExecutedCallbacks` by `executionPromise`, or `add_init_script` shim before the store is built); detect a fire from lane state before the
reset; score T-apply only with a request in flight and re-check in `took()`; pass a synthetic scratch-dash check with and without
`no_update`. Count EVICTIONS (the idle feeder answers `no_update`). Five triggers: gate write, tab switch, Apply clamp+release (simulate via
the clamp Store — a real Apply PATCHes the trio's cascor), display-mode change, 10 idle minutes. Window and verdict floor sized to the lane's
~7.5–8 s self-clocked cadence, fixed before the run. Leg: `util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <canopy worktree on
main>/src <port>`, export `JUNIPER_E2E_CANOPY_URL`; it reads `:8101`/`:8202` and must not write them; never `:8051`.

**A5 (redesign)** [NOT RE-PROBED — from ledger Phase 9 item 0]. Candidate: the **ledger's Phase 9 review Lane B** handshake pacer (ledger ~`:8996`): clientside request/ack tokens, no
`disabled`-prop guard, no `running=`, and it must cover a non-Interval Input (#613's feeder has one). Partial alternatives (from
`HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`): progress-based watchdog reset on `n_intervals`
change, or a gate returning `no_update` for global lanes on a tab-only change. Real-renderer tests: tab switch mid-request, Apply spanning a
request, second-Input change mid-request, 10 idle minutes with the watchdog. Live: census + triggers on the fix leg; F-CANOPY-025's allow arm
on a leg where old code fails and training may start. Correct the text F-058 contradicts (canopy main): `dashboard_manager.py:472` ("the
harmless window"), `:4736` ("Self-healing, bounded to one cycle"), `test_poll_gating.py:312-313` ("the apply clamp alone"). Why the first fix
was refuted: the fused gate writes `disabled` on every tab switch/mount/Apply change, the Apply releases, the strand watchdog false-fires, and
`completeJob()` releases the guard for an EVICTED request too (`dash_renderer.dev.js:925-937`, `:966-986`), so eviction cascades. KEEP canopy
worktree `…fix--f055-status-bar-running-guard--20260923-1425--ce78e0de` (provenance `884d22fb`, `cf6fb1dc`, `7a4a2e33`).

**A6 (ledger item 15, OG — O2/O4/O5).** Provenance for local-only commits the ledger cites (F1, F2 applied):

| repo | holder | cited commits |
|---|---|---|
| canopy | **reflog only** of `perf/idle-dispatch-cuts-v2` (+ its worktree HEAD) | `78c057e2` |
| canopy | **reflog only** of `fix/idle-cuts-round3-wording` (+ its worktree HEAD) | `26bf27b3`, `96e7b105`, `b07943d6` |
| canopy | branch `fix/f055-status-bar-running-guard` (KEEP) | `ce78e0de`, `884d22fb`, `cf6fb1dc`, `7a4a2e33` |
| canopy | branch `perf/idle-dispatch-cuts-v2` | `8990f65c`, `5310b81a`, `c360fb53`, `040dc5c1` |
| canopy | branch `perf/idle-dispatch-cuts` | `668380ec`, `723ee812` |
| canopy | branch `fix/f054-replay-block-clientside` | `723ee812` (two branches hold it) |
| canopy | branch `fix/idle-cuts-round3-wording` | (tip `135c2782`; holds the reflog-only row above) |
| juniper-ml | local `docs/canopy-e2e-phase9` (worktree `graceful-sprouting-panda`, tip `808b74df`) | `f6861234`, `5a0e4ea9`, the ten frozen Phase 9 commits `e624c281`…`b0eb4ac1` |
| juniper-ml | `worktree-squishy-dancing-moth` (tip `b54e3b3f`) | `b54e3b3f`, `800c20bb` |
| juniper-ml | `worktree-partitioned-twirling-stream` (Phase 8's own session worktree) | `ada8e50c` |

[VERIFIED 2026-10-03: canopy refs and reflog files read directly; juniper-ml `git branch -a --contains` from this worktree; none is on any
origin branch.] **The threat is cleanup, not `gc`**: gc config is default; removing a worktree deletes its HEAD reflog and `branch -d/-D`
deletes the branch reflog. Options for the owner: push to a provenance ref per remote (e.g. `refs/provenance/canopy-e2e-phase9`, pointing at
branch TIPS), keep a local ref, or accept loss. `util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py` (on main via #2096) reports
BRANCH 29 / REFLOG-ONLY 4; its reflog upgrade is unvalidated. Also owner: the account's later actions (update-branches on ml#2066 and
data#434 23:16–23:17Z; ml#2045 disarm/re-arm 23:48Z; cascor-worker#196 merge 01:21:37Z; #676's CI re-run 01:22:32Z; ml#2045 draft/ready
03:04–03:05Z, all 09-23/24) and the ratings on plan §6.3 (`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`):
F-056/057 P1, F-059 P0, against F-014's P1 precedent.

**A7 (ledger Phase 9 items, carried; the ledger text is authoritative)** [NOT RE-PROBED — from the ledger on main, unchanged since #2083]:
1 hunt the F-053 latency regression between `f9defb4` and `9bffaba1` (with the drain parked L sat 3.9–5.4 s under load; profile with
`util/ad-hoc/2026-09-22_canopy_idle_cpu_profile.py` and a dispatch-rate census by source); 2 the timestamp-only `/api/state` store rewrite,
needing a design that keeps the phase-duration clock; 3 OG F-004's contract (re-render measured 22–30 s vs ≤16 s); 4 OG
`FULL_HISTORY_POLL_TICK_MODULUS` → 1 (measured 32.4 s); 5 superseded by item 0; 6 F-CANOPY-049 and cascor#674's follow-ups (the same
swallow-and-forget pattern in juniper-service-core's and canopy's WS managers); 7 CAN-015's replay loop + F-056 +
F-057, behind F-059; 8 M-CANDIDATES-10/-11 re-drive; 9 OG M-DATASET-17..26, plus the M-TOPOLOGY-16 fade half and F-038's browser-level test
gap (AG); 10 OG the metrics replay drives no chart; 11 the starvation mechanism re-derived under FIFO (dash 4.2.0 priority is INERT;
`dashboard_manager.py:445` still says "the lowest-priority callbacks"); 12 F1 (pause at the current index on a slider trigger equal to
`slider_w`) and Phase 8's round-1 minors; 13 stale refresh-rate config (`conf/app_config.yaml:170,181`, `docs/USER_MANUAL.md:1344` —
re-locate, #684 edited the manual) and the live-check instrument's gaps (missing node reads 0 ticks; empty `paths.strs` reads "dead timer
absent"; PROBE never checks node id; no store read-back after `setProps`; `ticks_10s_cleared` keeps no raw counts; no host load) — fix
before `2026-09-23_idle_cuts_live_check.py` reruns; 14 standing rule: a census must be able to fail.

**A8 (MEMORY.md).** Limit is ~25,000 CHARACTERS (`wc -m`), owner target 20 KB (`feedback_memory_index_target_is_20kb.md`). Retire entries,
never strip hooks; `util/ad-hoc/2026-09-12_memory_index_linkset.py snapshot <f>` then `compare <f>`; compare link SETS, not counts; re-read
before each write. The canopy E2E entry is this path's (F22: there are no "ACTIVE" lines in MEMORY.md).

**A9 (cleanup, gated on A6).** Each repo's `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (juniper-ml:
`notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`). Eligible now: canopy `…control--main--20260923-1423--3a6dea95`
(detached). Hold until A6 is answered: `…fix--idle-cuts-round3-wording--20260923-2238--e9053227`, `…perf--idle-dispatch-cuts-v2--20260923-1418--3a6dea95`,
`…perf--idle-dispatch-cuts--20260923-0830--723ee812`, `…fix--f054-replay-block-clientside--20260923-0036--2f973ca2`; juniper-ml
`graceful-sprouting-panda`, `squishy-dancing-moth` (owner-run, C1). Also `bubbly-meandering-pie` (the combined session; its draft is
superseded by this file) and `lively-humming-pixel`, `partitioned-twirling-stream` (earlier Phase 7/8 sessions; the latter holds `ada8e50c`).
[VERIFIED 2026-10-03: all listed worktrees exist.]

**Lane A traps** [UNVERIFIED — from predecessor A and the combined draft, which were not validated]. The trio's cascor fixture is
"2/68/2" (uuid `1cd15120…`), and a resumed snapshot has NO metrics history. PNGs go through the signed API as LFS pointers
(`util/ad-hoc/2026-09-23_lfs_pointers_for_api_commit.py` stores each image and writes its pointer; then `git lfs push --object-id origin
<oids>`). Agent briefs must forbid printing secrets or env values AND sending the owner's email anywhere (the A-N2 subagent sent it to an
external site in a User-Agent header; `…queue-drained.md:105`). Lanes build fake secrets by concatenation and print booleans only.
Consensus mechanics: freeze the artifact as a local commit and have lanes read git OBJECTS; briefs live in `reports/e2e-canopy-2026-09-02/drafts/`.
canopy `addopts` already has `-q` (another `-q` hides the summary); use `conda run --no-capture-output -n JuniperCanopy1`.
Full canopy lane for refactors (source-window tests read `dashboard_manager.py`): repo root, `src/tests/{unit,regression,contract,performance}/`,
`--timeout=60`, `LIBTORCH= LD_LIBRARY_PATH=`. Browser runs: `JUNIPER_E2E_BROWSER_GPU=1`, ≤3 concurrent browsers (per-IP WS cap 5), `df -i /tmp`
first (39% on 2026-10-03; 98% on 09-23 crashed Chromium). Delivered-but-not-applied = eviction; no request = readiness block. canopy squashes
with `COMMIT_MESSAGES`; `safe_merge.py` sends no body, so `Allow-Symbol-Loss:` trailers in commit bodies survive; check `auto_merge` on your
own PR before landing. Archive lane reports with `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`; `--allow-shape
AGENT_ID=LITERAL` only after reviewing by known-literal and length; `key_material()` refuses key material whatever is allowed;
`util/ad-hoc/2026-09-24_secret_shape_check.py` tests the four shape users. Earlier E2E review lanes C5, R4-A, A1 and B2 printed the owner's
email in their own local output (nothing sent).

**Shared traps (all lanes)** [UNVERIFIED — from the combined draft, not validated]. gh 2.46.0: `gh pr edit` fails, so use `gh api -X
PATCH`; `gh pr checks` has no `--json`; wait on checks with `util/wait_for_checks.py`. Do not verify a squash waiver with `git log
--format='%(trailers:key=Allow-Symbol-Loss)'` (GitHub re-wraps the trailer block); the post-merge screen, which enforces the waiver, is the
authority. A whole-file upload against a moving `CHANGELOG.md`: repair with `git merge-file <yours> <base> <main>`; when both sides inserted at
the same point, `util/ad-hoc/2026-09-24_resolve_changelog_conflict_theirs_then_ours.py` puts main's entry verbatim with yours below. Only GraphQL
`createCommitOnBranch` signs (`util/push_signed_commit.py`, `util/open_signed_pr.py`); the sweeper arms with the repo's default squash body, so
a waiver trailer must be in a COMMIT body.

### Lane B — Y2 wave 2 and the 09-08 addendum `[ALSO P4 for its release tail]`

[UNVERIFIED unless tagged — from `HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md` and the combined draft, which were not validated]

- **Request** (verbatim, B's predecessor): "evaluate the current state of the juniper project with respect to the following handoff prompt:
  juniper-ml/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md determine if
  any outstanding work remains update the handoff document accordingly begin performing the outstanding tasks validation by consensus should
  be performed where appropriate merge approval granted", then "continue as planned". Its merge approval was "ONLY this session's four PRs
  (2b, 2a, 2c, addendum), plus the closing PR. No deploys, images, PyPI or GitHub Releases"; per-session, so it did not survive.
  **Restored rules (F6): "Never merge other sessions' PRs"; "The juniper-recurrence release is owner-gated".**
- **Short names**: `S` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle/reports/2026-09-23_y2-wave2-consensus/session-state/`
  (untracked; pass as the freeze tool's `--scratch`). `…queue-drained.md` = `HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md` (#2058).
- **The four PRs** (prepared, unopened): **2b** deploy — bind-mount the LMU snapshot root with a preflight on every bring-up path; **2a**
  recurrence — track `recurrence-snapshots/.gitkeep` and correct #172's unreleased claims; **2c** juniper-ml — both launchers declare the root,
  shared tripwire `tests/snapshot_root_tripwire.py`, two mutation harnesses; **addendum** — status addendum v13 spliced into the 09-08 handoff,
  with probe/splice/extract tools. Bodies/titles frozen in `S/main/`; **`S/main/PLAN.md` v5 is the open-and-merge procedure — read all of it.**
- **Round 15** frozen at `S/r15/` (140 files; `SHA256SUMS` digest `66742624…4a3171` [VERIFIED 2026-10-03: sha256sum]); reports
  `S/r15_reports/R15{A,B,C,D}.md` are authoritative over any summary (F20); tally 3 MAJOR, 10 MINOR, ~20 NIT. Evidence at freeze: launcher
  suites 193 OK, harness 103/103, 33/37 fired sweeps caught without the tripwire, deploy preflight 76, deploy suite 360 passed/42 skipped,
  deploy harness 111/111, re-probe 46/46 at pins (now 45/46: local tag `v0.16.0` contains `68c3cd7c`, F16).
- **Bases at freeze**: ml `f9c81d80`, recurrence `ca9609f0`, deploy `d589dd95`. ml#2061 merged three-way into 2c (`--merged 2c_ml.diff`).
  recurrence#183 and #184 OPEN [VERIFIED 2026-10-03].
- **Worktrees** (uncommitted state is the only copy — KEEP): `idempotent-jumping-sparkle` (branch
  `docs/canopy-selection-0908-handoff-status-2026-09-22` at `5ea8e273`; 2c + addendum modified; tripwire and four `2026-09-22_*` tools
  intent-to-add; `tests/process_cleanup.py` untracked = main's copy, in no upload set; `2026-09-23_*` tools and `S` untracked);
  `worktrees/juniper-recurrence--feature--y2-recurrence-snapshot-root--20260922-1512--749e7a35` (2a's four files);
  `worktrees/juniper-deploy--feature--y2-recurrence-snapshot-bind-mount--20260922-1520--13ee87aa` (2b's eight files, plus
  `k8s/helm/juniper/values.yaml` which no longer equals deploy main and is not uploaded) [VERIFIED 2026-10-03: worktrees exist].
- **What moved** [CHANGED SINCE HANDOFF: recurrence and deploy moved again after the combined draft]: recurrence #186 (CHANGELOG — a 2a path),
  #187, #188 (dependabot, `juniper-recurrence/` requirement); deploy #230–#232 (CHANGELOG, `docker-compose.yml`, helm values) and #233–#238
  (egress tests/fixes, dependabot). Both 2a and 2b take the **delta route** (PLAN step 2); merge main's changes three-way into their CHANGELOGs
  and 2b's `docker-compose.yml`. **Deploy's new compose and helm tests must run in 2b's delta route** (F18). Re-check 2c/addendum paths with
  `git log f9c81d80..origin/main -- <paths>`. canopy moved past the freeze: #679–#685 plus dependabot #686–#691; cascor #688–#690; re-run the
  probe with `--fetch --at-main` and bullet every merge that changes a row (R15C M1's own fix names only juniper-ml#2058; the #674/#675 bullets
  come from B's predecessor, F17). **Point the addendum at THIS file by explicit filename** (R15C's listing step greps `canopy-selection`, which
  this name lacks). X11 is no longer an open ruling (canopy#680).
- **The CHANGELOG conflicts differ** (F19): #186 lands 3 lines clear of 2a's edit (should pass `--merged`, not executed); 2b's `### Fixed` is
  adjacent to #231/#232's, so R15D MINOR 1 (`--merged` compares a CHANGELOG as a multiset of lines) is on 2b's path.
- **B1 fix pass**: apply the round-15 list in B's predecessor (`HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md` § "The round-15 fix list";
  also frozen on main at `reports/2026-09-24_canopy-combined-handoff-consensus/r1/predecessors/`) — R15A m1 (tripwire forms, then state them
  exhaustively), m2 (fixtures), n1–n6; R15B m1–m4, n1–n6, harness rows for mutation rows X10, X18–X21 and the gated starts; R15C M1 (re-point,
  see above), M2, m1 (probe 2.5.0), m2, NITs; R15D MAJOR 1 (as reframed by O7), MINOR 1–2, NIT 1–7, PLAN `--merged` doc. Sub-fixes the verbatim
  list omits (F20): R15A `:59` "Also missed"; R15A m2 "writes or deletes"; R15B n3 "drop DOCKER_CONTEXT"; R15C `:130` `--fetch`; R15D NIT 3 (a
  deleted version heading). Re-point `S/main/lane_common_r15.md:8` from the old tmpfs `…/798c2868-…/scratchpad/r15` (still exists) to `S`.
  Known limitations: `S/main/handoff_v4.md:50-54` (`JUNIPER_ROOT`, `JUNIPER_E2E_PROJECT_DIR`). Update `handoff_v4` and addendum rows for 45/46.
- **B2 round 16**: `python3 util/ad-hoc/2026-09-23_freeze_round.py --scratch S --round 16 --prior r15 --addendum addendum_v14.md --logs
  S/fix16/logs16 --reports S/r15_reports` (spell out `S`; `addendum_v14.md` goes in `S/main/`; create the logs dir), plus `--merged
  2a_recurrence.diff --merged 2b_deploy.diff` once those worktrees carry main's changes; widen the `TOOLS` glob for `2026-09-2[4-9]_*` tools.
  Four lanes from `S/main/lane_common_r15.md` + `lane_R15{A..D}.md`; archive each at once with
  `util/ad-hoc/2026-09-22_extract_lane_reports.py --require-heading "## Housekeeping" S/r16_reports NAME=<transcript>`. Tell R16B that
  `.env.secrets.enc` is tracked in juniper-deploy: delete it only from a lane's scratch rebuild, never from the deploy primary or the 2b worktree
  (F15). Touch no uploaded file while a round runs. Repeat until no MAJOR and no unresolved MINOR; record `APPROVED_FREEZE` in PLAN.md.
- **B3 open/merge** after O7: open 2b→2a→2c→addendum (each cites later numbers); merge 2c→2a→2b→addendum; after 2a, `git pull --ff-only` the
  shared `/home/pcalnon/Development/python/Juniper/juniper-recurrence` checkout (precondition: clean and on `main`). `util/safe_merge.py --pr N
  --repo <name> --execute --no-auto-fallback`, extracted with `wait_for_checks.py`, `push_signed_commit.py`, `open_signed_pr.py` from
  `origin/main` (`git show origin/main:util/<name>`); read MERGED back. Default if O7 unanswered: fix-forward, `gh pr view` all four before each
  merge, blob-compare after any out-of-order merge (F7). **Never pre-push a planned PR branch name** — the opener refuses an existing branch
  (F8).
- **The stake (X1/F7)**: if 2b lands before 2a is merged and pulled, every deploy-main bring-up refuses (recurrence in profiles full/demo/dev/
  test; long-form mount with `create_host_path: false`, so Docker refuses a missing source on every path; `JUNIPER_SNAPSHOT_ROOT_OK=1` bypasses
  only the preflight). Also 2b's comment and CHANGELOG and 2a's CHANGELOG are false until 2c merges, and merge-time checks never run. Real
  options: exclude the four PRs from the sweeper, or fix forward (owner may pre-create `juniper-recurrence/recurrence-snapshots/` in the shared
  checkout); R15D's alternative wording is "let 2b's preflight warn rather than refuse until 2a is released" (a code change → delta route).
- **B4 closing**: closing handoff from `S/main/handoff_v4.md` (fill `PR_2C`/`PR_2A`/`PR_2B`/`PR_ADD`, `GIT_STATUS_BLOCK`,
  `HANDOFF_VALIDATION_BLOCK`; point at the newest selection-arc handoff); archive `reports/2026-09-23_y2-wave2-consensus/` rounds 1–16+ with a
  README per §7 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`; a closing PR with the `util/ad-hoc/2026-09-23_*` tools; cleanup only on merge signals.
- **B5**: the final summary names every changed file and repeats the reminder to rotate `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` (O10).
- **B6 wave 3 and X10 (canopy, unstarted; claim lapsed)**: give each of five snapshot sites in canopy `src/main.py` a recurrence branch — locate by
  symbol: `_backend_snapshot_inventory`, `_backend_snapshot_detail` (both `!= "service"`), `create_snapshot`, the lookup and the load in
  `restore_snapshot`; `_require_service_adapter` keeps its 501 (replay, replay/control, resume, retrain, three network-editing routes). Add
  save/list/get/restore to `src/backend/recurrence_service_adapter.py` over raw `httpx` under the names in §8 of `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` (`save_snapshot`, `load_snapshot`,
  `list_snapshots`); service side is juniper-recurrence#172; list through the service (canopy's local listing admits only `.h5`/`.hdf5`,
  recurrence writes `.npz`). **Gating is contested** (O8). X10: `RecurrenceBackend.initialize()` returns `True` without probing;
  `selection_is_live` (`src/model_registry.py`) reads config only.
- **Lane B traps**: never print env values; never read or decrypt a secret; `make` only with `-o prepare-secrets` and a docker shim; tool
  claims must equal the implementation (state exhaustive recognized forms, everything else out of scope); verify against a pulled image, never
  a local build (`make build` tags unreleased source as `0.5.0`); mutation scripts edit in place — snapshot first, scan the snapshot for the
  mutants' strings, never upload while one runs.

### Lane C — selection arc

[UNVERIFIED unless tagged — from predecessor C and the combined draft; the combined draft was not validated]

- Done: W5 cleanup (26 worktrees, 20 branches in canopy/cascor/data; harvest 174 MB in 25 dirs at
  `/home/pcalnon/Development/python/Juniper/backups/worktree-harvest-2026-09-24-canopy-selection-arc/` [VERIFIED 2026-10-03: du 174M]); item 19
  closed; X8 CHANGELOG in data `[Unreleased]` via #438; Y7's dropdown half grounded in §4.3 of the selection design note.
- **C1 (OG, owner runs)**: remove juniper-ml worktrees `jazzy-soaring-minsky`, `bright-crunching-alpaca`, `tender-wibbling-flask` (verified
  superseded/on-main by C), and `enumerated-marinating-puddle` (#2087 merged; 0 untracked files at 09-24 — still run
  `util/ad-hoc/2026-09-24_same_repo_worktree_content_probe.py` first) [VERIFIED 2026-10-03: all four exist]. Re-run
  `util/ad-hoc/2026-09-02_worktree_inuse_probe.py`; `--force` needed (dirty with untracked copies of merged content; also deletes caches and
  jazzy's three near-empty `logs/*.log`). Commands in § Verification. A9's juniper-ml worktrees join after A6.
- **C2 (OG)** Y7: pick one of the four options in the §4.3 note of `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (the fourth is accepting the gap).
- **C3 (OG) `[ALSO P4]`** X8's release: next juniper-data release after 0.16.0 carries #437/#438. (Run `35977786108` for 0.16.0 failed its
  consumer-notify job after PyPI succeeded.)
- **C4** O9/U-6, from A2(b).
- **C5** [CHANGED SINCE HANDOFF: 2026-09-29T00:00Z has passed; the Y2 waves 2/3 and X10 claims lapsed; no PR or pushed branch carries them.]
- **C6** [CHANGED SINCE HANDOFF: the primaries were fast-forwarded by the owner's account outside any session — canopy/cascor at 09-24
  19:39Z, again at 09-25 04:20–04:23Z (data too), and at 10-02 23:31–23:32Z; canopy primary now `72b1a5f6` (one behind main `58b467ca`), cascor `b2921712` and
  data `1c67f8d6` equal main. The trio's processes (started 09-22) still run older code, so the trio is mixed-version.] Remaining: decide who
  may pull under the freeze and whether the trio is still wanted (O13). A clean holder scan is not proof (editable-finder imports leave no
  `/proc` trace).
- **C7** A-N9: no action (no `ModelSpec` accepts `structured`; `arc_agi` stays unseeded).
- Trap: an ignored path can still be committed (the A-N2 report's 92 `**/logs/` files were force-added) — compare with main before calling
  anything "ignored".

### Owner batch (one message) — O1–O17

O1 merge approval for this session (none carried). O2 A6 provenance refs (urgent before any cleanup). O3 ledger item 17. O4 the account's
later actions (A6). O5 the ratings (A6). O6 ledger items 3, 4, 9 (M-DATASET), 10. O7 Y2: continue after the lapsed claim? who runs it? sweeper
vs merge order (exclude the four PRs / fix-forward / preflight-warns). O8 wave 3 gating: capability test (§8 item 3 and §11.4 step 3 of `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`) vs third
branch (item 4 of `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` § B); record the choice in that persistence design. O9 Y7 (C2). O10 token rotation: `HF_TOKEN` and `JUNIPER_ML_PYPI` /
`JUNIPER_ML_TEST_PYPI` (leaked into agent transcripts; status unknown). O11 retain or retire the ad-hoc signed-commit driver copies (promoted in
juniper-ml#2036; `…queue-drained.md:36`). O12 make recurrence's `Settings` case-sensitive (`S/main/handoff_v4.md:54`). O13 who may stop the
trio and who pulls primaries under the freeze. O14 X8 release (C3). O15 C1 removals. O16 whether this consolidated handoff gets its own
consensus round (the 09-24 request "the combined handoff should be validated by consensus" was never completed) and whether to open a PR
archiving it with predecessors A and B. O17 (added 2026-10-08, ledger Phase 11's Matrix effect and counts) asks the §6.3 question in two
limbs. First: does a CHANGELOG or design-plan promise count as "documented"? That decides F-CANOPY-065, and may also reach F-CANOPY-057,
-018 and -012. Second: if it does, does that extend to a CHANGELOG's description of an internal mechanism? That decides F-CANOPY-068.
Moving 065 and 068 alone, the counts are 7/16, 6/17 or 5/18 open P1/P2. Phase 11's item 26 checks every open finding against canopy's
manual without waiting for the ruling, then sweeps the rest once the owner rules.

---

## Verification commands

```bash
# From a fresh juniper-ml worktree on main (Lane A / C)
gh api repos/pcalnon/juniper-ml/commits/main --jq .sha                     # afb02801… on 2026-10-03
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -8                     # 70 / 48 / 1 / 2 / 19; P0 1; P1 6; P2 12
grep -cE '^\| [A-Z0-9.-]+ .*\| BLOCKED' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md   # 20
gh pr list --repo pcalnon/juniper-canopy --state open --json number,title  # only dependabot on 2026-10-03
gh pr view 685 --repo pcalnon/juniper-canopy --json state,mergeCommit       # MERGED dc5ea02e
gh pr view 690 --repo pcalnon/juniper-cascor --json state,mergeCommit       # MERGED 0fbb447a
gh release list --repo pcalnon/juniper-data --limit 2                       # v0.16.0 Latest
python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py | tail -1           # 0 failed
ss -ltnp | grep -E ':(8101|8202|8051) '                                     # the trio; do not touch
df -i /tmp | tail -1
wc -m /home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md   # 24,929 on 2026-10-03
gh api repos/pcalnon/juniper-recurrence/compare/ca9609f0...main --jq '[.files[].filename]'
gh api repos/pcalnon/juniper-deploy/compare/d589dd95...main --jq '[.files[].filename]'
# C1, owner-run only:
python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jazzy-soaring-minsky /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bright-crunching-alpaca /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/tender-wibbling-flask /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/enumerated-marinating-puddle
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jazzy-soaring-minsky
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bright-crunching-alpaca
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/tender-wibbling-flask
python3 util/ad-hoc/2026-09-24_same_repo_worktree_content_probe.py /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/enumerated-marinating-puddle   # must show nothing off main first
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree remove --force /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/enumerated-marinating-puddle
git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree prune
git -C /home/pcalnon/Development/python/Juniper/juniper-ml branch -D worktree-jazzy-soaring-minsky worktree-bright-crunching-alpaca worktree-tender-wibbling-flask worktree-enumerated-marinating-puddle
```

```bash
# Lane B only, in a session started in /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle (all from the worktree root)
git status --short | head -40
(cd reports/2026-09-23_y2-wave2-consensus/session-state/r15 && sha256sum -c --quiet SHA256SUMS && sha256sum SHA256SUMS)   # 66742624…4a3171
env -u JUNIPER_E2E_RECURRENCE_SNAPSHOT_DIR -u JUNIPER_RECURRENCE_SNAPSHOTS_DIR python3 -m unittest tests.test_isolated_stack_script tests.test_experiment_stack_script   # 193 OK at freeze
python3 util/ad-hoc/2026-09-23_placeholder_census.py                          # 2c 6/4, 2a 4/0, 2b 0/0, addendum 3 (self-test)
python3 util/ad-hoc/2026-09-23_check_open_pinned_pr.py reports/2026-09-23_y2-wave2-consensus/session-state/r15   # bad=[]
du -sh /home/pcalnon/Development/python/Juniper/backups/worktree-harvest-2026-09-24-canopy-selection-arc   # 174M
# In Lane B's tree the E2E triage prints 63/42/1/2/18 and two Lane A tools are missing — use a main worktree for Lane A checks.
```

---

## Dispositioned / closed items

| item | source | disposition | evidence |
|---|---|---|---|
| F-CANOPY-054 fix | phase7 item 1 | DONE (canopy#670 `48074653`) | phase8 handoff; ledger Phase 8 |
| Idle cuts PR (rebuild, open, merge) | phase8 item 1; phase9 items 1–2 | DONE out of order: canopy#676 `e9053227` (09-24 01:38Z); round-3 fixes as canopy#684 `f2147403`; #676 body refreshed | [VERIFIED 2026-10-03: gh pr list] |
| Phase 7/8/9 ledger PRs | phase7/8/9 | MERGED #2030, #2054, #2083 | [VERIFIED 2026-10-03: gh] |
| "Land Phase 9 before #676" ordering | phase9 item 1 | MOOT (#676 merged first) | phase9's superseded-in-part note |
| F-055 first fix as a PR | phase8 item 2 | REFUTED in review; replaced by A4/A5 | ledger Phase 9 |
| Confirm F-058 live with an apply census | phase9 item 3 | SUPERSEDED: must count evictions; census refuted → A4 | ledger Phase 9 item 0 |
| "All three triggers" | phase9 item 4 | CORRECTED to four (+ second-Input change) | phase9 note |
| canopy#684 main-verify check | A | DONE: Post-Merge Main Verification success | R1-E (F22) |
| Get #685's number from bc31e993 | A item 2(a); combined A2 | CLOSED: #685 merged `dc5ea02e`, fixes F-061/062 | [VERIFIED 2026-10-03] |
| "Nothing was loaded" waits on cascor#690 | combined A2(a) | PRECONDITION FIRED: #690 merged `0fbb447a` (head moved `78e99414`→`81154187`) | [VERIFIED 2026-10-03] |
| Status bar one-browser measurement | phase7 item 4 | DONE → F-CANOPY-055 filed | phase8 |
| Profile/cheap cuts | phase7 items 2–3 | cuts DONE (#676); profile hunt carried as A7 item 1 | ledger |
| Apply F1–F22 to the combined draft; round 2; fill VALIDATION_RECORD_PENDING | combined Remaining 1–4 | SUPERSEDED: F1–F22 folded into this file; the draft is superseded; a fresh consensus round is O16 | this file |
| Combined handoff PR (the prompts/ draft, and archiving A and B) | combined Remaining 5 | OPEN → O16 (the #2096 merge, 09-26, carried only the round-1 handoff, `r1/` and the reachability tool; it put frozen copies of A, B and the draft as `DRAFT_r1.md` on main) | [VERIFIED 2026-10-03: gh pr view 2096 files] |
| F4 "C6 stale" / "freeze in force" | combined F4 | UPDATED: see C6 [CHANGED SINCE HANDOFF] | primary reflog files read |
| F10 canopy#685 exists, not armed | combined F10 | CLOSED: merged | [VERIFIED 2026-10-03] |
| X11, F1, F2, X8 rulings | selection chain | SHIPPED 09-24 (canopy#680/#681/#682, cascor#685/#687, data#437) | four-rulings-shipped handoff |
| Item 19 (data release with #421) | selection chain | CLOSED: 0.16.0 on PyPI | [VERIFIED 2026-10-03: PyPI JSON] |
| `Juniper/CLAUDE.md` false 0.16.0/X8 clause | four-rulings-shipped | DONE: guide now says 0.16.0 does NOT carry X8 | current ecosystem guide text |
| W5 selection cleanup | four-rulings-shipped | DONE (26 worktrees, 20 branches) | predecessor C |
| Register O2–O5 with the E2E arc | queue-drained item 4 | ACCEPTED by Lane A → A2(b) | predecessor C |
| canopy#368 mirror clause | queue-drained | status comment posted; issue still OPEN (not this path's to close) | [VERIFIED 2026-10-03: OPEN] |
| `/tmp` inode exhaustion | phase8/9 | RESOLVED for now (39%) | [VERIFIED 2026-10-03: df -i] |
| Legs `:8055`/`:8056` | phase8 | DOWN | [VERIFIED 2026-10-03: no listener] |
| canopy worktree `…f054-replay-block-clientside…` cleanup | phase8/9 | HELD by A6 (branch holds `723ee812`) | A6 table |
| R15D MAJOR 1 "use drafts" | B | OVERTAKEN: drafts do not hold (readied+armed 4–8 s apart); see O7 | memory `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md` |
| R15C M1 target `…queue-drained.md` | B | OVERTAKEN: point the addendum at this file | Lane B |
| "A pushed branch keeps the claim" (X2) | combined | WITHDRAWN (F8): never pre-push planned PR names; claim lapsed anyway | Lane B |
| MEMORY "ACTIVE lines" | A, combined A8 | CORRECTED (F22): no such lines exist | R1-E |

---

## Git state

- **This session**: juniper-ml worktree `snappy-strolling-waterfall`, branch `docs/handoff-consolidation-2026-10-03`. **Created**: this file.
  **Changed**: the four sources each received a SUPERSEDED banner under the H1 —
  `HANDOFF_2026-09-22_canopy-e2e-phase7-f053-and-f048-fixed-f054-open.md`, `HANDOFF_2026-09-23_canopy-e2e-phase8-f054-fixed-f055-filed-cuts-pending.md`,
  `HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`, `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md`.
  Nothing committed.
- **juniper-ml** (probed 2026-10-03): `main` `afb02801`. Origin branch `docs/canopy-e2e-handoff-2026-09-24` at `dd4413e5`, no PR (predecessor A).
  Origin `docs/canopy-e2e-phase9` and `docs/canopy-combined-handoff-2026-09-24` deleted (merged #2083, #2096). Worktrees present:
  `bubbly-meandering-pie` (`6c23fdde`; untracked combined draft), `graceful-sprouting-panda` (`docs/canopy-e2e-phase9`, `808b74df`),
  `squishy-dancing-moth` (`b54e3b3f`), `partitioned-twirling-stream` (`bb0efa2b`), `lively-humming-pixel` (`c4a67481`),
  `idempotent-jumping-sparkle` (`5ea8e273`, Lane B's uncommitted state), `jazzy-soaring-minsky`, `bright-crunching-alpaca`,
  `tender-wibbling-flask`, `enumerated-marinating-puddle` (`c32e5f2a`).
- **juniper-canopy**: `main` `58b467ca` (10-02 23:46Z); open PRs are dependabot only (#689, #692, #693). Local branches in A6's table exist;
  worktrees `…f055-status-bar-running-guard…` (KEEP), `…idle-cuts-round3-wording…`, `…perf--idle-dispatch-cuts-v2…`, `…perf--idle-dispatch-cuts…`,
  `…f054-replay-block-clientside…`, `…control--main…`, `…secret-leaks-683-validation…` (P3's; #685 merged), `…blank-key-678-followups…` (#683 merged; P3's).
- **juniper-cascor** `main` `b2921712`; **juniper-data** `1c67f8d6`; **juniper-recurrence** `be081fae`; **juniper-deploy** `9403dbf5`. No Y2 branch on
  recurrence or deploy origin; Y2 worktrees present with uncommitted 2a/2b.
- **Housekeeping**: one local read of a primary's reflog displayed an author line containing an email address in this session's tool output;
  nothing was copied into any file.
