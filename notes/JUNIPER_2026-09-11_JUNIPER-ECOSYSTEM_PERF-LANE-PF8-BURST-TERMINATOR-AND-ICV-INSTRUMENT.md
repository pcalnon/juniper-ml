# PF-8 follow-up: the burst is not "stopped" at all — the training thread is re-pinned during candidate result collection, and `torch.get_num_threads()` is not a passive read

**Project**: Juniper — performance lane
**Author**: Paul Calnon
**Date**: 2026-09-11
**Status**: residual 1 ANSWERED (question re-framed); residual 2 EXPLAINED; §5 step 2 now MEASURED; one narrowed residual named in §7
**License**: MIT License

---

## 0. What this document is

The two residuals left open by
[`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md)
("the attribution note") §7, executed:

1. **Residual 1 (§5.3), the live one** — what ends the burst after the initial output pass.
   Measured twice, unexplained, and not a re-pin by either of cascor's two `set_num_threads`
   sites. That note named the untested suspect: *"Candidate-pool creation is the obvious suspect
   and is untested."*
2. **Residual 2 (§5.1)** — which PyTorch path runs 16-wide off the constructor thread while a
   plain matmul does not.

It also converts the attribution note's §5 **step 2** — `omp_set_num_threads` binds the calling
thread, explicitly flagged there as *"the one INFERRED link in the chain"* — into a direct
measurement, and records a **new instrument hazard** that would have silently defeated the probe
note's own proposed discriminator.

"The probe note" is
[`JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`](JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md);
"the P2 plan" is
[`JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md).

**The headline correction.** The question "what *stops* the burst" contained a false premise.
Nothing stops it: the burst ends because the initial output pass ends. What the growth loop
changes is something else — it re-pins the training thread's OpenMP width from 16 to 2, so every
*later* pass runs 2-wide. Those are two different claims, the reducer separates them, and only
the second is true (§3.3).

---

## 1. The instrument the whole arc was missing

libgomp is already mapped into the process — the attribution note's native profile puts 47.6% of
samples there — so `omp_get_max_threads()` is callable through `ctypes`, and **it returns the
calling thread's `nthreads-var` ICV**. That is the width that thread will actually use for its
next parallel region: exactly the quantity every previous probe in this arc had to infer.

```python
lib = ctypes.CDLL("libgomp.so.1")     # already loaded: dlopen returns that same mapping
lib.omp_get_max_threads.restype = ctypes.c_int
lib.omp_get_max_threads()             # the CALLING THREAD's width
```

Every result below records `/proc/self/maps`'s libgomp path
(`/opt/miniforge3/envs/JuniperCascor1/lib/libgomp.so.1.0.0`) so the reading is tied to the
runtime torch is actually using, rather than to "some libgomp".

### 1.1 `torch.get_num_threads()` is not a passive read — it RE-PINS the calling thread

Two threads, identical except that one calls the getter (`getter-side-effect.json`):

| arm | calls `torch.get_num_threads()` | ICV before → after | re-pinned |
|---|---|---|---|
| `read_icv_twice` | no | 16 → **16** | no |
| `read_getter_between` | yes | 16 → **8** | **yes** |

**This retires the probe note's §4.2 proposed discriminator.** That section proposed *"reading
`torch.get_num_threads()` … from inside the listener during it"* as a way to identify the burst's
carrier. Executing it would have ended the burst it was trying to observe, and reported a pinned
thread as evidence that nothing was wrong.

The attribution note's §5 is right that the getter *reports* the library global rather than the
thread's width. What was not known is that **calling it also sets** the thread's width to that
global. Both halves matter; only the first is currently written down there.

### 1.2 The instrument's own first draft had exactly this defect

The first draft's checkpoint recorded the ICV *and* `torch.get_num_threads()`. Every `icv-map`
arm then reported an identical 16 → 8 re-pin — **including the do-nothing control arm**, which is
what exposed it. The control is retained and the summary prints a loud failure line if it ever
re-pins again, because with it the map is a measurement and without it the map is the
instrument's own footprint.

---

## 2. §5 step 2, measured rather than inferred

The attribution note's §5 step 2 reads:

> `torch.set_num_threads` reaches OpenMP through `omp_set_num_threads`, whose `nthreads-var` is
> documented as a **per-thread** internal control variable — it binds the calling thread. **This
> step is the one INFERRED link in the chain.**

It is now measured, in-process, on the real path (`growth.json`):

| checkpoint | thread | ICV |
|---|---|---|
| before torch import | main | 16 |
| after torch import | main | **8** |
| after `CascadeCorrelationNetwork(...)` (the constructor's `set_num_threads(2)`) | main | **2** |
| entry to the training thread | `cascor-train-probe` | **16** |

The constructor pins **its own** thread to 2; a thread created afterwards starts at libgomp's
default of `nproc` = 16 and has never heard of the pin. Step 2 is confirmed, and the chain's one
inferred link is closed.

Note the second row on its own: **importing torch pins the importing thread to 8**, not 16. The
16 that the training thread carries is libgomp's default, not torch's — which is why a probe that
compared against torch's intra-op default would have found the wrong number.

---

## 3. Residual 1 — what happens after the initial pass

### 3.1 The op-class map

Each arm on its **own fresh thread** (once re-pinned a thread stays re-pinned, so sharing one
thread would let the first arm mask every later one). Constructed on the main thread, as the
service does. `icv-map.json`:

| op | ICV entry → after | re-pinned | peak threads | peak cores |
|---|---|---|---|---|
| `none` (control) | 16 → 16 | no | 0 | 0.0 |
| `matmul` (512², one-shot) | 16 → 16 | no | 0 | 0.0 |
| `matmul_note_shape` (1500², sustained 4 s) | 16 → **2** | **yes** | 2 | 2.08 |
| `linear_fwd` | 16 → 16 | no | 0 | 0.0 |
| `linear_bwd` (fwd + `loss.backward()`) | 16 → 16 | no | **12** | **9.59** |
| `output_pass` (cascor's real `train_output_layer`) | 16 → 16 | no | **14** | **10.14** |
| `unpickle_tensor` (`pickle.loads` of a 64² tensor) | 16 → 16 | no | 0 | 0.0 |
| `from_numpy` | 16 → 16 | no | 0 | 0.0 |
| `construct_here` (constructor on the arm's thread) | 16 → **2** | **yes** | 0 | 0.0 |

The burst reproduces here at **10.14 cores** on a thread whose ICV is 16 — consistent with the
probe note's 10.6–11.4 and the attribution note's 9.45.

### 3.2 This explains §5.1, and inverts its reading

The attribution note's §5.1 says a plain torch matmul is *"**not** affected by the thread it runs
on: 1.84 cores / 2 threads whether run on the constructor's thread or a worker"*, and treats that
as showing the matmul is immune. The ICV column shows the opposite mechanism: **the sustained
matmul re-pins the thread to 2 itself** and then runs at the width it just set. It is not immune
to the thread — it *fixes* the thread on the way past.

`loss.backward()` and cascor's real output pass do **not** re-pin, keep the fresh thread's 16, and
burst. That is the discriminator §5.1 left unnamed: **the burst is the absence of a re-pin, not
the presence of a special wide path.**

**Do not generalise this to "matmul re-pins".** The one-shot 512² matmul does not; the sustained
1500² one does. The re-pin is op-shape dependent and neither arm licenses a claim about the
other.

### 3.3 The two claims the raw trace conflates

The reducer `util/ad-hoc/2026-09-11_icv_trace_align.py` states them separately and scores each
against the observed burn, because an ICV reading says what a thread *would* do and the burst is
what the process *did*:

| claim | verdict (`growth.json`) | verdict (`growth-bisect.json`) |
|---|---|---|
| (a) the ICV drop **ends the burst** | **REFUTED** — the burst was already over 2.90 s earlier | **REFUTED** — 3.49 s earlier |
| (b) the ICV drop is why **later passes do not burst** | **SUPPORTED** — peak 2 threads after it, over 15 samples | **SUPPORTED** — over 10 samples |

Stage spans from `growth.json` (3 growth iterations, `output_epochs` 800, `hidden_units` 3 grown;
`growth-bisect.json` is the 2-iteration run and grew 2 — do not cross the two files' numbers, which
an earlier draft of this note did):

| stage | span (s) | ICV on exit |
|---|---|---|
| `train_output_layer` (initial) | 2.198 → 7.150 — **contains the whole burst** (3.877 → 6.721) | **16** |
| `train_candidates` | 7.158 → 9.779 | 2 |
| ├ `_ensure_worker_pool` | 7.160 → 8.970 | **16** |
| ├ `_collect_training_results` | 8.971 → 9.724 | **2** ← the drop |
| `_retrain_output_layer` (first later pass) | 9.904 → 10.411 | 2 |

So: **nothing stops the burst.** It ends when the initial output pass ends, with the ICV still at
16. The growth loop's contribution is to re-pin the thread to 2 **before the first later pass
runs**, which is why the later passes are quiet — the measurement the attribution note's §5.3
recorded twice and could not explain.

### 3.4 Candidate-pool creation is EXCLUDED — the attribution note's stated suspect is wrong

`_ensure_worker_pool` spans 7.160 → 8.970 s and **returns with the ICV still at 16**, in both
runs. Pool creation, task generation, the stale-result drain and the shared-memory cleanup all
leave the width alone. The attribution note's *"candidate-pool creation is the obvious suspect"*
is now tested and refuted.

### 3.5 The re-pin is localised to one call

`_collect_training_results` is a `result_queue.get()` / `_validate_training_result` loop. Wrapping
the validator interleaves a checkpoint immediately after each `get()` (`growth-bisect.json`):

| checkpoint | t (s) | ICV |
|---|---|---|
| `_collect_training_results:before` | 10.197 | **16** |
| `_validate_training_result:before` (first result) | 10.862 | **2** |

Between those two points the only thing that runs is `result_queue.get(timeout=…)` — the
**unpickling of the first worker's `CandidateTrainingResult`**. That is where the training
thread's OpenMP width is re-pinned from 16 to 2, and the value it lands on (2) is torch's global,
set by the constructor.

The full enclosing stack the reducer prints, innermost last:
`train_candidates > _execute_candidate_training > _execute_parallel_training >
_collect_worker_results > _collect_training_results > _validate_training_result`. The innermost
frame is where the *checkpoint that first reads 2* sits; the re-pin itself happened in the
`result_queue.get()` immediately before it, which has no frame of its own because it is not a
method of the network.

**The precise rebuild path inside that payload is NOT named here.** A plain `pickle.loads` of a
64² tensor does not reproduce the re-pin (§3.1), so the trigger is something about the real
payload — its size, or the storage-rebuild path used for a tensor that was created in another
process — and not "unpickling a tensor" in general. See §7.

---

## 4. What this changes for the owner decisions

**Nothing is re-opened and no decision is taken here.** The six open decisions listed in
[`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_perf-lane-burst-is-libgomp-and-the-pin-binds-the-constructor-thread.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_perf-lane-burst-is-libgomp-and-the-pin-binds-the-constructor-thread.md)
§1 stand unchanged in substance. **One** of them is better informed — the cascor thread-pin
defect, whose extent is now bounded. The `runtime:` block decision is **unchanged**; it appears
below only because this work reconfirms its existing rationale, not because anything moved:

- **The cascor thread-pin defect.** The repair options in the attribution note's §6 — "pin on the
  thread that runs the training, or set the process-wide default before any BLAS-importing
  import" — are both still correct, and §2 above now measures the mechanism they address rather
  than inferring it. The *extent* is also now bounded: the defect costs the **initial output pass
  only**, because the thread is re-pinned to 2 during the first candidate collection and stays
  there for the rest of the run. It is not a whole-run 16-wide regime.
- **The `runtime:` block.** Unchanged: exporting `JUNIPER_CASCOR_BLAS_THREADS` would mask this
  defect rather than repair it, and cascor#531's counter-evidence (a BLAS cap *slowing* the
  candidate phase 1.52×) still applies.

---

## 5. What is NOT claimed

- **Not** that the ICV drop ends the burst — measured and refuted, twice (§3.3).
- **Not** that candidate-pool creation re-pins — measured and refuted, twice (§3.4).
- **Not** that unpickling a tensor re-pins in general — the 64² arm does not (§3.1, §3.5).
- **Not** that "a matmul re-pins" — the one-shot 512² arm does not (§3.2).
- **Not** any run-tier figure. The four evidence files record their own one-minute load at
  **9.20, 10.86, 11.71 and 12.10** on a 16-core host with a 21-hour `clamscan` running; the host
  was at 20.30 when the session opened, before any measurement. Quote the per-file figure, not a
  band — an earlier draft of this section said "11–20", which excluded two of its own four
  observations. The **discriminations** (16 vs 2; which stage spans the drop; which arm re-pins)
  are structural and load-insensitive; the cores, ms and wall-clock spans are not, and must not be
  compared against a suite cell.

---

## 6. Reproduction

```bash
# every -u must precede every NAME=VALUE: env(1) stops accepting options at the first assignment
P=/opt/miniforge3/envs/JuniperCascor1/bin/python
C=/home/pcalnon/Development/python/Juniper/juniper-cascor/src
S=util/ad-hoc/2026-09-11_omp_icv_checkpoint_probe.py

# 1. the getter side effect (§1.1) -- two threads, one call apart
env -C $C -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS $P $S \
    --mode torch-getter-side-effect --json <dir>/getter-side-effect.json

# 2. the op-class map (§3.1) -- fresh thread per arm; the `none` control MUST NOT re-pin
env -C $C -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS $P $S \
    --mode icv-map --json <dir>/icv-map.json

# 3. the growth loop (§3.3-3.5) -- checkpoints on the training thread at every stage
env -C $C -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS $P $S \
    --mode growth --output-epochs 800 --candidate-epochs 60 --max-iterations 3 \
    --json <dir>/growth.json

# 4. the reducer -- scores claims (a) and (b) separately against the observed burn
python3 util/ad-hoc/2026-09-11_icv_trace_align.py --json <dir>/growth.json
```

Evidence from this session is retained at
`~/.local/state/juniper-experiments/suites/pf8-icv-checkpoint-20260911/` — four files:
`getter-side-effect.json`, `icv-map.json`, `growth.json` (3 iterations),
`growth-bisect.json` (2 iterations, the §3.5 localisation).

**Stop condition.** If the `icv-map` control arm (`none`) reports `repinned: true`, the
instrument is perturbing the measurement and no arm in that run is interpretable — fix the
checkpoint before quoting anything from it.

---

## 7. Residuals

1. **The exact rebuild path inside the worker payload that re-pins** (§3.5). Localised to
   `result_queue.get()`; a plain small-tensor `pickle.loads` does not reproduce it. Naming it
   needs either a larger / shared-memory-backed payload arm, or an interposer on
   `omp_set_num_threads`.
2. **Why the re-pin is op-shape dependent** (§3.2) — 512² one-shot does not, 1500² sustained
   does. Untested whether the discriminator is size, duration, or repetition.
3. **The listener has not been re-measured with this instrument.** Every reading here is
   single-process. The listener's shape was established in the attribution note's §1 and is not
   in doubt, but the stage-level localisation of §3.5 has only been shown in-process.
   `ptrace_scope` is 1 on this host, and the `/proc/<pid>/task/` census needs no ptrace — but the
   ICV read does need to run *inside* the listener, which this probe does not do.
4. Magnitudes were taken at high ambient load (§5, last bullet).

---

## 8. Files

**Changed / added by this document's work**:

- `notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md` (this file, new)
- `util/ad-hoc/2026-09-11_omp_icv_checkpoint_probe.py` (new — the instrument)
- `util/ad-hoc/2026-09-11_icv_trace_align.py` (new — the reducer)
- `tests/test_pf8_icv_checkpoint_probe.py` (new)
- `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md` (§5, §5.1, §5.3, §7 corrections)
- `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` (§4.2 — the proposed discriminator is retired)
- `CHANGELOG.md`, `AGENTS.md`, `docs/REFERENCE.md`, `.github/workflows/ci.yml` (test wiring)
