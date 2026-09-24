# `util/ad-hoc/` — Single-use, temporary, and unfinished scripts

This directory is the home for scripts that:

- Will run once (or a handful of times) and then be **retained as provenance** of the work they produced (retention policy, owner decision 2026-08-25 — see Lifecycle below).
- Are work-in-progress and not yet ready for promotion to `util/` proper.
- Support a one-off investigation, migration, or analysis tied to a specific PR / incident.

It exists because the alternative — authoring such scripts in `/tmp/` — caused real, irrecoverable loss in the v1–v4 requirements-snapshot effort (`phase4_consolidate.py`, `v2_citation_validate.py`). See [`../../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md` §7](../../notes/JUNIPER_2026-05-18_JUNIPER-ECOSYSTEM_REQUIREMENTS-NEXT-STEPS.md#7-stale--drift-detection) and [plan-doc §12](../../notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md#12-open-issues--questions-discovered-during-execution).

The repo-level rule lives in [`../../AGENTS.md`](../../AGENTS.md#script-placement-mandatory); the ecosystem-level restatement lives in the parent `Juniper/AGENTS.md` "Cross-Project Conventions" section (one directory above this repo, outside the juniper-ml git tree).

---

## Conventions

### File header (Python)

Every Python script in this directory should declare its scope and lifecycle inline:

```python
"""
<one-line purpose>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: <name>
Created: YYYY-MM-DD
Status: ad-hoc — <intent: one-off | wip | migration | investigation>
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: <PR #, incident, or notes/ doc>
"""
```

### File header (bash)

```bash
#!/usr/bin/env bash
# <one-line purpose>
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     <name>
# Created:    YYYY-MM-DD
# Status:     ad-hoc — <one-off | wip | migration | investigation>
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    <PR #, incident, notes/ doc>
set -euo pipefail
```

### Naming

- Date-prefix optional but useful: `YYYY-MM-DD_<short-purpose>.{py,bash}`.
- Use kebab-case or snake_case consistently — match existing siblings.

---

## Lifecycle

| Stage                                 | Action                                                                                                            |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Created**                           | Place here. Include the header above; under the retention policy the `Retire when:` field reads `RETAINED`.       |
| **Used for its purpose**              | Commit any non-trivial output / log alongside the script (e.g., in `notes/`) so the artifact survives the script. |
| **Graduates to permanent utility**    | Move to `util/<name>` (drop `ad-hoc` from the header `Status:`). Update any docs that referenced the old path.    |
| **Retained (the default)**            | **Owner decision 2026-08-25: ad-hoc scripts carry no retirement deadline.** They are kept in place as the provenance of how evidence, migrations, and one-off analyses were produced, even after their purpose completes. Pre-policy `Retire when:` conditions were rewritten to `RETAINED (…) Previously: <condition>` so the historical trigger stays readable. |
| **Retired (exceptional, owner-directed only)** | Only on an explicit owner decision — never as routine cleanup. Move to `util/ad-hoc/retired/` with the retirement date in the filename; do not plain-delete. |

**Example (juniper-ml#928):** the seven `2026-07-28_flood_census_*` / `docs_census_*` / `fp_transition_c2` investigation scripts were moved to `util/ad-hoc/retired/` with a `_RETIRED-2026-08-05` suffix once the flood-remediation analysis landed and `util/sequence_safety/` + `util/fleet_triage/predict_merge.py` became the live screens. Keeping the retired files in-repo preserves notes/ appendix and provenance comments that still name the old paths.

---

## Resident-hazard gap triage (operational)

Three complementary scanners — keep all three; the first alone cannot find a directive that was never in `AGENTS.md`:

| Script | Question |
|--------|----------|
| `2026-08-28_hazard_triage.py` | Which *already-resident* `AGENTS.md` blocks look like hazards? (`gh api` on GitHub `main`; default `--min-score 2`) |
| `2026-08-28_resident_gap_scan.py` | Which source comments are hazard-shaped and resident nowhere? (local, read-only; ranks by identifier count) |
| `2026-08-31_resident_gap_triage.py` | Gap finding scored with four severity signals on the **block** (default `--min-score 3`; `--json` writes every scored row; `--self-check` pins cascor `cascade_correlation.py:1927`) |

The scored **total is not a health metric**. Relocation removes resident identifiers, so the gap predicate starts matching them — cutting widens the gap by construction. Read the score ≥ 3 count (and whether anything *new* appears there). `SKIP_DIRS` excludes in-repo worktrees (#1519).

Operator contract: [`docs/REFERENCE.md` § Resident-Hazard Gap Triage](../../docs/REFERENCE.md#resident-hazard-gap-triage). Fleet record: [`notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md`](../../notes/JUNIPER_2026-08-31_JUNIPER-ECOSYSTEM_RESIDENT-HAZARD-GAP-TRIAGE.md).

---

## Snapshot sidecar chain (operational)

`2026-08-24_regenerate_sidecar_chain.bash` (lands with juniper-ml#1333) regenerates index → classify → attribute → backfill in order. It is ad-hoc until a supported `util/` entry point exists.

Do **not** export `JUNIPER_CASCOR_SNAPSHOTS_DIR` for this script. That variable is both cascor's snapshot write directory and `snapshot_index.default_root()`; redirecting it (as the probe scripts in this directory do, so they cannot grow the archive) would point every stage at the scratch dir. Pass `--root` instead. `--backup DIR` is required and must already hold all four `snapshots_*.jsonl` files.

Operator contract: [`docs/REFERENCE.md` § Snapshot Attribution Dataset Pin](../../docs/REFERENCE.md#snapshot-attribution-dataset-pin).

---

## X7 off-loop census (operational)

`2026-09-04_x7_offload_census.py` (v1) and `2026-09-04_x7_offload_census_v2.py` (v2, v0.3.0) land with juniper-ml#1631. They are **not** CI and **not** the slice-1a authority — that is `juniper-canopy/src/tests/regression/test_x7_off_loop_discipline.py`.

- **v1 is retained unfixed as the negative example.** It matches receiver *names*. The bare name `client` is bound in canopy `main.py` to cascor, redis, cassandra, **and** an `httpx.AsyncClient`, so it reports an awaited async call as blocking. That is the same flaw that makes `ruff --select ASYNC` report "All checks passed!" against these sites.
- **v2 resolves assignment provenance** and reports an `UNRESOLVED` bucket rather than guessing. Use it to explore; use the canopy gate to decide when slice 1a is done.
- **Exemption must be site-local.** A module-global expression match ("this call text was handed to `to_thread` somewhere in the file") hides every twin of an offloaded call — including the three health endpoints X7 is defined by — and the miss grows as work proceeds. v2 v0.3.0 and the canopy gate at `d33ab0a` are site-local only. Do not reintroduce cross-site matching.
- Both read `main.py` only. Design §5.2 also puts the metrics relay's `extract_network_topology()` in slice 1a; a receiver-based scan cannot see a `self`-method with internal I/O.
- Both hardcode `CANOPY_MAIN` to `/home/pcalnon/Development/python/Juniper/juniper-canopy/src/main.py`. Retarget before running on any other host.

Operator contract: [`docs/REFERENCE.md` § X7 Off-Loop Census](../../docs/REFERENCE.md#x7-off-loop-census).

---

## Topology step order and blast-radius IDs (operational)

`e2e_seg17_topology_driver.py` `--step` is order-preserving on one page. `topo` fills the raw-topology store (M-03 Weight Matrix); a later `topostate` then scores M-18 `INDETERMINATE`. Re-drive `--step topostate` **alone**. Scorer predicates stay with in-flight docs #1675.

The copied blast-radius sentence *W4-01..17 and W1-12..14 stay BLOCKED* names 20 IDs that **are all defined** — matrix §4's `### W4` is 17 numbered steps and `### W1` is 19. They are written as ordinals under a heading, so a grep for `W4-09` finds nothing; that is a fact about the spelling, not the definition. The plan's zero matches are by design (it delegates workflow ids to the matrix).
**The module docstring is correct — leave it.** What is thin is coverage: only `W4-02` was ever driven. juniper-ml#1695 filed this as F-E2E-007 and **withdrew it the same day**.

`e2e_finding_triage.py` `pri_of` takes the **first** severity token anywhere in the bolded header body. Do not name another severity in header prose. Dispositions stay with in-flight docs #1646.

Operator contract: [`docs/REFERENCE.md` § Canopy E2E Topology Step Order and Blast-Radius IDs](../../docs/REFERENCE.md#canopy-e2e-topology-step-order-and-blast-radius-ids).

## Memory-budget slack (operational)

`2026-08-25_p5_port_memory_budget.py measure-growth`, `2026-08-26_p5_fleet_state.py`,
`2026-08-26_p5_promote_ready.py`, and `2026-08-28_p5_cut.py` size a ceiling's working room.
They are **not** the `Memory Budget` CI gate (`util/memory_budget_check.py`).

- **Headroom is not slack.** The checker prints `headroom = ceiling_chars - chars` and fails only
  on over-ceiling growth or an undeclared ceiling raise. It never reads `measure-growth`.
- **`measure-growth` prints `median` / nearest-rank `p90` / `max`.** There is no required-slack
  field and no exclusion flag. Planning slack is `max(max, 2000)` in the cut / promote helpers.
  Size from `max`, never from p90. Default `--ref` is `HEAD` — pass `origin/main` after a fetch.
- **`--ratchet` seeds, it does not leave working room.** After a cut, hand-edit slack.
- **`p5_fleet_state.py` counts chars** (`len()` of UTF-8 text from the GitHub API). The API
  `size` field is bytes.

Operator contract: [`docs/REFERENCE.md` § Memory-Budget Slack (Planning)](../../docs/REFERENCE.md#memory-budget-slack-planning).

## F-039 store probe (operational)

`e2e_f039_topoprobe_instrument.py` (`apply` / `report` / `revert`), `e2e_f039_metrics_store_soak.py`, and `e2e_f039_duplicate_store_probe.py` are the revertible server-side instrument that root-caused F-CANOPY-039 (FIXED in juniper-canopy#549). They are **not CI**.

- **Read the whole `report` series**, not its head. Topology's measured healthy shape is `eq=False` ×4 then `eq=True` ×11. A head-only reading of that same log produced the retracted "permanently empty" claim.
- **`--target topology` refuses** on current canopy: `_update_topology_store_handler` no longer receives the client's store copy. Use `--target metrics`, or add the `State` first.
- **Backup lives in the git dir** (`f039-topoprobe.f039bak`), never beside `dashboard_manager.py`. A work-tree bak is swept by `git add -A`.
- **`curl` cannot tick a Dash interval.** Hold a live browser session with the soak script.
- **`e2e_f039_duplicate_store_probe.py` exit 1 is not a verdict** — the probe could not run. `dcc.Store` has no DOM; `paths.strs` hides duplicates.
- **That `paths.strs` blindness now has a lift: `2026-09-05_dash_layout_id_census.py`.** Dash serves the layout tree as JSON from the *server* at `/<prefix>_dash-layout`, before dash-renderer indexes
  anything, so a duplicate id appears there as two nodes carrying one id — which `paths.strs`, a one-id-to-one-path map, cannot represent at all. Use it before reaching for the duplicate probe. It
  settled the question for `metrics-panel-metrics-store` on 2026-09-05 (465 id-bearing nodes, 465 distinct, zero duplicates anywhere) and a clean census is a **refutation**, not an absence of evidence.
  It reads the layout **as served**, so a component a callback adds later would not appear; every canopy panel declares its stores statically, but that bound is real.
- **A response census must detach its listener.** `2026-09-04_f035_candidate_loss_redrive.py` attached `page.on("response", …)`, never removed it, and returned the dict the handler keeps mutating —
  so its log printed an honest 30 s window while the JSON, dumped 48 s later at end of run, reported the whole listening lifetime. One run, two archived artifacts, 17 writes vs 46. Both censuses now
  `remove_listener`, return a copy, and record `window_s` in the artifact. If a census does not stop counting when its window closes, it is not a census — and the two artifacts will disagree silently.
- **`2026-09-05_f035_store_write_latency_probe.py`** times each store-writing round trip against the interval that re-requests it, because dash-renderer retires an in-flight call on re-request. Read its
  `overlap_fraction` as the retirement **precondition**, never as retirement: on 2026-09-05 it read 0.69 while the store was constant-empty across 130 server-side comparisons, so nine unopposed
  responses also failed to land. A number that explains most of a result is not the cause of it.
- **`2026-09-07_f035_renderer_dispatch_probe.py` needs no revert** — it patches nothing on the server. `window.store` is dash-renderer's Redux store, so wrapping `dispatch` and subscribing to state observes
  both "did the payload arrive at the reducer" and "was it applied" from the page alone. Prefer this shape over a server-side instrument whenever the question is about the *client's* copy. Two traps it
  paid for: (a) **a key match is not a value match** — asking "is the store id a key in this action?" also matches `paths.strs[id]`, dash-renderer's PATH INDEX, which reported 577 bogus `SET_PATHS` hits
  with `len=18` (a path length dressed as a row count) against 3 real ones, a 192x over-count; require the payload position to look like a props write. (b) **a pre-registered rule does not protect a
  branch that encodes the expected answer** — its `carrying and reached` branch *asserted* "something reverts it afterwards" and so mislabelled the one run in eight where the store actually worked and
  the value STAYED. Check for the revert; do not assume it.
- **Do not attribute a difference to a procedural detail on n=1.** Run 1 of that probe populated the store where the re-drive did not, and differed by a `page.reload()`. The obvious reading — "reload
  fixes it" — died to a 2x2 over {fresh server, loaded server} x {reload, no reload}: run 1 did not reproduce **in its own cell**. When a run behaves differently, drive the cell it sits in before naming
  the variable, and re-run the anomalous arm itself — a single success is an anomaly to be reported, not a condition to be announced.
- **`2026-09-07_f035_callback_lifecycle_probe.py` reads dash-renderer's pending-callback bookkeeping out of the SAME Redux store** (`state.callbacks`: `requested` / `prioritized` / `blocked` / `executing` /
  `watched` / `executed` / `stored`). No work against the minified bundle, no product change, nothing to revert. `--discover` dumps the real list names first — those names have been renamed across
  dash-renderer versions, and an instrument that assumes a schema it never checked is how a confident zero gets produced. Two traps it encodes: **match on the OUTPUT position, never a substring** (a store
  that is a `State` of its writer and an `Input` of five readers is mentioned by nearly every entry in every list, so a substring test measures "callbacks near the store" and returns a large confident
  number for the wrong question); and **a presence COUNT cannot distinguish supersession from a stuck request** — "present in `watched` for 2,344 notifies" fits both, and they need opposite fixes, so count
  the absent→present TRANSITIONS. 23 and 26 separate entries across two replicates is a series; one long run would have been a hung promise.
- **Sampling on Redux notifies can miss a fast transit.** An entry that passes through `executed` between two notifies is invisible, so "never reached a terminal list" is not self-supporting. Close it from
  outside the instrument: F-CANOPY-035's conclusion rests on that list evidence *plus* an independent `paths.strs` read showing the value never advances *plus* the dispatch probe's zero value-carrying
  dispatches. One instrument's blind spot is another's measurement; say which one closes it rather than asserting the negative.

Always `revert` before committing anything from the instrumented checkout.

Operator contract: [`docs/REFERENCE.md` § F-039 Store Probe](../../docs/REFERENCE.md#f-039-store-probe).

## Ruleset context audit (operational)

`2026-08-10_ruleset_context_audit.py` classifies each publishing repo's `required_status_checks` as BLOCKING / MATCHED / Tier 1 / path-gated / advisory. Read-only (`gh api` + `gh pr list`). It does **not** add or remove contexts — that is `2026-08-20_require_context_safely.py`.

A required name that never reports leaves `main` unmergeable with every visible check green (the 2026-08-10 fleet-union class). Re-run the auditor; do not quote the incident note's §1 counts. Human-mode exit 0 can still print `ERROR:` rows; `--json` fails closed on probe errors.

Operator contract: [`docs/REFERENCE.md` § Ruleset Context Audit](../../docs/REFERENCE.md#ruleset-context-audit).

## Canopy E2E matrix writes (operational)

The 298-row ledger is `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`. Do not hand-edit status cells.

| Script | Default | Load-bearing constraint |
|--------|---------|-------------------------|
| `e2e_matrix_fill.py` | dry-run (`--write` to apply) | Locates `status` by header per table; splits on unescaped pipes; first `--verdicts` source wins (newest first). `--overwrite` clobbers hand-authored `DIVERGENCE` cells — use rescore for a named subset. |
| `2026-09-02_matrix_set_verdicts.py` | **writes immediately** | `--from` must match every named row. Atomic: one miss updates nothing. Naive split on every pipe — do not use on escaped-pipe rows. |
| `e2e_matrix_rescore.py` | dry-run | Named `--row` only. Missing ids warn **and still write** the found rows. |
| `e2e_unfilled_rows.py` | read-only | Ledger reader. Do **not** plan from `e2e_row_coverage.py` (estimator). |

W-lane ids have no status cell (`no-matrix-row`, not an error). Operator contract: [`docs/REFERENCE.md` § Canopy E2E Matrix Writes](../../docs/REFERENCE.md#canopy-e2e-matrix-writes).

## F-CANOPY-027 poller starvation (operational)

The `e2e_f027_*.py` family is **retained provenance** of the canopy dashboard starvation investigation (finding **FIXED** in juniper-canopy #507 / #509 / #511). Recurrence looks like a wiring miss (store fills, consumers never paint) and is not.

Operator contract: [`docs/REFERENCE.md` § F-CANOPY-027 Poller Starvation Probes](../../docs/REFERENCE.md#f-canopy-027-poller-starvation-probes).

Do **not** add a new `dcc.Interval` / poller to "fix" a frozen panel — that re-saturates dash-renderer's hard-coded 12-slot pool. Feed an existing store instead (canopy#524 used `metrics-panel-metrics-store`).

Live probes (`e2e_f027_queues.py`, `e2e_f027_ready.py`, `e2e_f027_slots.py`) need a **live isolated** canopy (`JuniperCanopy1`, `DEMO_MODE=0`, empty `LD_LIBRARY_PATH`) and Playwright via `e2e_w3_params_driver.py`. Point them with `JUNIPER_E2E_CANOPY_URL` (default `http://127.0.0.1:8051`) — there is no `--base-url` flag.

`e2e_f027_deps_endpoint.py` is a **server-registry** check: run it from `juniper-canopy/src` so `frontend.dashboard_manager` imports. `e2e_f027_cleanroom.py` is self-hosted (default port `8399`); rebuild is the default, `--no-rebuild` omits the once-only `visualization-tabs.children` rewrite.

These scripts are **not** CI. Sibling `e2e_f027_*.py` files in this directory are earlier refutation probes (layout, dispatch, redux, DOM) kept as the twenty-mechanism record; start with queues / ready / slots.

## Worktree in-use probe (operational)

`2026-09-02_worktree_inuse_probe.py` is an independent second opinion for a worktree sweep. The cwd-only liveness probe (`2026-08-20_worktree_liveness_probe.py`) and the P5 cleaner's `occupied()` gate miss an editor or a long `pytest` whose cwd is elsewhere while a file inside the tree is still open.

- STRONG (cwd or an open fd inside the tree) → `IN USE`, exit 1 `REFUSE`.
- WEAK (cmdline substring) → `review` / `CAUTION`, exit stays 0. The first run reported every tree in use because the probe named the paths as arguments; self and parent pids are excluded from WEAK by pid.
- Empty argv exits 2 (the cwd-only probe exits 0 on that misuse).
- Read-only. Sibling `foo-extra` is not inside `foo`. Unreadable `/proc` (other users) is counted, not treated as in-use.

```bash
python3 util/ad-hoc/2026-09-02_worktree_inuse_probe.py <worktree-dir> [<worktree-dir> ...]
```

Operator contract: [`docs/REFERENCE.md` § Worktree Divergence](../../docs/REFERENCE.md#worktree-divergence-is-a-memory-cost).

## Canopy E2E finding triage (operational)

`e2e_finding_triage.py` is the mechanical P0/P1 open-count for Phase 2's exit criterion. It reads only line-starting `**F-<AREA>-<NNN> — …**` headers in the evidence ledger.

- `FIXED` / `HEALED` in the last 170 characters of the header → closed.
- `ACCEPTED` in that same tail, and not also FIXED → owner-deferred. Third disposition: not FIXED, not OPEN.
- `--open-only` hides closed rows; the totals block still counts every finding.
- Always exits 0. A green shell is not "no open P0/P1".

```bash
python3 util/ad-hoc/e2e_finding_triage.py
python3 util/ad-hoc/e2e_finding_triage.py --open-only
```

Operator contract: [`docs/REFERENCE.md` § Canopy E2E Finding Triage](../../docs/REFERENCE.md#canopy-e2e-finding-triage).

## F-CANOPY-037 render census (operational)

`e2e_f037_render_census.py` re-drives the topology-graph paint that F-CANOPY-037 measured in 2 of 11 sessions. Default `--sessions` is 11; a single session is not a comparable claim. Exit 0 means every session produced PASS or FAIL (even if painted==0); exit 2 means the census failed to measure. All-zero `hidden_units` is INVALID (nothing to draw), not a render FAIL. Idle populated is VALID.

The census does **not** start canopy. Bring up the isolated trio first (`util/isolated_stack.bash --up`), train a network, then:

```bash
python3 util/ad-hoc/e2e_f037_render_census.py
```

No `--base-url`; inherit `JUNIPER_E2E_CANOPY_URL` (default `http://127.0.0.1:8051`). A/B a pre-merge checkout on `:8052` with `e2e_f037_ab_premerge_leg.bash`. `_find_juniper_root` must see **both** `juniper-canopy` and `juniper-cascor`; three hops from a nested worktree recorded `sha=None`.

Operator contract: [`docs/REFERENCE.md` § F-CANOPY-037 Render Census](../../docs/REFERENCE.md#f-canopy-037-render-census).

## F-CANOPY-035 discriminating test, the live-run probe, and the leg tooling (operational, 2026-09-08)

The 2026-09-08 session lost the fixture to a host reboot (`/tmp` is tmpfs; the trio ran under `nohup` from it), restored it from
`snapshot_20260905T103912Z`, and found that cascor's resume path was itself broken. What it left behind:

- **`2026-09-08_f035_supersession_test.py` is the test that settles F-CANOPY-035's mechanism**, on the model of `e2e_f039_supersession_test.py`: baseline
  the contended regime, `setProps({disabled: true})` on `fast-update-interval` (which silences the writer's own trigger and the whole fast lane), let
  in-flight work drain, trigger the writer exactly once through `n_intervals`, watch. Run 1 on the 48-unit fixture: **39 responses carrying 71 rows in
  30 s with the store at 0, then the store at 71 within 2.9 s of the tick being disabled, and it stayed** → `APPLIED-UNCONTENDED`. That is
  supersession's own prediction — the last call in a series lands when nothing follows it — observed end to end with one `paths.strs` read per second
  and no other instrument attached. **Two things it did NOT show**: the single manual `n_intervals` trigger afterwards produced no request at all
  (recorded, not interpreted), and the *rule* that performs the supersession is still unnamed.
- **The lifecycle probe does not discriminate.** Its 2026-09-07 control on `network-visualizer-topology-store` had been set aside on a
  `hidden_units: 0` read taken on the Candidate Metrics tab, where that store's poll is tab-gated off. Re-driven on the **Network Topology** tab for
  90 s, on a store whose graph paints 48 nodes and whose value the dispatch probe saw dispatched three times, it returned the same
  `RETIRED-BEFORE-EXECUTION` (19 entries into `watched`, terminal bucket empty). So "never reaches a terminal list" is a property of the sampler, not of
  the store, and the 09-07 lifecycle verdict is downgraded to a non-discriminating observation. It also **perturbs what it measures**: it
  `JSON.stringify`s every entry of every list on every Redux notify, and its own independent read of the topology store came back at the mount
  default after its window. The mechanism claim now rests on the behavioural test above, not on `state.callbacks`.
- **The dispatch probe's positive control is positive** (`--store network-visualizer-topology-store --tab "Network Topology"`, added 2026-09-08): three
  `Callbacks.Aggregate` actions carrying the store's dict, independent read `hidden_units: 48`. Its verdict rule was list-only and scored that
  `DISPATCHED-EMPTY`; the rule now treats a non-null non-list value as carrying. Re-run the control after any change to the rule.
- **`2026-09-08_live_run_probe.py`** watches one growth run from three tabs at once (Candidate Metrics, Training Metrics, Network Topology — each
  per-tab poll lane gates on `active_tab`, so a closed tab measures nothing) and scores M-CANDIDATES-09/-10/-11, F-CANOPY-026's mid-run pair and
  M-TOPOLOGY-16 from rules fixed in its docstring; `--start` presses Start only after the tabs are open. **Its per-sample cost on a 944-connection
  topology was ~22 s** — the topology page's main thread is saturated and every `evaluate` waits for it — so a 50 s run yields three samples. Sample
  the topology page less often than the others, or run it in its own process. It records canopy's `/api/state` beside cascor's status so a blank
  badge can be attributed to the server never learning versus the browser never applying: on 2026-09-08 that attribution pointed at cascor's
  WebSocket relay, which had dropped both canopy legs at the instant training started (see the ledger, F-CASCOR-003).
- **`2026-09-08_cascor_ws_drop_probe.py`** is the raw-client reproduction of that drop: connect to `/ws/training`, sit past the 5 s resume handshake,
  trigger a state broadcast that trains nothing (`POST /v1/snapshots/<id>/resume` of the network the leg already holds), and report whether a
  `state` frame arrives, a close frame arrives, or nothing at all. Note that the trigger clears cascor's metrics buffer and leaves the FSM at
  `RESUME_READY`; run the COMPLETED-state instruments first (`2026-09-08_post_growth_sequence.bash` chains them, one browser at a time).
- **`2026-09-08_replay_block_redrive.py`** drives M-METRICS-11..16/-18 with every prop read through `paths.strs`. All three replay callbacks compute
  `max_index = len(metrics_data) - 1` from `State(metrics-panel-metrics-store)`, so the index rows are downstream of F-CANOPY-035 and are scored
  `BLOCKED-BY-F-035` when the store is empty, while the play toggle and the speed buttons are data-independent and are scored on their own merits.
- **Leg tooling.** `2026-09-04_canopy_verify_instance.bash` now (a) defaults its run dir to the reaper-protected `${JUNIPER_E2E_RUN_DIR:-/tmp/juniper-e2e}` —
  its old `/tmp/juniper-canopy-verify` was inside neither protected root, so the pid file it wrote protected nothing and its REAPER NOTE was false from
  2026-09-04 to 2026-09-08; (b) stamps `JUNIPER_CANOPY_GIT_SHA` / `_BUILD_DATE` from the checkout it launches, which canopy reports on `/v1/health` as
  `git_sha`, and `e2e_w3_params_driver.serving_commit()` reads that back so every driver's transcript carries the SERVING commit (ledger still-owed item 7);
  (c) lets `JUNIPER_CANOPY_CASCOR_WS_ORIGIN` be overridden, because cascor's control-WS allowlist admitted only the trio's :8051 origin and every :8052
  verify leg ran with its control stream 403-looping — `util/isolated_stack.bash` gained `JUNIPER_E2E_CASCOR_WS_EXTRA_ORIGINS` for the proper fix.
  **`2026-09-08_cascor_leg_swap.bash`** restarts the trio's cascor from a worktree by pid (keeping the stack's own pid file), points it at the primary's
  `cascor-snapshots/` (a worktree-run cascor otherwise resolves its snapshot root inside its own tree and lists nothing), and stamps its SHA the same way.
  The fixture does not survive a swap; re-`resume` it from its snapshot. **Its control-WS allowlist is `CASCOR_WS_ORIGINS` — a different name from the
  stack's `JUNIPER_E2E_CASCOR_WS_EXTRA_ORIGINS`, and its default is `http://127.0.0.1:8051` ALONE**, so a hand-run swap silently re-opens F-E2E-008 for the
  `:8052` verify leg. Pass `CASCOR_WS_ORIGINS=http://127.0.0.1:8051,http://127.0.0.1:8052` whenever both legs are up;
  `2026-09-08_relay_repair_sequence.bash` already does.
  **`2026-09-08_relay_repair_sequence.bash`** is the whole repair in one command, and the only script here that both swaps a leg and drives a growth window:
  (A) the drop probe against the running leg, (B) the swap onto the fix worktree plus a `/resume` and the same probe again, (C) stage the dataset, `PATCH`
  the cap and `candidate_patience`, run `2026-09-08_live_run_probe.py --start`, then restore `candidate_patience`, (D) snapshot. It writes a step-by-step
  summary to `${RUN_DIR}/relay_repair_sequence.txt`; read that before the per-step artifacts. `2026-09-08_post_growth_sequence.bash` is the same idea for
  the idle-fixture instruments (storestorm, dataset seq, cardsprobe, the f035 re-drive, the two probes, supersession run 2).
- **`2026-09-08_append_signed_commit.py`** is the verb `open_signed_pr.py` refuses by design: one GitHub-signed commit onto an EXISTING branch, pinned to
  the branch's current head. Built to extend juniper-cascor#632 after the first fix proved incomplete. **Superseded for new use by
  `util/push_signed_commit.py`**, which pins `expectedHeadOid` to the head your edits are based on (`--expected-head`) rather than to a live read; this
  script and its sibling existing-branch drivers are retained as provenance.
- **`2026-09-09_tab_crosstalk_probe.py`** answers whether two canopy pages in ONE browser context keep the tabs they selected. They do NOT: canopy
  persists the active tab in `layout-state-store`, a `dcc.Store(storage_type="local")`, and a clientside callback drives `visualization-tabs.active_tab`
  from it — so localStorage, which every page of one context shares, makes the LAST page to pick a tab move all the others. Verdicts `CROSSTALK` /
  `INDEPENDENT` / `INDETERMINATE`; reads each page's OWN `active_tab` through `state.paths.strs`, never from a screenshot. Run it before trusting any
  multi-page probe (it is why `2026-09-08_live_run_probe.py`'s three-tab design is unsound — see F-CANOPY-051).
- **`2026-09-09_verify_served_cascor_matches_merge.py`** proves what a `git_sha` stamp cannot when a leg runs a DIRTY worktree: it sha256s the served
  files against the blobs GitHub holds at a merge commit. Written when `/v1/health` on the `:8202` leg was found to report the worktree's BASE commit
  (a dependency bump containing none of the fix) while the fix rode uncommitted on top.
- **`2026-09-09_capture_endpoint_evidence.bash`** curls the six endpoints whose values the Phase-5 record cites — canopy and cascor `/v1/health`, the
  pool-history route, `/v1/metrics/transport`, `/v1/network`, data's `/v1/generators` — into one transcript. Written because four Phase-5 claims had been
  made from live reads that were never archived, which is the one thing this arc's own validation lanes reliably catch.
- **`2026-09-08_topology_store_dump.py`** prints the topology store's SHAPE (keys, the `hidden_units` field, node/connection counts) beside the stats bar
  and the graph, because "the store holds the mount default" and "the store holds a payload whose count field is 0" read identically through a bare
  `hidden_units` read. On :8052 the store filled ~15 s after the tab opened and the graph painted ~15 s after that.

---

## F-CANOPY-035 mechanism, fix and aftermath (operational, 2026-09-10)

The instruments that took F-CANOPY-035 from "leading hypothesis with an unexplained residual" to a merged
fix (juniper-canopy#613 `b792256`). Full write-up: **Phase 6 — 2026-09-10** in
`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`.

- **`2026-09-10_f035_unopposed_response_test.py`** brackets EVERY store-writing response individually —
  classified opposed/unopposed and matched against a continuous in-page trace of the store's length — where
  `2026-09-05_f035_store_write_latency_probe.py` reads the store only at window start and end. Its first
  run classified opposition by the next **HTTP request** and returned `SUPERSESSION-INSUFFICIENT`; that
  boundary is **wrong** (the renderer evicts on a new `requested` entry, created by the TICK) and the
  module now classifies on observed `n_intervals` transitions. **Read its docstring before quoting either
  verdict.** `--early-observer` installs the observer before the tab opens, which is required on a FIXED
  leg — the store fills during page load, so a late observer reads it already full and records no
  transition at all.
- **`2026-09-10_f035_trigger_period_sweep.py`** is the dose-response that actually closed the mechanism:
  raise only the Interval period and watch the store. `PERIOD-CONTROLS-LANDING` twice, with the threshold
  falling inside the measured round-trip range. Runs ASCENDING and STOPS at the first phase that lands,
  because a filled store stays filled and every later phase is unscoreable.
- **`2026-09-10_f035_running_guard_cleanroom.py`** reproduces the defect in ~80 lines with **no canopy at
  all** (an Interval, a slow callback, a store) and shows `running=` fixing it — the same technique
  `e2e_f027_cleanroom.py` used for the 12-slot cap. This is what proved the defect was dash-renderer's
  rather than canopy's wiring, and what proved `running=` applies to ORDINARY callbacks on dash 4.2.0.
- **`2026-09-10_f035_fix_wiring_check.py`** asserts the fix's six wiring properties against the **built**
  app (`app.callback_map` + `app._callback_list` + the real layout), never an AST pass — an AST census of
  canopy's frontend resolves only 151 of 182 callbacks and has already missed two real pollers. Note
  `running=` is NOT on the `callback_map` entry; it lives on the callback spec in `app._callback_list`.
- **`2026-09-10_f035_downstream_consumer_probe.py`** answers F-CANOPY-052 (the defect the empty store was
  masking): is the candidate loss plot empty because of the DATA or the RENDER, and does the consumer fire
  at all. **Use `--no-force`** for any render-rate observation — a forced arm is a different treatment and
  must not be pooled with unforced ones. **The original reason given for that flag was WRONG and is
  retracted**: it claimed the forced `window_size: 40` drops the candidate rows because they "sit EARLY",
  but they are at **indices 53–64 of 66** and a last-40 window keeps **all twelve**. The `RENDER-STILL-DEAD`
  run that story explained away is therefore **unexplained**, and is the only observation in the set where
  forcing a store change failed to render.

Two traps worth carrying forward. **`e2e_finding_triage.py` reads only the LAST 170 characters of a
finding's bold header** (`tail = body[-170:]`), so a `FIXED` placed early in a long header is invisible and
the finding still counts as open — put the disposition at the END. And **a `dcc.Interval` does not tick at
its nominal rate under load**: 54 ticks per 90 s at a 1000 ms period, ~0.6 Hz, which is why the sweep reads
the gap from observed `n_intervals` transitions and never from the constant.

---

## F-CANOPY-052 re-disposed as F-CANOPY-035's mechanism (operational, 2026-09-11)

- **`2026-09-11_f052_trigger_eviction_test.py`** is the unconfounded A/B the rest of this arc never got:
  `setProps` on `candidate-metrics-panel-update-interval.disabled` and **nothing else**, so the only
  variable is the one the hypothesis names. Control 1/3 renders, treatment 3/3, with **zero** loss-plot
  responses on the wire on every non-render against 79–88 naming other outputs in the same window. It
  checks that the intervention actually took (`n_intervals` held, `disabled` true at the end of every
  treatment run) rather than trusting `setProps`' return — the period sweep's 250 ms arm is the
  cautionary case, where nothing recorded that the period was ever delivered.

  Contrast it with `2026-09-10_f035_downstream_consumer_probe.py`, which asks an adjacent question. That
  probe's wire census swallows unparseable responses through a bare `except Exception: return` with **no
  `unparsed` counter**, and attaches ~5 s after navigation, so the page-load window where the deciding
  render happens is unobserved. "Found no evidence of" is what it supports; this one measures.

---

## Release-train ceremony preflight (operational, 2026-09-12)

Two instruments written while cutting juniper-canopy **v0.8.0**, both for the same failure: the ceremony
renders the published GitHub Release body **and** the archived notes file from the package CHANGELOG's
`## [<version>]` section (`util/release_train/ceremony.py:417`), and a Release body is not re-cuttable.
Whatever that section says at `--execute` time is what ships, permanently.

- **`2026-09-12_ceremony_notes_preview.py`** prints the exact body the ceremony would publish, before it
  runs. `ceremony.py --dry-run --json` reports the four planned actions but **not** `plan.archive_content`,
  so the one artefact a human should read first is the one the dry run does not show.
  **`notes_render.py` is not a substitute**: standalone it sources `[Unreleased]`, while the ceremony
  sources the RELEASED `[<version>]` section. On a package whose proposal PR has already moved the
  bullets, the standalone renderer prints *"no `[Unreleased]` bullets found; populate before release"*
  while the ceremony renders the full set — opposite answers to the same question, and the reassuring one
  is the wrong one. Note it must put `util/release_train/` on `sys.path`, not `util/`: `ceremony.py` does
  a flat `import detect`.
- **`2026-09-12_canopy_changelog_backfill_613_614_618.py`** is the repair that preview forced. canopy#613,
  #614 and #618 all merged **before** the release-bump PR (canopy#620, `4006e74`) and are in the v0.8.0
  tree, and none of the three touched `CHANGELOG.md` — so the section the notes are built from documented
  the dataset / selection arc and said nothing about the three poll fixes. Rendered before: `Added: 6,
  Changed: 1, **Fixed: 5**`. After: **`Fixed: 8`**. It writes to `--out` and never touches the shared
  sibling checkout, which other sessions may be using, and refuses to run twice by looking for `(#NNN)` in
  the target section.

**The general trap.** A version bump and a CHANGELOG move are one PR; the fixes that ship in that version
are other PRs, merged earlier, which need not have touched the CHANGELOG at all. Nothing in the release
train checks that correspondence — `detect.py` classifies on `declared > released` and never reads which
commits the section describes. **Diff `git log <last-tag>..HEAD` against the section's own PR references
before `--execute`**, not after.

---

## Worktree converge precheck (operational, 2026-09-12)

- **`2026-09-12_worktree_converge_precheck.py`** answers the one question that makes
  `git reset --hard origin/main` safe in a session worktree: *does any locally modified or untracked
  file differ from the target ref?* It buckets every such path into **SAME** (already landed
  upstream — safe to discard), **LOCAL-NEW** (absent from the ref, so nothing to clobber) and
  **DIVERGED** (present and different — stop), and exits 1 on the third.

  A session that commits through the GitHub API never touches its own working tree, so its edits
  show as modified/untracked indefinitely while being byte-identical to `main`. That looks exactly
  like unlanded work. Run this, confirm `DIVERGED: 0`, check `git merge-base --is-ancestor`, and
  only then reset.

**The failure that motivated it.** The juniper-canopy v0.8.0 ceremony was run from a worktree at
`a359dd8f`, which predates juniper-ml#1875 — the fix normalising `notes_render`'s return to
`"\n".join(lines).rstrip("\n") + "\n"`. The stale copy emitted a trailing blank line, so the archive
PR failed its own `end-of-file-fixer` on **one byte** (`@@ -427,4 +427,3 @@`), reddening Pre-commit
on 3.12/3.13/3.14 and Quality Gate with them. The renderer was not at fault and neither was the
content: `origin/main` had carried the fix for three days.

**`util/` is shared tooling, and a worktree pins it to the commit the worktree was cut from.** The
repo's own release train, sequence-safety screens and merge helpers all live there. Before invoking
any of them from a session worktree, `git fetch` and compare — the stale copy runs happily and
produces output that looks right. Same class as
[[reference_stale_local_checkout_clobbers_your_own_work]] and
[[reference_a_checkout_is_not_a_deployment]], on the tooling rather than the product.

---

## Published-wheel verification — juniper-canopy v0.8.0 (operational, 2026-09-15)

Written after the v0.8.0 PyPI deploy completed, to answer the question a green publish run does
not: **is the artifact PyPI serves the one the repo describes?** juniper-model-core 0.3.1 served
a docstring the repo had already fixed, for four days, under an unchanged version — so "main is
correct" and "the wheel is correct" are separate claims
([[reference_a_checkout_is_not_a_deployment]]).

- **`2026-09-15_verify_canopy_080_wheel.py`** checks the three v0.8.0 fixes against the wheel's
  own members — canopy#613's dedicated guarded interval, canopy#614's strand watchdog,
  canopy#618's Input → State demotion. **7 pass / 0 fail.** Two checks report MISSING-FILE
  because `canopy_constants.py` is not a wheel member, which is the finding below rather than a
  fault of the release.
- **`2026-09-15_canopy_wheel_import_probe.py`** extracts a published wheel to an empty directory,
  puts **only** that directory on the path, and imports in a fresh interpreter — so nothing
  resolves through the repo checkout, which is exactly what makes the same import succeed locally
  and fail for an installer. It classifies a `ModuleNotFoundError` by whether the missing name is
  a **canopy** module (the finding) or a **third-party** one (the probe's own environment).
  **Run it with `--python /opt/miniforge3/envs/JuniperCanopy1/bin/python`**: under a bare
  interpreter `import frontend` dies on `plotly` first and the real failure never surfaces — the
  probe reports that as SKIP rather than passing it off as a result.
- **`2026-09-15_canopy_missing_toplevel_modules.py`** cross-references every `src/*.py` against
  wheel membership *and* against what the shipped members actually import, so the report names
  the whole set rather than the first module that happens to break. Stopping at the first one
  sends the fix out short and the next module returns as a second incident.

**What they found — juniper-canopy#631.** `[tool.setuptools.packages.find]` collects **packages**
(dirs with `__init__.py`); a bare `src/<name>.py` is a top-level **module** and needs a
`py-modules` entry, which canopy has never had. **Ten** such modules are imported by shipped wheel
members and absent from the wheel — `canopy_constants` and `settings` by **13 of the 49 shipped
`.py` files each** — so `pip install juniper-canopy` yields a package whose dashboard cannot be
imported. True of every wheel back to **0.5.0**, and `juniper-ml[servers]` / `[all]` carry it.

Hidden for four releases because `Dockerfile:88` copies the whole `src/` tree in and `:98` sets
`PYTHONPATH=/app/src`, so the running service shadows site-packages entirely — the deployed
container is healthy and only the distributed artifact is broken. The `pip check` at `:48`
cannot see it: it validates dependency **metadata**, never importability
([[reference_vacuous_pass_check_class]]).

**Two instrument traps this cost, both worth carrying.** An f-string's **source** always contains
its brace expression, so reading a wheel cannot distinguish a live f-string from one that lost its
`f` prefix — the first draft "failed" canopy#614 on exactly that, and the honest test needs the
built app's `_inline_scripts`. And a **file-scoped** grep for
`Input(..."-training-state-store"...)` scores the three sibling callbacks that legitimately keep
that store as an Input, reporting canopy#618's shipped fix as absent; the check has to be scoped
to `update_loss_plot`'s own decorator ([[reference_check_unit_must_match_identity]]).

---

## juniper-canopy 0.8.1 — the packaging fix and how it was chosen (operational, 2026-09-15/17)

The instruments behind canopy#634 (`a1a0f13c`) and canopy#636, closing canopy#631. The headline
result is that **the obvious fix was wrong and failed silently**, and only building candidates and
opening their wheels showed it.

- **`2026-09-15_canopy_packaging_decision_inputs.py`** measures the three things the open decisions
  turned on: sdist coverage (**0 of 20** top-level modules, and it ships `pyproject.toml`, so
  `--no-binary` was never a workaround); the **transitive** closure of top-level imports by AST
  (12 from the shipped packages, 15 from `main`, union 19, only `adapter_validation` unreachable);
  and the re-parenting cost (711 import statements over 212 files — but **612 across 180 are
  tests**, and only 97 across 30 are library code). The one-hop list in the issue was **two short**:
  `csrf` and `ws_security` are reachable only through other modules, so a wheel built from it would
  still have failed. Use the AST, not a regex — this repo names its modules in prose constantly.
- **`2026-09-15_canopy_py_modules_build_trial.py`** builds each candidate `pyproject.toml` in its own
  copy of the tree and opens the resulting wheel. **`py-modules` alone builds successfully and ships
  0 of 19 modules** — exit 0, no warning — because it resolves against `package-dir`, which canopy
  never set. Adding `package-dir {"" = "src"}` then *fails outright* (`package directory
  'src/juniper_canopy' does not exist`) because `juniper_canopy/` sits at the repo root. Only the
  config with **both** an empty-string root and an explicit `juniper_canopy` entry ships 19/19 and
  keeps all five packages. Without build isolation config A errors instead of silently emptying the
  wheel, so **trial with isolation** — that is what CI does.
- **`2026-09-15_canopy_clean_install_import_matrix.py`** is what the publish guard's module list was
  drawn from: a real venv, `pip install` the wheel, `cd` out of the tree, import each candidate in a
  separate interpreter. Two lessons are baked into it. Classify a `ModuleNotFoundError` by whether
  the missing name belongs to an **optional extra** — the first draft called `demo_mode` (torch) and
  `backend.service_backend` (juniper_cascor_client) packaging defects. And run from a **writable**
  cwd, not `/`: canopy's logger creates its log directory relative to cwd at import, so `/` turns an
  ordinary side effect into a `PermissionError` and makes two importable modules look broken.
- **`2026-09-15_canopy_081_apply.py`** applies the whole 0.8.1 change to a sandbox so the set can be
  reviewed and built before anything is pushed, and **moves `[Unreleased]` into `[0.8.1]`** rather
  than inserting beside it — the ceremony renders the Release body from the `[<version>]` section
  alone, so anything left behind ships unmentioned.
- **`2026-09-17_canopy_changelog_merge_duplicate_categories.py`** repairs the shape that produced
  canopy#636, and refuses if the bullet count changes.

**The duplicate-category trap, which is now fixed in the train itself.** canopy#634 moved
`[Unreleased]` into `[0.8.1]` while canopy#633 and #635 were adding entries to `[Unreleased]`. Both
edit the top of the file; git resolved them cleanly; the section ended up with **`### Fixed`
twice**. It renders correctly on GitHub, so nothing flagged it — but
`ceremony.changelog_version_section` assigned rather than extended, so the **last** block won:
a section with three Fixed bullets rendered as **one**, and the published notes would have dropped
the packaging fix and the mount-500 fix. Both parsers now merge repeated headings
(`result.setdefault(cat, []).extend(...)`), pinned by two tests and mutation-checked per parser with
**`2026-09-17_mutate_duplicate_category_merge.py`**.

**Preview before `--execute`, every time.** `2026-09-12_ceremony_notes_preview.py` reported
`Fixed: 1` for a section that visibly contained three bullets. Nothing else in the pipeline would
have said a word, and a Release body cannot be re-cut.

---

## The 2026-09-10 canopy handoff re-evaluated: the relaunch, F-CANOPY-053, and two instrument repairs (operational, 2026-09-22)

- **`2026-09-22_fixture_grow.py`** grows the arc's cascor fixture by one window the arc's own way:
  re-stage `spirals/1000/0.25/1.5/2`, PATCH `max_hidden_units`, start, poll to a terminal FSM state, then
  snapshot. It refuses when cascor holds no network, and it flags a uuid change. **Why it exists:** a
  resumed snapshot restores the NETWORK, not the metrics buffer. Every "66 metrics rows" figure in the
  2026-09-10 handoff was accumulated in-process by three growth windows and died with the process on
  2026-09-19, so a relaunched stack serves a 52-unit network with an EMPTY history until a window runs.
- **`2026-09-22_state_store_consumer_roundtrip.py`** puts the WRITER's delivered values next to the
  RENDERER's held value. Per callback it records the round trip and the real re-request gap, both from
  the browser's own `request.timing`. It also censuses response bodies (carried / `no_update` /
  **unparsed**, with distinct values delivered) and reads the store in the renderer once a second, so
  "delivered N distinct values, renderer held 1" is a single run's direct measurement. Outputs are
  matched as whole Dash tokens: `metrics-panel-training-state-store.data` is a SUBSTRING of the
  candidate panel's store id. The positive control is built in, because the Training Metrics tab's
  store is read by the same method and does change. `--census-store` extends the census to any store
  (the F-CANOPY-038 re-measure). `--grow-to N` runs a growth window on the probe's own clock.
- **`2026-09-08_replay_block_redrive.py`** was repaired in place, fixing three defects:
  1. It now waits for the metrics store to fill before driving. The 09-11 run read it empty, watched it
     fill to 66 mid-run, and scored the index rows on the stale read.
  2. Each row is scored on the store length its OWN step saw.
  3. No row passes vacuously. On 09-22 step-back and start "passed" by expecting index 0 from an index
     that never left 0, and the slider "passed" because rc-slider moved its own value.
  It also gained a wire census of the server's `replay-state` responses (browser-side, not a server
  log), and `--park-metrics-poll`, which
  sets `metrics-store-interval.interval` to 1e9 ms. It uses `interval`, not `disabled`, because the
  CAN-000 gate and the canopy#614 strand watchdog both write `disabled`.
- **`e2e_f027_slots.py`** now also censuses `requested` and `executing`. Before, it named only `watched`
  and `prioritized`, so a callback that is never READY was invisible to it. It gained two options:
  `--focus SUBSTR`, which prints every queue's residency for matching callbacks, and
  `--click-id/--click-at`, which clicks a control mid-watch. This is what found F-CANOPY-048's block:
  `update_replay_ui` and the play label sat in `requested` in 6471 of 6471 samples, and
  `handle_replay_controls` in 4030 of 6471, from the click on.
- **`2026-09-22_f048_replay_cycle_cleanroom.py`**: canopy's replay-block shape with no canopy at all.
  It has two arms (the slider as an Input, which forms a cycle, or as State) and an optional
  always-pending callback. That callback is an `allow_duplicate` writer, whose `@hash` closure reaches
  nothing, so it locks the cycle by starving the breaker, not by feeding the block (Lane B's correction).
  **`2026-09-22_f048_laneB_variants.py`** holds Lane B's 30 discriminating runs.
  - The cycle alone does NOT lock: NO-DEADLOCK in 2/2.
  - The cycle plus the feeder locks 3/3 and the acyclic arm is live 3/3: FEEDER-CYCLE-LOCK under
    rule v2. The renderer's circular-dependency breaker (`dash_renderer.dev.js` ~:3048-3068) fires
    only when NOTHING else is pending.
  - Its first feeder run is recorded as INDETERMINATE under a MIS-SPECIFIED v1 rule. "Toggled" tested
    "shows ⏸" while the mount-time run had already set ⏸. That run was not re-scored; v2 was fixed
    before a fresh run.
- **`2026-09-22_canopy_idle_cpu_profile.py`**: a CDP sampling profile of the page's main thread, by
  self time and by INCLUSIVE time, with columns so minified frames can be located. At idle the thread
  is 0.1% idle, and 85% of self time is inside `dash_renderer.min.js`.
- **`2026-09-22_headless_gpu_renderer_check.py`**: the unmasked WebGL renderer per launch
  configuration. The arc's default launch renders through SwiftShader. `JUNIPER_E2E_BROWSER_GPU=1`
  (read by `e2e_w3_params_driver.open_dashboard`, which every seg17-derived driver shares) opts into
  the host GPU.
- **The four `2026-09-22_laneA*` scripts** are the independent Lane A validators' own instruments for
  F-CANOPY-053, F-CANOPY-038 and M-METRICS-18. By design each shares no code with the orchestrator's
  instruments, so treat them as re-derivations, not as tools to extend.

## F-CANOPY-054: the replay block moved clientside (operational, 2026-09-23)

See the E2E ledger's Phase 8 (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`).

- **`2026-09-23_f054_replay_tick_cleanroom.py`** runs four shapes of canopy's replay block with no canopy
  (dash 4.2.0), with a server-latency knob and an always-pending `running=` feeder:
  - `current`: canopy main 2f973ca2;
  - `cs_tick`: only the tick clientside, the direction Phase 7 recorded;
  - `cs_all`: canopy#670;
  - `cs_all_input`: canopy#670 with the store as an Input.

  **The verdict reads the Redux store, not the DOM.** In `cs_tick` every server refresh is evicted and
  the DOM freezes on a stale "▶ 0 / 119" that looks exactly like a pause. **Keep its port range clear of
  the trio's:** its first scored run counted up from 8201 and landed its second arm on the LIVE cascor
  at 8202. It now starts at 18501 and skips ports in use (`_free_port`).
- **`2026-09-23_f054_live_pause_check.py`**: the same rule against a live canopy leg. A Redux
  subscription records every write of the replay state's `(mode, current_index)` and of
  `replay-interval.disabled`, and resolves the path through `paths.strs`, which costs no layout walk per
  store change on a page whose main thread is ~0.1% idle. F-CANOPY-054 is a SEQUENCE (a `paused` write,
  then a late `playing` write), which a single read `settle` seconds after the click cannot see.
  - Run it against a parent leg as a negative control first. On `2f973ca2` it scored F054-UNDONE 3/3.
- **`2026-09-23_f054_mutation_check.py`** applies textual mutations, one at a time, to canopy#670's
  `metrics_panel.py` and runs the two replay test files: nine with `--set v1`, 18 with `--set v2`.
  - Bytecode is off, and `__pycache__` entries are cleared per run.
  - It restores the file byte-for-byte and verifies by sha256.
  - A mutation whose search text is absent is NOT-APPLIED, never "caught".
  - **By default every test runs, and the verdict says which kind of test caught it.** `TestSourceBackstop`
    pins source TEXT, so a mutation that deletes pinned text is caught whatever the behaviour. Under `-x`,
    four v2 mutations were first caught by that backstop, which proves only that the text is pinned.
    CAUGHT-BY-BEHAVIOUR needs a failing test outside the backstop. `--fail-fast` reproduces the old scoring.
- **`2026-09-23_f054_pdup_cleanroom_v1_v2.py`** is Lane B2's contention clean room, adapted.
  - It needs no ports: Playwright route interception serves Dash through Flask's test client.
  - It runs K guarded pollers, and v1 and v2 paired, each read from a git OBJECT (`git show <ref>:path`,
    or `:path` for the index), so a concurrent mutation check cannot leak into it.
  - A trial is RECOVERED when the click's request was replaced in `prioritized` and the pause still
    applied: that is the only path round 1's defect exercises.
  - Its comment's `'13'` against `'11'` priority story is refuted (see the next bullet), but the drop
    counts stand.
- **dash 4.2.0's priority is INERT.** `getPriority` returns `"0"` for every callback: its first pass is
  `filter(c => touched)` (`:1598`, `ramda/es/filter.js`), which drops its own start callback. So
  `prioritized` is FIFO. Lane A2 found it (`2026-09-23_f054_r2_laneA2_priority_probe.py`).
- **`2026-09-23_f054_v2_live_check.py`** drives every click DURING PLAYBACK on a live leg: pauses at 1x
  and 4x, steps and seeks. It records the pool at each click and whether the click was seen waiting,
  running or recovered.
- **`2026-09-23_matrix_f054_rows.py`** records the seven replay rows' verdicts on `c0530279`. It follows
  `2026-09-22_matrix_f053_rows.py`: it refuses a second run and refuses a row whose verdict is not the one
  it was written against. **`2026-09-23_matrix_f054_rows_v2.py`** then moves them to `85415f3c`, the revised
  fix, under the same two guards.
- **`2026-09-23_archive_consensus_reports_by_round.py`** archives validator reports per ROUND.
  - A subagent resumed with `SendMessage` appends to the same transcript, so "its last text" (the
    2026-09-22 archiver's rule) silently becomes the round-2 progress line.
  - This one splits each transcript at the round-2 brief (`--marker`).
- **`2026-09-23_f054_r2_laneA2_*.py`**: Lane A2's independent round-2 harness (slot contention, a post-hoc
  arm and the priority probe), built from the renderer source before it read any other lane.

## The idle dispatch cuts and the top status bar (operational, 2026-09-23)

The ledger's Phase 8 again.

- **`2026-09-23_canopy_interval_census.py`**: every `dcc.Interval` in the built app, with its steady-state
  tick rate and its consumers. A finite `max_intervals` counts as 0 in the steady state. The first version
  counted `params-init-interval` (`max_intervals=1`) as perpetual.
- **`2026-09-23_canopy_timer_park_ab.py`**: an in-page A/B that parks candidate timers
  (`setProps({disabled: true})`) in alternating windows, BEFORE any code change.
  - Run it in both orders (`--order forward|reverse`). The first run's baseline was still settling.
  - "Store updates/s" is not a cost measure on a saturated page: it ROSE when a timer was parked, because
    freed main-thread time goes to applying responses.
- **`2026-09-23_idle_cuts_live_check.py`**: the cuts leg against a control leg, in alternating windows.
  It checks the structure, the session path (a `replay-player-session` write must enable the drain) and
  the latency.
- **`2026-09-23_status_bar_apply_census.py`**: does `update_unified_status_bar` ever APPLY a response?
  - It counts wire requests and responses, renderer `watched`/`executed` entries, and store changes.
  - `--period-ms` adds the discriminating arm: the lane's period is set above the latency on the same
    page, and the bar then applies.
  - A bar showing exactly its layout defaults ("Stopped", "0", an empty latency) has never applied
    anything.

## F-CANOPY-055's first fix, its review, and the Phase 9 rescue from tmpfs (operational, 2026-09-23/24)

The ledger's Phase 9.

- **`2026-09-23_f055_f025_allow_arm_demo_drive.py`**: F-CANOPY-025's Live Switch allow and deny arms on DEMO
  legs. A demo leg runs its own training, so the trio's cascor is never touched. It needs
  `CANOPY_VERIFY_DEMO_MODE=1` on `2026-09-04_canopy_verify_instance.bash`.
  - It does NOT discriminate the fix from its parent: the allow arm landed on both. The drive records no
    latency, so "a demo page is fast enough for the old lane" is unmeasured.
  - Its BAR verdict is weak, because one apply before its clock starts satisfies it. The per-sample
    `step_text` is the stronger evidence.
- **`2026-09-23_status_bar_apply_census.py`** (Phase 8's tool) gained the first fix's predictions.
  - Size a window to the lane's cadence. The guarded lane self-clocked at ~7.5 s per applied response, so a
    60 s window fell under the 10-response VOID floor.
  - Note the units: `watched`/`executed` count renderer callback objects and `delivered` counts HTTP
    responses. They differ by one or two at a window's edges.
- **`2026-09-23_f055_r1_laneB_*`**: round 1 Lane B's scripts, archived verbatim with a provenance header.
  - `_repro.py` is the synthetic Dash app with the first fix's exact wiring on the real renderer, the
    F-CANOPY-058 repro. `_cascade_sim.py`, `_no_interaction_sim.js` and `_watchdog_alias_sim.js` are its
    models.
  - `2026-09-23_cuts_r1_laneB_probe_deps.py` is the idle cuts' single-writer probe.
- **`2026-09-24_archive_phase9_tmpfs_evidence.py`** copies the files Phase 9's claims rest on out of the
  authoring session's tmpfs scratchpad.
  - Raw outputs go to `reports/e2e-canopy-2026-09-02/phase9-scratch/`, which has an index README; the
    scripts go here.
  - It refuses to overwrite a file, and refuses a source that contains a secret-shaped string.
- **`2026-09-24_host_session_activity_window.py`**: which Claude Code sessions on this host made a tool call in
  a time window, and which hit a rate limit.
  - It answers whether any session made a tool call in a window. It cannot see a process launched BEFORE the
    window, which keeps acting after its session goes quiet; the launch scan below covers that.
  - It prints ids, counts and timestamps, never message text. It cannot see the GitHub UI, other hosts, cloud
    sessions or automations.
- **`2026-09-24_f058_trigger_census.py`**: F-CANOPY-058's live confirmation. **Refuted before its first run**
  by round 2 of the ledger's validation: do not run it as written. Its docstring lists the four defects and
  the fix direction.
  - It meant to count per-request EVICTIONS: a request that leaves the renderer's `watched` list without
    entering `executed`. But an answer with no props leaves `executed` inside the same dispatch that put it
    there, so a store subscriber never sees it there and scores it evicted.
  - On the idle trio the feeder answers `no_update`. That is HTTP 200 with an empty `response`, not a 204 (dash
    4.2.0's `has_output`), and it applies nothing, so an applies count cannot tell a healthy lane from a
    stalled one either.
  - Records are keyed by `executionPromise`. The observer copies a resolved request into `executed`, so keying
    by object identity would score every applied request as evicted.
  - It drives five triggers. It simulates an Apply through the `apply-in-flight` Store, because a real Apply
    PATCHes the trio's cascor.
- **`2026-09-24_phase9_ledger_round1_corrections.py`**: the ledger's round-1 fix pass, as exact substitutions
  that each must match once. It does not reproduce the whole pass: one bullet of the consensus record was
  applied by hand, so a replay onto a moved `main` must re-apply that bullet.
- **`2026-09-24_phase9_ledger_round2_corrections.py`** to **`…_round10_corrections.py`**: the round-2 to
  round-9 fix passes, and round 10's record of the review's termination, with no hand edit to the ledger.
- **`2026-09-24_owner_answer_extract.py`**: prints chosen records of a session transcript, by line number, with
  e-mail addresses and the token shapes its docstring lists redacted; any other shape is printed. Round 5 used
  it for the owner's answer to the sweeper question.
- **`2026-09-24_secret_shape_check.py`**: tests the secret and e-mail shapes of the answer extractor, the launch
  scan, the round-2 archive tool and the report archiver (`2026-09-23_archive_consensus_reports_by_round.py`,
  whose `--allow-shape` gate it also tests) against constructed fake values, both ways, printing labels only.
  Round 6 widened the first three after Lane R6-B found `sk-ant-…` keys passing the extractor. Round 7 set the
  bare `sk-` floor to 20 in all four (round 6 had raised the extractor's to 32; the other three had used 32 from
  the start) and scoped the archiver's allows to one agent's report (Lane R7-B). Round 8 added forms to the
  archiver's key-material refusal after Lanes R8-A and R8-B passed fake keys through it, but replaced round 7's
  form in doing so; round 9 kept that form as well (Lane R9-B). It now refuses any PEM END line; a PEM header
  followed by whitespace and 20 or more base64 characters; any base64 run of 40 or more characters within 400
  characters after a PEM header; and any age identity with a body.
- **`2026-09-24_merge_command_launch_scan.py`**: the Claude Code tool calls on this host, in a window, whose
  command line matches a pattern of commands that can ready, arm, merge, update-branch or re-run a PR, with
  each call's background flag.
  - It answers what the activity window cannot: a process launched BEFORE a window keeps acting after its
    session is rate-limited, and round 2 found one that did.
  - It is a PATTERN, not a proof. Rounds 3 and 4 found forms the first version missed (a converge driver's
    update-branch loop, `gh pr -R <repo> <verb>`, GraphQL `updatePullRequestBranch`, and more); a script run
    by a path the pattern does not name is still outside it, and its docstring names the forms it still
    misses.
  - It prints timestamps, session ids and the command's first 220 characters, with token shapes and e-mail
    addresses redacted.
- **`2026-09-24_archive_phase9_tmpfs_evidence_round2.py`**: the rest of Phase 9's tmpfs evidence, from two
  sessions' scratchpads, including round 2's lanes. Same rules as the first pass, plus a refusal of any file
  that holds an e-mail address other than a `noreply` one or the Codecov uploader's public key address
  (`@codecov.io`), which CI logs print.
- **`2026-09-24_push_phase9_signed_groups.py`**: uploads a local branch's change to its GitHub branch as signed
  commits in groups of at most 250 KB, except the ledger, which goes alone and last at about 780 KB (about 1 MB
  encoded), each pinned to the one before, then
  compares every uploaded blob with the local one. A large payload can return HTTP 499 or 502 and still land,
  so it re-reads the ref before any retry.
- **`2026-09-23_cuts_r1_laneB_probe_*`, `2026-09-24_ledger_r1_laneB1_*`, `2026-09-24_ledger_r2_laneB_*` and
  `2026-09-24_ledger_r2_laneF_*`**: review lanes' scripts, archived verbatim under a provenance header naming
  the report that cites them.
- **`2026-09-24_idle_cuts_check_mutants.py`**: the canopy follow-up to #676. Ten mutants of the
  `test_idle_dispatch_cuts.py` CLASS check; each must fail exactly its named test.

---

## What does NOT belong here

- Scripts that are part of a documented build / test / release flow → `util/` proper or `scripts/`.
- Scripts called by CI workflows → `util/` proper (CI should never invoke `util/ad-hoc/`).
- Tests → `tests/`.
- Generated artifacts (lockfiles, dep docs, build output) → wherever the build tooling expects.
