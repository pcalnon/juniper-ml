# Phase 9 scratch evidence, rescued from tmpfs

The canopy E2E arc's Phase 9 authoring session (`259b4d16`) kept these files in its scratchpad under
`/tmp`, which is tmpfs: a reboot deletes it. The ledger's validation (Lane A2, 2026-09-24) found that
several Phase 9 claims rest on them, including the only evidence for the P1 F-CANOPY-058. They were
copied here byte-for-byte on 2026-09-24 by `util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence.py`.
The lane scripts that produced some of them are in `util/ad-hoc/2026-09-23_f055_r1_laneB_*` and
`util/ad-hoc/2026-09-23_cuts_r1_laneB_probe_deps.py`, with a provenance header prepended.

None of these files carries the commit it ran against. The ledger
(`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 9) names the commit for each.

| directory | files | what they back |
|---|---|---|
| `orchestrator/` | `cuts_full_suite.log` | the cuts' suite count at `ce78e0de`: 6806 passed, 4 skipped (progress characters; the summary line was lost to `conda run`) |
| `orchestrator/` | `f055_full_suite.log` | F-CANOPY-055's first fix, suite at `884d22fb`: 6823 passed, 4 skipped |
| `orchestrator/` | `cuts_r2_tests.log` | the cuts' round-2 corrections: "168 passed" over eight named files |
| `orchestrator/` | `f055_tests_parent.log`, `f055_tests_fix.log`, `f055_tests_fix2.log`, `f055_watchdog.log` | F-CANOPY-055's first fix, its test files on the parent and on the fix |
| `orchestrator/` | `census_f055.log`, `census_f055_150s.log` | the status-bar census runs on the fix (60 s VOID, 150 s APPLIES) |
| `orchestrator/` | `f025_drive.log` | the F-CANOPY-025 allow-arm drive on demo legs |
| `orchestrator/` | `idle_cuts_live_check_rebuilt.log` | the cuts' live check against its parent (run 2) |
| `orchestrator/` | `cuts_fix_tests.log` | the cuts' round-1 correction tests |
| `f055_r1_laneA/` | `parent_junit.xml`, `fix_junit.xml` | "19 of the three files' 94 tests fail" on the parent |
| `f055_r1_laneA/` | `mut_{i,ii,iii,iv,iv_b,v,vi}_junit.xml` | "All six mutations were caught" (`iv_b` is the unequal-timeouts variant) |
| `cuts_r1_laneA/` | `m3_parent.log` | the cuts' falsification: 7 of 9 fail on `3a6dea95` |
| `cuts_r1_laneA/` | `m6_collect_ce78.txt` | the collection count at `ce78e0de`: 6810 |
| `cuts_r3_laneB3/` | `parent_run.txt`, `head_run.txt` | round 3: 7 of 9 fail on `0254a7ec`; the head's three named files pass |
| `cuts_r3_laneB3/` | `precommit_head.txt` | round 3's pinned pre-commit run on the eight PR files at `4b4cfb16` |
| `f055_r1_laneB/` | `run_watchdog.json`, `run_watchdog_r3.json` | Lane B's watchdog runs: 23 of 23 with no fire; 5 fires in 240 s, 17 of 56 dropped |
| `f055_r1_laneB/` | `run_apply.json` | Lane B's Apply run: 0 of 24 applied after the release |

Lane B's other F-CANOPY-058 figures (0 of 51, 4 of 4 then 0 of 28, 352 s, 37–44 false fires an hour) have
no surviving raw output. Their scripts are archived and can re-create them.
