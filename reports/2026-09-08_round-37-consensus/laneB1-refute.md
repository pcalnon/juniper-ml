# Lane B1-refute — final report (verbatim, 2026-09-08)

**Tally: 0 succeeded / 2 partially succeeded (Attacks 1, 6) / 4 failed (Attacks 2, 3, 4, 5).**

Frozen tree confirmed at the stated SHAs (data 03b7548, cascor d39d537, canopy eb05021, deploy 54abfb7).

## Attack 1 — §0.3 "option 3 not enforceable end to end" — PARTIALLY SUCCEEDED

**Disposition stands; one supporting argument is refuted.**

- (a) FAILED. The only 422s are `InputTooLargeError` (`equities/generator.py:558`, under `if not allow_truncation:`) and `IncompleteDataError` (`:289` under `policy == INCOMPLETE_FAIL`; `:301` when `drop` empties the set). Route `api/routes/datasets.py:211` is the sole 422 site. Edge: `:301` fires under env-on with `incomplete_rows="drop"` and an all-unrescued universe — requires sending a flag, so it does not express option 3.
- (b) FAILED. cascor sends no key when its flag is off (`manager.py:3956-3971`); juniper-data defaults `False`; the OR reads the value only, so absent ≡ explicit `false` at the gate.
- (c) **SUCCEEDED.** Probe (pydantic 2.12.5): `EquitiesParams()` → `'allow_truncation' in model_fields_set` = **False**; `EquitiesParams(allow_truncation=False)` → **True**; `model_dump()` equal. A guard `params.allow_truncation if "allow_truncation" in params.model_fields_set else settings.equities_allow_truncation` yields omitted→deployment, explicit-false→False, explicit-true→True. `model_copy(update=...)` adds the key to `model_fields_set` with the resolved value, so the second `_resolve_bounds` call from `_resolve_symbols` stays consistent. **"Expressing option 3 caller-side would require a schema change" is REFUTED, and "cascor#624's remedy is NOT portable here" is refuted as mechanism.** The privilege-model question is the Overtoad's.
- (d) FAILED. Default is `False` (`limits.py:139`; `api/settings.py:114,223`). juniper-deploy: zero `ALLOW_TRUNCAT` hits including ignored files. Latent confirmed.
- (e) FAILED (wording only). Three sites; `equities_seq/generator.py:114` calls `EquitiesGenerator._resolve_symbols` → site `:471`; it never reaches `:501`. A third *generator* through an existing site, not a fourth site.

**Corrected statement:** the OR makes option 3 unenforceable today, by design; a `model_fields_set` presence guard would express it on the current schema, and whether to do so is the privilege question, not a schema question.

## Attack 2 — §0.13 annotation can read `false` on a trained partial run — FAILED (claim survives)

`manager.py:3956-3998`: `allow_truncated = bool(Settings().allow_truncated_datasets)`; when false no key is sent; `create_dataset` runs; `meta = result.get("meta") or {}`; `_log_dataset_shortfall`; `_build_dataset_shortfall(..., allow_truncated=allow_truncated)` (`:3725` writes it verbatim); then `_artifact_to_tensors`. No refusal anywhere on `truncation`/`data_quality`. The field reads `false` and the run trains. The log at `:3749` is self-contradictory the same way.

**Precondition the doc omits:** cascor#630's finiteness loop (`:3877-3882`) refuses a NaN artifact, and at default `fundamentals_fill="nan"` + `start_date=2000-01-01` the artifact is NaN-laden. The §0.13 scenario needs `fundamentals_fill=zero|drop` or a post-2009 `start_date`.

## Attack 3 — §0.6 three look-ahead paths at DEFAULT parameters — FAILED

- (a) `adj_close`: `auto_adjust=False` hardcoded (`:785`), `adj_close` is the 11th entry of `EQUITIES_FEATURE_COLUMNS` — in the default emitted set. Cached `AAPL_2000-01-01_2026-06-03.csv`: close on 2020-08-28 = 124.81 (split-adjusted; unadjusted was ~499); `close/adj_close` runs 1.1930 (2000-01-03) → 1.0000 (series end) over 91 distinct steps — a monotone channel of future cumulative dividends. Does not survive as "not a defect" under the project's own rule quoted at `generator.py:675-677`; survives only as "magnitude unmeasured".
- (b) `cost_basis`: inert at default; `on_or_before` at `:756-758` gives the first row's close for default `purchase_date="2000-01-03"`. Reachable by a canopy user: `purchase_date` is rendered as a text input and `_translate_staged_config` (`manager.py:3611-3615`) pops only rotations/n_spirals/n_squares for equities.
- (c) `_SHARES_OUTLIER_FACTOR`: unconditional at `:932-934`; `_fetch_shares` takes no date bound. Feeds `total_shares` → `market_cap` and `report_date` → `days_since_report` — features, never labels. Re-derived from the 485 cached payloads: **61 CIKs lose ≥1 point (92 points)** — exact match.
- §0.9 vs §0.6/§0.7: no contradiction — the filter runs after the cache read on either branch, and `use_cache=True` is default. One imprecision: two empty-units guards exist; the loop's (`:887`) is cold-only, the post-load one (`:910`) runs on a warm cache too.

## Attack 4 — §0.12 `equities_seq` dataset_id collision — FAILED

`class EquitiesSeqGenerator:` is standalone, so `getattr(generator_class, "bind_deployment_defaults", None)` is `None`. `seed` defaults to 42, so no nonce. Probe, default params: env off: equities `equities-3.0.0-c4e2c6186cd72f1c`; equities_seq `…-ca0d2edd10d58154`; env on: equities `…-3c545d0b09b28138`; equities_seq `…-ca0d2edd10d58154` — **identical**. Decisive at defaults (503 constituents > cap 14).

## Attack 5 — §0.4 MAJOR bump / keep open — FAILED

`docs/api/JUNIPER_DATA_API.md:63` and `:75` verbatim; `/v1/datasets/filter` documented twice (`:427`, `:551`), both with `"total"`; no experimental/internal marker. Policy binds. The TTL cache is 5 s (`storage/base.py:31`) and is invalidated on every save/delete/update_meta, so under any write rate the O(N) walk returns; Postgres `list_all_metadata` is `SELECT * … ORDER BY created_at DESC` with no LIMIT (`:570`).

## Attack 6 — §0.2 "canopy must POLL, or cascor needs a new frame" — PARTIALLY SUCCEEDED

WS half survives: `training_stream.py:96` is the only `get_status()` reach; canopy's event handler (`cascor_service_adapter.py:846-853`) acts only on `training_complete`; the `dataset_swap` event fires only on the live-swap success branch.

**But canopy already polls `/v1/training/status` at 1 Hz**: `StatusCache` refresher, `REFRESH_INTERVAL_SECONDS = 1.0` (`status_cache.py:102`), wired at `main.py:175-183` to `get_training_status_for_refresh`; the dashboard's fast tick reads `/api/status` from that cache. The real gap is `normalize_status` (`service_backend.py:247-313`), a fixed key set that drops `dataset_shortfall`.

## New findings not in the document

1. **Canopy already renders the policy fields.** `dataset_schema.py:177-205` maps boolean→checkbox, enum→select, string→text, excluding only `INFRASTRUCTURE_FIELDS`. Probe on the real `EquitiesParams` schema: `allow_truncation` checkbox (default False), `incomplete_rows` select, `purchase_date` text, `max_symbols` number; **`symbols` is not renderable** (array).
2. **Canopy sends explicit `allow_truncation: false` on every equities apply, which defeats cascor#624.** `_collect_generator_params` (`dashboard_manager.py:2948-2962`) drops only `None`/`""`; the unticked checkbox's `False` is forwarded → cascor `params` → `jd_params`. cascor's presence test then withholds its deployment default; juniper-data refuses; and because `allow_truncated=True`, `_describe_dataset_fetch_failure` returns the bare "juniper-data fetch failed" without the remedy. Derived from source, not a live UI run.
3. **At canopy defaults equities cannot yield a trainable dataset**: the universe needs the checkbox (no `symbols` control), and `fundamentals_fill="nan"` + `start_date=2000-01-01` produce NaN rows that #630 refuses.
4. `val_ratio` is rendered while `train_ratio`/`test_ratio` are excluded — `INFRASTRUCTURE_FIELDS` drift.
5. `manager.py:3933` in §0.13 is `:3956` on d39d537 (harmless drift).

## What the evidence cannot support

That Yahoo restates rows for *future* splits (a past split is adjusted in the cached frame; the dividend ratio is non-causal by construction; the harm magnitude on a next-day target is unmeasured). §0.7's KO figures and §4's 43.1% / 100× — outside brief. Whether option 3 should be a caller right — Overtoad's question. Finding 2's UI behaviour end to end — inferred from the callback wiring.
