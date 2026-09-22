# CI-budget arc — the five owner decisions executed, and the four defects that surfaced

**Date**: 2026-09-17
**Repo**: juniper-ml (plus eight sibling repos for decision D)
**Author**: Paul Calnon
**Status**: RECORD of a completed arc. Every figure below was re-measured at the commit named
beside it; none is transcribed from the handoff that opened the arc.

Opened from
[`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md)
§3, which left ten items — four of them owner decisions.

---

## 0. Net effect

| | before the arc | after |
|---|---|---|
| Whole-tree markdown structure problems | 63 across 14 files (`e173ea81`) | **0 across 1095 paths** (`e7c191c1`) |
| PRs adding a `##`-bearing code block | **failed a required check** | pass |
| Open-PR budget alarm | juniper-ml only | **all 9 repos** |
| Weekly lockfile PR | opened with **zero checks** | triggers CI (App-token arm) |
| `md_structure_check.py` blind spots | documented, not fixed | **fixed**, and soaking in CI |
| Withdrawn rationales still shipped | 2 | 0 |

**Merged**: ml#1880 `db627616` · ml#1944 `2f8653c6` · ml#1946 `668ae575` · ml#1955 `e7c191c1`,
plus eight sibling-repo PRs listed in §4.

---

## 1. Decision A — `juniper-cascor-client`'s 3300 s budget

**Ruled**: the value STANDS; the row stays excluded from `KillResilienceTest`'s pin.

The budget exceeds 4× its p90 (724 → 2896), so it is excluded rather than enforced. Its historic
rationale — *"15,616 s is queue time"* — was already refuted by ml#1828 as a v1 bot-check-run
artifact (real max 1511 s). What remained false was the closing clause of the entry in
`util/safe_merge.py`: *"so it is left for an owner ruling."*

That clause is now the ruling itself, with the pinnable window `(observed max, 4× p90]` recorded
for whenever the repo next comes into play — and an instruction to **re-measure** rather than
reuse the figures, which have a shelf life of days.

**No budget value changed anywhere in this arc.**

---

## 2. Decision B — the structure debt: nothing to repair

**Ruled**: repair symlinks + the top three files. **Executed**: nothing, and that is the finding.

Two things had already happened by the time the decision was executed:

1. ml#1886 repaired the real damage — the unclosed fences and the missing table separators — and
   resolved the ten dangling symlinks by creating `notes/regressions/`.
2. That left 17 findings across 2 files. **All 17 were false positives.**

| file | fence | findings | what it actually is |
|---|---|---:|---|
| `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md` | ` ```text ` @1103, **closed** | 13 | ASCII banner art whose border character is `#` |
| `notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` | ` ````jinja2 ` @816, **closed** | 4 | a Jinja template whose `## Overview` lines are template OUTPUT |

Repairing either would have meant making the document wrong — retagging a Jinja block as
`markdown`, or editing a banner specimen so it misreports what the tool prints. **When every
available repair makes a document less true, the instrument is what is wrong.**

See §6.1 for what that instrument was doing to CI.

---

## 3. Decision C — the lockfile PR that arrived with no checks

**Ruled**: reuse the release-train App, then fan out. **Executed**: fixed here; the fan-out was
empty, and proving that took two probes.

`.github/workflows/lockfile-update.yml` opened its weekly PR through
`peter-evans/create-pull-request` with **no `token:` input**, so it fell to `GITHUB_TOKEN` — and a
`GITHUB_TOKEN`-authored PR does not trigger `pull_request` workflows. The PR arrived with zero
checks every week. The header's *"No additional secret is required for the common case"* is what
made that read as fine.

> **Refined 2026-09-22** (the re-evaluation in
> [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md)).
> "Does not trigger" is right in effect and incomplete as a mechanism. All 18 `GITHUB_TOKEN` PRs
> this workflow opened (#325–#1932) ran **zero jobs** at opening, in two shapes. 5 got no
> `pull_request` run at all, the latest #1139 on 2026-08-17. 13 had their runs **created** and
> parked at `action_required`: 12 of those were released by the owner re-running them, #1806 by a
> close/reopen. The fix is verified by effect: #1970 (2026-09-21), the first weekly PR after it,
> ran jobs in all 5 of its opening-commit `pull_request` runs on attempt 1, under
> `juniper-release-train[bot]`. That is one week, `n = 1`.

**No new secret was needed.** `release-train.yml` already mints a `create-github-app-token`
(`RELEASE_TRAIN_APP_ID` = 4362741) for exactly this reason. The same pattern now gates on that
variable, with `GITHUB_TOKEN` fallback when unset, and the token is scoped to the **current
repository only** (both `owner` and `repositories` omitted, which the action documents as
"access will be scoped to only the current repository").

### 3.1 The fan-out probe that was wrong

The first sweep asked `"token:" in file` across every repo's `lockfile-update.yml` and reported
**six already fixed**. That was a correct predicate over the wrong question. `juniper-cascor`
disproves it: its `lockfile-update.yml` is a *different workflow* — a dependabot regenerator whose
`token:` sits on `actions/checkout` and which pushes to an existing PR branch rather than opening
one. Same filename, unrelated design.

The right question was narrower: **does a step that OPENS a PR run on the built-in token?**
Re-probed across every workflow in all nine repos, **only juniper-ml used that action at all**.
So "fix here, then fan out" collapsed to "fix here" — which the first probe would have turned into
six unnecessary changes to workflows that did not have the defect.

---

## 4. Decision D — the alarm, fleet-wide

**Ruled**: stale-at-scale documentation DOES count as damage for the staged-escalation trigger of
[`JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md)
§4 decision 6 — and roll the detector out to all eight remaining repos.

That ruling is what made the roll-out load-bearing rather than tidy: cursor-fleet round 2 hit
**four** repos and the detector existed on **one**, so an escalation rule could not have fired on
three of the four.

Merged: `juniper-cascor#654` · `juniper-data#403` · `juniper-data-client#205` ·
`juniper-cascor-client#166` · `juniper-cascor-worker#187` · `juniper-canopy#635` ·
`juniper-deploy#218` · `juniper-recurrence#171`. All eight verified live on their default
branches by content, not by the roll-out script's own report.

### 4.1 One deliberate divergence from juniper-ml's copy

juniper-ml skips its Slack step **silently** when `SLACK_WEBHOOK_URL` is unset. Correct there — it
has the secret. A trap on all eight targets, none of which do: **a detector that cannot notify
looks exactly like a detector with nothing to report.** The ported copy emits a `::warning::`
annotation on a breach with no webhook. The run still never fails.

The substitution is anchored on the source's exact text, so editing the source makes
`util/ad-hoc/2026-09-15_fan_out_pr_budget_alarm.py` fail loudly rather than ship an unported copy.

---

## 5. Decision E — blind spots first, then ratification and wiring

**Ruled**: fix the blind spots, then re-evaluate. Both halves are done.

### 5.1 The blind spots (ml#1944)

`util/ad-hoc/2026-09-05_md_structure_check.py` — the standalone verifier, wired into nothing —
had five documented-but-unfixed defects. All five are fixed: the VCS command joined the `CODEY`
allowlist (~7% of `docs/REFERENCE.md`'s command lines were invisible), C2 counts multiplicity
instead of set membership, C4 compares heading TEXTS so a loss and a gain no longer cancel, every
vacuous run exits 2, and an ADDED file is checked absolutely rather than skipped.

**C3 had the identical set-membership defect as C2 and was not in the documented list at all.** It
was found by reading the neighbour while fixing C2 — see §6.4.

New suite `tests/test_md_structure_check.py` (15 tests) is wired into `.github/workflows/ci.yml`
and named in `docs/REFERENCE.md`; all three lists agree at 166.

### 5.2 Ratification — withdrawn (ml#1955)

The checker justified C2's base-relative form by pointing at *"6 in a pre-existing
`memory_index_check` block"* in `docs/REFERENCE.md`.

**Those six were not pre-existing.** They were juniper-ml#1746's residue — a `### Usage` section
whose six `python3 util/memory_index_check.py …` commands sat unfenced and rendered as prose.
[`HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md)
said explicitly to fence them rather than ratify them as `base 6` — and that instruction was
carried unactioned through three handoffs.

The checker's own output is the proof, run with `main` as base:

```text
[ OK ] docs/REFERENCE.md  fences=194 headings=409 unfenced=0 (base 6)
```

`base 6` → `unfenced=0`. Withdrawn, not reworded: **calling damage "pre-existing" is how a
base-relative check quietly grandfathers the thing it was built to find.**

### 5.3 Wiring — advisory soak, decided on a backtest

Replayed the checker over the **33 markdown files changed in 40 commits** of real history:

| | |
|---|---:|
| False positives | **0** |
| True positives | **1** |
| Vacuous passes | **0** |

The one finding was real and the required gate cannot see it: an orphaned
`| inode pressure | … |` row with no header in
[`JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`](JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md),
rendering as plain text. Repaired; the backtest is clean at 33/33.

**That is the case for wiring at all.** C2 and C4 cover two damage classes nothing gates. C2
catches a removed ` ```bash ` fence **pair** — parity stays even, no heading is swallowed, every
other check passes, and 17 lines of shell silently become prose.

**It is advisory, not required.** 33 files is a small sample and `CODEY` is an allowlist that
could fire on prose opening with `make` or `cd`. Making a screen required on that evidence is
precisely what produced the defect in §6.1. Promotion follows the owner-ratified path
(`JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md` §4 decision 8): soak
advisory, then promote **in the ruleset** — never via the Quality Gate's `needs:`.

---

## 6. The four defects the decisions surfaced

None of these was on the list. Each was found while executing something else.

### 6.1 A required check was failing PRs for defects they did not contain

`util/ad-hoc/2026-09-05_markdown_structure_check.py` — the screen the CI gate imports — flagged
any `## ` line inside any fence not tagged `markdown`. `util/markdown_structure_delta.py` grades
an **added** file against a baseline of **zero**, and its step runs in the `docs` job whose name,
`Documentation Links`, is a **required** status check.

Demonstrated end to end on an eleven-line synthetic note containing an ordinary ` ```text `
banner: **2 problems against a baseline of 0 → required check FAILS.**

The screen's own `SEPARATOR` comment records the identical failure from the `-{2,}` regex — *"a PR
adding any markdown file with a valid single-hyphen delimiter row failed a required check, for a
defect that was not in the PR"* — **repeating in the adjacent rule.**

Narrowed: an H2 inside a fence is reported only when that fence is UNCLOSED or carries no info
string. Nothing real escapes — a dropped closer leaves the fence unclosed, which is reported in
its own right *and* makes its H2s reportable again; the bare-fence arm keeps the two-closes-lost
heuristic, and ml#1746's own fence was bare.

### 6.2 The "structure debt" four handoffs tracked was largely not debt

The count moved 104/23 → 102/21 → 63/14 → 73/15 → 63/14 → 17/2 → **0/0** across ten days. The last
17 were §6.1's false positives. The earlier drops were ml#1834 and ml#1886 repairing real damage.

Every site quoting the figure now carries **a commit and a date** rather than a timeless
present-tense count, and states why zero does **not** make the delta scoping redundant: the count
regresses the moment damage lands, and an untouched file is still not the PR's problem.

### 6.3 `PUT /contents` does not sign, and the failure is silent

The roll-out's first eight commits were created through the Contents API. Result:
`verified: false, reason: "unsigned"`. `required_signatures` is in every repo's ruleset, so all
eight PRs sat at `mergeStateStatus: BLOCKED` with **every required context green, zero failing,
zero pending** — and the blocking rule does not appear in `gh pr checks` at all.

| API | committer | verification |
|---|---|---|
| `PUT /contents` | the authenticated user | **`verified: false`** |
| GraphQL `createCommitOnBranch` | `web-flow` | `verified: true` |

Repair had its own trap: an unsigned commit *anywhere* in the branch blocks the merge and squash
does not rescue it, so it must leave history — force-reset to base, re-commit through the
mutation. That momentarily leaves the branch with no diff, which **closes the PR**. All eight
closed silently and were reopened onto the signed commits.

The script now verifies the signature after committing rather than assuming it.

### 6.4 A correct predicate over an incomplete set — four times, including twice by this arc

This is the shape all four share, and the arc's own validation record names it twice already.

| where | the predicate | what it missed |
|---|---|---|
| The handoff's §3 item 7 | `grep -c "102 structural" ci.yml REFERENCE.md` | the figure was live in **six** sites, not the two the grep named |
| This arc's C fan-out probe | `"token:" in file` | six repos "already fixed" that had a different workflow entirely (§3.1) |
| Decision E's blind-spot list | the documented list of four | **C3 had C2's defect and was not on it** |
| ml#1944's own verification | the same two-file grep | caught only because the residual sweep was widened |

The lesson is not "grep more carefully". It is that **a predicate and its site enumeration are two
separate claims**, and a check that validates only the first reports success over whatever the
second happened to include.

---

## 7. What is still the owner's

1. **`SLACK_WEBHOOK_URL` on the eight sibling repos.** The alarms are live and running, but with
   no webhook they report to the Actions tab only. This is the gap between the §4 ruling being
   enforceable and being decorative, and it is the only item in this arc that cannot be closed
   from a session.
2. **Promoting the §5.3 soak** once it has run clean on enough real PRs — a ruleset change, adding
   the job name `Markdown Structure (advisory soak)` as a required context and dropping the step's
   trailing `exit 0`.
   > **Corrected 2026-09-22.** Dropping the trailing `exit 0` does not make the check able to fail:
   > the `if` before it becomes the last command and returns 0 either way. The step must end in
   > `exit "$rc"`. The soak has also not run clean — 7 false findings in its first four days, every
   > one present at its PR's final head — so the evidence is currently against promotion. Record:
   > [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md)
   > § Re-evaluation 2026-09-22.
3. **`juniper-cascor-client`'s budget** if that repo comes back into play (§1) — re-measure first.

---

## 8. What this record cannot support

- That the §5.3 backtest generalises. 33 files over 40 commits is a small, recent, and
  self-selected sample — it is the evidence for a **soak**, not for promotion.
- That the structure count will stay at zero. It is a moving floor; it moved six times in ten days.
- That §6.4 is the complete list of incomplete-set errors in this arc. It is the list of the ones
  that were caught.

---

## 9. Documents

**REFERENCED**:
[`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md),
[`HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md),
[`JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`](JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md),
[`JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`](JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md),
[`JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`](JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md),
`util/ad-hoc/README.md`.

**CHANGED across the arc** — `docs/REFERENCE.md`, `AGENTS.md`,
`JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`, and this file.

**CODE AND CONFIG CHANGED** — `util/safe_merge.py`,
`util/ad-hoc/2026-09-05_markdown_structure_check.py`,
`util/ad-hoc/2026-09-05_md_structure_check.py`, `util/markdown_structure_delta.py`,
`util/ad-hoc/2026-09-15_fan_out_pr_budget_alarm.py` (new),
`tests/test_markdown_structure_screen.py`, `tests/test_markdown_structure_delta.py`,
`tests/test_md_structure_check.py` (new), `.github/workflows/ci.yml`,
`.github/workflows/lockfile-update.yml`, and `.github/workflows/pr-budget-alarm.yml` in each of
the eight sibling repos.
