# HANDOFF 2026-09-10 — the first-pass burst is libgomp under torch, cascor's parent pin binds only the constructor's thread, and the owner decisions are unchanged but re-weighted

Successor to
[`HANDOFF_2026-09-10_perf-lane-pf8-located-pair-run-runtime-block-binds-nothing.md`](HANDOFF_2026-09-10_perf-lane-pf8-located-pair-run-runtime-block-binds-nothing.md).

> **THE PREDECESSOR IS NOT SUPERSEDED.** Its §1 work list, §3 (key context), §5 (retained state),
> §6 (twelve traps) and §7 remain live, and through it the 2026-09-09 and 2026-09-07 handoffs
> remain live too. This document carries only what this session changed or learned. **Its §4.2
> attribution is the one thing that IS superseded** — see §3 below.
>
> **NOTHING IS RUNNING from this session.** Verify by process, not by port:
> `ps -eo pid,cmd --no-headers | grep -E "[u]vicorn.*8217|[l]istener_thread_census|[f]irst_pass_library"`.
> Port 8217 was used and released; a **peer** session's cascor stack still listens on `:8202`
> from a cascor worktree — not yours. The cascor primary is at `a51b7c58`, clean, **not moved**,
> and had no holders at session end.

Document of record for everything below:
[`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`](../../notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md)
("the attribution note"), shipped on `juniper-ml#1881`. "The probe note" is
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`; "the P2 plan" is
`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`.

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. This session executed the predecessor's §1 item 4 —
the discriminating test the probe note left open — and it **refuted the probe note's published
leading candidate**. The burst that makes cascor's initial output pass ~8× slower is **libgomp,
the GNU OpenMP runtime, inside `libtorch_cpu`**, predominantly under `torch::autograd::Engine`;
NumPy's OpenBLAS pool carries **none** of it. The cause is a **cascor defect**: the parent thread
pin is applied in the network *constructor*, and the service constructs on the request thread but
trains on a different one. `juniper-ml#1881` is merged. Nothing else from the predecessor's work
list was executed — item 2 remains host-bound and items 1, 3 and 5 remain owner-gated.

### Work list, in order

1. **Six owner decisions are open — put them to the owner; do NOT take them yourself.** The
   predecessor's five are unchanged in substance but **item 1 is re-weighted and there is a new
   sixth**:
   - **NEW — the cascor thread-pin defect.** `torch.set_num_threads(2)` is called in
     `_init_multiprocessing` from the constructor
     (`juniper-cascor/src/cascade_correlation/cascade_correlation.py:617` → `:1179-1180`), but the
     service constructs in `_create_network_locked` (`api/lifecycle/manager.py:1538`) on the
     request thread and trains in `_run_training` (`:2476`) on the `cascor-train` executor
     (`:2431`). The training thread therefore keeps OpenMP's default width of 16 and the initial
     output pass — a 2→2 linear over 320 rows — burns 11–13 cores for no wall-clock gain. Repair
     is a **cascor** change (pin on the training thread, or set the process-wide default before
     any BLAS-importing import) and changes the speed regime of every service-path figure
     recorded, so it needs a new run-tier baseline exactly as the `runtime:` decision does.
   - **RE-WEIGHTED — the `runtime:` block** (probe note §4, §6 item 4). Unchanged as a finding:
     the three keys are validated, accepted and read by nothing. **But "implement" is no longer a
     fix.** Exporting `JUNIPER_CASCOR_BLAS_THREADS` from `runtime.blas_threads` would *mask* the
     defect above rather than repair it. cascor#531's counter-evidence still applies (a BLAS cap
     *slowed* the candidate phase 1.52×), and only the output phase has ever been measured.
   - **PF-3 (P2 item 2.2) is still BLOCKED** on that decision — `runtime.num_processes` is inert.
   - **PF-2's inert axis** — unchanged, carried.
   - **Item 4.2's CI hazard** — still optional.
   - **`epochs_completed` exact-match** — unchanged, carried.
2. **Needs an IDLE host (still, never taken)**: a micro cut at a 1-minute load under 3. Not
   available this session — load was 7.18 at start and 4.45 at end, with a `clamscan` of `/home`
   running throughout (9+ hours, ~0.8 cores sustained). Procedure and invocation unchanged:
   `juniper-cascor/docs/testing/REFERENCE.md` § Micro timing reference, and the first block of the
   probe note's §8. `0003` stays the recommended compare target; `--benchmark-compare=0003`, never
   `--benchmark-compare-fail`.
3. **The live residual — what ENDS the burst after the initial pass.** Measured twice and
   unexplained. `train_output_layer` has no early exit, later passes run the same budget on the
   same `cascor-train` thread, and cascor's production tree has exactly two `set_num_threads` sites
   (`:1180` parent-constructor, `:4153` candidate-worker child) so nothing re-pins — yet later
   passes do **not** burst. The two-command bisection handle is in the attribution note's §5.3:
   `--mode output_pass --on-thread --repeat 3` bursts continuously through all three passes, while
   `--mode fit --on-thread` bursts once and never again. Candidate-pool creation is the obvious
   suspect and is untested.
4. **Optional, S**: name the PyTorch path that runs 16-wide off the constructor thread while a
   plain torch matmul does not (the matmul is unaffected: 1.84 cores on either thread).

### Do NOT do these

- Do not repeat "NumPy's OpenBLAS pool" as the carrier — it is **refuted**, not merely narrowed:
  `OPENBLAS_NUM_THREADS=2` alone leaves the burst at 16 threads / 13.7 cores while that pool
  demonstrably shrinks by 14 threads, and `libopenblas` is **0.0%** of 614 native samples.
- Do not read `torch.get_num_threads()` as the width in force. It reads **2** throughout the
  burst; it reports the library global, not the calling thread's OpenMP width.
- Do not quote this session's cores or ms/epoch as run-tier figures. They were taken at a
  one-minute load of 2.9–5.8. The *discrimination* is load-insensitive; the magnitudes are not.
- Do not build a probe on a **unit-radius** spiral. cascor's own generator docstring records that
  at unit scale every tanh candidate sits in its linear regime and `grow_network` terminates with
  zero hidden units — a growth phase that never happens. Use `radius: 10.0`.
- Everything in the predecessor's "Do NOT" list still holds.

---

## 2. What shipped this session

| PR | merged | squash sha | what |
|---|---|---|---|
| `juniper-ml#1881` | 2026-09-10 | `83ed4055` | the attribution note, four `util/ad-hoc/` instruments, `tests/test_pf8_burst_attribution.py` (14 tests) wired into CI / `AGENTS.md` / `docs/REFERENCE.md`, and corrections to the probe note, the P2 plan, `docs/REFERENCE.md` and `CHANGELOG.md`. Five authored commits: the work, two precision corrections to the note, and one CodeQL fix |
| this handoff | opened after that merge | — | this file |

**The CodeQL fix was three real leftovers, not false positives** — a local assigned only to be
deleted, and the synthetic burn discarding its product (`a @ b` as a bare statement). They held
the merge behind three unresolved review threads while every required check was green; the threads
auto-resolved as *outdated* once the code changed and CodeQL re-ran. `util/safe_merge.py` refuses
on unresolved threads and reports that refusal as exit 1 — read the refusal, do not retry past it.

`juniper-ml#1881` changed, by filename:
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md` (new),
`util/ad-hoc/2026-09-10_first_pass_library_attribution.py`,
`util/ad-hoc/2026-09-10_listener_thread_census.py`,
`util/ad-hoc/2026-09-10_listener_burst_probe.bash`,
`util/ad-hoc/2026-09-10_pyspy_stack_attribute.py`, `tests/test_pf8_burst_attribution.py` (all new),
`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`,
`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`, `docs/REFERENCE.md`,
`AGENTS.md`, `CHANGELOG.md`, `.github/workflows/ci.yml`.

---

## 3. Key context — new this session

- **Three independent lines give the same answer.** (a) Single-variable pins on a real listener:
  unpinned 13.516 cores / 16 threads; `OPENBLAS_NUM_THREADS=2` alone 13.671 / **16** (unchanged)
  while alive threads fall by 14; `OMP_NUM_THREADS=2` alone **1.995 / 2**. All three arms ran the
  identical complete 4000-epoch pass (4400 log lines each), so it is not a vacuous comparison.
  (b) `py-spy --native`, 614 samples: `libopenblas` 0.0%, `libmkl` 0.0%, `libiomp5`/`libomp` 0.0%,
  `libgomp` 47.6%, `libtorch_cpu` 72.0%, `torch::autograd::Engine` 44.0%. (c) One process,
  unpinned, same 4000-epoch work: same thread 1.53 cores / 2 threads; **worker thread 9.45 / 16**;
  construct *and* train on that worker 1.48 / 2.
- **Thread NAMES do not discriminate on this build** — a validated OpenBLAS burn runs 16 threads
  all named `python`. Pool **width** does: torch intra-op is 2 (pinned) or 8 (default), OpenMP and
  OpenBLAS are both 16, so a sustained 16-thread burn excludes torch's intra-op pool. The internal
  control is in the same process: seconds after the burst ends, exactly 2 threads burn at ~1.9
  cores.
- **The probe note's "four hundred Epoch lines" are 4000 epochs**, not 400: `train_output_layer`
  logs INFO every `epoch_display_frequency` (default 10) and DEBUG every epoch, and its loop is
  `for epoch in range(epochs)` with **no break**. That reading survived six consensus rounds.
- **`ptrace_scope` is 1 on this host**, so py-spy can only attach to its own descendants — it
  cannot be pointed at a launcher-started listener. The `/proc/<pid>/task/` census needs no ptrace
  and is the instrument for a running service; py-spy is usable only as the *parent* of a
  deliberately-bursting process.
- **The listener needs no juniper-data**: `POST /v1/training/start` materialises the in-process
  `spiral` generator (`api/routes/training.py`, `_generate_spiral_data`), which is what makes the
  three-arm listener experiment a single-service, ~2-minute run.

---

## 4. Verification commands

```bash
git fetch origin && git rev-parse --short origin/main   # 83ed4055 or a descendant
git log --oneline -1 origin/main -- notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md   # 83ed4055
python3 -m unittest -q tests/test_pf8_burst_attribution.py tests/test_pf8_occupancy_probe.py tests/test_ci_test_wiring_drift.py   # 14 + 26 + 11 = 51 OK
python3 util/ad-hoc/2026-09-10_pyspy_stack_attribute.py --stacks ~/.local/state/juniper-experiments/suites/pf8-openmp-attribution-20260910/burst_stacks.txt   # libopenblas 0.0%, libgomp 47.6%
ls ~/.local/state/juniper-experiments/suites/pf8-openmp-attribution-20260910/   # 13 evidence files
ps -eo pid,cmd | grep "[/]juniper-cascor/src"   # empty: no holder on the cascor primary
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main   # a51b7c58...
```

**Stop condition.** If `libopenblas` is not 0.0% of that stack file, or the `omp-only` census does
not show 2 burning threads, the instrument or the tree drifted — stop and re-derive before quoting.

---

## 5. Retained state — do not delete

- Everything in the predecessor's §5.
- `~/.local/state/juniper-experiments/suites/pf8-openmp-attribution-20260910/` — 13 files: three
  listener censuses (`census-{unpinned,openblas-only,omp-only}.json`), the multi-pass census
  (`census-unpinned-multipass.json`), the six one-process arms, the synthetic instrument-validation
  arms, and `burst_stacks.txt` (the py-spy raw folded stacks).

---

## 6. Traps this session paid for

1. **`env(1)` stops accepting options at the first `NAME=VALUE`.** An arm written
   `(OMP_NUM_THREADS=2 -u MKL_NUM_THREADS …)` makes `env` treat `-u` as the command and the
   listener dies at startup with `env: '-u': No such file or directory` — which reads like a launch
   bug, not a mis-specified arm. Pinned by a test.
2. **`grep -c` over py-spy folded stacks answers the wrong question twice**: it counts LINES (one
   line can carry hundreds of samples) and it substring-matches (`omp` hits `compiled`,
   `component`, `Compute`). The first pass of this analysis reported "omp 195" that way.
3. **A width match is not an attribution when two pools share a width.** OpenBLAS and libgomp are
   both `nproc` = 16 here; only the single-variable pins separated them.
4. **`$?` after a pipe reads the last command's status**, so `cmd | tail; echo $?` reported the
   comparator's exit as 0 when it was 2. Read `PIPESTATUS`, or drop the pipe.
5. **A mechanism that explains the trigger need not explain the extent.** The thread finding is
   solid and its prediction that later passes burst is **wrong**; both are in the note.
6. **Bandit B105 fires on the NAME.** A loop variable called `token` compared against `"-u"` trips
   `hardcoded_password_string`. Rename the variable; do not `# nosec`.
7. **The worktree classifier** refuses `env … python -c "<code>"`, heredocs, and `sed` with a
   runtime-computed path. Put the code in a `util/ad-hoc/` file — which is where it belongs anyway.

---

## 7. What this handoff does NOT cover

The predecessor's §7, and the arcs it names (backup, canopy E2E, defect register, P5, soak,
partition, service-core) have other owners. The attribution note's §7 lists four residuals; §5.3 is
the live one.

## Git state at hand-off

- juniper-ml: `juniper-ml#1881` merged as `83ed4055` (branch
  `perf/pf8-burst-library-attribution-2026-09-10`, auto-deleted on merge). `main` also advanced
  under this session by `db627616` (ml#1880, the ci-budget arc) — the PR was based on it, so no
  sync was needed. This file on its own branch. The session worktree
  `.claude/worktrees/woolly-bubbling-galaxy` is locked and outlives the session — **do NOT remove
  it**; Phase 4 of `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md` requires
  the liveness and in-use probes first and forbids `--force`.
- juniper-cascor: primary at `a51b7c58`, clean, untouched, no holders.
