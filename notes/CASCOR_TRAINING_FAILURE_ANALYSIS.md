# Juniper CasCor Training Failure Analysis

**Date**: 2026-04-02
**Status**: Investigation Complete — Remediation Pending
**Severity**: Critical (P0) — Training runs fail shortly after first epoch
**Affected Component**: `juniper-cascor` — Cascade Correlation training pipeline

---

## 1. Executive Summary

Investigation of critical regressions in `juniper-cascor` has identified five
interrelated issues that combine to cause training crashes shortly after the
first epoch begins. The root causes stem from the OPT-5 SharedMemory
optimization and the RC-4/RC-5 persistent worker pool implementation:

| # | Issue | Origin | Severity |
|---|-------|--------|----------|
| 1 | SharedMemory resource leaks (semaphores + SHM blocks) | OPT-5 | P0 |
| 2 | Persistent worker pool queue contamination | RC-4/RC-5 | P1 |
| 3 | SharedMemory race condition — premature `unlink()` | OPT-5 | P0 |
| 4 | HDF5 serialization failures (save/load) | Pre-existing | P1 |
| 5 | Training crash after first epoch (composite failure) | Issues 1–3 | P0 |

The most critical finding is a **race condition** in shared memory lifecycle
management: the `finally` block in `_execute_parallel_training()` can call
`close_and_unlink()` on shared memory blocks while persistent pool workers are
still reading from them. This causes workers to crash on unmapped memory access,
producing incomplete or corrupt result sets that then trigger dimension
validation failures in `add_unit()`.

---

## 2. Issue 1: SharedMemory Resource Leaks (OPT-5)

### Evidence

Resource tracker warnings at shutdown:

```
ResourceTracker: 9 leaked semaphore objects to clean up at shutdown
ResourceTracker: 1 leaked shared_memory objects to clean up at shutdown:
  {'/juniper_train_7d25fbcc'}
```

### Root Cause

`SharedTrainingMemory` blocks are created in `_generate_candidate_tasks()`
(line 1826–1831) and appended to `self._active_shm_blocks`. The cleanup path
in the `finally` block of `_execute_parallel_training()` (line 2129–2134)
calls `close_and_unlink()` on each block. However, cleanup fails silently in
several scenarios:

1. **Exception before cleanup**: If an exception occurs between block creation
   and the `finally` block entry, blocks are orphaned.
2. **Partial iteration**: If `_generate_candidate_tasks()` is a generator and
   only partially consumed, blocks created for unconsumed tasks are never
   tracked in `_active_shm_blocks`.
3. **Emergency handler gap**: The `atexit` handler `_cleanup_shared_memory()`
   (line 3134–3142) serves as a fallback, but it only cleans blocks still
   referenced by `self._active_shm_blocks` — any blocks lost due to (1) or
   (2) are permanently leaked until process exit, at which point the OS
   resource tracker emits the warnings above.

### Impact

- **9 leaked semaphores** per training run — eventual exhaustion of system
  semaphore limits (`/proc/sys/kernel/sem`), causing `OSError` on subsequent
  `multiprocessing.Semaphore()` calls.
- **Leaked SHM blocks** consume physical memory until the process exits and
  the resource tracker force-cleans them.
- On long-running or restarted training sessions, leaked resources accumulate
  across runs if the parent process persists.

### Affected Code

| File | Lines | Symbol |
|------|-------|--------|
| `cascade_correlation.py` | 1826–1831 | `_generate_candidate_tasks()` — SHM block creation |
| `cascade_correlation.py` | 2129–2134 | `_execute_parallel_training()` — `finally` cleanup |
| `cascade_correlation.py` | 3134–3142 | `_cleanup_shared_memory()` — atexit handler |

---

## 3. Issue 2: Persistent Worker Pool Queue Contamination (RC-4/RC-5)

### Mechanism

The RC-5 fix introduces `round_id` tagging to prevent stale results from
previous training rounds from contaminating the current round's result set.
The implementation:

1. Tasks are tagged with `round_id` as a 4th tuple element before dispatch:
   ```python
   # line 2070
   tagged_task = (task[0], task[1], task[2], round_id)
   ```

2. Results are pre-drained from the queue before each round to discard
   stragglers from previous rounds.

3. Result collection filters by `round_id` to ensure only current-round
   results are accepted.

### Current Guards

- **Pre-drain**: Before dispatching new tasks, the result queue is drained of
  any pending items from prior rounds.
- **Round-ID filtering**: Results with mismatched `round_id` are discarded
  during collection.

### Remaining Gaps

The task unpacking path is fragile:

- `_process_worker_task()` (line 3235) checks `if shared_training_inputs is
  not None and len(task) == 2` — a 4-element tagged task does **not** match
  `len(task) == 2`, so it falls through to `full_task = task`.
- `train_candidate_worker()` then calls `_build_candidate_inputs()` which
  unpacks via `len(task_data_input) >= 4` (line 2824), correctly extracting
  the `round_id`.

While the current unpacking happens to work, the dual-path branching on tuple
length is **implicit and undocumented**. Any future change to task tuple
structure will silently break one of the two paths. This is a maintainability
risk rather than an active bug.

### Impact

- **Active risk**: Low — the current implementation correctly handles round_id
  tagging and filtering.
- **Maintenance risk**: High — the implicit tuple-length branching is a latent
  defect vector.

### Affected Code

| File | Lines | Symbol |
|------|-------|--------|
| `cascade_correlation.py` | 2070 | Task tagging with `round_id` |
| `cascade_correlation.py` | 3235 | `_process_worker_task()` — tuple length branching |
| `cascade_correlation.py` | 2824 | `_build_candidate_inputs()` — task unpacking |

---

## 4. Issue 3: SharedMemory Race Condition — Premature Unlink

### Root Cause

This is the **most critical defect** identified.

The persistent worker pool (RC-4) keeps workers alive across training rounds.
The SharedMemory lifecycle (OPT-5) assumes workers are finished when the
`finally` block in `_execute_parallel_training()` runs. This assumption is
violated:

```
Timeline:
  Main process                          Worker processes (persistent pool)
  ─────────────                         ──────────────────────────────────
  1. Create SHM blocks
  2. Dispatch tasks to workers
  3. Collect results (with timeout)
                                        3a. Worker N starts reading SHM
  4. Enter finally block
  5. close_and_unlink() on SHM blocks
                                        3b. Worker N reads from UNMAPPED memory
                                            → SIGBUS / corrupt data
```

**The race window**: Between step 3 (result collection completing, possibly via
timeout) and step 3b (a slow worker still reading shared memory), the main
process unlinks the shared memory segment. The worker's
`SharedTrainingMemory.reconstruct_tensors()` call then accesses unmapped
memory.

### Consequences

1. **Worker crash**: `SIGBUS` or `SIGSEGV` in the worker process when
   accessing the unlinked shared memory region.
2. **Silent data corruption**: If the memory region is partially reclaimed,
   the worker may read garbage data and produce a numerically wrong (but
   structurally valid) result.
3. **Incomplete result set**: Crashed workers don't return results. The main
   process may substitute dummy/default results with incorrect weight
   dimensions.
4. **Cascade into add_unit() failure**: The RC-5 weight dimension validation
   at line 3398 catches the mismatch:
   ```python
   if expected_weight_size != actual_weight_size:
       raise ValidationError(
           "Candidate weight dimension mismatch in add_unit..."
       )
   ```
   This is the proximate cause of the "fails shortly after beginning the first
   epoch" symptom.

### Affected Code

| File | Lines | Symbol |
|------|-------|--------|
| `cascade_correlation.py` | 2129–2134 | `_execute_parallel_training()` — premature cleanup |
| `cascade_correlation.py` | 1826–1831 | `_generate_candidate_tasks()` — SHM creation |
| `cascade_correlation.py` | 3398 | `add_unit()` — dimension validation (RC-5) |

---

## 5. Issue 4: HDF5 Serialization Failures

### Error 1: Buffer API Error During Save

```
TypeError: object supporting the buffer API required
```

This occurs during HDF5 snapshot serialization when attempting to write a
Python object that is not a numpy array or bytes-like object to an HDF5
dataset. Likely cause: a field that was previously a numpy array is now a
Python list or scalar after the OPT-5 shared memory changes altered data
types during reconstruction.

### Error 2: Missing Required Group During Validation

```
KeyError: Missing required group: random
```

This occurs during HDF5 snapshot loading/validation when the `random` group
(storing RNG state for reproducibility) is absent. Possible causes:

1. The save operation failed partway through (due to Error 1), producing a
   truncated HDF5 file missing later groups.
2. The RNG state serialization format changed without updating the validation
   schema.

### Impact

- **Snapshot save failures** mean training progress cannot be checkpointed.
- **Snapshot load failures** mean training cannot be resumed from prior
  checkpoints.
- Combined, this makes long training runs unrecoverable after any interruption.

### Affected Code

HDF5 serialization/deserialization routines in `cascade_correlation.py` (exact
lines depend on snapshot save/load methods — requires further investigation in
the `juniper-cascor` codebase).

---

## 6. Issue 5: Training Crash After First Epoch (Composite Failure)

### Failure Sequence

The "fails shortly after beginning the first epoch" symptom is a composite
failure caused by issues 1–3 interacting:

```
Step 1: grow_network() enters main grow loop (line 3562)
  │
  ├─ Initial output training completes successfully
  │
Step 2: First candidate training round begins
  │
  ├─ _execute_parallel_training() creates SharedMemory blocks (OPT-5)
  ├─ Tasks dispatched to persistent worker pool (RC-4)
  ├─ Workers begin reading SharedMemory via reconstruct_tensors()
  │
Step 3: Result collection completes (or times out)
  │
  ├─ finally block runs close_and_unlink() on SHM blocks     ← ISSUE 3
  ├─ Slow workers crash reading unmapped memory               ← ISSUE 3
  ├─ Leaked semaphores from crashed workers                   ← ISSUE 1
  │
Step 4: Incomplete/corrupt results processed
  │
  ├─ Best candidate selected from partial result set
  ├─ Candidate may have wrong weight dimensions (stale or dummy data)
  │
Step 5: add_unit() called with bad candidate
  │
  ├─ RC-5 validation catches dimension mismatch (line 3398)
  ├─ ValidationError raised
  └─ Training aborts
```

### Why It Manifests on First Epoch

The first epoch is where the race condition is most likely to trigger because:

1. The SharedMemory blocks are freshly created and the persistent pool workers
   are cold-starting — they take longer to read and process, widening the race
   window.
2. The pre-drain logic (RC-5) has no stale results to clear on the first
   round, so any contamination comes purely from the SHM race, not from queue
   leftovers.

---

## 7. Remediation Recommendations

### P0 — Critical (Must fix before next training run)

#### R1: Fix SharedMemory Lifecycle with Reference Counting

**Target**: Issue 1 (leaks) + Issue 3 (race condition)

Implement a reference-counting mechanism for `SharedTrainingMemory` blocks:

```python
class SharedTrainingMemory:
    def __init__(self, ...):
        self._ref_count = multiprocessing.Value('i', 1)  # creator holds 1 ref

    def acquire(self):
        """Worker calls this before reading."""
        with self._ref_count.get_lock():
            self._ref_count.value += 1

    def release(self):
        """Worker calls this when done reading."""
        with self._ref_count.get_lock():
            self._ref_count.value -= 1
            if self._ref_count.value == 0:
                self.close_and_unlink()
```

The main process calls `release()` instead of `close_and_unlink()` directly.
Workers call `acquire()` on entry and `release()` on exit. The last reference
triggers actual cleanup.

**Alternative (simpler)**: Use a `multiprocessing.Barrier` to synchronize
cleanup — the main process waits for all workers to signal completion before
unlinking.

#### R2: Defer SHM Cleanup Until Worker Acknowledgment

**Target**: Issue 3 (race condition)

If reference counting is too invasive, add an explicit acknowledgment protocol:

1. After result collection, send a "round complete" sentinel to all workers.
2. Workers send an acknowledgment after releasing their SHM references.
3. Main process waits for all acknowledgments (with timeout) before unlinking.

#### R3: Guard atexit Handler Against Double-Free

**Target**: Issue 1 (leaks)

```python
def _cleanup_shared_memory(self):
    for block in list(self._active_shm_blocks):
        try:
            block.close_and_unlink()
        except FileNotFoundError:
            pass  # Already cleaned up
        finally:
            self._active_shm_blocks.discard(block)
```

### P1 — High (Fix in next development cycle)

#### R4: Explicit Task Tuple Protocol

**Target**: Issue 2 (queue contamination maintenance risk)

Replace implicit tuple-length branching with a typed `NamedTuple` or
`dataclass`:

```python
from typing import NamedTuple, Any

class CandidateTask(NamedTuple):
    candidate_config: Any
    training_data: Any
    hyperparams: Any
    round_id: int
```

Update `_process_worker_task()` and `_build_candidate_inputs()` to use named
fields instead of positional indexing.

#### R5: Fix HDF5 Serialization Type Handling

**Target**: Issue 4 (HDF5 errors)

1. Add explicit `numpy.asarray()` conversion before writing datasets to HDF5.
2. Ensure the `random` group is written atomically — use a temporary file +
   rename pattern so partial writes don't produce corrupt snapshots.
3. Add a post-write validation step that reads back and verifies all required
   groups exist.

### P2 — Medium (Track for future improvement)

#### R6: SharedMemory Block Pool

Instead of creating and destroying SHM blocks per round, maintain a pool of
pre-allocated blocks that are reused across rounds. This eliminates the
create/destroy overhead and reduces the surface area for leaks.

#### R7: Worker Health Monitoring

Add heartbeat monitoring for persistent pool workers. If a worker stops
responding (e.g., due to SIGBUS from unmapped SHM), the main process can
detect this and:
- Restart the worker
- Re-dispatch the failed task
- Log diagnostic information

---

## 8. Files Affected

All line numbers reference the `juniper-cascor` repository, primary file
`cascade_correlation.py`:

| File | Lines | Component | Issues |
|------|-------|-----------|--------|
| `cascade_correlation.py` | 1826–1831 | `_generate_candidate_tasks()` | 1, 3 |
| `cascade_correlation.py` | 2070 | Task tagging with `round_id` | 2 |
| `cascade_correlation.py` | 2129–2134 | `_execute_parallel_training()` finally block | 1, 3 |
| `cascade_correlation.py` | 2824 | `_build_candidate_inputs()` | 2 |
| `cascade_correlation.py` | 3134–3142 | `_cleanup_shared_memory()` atexit handler | 1 |
| `cascade_correlation.py` | 3235 | `_process_worker_task()` | 2 |
| `cascade_correlation.py` | 3347 | `add_unit()` | 5 |
| `cascade_correlation.py` | 3398 | `add_unit()` weight dimension validation (RC-5) | 3, 5 |
| `cascade_correlation.py` | 3562 | `grow_network()` main loop | 5 |
| HDF5 serialization routines | TBD | Snapshot save/load | 4 |

---

## 9. Verification Plan

### Pre-Remediation Verification (Confirm Issues Exist)

```bash
# 1. Reproduce SharedMemory leak warnings
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
conda activate JuniperCascor
# Run a short training session and check stderr for ResourceTracker warnings
python -c "
from juniper_cascor.cascade_correlation import CascadeCorrelationNetwork
# ... minimal training run setup ...
" 2>&1 | grep -i "ResourceTracker\|leaked"

# 2. Check for semaphore accumulation during training
# Before training:
ls /dev/shm/ | grep juniper | wc -l
# During/after training:
ls /dev/shm/ | grep juniper | wc -l
# Non-zero after clean exit = confirmed leak

# 3. Verify HDF5 save/load failures
# Attempt to save a snapshot after a training round and check for TypeError
# Attempt to load existing snapshots and check for KeyError on 'random' group
```

### Post-Remediation Verification

```bash
# 1. Confirm no SharedMemory leaks
# Run full training session, verify zero ResourceTracker warnings at exit
python -m pytest tests/ -v -k "shared_memory" 2>&1 | grep -c "leaked"
# Expected: 0

# 2. Confirm /dev/shm cleanup
ls /dev/shm/ | grep juniper
# Expected: no output after clean training exit

# 3. Confirm training completes past first epoch
# Run a multi-epoch training session on a known-good dataset (e.g., SpiralProblem)
# Verify training progresses through multiple grow cycles without ValidationError

# 4. Confirm HDF5 save/load round-trip
# Save a snapshot after successful training round
# Load it back and verify all groups present, especially 'random'

# 5. Stress test: rapid sequential training rounds
# Run 10+ consecutive candidate training rounds to exercise the persistent
# worker pool and SharedMemory lifecycle under load

# 6. Run existing test suites
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
bash scripts/run_tests.bash
```

### Regression Tests to Add

1. **`test_shm_cleanup_after_training_round`** — Verify all SHM blocks are
   cleaned up after `_execute_parallel_training()` returns.
2. **`test_shm_no_premature_unlink`** — Verify workers can complete reads
   after the main process finishes result collection.
3. **`test_round_id_filtering`** — Inject stale results with wrong `round_id`
   and verify they are discarded.
4. **`test_hdf5_snapshot_round_trip`** — Save and load a snapshot, verify all
   required groups are present and data is intact.
5. **`test_add_unit_dimension_validation`** — Verify `add_unit()` rejects
   candidates with mismatched weight dimensions.

---

## Appendix: Historical Context

- **OPT-5**: SharedMemory optimization — replaced per-task data serialization
  with shared memory blocks for training data transfer to worker processes.
- **RC-4**: Persistent worker pool — replaced per-round `Pool.map()` with a
  long-lived worker pool and task/result queues.
- **RC-5**: Stale result mitigation — added `round_id` tagging and pre-drain
  logic to prevent cross-round result contamination. Also added weight
  dimension validation in `add_unit()`.
- **SpiralProblem `__init__` errors** (March 13): Historical log entries
  showing `CascadeCorrelationNetwork` construction failures. Likely from a
  prior broken state; not confirmed as current. Monitor but do not prioritize
  unless reproduced.
