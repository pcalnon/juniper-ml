# V38a/c Investigation Plan — Cascor `grow_network` Returns "Training Results Are None"

**Author:** Paul Calnon
**Date:** 2026-05-02
**Cycle:** Post-V01-V37 alignment closeout (juniper-ml)
**Status:** Investigation plan; no code changes have been applied for V38a/V38c.
**Related findings:** V38b, V38d, V38e (closed in cascor `cd86a90`); V38a/V38c
deferred for this investigation.

---

## 0. Plan

This document captures the investigation plan for V38a/V38c, which surfaced
once the upstream cascor CI gates (V01-V37) cleared and the Unit Tests +
Coverage matrix could finally exercise the deeper layers of the test suite.
The plan has six stages:

1. **Document the existing situation** — failing tests, their fixtures,
   the production call graph they exercise, and the warning emitted in
   the failing path.
2. **Detailed analysis** — trace the flow from `grow_network` down to the
   `best_candidate is None` predicate that aborts growth, and enumerate
   every code path that can produce empty training results.
3. **Suggest options** for each candidate root cause.
4. **Evaluate** each option's strengths, weaknesses, risks, and guard
   rails.
5. **Recommend** a preferred option with reasoning.
6. **Document** the results into this markdown file (notes/), audit and
   validate, and lint the markdown.

The investigation is scoped to V38a/V38c only. V38b/V38d/V38e were already
shipped in cascor `cd86a90` (sched_getaffinity macOS guard, SharedMemory
track= py3.13 guard, spiral_problem.check archived-module guard).

---

## 1. Existing Situation

### 1.1 Failing tests

Run [25251895081](https://github.com/pcalnon/juniper-cascor/actions/runs/25251895081)
on cascor HEAD `af19715` reported the following V38a/V38c failures across all four
unit-test legs (Python 3.12/3.13/3.14 ubuntu + Python 3.12 macos):

| Test | Symptom |
|------|---------|
| `src/tests/unit/test_cascade_correlation_coverage.py::TestNetworkGrowth::test_grow_network_adds_hidden_unit` | `assert 0 == (0 + 1)` — `len(simple_network.hidden_units) == 0` instead of expected `1` after `grow_network()` |
| `src/tests/unit/test_fast_fit.py::TestFastFit::test_fit_executes_full_training_path` | `AssertionError: grow_network should have added exactly 1 hidden unit` (`assert 0 == 1`) |
| `src/tests/unit/test_fast_fit.py::TestFastFit::test_fit_output_weights_grow_after_unit_addition` | `assert 2 == (2 + 1)` — `output_weights.shape[0]` did not grow because no hidden unit was added |
| `src/tests/unit/test_fast_fit.py::TestFastFit::test_fit_multiple_iterations` | `assert 0 == 2` — neither of the two expected hidden units was added |

The captured-stdout for the V38a (`test_grow_network_adds_hidden_unit`)
case showed two warnings emitted from production code:

```text
[WARNING] CascadeCorrelationNetwork: grow_network: Training results are None
          or best candidate is None, stopping growth of the network.
[WARNING] CascadeCorrelationNetwork: grow_network: No validation was performed
          (training loop exited early or did not execute). Iterations
          completed: 0/1.
```

Both warnings come from `src/cascade_correlation/cascade_correlation.py`,
specifically the early-exit path inside `grow_network`'s iteration loop.

### 1.2 Fixtures and inputs

**`test_grow_network_adds_hidden_unit`** (V38a) uses two pytest fixtures from
`src/tests/conftest.py`:

- `simple_network` (line 451) — built from `simple_config` (line 381):
  - `input_size=2`, `output_size=2`
  - `learning_rate=0.1`, `candidate_learning_rate=0.1`
  - `max_hidden_units=2`, `candidate_pool_size=2`
  - `correlation_threshold=0.01`, `patience=1`
  - `candidate_epochs=3`, `output_epochs=3`, `epochs_max=5`

- `simple_2d_data` (line 292):
  - 32 samples (16 per class)
  - Two well-separated 2D Gaussians at `(-1, -1)` and `(+1, +1)`
  - `y` is one-hot `(N, 2)` float

The test prepares the network by calling `train_output_layer(x, y, epochs=3)`
to establish a non-trivial residual error, then calls
`grow_network(x_train=x, y_train=y, max_iterations=1, early_stopping=False)`.

**`test_fit_*`** (V38c) use the local `ultrafast_network` fixture
(`src/tests/unit/test_fast_fit.py:18-33`):

- `input_size=2`, `output_size=2`
- `candidate_pool_size=1`, `candidate_epochs=1`, `output_epochs=1`
- `max_hidden_units=1`, `correlation_threshold=0.0`

with the local `tiny_data` fixture: 8 samples, 2 classes, `torch.randn`
seeded at 42. They invoke `network.fit(x, y, max_epochs=2, max_iterations=1)`
which internally exercises `train_output_layer → grow_network →
train_candidates → _execute_candidate_training → add_unit`.

### 1.3 Production call graph that the failing path traverses

From `src/cascade_correlation/cascade_correlation.py`:

```text
grow_network()                                             # line 3647
└── for iteration in range(max_iterations):
    ├── _calculate_residual_error_safe(x, y)               # line 3697
    └── _get_training_results(x, y, residual_error)        # line 3705 — falsy → break
        └── train_candidates(x, y, residual_error)         # line 3895
            ├── _prepare_candidate_input(x)
            ├── _generate_candidate_tasks(...)
            ├── _calculate_optimal_process_count()
            ├── _execute_candidate_training(tasks, pc, ...)# line 1717
            │   ├── (process_count <= 1 && no remote)
            │   │   └── _execute_sequential_training(tasks)
            │   └── (else)
            │       └── _task_distributor.distribute_and_collect(...)
            └── _process_training_results(results, tasks, …)# line 1744
                ├── if not results: results = _get_dummy_results(...)
                ├── results.sort(key=correlation, reverse=True)
                └── TrainingResults(best_candidate=results[0].candidate, …)
```

The `grow_network` early-exit predicate is at line 3705:

```python
if not (training_results := self._get_training_results(...)) or not training_results.best_candidate:
    self.logger.warning(
        "CascadeCorrelationNetwork: grow_network: "
        "Training results are None or best candidate is None, "
        "stopping growth of the network.")
    break
```

This is the line that is firing in CI.

### 1.4 What "best_candidate is None" can mean

Tracing back through `_process_training_results`
(`cascade_correlation.py:2362`):

- If `results` is **empty**, `_get_dummy_results(len(tasks))` is called
  to fabricate dummies. Each dummy is a `CandidateTrainingResult` with
  only `candidate_id` set — `candidate` defaults to `None` on the
  dataclass.
- After sorting, `results[0].candidate is None`, so
  `TrainingResults.best_candidate is None` and `grow_network`
  short-circuits.

So `best_candidate is None` reduces to `_execute_candidate_training`
returning **an empty list** (or a list whose entries all have
`.candidate is None`).

### 1.5 Why this only surfaced now

Cascor's pytest matrix runs with `--maxfail=5`. The earlier waves of
failures (V11/V20/V24/V29-V33/V35a-V35e/V37a/V37b/V38b/V38d/V38e)
tripped maxfail before pytest even reached `test_cascade_correlation_coverage.py`
or `test_fast_fit.py`. As each upstream gate cleared, the next layer
became visible. V38a/V38c has been latent for an unknown number of
weeks — it's the first time CI runs to far enough to exercise these
tests.

### 1.6 Local reproducibility status

- The `JuniperCascor` conda environment cannot import `torch` locally
  (per `juniper-ml` memory: free-threading Py3.14 ABI mismatch with
  `psutil` C extension, plus a separate torch C-extension issue).
- This means the test cannot currently be reproduced on the
  workstation — only in CI.
- The investigation must be either CI-driven or done on a separate
  machine / container with a working torch.

---

## 2. Detailed Analysis

### 2.1 Approach

The analysis enumerates every code path in `_execute_candidate_training`
and `_execute_sequential_training` (the relevant branch for unit-test
sized inputs) that can result in `_process_training_results` receiving
an empty `results` list, then maps each path to a candidate root cause
for V38a/V38c.

For each candidate root cause, I capture:

1. **Symptom signature** — what the failure looks like in CI logs.
2. **Likelihood** — high/medium/low based on what we already know.
3. **Falsifying signal** — what additional log line or trace would
   confirm or rule out the cause.

### 2.2 Candidate root causes

#### RC-1 — `_execute_sequential_training` itself raises and is silently swallowed

`_execute_candidate_training` wraps its body in `try/except`:

```python
try:
    if process_count <= 1 and not remote_available:
        results = self._execute_sequential_training(tasks)
    else:
        results = self._task_distributor.distribute_and_collect(...)
except CandidateTrainingError:
    raise          # PR #138 / BUG-CC-18: propagate
except Exception as e:
    raise TrainingError(...) from e
```

Both `except` arms re-raise, so a raised exception would propagate up
to `_get_training_results`, which has its own `try/except` that re-raises
as `TrainingError`. `grow_network` does **not** catch `TrainingError`,
so it would bubble out of the test and pytest would report a failure
with the exception traceback — not a warning + `assert 0 == 1`.

⇒ **RC-1 is ruled out by the symptom signature.** The test sees the
warning and an empty `hidden_units` list, not a thrown `TrainingError`.

#### RC-2 — `_execute_sequential_training` returns an empty list silently

If the sequential trainer iterates zero candidates and returns `[]`,
`_process_training_results` enters the `if not results` branch and
fabricates dummies, all of which have `candidate=None`.

This would happen if `tasks` is empty. `tasks` is generated by
`_generate_candidate_tasks(candidate_input, y, residual_error)`. If
`candidate_pool_size == 0` (or the task generator filters all
candidates out), `tasks` would be empty.

For V38a, `candidate_pool_size=2`. For V38c (`ultrafast_network`),
`candidate_pool_size=1`. Neither is zero. So tasks should be
non-empty.

⇒ **RC-2 is unlikely** unless `_generate_candidate_tasks` has a recent
regression that drops tasks. Worth verifying via a `print(len(tasks))`
or a one-line assertion at line 1707 of `cascade_correlation.py`.

#### RC-3 — Each task's training completes but the result has `candidate=None`

`_execute_sequential_training` produces `CandidateTrainingResult`
objects. If every result has `candidate=None` (for example, the
training loop completes but the candidate-selection step writes None
into the dataclass), `_process_training_results` sorts and picks
`results[0]`, which has `candidate=None`.

This could happen if:

- A `CandidateUnit` constructor or `train_step` raises an exception
  inside the per-task try-except block that's narrower than the outer
  exception handler.
- A `nan`/`inf` check on `correlation` causes a candidate to be marked
  invalid and have its `.candidate` attribute cleared.

⇒ **RC-3 is plausible.** This would explain the warning without an
exception bubbling up. Requires inspecting `_execute_sequential_training`
for fields that get nulled on errors.

#### RC-4 — `_calculate_optimal_process_count` returns a value that triggers the multiprocessing path under pytest, which then fails or returns empty

Pytest with multiprocessing under py3.14 free-threading has known
fragility:

- `psutil` ABI mismatch (already worked around in `run_tests.bash` /
  `conftest.py`).
- `multiprocessing.shared_memory.SharedMemory(track=False)` py3.13+
  kwarg (just fixed in V38d via `cd86a90`).

If the multiprocessing path silently empties results when a worker
crashes, V38a/V38c would manifest. The fix in V38d (`cd86a90`)
unblocks the SharedMemory case for py3.12; if there's *another*
multiprocessing fragility the failing tests are exercising, results
could come back empty.

⇒ **RC-4 is plausible** for tests where `_calculate_optimal_process_count`
returns >1. But for the 8-sample / 32-sample synthetic inputs in the
unit tests, the optimizer should select sequential (process_count=1).
The fixtures don't set `CASCOR_NUM_PROCESSES`. The default behaviour
on a 2-core CI runner with `_PROJECT_*_OPTIMAL_PROCESS_COUNT` heuristics
is the open question. Worth instrumenting.

#### RC-5 — `_prepare_candidate_input` returns a degenerate tensor

If `_prepare_candidate_input(x)` returns a zero-sized or all-zero tensor
for the 0-hidden-unit case, downstream candidate training may produce
zero-correlation candidates that are then filtered out as "invalid"
before the final results list is built.

⇒ **RC-5 is unlikely on its own** but interacts with RC-3. The
predicate that filters candidates is at `cascade_correlation.py:2395`:

```python
valid_candidates = [
    r.candidate_id is not None
    and r.candidate_uuid is not None
    and r.correlation is not None
    and r.candidate is not None
    for r in results
]
```

This builds a parallel list but **doesn't drop candidates** — it just
records which are valid. The sort at line 2388 keys on `(r.correlation
is not None, np.abs(r.correlation))` so if every candidate's
correlation is None, the sort is stable but the first entry's
`.candidate` may or may not be None depending on whether candidates
finished training.

#### RC-6 — Test data is too clean / candidate correlation is exactly zero

For V38c's `ultrafast_network` fixture, `correlation_threshold=0.0`
explicitly. So even a candidate with correlation = 0 would pass the
threshold check. But the **adaptive** threshold at `cascade_correlation.py:3714`:

```python
adaptive_threshold = max(1e-6, min(self.correlation_threshold, residual_magnitude * 0.01))
```

clamps to a minimum of `1e-6`. If the candidate's correlation is
**exactly zero** (or nan that gets sorted to the bottom), the
threshold check at line 3716 (`best_correlation < adaptive_threshold`)
would break out of the loop with the *info* log (line 3717), not the
*warning* log (line 3706). So this is a different failure mode.

⇒ **RC-6 is ruled out by log signature** — the warning, not the info,
is what fired.

#### RC-7 — Tests expected the old growth contract (manual unit append)

Per the V38a docstring:

```text
Previously this test faked the growth by manually appending a dict.
Now it calls grow_network() with ultra-minimal parameters so the
real candidate-training and unit-installation paths are exercised.
```

The test was intentionally rewritten in commit `4f9ca14`
(`fix: test quality improvements and documentation (CR-061, CR-063,
CR-073, CR-074, CR-076)`) to call the real growth path. So the test
was, at one point, passing against this code. Something has changed
since then — either in the production code or in the test
environment — to break it.

`git log` on the relevant lines of `cascade_correlation.py` shows
significant churn in PR #141 (Phase 2E topology/correlation work),
PR #138 (Phase 2A data-integrity bugs), PR #117 (root-cause
remediation), and PR #112 (`_compute_hidden_outputs` extraction).
Any of these could have shifted the candidate-training contract in a
way that drops results to an empty list under the test's parameter
budget.

⇒ **RC-7 is the *meta* root cause.** One or more of those refactors
broke the test's assumption about how few candidate-epochs and how
small a candidate-pool the growth path can tolerate. The mechanism
is one of RC-2/RC-3/RC-4 but the **driver** is parameter-budget
drift.

### 2.3 Most likely combined cause

The combination of **RC-3 + RC-7** fits the symptom best:

- The test parameters (`candidate_pool_size=1` or `2`,
  `candidate_epochs=1` or `3`, `output_epochs=1` or `3`) are
  intentionally minimal.
- A recent refactor in `_execute_sequential_training` or
  `_process_training_results` added a stricter validity check that
  treats results with insufficient training (e.g. a candidate that
  saw only 1 epoch and produced `correlation=nan` due to numerical
  underflow) as invalid, returning the candidate with `.candidate=None`.
- The dummy-fallback path then makes `best_candidate=None`, which
  trips the warning.

The deferred warning mentioned in the v38a investigation also points
this way: "No validation was performed (training loop exited early
or did not execute). Iterations completed: 0/1" — the loop never
completed even one iteration, consistent with first-iteration abort.

---

## 3. Options to Address V38a/V38c

The options below are organized by which layer of the stack the fix
touches. Each addresses the most-likely combined cause (RC-3 + RC-7)
but with different trade-offs.

### Option A — Investigate and fix the production regression directly

Reproduce locally (in a torch-capable environment), instrument the
candidate-training path, identify whether the regression is in
`_execute_sequential_training`, `_process_training_results`, or the
candidate-validity logic, and fix the production code.

### Option B — Soften the test parameters

Increase `candidate_pool_size`, `candidate_epochs`, and `output_epochs`
in the failing tests and `simple_config` fixture so candidates have
enough training signal to produce non-degenerate correlations under
the current production code. Keep the production code unchanged.

### Option C — Replace the real-growth tests with pinpointed unit tests

Reduce `test_grow_network_adds_hidden_unit` and the `test_fast_fit`
trio to direct calls of `_add_best_candidate` with a hand-crafted
`CandidateUnit` (similar to the *previous* "fake growth" pattern that
PR #110 / `4f9ca14` removed). Cover the real growth path via the
slow-test matrix or a dedicated soak test, not the fast unit-test
gate.

### Option D — Mark the four tests as `@pytest.mark.skip` / `xfail`

Skip the failing tests with a reason that points at a tracking issue
filed against the synthetic-data growth path.

### Option E — Add an integration-tier sanity test, leave the unit tests as a known-fragile area

Move the four tests into the integration-tier test suite (which
already runs with longer timeouts and richer fixtures) and treat the
unit-tier signal as pure isolation coverage.

---

## 4. Evaluation

### A — Production-side investigation

- **Strengths.** Highest fidelity. Surfaces and fixes any genuine regression
  that is also affecting non-test users. Restores the original PR #110
  testing intent.
- **Weaknesses.** Highest cost: needs a torch-capable environment,
  instrumentation, and possibly a multi-PR fix. Cannot be done from the
  current workstation.
- **Risks.** If the regression is multiprocessing-specific, the local repro
  may not reproduce; debugging may require iterative CI commits.
- **Guard rails.** Add diagnostic logging behind a `CASCOR_GROW_DEBUG=1` env
  so we can iterate via CI without permanent log noise. Pin the diagnostic
  to a feature branch with `--maxfail=99` so we see the full landscape.

### B — Soften test parameters

- **Strengths.** Lowest cost. Tests pass quickly. Preserves the "real
  growth path" intent at the unit-test tier.
- **Weaknesses.** If the underlying production regression is real, this
  masks it. Future users with similarly-minimal parameters will hit the
  same wall. The tests' current minimal parameters were a deliberate
  "ultrafast" choice; loosening them costs CI time.
- **Risks.** Symptom hiding. Could regress over time as parameters drift
  further.
- **Guard rails.** Pair with a code comment citing this finding ID and the
  PR(s) that introduced the parameter sensitivity, so the next person who
  looks at the fixture knows why the numbers are higher.

### C — Replace real-growth tests with pinpointed unit tests

- **Strengths.** Restores the per-stage isolation that the *original*
  coverage tests had pre-PR #110. Decouples unit-test gate from
  candidate-training stochasticity.
- **Weaknesses.** Loses end-to-end coverage of the growth path at the
  unit-test tier. Reverses the PR #110 design decision.
- **Risks.** Could mask future genuine breaks in `grow_network`'s
  integration logic.
- **Guard rails.** Pair with a `slow`-marker integration test that
  exercises the full growth path with realistic parameters; gate the slow
  test on the `scheduled-tests.yml` workflow which already runs nightly.

### D — Skip / xfail the four tests

- **Strengths.** Zero engineering cost. Unblocks CI immediately. Documents
  the issue with a tracking pointer.
- **Weaknesses.** No fix, just deferral. Coverage gate stops measuring
  growth-path integration.
- **Risks.** If the underlying issue is a real regression, it stays latent.
- **Guard rails.** File a GitHub issue with a reproducer, link from the
  `@pytest.mark.skip(reason=...)` decorator, and add a calendar reminder
  (or `/schedule` agent) to revisit.

### E — Move to integration tier

- **Strengths.** Maintains the spirit of PR #110 (real growth path is
  exercised) while moving the gate to a tier that has the time and
  parameters to actually pass.
- **Weaknesses.** Reduces unit-test signal. Integration tier runs less
  frequently.
- **Risks.** Same as D for the period between integration runs.
- **Guard rails.** Tag tests `@pytest.mark.integration` and add them to
  `scheduled-tests.yml`'s slow-integration job. Keep a thin
  `@pytest.mark.unit` test that asserts `grow_network()` returns *some*
  result without asserting unit-count.

### Cross-cutting considerations

- **Free-threading**: cascor's CI matrix includes Python 3.14t. Any
  fix that depends on multiprocessing semantics has to behave
  identically under free-threading. Option A should explicitly
  validate against the 3.14t leg.
- **Macos signal**: the four V38a/c failures all replicate on macos;
  whatever the cause, it is not Linux-only. Options B/C/E need to
  preserve macos coverage.
- **Coverage gate**: cascor enforces an 80% coverage floor. Skipping
  tests (D) lowers the floor; loosening parameters (B) keeps it.
  Moving to integration tier (E) drops the unit-tier coverage but
  likely raises the integration-tier coverage by a similar amount —
  net effect depends on which jobs feed which gate.

---

## 5. Recommendation

### Preferred option: **A (production-side investigation) for the *primary* fix, with E (integration tier) as a fallback**

#### Reasoning

1. **The V22-pattern lesson reinforces this choice.** Every previous
   "looks like a real product issue" deferral in the V01-V37 cycle
   (V11, V13, V14, V19, V20, V22, V24, V27, V28, V29, V31, V33,
   V35a-e, V37a/b, V38b/d/e) turned out, on real investigation, to
   be *config drift* or a *stale fixture* — never a real product
   issue. The V38d guard (`SharedMemory(track=False)` py3.13+) was
   the only fix in the whole tail to genuinely change production
   behaviour. The base-rate prior is therefore that V38a/c is also
   a config-drift / parameter-budget issue rather than a real
   product break, and the fastest way to confirm-or-deny that is
   targeted instrumentation against the real path.

2. **Test parameters are minimal-by-design and document what the
   minimum *should* be.** PR #110 explicitly switched the test from
   a fake-growth manual append to a real-growth call so that the
   "minimum viable" growth invocation has unit-test coverage. If
   that minimum has shifted, the change is itself worth surfacing
   — *somebody* will trip on the new minimum eventually, and a
   silent loosening (Option B) just hides the cliff.

3. **Option E is the safe-harbour landing.** If the investigation
   turns out to need a multi-PR fix or a deeper redesign, moving
   the four tests to the integration tier preserves their
   end-to-end value without blocking the unit-tier gate. Option E
   is reversible — once the production fix lands, the tests can
   migrate back to unit tier.

4. **Options C and D are explicitly discouraged.** C reverses an
   intentional design decision (PR #110) on weak evidence. D loses
   coverage permanently unless paired with a reminder mechanism, and
   the V01-V37 cycle has just demonstrated that "deferred" findings
   accumulate dangerously fast.

#### Concrete next-steps for Option A

1. **Stand up a torch-capable repro environment.** Either:
   - Use the JuniperData or JuniperCanopy conda env (which have
     working torch builds) and `pip install -e ../juniper-cascor`,
     or
   - Spin up a clean Docker container off `juniper-deploy` and run
     `pytest src/tests/unit/test_fast_fit.py -x -vv`.

2. **Instrument `_execute_sequential_training` and
   `_process_training_results`** with debug logs that fire only when
   the env var `CASCOR_GROW_DEBUG=1` is set. Log:
   - `len(tasks)` at entry
   - `len(results)` after sequential training
   - For each result: `(candidate_id, candidate is None,
     correlation)`
   - The `_get_dummy_results` invocation if it triggers

3. **Run the four failing tests with `CASCOR_GROW_DEBUG=1` in CI** on
   a feature branch. Don't merge the diagnostic commit; collect the
   logs from the failed run and revert.

4. **Triage the diagnostic output** against the RC-2 / RC-3 / RC-4
   hypotheses. Apply a targeted fix.

5. **Verify via the same matrix.** If the diagnostic confirms RC-3,
   the fix is most likely a tightened candidate-validity check or a
   numerical-stability guard in `_execute_sequential_training`. If
   the diagnostic confirms RC-2, the fix is in
   `_generate_candidate_tasks`. If the diagnostic confirms RC-4,
   the fix is in the multiprocessing/distributor path or the
   process-count optimizer.

6. **Fall back to E** if the above takes more than two CI cycles
   without convergence. Tag the tests `@pytest.mark.integration`
   and add them to `scheduled-tests.yml`'s slow-integration job.

#### Effort and risk estimate

- **Best case (RC-3 numerical guard + 1-line fix):** ~2 hours of
  CI iteration + 1 PR.
- **Medium case (RC-4 distributor or process-count regression):**
  ~half-day; may need a worker-coordinator audit.
- **Worst case (real product regression in the cascade-correlation
  candidate-training algorithm):** open-ended; fall back to Option E
  and file a tracked issue against the cascade-correlation owner.

#### Decision criteria for falling back to E

Trigger the fallback if:

- Two CI cycles of instrumentation produce inconclusive logs, OR
- The fix touches `>1` file in `src/cascade_correlation/` and is not
  obvious-with-a-traceback, OR
- The behaviour reproduces under very different parameter budgets
  (suggesting the regression is fundamental, not parameter-sensitive).

---

## 6. Audit and Validation

This section validates the document against the user's stated
investigation requirements:

| Requirement | Section | Status |
|-------------|---------|--------|
| Develop a plan for addressing V38a/c | §0 | ✅ |
| Thoroughly document the existing situation for V38a/c | §1 | ✅ — failing tests, fixtures, call graph, warnings, why it surfaced now, local-repro status |
| Perform a detailed analysis of V38a/c, document approach + results | §2 | ✅ — 7 root-cause candidates, falsifying signals, most-likely combined cause |
| Suggest several options to address each element | §3 | ✅ — 5 options spanning production-fix, test-parameter-loosening, test-redesign, skip/xfail, integration-tier migration |
| Evaluate options' strengths/weaknesses/risks/guard rails | §4 | ✅ — table + cross-cutting considerations |
| Recommend a preferred option with justification | §5 | ✅ — Option A primary, Option E fallback, with reasoning grounded in the V22-pattern observation |
| Document results into notes/ | this file | ✅ — `notes/V38_GROW_NETWORK_INVESTIGATION_PLAN_2026-05-02.md` |
| Audit and validate all aspects | this section | ✅ |
| Lint markdown, fix syntax violations | post-write step | runs after this file is saved (see process notes below) |

### Cross-references that should not rot

- The four failing test IDs (§1.1) are stable test names; they will
  rot only if the tests are renamed or deleted.
- The cascade_correlation.py line numbers (§1.3, §2.4) are pinned to
  HEAD `af19715` on cascor. They WILL rot as the file evolves; the
  symbol names (`grow_network`, `_get_training_results`,
  `train_candidates`, `_execute_candidate_training`,
  `_process_training_results`, `_get_dummy_results`,
  `_prepare_candidate_input`) are the durable anchors.
- PR references (#110, #112, #117, #138, #141) are durable.

### Linting

After saving, run:

```bash
markdownlint -c .markdownlint.yaml notes/V38_GROW_NETWORK_INVESTIGATION_PLAN_2026-05-02.md
```

The juniper-ml `.markdownlint.yaml` sets `line-length: 512` and
disables `ol-prefix` — which this document complies with. Long table
rows and prose paragraphs intentionally use long lines for readability.

---

## Appendix A — Commit and PR pointers

- Cascor commits referenced:
  - `af19715` — V35b round-3 + V37 (HEAD when V38a/c was first observed in CI)
  - `cd86a90` — V38b/V38d/V38e fixes (already shipped; not part of this investigation)
  - `4f9ca14` — PR #110: switched the V38a test from fake growth to real growth
  - `eb88cfd` — PR #141: Phase 2E topology/correlation work
  - `4bb0ccc` — PR #138: BUG-CC-18 / ROBUST-01 candidate-training error propagation
  - `369c6df` — PR #117: 6 root-cause remediation
  - `7b99050` — PR #112: `_compute_hidden_outputs` extraction
  - `27ad123` — PR #100: added `test_fast_fit.py`

- CI runs referenced:
  - [25251895081](https://github.com/pcalnon/juniper-cascor/actions/runs/25251895081) — cascor HEAD `af19715`, exposes V38a/V38c/V38b/V38d/V38e
  - [25251743281](https://github.com/pcalnon/canopy/actions/runs/25251743281) — canopy HEAD `8cc72d9`, all unit-test legs green (used as the closeout reference)

- Findings doc:
  `notes/CI_VALIDATION_FINDINGS_2026-04-29.md` (V38 row, status
  "partially fixed" — V38a/V38c carried as deferred).

- Audit doc:
  `notes/CI_ALIGNMENT_AUDIT_2026-04-29.md` (V38a/c noted in cascor
  fleet-table row).

---

## Appendix B — Why this isn't being fixed inline in the V01-V38 alignment cycle

The cascor pipeline now passes Pre-commit, Lockfile Freshness,
Documentation Links, Security Scans (bandit + gitleaks), and Build
Notification on every leg. The Unit Tests + Coverage matrix has 4
failing tests out of 244+; the rest pass. The V01-V37 cycle's
explicit scope was the **CI-pipeline gate** layer (workflow startup,
linters, security, lockfiles, dependency policies), not the
candidate-training algorithm itself.

V38a/V38c is the only deferral in the current cycle that touches the
**model-training layer** rather than the CI-layer. It is therefore
the natural break point: ship the cycle's closeout, and revisit
V38a/V38c as a separate, narrower investigation under Option A above.
