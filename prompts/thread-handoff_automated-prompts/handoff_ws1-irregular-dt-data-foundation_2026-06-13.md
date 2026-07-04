# Handoff — WS-1 irregular-Δt / time-series dataset foundation (COMPLETE) + WS-4 follow-ups

**Date**: 2026-06-13
**Topic**: WS-1 of the juniper-recurse Model/Middleware refactor — the additive 3-D time-series + irregular-Δt NPZ contract in `juniper-data` + `juniper-data-client`. **WS-1 is fully shipped and merged.** This handoff records the completed state and the deferred forward work.
**Use as the initial prompt for a fresh thread.**

---

**WS-1 (`juniper-data#168`) is COMPLETE** — the additive 3-D time-series / irregular-Δt NPZ contract shipped across four merged PRs, #168 is closed, and the deferred tail is tracked in **`juniper-data#179`** (label `workstream:WS-4`). There is **no in-flight code** from this thread. The next *actionable* forward work is **#179 §A** (synthetic time-series generators — not blocked); the model-side items (#179 §C) are blocked on **[OQ-4]** + repos that don't exist yet.

## Completed so far (all MERGED)

Spec of record: `notes/JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md` (juniper-ml#378) — §6 contract, §7 leakage test, §8 Approach C. Decomposition chosen with Paul: **4 dependency-ordered PRs, "windowing-first, lean contract."**

- **`juniper-data#169`** (MERGED) — `juniper_data/generators/_sequence.py`: `window_one_ticker` + `_yyyymmdd_to_ordinal` (per-entity windowing; derives per-step `dt` from row dates; splits windows by target-time). `tests/unit/test_sequence_windowing_leakage.py`: Hypothesis property test pinning invariants **I1–I5**. `hypothesis` added to the `test` extra.
- **`juniper-data#170`** (MERGED) — `core/meta.py::compute_shape_meta(arrays, task_type)`; `DatasetMeta.n_classes`/`class_distribution` made **optional** + new **`task_type`** field; `task_type` declared per generator in `GENERATOR_REGISTRY`; route dispatches (`n_features` = trailing axis → handles 2-D + 3-D; `argmax`/`class_distribution` only for classification). 2-D classification path **byte-identical**.
- **`juniper-data#171`** (MERGED) — `generators/equities_seq/` **sibling** generator (reuses `EquitiesGenerator`'s static pipeline, windows each ticker via `_sequence`, concatenates; `dt` from the `date_*` trading-day gaps — weekend/holiday gaps ARE the irregular Δt). `core/split.py::temporal_split_index` (chronological cut helper). `DatasetMeta` gains `sequence`/`lookback`/`time_unit` (route-derived from X rank; `time_unit` registry-declared). The flat 2-D `equities` generator is untouched.
- **`juniper-data-client#87`** (MERGED) — `juniper_data_client/contract.py::validate_npz_contract` (§6.4 `X.ndim` dispatch → `"tabular"`/`"sequence"`, enforces dt/mask rules); NPZ key constants in `constants.py`; exported in `__init__.py`; `download_artifact_npz` docstring documents the extended keys + validator. The client already returns dict-typed metadata + all NPZ keys, so `y_reg`/`task_type`/`dt` flow through unchanged — purely additive.

**Closeout:** #168 closed (it auto-closed when #169 merged 2026-06-07, before #171/#87 landed; I added the missing delivery-summary comment). **#179 opened** as the WS-4 follow-up tracker; the `workstream:WS-4` label was created.

## Remaining work — all in `juniper-data#179`

### §A — data-layer, ACTIONABLE NOW (juniper-data; not blocked)

- Synthetic time-series **regression** generators ([OQ-5]): `multi_sine`, `mackey_glass`, `ar_p` — deterministic / seeded / offline / known-answer; register with `task_type="regression"`; golden tests. (These are the recurse CLI "hello-world" datasets; equities is network-bound and unsuitable for that role.) **This is the first real `task_type="regression"` generator → closes the "pure-regression NPZ traverses the route end-to-end" check (#170 only unit-tested the dispatch).**
- At least one **irregular-Δt synthetic** (non-uniform sampling) to exercise `dt`/`observed_mask` beyond equities.
- **Dynamic `dt_scaling`/`target_scaling` meta + generator→meta channel** (§6.5) — the mechanism for a generator to pass *non-derivable* metadata into `DatasetMeta` (deferred from #170/#171's lean scope, where sequence meta is route-derived / registry-declared). Unblocks the denorm round-trip check.
- **Walk-forward** option on `temporal_split_index` (deferred from #171 scope C).
- *(optional)* migrate the flat 2-D `equities` generator to consume `temporal_split_index` (kept inline to preserve byte-identical output, RK-9).

### §C — BLOCKED model-side (gated on [OQ-4] + repos that don't exist yet)

- **WS-3 — `juniper-model-core` (repo TBD):** `TrainableModel` "consumes per-step Δt" capability flag + conformance kit (shuffle-`dt` R-Δt-3, masked-step R-Δt-6).
- **WS-4 — `juniper-recurse` (repo TBD):** Approach A (`dt` as input channel), Approach C (§8 solver-free variable-step LMU + grid-invariance test §8.6), Approach B (RCC/ESN Δt-gated decay).
- When those repos exist, migrate #179 §C to issues there.

## Key context (decisions + constraints — do not re-litigate)

- **Lean contract (Paul-approved):** `task_type` + `time_unit` are **registry-declared** per generator; `sequence` + `lookback` are **route-derived** from `X.ndim`/`shape`. Dynamic `dt_scaling`/`target_scaling` deliberately **deferred to WS-4** (model-side normalization need) — `dt` is emitted **raw** (calendar days); `observed_mask` is all-ones (trading-day-native).
- **`equities_seq` is a SIBLING generator, not in-place** — the flat 2-D `equities` artifact stays **byte-identical** (RK-9). It reuses `EquitiesGenerator`'s `@staticmethod` pipeline (`_resolve_symbols`/`_condition_one`/`_features`/`_direction_onehot`/`_dates_yyyymmdd`/`_fit_normalizer`) — intentional internal reuse; do not duplicate the data pipeline.
- **Per-ticker cut** = `ords[temporal_split_index(n, train_ratio)]`; windows split by **target time** (train iff target < cut). `test_ratio` is vestigial for the sequence cut (test = every window after the cut).
- **[OQ-7] irregular-Δt is GATING** (not deferrable) and is **satisfied** by `equities_seq`'s real weekend/holiday Δt — WS-1 did not need the synthetics for the gating demo.
- **[OQ-4] (model pick — RCC vs ESN vs NEAT/LMU) is still OPEN and under active analysis** (juniper-ml#377 + newer P4 delay-line evaluation docs #399/#400/#402) → all #179 §C model-side work is blocked on it. (OQ-4 is its own thread — see `handoff_recurrent-structure-add-on_2026-06-07.md`.)
- **Repos don't exist:** `juniper-recurse` and `juniper-model-core` are not GitHub repos yet (verified 2026-06-09). That's why #179 §C items are cross-repo placeholders, not filed in those repos.
- **Lint toolchains differ:** `juniper-data` = **ruff** (+ mypy/bandit, line 512); `juniper-data-client` = **black/isort/flake8** (+ mypy/bandit, line 512, flake8 `max-complexity=15` → `validate_npz_contract` is split into helpers to stay under it). Both validated via `pre-commit run --files`.
- **Local test env:** `/opt/miniforge3/envs/JuniperData/bin/python` (3.14.2; numpy 2.4.1, pandas 3.0.3, yfinance, hypothesis). Run pytest with `PYTHONPATH=<worktree>` so the worktree package wins over the env's editable install (the PEP 660 finder did NOT shadow it in practice, but the prefix is belt-and-suspenders).
- **CONCURRENCY:** a parallel session is actively advancing juniper-ml `main` (OQ-4 docs landed through #402 as of 2026-06-13) — `gh pr list` + check recent `main` before editing shared docs; coordinate, don't race.

## Git status

- **No in-flight code.** All four WS-1 PRs MERGED (`juniper-data#169`/#170/#171, `juniper-data-client#87`); both task worktrees removed + branches deleted + pruned. `juniper-data` + `juniper-data-client` `main` are current.
- **#168** CLOSED (with delivery-summary comment); **#179** OPEN (label `workstream:WS-4`).
- This handoff doc is on its own docs branch (`docs/ws1-thread-handoff`) → PR; nothing else outstanding.
- Continuity memory: `project_ws1_irregular_dt_data_foundation.md` (juniper-ml auto-memory).

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-data
for n in 169 170 171; do echo -n "#$n "; gh pr view "$n" --json state -q .state; done   # all MERGED
gh issue view 168 --repo pcalnon/juniper-data --json state -q .state                    # CLOSED
gh issue view 179 --repo pcalnon/juniper-data --json state,title -q '.state + " — " + .title'   # OPEN (WS-4 tracker)
gh pr view 87 --repo pcalnon/juniper-data-client --json state -q .state                 # MERGED
# repos still absent (so #179 §C is blocked):
gh repo view pcalnon/juniper-recurse  >/dev/null 2>&1 && echo "juniper-recurse EXISTS"  || echo "no juniper-recurse repo"
gh repo view pcalnon/juniper-model-core >/dev/null 2>&1 && echo "juniper-model-core EXISTS" || echo "no juniper-model-core repo"
```

---
