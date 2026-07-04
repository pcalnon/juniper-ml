# Juniper-Recurse — Design & Implementation Plan  *(SPLIT — see below)*

**Project**: juniper-recurse — Recurrent / Constructive Neural-Network Application for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.2.0 (SUPERSEDED — split into two documents 2026-06-03)
**Last Updated**: 2026-06-03

---

> **⚑ THIS DOCUMENT HAS BEEN SPLIT (2026-06-03).** The original single master plan (`v0.1.0`, dated 2026-05-31) was divided into two focused documents at Paul's request. This file is retained only as a redirect so existing references and links keep resolving. **Do not edit content here — edit the split documents.**

## Where the content went

| New document | Contains |
|--------------|----------|
| **[Recurrent Model Design & Plan](JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md)** | Everything about **adding recurrent NN capability**: requirements & scoring (Part 1.1), the candidate-architecture landscape (1.2), the top-3 deep dives (1.3 — RCC / Growing-ESN / LMU), runners-up & rejections (1.4), the recommendation (1.5), model open questions (1.6), the "recurrent vs. recursive" terminology decision (0.5), the first-principles constraint C1, model-level testing (3.2), the model-risk slice, and the external literature survey (6.2). |
| **[Model/Middleware Refactor Design & Plan](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md)** | Everything about **refactoring the model out of the middleware**: the cascor model↔service seam (2.1), extract/abstract/keep classification (2.2), the target architecture & two new shared packages `juniper-service-core` + `juniper-model-core` (2.3), juniper-data extensions (2.4), canopy generalization (2.5), ecosystem changes (2.6), phased rollout (2.7), refactor risks (2.8), middleware/cross-cutting testing (3.1, 3.3–3.7). **Plus all cross-cutting scaffolding** — Status Tracker, binding constraints & method (Part 0), the consolidated Risk Register (Part 4), the consolidated Open-Questions table (Part 5), internal sources (6.1, 6.3), and the Verification Log (Part 7) — each flagged `⚑ CROSS-CUTTING (review)`. |

**Identifiers are stable.** All `WS-*`, `OQ-*`, `RK-*`, `C1–C5`, and `F*` IDs are preserved verbatim across both documents, so any external reference (memory notes, PRs, commits) still resolves.

**Reading order:** start with the **refactor** document for the Status Tracker / open-questions / overall framing, then the **model** document for the architecture decision. The two are coupled: the model is built greenfield against the refactor's abstractions, proving the template before production cascor is touched.

> **Live design state (2026-06-03):** WS-0 is **not ratified** — the model pick was reopened as **[OQ-4]** (RCC's no-count/no-group "star-free" representational ceiling) and is under active literature review; a model-pick redesign is likely. Canonical status lives in the refactor document's [Status Tracker](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md#status-tracker) and [Open-Questions table](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md#part-5--open-questions--areas-of-uncertainty).

---

*This redirect intentionally contains no design content. See the two linked documents above.*
