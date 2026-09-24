You are Lane A (measurement re-creation) of the Juniper independent-agent consensus procedure (juniper-ml `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2). An observation is verified only when YOU re-derive it from primary artifacts and get the same value. Prose (PR bodies, commit messages, CHANGELOG, this brief) is a CLAIM. "NO ARTIFACT" / "UNTRACEABLE" are allowed and expected answers; never reconstruct a number from the narrative.

READ-ONLY with respect to the repos: do not edit tracked files, commit, push, or comment on PRs. Do not start or stop any canopy/cascor/data process; never touch ports :8051, :8101, :8202 or any :805x leg. Scratch work in a `mktemp -d` directory. Python: `conda run -n JuniperCanopy1 python ...`.

Repos: canopy git objects at /home/pcalnon/Development/python/Juniper/juniper-canopy (`git -C <path> show/diff/archive <sha>`); evidence in the juniper-ml worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-dancing-moth.

The fix is canopy commit `884d22fb`; its parent is `ce78e0de`.

MEASUREMENTS TO RE-DERIVE (for each: claimed value, your value, command(s), MATCH / MISMATCH / NO ARTIFACT):

M1. FALSIFICATION. Claimed: on the fix, all tests in `src/tests/unit/frontend/test_f055_status_bar_own_lane.py`, `src/tests/unit/frontend/test_poll_gating.py`, `src/tests/unit/frontend/test_stage2_global_lane.py` and `src/tests/unit/frontend/test_idle_dispatch_cuts.py` pass; on the parent (the three changed/new test files copied from the fix into an extract of `ce78e0de`), exactly 19 of the three files' 94 tests fail and 75 pass; the failures are all 5 non-premise tests of test_f055_status_bar_own_lane.py, all 9 tests of TestStatusBarStrandWatchdog, test_registry_ids_all_exist_in_layout, test_exactly_one_writer_per_disabled_prop, test_gate_writes_every_registered_interval, test_source_registry_matches_the_spec and test_global_lane_shape_is_pinned; the metrics-store TestStrandWatchdog (including test_watchdog_behaviour_under_node) passes on BOTH sides. Re-run both sides from `git archive` extracts (`mkdir <dir>/logs` first) and report per-test outcomes.

M2. MUTATIONS. For each mutation below, applied to an extract of the fix, report which tests (from the four files above) fail. A mutation no test catches is a finding.
  (i) delete the `running=[...]` line from `update_unified_status_bar`;
  (ii) change that callback's Input back to `fast-update-interval`;
  (iii) register the lane as `(_STATUS_BAR_INTERVAL, "metrics")` instead of `None`;
  (iv) give both watchdog registrations the same clock variable `__metricsStoreDisabledSince`;
  (v) in the watchdog JS, change `<` to `<=` in the timeout comparison;
  (vi) delete the status-bar tuple from the watchdog loop.

M3. THE CENSUS. `util/ad-hoc/2026-09-23_status_bar_apply_census.py` (juniper-ml worktree) fixes a VERDICT RULE in its docstring. Its transcripts for this fix are `reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_status_bar_apply_census_f055_parent_8056.json, 2026-09-23_status_bar_apply_census_f055_fix_8057.json (60 s, scored VOID) and 2026-09-23_status_bar_apply_census_f055_fix_8057_150s.json (150 s)`. Recompute each baseline verdict from the raw record (responses delivered, executed entries, latency-display changes) with the rule as the script's CODE implements it, and check each transcript's `serving.git_sha` against the leg it claims.

M4. THE ALLOW-ARM DRIVE. `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` fixes a VERDICT RULE; its transcript is `reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f055_f025_allow_arm_demo_drive.json`. Recompute ALLOW / DENY / BAR per leg from the raw samples, and check `serving.git_sha` per leg.

M5. INSTRUMENT ADEQUACY (required). For the census: could `executed_entries` be 0 on a leg where the bar DID apply (e.g. the Redux subscription installed after the queue was already drained, or the MARK string not matching the callback's output key after the fix)? Could it be non-zero where nothing applied? For the drive: could `button_disabled` read False without the gate having applied (DOM attribute semantics of dbc.Button)? Cite lines.

FINAL MESSAGE FORMAT (nothing else): a table M1..M5 (measurement | claimed | re-derived | verdict | evidence), then "INSTRUMENT FINDINGS", then "ANYTHING ELSE THAT LOOKS WRONG".
