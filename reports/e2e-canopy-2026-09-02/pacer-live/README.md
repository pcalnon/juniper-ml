# Live checks of canopy#731's request/ack pacer (F-CANOPY-055, -058, -068) — 2026-10-08

These are verify legs on `:8052`, run with `util/ad-hoc/2026-09-04_canopy_verify_instance.bash`, each serving canopy
branch `fix/f055-f058-f068-request-ack-pacer` from worktree
`juniper-canopy--fix--f055-f058-f068-request-ack-pacer--20261008-1713--3029d07d`. Each leg read the trio's cascor
`:8202` and data `:8101` and wrote neither. `:8051` was never touched. The dash 4.2.0 renderer (JuniperCanopy1)
drove one headless Chromium page per run.

## What each run served

The legs for runs 1–3 served an **uncommitted** working tree, so their `/v1/health` reported the base commit
`3029d07d`, not the code under test.

| run | when (CDT) | served code | how it is known |
|---|---|---|---|
| F-055 census, run 1, run 2 | 17:43–18:47 | the tree before commit 1 (its pacer is commit 1's) | this session's edit history; **not recorded by hash** |
| F-055 census (v2), run 3 | 19:02–19:33 | commit 2's tree (`b344ff97`'s content) | the page carried `__junPollPacerLastUnacked`, which only commit 2 has |
| F-055 census (final), run 4 | 19:33–20:04 | **`2689a207`** | `/v1/health` `git_sha` (`2026-10-08_final_leg_health_2689a207.json`) and the captured `_dash-dependencies` (`2026-10-08_final_leg_dash_dependencies_2689a207.json`: no `running=` guard; each feeder's only Input is its request store) |

`65ead946` (commit 5, a CodeQL fix) has a callback graph identical to that capture: 179 callbacks, symmetric
difference 0 (`util/ad-hoc/2026-10-08_compare_canopy_wiring.py`). Its pacer JavaScript is unchanged from commit 3's.

Each run's console log is beside its JSON as `*.log.txt`; the repository ignores `*.log`.

## F-058 census v2

The census is run unchanged through `util/ad-hoc/2026-10-08_f058_census_v2_on_pacer_leg.py`, which only sets the
census's feeder key to the paced feeder's multi-output key.

| run | file | evicted / resolved (scored windows) | whole transcript (answered / evicted) | median cycle by window | in flight from `watched`: median / max | 1-min load, read after |
|---|---|---|---|---|---|---|
| 1 | `f058-census-run1.json` | 0 / 170 | 188 / 0 | 6.0–15.5 s | 6.2 / 16.4 s | 32.7 |
| 2 | `f058-census-run2.json` | 0 / 149 | 164 / 0 | 8.0–12.4 s | 7.9 / 17.3 s | 13.8 |
| 3 | `f058-census-run3-v2.json` | 0 / 240 | 256 / 0 | 5.1–6.9 s | 4.8 / 9.5 s | 5.4 |
| 4 | `f058-census-run4-final.json` | 0 / 286 | 304 / 0 | 5.0–6.3 s | 4.0 / 6.7 s | 9.9 |

Totals: **0 evicted of 912 resolved** (845 inside the scored windows), and no watchdog fire, because there is
none. For comparison, Phase 11 measured 29 of 611 evicted on canopy `main` at 1-minute load averages of 1.9–4.6.

- **Load.** Each figure is a single `uptime` reading taken after the run, not a sample over it. Run 1's 32.7 /
  29.0 / 21.9 and run 2's 13.8 / 16.0 / 19.6 came from other sessions' work and canopy unit suites. Cycles and
  in-flight times under that load are not comparable with Phase 11's. Run 4, at about 5–10, is the closest:
  a ~5.0 s cycle against Phase 11's 4.9 s.
- **Triggers.** T-gate, T-tab and T-mode read NO-EFFECT, as the fix predicts. Their TOOK predicates look for a
  gate write of `false` onto a disabled lane, or a second feeder request while one is open, and the pacer leaves
  neither.
- **T-apply did not test a mid-request Apply release.** Under the clamp the pacer issues nothing, so the census
  found no open request. The clamp was released about 58–60 s after it was set (e.g. run 1: 678,001 → 736,440 ms),
  which fits E-3's 60 s force-release (inferred from the timing; no log records it). The census's own release
  then landed on an enabled lane.

## F-055 status-bar census

Instrument: `util/ad-hoc/2026-09-23_status_bar_apply_census.py`, rule unchanged: 45 s settle, then a 60 s window.

| file | served | verdict | watched / executed | latency changes | wire latency median |
|---|---|---|---|---|---|
| `…_8052_pacer.json` | tree before commit 1 | **APPLIES** | 56 / 56 | 42 | 0.16 s |
| `…_8052_pacer_v2.json` | commit 2's tree | **VOID** (9 responses, under the floor of 10) | 9 / 9 | 8 | 2.17 s |
| `…_8052_final_2689a207.json` | `2689a207` | **APPLIES** | 12 / 11 (one was in flight at the end) | 11 | 0.74 s |
| `…_8053_main_control.json` | a `git archive` of canopy `origin/main` `3029d07d` on `:8053` (`git_sha` null; main by assertion) | **NEVER-APPLIES** | 34 / 0 | 0 | 1.57 s |

On every pacer leg the bar showed the server's state, `Completed — early stopped` at epoch 76. On the control it
held its layout defaults, `Stopped` / `0`, as on 2026-09-23.

## What this does not show

- A run of live training. Every page was on an idle trio, so the WS short-circuit (`ws_live`) and the full-history
  views went unexercised.
- The scored mid-request triggers of item 25. The census's triggers are scripted from Playwright and landed late
  (Phase 11, Instruments), and T-apply cannot reach a request under the clamp.
- The cost the PR discloses: a non-OK reply or a network failure waits out the stale bound. No run injected one
  on a live leg; the real-renderer check strands one request (`../pacer-renderer-check/`).
