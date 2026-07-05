# P-1 / RC-4 multiprocessing race — investigation takeoff plan

**Author:** Paul Calnon
**Date:** 2026-05-03
**Status:** Plan; ready for user-approved execution
**Predecessor:** [`JUNIPER_2026-05-02_JUNIPER-CASCOR_V38-GROW-NETWORK-INVESTIGATION-PLAN.md`](./JUNIPER_2026-05-02_JUNIPER-CASCOR_V38-GROW-NETWORK-INVESTIGATION-PLAN.md) §7 (closed via Option E retag)
**Gating:** P-5 unblocked (recovery env `JuniperCascor1` works for local repro)

---

## 0. What's already known (from V38 Phase A.2)

- Symptom: `_process_training_results(results, tasks, ...)` occasionally
  receives `results=[]` for `len(tasks)>0`, triggering the
  `_get_dummy_results` fallback. Tests asserting unit growth then see
  `best_candidate=None`.
- Heisenbug confirmed: `print(..., flush=True)` checkpoints around the
  IPC boundary make the failure deterministically disappear.
- Eliminated: RC-2 (empty tasks list at entry), RC-3 (silent exception
  swallowing). Every observed result during the diagnostic run had
  `success=True`, `error_message=None`, `candidate_is_none=False`.
- Suspected location: the `_task_distributor.distribute_and_collect`
  → `_execute_parallel_training` → `_collect_worker_results` →
  `_collect_training_results` chain.

## 1. IPC architecture (mapped 2026-05-03)

```text
parent: train_candidates
  ↓ generates tasks
parent: _execute_candidate_training
  ↓ delegates to TaskDistributor.distribute_and_collect
parent: TaskDistributor._split_tasks → all-local for unit-test budgets
  ↓ calls local_fn = _execute_parallel_training
parent: _execute_parallel_training
  ├─ _drain_stale_results(result_queue)         ◀── RC-5 hardening already in place
  ├─ _cleanup_pending_shared_memory()           ◀── OPT-5 deferred unlinks
  ├─ for task: task_queue.put(tagged_task)      ◀── tagged with round_id
  ├─ workers = self._persistent_workers          ◀── RC-4 persistent pool
  └─ results = _collect_worker_results(...)
       ├─ wait loop (max_wait_time=60s):
       │     - alive_workers check (never empties for persistent pool)
       │     - result_queue.qsize() >= len(tasks) ⇒ break
       │     - else time.sleep(sleepytime)
       └─ _collect_training_results(result_queue, len(tasks), round_id):
             - while collected < num_tasks and time < deadline:
                   try: result = result_queue.get(timeout=1.0)
                   discard if round_id mismatch (RC-5)
                   else: append, collected += 1
                   except Empty: continue
             - return results

worker: _worker_loop
  ├─ task_queue.get(timeout=task_queue_timeout)
  ├─ _process_worker_task(task, ..., result_queue, ...)
  │     ├─ trains the candidate (sub-second on the V38a/c fixtures)
  │     └─ result_queue.put(CandidateTrainingResult(...))
  └─ loop forever (persistent pool, no exit between rounds)
```

The race window must lie between the worker's `result_queue.put()`
and the parent's `result_queue.get()` returning that item.

## 2. Three plausible race hypotheses

### H1 — `multiprocessing.Queue` feeder-thread visibility

`multiprocessing.Queue.put()` is **non-atomic with respect to
qsize/get**. Internally:

1. Worker calls `put(result)`.
2. The result is pickled and appended to the worker's in-process
   `_buffer` deque.
3. A daemon `_thread` (the "feeder") wakes and writes the pickle to
   the underlying `Pipe`'s write end.
4. Only after the write succeeds is the queue's `_sem` (semaphore)
   incremented. `qsize()` is `_sem._value`.

So between (1) and (4) there is a window where the result has been
"put" from the worker's caller perspective but is **not yet visible**
to the parent's `qsize()` or `get()`. For a sub-second per-candidate
budget, all 4 workers may all reach (1) within microseconds; if the
parent's `_collect_worker_results` wait loop's `qsize()` check fires
in the gap before any of (4) lands, the loop continues for one
`sleepytime` interval — which may be enough OR may race the next
iteration.

**Why `print(flush=True)` masks it:** the I/O sync forces the parent
to give up the GIL and gives the feeder threads in the workers
several context-switch quanta to flush. By the time the print
returns, all `_sem` increments have landed.

**Validation:** instrument the parent's wait loop with non-blocking
checkpoints that count how often `qsize()` returns each integer
value across iterations. Under repro, expect `qsize()` to plateau
just below `len(tasks)` for several iterations before settling.

**Fix shape:** replace the `qsize()` early-exit with a stronger
guarantee. Two options:

1. **Track expected results** — block on a `multiprocessing.Event`
   that workers set when they observe the queue's `_sem` post-put.
   Adds round-trip latency.
2. **Drop the early-exit** — let the wait loop run the full
   `max_wait_time` budget OR until workers genuinely exit. Trades
   throughput for determinism. For unit-test budgets, the budget is
   already capped at 60 s, so worst-case wall time would only matter
   for production-realistic candidate runs (where the actual training
   dominates the wait anyway).
3. **Skip the wait loop entirely** — `_collect_training_results`
   already has its own 60 s deadline and per-`get()` timeout. The
   wait loop is redundant; removing it forces the race window to
   close inside `get()`'s blocking call (which DOES block on `_sem`
   correctly).

Option 3 is the smallest delta and the most likely to fix the race.
The wait loop is primarily an optimization to dodge the per-`get()`
1 s timeout on already-completed rounds — if the queue's `_sem`
already reflects all results, `get()` returns each in microseconds
without timing out.

### H2 — `_drain_stale_results` racing in-flight feeders from the prior round

`_drain_stale_results` is called at the START of each round to clear
results from prior rounds. It uses `result_queue.get_nowait()` in a
tight loop until `Empty`.

If the prior round's last worker is STILL in the (1)→(4) window when
the next round starts:

1. Round N completes; parent collects N results; calls `train_candidates`
   for round N+1.
2. The N+1th worker's feeder thread is still flushing round N's last
   result into the Pipe.
3. Round N+1 begins, drains nothing (queue empty per Pipe).
4. Round N+1 puts tasks. Workers pick them up.
5. Suddenly the prior-round feeder lands a stale result into the
   Pipe, AFTER round N+1's drain. That result has the OLD `round_id`.
6. `_collect_training_results` sees the stale result, RC-5 round_id
   mismatch fires, result is discarded.
7. The stale result took the slot of one of round N+1's results in
   the queue. We collect `num_tasks - 1` valid results plus 1 stale.
8. Loop continues until deadline (60 s) waiting for the missing
   round-N+1 result… but it never arrives, because all 4 workers
   already put their results.
9. Deadline hit. `_collect_training_results` returns 3 valid results.
10. `_process_training_results` enters the `len(results) != len(tasks)`
    branch (warning), processes 3 results, picks the best.

**This doesn't match the V38 symptom.** The V38 symptom is `results=[]`,
not `results=3`.

But there's a variant: if MULTIPLE prior-round feeders race the drain,
ALL N+1 results could be displaced by stale ones. Drain runs once at
the start; further stale arrivals are discarded one-by-one in
`_collect_training_results`, displacing fresh slots.

For 4 tasks with 4 workers, this would require 4 stale prior-round
results to all land mid-collection. Unlikely but not impossible if
the wait loop gives them enough time.

**Validation:** instrument `_drain_stale_results` to log on every
stale result drained AND on every round_id mismatch in
`_collect_training_results`. If both fire under repro, this is the
mechanism.

**Fix shape:** add a brief `time.sleep(0.01)` or
`os.fsync()` before the drain to let any in-flight feeders land. OR
move to a fresh queue per round (drop the persistent-pool RC-4
optimization for this queue specifically — workers persist, queues
don't).

### H3 — SharedMemory close/unlink race

The OPT-5 `_active_shm_blocks` / `_pending_shm_unlinks` mechanism
defers SharedMemory unlinks to the start of the NEXT round, after
the prior round's results are drained. The intent is to keep the
shared memory available to workers through result collection.

Possible race:

1. Round N: parent allocates SharedMemory, workers read training
   data from it.
2. Workers train, put results.
3. Parent collects results.
4. Parent's `finally` block calls `shm_block.close()` on each block,
   appends to `_pending_shm_unlinks`.
5. Round N+1 starts. `_cleanup_pending_shared_memory` calls
   `shm_block.unlink()` on each pending block.
6. If a worker from round N is **still** reading from the block
   (e.g. its result is sitting in the feeder buffer, the worker has
   moved on to round N+1's task but hasn't released the round-N
   shm handle yet), `unlink()` could race the worker's release.
7. Depending on the OS, the worker's read may corrupt or fault.
   The worker's result may be malformed, pickling fails inside
   `result_queue.put()`, the result is silently lost.

This would manifest as `results=[]` in the WORST case (all workers
hit the same race).

**Validation:** instrument the worker loop to log around every
SharedMemory access and around `result_queue.put()`. If pickling
exceptions appear under repro, this is the mechanism. Also log every
`unlink()` with the block name and a worker liveness snapshot.

**Fix shape:** synchronize round transitions via a
`multiprocessing.Barrier` that all workers must reach before the
parent unlinks shared memory. Or move the unlink into the worker
itself once it confirms its result has been put successfully.

## 3. Reproducibility plan

### 3.1 Local repro target

Use the recovery env `JuniperCascor1` (Python 3.13, regular CPython,
torch 2.11.0+cu130, verified by `util/check_conda_env_torch.bash`).

The 4 retagged tests are the highest-yield repro targets:

```bash
conda activate JuniperCascor1
cd /home/pcalnon/Development/python/Juniper/juniper-cascor

python -m pytest \
    -m integration \
    src/tests/unit/test_fast_fit.py \
    src/tests/unit/test_cascade_correlation_coverage.py::TestCascadeCorrelationCoverage::test_grow_network_adds_hidden_unit \
    -p no:randomly \
    -p no:cacheprovider \
    -v --count=50 --maxfail=1
```

`pytest-repeat`'s `--count=50` runs each test 50× in the same process,
maximizing the chance of hitting the race within a single session.
Expected: at least one failure if the race reproduces under regular
CPython 3.13. If 50× is clean, escalate to 200× or run with
`pytest-xdist` `-n auto` to also exercise process-level concurrency
(though that's a different scenario from the production code path).

### 3.2 Instrumentation strategy

A blunt `print(flush=True)` masks the race. Instead, use a per-event
ring buffer — `collections.deque(maxlen=10000)` of `(monotonic_ns,
event_name, payload)` — and dump it ONLY on test failure (via a
pytest fixture's teardown). The ring buffer's `append` is O(1)
and free of I/O sync, so it shouldn't perturb timing.

Hooks:

- `_execute_parallel_training`: before `task_queue.put()`, after
  every `put()`, after the `_collect_worker_results` call.
- `_collect_worker_results`: every iteration of the wait loop with
  `(qsize, alive_count, elapsed)`.
- `_collect_training_results`: every `get()` with `(deadline_remaining,
  result_round_id, expected_round_id)`. Every `Empty` exception.
- `_worker_loop` (in each worker): before `task_queue.get()`, after
  task pickup, before `result_queue.put()`, after `put()`.

Workers can't share the ring buffer directly (separate processes);
they emit events through a third `instrumentation_queue` that the
parent merges on test failure. To avoid masking the race with the
new queue, this third queue is created lazily (only when the env
flag is set) and is bounded with `put_nowait` (drop on overflow).

### 3.3 Decision rule

For each hypothesis (H1, H2, H3), the ring-buffer dump should show
specific signatures:

| Hypothesis | Signature in the dump |
|---|---|
| H1 — feeder visibility | `_collect_worker_results` plateaus at `qsize=N-1` (or N-k) for several iterations before reaching N. `_collect_training_results` then collects all N quickly. **Race doesn't manifest.** |
| H2 — drain race | `_drain_stale_results` empties the queue at round start. Mid-collection, RC-5 round_id mismatch fires. Final `len(results) != len(tasks)`. |
| H3 — shm unlink race | Worker logs `result_queue.put()` BEFORE the parent's `_cleanup_pending_shared_memory`, but the put never lands in qsize. OR a pickling exception appears in worker logs around shm access. |

If none of the three signatures fires but the race repros, escalate
to a Phase B investigation with `strace`/`py-spy` on the worker
processes.

## 4. Fix-shape preference

In order of escalating delta:

1. **H1 fix (drop wait-loop early exit)** — single-line change in
   `_collect_worker_results`: skip the `qsize() >= len(tasks)`
   `break`. Adds at most one extra `sleepytime` interval to the
   common case; for the production case where training dominates
   wall time, the impact is negligible.
2. **H2 fix (sync before drain)** — three-line change in
   `_drain_stale_results`: `time.sleep(0.01)` before the
   `get_nowait()` loop. Adds 10 ms per round; over ~100 rounds in a
   typical training run that's 1 s — acceptable.
3. **H3 fix (barrier)** — multi-line change adding a
   `multiprocessing.Barrier` that workers reach after `put()` and
   the parent reaches before `unlink()`. Most invasive; only worth
   doing if H1 and H2 don't close the race.

In all three cases, after the fix, the 4 retagged tests should be
flipped back to `@pytest.mark.unit` and the unit-tier gate verified
green over a 50-iteration loop.

## 5. Rollback contingency

If the fix introduces a deadlock or significantly slows training:

- Re-tag tests as integration (Option E pattern from V38).
- Revert the multiprocessing change.
- Document the failed-fix in this doc's `§6` with the specific
  observed regression.

## 6. Status

- Plan drafted 2026-05-03 against cascor `9348a26` HEAD (post-PR-#188
  R5-4-pre training counters; pre-PR-#195 range-dict revert).
- Awaiting user approval on the fix-shape preference (§4) before
  implementing instrumentation (§3.2) and validation runs (§3.1).
- Once approved, the implementation will be a separate PR off cascor
  main with the instrumentation gated behind `CASCOR_RC4_RING_BUFFER=1`
  so it doesn't ship to production.
