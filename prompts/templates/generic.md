# {{CATEGORY_TITLE}}

<!--
Generic fallback prompt template for the Juniper custom-agent suite.
The Template Agent instantiates a COPY of this file and fills it (it never edits this
source -- D-5). Fill every required slot; fill or drop optional slots as the task
warrants. If a task of this shape recurs, propose promoting the filled copy into a new
named template (a new prompts/templates/<id>.md + a manifest.yaml entry).
Placeholder convention: NAME = fill, !NAME: hint = required, ?NAME: hint = optional
(each wrapped in double braces; enforced by tests/test_template_library_drift.py).
-->

## Role

{{!ROLE: the expert role the agent should adopt, e.g. "principal software engineer for <repo>"}}

## Resources

{{!RESOURCES: concrete grounding -- real file and line anchors, repo and branch, relevant docs and conventions. Inject the discovery grounding bundle here so the prompt cites real facts, not invented ones.}}

## Primary Objective

{{!PRIMARY_OBJECTIVE: a faithful one-paragraph restatement of the task intent and the desired outcome}}

## Assigned Tasks / Directives

{{!DIRECTIVES: ordered, unambiguous, individually verifiable steps the agent must perform}}

## Key Deliverables & Requirements

{{!DELIVERABLES: enumerate deliverables with measurable acceptance criteria -- named tests pass, lint clean, specific files written, observable behavior; avoid adjective-only criteria like "works correctly"}}

## Constraints

{{?CONSTRAINTS: hard limits -- do-not-touch areas, standing conventions (worktree isolation, one PR per work-unit, line-length 512), anti-hallucination doctrine (verify-before-claim, cite file and line, do not invent APIs/paths/flags)}}

## Finalize / Validation

{{?VALIDATION: how to verify success and how to recover or abort -- run the named tests/lint, no merge without a PR, worktree cleanup only on merge, gh pr list dup-guard}}
