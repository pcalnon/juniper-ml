# PF-8 follow-up: the first-pass burst is libgomp under torch, not NumPy's OpenBLAS — and cascor's parent pin binds only the thread that ran the constructor

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-10
**Status**: attribution SETTLED; §7 residuals 1 and 2 CLOSED 2026-09-11 by [`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md), which also discharges §5's one inferred link — read the dated blockquotes in §5, §5.1 and §5.3 before quoting those sections
**License**: MIT License

---

## 0. What this document is

The discriminating test that
[`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md)
("the probe note") §4.2 left open, executed. That section established that cascor's *initial*
output-layer pass burns 10.6–11.4 cores and runs ~8× slower than it does with
`OMP/MKL/OPENBLAS_NUM_THREADS=2` exported, could not say which library carried it, and named
NumPy's OpenBLAS pool the **leading candidate**:

> Its magnitude (10.6–11.4) sits between an unpinned torch loop at the real shape (7.5) and an
> unpinned NumPy matmul (11–13), so the probes do not discriminate the library. … torch is the
> less likely source and NumPy's OpenBLAS pool the leading candidate. … The discriminating test
> is a profile of the listener's first pass, or reading both pool sizes from inside the process;
> neither was done.

Both have now been done, plus a single-variable pin experiment the probe note explicitly noted it
had never run ("the probe never sets one alone").

**The leading candidate is REFUTED.** The burst is carried by **libgomp — the GNU OpenMP runtime —
inside `libtorch_cpu`, predominantly under `torch::autograd::Engine`**. NumPy's OpenBLAS pool
carries none of it. The root cause is that cascor's parent thread pin is applied in the network
**constructor**, and `omp_set_num_threads` — which `torch.set_num_threads` calls — binds **only
the calling thread**; the service constructs on the request thread and trains on a different
one (`cascor-train`), so the training thread keeps OpenMP's default width of 16.

Item numbers refer to
[`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
("the P2 plan").

---

## 1. Result in one table

Every row is one process, the same 4000-epoch initial output pass over the same 320×2 spiral,
BLAS variables **unset** unless stated. "threads" is the count burning above 0.30 cores in a
single 0.2–0.5 s interval, from `/proc/<pid>/task/<tid>/stat` — except the `unpinned4000.json`
row, which predates the per-interval series and reports threads burning above 0.05 cores across
the whole window; both readings give 2 there.

| arrangement | cores | threads | ms/epoch | evidence |
|---|---|---|---|---|
| **cascor listener**, service default | **13.5 peak** | **16** | ~2.8 | `census-unpinned.json` |
| cascor listener, `OPENBLAS_NUM_THREADS=2` **only** | 13.7 peak | **16** | ~2.8 | `census-openblas-only.json` |
| cascor listener, `OMP_NUM_THREADS=2` **only** | **2.0 peak** | **2** | — | `census-omp-only.json` |
| trainer alone, construct + train on the **same** thread | 1.53 | 2 | 0.66 | `unpinned4000.json` |
| trainer alone, construct on main, **train on a worker thread** | **9.45** | **16** | **4.74** | `onthread.json` |
| trainer alone, construct **and** train on the same worker thread | 1.48 | 2 | 0.75 | `ctor_on_thread.json` |
| trainer alone, worker thread, **three passes back to back** | 10.21 | **16** | — | `repeat3.json` |
| trainer alone, worker thread, **full `fit()`** (3 growth iterations) | 3.50 | 16 **in one 2.4 s block only** | — | `fit_onthread.json` |

Two independent cuts of the same conclusion:

1. **Which library** — pinning `OPENBLAS_NUM_THREADS` alone leaves the burst completely intact;
   pinning `OMP_NUM_THREADS` alone removes it completely. A native profile agrees: of 614
   samples taken during a bursting pass, **`libopenblas`/`scipy_openblas` appears in 0.0%** while
   `libgomp` appears in 47.6% and `libtorch_cpu` in 72.0%.
2. **What triggers it** — in a single process with nothing else changed, moving the pass off the
   thread that constructed the network takes it from 1.53 cores to 9.45 and from 2 threads to 16.
   Constructing on that same worker thread puts it back to 1.48 / 2. It is not a warm-up: three
   passes back to back on the worker thread burst continuously through all three (§5.2).
3. **What ends it** — a full `fit()` on that worker thread bursts for exactly one block and then
   never again, reproducing the listener's structure in one process. Something in the growth loop
   stops it, and it is **not** a re-pin: cascor's production tree contains exactly two
   `set_num_threads` call sites and neither runs on the parent's training thread after
   construction (§5.3). This is the one thing this document does not explain.

---

## 2. The instrument, and why thread NAMES could not be used

The census counts threads and their CPU, from `/proc/<pid>/task/<tid>/stat` (fields 14/15) and
`comm`. It needs no ptrace, which matters: `/proc/sys/kernel/yama/ptrace_scope` is **1** on this
host, so py-spy can only attach to its own descendants and cannot be pointed at a listener that
the launcher started under `nohup`.

**Names do not discriminate on this build.** A validated burn of NumPy's OpenBLAS pool
(`2026-09-10_first_pass_library_attribution.py --synthetic numpy`) produced **12.65 cores across
16 threads, every one named `python`** (`syn_numpy.json`). Width does discriminate, because the
pools differ in maximum on this 16-core host:

| pool | width | ceiling |
|---|---|---|
| torch intra-op, cascor's parent pin (`max(2, worker_thread_count × 2)`) | 2 | ~2 cores |
| torch intra-op, unpinned default | 8 | ~8 cores |
| OpenMP (libgomp) default = `nproc` | 16 | ~16 cores |
| OpenBLAS default = `nproc` | 16 | ~12.6 cores measured |

A **sustained 16-thread** burn therefore excludes torch's intra-op pool at either setting, and
that exclusion has an internal control: in the same unpinned listener process, immediately after
the burst ends, the surviving activity is **exactly 2 threads at ~1.9 cores** — the pin, visibly
in force, in the same process, seconds later.

---

## 3. The single-variable arms (the discrimination the probe note never ran)

`util/ad-hoc/2026-09-10_listener_burst_probe.bash` brings up a cascor listener, drives one run
through `POST /v1/training/start`, and censuses the listener's own threads. It needs **no
juniper-data**: the route materialises the in-process `spiral` generator
(`juniper-cascor/src/api/routes/training.py`, `_generate_spiral_data`).

| arm | env applied at launch | peak cores | threads burning | threads alive |
|---|---|---|---|---|
| `unpinned` | none | 13.516 | 16 | 43 |
| `openblas-only` | `OPENBLAS_NUM_THREADS=2` | 13.671 | 16 | 29 |
| `omp-only` | `OMP_NUM_THREADS=2` | 1.995 | 2 | 16 |

The `openblas-only` arm is the load-bearing one. Alive threads fall by **14** — 43 → 29 at each
arm's peak interval, 44 → 30 at each window's maximum, the same drop either way — so the OpenBLAS
pool **did** shrink from 16 to 2, and the burst is **unchanged at 16 threads and 13.7 cores**. The
pool that shrank is not the pool that was burning.

**This is not a vacuous pass.** All three arms ran the identical, complete initial pass: 4400
`train_output_layer … Epoch` lines each, which is 4000 DEBUG lines (one per epoch) plus 400 INFO
lines (`epoch_display_frequency` = 10). Same work, 13 cores or 2 depending only on which variable
was set.

> **Correction to a reading in the probe note.** Its §4.2 describes "four hundred
> `train_output_layer … Epoch N` lines over eighteen seconds". The line count is right; the
> implied epoch count is not. `train_output_layer` logs at INFO every `epoch_display_frequency`
> (default **10**) epochs and at DEBUG every epoch, so 400 INFO lines is **4000 epochs**, matching
> the cell's `output_epochs: 4000`. The pass has no early exit — its loop is
> `for epoch in range(epochs)` with no `break` — so it always runs the full budget.

---

## 4. The native profile

`py-spy record --native` run as the **parent** of a deliberately-bursting process (the only way
to profile under `ptrace_scope=1`), attributed by sample count with
`util/ad-hoc/2026-09-10_pyspy_stack_attribute.py`. 614 samples:

| marker | samples | share |
|---|---|---|
| `libopenblas` / `scipy_openblas` | 0 | **0.0%** |
| `libmkl` | 0 | 0.0% |
| `libiomp5` / `libomp` | 0 | 0.0% |
| `libgomp` (GNU OpenMP) | 292 | 47.6% |
| `libtorch_cpu` | 442 | 72.0% |
| `libtorch_python` | 422 | 68.7% |
| `torch::autograd::Engine` | 270 | 44.0% |
| GOMP parallel region (`GOMP_parallel` / `gomp_thread`) | 104 | 16.9% |

The deepest recurring native frame is
`torch::autograd::python::PythonEngine::thread_init → torch::autograd::Engine::thread_init →
Engine::thread_main → ReadyQueue::pop`.

> **Read the attribution by SAMPLE count, not line count.** The folded format is
> `<frame>;<frame>;… <count>`, so one line can carry hundreds of samples, and a `grep -c` counts
> lines. `grep -c` also substring-matches: a bare `omp` hits `compiled`, `component` and
> `Compute`. The first pass of this analysis reported "omp 195" that way and it meant nothing.
> The patterns in the attributor are anchored to real `lib*.so` names for that reason.

---

## 5. Root cause

1. cascor pins the parent process with `torch.set_num_threads(max(2, worker_thread_count × 2))`
   = **2** in `_init_multiprocessing`, called unconditionally from the constructor
   (`juniper-cascor/src/cascade_correlation/cascade_correlation.py:617` → `:1179-1180`; there is
   no early return on the path between them).
2. `torch.set_num_threads` reaches OpenMP through `omp_set_num_threads`, whose `nthreads-var` is
   documented as a **per-thread** internal control variable — it binds the calling thread.
   **This step is the one INFERRED link in the chain**, and it is the standard documented
   semantics rather than something verified inside PyTorch here. It is consistent with every
   measurement in §1, but it does **not** on its own predict §5.1 (a plain torch matmul is
   unaffected by the thread it runs on) or §5.3 (later passes on the same wrong thread do not
   burst). Treat steps 1 and 3–6 as measured or read from source, and step 2 as the best-supported
   reading of why they compose the way they do.

   > **2026-09-11 — step 2 is now MEASURED, and this caveat is discharged.**
   > `omp_get_max_threads()`, read through `ctypes` from the already-loaded libgomp, returns the
   > **calling thread's** `nthreads-var`. On the real path it reads 2 on the constructor's thread
   > and **16** on the training thread created afterwards. The chain has no inferred link left.
   > §5.1 and §5.3 are also no longer unpredicted — both are explained by the same instrument.
   > See [`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
   > §2. Note also that **importing torch pins the importing thread to 8**, not 16; the 16 the
   > training thread carries is libgomp's default, not torch's.
3. The service constructs the network in `_create_network_locked`
   (`juniper-cascor/src/api/lifecycle/manager.py:1538`; the constructor call is at `:1578`),
   which runs on the **request** thread — `POST /v1/training/start` creates the network from the
   dataset dims when none exists.
4. The service runs training in `_run_training` (`manager.py:2476`), submitted at `:2472` to a
   single-worker `ThreadPoolExecutor(max_workers=1, thread_name_prefix="cascor-train")` created
   at `:2431`. **Different thread.**
5. So the thread that actually runs the pass never received the pin, and OpenMP uses its default
   width for that thread: `nproc` = 16. The initial output pass is a 2→2 linear layer over 320
   rows — ops far too small to parallelise — so 16-wide regions spend their time in
   synchronisation, not work: ~11–13 cores for **no** wall-clock gain, at ~4–8× the per-epoch
   cost of the 2-wide arrangement.
6. `OMP_NUM_THREADS=2` fixes it because that sets the ICV's **default for every thread** at
   library load, before any thread exists to miss the pin. `OPENBLAS_NUM_THREADS` does not,
   because OpenBLAS is not the carrier.

**`torch.get_num_threads()` reads 2 the entire time.** It reports the library-global setting, not
the width in force on the thread doing the work — which is exactly why the probe note's §4.2
open question ("whether `torch.get_num_threads()` reads 2 inside the listener while the burst
runs") could not have discriminated anything on its own. It does read 2, and the pass still runs
16-wide.

> **2026-09-11 — that is only HALF of why the getter is useless here, and the other half is
> worse.** Calling it is **not a passive read**: it runs torch's per-thread lazy init and
> **re-pins the calling thread's ICV** to the global it reports. Two threads identical but for
> that one call go 16 → 16 without it and 16 → **8** with it. So a probe that reads it inside the
> listener during the burst does not merely fail to discriminate — it **ends the burst** and then
> reports a quiet, correctly-pinned thread. Both halves are stated together here because until
> 2026-09-11 they lived in separate documents. The safe instrument is libgomp's
> `omp_get_max_threads()` through `ctypes`, which returns the calling thread's own width and
> mutates nothing:
> [`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
> §1.1.

### 5.1 What is NOT true

A plain torch matmul is **not** affected by the thread it runs on: 1.84 cores / 2 threads whether
run on the constructor's thread or a worker (`syn_torch_same.json`, `syn_torch_thread.json`). So
this is not "any torch op off-thread loses the pin". It is specific to the path this workload
takes — a tight training loop with `loss.backward()`, which the profile shows running through the
autograd engine. Naming the precise PyTorch code path that re-widens is left open (§7).

> **2026-09-11 — the mechanism is now measured, and it INVERTS this section's reading.** The
> matmul is not *immune* to the thread it runs on: a sustained 1500² matmul **re-pins its own
> thread** from 16 to 2 (torch's global) and then runs at the width it just set. `loss.backward()`
> and cascor's real `train_output_layer` do **not** re-pin, keep the fresh thread's 16, and burst —
> 9.59 and 10.14 cores respectively. So **the burst is the ABSENCE of a re-pin, not the presence
> of a special wide path**, which is the discriminator this section left unnamed. Two cautions:
> the one-shot 512² matmul does **not** re-pin, so the effect is op-shape dependent and "a matmul
> re-pins" does not generalise; and nothing here re-widens anything — a thread that was never
> pinned has nothing to widen. See the 2026-09-11 note's §3.1–§3.2.

### 5.2 It is not a warm-up effect

The obvious competing explanation — that only the *first* parallel workload on a fresh thread runs
wide, and the thread then settles — is **refuted**. Three 1500-epoch passes run back to back on the
same worker thread produce **one continuous ≥10-thread block spanning all three** (pass boundaries
at 6.64 s and 12.58 s inside a block running 1.3 s → 18.8 s; 87 of 93 intervals at ≥ 10 threads,
`repeat3.json`). Every pass on the wrong thread bursts, not just the first.

### 5.3 What stops it after the initial pass is NOT explained here

Steps 1–6 above predict that the ten later output passes burst too: `train_output_layer` has no
early exit, each later pass runs the same `output_epochs` budget, and `grow_network` drives them
from `_run_training` on the same `cascor-train` thread. **They do not burst**, and that is measured
twice, not assumed:

- **In the listener**: a 150 s census of a run with `output_epochs: 800`, `candidate_epochs: 60`,
  `max_iterations: 4` completed four growth iterations and **16 `_retrain_output_layer` calls**,
  and contains exactly **one** ≥10-thread block (t = 3.0 → 5.5 s), whose 2.5 s duration scales
  correctly from the 4000-epoch pass's 11.1 s (`census-unpinned-multipass.json`).
- **In one process**: `--mode fit --on-thread` — construct on main, run the whole fit on a worker
  thread — reproduces exactly that shape: one 2.4 s block (t = 1.3 → 3.8) and nothing after, across
  three growth iterations (`fit_onthread.json`).

So the burst is genuinely confined to the initial pass, the probe note's §2.2 observation stands,
and **a prediction made from the mechanism in §5 is wrong**. The terminator is inside the growth
loop and is not a re-pin: `grep -rn set_num_threads --include=*.py` over
`juniper-cascor/src`, excluding tests and `backups/`, returns exactly two production sites —
`cascade_correlation.py:1180` (the parent, in the constructor) and `:4153` (inside the candidate
worker function, which executes in the child processes). Neither runs on the parent's training
thread after construction. Candidate-pool creation is the obvious suspect and is untested.

The pair `--mode output_pass --on-thread --repeat 3` (bursts throughout) against
`--mode fit --on-thread` (one block) is a two-command bisection handle for whoever takes it.

> **2026-09-11 — ANSWERED, and this section's question contained a false premise.** Nothing
> "stops" the burst: it ends because the **initial output pass ends**, with the training thread's
> ICV still at 16. What the growth loop changes is separate — it **re-pins the thread from 16 to
> 2**, so every *later* pass runs 2-wide. Measured twice, and the two claims score oppositely:
> "the drop ends the burst" is **REFUTED** (the burst was over 2.90 s / 3.49 s before the drop),
> while "the drop is why later passes do not burst" is **SUPPORTED** (peak 2 threads after it).
>
> **The suspect named in the paragraph above is WRONG.** Candidate-pool creation does not re-pin:
> `_ensure_worker_pool` returns with the ICV still at **16** in both runs. The re-pin happens
> later, inside `_collect_training_results`, between its entry and the first
> `_validate_training_result` — i.e. in the `result_queue.get()` that **unpickles the first
> worker's `CandidateTrainingResult`**. Full enclosing stack and the two-run evidence:
> [`JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
> §3.3–§3.5. A plain `pickle.loads` of a small tensor does **not** reproduce it, so the precise
> rebuild path inside the payload remains open.
>
> **Consequence for the defect's extent**: the thread-pin defect costs the **initial output pass
> only**. The thread is re-pinned to 2 during the first candidate collection and stays there for
> the rest of the run — it is not a whole-run 16-wide regime.

---

## 6. What this costs, and what it changes

- **Every service-path timing this lane has recorded was taken with the initial output pass
  running 16-wide.** That is the probe note's §4.3 conclusion, unchanged — but the mechanism is
  now known, so the fix is no longer only "export three variables at bring-up".
- The defect is in **cascor**, not in the experiment YAML. The `runtime:` block being inert
  (probe note §4.1) is a separate, real finding; fixing it by exporting `JUNIPER_CASCOR_BLAS_THREADS`
  would mask this defect rather than repair it.
- The narrower repair — pin on the thread that runs the training, or set the process-wide default
  before any BLAS-importing import — is a **cascor** change and an owner decision, not something
  this document takes.

---

## 7. Residuals — what is still open

1. ~~**What ends the burst after the initial pass** (§5.3)~~ — **CLOSED 2026-09-11.** The premise
   was wrong: nothing ends it, the pass ends. The later passes are quiet because the thread is
   re-pinned 16 → 2 inside `_collect_training_results`; candidate-pool creation is excluded. See
   the §5.3 blockquote. **Successor residual**: the exact rebuild path inside the worker payload
   that re-pins — a small-tensor `pickle.loads` does not reproduce it.
2. ~~The exact PyTorch code path that runs 16-wide off the constructor thread while a plain matmul
   does not (§5.1).~~ — **CLOSED 2026-09-11, question inverted.** Nothing runs "16-wide off the
   constructor thread" as a special path: a fresh thread is 16-wide for everything, and the
   *matmul* is the exception because it re-pins itself. See the §5.1 blockquote.
   **Successor residual**: why the re-pin is op-shape dependent (512² one-shot does not, 1500²
   sustained does).
3. Magnitudes here were taken at a one-minute load of 2.9–5.8 on a 16-core host, not on a quiet
   one. The **discrimination** (which variable removes the burst; which library appears in the
   profile; 16 threads vs 2) is not load-sensitive; the **cores and ms/epoch figures are**, and
   should not be quoted as run-tier numbers or compared against a suite cell.
4. The spiral used by the standalone arms is generated locally to the cell's parameters, not
   fetched from juniper-data. Shape and dtype are reproduced exactly; values are not the cell's.
   `radius_scale` is 10.0 because the **unit-radius spiral is degenerate** for candidate training
   — cascor's own generator docstring records that at unit scale every tanh candidate sits in its
   linear regime, best-of-pool correlation pins at ~2.7e-4, and `grow_network` terminates
   `below_threshold` with zero hidden units. An earlier draft of the probe script used unit radius
   and its `--mode fit` arm measured a growth phase that never happened.

---

## 8. Reproduction

```bash
# 1. the three listener arms (no juniper-data needed; ~2 min each)
bash util/ad-hoc/2026-09-10_listener_burst_probe.bash --arm unpinned      --port 8217 --outdir <dir> --census-seconds 40
bash util/ad-hoc/2026-09-10_listener_burst_probe.bash --arm openblas-only --port 8217 --outdir <dir> --census-seconds 40
bash util/ad-hoc/2026-09-10_listener_burst_probe.bash --arm omp-only      --port 8217 --outdir <dir> --census-seconds 40

# 2. the one-process thread experiment (the mechanism)
env -C <cascor>/src -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS \
    /opt/miniforge3/envs/JuniperCascor1/bin/python \
    util/ad-hoc/2026-09-10_first_pass_library_attribution.py --arm unpinned --mode output_pass [--on-thread] [--construct-on-thread]

# 3. the native profile (py-spy must be the PARENT: ptrace_scope is 1)
env -C <cascor>/src -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS \
    /opt/miniforge3/envs/JuniperCascor1/bin/py-spy record --native --rate 40 --duration 15 --threads \
    -f raw -o stacks.txt -- <python> util/ad-hoc/2026-09-10_first_pass_library_attribution.py \
    --arm unpinned --mode output_pass --on-thread
python3 util/ad-hoc/2026-09-10_pyspy_stack_attribute.py --stacks stacks.txt

# 4. do LATER output passes burst? (answered: NO -- one block across 4 iterations / 16 retrains)
bash util/ad-hoc/2026-09-10_listener_burst_probe.bash --arm unpinned --port 8217 --outdir <dir> \
    --census-seconds 150 --output-epochs 800 --candidate-epochs 60 --max-iterations 4

# 5. the open residual (section 5.3): these two differ, and the difference is the growth loop
#    -- every pass bursts                       vs      -- exactly one block, then nothing
--mode output_pass --on-thread --repeat 3               --mode fit --on-thread --max-iterations 3
```

Evidence from this session is retained at
`~/.local/state/juniper-experiments/suites/pf8-openmp-attribution-20260910/`.

**`--arm` note.** The arms set the variables on the **listener's own** environment at launch,
because they are read once at BLAS load time. `env(1)` stops accepting options at the first
`NAME=VALUE`, so every `-u` must precede every assignment — getting that wrong kills the listener
at startup with `env: '-u': No such file or directory`, which reads like a launch bug rather than
a mis-specified arm.

---

## 9. Files

**Changed / added by this document's work**:

- `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md` (this file, new)
- `util/ad-hoc/2026-09-10_first_pass_library_attribution.py` (new)
- `util/ad-hoc/2026-09-10_listener_thread_census.py` (new)
- `util/ad-hoc/2026-09-10_listener_burst_probe.bash` (new)
- `util/ad-hoc/2026-09-10_pyspy_stack_attribute.py` (new)
- `tests/test_pf8_burst_attribution.py` (new)
- `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` (§4.2 correction blockquote)
- `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md` (§4 hazard updated)
- `CHANGELOG.md`, `AGENTS.md`, `docs/REFERENCE.md`, `.github/workflows/ci.yml` (test wiring)
