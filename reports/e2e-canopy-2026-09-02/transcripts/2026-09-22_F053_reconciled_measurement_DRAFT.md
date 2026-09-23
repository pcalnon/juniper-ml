# F-CANOPY-053 — reconciled Lane A measurement (DRAFT for Lane B review, 2026-09-22)

This is the object of the Lane B review under
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2/§4. It is not
yet in the ledger (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`). All paths below
are relative to the juniper-ml repo root unless stated otherwise.

## Proposed finding

**F-CANOPY-053 — the Candidate Metrics panel's training-state writer never applies after mount, so its
status badge, phase, pool size, epoch progress, pool info and pool-history cards show their mount/empty
defaults through a live candidate phase. It is F-CANOPY-035's mechanism on a third store (proposed P1,
canopy repo).**

`fetch_training_state` (juniper-canopy `src/frontend/components/candidate_metrics_panel.py:247-268` on
`main` 9bffaba1) writes `candidate-metrics-panel-training-state-store.data` and `-pool-history-store.data`
off its own `dcc.Interval` `candidate-metrics-panel-update-interval`. That interval is nominally 1000 ms
and delivers one tick every 1.3–3.8 s. The interval is dedicated to this callback, and the CAN-000 gate
is the only writer of its `disabled` prop.

## Observations (every one names its artifact under `reports/e2e-canopy-2026-09-02/transcripts/`)

| source | entry point | runs | result |
|---|---|---|---|
| orchestrator | wire timing + response census + renderer read (`paths.strs`), SwiftShader | 2 idle | writer 26 / 27 requests, ~26–29 ms round trip, every response carries the store (27/27 distinct values). The renderer held ONE value, a timestamp from page load, across 25 and 27 reads. The consumers fired once each, at mount. `2026-09-22_consumer_rt_candidates_idle.json`, `…_idle_run2.json` |
| orchestrator | same + DOM vs `/api/state`, one growth window 54→58, SwiftShader | 1 | 34 delivered, 34 distinct; renderer 1 of 20 reads; the DOM badge was only ever `Inactive` while the server said `Inactive`/`Training`. `…_candidates_growth.json`, `…_growth_grow_58.json` |
| orchestrator | same, **host GPU** (RTX 2080 via ANGLE/Vulkan; `util/ad-hoc/2026-09-22_headless_gpu_renderer_check.py`) | 1 idle | 24 delivered, 24 distinct; renderer held **no** timestamped value (the mount default) in 14 reads; zero consumer requests. `…_candidates_idle_GPU.json` |
| Lane A1 | own Playwright script, DOM against `/api/state`, one growth window 58→62 | 1 (+2 idle dry runs) | Badge / phase / pool size read `Inactive` / `Idle` / `0` in all 32 samples, and an in-page change recorder saw no change. The server said `Training` in 13 of 106 polls and pool size 8 in every one. Positive control: a click-driven toggle changed 5 of 5 times, 9–15 s late. The top status bar ALSO never updated. `2026-09-22_laneA1_candidate_panel_dom.json`, `…_laneA1_grow_62.json` |
| Lane A2 | CDP wire + response bodies, renderer read by a layout walk that never uses `paths` and by the React fiber, idle | 3 | 27 / 25 / 30 writer requests, all carrying the store, **0 applied**; the renderer held the mount default `{}`. `fetch()` → parsed JSON took 3.2–5.5 s against a ~30 ms network leg, with the main thread 66–75% busy in long tasks. Positive control `stream-health-store`: 8 of 12 applied (idle run 3). `latency-display` held 1 value while 6–10 were delivered. `2026-09-22_laneA2_cdp_store_apply_run{1,2,3}*.json` |
| Lane A3 | source reading + ONE variable (the interval's `interval` prop via `setProps`), verdict rule hashed before run 1 | 3 | **PERIOD-BOUND ×3**. Writes landed / issued at 1000 ms: 0/74, 0/67, 0/84. At 4000 ms: 0/13, 1/13, 4/13. At 10000 ms: 8/8, 7/8, 8/8. Returning to 1000 ms stops landing again. With a tick inside the processing window, 2 of 479 landed; with no tick inside it, 36 of 36 landed. Page-side processing took 4.3–7.7 s (median) after the network finished. `2026-09-22_laneA3_candidate_tick_period_run{1,2,3}*.json` |
| orchestrator | CDP CPU profile, GPU browser, idle, Training Metrics tab, 20 s | 1 | 0.1% idle; 85% of self time in `dash_renderer.min.js`, 9% react-dom. The `requestedCallbacks` observer (readiness, dedup, prune) is 45% of the total inclusively. `2026-09-22_idle_cpu_profile_training_metrics.json` |

**Reconciled statement.** No periodic write from this callback applies in the renderer while its tick is
faster than the page's processing lag. At the delivered ~0.5 Hz that is none: 0 of 225 across A3's three
1000 ms phases, and 0 across every other run's window. At most the page-load write lands; one run in five
held it. The panel therefore shows mount or empty-state defaults, not stale data: pool size "0" against a
server value of 8 even at idle.

**Mechanism (source + one-variable test).** This is the renderer's own-tick self-eviction.
`getUniqueIdentifier` (`dash_renderer.dev.js:1715-1726`) makes every invocation of the callback one
identity. The next tick's `requested` entry evicts the in-flight `watched` entry (`:3024-3027`, the
removal dispatched at `:3151`), and the late response is discarded at `:2699`. A3 checked the enclosing
functions.

**Dissent resolved.**
1. "One distinct timestamp" (orchestrator) against "`{}`, zero applied" (A2, A3, the GPU run): both
   happened. The load-time write landed in the orchestrator's first two sessions and in no other.
2. The dev-bundle line `:2698` is `:2699`. The page serves the MINIFIED bundle, which has the same logic.

**What the evidence cannot support.**
- That a real user's browser shows it. All runs are headless Chromium, although the GPU run removes the
  software-GL objection.
- That host load is irrelevant. Load average was 5–10 on 16 cores during the runs, with up to four
  concurrent headless browsers and a canopy pytest run.
- That `running=` fixes it. That is predicted, not tested.
- Any claim about WHY the page-side lag is 4–8 s beyond the CPU profile's location of the time.

## Proposed dispositions (the things Lane B should attack)

1. File F-CANOPY-053 as a NEW finding at **P1**. The precedent is F-035 and F-052, each filed as its own
   finding despite F-CANOPY-004's accepted freshness contract, because a PERMANENT never-apply violates
   that contract (3–16 s interaction-triggered, 20–40 s fresh-session).
2. Overturn the 2026-09-11 sibling sweep's disposition. The ledger's Phase 6 "the sibling sweep, done"
   recorded the three consumers as "a latent risk, not an open defect … they survive on a margin". The
   consumers do not survive on a margin: their writer's responses never apply.
3. Matrix: M-CANDIDATES-01/-02/-03/-04/-06 read "PASS (re-validated @ f9defb4)". On current main they
   render only mount defaults while the server moves, so they become **FAIL on F-CANOPY-053**. A leg at
   f9defb4 re-measured on 2026-09-22 applied 3 of 36 writes at idle with 4.8 s round trips and 25
   overlaps (`…_candidates_idle_baseline_f9defb4.json`), so the historical PASS was probably scored on
   mount content, not liveness.
4. Fix at the trigger, per canopy#613: `running=[(Output(<interval>,"disabled"), True, False)]` on
   `fetch_training_state`, plus canopy#614's strand watchdog extended to this interval. The canopy PR is
   in preparation.
5. Record, do not file: the top status bar (the fast lane's `update_unified_status_bar`) also never
   updated in A1's windows, and A2 saw `latency-display` hold 1 of 6–10 delivered values. That is
   F-CANOPY-004's accepted class, now observed violating its own contract (no population in 100 s against
   20–40 s). The disposition belongs to the owner.
