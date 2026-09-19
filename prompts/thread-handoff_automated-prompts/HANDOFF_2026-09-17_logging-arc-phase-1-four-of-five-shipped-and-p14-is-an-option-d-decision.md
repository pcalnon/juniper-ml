# HANDOFF 2026-09-17 — logging arc: Phase 1 four-fifths shipped, and P1.4's second half is an Option D decision, not a wiring chore

Successor to
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_logging-redesign-arc-documents-merged-no-phase-started.md`
(the **predecessor**; every bare "the predecessor" below means that file).

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`).

**A bare "§N" means a section OF this document.** Every reference to another file names it. This
document is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md`.
All dates UTC.

**The arc**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573), still OPEN.
Roadmap of record: `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.
Design of record for P4: `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`.
Recon: `notes/JUNIPER_2026-09-01_JUNIPER-CASCOR_LOGGING-RECON.md`.

**The one thing to hold in mind.** The predecessor handed over an arc blocked on six owner
decisions with no phase started. All six are now ruled and recorded in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`, and Phase 1 is four-fifths
shipped. What remains of Phase 1 is **one half-step, and it is not mechanical**: the owner ruled
P1.4 as "**C — Adopt: fix the levels and wire it to a real call site**". The fix half is done and
checkpointed. The wire half, done the obvious way, **adopts migration-analysis Option D** — and
§11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` says Option D and a
queued P7 writer "**must not be adopted independently**". See §2. Do not treat it as a chore.

---

## 0. Remaining work

### 0.1 P1.4 second half — wire `log_if_enabled`, or rule that it is not wired (BLOCKING Phase 1)

State: the **fix** half is complete, tested and checkpointed on branch
`wip/logging-p14-adopt-logging-utils` in `juniper-cascor` (§6). No PR is open. The **wire** half
is not started, and §2 argues it needs an owner ruling first.

Steps, in order:

1. Read §2 and decide whether to put the Option D question to the owner. Recommended: yes, as a
   short interactive question with the measurement in hand — the same shape the owner accepted for
   decisions 5 and 6.
2. Measure before wiring. Write `util/ad-hoc/2026-09-17_p14_guard_idiom_bench.py` comparing, at
   both a disabled and an enabled configured level, against the **real** cascor `Logger`:
   (a) today's unguarded `self.logger.verbose(f"…")`; (b) the hand-rolled hoisted guard
   `if _log_verbose:`; (c) `log_if_enabled(self.logger, Logger.VERBOSE, lambda: f"…")`.
   The interesting number is (c) − (b) at the **disabled** level, which is the per-call closure
   allocation §11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` warns
   about at ~872 suppressed sites. My prior is that (c) loses to (b) on speed and wins on
   correctness; do not ship the claim without the number.
3. The adoption target, already located: `CandidateUnit._display_training_progress`
   (`src/candidate_unit/candidate_unit.py:728`). It is the innermost per-epoch loop and holds
   **three unguarded log calls evaluated on every epoch of every candidate regardless of level** —
   `debug` at `:730` and `:731`, `verbose` at `:742`. (Two further `debug` calls at `:734`/`:735`
   sit inside a rare re-initialisation branch; the `info` at `:740` is already frequency-gated.)
   Its sibling `_tensor_brief` (`:702`) already carries the measured evidence that f-string
   interpolation of tensors in this loop cost ~33 % of candidate-worker self time.
4. Then: lint with the **pinned** tools (§5.3), open the PR from the existing branch, merge.
   Merge approval is granted for this arc (§4).

### 0.2 Close out P1.4's bookkeeping

- Commit the P1.4 probes to `juniper-ml` under `util/ad-hoc/` (the pattern followed after P1.1,
  P1.2 and P1.3 — the latter two landed as juniper-ml#1948). At handoff time **no P1.4 probe
  exists yet**; the benchmark in 0.1 step 2 will be the first. P1.5 needed none.
- Record the **P7 Option D foreclosure** as a decision in §13.1 of
  `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`, whichever way it goes.
  §11 of that file names the conflict but nothing records a ruling on it.

### 0.3 P6.4 — still open, owner has seen the evidence and not ruled

Decision 6 in §13.1 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`
authorised P6.1–P6.3 and held P6.4. The owner asked for and received sample affected lines
(2026-09-09, from `util/ad-hoc/2026-09-09_p64_fstring_classify.py` in `juniper-ml`) and has not
ruled on the 507 mechanical `{name}` conversions. **Do not start P6.4.** Re-ask when convenient.

### 0.4 P0.1 / P0.2 — the post-merge corpus, which gates P2 and P3

Unstarted, and on the critical path: decision 1 in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` pre-authorised a **10 %**
threshold — below it P2 is cancelled and recorded as cancelled. Nothing can measure that threshold
until the corpus is re-baselined after the four merged Phase 1 PRs. §3.1 of that file carries the
standing caveat that P0.2 must not promise the construction cost of discarded records.

### 0.5 `JuniperCascor1` environment repair — owner has not ruled, asked 3+ times

See §5.1. Do not re-ask a fourth time unprompted; state the workaround and move on.

---

## 1. Verify starting state

```bash
# juniper-cascor — main must be clean except .serena/project.yml (not ours; serena MCP writes it)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git status --short && git log --oneline -5
git log --oneline -1 origin/wip/logging-p14-adopt-logging-utils   # expect 1b918e6

# the four merged Phase 1 PRs
gh pr view 644 --json state,title; gh pr view 648 --json state,title
gh pr view 652 --json state,title; gh pr view 653 --json state,title

# the P1.4 work in progress, restored onto a worktree (do NOT edit main)
git worktree add \
  ../worktrees/juniper-cascor--wip--logging-p14--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD) \
  wip/logging-p14-adopt-logging-utils

# run the P1.4 suites (see §5.1 for why the private venv and the env -u)
env -u LD_LIBRARY_PATH -u LIBTORCH JUNIPER_CASCOR_LOG_DIR=/tmp/claude-1000/p14logs \
  /tmp/claude-1000/cascorenv/bin/python -m pytest \
  src/tests/unit/test_logging_utils_extended.py src/tests/unit/test_profiling_module.py \
  -p no:cacheprovider --timeout=120        # expect 47 passed
```

If `/tmp/claude-1000/cascorenv` is gone — `/tmp` is tmpfs and a reboot reaps it (memory
`reference_tmp_is_tmpfs_reboot_kills_the_isolated_stack`) — rebuild it per §5.1.

---

## 2. The P1.4 decision the next session must not skip

The owner ruled P1.4 as **C — Adopt: fix the levels and wire it to a real call site**. The obvious
wiring is:

```python
log_if_enabled(self.logger, Logger.VERBOSE, lambda: f"… Residual Error: Shape: {residual_error.shape} …")
```

**That lambda is Option D.** §11 of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`
records the conflict precisely: lazy message callables and a deferred/queued P7 writer are mutually
unsafe, because a closure captures by reference and a message evaluated after the fact can render a
**different value** than it would have at the call site. Adopting one forecloses the other. It also
names two further constraints: a lambda that raises must not take down a training run, so it needs
its own swallow-path; and it allocates a closure per call **even when suppressed**, at ~872 live
suppressed Path-A sites.

Three ways out, and the choice is the owner's:

- **Wire it as written, and record P7's queued writer as foreclosed.** Honest, cheap, and it makes
  `src/profiling/logging_utils.py` live code. Costs a closure per suppressed call at the site.
- **Wire only the non-lazy helpers** (`SampledLogger`, `log_timing`) and leave `log_if_enabled`
  fixed-but-unwired. Satisfies "wire it to a real call site" without taking the Option D decision.
  This was my stated intention before the conflict surfaced, and it is the narrower reading.
- **Convert the three sites to the hoisted-guard idiom instead** and rule P1.4 as "fix, do not
  wire". This contradicts the letter of ruling C and should only be proposed with the benchmark.

My recommendation: take option 2 to the owner alongside the benchmark from §0.1 step 2, because it
is the only one that discharges the ruling without spending a decision that belongs to P7.

The countervailing argument, which is real: the hand-rolled guard states the level **twice** —
`_log_verbose = isEnabledFor(8)` next to `self.logger.verbose(...)` — and in this very file that
two-place statement was **wrong in two of three cases** before P1.3 fixed it (`8` is not a level at
all; `5` is VERBOSE's number, not TRACE's). `log_if_enabled` states the level once and cannot
drift. That is the strongest case for wiring it, and it is a correctness argument, not a
performance one.

---

## 3. What this session did

Four PRs merged to `juniper-cascor`, all of Phase 1 except P1.4:

| PR | step | what it fixed |
| --- | --- | --- |
| **#644** | P1.1 | `set_level()` was a **no-op for emission**. `isEnabledFor` read `_log_level`; `_log_at_level`'s filter read `_level_logger_config`/`_level_logger_name`, assigned once in the class body and never written again. One configured level, two readers. Also fixed `is_valid_level`'s `level == level` typo, which returned `True` for `None` and `"BANANA"` alike. New `src/tests/unit/test_logger_level_state_reconciliation.py`, 9 tests |
| **#648** | P1.2 | Three numeric level tables became one. `logger.py`'s duplicate is now **derived** (`_level_numbers = dict(_LOGGER_LOG_LEVEL_NUMBERS_DICT)` — a copy, not an alias); `src/profiling/logging_utils.py`'s contradicting `TRACE = 5, VERBOSE = 15` was **deleted**; eight symbolic constants `Logger.TRACE … Logger.FATAL` exported without colliding with the `_level_trace = "TRACE"` string attributes |
| **#652** | P1.3 | The 8 `isEnabledFor` guard sites in `src/candidate_unit/candidate_unit.py` stop naming integers. Output-neutral, proven by arithmetic over the real table. **Also added the eight constants to `juniper-cascor-model/log_config/logger/logger.py`** — see §5.2, this was a near-miss |
| **#653** | P1.5 | `src/tests/unit/test_logger_per_level_exercise.py`, 4 tests / 8 subtests, the first test that reaches the guard sites once per level. Includes an explicitly anti-vacuous `test_trace_actually_emits_at_trace` |

Plus **#647**, which is not a Phase 1 step but was found while writing them: **146 unit tests
across 15 files never ran in CI**. CI selects with `pytest -m "unit and not slow"` and those files
carried no marker, so they were silently deselected. (I got this count wrong twice by grepping —
grep counts *files*, and it missed `src/tests/unit/api/`'s 41 tests entirely. 146/15 is the
verified figure.)

And **#654**, the open-PR budget alarm ported from `juniper-ml` — unrelated to this arc.

**Changed** in `juniper-ml` this session: `util/ad-hoc/2026-09-11_p11_level_constants_probe.py`,
`util/ad-hoc/2026-09-11_p11_setlevel_blast_radius.py`,
`util/ad-hoc/2026-09-11_p11_verify_patched_logger.py`,
`util/ad-hoc/2026-09-11_p11_run_regression_test.py`,
`util/ad-hoc/2026-09-11_cascor_unit_marker_gap.py`,
`util/ad-hoc/2026-09-11_cascor_add_unit_markers.py`,
`util/ad-hoc/2026-09-12_p12_level_table_equivalence.py`, `util/ad-hoc/2026-09-12_p12_verify.py`,
`util/ad-hoc/2026-09-15_p13_guard_integer_audit.py`,
`util/ad-hoc/2026-09-15_p13_verify_both_trees.py` (all merged, latterly by juniper-ml#1948); and
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` §13.1, which now carries all
seven rulings, and `notes/JUNIPER_2026-09-09_JUNIPER-CASCOR_LOGGING-PER-LOGGER-LEVELS-DESIGN.md`
§9.1–§11, which carries the A2-bind ruling, its measurement and the implementation design. This
handoff adds
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md`.

---

## 4. Owner rulings taken this session

All are recorded canonically in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`. Do not re-litigate them.

1. **Merge approval granted for all PRs this session and this work arc.** I still showed each PR
   before merging; keep doing that.
2. **Decision 5 → A2-bind with a `_default` setter.** Nine public attributes become class
   attributes bound to a default `BoundLogger`; `Logger._default = X` is a **data descriptor on
   the metaclass** (a plain `property` on the class only intercepts *instance* assignment) that
   rebinds all nine. Measured faster than the status quo at every call site. The A2 **delegator**
   form was measured and rejected at **+146 ns** — my own estimate for it was +45 ns, i.e. 3×
   wrong, so measure rather than estimate here. Nothing lands until P1.1, which is now shipped.
3. **Decision 6 → P6.1–P6.3 authorised, P6.4 held** (§0.3).
4. **P1.4 → option C, adopt** — the ruling §2 is about.

---

## 5. Traps

### 5.1 `JuniperCascor1` is broken and the owner has not ruled

The env moved Python 3.13.13 → **3.14.7**; torch 2.11.0 exists only under
`lib/python3.13/site-packages` and the 3.13 binary is gone. Separately
`LD_LIBRARY_PATH=…/rust_mudgeon/juniper/libs/libtorch/lib` shadows torch's own libs, and that
`libtorch_python.so` needs `_PyObject_NextNotImplemented`, **removed in Python 3.14**.
`Juniper/CLAUDE.md` still documents the env as 3.13.13 and is wrong. Workaround in use all
session: a private venv `/tmp/claude-1000/cascorenv` with `torch==2.14.0+cpu`, run with
`env -u LD_LIBRARY_PATH -u LIBTORCH`. Rebuild it if `/tmp` was reaped. Related memories:
`project_juniper_cascor_torch_env_broken`, `project_canopy_libtorch_python_collision_2026-05-07`.

### 5.2 The byte-gate mirrors the CALLER; nothing mirrors the CALLEE

`_EXTRACTED_DIRS` covers `candidate_unit`, `utils`, `log_config`, `cascor_constants` — but
`log_config/logger/logger.py` is on `_INTENTIONAL_DIVERGENCE` and is **not** byte-compared, and
there is a *reverse* guard asserting the copies DIFFER. So P1.3's mirrored `candidate_unit.py`
would have shipped `Logger.DEBUG` against a package logger that does not define it —
`AttributeError` on **every candidate construction**, in a package that is live on PyPI, while
`src/` stayed perfectly green. `util/ad-hoc/2026-09-15_p13_verify_both_trees.py` in `juniper-ml`
demonstrates the hazard negatively and now reports it CLOSED. Decision 4 in §13.1 of
`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` is to **converge** the two
trees and retire `_INTENTIONAL_DIVERGENCE` — that work is not started. Memory:
`reference_cascor_model_verbatim_extraction_drift`.

### 5.3 Lint with the PINNED tools, not the local ones

Local `black` is 26.5.1; the repo pins **25.1.0**, and the two disagree about two files in this
change set — I nearly shipped the churn. A venv at `/tmp/claude-1000/lintenv` carries
`black==25.1.0` and `flake8==7.1.1` plus plugins. Also: run `isort` with `--settings-path <repo>`
— run from a staging directory it loses `known_first_party` and merges the `pytest` and
`log_config` import groups.

### 5.4 A staging tree without `__init__.py` measures the file you did not patch

Cost me two probe runs (P1.2 and P1.3). The package resolves to the real checkout and the probe
reports on the unpatched file while looking like it worked. Related: `sys.path.insert(0, p)` in a
**loop** puts the LAST path first — use `sys.path[:0] = paths`. Both fixes are in
`util/ad-hoc/2026-09-15_p13_verify_both_trees.py`, which documents them in comments.

### 5.5 A probe must not reconstruct the code under test

The first `util/ad-hoc/2026-09-11_p11_verify_patched_logger.py` computed the **patched**
expression itself, so the baseline showed zero splits and the defect looked absent. Drive the real
function and capture its output. Its own guard caught this; keep that guard. Memory:
`reference_instrument_answers_an_adjacent_question`.

### 5.6 A MagicMock logger is where this class of defect hides

All five `logger.log(level, msg)` sites in `src/profiling/logging_utils.py` raised
`TypeError: Logger.log() missing 1 required positional argument: 'msg'` against the real logger —
cascor binds the **class** (`self.logger = Logger`, `src/candidate_unit/candidate_unit.py:187`),
so `10` binds to `self`. 31 tests at full line coverage never saw it because they inject mocks.
The new `TestAgainstRealLoggers` drives real objects. **Mutation-check every new "it works with
the real thing" test**: my first draft of `test_log_if_enabled_works_with_the_cascor_logger_CLASS`
passed against the broken code because `isEnabledFor(INFO)` happened to be False. After
strengthening it, the mutation (reverting `_emit` to a bare `logger.log`) fails 4 of 4
cascor-Logger tests, and the stdlib-fallback test correctly passes — `logger.log(level, msg)` *is*
right for a stdlib logger. Memories: `reference_vacuous_pass_check_class`,
`reference_mutation_check_stale_pyc_and_piped_exit`.

### 5.7 `gh` is 2.46.0

`gh pr checks --json` **does not exist** and **all** `gh pr edit` flags are broken. Use
`util/wait_for_checks.py`; edit PR bodies through the API. I hand-rolled a Monitor loop against
`gh pr checks --json`, fed jq an error string, and spun **50 minutes** — this was trap 7 in the
predecessor handoff and I walked into it anyway. Memories: `reference_ci_wait_for_checks`,
`reference_gh_246_breaks_all_pr_edit`.

### 5.8 Signing and rate limits

Local commit signing **hangs** headless (YubiKey touch). Land commits via the GitHub API —
`util/open_signed_pr.py` for branch+commit+PR, `util/ad-hoc/push_signed_commit.py` for a follow-up
on an existing branch (both send **whole files**: sync first). The WIP checkpoint on
`wip/logging-p14-adopt-logging-utils` was made with `--no-gpg-sign` deliberately — it is a
*backup*, not a mergeable commit; re-land its content through `util/open_signed_pr.py`. Separately,
GitHub's **secondary** rate limit rejects mutations while `gh api rate_limit` still reports
5000/5000; it once left a branch created with no commit on it, recovered with
`util/ad-hoc/push_signed_commit.py`. Memories:
`reference_headless_commit_signing_hangs_use_api_commits`,
`reference_open_signed_pr_whole_file_clobber`.

### 5.9 Two smaller ones

- `git grep -E` does not support `(?:…)` and returns an empty file list rather than an error.
- `str.format()` on a template containing f-string braces raises `KeyError`. Use
  `str.replace("@@SRC@@", …)`, as the probes in `juniper-ml/util/ad-hoc/` do.

---

## 6. Git status

**juniper-cascor** — `/home/pcalnon/Development/python/Juniper/juniper-cascor`

- Branch `main` at `70d5ca1`, up to date with origin. Working tree clean **except**
  `.serena/project.yml`, which was already modified when this session started and is written by
  the serena MCP tooling — **not ours, leave it**.
- Branch `wip/logging-p14-adopt-logging-utils` at `1b918e6`, pushed to origin. One unsigned WIP
  commit carrying the three P1.4 files: `src/profiling/logging_utils.py`,
  `src/tests/unit/test_logging_utils_extended.py`, `src/tests/unit/test_profiling_module.py`.
  **No PR is open for it.** Its commit message carries the full done/not-done inventory.
- This session edited `main` directly as a staging area and then checkpointed onto the branch. Do
  not repeat that — use a worktree (`Juniper/CLAUDE.md` § Worktree Procedures), as §1 shows.

**juniper-ml** — worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/luminous-shimmying-crab`

- Branch `main` at `b9862984` (`chore(util): the four probes behind P1.2 and P1.3 (#1948)`).
  Working tree clean apart from this document, which is new and uncommitted.

**Scratch that will not survive a reboot**: `/tmp/claude-1000/p14/` (staging copies, including
`logging_utils.GOOD.py` and `logging_utils.MUTANT.py`), `/tmp/claude-1000/cascorenv`,
`/tmp/claude-1000/lintenv`. The branch in `juniper-cascor` is the durable copy of the only content
that matters.

---

## 7. Corrections this session made to its own work

Listed because each is a claim a successor might otherwise inherit:

- **"12 files / 156 tests"** for the marker gap was wrong twice. Truth: **146 tests / 15 files**.
  Grep counts files, not tests; it missed `src/tests/unit/api/` entirely; and it conflated 10
  deliberate `slow` exclusions. Corrected in the PR body, the source comment and memory.
- **"P1.2 removed the third contradicting table"** was half true when I first said it. The named
  constants went, but the wrong numbers survived **inline** at `src/profiling/logging_utils.py:90`
  (`5`) and `:94` (`15`) with two tests pinning them. Both are now fixed on the P1.4 branch.
- **The A2 delegator estimate was 3× low** (+45 ns estimated, +146 ns measured). Recorded in §13.1
  of `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`.
