# Lane A2 — measurement re-creation from SOURCE ONLY

- **Artifact under review**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` v1.0.0 (W5.1 note; P5 GO; R5 band)
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A
- **Entry point**: source code and the installed environment only. Nothing under `reports/` was opened (a directory listing of my own output folder is the only contact; no sibling lane's files were read). All numbers quoted from the note are quoted as *claims*; everything I verified is cited `file:line`.
- **Date**: 2026-10-05 — Reviewer: Lane A2 (independent agent)
- **Checkouts read** (read-only):
  - juniper-ml worktree `misty-kindling-pascal` @ `a0a120d5` (main)
  - juniper-recurrence local `main` = **`be081fae`** (= the SHA the note §0.1 names). **The brief's `2c34805c` is NOT an object in that repo** (`git cat-file -t 2c34805c` → "Not a valid object name"); `origin/main` = `695df69` (#189), which differs from `be081fae` by `AGENTS.md` only (`git diff --stat`: 1 file, +24). Code under review is therefore `be081fae`.
  - juniper-data `main` @ `29be6d35`; juniper-data-client @ `75f15a6`
  - model-core as installed: `/opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages/juniper_model_core/` (0.2.0)
- **Probes run with the env interpreters** (scratchpad scripts, not repo files): `walk_forward_folds(1698, …)`; `compute_checksum` time-invariance; `_GCV_GRID` endpoints; route-scorer vs script-scorer divergence at |r²| ≈ 1e5 with float32 `y`.

Path abbreviations used below: `APP` = `juniper-recurrence/juniper-recurrence/juniper_recurrence/`, `MODEL` = `juniper-recurrence/juniper-recurrence-model/juniper_recurrence_model/`, `MC` = installed `juniper_model_core/`, `DATA` = `juniper-data/juniper_data/`, `DC` = `juniper-data-client/juniper_data_client/`, `ML` = this juniper-ml worktree, `MATRIX` = `ML/util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py`, `COND` = `ML/util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py`.

---

## Findings (numbered per the brief)

### 1. Service defaults and what a bare `POST /v1/crossval` resolves to — **CONFIRMED** (with two precision notes)

| Claim | Verdict | Evidence |
| --- | --- | --- |
| `default_d = 16` | CONFIRMED | `APP/settings.py:181` `default_d: int = 16` |
| `default_theta = None` | CONFIRMED | `APP/settings.py:182` `default_theta: float \| None = None` |
| `default_ridge = 0.0` | CONFIRMED | `APP/settings.py:183` `default_ridge: float \| Literal["gcv"] = 0.0` (the `"gcv"` literal is already accepted — §3.2(i) is a one-token change) |
| default readout linear | CONFIRMED | `APP/schemas.py:251` `readout: ReadoutKind \| None = None`; `APP/_readout.py:91` `kind = readout or "linear"` |

Resolution path in the route: `APP/routers/crossval.py:78-79` (`d`/`theta` fall back to settings), `:96-110` builds `partial(build_lmu_regressor, …, readout=req.readout, ridge=req.ridge, …, default_ridge=settings.default_ridge)`. In `APP/_readout.py:101-103` the **linear** rung resolves `ridge if ridge is not None else default_ridge` → `LMURegressor(d, theta, ridge=…)`; `:104-111` the **RFF** rung resolves `ridge if not None else _RFF_DEFAULT_RIDGE` (= `"gcv"`, `:40`) — **`default_ridge` never reaches the RFF rung**, consistent with the note's framing that the hazard is the linear rung's.

Precision notes (not defects in the note, but the note's words are looser than the schema):

- `APP/schemas.py:244` `n_folds: int = Field(ge=2)` is **required**; `:245-247` `scheme="expanding"`, `embargo=0`, `min_train=None`. A *literally* bare body `{"dataset":…, "n_folds":5}` therefore resolves to linear / ridge 0.0 / d 16 / data-driven theta **with embargo 0** (train sizes would be 283/566/849/1132/1415). The note's "control" (§1.3) carried the E-H CV params (`n_folds 5, expanding, embargo 2`) with no *model* params (`MATRIX:74,123-124`), which is what "bare" means for the model side. §3.2 item 1's "the configuration a bare `POST /v1/crossval` … gets" is right about the model configuration.
- `MODEL/model.py:89` `LMURegressor(d=16, theta=None, *, readout=None, ridge=0.0, time_unit="steps", random_seed=0)`; `:99` wraps `ridge` in `LinearReadoutSpec(ridge=0.0)` (`MODEL/readouts.py:212-220`). So the class default and the service default coincide: there is no layer at which an unset ridge becomes anything but `0.0` on the linear rung.

### 2. `_lmu_hyperparams` drops `theta: null`; the E-H body; the YAML inheritance — **CONFIRMED**

- `ML/util/experiments/run_experiment.py:1866-1868`: `_lmu_hyperparams` = `{key: value for key, value in train_block.items() if value is not None}` — drops `theta: null`.
- The `train:` block survives validation with its `None`s: `:686-688` `_reject_unknown_keys(train_block, TRAIN_KEYS_RECURRENCE)` then `config["train"] = dict(train_block)` (`TRAIN_KEYS_RECURRENCE` at `:168`).
- Crossval body: `:2029` `hyper = _lmu_hyperparams(config["train"])`; `:2066-2075` `{"dataset": {"dataset_id": …}, "n_folds", "scheme", "embargo", **hyper}` plus `min_train` **only if not None** (`:2074-2075`). The train body (`:2034`) is `{"dataset": {"dataset_id", "split"}, **hyper}`.

YAML inheritance, traced:

1. `ML/util/experiments/suites/p4/e-h-recurrence-real-data.yaml:9` `base_config: [../../../../../juniper-recurrence/conf/experiments/irregular-sine-rff.yaml]`; `:10` `seed_policy: fixed`; `:13` one `include` cell with overrides `dataset.generator: equities_seq` and `dataset.params: {symbols:[AAPL], start_date:"2015-01-01", end_date:"2022-01-01", lookback:64, regression_target:log_return, seed:20260807}`.
2. `ML/util/experiments/run_suite.py:371` `config_rel = item.get("config", suite["base_config"][0])` → the irregular-sine YAML; `:386-390` `materialise_cell` loads it and applies each override with `_set_dotted` (`:321-332`), whose last line `node[parts[-1]] = value` **replaces the `dataset.params` mapping wholesale** — none of the irregular_sine params (`n_steps`, `horizon`, `sample_dt`, `jitter`, `n_components`, `noise_std`, `train_ratio`, `seed`) is inherited. `seed_policy: fixed` skips the per-cell seed derivation (`:391-397`). `run_experiment.py:667-668` `params.setdefault("seed", seed)` is a no-op (seed present).
3. Resolved cell config, every key and value (`juniper-recurrence/conf/experiments/irregular-sine-rff.yaml` lines cited):
   - `experiment`: name → `e-h-recurrence-real-data-<cell_id>` (`run_suite.py:398-399`), seed `20260729` (`:11`)
   - `service` (`:13-20`): `log_level INFO`, `log_format text`, `metrics_enabled true`, `rate_limit_enabled false`, `default_d 16`, `default_theta null`, `default_ridge 0.0`
   - `dataset`: `generator equities_seq` (override), `split train` (`:25`), `params` = the six override keys, `persist true` / `tags ["experiment", <name>]` / `ttl_seconds null` (run_experiment defaults `:672-681`)
   - `train` (`:37-43`): `d 16`, `theta null`, `ridge 1.0`, `readout rff`, `rff_features 256`, `rff_gamma median`
   - `crossval` (`:45-50`): `enabled true`, `n_folds 5`, `scheme expanding`, `embargo 2`, `min_train null`
   - `predict` (`:52-54`): `enabled true`, `from_dataset_split test`; `outputs` (`:56-60`) plots list, `grafana_bridge true`, `save_model true`, `max_wall_seconds 900`
4. Hence the suite's crossval body is **exactly** `{"dataset": {"dataset_id": …}, "n_folds": 5, "scheme": "expanding", "embargo": 2, "d": 16, "ridge": 1.0, "readout": "rff", "rff_features": 256, "rff_gamma": "median"}` — identical (key order aside) to the note §1.2 and to `MATRIX:73-74,124` (`E_H_MODEL`, `E_H_CV`).

**"The irregular-sine YAML pins `0.0` explicitly" (§3.2 item 1)**: `irregular-sine-rff.yaml:20` `default_ridge: 0.0` — in the **`service:` block** (`:13-20`), *not* the `train:` block (whose `ridge: 1.0` at `:40` pairs with `readout: rff` at `:41`). Mechanism: `ML/util/experiment_stack.bash:820,837,844` export `JUNIPER_RECURRENCE_CONFIG_FILE=$RUN_DIR/config/experiment.yaml`; `APP/settings.py:138-143` inserts `ExperimentYamlSettingsSource` **above** env and class defaults (`:107-110` validates the service keys). So "the reference experiment is unaffected" holds for two independent reasons: (a) the YAML projection overrides any new class default; (b) the reference experiment's own train block uses the RFF rung with an explicit ridge, which never consults `default_ridge` (`APP/_readout.py:104-105`). **Code corollary the note does not state**: the same YAML is the E-H suite's `base_config`, so §3.2 option (i) alone (changing `Settings.default_ridge`) would **not** change what a bare request to an E-H-launched stack receives — the staged YAML keeps pinning `0.0`. Lane B may want this.

### 3. `walk_forward_folds(1698, n_folds=5, scheme="expanding", embargo=2)` and `pass_eval_as_val` — **CONFIRMED** (live run)

`MC/crossval/splits.py:87` `fold_size = n_samples // (n_folds + 1)` = 1698 // 6 = **283**; `:95-98` `eval_start=(i+1)*283`, `train_end = eval_start - embargo`, `train_start = 0`. Run with `/opt/miniforge3/envs/JuniperCascor1/bin/python`:

| fold | train idx | n_train | eval idx | n_eval | gap |
| --- | --- | --- | --- | --- | --- |
| 0 | 0..280 | **281** | 283..565 | 283 | 2 |
| 1 | 0..563 | **564** | 566..848 | 283 | 2 |
| 2 | 0..846 | **847** | 849..1131 | 283 | 2 |
| 3 | 0..1129 | **1,130** | 1132..1414 | 283 | 2 |
| 4 | 0..1412 | **1,413** | 1415..1697 | 283 | 2 |

Matches the note §0.1 to the row. `pass_eval_as_val`: `MC/crossval/executor.py:77` default `False`; the route (`APP/routers/crossval.py:119-125`) does not pass it → `:132-134` `X_val = y_val = None`. The matrix script never calls `cross_validate`; `MATRIX:190` `model.fit(Xtr, ytr, **aux_tr)` leaves `X_val`/`y_val` at `None` (`MODEL/model.py:158`) — equivalent. `min_train`: route passes `req.min_train` (= `None`, `crossval.py:87`); both scripts omit it → same folds (`MATRIX:244`, `COND:61`).

### 4. `readouts.py` / `model.py` — **CONFIRMED** (one wording note on "cond")

- **RFF standardises per fold, train-only**: `MODEL/readouts.py:226-231` `_standardize_fit` (per-column mean/std, `std→1.0` zero-variance guard); `:298-299` in `RFFReadout.fit` on the **train** `M` only; `:290-293` `_phi` applies the stored stats at predict.
- **Linear rung does not standardise**: `MODEL/readouts.py:179-180` `_design` → `_assemble_design(M, extra)`; `:189-193` fit on that raw design. No scaling anywhere in `LinearReadout`.
- **Design** = `[ M | extra | 1 ]`: `:105-108` `np.concatenate([block, extra, np.ones((n,1))], axis=1)` — intercept is the trailing ones column. `extra` = `MODEL/model.py:150-155` `_side_channel`: an `(n,1)` float64 column of `target_dt` when `_uses_target_dt` (set at `:171` from `kw.get("target_dt") is not None`), else `(n,0)`. `target_dt` **is** a real column for equities_seq (see §5). Column order inside `M`: `:148` `reshape(n, n_features * d)` of `(n, F, d)` → feature-major, order-minor; `F·d = 15·16 = 240` (15 columns: `DATA/generators/equities/defaults.py:127-155`), so 240 + 1 + 1 = **242** ✓.
- **Solver per `ridge`** (`:182-193`): `0.0` → `np.linalg.lstsq(design, y, rcond=None)` (`:193`) — LAPACK `gelsd`, the **minimum-norm** least-squares solution; "min-norm" is the right word. `rcond=None` → "machine precision times `max(M, N)`" (numpy 2.5.3 docstring; = 6.24e-14 for `(281, 242)`). `> 0.0` → `_ridge_solve` (`:111-116`): normal equations `np.linalg.solve(gram + λI, Xᵀy)` with the bias entry of the penalty zeroed (`:115`) — **not** `lstsq`; the `target_dt` column *is* penalised (it is in `design`, not the bias). `"gcv"` → `_gcv_select` (`:119-153`): centres `[M | extra]` and `y`, **one** thin SVD, `GCV(λ) = n·RSS/(n − tr H)²` with `tr H = 1 + Σ s²/(s²+λ)`, picks the grid argmin, returns coef in `[features | 1]` layout + λ.
- **`_GCV_GRID`**: `:54` `np.logspace(-6.0, 3.0, 60)` — 60 points, `1e-6 … 1000.0`; probe: `grid[-1] == 1000.0` is `True`, so a selected `1000.0` is exactly the ceiling.
- **GCV write-back**: `LinearReadout.fit` `:186-187` `self._coef, self.ridge = _gcv_select(...)`; `RFFReadout.fit` `:309` `self._beta, self.ridge = _gcv_select(...)`. `MODEL/model.py:207-210` propagates to `model.ridge` **only for `kind == "linear"`**; the matrix script reads `readout.ridge` (`MATRIX:210`), so it sees the selected λ on **both** rungs (the note's "ridge is the resolved value (GCV writes back the selected λ)" is correct for the instrument used).
- **RFF `d_out`**: `:302` `min(n_features_out, n)` → 256 in every fold (n_train ≥ 281) ✓ "256 features".
- **theta**: `MODEL/model.py:174-177` `theta = median(sum(dt, axis=1))` over the dt the fit receives (the fold's train slice), fallback `n_steps` when dt absent or theta ≤ 0; `:178-179` memory built fresh on each (per-fold) model. ✓ "fold-resolved".
- **dtype**: `MODEL/model.py:159-160` casts `X`, `y` to float64 at fit; `:137` `_memory_block` casts `X` to float64; `MODEL/units/lmu_varstep.py:204-224` rolls out in float64 / complex128; `:154` side channel float64 → **the linear solve runs in float64** over float64-cast float32 inputs.

### 5. `data.py`: `derive_full_split`, `sequence_data_from_arrays(arrays, "full")`, `fit_kwargs()` — **CONFIRMED**

- `MODEL/data.py:142-143` `split == "full"` with no `X_full` → `derive_full_split`. `:103-116` composes `<base>_full` by `np.concatenate` over `_FULL_COMPONENT_SPLITS = ("train", "val", "test")` (`:66`) for every base key present in **all three** partitions; `:114-115` never overwrites a producer-supplied `*_full`; `:121-124` **stable** argsort on the concatenated `ticker_code_*` → entity-major. For one ticker the sort key is constant → identity permutation → the full view is plain `train | val | test`. `ticker_vocab` (no split suffix) is not composed. (Producer side agrees: `DATA/generators/equities_seq/generator.py:274-300` `_assemble` is split-major with the entity-major note in its docstring.)
- `fit_kwargs()` `:43-50`: `{"dt": dt}` always (dt cast to float64 at `:178`), plus `"target_dt"` when present (`:194` reads `target_dt_full`, reshaped `(n,)`), plus `"seq_lengths"` when present — **absent** for equities_seq (`_WINDOW_KEYS`, `generator.py:61`, has no `seq_lengths`), so the readout step is the last step (`model.py:133`). `observed_mask_*` exists in the artifact but is **not** passed on either path (not in `fit_kwargs`; `readout_mask` never set). **`target_dt` reaches the fit** and becomes the side-channel column.

### 6. juniper-data meta `checksum` and `equities_seq` 6.0.0 — **PARTIAL** (version CONFIRMED; F-P8's mechanism REFUTED)

- **Where/what**: `DATA/core/artifacts.py:50-63` `compute_checksum` = SHA-256 over `arrays_to_bytes(arrays)` (`:33-47`: keys **sorted**, `np.savez` into a `BytesIO`, uncompressed). Called at `DATA/api/routes/datasets.py:392`, **after** the three reserved-channel pops (`:377-390`) and **before** persist (`:446` `store.save_versioned(dataset_id, meta, arrays)`); an `awk` scan finds no array mutation after `:392`. So the stored checksum is over exactly the persisted array-only dict. The note's "it fingerprints the NPZ container … not the arrays" is **half right**: it hashes the container bytes.
- **"whose zip entries carry write timestamps" — REFUTED on this environment.** Probe (JuniperData env, numpy 2.4.1): `compute_checksum` on identical arrays, 2.5 s apart → **identical** digests; both containers' entries carry `date_time = (1980, 1, 1, 0, 0, 0)`. Cause in numpy: `numpy/lib/_npyio_impl.py::_savez` (JuniperData env) writes each member with `zipf.open(fname, 'w', force_zip64=True)` (function line 30), which constructs `ZipInfo(name)` with its default 1980-01-01 timestamp — no wall-clock time enters. juniper-data's own documentation agrees the hash is content-determined: `DATA/api/http_cache.py:10-20` — "a CANONICAL serialization of the arrays … It changes whenever the arrays change … identical arrays re-serialized (another numpy or zlib, another key order …) can change the served **bytes** and keep the **hash**" (weak w.r.t. served bytes, not w.r.t. content).
- **Consequence**: two different checksums (`037baab7…` vs `c02004e1…`) on arrays that compare byte-identical is **not explained by the code as written**. Code-consistent causes I could not settle from source (NOT FOUND): (a) the 2026-10-03 data instance ran a different numpy or juniper-data (the note §0.1 states the data checkout only for 10-04 — a different npy header writer or `ticker_vocab` string dtype would change the bytes); (b) on one day the arrays at checksum time differed from the arrays persisted (that would be a juniper-data defect, not a doc gap); (c) the 28-key comparison was value-equality rather than dtype/shape-level (e.g. a `<U4` vs wider unicode `ticker_vocab`). **F-P8 as worded ("not a content fingerprint", "zip entry timestamps") should not be filed**; what the observation supports is "the checksum differed on arrays that compare equal — cause unknown", which is a sharper and more interesting finding. The note's §1.1 conclusion (same data) rests on the array diff and survives; its explanation of the checksum does not.
- **`equities_seq` 6.0.0 on main**: `DATA/generators/equities_seq/generator.py:52-56` `VERSION = "6.0.0"` (comment cites X8 / owner ruling 2026-09-24); `DATA/tests/unit/test_val_emission_guards.py:292-301` allow-list `{"arc_agi": "4.0.0", "equities": "5.0.0", "equities_seq": "6.0.0"}` — CONFIRMED.
- dataset_id shape: `DATA/core/dataset_id.py:46-61` → `f"{generator}-{version}-{sha256(canonical json)[:16]}"` over `params.model_dump()` (plus deployment-bound defaults, `datasets.py:237-246`) — `equities_seq-6.0.0-<16 hex>` ✓; the specific hash `15505731cba5b86d` is UNTRACEABLE from source.

### 7. Matrix script fidelity vs `routers/crossval.py` + `cross_validate`, line by line — **CONFIRMED structurally; one real divergence (D1), three immaterial ones**

Same, step by step:

| step | route | script | verdict |
| --- | --- | --- | --- |
| dataset load | `APP/data.py:73-78` `JuniperDataClient(base_url, api_key)` → `download_artifact_npz` (`DC/client.py:640-680`, `np.asarray(npz[key])`, no cast) → `validate_npz_contract` (`DC/contract.py:45-83`, no mutation) → `sequence_data_from_arrays(arrays, "full")` | `MATRIX:142-156` identical chain (plus a `create_dataset` first; the route takes the id) | same |
| folds | `crossval.py:82-88` `walk_forward_folds(n, n_folds, scheme, embargo, min_train=None)` | `MATRIX:244` | same |
| factory | `crossval.py:96-110` → `build_lmu_regressor(d, theta, readout=req.readout, ridge=req.ridge, rff_features, rff_gamma, mlp_*=None, default_ridge=settings.default_ridge)` | `MATRIX:269-278` `d=16, theta=None/theta_cfg, readout="linear"/"rff", ridge∈{0.0,1.0,"gcv"}, rff_features=256/None, rff_gamma="median"/None, default_ridge=0.0` | same for the two HTTP-compared cells: service-defaults ⇒ linear/`default_ridge`=0.0 (staged YAML); E-H ⇒ rff/1.0/256/median |
| seed / time_unit | neither passes `random_seed` → `LMURegressor` default `0` (`MODEL/model.py:89`); `time_unit="steps"` | same | same |
| fit | `MC/crossval/executor.py:128,134` `fit(X[tr], y[tr], X_val=None, y_val=None, on_event=None, **{k: arr[tr]})`; `:107` `np.asarray(X)` keeps float32 | `MATRIX:185,190` `fit(Xtr, ytr, **aux_tr)` with `aux_tr = {k: v[tr]}` | same |
| predict | `executor.py:136` `predict(X[ev], **eval_aux)` | `MATRIX:193` `predict(Xev, **aux_ev)` | same |
| aggregation | `executor.py:55-66` per-metric **mean of per-fold** values and **population** std (`np.std`, ddof 0) — not pooled | `MATRIX:224-225` `np.mean` / `np.std` over folds | same |
| RFF randomness | `MODEL/readouts.py:296` `default_rng(random_seed)` created inside `fit`; `:241` median-gamma subsample then `:303-304` `W`, `b` from the same stream → deterministic given the fold's data; identical between route, script and re-runs | same objects | same — two runs of a cell give the same gamma and features |
| private attributes | `_memory_block` `MODEL/model.py:135`, `_side_channel` `:150`, `_readout` `:100`, `model.theta` `:95`; `readout.kind/ridge` `readouts.py:165,168` (linear) `:268,275` (rff), `readout.gamma` `:274`, `readout.coef` `:176` | `MATRIX:197-211` | all exist on `be081fae` |

Divergences:

- **D1 — different eval scorer, different precision.** Route: `executor.py:137` `_score` → `MC/crossval/metrics.py:32-33` → `MC/_metrics.py:22-38`, which **casts `y_true`/`y_pred` to float64** (`:30-31`) before `ss_tot`. Script: `MATRIX:179,195` `juniper_recurrence_model.model._regression_metrics` (`MODEL/model.py:48-56`), **no cast**. `y_reg` is float32 by construction (`DATA/generators/equities/generator.py:1283` `_regression_target` → `:1302` `values.astype(np.float32).reshape(-1, 1)`; carried through `derive_full_split` / `sequence_data_from_arrays` unchanged), so the script's `ss_tot` is accumulated in float32. The formulas are otherwise identical (`1 − ss_res/ss_tot`, per-column mean). Probe at fold-0 scales (n=283, target std 0.0113, prediction std 3.46) with the env interpreter: the two scorers differ by **−0.0013 to −0.0048 at |r²| ≈ 1e5** (ss_tot relative difference ≈ 1.3e-8); they are bit-identical once `y` is float64. The note's "reproduces the HTTP control to every printed digit (aggregate −20,344.64; fold 0 −93,606.23)" is therefore **PARTIAL**: it can hold at two decimals only by rounding, and the aggregate (÷5) is more likely to match than fold 0. Immaterial to any conclusion (3e-3 on 9.4e4), but the instruments are not the same scorer; the reports lane should confirm the digits in `10-crossval-service-defaults.json` vs `21-matrix-cells.json`. The train-side difference (route: `model.py:211` on float64-cast `y`; script: `MATRIX:194` on float32 `ytr`) is ~1e-8 at r² ≈ 0.45 — invisible.
- **D2 — HTTP middleware.** Route sits behind `SecurityMiddleware` with `build_rate_limiter(enabled=settings.rate_limit_enabled)` (`APP/app.py:135-139`); the stack disables it (`experiment_stack.bash:838-842` `JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED=false`, and the YAML `:17`). The script is in-process. No numeric effect.
- **D3 — data-client timeout.** Route: default **30 s** (`APP/data.py:73` constructs the client without `timeout` → `DC/client.py:178` `timeout: int = DEFAULT_TIMEOUT` → `DC/constants.py:193` `DEFAULT_TIMEOUT: int = 30`). Script: 900 s (`MATRIX:146`). No numeric effect; it is why the replay creates the dataset before the crossval call (the note's F-S9 reference) — CONFIRMED.
- **D4 — the "configured theta" axis** is `median(sum(dt))` over the **full** set (`MATRIX:245`), a value the route accepts only as a caller-supplied float; on this artifact it equals the per-fold medians (the note says so), so the axis is degenerate and measures nothing about theta sensitivity beyond "no difference here".

### 8. Conditioning script — **CONFIRMED** rebuild and rank; **REFUTED** label on "weak-direction amplification"; **PARTIAL** on "2-norm condition number"

- **Exact rebuild, same dtype**: `COND:68-69` builds the linear/ridge-0.0 model and **fits it** (so `_uses_target_dt` and theta are set as in the solve); `:70-75` rebuilds `D = [ _memory_block | _side_channel | 1 ]` from the model's own methods, which recompute the float64 memory block deterministically (no RNG in the rollout) — bitwise the matrix `LinearReadout.fit` solved (`readouts.py:105-108,189-193`). Since the solve itself ran in float64 (§4), this is **not** "a float64 rebuild of a float32 solve"; it is the same instrument. `coef` (`:85`) is the actual `lstsq` solution (`readouts.py:176,193`); `‖coef‖₂` (`:97`) on a `(242,1)` array is the 2-norm ✓. 242 columns when F = 15 ✓.
- **"numerical rank (eps)"**: `COND:78-79` `eps_rank = s.max() * max(D.shape) * np.finfo(float).eps; rank = Σ(s > eps_rank)` — numpy `matrix_rank`'s default tolerance **and** `lstsq(rcond=None)`'s cutoff (`eps·max(M,N)` relative to σ_max; `gelsd` treats `σ ≤ rcond·σ₁` as zero). So the reported rank is the effective rank the solve used, up to ULP-level disagreement between two separately computed SVDs at a borderline σ. CONFIRMED.
- **"weak-direction amplification"**: `COND:82-84` `weak = vt[-10:]`; `amp = |D @ weakᵀ| / s[-10:]` → `|row·vᵢ| / σᵢ` over the **ten smallest** singular directions; `:98-99` p99 over all rows × 10. Textually matches the note's definition. **But** the note's own table reports numerical rank 113–226 of 242 in every row, so directions 233–242 are **all below the `lstsq` cutoff**: `gelsd` zeroes their coefficients, and the pseudo-inverse's `1/σ` is **never applied** along them. The column therefore does not measure "what the min-norm solution does to a row's component along them" (note §2.4 parenthetical); it measures how far eval rows leave the training row-space along numerically-null directions — a legitimate out-of-support indicator, mislabelled. The mechanism the prose states ("multiplies … by 1/σ for every σ just above the rank cutoff") is physically right but is not what this column quantifies; the script never isolates the retained-but-tiny directions (it only counts `σ/σ_max < 1e-8` and `< 1e-6`, `:95-96`). The note's hedge ("partial view … fold 4 raw blows up along directions outside the last ten") understates this: on these ranks **none** of the last ten is inside the solve. Verdict on the label: **REFUTED**; verdict on the mechanism claim: CONFIRMED-by-theory, not by this column.
- **"σ_max / σ_min" = "2-norm condition number 1e22–1e32"**: `COND:93` divides by the smallest σ, which for a rank-deficient `D` is the rounding floor (relative 1e-32 … 1e-22). That is κ₂(D) by definition, but it is **not** the amplification bound of the computed min-norm solution (that would be σ_max/σ_rank over the retained directions, which the script does not report). The note uses the number to argue "determined by floating-point rounding"; the rank-cutoff mechanism (a σ within ULPs of `rcond·σ_max` flipping between retained/discarded between BLAS runs) is a valid reading of `lstsq`'s behaviour and does not need the 1e32 figure. **PARTIAL**.
- **Fold cuts**: `COND:61` same call as the route and the matrix script ✓.

### 9. Instrument adequacy (procedure §2 Lane A)

**Matrix script** — *Could it have produced a different answer?* Yes. It fits 24 independent cells, records per-fold `theta_resolved`, `gamma_resolved`, `ridge_resolved`, train/eval metrics, z-ranges and prediction scales (`MATRIX:200-222`), renders an errored cell as `ERROR` rather than a number (`:282-287,305-307`), and its HTTP fidelity check pins the in-process path to the served one. A theta lever, a normalisation rescue or a sane ridge-0 cell would each have shown. *What would have made it silently wrong?* (a) D1 above — immaterial; (b) `default_ridge=0.0` and the implicit `random_seed=0` are **assumed**, not read from the service: a deployment whose YAML or class default differs, or a future `build_lmu_regressor` that forwards a seed, desyncs the script from the route with no error; (c) the configured-theta axis is degenerate on this data (D4) — it cannot say anything about theta sensitivity, only that the two values coincide here; (d) nothing asserts `X.shape[2] == 15` or that `target_dt` is present — a producer change would silently change the design width the note quotes; (e) `_z_against` (`:164-175`) uses population std with the same zero-variance guard as `_standardize_fit`, so "eval memory z-range against the train fold's column statistics" is measured in the RFF rung's own units ✓.

**Conditioning script** — *Could it have produced a different answer?* Yes: on a well-conditioned design it would report rank ≈ 242 and κ₂ ~ 1e3–1e6, and the note's argument would collapse. *Silently wrong modes*: (a) the weak-direction column (label ≠ quantity, §8); (b) σ_min-based κ₂ (§8); (c) `rank` tracks `lstsq`'s cutoff only while the solver keeps `rcond=None` — an explicit `rcond` in `readouts.py:193` would desync it without error; (d) it re-fits its own model rather than reading the matrix script's — harmless because the solve is deterministic.

### 10. Other code claims in §0–§2 (and two cheap ones from §3)

| Claim | Verdict | Evidence |
| --- | --- | --- |
| F-S7: the start log prints `theta=None` | CONFIRMED | `APP/routers/crossval.py:117` logs the request/settings-resolved `theta` (`None`), never the per-fold `model.theta` set at `MODEL/model.py:177`; `APP/routers/training.py:88` same |
| the route cannot return resolved theta / selected ridge / gamma | CONFIRMED | `APP/schemas.py:285-293` `CrossValResponse` = task_type, n_folds, folds (metrics only), eval_aggregate, eval_std, dataset |
| "the service's 30 s data-client default" (F-S9) | CONFIRMED | `APP/data.py:73`, `DC/client.py:178`, `DC/constants.py:193` |
| `_STAGED_PARAM_KEYS` | NOT FOUND | 0 matches in `ML/util/`, `ML/scripts/`, and 0 in the note itself — not a claim the note makes |
| §0.1 stack staging: service block matches the suite, rate limit off | CONFIRMED | `experiment_stack.bash:820-844` (`JUNIPER_RECURRENCE_CONFIG_FILE`, `RATE_LIMIT_ENABLED=false`, `JUNIPER_DATA_URL`); `APP/settings.py:138-143`; YAML `:13-20`. Live now: `ss -ltnp` shows 127.0.0.1:**8110** (python), :**8260** (`juniper-recurre`), :8101, :8051, :**8202** (uvicorn) — consistent with §0.1/§0.3 (what pid 2857489 imports was not probed) |
| §0.1 versions | CONFIRMED | pip/import probes: juniper-recurrence 0.5.0 editable at `…/juniper-recurrence` (HEAD `be081fae`); juniper-recurrence-model 0.3.0 editable; juniper-model-core 0.2.0; juniper-service-core **dist 0.5.0 / `__version__` 0.4.0** (the note's odd pairing is real); juniper-data-client 0.5.0 editable; numpy 2.5.3; Python 3.14.7; juniper-data editable at `29be6d35` in JuniperData (dist 0.12.0, numpy 2.4.1, Python 3.14.2) |
| §0.1 "64 × 15 features", generator defaults `fundamentals_fill: nan`, `normalize_features: false` | CONFIRMED | `DATA/generators/equities/defaults.py:127-155` (15 names), `:45`, `:50`; `params.py:80-96` |
| §0.1 `sum(dt)` in calendar days | CONFIRMED (units) | `DATA/generators/equities_seq/generator.py:11-13` (docstring), `:223` `_yyyymmdd_to_ordinal(dates)` feeds `window_one_ticker` (`:228-236`); the 88–97 range is data (UNTRACEABLE here) |
| §2.1 "feature columns **z-scored** by the producer on the pooled `train` partition" | **REFUTED on the transform; CONFIRMED on the fit set** | It is **min-max to [0, 1]**: `DATA/generators/equities/generator.py:1245-1253` `_fit_normalizer` (nanmin / span, `span==0 → 1`), `:1262-1270` `(matrix − min) / span`; fit on the concatenation of each ticker's **train** rows, `DATA/generators/equities_seq/generator.py:198-210` (`params.py:94-96` says the same). The CV-fold-vs-partition leakage reading is consistent with code (the scaler sees rows 0..1345 while fold 0 trains on 0..280). The matrix measured the knob as shipped, so its numbers stand; the description of what the knob does is wrong |
| §1.4 `metrics: {train_r2, cv_r2, cv_r2_std, n_windows}`; "the loader documents the override" | CONFIRMED | `run_suite.py:94-96` (`final_metrics.r2`, `crossval.eval_aggregate.r2`, `crossval.eval_std.r2`); `JUNIPER_EXP_PROJECT_DIR` docstring `:290-306`, rebase `:309-317`; the suite's `base_config` walks five levels up (`suite yaml:9`), which from `.claude/worktrees/<x>/util/experiments/suites/p4/` lands in `.claude/` — hence the override |
| §1.3 "same model code `be081fae` both days" | UNTRACEABLE | commit is dated 2026-10-02 21:23Z (so available both days); what the 10-03 process imported cannot be read from source |
| §2.3 "15 of 20 GCV folds selected `1000.0`, the last point of `_GCV_GRID`" | ceiling CONFIRMED, count UNTRACEABLE | grid endpoint probe; the count lives in `reports/` |
| §3.2 "canopy's registry seed … fall into [the default]" | CONFIRMED (mechanism) | `juniper-canopy/src/backend/recurrence_service_adapter.py:263-268` sends `d`/`theta`/`ridge` only when set and **never `readout`** → linear rung, `ridge` unset ⇒ service default; `recurrence_backend.py:96` `_HYPERPARAM_KEYS = ("d", "theta", "ridge")` |

---

## Tallies

49 sub-claims examined (A2-01 … A2-49, enumerated below).

| Verdict | Count | Items |
| --- | --- | --- |
| CONFIRMED | **39** | 1-defaults (×4), bare-POST resolution, `default_ridge` linear-only, `_lmu_hyperparams`, E-H body, params replaced wholesale, YAML `:20` service-block pin, folds, `pass_eval_as_val`, RFF standardise, linear no-standardise, design/242, lstsq min-norm, ridge>0 normal eq, `_GCV_GRID`, GCV write-back, theta median, F·d + float64, `derive_full_split`, `fit_kwargs`, checksum code path, equities_seq 6.0.0, script = route structure, RNG determinism, private attrs, COND rebuild, numerical rank = lstsq cutoff, fold cuts, F-S7, 30 s default, 15 features + defaults, stack staging + live ports, versions table, response lacks theta/ridge/gamma, `cv_r2` extraction + `JUNIPER_EXP_PROJECT_DIR`, canopy mechanism, `dt` units, "pooled train" fit set |
| PARTIAL | **2** | "identical to every printed digit" (D1 scorer precision); "2-norm condition number" (σ_min is the rounding floor) |
| REFUTED | **3** | F-P8 mechanism (zip timestamps; checksum **is** content-determined — cause of the differing digests NOT FOUND); "weak-direction amplification = what the min-norm solution does" (those directions are discarded by `lstsq`); producer normalisation "z-scored" (it is min-max) |
| NOT FOUND / UNTRACEABLE | **5** | `_STAGED_PARAM_KEYS`; dataset_id hash value; "same model code both days"; all measured numbers (live in `reports/`, not opened by design); the brief's juniper-recurrence SHA `2c34805c` |

None of the three refutations touches the P5 verdict's load-bearing chain (service defaults → linear/ridge-0 min-norm solve on an unstandardised, rank-deficient design; E-H RFF/ridge-1.0 standardised) — that chain is CONFIRMED in code at every link. They do touch (a) the F-P8 finding as proposed for the plan, which should be re-worded or withdrawn, (b) one column of the §2.4 table and its caption, and (c) one sentence of §2.1.

## Instrument-adequacy answers (short form)

- **Matrix script**: adequate for the question asked (which configuration class blows up, and whether theta / normalisation are levers). It can produce a different answer and renders failures visibly. Its silent-wrong surface is assumption-shaped: `default_ridge=0.0` and `random_seed=0` are assumed rather than read from the running service; the eval scorer differs from the route's at the ~1e-3 level at |r²| ≈ 1e5 (float32 `y`); the configured-theta axis is degenerate on this artifact.
- **Conditioning script**: adequate for rank and for "is the design rank-deficient"; its design rebuild is exact. Inadequate as labelled for "amplification": the ten directions it measures are below the solver's cutoff in every fold the note reports, so the column cannot be what the pseudo-inverse does; and σ_max/σ_min reports the rounding floor rather than the amplification of the retained system. The mechanism the note argues is still available from the code (`lstsq` rank cutoff + retained tiny σ), just not from that column.

## Note claims about code I could NOT locate or trace

1. `_STAGED_PARAM_KEYS` — no such symbol in `ML/util/`, `ML/scripts/`, or the note (brief example only).
2. The dataset_id `equities_seq-6.0.0-15505731cba5b86d` — format confirmed; the hash needs `params.model_dump()` plus the deployment binder (`DATA/api/routes/datasets.py:237-246`) and was not recomputed.
3. The 2026-10-03 data instance's juniper-data / numpy versions — the most plausible code-consistent explanation of the checksum difference; not stated in the note for 10-03.
4. What the `:8202` listener (pid 2857489) imports (§0.3) — would need `/proc/<pid>/maps`; not probed.
5. Every measured value (r², ranks, κ₂, 15/20, timings, 88–97, 1,346/176/176, z-ranges) — by design of this lane these live in `reports/` and were not opened.

## Scratch probes (session scratchpad, not repo files)

- `checksum_probe.py` — `compute_checksum` on fixed arrays at t and t+2.5 s; zip `date_time` dump; `_GCV_GRID` endpoints; `lstsq` rcond value for (281, 242).
- `scorer_probe.py` — `juniper_model_core._metrics.regression_metrics` vs `juniper_recurrence_model.model._regression_metrics` on float32 `y` at fold-0 scales, five trials.
