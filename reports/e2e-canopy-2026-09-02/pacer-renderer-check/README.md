# Real-renderer check of canopy's request/ack pacer (F-CANOPY-055, -058, -068) — 2026-10-08

Instrument: `util/ad-hoc/2026-10-08_f055_f058_f068_pacer_renderer_check.py` (its docstring holds the phases, the
verdict rule and the expectations, fixed before the first run). Canopy code under test: branch
`fix/f055-f058-f068-request-ack-pacer`, working tree on `3029d07d`, imported through `--canopy-src`, so the
pacer JavaScript is canopy's own `poll_pacer_js`. dash 4.2.0 (JuniperCanopy1), headless Chromium (Playwright
1.59.0). Round trips drawn per request from a seeded normal around 3,600 ms (sd 450, clipped to 888–5,345 ms,
Phase 11's measured range). The measured median gaps between applied responses were 4,153 ms (pacer) and
4,618 ms (guard), against canopy `main`'s ~4.9 s in Phase 11.

**The first two runs (17:40–17:54 CDT) predate commit 1 of canopy#731.** They imported the uncommitted working
tree, whose pacer is commit 1's by this session's edit history; its identity was not recorded by hash. That pacer
had a fixed 30 s stale bound and let `reason: "stale"` take precedence over a mode change. Commits 2 and 3 changed
both. The run on the final pacer has its own section below.

Both arms ran concurrently, 17:40–17:54 CDT, beside two canopy unit suites and other sessions' work. Load was
not sampled during the runs; read at 18:17 the host's 1/5/15-minute load averages were 32.7 / 29.0 / 21.9 on 16
cores.

| file | what |
|---|---|
| `20261008T174112_pacer_run.json` / `_score.json` | the fix: 10 idle minutes, 3 rounds of the four triggers, one stranded request (45 s) |
| `20261008T174018_guard_run.json` / `_score.json` | the control: canopy#613's `running=` guard plus the strand watchdog (verbatim logic from `main` `3029d07d`), same app, same draw, no strand phase |
| `pacer_stdout.json`, `guard_stdout.json` | each run's stdout as first scored (see the correction below) |

## Results

| | pacer (fix) | guard (control) |
|---|---|---|
| requests / completed | 172 / 171 | 198 / 197 |
| evicted (excluding the stranded request) | **0** | **88** (70 in idle) |
| requests made while another was in flight (excluding over the stranded one) | 0 | 96 |
| watchdog fires (idle) | — (no watchdog) | 4 |
| stale re-issues in idle | 0 | — |
| triggers followed by an applied response | 12 of 12 | 2 of 12 |
| median gap between applied responses, idle | 4,153 ms | 4,618 ms |
| stranded request | re-issued 30,995 ms after it began; the lane applied 3,968 ms after the re-issue | not run |
| verdict | **PASS** | **FAIL** (as expected) |

The pacer's three display-mode changes were issued as `reason: "extra"` requests, each after the fetch in flight
was acknowledged.

The stranded request (k=166) is excluded from both counts by the scorer's design. The stale re-issue (k=167)
evicts it deliberately, and k=167–170 began while it was still open on the server: that is the recovery path, not
a defect. The guard arm has no ack-derived correction, so its 88 may include recorder coalescing; its 96 requests
made in flight do not depend on the recorder.

## The final pacer: `2689a207`, 20:04–20:16 CDT

The same instrument and settings were run against the branch at its final pacer code: commit 3's pacer
JavaScript, which commits 4 and 5 left unchanged. The host's 1-minute load average was 9.9 before the run and 5.9
after it. Files: `20261008T201631_pacer_run.json` / `_score.json` and `pacer_final_stdout.json`. The instrument now
logs each request's `stale` flag, and derives acks and stale re-issues from it.

- **PASS**: 172 requests, 0 evicted.
- Idle: 145 requests, 0 stale, 0 made in flight, median applied gap 4,161 ms. The first request after mount was
  `reason: "extra"`, by design: the seq-0 request records no display mode.
- Triggers: 12 of 12 followed by an applied response, with the three mode changes as `extra`.
- Strand: re-issued 30,999 ms after the stranded request began, and the lane applied 3,969 ms later.
- One response, k=118, was ack-derived; the recorder coalescing described below recurred once.

## Correction to the first scoring (made before any result was reported)

The first score of the pacer run read one eviction in idle, k=109, with no request made while another was in
flight. The scorer read application only from the page's recording callback (a clientside callback whose Input
is the data store). The response for k=109 ended at 443,973 ms and the pacer issued the next request 10 ms
later, the shortest such gap in the run (next shortest: 19 ms, recorded). That request's req_seq, 109, proves
the pacer read ack 108, and the feeder writes the ack and the data in one response, so k=109 applied. The
recorder was queued behind the new feeder request, which claims the data store, and its two pending runs
collapsed into one. The scorer now also derives application from the acks (`applied_by_ack_only`) and reports
it separately. Only k=109 is ack-derived. `pacer_stdout.json` keeps the first score.

## What this does not show

- canopy itself: this is a scratch app with canopy's wiring and canopy's pacer source. The live census on a leg
  serving the branch is in `../pacer-live/`.
- any browser but headless Chromium, or a renderer but dash 4.2.0 (canopy's lock ships 4.4.1).
