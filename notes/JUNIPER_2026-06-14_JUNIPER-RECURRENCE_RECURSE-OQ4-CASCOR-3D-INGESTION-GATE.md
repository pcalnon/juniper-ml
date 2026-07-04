# Cascor 3-D Sequence-Ingestion Gate — OQ-4 Build-Side Scoping

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 build-side investigation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — investigation, not ratified)
**Last Updated**: 2026-06-14

---

> **Epistemic legend.** `VERIFIED-CODE` = re-read against the live `file:line` this session (lead-read, juniper-cascor `main @ 0914ca1`). `SWEEP` = surfaced by a read-only sub-agent sweep this session; **every `SWEEP` citation was independently re-validated in §14** (all confirmed, with the minor line-number corrections recorded there). `INFERRED` = a deduction (lower confidence; flagged). `DATA-SIDE` = corroborated against the juniper-data / juniper-data-client repos + prior memory. Throughout, three things are kept strictly separate: a **rejection** (raises an error), a **silent mis-index** (runs, wrong axis), and the **algorithmic core** (the math that makes cascor 2-D by construction). Conflating "lift the cap" with "ingest a sequence" is the failure mode this document guards against.

> **Provenance.** Produced 2026-06-14 by a lead investigation of juniper-cascor (`main @ 0914ca1`) plus two read-only sub-agent sweeps (one mapping the cascor ingestion path, one mapping the juniper-data 3-D contract + the juniper-cascor-worker transport + cascor test coverage). The load-bearing architectural claims (the forward GEMM, the validation gate, `SharedTrainingMemory`, the candidate/hidden math) were lead-re-read line-by-line. §14 records the multi-agent validation pass run *after* this draft was written, per the anti-hallucination protocol.

---

## 1. Executive summary — the gate is a boundary, not a cap

The memory shorthand for this work was *"juniper-cascor `SharedTrainingMemory` `ndim>2` cap blocks 3-D windows."* That is true but it under-describes the situation by an order of magnitude. The accurate finding:

> **The "3-D ingestion gate" decomposes into three tiers. The shallow two are plumbing (a handful of rejections and ~a dozen `shape[1] ≡ features` indexings). The deep one is not a gate at all — it is the boundary between feedforward Cascade-Correlation and a recurrent network. cascor's forward pass, hidden-unit math, candidate-correlation math, and output layer are all 2-D GEMMs by construction. Lifting the shallow tiers lets a 3-D array *in*, but the only way to feed it to the 2-D core without touching the algorithm is to FLATTEN `(batch, lookback, features) → (batch, lookback·features)` — and flatten-then-feedforward is exactly the P4 delay-line / Takens lag-embedding, the design the OQ-4 evals ranked *weakest* (FIR, inherits the star-free ceiling, discards Δt). To genuinely consume the sequence/Δt axis (P1 / P3-C / LMU — the actual picks) is model work: a recurrent forward path, not a gate-lift.**

Two corollaries that sharpen the build plan:

- **The data side is already 3-D-ready; cascor is the sole unready consumer.** `equities_seq` emits `(W, 64, 10)` windows with explicit per-step `dt` and `target_dt` channels, and `juniper-data-client` already dispatches 2-D vs 3-D in `validate_npz_contract`. cascor's NPZ ingestion reads *only* the 2-D contract keys (`X_train`/`y_train`/`X_test`/`y_test` + `X_full`/`y_full`) and **never touches `dt`/`target_dt`** — so the irregular-Δt signal that is the entire point of the P3-C/LMU pick is dropped at the cascor boundary today (§7).
- **The distributed worker is *transport*-ready but not *math*-ready.** cascor has two IPC paths. The in-process candidate pool uses `SharedTrainingMemory`, whose binary descriptor stores exactly two shape dims (the hard cap). The *distributed* worker uses a *different* serializer (`SharedBinaryFrame`) that already round-trips N-D tensors — but it then runs the cascor-core `CandidateUnit` math, which is 2-D (`torch.sum(x * weights, dim=1)`). So neither path is end-to-end 3-D-capable; they are blocked at different layers (§5).

This investigation is the **build-side** complement to the design arc: the [dataset audit](JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md) already concluded the star-free ceiling-break is *not required* by any Juniper dataset, which is what makes the FLATTEN/P4 shortcut both available and undesirable — the requirement points at P3-C/LMU, the path the flatten shortcut cannot reach.

---

## 2. Scope, method, and what is meant by "the gate"

**Question scoped.** What would it take for juniper-cascor to *ingest and train on* 3-D windowed time-series input of shape `(batch, lookback, features)` instead of the current 2-D `(batch, features)`?

**Method.** Lead re-read of the network core in `src/cascade_correlation/cascade_correlation.py` (5,905 lines, `main @ 0914ca1`) and the shared `candidate_unit/candidate_unit.py`; two read-only sub-agent sweeps for breadth (ingestion path, data contract, worker, tests). Every architectural load-bearing claim was lead-verified; the long-tail gate inventory and the data/worker/test citations are `SWEEP` and are validated in §14.

**Definitions used throughout.**

| Term | Meaning | Build implication |
|------|---------|-------------------|
| **Rejection gate** | An explicit guard that raises on `ndim != 2` / `ndim > 2`. | Easy to change; fails loudly. |
| **Mis-index gate** | Code that reads `x.shape[1]` assuming axis 1 = features. | Runs on 3-D but grabs the *lookback* axis → silently wrong. Pervasive. |
| **Algorithmic core** | The 2-D GEMM forward, hidden-unit sum, candidate correlation, output weights. | Not a gate. The reason cascor *is* 2-D. Changing it = building a recurrent model. |

---

## 3. The data side is already 3-D-ready (not the bottleneck)

`DATA-SIDE` (juniper-data, juniper-data-client; corroborated by prior memory + the §14 sweep). Included so the doc records *where* the boundary actually sits.

- **`equities_seq` generator** emits 3-D windows. Per split (train/test/full): `X (W, L, F)` with default `L = 64` lookback and `F = 10` features (`generators/equities_seq/...`, lookback default in `params.py:30`, 10 features in `equities/defaults.py:50-61`), `y (W, 2)` one-hot direction, `y_reg (W, 1)` next-day close. All float32.
- **The 3-D / Δt contract adds keys** beyond the classic six: per-step `dt (W, L)` (elapsed calendar days, `dt[:,0]==0`), `target_dt (W,)` (irregular horizon to the predicted day), `date (W, L)`, `window_end_date (W,)`, `ticker_code (W,)`, `observed_mask (W, L)`, plus singleton `ticker_vocab`. Canonical spec: `JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md` §6.1.
- **juniper-data-client already dispatches on rank.** `validate_npz_contract` branches `X.ndim == 2` (legacy tabular, untouched) vs `X.ndim == 3` (sequence: validates `dt ≥ 0`, `dt[:,0]==0`, mask consistency) — `contract.py:41-126` (dispatch `:63-73`, `dt` checks `:91-98`); NPZ key constants in `constants.py:219-243`.

**Takeaway:** the producer and the transport client speak 3-D. The contract was shipped by the WS-1 data foundation (juniper-data #169/#170/#171 + juniper-data-client #87). cascor is the one consumer that cannot yet read it.

---

## 4. The cascor gate — three tiers

All citations in this section are `VERIFIED-CODE` unless tagged `SWEEP`.

### 4.1 Tier 1 — hard rejection gates (mechanically easy, fail loudly)

- **`SharedTrainingMemory.__init__` — `cascade_correlation.py:272-273`** — `if ct.ndim > 2: raise ValueError("SharedTrainingMemory only supports tensors up to 2 dimensions, …")`. The memory's cited gate.
- **The binary descriptor is the *real* cap — `:301-317`.** Each tensor descriptor is packed `struct.pack_into("<QQBBII6x", …)` storing only `shape_0` (`:301`) and `shape_1` (`:302`); the in-code `NOTE` at `:304-306` states the format "only stores shape_0 and shape_1, limiting support to tensors with ndim <= 2." Header/descriptor sizes are fixed at `HEADER_SIZE = 64`, `DESCRIPTOR_SIZE = 32` (`:251-252`).
- **`reconstruct_tensors` has no 3-D branch — `:359-372`.** Unpacks the same `<QQBBII6x`, reconstructs `shape` only for `ndim == 1` (`:365-366`) and `ndim == 2` (`:367-368`); the `else` (`:369-370`) is a broken fallback (`(shape_0,) if shape_0 > 0 else ()`) — currently unreachable because `__init__` rejects ndim>2 before serialization.
- **`InlineDataset` Pydantic schema — `api/models/training.py:26-29`** `SWEEP` — `train_x: List[List[float]]` (2-D nested lists); a 3-D inline payload fails schema validation.
- **Spiral data-provider — `spiral_problem/data_provider.py:200-204`** `SWEEP` — `if arr.ndim != 2: raise SpiralDataProviderError(…)` and `shape[1] != 2` (spiral-specific, also pins exactly 2 features).

### 4.2 Tier 2 — silent mis-indexing (`shape[1] ≡ features`, ~10 sites)

These do not reject 3-D; they read the wrong axis. The universal wall is the shared validator, which *every* forward / fit / residual call routes through:

- **`_validate_tensor_shapes` — `:1632-1640`** — `if len(x.shape) != 2: raise ValidationError("Input tensor must be 2D (batch_size, features)…")`; then `x.shape[1] != expected_input_features` (`:1634`), `len(y.shape) != 2` (`:1637`), batch match (`:1639`). This is both a rejection (the `len != 2`) and the gateway to the mis-index assumption. Called from `forward` (`:1963`) and `fit` (`:1833`, `:1842`, `:1847`).
- **`fit` output-size checks — `:1836-1837`, `:1848-1849`** — `y_train.shape[1] != self.output_size` (and the `y_val` twin).
- **`train_output_layer` — `:2021`** — `input_size = x.shape[1]`; for a 3-D input this reads `lookback`, not features, then builds `nn.Linear(input_size, self.output_size)` (`:2032`) of the wrong size.
- **`calculate_residual_error` — `:3954`, `:3975`** — `y.shape[1] != self.output_size`; the P2-1d residual mask indexes `residual.shape[1]`.
- **`add_unit` — `:4115`, `:4121`** — `candidate_input.shape[1]` taken as the candidate weight size; mismatch raises a stale-candidate `ValidationError`.
- **Auto-start / reload shape inference — `api/app.py:348-349`, `api/lifecycle/manager.py:2976-2988`** `SWEEP` — `network_config.setdefault("input_size", x_train.shape[1])`; `output_size` from `y_train.shape[1]`.
- **`_pad_dataset_for_network` — `api/lifecycle/manager.py:2822-2840`** `SWEEP` — pads features along `dim=1` only (`active_input_dim = int(x.shape[1])`).
- **Config schemas — `api/models/network.py:25-29`** `SWEEP` — `input_size` / `output_size` are scalar `int` fields; there is no lookback / shape-tuple concept anywhere in the request contract.

### 4.3 Tier 3 — the algorithmic core (the real boundary, not a gate)

This is the load-bearing finding, lead-re-read in full:

- **Output weights are a 2-D matrix — `:738`** — `self.output_weights = torch.randn(self.config.input_size, self.config.output_size, …)`.
- **The forward pass is a 2-D GEMM — `:1979`** — `output = torch.matmul(output_input, self.output_weights) + self.output_bias`, where `output_input` is `(batch, input_size + n_hidden)`. A 3-D `(batch, lookback, features)` input would produce a `(batch, lookback, output)` tensor — meaningless to the residual/correlation/accuracy code that assumes `(batch, output)`.
- **Hidden-unit activation is a per-sample feature sum — `:1939-1946`** — `_compute_hidden_outputs` builds a `(batch_size, input_size + n_hidden)` buffer (`:1941`) and computes each unit as `activation_fn(torch.sum(unit_input * unit["weights"], dim=1) + bias)` (`:1946`). `dim=1` *is* the feature axis; the unit weight is a 1-D feature vector.
- **Candidate-unit math is the same 2-D pattern — `candidate_unit.py:458-479`** — `CandidateUnit.forward` coerces 1-D→2-D via `x = x.unsqueeze(0)` (`:475`) then `output = activation_fn(torch.sum(x * self.weights, dim=1) + self.bias)` (`:479`). There is **no** 3-D handling; a 3-D window would `sum` over the *lookback* axis. The candidate **correlation objective** (`_get_correlations`, trained in `train_detailed` `:528`) correlates this 2-D activation against the 2-D residual.

The whole Cascade-Correlation algorithm — input→hidden buffer, candidate correlation, output GEMM — operates on `(batch, features)` activation matrices. There is no axis in the math for "time."

### 4.4 Consolidated gate inventory

| # | Tier | Site (`file:line`) | Condition / expression | 3-D effect | Provenance |
|---|------|--------------------|------------------------|------------|------------|
| 1 | reject | `cascade_correlation.py:272-273` | `ct.ndim > 2` → `ValueError` | explicit reject (in-process pool) | VERIFIED-CODE |
| 2 | reject | `cascade_correlation.py:301-317` | descriptor `"<QQBBII6x"`, only `shape_0/1` | binary format holds 2 dims | VERIFIED-CODE |
| 3 | reject | `cascade_correlation.py:359-372` | unpack handles ndim 1/2 only | no 3-D reconstruct branch | VERIFIED-CODE |
| 4 | reject | `api/models/training.py:26-29` | `train_x: List[List[float]]` | inline 3-D fails schema | SWEEP |
| 5 | reject | `spiral_problem/data_provider.py:200-204` | `arr.ndim != 2`, `shape[1] != 2` | NPZ 3-D reject (spiral) | SWEEP |
| 6 | mis-index | `cascade_correlation.py:1632-1640` | `len(x.shape) != 2`; `x.shape[1]` | universal wall (reject + mis-index) | VERIFIED-CODE |
| 7 | mis-index | `cascade_correlation.py:1836-1849` | `y.shape[1] != output_size` | wrong target axis | VERIFIED-CODE |
| 8 | mis-index | `cascade_correlation.py:2021` | `input_size = x.shape[1]` | reads lookback as features | VERIFIED-CODE |
| 9 | mis-index | `cascade_correlation.py:3954,3975` | `y.shape[1]`, `residual.shape[1]` | wrong residual axis | VERIFIED-CODE |
| 10 | mis-index | `cascade_correlation.py:4115,4121` | `candidate_input.shape[1]` | wrong candidate weight size | VERIFIED-CODE |
| 11 | mis-index | `api/app.py:348-349` | `setdefault(input_size, x_train.shape[1])` | wrong inferred size | SWEEP |
| 12 | mis-index | `api/lifecycle/manager.py:2822-2840` | pad `dim=1` | pads wrong axis | SWEEP |
| 13 | mis-index | `api/models/network.py:25-29` | scalar `input_size`/`output_size` | no shape-tuple surface | SWEEP |
| 14 | **core** | `cascade_correlation.py:738` | `output_weights = randn(in, out)` | 2-D weight matrix | VERIFIED-CODE |
| 15 | **core** | `cascade_correlation.py:1979` | `matmul(output_input, output_weights)` | 2-D GEMM forward | VERIFIED-CODE |
| 16 | **core** | `cascade_correlation.py:1939-1946` | `sum(unit_input*weights, dim=1)` | hidden sum over features | VERIFIED-CODE |
| 17 | **core** | `candidate_unit.py:475,479` | `unsqueeze(0)`; `sum(x*weights, dim=1)` | candidate sum over features | VERIFIED-CODE |

---

## 5. Two IPC mechanisms — transport-ready ≠ math-ready

cascor trains candidate units on two paths (the "dual-path" tier split, cf. `project_cascor_dualpath_candidate_stall`):

1. **In-process multiprocessing pool** — `SharedTrainingMemory` (`cascade_correlation.py:239`), `reconstruct_tensors` consumed at `:2348` and `:3381` (`_build_candidate_inputs`). **Blocked at the transport layer**: the 2-D descriptor (#2 above).
2. **Distributed worker** (`juniper-cascor-worker`, separate package, pins `juniper-cascor-core>=0.1.0` + `juniper-cascor-protocol>=0.1.0`) — uses a *different* serializer, `SharedBinaryFrame` / `_decode_binary_frame` (`worker.py:671`), which unpacks `struct.unpack_from(f"<{ndim}I", …)` for arbitrary `ndim` up to `BINARY_FRAME_MAX_NDIM = 10` (`worker.py:650`) and has a passing 3-D round-trip test (`tests/test_no_pydantic_at_runtime.py:91-97`). `SWEEP` **Transport is already N-D-capable.**

**But the worker is not end-to-end 3-D-ready.** It delegates the actual candidate training to `CandidateUnit.train_detailed` (`task_executor.py:110-120`) `SWEEP`, and that math is the 2-D `torch.sum(x*weights, dim=1)` from §4.3 (`candidate_unit.py:479`, `VERIFIED-CODE`). Note the two `CandidateUnit` copies — `juniper-cascor/src/candidate_unit/candidate_unit.py` and the cascor-core copy the worker imports — are **byte-identical** (`diff -q` → IDENTICAL this session), so a math change must land in both (or in the single cascor-core source once relocation/publish completes — cf. `project_juniper_package_placement_plan_2026-06-09`).

**Consequence for the build:** the in-process path needs a *transport* change (descriptor, §8) **and** a *math* change; the worker path needs *only* the math change (its transport already copes). Both paths converge on the same Tier-3 core rewrite — which is the recurrent-model work, not plumbing.

---

## 6. What lifting the gate actually buys: two paths

Once Tiers 1–2 are lifted, a 3-D array reaches the 2-D core. There are exactly two ways to make the core consume it:

### Path A — FLATTEN `(batch, lookback, features) → (batch, lookback·features)`

- **Cost:** a single reshape ahead of Tier 2; no core change. By far the cheapest.
- **What it is:** a fixed-window lag-embedding (Takens). This is **precisely the P4 delay-line design** evaluated in `JUNIPER_RECURSE_OQ4_DELAY_LINE_OUTPUT_MODULE_EVAL_2026-06-09.md` — FIR, inherits the star-free ceiling, horizon hard-capped at the window, and it **discards `dt`** (a flattened window has no place for per-step elapsed time unless `dt` is concatenated as extra columns, which only re-encodes it as more static features). The OQ-4 evals ranked P4 *weakest*. `INFERRED` (flatten ≡ P4 lag-embedding).
- **When it is acceptable:** as a finite-memory baseline / smoke-test of the data path, explicitly labeled as lag-embedding — never as the recurrent deliverable.

### Path B — recurrent forward over the lookback axis (P1 / P3-C / LMU)

- **Cost:** model work — a forward that scans `lookback` sequentially (state recurrence), a hidden/candidate math that carries state, and a training loop that is no longer a single static output-GEMM solve. This is where `dt` / `target_dt` are actually consumed (Δt-gated state update — the P3-C/Approach-C win).
- **What it is:** the genuine recurrent extension. P3-C/LMU (the OQ-4 pick) can be built **fixed-order, outside the cascade growth loop**, which sidesteps both the candidate-growability question and the per-unit 2-D math — i.e., a 3-D-native recurrent block can front the existing 2-D cascade head. `INFERRED` (consistent with re-eval §1(B), §9).

**The decision this surfaces is not "lift the cap."** It is *"recurrent ingestion (build Path B, consume `dt`) or lag-embedding (Path A, flatten → P4)?"* — and the dataset audit already answers it (§11).

---

## 7. The discarded Δt channel

cascor's NPZ ingestion (`api/app.py:340-349`, `api/lifecycle/manager.py:2976-2988`) reads only the 2-D contract keys (`X_train`/`y_train`/`X_test`/`y_test` + `X_full`/`y_full`). It does **not** call `juniper-data-client`'s `validate_npz_contract`, and it never reads `dt`, `target_dt`, `observed_mask`, or `ticker_code` (confirmed by exhaustive `src/` grep — zero hits, §14). So even if the shape gates were lifted and the windows flattened (Path A), the *irregular-Δt* signal — the one cross-cutting demand the dataset audit found (forecasting under non-uniform sampling) and the entire rationale for the P3-C/LMU pick — is dropped at the cascor boundary. **Consuming `dt` is therefore part of the gate, not a later refinement**, and it is only meaningful under Path B (a recurrent state update can be Δt-scaled; a static GEMM cannot).

---

## 8. A cheap, non-breaking descriptor extension (independent of the model decision)

For whenever a 3-D tensor must cross the in-process `SharedTrainingMemory` boundary, the descriptor can carry a third dimension **without growing** — `INFERRED` design proposal; the byte arithmetic below is independently `VERIFIED` (`struct.calcsize`, two validators, §14):

- Current: `"<QQBBII6x"` = 8 + 8 + 1 + 1 + 4 + 4 + 6 = **32 B** = `DESCRIPTOR_SIZE`.
- Proposed: `"<QQBBIII2x"` = 8 + 8 + 1 + 1 + 4 + 4 + 4 + 2 = **32 B** — adds `shape_2` (one `I`), keeps 2 reserved bytes, descriptor size unchanged.

This fits `(batch, lookback, features)` **exactly** (3 dims); a 4th dim would require a real format redesign (e.g. variable-length shape encoding). It requires: bumping `VERSION` (`:250`, currently `1`) so old readers reject new blocks, adding an `ndim == 3` branch in `reconstruct_tensors` (`:365-370`), and relaxing the `ndim > 2` guard (`:272-273`) to `ndim > 3`. **This is necessary but not sufficient** — it only moves the 3-D tensor through the pipe; the §4.3 core still cannot train on it. Land it only as part of Path B, not on its own.

---

## 9. Tests that pin the 2-D contract

`SWEEP` (validate in §14). These encode the current contract and bound the change surface:

- `src/tests/unit/test_shared_memory_validation.py:34,42,50,67` — assert `SharedTrainingMemory` raises on 3-D/4-D/5-D and on a 3-D tensor mixed into a 2-D list.
- `src/tests/performance/test_shared_memory.py:46-71,102-122` — 2-D round-trip coverage (incl. a 1-D case) — the serialization regression suite a descriptor change must extend.
- `src/tests/unit/test_parallel_training.py:315-335` — mixed 2-D/1-D round-trip.
- `src/tests/unit/test_data_provider_coverage.py:208,228` — assert the spiral provider rejects non-2-D NPZ arrays.
- `juniper-cascor-worker/tests/test_no_pydantic_at_runtime.py:91-97` + `tests/test_sec18_binary_frame_bounds.py` — already exercise the worker's N-D `SharedBinaryFrame` (the transport that is *not* the blocker).

---

## 10. Scope / effort estimate per path

`INFERRED` — grounded in the gate inventory, not measured.

| Path | Transport | Mis-index gates | Core / math | Δt consumed | Net | Verdict |
|------|-----------|-----------------|-------------|-------------|-----|---------|
| **A — flatten / P4** | none (flatten before pipe) | reshape upstream of Tier 2; leave 2-D core untouched | none | no (or as static cols) | **small** | lag-embedding baseline only; not the deliverable |
| **B — recurrent / P3-C·LMU·P1** | in-proc descriptor (§8) + worker already N-D | redefine "features" axis; thread shape-tuple config | **new recurrent forward + candidate state** (both `CandidateUnit` copies / cascor-core) | yes (Δt-scaled state) | **large** | the genuine pick; the model work the OQ-4 arc has been scoping |

The honest headline: **there is no cheap path to *recurrent* 3-D ingestion.** The cheap path (A) lands on the design the evals already rejected. The right path (B) is a model build whose plumbing prerequisites (§8, §7, Tiers 1–2) are minor relative to the recurrent forward itself.

---

## 11. Recommendation (requirement-first) + decision framing

1. **Do not ship Path A as the answer.** Flatten/P4 is available and cheap, but the [dataset audit](JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md) found *no* dataset needs the ceiling-break, and the one cross-cutting demand is irregular Δt — which Path A cannot represent. Building the cheap thing would spend effort to land on the weakest option. Use Path A only as an explicitly-labeled finite-memory smoke-test of the ingestion plumbing.
2. **Scope Path B as a fixed-order recurrent block fronting the existing 2-D cascade head** (P3-C/LMU via Approach-C, per re-eval §9), with **P1** as the cheap hidden-recurrence increment. This consumes `dt`/`target_dt` (§7) and sidesteps the candidate-growability + 2-D-per-unit math by keeping the recurrent block outside the cascade growth loop.
3. **Sequence the plumbing prerequisites with the model, not before it:** (a) cascor NPZ ingestion to call `validate_npz_contract` and carry `dt`/`target_dt` (§7); (b) a 3-D-aware input contract (shape-tuple config, §4.2 #13); (c) the in-process descriptor extension (§8) *if* the recurrent block trains via the in-process pool; the worker path needs only the math change (§5).
4. **The only standalone, no-regret change** is the descriptor extension (§8) — but even that should land with Path B, since on its own it moves 3-D tensors the core cannot train on.

**One-line decision for Paul:** *recurrent ingestion (Path B — build the P3-C/LMU forward + consume `dt`) vs lag-embedding (Path A — flatten → P4)*. The audit points at B; this doc confirms B has no plumbing shortcut and that A is a trap dressed as a quick win.

---

## 12. Open questions & unverified gaps

- **`SWEEP` citations** (§4 #4,5,11,12,13; §5 worker; §9 tests; §3 data-side line numbers) are agent-reported and validated in §14; treat as provisional until then.
- **Does the live `equities_seq` NPZ route through the spiral `data_provider` (#5) or the generic `app.py`/`manager.py` loader (#11)?** Determines whether the *first* wall for real 3-D equities data is the spiral reject or the universal validator (#6). Not yet traced end-to-end.
- **cascor-core relocation/publish state.** This doc assumes the byte-identical `CandidateUnit` copies stay in sync; the relocation→rename→publish plan (`project_juniper_package_placement_plan_2026-06-09`) may make cascor-core the single source — a math change should target whichever is canonical at build time.
- **Whether a 3-D-native recurrent block truly needs the in-process descriptor change at all** — if Path B trains its recurrent front-end outside the candidate pool (e.g. a standalone Δt-native model, re-eval §9), `SharedTrainingMemory` may never see a 3-D tensor and §8 becomes moot. To be decided by the Path B design.

---

## 13. Cross-references

- `JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md` — the requirement validator (ceiling-break not required; irregular Δt is the demand). The reason Path A is a trap.
- `JUNIPER_RECURSE_OQ4_ARCHITECTURE_REEVALUATION_2026-06-12.md` — the model pick (P3-C/LMU + P1); §9 fixed-order recurrent block.
- `JUNIPER_RECURSE_OQ4_DELAY_LINE_OUTPUT_MODULE_EVAL_2026-06-09.md` — P4 = the flatten/lag-embedding Path A lands on.
- `JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md` — the 3-D / Δt NPZ contract spec (§6.1 canonical keys).
- `JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md` — P1–P6 corpus root.

---

## 14. Validation (multi-agent, anti-hallucination)

Run 2026-06-14 after the draft. Five independent read-only sub-agents, each adversarially re-opening the cited sources for a partition of the doc — instructed to assume each claim is wrong, quote the *live* line, and return CONFIRMED / REFUTED / IMPRECISE(+correction). Partition and outcome:

| Validator | Scope | Items | Result |
|-----------|-------|-------|--------|
| V1 | cascor core (`cascade_correlation.py`) — §4.1/4.2/4.3 + §8 byte arithmetic | 19 + arithmetic | **all CONFIRMED**; line numbers exact |
| V2 | `CandidateUnit` math + worker transport + byte-identical copies | 12 | **all CONFIRMED** |
| V3 | ingestion path, Pydantic schemas, spiral provider, 2-D tests, §7 Δt-discard | 11 | **all CONFIRMED** |
| V4 | data side — `equities_seq` shapes, client contract, constants, Δt spec | 9 | **all CONFIRMED** |
| V5 | meta-review — cross-doc framing, internal consistency, overclaims, mis-tags | 6 strands | **all FAIR / SOUND / SUPPORTED** |

**Load-bearing claims, independently confirmed against live code:**

- The 2-D algorithmic core: forward GEMM (`:1979`), hidden-unit sum-over-`dim=1` (`:1946`), candidate sum-over-`dim=1` (`candidate_unit.py:479`) with **no 3-D branch**. [V1, V2]
- The two `CandidateUnit` copies are **byte-identical** — SHA256 `38acd7f…` for both. [V2]
- Worker is **transport-ready, not math-ready**: `struct.unpack_from(f"<{ndim}I")` + a passing `(2,3,4)` round-trip test prove N-D transport; the worker carries no 2-D assumption of its own (zero grep hits) and delegates training to the 2-D `CandidateUnit`. [V2]
- cascor reads only the 2-D NPZ keys and references **none** of `dt`/`target_dt`/`observed_mask`/`ticker_code`/`validate_npz_contract` (exhaustive `src/` grep, zero hits). [V3]
- `equities_seq` genuinely emits `(W, 64, 10)` float32 windows + `dt (W,L)` with `dt[:,0]==0` + `target_dt (W,)`; the client dispatches on `X.ndim`. [V4]
- Descriptor byte arithmetic: `"<QQBBII6x"` = 32 B and `"<QQBBIII2x"` = 32 B, both via `struct.calcsize`. [V1, V5]
- Cross-doc framing is faithful: flatten ≡ P4/Takens-FIR (P4 doc §3.2 "the only mechanically viable interpretation … `D` columns to the flat fan-in"); audit exception-list-EMPTY + irregular-Δt-the-demand; re-eval P3-C/LMU fixed-order pick — all quoted-verbatim fair. [V5]

**Corrections applied post-validation (all minor, none load-bearing):**

- `contract.py` validator range `41-125` → `41-126`; added the sub-ranges (dispatch `:63-73`, `dt` checks `:91-98`). [V4]
- "cascor reads only `X_train`/`y_train`/`X_test`/`y_test`" → added `X_full`/`y_full` (cascor reads those too; still no Δt keys). [V3]
- §5 worker citations sharpened to `worker.py:671` (unpack) and `:650` (`BINARY_FRAME_MAX_NDIM`). [V2]
- §8 re-tagged: the *proposal* stays `INFERRED`; the *byte arithmetic* is `VERIFIED`. [V5]

**Flagged-but-non-issues (recorded for honesty):**

- V1 marked `:738` "REFUTED" only because the doc's `…` elides `requires_grad=True … * self.random_value_scale`; the substance (a 2-D `(input_size, output_size)` weight matrix) is correct.
- V2 marked the "worker does not depend on `juniper-cascor`" item "REFUTED" — but its evidence *confirms* the doc (worker pins only `juniper-cascor-core` + `juniper-cascor-protocol`).
- V5 noted the §8 arithmetic was conservatively tagged `INFERRED`; addressed by the re-tag above.

**Bottom line:** no hallucinations, no internal contradictions, no overclaims surfaced. Every `file:line` resolves to the asserted live code; the three cross-document framings are faithful paraphrases; the architectural conclusion — *the gate is the feedforward↔recurrent boundary; flatten = the P4 trap; recurrent (P3-C/LMU + Δt) = the real work* — stands as written.
