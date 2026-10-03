# HANDOFF — Cursor fleet round 2: repaired, not ratified, and the screen that hid half of it

**Date**: 2026-09-10 (merged 2026-09-11 UTC)
**Session**: `2db9c4aa-8815-4ae4-8faa-cba1ecfd4f41` (`https://claude.ai/code/session_0142dJD2GUxBkoWxbieagNGQ`)
**Worktree**: `juniper-ml/.claude/worktrees/elegant-watching-chipmunk`
**Shipped**: **juniper-ml#1886**, squash `7f533b4d` on `main`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_cursor-fleet-round-2-tail-closed-and-validation-overturned-four-conclusions.md`

---

## 1. Goal statement for the next thread

```text
Continue the cursor-fleet round-2 arc for juniper-ml. Items 1-4 of the 2026-09-09 handoff
are MERGED in #1886 (7f533b4d), item 5 is DISSOLVED rather than done, and 6c/6e are closed.
THREE items remain, all measured, none of them started.

Completed so far (verified on main by CONTENT, not by a sha stamp):
- Whole-tree markdown structural debt 63 problems / 14 files -> 17 / 2. Both survivors are
  screen FALSE POSITIVES that no repair can clear without lying about content: the ```text
  banner at STANDING-ITEMS:1103 (13) and the ````jinja2 template sample at
  PROMPT-ANALYSIS:816 (4).
- Item 1: the jinja2 fence. Fixed by lengthening the WRAPPER to four backticks, not by
  retagging the inner pair -- that would change what the template is documented to emit.
- Item 2: four §3.2 rows restored byte-identical to 22c32bd1. 4da40fe9 deleted header,
  separator and rows in ONE hunk while padding four others: a reformat that ate the top of
  a table, not a removal of four suites.
- Item 3: all TEN symlinks retargeted, two recipes, every mapping read from
  `git show 432ed644 --diff-filter=R` at R100. Zero dangling on main; 12 tracked links.
- Item 4: SEPARATOR relaxed to GFM's single hyphen (this was a REQUIRED-GATE defect, not
  accounting), fence walk rewritten to CommonMark, symlink aliases deduped AND named.
- NOT in the predecessor at all: notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md:1046 had
  two documents welded onto one line, leaving a ```python fence open across 161 lines and
  ten H2s. It sat INSIDE the set an owner was asked to ratify as benign.
- Item 6c: REOPENED by ml#1881 (branched before ml#1880, reverted three of its six sites
  nine hours later). Restored with current numbers.
- Item 6e: was ONE missing suite in the handoff, THREE in ml#1883; it was 49. The list
  relocated to docs/REFERENCE.md § Test Suite Reference. Set difference now 0.

Remaining work, in priority order:
1. 6a CROSS-REPO FAN-OUT. All EIGHT sibling sequence-safety.yml files still carry 10-12
   lines of "ADVISORY ... never blocks a merge". MEASURED THIS SESSION by grep over the
   local checkouts. What is NOT verified is the premise: that `Sequence Safety` is actually
   a REQUIRED context in all eight. Check the RULESETS (util/ad-hoc/2026-08-20_require_context_safely.py
   TARGETS), not the workflow files -- a comment and a ruleset are different authorities,
   and this arc has already paid for conflating them. Eight repos, so eight PRs; none of
   them can reuse util/ad-hoc/2026-09-09_required_check_comment_drift.py as-is because it
   hard-codes DEFAULT_RULESET and the juniper-ml API path.
2. 6b THE `or {}` SWEEP. `or {}` occurs across 120 files under util/, the large majority
   legitimate. The predecessor's figure of 28 unguarded chains comes from a census it also
   records as (a) blind to the split-across-lines form and (b) hard-coded to a juniper-ml
   artifact roster, returning NOTHING when pointed at a sibling. FIX THE INSTRUMENT BEFORE
   TRUSTING A NUMBER FROM IT. A clean run from the current census is not evidence.
3. 6d 87 RESIDUE LINES, still unadjudicated -- §4 of
   notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md, one
   commit ever. The arc's only remaining open CONTENT-LOSS question, and the only item here
   that can still turn up lost text.

Key context:
- RE-MEASURE BEFORE ACTING. main took four merges during this session (#1883, #1887 and two
  base syncs). Every number below is timestamped at 7f533b4d.
- The screen is no longer the instrument that hid things, but it still has a KNOWN LIMIT:
  fences nested in blockquotes or list items are invisible to it (215 lines / 10 files of
  residual divergence from markdown-it-py, all pre-existing). Re-run
  util/ad-hoc/2026-09-10_fence_walker_crosscheck.py after any change to it; do not trust
  the unit fixtures alone, which only pin cases their author thought of.
- THREE OF MY OWN NEW TESTS WERE VACUOUS on first write -- they passed against the
  unfixed code. util/ad-hoc/2026-09-10_screen_test_mutation_check.py caught that. Run a
  mutation check on any test written for a fix in the same change as the fix.
```

---

## 2. State at handoff

| | |
| --- | --- |
| `origin/main` at write time | `7f533b4d` — **re-measure; it moves every few minutes** |
| this session's PR | **#1886, MERGED** (squash `7f533b4d`, body 5547 chars, both trailers present) |
| whole-tree structure debt | **17 problems / 2 files** (was 63 / 14) |
| — both survivors | **screen false positives**, not debt; nothing left to ratify |
| dangling markdown symlinks | **0** (12 tracked links, all resolve) |
| screen ↔ CommonMark divergence | **215 lines / 10 files** (was 1972 / 89); −89.1%, none introduced |
| `AGENTS.md` | **28271 / 38000 chars**, headroom **9729** (was 3415) |
| doc test-list vs `ci.yml` | **164 / 164**, set difference 0 in all three directions |

### Verification commands

Run from the repo root on a tree synced to `origin/main`. **Never read a gate's exit code
through a pipe** — and `xargs` additionally remaps any child exit in 1–125 to **123**, so the
screen's exit 2 is invisible through it. The invocations below avoid `xargs`.

```bash
git fetch origin main && git log origin/main --oneline -1

# Whole-tree structure debt. Exit 1 now (findings), NOT 2 -- the ten dangling symlinks that
# made it refuse are repaired, so it examines every tracked path.
git ls-files -z '*.md' > /tmp/md0
python3 - <<'PY'
import subprocess, sys
paths = [p for p in open('/tmp/md0').read().split('\0') if p]
r = subprocess.run([sys.executable, 'util/ad-hoc/2026-09-05_markdown_structure_check.py'] + paths)
print("screen exit =", r.returncode)   # 1 = reported; 2 = refused to report
PY

# Expect: 17 problems / 2 files; "examined 1062 of 1073; 11 symlink alias(es)".
# The alias line is not a skip -- each alias is NAMED. CLAUDE.md -> AGENTS.md is one.

# The instrument's own conformance. Expect 215 disagreeing lines across 10 files, all
# blockquote- or list-nested. A LARGER number means someone widened the walker; a SMALLER
# one means someone fixed container blocks -- either way, read the diff.
python3 util/ad-hoc/2026-09-10_fence_walker_crosscheck.py $(git ls-files '*.md') | tail -3

# Both of these now REFUSE, and the refusal is the proof the repair landed.
python3 util/ad-hoc/2026-09-10_retarget_dangling_note_links.py   # "does not start 'regressions/'"
python3 util/ad-hoc/2026-09-10_restore_recurse_model_suites.py   # "is ALREADY present"

# Zero drift in all three directions (ci.yml / docs / disk).
python3 util/ad-hoc/2026-09-10_agents_md_test_list_drift.py; echo "exit=$?"   # 0

# Zero dangling symlinks.
python3 - <<'PY'
import os, subprocess
rows = subprocess.run(["git","ls-files","-s"],capture_output=True,text=True).stdout.splitlines()
links = [r.split("\t")[1] for r in rows if r.split()[0] == "120000"]
bad = [l for l in links if not os.path.exists(l)]
print(f"tracked symlinks {len(links)}, dangling {len(bad)}", bad)
PY
```

---

## 3. Tools this session built

All on `origin/main` under `util/ad-hoc/`. **Read the docstring first.** `writes?` marks file
mutators; each defaults to dry-run and needs `--apply`, and each asserts its targets first.

| tool | writes? | question |
| --- | --- | --- |
| `2026-09-10_fence_render_probe.py` | no | what does a REAL renderer do with these lines — `CODE` or prose? `--diff-against` shows only what a repair changed |
| `2026-09-10_fence_walker_crosscheck.py` | no | does the screen's fence model agree with CommonMark, over the whole tree? |
| `2026-09-10_screen_test_mutation_check.py` | no | **do the new tests discriminate, or pass against the unfixed code too?** |
| `2026-09-10_loss_check_changed_docs.py` | no | run the loss check over EVERY markdown file a PR touches, not one pair |
| `2026-09-10_agents_md_test_list_drift.py` | no | which suites does CI run that the docs do not name (all three directions)? |
| `2026-09-10_retarget_dangling_note_links.py` | **yes** | repoint the ten links, two recipes, post-condition resolves every one |
| `2026-09-10_restore_recurse_model_suites.py` | **yes** | restore the four §3.2 rows from the PRE-RENAME blob |
| `2026-09-10_repair_cascor_demo_concat.py` | **yes** | split the welded line and close the fence it left open |
| `2026-09-10_relocate_test_command_list.py` | **yes** | move the 164 commands out of the budget-governed file |

**Two carry a limit worth stating, because a clean run from either is not evidence:**
`fence_walker_crosscheck.py` compares only fence membership — a table defect is invisible to
it. `loss_check_changed_docs.py` reports atom loss, and **a fence repair always trips it**:
un-fencing lines removes them from `fenced_lines()` while the text never moves. Adjudicate
by asking whether each reported atom is still present as a raw line.

---

## 4. Traps this session paid for

1. **A boolean fence toggle produces a confident wrong answer, never an error.** It
   mis-located the CASCOR_DEMO damage twice across two review rounds — `:1454` in round 1,
   "the file is balanced" in round 2. It *is* balanced. Balance was the wrong question; the
   right one is which lines land inside a block, and 161 of them did.
2. **A test written after the fix can pass against the code before it.** Three of six new
   fence tests were vacuous: the old toggle happened to come out balanced on those
   fixtures. Only a mutation check distinguishes a test from a decoration.
3. **A stale branch reverts a shipped contract.** ml#1881's parent *is* ml#1880, and it
   still re-introduced the figure ml#1880 had just corrected, in two of six files. A figure
   duplicated across files does not stay corrected.
4. **Do not cite a PR number for the PR you are opening.** I wrote `ml#1883` into eight
   files assuming it would be mine; #1883 was taken by an unrelated PR that merged
   mid-session. Cite dates. Grep the diff for `#NNN` before pushing.
5. **`open_signed_pr.py` would have destroyed ten symlinks.** It base64s `read_text()`, and
   `createCommitOnBranch` has no mode field, so a `120000` link becomes a `100644` file
   holding the target's content. The signing hang is CONDITIONAL on the gpg-agent PIN
   cache — probe it (`timeout 25 gpg --detach-sign`) rather than assuming; it returned 0
   here and a local signed commit preserved every mode.
6. **Re-arming the auto-merge net needs `--disable-auto` FIRST.** `gh pr merge --auto
   --subject --body-file` against an already-enabled PR exits 0, prints nothing, and changes
   nothing. The fields are `null`, not `""`, so `commitBody|length` reads 0 either way — a
   non-zero value is the only proof the re-arm took. **This mattered: #1886 was merged by
   the NET, not by safe_merge's local path**, so without the re-arm the squash would have
   shipped subject-only and dropped both trailers.
7. **`safe_merge` refusing is exit 0, and the refusal is the useful output.** It refused on
   two unresolved CodeQL threads. Both were real defects in my own new scripts — an
   `if True:` left by my own `sed` edit, and implicit string concatenation inside a list
   literal whose entries become markdown LINES (a missing comma there welds two lines with
   no error anywhere). Fixed, not suppressed.
8. **The `Verify AGENTS.md Last Updated` gate uses UTC.** Local 2026-09-10 was already
   2026-09-11Z.

---

## 5. Decisions made — do not re-litigate

- **Item 5 (record the ratification) is DISSOLVED, not deferred.** The owner ruled "fix live
  `notes/` only, ratify the rest" without knowing the ratified set held real defects. It held
  five, including 161 swallowed lines in `notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md`.
  They are repaired rather than recorded. The only thing left to accept is 17 findings in 2
  files that are provably screen artifacts. **Open question put to the owner in #1886's body,
  unanswered at handoff:** whether that residue should still be written down as a standing
  note. It needs no action to stay correct.
- **The jinja2 fence is fixed by lengthening the WRAPPER**, resolving the predecessor's
  unresolved dissent. A closing fence cannot carry an info string and a longer bare run still
  closes a 3-backtick opener, so retagging the inner pair only works if they become `~~~` —
  which would change what the template is documented to emit. Four backticks leave the
  sample's bytes untouched.
- **The test-command list MOVED rather than being completed.** Measured, not preferred:
  completing it in `AGENTS.md` lands at 37466 of a 38000 ceiling — **534 chars of headroom**,
  below the +605 a single documentation PR has already been measured to cost.
- **`DEVELOPER_CHEATSHEET-ORIGINAL.md:22` got an ADDED header, not a recovered one.** The
  table has had a delimiter row and no header since its first commit; nothing was lost, so
  nothing could be restored. This is the one judgement call in the PR and is flagged as such.
- **The generated agent-suite plan's lost command line was NOT invented.** Only the missing
  ` ```bash ` opener was restored; the first line of the command `3d9b69db` dropped is gone
  and is left gone.

---

## 6. Documents this handoff references or changes

**References**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_cursor-fleet-round-2-tail-closed-and-validation-overturned-four-conclusions.md`,
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`,
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md`,
`notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md`,
`notes/JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md`,
`notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md`,
`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md`,
`notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md`,
`notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md`,
`notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md`,
`prompts/agent_templates/README.md`, `prompts/manual/prompt053_2026-03-30.md`,
`prompts/generated/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-26_2048.md`,
`docs/REFERENCE.md`, `AGENTS.md`, `conf/memory_budget.json`.

**Changed** (this file, plus everything merged in #1886):
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_cursor-fleet-round-2-repaired-not-ratified-and-the-screen-that-hid-it.md`;
`AGENTS.md`, `docs/REFERENCE.md`, `.github/workflows/ci.yml`,
`util/markdown_structure_delta.py`, `util/ad-hoc/2026-09-05_markdown_structure_check.py`,
`tests/test_markdown_structure_screen.py`, `tests/test_markdown_structure_delta.py`,
`notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md`,
`notes/JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md`,
`notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md`,
`notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md`,
`notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md`,
`prompts/agent_templates/README.md`, `prompts/manual/prompt053_2026-03-30.md`,
`prompts/generated/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-26_2048.md`,
the ten retargeted symlinks under `notes/legacy/` and `notes/development/`, and the nine new
`util/ad-hoc/2026-09-10_*.py` tools listed in §3.

---

## 7. What was NOT done, and why

- **No independent validation was run on this session's own work.** The predecessor's record
  (§7 of the 2026-09-09 handoff) is that validation overturned eight of its claims and a
  second round found five more introduced by the fix pass. This session substituted
  *mechanical* cross-checks for that — a CommonMark reference parser over all 1073 files, a
  mutation check on every new test, and a whole-change-set loss screen — which catch a
  different class of error than an adversarial reader does. **A reader who wants the claims
  in §2 checked should re-derive them from the verification block, not trust this file.**
  The numbers are the least trustworthy part of any document written by the agent that
  produced them.
- **Items 6a / 6b / 6d are untouched**, with the scoping in §1. 6a needs the ruleset premise
  verified before any PR; 6b needs its instrument fixed before its number is worth anything;
  6d is the only remaining item that can still surface lost text.
- **`git_sha` was not trusted anywhere.** Every claim in §2 was re-derived from file content
  on a tree synced to `origin/main` after the merge.
