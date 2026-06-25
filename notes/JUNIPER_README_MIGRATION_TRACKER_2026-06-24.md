# Juniper README Migration Tracker

**Project**: Juniper ML Research Platform
**Author**: Paul Calnon
**Started**: 2026-06-24
**Status**: COMPLETE 2026-06-25 — all 9 migrated (only the `juniper-ml` root README intentionally stays Style A)
**Design of record**: [`JUNIPER_README_STYLE_RECONCILIATION_2026-06-24.md`](JUNIPER_README_STYLE_RECONCILIATION_2026-06-24.md)
**Template**: [`templates/TEMPLATE_README_PACKAGE.md`](templates/TEMPLATE_README_PACKAGE.md) ·
**Callout snippet**: [`templates/SNIPPET_JUNIPER_PLATFORM_CALLOUT.md`](templates/SNIPPET_JUNIPER_PLATFORM_CALLOUT.md)

Phase 1 (the lean template + callout snippet above and the verified A/B inventory below) and Phase 2
(migrating all nine Style-A package READMEs to the lean style, one repo per PR) are **both complete** as
of 2026-06-25. The §5 migration is done; only the `juniper-ml` root README intentionally stays Style A.

---

## 1. Inventory (verified 2026-06-24)

Classification marker: a README is **Style A** if it carries the right-aligned Juniper logo and/or the
shared `## Research Philosophy` essay; otherwise **Style B** (lean). 20 user-facing READMEs:

| README | Style | Action |
|--------|-------|--------|
| `juniper-ml/README.md` (root) | A | **Stays A** — sole home of the platform narrative |
| `juniper-ml/juniper-observability/README.md` | A | ✅ migrated |
| `juniper-ml/juniper-doc-tools/README.md` | A | ✅ migrated |
| `juniper-canopy/README.md` | A | ✅ migrated |
| `juniper-cascor/README.md` | A | ✅ migrated |
| `juniper-cascor-client/README.md` | A | ✅ migrated |
| `juniper-cascor-worker/README.md` | A | ✅ migrated |
| `juniper-data/README.md` | A | ✅ migrated |
| `juniper-data-client/README.md` | A | ✅ migrated |
| `juniper-deploy/README.md` | A | ✅ migrated (see notes) |
| `juniper-ml/juniper-model-core/README.md` | B | already lean |
| `juniper-ml/juniper-service-core/README.md` | B | already lean (sweep ml#531) |
| `juniper-ml/juniper-ci-tools/README.md` | B | already lean |
| `juniper-ml/juniper-config-tools/README.md` | B | already lean |
| `juniper-cascor/juniper-cascor-model/README.md` | B | already lean |
| `juniper-cascor/juniper-cascor-protocol/README.md` | B | already lean |
| `juniper-recurrence/README.md` | B | already lean (sweep, reference) |
| `juniper-recurrence/juniper-recurrence/README.md` | B | already lean |
| `juniper-recurrence/juniper-recurrence-model/README.md` | B | already lean |
| `juniper-recurrence/juniper-recurrence-client/README.md` | B | already lean |

**Scope:** 10 already lean · 1 stays A by design (the root) · **9 to migrate**.

## 2. Phase 2 checklist (9 to migrate)

Suggested order: PyPI-published shared libs first (easiest, same repo, highest visibility), then the
service/app repos, then clients, with `juniper-deploy` last (not a package — its README is an
operator runbook, so the lean callout applies but the body stays runbook-shaped).

| # | README | Repo | PyPI? | Status |
|---|--------|------|-------|--------|
| 1 | `juniper-observability/README.md` | juniper-ml | yes | ✅ ml#549 |
| 2 | `juniper-doc-tools/README.md` | juniper-ml | yes | ✅ ml#549 |
| 3 | `juniper-data/README.md` | juniper-data | yes | ✅ data#206 |
| 4 | `juniper-cascor/README.md` | juniper-cascor | yes | ✅ cascor#359 |
| 5 | `juniper-canopy/README.md` | juniper-canopy | yes | ✅ canopy#396 |
| 6 | `juniper-data-client/README.md` | juniper-data-client | yes | ✅ data-client#102 |
| 7 | `juniper-cascor-client/README.md` | juniper-cascor-client | yes | ✅ cascor-client#81 |
| 8 | `juniper-cascor-worker/README.md` | juniper-cascor-worker | yes | ✅ cascor-worker#111 |
| 9 | `juniper-deploy/README.md` | juniper-deploy | no | ✅ deploy#134 |

## 3. Per-migration definition of done

For each README: copy the [template](templates/TEMPLATE_README_PACKAGE.md); carry over the accurate
package-specific content (install, a *verified* quick-start, status); replace the platform intro +
Research Philosophy with the [callout snippet](templates/SNIPPET_JUNIPER_PLATFORM_CALLOUT.md);
replace hardcoded version/"latest published" tables with badges; keep any genuinely useful
Architecture/ASCII diagram; preserve `AGENTS.md` untouched. One repo per PR, docs-only, no release
impact.

## 4. Notes

- **Root README is excluded on purpose** — it keeps the logo + Research Philosophy as the platform's
  single front door (reconciliation note §4).
- **`juniper-deploy`** is orchestration, not a package; migrate its *opening* to the lean
  tagline + callout + badges, but the body remains an operator runbook. (It also has the deferred
  ASCII-diagram redraw from the reconciliation note §8.)
- **Two deferred content fixes** for whichever PR next touches those READMEs are tracked in the
  reconciliation note §8 (root README headline tables/diagram; deploy diagram redraw).
