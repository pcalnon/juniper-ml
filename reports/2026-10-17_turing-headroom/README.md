# turing memory-headroom baseline (task F3): dev mode

Task F3 of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` asks for at least 480 samples per
mode, taken at 60 s intervals, in dev mode and node mode. This directory holds the **dev-mode** run. Node mode (desktop apps
and Docker Desktop quit, no VM running) is still to do: the owner sets that host state.

## Files

- `dev.tsv`: the 487 raw samples, one per minute, with a header row. Columns: `vm_stat` page counts, `sysctl vm.swapusage`,
  `memory_pressure` free %, and whether Docker Desktop was running.
- `summary.md`: the summary, written by
  `python3 util/ad-hoc/2026-10-17_turing_headroom_summarize.py dev.tsv --out summary.md`.

## Method

- Sampler: `util/ad-hoc/2026-10-17_turing_headroom_sampler.bash --mode dev`, detached from the session.
- **Available memory** is free + speculative + inactive pages, the same accounting `util/macvm_ctl.bash` uses for G-MEM.
- The **first run** started 2026-10-17T23:19Z and died silently after 307 samples, at 2026-10-18T04:27Z. There was no reboot,
  sleep or kill on record. The sampler was then hardened (no `-e`/`pipefail`, plus an EXIT trap that logs rc and sample
  count). It **restarted at 2026-10-18T17:29Z with `--samples 180`**, appending to the same file, and exited rc 0 at
  20:29Z after 180 of 180.
- The 13-hour gap between the runs is overnight, so the samples are 487 desktop-session minutes, not one continuous day.

## Result (dev mode)

| Measure | p5 | p50 | p95 |
|---|---|---|---|
| Available memory, MiB | 1781 | 2937 | 5420 |
| Swap used, MiB | 16243 | 17960 | 20282 |
| `memory_pressure` free % | 21 | 33 | 52 |

- Docker Desktop was running in **487 of 487** samples.
- **G-MEM passed 0 of 487** samples. The gate needs available ≥ 6 GiB VM + 4 GiB reserve, swap ≤ 2 GiB, and Docker Desktop
  not running. It fails all three conditions throughout dev mode.

So in dev mode turing cannot host the `juniper-macvm` worker VM, and plan D1's admin-only fallback applies. Whether node
mode clears G-MEM is what the node-mode run decides.
