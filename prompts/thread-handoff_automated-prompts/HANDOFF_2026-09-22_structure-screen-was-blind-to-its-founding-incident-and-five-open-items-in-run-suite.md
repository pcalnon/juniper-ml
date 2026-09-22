# HANDOFF — The structure screen was blind to its founding incident, and five open items in `util/experiments/`

**Date**: 2026-09-22
**Session**: `1202f4c2-c2e6-4e37-828d-db9b061f63a0` (`https://claude.ai/code/session_01Ew6dQC9sU4y7CtaCCaxYtB`)
**Worktree**: `juniper-ml/.claude/worktrees/gentle-kindling-pascal`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`

---

## 1. Goal statement for the next thread

```text
The cursor-fleet round-2 arc's two standing items are DISCHARGED. Neither closed the
way its handoff expected, and the arc's through-line -- every headline number measures
the INSTRUMENT, not the tree -- held three more times. Three PRs merged today:
ml#2000, ml#2001, ml#2010. There is no queued work from that arc.

What is OPEN is a different arc, in util/experiments/: five findings, all verified
against the real tree or the live run corpus, none of them a falsy guard. Item 2 is
the one to start from, and items 2 and 4 must be fixed in the SAME PR as the guards
they silently protect.

THE HEADLINE FROM TODAY, because it governs how you read any "zero" in this repo:

  ml#1944 narrowed the markdown structure screen to clear 17 false positives. The 17
  WERE false positives -- that half was right. Its SAFETY argument was not, and its
  stated premise is checkably false: it says "ml#1746's own fence was bare", while
  ml#1749's repair commit (7a4b1cb4) records the lost line as "the close of the `text`
  block at REFERENCE.md:1522" -- TYPED, the exact class the narrowing exempts.
  Measured on the real damaged blob bcc89c45:docs/REFERENCE.md --

    pre-narrowing screen  2 findings, exit 1
    narrowed screen       0 findings, exit 0   <- blind to its own founding incident
    after ml#2000         2 findings, exit 1

  util/markdown_structure_delta.py execs that screen inside `Documentation Links`, a
  REQUIRED status check, so ml#1746-class damage would have shipped with every check
  green. ml#1955 (2026-09-17) independently hit this and wrote that "the REQUIRED gate
  cannot see it". The ml#1944 trade-off was FALSE: ml#2000 detects ml#1746 again AND
  the tree still screens ZERO. Both were available at once.

OPEN WORK -- all in util/experiments/, all verified this session. Mechanism,
evidence and the traps in each fix are in SECTION 8; these are the summaries.

1. `run_suite.py` `_headline_metrics` CAN NEVER MATCH, and never has. It reads six
   metric names off the TOP of stats["cascor"] / stats["recurrence"]; build_stats
   nests them under `final` / `eval_scalars` / `final_metrics`. 413 real stats.json
   yield ZERO metrics, 107 real aggregate.csv have ZERO metric columns, 418 registry
   rows have ZERO non-empty `metrics`. DO NOT "fix" it by unwrapping one level: four
   of the six names exist at NO depth in the corpus. Its three companion guards are
   NOT vacuous and the fix does not endanger them -- the reason to do both in one PR
   is that ZERO tests exercise those columns. (§8.1)

2. `run_suite.py` `expand_cells` raises RAW exceptions on operator-typeable YAML,
   exiting 1 where its own docstring contract says 2 -- colliding with the documented
   meaning of 1, "suite completed with failed cells". Four shapes reproduce; `matrix:`
   and `exclude:` exit 2 cleanly, which is the contrast that makes it a defect. (§8.2)

3. `_emit_stats` (run_experiment.py:1166-1186) fails SILENTLY: it sets
   manifest["stats_error"], never changes the exit code, and nothing reads the receipt
   -- no gate, no CI, and both tests pin only the happy path. It loses exactly
   stats.json and summary.md on a completed run. (§8.3)

4. `stats_summary.py`:238-239 copies eval_aggregate / eval_std VERBATIM from the
   crossval response and :329 reads them bare -- while `plots_recurrence.py` guards
   THE SAME TWO KEYS from THE SAME payload in THE SAME run. This is local
   inconsistency, not a cross-repo dependency, and its cost is item 3's silent
   class. (§8.4)

5. `stats_summary.py`:340's `present` fallback is production-unreachable but
   TEST-PINNED -- **do not delete it.** The item is the latent coupling it reveals:
   add the disk re-render tool it implies and every guard validated safe this session
   becomes live at once. (§8.5)

Key context:
- DO NOT SWEEP the remaining falsy guards. Two batches have been taken on IN-FILE
  EVIDENCE (ml#1914's six, ml#2001's five), never by count.
  util/ad-hoc/2026-09-22_falsy_guard_next_batch.py implements that bar, and what it
  currently SELECTS is small: `same-key` 9, of which 7 are run_suite's `doc` behind
  load_suite's LOAD-TIME GATE and need nothing. The two genuine candidates are
  util/experiments/run_experiment.py:397 (`_mapping(payload.get('data')).get('result')
  or []`, precedent at :1816) and util/experiments/stats_summary.py:274
  (`dataset = stats.get('dataset') or {}`, precedent at :125), plus a `helper` tier of 2.
  >> TAKE A FLOOR FROM ONE TOOL, NEVER BY ADDING ACROSS TWO. next_batch reports 75
  guards / 18 files on its criterion (non-ad-hoc); the triage's --blind-spot arm reports
  73 + 7 = 80 on ITS OWN. They differ by two guards
  (util/release_train/propose.py:918 and :1070) because the criteria differ. An earlier
  draft of this handoff wrote "82" by adding next_batch's 75 to triage's 7 -- the
  matching-criteria error the predecessor's own §2a warns about, one paragraph below
  where it warns about it.
- ROWS AND GUARDS MUST COME FROM THE SAME RUN. The census emits one row per USE; the
  unit of repair is the GUARD. Adding figures from two runs is the error ml#2010 fixed
  in HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-
  instrument-artifacts.md -- committed inside the document that explains it, and again
  in the first draft of THIS one (see the floor note above).
- THE REFUSAL IS THE RECEIPT. Several tools from this arc now REFUSE on a repaired
  tree -- the seq-safety patcher, the row restorer, the relocation script, the row
  adjudicator. A refusal from any of them is proof the repair landed, not a fault.
- CHECK util/ad-hoc/retired/ BEFORE CONCLUDING A TOOL IS GONE. Ad-hoc scripts are
  provenance of record (owner policy 2026-08-25) and are RENAMED, not deleted:
  2026-09-11_seqsafety_fanout_arm_merge.py moved there in ml#1919.
- A GUARD BESIDE A DEFECT MAY BE VACUOUS. declared_floors' `isinstance(data, dict)`
  can never be False, because tomllib.load always returns a dict. It read as evidence
  the author distrusted the value; it was a SECOND INSTANCE of the same defect.
```

---

## 2. State at handoff

| | |
| --- | --- |
| branch | `worktree-gentle-kindling-pascal`, tracking `origin/main`. **The only working-tree change is THIS FILE, untracked** — committing and PR-ing it is the first outstanding task (§7) |
| `origin/main` | re-measure — it took 6 merges in the 70 minutes this session watched it |
| this session's PRs | **#2000, #2001, #2010 — all MERGED** (`57e84be8`, `e6419175`, `e3186919`) |
| post-merge CI | **18 success / 5 skipped on all three** — `57e84be8`, `e6419175`, `e3186919` |
| markdown structure debt | **ZERO** — denominator drifts (1084 on 09-15, 1119 and 1127 on 09-22). Re-run; do not quote a total |
| falsy-guard population | **take a floor from ONE tool.** `next_batch` → **75 guards / 18 files** (non-ad-hoc); `triage --blind-spot` → **73 + 7 = 80** on its own criterion. They differ by 2 (`util/release_train/propose.py:918`, `:1070`). Do **not** add across them |
| open PRs authored here | none |

### Verification commands

Run from the juniper-ml repo root. **Never read a gate's exit code through a pipe**;
`xargs` remaps any child exit in 1–125 to **123**.

```bash
# The headline, re-runnable from git. Refuses (exit 2) rather than reporting a pass
# it did not measure, if a required rev is unavailable.
python3 util/ad-hoc/2026-09-22_structure_screen_ml1746_regression.py
#   -> pre-narrowing 2 / narrowed 0 / current 2, and ZERO across the whole tree

# The falsy-guard population, in the two units that must not be added
python3 util/ad-hoc/2026-09-11_falsy_guard_census.py --json util/ > /tmp/c.json
python3 util/ad-hoc/2026-09-22_falsy_guard_next_batch.py /tmp/c.json   # 75 / 18, by evidence tier
python3 util/ad-hoc/2026-09-11_falsy_guard_triage.py /tmp/c.json --blind-spot   # 73 + 7 = 80, ITS OWN floor

# The mutation matrix -- ONE baseline, whole class
python3 util/ad-hoc/2026-09-22_env_floor_full_mutation_matrix.py   # pins 9 / controls 3
python3 util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py   # residual pair load-bearing

# Open item 1, structurally and against the live corpus (no repo state needed)
python3 - <<'PY'
import json, pathlib
root = pathlib.Path.home()/'.local/state/juniper-experiments'
KEYS = ("final_accuracy","test_accuracy","val_accuracy","train_r2","cv_r2","r2")
tot=hit=0; top=set()
for p in root.rglob('stats.json'):
    try: s=json.loads(p.read_text())
    except Exception: continue
    tot+=1
    for k in ("cascor","recurrence"):
        b=s.get(k)
        if isinstance(b,dict):
            top|=set(b)
            if any(isinstance(b.get(m),(int,float)) for m in KEYS): hit+=1
print(tot,"stats.json ->",hit,"with a metric; key intersection:",sorted(top & set(KEYS)))
PY

# Open item 2, reproduced end-to-end
mkdir -p /tmp/s && printf 'schema_version: 1\nsuite:\n  name: s\n  app: recurrence\n  base_config: [123]\n' > /tmp/s/s.yaml
python3 util/experiments/run_suite.py --suite /tmp/s/s.yaml --dry-run; echo "exit=$?"
#   -> TypeError traceback, exit 1 (documented contract is exit 2)

# Suites touched today
python3 -m unittest tests.test_env_floor_drift_check tests.test_markdown_structure_screen \
                    tests.test_markdown_structure_delta tests.test_run_experiment tests.test_run_suite
```

---

## 3. Tools this session built

All under `util/ad-hoc/`, all on `main`. **Read the docstring first — each states its limits.**

| tool | writes? | question |
| --- | --- | --- |
| `2026-09-22_structure_screen_ml1746_regression.py` | no | **does the screen still see ml#1746?** Measures three screen versions out of git against the real damaged blob, plus the whole-tree false-positive arm |
| `2026-09-22_falsy_guard_next_batch.py` | no | implements the §6 BAR of `notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md` — classifies each guard by the in-file evidence its own author distrusts the value (`same-key` / `helper` / `file-level` / `none`) |
| `2026-09-22_env_floor_full_mutation_matrix.py` | no | **which tests actually pin the fix?** Whole class, ONE baseline |
| `2026-09-22_env_floor_residual_mutation_check.py` | no | the residual guard pair specifically, per-guard |

---

## 4. Traps this session paid for

1. **A screen narrowed to clear false positives can go blind to the defect it exists
   for.** The 17 findings were genuinely false; the narrowing that cleared them exempted
   every CLOSED fence carrying an info string — **86.9% of this tree's fence openers**
   (3302 typed of 3798, over 1116 deduped files, measured 2026-09-22 by walking
   `_fence_spans` and counting openers with a non-empty `_info_string`) — and swallowed
   ml#1746 with them. A "zero" is a claim about the instrument until you test the
   instrument against known damage.
2. **`PYTHONPATH` does not shadow a module the suite imports via
   `sys.path.insert(0, util/)`.** The first mutation harness tested the UNMUTATED module
   and reported both tests passing — i.e. *the fix is unnecessary*, the inverse of the
   truth. Pre-seed `sys.modules` and **assert the binding took**.
3. **A guard beside a defect may be vacuous.** `isinstance(data, dict)` where the value
   is always a dict is not evidence of care; it was a second instance of the same defect,
   and the reachable one.
4. **Adding figures from two runs is the unit error, even when the figures are about
   rigour.** "5 + 2 mutation-checked" was 5 of the original eight plus 2 added later;
   one run over the whole class says **9 pin the fix, 3 are controls**.
5. **A denominator drifts while an invariant holds.** `ZERO` was stable; the path total
   moved 1084 → 1119 → 1127 in a week. Quote the invariant, re-run for the total.
6. **`safe_merge` exit 0 ≠ merged, and neither does a hand-rolled watcher.** A
   `grep -qv null` poll matched a blank line and reported `MERGED` on an OPEN PR. Test
   `[ -n "$m" ] && [ "$m" != "null" ]`, and read the `MERGED` line.
7. **An unresolved CodeQL thread blocks a merge independently of checks.** ml#2001 sat
   `BLOCKED` at 21/21 green on a real leak (`open("/dev/null","w")` never closed) in a
   file this session wrote. Restructure, never suppress.
8. **A contended lane defeats `safe_merge`'s BEHIND cycle.** Six merges to `main` in 70
   minutes against a ~10-minute CI cycle: it refused after 3 cycles with a stated reason.
   The sanctioned fallback is the native auto-merge net — and only after that refusal.

---

## 5. Decisions made — do not re-litigate

- **ml#1944's narrowing was KEPT, not reverted.** The 17 were real false positives.
  ml#2000 adds `_absorbed_openers`, which is *narrower* than the pre-2026-09-15 rule and
  catches by mechanism what the old rule caught by accident. Do not widen it back.
- **The `operator` falsy-guard class reading the SUITE DOC in `run_suite.py` needs
  NOTHING.** ml#1895 did not patch a single site; it added `_require_mapping` /
  `_require_sequence` gates at `load_suite`:129-134 that type-check every nested block.
  Verified by call-site sweep: `expand_cells`, `check_cascor_parallel_floor` and `main`
  receive `doc` only from `load_suite`. A gate at the door beats a guard at every table.
  > **ml#2002 (`f8ffaa48`) rewrote this file after that sweep was taken**, adding 195
  > lines and three new `or {}` sites — `:446` (`overrides or {}`), `:645`
  > (`**(runtime_env or {})`) and `:950` (`yaml.safe_load(path.read_text()) or {}`).
  > `:950` parses a **materialised cell YAML**, a different object `load_suite`'s gates
  > never see, so the sweep above no longer covers the whole file. The CONCLUSION still
  > holds — the new `runtime_block_env` raises `SuiteError` on a non-mapping — but the
  > JUSTIFICATION does not, and a successor re-deriving it will find the sweep falls
  > short. Re-take the sweep before quoting this ruling.
- **Reachability is NOT uniform and the tests say so.** `ecosystem.yaml` is the operative
  input (juniper-ml only, every sibling check falls back to it, nothing else consumes
  `conda_envs`, yamllint checks syntax not structure). The two `pyproject.toml` arms are
  weaker — a malformed sibling pyproject fails `pip install` first. Both pinned; one likely.
- **`_headline_metrics` was NOT fixed here, deliberately.** Fixing it activates three
  currently-vacuous guards against machine-provenance JSON. The instrument and the guards
  belong in one PR with one set of tests.

---

## 6. Documents this handoff references or changes

**References**:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`,
`notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md`,
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`,
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`,
`util/ad-hoc/2026-09-05_markdown_structure_check.py`, `util/markdown_structure_delta.py`,
`util/ad-hoc/2026-09-11_falsy_guard_census.py`,
`util/ad-hoc/2026-09-11_falsy_guard_triage.py`,
`util/ad-hoc/2026-09-22_falsy_guard_next_batch.py`,
`util/ad-hoc/2026-09-22_env_floor_full_mutation_matrix.py`,
`util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py`,
`util/ad-hoc/2026-09-22_structure_screen_ml1746_regression.py`,
`util/env_floor_drift_check.py`, `util/experiments/run_suite.py`,
`util/experiments/run_experiment.py`, `util/experiments/stats_summary.py`,
`util/release_train/propose.py`, `util/safe_merge.py`, `util/wait_for_checks.py`,
`tests/test_env_floor_drift_check.py`, `tests/test_markdown_structure_screen.py`,
`tests/test_markdown_structure_delta.py`, `tests/test_run_experiment.py`,
`tests/test_run_suite.py`, `docs/REFERENCE.md`,
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `.github/workflows/ci.yml`,
`.github/workflows/main-verify.yml`,
`juniper-recurrence/juniper-recurrence/juniper_recurrence/schemas.py` (note the DOUBLED
directory — the repo root contains a same-named package dir), and the memory index
`MEMORY.md`.

**Changed**: this file,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md`,
and `MEMORY.md` (one pointer folded into the existing cursor-fleet line; the memory files
`project_cursor_fleet_round2_arc_closed_2026-09-11.md` and
`reference_mutation_check_stale_pyc_and_piped_exit.md` were also updated).
Merged earlier today — ml#2000: `util/ad-hoc/2026-09-05_markdown_structure_check.py`,
`tests/test_markdown_structure_screen.py`,
`util/ad-hoc/2026-09-22_structure_screen_ml1746_regression.py`; ml#2001:
`util/env_floor_drift_check.py`, `tests/test_env_floor_drift_check.py`,
`util/ad-hoc/2026-09-22_falsy_guard_next_batch.py`,
`util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py`, and
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`;
ml#2010: that same predecessor handoff again and
`util/ad-hoc/2026-09-22_env_floor_full_mutation_matrix.py`.

---

## 7. What was NOT done, and why

- **THIS FILE IS UNCOMMITTED.** It is the only working-tree change and has no PR. Commit
  it, open a PR against `main`, and merge with `util/safe_merge.py --pr N --execute` — the
  lane took 6 merges in 70 minutes today, so expect BEHIND cycles and read the `MERGED`
  line, never the exit code.
- **The five open items in §1 were not fixed.** They are a `util/experiments/` arc, not a
  falsy-guard arc, and item 1 is coupled to three guards that are only safe while it stays
  broken. Fixing them piecemeal would activate a defect class silently.
- **The five items were NOT filed in the defect register**, and that is a gap rather than a
  ruling. `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` defines its
  inclusion criterion as *"a concrete, actionable problem a maintainer could ticket: a bug,
  … a missing guard, a stale comment that misleads, dead code"* — all five qualify, and
  item 5 is literally dead code. That same register carries a resident warning against
  exactly this: *"A rule that lives only in the document that hands off the work stops
  existing the first time one successor omits it."* **Filing them is outstanding work.**
- **The remaining falsy guards were not swept**, by standing decision. The bar is in-file
  evidence, and `util/ad-hoc/2026-09-22_falsy_guard_next_batch.py` now measures it; §1
  names the two candidates it currently selects.
- **`MEMORY.md` was not compacted.** It is **25,843 bytes** against the owner's 20 KB
  target — a **~29% overshoot**, not the ~12% an earlier draft of this file claimed. Several
  sessions write it concurrently, so `stat` it rather than quoting any figure, including
  this one. Compact by RETIRING entries, never by stripping hooks. One pointer was folded
  into an existing line here rather than added as a new one.
- **The `env_floor_drift_check` reason string was not reworked.** A malformed pyproject now
  correctly exits 2, but says *"no juniper-\* version floors declared"* — true, yet it
  describes a declaration gap rather than a malformed document.
- **Adversarial validation was run on this session's own work and overturned three
  conclusions** (the vacuous precedent, two missed residuals, and the screen "closure").
  The handoff you are reading was validated the same way.

---

## 8. The five open items — mechanism, evidence, and the trap in each fix

Every line number here was re-probed 2026-09-22. `util/experiments/run_suite.py` was
rewritten by ml#2002 (`f8ffaa48`) **mid-session**, so re-grep before editing.

### 8.1 `_headline_metrics` can never match — and four of its six names do not exist

`run_suite.py:580-595` reads `final_accuracy` / `test_accuracy` / `val_accuracy` /
`train_r2` / `cv_r2` / `r2` off the **top** of `stats["cascor"]` / `stats["recurrence"]`.
`stats_summary.py:223-229` / `:246-254` emit top-level keys `{final, eval_scalars,
completion_reason, candidate_correlation, training_step_duration}` and `{final_metrics,
n_epochs, stopped_reason, dataset_descriptor, theta, readout, crossval}`. **Intersection =
∅.** The results path is *not* the bug: `run_experiment.py:1560` / `:1897` build
`run_dir/artifacts/results`, matching `run_suite.py:581` exactly.

*"Always has been"* is literal — `git log -L` shows `_headline_metrics` has **one** commit,
`513e7df2` (ml#1032), and `build_stats`' cascor block is byte-identical there.

**The trap.** Only **two** of the six names exist at *any* depth in the 413-file corpus:
`cascor.final.val_accuracy` (348 files) and `recurrence.final_metrics.r2` /
`recurrence.crossval.*.r2` (38). `final_accuracy`, `test_accuracy`, `train_r2` and `cv_r2`
appear **nowhere, at any depth**. A one-level unwrap harvests 2 of 6 and looks like a fix.

**The coupling, corrected.** An earlier draft called `run_suite.py:750 / :773 / :792`
VACUOUS. They are not: **26 of the 418 registry rows have no `metrics` key at all**, so
`row.get("metrics") or {}` converts a real `None` today — delete it and `for k in None`
raises at `:750`. Nor does fixing `_headline_metrics` endanger them: it is **type-closed**
(`out[metric] = block[metric]` behind an `isinstance(..., (int, float))` test), so it can
only ever emit a dict of numbers. The one crashing shape — `metrics` as a truthy non-dict —
is reachable solely from a corrupt or hand-edited `registry.jsonl` and is unchanged by the
fix.

**So the one-PR argument is COVERAGE, not safety**: `tests/test_run_suite.py`,
`tests/test_run_suite_gate_metrics.py` and `tests/test_run_suite_uncountable_report.py`
contain **zero** references to `metrics` / `metric_keys` / `_headline_metrics`. Those
columns have never been exercised with data, so the fix ships their first tests.

### 8.2 `expand_cells` raises raw exceptions where the contract promises exit 2

| suite YAML | result |
| --- | --- |
| `base_config: [123]` | `TypeError … 'PosixPath' and 'int'` at `_resolve_base_config:286` via `expand_cells:337` — **exit 1** |
| `include: [{config: 7, overrides: {}}]` | same `TypeError` via `expand_cells:350` — **exit 1** |
| `include: [{overrides: abc}]` | `ValueError: dictionary update sequence element #0 has length 1; 2 is required` at `:351` — **exit 1** |
| `include: [{overrides: [1,2]}]` | `TypeError: object is not iterable` at `:351` — **exit 1** |
| *control* `matrix: [1,2]` | `suite error: matrix: must be a mapping, got list` — **exit 2** |
| *control* `exclude: foo` | `suite error: exclude: must be a list, got str` — **exit 2** |

> **`include: [{config: 7}]` ALONE is NOT one of them** — it exits **2** correctly with
> *"include entries must be mappings with an 'overrides' key"*. An earlier draft listed it;
> it only becomes a raw `TypeError` when paired with `overrides`. Quote the paired form.

Mechanism: `main:875-880` is `try: … except SuiteError: return 2`; anything else escapes
`sys.exit(main())` and CPython exits **1**. The contract is `run_suite.py:28-29` —
*"2 = misuse / suite-validation error"*, *"1 = suite completed with failed cells"* — printed
by `--help` via `description=__doc__` at `:859`. **The collision is exact.** Note it lives
only there: `docs/REFERENCE.md` § Suite Driver and
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:41-53` do not restate the exit codes.

### 8.3 `_emit_stats` fails silently and nothing reads the receipt

`run_experiment.py:1166-1186`. `except Exception` at `:1183` sets `manifest["stats_error"]`
at `:1184`; the exit code is never touched, because the call sites `:1756` / `:2103` are
inside a `finally:` opened at `:1703` / `:2052`, after `exit_code` is fixed at `:1679-1698` /
`:2030-2047`.

Consumers repo-wide: `tests/test_run_experiment.py:1008` and `:1549` — **both
`assertIsNone`, so only the happy path is pinned and no test pins a failure** — plus the jq
recipe at `docs/REFERENCE.md:5303`. **Zero** hits under `.github/`: no gate, no CI.

And `_headline_metrics` returns `{}` for a missing `stats.json` (`:583-584`) — **the same
value a healthy one returns** — so the loss is indistinguishable from success downstream.

> **Correction to an earlier draft**: the manifest's `artifacts` list does **not** come back
> empty. It is seeded with the config copy at `:1582` / `:1916` and assigned at `:1186`,
> *outside* the try. What is lost is exactly `stats.json` and `summary.md`; and since
> `_write_json(stats_path)` at `:1175` precedes `render_summary_md` at `:1179`, a
> render-only failure loses `summary.md` alone.

### 8.4 The crossval passthrough is a LOCAL inconsistency, not a cross-repo dependency

`stats_summary.py:238-239` copies `eval_aggregate` / `eval_std` verbatim
(`run_experiment.py:2010` type-checks only the envelope; `:2012` does the copy), and
`render_summary_md:329` reads both with a bare `or {}` + `.items()` / `.get()`.

The remote pin is real —
`juniper-recurrence/juniper-recurrence/juniper_recurrence/schemas.py:291-292` (note the
**doubled** directory) plus `routers/crossval.py` `response_model=CrossValResponse`, present
since the endpoint's first commit, so no older service ever served it unpinned.

**But that is not the argument.** `util/experiments/plots_recurrence.py:178-179` **and**
`:216-217` consume the *same* `crossval_full` payload in the *same* driver run and guard
*exactly these two keys* with `isinstance(..., Mapping)`. A sibling module already treats
them as untrusted; `stats_summary.py` is the outlier. (`folds` is guarded locally too, at
`:242-243`.) `--recurrence-url` (`run_experiment.py:2158`) also lets an operator aim the
driver at an arbitrary base URL.

**Severity is §8.3's class, not a crash**: `render_summary_md` raises only on a *truthy*
non-mapping, `_emit_stats` catches it, `stats.json` is already written — so the cost is
`summary.md`, silently, exit code unchanged.

### 8.5 The `present` fallback is unreachable in production but TEST-PINNED — keep it

`stats_summary.py:340`: `scraped.get("target_file_written", scraped.get("present"))`.

Both mechanism halves hold: `_metrics_scraped` (`run_experiment.py:353-400`) emits
`target_file_written` at `:378` and never `present`; and the only production caller of
`render_summary_md` is `_emit_stats` (`:1179`), fed the dict `build_stats` just returned from
the live in-memory manifest — no disk round-trip exists anywhere in `util/`, `scripts/` or
`tests/`.

**It is still not dead code.** Mutation-checked: removing `scraped.get("present")` turns
`tests/test_stats_summary_render.py:105`
`test_missing_key_is_pre_2026_09_01_na_and_present_is_the_written_fallback` **red**; `:112`
`test_written_key_wins_over_present_fallback` pins the precedence, and
`tests/test_stats_summary_git_and_confirmed.py:106` exercises it too. The comment at `:339`
documents it as intentional back-compat, and the need is measurable: **330 of 413** on-disk
`stats.json` and **330 of 414** `manifest.json` carry `metrics_scraped.present`; only 83
carry `target_file_written`.

**The item is the latent coupling, not a deletion.** The branch is evidence its author
expected `render_summary_md` to be fed disk-loaded manifests. Add the re-render tool it
implies and every guard validated safe this session becomes live at once.
