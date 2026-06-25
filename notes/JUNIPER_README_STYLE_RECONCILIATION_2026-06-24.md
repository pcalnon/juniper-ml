# Juniper README Style Reconciliation

**Project**: Juniper ML Research Platform
**Author**: Paul Calnon
**Date**: 2026-06-24
**Status**: RATIFIED 2026-06-24 (Paul Calnon) — the §3 recommendation is adopted as written
**Supersedes (partial)**: [`README_NORMALIZATION_PLAN_2026-05-19.md`](README_NORMALIZATION_PLAN_2026-05-19.md)

---

## 1. Context

The 2026-06-24 ecosystem README sweep surfaced that **two README conventions now coexist** across
Juniper, applied inconsistently — sometimes within a single repository. This note recommends a
canonical style and a low-risk migration path. It was ratified as written on 2026-06-24; fleet-wide
migration proceeds per §5.

## 2. The two styles

| | **Style A — Normalized house style** | **Style B — Lean accessible overview** |
|---|---|---|
| Defined by | [`README_NORMALIZATION_PLAN_2026-05-19.md`](README_NORMALIZATION_PLAN_2026-05-19.md) | Emergent (no written standard yet) |
| Opens with | Right-aligned logo + shared "Juniper is an AI/ML research platform…" platform intro | One-line tagline + PyPI/Python/License **badges** |
| Versioning | Hardcoded compatibility tables / "Latest published" columns | Badges (auto-update) |
| Sections | Distribution → Ecosystem Compatibility → Architecture (ASCII) → Related Services → **Active Research Components / Design Notes** → Quick Start → **Research Philosophy** (shared 2-paragraph essay) → Documentation → License | Problem-first intro → Install → Quick start → What's in the box → Status → Design link → License |
| Used by today | `juniper-ml` root, `juniper-observability`, `juniper-doc-tools`, and the cascor/canopy/data service repos | The whole `juniper-recurrence` repo (app + model + client), plus `juniper-model-core`, `juniper-ci-tools`, `juniper-config-tools`, and now `juniper-service-core` |

The split runs *inside* `juniper-ml`: its shared libraries are themselves divided — `observability`
and `doc-tools` are Style A; `model-core`, `ci-tools`, `config-tools`, `service-core` are Style B.

## 3. Recommendation

**Adopt Style B (lean) as canonical for individual package READMEs, with a short ecosystem callout —
and keep the full platform narrative in exactly one place (the `juniper-ml` root README).**

Concretely, a canonical package README is:

1. Title + one-line tagline + **badges** (PyPI version, Python, license).
2. **Problem-first** intro — what it is and the problem it solves, in plain language.
3. A **short "Part of the Juniper platform" callout** (2–3 sentences + link) — preserves the
   "unfamiliar with Juniper itself" on-ramp without reprinting the full philosophy essay.
4. Install → Quick start → What's in the box → Status → Design/deep-doc link → License.

### Rationale

- **Serves the stated goal.** The sweep's brief was "an accessible overview for a reader comfortable
  with ML/AI but unfamiliar with the package." Problem-first + quickstart does that; a logo and a
  two-paragraph research-philosophy essay above the fold do not.
- **Kills version drift by construction.** Badges replace the hardcoded compatibility/"latest
  published" tables that went stale in this very sweep (root README, deploy container count).
- **Stops boilerplate duplication.** The identical "Research Philosophy" essay is currently copied
  onto every package's PyPI landing page, where it both buries package-specific content and goes
  stale ("the current platform comprises…"). It belongs in **one** canonical place.
- **Idiomatic.** Style B matches how a developer expects a PyPI package README to read.
- **Proven.** `juniper-recurrence` (4 READMEs) and the four lean `-core`/`-tools` libraries already
  demonstrate it working at PyPI-landing-page quality.

## 4. What stays where

- The **`juniper-ml` root README** remains the platform's front door: it keeps the fuller platform
  intro and the Research Philosophy essay — the **one** place that narrative lives.
- **Architecture/ASCII diagrams** stay where they add value (e.g. `juniper-deploy`, `service-core`);
  they are not Style-A-exclusive.
- **`AGENTS.md`** is unaffected — it is the contributor guide, governed separately (header-schema +
  version-drift lints, touch-up workflow).

## 5. Migration sketch (all docs-only, incremental, low-risk)

- **Phase 0 — Ratify.** Approve this note; mark the relevant sections of
  `README_NORMALIZATION_PLAN_2026-05-19.md` as superseded. *(Done 2026-06-24, in the same PR as this
  note.)*
- **Phase 1 — Template.** Add `notes/templates/TEMPLATE_README_PACKAGE.md` (the lean skeleton) and a
  reusable "Part of the Juniper platform" snippet. Do a quick inventory confirming which of the ~16
  user-facing READMEs are A vs B (this note's §2 list is close but unverified for the cascor
  client/worker/data-client trio).
- **Phase 2 — Migrate opportunistically**, one repo per PR, highest-visibility (PyPI-published)
  first: `observability`, `doc-tools`, then the service repos. Each PR is a self-contained docs
  change; no code or release impact.
- **Phase 3 — Retire** the superseded normalization sections and (optionally) the per-package logo,
  keeping branding to the root README + badges.

No phase blocks a release; the work can pause at any point with the ecosystem in a consistent-enough
state (badges + problem-first everywhere migrated so far).

## 6. Counter-option (and why not)

**Keep Style A everywhere** and convert the lean repos back. Rejected because: it re-introduces the
hardcoded-version drift this sweep just removed, duplicates the philosophy essay onto every PyPI
page, and reads less like an accessible package overview — the opposite of the sweep's brief. It is
also the larger rewrite (the recurrence repo + four libraries already shipped lean).

## 7. Decisions (ratified 2026-06-24)

Ratified as written by Paul Calnon on 2026-06-24. The §3 recommendation is adopted in full:

1. **Canonical style: Style B (lean) + short ecosystem callout.**
2. **Root README** keeps the full platform narrative / Research Philosophy essay — the single home
   for it.
3. **Badges are the version surface;** per-package logos are not required (branding consolidates to
   the root README + badges). Whether to physically strip existing per-package logos is a Phase-3
   cleanup detail, not a blocker.
