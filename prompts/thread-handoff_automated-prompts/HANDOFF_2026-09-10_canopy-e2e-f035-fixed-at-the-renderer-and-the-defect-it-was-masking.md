# HANDOFF — canopy E2E arc: F-CANOPY-035 read out of the renderer, FIXED and merged, and the defect that was hiding behind it

**Date**: 2026-09-10 · **Session**: <https://claude.ai/code/session_01SDwaTPuGgzypx9f1tE1ahB>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/glittery-wondering-cosmos`
**PRs**: juniper-canopy **#613 MERGED** (`b792256`) · juniper-ml **#1878 MERGED** (`c732e631`) · juniper-canopy **#614** (the strand repair round-1 validation forced)
**Validated**: rounds 1 and 2 run; the document **FAILED both**. Round 2 overturned the DISPOSITION —
see §9. Read §9 before trusting anything in §1–§6.

**Documents REFERENCED** (the ecosystem convention in `/home/pcalnon/Development/python/Juniper/AGENTS.md`
§ Cross-Project Conventions requires the filename on every citation, because more than one is cited):

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` — the finding ledger, the arc's
  document of record; this session added **Phase 6 — 2026-09-10** at its end
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md` — the row matrix
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_canopy-e2e-arc-f035-supersession-measured-and-the-relay-drop.md`
  — the handoff this session inherited; its §3 item 1 is now closed
- `util/ad-hoc/README.md` — the instrument inventory, with a new section for this session's five tools

**Documents CHANGED by this session**: `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`, `util/ad-hoc/README.md`, and
this file. **Added**: five instruments under `util/ad-hoc/` (all `2026-09-10_*`) and 14 evidence artifacts
under `reports/e2e-canopy-2026-09-02/transcripts/`. **In juniper-canopy**: `src/canopy_constants.py`,
`src/frontend/dashboard_manager.py`, `src/tests/unit/frontend/test_poll_gating.py`,
`src/tests/unit/frontend/test_stage2_global_lane.py` (PR #613, merged as `b792256`).

---

## 0. PREFLIGHT

1. **`uptime -s` before trusting any leg.** The host has not rebooted since **2026-09-07 23:12**, so every
   leg from Phase 5 was still up when this session ran. `/tmp` is tmpfs; a reboot destroys `/tmp/juniper-e2e`
   and the fixture lives in cascor's process.
2. **There are now TWO canopy verify legs and they are different builds.** `:8052` serves `eb05021d`
   (**before** the fix) and `:8053` serves `eab7cf43` (**after**). Neither is the trio's `:8051`, whose
   browser instruments still default to it — **`JUNIPER_E2E_CANOPY_URL` must be exported for every probe**,
   the failure this arc has paid for three times now.
3. **canopy `main` already carries the fix** (`b792256`), plus the strand repair once **#614** lands. The
   `:8053` leg was launched from the fix worktree
   `worktrees/juniper-canopy--fix--f035-metrics-store-running-guard--20260910-0459--8cfb29ac`. Its HEAD is
   **`6f04da6e`**, not `eab7cf43` (the commit was amended after the leg launched), and its files were
   rewritten **9 minutes after the process started** — so the leg is executing `eab7cf43`'s bytes while the
   tree on disk is byte-identical to `main`. The `eab7cf43 → main` delta is 22 lines across 2 files and
   **every one is a comment**, so the leg is functionally main's fix; that is proven by content, not by the
   stamp. **Do not delete that worktree while `:8053` runs.**
4. **The fixture is untouched.** uuid `1cd15120…`, 2/52/2/1538, `COMPLETED`, epoch 56, **66 metrics rows**
   (`output` 54 / `candidate` 12). Snapshots `snapshot_20260905T103912Z` (40), `…20260908T123427Z` (48),
   `…20260909T002658Z` (52). No growth run was done this session.

---

## 1. Goal statement

Continue the juniper-canopy E2E validation arc. Ledger
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, matrix
`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.

State: **63 findings — 42 fixed / 1 accepted / 2 withdrawn / 18 open (0 P0, 3 P1, 15 P2)**; it was
62 / 41 / 1 / 2 / 18 with 4 open P1. Matrix **298 rows, 296 verdicted** (the known slash-enumeration
artifact — both `M-PARAMETERS-01/02/03` rows carry PASS in the matrix itself), **21 BLOCKED**. Count
BLOCKED with a pattern that has **no trailing pipe**, or `C2.10-03`'s `BLOCKED (F-CANOPY-025)` is missed
and you get 20.

**What this session settled.** F-CANOPY-035's mechanism, read out of the shipped dash-renderer bundle
(`dash_renderer.dev.js`, unminified in `JuniperCanopy1`, dash 4.2.0) rather than inferred from behaviour:
`:2698` discards a response whose callback has left `watched`; `:3027` evicts a `watched` entry the instant
the same identity appears in `requested` (`concat(watched, requested)` grouped by `getUniqueIdentifier`,
each group sliced `[0:-1]`, `requested` concatenated LAST). `getUniqueIdentifier` hashes **one callback's
own** inputs/outputs/state, so the other nine fast-lane callbacks are different identities and **cannot**
evict it — which separates self-eviction from fast-lane promotion starvation **at the source**, and is what
the inherited handoff's §3 item 1 asked for.

**The displacing event is the TICK creating a `requested` entry**, not the next HTTP request. Every prior
measurement on this finding — and this session's first one — used the HTTP boundary, which is why the
ledger carried four numbers read as evidence *against* the mechanism. Three were boundary errors; the
fourth (`everSeen: {watched: 1}` — two concurrent entries never observed) is what the mechanism
**predicts**, because the eviction is synchronous with the insertion.

**What closed it** — corrected after validation. The **source reading** (`:2698`, `:3027`, and
`getUniqueIdentifier`'s contents, all independently re-verified in round 1) and the **clean room**, an
~80-line app with no canopy at all that reproduces the defect and shows `running=` fixing it. The
dose-response is a supporting correlate and **not** the load-bearing evidence: its verdict was
structurally forced, and neither of its two fills is attributable to the long period (§9, C2).

**The fix (canopy#613, merged).** `update_metrics_store` gets its own `dcc.Interval` and
`running=[(Output(<that interval>,"disabled"), True, False)]`, which stops this callback re-requesting over
itself **on its own clock** — not, as first written, "structurally impossible" full stop (§9, C1 and the
two unmeasured holes there). Live: the store went from **0 across a 90 s window and 52 pre-control
full-payload responses** to filling **7.3 s after observer install**, with the fast lane still ticking at
its delivered ~0.51 Hz (not the nominal 1 Hz — §9, C5).

**What this session did NOT get, and got WRONG.** M-CANDIDATES-07 is still **FAIL**, and the reason is
not what this session filed. The candidate loss figure rendered in 2 of 6 loads and that was filed as
**F-CANOPY-052**, "the defect the empty store was masking". Round 2 established it is **the same defect**:
`update_loss_plot` took the training-state store as an Input, that store is rewritten every second with a
value that always differs, and the renderer evicts the in-flight invocation exactly as it did for the
metrics store. Re-disposed **P2 → P1**, fixed in **canopy#618**. Measured 1/3 with the re-trigger running
vs **3/3 with it stopped** (§9, R1).

---

## 2. State at handoff

| | |
|---|---|
| Findings ledger | **63 — 42 fixed / 1 accepted / 2 withdrawn / 18 open (0 P0, 4 P1, 14 P2)** — F-CANOPY-052 re-disposed P2 → P1 on 2026-09-11 |
| Matrix rows | 298, 296 verdicted / **21 BLOCKED**; M-CANDIDATES-07 FAIL — **never yet driven against canopy#618**, which is the fix for its cause |
| cascor fixture | uuid `1cd15120…`, 2/52/2/1538, `COMPLETED`, 66 metrics rows (`output` 54 / `candidate` 12) |
| Services | `:8051` canopy (trio, `git_sha null`, v0.4.0) · `:8052` canopy `eb05021d` v0.6.0 — **the BEFORE leg** · `:8053` canopy `eab7cf43` v0.6.0 — **the AFTER leg** · `:8101` data 0.13.0 · `:8202` cascor `d39d537` (dirty; content-proven identical to merged `5eb6f144`) · `:8050`/`:8201`/`:8211` Docker deploy stack — do not touch |
| PRs | juniper-canopy **#613 MERGED** `b792256` · juniper-ml **#1878 MERGED** `c732e631` · juniper-canopy **#614** (strand repair, round 1) · juniper-canopy **#618** (the F-052 trigger demotion, round 2) |
| Product code changed | juniper-canopy only — #613, #614 (the strand defect #613 introduced), #618 (the consumer #613 left evicted). No cascor, no data. |

---

## 3. What is still owed (in order) — RE-ORDERED by round 2

**Read §9 first.** The previous ordering put the most expensive item first and it was misdirected; the
two cheapest and highest-value items were buried behind it.

1. **Re-drive M-CANDIDATES-07 against a leg serving canopy#618.** The row has never been driven against
   the fix for its actual cause. `:8053` predates both #614 and #618, so every F-052 observation in this
   record describes a build with the defect still in it. Launch a new leg
   (`util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <worktree>/src 8054`) and re-run
   `util/ad-hoc/2026-09-11_f052_trigger_eviction_test.py --runs 3` — with #618 in, the CONTROL arm should
   now render 3/3 on its own.
2. **M-METRICS-11..16/-18 re-drive.** Cheap, unblocked, and it converts **seven** matrix rows that were
   untestable before #613. All three replay callbacks compute
   `max_index = len(metrics_data) - 1 if metrics_data else 0` from the store #613 repaired
   (`metrics_panel.py:1013/1060/1088`). `util/ad-hoc/2026-09-08_replay_block_redrive.py` exists and has
   **not** been run against a fixed leg. This was item 2 and should have been item 1.
3. **The sibling sweep is DONE — decide what to do about the three it found.** `update_status_display`
   (`:283`), `update_epoch_progress` (`:303`) and `update_pool_info` (`:322`) each take that same 1 Hz
   store as their **only** Input, so all three are structurally exposed to the identical eviction. They
   are **not** currently broken: they build a badge, a progress figure and a text block, so their round
   trip stays under the re-request period, while `update_loss_plot` built a Plotly figure and lost. That
   is a margin nobody chose and nobody measures — any change that slows one of them flips it to
   intermittent-blank with no error anywhere. Measure the three round trips, then either demote the
   Inputs (as canopy#618 did) or fix the WRITER: `fetch_training_state` returns unconditionally for this
   store while identity-suppressing its OTHER output in the same function. Recorded in Phase 6 as a
   latent risk, deliberately **not** filed as a finding — nothing observed is broken.
4. **F-CASCOR-004 / F-CANOPY-049** — unchanged and untouched. cascor: log in `_send_json`, `close()` in
   `broadcast`'s drop path. canopy: **not** a new liveness rule — `StreamHealth` already degrades after
   60 s and `cascor_service_adapter.py` re-arms it every 30 s off cascor's transport pings.
   `util/ad-hoc/2026-09-08_cascor_ws_drop_probe.py`'s transport-counter rule has still **never** run.
5. **The 27–37 s full-history regression** (§9, R5) — quantify it and decide whether
   `FULL_HISTORY_POLL_TICK_MODULUS` moves. Needs a full-mode round-trip measurement nobody has taken.
6. **The fix's ~4–5 s re-enable overhead** — measured, unexplained, and now less urgent than it looked:
   it is a cadence cost, while item 5 is a 5–7× staleness regression on the same surface.
7. **Re-baseline after #614 and #618 merge.** Every `:8053` number in this record then describes a
   superseded build. Either relaunch the AFTER leg or mark them.
8. **Phase 5's items 3, 5, 6, 7 and 9** are untouched.

## 4. Instruments added (all `util/ad-hoc/2026-09-10_*`)

| instrument | answers |
|---|---|
| `2026-09-10_f035_unopposed_response_test.py` | per-response bracket: did THIS response land, and could anything evict it. **Read the docstring** — its first verdict used the wrong boundary and is marked superseded |
| `2026-09-10_f035_trigger_period_sweep.py` | the dose-response that closed the mechanism |
| `2026-09-10_f035_running_guard_cleanroom.py` | reproduce with no canopy; test `running=` as the fix |
| `2026-09-10_f035_fix_wiring_check.py` | the fix's six wiring properties, off the BUILT app |
| `2026-09-10_f035_downstream_consumer_probe.py` | F-CANOPY-052: data or render, and does the consumer fire |

---

## 5. Verify the starting state

**These numbers are the state AFTER juniper-ml#1878 merges.** Until then `main` reads 62 / 41 / 1 / 2 / 18
with 4 open P1 — if you see that, the record has not landed yet, not been reverted.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # or a fresh worktree
uptime -s                                                 # after 2026-09-07 23:12 → the legs below are gone
gh api repos/pcalnon/juniper-canopy/pulls/613 --jq '{merged,merge_commit_sha}'   # true, b792256…
gh api repos/pcalnon/juniper-ml/pulls/1878   --jq '{state,merged}'
python3 util/ad-hoc/e2e_finding_triage.py --note notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | tail -8
python3 util/ad-hoc/e2e_row_coverage.py | head -4        # "remaining: 2" is the KNOWN artifact
grep -cE '^\| [A-Z0-9.-]+ .*\| BLOCKED' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md   # 21 — no trailing pipe
ss -ltn | grep -E ':(8051|8052|8053|8101|8202)\b'
curl -s http://127.0.0.1:8053/v1/health | grep -o '"git_sha":"[0-9a-f]*"'   # eab7cf43… — the FIXED leg
curl -s http://127.0.0.1:8052/v1/health | grep -o '"git_sha":"[0-9a-f]*"'   # eb05021d… — the BEFORE leg
curl -s http://127.0.0.1:8202/v1/network                                     # uuid 1cd15120…, hidden_units 52
grep 'WS emission summary' /tmp/juniper-e2e/logs/juniper-cascor.log | tail -1   # N active connections, N > 0
```

---

## 6. Traps (new; Phase 5's still apply)

1. **The renderer's eviction boundary is neither the HTTP request NOR the tick timestamp — it is the
   contents of `requested`/`watched` at the reducer pass that resolves the call.** The HTTP boundary is
   wrong at the head (a `requested` entry from an earlier tick still evicts) and the tick boundary is wrong
   at the tail (the check happens at APPLY time, measured 0.7–7.0 s after the response arrives). **Both
   boundaries returned `SUPERSESSION-INSUFFICIENT` in this session** — the corrected run did not overturn
   the first, and an earlier draft of this handoff implied it had (§9, C10). Neither verdict is sound; the
   mechanism rests on the source reading and the clean room, not on these runs.
2. **A `dcc.Interval` does not tick at its nominal rate under load.** 54 ticks per 90 s at a 1000 ms
   period, ~0.6 Hz. Read the gap from observed `n_intervals` transitions, never from the constant.
3. **~~Forcing a store change destroys the data you are testing.~~ FALSE — and this is the trap to learn
   from.** The claim was that `window_size: 40` drops the candidate rows because they "sit EARLY". Against
   the live fixture they are at **indices 53–64 of 66**, and a last-40 window keeps **all twelve**. The
   force did not remove them, and the `RENDER-STILL-DEAD` result it was invented to explain away stands
   **unexplained**. Keep `--no-force` for rate observations anyway (a forced arm is a different treatment),
   but the lesson is the general one: an inconvenient result got an invented mechanism instead of a
   measurement, and nobody checked the fixture until round-1 validation did.
4. **On a FIXED leg the store fills during page load**, so an observer installed after the tab settle reads
   it already full and records no transition. Use `--early-observer`.
5. **`e2e_finding_triage.py` reads only the LAST 170 characters** of a finding's bold header
   (`tail = body[-170:]`). A `FIXED` placed early in a long header is invisible and the finding still
   counts as open. Put the disposition at the END. (Also: the header must be a bold `**F-… — …**` line at
   column 0 — an `###` heading is not counted at all.)
6. **`running=` is not on the `callback_map` entry.** `dash/_callback.py:326` puts it on the callback SPEC,
   in `app._callback_list`, which is what is served as `_dash-dependencies`. A test that asserts it off
   `callback_map` silently reads `None` and passes for the wrong reason.
7. **Force-resetting a PR branch closes the PR.** Pushing the branch back to `main` to rewrite a commit
   made GitHub auto-close canopy#613 (zero commits at that instant); it reopened cleanly via
   `gh api -X PATCH …/pulls/613 -f state=open` once the new commit landed. Expect it; do not re-cut.
8. **`open_signed_pr.py --commit-body-file` takes a BODY, not a full message.** Passing the whole message
   duplicates the subject line, and juniper-canopy's `squash_merge_commit_message` is `COMMIT_MESSAGES`, so
   the duplicate would reach `main`.
10. **Verify the ENCLOSING FUNCTION, not just the line.** This is the error that shipped a live defect
   to `main`. `:1113` was checked and does dispatch `runningOff` on an error path — but it is inside
   `_handleWebsocketCallback`, a transport the callback never takes. The line did what was claimed; it was
   not on the code path. Three documents asserted the guarantee. Before citing a renderer line, establish
   which function contains it and which branch reaches it — §1's whole mechanism rests on three such reads.
11. **An inconvenient result is where invented mechanisms get in.** `RENDER-STILL-DEAD` was explained away
   with "the candidate rows sit EARLY so the force dropped them" — a claim nobody checked against the
   fixture, and false (they sit at indices 53–64 of 66). The general form: when a result contradicts the
   working hypothesis, the next step is a measurement, not a story.
12. **`state.callbacks` has a reader already, and it was RETIRED on a positive control.**
   `util/ad-hoc/2026-09-07_f035_callback_lifecycle_probe.py` reads `getState().callbacks` via
   `store.subscribe`. It returns the same `RETIRED-BEFORE-EXECUTION` verdict for a store that provably
   works, and it perturbs the page (`JSON.stringify` on every entry of every list, every notify). Do not
   rebuild it; do not trust it without a positive control that can come out negative.

13. **`2026-09-08_append_signed_commit.py` reports a network failure as "branch not found".** A TLS
   handshake timeout printed `REFUSED: branch … not found`. Re-check the ref before believing it.

---

## 7. Repository state at handoff

**juniper-ml** — **#1878 is MERGED** as `c732e631`, carrying **23 files** (3 modified, 20 added) in **two**
signed commits: `fcb3ad8b` (19 added + 3 modified) and `20e121d2` (this handoff). Both were created
through the GitHub API — a local commit hangs on a YubiKey touch that never comes in a headless session.
The round-1 corrections to the ledger, the matrix, this file and
`util/ad-hoc/2026-09-10_f035_downstream_consumer_probe.py` are a **separate, later** change; check whether
they have landed before assuming the numbers here are the ones on `main`.

**juniper-canopy** — `main` at `b792256` carries the F-CANOPY-035 fix. **#614 is the strand repair** that
round-1 validation forced (a network-level fetch failure permanently disables the guarded Interval); check
its state before reading `:8053`'s behaviour as final, since that leg predates it. The fix worktree
`juniper-canopy--fix--f035-metrics-store-running-guard--20260910-0459--8cfb29ac` is clean at HEAD
**`6f04da6e`** and **is serving `:8053`** — do not remove it while that leg runs. Its branch
`fix/f035-metrics-store-running-guard` was deleted on merge. The strand repair has its own worktree,
`juniper-canopy--fix--f035-running-guard-strand-repair--20260910-2002--b7922569`.

**juniper-cascor / juniper-data** — untouched.

---

## 8. Validation status — TWO rounds run, and this document failed both

Per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, sized to the
top-right cell (six of seven escalators). **Round 1** — three Lane A reviewers at distinct entry points —
produced 10 corrections and one live code defect (canopy#614). **Round 2** — two Lane B reviewers on
opposing briefs, run on the round-1-corrected text as §2 requires — overturned the **disposition**, found
**two errors introduced by round 1's own fix pass**, and found that the control round 1 declared untouched
is confounded.

**What survived both rounds**: the eviction mechanism. Re-verified from the bundle by a reviewer who read
`getUniqueIdentifier` independently, reproduced in a canopy-free clean room, and demonstrated a third time
by the F-052 A/B — the only genuinely single-variable measurement in the set. **Nothing was reverted.**

A third round is **not** owed on the termination rule (§4: stop when a round produces no finding that
changes a number, a disposition, or an action) — but round 2 changed all three, so its own corrections are
unreviewed. Treat §9 R1–R7 as the least-audited text here.

---

## 9. Corrections (read before §1–§6)

### Round 2 — the disposition was wrong

| # | as written | what round 2 found |
|---|---|---|
| R1 | F-CANOPY-052 is "a second defect the empty store was masking", P2 | **It is F-CANOPY-035's mechanism**, one callback downstream. `update_loss_plot` took the training-state store as an Input; that store is written off a 1000 ms interval **unconditionally**, and `/api/state` carries a per-call `timestamp` so the value always differs. Re-`requested` at ~1 Hz under one `getUniqueIdentifier` → `:3027` evicts, `:2698` discards. **Measured: 1/3 with the tick running, 3/3 with it stopped.** Re-disposed **P1**; fixed in canopy#618 |
| R2 | "F-CANOPY-035 FIXED" | **fixed for ONE victim.** The store was repaired; the consumer that reads it was left evicted. With F-052 at P2 this also produced "canopy has zero open P1" while a panel was blank on two thirds of loads |
| R3 | the remaining split is "never fired vs fired and returned `no_update`" | **the second branch is impossible in the source** — `update_loss_plot` has two returns and neither is `no_update`. And "zero traces AND zero annotations" is reachable only as the `dcc.Graph` mount default (no `figure=` prop), which is proof no output was ever applied |
| R4 | still-owed item 1: build a `store.subscribe` reader of `getState().callbacks`, "no probe in this arc has ever built" one | **it exists** — `2026-09-07_f035_callback_lifecycle_probe.py`, 25 KB, documented in this ledger ~6,000 lines earlier — and was **retired on a positive control**. The item would have cost a successor a day |
| R5 | the fix's only cost is the ~4–5 s cadence overhead | #613 also moved the tick `FULL_HISTORY_POLL_TICK_MODULUS` counts, so full-history refetch went **~5 s → ~27–37 s**. Named in canopy#614 and nowhere here |
| R6 | round 1's "the clean room varies only `running=`, on a shared lane" | **false** — one Interval, one callback: a *dedicated* lane, and the `plain` arm **is** a dedicated lane without the guard, which never filled. Round 1 discarded the arm supporting half the shipped fix |
| R7 | round 1's C4, "the wire census **excludes** 'fired and was not applied'" | too strong — the census swallows unparseable responses (`except Exception: return`, **no `unparsed` counter**) and attaches ~5 s after navigation. And that branch is the one that was happening |
| R8 | "Before / after, **matched legs**", three times | **false.** `eb05021d → eab7cf43` is 39 files / 3726 insertions / 12 commits, with **442 insertions in `dashboard_manager.py` alone** — 8× the fix's delta, in the file that registers every callback. Struck; it is suggestive, not a control |

### Round 1 — the counts and one live defect

| # | as first written | what round 1 found |
|---|---|---|
| C1 | "`running=` … so a failed fetch cannot strand the poller" | **FALSE, and a live defect.** `:1113` is in `_handleWebsocketCallback`. On the HTTP path `runningOff` comes only from `completeJob()`; `handleError` rejects without it, so a **network failure strands the poll for the life of the page**. Repaired in canopy#614 |
| C2 | the dose-response "closed it" | **structurally forced** (ascending + stop-on-land ⇒ its falsifier is unreachable), and neither fill is attributable to the long period; 0 of 37 long-period invocations landed anything |
| C3 | "the 12 candidate entries sit EARLY" | **FALSE** — indices 53–64 of 66. `RENDER-STILL-DEAD` was unexplained, not contaminated (and R1 now explains it) |
| C5 | "fast lane still ticking at 1 Hz" | **0.507 Hz** — the error this document's own trap 2 warns against |
| C6 | "~7.3 s … NOT period-bound" | one of two 1000 ms runs cited; the other gives 5.5 s. n_treated = 1, treatment never verified as delivered |
| C7 | "2 of 5" | **2 of 6** |
| C8 | "the consumer fired exactly once" | 1 in one rendering run, **2** in the other |
| C9 | "53 responses … none applied" | **52** pre-control |
| C10 | trap 1 attributed the verdict to the boundary error | the corrected boundary returned **the same verdict**; neither is sound |

**Instrument defects, recorded because the artifacts stay in the tree**: the tick boundary is computed
against `fast-update-interval` on all three `:8053` runs; `LAND_WINDOW_S = 2.0` is calibrated on
round-trip rather than a measured **6.95 s** apply latency; all three post-fix runs ran `--no-control`
while two print "the instrument's own control failed"; and `2026-09-10_f035_fix_wiring_check.py` archives
nothing (and its "exactly one writer" assertion goes red once #614 lands).

**One charge cleared**: the `paths.strs` reader is not hiding duplicates — a live layout census finds zero
duplicate ids anywhere.
