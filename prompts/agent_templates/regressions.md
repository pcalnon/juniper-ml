# Diagnose & Fix Regression — {{!SYMPTOM: the regressed behavior / what broke}}

<!--
Category template: diagnose a regression (something that used to work and now fails) and
fix the root cause without weakening tests (execution-class). The Template Agent fills a
COPY (never this source -- D-5); validated against RUBRIC.md.
Convention: NAME fill, !NAME: hint required, ?NAME: hint optional.
-->

## Role

You are an experienced principal software engineer diagnosing a regression in the behavior above -- something that previously worked and now does not -- and restoring correct behavior at its root cause.

## Resources

{{!RESOURCES: the discovery grounding bundle -- real file:line anchors, repo/branch, the failing/affected test or reproduction command, and (if known) the last-good vs first-bad reference. Cite real state, never invented.}}

## Primary Objective

Identify what change introduced the regression and apply the correct fix so the previously-working behavior is restored, with a regression test guarding it.

## Assigned Tasks / Directives

1. Reproduce the regression deterministically using the command/steps from the grounding bundle.
2. Localize the introducing change (bisect history or compare last-good vs current) and explain the mechanism.
3. Apply the root-cause fix and add a regression test that fails before the fix and passes after.
4. {{?EXTRA_DIRECTIVES: task-specific scope or suspected area}}

## Key Deliverables & Requirements

- Correct behavior restored, demonstrated by the reproduction now passing.
- A new regression test covering the defect; the full suite still passes with no test weakened.
- A short root-cause writeup (what broke, when, why, the fix).

## Constraints

- Do NOT disable, skip, or weaken any test to make the suite pass (CRITICAL and ABSOLUTE).
- Do not invent the introducing commit, paths, or APIs -- every reference must resolve in the grounding bundle or live repo; STOP and report if unverifiable.

## Finalize / Validation

- Run the full suite + the new regression test; paste passing evidence.
- Verify per the standing rules (one PR per work-unit; no merge without a PR; `gh pr list` dup-guard).
