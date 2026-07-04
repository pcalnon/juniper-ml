# Juniper — `notes/` File Naming Convention

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**Document Type**: Convention (design-of-record)
**Status**: Ratified (owner decision 2026-07-04)
**Last Updated**: 2026-07-04

---

## 1. Format

Every document in `notes/` (and its content subdirectories) is named:

```text
JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<CONTENTS-DESCRIPTION-PHRASE>.md
```

Example: `JUNIPER_2026-07-03_JUNIPER-CANOPY_CONTROL-SURFACE-AUTH-AND-NAT-DESIGN.md`

Underscores (`_`) separate only the four fields; hyphens (`-`) join words **within** a field. The
description phrase is UPPER-KEBAB-CASE (`[A-Z0-9-]`); no other underscores, spaces, or lowercase.

## 2. Fields

| Field | Rule |
| ----- | ---- |
| `JUNIPER` | Literal prefix, always. |
| `<YYYY-MM-DD>` | The document date. For new documents: the date the document is created (or last substantively re-issued). For the 2026-07-04 migration: the date already embedded in the old filename when present, else the file's last git-commit date (worktree mtimes are checkout-time and therefore unusable). |
| `JUNIPER-<REPO>` | The subject repository: `ML`, `CANOPY`, `RECURRENCE`, `CASCOR`, `CASCOR-CLIENT`, `CASCOR-WORKER`, `DATA`, `DATA-CLIENT`, `DEPLOY`, or `ECOSYSTEM`. |
| `<CONTENTS-DESCRIPTION-PHRASE>` | What the document is about, UPPER-KEBAB-CASE. Documents produced by the planner / auditor / code-review agents end the phrase with the doc type: `-DESIGN`, `-PLAN`, `-ROADMAP`, `-ANALYSIS`, `-AUDIT`, `-CODE-REVIEW`. |

### Repo-tag assignment rules

- **`ECOSYSTEM`** — cross-repo or platform-wide subjects (ecosystem audits, cross-repo CI/roadmap/release docs, the canopy↔cascor interface program, stack-wide regression/security work, shared procedures such as PyPI publishing or conda-env rebuilds).
- **Sub-packages hosted in this repo** (`juniper-model-core`, `juniper-service-core`, `juniper-observability`, `juniper-ci-tools`, `juniper-doc-tools`, `juniper-config-tools`) and juniper-ml's own tooling (launcher scripts, custom-agent suite, worktree/handoff procedures) → **`ML`**.
- **The recurrence family** (`juniper-recurrence`, `juniper-recurrence-model`, `juniper-recurrence-client`, and the pre-rename `juniper-recurse` working notes) → **`RECURRENCE`**.
- Otherwise: the single repo the document most concerns.

## 3. Scope and exemptions

The convention applies to all tracked `notes/**/*.md` **except** (owner decision 2026-07-04):

| Exempt | Why |
| ------ | --- |
| `notes/releases/` | `RELEASE_NOTES_v<version>.md` / `RELEASE_NOTES_<pkg>_v<version>.md` is the mandatory release-archival convention (see the PyPI publish procedure §11). |
| `notes/templates/` | `TEMPLATE_*.md` names are referenced by the release / PR procedures. |
| `notes/requirements/` | The by-area / by-repo / by-status views are generated from the requirements snapshot; regeneration would recreate the old names. |
| `notes/legacy/` | Archived pre-polyrepo material; its git last-modified dates are the 2026-05-05 bulk-archive date, not authorship dates. |
| `README.md` files | Directory-index role depends on the fixed name. |

## 4. Migration record (2026-07-04)

- 251 files renamed in place (same directory) on branch `chore/notes-naming-convention`.
- Full old→new mapping: [`util/ad-hoc/2026-07-04_notes_rename_map.tsv`](../util/ad-hoc/2026-07-04_notes_rename_map.tsv).
- Generator: `util/ad-hoc/2026-07-04_notes_rename_convention.py` (classification table + mechanical phrase derivation).
- Reference rewriter: `util/ad-hoc/2026-07-04_notes_rename_refupdate.py` (~7,000 in-repo reference updates, including the `notes/requirements/id_assignments.yaml` citations; boundary-guarded).
- Tag distribution: 145 ECOSYSTEM, 36 ML, 28 CASCOR, 23 RECURRENCE, 17 CANOPY, 2 DEPLOY.

## 5. Where the convention is stated

- `.claude/agents/planner.md` and `.claude/agents/auditor.md` (agent output contracts).
- `prompts/agent_templates/{plan,audit,code-review}.md` (deliverable naming in generated prompts).
- `AGENTS.md` → Conventions (pointer to this document).

This document is the convention's source of truth; update it first, then the surfaces above.
