# HANDOFF 2026-09-22 — the `runtime:` block binds at last, D6's premise was false, and two of my own tests were measuring the workstation

Successor to
[`HANDOFF_2026-09-11_perf-lane-burst-terminator-is-the-result-queue-unpickle-and-the-getter-repins.md`](HANDOFF_2026-09-11_perf-lane-burst-terminator-is-the-result-queue-unpickle-and-the-getter-repins.md).

> **THE PREDECESSOR IS NOT SUPERSEDED — but it has been AMENDED IN PLACE.** This session
> re-probed it and edited it directly: it now carries a `⚠ RE-PROBED 2026-09-22` block, a
> per-decision D1–D6 table, three corrections to what the 09-16 sweep is usually quoted as
> settling, and a retirement of its `--benchmark-compare=0003` recipe. **Read that block before
> anything else in it.** Through it, the 09-10, 09-09 and 09-07 handoffs remain live.
>
> **NOTHING IS RUNNING from this session.** No listener was started and no port bound. The D6
> instrument does create a real candidate pool via `train_detailed`, so check for strays:
> ```bash
> ps -eo pid,etimes,cmd --no-headers | grep -E "[d]6_epochs_completed_spread|[r]un_ci_regression_list"
> ps -eo pid,ppid,etimes,cmd --no-headers | grep -E "[f]orkserver|[s]pawn_main|[r]esource_tracker"
> ```
> **BOTH commands return rows that are NOT yours.** The second catches peers' cascor stacks. The
> **first** catches peers too — `run_ci_regression_list.bash` is §4's own verification command 3,
> so *every reader of this handoff* trips that pattern, and four such rows were running from this
> very worktree at hand-off. Discriminate by `etimes` and by when you started your own run; **do
> not read a hit as a stray to kill.** Checked at hand-off: no child of this session survived.

Documents of record, all on `main`:
[`notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`](../../notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md)
("the D6 note"),
[`notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`](../../notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md)
("the width sweep", now carrying a §2 correction),
[`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`](../../notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md)
("the rulings"),
[`notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md`](../../notes/JUNIPER_2026-09-12_JUNIPER-ECOSYSTEM_PERF-LANE-PF2-RESPECIFICATION.md)
("the PF-2 re-spec"),
[`notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md)
("the P2 plan").

---

## 1. GOAL (paste this into the new thread)

Continue the **juniper-ml performance lane**. `juniper-ml#2002` merged as **`f8ffaa48`**,
implementing owner decision **D2** (the experiment YAML's `runtime:` block now binds) and
discharging **D6** (`epochs_completed` spread is zero, and D6's stated premise is refuted).

**Do not re-ask the owner to RULE D1–D6 — that was done 2026-09-11. But four of the six left an
explicit `Not decided:` clause, and all four are still open.** Do not read "ruled" as "closed":

| | still undecided | where |
|---|---|---|
| **D1** | **which repair mechanism** — training-thread pin vs setting the process default before any BLAS-importing import | rulings `:65` |
| **D2** | **the key's final name**, and whether a **second per-thread knob** is also offered | rulings `:93` |
| **D4** | the exact **cell counts and budgets** — these need the floor/wall calibration, not a guessed number | rulings `:118` |
| **D6** | **whether the gate is BUILT at all.** "This ruling buys the measurement, not the gate." | rulings `:148` |

D2's is the one with a deadline attached: `blas_threads` / `num_processes` / `eval_metrics_enabled`
now have users, so renaming them gets more expensive every week. It is cheap **today** and was
never ratified.

### Work list, in priority order

1. **CUT ONE NEW PF-1 BASELINE — new work that D2 created.** It blocks **PF-1 baseline
   comparisons and nothing else**: `run_suite --compare-baseline` is *"REPORTING ONLY: the
   suite's exit code is unchanged by the verdict"*, PF-3 never compares against a `pf1-*` tag,
   and items 2–7 touch no baseline at all. **Items 3, 4 and 6 need no host time — do them while
   waiting.** (An earlier draft of this handoff said "nothing else can proceed past it"; that
   was false, and it converts "wait for a quiet host" into "do nothing".)

   **ONE run and ONE new tag discharges this, not two.** `pf1-2026-09-04` and
   `pf1-2026-09-04b` are two blessings of *the same five runs* — identical `run_id`s
   (`20260903T040803Z-3439`, …), identical statistics, byte-identical `HOST.json`; `-04b` merely
   adds `work.completion_reason`. `-04b` supersedes `-04`.

   `spiral-smoke.yaml` carries `runtime: {blas_threads: 2}`, which now *binds*, so a fresh
   run records a non-null `thread_budget` while `~/.local/state/juniper-experiments/baselines/pf1-2026-09-04/`
   and `…-09-04b/` both recorded all-null. `thread_budget` is a `HOST_IDENTITY_FIELDS` member
   (`util/experiments/compare_baseline.py`), so every comparison against them now exits 2 with
   `verdict: REFUSED`. **That refusal is CORRECT — the condition genuinely changed — and it is
   not a tooling bug.** Until they are re-cut, any `run_suite --compare-baseline` against them
   writes REFUSED into `REPORT.md`. Needs a quiet host (see item 5).

   The mechanics, so this is executable rather than merely described — run the suite first,
   then bless the run directory it produced:
   ```bash
   python3 util/experiments/run_suite.py --suite util/experiments/suites/perf/pf1-cascor-spiral-repeats.yaml
   python3 util/experiments/make_baseline.py --tag pf1-<YYYY-MM-DD> --suite <SUITE_DIR printed above> --dry-run
   ```
   `make_baseline.py` takes `--tag` (operator-chosen) and a repeatable `--suite` pointing at the
   **suite directory**, not the YAML. **Run `--dry-run` first**: it validates and prints without
   writing, which is the cheap way to confirm the new `thread_budget` is what you expect before
   a baseline is minted under it. Do **not** reach for `--accept-warnings` to make a noisy run
   pass — a baseline blessed over validation warnings records that acceptance in `baseline.json`
   and every later comparison inherits it.

   **The tag MUST be new, and there is no `--force`.** `write_baseline` refuses an existing
   target: *"Baselines are never overwritten or auto-deleted — a superseded baseline is
   superseded BY NAME (§4 of the P1 design). Choose a new tag."* So "re-cut" is a misnomer: you
   are **minting a successor**, not replacing anything. **Do not delete `pf1-2026-09-04*` to make
   room** — supersession is by name, the retention policy forbids deletion, and they are listed
   in §5 as retained state.

   **Decide deliberately whether the new baseline should be capped or uncapped**, and say which
   in the tag: `spiral-smoke.yaml`'s `blas_threads: 2` now binds, so the re-cut captures the
   *capped* regime, while the retired baselines captured the unpinned one. They are not
   interchangeable, and a successor comparing across that boundary would be measuring D2 rather
   than whatever they meant to measure.
2. **PF-3 is unblocked on its axis but NOT ready to launch. Re-shape the matrix first.**
   `util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml` now has a live
   `runtime.num_processes` axis, and its header records the three remaining blockers:
   - **D3's ruling requires a ONE-CELL RUN** proving the cell's `thread_env` is non-null —
     `--only <cell_id>`, then read `thread_env` in that run's `manifest.json`. **NOT
     `--dry-run`**: `run_suite.main` returns before cells are materialised and prints neither
     the runtime env nor the thread budget.
   - **The axis does not discriminate everywhere.** cascor clamps workers to
     `min(process_count, len(tasks))` (`cascade_correlation.py:2685`) where `len(tasks)` IS the
     pool size, so at `candidate_pool_size: 2` the `np=2` and `np=4` legs are the same
     configuration — i.e. **ONE redundant cell, expressed as a pair. Delete one of them, not
     two**, or you remove a real data point. And `np=1` takes the *sequential* branch (`:2473`,
     and only when no remote workers are available), a different code path rather than a
     one-worker pool, so it is not a point on the same speedup curve. Binding the variable was
     necessary, not sufficient.
   - **"Re-shape" is a DECISION this handoff does not make for you.** The three bullets above
     diagnose; they do not specify a target matrix. Drop `np=4` at `pool=2`? Drop `np=1`
     entirely, or keep it as an explicitly-labelled sequential control? Extend to `np=8/16` now
     that the axis binds? Two competent readers ship different suites. **Write the chosen shape
     into the suite header with its reason** before spending ~6.7 h on it.
   - **Cell ids come from `--dry-run`** — it is the only thing that prints them. The "NOT
     `--dry-run`" above applies to the `thread_env` *proof*, not to discovering ids. Note `c000`
     is an `np=1` cell, i.e. the sequential branch; pick a cell on the curve you actually care
     about.
   - A quiet host — or a loaded-host design, see §9.
   - **Its thresholds remain UNRATIFIED** (the suite header says so). Do not read a result
     against a threshold nobody approved.
3. **Put D4's axis 2 to the owner — it is a DECISION, not a calibration.** The PF-2 re-spec §1
   carries a correction: the experiment/driver path fetches from juniper-data, so `MAX_POINTS =
   10000` binds (`juniper_data/generators/spiral/defaults.py:31`). The owner's requested
   250 → 500,000 range is **unreachable on the suite path**. Options: cap at 10,000 (still 40×,
   5× wider than the inert 8×), raise `MAX_POINTS` in juniper-data as its own decision, or run
   outside the suite harness. Axis 3 is already calibrated (viable; **gate on accuracy**, sample
   2,3,4,5 — not 2,6,10). Axis 1 is specifiable now, **but two of the re-spec's obligations are
   easy to drop and each inverts a result if dropped**:
   - **Axis 1 must record `epochs_completed` PER CELL**, not just wall time — a cell that is
     faster per epoch and runs more epochs is *slower*, and a wall-time-only reading reports the
     opposite. Also: `spiral-smoke.yaml` leaves `candidate_epochs` at a constant default, so it
     must be set **explicitly in the base** or every cell silently inherits the fallback.
   - **Axis 2 needs `continue_on_failure: true` and a raised `max_wall_seconds`** — the cell that
     first breaches the wall **is** the measurement, and a suite that aborts on it throws away
     the answer. The breach must be reported explicitly in the aggregate, or the curve flattens
     at the budget rather than at the machine's limit. Calibrate the upper end with a probe
     before committing the sweep.
   - Do **not** conclude "6 spirals is intractable for cascor" from §4.1 — only "unsolved at
     this budget" is supported; `output_epochs: 50` and the candidate budget were never varied.
4. **Commit or retire the 09-17 D6 work — it is uncommitted and only a worktree lock preserves
   it.** `.claude/worktrees/optimized-giggling-koala/` holds
   `util/ad-hoc/2026-09-17_epochs_completed_spread.py` and
   `notes/JUNIPER_2026-09-17_JUNIPER-ECOSYSTEM_PERF-LANE-EPOCHS-COMPLETED-SPREAD.md`, both
   untracked, both reaching this session's D6 conclusion five days earlier. **That worktree is NOT LOCKED — probed, not repeated.**
   `.git/worktrees/optimized-giggling-koala/` contains **no `locked` file**, though ~20 sibling
   worktrees do. The 09-11 handoff asserts it *is* locked; that assertion is **false**, and
   `git worktree remove` deletes untracked files. **Nothing currently protects the only copy of
   that work.** Lock it or rescue the files today.
   **You cannot commit them in place**: the worktree command classifier refuses any cross-worktree
   git redirection (*"a worktree-isolated session's git operations must target its own
   worktree"*). Copy the two files into your own worktree and commit from there.
   Decide: commit them, or
   retire them in favour of `util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py`, which is on
   `main` and adds the ICV-in-force reading and a do-nothing control that the 09-17 one lacks.
5. **Still needs an IDLE host (never taken across SIX sessions): the micro timing cut.** Load at
   hand-off was **9.90 / 18.44 / 12.77**; it hit **54.49** during this session. The gate is a
   1-minute load under 3.
   - **The procedure lives at an ABSOLUTE path, and that matters**:
     `/home/pcalnon/Development/python/Juniper/juniper-cascor/docs/testing/REFERENCE.md`
     § *Micro timing reference*. It is ecosystem-root-relative, so `cat
     juniper-cascor/docs/testing/REFERENCE.md` from this worktree returns *No such file*, while
     juniper-ml ships a `docs/REFERENCE.md` of its own that a bare relative path silently
     resolves to instead. The runnable invocation is the first block of the probe note's §8
     (`notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md`), which
     already uses absolute paths.
   - **`--benchmark-compare=<N>`, NEVER `--benchmark-compare-fail`.** Owner decision 2.5: PF-4
     is **report-only on timing, permanently** (P2 plan `:338`). A tolerance gate is worse than
     useless here — §8.4 measured six competing processes at **+19.9%**, i.e. blind to real
     regressions yet firing on an ordinary loaded host. Cutting a fresh reference does not
     reopen that.
   - **The old compare target is retired**: `--benchmark-compare=0003` cannot
   resolve, because pytest-benchmark keys its store on the interpreter
   (`session.py:45-49` always sets `default_machine_id`; `storage/file.py:30` joins it) and
   `JuniperCascor1` moved 3.13 → 3.14, leaving only `Linux-CPython-3.13-64bit/`. **Cut a fresh
   3.14 reference and say so.** The two-part form `Linux-CPython-3.13-64bit/0003` *does* resolve
   (`file.py:72-77`) — **do not use it**; it compares across interpreter *and* torch versions and
   produces a number that looks comparable and is not.
6. **The cascor thread-pin defect is STILL UNREPAIRED and is still an open owner item.**
   `cascade_correlation.py:1180` calls `torch.set_num_threads(max(2, worker_thread_count * 2))`
   inside `_init_multiprocessing`, binding only the constructing thread. D1 answered the *width*
   question (keep 2; 2–8 indistinguishable); it did **not** repair the defect, and D2's env route
   is a harness-side workaround, not a cascor fix.
   - **Two repair options, both still on the table** (rulings `:65`): pin on the **training
     thread**, or set the **process default before any BLAS-importing import**.
   - **SIZE IT AGAINST ONE PHASE, NOT THE RUN.** The defect costs the **initial output pass
     only** — the training thread is re-pinned to 2 during the first candidate-result
     collection and stays there. It is not a whole-run 16-wide regime.
7. **Carried items — the table below (§8) names where each one's substance lives.** "Optional,
   all unchanged" is not a brief: six distinct items ride here and at least three are not
   recoverable from this document alone. **Read §8 before deciding any of them is unimportant.**

### Do NOT do these

- **Do not cite the width sweep's `−33%`.** Its "initial pass" column sums **every**
  `train_output_layer` stage (cascor emits five per run), so it is total output time. The true
  first-pass benefit is **−49.2%** (2.2838 s → 1.1593 s, medians of 3). Its §2.1 "3.3× gap at
  identical OpenMP width" is an **artifact** of the same contamination — true first passes are
  2.1772 vs 2.0404, within noise. `later_passes_seconds` and `candidate_seconds` are clean, so
  D1 and the cascor#531 non-reproduction stand.
- **Do not treat "cascor#531's penalty does not reproduce" as closed.** Both D1's and D2's gates
  demanded **epoch counts**; the instrument emits **stage** counts and the string `epoch` appears
  in none of the 40 evidence files — though its own docstring claims otherwise. Wall time cannot
  separate *no effect* from *two effects cancelling*, and the rulings' §1 records two channels
  moving oppositely.
- **Do not quote "16 is 5–7× worse" without its mechanism.** That is the `thread` mechanism; on
  the `env` route — the one the owner ruled for — width 16 costs about **1%**. True span across
  both runs is **4.97–7.42×**.
- **Do not say the 09-17 D6 work was lost.** It was never committed. Different failure, different
  fix.
- **Do not read `torch.get_num_threads()` to diagnose a thread-width question** — it re-pins the
  caller. It has now destroyed two measurements in this lane. Use
  `ctypes.CDLL("libgomp.so.1").omp_get_max_threads()`.
- Everything in the predecessor's "Do NOT" list still holds.

---

## 2. What shipped this session

| PR | merged | squash sha | what |
|---|---|---|---|
| `juniper-ml#2002` | 2026-09-22T09:44:49Z | **`f8ffaa48`** | D2 implemented, D6 discharged, the 09-11 handoff amended, three corrections to merged work |

Nine signed commits, all created through the API (local GPG signing hangs headless).
**`f8ffaa48` is an ancestor of `origin/main`** (verified, not asserted); the branch
`perf/d2-runtime-block-binds-and-d6-discharged-2026-09-22` auto-deleted on merge.
`Post-Merge Main Verification` passed on `f8ffaa48`.

`juniper-ml#2002` changed, **by filename**: `util/experiments/run_suite.py`,
`util/experiment_stack.bash`, `tests/test_run_suite.py`, `tests/test_experiment_stack_script.py`,
`util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml`,
`util/experiments/suites/perf/README.md`, `CHANGELOG.md`,
`notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_perf-lane-burst-terminator-is-the-result-queue-unpickle-and-the-getter-repins.md`,
and new: `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`,
`util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py`,
`util/ad-hoc/2026-09-22_run_ci_regression_list.bash`.

---

## 3. Key context — new this session

- **D2's shape.** `run_suite.runtime_block_env` maps `blas_threads` → the three BLAS vars,
  `num_processes` → `CASCOR_NUM_PROCESSES` (**cascor only**; withheld for recurrence, as
  `thread_budget_env` already does), `eval_metrics_enabled` → `JUNIPER_CASCOR_EVAL_METRICS_ENABLED`
  (emit the *word* `false`, never `""` — cascor's `_env_flag` treats blank as the default, which
  is `True`, so an empty string would **invert** the setting). Resolved before the first `--up`,
  so a bad value refuses the suite, not one cell.
- **`null` means CLEAR, not error.** `_set_dotted` cannot delete a key — it *writes* `None` — so
  `matrix: {runtime.blas_threads: [2, null]}` is the only way to express an unpinned cell.
- **Precedence is scoped to intent.** A width the **suite names** (a `runtime.*` dotted override)
  beats the H-11 parallel split; a width merely **inherited** from a base config does not.
  Without that scoping, `spiral-baseline.yaml`'s `num_processes: 4` would silently disarm H-11
  for any parallel cascor suite built on it — 2× oversubscription, invisible because `REPORT.md`
  prints neither budget.
- **The launcher half adds RECORDING, not delivery.** The variables already reached cascor by
  inheritance. What was missing was `env/launch.env` stating the width the service ran at.
  Corollary: because delivery *is* inheritance, `data_up` and `recurrence_up` get them too —
  **`runtime.blas_threads` pins juniper-data's BLAS as well.**
- **D6's answer, and its refuted premise.** 100 observations, **max within-cell spread 0**, every
  budget resolving to one value ({10, 50, 68, 68}), at three load levels spanning 2.8× —
  **19.50, 32.26, 54.49**. D6 was gated on "ambient load moves the count"; load does not, and
  neither does thread width (the mechanism by which load would have had to act). The ICV was
  verified live per cell (w1→1 … w16→16), so this is a real invariance, not an inert axis. **The
  historical `52` is an observation of unknown provenance, not evidence of instability.**
- **Only 2 of 4 cells would be a real gate.** At budgets 10 and 50 the count *equals* the
  request. The emergent behaviour is at 100 and 200, both landing on 68. Scope is **1 of the 5**
  cascor micro files (`test_micro_candidate.py`); the other four are genuinely fixed-count.
- **The D6 note nominates its own REAL open question, and it is not the spread.** The gate's
  reference is **tree-sensitive by construction** — the count is invariant to the runtime
  environment but not to cascor's numerics, which is exactly why it is emergent. So the gate
  will legitimately fire on any cascor change that moves candidate training. Whether that is its
  whole value (it detects silent numeric drift) or its whole cost (it fires on intended changes)
  depends on how often that happens, and **this measurement does not say**.
- **The mapped libgomp changed.** Now `…/lib/python3.14/site-packages/torch/lib/libgomp.so.1`,
  not the conda-env copy the ICV note records. Readings across the 09-12 rebuild are of two
  different libraries.

---

## 4. Verification commands

```bash
git fetch origin && git merge-base --is-ancestor f8ffaa48 origin/main && echo "D2+D6 on main"
python3 -c "import importlib.util;s=importlib.util.spec_from_file_location('r','util/experiments/run_suite.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.runtime_block_env({'runtime':{'blas_threads':2}}))"   # three BLAS vars = '2', NOT {}
python3 -m unittest -q tests.test_run_suite tests.test_experiment_stack_script tests.test_env_repr_safety   # 118 + 92 + 6 = 216 OK
bash util/ad-hoc/2026-09-22_run_ci_regression_list.bash   # 165/166; the duplicati miss is tmpfs, see its caveat 1
/opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py --widths 1 16 --epochs 100 --repeats 2   # control stable, spread 0, 68 at both widths
python3 util/experiments/run_suite.py --suite util/experiments/suites/perf/pf3-cascor-pool-scaling.yaml --dry-run | head -3   # 12 cells, runtime.num_processes varying
ls ~/.local/state/juniper-experiments/baselines/cascor-micro/   # ONLY Linux-CPython-3.13-64bit — item 5
```

**Stop condition for the D6 instrument.** If `control.stable` is `false`, the instrument
perturbed the measurement and **no arm in that run is interpretable**. If
`max_spread_within_cell` is non-zero, the verdict does not hold on that host and the gate
question reopens.

---

## 5. Retained state — do not delete

- Everything in the predecessor's §5.
- `~/.local/state/juniper-experiments/baselines/pf1-2026-09-04/` and `…-09-04b/` — **retained
  even though superseded.** Supersession is BY NAME; `make_baseline` never overwrites or
  auto-deletes, and deleting them to "make room" for a new tag is exactly what the retention
  policy forbids.
- `~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260922/spread.json` — the citable
  D6 run (100 observations, ICV per cell, control before and after).
- `~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260917/spread.json` — the earlier
  run; corroboration only, and see item 4 about its uncommitted instrument.
- `~/.local/state/juniper-experiments/suites/d1-d2-width-sweep-20260917-corrected/` — 40 files,
  the source of the §2 contamination correction.
- `.claude/worktrees/optimized-giggling-koala/` — **LOCKED, do not remove**; holds the only copy
  of the 09-17 D6 instrument and note.

---

## 6. Traps this session paid for

1. **A dev box is HOST-ADVANTAGED, and running more local suites does not fix it.** Two of my
   tests passed here and were vacuous in CI. (a) `check_cascor_parallel_floor` probes upward for
   a **juniper-cascor sibling**; a dev checkout has one, a runner does not, so the suite exited 2
   and the assertions never reached their subject. Pin `JUNIPER_EXP_CASCOR_SRC_DIR` at a tree the
   test builds — the D5 tests in the same file already did. (b) `thread_budget_env` splits on
   `os.cpu_count()`, so a literal `"4"` encodes 16 cores and reads `1` on a 2-core runner —
   **derive** expected values from the function. To flush class (b) locally, monkeypatch
   `os.cpu_count` *before* importing the suite, and confirm the patch actually moves the value or
   the re-run is vacuous.
2. **`open_signed_pr.py` sends WHOLE FILE CONTENTS, and this worktree is 44 files behind `main`.**
   The first commit deleted two `CHANGELOG.md` entries concurrent sessions had landed. Caught by
   diffing the **pushed branch against `origin/main`**, not the local diff. Always check
   `git diff --numstat origin/main...FETCH_HEAD` for unexpected deletions after an API push.
3. **`pre-commit run --files` SKIPS UNTRACKED FILES.** New files pushed via API are untracked
   locally, so Black/flake8/mypy/markdownlint silently reported "no files to check" on them. Run
   the tools directly, or `git add -N` first.
4. **The CI regression list is hand-maintained and includes suites that lint OTHER test files.**
   `tests/test_env_repr_safety.py` forbids raw `os.environ`-derived mappings anywhere under
   `tests/` — no subset chosen from the diff would include it. Use
   `util/ad-hoc/2026-09-22_run_ci_regression_list.bash`.
5. **A hidden directory defeats a "search everywhere" census.** Three sweeps concluded the 09-17
   D6 work did not exist; it was in `.claude/worktrees/…`, which dotfile-skipping idioms miss —
   and two of the three used a pattern taken from the *evidence directory's* name rather than the
   instrument's. Agreement between sweeps sharing a blind spot is not evidence of absence.
6. **The worktree command classifier** refuses compound `cd X && …` chains, heredocs passed to
   `bash -c`, `gh --jq` expressions it cannot parse, **and any cross-worktree git redirection** —
   the last of which is what stops item 4 being done in place. It also refuses a heredoc whose
   *text* merely names such a command, so a `python3` patch script that only *mentions* one is
   rejected too (hit twice while writing this handoff). Split into plain single commands, or put
   the code in a `util/ad-hoc/` file; for another worktree, copy the files across and act in
   your own.
7. **`safe_merge.py` syncs a BEHIND branch and then waits** — read the `MERGED` line, never the
   exit status. It armed an auto-merge net pinned to the pre-sync head and warned that anything
   pushed after arming would be **missing from the squash message**; nothing was pushed, so
   nothing was lost.

---

## 7. What this handoff does NOT cover

The predecessor's §7 and the arcs it names (backup, canopy E2E, defect register, P5, soak,
partition, service-core, container registry) have other owners. **That enumeration is NOT
complete** — the CLI-experimentation arc tail also rides in the predecessor's §8 and is now three
hops behind unnamed pointers; it is listed in §8 above rather than dropped here. Also out of scope but worth
flagging: **`MEMORY.md` is 25.8 KB against its 20 KB target** and grew during this session; it
must be compacted by RETIRING entries, never by stripping hooks, and a concurrent session was
already compacting it — coordinate before editing.

## 8. Carried items — where each one's substance lives

The predecessor wrote this table and prefaced it *"'carried unchanged' is not a brief, and three
of these are not recoverable from the predecessor alone."* That is still true, and the first
draft of this handoff collapsed all six into one sentence with a pointer to a section that does
not exist. Reinstated.

| carried item | where its substance lives | note |
|---|---|---|
| **The three ICV residuals** | the ICV note **§7** — `notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md` | **NOT the width sweep** — it has no §7 and its §5 is a *closed* residual. Detail below |
| **PF-5 / PF-6 / PF-7 never executed** | P2 plan `:337` (item 2.3) | **REPORT-ONLY FOREVER, can never be gated.** Plus the MLP carve-out — detail below |
| **P2 item 4.2's still-open half** | P2 plan `:481` | **D5 removed its blocker and nothing recorded that it became actionable.** A parallel cascor suite may now be committed under `suites/perf/`; *whether PF-8 should get one* is the separate, still-open half |
| **The wall-ordering survey, unapplied to PF-2's new axes** | P2 plan §4, `util/ad-hoc/2026-08-20_wall_ordering_survey.py` | "A timeout is not a measurement." Matters most for axis 2, which **deliberately** raises `max_wall_seconds` and expects breaches. **Trap**: the survey reports `UNRESOLVED` for every sibling-repo `base_config` when run from a session worktree — run it from the primary checkout |
| **P2 item 5.2 — experiment-scoped alerts** | P2 plan `:375` | juniper-deploy, S-sized, the only Wave 5 row without a DONE marker |
| **The CLI-experimentation arc tail** | `HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md` §8; `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-TAIL-REPROBE.md` | Three hops behind unnamed pointers and decaying. Detail below |

**The three ICV residuals, in full** (ICV note §7), because two of them are not reconstructable
from the name alone:

1. **The exact rebuild path inside the worker payload that re-pins.** Localised to the
   `result_queue.get()` that unpickles the first `CandidateTrainingResult`; a plain
   `pickle.loads` of a 64² tensor does **not** reproduce it. Needs a larger / shared-memory-backed
   arm, or an interposer on `omp_set_num_threads`.
2. **Why the re-pin is op-shape dependent** — a one-shot 512² matmul does not re-pin, a sustained
   1500² one does. Untested whether the discriminator is size, duration, or repetition.
3. **The listener has never been measured with this instrument.** Every ICV reading in the arc is
   single-process. `ptrace_scope` is 1 on this host and the arc's standing rule is not to modify
   juniper-cascor, so reading the ICV inside a live listener needs a **new mechanism**.

**The PF-5/6/7 carve-out**, which has been amputated once before and restored: the claim
*"recurrence exposes no work-done counter"* is **false for the MLP readout** —
`_readout_mlp.py:77,150` maintains a real `n_epochs_`. That fact lives **only** in
`HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`; `docs/REFERENCE.md` and
the P2 plan still state the unqualified version. Executing PF-5/6/7 is legitimate; **gating** them
is not — `make_baseline` refuses them deliberately.

**The CLI-experimentation arc tail's highest item** is the **title-repair acceptance gate**:
`util/ad-hoc/2026-08-29_requirements_title_artifact_scan.py --check` still exits 1 with 91
artifacts, and §5 of the re-probe note records that **163 of 172 broken titles were produced BY a
repair pass** — so dropping this is work-destroying rather than merely untidy. Also live there:
`JR-ML-OBS-003` (`notes/requirements/id_assignments.yaml:459`, `status: designed`), R-1's second
clause, F-P4-7, W-12, G-16's refusal half, and the owner's standing rider on the withdrawn 0.5%
threshold.

### Two debts that are currently stated only as prohibitions

A prohibition is not a task, and neither of these will be paid unless someone schedules them:

1. **The D1/D2 gate debt.** Both gates demanded **epoch counts**; the instrument emitted stage
   counts. Until an arm emits `epochs_completed` per phase, "cascor#531's penalty does not
   reproduce" rests on wall time alone and cannot separate *no effect* from *two effects
   cancelling*. **Fix the arm, or record that the question is being left open deliberately.**
2. **"Prose warnings do not bind."** The width sweep's §5 concludes that the
   `torch.get_num_threads()` guard *"belongs inside a shared helper that instruments cannot
   bypass"* — having watched a prose warning fail twice in six days. This handoff's §1 "Do NOT"
   list re-encodes it as **prose a third time**. Build the helper.

## 9. Designing for a LOADED host — the only executable path left

Six sessions have waited for a 1-minute load under 3 and not one has had it. The rulings §3 and
the PF-2 re-spec §5 both say what to do instead, and it has been dropped from every recent
handoff:

> **Interleave or randomise arm ordering, with enough repeats to separate signal from ambient
> drift — or the measurement measures the shell.**

The 09-17 width sweep did exactly this (order reshuffled every repeat from a recorded seed) and
produced usable results at load 4–12. **Structural outcomes are load-insensitive** —
`step_count`, `epochs_completed`, hidden units grown, thread counts, which library, which stage.
**Wall clock is not.** Items 1, 2 and 5 are all wall-clock work; design them for a loaded host
rather than continuing to wait.

## Git state at hand-off

- **juniper-ml**: `origin/main` at `c4a67481`, which contains `f8ffaa48`. The session worktree
  `.claude/worktrees/lively-marinating-truffle` is on branch
  `worktree-lively-marinating-truffle` at `d721fc78` and shows **9 modified + 4 untracked** files.

  > ## ⚠ ONE OF THE FOUR UNTRACKED FILES IS **THIS HANDOFF**, AND IT IS NOT ON `main`
  >
  > `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md`
  > is **genuinely unpushed work** and is **not** in §2's `#2002` file list. **Commit and push it
  > before converging anything.**
  >
  > **Do not merge first.** `git merge origin/main` refuses twice here — once for the modified
  > tracked files (*"Your local changes would be overwritten"*) and once for the untracked ones
  > (*"The following untracked working tree files would be overwritten… Please move or remove
  > them"*) — **and it refuses even when the untracked file is byte-identical to the incoming
  > version.** The reflex answers are both wrong: `git clean -fd` / `rm -r` takes this handoff
  > with the rest, and `git stash` is forbidden in this repo (the stash stack is shared across
  > ~140 worktrees). Safe order:
  >
  > ```bash
  > # 1. push THIS file first — it is the only copy
  > # 2. then discard the 9 tracked files (all identical to main, nothing is lost)
  > git checkout -- .
  > # 3. then remove the three SHIPPED untracked files BY NAME (never `git clean`)
  > rm notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md
  > rm util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py
  > rm util/ad-hoc/2026-09-22_run_ci_regression_list.bash
  > # 4. now converge
  > git merge origin/main
  > ```

  Of the rest, **none is unpushed work** — the API-commit path never touches the local tree, so
  the worktree is *behind* `main`, never ahead. Verified file by file, not assumed:

  | | state vs `origin/main` |
  |---|---|
  | 7 of the 8 modified files, and **3 of the 4** untracked files | **byte-identical** (`git diff origin/main -- <path>` empty; the untracked three confirmed by `md5sum` against `git show origin/main:<path>`, since `git diff` reports an untracked file as a deletion at this stale HEAD) |
  | the 4th untracked file — **this handoff** | **not on `main` at all** — see the block above |
  | **`CHANGELOG.md`** | **BEHIND — and re-pushing it would DELETE A RELEASED SECTION.** |

  > **The `CHANGELOG.md` case, because it is the one that can destroy something.** `main`
  > carries `## [0.9.0] - 2026-09-22`; the local copy does not. `safe_merge.py` refreshed the
  > branch's base before merging (the `BEHIND — refreshing base (cycle 1/3)` line in its
  > receipt), which pulled that release section into the **branch**; the local tree never
  > received that sync and cannot, because nothing writes back to it. A whole-file API push of
  > the local copy — the shape `util/open_signed_pr.py` and
  > `util/ad-hoc/2026-09-08_append_signed_commit.py` both use — would therefore **remove the
  > 0.9.0 release section from `main`.** This is the same clobber class as trap 2 in §6, one
  > cycle later, and it is why "do not re-push" is stated as an instruction rather than an
  > observation.

  **Converge the worktree before doing further work here** (merge `origin/main` into it); do not
  remove it. Re-verify the table above after converging rather than trusting it — `main` moves
  hourly.
- **juniper-cascor**: **RE-PROBE THIS BEFORE ANY MEASUREMENT — it moved during this session.**
  At the time D6 and the width sweep were measured it was on branch `fix/serena-mcp-file` at
  `b35fab1`. **It is now on `main` at `05c13d5`, and `b35fab1` is NO LONGER AN ANCESTOR.**
  - **`candidate_unit/candidate_unit.py` changed (+28/−5)** — `8065ca0`, *"perf(logging): guard
    the three per-epoch sites in `_display_training_progress` (P1.4)"* (cascor#670). That is the
    exact file D6 measures and the one that produces `candidate_seconds`, on which this
    document's "Do NOT" list leans.
  - **Re-verified empirically rather than reasoned about**: the D6 instrument re-run against
    `05c13d5` returns **68 at both budgets and both widths, spread 0, control stable** (load
    12.08). So `epochs_completed` is invariant across cascor#670 as well — which is a small but
    real datum for D6's open tree-sensitivity question (§3). **Wall-clock figures are NOT
    re-verified**; #670 removes ~2,330 ns per epoch per candidate by its own measurement, so any
    `candidate_seconds` comparison across that boundary is measuring #670.
  - `util/experiment_stack.bash:112` launches from `${PROJECT_DIR}/juniper-cascor/src` by
    default, so **every run items 1 and 2 produce will use this changed tree**. Quote the SHA you
    actually ran against; do not write "main" without one.
