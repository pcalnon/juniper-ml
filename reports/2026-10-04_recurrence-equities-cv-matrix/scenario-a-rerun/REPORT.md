# Suite report — e-h-recurrence-real-data

E-H (recurrence): equities_seq AAPL 2015-2022 vs irregular_sine control

Cells: 2 total, 2 succeeded, 0 degraded, 0 failed/other, 0 not run.

| cell | outcome | step_count | mean step (ms) | wall (s) | dataset.generator | dataset.params | cv_r2 | cv_r2_std | n_windows | train_r2 |
|---|---|---|---|---|---|---|---|---|---|---|
| c000-cd6f1c31 | succeeded |  |  | 16.064 |  |  | 0.9749239559080349 | 0.0036413221573580374 | 3149 | 0.9794807734649803 |
| c001-0d8782ae | succeeded |  |  | 30.1 | equities_seq | {'symbols': ['AAPL'], 'start_date': '2015-01-01', 'end_date': '2022-01-01', 'lookback': 64, 'regression_target': 'log_return', 'seed': 20260807} | -0.11526096841533144 | 0.07353723443032745 | 1346 | 0.11632826498677562 |

## Gate inputs

**`wall_seconds` is DE-RATIFIED** — it absorbs plot rendering and stack bring-up, and enabling the
Grafana bridge alone moves it ~5%. It is kept for continuity only. The gated quantity is
**`step_count`** (work, compared exactly); **mean step duration** is reported and never gated,
because this host's own drift floor is 13–20.5%.

- **work invariant**: not countable — kind ['recurrence'] has no work counter
- **single workload**: NO — fingerprint ['12715f009e0c...', '6f962ec8041f...']
- **reported instead**: n_epochs ['1'], stopped_reason ['converged'], n_windows ['1346', '3149'] — these are INPUT size and readout type, not work done, so they are reported and never gated.
