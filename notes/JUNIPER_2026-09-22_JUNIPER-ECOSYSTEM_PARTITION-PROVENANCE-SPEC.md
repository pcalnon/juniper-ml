# Decision 12 — the `partition_provenance` block: specification

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-data → juniper-data-client → juniper-cascor / canopy / recurrence / ml)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0
**Document Type**: SPECIFICATION
**Last Updated**: 2026-09-23
**Status**: SPEC v1 — DRAFT, **not ready for ratification**. Consensus review round 1 (2026-09-23; three independent lanes) rated it **UNSOUND as written** in its identity, versioning and legality layers. The choice of encoding and the digest's construction held, although §14 B-5 and B-6 find gaps in the dtype allowlist and in how canonical JSON is enforced. §14 records the findings, which are **not yet folded in**. A v2 must fold them and pass its own review round before the owner ratifies anything.
**History**: Decision 12 was ruled on 2026-09-03. On 2026-09-22 the owner asked for it to be **specified before it is built**. No code has moved. §12 lists six questions. #422's fix answered OQ-4, and the other five belong to the owner. This document recommends an answer to each of those five and decides none of them, although §14 R-2 notes that §8.3 and §9.4 presume OQ-2's answer.

**Tracks**: [juniper-data#423](https://github.com/pcalnon/juniper-data/issues/423)
**Ruling of record**: [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) §9.6.3 and §9.6.6, which build on its §9.4.1 (Proposal B), §9.4.4 and §9.4.5
**Rollout context**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md) §4, §5, §10
**Grounded at** `origin/main`, re-checked on 2026-09-23:

- juniper-data `68c3cd7` (the tip, `5a408a8`, changes only CI and CHANGELOG);
- juniper-data-client `9bc8870`;
- juniper-cascor `e052ef8`;
- juniper-canopy `2f973ca2`;
- juniper-recurrence `1c84c40`, with cited files unchanged at the tip;
- open PR juniper-data#422 at head `11e45297`. Its three commits: the contract change; review round 1's fixes (`4574d7e1`); and the decision-7 fit-scope fix, with review round 2's residuals. **#422 merged on 2026-09-23 as `ce436819`, after review round 1.** A fourth commit changed tests only, and every store line this spec cites at `11e45297` is identical on juniper-data `main` at `ce436819`. It is not yet released.

Line numbers drift, so every citation also quotes a token you can grep for.
**Evidence**: [`util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py`](../util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py). Results are in §10.

> **Reading guide.** §1 is the whole decision set. §4–§9 are normative: every MUST and SHOULD is a requirement on the implementation. §3 records the code the schema has to describe, including two defects found while grounding. Both of those gate parts of the rollout. §13 says what the mechanism cannot do. **§14 records review round 1's findings against §1–§13, which are not yet folded in. Read it before relying on any normative statement above it.**

---

## 1. Summary

The ruling fixed *what* the block declares and *that* one gate checks it. This document fixes everything else.

1. **Encoding** (§4). Key `partition_provenance`, holding a **0-d fixed-width unicode array** built with `np.array(text, dtype=np.str_)` (dtype `<U{n}`). The text is canonical JSON, in exactly the `json.dumps(…, sort_keys=True, separators=(",", ":"))` form that `generate_dataset_id` already hashes. It survives every consumer's `allow_pickle=False` load; this was verified on numpy 1.26.4 through 2.5.3.
2. **Schema v1** (§5). Twelve required top-level fields: `schema_version`, `generator`, `generator_version`, `dataset_id`, `params`, `resolved_inputs`, `seed`, `strategy`, `normaliser`, `partitions`, `unpartitioned`, `digest`.
3. **Digest** (§6). The `juniper-array-v1` scheme: SHA-256 over a header that names the canonical little-endian dtype and the shape, followed by the elements in C order. Two independently written implementations agree, and the golden vectors are identical on five numpy versions.
4. **Identity** (§7). The block does not change `dataset_id`, which is hashed from the request before generation. It does change the artifact bytes and `DatasetMeta.checksum`. Because the block carries `params` exactly as hashed, the gate can **re-derive the dataset id**. That is the one derivable check that binds the declared configuration to the content address.
5. **Legality table** (§8). It is keyed on a generator *class*, looked up from the generator name that the id re-derivation authenticates.
6. **Gate** (§9). `validate_partition_provenance`, in a new `juniper_data_client/provenance.py`, **beside** `validate_npz_contract` rather than inside it:
   - absent block: tolerate;
   - integrity failure: refuse, never overridable;
   - legality failure: refuse, unless the consumer opts in and records the findings;
   - unknown `schema_version`: tolerate, reported as unverifiable.
7. **Rollout: gate first** (§11).
   - The client ships the gate as 0.6.0, after two `<0.6.0` caps are widened.
   - Consumers wire the gate in while it is still a no-op.
   - The producer ships last, and its CI runs every generator's artifact through the published gate.
8. **Two defects found while grounding** (§3.2) gate parts of that rollout.
   - F-1: no consumer can load an `arc_agi` artifact today. Filed as juniper-data#429.
   - F-2: both external stores normalised before they carved. Fixed at #422's head.

## 2. Scope and non-goals

**In scope**: the encoding, the fields, the digest, versioning and identity, the legality table, the gate, where the producer and every consumer attach, and the rollout order with its per-repo work items.

**Non-goals**, each deliberate:

- **No `DatasetMeta` field.** The ruling puts the block in the NPZ for a reason. All three cascor ingestion paths keep only `dataset_id` and download the NPZ (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3). A new `DatasetMeta` field would also re-open risk R-3 (`…PARTITION-IMPLEMENTATION-PLAN.md` §5): stored metadata is loaded with `DatasetMeta(**meta_dict)` (`juniper_data/storage/local_fs.py:261`).
- **No `seed_sensitivity`.** The ruling did not adopt it (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3). Its §9.4.4 item 4 showed it is not a property of the run.
- **No check on the arrays themselves.** The row-reuse and degeneracy assertion was dropped on 2026-09-03 (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.4). §13 records what that leaves uncovered.
- **No re-derivation of partition *counts* from `params`.** §8.4 explains why.
- **No backfill.** Stored artifacts are never rewritten. The gate reports them as `absent` (§9.4).
- **No change to `validate_npz_contract`.** Its tabular path "is untouched and returns immediately" (`juniper_data_client/contract.py:13`), and callers rely on that.

## 3. Ground truth

### 3.1 How the 16 generators and the 2 stores partition today

The route computes `dataset_id` before generation, from `params.model_dump()` after `bind_deployment_defaults` (`juniper_data/api/routes/datasets.py:146-154`). It then pops the reserved non-array channels `scaling`, `truncation` and `data_quality`, so that "the stored arrays stay array-only" (`:284-298`).
Finally it checksums (`:300`) and persists (`:355`); the stores write `np.savez_compressed` (`storage/local_fs.py:211`). The 16 generators are registered in `GENERATOR_REGISTRY` (`api/routes/generators.py:45`). There are six distinct behaviours to describe:

| class | members | how the cut is made | seed | normaliser as implemented |
| --- | --- | --- | --- | --- |
| `synthetic_tabular` | spiral, xor, gaussian, circles, moon, checkerboard | `resolve_counts_for_params`, then `partition_and_assemble` (e.g. `spiral/generator.py:45-52`): one realisation, one permutation (`core/split.py:43`), then a contiguous cut (`split_three_way`, `:211`). The sizing mode is `PartitionParams.sizing_mode` (`core/partition_params.py:81`) | int or null; default `DEFAULT_GENERATOR_SEED` (`core/constants.py:92`), read from `JUNIPER_DATA_DEFAULT_GENERATOR_SEED` at import | none |
| `real_carve` | mnist, csv_import, arc_agi | Same helpers over a fixed corpus (`mnist/generator.py:94-96`, `csv_import/generator.py:63-64`, `arc_agi/generator.py:106-118`). `CarveOnlyPartitionParams` rejects `additive` (`core/partition_params.py:110-111`) | int or null (note 1) | mnist: `/ 255.0` (`:124`). csv_import: min-max fitted on train, falling back to val and test (`csv_import/generator.py:85-100`). arc_agi: none |
| `temporal_rows` | equities | Its own per-ticker code: each ticker's date-sorted rows are cut by independently rounded ratios with an end-trim, then concatenated split-major (`equities/generator.py:346-372`). `EquitiesParams` is a plain `BaseModel` (`equities/params.py:47`) | Carried but "Unused for the temporal split" (`equities/params.py:137`). `end_date` defaults to the wall clock (`equities/generator.py:315`) | Optional min-max fitted on train, falling back to every conditioned row (`:393-396`) |
| `temporal_windows` | multi_sine, mackey_glass, ar_p, irregular_sine, delay_product | One series, windowed (note 2). Windows are cut by index at `temporal_split_indices`, and test takes the remainder (`_sequence.py:277`, `:376`) | `seed: int`, default 0, never null (`_synthetic.py:65`); inert for mackey_glass at `init_noise_std=0` | None: "The NPZ stays RAW either way" (`_synthetic.py:66`) |
| `temporal_entity_windows` | equities_seq | Per ticker, windows are assigned by **target date** against that ticker's `temporal_split_indices` row cuts (`equities_seq/generator.py:224-234`, `_sequence.py:125-133`). There is no embargo: `embargo: bool = False` (`_sequence.py:71`) is never passed | As equities | Train rows of every ticker, falling back to all frames (`equities_seq/generator.py:194-206`) |
| `external_store` | huggingface, kaggle (PR #422) | An optional pre-shuffle, **only if `seed is not None`**, then `carve_three_way` (`external_partition.py:66`), 0.8 / 0.1 / 0.1 by default (note 3) | int or null. Null means **no shuffle**, unlike the generators | HF images: the constant `/ 255.0` (`hf_store.py:282`). HF tabular and Kaggle min-max: fit on `X_train` after the carve (note 3) |

Notes on the table:

1. **`real_carve` seeds.** mnist also passes the seed to the HF `ds.shuffle(seed=…)` before subsetting (`mnist/generator.py:115-116`). arc_agi branches on `seed is None` when it samples tasks (`arc_agi/generator.py:177-184`, `:209-216`).
2. **`temporal_windows` plumbing.** These generators reach the windower through `build_sequence_arrays` (`_synthetic.py:100`) or through `window_timed_series` (`irregular_sine/generator.py:57`, `delay_product/generator.py:71`). A train-fitted *advisory* scaling descriptor goes to `DatasetMeta`, not to the arrays (`_synthetic.py:111-130`). mackey_glass's inert seed is recorded in `…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.5.
3. **`external_store`, at PR #422's head `11e45297`.**
   - **Pre-shuffle.** HF `ds.shuffle(seed=seed)` (`hf_store.py:132-133`); Kaggle `random.seed(seed); random.shuffle(data)` (`kaggle_store.py:195-199`).
   - **Ratios.** Checked before any download by `validate_carve_ratios` (`external_partition.py:45`), after conversion to plain `float`.
   - **Normaliser.** HF tabular `/ max` and Kaggle min-max are fit on `X_train` after the carve and applied unchanged to val and test (`hf_store.py:152`, `kaggle_store.py:241`). That is F-2's fix, §3.2.

### 3.2 Findings made while grounding

- **F-1: No consumer can load an `arc_agi` artifact. Verified.**
  - **Cause.** `task_ids` is built as `np.array(task_ids, dtype=object)` (`arc_agi/generator.py:275`, and also `:262`), so `np.savez` pickles it.
  - **Failure.** `download_artifact_npz` loads with numpy's default `allow_pickle=False` and reads every key (`juniper_data_client/client.py:679-680`). It raises `ValueError: Object arrays cannot be loaded when allow_pickle=False`.
  - **Reproduction.** Checks P3 and L2 reproduced this through the real generator, run offline against local task JSON, and through the real client.
  - **Silent cache loss.** juniper-data's cached store hits the same error inside `contextlib.suppress(Exception)` (`storage/cached.py:135-141`), so it never caches these artifacts and says nothing.
  - **Why nothing caught it.** No test round-trips an `arc_agi` artifact through `np.load`, and `allow_pickle` appears nowhere in juniper-data.
  - **Why it matters here.** It proves the hazard in §4.2 is live. `task_ids` also cannot be digested (§6) until it is a `<U` array, like `ticker_vocab` (`equities/generator.py:414`).
  - **Status.** Filed as juniper-data#429 on 2026-09-23.
- **F-2: Both external stores fit their normaliser before carving. FIXED at #422's head `11e45297`.**
  - **Where it was.** At `33dffb8e`, HF tabular `X / X.max()` (`normalize=True` by default) and Kaggle min-max (off by default) ran before `carve_three_way`. Since `11e45297` both are fit on `X_train` after the carve and applied unchanged to val and test (`hf_store.py:152`, `kaggle_store.py:241`).
  - **Why it mattered.** This was the decision-7 leak that juniper-data#314 removed from `csv_import`. A truthful block would have had to declare it as `all_rows`, which §8 makes illegal.
  - **Exposure.** Neither store has a route or a service caller (PR #422's description), so no served artifact was affected. OQ-4 is answered by the fix.
- **F-3: `DatasetMeta.checksum` is not a hash of the served artifact.**
  - **What it hashes.** `np.savez` over sorted keys (`core/artifacts.py:44-45`, `:62-63`). The stores serve `np.savez_compressed` instead.
  - **Why the block cannot rely on it.**
    - It can be checked only by re-serialising, which reproduces it under a single numpy version (check C1).
    - It lives where cascor never reads it (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3).
    - One hash cannot say *which* partition changed.
  - **Consequence.** The block carries its own digest for every array.
- **F-4: One `dataset_id` can name different equities content on different days.** This is documented (`equities/params.py:137`). The block makes it visible by recording the resolved `end_date` (§5.1).

## 4. Encoding inside the NPZ

### 4.1 The rule

- **Key and value.** The key is **`partition_provenance`**. The value is `np.array(text, dtype=np.str_)`: a **0-d** array whose dtype is `<U{len(text)}`.
- **Serialisation.** `text` is `json.dumps(block, sort_keys=True, separators=(",", ":"))`, with the `json` module's other defaults left alone (`ensure_ascii=True`, `allow_nan=True`). This is the same call `generate_dataset_id` makes (`core/dataset_id.py:57`).
  - `ensure_ascii` keeps the payload ASCII.
  - `allow_nan` is required, because a legal `params` can hold `inf`. Check J1 shows `Infinity` round-trips. Strict JSON parsers outside Python would reject that token; every consumer is Python.
- **Decoding.** The value MUST be 0-d with `dtype.kind == "U"`, and `json.loads(str(arr.item()))` MUST yield an object. Anything else is a malformed block (§9.4).
- **No `StringDType`.** Writers MUST NOT use numpy 2's `StringDType`. It saves as a pickled object, and an `allow_pickle=False` load of it fails (check E4). numpy itself warns: "Custom dtypes are saved as python objects using the pickle protocol". `np.array(str)` infers `<U` (check E3), but writers pass `dtype=np.str_` explicitly anyway.

### 4.2 Alternatives rejected

| option | why not |
| --- | --- |
| object array or pickled dict | Unloadable under `allow_pickle=False`; F-1 is the live proof (checks E6, P3, L2) |
| numpy 2 `StringDType` | Saved as a pickled object, so it fails the same way (check E4) |
| `uint8` array of UTF-8 bytes | It round-trips (check E2) and is 4× smaller, but any consumer walking the keys sees a numeric array, and there is no precedent for it. `<U` has one: `ticker_vocab` already reaches every consumer as `np.str_` (`equities/generator.py:414`) |
| `DatasetMeta`, or a reserved channel such as `scaling` | Invisible to cascor (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3). The route pops those channels *out* of the NPZ (`datasets.py:284-298`) |

`<U` costs 4 bytes per character. The spiral block in check P1 is 1,155 characters, and `np.savez_compressed` absorbs most of that: the stored 170-row artifact grows from 2,657 to 3,822 bytes. `<U` strips trailing NULs (check E5), but canonical JSON never contains a raw NUL, because `json.dumps` escapes it as `\u0000`.

### 4.3 Naming rules and consumer safety

The key MUST NOT end in `_train`, `_val`, `_test` or `_full`. Readers that work across splits enumerate keys by suffix. For example, `derive_full_split` in juniper-recurrence-model collects `key.endswith(f"_{present[0]}")` (`juniper_recurrence_model/data.py:109`). A key with a split suffix would therefore be read as a partition array.

No existing reader breaks on an extra `<U` key:

- cascor's CLI reader states "Extra keys are ignored" (`src/spiral_problem/data_provider.py:218`);
- cascor's service reads named keys only (`_artifact_to_tensors`, `src/api/lifecycle/manager.py:4068`);
- canopy walks `_VALIDATED_PARTITIONS` only (`src/demo_mode.py:848`);
- juniper-data's metadata readers read named keys (`core/meta.py:80-86`, `:164`).

### 4.4 Where the producer writes it

- **Placement.** The route inserts the block **after** it pops the reserved channels and **before** `compute_checksum`, that is, between `datasets.py:298` and `:300`. The checksum then covers the block, and the stored artifact carries it.
- **Counts and digests.** These are computed **from the arrays about to be written**, never taken from the generator's own bookkeeping. The block therefore cannot disagree with the artifact at the moment it is produced.
- **What only the generator knows.** Three facts come from the generator: the method, the fit scope with its stems, and the resolved inputs. They reach the route through one new reserved channel, `partition_facts` (proposed name), popped beside the existing three (`core/meta.py:172-229`).
  - Anything that calls `generate()` directly sees that channel, just as it sees `scaling` today. juniper-ml's `util/snapshot_attribute.py:341` is one such caller.
  - The stores bypass the route, so they MUST call the same builder before `self._cache_store.save(...)` in their loaders (`hf_store.py:199` and `kaggle_store.py:288` on PR #422's head `11e45297`).

## 5. Schema v1

### 5.1 Fields

All twelve top-level fields are REQUIRED. A v1 reader MUST ignore unknown fields; §7.1 explains why.

| field | type | units / format | meaning and source |
| --- | --- | --- | --- |
| `schema_version` | int | — | `1` |
| `generator` | string | registry key, or `huggingface` / `kaggle` | `DatasetMeta.generator`; hashed into the id |
| `generator_version` | string | SemVer | The `VERSION` hashed into the id |
| `dataset_id` | string | `{generator}-{version}-{16 hex}`; the stores add a readable prefix | The id the producer assigned (`datasets.py:150`; `external_dataset_id`, `external_partition.py:116`) |
| `params` | object | JSON | **Exactly** the dict that was hashed: `params.model_dump()` after `bind_deployment_defaults` (`datasets.py:146-154`). For the stores, the dict `external_dataset_id` HASHED, not the one `DatasetMeta.params` records (§7.2, §14 B-3). The recorded dicts are `params = {` at `hf_store.py:162` and `kaggle_store.py:256` on `11e45297` |
| `resolved_inputs` | object | JSON | Values that decide the content but are absent from `params`. For the equities pair, `end_date` (`YYYY-MM-DD`) when `params.end_date` is null (`equities/generator.py:315`). `source_sha256` if OQ-3 is accepted. Otherwise `{}` |
| `seed` | int or null | — | The seed the run used. It equals `params["seed"]` whenever that value is an integer. Null means OS entropy for a generator, or no shuffle for a store |
| `strategy.method` | enum | §5.2 | How rows were assigned to partitions |
| `strategy.sizing_mode` | `"additive"`, `"carve"` or null | — | `params.sizing_mode` where the params model has one (`core/partition_params.py:81`); `"carve"` for the stores; null for the temporal classes |
| `normaliser.fit_scope` | enum | §5.3 | What the feature statistics were fitted on |
| `normaliser.stems` | list of string | array stems | The stems the transform was applied to, e.g. `["X"]`; `[]` when `fit_scope` is `none` |
| `partitions` | object | keys exactly `train`, `val`, `test` | Each is `{"rows": int, "arrays": {stem: digest}}` |
| `unpartitioned` | object | key → digest | Every other array key except the block itself: `ticker_vocab`, and `task_ids` once F-1 is fixed. `{}` if there are none |
| `digest` | object | — | `{"algorithm": "sha256", "scheme": "juniper-array-v1"}` (§6) |

Rules for `partitions`:

- **`rows`** is the length of the leading axis: samples for a 2-D artifact, windows for a 3-D one.
- **`arrays`** names every `{stem}_{split}` key in the artifact, and MUST include `X` and `y` in all three partitions.
- **Empty partitions.** A partition with 0 rows is declared, never omitted (`test_val_emission_guards.py:162-163`).

**Deliberately absent**: the producer's package version, the numpy version, host names and timestamps. The block is a pure function of generator, version, `params`, resolved inputs and arrays. So for a seeded request with pinned inputs, **one `dataset_id` always carries one byte-identical block**, and W6 in §11 tests exactly that. `DatasetMeta.created_at` already records *when*.

### 5.2 `strategy.method`

| value | meaning | produced by |
| --- | --- | --- |
| `shuffled_carve` | One realisation, one permutation of all rows, then a contiguous train, val, test cut. Surplus rows at the shuffled tail are dropped | `partition_and_assemble(shuffle=True)` (`core/split.py:584`); a store given a seed |
| `ordered_carve` | The same cut, in generation or read order | `partition_and_assemble(shuffle=False)`; a store with a null seed |
| `temporal_rows_per_entity` | Each entity's date-sorted rows are cut earliest-first, and the partitions are concatenated split-major in `ticker_vocab` order | equities (`equities/generator.py:346-372`) |
| `temporal_windows` | One series is windowed, and the windows are cut by index. Test takes the remainder. Neighbouring partitions share lookback input steps | `_sequence.py:277`, `:376` |
| `temporal_windows_per_entity` | For each entity, windows are assigned by target date against that entity's row cuts. No embargo | equities_seq (`equities_seq/generator.py:224-234`) |

### 5.3 `normaliser.fit_scope`

| value | meaning | where it occurs today |
| --- | --- | --- |
| `none` | No transform on any emitted array | The 2-D synthetics; the sequence synthetics, whose advisory scaling lives in `DatasetMeta` (`_synthetic.py:66`); any run with its normalise flag off |
| `constant` | A data-independent transform | mnist `/ 255.0` (`mnist/generator.py:124`); HF images (`hf_store.py:282`) |
| `train` | Statistics fitted on the train partition only, as decision 7 requires | csv_import (`csv_import/generator.py:95`), equities (`:395`), equities_seq (`:200-206`) whenever train is non-empty |
| `non_train_fallback` | Train was empty, so the fit used other rows | The same three generators' fallback branch; pinned by `test_normaliser_fit_scope.py:172` |
| `all_rows` | Fitted on every row before the carve | HF tabular and Kaggle (F-2) |

### 5.4 Values by class

| class | `method` | `sizing_mode` | `seed` | `fit_scope` | `resolved_inputs` | `unpartitioned` |
| --- | --- | --- | --- | --- | --- | --- |
| `synthetic_tabular` | `shuffled_carve` or `ordered_carve`, following `params.shuffle` | `params.sizing_mode` | int or null | `none` | `{}` | `{}` |
| `real_carve` | as above | `carve` | int or null | mnist: `none`, `constant`. csv_import: `none`, `train`, `non_train_fallback`. arc_agi: `none` | csv_import: `source_sha256` (OQ-3) | arc_agi: `task_ids` |
| `temporal_rows` | `temporal_rows_per_entity` | null | int or null (inert) | `none`, `train`, `non_train_fallback` | `end_date` when `params.end_date` is null | `ticker_vocab` |
| `temporal_windows` | `temporal_windows` | null | int, never null | `none` | `{}` | `{}` |
| `temporal_entity_windows` | `temporal_windows_per_entity` | null | int or null (inert) | `none`, `train`, `non_train_fallback` | as `temporal_rows` | `ticker_vocab` |
| `external_store` | `shuffled_carve` with a seed; otherwise `ordered_carve` | `carve` | int or null | HF: `none`, `constant`. Kaggle: `none` | (OQ-3) | `{}` |

### 5.5 Example

The real block from check P1 (spiral, `n_points_per_spiral=50`, `seed=7`). Digests and most `params` are elided, and the lines are wrapped for reading; the stored text is a single line.

```json
{"dataset_id":"spiral-3.0.0-e47858c8932eb006","digest":{"algorithm":"sha256","scheme":"juniper-array-v1"},
 "generator":"spiral","generator_version":"3.0.0","normaliser":{"fit_scope":"none","stems":[]},
 "params":{"n_points_per_spiral":50,"seed":7,"shuffle":true,"sizing_mode":"additive","val_percent":40.0},
 "partitions":{"test":{"arrays":{"X":"…","y":"…"},"rows":30},"train":{"arrays":{"X":"…","y":"…"},"rows":100},
               "val":{"arrays":{"X":"…","y":"…"},"rows":40}},
 "resolved_inputs":{},"schema_version":1,"seed":7,"strategy":{"method":"shuffled_carve","sizing_mode":"additive"},
 "unpartitioned":{}}
```

## 6. Digest — `juniper-array-v1`

For each array `a`:

```text
canon  = a.dtype with little-endian byte order          (numpy: a.dtype.newbyteorder("<"))
header = "juniper-array-v1" LF canon.str LF shape LF     (ASCII)
         canon.str is numpy's dtype string: "<f4", "<f8", "<i4", "<i8", "|u1", "|b1", "<U4", ...
         shape is the decimal dimensions joined by ","   ("0,2" for an empty (0, 2) array)
data   = every element in C (row-major) order, little-endian IEEE-754 or two's complement;
         each "U" element as UCS-4 little-endian code points, NUL-padded to the item size
digest = lowercase hex SHA-256(header || data)
```

- **Allowed dtype kinds**: `b`, `i`, `u`, `f` and `U`. Object, structured and sub-array dtypes, and every other kind, are outside the scheme. A producer MUST NOT emit them, and the gate treats one as a malformed block. Every array emitted today is in scope except `arc_agi`'s `task_ids` (F-1).
- **Invariant** under memory layout (Fortran order, strided views), byte order, and an NPZ round trip, compressed or not.
- **Sensitive** to shape, to dtype and to every bit: `+0.0` and `-0.0` differ, as do different NaN payloads. It is a byte digest, not a value digest (checks D2, D3).
- **Streaming.** Implementations MAY feed `data` into the hash in pieces rather than building it in memory.
- **Why not reuse cascor's precedent**, `calculate_tensor_checksum` (`src/snapshots/snapshot_common.py:292-303`, which hashes `numpy().tobytes()`)? It hashes the bytes alone. Arrays of different shape or dtype but identical bytes therefore collide (check D3's reshape and reinterpret cases), and the digest depends on the host's byte order.
- **Golden vectors.** Every implementation MUST reproduce these nine digests:

| input (numpy expression) | digest |
| --- | --- |
| `np.zeros((0, 2), dtype="<f4")` | `5e67ae4f1967f08822c4b382bb0d123b3c859c20cea23bb0e3e4c805a3bc753b` |
| `np.arange(6, dtype="<f4").reshape(2, 3)` | `ec7f2a61261a10346a0e9ffea3e49795d9a1735ddecd8dab83c45d951ad413a2` |
| `np.array([[1, 0], [0, 1], [1, 0]], dtype="<f4")` | `fa7ecca04f364d7524e7306a784b8a7d8688a3b8292c100378ee27aa98e46dd3` |
| `np.array([20260922, 20260923], dtype="<i4")` | `f0bcbbd287116e06af3f4a304aaaf1f36bf1a0a38a4614d600f6bb6e49652996` |
| `np.ones((2, 3), dtype="u1")` | `9294fb7ea8071edc6e670ffb7cc19c8c70209bff73f838c45659fd5842e8fb2a` |
| `np.array(["AAPL", "MSFT"], dtype="<U4")` | `4c5ebf265609a4cda4da5ef090e5f29bd68005223a5ad81aa6eb5dabbfde2c76` |
| `np.linspace(0, 1, 6, dtype="<f4").reshape(2, 3, 1)` | `14344b84e68d18df440c751373caf89cc9e5a396bbe7c3b62650850cbcdf6783` |
| `np.array([True, False, True])` | `20151a47ee82d897ad53febdfc5f803d4c9093ed018af3402d7bc6c77e801d3c` |
| `np.arange(6, dtype="<f8").reshape(3, 2) / 7.0` | `21aaf714507457e27a6d7eb587d61e098b434a533b05c3080de270a8f5358f15` |

Their fingerprint is `47fba46f786387baf2c1d6e06f7d5825306cd649554413e9dd4b0df1aa6c5733`: the SHA-256 of the canonical JSON of all nine, keyed `g1_…` to `g9_…` as in the script.

## 7. `schema_version`, `generator_version` and `dataset_id`

### 7.1 `schema_version`

- **What it is.** An integer, `1` for this document, independent of `generator_version`.
- **When it changes.** Only when a v1 reader would **misjudge** a new block: a changed digest scheme, a changed meaning, or a removed field.
- **Adding a field does not change it**, because v1 readers ignore unknown fields.
- **Old and new versions.** A gate MUST verify every schema version up to its own. For a higher version it MUST return `unverifiable`: tolerate, never refuse. That way a producer upgrade cannot break an older consumer.
- **Not in the id.** `schema_version` is not hashed into `dataset_id`.

### 7.2 What the block changes, and what it makes checkable

- **`dataset_id` does not change.** It is `sha256` over `json.dumps` of `generator`, `version` and `params`, truncated to 16 hex digits and computed before generation (`datasets.py:150-154`, `core/dataset_id.py:46-61`). Nothing generated reaches it.
- **The artifact bytes and `DatasetMeta.checksum` do change**, because the block is inserted before `compute_checksum` (§4.4). Check P1 ran the real `compute_checksum` over a dict carrying the block.
- **The id becomes checkable.**
  - **The check.** `params` is carried exactly as it was hashed, so the gate recomputes the suffix `f"{generator}-{generator_version}-{hash16}"` and requires `dataset_id` to end with it. "Ends with" admits the stores' readable prefix (`external_partition.py:140`, `return f"{prefix}-{generate_dataset_id(...)}"`).
  - **Evidence.** Check J2 re-derived the real id for the default params of all 16 generators after a JSON round trip. Check P2 shows that editing one `params` value is caught.
  - **When it is skipped.** `generate_dataset_id` mixes in a per-call nonce when `params.get("seed") is None` (`core/dataset_id.py:54-55`). The gate mirrors that condition and skips the check whenever the hashed `params` has no seed value.
- **The stores.** Since PR #422's `4574d7e1`, a null store seed is **not** given the nonce.
  - `external_dataset_id` (`external_partition.py:116`) hashes a copy of `params` in which a `None` seed becomes the fixed marker `"unshuffled"` (`:139`). The stores shuffle only when a seed is given, so an unseeded load is repeatable and should keep one id. `DatasetMeta.params` keeps the real `None`.
  - **So store ids are derivable, provided the block's `params` carries the HASHED copy, marker included, not `DatasetMeta.params`.** The producer MUST build the store block from the dict it hashed.
  - That is also why L5 in §8.1 compares against integer seeds only.

### 7.3 Is a generator `VERSION` bump required? (OQ-1)

**Not for correctness.** The arrays do not change, and consumers tolerate a missing block.

**Recommended anyway: a MINOR bump** in the release that starts emitting the block:

- the generators `3.0.0 → 3.1.0`;
- the equities pair `5.0.0 → 5.1.0`;
- `EXTERNAL_STORE_VERSION` `3.0.0 → 3.1.0`.

Reasons for the bump:

- **The decision-11 precedent says so in as many words**: "Which shape a consumer sees is then decided by cache state rather than by the contract" (`juniper_data/tests/unit/test_val_emission_guards.py:241-244`).
- **Without a bump, cache state decides what consumers see.**
  - A request made after the upgrade can be served a cached artifact without the block, under the same id.
  - The gate then reports `absent` for an artifact the new producer would have stamped.
  - "`generator_version` ≥ 3.1.0 ⟹ block present" can then never become an invariant.
- **MINOR is the right size**, because the change is additive. It also clears decision 11's floor test, which reads only the major version (`:288`).
- **One edit rides along.** That test's allow-list (`:290-293`, `ahead == {"equities": "5.0.0", "equities_seq": "5.0.0"}`) is rewritten in the same PR.

**Cost:**

- Every cached artifact misses once and is regenerated. equities goes to the network, and `arc_agi` from HF took 511 s (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.4.6).
- Ids pinned in configs stop matching new requests, although the old ids still resolve in the store.

## 8. The legality table

The gate finds a block's class from `generator`, a value the id re-derivation authenticates (§7.2). It does so through a client-side map of the 16 registry names plus `huggingface` and `kaggle`. The client's constants already name all 16 (`juniper_data_client/constants.py:283-307`, the `GENERATOR_*` block). An unknown generator gets only the class-independent rules; being unknown is never, on its own, a reason to refuse.

### 8.1 Class-independent rules

| rule | condition | derivable? |
| --- | --- | --- |
| L1 | `method`, `sizing_mode` and `fit_scope` are members of their enums | — |
| L2 | `fit_scope` is not `all_rows` (decision 7) | no |
| L3 | `fit_scope == "non_train_fallback"` implies `partitions.train.rows == 0` | yes; rows are verified against the array shapes |
| L4 | `fit_scope == "none"` if and only if `normaliser.stems == []`; otherwise every stem listed is a declared stem | yes |
| L5 | `seed` equals `params["seed"]` when that value is an integer, and is null otherwise | yes; `params` is id-bound |
| L6 | When `"shuffle" in params` and the method is a carve: `method == "shuffled_carve"` if and only if `params["shuffle"]` is true | yes |
| L7 | `"sizing_mode" in params` implies `strategy.sizing_mode == params["sizing_mode"]` | yes |

### 8.2 Class rows

Each row is a (class, method, sizing_mode) triple. Any triple not listed is **illegal**.

| class | method | sizing_mode | legal `seed` | legal `fit_scope` | further |
| --- | --- | --- | --- | --- | --- |
| `synthetic_tabular` | `shuffled_carve`, `ordered_carve` | `additive`, `carve` | int, null | `none` | — |
| `real_carve` | `shuffled_carve`, `ordered_carve` | `carve` | int, null | mnist: `none`, `constant`. csv_import: `none`, `train`, `non_train_fallback`. arc_agi: `none` | `additive` is illegal. The params model rejects it (`partition_params.py:110-111`), so a block that declares it did not come from this code |
| `temporal_rows` | `temporal_rows_per_entity` | null | int, null | `none`, `train`, `non_train_fallback` | a null `params.end_date` requires `resolved_inputs.end_date` |
| `temporal_windows` | `temporal_windows` | null | int only | `none` | — |
| `temporal_entity_windows` | `temporal_windows_per_entity` | null | int, null | `none`, `train`, `non_train_fallback` | as `temporal_rows` |
| `external_store` | `shuffled_carve` | `carve` | int only | HF: `none`, `constant`. Kaggle: `none` | — |
| `external_store` | `ordered_carve` | `carve` | null only | as above | — |

### 8.3 What the gate does with an illegal combination

- **By default it raises.**
- **Opting in.** A consumer may pass `allow_illegal=True`. The gate then returns the findings with status `accepted_with_findings` instead of raising.
- **The consumer's duty.** It MUST then record those findings on the run, the way cascor records the §6.4 override: as a caveat on the reported metrics, behind `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT` (`src/api/lifecycle/manager.py:3739-3746`).
- **Integrity failures (G0–G4 in §9.3) can never be overridden.** A block that disagrees with its own artifact describes some other artifact. See OQ-2.

### 8.4 Deliberately not checked: counts re-derived from `params`

Some counts are closed-form in `params` and the verified row counts:

- additive `val = round(train × val_percent / 100)` (`core/split.py:200-201`);
- a carve whose ratios cover the whole dataset (`:489-490`);
- `temporal_split_indices` over the window total (`:343`).

**Why v1 does not re-derive them.** Doing so would copy the producer's rounding and trim logic into the client, including `resolve_partition_counts`'s negative-remainder path (`:504-510`). A mismatch would then be as likely to be a client bug as a producer bug. **v1 checks counts against array shapes only**, which is what the ruling itself says. Revisit this if a sizing defect ever ships.

## 9. The gate

### 9.1 Where it lives

**Location.** A new module, `juniper_data_client/provenance.py` (proposed). It is exported from the package root beside `validate_npz_contract` (`juniper_data_client/__init__.py:9,16`).

**It is not placed inside `validate_npz_contract`**, for three reasons:

- `validate_npz_contract`'s tabular path returns before any check (`contract.py:73-74`);
- cascor never calls it;
- canopy does not gate on it. At canopy main `2f973ca2` it does not call it at all. The owner ruled on 2026-09-22 (canopy#559) that it runs **advisory-only**, which the open PR juniper-canopy#663 implements. A helper that canopy may only warn on cannot host a gate canopy must enforce.

Hosting provenance there would reach only one of the three consumers.

**The client, not the producer, hosts the gate.** Every consumer already depends on the client. The producer does not at runtime: juniper-data pins the client only in its `test` extra (`pyproject.toml:123`). So juniper-data keeps its own builder and digest (W6 in §11). Two things hold the two implementations together: the golden vectors (§6), and a producer test that runs every generator's artifact through the published gate.

### 9.2 Interface (proposed names)

```python
def validate_partition_provenance(
    arrays: Mapping[str, np.ndarray],
    *,
    dataset_id: str | None = None,   # the id the consumer requested, when it has one
    allow_illegal: bool = False,
) -> ProvenanceReport: ...            # status, findings, decoded block
# on refusal: raises JuniperDataProvenanceError, a subclass of JuniperDataContractError
```

Also exported: `decode_partition_provenance`, `array_digest`, `build_partition_provenance` (for the `testing` fakes and third-party producers), `NPZ_KEY_PARTITION_PROVENANCE` and `ARRAY_DIGEST_SCHEME`. `JuniperDataContractError` is already a `ValueError` subclass (`exceptions.py:82`: `class JuniperDataContractError(JuniperDataClientError, ValueError):`), so existing `except ValueError` call sites keep working.

### 9.3 Checks, in order

Every finding is collected; no check stops the others from running.

| id | check | re-derives or trusts |
| --- | --- | --- |
| G0 | Decode (§4.1); `schema_version`; the twelve fields and their types; `digest` is `sha256` with `juniper-array-v1` | — |
| G1 | Coverage: every artifact key except the block is declared, every declared key exists, and `X` and `y` are present in all three partitions | re-derives |
| G2 | Counts: each declared array's `shape[0]` equals its partition's `rows` | re-derives |
| G3 | Digests: recompute each one (§6) | re-derives |
| G4 | Identity: `dataset_id` equals the requested id, and the id re-derivation of §7.2 succeeds | re-derives |
| G5 | Legality: §8.1 and §8.2 | Trusts `method`, `fit_scope`, `stems`, `resolved_inputs`, and whether a non-null seed actually mattered. Constrains only their combinations |

### 9.4 Outcomes

| state | status | action |
| --- | --- | --- |
| Key absent (every artifact minted before the producer ships) | `absent` | Tolerate: "Legacy artifacts without the block must stay loadable, per the contract rule 'tolerate, never require'" (juniper-data#423). See §14 B-4 for the case where the requested id proves a block must exist |
| `schema_version` higher than the gate knows | `unverifiable` | Tolerate, and log a warning |
| G0 fails for a known version (a malformed block) | — | Refuse; not overridable |
| Any G1–G4 finding | — | Refuse; not overridable |
| G5 findings only | — | Refuse. With `allow_illegal=True`: `accepted_with_findings`, and the consumer records them |
| No findings | `verified` | Proceed |

### 9.5 Call sites

Each consumer calls the gate immediately after downloading the artifact, where `dataset_id` is still in scope.

| repo | site (origin/main) | note |
| --- | --- | --- |
| cascor | `src/api/lifecycle/manager.py:4210` (`_reload_dataset`) | Before `_artifact_to_tensors` (`:4239`). Publish the status on `get_status()` beside `dataset_shortfall` (`:2846`) and `current_dataset` (`:2868`) |
| cascor | `src/api/app.py:563` (auto-start) | Before `_artifact_to_tensors` (`:603`) |
| cascor | `src/spiral_problem/data_provider.py:193` (the CLI) | Before `_convert_arrays_to_tensors` (`:196`) |
| canopy | `src/demo_mode.py:1074` and `:1977` | Before `_validate_npz_arrays` (`:1082`, `:2014`). See OQ-5 |
| recurrence | `juniper-recurrence/juniper_recurrence/data.py:76-77` | After `validate_npz_contract`. Also the file loader `juniper_recurrence_model/data.py:59`, which bypasses the client |
| data | the test suite | Every generator's artifact goes through the published gate (W6 in §11) |

juniper-ml has no permanent consumer. No file outside `util/ad-hoc/` calls `download_artifact_npz`, and `util/snapshot_attribute.py:341` generates in-process, so it never sees an NPZ.

## 10. Verification — the round-trip script

`util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py` runs 18 checks, and it was run in five interpreters on 2026-09-22.

| interpreter | Python / numpy | producer and client under test | result |
| --- | --- | --- | --- |
| `JuniperData` | 3.14.2 (free-threaded) / 2.4.1 | editable installs of the checkouts listed in the header | 15 PASS, 3 INFO, 0 FAIL |
| `JuniperCascor1` | 3.14.7 / 2.5.3 | the same checkouts | 15 PASS, 3 INFO, 0 FAIL |
| `JuniperCanopy1` | 3.13.13 / 2.4.6 | client 0.5.0, plus a **stale site-packages juniper-data 0.6.0** | 13 PASS, 3 INFO, 1 SKIP, 1 FAIL. The FAIL is P1: juniper-data 0.6.0 predates `sizing_mode`, so the producer-side results say nothing about current code. Its J2 result is moot for the same reason |
| `JuniperCassandra` | 3.11.13 / 2.3.3 | neither installed | 9 PASS, 3 INFO, 6 SKIP |
| scratch venv | 3.11.13 / 1.26.4 | neither installed | 9 PASS, 2 INFO, 7 SKIP (numpy 1.x has no `StringDType`) |

- **Golden vectors.** The fingerprint (`47fba46f…6c5733`) is identical in all five. That spans numpy 1.x and 2.x, big-endian inputs, Fortran order, and both NPZ writers.
- **Cross-version files.** An artifact written by the numpy 2.4.1 producer loaded and verified under numpy 1.26.4 and under 2.5.3 (`--write-payload`, then `--read-payload`).
- **Tamper detection** (check P2) on a real spiral artifact:
  - a flipped value in `X_val` gives `digest: X_val`;
  - a dropped test row gives `count: X_test has 29 rows, block declares 30`;
  - an extra key gives a coverage finding;
  - an edited `params.noise` stops the id re-deriving;
  - a wrong requested id gives an identity finding.
- **Encoding hazards.** Object arrays (checks E6, P3, L2) and `StringDType` (E4) both fail under `allow_pickle=False`. `<U` survives it (E1), including through the real `download_artifact_npz` (L1).

## 11. Rollout and work items

### 11.1 Order: gate first

Either order is safe for today's consumers, because none of them breaks on an extra key (§4.3). Gate first is recommended for three reasons:

- **The producer can prove agreement before it ships.** juniper-data's CI runs every generator's artifact through the *published* gate. A digest disagreement then fails a build, instead of making every consumer refuse every new artifact on the day of the deploy.
- **Consumer PRs merge as no-ops.** Every existing artifact reports `absent`, so enforcement begins by itself once blocks appear.
- **Producer first would store blocks that nothing checks.** They would sit in content-addressed, long-lived storage, so a producer bug would persist there until the gate arrived to refuse it.

### 11.2 Versions, floors and caps

- **juniper-data-client 0.5.0 → 0.6.0.** A MINOR bump, because it adds public API.
  - Both consumer caps are `<0.6.0`: canopy (`juniper-canopy/pyproject.toml:192`) and recurrence (`juniper-recurrence/pyproject.toml:54`).
  - Both are widened to `<0.7.0` **before** the Release. The owner ruled on 2026-09-05 that a downstream cap never lowers a SemVer bump (juniper-cascor-client#155, juniper-canopy#584).
  - The release train proposes those ceiling PRs for any pre-1.0 MINOR bump (`util/release_train/propose.py:930`).
  - Floors rise only once the wheel is on PyPI.
- **juniper-data 0.15.0 → 0.16.0.** MINOR, because it adds an artifact key. Its `test` extra's client floor rises to `>=0.6.0`.
- **cascor.** Its client pin has no cap: `juniper-data-client>=0.3.0` in the `juniper-data` extra (`juniper-cascor/pyproject.toml:118`). The floor rises to `>=0.6.0` together with the call sites.
- **juniper-ml meta-package**, after both releases are published:
  - `[clients]`: `juniper-data-client>=0.6.0` (`pyproject.toml:67`);
  - `[servers]`: `juniper-data>=0.16.0` (`:86`), so that `pip install juniper-ml[all]` installs a producer that emits the block.

### 11.3 Work items

Sizes: S is one PR in under a day; M is one or two PRs over a few days; L is several PRs.

| # | repo | item | size | depends on |
| --- | --- | --- | --- | --- |
| W0 | data | F-1: store `task_ids` as `np.str_`. Bump `arc_agi`'s VERSION so cached unloadable artifacts are not served again. Add a test that loads every generator's artifact with `np.load(allow_pickle=False)` | S | — |
| W1 | data | Land PR #422 (the stores emit three partitions) | in review | — |
| W2 | data | F-2: the stores fit on train, after the carve (OQ-4). **Done inside W1**: #422's head `11e45297` carries it | — | W1 |
| W3 | ml | Ratify this spec and rule on OQ-1 to OQ-6 | S | — |
| W4 | canopy, recurrence | Widen the `juniper-data-client` caps to `<0.7.0` | S each | W3 |
| W5 | data-client | `provenance.py`: decode, digest, gate, class map, exception. The `testing` fakes emit blocks (`testing/fake_client.py:636`, `:818`). Golden-vector tests. Release 0.6.0 | M | W3, W4 |
| W6 | data | See the list below; ends with Release 0.16.0 | L | W0, W2, W5 |
| W7 | cascor | The three call sites (§9.5); the legality override setting (OQ-2); the gate status on the run; floor `>=0.6.0` | M | W5 |
| W8 | canopy | The two call sites (OQ-5); floor | S | W5 |
| W9 | recurrence | The client path and the file loader; floor | S | W5 |
| W10 | ml | The meta-package floors (§11.2) | S | W5 and W6 published |

W6 (juniper-data) covers:

- the `core/provenance.py` builder;
- the reserved `partition_facts` channel in all 16 generators, popped beside `pop_scaling_meta` (`core/meta.py:172`);
- the route insertion (§4.4), and the stores calling the builder;
- the VERSION bumps (OQ-1) and the floor test's allow-list;
- fleet tests: every generator emits a block, each seeded id has a byte-identical block, and every artifact passes the client gate.

W7–W9 can merge before W6, because they are no-ops until blocks exist.

## 12. Open questions for the owner

**OQ-1. Should generator `VERSION` be bumped when producers start emitting the block?**

- **Recommendation**: yes, MINOR: 3.1.0, 5.1.0 for the equities pair, 3.1.0 for the stores (§7.3).
- **Evidence**: decision 11's reasoning about cache state (`test_val_emission_guards.py:241-244`). The floor test reads only the major version (`:288`). The cost is one fleet-wide cache miss.

**OQ-2. On a legality failure, refuse by default with a recorded per-consumer override, or only warn?**

- **Recommendation**: refuse by default, with a per-consumer override that is recorded as a caveat on the metrics.
- **Evidence**: this mirrors `…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §6.4 and cascor's `allow_missing_validation_split` (`manager.py:3739-3746`). A legality check that only warns is a declaration nobody reads.

**OQ-3. Should real-data sources record a digest of their input, as `resolved_inputs.source_sha256`?**

- **Recommendation**: yes for `csv_import`, as the SHA-256 of the bytes read. Defer the HF, Yahoo and SEC sources.
- **Evidence**: identical `CsvImportParams` produce different data under a different `JUNIPER_DATA_IMPORT_DIR` (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.4.4 item 6).

**OQ-4. The external stores normalise before they carve (F-2). Fix them first, or let them emit `all_rows` and be refused?** **Answered by the fix: the stores are fixed first.**

- **Resolution**: #422's head `11e45297` fits the stores' statistics on `X_train` after the carve, under the owner's 2026-09-22 ruling to conform the stores. No ruling is needed.
- **Evidence**: decision 7 is already ruled, and juniper-data#314 fixed the same leak in `csv_import`. The stores have served nothing.

**OQ-5. Should canopy call the provenance gate?**

- **Recommendation**: yes.
- **Evidence**: on 2026-09-22 the owner ruled that canopy runs `validate_npz_contract` as an **advisory** check only (canopy#559, implemented in the open PR juniper-canopy#663). The reason was that the helper fails closed on a legacy artifact that canopy must still load. This gate tolerates an absent block by construction, so that objection does not apply to it. Whether its *legality* refusals should be advisory in canopy, as the contract helper's are, is part of OQ-2.

**OQ-6. Enforce from the first release, or ship one release in report-only mode?**

- **Recommendation**: enforce from the first release.
- **Evidence**: W6's producer test runs every artifact through the published gate before release, which is the risk a report-only release would guard against. A report-only mode is a switch someone can forget to turn off.

## 13. What this specification cannot do

The first three items carry forward the limits in `…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3. The rest were found while grounding this document.

1. **A truthful block can describe a degenerate artifact.**
   - **The case.** Lane B's `xor(margin=x_range=y_range)` artifact had every provenance field correct and passed every derivable check. Yet 40 of 40 test rows were byte-identical to train rows (§9.6.3 of the same design), and it contained only 4 distinct rows out of 200 (§9.6.4).
   - **The limit.** The block checks an artifact against its own declaration, never against usefulness. The degeneracy check that would have caught this was dropped on 2026-09-03, and nothing here restores it.
2. **Strategy, seed and fit scope are declarations.** None of them can be derived from a single artifact. The legality table constrains how they combine and ties some of them to the id-bound `params`, but it cannot show that the producer did what it declared.
3. **A declared seed does not mean the seed mattered.** `seed_sensitivity` is not adopted: in §9.4.4 item 4 of the same design, 19 of 60 seed pairs disagreed at a single configuration. `mackey_glass` at `init_noise_std=0` (§9.6.5) and the equities pair (`equities/params.py:137`) carry seeds that change nothing.
4. **Integrity, not authenticity.** The arrays are not part of the id hash. Whoever can rewrite an artifact can therefore build a consistent block around new arrays while keeping `params` unchanged. The gate catches corruption, truncation, the wrong artifact being served, and inconsistent edits (check P2). It does not catch deliberate forgery, which would need a signature.
5. **Recording is not reproducing.**
   - **Unpinned inputs.** A null seed means OS entropy. The real-data inputs are not pinned by `params`: `csv_import` files (unless OQ-3 is accepted), HF datasets, and Yahoo and SEC data.
   - **Unpinned RNG.** The block names the seed but not the RNG implementation. Content under a given seed also depends on numpy's `Generator` algorithms, and this spec neither relies on nor verifies that their streams stay stable across numpy releases.
6. **Disjoint rows are not independent rows.**
   - **Temporal windows** share lookback input steps across partition boundaries; there is no embargo (`_sequence.py:71`).
   - **`arc_agi`** turns each task into several input/output pairs (`arc_agi/generator.py:237-257`) and shuffles them row by row, so one task can span partitions.
   - **The limit.** The block names the method; it does not measure dependence between partitions.
7. **Legacy artifacts stay unverifiable.** Every artifact minted before the producer ships reports `absent`, and none is backfilled: rewriting a content-addressed artifact would change its bytes under an unchanged id.
8. **The gate sees only what a consumer passes it.** A reader that bypasses the client stays unchecked unless it calls the gate itself. The recurrence-model file loader, ad-hoc scripts and notebooks are all such readers.
9. **Cross-snapshot comparability** is not obtained (§9.6.1 of the same design) and is not a goal.

## 14. Review round 1 — KNOWN-OPEN findings, not yet folded in

Consensus review round 1 ran on 2026-09-23 against this document as it then stood. Three independent lanes were each told to refute it:

- **S1** re-probed every citation. It found **three wrong citations**. They are fixed in place (§14.3) because they change no design. A later lane, which validated the handoff that records this round, found a fourth (C-4).
- **S2** attacked the identity, versioning, legality and digest layers. Verdict: **UNSOUND** in identity, versioning and legality. The choice of encoding (§4: one 0-d `<U` array under one key) and the digest's construction (§6) held. B-5 and B-6 are still findings against the digest's dtype allowlist and against how the gate enforces canonical JSON.
- **S3** tried to execute §11 as a work plan. Verdict: **EXECUTABLE WITH GAPS**: one blocker, four majors and two minors.

**Why the body above is left as reviewed.** The partition plan set the precedent in its §9 (`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`): correcting a design in place while its review is still open produced that plan's v2 and v3 defects. So §1–§13 still say what round 1 reviewed, and this section records what is wrong with them. A v2 folds these items and then gets a review round of its own. **W3 (ratification) cannot start before that.**

The session that wrote this section re-verified each finding against code before recording it. An independent lane then re-probed this section and corrected four details: B-1's arc_agi condition, B-3's scope in the index table, R-1's bench scope and R-7's locations. Unless stated, citations are at the commits in the header. Three sets of citations are pinned elsewhere:

- mnist, arc_agi and the dataset-id module: juniper-data `origin/main` on 2026-09-23;
- juniper-ml: `b6580529`;
- juniper-recurrence: `9b240253`.

### 14.1 Soundness (lane S2)

| id | severity | finding |
| --- | --- | --- |
| B-1 | BLOCKER | The legality layer refuses correct store artifacts, and L6 mislabels mnist and arc_agi |
| B-2 | BLOCKER | Tolerating an unknown `schema_version` turns refusals into passes |
| B-3 | BLOCKER | The id binding is skipped for every unseeded generator artifact |
| B-4 | MAJOR | An absent block is tolerated where the id proves one must exist |
| B-5 | MAJOR | The digest's dtype kinds admit `longdouble`, whose padding bytes are unspecified |
| B-6 | MAJOR | Canonical JSON is declared, not enforced |
| B-7 | MAJOR | Four robustness gaps in the gate as specified |

**B-1. The legality layer refuses correct artifacts and mislabels others.**

- **The stores.** #422's head `11e45297` makes the stores fit on train. §5.3 still lists them under `all_rows`, and §5.4 and §8.2 allow them only `none` or `constant`. A correctly normalised store artifact, `fit_scope: "train"`, would therefore be refused.
- **mnist and arc_agi.** L6 ties `ordered_carve` to `params.shuffle`, but both generators can reorder rows outside the carve, whatever `params.shuffle` says:
  - mnist shuffles the HF dataset whenever a seed is set (`mnist/generator.py:115-116`, `ds = ds.shuffle(seed=params.seed)`);
  - arc_agi draws its task subset in random order when **both** a seed and `n_tasks` are set (`arc_agi/generator.py:182-183` and `:214-215`, `rng.choice(...)`, inside `if params.n_tasks is not None:`). At its default `n_tasks=None` (`arc_agi/params.py:46`) it keeps read order.

  In those cases a `shuffle=False` artifact is not in generation order, yet L6 labels it `ordered_carve`.
- **Proposed.**
  - Stores: HF `none`, `constant` or `train`; Kaggle `none` or `train`. #422 merged on 2026-09-23 (`ce436819`), so `all_rows` now occurs nowhere on `main`. It remains in juniper-data 0.15.0's stores until a release ships #422.
  - Define `method` as the carve's own permutation only, and record a seeded pre-carve reordering in a field of its own. Alternatively, give mnist and arc_agi class rows of their own.

**B-2. Tolerating an unknown `schema_version` turns refusals into passes.**

- **The defect.** §7.1 makes any higher version `unverifiable`, and §9.4 tolerates that.
  - A block corrupted or mis-produced to `schema_version: 2` therefore skips G1–G4 entirely.
  - So may a malformed value such as `"1"`, because nothing says it is not "higher than the gate knows".
- **Proposed.**
  - G0 refuses any version that is not a positive `int`.
  - Whenever `digest.scheme` names a scheme the gate knows, G1–G4 run whatever the version says.
  - Add `min_reader_version`, so a producer can tell older readers not to trust a block.
  - An unknown enum value makes the block `unverifiable`, not illegal.

**B-3. The id binding is skipped where it matters.**

- **Unseeded generator artifacts.** §7.2 skips the re-derivation whenever the hashed `params` has no seed. That is because `generate_dataset_id` mixes in a nonce that it never returns (`core/dataset_id.py:54-55`, `canonical_data["_nonce"] = uuid.uuid4().hex[...]`). Every unseeded generator artifact is therefore unbound.
- **The stores.** §5.1 first pointed `params` at the dict that `DatasetMeta.params` records, whose seed is `None`, instead of at the hashed copy that carries the marker. That row has been re-pointed. Nothing in the design yet stops a builder from passing the wrong dict.
- **Proposed.**
  - Record the nonce in the block as `id_nonce`, null when seeded; `generate_dataset_id` must then accept or return it.
  - Make G4 unconditional.
  - Have `external_dataset_id` return the dict it hashed, so a store builder cannot pick the other one.

**B-4. An absent block is tolerated even where the id proves one must exist.**

- **The defect.** §9.4's `absent` row carries no version condition. Once OQ-1's bump ships, a requested id at or above the first emitting version (3.1.0, or 5.1.0 for the equities pair) names an artifact that was stamped. A missing block there means the block was stripped or the artifact substituted.
- **Proposed.** `absent` becomes a refusal when the consumer passes `dataset_id` and that id's version is at or above the generator's first emitting version. This depends on OQ-1 being answered yes.

**B-5. The digest's dtype kinds are too wide to be portable.**

- **The defect.** §6 allows kind `f`, which admits `longdouble`. On x86-64 that is `<f16`: an 80-bit value padded to 16 bytes. The digest would hash the padding bytes, and their content is unspecified, so equal values need not digest equally, even on one host.
- **Proposed.** Replace the kind list with an exact dtype allowlist: `<f4`, `<f8`, `<i4`, `<i8`, `|u1`, `|b1`, `<U{n}`, plus any other dtype a generator emits today. Add vectors that show a disallowed dtype is refused.

**B-6. Canonical JSON is declared, not enforced.**

- **The defect.** §4.1 says the text is canonical JSON, but G0 only decodes it.
  - `json.loads` accepts duplicate keys (the last one wins), so two readers can see different blocks.
  - Python's `bool` is an `int`, so `seed: true` passes L5's integer comparison.
- **Proposed.**
  - G0 requires the text to equal its own re-serialisation, `json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"))`.
  - G0 refuses duplicate keys through `object_pairs_hook`.
  - Integers are type-checked strictly: `type(x) is int`.

**B-7. Four robustness gaps in the gate as specified.**

| gap | the defect | proposed |
| --- | --- | --- |
| (a) | G2 reads `shape[0]`, which raises `IndexError` on a 0-d `X_train`. A malformed artifact should produce a finding, not a crash | Check rank before G2 |
| (b) | The gate has to see the arrays exactly as loaded. recurrence's `derive_full_split` adds keys, so a gate called after it trips G1 | Call sites pass the loaded mapping unmodified |
| (c) | §7.2's "ends with" check admits any prefix. The stores' prefix is derivable from `params`, so exact equality is possible: `hf-{dataset_name}`, plus `-{config_name}` when one is given; or `kaggle-` plus `dataset_ref` with `/` replaced by `-` | Require exact equality, with a per-store prefix rule |
| (d) | W9 places a check in `juniper_recurrence_model/data.py`, but juniper-recurrence-model depends only on numpy and juniper-model-core | Give recurrence-model an optional client dependency, or move the check into the app |

### 14.2 Executability (lane S3)

| id | severity | finding | proposed |
| --- | --- | --- | --- |
| R-1 | BLOCKER | §9.5's consumer census is incomplete (detail below) | See below |
| R-2 | MAJOR | OQ-2 is open, but the body presumes its answer: §8.3 ("By default it raises") and §9.4's G5 row write OQ-2's recommendation as a requirement | Mark both as conditional on OQ-2, or record OQ-2 as ruled before they stand |
| R-3 | MAJOR | W8 and W9 say "floor" without giving a value | `juniper-data-client>=0.6.0` in both, as W7 states |
| R-4 | MAJOR | W0 names no target for arc_agi's `VERSION`, which collides with §7.3 (detail below) | See below |
| R-5 | MAJOR | W3 names no artifact: "Ratify this spec" leaves the ruling nowhere to be recorded | A ruling section in this document, mirrored as a comment on juniper-data#423 |
| R-6 | MINOR | W7 does not name the legality-override setting | Name it in the `JUNIPER_CASCOR_*` family, beside `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT` |
| R-7 | MINOR | The "fixed at #422's head" wording in §1 item 8, §3.1 note 3, the §3.2 F-2 heading, W2 and OQ-4 was written while #422 was still open | #422 merged on 2026-09-23 as `ce436819`, so the wording can now be folded: "fixed on `main` by #422, not yet released" |

**R-1. §9.5's consumer census is incomplete.**

- **What §9.5 says.** It says juniper-ml has no permanent consumer. Its search for `download_artifact_npz` is accurate.
- **What that search misses.** Two paths bypass the client.
  - **juniper-ml's plot loaders.** `util/experiments/run_experiment.py:1230` and `:1332` fetch the raw `/v1/datasets/{id}/artifact` body, and `load_npz_bytes` turns it into arrays (`plots_cascor.py:43`, `plots_recurrence.py:49`).
  - **juniper-recurrence's `bench/datasets.py`.** It calls the generators in-process (e.g. `EquitiesSeqGenerator.generate`, `:267`), so it never sees an NPZ.
  - **Not a gap: `bench/app_e2e.py`.** It drives `juniper_recurrence.data.load_sequence_data` through a `_FakeClient` (`:47`, patched in at `:64`), so a gate at W9's client-path site (`data.py:76-77`) already runs in bench.
- **Proposed.**
  - Add the two juniper-ml loaders as call sites, or state why a plotting path need not be gated.
  - List `bench/datasets.py`, not the whole bench, as a declared non-consumer.
  - Re-run the census with a sweep for raw `/artifact` fetches and in-process `generate` calls, not only for the client method.

**R-4. W0's arc_agi `VERSION` target.**

- **The collision.** Suppose W0 moves arc_agi to 3.1.0 to evict the unloadable artifacts. Then some 3.1.0 arc_agi artifacts carry a block and some do not, and "`generator_version` ≥ 3.1.0 ⟹ block present" fails for arc_agi.
- **Proposed.** Name W0's target (3.0.1, say) and the version W6 then gives arc_agi, so that the implication holds for each generator.

### 14.3 Citations, fixed in place

- **C-1.** The stores insert the block at their loaders' `save` (`hf_store.py:199`, `kaggle_store.py:288`), not at `hf_store.py:173`.
- **C-2.** The recorded `params` dicts are at `hf_store.py:162` and `kaggle_store.py:256`, not `hf_store.py:136-150`.
- **C-3.** `JuniperDataContractError` is defined at `juniper_data_client/exceptions.py:82`, not `contract.py:13-15`. The words "tolerate, never require" come from juniper-data#423, not from the design's §9.5.4.
- **C-4** (found later, by the lane that validated the handoff recording this round). §5.3's `constant` row cited `hf_store.py:243` for the HF images' `/ 255.0`. That was right at #422's first commit (`33dffb8e`); at `11e45297` and on `ce436819` the line is `:282`, as §3.1 already said.

## 15. References

- **Ruling**: `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`:
  - §6.1 and §6.4;
  - §9.2, decision 7;
  - §9.4.1, and §9.4.4 to §9.4.6;
  - §9.5.4, whose "Backward compatibility" paragraph is where the rule that consumers tolerate a retired key without requiring it originates. §9.4's absent-key row cites the wording juniper-data#423 gives it, because §9.5.4 does not use the phrase "tolerate, never require";
  - §9.6.1 to §9.6.6.
- **Rollout**: `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §4, §5, §6a and §10.
- **Issues and PRs**:
  - juniper-data#423: this decision;
  - juniper-data#411, and PR #422: the stores;
  - juniper-data#314: fit scope;
  - juniper-data#319: seed defaults;
  - juniper-data#369: decision 11;
  - juniper-canopy#559;
  - juniper-cascor-client#155 and juniper-canopy#584: SemVer versus consumer caps.
- **Evidence**: `util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py`.
