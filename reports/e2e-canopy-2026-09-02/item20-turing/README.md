# Item 20 on turing — F-CANOPY-065: the WS leg's partition never reached the apply toast

**Date:** 2026-10-21 (EDT times below; the cascor and canopy logs are local time).
**Host:** turing (macOS), no trio. Throwaway legs only.
**Ledger:** `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, F-CANOPY-065 (filed in Phase 10) and
Phase 10 "Still owed" item 20. Not yet recorded in a ledger phase.

## Trees

- **`main`**: `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028`, equal to canopy `main` `aeeaf29b` on
  every file the fix touches (`util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py`, ALL MATCH, 2026-10-21).
- **fix**: `~/.local/state/juniper/turing-e2/trees/juniper-canopy-f065`, a copy of that tree with the fix applied
  (the canopy PR's files): `src/backend/cascor_service_adapter.py`, `src/settings.py`,
  `src/tests/integration/test_n5_apply_params_ux.py`, `src/tests/unit/test_phase_c_set_params_adapter.py`.

## The instrument (`o3_rederive_*.txt`)

`util/ad-hoc/2026-10-04_phase10_o3_rederive.py`, run with
`~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python -I … --canopy-src <tree>/src`. Its four
Phase 10 arms copy `apply_params`' merge and print the same on both trees. The fifth arm, added for item 20,
drives the tree's real `apply_params` with the same frames:

- `o3_rederive_main_aeeaf29b.txt`: `applied=['cn_training_iterations']  skipped=[]`, A-N2's answer;
- `o3_rederive_f065_fix.txt`: the three WS keys and `cn_training_iterations`, and
  `nn_max_total_epochs (not-updatable)`.

## Live (`live_set_params_*.json`)

One cascor leg (`util/ad-hoc/2026-10-20_turing_cascor_leg.bash up 8230 http://127.0.0.1:8062`, cascor 0.12.0 from
the E2 tree, `/ws/control` origin allowlist the canopy leg's). A network was created by
`POST /v1/training/start` with a 2x1 inline XOR set and `epochs: 50`; the run went from 05:00:43.215 to Completed at
05:01:29.885 (cascor log). Canopy service legs on port 8062, one at a time, through
`util/ad-hoc/2026-10-21_f065_service_leg.bash` (dash 4.4.1 venv; `/v1/health` `git_sha` stamped
`aeeaf29b…+tree-f028` and `aeeaf29b…+f065-fix-unlanded`).

Each Apply is `POST /api/set_params` with A-N2's five keys: `nn_max_iterations` 5, `nn_max_total_epochs` 5000,
`nn_max_hidden_units` 4, `nn_output_epochs` 100, `cn_training_iterations` 50. Every leg logged
`Cascor params updated via WS: ['max_iterations', 'epochs_max', 'max_hidden_units', 'output_epochs']` and
`via REST: ['candidate_epochs']`.

| record | tree | when | `applied` | `skipped_detail` |
|---|---|---|---|---|
| `live_set_params_main_aeeaf29b.json` | `main` | 05:01:21, during the run | `["cn_training_iterations"]` | absent |
| `live_set_params_f065_fix.json` | fix | 05:01:47, after it | `["nn_max_hidden_units", "nn_max_iterations", "nn_output_epochs", "cn_training_iterations"]` | `[{"key": "nn_max_total_epochs", "reason": "not-updatable"}]` |
| `live_set_params_main_aeeaf29b_after_run.json` | `main` | after the run | `["cn_training_iterations"]` | absent |

The third row removes the run-state confound between the first two: `main` answers the same with the run ended.

**After the merges.** canopy#763 merged 2026-10-21T09:28:16Z as `e30010c9` (on canopy#762's `11e8de90`).
`blob_check_main_e30010c9.json` proves the tree `~/.local/state/juniper/turing-e2/trees/juniper-canopy-main-e30010c9`
(the fix tree with canopy#762's three files copied in) equal to that `main` on all 19 files canopy#760 to #763
touch. It is the tree item 27's leg should serve.

**Logs.** The canopy launcher truncates its log on each `up`, so only the last leg's lines survive
(`canopy-8062_main_after_run.log.txt`). The first two legs' `via WS` / `via REST` lines (05:01:21.906 / .914 and
05:01:47.886 / .891) are transcribed from the session's tool output. Both legs were stopped by pidfile afterwards;
nothing listens on 8230 or 8062.
