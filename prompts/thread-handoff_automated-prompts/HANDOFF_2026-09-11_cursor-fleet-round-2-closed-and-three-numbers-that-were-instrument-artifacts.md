# HANDOFF — Cursor fleet round 2 CLOSED, and three numbers that were instrument artifacts

**Date**: 2026-09-11
**Session**: `2db9c4aa-8815-4ae4-8faa-cba1ecfd4f41` (`https://claude.ai/code/session_0142dJD2GUxBkoWxbieagNGQ`)
**Worktree**: `juniper-ml/.claude/worktrees/elegant-watching-chipmunk`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_cursor-fleet-round-2-repaired-not-ratified-and-the-screen-that-hid-it.md`

---

> ## RE-EVALUATION 2026-09-22 — the through-line claimed TWO more victims
>
> Re-probed against the tree rather than edited from memory, then put through adversarial
> validation. **Both §1 standing items are discharged — but neither closed the way this
> document expected, and the instrument-artifact through-line held twice more. Four for
> four, then five.**
>
> 1. **The OWNER QUESTION (the 17 residual structure findings) is MOOT — but the fix that
>    made it moot BLINDED A REQUIRED GATE, and that is now repaired.** ml#1944 (2026-09-15)
>    narrowed the screen rule to fire only when a fence is **UNCLOSED or carries no info
>    string**, taking the tree from 17/2 to zero. The 17 were genuine false positives and no
>    standing note is owed — that half holds.
>    **Its safety argument did not.** It rested on *"a dropped closer leaves the fence
>    UNCLOSED, which is reported in its own right"* and on *"ml#1746's own fence was bare."*
>    The second is checkably false: ml#1749's repair commit (`7a4b1cb4`) records the lost
>    line as *"the close of the ``text`` block at REFERENCE.md:1522"* — **typed**, the class
>    the narrowing exempts. The first fails in any document with fences after the damage: the
>    next opener is absorbed (a delimiter with an info string cannot close), a later bare
>    delimiter re-closes the span, polarity is restored and **no UNCLOSED finding exists**.
>    Measured against the real damaged blob `bcc89c45:docs/REFERENCE.md` — pre-narrowing
>    screen **2**, narrowed screen **0, exit 0**, i.e. the instrument could no longer see its
>    own founding incident, inside the `Documentation Links` **required check** that execs it
>    via `util/markdown_structure_delta.py`.
>    **Repaired 2026-09-22** by detecting the dropped-closer fingerprint directly
>    (`_absorbed_openers`): ml#1746 scores **2** again and the tree still screens **ZERO
>    across 1119 tracked paths**. The trade-off ml#1944 accepted was false — both were
>    available at once. Proof is re-runnable:
>    `util/ad-hoc/2026-09-22_structure_screen_ml1746_regression.py`.
> 2. **The `or {}` population was TRIAGED — ml#1914, merged 2026-09-11**, hours after this
>    handoff was written, and again on **2026-09-22** (this re-probe). See
>    `notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md`.
>    **"117 live read-class sites" was wrong in both directions at once**: the census emits
>    one row per *use*, not per guard (116 rows = 77 guards), and it structurally cannot see
>    a guard nested inside `while:` / `try:` / `if:` / `for:` (+8 more). The unit of repair
>    is the **guard**; the unit of the census is the **use**; they must not be added.
>
> **What the re-probe changed, 2026-09-22.** §6 of the triage note set a bar for the next
> batch — *"the file's own helper and its own `isinstance` precedent proved the author
> already considered the value untrusted"* — and **nothing implemented it**. It does now:
> `util/ad-hoc/2026-09-22_falsy_guard_next_batch.py` classifies every guard by the in-file
> evidence that its own author distrusts the value. Applying it found **three reproducible
> defects of the ml#1914 class in a second file**, `util/env_floor_drift_check.py`, which is
> gated in **two** CI workflows:
>
> | site | input | symptom |
> | --- | --- | --- |
> | `_project_name`:142 | `project = ["x"]` in a target repo's `pyproject.toml` | `AttributeError: 'list' object has no attribute 'get'` — while `declared_floors`:175 guarded the **identical read** with `isinstance(data, dict)` |
> | `declared_floors`:179 | `optional-dependencies = ["oops"]` | `AttributeError: ... has no attribute 'values'` |
> | `_load_ecosystem_envs`:266 | `conda_envs:` as a YAML **sequence** | `AttributeError: ... has no attribute 'items'`, **escaping the function's own documented contract** — its docstring promises *"empty on any failure … or malformed"* and its `except` catches only `(OSError, yaml.YAMLError)`. The operator got a traceback where `docs/REFERENCE.md` promises exit 2. |
>
> Both inputs are **hand-authored**, so this is the `operator` provenance class — reachable
> by typing, not only across a version skew. Fixed with the `run_experiment.py` idiom
> (`_mapping()`); the guard population fell **77 → 75 guards / 19 → 18 files** because that
> file left it entirely.
>
> **Adversarial validation then corrected the finding itself, in three ways worth keeping:**
> - **The claimed precedent was vacuous.** `declared_floors` guards `data` — the parsed
>   document — with `isinstance(data, dict)`, and `_pyproject_data` returns `tomllib.load`
>   (always a dict) or `{}`. **That test can never be False.** It was not evidence the author
>   distrusted the read; it was *a second instance of the same defect one line later*, and
>   the reachable one. `_load_ecosystem_envs`'s inner `isinstance(meta, dict)` is the only
>   genuine precedent in the file.
> - **Reachability is NOT uniform.** The `ecosystem.yaml` arm is operative: that file exists
>   in juniper-ml only, `resolve_site_dirs` falls back to it for **every** sibling-repo
>   check, nothing else in the repo consumes `conda_envs`, and yamllint checks syntax, not
>   structure. The two `pyproject.toml` arms are weaker — a sibling pyproject that malformed
>   would fail `pip install` and `python -m build` first. Both pinned; only one is likely.
> - **Two residuals the first pass missed**, both in `_load_ecosystem_envs`, both breaking the
>   *same* docstring contract by routes the first fix left open: `UnicodeDecodeError` is a
>   `ValueError`, not an `OSError`, so it escaped the except tuple; and a YAML **key** need
>   not be a string — `NO:` parses as boolean `False` (the "Norway problem") and reached
>   `site_packages_for_env`, where `conda_dir / "envs" / env_name` raises `TypeError`.
>
> Final: **12 tests**, 5 + 2 mutation-checked against the pre-fix code, the rest negative
> controls. The residual pair is proved load-bearing by
> `util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py` — whose **first version was
> itself vacuous**, shadowing by `PYTHONPATH` while the suite's own
> `sys.path.insert(0, util/)` won, so every test "passed" against a module that was never
> mutated. It now pre-seeds `sys.modules` and asserts the binding took.
>
> **Do not quote a falsy-guard number from this document.** Re-run both tools and say which
> unit you mean. Today's figures are in §2, and they moved between the top and bottom of this
> very session.

---

## 1. Goal statement for the next thread

```text
The cursor-fleet round-2 arc is CLOSED. Items 1-4 shipped 2026-09-10 (ml#1886); items
6a / 6b / 6d shipped 2026-09-11 across NINE repos. Item 5 was dissolved, not done.
There is no queued work from this arc. What follows is what a successor should know
before touching any of it again, and the one thing left open is an OWNER question,
not a task.

The through-line: EVERY headline number this arc carried was an artifact of the
instrument that produced it, not a property of the tree. Three for three.
[FOUR for four, as of 2026-09-22: the replacement figures BELOW were artifacts too.
See the RE-EVALUATION banner. The through-line held one turn longer than its author did.]

  - "63 structural problems / 14 files"  -> real, but the screen could not see the
    worst damage (161 lines swallowed in notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md)
    and mis-located it twice across two review rounds. Fixed 2026-09-10; tree is 17/2
    and both survivors are provable screen artifacts.
    [The 17/2 was an artifact of the SCREEN's over-strong fence rule, not of the tree.
     ml#1944 narrowed the rule 2026-09-15; the tree is ZERO / 1084.]
  - "28 unguarded `or {}` chains across 7 files" -> the census matched ONE expression
    shape, GATED whole files on a hard-coded ten-filename roster, and counted any
    `isinstance` in a function as a guard for every chain in it. Rebuilt: 397 sites /
    96 files in ml util/, of which 294 are `read` class and ~117 live (177 are in
    util/ad-hoc/ one-shot scripts). Siblings are ~32, NOT the ~135 estimated.
    [The rebuilt census counts USES; the unit of repair is the GUARD. 294 read-class
     uses collapse to 77 guards, and 8 more are invisible to it. ml#1914.]
  - "87 residue lines unadjudicated" -> §4 of the residue document holds 173 lines,
    not 87; the 87 was `173 - 86` arithmetic nobody checked against the section it
    describes. Adjudicated: ZERO content losses.

Remaining work: NONE from this arc. Two standing items a successor may pick up:
[BOTH CLOSED 2026-09-22 -- see the RE-EVALUATION banner above. Kept verbatim because
the reasoning is the durable part; the STATUS is not.]

1. [CLOSED -- ml#1944, 2026-09-15. The screen was narrowed; the tree is ZERO / 1084.]
   OWNER QUESTION, unanswered since ml#1886's body: whether the 17 residual
   markdown-structure findings (13 in STANDING-ITEMS' ```text banner, 4 in
   PROMPT-ANALYSIS' ````jinja2 sample) should be written down as a standing note.
   They need no action to stay correct; both are screen false positives that no
   repair can clear without lying about the content.
2. [TRIAGED -- ml#1914, 2026-09-11, and again 2026-09-22. The FIGURE BELOW IS WRONG:
   117 counts USES, not guards, and misses 8 the census cannot see. See
   notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md.]
   THE `or {}` POPULATION IS MEASURED, NOT TRIAGED. 117 live read-class sites across
   19 files remain, concentrated in util/experiments/ (stats_summary.py 40,
   run_suite.py was 20). ONE was fixed -- the only one where a defect is
   REPRODUCIBLE. Do not sweep the rest mechanically: it is a large change against a
   class with one known incident (ml#1781, 4 sites). Triage on evidence, using
   util/ad-hoc/2026-09-11_falsy_guard_census.py, and fix what you can make fail.
   [The standing advice -- triage, never sweep -- STANDS and has now been applied
   twice, to run_experiment.py (6 sites) and env_floor_drift_check.py (3 sites).
   Both batches were chosen by in-file evidence, not by count.]

Key context:
- RE-MEASURE BEFORE QUOTING. main took merges throughout this session; the census
  count moved 396 -> 397 while this handoff was being written, because the session
  added its own ad-hoc scripts to the corpus it measures.
- THE REFUSAL IS THE RECEIPT. Four tools in this arc now REFUSE on a repaired tree
  (the symlink retargeter, the row restorer, the seq-safety patcher, the relocation
  script). A refusal from any of them is proof the repair landed, not a fault.
```

---

## 2. State at handoff

| | |
| --- | --- |
| `origin/main` (juniper-ml) | re-measure — it moves every few minutes |
| this session's ml PRs | **#1886, #1890, #1895** |
| the 6a fan-out | **8 sibling PRs, all MERGED** — canopy#617, cascor#643, cascor-client#162, cascor-worker#182, data#393, data-client#198, deploy#210, recurrence#167 |
| markdown structure debt | ~~**17 / 2** — both known screen false positives~~ **ZERO across 1084 paths** (re-measured 2026-09-22; ml#1944 narrowed the screen) |
| `Sequence Safety` comment drift | **zero** across all nine repos |
| residue §4 | **adjudicated, zero content losses** |
| `or {}` population (ml `util/`) | ~~**397 sites / 96 files**; 294 `read`-class, ~117 live~~ **the unit was wrong.** Re-measured 2026-09-22 *after* the env-floor fix: **402 rows / 102 files** (299 `read`-class) collapse to **75 distinct guards / 18 files** outside `util/ad-hoc/`, **+7 the census structurally cannot see** = **82, a FLOOR**. By in-file evidence: `same-key` 9 (7 of them run_suite's already-gated `doc`), `helper` 2, `file-level` 51, `none` 13 |

### Verification commands

Run from the juniper-ml repo root. **Never read a gate's exit code through a pipe**, and
note `xargs` remaps any child exit in 1–125 to **123**.

```bash
# 6a -- the fan-out landed. BOTH directions, because either alone is weak.
# (a) the patcher REFUSES on all eight: "header paragraph start not found"
python3 util/ad-hoc/2026-09-11_seqsafety_comment_fanout.py | tail -3     # 0 patched, 8 "failures"
# (b) the premise still holds, read from the live rulesets rather than the workflows
python3 util/ad-hoc/2026-09-11_fleet_required_context_probe.py --context "Sequence Safety"
#     -> REQUIRED in all nine

# NOTE a documented FALSE POSITIVE: every corrected header QUOTES the old phrasing to
# explain it ('opened "ADVISORY, NOT a required check" and promised ...'), so a bare grep
# for that string still hits. Check it is INSIDE quotes before calling it drift.

# 6b -- the rebuilt census, and the one fix
python3 util/ad-hoc/2026-09-11_falsy_guard_census.py util/ | tail -4
python3 -m unittest -v tests.test_run_suite.NestedBlockTypeTest                # 9 tests

# 6d -- the adjudication is reproducible
python3 util/ad-hoc/2026-09-11_residue_section4_adjudicate.py --show-absent | tail -20
#     -> 173 lines, 24 structural, 107 of 149 accounted for, 42 absent (32 from §3's four)

# Whole-tree structure, unchanged by this session's work
git ls-files -z '*.md' > /tmp/md0
python3 - <<'PY'
import subprocess, sys
paths = [p for p in open('/tmp/md0').read().split('\0') if p]
r = subprocess.run([sys.executable, 'util/ad-hoc/2026-09-05_markdown_structure_check.py'] + paths)
print("screen exit =", r.returncode)   # 1 = reported; 2 = refused to report
PY
```

---

## 3. Tools this session built

All under `util/ad-hoc/`, all on `main`. **Read the docstring first.**

> **Re-probed 2026-09-22: six of the seven are still at the paths below; one was RETIRED.**
> `2026-09-11_seqsafety_fanout_arm_merge.py` moved to `util/ad-hoc/retired/` in ml#1919
> (`0532ffa5`) — retired under the owner's provenance-of-record policy, not deleted, so the
> path in this table no longer resolves while the tool still exists. Check
> `util/ad-hoc/retired/` before concluding a tool from any handoff is gone.

| tool | writes? | question |
| --- | --- | --- |
| `2026-09-11_fleet_required_context_probe.py` | no | **what does each repo's RULESET actually require?** — the premise check 6a needed before any edit |
| `2026-09-11_seqsafety_comment_fanout.py` | **yes** | patch the eight headers; anchors located structurally, not by line number |
| `2026-09-11_seqsafety_fanout_open_prs.py` | **yes** | drive `open_signed_pr.py` once per repo, each with its OWN ruleset id |
| ~~`2026-09-11_seqsafety_fanout_arm_merge.py`~~ **RETIRED** — now `util/ad-hoc/retired/2026-09-11_seqsafety_fanout_arm_merge_RETIRED-2026-09-11.py` (ml#1919) | **yes** | arm eight nets WITH A BODY; disarms first, reads back, checks state before body |
| `2026-09-11_seqsafety_fanout_status.py` | no | one line per PR, one verdict line — a wall of near-identical green hides a red |
| `2026-09-11_falsy_guard_census.py` | no | **`or {}` sites, classified by the PROVENANCE of the guarded value** |
| `2026-09-11_residue_section4_adjudicate.py` | no | does each held-back residue line survive anywhere in the tree today? |

**Every one states a limit, because a clean run from any of them is not evidence:**
the census cannot know a type (that is the whole reason the pattern is a problem); the
adjudicator's ANCHOR key proves identifiers co-occur, not that the claim survives; the
fan-out patcher rewrites comments and cannot tell a correct comment from a stale one —
which is why the ruleset probe runs first.

---

## 4. Traps this session paid for

1. **A self-matching corpus reports a perfect score.** The residue document is tracked
   markdown and its §4 quotes every held-back line verbatim, so a corpus built from
   `git ls-files '*.md'` matched every line against ITSELF: 149/149 accounted for. Not a
   weak signal — a measurement of the wrong thing that looks like success.
2. **Casing and a suffix manufacture losses.** Six headings scored ABSENT against
   sections that exist, because the branch wrote `## Cascor primary freeze tell
   (operational)` and the tree writes `### Cascor Primary Freeze Tell`. A verdict of
   "lost" from an exact-match key is a statement about the key.
3. **`--auto` on a mergeable PR MERGES it, leaving no net to inspect.** The arming tool
   read `commitBody` before `state` and reported three successful merges as empty-body
   FAILURES. Check state first.
4. **Re-arming an already-armed net is a silent no-op.** `gh pr merge --auto --subject
   --body-file` against an armed PR exits 0, prints nothing, changes nothing. Disarm
   first, then re-arm, then read back — `null` and `""` both render as length 0.
5. **The armed net never updates a BEHIND branch.** ml#1895 sat green-and-armed at
   `BEHIND` twice while other sessions merged. `gh pr update-branch` is not a subcommand
   in this `gh`; the server-side `PUT .../pulls/N/update-branch` is. `safe_merge` has a
   BEHIND cycle and is the sanctioned path.
6. **Three of four matrix cells passing is a flake, and the log says which.** canopy#617
   failed `test_x7_loop_responsiveness::test_health_stays_fast_while_upstream_is_slow`
   — a wall-clock bound, `0.831s` against `0.5s` — on 3.12-ubuntu while 3.12-macOS,
   3.13-ubuntu and 3.14-ubuntu passed the SAME commit alongside 6355 other tests. Pull
   the job log before re-running; "re-run until green" without knowing what failed is
   the anti-pattern this arc exists to avoid.
7. **`gh run rerun --failed` prints "cannot be rerun; its workflow file may be broken"
   while succeeding.** The rerun had started. Confirm by reading the job ids, not the
   message.

---

## 5. Decisions made — do not re-litigate

- **6a's premise was CHECKED, not inherited.** The predecessor asserted `Sequence Safety`
  is required in all eight siblings from juniper-ml's ruleset alone. It is — verified per
  repo — but had it been advisory anywhere, that repo's comment would have been CORRECT
  and editing it would have introduced the defect. A comment and a ruleset are different
  authorities; only the ruleset was treated as one.
- **"Never wired into the CI Quality Gate" was KEPT in all eight.** It is still true and
  is a *different* claim from "not required". Conflating them is what produced the drift.
- **6b fixed ONE file, deliberately.** `run_suite.py:load_suite` is the only place a
  defect was reproducible (`TypeError: unhashable type: 'dict'` from a `suite:` written
  as a list). Sweeping 294 read-class sites is a large mechanical change against a class
  with one known incident; the corrected census exists so the rest can be triaged on
  evidence.
  > **This decision STANDS and has been vindicated twice** — but the *scale* it argues
  > against was overstated by ~4x (294 uses ≈ 77 guards), and this document's own
  > description of the fix was too small. ml#1895 did **not** patch a single site: it added
  > `_require_mapping` / `_require_sequence` gates at `load_suite`:129-134 that type-check
  > **every** nested block before any `or {}` runs, which is why all seven surviving
  > `doc.get(...) or {}` reads in that file are correct and need nothing. Verified
  > 2026-09-22 by call-site sweep: `expand_cells`, `check_cascor_parallel_floor` and `main`
  > receive `doc` only from `load_suite`, and the file's sole other `yaml.safe_load` builds
  > a different object. A gate at the door beats a guard at every table.
- **6d found ZERO content losses, and one refusal that PROTECTED main.** `#1668`'s four
  residue lines are a status header reading *"Still do not implement from this
  document"*; the tree now reads *"PLAN v3 — LARGELY DISCHARGED 2026-09-05."* Merging the
  residue would have reverted a shipped status to a false one — the case the
  refuse-and-report consolidator design exists for.
- **The 6a fan-out used whole-file API commits, which is safe HERE and not in general.**
  These are plain text files. `open_signed_pr.py` base64s `read_text()` and
  `createCommitOnBranch` has no mode field, so a symlink or an LFS path would be
  destroyed silently. ml#1886 needed a LOCAL signed commit for exactly that reason.

---

## 6. Documents this handoff references or changes

**References**:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_cursor-fleet-round-2-repaired-not-ratified-and-the-screen-that-hid-it.md`,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_cursor-fleet-round-2-tail-closed-and-validation-overturned-four-conclusions.md`,
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`,
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md`,
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`,
`util/experiments/run_suite.py`, `util/experiments/read_run_metrics.py`,
`util/ad-hoc/2026-09-06_untyped_json_read_census.py`, `util/safe_merge.py`,
`util/open_signed_pr.py`, `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`,
and `.github/workflows/sequence-safety.yml` in all eight sibling repos.

**Changed**: this file,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`;
plus, merged in ml#1895 — `util/experiments/run_suite.py`, `tests/test_run_suite.py`,
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md` (new §6),
and the seven new `util/ad-hoc/2026-09-11_*.py` tools listed in §3; and, in the eight
siblings, each repo's `.github/workflows/sequence-safety.yml`.

### 6a. Added by the 2026-09-22 re-evaluation

**References** (beyond the list above):
`notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md` (the ml#1914 record
that corrected this document's standing item 2, and whose §6 set the bar the re-probe
implemented), `util/ad-hoc/2026-09-11_falsy_guard_census.py`,
`util/ad-hoc/2026-09-11_falsy_guard_triage.py`,
`util/ad-hoc/2026-09-05_markdown_structure_check.py`, `util/markdown_structure_delta.py`,
`util/experiments/run_suite.py`, `util/experiments/stats_summary.py`,
`util/experiments/run_experiment.py`, `docs/REFERENCE.md`,
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `.github/workflows/ci.yml`,
`.github/workflows/main-verify.yml`, and
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md`
(the re-probe-in-place precedent this banner follows).

**Changed**: this file;
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`;
`util/ad-hoc/2026-09-05_markdown_structure_check.py` (new `_absorbed_openers`, corrected
`_can_swallow_headings`); `tests/test_markdown_structure_screen.py` (new
`AbsorbedOpenerRestoresDroppedCloserDetectionTest`, 7 tests, plus a corrected comment on
`test_a_BARE_closed_fence_containing_an_h2_is_STILL_reported`);
`util/env_floor_drift_check.py` (five sites + a new `_mapping()` coercer, a widened
`except`, and a non-string-key skip); `tests/test_env_floor_drift_check.py` (new
`MalformedOperatorInputGuardTest`, 12 tests); and three new tools,
`util/ad-hoc/2026-09-22_falsy_guard_next_batch.py`,
`util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py`, and
`util/ad-hoc/2026-09-22_structure_screen_ml1746_regression.py`.

### 6c. OPEN — five things validation found that this session did NOT fix

Adversarial validation of the "everything else is derived-safe" conclusion **upheld it**
(`run_suite`'s `doc` guards and `render_summary_md`'s top-level `stats` guards are genuinely
gated; no disk round-trip into `build_stats` / `render_summary_md` exists anywhere in
`util/`, `scripts/` or `tests/`). It also surfaced five adjacent items, left open
deliberately — they are a different arc and none is a falsy guard:

1. **`util/experiments/run_suite.py` `expand_cells` raises RAW exceptions on
   operator-typeable YAML** — the exact symptom `load_suite`'s gates were added to end, one
   function downstream. `base_config: [123]` → `TypeError: unsupported operand type(s) for
   /: 'PosixPath' and 'int'`, escaping `main`'s `except SuiteError` as a traceback **with
   exit 1**, where the documented contract is exit 2 (suite-validation error). Also
   `include: [{config: 7, …}]`, `include: [{overrides: abc}]`, `include: [{overrides:
   [1,2]}]`. A caller cannot distinguish "bad suite" from "cells failed".
2. **`util/experiments/run_suite.py` `_headline_metrics` is off by one nesting level, and
   has ALWAYS been.** It looks for `final_accuracy` / `test_accuracy` / `val_accuracy` /
   `train_r2` / `cv_r2` / `r2` at the top of `stats["cascor"]` / `stats["recurrence"]`;
   `build_stats` nests them under `final` / `eval_scalars` / `final_metrics`. Measured
   against the live corpus in `~/.local/state/juniper-experiments`: **398 real `stats.json`
   → 0 yield a metric; 418 registry rows across 107 suites → 0 non-empty `metrics`; 107 real
   `aggregate.csv` → 0 headers contain `accuracy` or `r2`.** `aggregate.csv` has never
   carried a single metric.
   > **And this is why `run_suite.py`:590 / :613 / :632 are safe — they are VACUOUS.**
   > `metric_keys` is the union over `row.get("metrics")`, which has always been `[]`. Fix
   > `_headline_metrics` and those three guards immediately begin reading `row["metrics"]`
   > from an on-disk, append-only, `--resume`-replayed `registry.jsonl` — the `machine`
   > provenance class. **Fix the instrument and the guards in the same PR.**
3. **`stats_summary.py`:236-237 copies `eval_aggregate` / `eval_std` VERBATIM from the
   `POST /v1/crossval` response** (`run_experiment.py`:2011-2012 type-checks only the
   envelope), and `render_summary_md`:329 reads them with a bare `or {}` + `.items()` /
   `.get()`. They are safe **only** because `juniper-recurrence`'s
   `juniper_recurrence/schemas.py`:291-292 pins them and the route declares
   `response_model=CrossValResponse`. That is a guarantee in a **different repo** — the one
   the ecosystem `AGENTS.md` records as having been missing from the decision-11 consumer
   census. Three lines away, `folds` **is** locally guarded.
4. **`_emit_stats` fails silently and nothing reads the receipt.** `run_experiment.py`:1166
   catches `Exception`, sets `manifest["stats_error"]`, and **does not change the exit
   code** (it runs in `finally:`, after `exit_code` is computed). Repo-wide, `stats_error`
   is read by two test assertions and one `jq` recipe in `docs/REFERENCE.md`:5303 — no gate,
   no suite check, no CI. On the `build_stats` branch the manifest's `artifacts` list also
   comes back empty, so the run's evidence index is lost too, and `run_suite`'s
   `_headline_metrics` returns `{}` for a missing `stats.json` — **the same value a healthy
   one returns**, so the loss is indistinguishable.
5. **`stats_summary.py`:341's `scraped.get("target_file_written", scraped.get("present"))`
   is dead code** — nothing renders a manifest from disk and `_metrics_scraped` has not
   emitted `present` since it was rewritten. It is evidence its author expected
   `render_summary_md` to be fed disk-loaded manifests. **If anyone adds the re-render tool
   that comment implies, every guard confirmed safe above becomes live at once.**

### 6b. What a successor should NOT re-do

- **Do not re-widen the structure screen to the pre-2026-09-15 rule.** The 17 false
  positives were real false positives; the repair is `_absorbed_openers`, which is narrower
  than the old rule and catches the case the old rule caught by accident.
- **Do not sweep the remaining 75 + 7 falsy guards.** Two batches have now been taken on
  in-file evidence (ml#1914's six, this session's five). The `same-key` tier is down to two
  genuine entries; the other seven are run_suite's `doc`, gated once at `load_suite`.
- **Do not quote a guard count without its unit** — rows are uses, not guards, and the
  census cannot see guards nested in control flow.

---

## 7. What was NOT done, and why

- **No independent agent validation was run on this session's own work**, the same
  caveat the predecessor carried. Mechanical cross-checks were substituted: the parsed
  YAML was proven byte-identical before/after in all eight fan-out repos; the new
  `run_suite` tests were mutation-checked (6 of 9 fail against the pre-fix code, and the
  3 that pass are negative controls that must); every 6d verdict is re-runnable from §2.
  Those catch a different class of error than an adversarial reader does.
- ~~**The `or {}` population is measured and NOT triaged** — 117 live read-class sites
  remain, by choice, with the reasoning in §5.~~ **TRIAGED 2026-09-11 (ml#1914) and
  again 2026-09-22.** The figure was an artifact — see the RE-EVALUATION banner. The
  *choice* it describes (triage, never sweep) was correct and still governs.
- **`util/ad-hoc/2026-09-06_untyped_json_read_census.py` was NOT deleted.** Ad-hoc
  scripts are provenance of record (owner policy 2026-08-25). Its successor names it and
  the three defects in its docstring, so a reader who finds the old one first is told
  where to go.
- ~~**The 17 residual structure findings are untouched** and need no action; whether to
  record them as a standing note is the owner question in §1.~~ **RESOLVED by ml#1944
  (2026-09-15), and the "need no action" half was wrong.** They were failing the
  `Documentation Links` required check on unrelated PRs, via
  `util/markdown_structure_delta.py`'s zero-baseline grading of ADDED files. A finding a
  screen cannot clear is not inert when a gate reads that screen.
