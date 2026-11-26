# run_tests: Engine-Extraction Proposal (after two copies)

**Project**: Juniper (ecosystem-wide)
**Owner**: Paul Calnon
**Status**: Proposal for the Overtoad's ruling, 2026-11-26. Nothing in it is built yet.
**Date**: 2026-11-26
**Author**: session c62abc55 (Claude Code), worktree `juniper-ml/.claude/worktrees/floofy-doodling-aho`

---

## 1. What is being decided

The Overtoad ruled on 2026-11-25 at 11:58:05Z: **"Two copies, then decide"**. The ruling is recorded in
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_run-tests-rollout-recurrence-copy-landed-data-client-copy-next.md`.
juniper-recurrence and juniper-data-client each got a standalone copy of juniper-ml's `util/run_tests.py`, and a
concrete proposal for the shared engine comes **before** the other seven repos. Both copies now exist:

| Copy | Lines | PR | State |
|---|---:|---|---|
| juniper-ml (the original) | 2,133 | juniper-ml#2629 | merged 2026-11-24 |
| juniper-recurrence (copy 1) | 2,229 | juniper-recurrence#240 | merged 2026-11-25, `2ce346da` |
| juniper-data-client (copy 2) | 2,533 | juniper-data-client#273 | open, awaiting merge approval |

The question: **the other seven repos get the runner how?**

- juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-harcot;
- juniper-cascor, juniper-canopy, juniper-deploy.

**Recommendation (section 4):** move the engine into juniper-ci-tools as `juniper_ci_tools.run_tests`, released in
ci-tools 0.10.0. Each repo keeps a thin `util/run_tests.py` that declares only what is its own.

## 2. What the two copies showed

All figures were measured on 2026-11-26.

### 2.1 How much is shared, and where it diverges

`util/ad-hoc/2026-11-26_run_tests_function_divergence.py` compares the three copies by top-level unit (each `def`,
`class` and assignment):

- **812 lines are byte-identical in all three**: 44% of juniper-ml's copy, 43% of recurrence's and 37% of
  data-client's.
- Most of the rest differs only at a few hook points. `_main` (230 lines) differs in its checkout check, its header
  line and how it applies `--changed`. `Engine` (130 lines) differs by one branch, the exit codes a step accepts.
  `summarize` differs by its coverage-floor parsing.

`util/ad-hoc/2026-11-25_run_tests_copy_divergence.py` gives the same picture by section, against juniper-ml's original:

| Section | recurrence +/- | data-client +/- |
|---|---:|---:|
| preamble | +37 / -30 | +71 / -37 |
| Reading the workflows | +45 / -10 | +194 / -10 |
| Lanes and jobs | +114 / -56 | +199 / -93 |
| Selection | +24 / -24 | +75 / -47 |
| Environment | +0 / -2 | +0 / -2 |
| Preflight | +1 / -5 | +2 / -6 |
| Planning | **identical** | +33 / -8 |
| Running | **identical** | +12 / -6 |
| Output | identical | identical |
| The command line | +41 / -39 | +70 / -47 |

**The second copy forked the engine itself.** Planning and Running were identical between juniper-ml and recurrence.
data-client's CI made them change, and every change is general, not data-client's own:

- workflow and step `env:` expansion;
- exit codes a step accepts;
- report routing;
- `coverage report --fail-under` as a gate.

### 2.2 Copies drift: two latent bugs, found only by the second copy

Porting copy 2 found two defects that recurrence's copy and juniper-ml's original still carry. Under copying, each is
a separate PR per copy:

- **A `--cov-report=<terminal>:skip-covered` value is rewritten as a file path.** It would become
  `term-missing:<run dir>/skip-covered`. No repo's workflow uses that form today: a census of every repo's
  `origin/main`, run with `--grep`, found none. So the bug is latent.
- **pytest 9's `SUBFAILED(...)` summary lines are not listed among a job's failed tests.** A `subTest` failure is
  counted, but not named in the summary.
- Also, a choice to confirm: recurrence's unittest lane admits a `workflow_dispatch`-only workflow. data-client's
  admits only `pull_request` and `push` workflows, as its docstring always said.

### 2.3 What the next seven need

The 2026-11-24 survey is the table in
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_local-test-runner-follow-ups-landed-cross-repo-run-tests-rollout-next.md`
§ 1. Read against what copy 2 added, it says what the remaining repos need from the engine:

| Repo | Needs beyond copy 2's engine (to be confirmed per repo) |
|---|---|
| juniper-cascor-client, juniper-cascor-worker | nothing: the same `ci.yml` job shape as data-client (unit-tests, integration-tests, security, scheduled). The worker pulls torch |
| juniper-data | its `-m slow` lane treats exit 5 as a failure, which is the engine's default; it uses ruff, not black (irrelevant to the runner); env `JuniperData` |
| juniper-harcot | a contract-tests lane that drives juniper-ml's experiment runner (a cross-repo path); private; env `JuniperHarcot` |
| juniper-cascor | six workflows; package lanes (`ci-cascor-model.yml`, `ci-protocol.yml`, recurrence's shape); long-running and performance lanes, opt-in; six tests fail when `JUNIPER_CASCOR_LOG_DIR` is set (a variable the lane must unset) |
| juniper-canopy | an exit rule of a new kind: CI tolerates SIGABRT 134 when the JUnit report shows 0 failures. A Playwright lane, opt-in. Its existing `util/run_tests.bash` must be reconciled |
| juniper-deploy | its pytest drives live local services (it POSTs to canopy on :8050), so its live modules need to be opt-in, with a preflight port check (`ss`) |

Three of them (cascor, canopy, deploy) add engine features, not just per-repo data. Under copying, each would fork
Planning or Running again.

### 2.4 Every repo already installs juniper-ci-tools

`util/ad-hoc/2026-11-26_run_tests_ci_tools_census.py` read each repo's `origin/main`:

- **All ten repos** install `juniper-ci-tools>=0.9.0,<0.10.0` in at least one workflow, juniper-deploy and
  juniper-harcot included. The 2026-11-25 handoff's "seven of the nine" understated it.
- ci-tools 0.9.1 (on PyPI since 2026-10-10) requires Python `>=3.11`, and every repo's floor is `>=3.11` or higher.
- ci-tools already depends on `PyYAML>=6.0`, the runner's only import outside the standard library.
- Locally, a lane's per-file gate (`juniper-coverage-gap-map`) already needs ci-tools installed.

## 3. Options

### A. Extract the engine into juniper-ci-tools (recommended)

- The engine becomes the `juniper_ci_tools.run_tests` module.
- Each repo's `util/run_tests.py` becomes a thin spec of about 60 to 150 lines: the repo's name, how it finds its
  lanes, its opt-in table, its group and alias names, its help text and where its docs live.
- The engine's fake-checkout suite moves to `juniper-ci-tools/tests/`. Each repo keeps its real-workflow and docs
  tests (about 150 lines), so a workflow change the runner cannot read still fails in that repo's own PR.

### B. Keep copying

- Seven more copies of 2,500 to 2,800 lines each, about 25,000 lines across ten repos.
- Every engine fix becomes ten PRs, and each new need (canopy's 134 rule, deploy's port check) forks the engine
  again.
- A drift guard could compare each copy's shared sections against a canonical copy. But keeping that canonical copy
  is exactly the engine extraction, without the release.

### C. Declarative configuration, no per-repo Python

- A `[tool.juniper-run-tests]` table (or `conf/run_tests.toml`) per repo, and a `juniper-run-tests` console script.
- The three copies find their lanes in structurally different ways:
  - juniper-ml: one CI step's unittest list, plus its package workflows;
  - recurrence: one workflow per package, with `test-*` jobs opt-in;
  - data-client: every job that runs pytest, plus an opt-in table.
- A configuration language expressive enough for all three becomes a small DSL. Option A can still take a declarative
  spec wherever one suffices.

## 4. The recommended design (option A)

### 4.1 The engine: `juniper-ci-tools/juniper_ci_tools/run_tests.py`

- **Start from data-client's copy**, the superset. Make it one module first, moved mechanically, so the extraction
  diff is reviewable; it can be split into submodules later.
- **The engine owns everything shared:**
  - reading workflows (comments, continuations, shlex, `env:` blocks, expansion, the rc-capture rule, events, path
    filters);
  - the Step, Job and Lane records;
  - selection;
  - the child environment and the `TMPDIR` rule;
  - the preflight, planning, running (process groups, timeouts, the re-run alone) and output;
  - `summary.json` (schema 1), the exit codes 0/1/2/3/5/130, and the command line.
- **The engine offers discovery as strategies**, so most repos need no discovery code:
  - `job_lanes(workflows=..., jobs=..., name=..., optional=...)`: every job that runs pytest in the named workflows.
    With `name=job id`, this is data-client's discovery. With `name=workflow stem` and `jobs=["test", "test-*"]`,
    it is recurrence's, and juniper-cascor's package lanes.
  - `unittest_lane()`: every `python3 -m unittest` step of a pull-request workflow (all three copies).
  - `step_lane(workflow, job, step)`: one named step's commands as a lane (juniper-ml's `regression` and `bash`
    lanes).
- **New behaviour lands in the engine once**, behind a spec field, when a repo first needs it:
  - an exit rule of the 134-with-JUnit kind (canopy);
  - variables a lane must unset (cascor);
  - a preflight port check (deploy).

### 4.2 The per-repo surface: a `RepoSpec`

```python
# util/run_tests.py in juniper-data-client, about 60 lines in full
from juniper_ci_tools import run_tests as rt   # ImportError -> print the pip install command, exit 3

SPEC = rt.RepoSpec(
    project="juniper-data-client",                       # the checkout check (pyproject name) and the header
    lanes=[rt.unittest_lane(), rt.job_lanes(workflows=["*.yml"], name=rt.JOB_ID)],
    opt_in={"generator-parity": "needs juniper-data[api] ...", "security": "needs the gitleaks binary ..."},
    aliases=rt.strip_suffix("-tests"),
    docs="docs/REFERENCE.md § Running Tests Locally",
    description=..., epilog=...,                         # --help, which the repo's docs test pins
)

if __name__ == "__main__":
    raise SystemExit(rt.main(SPEC))
```

- `RepoSpec`, the strategy functions and the Lane/Step records are the engine's **public API** and follow SemVer.
  Everything else stays `_`-private.
- `python3 util/run_tests.py` stays each repo's documented entry point, so no repo's docs change command.

### 4.3 Versions and the rollout

1. **Land juniper-data-client#273** (copy 2) as it is: it is the extraction's starting point.
2. **juniper-ml PR: the engine.**
   - `juniper_ci_tools/run_tests.py`, and the merged fake-checkout suite in `juniper-ci-tools/tests/`.
   - ci-tools `0.10.0`: a minor release, because it adds a module and changes nothing else. Its CHANGELOG, and
     `notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md`.
   - juniper-ml's own `util/run_tests.py` becomes a thin spec over the in-repo engine, the canonical home.
3. **The release.** The Overtoad cuts the GitHub Release `juniper-ci-tools-v0.10.0`, which fires
   `publish-ci-tools.yml` (TestPyPI, then PyPI). It is a deploy, and needs its own approval.
4. **Convert the two copies.** juniper-recurrence and juniper-data-client become thin specs, pinned
   `juniper-ci-tools>=0.10.0,<0.11.0` where the runner runs. Each keeps its real-workflow tests, and each conversion
   PR must show the same `--list` and `--dry-run` output before and after.
5. **The seven**, one PR each, in the 2026-11-24 survey's order:
   1. juniper-cascor-client
   2. juniper-cascor-worker
   3. juniper-data
   4. juniper-harcot
   5. juniper-cascor
   6. juniper-canopy
   7. juniper-deploy

   A repo that needs an engine feature first gets it in ci-tools, in a patch or minor release, so a release can
   gate a repo's PR.

### 4.4 Costs and risks

- **A local run needs ci-tools installed.** That is one `pip install`, the same one the per-file gate already
  needs. The thin script prints the exact command, and exits 3 (UNAVAILABLE).
- **The engine becomes an API.** A breaking change needs a minor release and ten pin bumps, which is today's cost for
  every ci-tools change. A fix needs only a patch release: every repo's next `pip install -U` takes it, with no PR in
  any repo. Under copying, a fix is ten PRs.
- **Releases gate rollout steps 3 and 5.** Each needs the Overtoad's approval. Batching engine features per release
  keeps that to a few.
- **The extraction can silently change behaviour.** Step 4 compares each repo's `--list` and `--dry-run` before and
  after. data-client's mutation check (`util/ad-hoc/2026-11-26_run_tests_data_client_mutation_check.py`: 16 of 16
  mutants killed) moves with the engine suite and is re-run there.
- **Rule B is a choice the extraction must confirm.** In data-client's copy, a lane runs only its job's test and
  gate steps; recurrence's and juniper-ml's run every step that needs no shell. The two give the same lanes for
  recurrence, whose test jobs hold only pytest and the gate. juniper-ml's package lanes must be checked when it
  converts in step 2.

## 5. Decisions for the Overtoad

1. **Option A, B or C** for the other seven repos (recommended: A).
2. **Merge approval** for juniper-data-client#273, and for the juniper-ml PR that carries this proposal and this
   arc's scripts.
3. Still open from 2026-11-25: whether juniper-recurrence's `Local test runner suite` (from `ci-tooling.yml`) joins
   ruleset `juniper-recurrent-rules` (id `20634527`) as a required check. data-client needs no such ruling: its
   runner suite runs inside `unit-tests`, which is already required.

## 6. Evidence and scripts

All of these are in juniper-ml, under `util/ad-hoc/`:

- `2026-11-26_run_tests_function_divergence.py`: the per-unit comparison in § 2.1.
- `2026-11-25_run_tests_copy_divergence.py`: the per-section comparison in § 2.1.
- `2026-11-26_run_tests_ci_tools_census.py`: § 2.4, and the `--grep` check in § 2.2.
- `2026-11-26_run_tests_data_client_mutation_check.py`: data-client's 16 mutants.
- `2026-11-26_probe_sequence_safety_screens.py`: runs a sibling's Sequence Safety screens on uncommitted work through
  a throwaway index, so no ref moves. It found both of data-client#273's screens passing before the upload.
