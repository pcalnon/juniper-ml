# Decision 12 — the `partition_provenance` block: specification

**Project**: Juniper
**Sub-Project**: juniper-ecosystem (juniper-data → juniper-data-client → juniper-cascor / canopy / recurrence / ml)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.2.0
**Document Type**: SPECIFICATION
**Last Updated**: 2026-09-23
**Status**: SPEC v2 — DRAFT, **not ratifiable**. v1 (0.1.0, merged in juniper-ml#2043) was rated **UNSOUND** by consensus review round 1 in its identity, versioning and legality layers. v2 folds all fourteen of that round's findings into §1–§13; §14 records where each one went. **Review round 2 (§15, 2026-09-23) found v2 not ready for ratification**: round 1's blockers are fixed, but ten clusters of MAJOR findings remain, in versioning, identity, the OQ-1 dependency and the release plan. §1–§13 below are v2 as that round reviewed them, left unedited. v3 folds §15's findings, and a round 3 reviews it before the owner rules on anything.
**History**: Decision 12 was ruled on 2026-09-03. On 2026-09-22 the owner asked for it to be **specified before it is built**. No producer or gate code has moved. §12 lists six questions: OQ-4 is answered by a fix, and the other five belong to the owner. This document recommends an answer to each and decides none of them. §8.3 and §9.4 are written for both answers to OQ-2.

**Tracks**: [juniper-data#423](https://github.com/pcalnon/juniper-data/issues/423)
**Ruling of record**: [`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`](JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md) §9.6.3 and §9.6.6, which build on its §9.4.1 (Proposal B), §9.4.4 and §9.4.5
**Rollout context**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md) §4, §5, §10
**Grounded at** `origin/main` on 2026-09-23. Line numbers drift, so every citation also quotes a token you can grep for, and `util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py` re-checks each (file, line, token) triple at these pins:

- juniper-data `90ad035e`, the merge of juniper-data#430 (§3.2 F-1). Only #430's files differ from `ce436819`, the merge of #422;
- juniper-data-client `9bc8870a`;
- juniper-cascor `f7a6d573`;
- juniper-canopy `894a2cc7`;
- juniper-recurrence `9b240253`. juniper-recurrence#185 (`ca9609f0`) has since changed only a workflow;
- juniper-ml `c2bcb96c`.

**Evidence**:

- [`util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py`](../util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py) — v1's encoding, digest and tamper checks (§10.1);
- [`util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py`](../util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py) — **new**: the v2 gate implemented from this text, attacked with vectors for every round-1 finding, and run over a real artifact of every generator (§10.2);
- [`util/ad-hoc/2026-09-23_partition_provenance_dtype_inventory.py`](../util/ad-hoc/2026-09-23_partition_provenance_dtype_inventory.py) — **new**: every dtype the generators emit today (§6).

> **Reading guide.** §1 is the whole decision set. §4–§9 are normative: every MUST and SHOULD is a requirement on the implementation. §3 records the code the schema has to describe. §13 says what the mechanism cannot do. §14 maps each review-round-1 finding to the section that now answers it; read it to see what changed from v1. §15 is where review round 2 will be recorded.

---

## 1. Summary

The ruling fixed *what* the block declares and *that* one gate checks it. This document fixes everything else.

1. **Encoding** (§4). Key `partition_provenance`, holding a **0-d fixed-width unicode array** built with `np.array(text, dtype=np.str_)`. The text is canonical JSON, in exactly the `json.dumps(…, sort_keys=True, separators=(",", ":"))` form that `generate_dataset_id` already hashes, and the gate **enforces** that form: no duplicate keys, and the text must equal its own re-serialisation. It survives every consumer's `allow_pickle=False` load, verified on numpy 1.26.4 through 2.5.3.
2. **Schema** (§5), `schema_version` 1. Fourteen required top-level fields in two layers:
   - an **integrity core** that no later schema may change: `generator`, `generator_version`, `dataset_id`, `params`, `id_nonce`, `partitions`, `unpartitioned`, `digest`;
   - a **legality layer**, versioned: `resolved_inputs`, `seed`, `strategy` (with a new `pre_carve_order`), `normaliser`;
   - two version fields: `schema_version` and `min_reader_version`.
3. **Digest** (§6). The `juniper-array-v1` scheme, unchanged from v1 for every array a generator emits today: SHA-256 over a header naming the canonical little-endian dtype and the shape, then the elements in C order. Its dtype list is now **exact**: `<f4`, `<f8`, `<i4`, `<i8`, `|u1`, `|b1`, `<U{n}`. `longdouble` and every other dtype are refused, and `|b1` is hashed by value. v1's nine golden vectors are unchanged.
4. **Versioning** (§7.1). Integrity is keyed on `digest.scheme`, legality on `min_reader_version`. A gate always runs the integrity checks when it knows the scheme, whatever `schema_version` says, so a newer or corrupted version number can no longer skip them.
5. **Identity** (§7.2). The block carries `params` exactly as hashed, and **the nonce** that `generate_dataset_id` mixes into an unseeded request's id, as `id_nonce`. The gate therefore re-derives **every** dataset id, seeded or not, and compares it exactly, store prefix included.
6. **Legality table** (§8). It is keyed on a generator *class*, looked up from the generator name that the id re-derivation authenticates. The stores are legal with a train fit. `strategy.method` describes the carve's own permutation only, and a seeded reordering before the carve (mnist, arc_agi, the stores) is declared in `pre_carve_order`, whose value the gate **derives** from the id-bound `params`.
7. **Gate** (§9). `validate_partition_provenance`, in a new `juniper_data_client/provenance.py`, **beside** `validate_npz_contract` rather than inside it:
   - absent block: tolerate, **unless** the requested id's version shows the block must exist (§9.4);
   - integrity failure: refuse, never overridable;
   - legality failure: refuse by default, with a recorded opt-in, if OQ-2 is answered as recommended;
   - unknown digest scheme: tolerate as `unverifiable`; a block this gate may not judge for legality: `integrity_only`.
8. **Rollout: gate first** (§11). The client ships the gate as 0.6.0, after two `<0.6.0` caps are widened. Consumers wire it in while it is still a no-op. The producer ships last, and its CI runs every generator's artifact through the published gate. The table that lets the gate refuse a stripped block is filled in **after** the producer's release, from what it actually shipped (W11).
9. **Two defects found while grounding v1** (§3.2), both now fixed on `main` and not yet released:
   - F-1: no consumer could load an `arc_agi` artifact. Fixed by juniper-data#430, which also bumps arc_agi to `4.0.0`.
   - F-2: both external stores normalised before they carved. Fixed by juniper-data#422 (`ce436819`).

## 2. Scope and non-goals

**In scope**: the encoding, the fields, the digest, versioning and identity, the legality table, the gate, where the producer and every consumer attach, and the rollout order with its per-repo work items.

**Non-goals**, each deliberate:

- **No `DatasetMeta` field.** The ruling puts the block in the NPZ for a reason. All three cascor ingestion paths keep only `dataset_id` and download the NPZ (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3). A new `DatasetMeta` field would also re-open risk R-3 (`…PARTITION-IMPLEMENTATION-PLAN.md` §5): stored metadata is loaded with `DatasetMeta(**meta_dict)` (`juniper_data/storage/local_fs.py:261`).
- **No `seed_sensitivity`.** The ruling did not adopt it (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3). Its §9.4.4 item 4 showed it is not a property of the run.
- **No check on the arrays themselves.** The row-reuse and degeneracy assertion was dropped on 2026-09-03 (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.4). §13 records what that leaves uncovered.
- **No re-derivation of partition *counts* from `params`.** §8.4 explains why.
- **No backfill.** Stored artifacts are never rewritten. The gate reports them as `absent` (§9.4).
- **No change to `validate_npz_contract`.** Its tabular path "is untouched and returns immediately" (`juniper_data_client/contract.py:13`), and callers rely on that.
- **No change to any seeded dataset id.** Exposing the nonce (§7.2) changes how an unseeded id is *recorded*, not how any id is computed (§10.2 check I2).

## 3. Ground truth

### 3.1 How the 16 generators and the 2 stores partition today

The route computes `dataset_id` before generation, from `params.model_dump()` after `bind_deployment_defaults` (`juniper_data/api/routes/datasets.py:146-154`). It then pops the reserved non-array channels `scaling`, `truncation` and `data_quality`, so that "the stored arrays stay array-only" (`:287-298`). Finally it checksums (`:300`) and persists (`:355`); the stores write `np.savez_compressed` (`storage/local_fs.py:211`). The 16 generators are registered in `GENERATOR_REGISTRY` (`api/routes/generators.py:45`). There are six distinct behaviours to describe:

| class | members | how rows reach the carve, and how it is made | seed | normaliser as implemented |
| --- | --- | --- | --- | --- |
| `synthetic_tabular` | spiral, xor, gaussian, circles, moon, checkerboard | Generated, then `resolve_counts_for_params` and `partition_and_assemble` (e.g. `spiral/generator.py:45-52`): one permutation when `params.shuffle` (`core/split.py:43`), then a contiguous cut (`split_three_way`, `:211`). The sizing mode is `PartitionParams.sizing_mode` (`core/partition_params.py:81`) | int or null; default `DEFAULT_GENERATOR_SEED` (`core/constants.py:92`), read from `JUNIPER_DATA_DEFAULT_GENERATOR_SEED` at import | none |
| `real_carve` | mnist, csv_import, arc_agi | The same helpers over a fixed corpus (`mnist/generator.py:94-96`, `csv_import/generator.py:63-64`, `arc_agi/generator.py:106-124`). `CarveOnlyPartitionParams` rejects `additive` (`core/partition_params.py:110-111`). **mnist and arc_agi can reorder rows BEFORE the carve** (note 1) | int or null | mnist: `/ 255.0` (`:124`). csv_import: min-max fitted on train, falling back to val and test (`csv_import/generator.py:95`). arc_agi: none |
| `temporal_rows` | equities | Its own per-ticker code: each ticker's date-sorted rows are cut by independently rounded ratios with an end-trim, then concatenated split-major (`equities/generator.py:346-372`). `EquitiesParams` is a plain `BaseModel` (`equities/params.py:47`) | Carried but "Unused for the temporal split" (`equities/params.py:137`). `end_date` defaults to the wall clock (`equities/generator.py:315`) | Optional min-max fitted on train, falling back to every conditioned row (`:395`) |
| `temporal_windows` | multi_sine, mackey_glass, ar_p, irregular_sine, delay_product | One series, windowed (note 2). Windows are cut by index at `temporal_split_indices`, and test takes the remainder (`_sequence.py:277`, `:376`) | `seed: int`, default 0, never null (`_synthetic.py:65`); inert for mackey_glass at `init_noise_std=0` | None: "The NPZ stays RAW either way" (`_synthetic.py:66`) |
| `temporal_entity_windows` | equities_seq | Per ticker, windows are assigned by **target date** against that ticker's `temporal_split_indices` row cuts (`equities_seq/generator.py:224-234`, `_sequence.py:125-133`). There is no embargo: `embargo: bool = False` (`_sequence.py:71`) is never passed | As equities | Train **frame rows** of every ticker, falling back to all frames (`equities_seq/generator.py:194-206`); note 4 |
| `external_store` | huggingface, kaggle (juniper-data#422) | A seeded pre-shuffle **only if `seed is not None`**, then `carve_three_way` (`external_partition.py:66`), which cuts rows "in their current order", 0.8 / 0.1 / 0.1 by default (note 3) | int or null. Null means **no shuffle**, unlike the generators | HF images: the constant `/ 255.0` (`hf_store.py:282`). HF tabular `/ max` and Kaggle min-max: fit on `X_train` after the carve (note 3) |

Notes on the table:

1. **Reordering before the carve.** mnist shuffles the Hub dataset whenever a seed is set, before subsetting: `ds = ds.shuffle(seed=params.seed)` (`mnist/generator.py:115-116`). arc_agi draws its task subset in random order when **both** a seed and `n_tasks` are set, `rng.choice(...)` inside `if params.n_tasks is not None:` (`arc_agi/generator.py:183-189` for the Hub, `:215-221` for local files). At its default `n_tasks=None` (`arc_agi/params.py:46`) it keeps read order. In both cases a `shuffle=False` artifact is **not** in source order. csv_import never reorders before its carve.
2. **`temporal_windows` plumbing.** These generators reach the windower through `build_sequence_arrays` (`_synthetic.py:90`, which calls `window_regular_series` at `:100`) or through `window_timed_series` (`irregular_sine/generator.py:57`, `delay_product/generator.py:71`). A train-fitted *advisory* scaling descriptor goes to `DatasetMeta`, not to the arrays (`_synthetic.py:111-130`). mackey_glass's inert seed is recorded in `…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.5.
3. **`external_store`, on `main` since juniper-data#422 (`ce436819`), not yet released.** juniper-data 0.15.0's stores still cut two ways and normalise before the carve.
   - **Pre-shuffle.** HF `ds = ds.shuffle(seed=seed)` (`hf_store.py:133`); Kaggle `random.seed(seed); random.shuffle(data)` (`kaggle_store.py:195-199`).
   - **Ratios.** Checked before any download by `validate_carve_ratios` (`external_partition.py:45`), after conversion to plain `float`.
   - **Normaliser.** HF tabular: `scale = float(x_train.max()) if x_train.size else 0.0`, applied to all three partitions only when `scale > 1.0` (`hf_store.py:157`), so a normalise request can still leave the arrays untransformed. Kaggle: min-max fitted on `X_train` only when it is non-empty (`kaggle_store.py:245`). Neither falls back to other rows.
4. **equities_seq counts windows, but fits on rows.** Its normaliser fits on each ticker's train **frame rows**, while `partitions.train.rows` counts **windows**. A ticker whose train cut is shorter than `lookback + 1` rows contributes to the fit and to no train window. A train fit with zero train windows is therefore a correct artifact, which is why §8 has no rule tying `fit_scope: train` to a non-empty train partition (§10.2 check B1.g).

### 3.2 Findings made while grounding

- **F-1: No consumer could load an `arc_agi` artifact. FIXED on `main` by juniper-data#430, not yet released.**
  - **Cause.** `task_ids` has been an object array since the generator was added (`8fa3f95`), so `np.savez` pickled it.
  - **Failure.** `download_artifact_npz` loads with numpy's default `allow_pickle=False` and reads every key (`juniper_data_client/client.py:679-680`). It raised `ValueError: Object arrays cannot be loaded when allow_pickle=False`.
  - **Silent cache loss.** juniper-data's cached store hit the same error inside `contextlib.suppress(Exception)`, so it never cached these artifacts and said nothing.
  - **The fix.** `task_ids` is now a `<U` array, like `ticker_vocab` (`arc_agi/generator.py:272`, `:285`); arc_agi's `VERSION` is `4.0.0` (`:25`), so a cached unloadable artifact cannot answer a new request (§7.3); the cached store logs a failed population (`storage/cached.py:150`); and a new fleet test round-trips every generator's artifact through an `allow_pickle=False` load (`tests/unit/test_artifacts_load_without_pickle.py`). The same bump closes juniper-data#427, where #402 had changed arc_agi's metadata without one.
  - **Why it matters here.** It proved the hazard in §4.2 live, and `task_ids` could not have been digested (§6) until it was a `<U` array.
- **F-2: Both external stores fit their normaliser before carving. FIXED on `main` by juniper-data#422 (`ce436819`), not yet released.**
  - **Where it was.** At `33dffb8e`, HF tabular `X / X.max()` (`normalize=True` by default) and Kaggle min-max (off by default) ran before the carve. Both now fit on `X_train` after it (§3.1 note 3).
  - **Why it mattered.** This was the decision-7 leak that juniper-data#314 removed from `csv_import`. A truthful block would have had to declare it as `all_rows`, which §8 makes illegal.
  - **Exposure.** Neither store has a route or a service caller, so no served artifact was affected. OQ-4 is answered by the fix.
- **F-3: `DatasetMeta.checksum` is not a hash of the served artifact.**
  - **What it hashes.** `np.savez` over sorted keys (`core/artifacts.py:44-45`, `:62-63`). The stores serve `np.savez_compressed` instead.
  - **Why the block cannot rely on it.** It can be checked only by re-serialising, which reproduces it under a single numpy version (check C1); it lives where cascor never reads it (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3); and one hash cannot say *which* partition changed.
  - **Consequence.** The block carries its own digest for every array.
- **F-4: One `dataset_id` can name different equities content on different days.** This is documented (`equities/params.py:137`). The block makes it visible by recording the resolved `end_date` (§5.1).

## 4. Encoding inside the NPZ

### 4.1 The rule

- **Key and value.** The key is **`partition_provenance`**. The value is `np.array(text, dtype=np.str_)`: a **0-d** array whose dtype is `<U{len(text)}`.
- **Serialisation.** `text` is `json.dumps(block, sort_keys=True, separators=(",", ":"))`, with the `json` module's other defaults left alone (`ensure_ascii=True`, `allow_nan=True`). This is the same call `generate_dataset_id` makes (`core/dataset_id.py:57`).
  - `ensure_ascii` keeps the payload ASCII.
  - `allow_nan` is required, because a legal `params` can hold `inf`. Check J1 shows `Infinity` round-trips. Strict JSON parsers outside Python would reject that token; every consumer is Python.
- **Decoding is strict** (the gate's G0, §9.3). The value MUST be 0-d with `dtype.kind == "U"`. The text MUST parse as a JSON object **with no duplicate key at any depth**, checked through `object_pairs_hook`: `json.loads` otherwise keeps the last duplicate, so two readers could see two different blocks. The text MUST equal `json.dumps(json.loads(text), sort_keys=True, separators=(",", ":"))`. Anything else is a malformed block.
- **No `StringDType`.** Writers MUST NOT use numpy 2's `StringDType`. It saves as a pickled object, and an `allow_pickle=False` load of it fails (check E4). `np.array(str)` infers `<U` (check E3), but writers pass `dtype=np.str_` explicitly anyway.

### 4.2 Alternatives rejected

| option | why not |
| --- | --- |
| object array or pickled dict | Unloadable under `allow_pickle=False`; F-1 was the live proof (checks E6, P3, L2) |
| numpy 2 `StringDType` | Saved as a pickled object, so it fails the same way (check E4) |
| `uint8` array of UTF-8 bytes | It round-trips (check E2) and is 4× smaller, but any consumer walking the keys sees a numeric array, and there is no precedent for it. `<U` has one: `ticker_vocab` already reaches every consumer as `np.str_` (`equities/generator.py:414`) |
| `DatasetMeta`, or a reserved channel such as `scaling` | Invisible to cascor (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3). The route pops those channels *out* of the NPZ (`datasets.py:287-298`) |

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
- **What only the generator knows.** Four facts come from the generator: the method, the pre-carve order, the fit scope with its stems, and the resolved inputs. They reach the route through one new reserved channel, `partition_facts` (proposed name), popped beside the existing three (`core/meta.py:172-229`).
  - Anything that calls `generate()` directly sees that channel, just as it sees `scaling` today. juniper-ml's `util/snapshot_attribute.py:341` and juniper-recurrence's `bench/datasets.py` are such callers (§9.5).
  - The stores bypass the route, so they MUST call the same builder before `self._cache_store.save(...)` in their loaders (`hf_store.py:199`, `kaggle_store.py:288`), building `params` from the dict their id function **hashed** (§7.2).
- **The cache round trip preserves it.** `CachedDatasetStore.get_artifact_bytes` re-loads a primary's artifact and re-saves every key into the cache (`storage/cached.py:145`). The block is an ordinary key, so it is re-saved unchanged, and the digests describe arrays that are re-saved unchanged too.

## 5. Schema

### 5.1 Fields

All fourteen top-level fields are REQUIRED. A reader MUST ignore a top-level field it does not know; §7.1 explains why that is safe.

| layer | field | type | meaning and source |
| --- | --- | --- | --- |
| version | `schema_version` | int ≥ 1 | `1` for this document |
| version | `min_reader_version` | int, 1 ≤ it ≤ `schema_version` | The lowest gate schema version that can judge this block's legality layer. `1` for this document (§7.1) |
| core | `generator` | string | Registry key, or `huggingface` / `kaggle`. `DatasetMeta.generator`; hashed into the id |
| core | `generator_version` | string, `X.Y.Z` | The `VERSION` hashed into the id |
| core | `dataset_id` | string | The id the producer assigned: `{generator}-{version}-{16 hex}` (`datasets.py:150`), with the stores' readable prefix in front (`external_partition.py:140`) |
| core | `params` | object | **Exactly** the dict that was hashed: `params.model_dump()` after `bind_deployment_defaults` (`datasets.py:146-154`). For the stores, the copy `external_dataset_id` hashed, whose null seed is the marker `"unshuffled"` (`external_partition.py:139`), not `DatasetMeta.params` (`hf_store.py:162`, `kaggle_store.py:256`) |
| core | `id_nonce` | string or null | The nonce `generate_dataset_id` mixed into the id (`core/dataset_id.py:54-55`): 8 lowercase hex characters when `params` has no seed, null otherwise (§7.2) |
| core | `partitions` | object | Keys exactly `train`, `val`, `test`; each exactly `{"rows": int ≥ 0, "arrays": {stem: digest}}` |
| core | `unpartitioned` | object | Array key → digest, for every other array key except the block itself: `ticker_vocab`, and arc_agi's `task_ids`. `{}` if there are none |
| core | `digest` | object | `{"algorithm": "sha256", "scheme": "juniper-array-v1"}` (§6) |
| legality | `resolved_inputs` | object | Values that decide the content but are absent from `params`. For the equities pair, `end_date` (`YYYY-MM-DD`) when `params.end_date` is null (`equities/generator.py:315`). `source_sha256` if OQ-3 is accepted. Otherwise `{}` |
| legality | `seed` | int or null | The seed the run used. It equals `params["seed"]` whenever that value is an integer, and is null otherwise. Null means OS entropy for a generator, or no shuffle for a store |
| legality | `strategy` | object | `{"method": enum, "pre_carve_order": enum, "sizing_mode": "additive" / "carve" / null}` (§5.2) |
| legality | `normaliser` | object | `{"fit_scope": enum, "stems": [string]}` (§5.3). `stems` names the array stems transformed, e.g. `["X"]`, and is `[]` when `fit_scope` is `none` |

Every integer in the block (`schema_version`, `min_reader_version`, `rows`, `seed`) MUST be a JSON integer, and the gate checks it with `type(x) is int`. Python's `bool` is an `int` subclass, so `true` would otherwise pass as `1`.

Rules for `partitions`:

- **`rows`** is the length of the leading axis: samples for a 2-D artifact, windows for a 3-D one.
- **`arrays`** names every `{stem}_{split}` key in the artifact, and MUST include `X` and `y` in all three partitions.
- **Empty partitions.** A partition with 0 rows is declared, never omitted (`test_val_emission_guards.py:162-163`).

**Deliberately absent**: the producer's package version, the numpy version, host names and timestamps. The block is a pure function of generator, version, `params`, nonce, resolved inputs and arrays. So for a seeded request with pinned inputs, **one `dataset_id` always carries one byte-identical block**, and W6 in §11 tests exactly that. `DatasetMeta.created_at` already records *when*.

### 5.2 `strategy`

**`method`** says how the carve itself assigned rows to partitions. It describes the carve's **own** permutation only.

| value | meaning | produced by |
| --- | --- | --- |
| `shuffled_carve` | One permutation of the rows as they reached the carve, then a contiguous train, val, test cut. Surplus rows at the shuffled tail are dropped | `partition_and_assemble(shuffle=True)` (`core/split.py:584`) |
| `ordered_carve` | The same contiguous cut, with no permutation at the carve | `partition_and_assemble(shuffle=False)`; the stores' `carve_three_way`, always |
| `temporal_rows_per_entity` | Each entity's date-sorted rows are cut earliest-first, and the partitions are concatenated split-major in `ticker_vocab` order | equities (`equities/generator.py:346-372`) |
| `temporal_windows` | One series is windowed, and the windows are cut by index. Test takes the remainder. Neighbouring partitions share lookback input steps | `_sequence.py:277`, `:376` |
| `temporal_windows_per_entity` | For each entity, windows are assigned by target date against that entity's row cuts. No embargo | equities_seq (`equities_seq/generator.py:224-234`) |

**`pre_carve_order`** (new in v2) says whether the rows were reordered **before** the carve.

| value | meaning | produced by |
| --- | --- | --- |
| `as_produced` | The rows reached the carve in the order the generator produced them or the source delivered them | every generator not listed below; mnist without a seed; arc_agi without both a seed and `n_tasks`; a store without a seed |
| `seeded_shuffle` | A seeded shuffle or seeded sample reordered the rows before the carve | mnist with a seed (`mnist/generator.py:115-116`); arc_agi with a seed and `n_tasks` (`arc_agi/generator.py:183-189`, `:215-221`); a store with a seed (`hf_store.py:133`, `kaggle_store.py:199`) |

The two together are what a consumer needs: whether partition membership was random, and whether the rows inside a partition keep source order. v1 folded both into `method`, which mislabelled a seeded, unshuffled mnist or arc_agi artifact as `ordered_carve` in source order, and labelled the stores' seeded case `shuffled_carve` although their carve never permutes.

**`sizing_mode`** is `params.sizing_mode` where the params model has one (`core/partition_params.py:81`), `"carve"` for the stores, and null for the temporal classes.

### 5.3 `normaliser.fit_scope`

| value | meaning | where it occurs today |
| --- | --- | --- |
| `none` | No transform on any emitted array | The 2-D synthetics; the sequence synthetics, whose advisory scaling lives in `DatasetMeta` (`_synthetic.py:66`); any run with its normalise flag off; an HF tabular run whose train maximum is at most 1 or whose train partition is empty (`hf_store.py:157`); a Kaggle run with an empty train partition (`kaggle_store.py:245`); a csv_import run whose three partitions are all empty |
| `constant` | A data-independent transform | mnist `/ 255.0` (`mnist/generator.py:124`); HF images (`hf_store.py:282`) |
| `train` | Statistics fitted on the train partition only, as decision 7 requires | csv_import (`csv_import/generator.py:95`), equities (`:395`), equities_seq (`:194-206`) whenever train is non-empty; HF tabular and Kaggle min-max, since juniper-data#422 |
| `non_train_fallback` | Train was empty, so the fit used other rows | The first three generators' fallback branch; pinned by `test_normaliser_fit_scope.py:172` |
| `all_rows` | Fitted on every row before the carve | **Nowhere on `main`.** The 0.15.0 stores still do it (F-2). The value stays in the enum so that a truthful producer can declare the leak and be refused, rather than be forced to lie |

### 5.4 Values by class

| class | `method` | `pre_carve_order` | `sizing_mode` | `seed` | `fit_scope` | `resolved_inputs` | `unpartitioned` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `synthetic_tabular` | `shuffled_carve` or `ordered_carve`, following `params.shuffle` | `as_produced` | `params.sizing_mode` | int or null | `none` | `{}` | `{}` |
| `real_carve` | as above | mnist: `seeded_shuffle` iff an int seed. arc_agi: `seeded_shuffle` iff an int seed and a non-null `n_tasks`. csv_import: `as_produced` | `carve` | int or null | mnist: `none`, `constant`. csv_import: `none`, `train`, `non_train_fallback`. arc_agi: `none` | csv_import: `source_sha256` (OQ-3) | arc_agi: `task_ids` |
| `temporal_rows` | `temporal_rows_per_entity` | `as_produced` | null | int or null (inert) | `none`, `train`, `non_train_fallback` | `end_date` when `params.end_date` is null | `ticker_vocab` |
| `temporal_windows` | `temporal_windows` | `as_produced` | null | int, never null | `none` | `{}` | `{}` |
| `temporal_entity_windows` | `temporal_windows_per_entity` | `as_produced` | null | int or null (inert) | `none`, `train`, `non_train_fallback` | as `temporal_rows` | `ticker_vocab` |
| `external_store` | `ordered_carve` | `seeded_shuffle` iff an int seed | `carve` | int or null | HF: `none`, `constant`, `train`. Kaggle: `none`, `train` | (OQ-3) | `{}` |

### 5.5 Example

A block for spiral (`n_points_per_spiral=50`, `seed=7`). Digests and most `params` are elided, and the lines are wrapped for reading; the stored text is a single line.

```json
{"dataset_id":"spiral-3.1.0-…","digest":{"algorithm":"sha256","scheme":"juniper-array-v1"},
 "generator":"spiral","generator_version":"3.1.0","id_nonce":null,"min_reader_version":1,
 "normaliser":{"fit_scope":"none","stems":[]},
 "params":{"n_points_per_spiral":50,"seed":7,"shuffle":true,"sizing_mode":"additive","val_percent":40.0},
 "partitions":{"test":{"arrays":{"X":"…","y":"…"},"rows":30},"train":{"arrays":{"X":"…","y":"…"},"rows":100},
               "val":{"arrays":{"X":"…","y":"…"},"rows":40}},
 "resolved_inputs":{},"schema_version":1,"seed":7,
 "strategy":{"method":"shuffled_carve","pre_carve_order":"as_produced","sizing_mode":"additive"},
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
         each "b" element as one byte, 0x00 for False and 0x01 for True;
         each "U" element as UCS-4 little-endian code points, NUL-padded to the item size
digest = lowercase hex SHA-256(header || data)
```

- **Allowed dtypes, exactly**: `<f4`, `<f8`, `<i4`, `<i8`, `|u1`, `|b1`, and `<U{n}` for n ≥ 1, after canonicalisation (so a big-endian input is admitted and digested as its little-endian form). Everything else is outside the scheme: `longdouble`, `float16`, complex, `datetime64` and `timedelta64`, every other integer width, bytes (`S`), object, structured and sub-array dtypes. A producer MUST NOT emit them, and the gate reports one as an integrity finding (G3). This replaces v1's list of dtype **kinds**, whose `f` admitted `longdouble`: on x86-64 that is `<f16`, an 80-bit value padded to 16 bytes whose padding the digest would hash, so equal values need not digest equally even on one host.
- **What is emitted today**, measured by `util/ad-hoc/2026-09-23_partition_provenance_dtype_inventory.py` over every generator's artifact: **four** dtypes. `<f4` (138 keys), `<i4` (24: the equities pair's dates, report dates and ticker codes), `|u1` (18: every `observed_mask_*`) and `<U{n}` (3: `ticker_vocab` twice, and arc_agi's `task_ids` since F-1's fix). `<f8`, `<i8` and `|b1` are admitted for the golden vectors and for parity with the stores' code, and no generator emits them. No generator emits a 0-d array.
- **`|b1` is hashed by value.** numpy stores a bool in one byte but does not force that byte to 0 or 1: `np.frombuffer(bytes([2]), dtype=bool)` is `True`. The scheme hashes `0x01` for every true element, so two value-equal bool arrays digest equally (§10.2 check V3).
- **Invariant** under memory layout (Fortran order, strided views), byte order, and an NPZ round trip, compressed or not.
- **Sensitive** to shape, to dtype and to every bit of a numeric element: `+0.0` and `-0.0` differ, as do different NaN payloads. For those dtypes it is a byte digest, not a value digest (checks D2, D3).
- **Streaming.** Implementations MAY feed `data` into the hash in pieces rather than building it in memory.
- **Why not reuse cascor's precedent**, `calculate_tensor_checksum` (`src/snapshots/snapshot_common.py:292-303`, which hashes `numpy().tobytes()`)? It hashes the bytes alone. Arrays of different shape or dtype but identical bytes therefore collide (check D3's reshape and reinterpret cases), and the digest depends on the host's byte order.
- **Golden vectors.** Every implementation MUST reproduce these nine digests, unchanged from v1:

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

Their fingerprint is `47fba46f786387baf2c1d6e06f7d5825306cd649554413e9dd4b0df1aa6c5733`: the SHA-256 of the canonical JSON of all nine, keyed `g1_…` to `g9_…` as in the scripts. **Refusal vectors**: an implementation MUST refuse, not digest, `np.array([1.0], dtype=np.longdouble)`, `np.array([1.0], dtype="<f2")`, `np.array([1 + 2j], dtype="<c8")`, `np.array(["2026-09-23"], dtype="datetime64[D]")`, `np.array([1], dtype="<i2")`, `np.array([1], dtype="<u4")`, `np.array([b"abc"], dtype="S3")`, `np.array(["a"], dtype=object)` and `np.zeros(1, dtype=[("a", "<f4")])` (check V2).

## 7. Versions and identity

### 7.1 `schema_version` and `min_reader_version`

- **The block is two layers** (§5.1). The **integrity core** is frozen: no later schema version may change the meaning or the shape of `generator`, `generator_version`, `dataset_id`, `params`, `id_nonce`, `partitions`, `unpartitioned` or `digest`. A change to any of them MUST come with a new `digest.scheme` name. The **legality layer** (`resolved_inputs`, `seed`, `strategy`, `normaliser`) may change with `schema_version`.
- **Integrity is keyed on `digest.scheme`.** A gate that knows the scheme runs G1–G4 (§9.3) **whatever `schema_version` says**. A corrupted or mis-produced version number therefore cannot skip them, which is what v1's "tolerate a higher version" did. A gate that does not know the scheme can check nothing but G0, and reports `unverifiable` (§9.4).
- **Legality is keyed on `min_reader_version`.** It is the producer's promise: a gate whose own schema version is at least this value can judge the whole legality layer. A gate below it reports `integrity_only`: integrity checked, legality not judged. So:
  - a producer that **adds** an informational field keeps `min_reader_version` where it is, and older gates keep verifying fully, ignoring the field;
  - a producer that changes the meaning of a legality field, or **adds an enum value** an older gate would misjudge, MUST raise `min_reader_version` to the version that understands it.
  - An enum value the gate does not know, in a block whose `min_reader_version` the gate meets, is therefore **illegal** (L1), not unverifiable: the producer promised this gate could judge it.
- **Malformed versions are refused.** G0 requires `schema_version` to be an int ≥ 1 and `min_reader_version` an int with 1 ≤ it ≤ `schema_version`, both checked with `type(x) is int`. A string `"1"`, a `true` or a `min_reader_version` above `schema_version` is a malformed block, never "a version this gate does not know".
- **Not in the id.** Neither version field is hashed into `dataset_id`.

### 7.2 What the block changes, and what it makes checkable

- **`dataset_id` does not change.** It is `sha256` over `json.dumps` of `generator`, `version` and `params`, truncated to 16 hex digits and computed before generation (`datasets.py:150-154`, `core/dataset_id.py:46-61`). Nothing generated reaches it.
- **The artifact bytes and `DatasetMeta.checksum` do change**, because the block is inserted before `compute_checksum` (§4.4). Check P1 ran the real `compute_checksum` over a dict carrying the block.
- **Every id becomes checkable.**
  - **The check.** `params` is carried exactly as it was hashed, and so is the nonce. The gate recomputes `f"{generator}-{generator_version}-{hash16}"` over `{"generator", "version", "params"}`, plus `"_nonce": id_nonce` when the nonce is non-null, exactly as `generate_dataset_id` builds its canonical dict (`core/dataset_id.py:47-57`). It then requires `dataset_id` to **equal** the result, with the store prefix below in front for the two stores. v1 required only "ends with", which admitted any prefix.
  - **Unseeded requests.** `generate_dataset_id` mixes a nonce into an unseeded request's id, `canonical_data["_nonce"] = uuid.uuid4().hex[:_DATASET_ID_NONCE_LENGTH]` (`core/dataset_id.py:54-55`), and never returns it. v1 therefore skipped the check for every unseeded artifact. v2 records the nonce as `id_nonce`: the producer draws it, passes it into `generate_dataset_id` (W6 adds that parameter), and writes the same value into the block. The gate requires `id_nonce` to be 8 lowercase hex characters exactly when `params.get("seed") is None`, and null otherwise. The canonical form is unchanged: §10.2 check I2 fixes the nonce and shows the reference re-derivation equals the real function's id.
  - **The stores' prefix is derivable** from their hashed `params`: `hf-{dataset_name}`, plus `-{config_name}` when one is given (`hf_store.py:176-178`), or `kaggle-` plus `dataset_ref` with `/` replaced by `-` (`kaggle_store.py:270`). §10.2 check I3 re-derives four store ids exactly through the real `external_dataset_id`.
  - **The stores' seed.** `external_dataset_id` hashes a copy of `params` in which a null seed becomes the fixed marker `"unshuffled"` (`external_partition.py:139`), because the stores shuffle only when given a seed and an unseeded load should keep one id. Their hashed `params` therefore never has a null seed, so their `id_nonce` is always null. The producer MUST build a store's block from the dict it hashed; W6 has `external_dataset_id` return that dict, so a builder cannot pick `DatasetMeta.params` by mistake.
  - **Evidence.** v1's check J2 re-derived the real id for the default params of all 16 generators after a JSON round trip, and P2 caught an edited `params` value. v2's I1 repeats the seeded case for the 15 generators with default-constructible params, and B3 attacks the unseeded case (§10.2).

### 7.3 Is a generator `VERSION` bump required? (OQ-1)

**Not for correctness.** The arrays do not change, and consumers tolerate a missing block.

**Recommended anyway: a MINOR bump** in the release that starts emitting the block:

| generators | today (`main`) | first emitting version |
| --- | --- | --- |
| the thirteen others (the 2-D synthetics, mnist, csv_import, the five sequence synthetics) | `3.0.0` | `3.1.0` |
| arc_agi | `4.0.0` (juniper-data#430; §3.2 F-1) | `4.1.0` |
| equities, equities_seq | `5.0.0` | `5.1.0` |
| the stores' `EXTERNAL_STORE_VERSION` (`external_partition.py:30`) | `3.0.0` | `3.1.0` |

Reasons for the bump:

- **The decision-11 precedent says so in as many words**: "Which shape a consumer sees is then decided by cache state rather than by the contract" (`test_val_emission_guards.py:241-244`).
- **Without a bump, cache state decides what consumers see.** A request made after the upgrade can be served a cached artifact without the block, under the same id, and the gate then reports `absent` for an artifact the new producer would have stamped. "At or above a generator's first emitting version ⟹ block present" can then never become an invariant, and §9.4's refusal of a stripped block depends on it.
- **MINOR is the right size**, because the change is additive. It also clears decision 11's floor test, which reads only the major version (`:288`). That test's allow-list (`:296`, `ahead == {"arc_agi": "4.0.0", "equities": "5.0.0", "equities_seq": "5.0.0"}` since juniper-data#430) is rewritten in the same PR.
- **arc_agi's target does not collide.** v1's W0 named no target, and a W0 bump to `3.1.0` would have put block-less and block-carrying artifacts under one version. W0 took `4.0.0` (MAJOR, for the metadata and dtype corrections), so arc_agi's first emitting version is `4.1.0`.

**Cost:**

- Every cached artifact misses once and is regenerated. equities goes to the network, and `arc_agi` from HF took 511 s (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.4.6).
- Ids pinned in configs stop matching new requests, although the old ids still resolve in the store.

## 8. The legality table

The gate finds a block's class from `generator`, a value the id re-derivation authenticates (§7.2). It does so through a client-side map of the 16 registry names plus `huggingface` and `kaggle`. The client's constants already name all 16 (`juniper_data_client/constants.py:283-307`, the `GENERATOR_*` block). An unknown generator gets only the class-independent rules; being unknown is never, on its own, a reason to refuse.

### 8.1 Class-independent rules

| rule | condition | derivable? |
| --- | --- | --- |
| L1 | `method`, `pre_carve_order`, `sizing_mode` (when non-null) and `fit_scope` are members of their enums | — |
| L2 | `fit_scope` is not `all_rows` (decision 7) | no |
| L3 | `fit_scope == "non_train_fallback"` implies `partitions.train.rows == 0` | yes; rows are verified against the array shapes |
| L4 | `fit_scope == "none"` if and only if `normaliser.stems == []`; otherwise every stem listed is a declared stem | yes |
| L5 | `seed` equals `params["seed"]` when that value is an integer (`type(x) is int`), and is null otherwise | yes; `params` is id-bound |
| L6 | When `"shuffle" in params` and the method is a carve: `params["shuffle"]` is a bool, and `method == "shuffled_carve"` if and only if it is true | yes |
| L7 | `"sizing_mode" in params` implies `strategy.sizing_mode == params["sizing_mode"]` | yes |
| L8 | `pre_carve_order == "seeded_shuffle"` implies an integer `seed` | yes |

There is deliberately **no** rule that `fit_scope == "train"` implies a non-empty train partition: equities_seq fits on frame rows and counts windows (§3.1 note 4).

### 8.2 Class rows

Each row gives the legal methods, sizing modes, seeds and fit scopes of a class, and the `pre_carve_order` its `params` imply. That last column is **derived**: the gate computes it from the id-bound `params` and compares, so it is not a declaration the gate must trust.

| class | method | sizing_mode | legal `seed` | `pre_carve_order` implied by `params` | legal `fit_scope` | further |
| --- | --- | --- | --- | --- | --- | --- |
| `synthetic_tabular` | `shuffled_carve`, `ordered_carve` | `additive`, `carve` | int, null | `as_produced` | `none` | — |
| `real_carve`: mnist | `shuffled_carve`, `ordered_carve` | `carve` | int, null | `seeded_shuffle` iff `params.seed` is an int | `none`, `constant` | `additive` is illegal: the params model rejects it (`partition_params.py:110-111`), so a block that declares it did not come from this code |
| `real_carve`: arc_agi | as mnist | `carve` | int, null | `seeded_shuffle` iff `params.seed` is an int **and** `params.n_tasks` is non-null | `none` | as mnist |
| `real_carve`: csv_import | as mnist | `carve` | int, null | `as_produced` | `none`, `train`, `non_train_fallback` | as mnist |
| `temporal_rows` | `temporal_rows_per_entity` | null | int, null | `as_produced` | `none`, `train`, `non_train_fallback` | a null `params.end_date` requires `resolved_inputs.end_date` |
| `temporal_windows` | `temporal_windows` | null | int only | `as_produced` | `none` | — |
| `temporal_entity_windows` | `temporal_windows_per_entity` | null | int, null | `as_produced` | `none`, `train`, `non_train_fallback` | as `temporal_rows` |
| `external_store`: huggingface | `ordered_carve` | `carve` | int, null | `seeded_shuffle` iff the hashed `params.seed` is an int | `none`, `constant`, `train` | — |
| `external_store`: kaggle | `ordered_carve` | `carve` | int, null | as huggingface | `none`, `train` | — |

### 8.3 What the gate does with an illegal combination

**This subsection depends on OQ-2**, which is open. It is written for both answers.

- **If OQ-2 is answered as recommended** (refuse by default, with a recorded override):
  - By default the gate raises.
  - A consumer may pass `allow_illegal=True`. The gate then returns the findings with status `accepted_with_findings` instead of raising.
  - The consumer MUST record those findings on the run, the way cascor records the §6.4 override: as a caveat on the reported metrics, behind a setting of its own (cascor: `JUNIPER_CASCOR_ALLOW_ILLEGAL_PARTITION_PROVENANCE`, W7), beside `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT` (`src/api/settings.py:557`, read at `src/api/lifecycle/manager.py:3739`).
- **If OQ-2 is answered "warn only"**: the gate never raises on a legality finding. It returns `accepted_with_findings`, and every consumer MUST log and record the findings the same way.
- **In both cases, integrity failures (G0–G4 in §9.3) can never be overridden.** A block that disagrees with its own artifact describes some other artifact.

### 8.4 Deliberately not checked: counts re-derived from `params`

Some counts are closed-form in `params` and the verified row counts:

- additive `val = round(train × val_percent / 100)` (`core/split.py:200-201`);
- a carve whose ratios cover the whole dataset (`:489-490`);
- `temporal_split_indices` over the window total (`:343`).

**Why the gate does not re-derive them.** Doing so would copy the producer's rounding and trim logic into the client, including `resolve_partition_counts`'s negative-remainder path (`:504-510`). A mismatch would then be as likely to be a client bug as a producer bug. **The gate checks counts against array shapes only**, which is what the ruling itself says. Revisit this if a sizing defect ever ships.

## 9. The gate

### 9.1 Where it lives

**Location.** A new module, `juniper_data_client/provenance.py` (proposed). It is exported from the package root beside `validate_npz_contract` (`juniper_data_client/__init__.py:9,16`).

**It is not placed inside `validate_npz_contract`**, for three reasons:

- `validate_npz_contract`'s tabular path returns before any check (`contract.py:74`);
- cascor never calls it;
- canopy does not gate on it: the owner ruled on 2026-09-22 (canopy#559) that canopy runs it **advisory-only**, and juniper-canopy#663 (merged 2026-09-23, `cc3588a8`) implements that. A helper that canopy may only warn on cannot host a gate canopy must enforce.

Hosting provenance there would reach only one of the three consumers.

**The client, not the producer, hosts the gate.** Every consumer already depends on the client. The producer does not at runtime: juniper-data pins the client only in its `test` extra (`pyproject.toml:123`). So juniper-data keeps its own builder and digest (W6 in §11). Two things hold the two implementations together: the golden vectors (§6), and a producer test that runs every generator's artifact through the published gate.

### 9.2 Interface (proposed names)

```python
def validate_partition_provenance(
    arrays: Mapping[str, np.ndarray],
    *,
    dataset_id: str | None = None,   # the id the consumer requested, when it has one
    allow_illegal: bool = False,     # meaningful only under OQ-2's recommended answer (§8.3)
) -> ProvenanceReport: ...            # status, findings, decoded block
# on refusal: raises JuniperDataProvenanceError, a subclass of JuniperDataContractError
```

Also exported: `decode_partition_provenance`, `array_digest`, `build_partition_provenance` (for the `testing` fakes and third-party producers), `NPZ_KEY_PARTITION_PROVENANCE`, `ARRAY_DIGEST_SCHEME`, `GATE_SCHEMA_VERSION` (`1`) and `FIRST_EMITTING_VERSION`, the per-generator table of §7.3. **`FIRST_EMITTING_VERSION` ships EMPTY** and is filled only after the producer's release (W11 in §11). `JuniperDataContractError` is already a `ValueError` subclass (`exceptions.py:82`: `class JuniperDataContractError(JuniperDataClientError, ValueError):`), so existing `except ValueError` call sites keep working.

### 9.3 Checks, in order

Every finding within a stage is collected; no check stops the others in its stage from running.

| id | stage | check | re-derives or trusts |
| --- | --- | --- | --- |
| G0 | decode | §4.1's strict decode (0-d `<U`; a JSON object; no duplicate key; canonical form); the two version fields (§7.1); the eight core fields present with their JSON types; `digest.algorithm` is `sha256`. When the gate meets `min_reader_version`, also the four legality fields and their types | — |
| — | scheme | If `digest.scheme` is not one this gate implements, stop: `unverifiable` | — |
| G1 | integrity | Structure: `partitions` has exactly `train`, `val`, `test`, each exactly `rows` and `arrays`. Coverage: every artifact key except the block is declared exactly once, every declared key exists, `X` and `y` are declared in all three partitions, and no `unpartitioned` key ends in a split suffix | re-derives |
| G2 | integrity | Every declared partition array has rank ≥ 1, and its `shape[0]` equals its partition's `rows` | re-derives |
| G3 | integrity | Every declared array's dtype is in §6's allowlist and its digest recomputes | re-derives |
| G4 | integrity | `dataset_id` equals the requested id when the consumer passed one; `id_nonce` is consistent with `params` (§7.2); and the id re-derives **exactly**, store prefix included. **Unconditional**: seeded or not | re-derives |
| — | reader | If `min_reader_version` exceeds `GATE_SCHEMA_VERSION`, stop: `integrity_only` | — |
| G5 | legality | §8.1 and §8.2 | Trusts `method`, `fit_scope`, `stems`, `resolved_inputs`, and whether a non-null seed actually mattered. **Derives** `pre_carve_order`. Constrains only their combinations |

G2's rank check comes first so that a malformed artifact, such as a 0-d `X_train`, produces a finding rather than an `IndexError` (§10.2 check B7.a).

### 9.4 Outcomes

| state | status | action |
| --- | --- | --- |
| Key absent, and the consumer passed no `dataset_id`, or its id is for a generator not in `FIRST_EMITTING_VERSION`, or is below that generator's first emitting version | `absent` | Tolerate: "Legacy artifacts without the block must stay loadable, per the contract rule 'tolerate, never require'" (juniper-data#423). Every artifact minted before the producer ships is here |
| Key absent, and the requested id's version is **at or above** its generator's first emitting version | — | **Refuse; not overridable.** The id proves the producer stamped this artifact, so the block was stripped or the artifact substituted. The id is parsed from the right: `…-{generator}-{X.Y.Z}-{16 hex}`, which also covers the stores' prefix. Depends on OQ-1 being answered yes, and is inert until W11 fills the table |
| G0 fails | — | Refuse; not overridable (malformed) |
| `digest.scheme` unknown | `unverifiable` | Tolerate, and log a warning. Only G0 ran |
| Any G1–G4 finding | — | Refuse; not overridable |
| `min_reader_version` above the gate's | `integrity_only` | Tolerate, and log. Integrity verified; legality not judged |
| G5 findings only | — | Per §8.3: refuse, or with `allow_illegal=True` `accepted_with_findings` (OQ-2 recommended); `accepted_with_findings` (OQ-2 "warn only") |
| No findings | `verified` | Proceed |

A consumer MUST NOT treat `unverifiable` or `integrity_only` as `verified`: it records the status beside the run, as it records `absent`.

### 9.5 Call sites

Each consumer calls the gate **immediately after downloading the artifact**, on the mapping **exactly as loaded**, while `dataset_id` is still in scope. A call site that adds keys first trips G1: recurrence's `derive_full_split` adds `*_full` keys, for example (§10.2 check B7.b). This census was re-run for v2 with a sweep for raw `/artifact` fetches, `np.load` of artifact bytes, and in-process `generate` calls, not only for the client method.

| repo | site (at the pins in the header) | note |
| --- | --- | --- |
| cascor | `src/api/lifecycle/manager.py:4210` (`_reload_dataset`) | Before `_artifact_to_tensors` (`:4239`). Publish the status on `get_status()` beside `dataset_shortfall` (`:2846`) and `current_dataset` (`:2868`) |
| cascor | `src/api/app.py:563` (`_auto_start_training`) | Before `_artifact_to_tensors` (`:603`) |
| cascor | `src/spiral_problem/data_provider.py:193` (the CLI) | Before `_convert_arrays_to_tensors` (`:196`) |
| canopy | `src/demo_mode.py:1123` (`_generate_spiral_dataset_from_juniper_data`) | Right after the download, before `_validate_npz_arrays` (`:1131`). OQ-5 |
| canopy | `src/demo_mode.py:2026` (`regenerate_dataset_from_generator`) | Right after the download. Not before `_validate_npz_arrays` (`:2061`): a 3-D artifact returns through `_install_sequence_dataset` (`:2059`) and never reaches it. The advisory `_advise_npz_contract` runs at `:2043`. OQ-5 |
| recurrence | `juniper-recurrence/juniper_recurrence/data.py:76` (`load_sequence_data`) | After the download, before `validate_npz_contract` (`:77`) and before `sequence_data_from_arrays` (`:78`), which derives `*_full` keys for `split="full"` |
| ml | `util/experiments/run_experiment.py:1230` and `:1332` | Raw `/v1/datasets/{id}/artifact` fetches through `_http_bytes`, turned into arrays by `load_npz_bytes` (`util/experiments/plots_cascor.py:43`, `util/experiments/plots_recurrence.py:49`). W12: run the gate and record its status in the run's evidence, but never refuse, because a plot is not a trained result |
| data | the test suite | Every generator's artifact goes through the published gate (W6) |

**Declared non-consumers**, each checked:

- **juniper-recurrence `bench/datasets.py`** calls the generators in-process, e.g. `EquitiesSeqGenerator.generate` (`:267`), so it never sees an NPZ or a block. `bench/app_e2e.py` drives `load_sequence_data` through a `_FakeClient` (`:47`, patched in at `:64`), so the recurrence call site above already runs there.
- **juniper-ml `util/snapshot_attribute.py:341`** generates in-process. Nothing else in juniper-ml outside `util/ad-hoc/` calls `download_artifact_npz`.
- **juniper-recurrence-model's `load_sequence_npz`** (`juniper_recurrence_model/data.py:53-59`) reads an `.npz` from a path. It is public API with **no production caller** in the ecosystem; only its own tests use it. juniper-recurrence-model depends only on numpy and juniper-model-core (`juniper-recurrence-model/pyproject.toml:31-37`), so v2 does not add a client dependency to gate it. W9 documents in its docstring that it performs no provenance check, and that a caller wanting one runs the client's gate on the loaded mapping. v1's W9 placed a check there without the dependency to make it.
- **Client methods that bypass `download_artifact_npz`**: `download_artifact_bytes`, `batch_export` (a ZIP of NPZs) and `get_preview`. No production code calls them. A future caller of either of the first two gates each NPZ it loads.
- **juniper-data's own reads** (`preview_dataset`, the cached store) are not consumers. The cached store's re-save preserves the block (§4.4).

## 10. Verification

### 10.1 v1's round-trip script

`util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py` runs 18 checks, and it was run in five interpreters on 2026-09-22.

| interpreter | Python / numpy | producer and client under test | result |
| --- | --- | --- | --- |
| `JuniperData` | 3.14.2 (free-threaded) / 2.4.1 | editable installs of the v1 checkouts | 15 PASS, 3 INFO, 0 FAIL |
| `JuniperCascor1` | 3.14.7 / 2.5.3 | the same checkouts | 15 PASS, 3 INFO, 0 FAIL |
| `JuniperCanopy1` | 3.13.13 / 2.4.6 | client 0.5.0, plus a **stale site-packages juniper-data 0.6.0** | 13 PASS, 3 INFO, 1 SKIP, 1 FAIL. The FAIL is P1: juniper-data 0.6.0 predates `sizing_mode`, so the producer-side results say nothing about current code. Its J2 result is moot for the same reason |
| `JuniperCassandra` | 3.11.13 / 2.3.3 | neither installed | 9 PASS, 3 INFO, 6 SKIP |
| scratch venv | 3.11.13 / 1.26.4 | neither installed | 9 PASS, 2 INFO, 7 SKIP (numpy 1.x has no `StringDType`) |

- **Golden vectors.** The fingerprint (`47fba46f…6c5733`) is identical in all five. That spans numpy 1.x and 2.x, big-endian inputs, Fortran order, and both NPZ writers.
- **Cross-version files.** An artifact written by the numpy 2.4.1 producer loaded and verified under numpy 1.26.4 and under 2.5.3 (`--write-payload`, then `--read-payload`).
- **Tamper detection** (check P2) on a real spiral artifact: a flipped value, a dropped row, an extra key, an edited `params` value, and a wrong requested id each produce the right finding.
- **Encoding hazards.** Object arrays (checks E6, P3, L2) and `StringDType` (E4) both fail under `allow_pickle=False`. `<U` survives it (E1), including through the real `download_artifact_npz` (L1).

**What it does not show.** Its gate was a prototype. Round 1's defects were in gate logic that existed only as prose, and those 15 PASS results said nothing about them.

### 10.2 v2's reference gate

`util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py` implements §4–§9 of this document independently of any juniper-data or juniper-data-client code, and attacks it. Run on 2026-09-23 under `JuniperData` (Python 3.14.2, numpy 2.4.1) against a juniper-data checkout at the pin, `90ad035e`: **52 PASS, 0 FAIL, 0 SKIP**. Without such a checkout, groups I and R SKIP and the other 48 checks still run.

| group | what it shows |
| --- | --- |
| V1–V3 | v1's nine golden digests and fingerprint are unchanged under v2's allowlist; the nine refusal vectors of §6 are refused (`longdouble` is `<f16` on this host); a `True` stored as byte `0x02` digests like a canonical `True` |
| I1–I3 | For the 15 generators with default-constructible params (csv_import needs a file), the reference re-derivation equals juniper-data's real `generate_dataset_id`. With the nonce fixed, an unseeded id re-derives exactly. Four store ids re-derive exactly through the real `external_dataset_id` |
| R1 | Every one of the 16 generators, built offline with juniper-data#430's fleet builders, gets a block, survives an `allow_pickle=False` NPZ round trip, and verifies. mnist comes out `shuffled_carve` / `seeded_shuffle` / `constant`, csv_import `train`, the rest as §5.4 predicts |
| B1–B7 | One or more vectors for each round-1 finding (§14): the stores' train fit verifies; a seeded mnist or arc_agi artifact must declare `seeded_shuffle`; `schema_version` `"1"` and `true` are refused; a newer schema cannot hide a corrupted array; an unknown scheme is `unverifiable`; an unseeded artifact is id-bound; a stripped block is refused only at or above the first emitting version, and never while the table is empty; `longdouble` is refused; duplicate keys, non-canonical text, `seed: true` and `rows: 2.0` are refused; a 0-d `X_train` is a finding; a key added after loading trips G1; a wrong store prefix is refused |
| T0–T5, O1–O2 | v1's tamper cases against the v2 gate; the legality override, and that integrity ignores it |

**What it does not show.** The script derives each real artifact's facts (method, pre-carve order, fit scope) itself, from the generator code as §3 describes it. So R1 shows that §8 admits blocks built that way. It does not show that a producer will build them that way: that is W6's builder, whose facts must come from the generator's own code paths. And it runs no network source: mnist and the equities pair are built from offline stand-ins.

## 11. Rollout and work items

### 11.1 Order: gate first

Either order is safe for today's consumers, because none of them breaks on an extra key (§4.3). Gate first is recommended for three reasons:

- **The producer can prove agreement before it ships.** juniper-data's CI runs every generator's artifact through the *published* gate. A digest disagreement then fails a build, instead of making every consumer refuse every new artifact on the day of the deploy.
- **Consumer PRs merge as no-ops.** Every existing artifact reports `absent`, so enforcement begins by itself once blocks appear.
- **Producer first would store blocks that nothing checks.** They would sit in content-addressed, long-lived storage, so a producer bug would persist there until the gate arrived to refuse it.

**The one exception is the stripped-block refusal** (§9.4). It compares a requested id's version with `FIRST_EMITTING_VERSION`, so that table must record versions the producer has **actually shipped** with blocks. Shipped before the producer, the table could only record a plan: if any generator then moved to its planned version or beyond for another reason, every consumer would refuse that generator's legitimate block-less artifacts. So the table ships empty (W5) and is filled after W6's release (W11).

### 11.2 Versions, floors and caps

- **juniper-data-client 0.5.0 → 0.6.0.** A MINOR bump, because it adds public API.
  - Both consumer caps are `<0.6.0`: canopy (`juniper-canopy/pyproject.toml:192`) and recurrence (`juniper-recurrence/pyproject.toml:54`).
  - Both are widened to `<0.7.0` **before** the Release. The owner ruled on 2026-09-05 that a downstream cap never lowers a SemVer bump (juniper-cascor-client#155, juniper-canopy#584).
  - The release train proposes those ceiling PRs for any pre-1.0 MINOR bump (`util/release_train/propose.py:930`).
  - Floors rise only once the wheel is on PyPI.
- **juniper-data-client 0.6.0 → 0.6.1 (W11).** A PATCH: filling `FIRST_EMITTING_VERSION` refuses only artifacts whose block was stripped, and a genuine artifact at or above its generator's first emitting version always carries one (W6's fleet test). The `<0.7.0` caps admit it.
- **juniper-data 0.15.0 → 0.16.0.** MINOR, because it adds an artifact key. Its `test` extra's client floor rises to `>=0.6.0`.
- **cascor.** Its client pin has no cap: `juniper-data-client>=0.3.0` in the `juniper-data` extra (`juniper-cascor/pyproject.toml:118`). The floor rises to `>=0.6.0` together with the call sites.
- **juniper-ml meta-package**, after both releases are published:
  - `[clients]`: `juniper-data-client>=0.6.0` (`pyproject.toml:67`);
  - `[servers]`: `juniper-data>=0.16.0` (`:86`), so that `pip install juniper-ml[all]` installs a producer that emits the block.

### 11.3 Work items

Sizes: S is one PR in under a day; M is one or two PRs over a few days; L is several PRs.

| # | repo | item | size | depends on |
| --- | --- | --- | --- | --- |
| W0 | data | F-1: `task_ids` as `np.str_`; arc_agi `VERSION` `3.0.0 → 4.0.0`; a fleet test loading every generator's artifact with `allow_pickle=False`. **juniper-data#430** | S | — |
| W1 | data | The stores emit three partitions. **Done: juniper-data#422**, merged 2026-09-23 as `ce436819` | — | — |
| W2 | data | F-2: the stores fit on train, after the carve (OQ-4). **Done inside W1** | — | W1 |
| W3 | ml | Ratify this spec and rule on OQ-1 to OQ-6, **recorded in §16** of this document and mirrored as a comment on juniper-data#423 | S | §15's round passing |
| W4 | canopy, recurrence | Widen the `juniper-data-client` caps to `<0.7.0` | S each | W3 |
| W5 | data-client | `provenance.py`: decode, digest, gate, class map, exception, `FIRST_EMITTING_VERSION` **empty**. The `testing` fakes emit blocks, and **mint their dataset ids from the block's re-derivation** instead of `uuid4` (`testing/fake_client.py:417`), or every fake-backed test fails G4. Golden and refusal vectors as tests. Release 0.6.0 | M | W3, W4 |
| W6 | data | See the list below; ends with Release 0.16.0 | L | W0, W2, W5 |
| W7 | cascor | The three call sites (§9.5); the setting `allow_illegal_partition_provenance` / `JUNIPER_CASCOR_ALLOW_ILLEGAL_PARTITION_PROVENANCE` (default false; only under OQ-2's recommended answer); the gate status on `get_status()`; floor `juniper-data-client>=0.6.0` | M | W5 |
| W8 | canopy | The two call sites (OQ-5); floor `juniper-data-client>=0.6.0` | S | W5 |
| W9 | recurrence | The client call site; a docstring on `load_sequence_npz` saying it performs no provenance check (§9.5); floor `juniper-data-client>=0.6.0` | S | W5 |
| W10 | ml | The meta-package floors (§11.2) | S | W5 and W6 published |
| W11 | data-client | Fill `FIRST_EMITTING_VERSION` with the versions W6's release **actually** shipped, read from the published wheel, and release 0.6.1 | S | W6 published |
| W12 | ml | The two plot loaders run the gate and record its status; they never refuse (§9.5) | S | W5 |

W6 (juniper-data) covers:

- the `core/provenance.py` builder;
- `generate_dataset_id` gains an optional `nonce` argument, and the route draws the nonce itself so it can record it (§7.2); a seeded call is unchanged;
- `external_dataset_id` returns the dict it hashed as well as the id, and the stores build their blocks from it;
- the reserved `partition_facts` channel in all 16 generators, popped beside `pop_scaling_meta` (`core/meta.py:172`), carrying method, pre-carve order, fit scope and stems, and resolved inputs from the generator's own code paths;
- the route insertion (§4.4), and the stores calling the builder;
- the VERSION bumps (OQ-1, §7.3) and the floor test's allow-list;
- fleet tests: every generator emits a block; each seeded id has a byte-identical block; every artifact passes the published client gate with status **`verified`** (not merely "not refused", so a producer cannot ship a scheme or a reader version the published gate does not know); and a cached re-save preserves the block.

W7–W9 and W12 can merge before W6, because they are no-ops until blocks exist.

## 12. Open questions for the owner

**OQ-1. Should generator `VERSION` be bumped when producers start emitting the block?**

- **Recommendation**: yes, MINOR: `3.1.0`, `4.1.0` for arc_agi, `5.1.0` for the equities pair, `3.1.0` for the stores (§7.3).
- **Evidence**: decision 11's reasoning about cache state (`test_val_emission_guards.py:241-244`). The floor test reads only the major version (`:288`). The cost is one fleet-wide cache miss. §9.4's stripped-block refusal depends on a yes.

**OQ-2. On a legality failure, refuse by default with a recorded per-consumer override, or only warn?**

- **Recommendation**: refuse by default, with a per-consumer override that is recorded as a caveat on the metrics.
- **Evidence**: this mirrors `…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §6.4 and cascor's `allow_missing_validation_split` (`manager.py:3739`). A legality check that only warns is a declaration nobody reads. §8.3 and §9.4 are written for both answers.

**OQ-3. Should real-data sources record a digest of their input, as `resolved_inputs.source_sha256`?**

- **Recommendation**: yes for `csv_import`, as the SHA-256 of the bytes read. Defer the HF, Yahoo and SEC sources.
- **Evidence**: identical `CsvImportParams` produce different data under a different `JUNIPER_DATA_IMPORT_DIR` (`…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.4.4 item 6).

**OQ-4. The external stores normalised before they carved (F-2). Fix them first, or let them emit `all_rows` and be refused?** **Answered by the fix: the stores were fixed first.**

- **Resolution**: juniper-data#422 (`ce436819`) fits the stores' statistics on `X_train` after the carve, under the owner's 2026-09-22 ruling to conform the stores. No ruling is needed.

**OQ-5. Should canopy call the provenance gate?**

- **Recommendation**: yes, at both download sites (§9.5).
- **Evidence**: on 2026-09-22 the owner ruled that canopy runs `validate_npz_contract` as an **advisory** check only (canopy#559, implemented by juniper-canopy#663). The reason was that the helper fails closed on a legacy artifact that canopy must still load. This gate tolerates an absent block by construction, so that objection does not apply to it. Whether its *legality* refusals should be advisory in canopy is part of OQ-2.

**OQ-6. Enforce from the first release, or ship one release in report-only mode?**

- **Recommendation**: enforce from the first release.
- **Evidence**: W6's producer test runs every artifact through the published gate before release, which is the risk a report-only release would guard against. A report-only mode is a switch someone can forget to turn off. The stripped-block refusal is already staged (W11).

## 13. What this specification cannot do

The first three items carry forward the limits in `…TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.6.3. The rest were found while grounding this document or reviewing it.

1. **A truthful block can describe a degenerate artifact.**
   - **The case.** Lane B's `xor(margin=x_range=y_range)` artifact had every provenance field correct and passed every derivable check. Yet 40 of 40 test rows were byte-identical to train rows (§9.6.3 of the same design), and it contained only 4 distinct rows out of 200 (§9.6.4).
   - **The limit.** The block checks an artifact against its own declaration, never against usefulness. The degeneracy check that would have caught this was dropped on 2026-09-03, and nothing here restores it.
2. **Strategy, seed and fit scope are declarations.** None of them can be derived from a single artifact. The legality table constrains how they combine and ties some of them to the id-bound `params` (`pre_carve_order` entirely), but it cannot show that the producer did what it declared.
3. **A declared seed does not mean the seed mattered.** `seed_sensitivity` is not adopted: in §9.4.4 item 4 of the same design, 19 of 60 seed pairs disagreed at a single configuration. `mackey_glass` at `init_noise_std=0` (§9.6.5) and the equities pair (`equities/params.py:137`) carry seeds that change nothing.
4. **Integrity, not authenticity.** The arrays are not part of the id hash. Whoever can rewrite an artifact can therefore build a consistent block around new arrays while keeping `params` unchanged. The gate catches corruption, truncation, the wrong artifact being served, a stripped block (once W11 ships), and inconsistent edits (check P2). It does not catch deliberate forgery, which would need a signature.
5. **An unknown scheme is tolerated.** A block naming a digest scheme the gate does not implement is `unverifiable`, so an edit that changes only that string escapes G1–G4. Random corruption cannot produce a canonical block with a different, valid scheme name; a deliberate edit is forgery (item 4). W6's fleet test requires `verified`, so the producer cannot ship an unknown scheme by mistake.
6. **Recording is not reproducing.**
   - **Unpinned inputs.** A null seed means OS entropy. The real-data inputs are not pinned by `params`: `csv_import` files (unless OQ-3 is accepted), HF datasets, and Yahoo and SEC data.
   - **Unpinned RNG.** The block names the seed but not the RNG implementation. Content under a given seed also depends on numpy's `Generator` algorithms, and this spec neither relies on nor verifies that their streams stay stable across numpy releases.
7. **Disjoint rows are not independent rows.**
   - **Temporal windows** share lookback input steps across partition boundaries; there is no embargo (`_sequence.py:71`).
   - **`arc_agi`** turns each task into several input/output pairs (`arc_agi/generator.py:237-257`) and shuffles them row by row, so one task can span partitions.
   - **The limit.** The block names the method; it does not measure dependence between partitions.
8. **Legacy artifacts stay unverifiable.** Every artifact minted before the producer ships reports `absent`, and none is backfilled: rewriting a content-addressed artifact would change its bytes under an unchanged id.
9. **The gate sees only what a consumer passes it.** A reader that bypasses the client stays unchecked unless it calls the gate itself: juniper-recurrence-model's `load_sequence_npz`, ad-hoc scripts (several of juniper-ml's `util/ad-hoc/` scripts read store files from disk), and notebooks.
10. **The stripped-block refusal starts late.** Until W11 ships and consumers pick up 0.6.1, a stripped block reads as `absent`.
11. **Cross-snapshot comparability** is not obtained (§9.6.1 of the same design) and is not a goal.

## 14. Review round 1 — findings and their disposition

Consensus review round 1 ran on 2026-09-23 against v1 as it then stood (juniper-ml#2043, `8b8d5d94`; v1's §14 at that commit holds each finding's full text). Three lanes were each told to refute it: **S1** re-probed every citation, **S2** attacked the identity, versioning, legality and digest layers, and **S3** tried to execute §11 as a work plan. S2 rated v1 **UNSOUND** in identity, versioning and legality; S3 rated it **EXECUTABLE WITH GAPS**. The encoding (one 0-d `<U` array under one key) and the digest's construction held.

v1 left its body as reviewed and recorded the findings here, following the precedent of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §9. v2 folds every finding into §1–§13:

| id | severity | finding | disposition in v2 |
| --- | --- | --- | --- |
| B-1 | BLOCKER | The legality layer refused correct store artifacts, and L6 mislabelled mnist and arc_agi | §5.3 lists the stores under `train`. §5.2 redefines `method` as the carve's own permutation and adds `pre_carve_order`; §8.2 derives it from `params` for mnist, arc_agi and the stores, so it is checked, not trusted (B1.a–B1.g) |
| B-2 | BLOCKER | Tolerating an unknown `schema_version` turned refusals into passes | §7.1: an integrity core keyed on `digest.scheme`, a legality layer keyed on the new `min_reader_version`, strict int checks in G0, and `integrity_only` as a status. An unknown enum at a readable version is illegal (B2.a–B2.h) |
| B-3 | BLOCKER | The id binding was skipped for every unseeded generator artifact | §7.2: the nonce is recorded as `id_nonce`, G4 is unconditional, and `external_dataset_id` returns the dict it hashed (I1–I3, B3.a–B3.e) |
| B-4 | MAJOR | An absent block was tolerated where the id proves one must exist | §9.4: refused at or above a generator's first emitting version. **Resolved differently from the proposal**: the table is filled after the producer ships (W11), not planned in advance, because a planned table would refuse legitimate artifacts if a generator moved to its planned version for another reason (§11.1) (B4.a–B4.g) |
| B-5 | MAJOR | The digest's dtype kinds admitted `longdouble` | §6: an exact allowlist, measured against every generator's output, nine refusal vectors, and `|b1` hashed by value (V1–V3, B5.a) |
| B-6 | MAJOR | Canonical JSON was declared, not enforced | §4.1 and G0: duplicate keys refused through `object_pairs_hook`, the text must equal its re-serialisation, and integers are checked with `type(x) is int` (B6.a–B6.e) |
| B-7 | MAJOR | Four robustness gaps in the gate | (a) G2 checks rank first; (b) §9.5 requires the mapping exactly as loaded; (c) G4 requires exact equality with a per-store prefix rule; (d) §9.5 declares `load_sequence_npz` an ungated reader with no production caller, instead of adding a client dependency to juniper-recurrence-model (B7.a–B7.c) |
| R-1 | BLOCKER | §9.5's consumer census was incomplete | Re-run with the wider sweep. It found both juniper-ml plot loaders (now W12) and **one v1 error**: canopy's second site returns 3-D artifacts before `_validate_npz_arrays`, so the gate goes right after the download. `bench/datasets.py` and `snapshot_attribute.py` are declared non-consumers |
| R-2 | MAJOR | OQ-2 was open, but §8.3 and §9.4 presumed its answer | §8.3 and §9.4 are written for both answers |
| R-3 | MAJOR | W8 and W9 said "floor" without a value | `juniper-data-client>=0.6.0` in W7, W8 and W9 |
| R-4 | MAJOR | W0 named no target for arc_agi's `VERSION`, which collided with §7.3 | W0 is `4.0.0` (juniper-data#430); arc_agi's first emitting version is `4.1.0` (§7.3) |
| R-5 | MAJOR | W3 named no artifact for the ruling | §16 of this document, mirrored on juniper-data#423 |
| R-6 | MINOR | W7 did not name the legality-override setting | `JUNIPER_CASCOR_ALLOW_ILLEGAL_PARTITION_PROVENANCE` (§8.3, W7) |
| R-7 | MINOR | "Fixed at #422's head" wording was written while #422 was open | "fixed on `main` by juniper-data#422 (`ce436819`), not yet released", throughout |

Citations fixed in place during round 1, all re-checked at v2's pins: **C-1** the stores insert the block at their loaders' `save` (`hf_store.py:199`, `kaggle_store.py:288`); **C-2** the recorded `params` dicts are at `hf_store.py:162` and `kaggle_store.py:256`; **C-3** `JuniperDataContractError` is at `juniper_data_client/exceptions.py:82`, and the words "tolerate, never require" come from juniper-data#423; **C-4** the HF images' `/ 255.0` is at `hf_store.py:282`.

## 15. Review round 2

Consensus review round 2 ran on 2026-09-23 against v2 as committed (juniper-ml#2060, `8c9d65f`), with the text frozen for its duration. Four lanes were each told to refute it:

- **S1** re-probed every factual claim, and did not trust the citation checker's rows to check what the text claims;
- **S2** attacked the identity, versioning, legality, digest and encoding layers;
- **S3** tried to execute §11 as a work plan;
- **S4** checked that each of round 1's findings was folded and that nothing load-bearing was amputated.

**Each lane's final report is archived verbatim** under `reports/partition-provenance-spec-v2-review-2026-09-23/`, as `S1-grounding.md`, `S2-soundness.md`, `S3-executability.md` and `S4-fold-completeness.md`, and holds the vectors and scratch-script names behind each finding. The ids below (S1-F1, S4-D3 and so on) are those reports' own.

| lane | verdict | MAJOR | MINOR | NIT |
| --- | --- | --- | --- | --- |
| S1 grounding | GROUNDED WITH FINDINGS | 2 | 4 | 7 |
| S2 soundness | **not ready for ratification**: versioning unsound but fixable; identity, legality and encoding sound with findings; digest sound | 3 | 5 | 3 |
| S3 executability | EXECUTABLE WITH GAPS | 5 | 6 | 1 |
| S4 fold completeness | COMPLETE WITH FINDINGS | 3 | 11 | 10 |

**What held.**
- Round 1's four blockers are fixed. A newer or corrupted `schema_version` can no longer skip the integrity checks.
- Every class row, `pre_carve_order` derivation and seed rule is true of the code at the pins. No truthful artifact of today's code was refused.
- S1 reproduced all nine golden digests and the fingerprint from §6's prose alone, with an implementation of its own.
- The consumer census was re-swept by S1, and nothing was missing or mislocated.

**v2 is not ratifiable.** Deduplicated, the round's MAJOR findings fall into ten clusters. Where two lanes found the same defect independently, both ids are given.

| cluster | finding | lanes | v3 must |
| --- | --- | --- | --- |
| **R2-1** versioning | G0 checks the core fields' types and `digest.algorithm` **before** the scheme check, so a core change under a new `digest.scheme`, the one path §7.1 sanctions, is refused rather than reported `unverifiable`. At an unknown scheme, the requested-id compare is skipped too | S2-F1, S4-D1 | Split G0: first decoding, the version fields, a string `digest.scheme` and `dataset_id` against the requested id; the core types and the algorithm after the scheme. Freeze where `digest.scheme` lives, and add the missing vector |
| **R2-2** versioning | v1's §7.1 rules for when `schema_version` increments and what a gate must judge were dropped with no replacement. The two version fields are in neither layer, and the gate's own B2.c bumps the version for an added field, the opposite of v1's rule | S4-D2 | Restore an increment rule and the obligation to judge every schema up to the gate's own, and freeze the version fields |
| **R2-3** legality | Class rows are keyed on generator **name**, not version. A generator that gains a legal behaviour at a new version is refused (mnist with a train fit; csv_import with a seeded sample). L6 and L7 apply to unknown generators, contradicting §8 | S2-F3 | Key class rows on generator and known version range, restrict L6 and L7 to known generators, widen the `min_reader_version` trigger, and run producer CI against the oldest supported gate |
| **R2-4** identity | The exact store-prefix rule is a two-entry table, so a third store built through the real `external_dataset_id` gets a non-overridable G4 refusal, contradicting §8. The rule is not in the frozen core either | S2-F2 | Carry the prefix in the core, check it exactly only for known stores, and freeze the prefix rules and the `"unshuffled"` marker |
| **R2-5** decision | The body decides OQ-1 while the header says it decides nothing: `FIRST_EMITTING_VERSION`, W11 and the §11.2 versions are written unconditionally. W11's premise, that every artifact at or above the listed version carries a block, is asserted rather than produced, and an intermediate `main` or a missed bump would make its refusal permanent | S4-D3, S3-F3 (and S2-F6) | Make W11 and the table conditional on OQ-1, write the "no" branch, bump each generator's VERSION in the same PR as its emission, and fill W11 from W6's own verified list |
| **R2-6** release | juniper-data **0.16.0 is already taken**: #433 merged five minutes before `8c9d65f` and ships without a block. A `>=0.16.0` floor would admit a producer that emits none | S1-F1, S4-D13 | The block ships in 0.17.0, and every floor and sentence that names 0.16.0 moves |
| **R2-7** release | W10 makes `juniper-ml[all]` unresolvable. The only published juniper-recurrence (0.5.0) requires `juniper-data-client<0.6.0`, and `publish.yml` checks only `[clients]` and `[tools]` | S1-F2, S3-F1 | Make a recurrence release carrying W4's widened cap a precondition of W10, and add an `[all]` dry-run resolve |
| **R2-8** release | juniper-data's CI installs the client from git `main`, not the published release, so a gate fix merged but unreleased passes the producer while consumers still refuse | S3-F2 | A W6 CI job that tests against the published client |
| **R2-9** release | "0.6.1 is a PATCH" conflicts with the owner rule of juniper-cascor-client#155: W11 turns a tolerated `absent` into a non-overridable refusal, a behaviour change | S3-F4 | Drop the caps argument, and either release 0.7.0 or put the question in §16 |
| **R2-10** consumers | The status and override surfaces are unnamed. The caveat W7 is told to copy (`_validation_warning`) is written but never read in cascor | S3-F5 | For each consumer and both OQ-2 answers, name the status field, the setting and a caveat slot that something reads, and add a canopy line to §16 |

**MINOR findings, recorded here and folded in v3:**
- **Integrity.** `fit_scope` is derivable for 16 of 18 sources but is trusted, so §13 item 2 is false (S2-F5). Legality can be switched off by editing two integers (S2-F4). Two decode failures escape G0 as the wrong exception type (S2-F7). Unknown nested keys are unspecified, and the gate treats them inconsistently (S2-F8).
- **Figures and citations.** §4.2's sizes are v1's block, not v2's (S1-F4). §7.3's 511 s is a defective run (S1-F5). §5.3 overstates what `test_normaliser_fit_scope.py:172` pins (S1-F6). The stores emit `<f4` only, so "parity with the stores" does not justify `<f8`, `<i8` and `|b1` (S4-D5, S1-F7). recurrence's `[bench]` caps `juniper-data<0.16.0` (S1-F3).
- **Consumers.** The fake depends on uuid ids in more places than `:417` (S3-F6). Wiring the gate into cascor breaks about 20 tests (S3-F7). The nonce and store-id interfaces are loose (S3-F8). Floors conflict with `==0.5.0` lock pins, and nothing adopts 0.6.1 (S3-F9). Two of the owner's possible answers have no plan (S3-F10). The document omits AGENTS/README edits, CHANGELOGs, image tags and operator notes (S3-F11).
- **Fold record.** §14 leaves two departures from round 1's proposals unlabelled (S4-D4, S1-F11). The census re-run has no recorded method (S4-D6). §9.1 went stale when W12 was added (S4-D7), and §4.3's reader list is incomplete (S4-D8). The vector coverage is overstated (S4-D9). §9.3 omits the stripped-block refusal (S4-D10). OQ-6 argues against the kind of switch W11 adds (S4-D11). §5.3 contradicts §3.1 note 4 (S4-D12). v1's pins were amputated (S4-D14).

**NITs** (S1-F7 to F13, S2-F9 to F11, S3-F12, S4-D15) are listed in the reports and folded with the rest.

**Disposition.** v3 folds every finding above into §1–§13, and a new §14-style table maps each id to where it went. A **round 3** then reviews v3's corrections, again with the text frozen, before the owner rules on anything (§16).

## 16. Ruling record

**Empty until the owner rules.** Each line records a ruling, its date and where it was given. W3 is complete when every question below has a line, and this section is mirrored as a comment on juniper-data#423.

| question | ruling | date | where |
| --- | --- | --- | --- |
| Ratify v2 (or its successor) | — | — | — |
| OQ-1 VERSION bump | — | — | — |
| OQ-2 refuse or warn | — | — | — |
| OQ-3 `source_sha256` | — | — | — |
| OQ-4 | answered by juniper-data#422 | 2026-09-23 | §12 |
| OQ-5 canopy | — | — | — |
| OQ-6 enforce from the first release | — | — | — |

## 17. References

- **Ruling**: `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`:
  - §6.1 and §6.4;
  - §9.2, decision 7;
  - §9.4.1, and §9.4.4 to §9.4.6;
  - §9.5.4, whose "Backward compatibility" paragraph is where the rule that consumers tolerate a retired key without requiring it originates. §9.4's absent-key row cites the wording juniper-data#423 gives it, because §9.5.4 does not use the phrase "tolerate, never require";
  - §9.6.1 to §9.6.6.
- **Rollout**: `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §4, §5, §6a, §9 and §10.
- **Issues and PRs**:
  - juniper-data#423: this decision;
  - juniper-data#411 and PR #422: the stores;
  - juniper-data#429 and #427, and PR #430: F-1 and arc_agi's `VERSION`;
  - juniper-data#314: fit scope;
  - juniper-data#319: seed defaults;
  - juniper-data#369: decision 11;
  - juniper-canopy#559 and PR #663;
  - juniper-cascor-client#155 and juniper-canopy#584: SemVer versus consumer caps.
- **Evidence**: `util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py`, `util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py`, `util/ad-hoc/2026-09-23_partition_provenance_dtype_inventory.py`, `util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py`.
- **Review round 2**: the four lane reports, verbatim, in `reports/partition-provenance-spec-v2-review-2026-09-23/` (extracted with `util/ad-hoc/2026-09-23_extract_agent_final_reports.py`).
