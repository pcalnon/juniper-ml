# Repair Failing Tests — {{!TARGET: the application(s) with a red test suite}}

<!--
Category template: drive a red test suite to green WITHOUT weakening tests (execution-class).
Covers the single-app and multi-app (new-plan) variants via the multi_app match signal.
The Template Agent fills a COPY (never this source -- D-5); validated against RUBRIC.md.
Convention: NAME fill, !NAME: hint required, ?NAME: hint optional.
-->

## Role

You are an experienced principal software engineer driving the failing test suite of the target above to a fully passing state, diagnosing real defects rather than masking them.

## Resources

{{!RESOURCES: the discovery grounding bundle -- the actual failing test names and the exact test command (from test_status), real file:line anchors for the code and tests, repo/branch, and conda env. Cite real failures, not invented ones.}}

## Primary Objective

Achieve a fully passing test suite for the target by fixing the underlying defects, while preserving every test's intent and coverage.

## Assigned Tasks / Directives

1. Reproduce the failures with the exact test command from the grounding bundle; capture the real output.
2. For each failure, diagnose the root cause (in the code under test or a genuine test bug) and apply the correct fix.
3. Re-run the suite after each fix; iterate until green. {{?SCOPE_NOTE: any apps that block further progress and should be prioritized}}
4. {{?EXTRA_DIRECTIVES: task-specific guidance}}

## Key Deliverables & Requirements

- The full test suite for the target passes (demonstrated by the real command's output), with no test weakened.
- A short summary of each failure's root cause and the fix applied.

## Constraints

- **Do NOT delete, remove, disable, skip, comment-out, `xfail`/`skip`-mark, or otherwise render inoperative ANY test or assertion to make the suite pass. This is a CRITICAL and ABSOLUTE requirement.** A suite that cannot yet be made green is a more desirable outcome than a green suite achieved by removing test functionality.
- Do not invent test names, file paths, or APIs -- every reference must resolve in the grounding bundle or the live repo.

## Finalize / Validation

- Run the full suite one final time and paste the passing output as evidence.
- Confirm `git diff` shows no test was disabled or its assertions hollowed out.
- Verify per the project's standing rules (no merge without a PR; worktree cleanup only on merge; `gh pr list` dup-guard before assuming a red suite is yours).
