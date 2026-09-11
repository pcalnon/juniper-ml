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
  the branch's current head. Built to extend juniper-cascor#632 after the first fix proved incomplete.
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

## What does NOT belong here

- Scripts that are part of a documented build / test / release flow → `util/` proper or `scripts/`.
- Scripts called by CI workflows → `util/` proper (CI should never invoke `util/ad-hoc/`).
- Tests → `tests/`.
- Generated artifacts (lockfiles, dep docs, build output) → wherever the build tooling expects.
