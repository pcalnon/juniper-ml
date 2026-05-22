# AGENTS.md Header Standardization Plan

**Created**: 2026-05-22
**Author**: Paul Calnon (with Claude Opus 4.7)
**Status**: Phase 1 in flight (this PR); Phases 2–4 deferred

---

## Motivation

Audit on 2026-05-22 revealed that the `**Last Updated**:` header in
each Juniper repo's `AGENTS.md` drifts silently:

| Repo                  | Header value     | Git mtime of AGENTS.md | Drift   |
| --------------------- | ---------------- | ---------------------- | ------- |
| juniper-ml            | *(field absent)* | 2026-05-21             | n/a     |
| juniper-canopy        | *(field absent)* | 2026-05-18             | n/a     |
| juniper-data          | 2026-04-02       | 2026-05-21             | ~50 d   |
| juniper-cascor        | 2026-04-02       | 2026-05-18             | ~46 d   |
| juniper-cascor-worker | 2026-04-02       | 2026-05-18             | ~46 d   |
| juniper-cascor-client | 2026-04-02       | 2026-05-21             | ~50 d   |
| juniper-data-client   | 2026-04-02       | 2026-05-21             | ~50 d   |
| juniper-deploy        | 2026-04-02       | 2026-05-18             | ~46 d   |

The uniform `2026-04-02` across six repos points to a bulk update
that day, with no maintenance since. juniper-ml and juniper-canopy
use a "minimal header" format that omits the field entirely.

Manual maintenance has lost. The same playbook the prior session
applied to AGENTS.md `**Version**:` drift (lint + CI fanout, see
juniper-ml#305) is the model here, plus a CI auto-bump workflow so
contributors (and Claude) don't have to remember to update the date
manually.

---

## Canonical Schema

Six required fields, in this relative order. Extra fields (e.g.
`**Python**:` in juniper-cascor-worker) may be interleaved freely.

```markdown
**Project**: <descriptive name>
**Repository**: <github-org>/<repo-name>
**Author**: <name>
**License**: <license string>
**Version**: <X.Y.Z>
**Last Updated**: <YYYY-MM-DD>
```

Lint rules:

| Field          | Required | Format check                              |
| -------------- | -------- | ----------------------------------------- |
| Project        | yes      | non-empty                                 |
| Repository     | yes      | non-empty                                 |
| Author         | yes      | non-empty                                 |
| License        | yes      | non-empty                                 |
| Version        | yes      | non-empty (semver-equality vs pyproject already linted by `test_agents_md_version_drift.py` where pyproject exists) |
| Last Updated   | yes      | `YYYY-MM-DD` ISO 8601 date                |

---

## Three Deliverables

1. **`tests/test_agents_md_header_schema.py`** — portable lint
   (self-locating from `<repo>/.github` sibling); asserts presence,
   canonical relative order, non-empty values, ISO date format.
2. **`.github/workflows/agents-md-touch-up.yml`** — new workflow,
   triggers on `pull_request` types `[opened, reopened, synchronize]`
   with `paths: ["AGENTS.md"]`. Reads the current `**Last Updated**`
   value; if it differs from today's UTC date, sed-rewrites the
   line, commits as `github-actions[bot]` with `[skip ci]`, rebases
   against any concurrent pushes, force-safe-pushes back. Idempotent.
3. **Per-repo AGENTS.md standardization** — bump 6 stale, add full
   header block to juniper-ml & juniper-canopy.

---

## Rollout Phases

| Phase | Work                                                                                            | PR count   |
| ----- | ----------------------------------------------------------------------------------------------- | ---------- |
| 1     | Build canonical artifacts in juniper-ml: lint + workflow + standardize juniper-ml's AGENTS.md   | 1          |
| 2     | Bump the 6 stale `Last Updated` values to today                                                 | 6          |
| 3     | Add full header block to juniper-canopy + adopt lint + workflow                                 | 1          |
| 4     | Adopt lint + workflow in remaining 6 (port test + workflow file)                                | 6          |
| Total |                                                                                                 | **14**     |

**Phase 1 is this PR.** It is the canonical source of truth for the
schema, the lint, and the workflow. Subsequent phases port these
artifacts (copy-paste, no per-repo changes) and standardize each
sibling's AGENTS.md header.

---

## Open Questions / Follow-ups

- Should `juniper-ci-tools` v0.4.0 ship `juniper-lint-agents-md-header`
  as a console script, mirroring the `juniper-lint-workflow-paths`
  (v0.2.0) and `juniper-lint-agents-md-version` (v0.3.0) precedents?
  This would let consumer repos install a single PyPI dependency
  instead of carrying the inline `util/test_agents_md_header_schema.py`
  copy. Deferred to Wave 4 of this plan; out of scope for Phase 1.
- The auto-bump workflow uses `[skip ci]` to prevent recursion.
  This means the bump commit itself does not exercise the main CI;
  it relies on the lint's idempotency to be safe. Acceptable.
- Optional fields (`**Python**:`, `**Status**:`, etc.) are
  permitted but not validated. A future iteration could pin a
  per-repo allow-list of optional fields if drift becomes a problem.
