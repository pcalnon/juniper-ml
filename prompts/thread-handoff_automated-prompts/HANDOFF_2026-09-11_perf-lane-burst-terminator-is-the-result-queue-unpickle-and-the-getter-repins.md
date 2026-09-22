# HANDOFF 2026-09-11 — nothing stops the burst, the terminator is the candidate-result `queue.get()`, and `torch.get_num_threads()` would have destroyed the measurement

Successor to
[`HANDOFF_2026-09-10_perf-lane-burst-is-libgomp-and-the-pin-binds-the-constructor-thread.md`](HANDOFF_2026-09-10_perf-lane-burst-is-libgomp-and-the-pin-binds-the-constructor-thread.md).

> **THE PREDECESSOR IS NOT SUPERSEDED.** Its §1 items 1 and 2, and its §3, §5, §6 and §7,
> remain live, and through it the 2026-09-10, 2026-09-09 and 2026-09-07 handoffs remain live too.
> This document carries only what this session changed or learned. **What IS superseded**: its §1
> item 3 (the live residual) and item 4 are both discharged, and its item 3 named the wrong
> suspect — see §3.
>
> **NOTHING IS RUNNING from this session.** No listener was started at all, so no port was bound —
> but **the `growth` arms are NOT single-process**: `network.fit()` creates a real candidate worker
> pool, so an abnormal exit can leave forkserver children behind. Check both:
> ```bash
> ps -eo pid,cmd --no-headers | grep -E "[o]mp_icv_checkpoint_probe|[i]cv_trace_align"
> ps -eo pid,ppid,etimes,cmd --no-headers | grep -E "[f]orkserver|[s]pawn_main|[r]esource_tracker"
> ```
> The second returns rows that are **not** yours: a peer's cascor stack on `:8202` (from
> `worktrees/juniper-cascor--fix--snapshot-restore-seed-numpy-scalar--…`) and a container under
> `/app/src`, both ~57 h old at hand-off. Discriminate by `etimes` and by the `sys_path` in the
> cmdline — a child of this session's probe would be minutes old and carry the cascor **primary**
> path. Both were checked at hand-off: no child of this session survived.

---

> # ⚠ RE-PROBED 2026-09-22 — §1's WORK LIST IS SUBSTANTIALLY DISCHARGED, AND ONE OF ITS STANDING RECOMMENDATIONS IS NOW BROKEN
>
> Eleven days passed and **no successor handoff was ever written**, while three perf-lane PRs
> shipped. Read this block before acting on anything below it.
>
> | §1 item | state on 2026-09-22 |
> |---|---|
> | **1 — six owner decisions, "put them to the owner"** | **DONE, on 2026-09-11, hours after this file was written.** All six RULED: [`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](../../notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md) (`juniper-ml#1927`). Per-decision status in the table below. **Do not re-ask the owner.** |
> | **2 — a micro cut on an idle host** | **STILL BLOCKED (5th session), and the recipe below is now BROKEN** — see the `0003` block in §1 item 2. |
> | **3 — three narrowed ICV residuals** | **UNTOUCHED.** Still open, still optional. The 09-16 sweep closed a *different* residual (its own draft's), not these. |
>
> **The six decisions, as ruled and as executed:**
>
> | D | ruling (2026-09-11) | state 2026-09-22 |
> |---|---|---|
> | **D1** cascor thread-pin defect | measure later output passes at widths > 2 first | **The WIDTH question is answered** — [`…THREAD-WIDTH-SWEEP.md`](../../notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md): widths 2–8 indistinguishable, keep 2 (16 is 4.97–7.42× worse across both runs — see ⚠ 2 for the mechanism qualifier). **The DEFECT is not repaired and the repair is still an open owner item** — see the ⚠ below. |
> | **D2** `runtime:` block via the env route | implement, **gated** on a two-phase cap sweep | **route half measured** — it binds, and capping helps (the published −33% is measured on a contaminated column and **understates** it, ⚠ 3 below); **epoch-count half never delivered** — see ⚠ below. **IMPLEMENTED 2026-09-22**, this session. |
> | **D3** PF-3 | unblock via D2, then a quiet host | **still blocked** — D2's code has only just landed, and the host has never been quiet. |
> | **D4** PF-2 retarget | retarget at the candidate phase + 2 axes | **SPEC'd**; axis 3 calibrated (viable, gate on *accuracy*, sample 2,3,4,5). **Axis 2 needs an OWNER CALL** — 250 → 500,000 is unreachable, juniper-data caps `n_points_per_spiral` at 10,000. |
> | **D5** CI floor-check hazard | relocate onto the execution path | **SHIPPED** — `check_cascor_parallel_floor`, `util/experiments/run_suite.py:162`, called from `main`. Six assertions reference it, of which **three are refusals** (`assertRaisesRegex`) and three are allow-cases. |
> | **D6** `epochs_completed` | re-measure the spread before gating | **DISCHARGED 2026-09-22** — spread is **zero**, and D6's premise is refuted. [`notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`](../../notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md). |
>
> ## ⚠ Three corrections to what the 09-16 sweep is usually quoted as having settled
>
> **1. "No repair is owed" would be wrong.** D1 asked whether 2 is the right width; the answer
> is "nothing in 2–8 beats it". That is *not* the same as the **cascor thread-pin defect being
> repaired**. `cascade_correlation.py:1180` still calls `torch.set_num_threads(max(2,
> worker_thread_count * 2))` inside `_init_multiprocessing`, which binds only the constructing
> thread — so the training thread still runs the initial output pass unpinned at 16.
> `…ICV-INSTRUMENT.md` and `…BURST-LIBRARY-ATTRIBUTION.md` both still call the repair an open
> owner decision, and the 09-16 sweep never retracts them. D2's environment route is a
> **workaround available to the experiment harness**, not a fix to cascor.
>
> **2. "16 is 5–7× worse" needs its mechanism qualifier.** That penalty is the `thread`
> mechanism's. On the `env` route — the one the owner actually ruled for — width 16 costs about
> **1%** (later-pass medians 1.574 vs ~1.55 at width 2). "5–7×" is also loose: the true span
> across both runs is **4.97–7.42×**. The 09-16 note itself calls `thread`
> w16 "an artificial worst case that no production configuration produces". Quoting the 5–7×
> without saying which mechanism produced it overstates the case for capping by a wide margin.
>
> **3. The sweep's "initial pass" column is not the initial pass**, and its §2.1 3.3× gap is an
> artifact of that. Full correction, with the reconciling arithmetic, is now in
> [`notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`](../../notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md) §2.
> The −33% **understates** the real capping benefit; D1's conclusion and the cascor#531
> non-reproduction are unaffected.
>
> ## ⚠ The D1/D2 gates were reported as met, and the instrument never emitted what they asked for
>
> Both gates demanded **epoch counts** — D1: *"reporting epoch count and total wall time, never
> ms/epoch"*; D2 item 4: *"epoch counts per phase"*. `util/ad-hoc/2026-09-16_thread_width_arm.py`
> emits `later_pass_count` and `candidate_phase_count`, which count **STAGES, not epochs**, and
> the string `epoch` occurs in **none of the 40 evidence files**. The arm's own docstring claims
> it reports *"epochs completed and the final accuracy"*; it reports neither.
>
> **Why it matters, narrowly.** The headline *"cascor#531's candidate-phase penalty does not
> reproduce"* rests on candidate-phase **wall time** alone. Wall time is epochs × time-per-epoch,
> so a flat wall is equally consistent with *no effect* and with *two effects cancelling* — and
> cancelling is live, because the ruling's §1 records two channels moving oppositely (throughput
> 1.26× → 1.14×, epoch count 1.21× → 1.03×). The epoch-count channel is numerics-driven, so it
> bears on result **identity**, not merely speed.
>
> **This does not undo D2's implementation** — a key that is accepted and discarded is a defect
> either way — but **nobody may cite the 09-16 note as closing the penalty question.**
>
> ## What shipped 2026-09-22 (this re-probe session)
>
> - **D2 IMPLEMENTED.** `runtime:` no longer binds nothing. See the §1 item 1 D2 block below.
> - **D6 DISCHARGED** from a committed instrument. Its 09-17 predecessor is **not lost** — the
>   instrument and a note both exist, UNCOMMITTED, in `.claude/worktrees/optimized-giggling-koala`
>   (that worktree is locked; do not remove it). Committing them is the owner's call.
>
> **Changed by this session, by filename**: `util/experiments/run_suite.py`,
> `util/experiment_stack.bash`, `tests/test_run_suite.py`,
> `tests/test_experiment_stack_script.py`,
> `util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py` (new),
> `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md` (new),
> and this file.

---

Document of record:
[`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`](../../notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md)
("the ICV note"), shipped on `juniper-ml#1896`. "The attribution note" is
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`; "the
probe note" is `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`; "the
P2 plan" is `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`.

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. This session executed the predecessor's §1 items 3
and 4 — the two residuals the attribution note's §7 left open — and closed both. The enabling move
was that libgomp's **per-thread** `nthreads-var` ICV is readable through `ctypes`
(`omp_get_max_threads()` returns the *calling thread's* width), which is the quantity the whole arc
had been inferring from thread counts and core totals. `juniper-ml#1896` is merged (see §2 for the
squash sha). Item 2 remains host-bound — the four evidence files record one-minute loads of 9.20 /
10.86 / 11.71 / 12.10, and the host was at 20.30 when the session opened — and item 1's six owner
decisions remain owner-gated, unchanged in substance.

### Work list, in order

1. ~~**Six owner decisions are open — put them to the owner; do NOT take them yourself.**~~
   **ALL SIX RULED 2026-09-11** (`juniper-ml#1927`). The table below is kept because each row
   still names where a decision's *substance* lives, which the ruling note cites rather than
   restates. **Do not re-ask.** Current status per decision is in the re-probe block at the top.

   > **D2 is now IMPLEMENTED (2026-09-22).** The `runtime:` block had been **accepted and
   > discarded**: `run_experiment.py` validated all three `RUNTIME_KEYS` and nothing read any of
   > them, so `runtime: {blas_threads: 2}` ran 16-wide and a matrix that *varied* the key
   > measured one configuration N times. `eval_metrics_enabled` was worst — `service:` rejects it
   > with *"belongs in runtime: (process env)"*, herding authors into a key that did nothing.
   >
   > Implemented as the owner ruled it, via the environment route: `run_suite.runtime_block_env`
   > resolves the block before the first `--up` (fail-closed — a bad value refuses the suite,
   > D5's lesson), and `experiment_stack.bash` exports and **records** the variables at cascor
   > bring-up, so `env/launch.env` finally states the width the service actually ran at.
   >
   > **An explicit `runtime:` value beats the H-11 parallel budget split.** Not a preference:
   > PF-3's second axis *is* per-cell thread width, so if the H-11 split won, every PF-3 cell
   > would run at width 2 and the axis would be inert a second time — the exact failure D3's
   > ruling tells you to dry-run-check for. Both values are recorded on the registry row
   > (`thread_budget` and `runtime_env`), so an oversubscribing override is visible in the
   > evidence rather than inferred from the YAML.
   >
   > **This makes D3's prescribed check meaningful for the first time.** "Verify with a one-cell
   > dry run that the cell's `thread_env` is non-null" could not have failed informatively
   > before — nothing set it.

   One is better informed:
   - **The cascor thread-pin defect.** Repair options unchanged (pin on the training thread, or
     set the process default before any BLAS-importing import). **Its EXTENT is now bounded**: the
     defect costs the **initial output pass only**, because the training thread is re-pinned to 2
     during the first candidate result collection and stays there. It is not a whole-run 16-wide
     regime, so size the repair against one phase, not the run.
   - The other five, **each with the document that actually holds its substance** — "carried
     unchanged" is not a brief, and three of these are not recoverable from the predecessor alone:
     | decision | where its substance lives |
     |---|---|
     | the `runtime:` block | the predecessor's §1 item 1, and `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` §4 |
     | PF-3 blocked on it | `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md` row 2.2 |
     | PF-2's inert axis | `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md` row 2.1 |
     | P2-plan item 4.2's CI hazard (optional) | `notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md` row 4.2, and §1.5 of `notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md` |
     | `epochs_completed` exact-match | **`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md` §3.3 — and NOWHERE ELSE.** It appears zero times in the P2 plan; every handoff since has said only "carried unchanged" |
2. **Needs an IDLE host (still, never taken across four sessions)**: a micro cut at a 1-minute load
   under 3. Not available this session — load was **20.30 at start**, 11.38 five-minute, with the
   same `clamscan` of `/home` still running (now 21+ hours). Procedure and invocation unchanged:
   `/home/pcalnon/Development/python/Juniper/juniper-cascor/docs/testing/REFERENCE.md` § Micro
   timing reference — **the absolute path matters**: that file is ecosystem-root-relative and
   `cat juniper-cascor/docs/testing/REFERENCE.md` from this worktree returns "No such file or
   directory", while juniper-ml ships a `docs/REFERENCE.md` of its own that a bare relative path
   can silently resolve to. The runnable invocation is the first block of the probe note's §8,
   which already uses absolute paths. ~~`0003` stays the recommended compare target;
   `--benchmark-compare=0003`~~, never `--benchmark-compare-fail`.

   > ## ⚠ RE-PROBED 2026-09-22 — `--benchmark-compare=0003` CANNOT RESOLVE ANY MORE
   >
   > pytest-benchmark keys its storage directory on the **interpreter**, and `JuniperCascor1`
   > was rebuilt 3.13 → 3.14 on 2026-09-12. The store holds exactly one directory:
   >
   > ```
   > ~/.local/state/juniper-experiments/baselines/cascor-micro/Linux-CPython-3.13-64bit/
   >     0001_3286b758…  0002_145fbe92…  0003_a51b7c58…
   > ```
   >
   > `Linux-CPython-3.14-64bit/` does not exist. The next cut lands there, in an **empty** store,
   > numbered `0001`.
   >
   > **Verified in the installed source, not assumed.** `pytest_benchmark/session.py:45-49`
   > always sets `default_machine_id = get_machine_id()`, and `get_machine_id()` is
   > `'{system}-{implementation}-{major.minor}-{arch}'`. `storage/file.py:80` then resolves a
   > one-part glob as `platform_glob = self.default_machine_id` — so a **bare**
   > `--benchmark-compare=0003` searches `Linux-CPython-3.14-64bit/` **only**, and finds
   > nothing. The standing recommendation repeated across three handoffs and
   > `docs/REFERENCE.md` is dead as written.
   >
   > **The two-part form still resolves**: `--benchmark-compare=Linux-CPython-3.13-64bit/0003`
   > takes the `len(parts) == 2` branch (`file.py:77-78`) and would load it. **Do not reach for
   > that as the fix.** It compares across a different interpreter *and* a different torch, so
   > it is not like-for-like; it would produce a number that looks comparable and is not —
   > which is worse than no comparison. Whoever gets the quiet host should cut a **fresh 3.14
   > reference** and say so. Treat the four-session-old "re-cut and compare to `0003`" plan as
   > retired.
3. **Three narrowed residuals** (the ICV note's §7), all optional. The first is S only by the
   larger-payload route; its interposer alternative is an LD_PRELOAD-class native shim and is not
   S. The third is **not S** — `ptrace_scope` is 1 here and the arc's standing rule is not to
   modify juniper-cascor, so reading the ICV inside a live listener needs a new mechanism:
   - **The exact rebuild path inside the worker payload that re-pins.** Localised to the
     `result_queue.get()` that unpickles the first `CandidateTrainingResult`; a plain
     `pickle.loads` of a 64² tensor does **not** reproduce it, so it is something about the real
     payload (size, or the storage-rebuild path for a tensor created in another process). Needs a
     larger / shared-memory-backed arm, or an interposer on `omp_set_num_threads`.
   - **Why the re-pin is op-shape dependent** — a one-shot 512² matmul does not re-pin, a sustained
     1500² one does. Untested whether the discriminator is size, duration or repetition.
   - **The listener has not been re-measured with this instrument.** Every ICV reading here is
     single-process. The ICV read must run *inside* the listener, which this probe does not do.

### Do NOT do these

- **Do not read `torch.get_num_threads()` to diagnose a thread-width question.** It is not a
  passive read: it runs torch's per-thread lazy init and **re-pins the calling thread**. Reading it
  inside the listener during the burst — which the probe note's §4.2 proposed — would *end the
  burst* and report a quiet, correctly-pinned thread as evidence that nothing was wrong. Use
  `ctypes.CDLL("libgomp.so.1").omp_get_max_threads()`, which mutates nothing.
- **Do not repeat "candidate-pool creation is the obvious suspect"** — it is measured and
  **excluded**: `_ensure_worker_pool` returns with the ICV still 16, in both runs.
- **Do not say the ICV drop "ends the burst".** Measured and refuted twice (the burst was over 2.90
  s / 3.49 s earlier). The true claim is the narrower one: the drop is why *later* passes do not
  burst.
- **Do not generalise "a matmul re-pins"** from the sustained arm, or "unpickling re-pins" from the
  real payload — the one-shot matmul and the small-tensor unpickle both do **not**.
- Do not quote this session's cores or ms as run-tier figures: the evidence files' own one-minute loads run 9.20–12.10, and the host was at 20.30 when the session opened. Quote the per-file figure, never a band. The
  discriminations are structural and load-insensitive; the magnitudes are not.
- Everything in the predecessor's "Do NOT" list still holds.

---

## 2. What shipped this session

| PR | merged | squash sha | what |
|---|---|---|---|
| `juniper-ml#1896` | 2026-09-11T10:06:57Z | `4b13f318` | the ICV note, two `util/ad-hoc/` instruments, `tests/test_pf8_icv_checkpoint_probe.py` (18 tests) wired into CI / `AGENTS.md` / `docs/REFERENCE.md`, and corrections to the attribution note, the probe note, the P2 plan and `CHANGELOG.md`. Three signed commits (work, validation corrections, clobber repair) |
| this handoff | opened after that merge | — | this file |

`juniper-ml#1896` changed, by filename:
`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md`
(new), `util/ad-hoc/2026-09-11_omp_icv_checkpoint_probe.py` (new),
`util/ad-hoc/2026-09-11_icv_trace_align.py` (new), `tests/test_pf8_icv_checkpoint_probe.py` (new),
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`,
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`,
`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`, `.github/workflows/ci.yml`,
`AGENTS.md`, `docs/REFERENCE.md`, `CHANGELOG.md`.

---

## 3. Key context — new this session

- **The instrument.** libgomp is already mapped in, so `ctypes.CDLL("libgomp.so.1")` returns a
  handle to *that* mapping and `omp_get_max_threads()` reads the **calling thread's** width. Record
  `/proc/self/maps`'s libgomp path with every reading
  (`/opt/miniforge3/envs/JuniperCascor1/lib/libgomp.so.1.0.0`) or the reading is "some libgomp says
  16".
- **The attribution note's §5 step 2 — its one INFERRED link — is now measured.** Constructor
  thread **2**, training thread created afterwards **16**. Also: *importing torch* pins the
  importing thread to **8**, so a fresh thread's 16 is libgomp's default, not torch's.
- **The terminator, localised to one call.** ICV 16 at `_collect_training_results:before`, already
  **2** at the first `_validate_training_result:before`; between them the only thing that runs is
  `result_queue.get()`. Enclosing stack, as the reducer prints it: `train_candidates > _execute_candidate_training >
  _execute_parallel_training > _collect_worker_results > _collect_training_results >
  _validate_training_result` — the innermost frame is the checkpoint that first reads 2; the
  `result_queue.get()` that did the re-pin has no frame of its own.
- **The op-class map** (fresh thread per arm, network constructed on main): `none` 16→16 (control),
  `matmul` 512² 16→16, `matmul_note_shape` 1500²/4 s **16→2** (2 threads, 2.08 cores), `linear_fwd`
  16→16, `linear_bwd` 16→16 (**12 threads, 9.59 cores**), `output_pass` — cascor's real
  `train_output_layer` — 16→16 (**14 threads, 10.14 cores**), `unpickle_tensor` 16→16, `from_numpy`
  16→16, `construct_here` **16→2**. So **the burst is the ABSENCE of a re-pin**, which inverts the
  attribution note's §5.1 reading of the matmul.
- **Two claims, scored separately** by `2026-09-11_icv_trace_align.py`: "the drop ends the burst"
  **REFUTED** (2.90 s / 3.49 s gap), "the drop is why later passes do not burst" **SUPPORTED**
  (peak 2 threads after, over 15 / 10 samples). A reducer that emitted one verdict would have
  licensed the wrong claim.

---

## 4. Verification commands

```bash
git fetch origin && git rev-parse --short origin/main   # 4b13f318 or a descendant
git log --oneline -1 origin/main -- notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md
python3 -m unittest -q tests/test_pf8_icv_checkpoint_probe.py tests/test_pf8_burst_attribution.py tests/test_pf8_occupancy_probe.py tests/test_ci_test_wiring_drift.py   # 18 + 14 + 26 + 11 = 69 OK  (re-probed 2026-09-22: 72 — the suites grew; the count, not the result, is stale)
python3 util/ad-hoc/2026-09-11_icv_trace_align.py --json ~/.local/state/juniper-experiments/suites/pf8-icv-checkpoint-20260911/growth.json   # (a) REFUTED, (b) SUPPORTED, re-pin inside _validate_training_result
python3 util/ad-hoc/2026-09-10_agents_md_test_list_drift.py   # 165 / 165 / 165, zero drift
ls ~/.local/state/juniper-experiments/suites/pf8-icv-checkpoint-20260911/   # 4 evidence files
ps -eo pid,cmd | grep "[/]juniper-cascor/src"   # empty: no holder on the cascor primary
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main   # cc0d1630..., NOT a51b7c58
```

Added 2026-09-22, for the two items this re-probe closed:

```bash
python3 -m unittest -q tests.test_run_suite tests.test_experiment_stack_script   # 118 + 92 = 210 OK
python3 -c "import importlib.util,pathlib; s=importlib.util.spec_from_file_location('r','util/experiments/run_suite.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.runtime_block_env({'runtime':{'blas_threads':2}}))"   # all three BLAS vars = '2', not {}
/opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py --widths 1 16 --epochs 100 --repeats 2   # control stable, spread 0, 68 at both widths
ls ~/.local/state/juniper-experiments/baselines/cascor-micro/   # ONLY Linux-CPython-3.13-64bit — see the 0003 block in §1 item 2
```

**Stop condition.** Re-run the `icv-map` mode and check the **`none` control arm**: if it reports
`repinned: true`, the instrument is perturbing the measurement and **no arm in that run is
interpretable**. Fix the checkpoint before quoting anything.

---

## 5. Retained state — do not delete

- Everything in the predecessor's §5, including
  `~/.local/state/juniper-experiments/suites/pf8-openmp-attribution-20260910/` (13 files).
- `~/.local/state/juniper-experiments/suites/pf8-icv-checkpoint-20260911/` — **4 files**:
  `getter-side-effect.json` (the two-arm proof), `icv-map.json` (nine op-class arms),
  `growth.json` (3 growth iterations, the canonical run), `growth-bisect.json` (2 iterations, the
  deepest wrap set — the §3.5 localisation).

---

## 6. Traps this session paid for

1. **`torch.get_num_threads()` RE-PINS the calling thread.** The probe's first draft recorded it in
   every checkpoint, so every `icv-map` arm — **including the do-nothing control** — reported an
   identical 16 → 8 re-pin caused by the instrument. **The control arm is the only thing that
   caught it.** Always carry a do-nothing arm when the measurement and the instrument touch the
   same state.
2. **An arm that constructs the object it measures measures the constructor.** The first
   `output_pass` arm built its network on the arm's own thread, so it recorded the constructor's
   `set_num_threads(2)` (16 → 2) and looked like the pass re-pinning. Constructing on main — the
   service's real shape — gives 16 → 16.
3. **A control that fails is a result, not a nuisance.** The reducer's first run said "NOT ALIGNED"
   for the drop-vs-burst-end alignment; that misalignment *is* the finding (the question's premise
   was false), not a broken instrument. It is now reported as two separately-scored claims.
4. **The worktree classifier refuses `env -C … && …` chains, and `cd … && python3 - <<'PY'`
   heredocs.** Split into plain single commands, or put the code in a `util/ad-hoc/` file — which
   is where it belongs anyway. It accepted a bare `cd X && python3 - <<PY` once and refused the
   same shape later; do not rely on it.
5. **`util/open_signed_pr.py` takes `--message` (headline) plus `--commit-body-file`**, not
   `--message-file`. The trailer must be in the commit *body* file, as its last paragraph.
6. **mypy does not narrow through `self.assertIsInstance`.** `default.value` after it is an
   `attr-defined` error; use a plain `assert isinstance(...)`, which is permitted in `tests/`.
7. **`gh pr checks --json` is unsupported on this `gh`** — parse the plain output, or use
   `util/wait_for_checks.py --anchor required`.
8. **`origin/main` moved mid-session** (a peer's soak-probe work) and **the cascor primary moved
   too**, `a51b7c58` → `cc0d1630` (cascor#642, a ci-tools ceiling widen). The predecessor's §4 said
   `a51b7c58`; that is now stale. Merge origin/main locally and re-run the gates *before* opening
   the PR — `open_signed_pr.py` sends whole file contents, so a stale local copy of a file you
   touch would clobber the peer's change to it.

---

## 7. What this handoff does NOT cover

The predecessor's §7, and the arcs it names (backup, canopy E2E, defect register, P5, soak,
partition, service-core) have other owners. The ICV note's §7 lists four residuals; the first three
are in §1 item 3 above.

## Git state at hand-off

- juniper-ml: `juniper-ml#1896` **merged 2026-09-11T10:06:57Z as `4b13f318`** — read from
  `gh pr view 1896 --json state,mergedAt,mergeCommit` after the fact, not asserted from the plan.
  Branch `perf/pf8-burst-terminator-icv-2026-09-11` auto-deleted on merge (`git ls-remote --heads
  origin <branch>` returns nothing). **Three** signed commits, all created through the API because
  local GPG signing hangs headless: `debfe5f8` (the work, `util/open_signed_pr.py`), then
  `77942e81` and `c3440ac7` (the validation corrections and a clobber repair, via
  `util/ad-hoc/2026-09-08_append_signed_commit.py`). **The lane was contended**: `util/safe_merge.py`
  went `BEHIND` twice while waiting and the merge was finished by its armed auto-merge net rather
  than by the script's own call — so read the receipt, not the script's exit. This handoff file is
  on its own branch as a separate PR. The session worktree
  `.claude/worktrees/optimized-giggling-koala` is locked and outlives the session — **do NOT remove
  it**; Phase 4 of `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` requires
  the liveness and in-use probes first and forbids `--force`.
- juniper-cascor: primary at **`cc0d1630`**, clean, untouched by this session, no holders. Every
  probe ran against it read-only via `env -C <cascor>/src`.
