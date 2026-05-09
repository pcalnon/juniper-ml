# Cascade Correlation Tensor Dimension Mismatch Analysis

**Date**: 2026-03-20
**Project**: juniper-cascor
**Severity**: Critical (training crash)
**Error**: `RuntimeError: The size of tensor a (3) must match the size of tensor b (2) at non-singleton dimension 1`

---

## Table of Contents

1. [Background](#background)
2. [Root Cause Analysis](#root-cause-analysis)
3. [Remediation Proposals](#remediation-proposals)
4. [Proposal Evaluation](#proposal-evaluation)
5. [Recommendations](#recommendations)
6. [Potential Fixes](#potential-fixes)
7. [Advantages and Disadvantages](#advantages-and-disadvantages)
8. [Risks and Guardrails](#risks-and-guardrails)
9. [Underlying Code Problems](#underlying-code-problems)
10. [Underlying Architecture Problems](#underlying-architecture-problems)

---

## Background

### The Cascade Correlation Algorithm

Cascade Correlation (Fahlman & Lebiere, 1990) is a constructive neural network algorithm that **grows** the network by adding hidden units one at a time. A critical invariant of the algorithm is:

> **Each new hidden unit N receives input from ALL original inputs PLUS the outputs of ALL previously added hidden units (0 through N-1).**

This means the **input dimensionality grows by 1 every time a hidden unit is added**:

| Network State  | Input Dimension for Next Candidate           |
|----------------|----------------------------------------------|
| 0 hidden units | `original_input_size` (e.g., 2 for 2-spiral) |
| 1 hidden unit  | `original_input_size + 1` (e.g., 3)          |
| 2 hidden units | `original_input_size + 2` (e.g., 4)          |
| N hidden units | `original_input_size + N`                    |

### The Training Loop

The `grow_network()` method (`cascade_correlation.py:3248`) runs a loop where each epoch:

1. **Calculates residual error** between network output and targets
2. **Trains a pool of candidate units** via `train_candidates()`, each with weights sized to `candidate_input.shape[1]`
3. **Selects the best candidate** by highest correlation with residual error
4. **Adds the best candidate** to the network via `add_unit()`, which rebuilds `candidate_input` from the current hidden units and applies the candidate's weights

### The Error

```bash
cascade_correlation.py:3101, in add_unit
    unit_output = self.activation_fn(torch.sum(candidate_input * new_unit["weights"], dim=1) + new_unit["bias"]).unsqueeze(1)
RuntimeError: The size of tensor a (3) must match the size of tensor b (2) at non-singleton dimension 1
```

The element-wise multiplication `candidate_input * new_unit["weights"]` fails because:

- `candidate_input` has **3 columns** (2 original inputs + 1 hidden unit output)
- `new_unit["weights"]` has **2 elements** (trained when no hidden units existed)

This means a candidate trained when the network had **0 hidden units** is being applied when the network has **1 hidden unit**.

### Call Stack

```bash
main.py:402 → main()
main.py:329 → sp.evaluate(...)
spiral_problem.py:1431 → self.solve_n_spiral_problem(...)
spiral_problem.py:1336 → self.network.fit(self.x, self.y, ...)
cascade_correlation.py:1387 → self.grow_network(candidate=CandidateUnit(...), ...)
cascade_correlation.py:3287 → self._add_best_candidate(training_results.best_candidate, ...)
cascade_correlation.py:3433 → self.add_unit(best_candidate, x_train)
cascade_correlation.py:3101 → CRASH: candidate_input * new_unit["weights"]
```

The error occurs on the **single-candidate path** (line 3287, the `else` branch at line 3284).

---

## Root Cause Analysis

### Primary Root Cause: Persistent Worker Pool Result Queue Contamination

**Confidence: High:**

The PARALLEL-FIX RC-4 optimization (`cascade_correlation.py:2752-2807`) introduced a **persistent worker pool** that keeps workers alive across training rounds to eliminate per-round process creation overhead. However, this introduced a critical regression: **the result queue is never drained between rounds**.

#### The Mechanism

1. **Round N** (epoch 0, 0 hidden units):
   - 16 tasks submitted to `task_queue` (candidates with `input_size=2`)
   - Workers process tasks and put `CandidateTrainingResult` objects into `result_queue`
   - `_collect_training_results()` collects results with a **60-second timeout** (`cascade_correlation.py:1977`)
   - If a slow worker completes after the timeout, its result **remains in the queue**

2. **Round N+1** (epoch 1, 1 hidden unit):
   - 16 new tasks submitted (candidates with `input_size=3`)
   - Workers process new tasks
   - `_collect_training_results()` starts collecting — but the **stale Round N result is first in the FIFO queue**
   - The stale result (candidate with `weights.shape=(2,)`) is collected as a valid Round N+1 result
   - If it has the highest correlation, it becomes `training_results.best_candidate`
   - `add_unit()` rebuilds `candidate_input` with `shape=(batch, 3)` and attempts `(batch, 3) * (2,)` → **crash**

#### Evidence

1. **No queue draining**: Grep for `drain|flush|clear.*queue` finds zero results — the result queue is never cleared between rounds
2. **No round identification**: `CandidateTrainingResult` (`candidate_unit.py:79-95`) has no `round_id` or `epoch` field — stale results are indistinguishable from current results
3. **Early exit on stale count**: The wait loop at `cascade_correlation.py:1889` checks `result_queue.qsize() >= len(tasks)`, which includes stale items, causing premature exit
4. **No weight-shape validation**: `_validate_training_result()` (`cascade_correlation.py:1933-1970`) checks types, NaN/Inf, and magnitude, but **does not verify that candidate weight dimensions match the current network state**
5. **Persistent queues confirmed**: `_ensure_worker_pool()` at line 2772-2774 returns existing queues when the pool is valid — same `result_queue` object across rounds
6. **Remote path has round isolation but local path does not**: The remote dispatch path (`cascade_correlation.py:753`) uses `round_id = str(uuid.uuid4())`, but the local parallel path has no equivalent

#### Trigger Conditions

This bug triggers when:

- A worker in round N is slower than the collection timeout (60s default)
- The late result arrives before round N+1's collection starts
- The stale candidate happens to have a high enough correlation to be selected as "best"
- The network has grown (added hidden units) between when the stale candidate was trained and when it's applied

### Secondary Root Cause: `add_units_as_layer` Sequential Dimension Mismatch

**Confidence: High (confirmed bug, but not triggered in this specific error trace):**

The `add_units_as_layer()` method (`cascade_correlation.py:3173-3192`) has a **definitive dimension mismatch bug** when `candidates_per_layer > 1`.

#### The Mechanism

```python
def add_units_as_layer(self, candidates: list, x: torch.Tensor) -> None:
    for candidate in candidates:
        if candidate.candidate and hasattr(candidate.candidate, "weights"):
            self.add_unit(candidate.candidate, x)  # Each call grows self.hidden_units!
```

All candidates in the list were trained with the **same** `candidate_input` (same number of hidden units). But `add_unit()` modifies `self.hidden_units` at line 3091. After the first candidate is added:

| Candidate     | Trained With     | Applied With                       | Result       |
|---------------|------------------|------------------------------------|--------------|
| candidates[0] | `input_size = N` | `candidate_input.shape[1] = N`     | WORKS        |
| candidates[1] | `input_size = N` | `candidate_input.shape[1] = N + 1` | **MISMATCH** |
| candidates[2] | `input_size = N` | `candidate_input.shape[1] = N + 2` | **MISMATCH** |

#### Current Status

This bug does **not** trigger in the reported error because:

- The error trace shows line 3287 (single-candidate path, the `else` branch)
- `candidates_per_layer` defaults to 1 (`getattr(self, "candidates_per_layer", 1)` at line 3269)

However, this is a **latent critical bug** that will crash whenever multi-candidate layer addition is used.

### Contributing Factor: Dead Code Creates Confusion

The `candidate` parameter passed from `fit()` to `grow_network()` at line 1387-1400 creates a `CandidateUnit` with `_CandidateUnit__input_size=self.input_size` (the **static original** input size). However, **this parameter is never used** inside `grow_network()`. The actual candidates come from `train_candidates()`, which correctly computes `input_size` dynamically from `_prepare_candidate_input()`.

The `candidate` parameter at `grow_network()` line 3205 is accepted but never referenced in the method body. This dead code is misleading during debugging because it appears to pass a static input_size into the training loop.

---

## Remediation Proposals

### Proposal 1: Result Queue Drain Between Rounds

**Description**: Drain (empty) the persistent result queue at the start of each training round, before submitting new tasks.

**Implementation**:

```python
# In _execute_parallel_training, before putting new tasks:
while not result_queue.empty():
    try:
        stale = result_queue.get_nowait()
        self.logger.warning(f"Drained stale result from previous round: candidate_id={stale.candidate_id}")
    except Empty:
        break
```

### Proposal 2: Round-Tagged Results

**Description**: Add a `round_id` (UUID) to each training round. Tag tasks with the round_id, include it in results, and filter out results that don't match the current round.

**Implementation**:

- Add `round_id: Optional[str] = None` field to `CandidateTrainingResult`
- Generate `round_id = str(uuid.uuid4())` at the start of each `_execute_parallel_training` call
- Include `round_id` in task data
- Workers propagate `round_id` to results
- `_collect_training_results` filters results by `round_id`

### Proposal 3: Weight Shape Validation in `add_unit`

**Description**: Add a defensive shape check in `add_unit()` before the element-wise multiplication.

**Implementation**:

```python
# In add_unit, before line 3101:
expected_size = candidate_input.shape[1]
actual_size = new_unit["weights"].shape[0]
if expected_size != actual_size:
    raise ValidationError(
        f"Weight dimension mismatch: candidate_input has {expected_size} features "
        f"but candidate weights have {actual_size} elements. "
        f"Network has {len(self.hidden_units)} hidden units."
    )
```

### Proposal 4: Fresh Queues Per Round

**Description**: Create new task and result queues for each training round while keeping workers persistent.

**Implementation**: Use a round-specific queue pair. Workers receive a reference to the current queues via a shared state mechanism, or queues are passed per-task.

### Proposal 5: Fix `add_units_as_layer` Dimension Tracking

**Description**: When adding multiple candidates as a layer, compute all outputs with the **pre-addition** hidden units, then add all units at once.

**Implementation**:

```python
def add_units_as_layer(self, candidates: list, x: torch.Tensor) -> None:
    # Compute candidate_input ONCE with current hidden units
    hidden_outputs = []
    for unit in self.hidden_units:
        unit_input = torch.cat([x] + hidden_outputs, dim=1) if hidden_outputs else x
        unit_output = unit["activation_fn"](
            torch.sum(unit_input * unit["weights"], dim=1) + unit["bias"]
        ).unsqueeze(1)
        hidden_outputs.append(unit_output)
    candidate_input = torch.cat([x] + hidden_outputs, dim=1) if hidden_outputs else x

    # Add all candidates using the pre-computed input
    for candidate_result in candidates:
        candidate = candidate_result.candidate
        if candidate and hasattr(candidate, "weights"):
            new_unit = {
                "weights": candidate.weights.clone().detach(),
                "bias": candidate.bias.clone().detach(),
                "activation_fn": self.activation_fn,
                "correlation": candidate.correlation,
            }
            self.hidden_units.append(new_unit)

    # Update output weights once for all new units
    self._update_output_weights_for_new_units(x, len(candidates))
```

### Proposal 6: Remove Dead Code and Unused Parameters

**Description**: Remove the unused `candidate` parameter from `grow_network()` and the dead `CandidateUnit` instantiation in `fit()`.

---

## Proposal Evaluation

| Proposal                 | Addresses Primary RC | Addresses Secondary RC | Complexity | Risk     | Standalone Fix?     |
|--------------------------|----------------------|------------------------|------------|----------|---------------------|
| **P1: Queue Drain**      | Yes                  | No                     | Low        | Low      | Yes (for primary)   |
| **P2: Round Tags**       | Yes                  | No                     | Medium     | Low      | Yes (for primary)   |
| **P3: Shape Validation** | Detects only         | Detects only           | Low        | Very Low | No (defensive only) |
| **P4: Fresh Queues**     | Yes                  | No                     | High       | Medium   | Yes (for primary)   |
| **P5: Layer Fix**        | No                   | Yes                    | Medium     | Low      | Yes (for secondary) |
| **P6: Dead Code**        | No                   | No                     | Low        | Very Low | No (quality only)   |

### Analysis

**P1 (Queue Drain)** is the simplest fix for the primary root cause. It has minimal risk but introduces a subtle race: a result could arrive between the drain and the first new result collection. In practice, this window is negligible because workers process new tasks from the queue, not old ones.

**P2 (Round Tags)** is the most architecturally correct solution. It completely eliminates cross-round contamination regardless of timing. The cost is a schema change to `CandidateTrainingResult` and propagation through the worker pipeline.

**P3 (Shape Validation)** is a critical defensive measure regardless of which root cause fix is chosen. It converts a cryptic `RuntimeError` into a meaningful `ValidationError` with diagnostic information. This should be implemented regardless.

**P4 (Fresh Queues)** is over-engineered for this problem. Creating new queues each round partially defeats the purpose of the persistent pool (workers would need a mechanism to discover new queues).

**P5 (Layer Fix)** is independent of the primary root cause and must be fixed separately if multi-candidate layer addition is a supported feature.

**P6 (Dead Code)** is low-risk cleanup that improves maintainability.

---

## Recommendations

### Immediate (Fix the Crash)

1. **Implement P1 (Queue Drain)** — Drain the persistent result queue at the start of each `_execute_parallel_training` call. This is the minimum viable fix.
2. **Implement P3 (Shape Validation)** — Add weight shape validation in `add_unit()` as a defensive guardrail. This ensures any future dimension mismatches produce clear diagnostics.

### Short-Term (Robust Fix)

3. **Implement P2 (Round Tags)** — Add `round_id` to the training result pipeline. This replaces P1 with an architecturally sound solution that doesn't rely on timing assumptions.
4. **Implement P5 (Layer Fix)** — Fix `add_units_as_layer()` to compute all outputs before mutating the hidden units list.

### Housekeeping

5. **Implement P6 (Dead Code)** — Remove the unused `candidate` parameter from `grow_network()` and the static `CandidateUnit` instantiation in `fit()`.

---

## Potential Fixes

### Fix 1: Minimal — Queue Drain + Shape Guard (Recommended Immediate Fix)

**Files Modified**:

- `cascade_correlation.py`: `_execute_parallel_training()`, `add_unit()`

**Changes**:

In `_execute_parallel_training()`, before line 1856 (task submission):

```python
# Drain any stale results from previous rounds (RC-4 persistent pool safety)
drained = 0
while True:
    try:
        stale_result = result_queue.get_nowait()
        drained += 1
        self.logger.warning(
            f"Drained stale result from previous round: "
            f"candidate_id={getattr(stale_result, 'candidate_id', '?')}"
        )
    except Empty:
        break
if drained:
    self.logger.warning(f"Drained {drained} stale result(s) from persistent result queue")
```

In `add_unit()`, before line 3101:

```python
expected_weight_size = candidate_input.shape[1]
actual_weight_size = new_unit["weights"].shape[0]
if expected_weight_size != actual_weight_size:
    raise ValidationError(
        f"Candidate weight dimension mismatch in add_unit: "
        f"candidate_input has {expected_weight_size} features "
        f"(original_input={x.shape[1]}, hidden_units={len(self.hidden_units)}), "
        f"but candidate weights have {actual_weight_size} elements. "
        f"This indicates a stale candidate from a previous training round."
    )
```

### Fix 2: Comprehensive — Round-Tagged Results

**Files Modified**:

- `candidate_unit.py`: `CandidateTrainingResult`
- `cascade_correlation.py`: `_generate_candidate_tasks()`, `_build_candidate_inputs()`, `train_candidate_worker()`, `_execute_parallel_training()`, `_collect_training_results()`

**Changes**:

- Add `round_id: Optional[str] = None` to `CandidateTrainingResult`
- Generate `round_id` in `_execute_parallel_training()`
- Include `round_id` in task tuple
- Workers propagate `round_id` to results
- `_collect_training_results()` filters by `round_id`, discarding mismatched results

### Fix 3: `add_units_as_layer` Dimension Safety

**Files Modified**:

- `cascade_correlation.py`: `add_units_as_layer()`

**Changes**:

- Pre-compute `candidate_input` from current hidden units before the loop
- Add all units using the pre-computed input
- Update output weights once after all units are added
- Add shape assertions for each candidate

---

## Advantages and Disadvantages

### Fix 1 (Queue Drain + Shape Guard)

| Advantages                                      | Disadvantages                                                |
|-------------------------------------------------|--------------------------------------------------------------|
| Minimal code change (< 20 lines)                | Small theoretical race window during drain                   |
| Low risk of regression                          | Does not address root architecture issue                     |
| Shape guard provides permanent diagnostic value | Drain is a workaround, not a structural fix                  |
| Can be deployed immediately                     | Stale results are discarded silently (loss of training work) |
| Does not require schema changes                 |                                                              |

### Fix 2 (Round Tags)

| Advantages                                                        | Disadvantages                                       |
|-------------------------------------------------------------------|-----------------------------------------------------|
| Architecturally correct — eliminates contamination by design      | Requires schema change to `CandidateTrainingResult` |
| No race conditions                                                | Requires propagation through worker pipeline        |
| Stale results can be logged with full context                     | More lines of code to review and test               |
| Aligns local path with remote path (which already has `round_id`) | Slightly increases per-result overhead (UUID field) |
| Future-proof against other queue contamination scenarios          |                                                     |

### Fix 3 (Layer Fix)

| Advantages                                            | Disadvantages                                   |
|-------------------------------------------------------|-------------------------------------------------|
| Fixes a definitive bug in multi-candidate mode        | Only matters when `candidates_per_layer > 1`    |
| Architecturally correct — compute-then-mutate pattern | Requires restructuring `add_units_as_layer`     |
| Enables N-best candidate selection (research feature) | Need to add/refactor output weight update logic |

---

## Risks and Guardrails

### Risk: Queue Drain Discards Valid Late Results

**Severity**: Low
**Mitigation**: The drain only removes results at the START of a new round. By this time, the previous round has already selected its best candidate and added it to the network. Late results from the previous round serve no purpose and are correctly discarded.

**Guardrail**: Log every drained result at WARNING level with `candidate_id` and `correlation`, enabling monitoring for systemic slow-worker issues.

### Risk: Round Tag Propagation Breaks Worker Compatibility

**Severity**: Low
**Mitigation**: Add `round_id` as an optional field with default `None` in `CandidateTrainingResult`. Workers that don't propagate it still produce valid results. The filter treats `None` round_id as "unknown round" and accepts it with a warning.

**Guardrail**: Regression tests should verify that results without `round_id` are still accepted (backward compatibility).

### Risk: Shape Validation Catches Issues Too Late

**Severity**: Low
**Mitigation**: The shape check in `add_unit()` is a last line of defense. It converts a cryptic `RuntimeError` into a `ValidationError` with diagnostic context. The actual fix (queue drain or round tags) prevents the mismatch from occurring in the first place.

**Guardrail**: The `ValidationError` message should include enough detail to diagnose the source: candidate weight size, expected size, number of hidden units, and a hint about stale candidates.

### Risk: `add_units_as_layer` Refactor Breaks Existing Behavior

**Severity**: Medium
**Mitigation**: The current `add_units_as_layer` only works correctly when adding 1 candidate (in which case it's equivalent to `add_unit`). Any multi-candidate usage already crashes. The refactor fixes broken behavior, not working behavior.

**Guardrail**: Add explicit tests for multi-candidate layer addition with known dimensions.

### Risk: Persistent Worker Pool May Have Other Latent Issues

**Severity**: Medium
**Mitigation**: The RC-4 optimization was designed for performance but didn't account for cross-round state isolation. Beyond the result queue, verify that:

- The task queue is also properly drained (or that workers don't cache task state)
- Workers don't accumulate memory across rounds
- Worker failures are properly detected and recovered

**Guardrail**: Add a round-start assertion that both queues are empty. Add periodic worker health monitoring.

---

## Underlying Code Problems

### 1. No Round Isolation in Persistent Worker Pool

**Location**: `cascade_correlation.py:1838-1914` (`_execute_parallel_training`)
**Impact**: Critical

The persistent pool (RC-4) reuses queues across rounds without any round boundary mechanism. The local parallel path lacks the `round_id` concept that the remote worker path already uses (`cascade_correlation.py:753`).

### 2. Missing Dimension Invariant Checks

**Location**: `cascade_correlation.py:3101` (`add_unit`)
**Impact**: Critical

The code performs `candidate_input * new_unit["weights"]` without verifying that shapes are compatible. This is a violation of the PyTorch best practice of asserting tensor shapes at API boundaries.

### 3. Dead Code — Unused `candidate` Parameter

**Location**: `cascade_correlation.py:1387-1400` (`fit` → `grow_network`)
**Impact**: Low (confusion, not functional)

The `CandidateUnit` created at line 1388 with `_CandidateUnit__input_size=self.input_size` is passed to `grow_network()` but never used. The `candidate` parameter at `grow_network` line 3205 is accepted but unreferenced in the method body. The actual candidates are created dynamically in `train_candidates()`.

### 4. `_validate_training_result` Missing Shape Check

**Location**: `cascade_correlation.py:1933-1970`
**Impact**: High

The validation function checks type, bounds, NaN/Inf, and magnitude, but does not validate that the candidate's weight dimensions are consistent with the current network state. A structurally invalid candidate passes validation and causes a crash downstream.

### 5. `_collect_training_results` Has No Deduplication

**Location**: `cascade_correlation.py:1972-2015`
**Impact**: Medium

Results are collected purely by count (`num_tasks`). If stale results occupy slots, legitimate current-round results may be left in the queue, accumulating across rounds.

### 6. `qsize()` Used for Flow Control

**Location**: `cascade_correlation.py:1889`
**Impact**: Medium

The `result_queue.qsize() >= len(tasks)` check triggers early exit based on total queue depth, which may include stale items. The `qsize()` documentation explicitly warns it is unreliable for flow control in multiprocessing contexts.

---

## Underlying Architecture Problems

### 1. State Coupling Between Training and Insertion

The cascade correlation algorithm inherently couples the candidate training context (input dimensions during training) with the insertion context (input dimensions when adding to network). The code assumes these are always identical, but the persistent worker pool breaks this assumption by allowing temporal displacement of results.

**Recommendation**: Make the coupling explicit by either:

- Storing the expected `input_size` alongside each trained candidate and verifying at insertion time
- Using an immutable snapshot of network state for each training round

### 2. Mutable Network State During Batch Operations

`add_units_as_layer()` mutates `self.hidden_units` inside a loop while other iterations depend on the pre-mutation state. This is a classic iterator-invalidation pattern.

**Recommendation**: Adopt a compute-then-mutate pattern: compute all outputs first, then append all units. This pattern is already used in `_prepare_candidate_input()` (which correctly builds outputs incrementally) but is missing from `add_units_as_layer()`.

### 3. Asymmetric Round Isolation (Local vs. Remote)

The remote worker dispatch path (`_dispatch_to_remote_workers` at line 753) uses `round_id` for isolation, but the local parallel path (`_execute_parallel_training`) has no equivalent. This creates an architectural inconsistency where the same training logic behaves differently depending on whether workers are local or remote.

**Recommendation**: Unify round isolation across both paths. The `round_id` pattern from the remote path should be adopted by the local path.

### 4. Persistent Pool as Performance-Safety Tradeoff

The RC-4 persistent pool optimization trades process-creation overhead for cross-round state leakage risk. The original per-round worker creation (commented out at lines 1862-1866) was naturally safe because fresh queues were created each round. The persistent pool removed this safety boundary without replacing it.

**Recommendation**: When converting ephemeral resources to persistent ones for performance, always audit what isolation guarantees the ephemeral pattern provided and explicitly replicate them.

### 5. No Defensive Shape Assertions in Hot Path

The cascade correlation hot path (`forward()`, `add_unit()`, `_prepare_candidate_input()`) performs tensor operations without shape assertions. While these checks add minimal overhead, they convert cryptic `RuntimeError` messages into domain-specific diagnostics that accelerate debugging.

**Recommendation**: Add `assert` or explicit checks at key tensor operation boundaries, especially where tensors from different code paths (training vs. insertion) are combined.

---

## Key File References

| File                     | Lines     | Relevance                                                         |
|--------------------------|-----------|-------------------------------------------------------------------|
| `cascade_correlation.py` | 3101      | **Crash site** — element-wise multiply with mismatched shapes     |
| `cascade_correlation.py` | 3045-3139 | `add_unit()` — unit insertion method                              |
| `cascade_correlation.py` | 3198-3337 | `grow_network()` — main training loop                             |
| `cascade_correlation.py` | 3417-3445 | `_add_best_candidate()` — single candidate insertion              |
| `cascade_correlation.py` | 1566-1615 | `train_candidates()` — candidate pool training                    |
| `cascade_correlation.py` | 1619-1636 | `_prepare_candidate_input()` — input dimension construction       |
| `cascade_correlation.py` | 1638-1682 | `_generate_candidate_tasks()` — dynamic input_size extraction     |
| `cascade_correlation.py` | 1798-1914 | `_execute_parallel_training()` — persistent pool usage            |
| `cascade_correlation.py` | 1972-2015 | `_collect_training_results()` — result collection                 |
| `cascade_correlation.py` | 2752-2807 | `_ensure_worker_pool()` — persistent pool management              |
| `cascade_correlation.py` | 2855-2935 | `_worker_loop()` — worker process                                 |
| `cascade_correlation.py` | 3173-3192 | `add_units_as_layer()` — multi-candidate addition (secondary bug) |
| `cascade_correlation.py` | 1387-1400 | `fit()` → `grow_network()` — unused candidate parameter           |
| `cascade_correlation.py` | 1933-1970 | `_validate_training_result()` — missing shape check               |
| `candidate_unit.py`      | 79-95     | `CandidateTrainingResult` — no round_id field                     |
| `candidate_unit.py`      | 336       | Weight initialization — `torch.randn(self.input_size)`            |

---

## Appendix: Dimension Trace for 2-Spiral Problem

The 2-spiral problem uses `input_size=2` (x, y coordinates).

### Normal Flow (No Bug)

```bash
Epoch 0: Network has 0 hidden units
  _prepare_candidate_input(x): hidden_outputs=[], candidate_input=x → shape (batch, 2)
  _generate_candidate_tasks: input_size = 2
  Candidate trained: weights.shape = (2,)
  add_unit:
    hidden_outputs loop: 0 iterations
    candidate_input = x → shape (batch, 2)
    candidate_input * weights = (batch, 2) * (2,) → OK
    hidden_units: [unit_0]

Epoch 1: Network has 1 hidden unit
  _prepare_candidate_input(x): hidden_outputs=[unit_0_output], candidate_input → shape (batch, 3)
  _generate_candidate_tasks: input_size = 3
  Candidate trained: weights.shape = (3,)
  add_unit:
    hidden_outputs loop: 1 iteration → hidden_outputs=[unit_0_output]
    candidate_input → shape (batch, 3)
    candidate_input * weights = (batch, 3) * (3,) → OK
    hidden_units: [unit_0, unit_1]
```

### Bug Trigger: Stale Result from Epoch 0 Appears in Epoch 1

```bash
Epoch 0: Network has 0 hidden units
  Candidate trained: weights.shape = (2,)
  One worker is slow — its result misses the collection deadline
  Best candidate from 15/16 results added → hidden_units: [unit_0]
  Slow worker's result (weights.shape = (2,)) arrives AFTER collection ends
  Result stays in persistent result_queue

Epoch 1: Network has 1 hidden unit
  16 new tasks submitted (input_size=3)
  _collect_training_results starts collecting from result_queue
  FIRST result collected: STALE epoch 0 result (weights.shape = (2,), correlation=0.85)
  Next 15 results: epoch 1 results (weights.shape = (3,), correlations vary)
  Stale result happens to have highest correlation → selected as best_candidate
  add_unit:
    candidate_input → shape (batch, 3)
    candidate_input * weights = (batch, 3) * (2,) → CRASH
    RuntimeError: size of tensor a (3) must match size of tensor b (2)
```

---
