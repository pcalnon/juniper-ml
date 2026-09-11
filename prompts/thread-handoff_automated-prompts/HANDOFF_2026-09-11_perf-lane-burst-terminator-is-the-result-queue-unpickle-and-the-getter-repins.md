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

1. **Six owner decisions are open — put them to the owner; do NOT take them yourself.** Unchanged
   in substance from the predecessor's §1 item 1. One is better informed:
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
   which already uses absolute paths. `0003` stays the recommended compare target;
   `--benchmark-compare=0003`, never `--benchmark-compare-fail`.
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
python3 -m unittest -q tests/test_pf8_icv_checkpoint_probe.py tests/test_pf8_burst_attribution.py tests/test_pf8_occupancy_probe.py tests/test_ci_test_wiring_drift.py   # 18 + 14 + 26 + 11 = 69 OK
python3 util/ad-hoc/2026-09-11_icv_trace_align.py --json ~/.local/state/juniper-experiments/suites/pf8-icv-checkpoint-20260911/growth.json   # (a) REFUTED, (b) SUPPORTED, re-pin inside _validate_training_result
python3 util/ad-hoc/2026-09-10_agents_md_test_list_drift.py   # 165 / 165 / 165, zero drift
ls ~/.local/state/juniper-experiments/suites/pf8-icv-checkpoint-20260911/   # 4 evidence files
ps -eo pid,cmd | grep "[/]juniper-cascor/src"   # empty: no holder on the cascor primary
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main   # cc0d1630..., NOT a51b7c58
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
