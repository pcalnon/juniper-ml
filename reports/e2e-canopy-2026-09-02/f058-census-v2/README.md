# F-CANOPY-058 census v2 — the live runs of 2026-10-05

The census that confirmed F-CANOPY-058 on canopy `main` and found F-CANOPY-068, run twice. The reviewed reading
of both runs is the ledger's Phase 11, in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`.
Where the first run session's own note (`2026-10-05_RESULTS.md`, below) and the ledger's Phase 11 disagree, the
ledger's Phase 11 governs; the four corrections are listed at the end of this file.

The first run was made by the P2 Lane A session in juniper-ml worktree `clever-juggling-spring`, then kept
outside the repo in `backups/2026-10-05_f058_census_v2_final/`; its files were copied here byte for byte on
2026-10-05, and the six census scripts to `util/ad-hoc/2026-10-04_f058_census_v2_*.py`. The second run was made
the same day by the session in worktree `dreamy-fluttering-kite`, with those scripts unchanged, on current canopy
`main` `c7876f5a`; its files are in `run2/`.

## What was run (the first run; the second differs only as noted)

- A verify leg on `:8052` (`util/ad-hoc/2026-09-04_canopy_verify_instance.bash`), serving canopy `main`
  `60ae1870` from a tarball tree; the commit it served was read back off its `/v1/health`. It read the trio's
  cascor `:8202` and data `:8101` and wrote neither. cascor was idle. `:8051` was never touched.
- One headless Chromium page, driven by `util/ad-hoc/2026-10-04_f058_census_v2_live.py`, with the shim
  `…_shim.py` installed before the page's own scripts. Settle 45 s, baseline 240 s, four triggers of 180 s each,
  idle 600 s: about 25 minutes, 2026-10-05 10:56–11:21Z.
- Before it, the synthetic known-answer check `…_synth_check.py` on `…_synth_app.py`: 6 of 6.
- The second run: the same leg script and port, serving a tarball tree of canopy `main` `c7876f5a`, fetched
  through the GitHub API (`gh api repos/pcalnon/juniper-canopy/tarball/<sha>`), with `JUNIPER_CANOPY_GIT_SHA`
  set, 2026-10-05 21:11–21:36Z. The trio's three processes, started 2026-09-22, were still the same after it,
  by their pids and start times, read then; no file here records that reading.

## Files

| file | what it is |
|---|---|
| `2026-10-05_census_live.json` | the transcript: the shim's raw logs (`raw.req`, `raw.lane`, `raw.fires`, `raw.gate`), the triggers and the window verdicts |
| `2026-10-05_census_live.log` | the live driver's console output (wall clock is the host's CDT); `exit=0` |
| `2026-10-05_canopy-8052.log` | the leg's canopy log: one page connection, 05:56:14 to 06:21:29 CDT, no restart; one metrics frame, cascor's `initial_metrics` burst at the leg's own connection (05:56:00), before the page connected; 62 control-stream refusals by cascor's origin allowlist, which the leg script documents as expected |
| `2026-10-05_host_load.txt` | load average at the start and the end (UTC) |
| `2026-10-05_synth_check.jsonl` | the synthetic check's output, 6 of 6, under the census's final file names |
| `2026-10-05_RESULTS.md` | the first run session's note, verbatim; NOT consensus-validated |
| `run2/2026-10-05_census_live.json` | the second run's transcript, same format |
| `run2/2026-10-05_census_live.log` | the second run's console output (CDT); `exit=0` |
| `run2/2026-10-05_canopy-8052.log` | the second leg's canopy log, copied before the leg was stopped: one page connection, 16:11:19 to 16:36:31 CDT, no restart; one metrics frame, cascor's `initial_metrics` burst at the leg's own connection (16:11:02), before the page connected; 55 control-stream refusals |
| `run2/2026-10-05_host_load.txt` | load average at the second run's start and end (UTC) |

The `.log` files are force-added: `.gitignore` excludes `*.log`.

## Replaying the reading (no browser, plain `python3`)

```bash
T=reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json
python3 util/ad-hoc/2026-10-04_f058_census_v2_analyze.py "$T"            # 307 requests, 18 evicted in runs of 1, 2, 11, 4; 13 fires
python3 util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py "$T"      # 18 of 18 evictions released the lane under a successor; 13 of 13 fires false
python3 util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py "$T" --self-test   # five known-answer mutations
python3 util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py "$T"        # the watchdog's logic on the measured lane, in phase and phase-randomized
T2=reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json
python3 util/ad-hoc/2026-10-04_f058_census_v2_analyze.py "$T2"           # 304 requests (one open at the end), 11 evicted in runs of 1, 2, 4, 4; 15 fires
python3 util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py "$T2"     # 11 of 11; 15 of 15
python3 util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py "$T2" --self-test
python3 util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py "$T2"
```

## Running it again (live)

In the canopy environment, against a verify leg serving the commit under test (never `:8051`):

```bash
JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:<port> env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB \
    /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/2026-10-04_f058_census_v2_live.py --out <transcript.json>
```

Its gate and tab triggers take effect 1.3–4.2 s after they fire, a delay the transcript splits only for T-tab,
and only in part, and T-mode's effect is not recorded, so as written they cannot test a mid-request re-enable
(the ledger's Phase 11, Instruments). A leg from a tarball tree needs `JUNIPER_CANOPY_GIT_SHA` set,
or `/v1/health` cannot report the commit.

## Corrections to `2026-10-05_RESULTS.md`

1. "In the cascades, the responses of the in-flight requests would have landed 1.6–2.4 s after the fire": 1.6–2.4 s
   is when those requests were EVICTED, which is when their successors were requested. Their responses landed
   later, 2.1, 2.2 and 3.1 s after the fire, read from the release each response caused
   (`2026-10-05_f058_census_v2_release_trace.py`).
2. "An evicted response lost nothing here; during a run it would lose data": the feeder replaces the store with
   the whole fetched window or history (`_update_metrics_store_handler`, `dashboard_manager.py:7879-7990` at
   canopy `60ae1870`), so an eviction delays the chart until the next applied answer, and loses no row that the
   next answer carries. The run of 11 left the lane 34.8 s without an applied answer.
3. The watchdog's aliasing is an inference, not an observation: the shim logs fires only, never the watchdog's
   non-firing samples. Replaying the watchdog's own logic over the run's measured lane every 5,000 ms, in phase,
   gives 5–16 fires at every one of 500 sampling phases (median 9), against 13 observed; at the same rate with
   each sample's phase randomized it gives a median of 1 (`2026-10-05_f058_watchdog_alias_replay.py`; the second
   run gives 3–18, median 7, against 15, and the same randomized median). Those figures read the lane from each
   change's innermost record, as the ledger's Phase 11 explains; before its round 1 the replay dated changes
   early and gave medians of 9, 8 and 2. That shows aliasing sufficient; it does not exclude a phase lock
   through the renderer's queue.
4. T-apply: the clamp's gate write landed 316 ms after the request in flight was answered, so nothing was in
   flight under the clamp. By timing, canopy's own clamp watchdog (E-3, `APPLY_IN_FLIGHT_MAX_MS` 60 s) released
   the clamp after 62.3 s, before the census's own release, which landed 2.1 s later as a redundant `false`. The
   gate wrote that to the lane 0.7 s into request 140, which was answered 1.1 s later.
