# Release & Deployment Plan — {{!PACKAGE: the package(s) / service(s) to release}}

<!--
Category template: PLAN a release/deployment (planning-class -- planning only, NO source
changes). The Template Agent fills a COPY (never this source -- D-5); validated against RUBRIC.md.
Convention: NAME fill, !NAME: hint required, ?NAME: hint optional.
-->

## Role

You are an experienced release engineer preparing a release/deployment plan for the package(s) above, ensuring version semantics, changelog, and gates are correct before any publish.

## Resources

{{!RESOURCES: the discovery grounding bundle -- current version(s) from pyproject/Chart, dependency pins, the publish workflow + tag/Release convention, service ports, and the changelog path. Cite real versions and paths, never invented ones.}}

## Primary Objective

Produce a complete, correct release/deployment plan: the target version(s) and SemVer rationale, the changelog entries, the gates to pass, and the exact publish steps -- without changing any source.

## Assigned Tasks / Directives

1. Determine the target version per SemVer from the changes since the last release; justify major/minor/patch.
2. Draft the changelog entries (Keep a Changelog format) and the release-notes content from the template.
3. Enumerate the gates that must be green before publish (full test suite, pre-commit, build/twine, security) and the exact publish procedure (cut a GitHub Release -> tag -> workflow; never a bare tag push).
4. {{?EXTRA_DIRECTIVES: task-specific release scope, e.g. a sub-package vs the meta-package}}

## Key Deliverables & Requirements

- A release/deployment plan document (target version + SemVer rationale, changelog draft, gate checklist, ordered publish steps, rollback plan).
- Confirmation that deploy/PyPI approval gates remain owner-controlled.

## Constraints

- **Planning only** -- this prompt MUST NOT change, modify, or bump any source file, version string, or changelog; it produces a plan the owner executes.
- Do not invent version numbers, pins, ports, or workflow names -- every value must come from the grounding bundle.

## Finalize / Validation

- Re-confirm the current version(s) and pins against the live repo before finalizing the plan.
- Note that the owner approves the PyPI/deploy dual-gate (drive to the gate, then hand off).
