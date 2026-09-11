# HANDOFF — Cursor fleet round 2 CLOSED, and three numbers that were instrument artifacts

**Date**: 2026-09-11
**Session**: `2db9c4aa-8815-4ae4-8faa-cba1ecfd4f41` (`https://claude.ai/code/session_0142dJD2GUxBkoWxbieagNGQ`)
**Worktree**: `juniper-ml/.claude/worktrees/elegant-watching-chipmunk`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_cursor-fleet-round-2-repaired-not-ratified-and-the-screen-that-hid-it.md`

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

  - "63 structural problems / 14 files"  -> real, but the screen could not see the
    worst damage (161 lines swallowed in notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md)
    and mis-located it twice across two review rounds. Fixed 2026-09-10; tree is 17/2
    and both survivors are provable screen artifacts.
  - "28 unguarded `or {}` chains across 7 files" -> the census matched ONE expression
    shape, GATED whole files on a hard-coded ten-filename roster, and counted any
    `isinstance` in a function as a guard for every chain in it. Rebuilt: 397 sites /
    96 files in ml util/, of which 294 are `read` class and ~117 live (177 are in
    util/ad-hoc/ one-shot scripts). Siblings are ~32, NOT the ~135 estimated.
  - "87 residue lines unadjudicated" -> §4 of the residue document holds 173 lines,
    not 87; the 87 was `173 - 86` arithmetic nobody checked against the section it
    describes. Adjudicated: ZERO content losses.

Remaining work: NONE from this arc. Two standing items a successor may pick up:

1. OWNER QUESTION, unanswered since ml#1886's body: whether the 17 residual
   markdown-structure findings (13 in STANDING-ITEMS' ```text banner, 4 in
   PROMPT-ANALYSIS' ````jinja2 sample) should be written down as a standing note.
   They need no action to stay correct; both are screen false positives that no
   repair can clear without lying about the content.
2. THE `or {}` POPULATION IS MEASURED, NOT TRIAGED. 117 live read-class sites across
   19 files remain, concentrated in util/experiments/ (stats_summary.py 40,
   run_suite.py was 20). ONE was fixed -- the only one where a defect is
   REPRODUCIBLE. Do not sweep the rest mechanically: it is a large change against a
   class with one known incident (ml#1781, 4 sites). Triage on evidence, using
   util/ad-hoc/2026-09-11_falsy_guard_census.py, and fix what you can make fail.

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
| markdown structure debt | **17 / 2** — both known screen false positives |
| `Sequence Safety` comment drift | **zero** across all nine repos |
| residue §4 | **adjudicated, zero content losses** |
| `or {}` population (ml `util/`) | **397 sites / 96 files**; 294 `read`-class, ~117 live |

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

| tool | writes? | question |
| --- | --- | --- |
| `2026-09-11_fleet_required_context_probe.py` | no | **what does each repo's RULESET actually require?** — the premise check 6a needed before any edit |
| `2026-09-11_seqsafety_comment_fanout.py` | **yes** | patch the eight headers; anchors located structurally, not by line number |
| `2026-09-11_seqsafety_fanout_open_prs.py` | **yes** | drive `open_signed_pr.py` once per repo, each with its OWN ruleset id |
| `2026-09-11_seqsafety_fanout_arm_merge.py` | **yes** | arm eight nets WITH A BODY; disarms first, reads back, checks state before body |
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

---

## 7. What was NOT done, and why

- **No independent agent validation was run on this session's own work**, the same
  caveat the predecessor carried. Mechanical cross-checks were substituted: the parsed
  YAML was proven byte-identical before/after in all eight fan-out repos; the new
  `run_suite` tests were mutation-checked (6 of 9 fail against the pre-fix code, and the
  3 that pass are negative controls that must); every 6d verdict is re-runnable from §2.
  Those catch a different class of error than an adversarial reader does.
- **The `or {}` population is measured and NOT triaged** — 117 live read-class sites
  remain, by choice, with the reasoning in §5.
- **`util/ad-hoc/2026-09-06_untyped_json_read_census.py` was NOT deleted.** Ad-hoc
  scripts are provenance of record (owner policy 2026-08-25). Its successor names it and
  the three defects in its docstring, so a reader who finds the old one first is told
  where to go.
- **The 17 residual structure findings are untouched** and need no action; whether to
  record them as a standing note is the owner question in §1.
