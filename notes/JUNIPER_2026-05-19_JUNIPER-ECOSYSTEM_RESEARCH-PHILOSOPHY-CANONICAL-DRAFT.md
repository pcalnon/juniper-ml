# Research Philosophy — Canonical Draft (READMEs)

**Date**: 2026-05-19
**Last Updated**: 2026-11-27
**Author**: Paul Calnon
**Status**: Canonical — the Overtoad approved the current §2 and §3.1 text on 2026-11-27 (§7). First drafted for review as §12 step 2 of [`JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_README-NORMALIZATION-PLAN.md`](JUNIPER_2026-05-19_JUNIPER-ECOSYSTEM_README-NORMALIZATION-PLAN.md)
**Consumed by**: Per-README inline copies produced by §12 steps 3–8 of the same plan

---

## 1. Purpose

The README normalization plan adopts a single canonical Research Philosophy text that is inlined verbatim into every Juniper application README. This file is the source of truth for that text. The block in §2 below (three paragraphs since 2026-11-27; two before) is to be copy-pasted, unchanged, under a `## Research Philosophy` heading in each of the ten in-scope READMEs. Where the plan's §10 per-repository notes sanction an optional closing paragraph, that paragraph is drawn from §3 of this file.

The source-of-truth model is explicit per the normalization plan's §9.6: the canonical paragraphs are duplicated across READMEs rather than extracted into a shared include, because README rendering does not support includes and the duplication is intentional — each README must remain a self-contained landing page.

No edits to the canonical text are permitted in a downstream README PR. If a per-repository PR needs the text to read differently for that repository, the change is made here first, and every README that already inlines the text is re-synchronised in a follow-up sweep.

---

## 2. Canonical Paragraphs

The block below is the canonical text. Everything between the two `---CANONICAL BEGIN---` and `---CANONICAL END---` markers is inlined verbatim under a `## Research Philosophy` heading in every in-scope README.

```markdown
---CANONICAL BEGIN---
## Research Philosophy

The Juniper platform is intended to study learning algorithms for network architectures not fixed in advance (e.g., when training begins). Its initial anchor is the [Cascade-Correlation algorithm](https://kilthub.cmu.edu/articles/journal_contribution/The_Cascade-Correlation_learning_architecture/6610403?file=12102545) of [Fahlman and Lebiere](https://kilthub.cmu.edu/ndownloader/files/12102545) (1990), implemented from the primary literature without recourse to higher-level abstractions that hide the algorithm's operational detail.
A recently added extension includes a new [recurrence service](https://github.com/pcalnon/juniper-recurrence) implementing the [Legendre Memory Unit](https://github.com/wuphilipp/lmu) algorithm of [Voelker, Kajić, and Eliasmith](https://proceedings.neurips.cc/paper_files/paper/2019/file/952285b9b7e7a1be5aa7849f32ffff05-Paper.pdf) (2019). This [LMU-based recurrence service](https://github.com/pcalnon/juniper-recurrence) performs time-series regression with a recurrent neural network that natively handles irregular sampling.

The organizing commitment behind Juniper Project's network model development is that algorithm implementations remain inspectable at the level at which they were originally specified. The Cascade-Correlation model's candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper. This structural transparency enables comparative work across algorithms, datasets, and hyperparameter regimes on a known and reproducible substrate.

The current platform comprises a [Cascade-Correlation training service](https://github.com/pcalnon/juniper-cascor) exposing a REST and WebSocket interface, a [dataset-generation service](https://github.com/pcalnon/juniper-data#juniper-data) with a named-version registry that includes, among others, the ARC-AGI ([1](https://arcprize.org/arc-agi/1), [2](https://arcprize.org/arc-agi/2), [3](https://arcprize.org/arc-agi/3)), [MNIST](https://www.nist.gov/itl/products-and-services/emnist-dataset) (technically EMNIST), and [Spiral Problem](https://www.kaggle.com/datasets/pcalnon/spiralproblemdataset-9) dataset families, a real-time [training dashboard](https://github.com/pcalnon/juniper-canopy) for inspecting, guiding, and monitoring network dynamics as they occur, a [Legendre Memory Unit training service](https://github.com/pcalnon/juniper-recurrence), and a [distributed worker](https://github.com/pcalnon/juniper-cascor-worker) that parallelizes candidate-unit training across hosts, operating systems, and hardware architectures. The training service, training dashboard, and available datasets have recently been extended to include recurrent architectures and their required datasets. Near-term work builds the architectural-growth catalog beyond [Cascade-Correlation](https://github.com/pcalnon/juniper-cascor) and [Legendre Memory Unit](https://github.com/pcalnon/juniper-recurrence), introduces multi-network orchestration for comparative experiments at the level of network populations rather than individual runs, and tightens the dataset–training–monitoring loop into a reproducible research workbench. The longer-term direction is the systematic empirical study of constructive and architecture-growing learning algorithms, with the development, comparison, and replication that such research requires.
---CANONICAL END---
```

The `---CANONICAL BEGIN---` / `---CANONICAL END---` markers are not part of the inlined text. They exist in this draft file only so a reviewer (or a future automation pass) can identify the exact boundaries of the canonical block.

---

## 3. Optional Per-Component Closing Paragraphs

Per the plan's §9.5, a closing one-to-three-sentence paragraph may follow the canonical block in a README, describing the component's specific role in the research programme. The plan calls it a third paragraph; since 2026-11-27 the canonical block has three paragraphs of its own, so it is now the fourth. The closing paragraph is **omitted** wherever it would merely repeat the application description from the README's preamble.

The plan's §10 sanctions a closing paragraph for exactly two repositories. The drafts for those follow. Every other repository uses the canonical block only, with no closing paragraph.

### 3.1 `juniper-ml` (per §10.1)

```markdown
Within this program, `juniper-ml` is the integration surface: a single installation entry point that aggregates the client libraries needed to interact with the platform from external Python code, and a version anchor that makes component compatibility legible at a glance.
```

### 3.2 `juniper-data-client` (per §10.5)

```markdown
Within this programme, `juniper-data-client` is the canonical integration boundary between the training and data services. Its contract is the dataset-fetch interface used by every training-side consumer; changes to its surface are therefore changes to the platform's shared dataset semantics.
```

### 3.3 Repositories using only the canonical block

The following eight repositories inline §2 alone, with no closing paragraph:

- `juniper-canopy` — the application description in the preamble already names the dashboard's role.
- `juniper-cascor` — the application description already names the training-service role.
- `juniper-data` — the application description already names the dataset-service role.
- `juniper-cascor-client` — the application description already names the WebSocket client role.
- `juniper-cascor-worker` — the application description already names the worker role.
- `juniper-observability` — the application description already names the shared-primitives role.
- `juniper-doc-tools` — the application description already names the link-validator role.
- `juniper-deploy` — the application description already names the orchestration role.

If, during a per-repository PR, an author identifies a research-programme framing for one of these eight repositories that is genuinely additive over its application description, the framing is to be drafted here first, reviewed under this file, and merged into this file before being inlined.

---

## 4. Constraints Self-Check

The plan's §9.1–§9.4 impose specific constraints on the rewrite. Each is checked below against the canonical text in §2. The check was re-run on 2026-11-27 against the text approved that day; rows 2 and 6 record where that text departs from the plan.

| # | Constraint | Source | Status |
|---|------------|--------|--------|
| 1 | Tone: declarative, post-doctoral, no glosses of standard terminology | §9.1 | PASS — "candidate units", "correlation objectives", "weight-freezing semantics", "network populations", and "replication" are used without glossing |
| 2 | Length: exactly two paragraphs; first = research direction, second = current functionality and future direction | §9.2 | DEPARTS (text approved by the Overtoad, 2026-11-27) — three paragraphs: paragraph 1 names the research direction (study of architectures not fixed in advance, CasCor anchor, primary-literature implementation) and the Legendre Memory Unit recurrence extension; paragraph 2 states the inspectability commitment and the comparative substrate it enables; paragraph 3 names current capabilities, near-term direction, and longer-term direction |
| 3 | Cites Cascade-Correlation (Fahlman & Lebiere, 1990) as present anchor | §9.3 | PASS |
| 4 | Names current capabilities: CasCor REST+WS, dataset service with named-version registry incl. ARC-AGI, real-time monitoring dashboard, distributed worker for candidate-pool training | §9.3 | PASS — all four named in paragraph 3, sentence 1, which also names the Legendre Memory Unit training service |
| 5 | Names near-term direction: extension beyond CasCor, multi-network orchestration, reproducible workbench | §9.3 | PASS — paragraph 3, sentence 3 |
| 6 | Names longer-term direction: systematic study of constructive / architecture-growing algorithms with empirical infrastructure for ablation and comparison | §9.3 | PARTIAL (text approved by the Overtoad, 2026-11-27) — paragraph 3, sentence 4 names the systematic empirical study, comparison, and replication; it no longer names ablation or the infrastructure for it |
| 7 | Avoids forbidden words: *powerful, robust, comprehensive, cutting-edge, next-generation, state-of-the-art* | §9.4 | PASS — none present |
| 8 | No second-person address | §9.4 | PASS — no "you" anywhere |
| 9 | No bullet-point lists | §9.4 | PASS — pure prose |
| 10 | No hedging modal verbs (*might, may, could*) when describing current behaviour | §9.4 | PASS — current-behaviour clauses ("comprises", "includes", "performs", "enables") are present indicative; future-direction clauses use present-tense decisive verbs ("builds", "introduces", "tightens") rather than hedged modals |

A future automation pass may want to encode these checks as a linter that runs against every README's Research Philosophy section. That is out of scope for the present plan; the manual self-check above suffices for the inlining PRs.

---

## 5. Review and Acceptance Procedure

1. **This PR is the dedicated forum for review of the canonical text.** Comments on the wording of the two paragraphs belong on this PR's diff, not on downstream README PRs.
2. **Acceptance gate.** The PR is mergeable when (a) the §4 self-check still passes, (b) any objections raised on the diff have been resolved by edit or by explicit rejection rationale, and (c) the optional third paragraphs in §3 have been reviewed against the corresponding §10 entries in the normalization plan.
3. **Post-merge.** Once this file is on `main`, the per-README PRs in §12 steps 3–8 of the normalization plan may proceed. Each inlining PR must include, in its description, a one-line affirmation that the canonical text was inlined verbatim without modification, plus a diff snippet showing the canonical block matches §2 character-for-character.
4. **Subsequent edits.** Any change to the canonical text after first inlining triggers a sweep PR that re-synchronises every README that already inlines it. This file is the single source from which all sweeps originate.

---

## 6. Out of Scope

- Per-repository deviations from the canonical text. Repositories that need a different framing record that framing as a closing paragraph in §3 of this file; the canonical block itself does not vary across repositories.
- A shared-include rendering mechanism. The plan's §9.6 explicitly rejects this; the duplication is intentional.
- A linter encoding the §4 self-check. May be valuable in future, not in scope here.
- Translation of the canonical text into other natural languages. The platform is documented in English only.

---

## 7. Revision History

| Date | Change |
|------|--------|
| 2026-05-19 | First draft for review: the two-paragraph canonical block (§2) and the `juniper-ml` and `juniper-data-client` closing paragraphs (§3). |
| 2026-11-27 | §2 and §3.1 now carry the Research Philosophy text of `juniper-ml`'s README.md, which the Overtoad approved as canonical: the revision merged in juniper-ml#2662, with "Candidate units" lower-cased and "OS's" spelled "operating systems" in the follow-up that carries this change. The canonical block grows to three paragraphs and adds the Legendre Memory Unit recurrence service. §1–§3 and §6 no longer describe two canonical paragraphs and a third per-component one, and §4 is re-run against the new text. `juniper-ml`'s README.md is the only README that inlines §2: none of the other nine in-scope READMEs on `main` has a Research Philosophy section (each read through the GitHub API on 2026-11-27), so the sweep in §5 item 4 has no other target. |
