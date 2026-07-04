# README Normalization Plan — Juniper Application Suite

**Date**: 2026-05-19 (last updated 2026-05-21 for `juniper-ml` 0.5.0 extras-surface expansion)
**Author**: Paul Calnon
**Status**: SUPERSEDED (partial) 2026-06-24 by [`JUNIPER_2026-06-24_JUNIPER-ECOSYSTEM_README-STYLE-RECONCILIATION.md`](JUNIPER_2026-06-24_JUNIPER-ECOSYSTEM_README-STYLE-RECONCILIATION.md) — see banner below
**Applies to**: All ten application/library repositories in the Juniper ecosystem

---

> **⚠️ Superseded (partial), 2026-06-24.** The per-package *structure* mandated by this plan — the logo + platform-intro preamble (§3, §5), the canonical Style-A section order (§4), the ecosystem-wide Research Philosophy on every package (§7.7, §9), and the Active Research Components / Design Notes substitution (§10.9, §10.10) — is superseded by [`JUNIPER_2026-06-24_JUNIPER-ECOSYSTEM_README-STYLE-RECONCILIATION.md`](JUNIPER_2026-06-24_JUNIPER-ECOSYSTEM_README-STYLE-RECONCILIATION.md), which adopts the lean *badges + problem-first* style as canonical for individual package READMEs (the full platform narrative now lives only in the `juniper-ml` root README). This document is retained for historical context and for the parts **not** superseded — the writing-register guidance (§1) and the §11 documentation-audit procedure.

## 1. Motivation and Scope

Every Juniper application currently ships its own README, but the result is heterogeneous: only `juniper-canopy` carries a project-level preamble (title, logo, project description), only three of ten READMEs include any meaningful "Research Philosophy" framing, lockfile, Docker-deployment, and active-research sections appear in some repositories and not others, and only two READMEs reference the canonical PyPI distribution channels.
Cross-repository navigation is similarly inconsistent: some READMEs end with an ecosystem table, some do not, and the meta-package — `juniper-ml` — does not currently advertise itself as the public-facing entry point to the platform.

This plan specifies, repository by repository, what each application README must contain in order to (a) serve as a self-contained landing page for that application and (b) demonstrate uniform membership in the Juniper project.
It is a planning artifact only: no README content is to be modified as a result of writing this document.
Each subsequent implementation step is expected to be executed under its own pull request, scoped to a single repository, and verified against the acceptance criteria in §11.

Writing style for every README is to be straight-forward and declarative throughout, at the register expected of a post-doctoral researcher communicating with peers.
Marketing language, exhortations, and adjective-heavy prose are out of scope. Where prior README text already meets that bar, it is preserved verbatim; where it does not, it is rewritten.

---

## 2. Inventory of In-Scope READMEs

| # | Repository                                                    | Current README (lines) | Role                                                                    |
|---|---------------------------------------------------------------|------------------------|-------------------------------------------------------------------------|
| 1 | `juniper-ml`                                                  | 67                     | Meta-package; **designated public face of the project**                 |
| 2 | `juniper-canopy`                                              | 256                    | Monitoring dashboard service (Dash/FastAPI); current reference template |
| 3 | `juniper-cascor`                                              | 200                    | Cascade-Correlation training service                                    |
| 4 | `juniper-data`                                                | 223                    | Dataset-generation service (FastAPI)                                    |
| 5 | `juniper-data-client`                                         | 226                    | HTTP client for `juniper-data`                                          |
| 6 | `juniper-cascor-client`                                       | 156                    | HTTP/WebSocket client for `juniper-cascor`                              |
| 7 | `juniper-cascor-worker`                                       | 107                    | Distributed candidate-training worker                                   |
| 8 | `juniper-deploy`                                              | 447                    | Docker Compose orchestration; not on PyPI                               |
| 9 | `juniper-observability` (`juniper-ml/juniper-observability/`) | 53                     | Shared Prometheus/Sentry/logging primitives                             |
| 10 | `juniper-doc-tools` (`juniper-ml/juniper-doc-tools/`)        | 87                     | Shared markdown link-validator library and `juniper-check-doc-links` CLI |

All ten are addressed in this plan. `juniper-deploy` is treated as an application even though it is not distributed via PyPI; the PyPI-link requirement is replaced with a "Distribution" subsection that points to the source repository and the meta-package. `juniper-doc-tools` and `juniper-observability` are both sibling libraries published from the `juniper-ml` repository on independent tag patterns; they follow the same README pattern as each other.

---

## 3. Reference Template (Derived from `juniper-canopy`)

The current `juniper-canopy/README.md` provides the structural pattern this plan adopts. The first six lines of that file are reproduced here as the canonical preamble form:

```markdown
<div align="right" width="150px" height="150px" align="right" valign="top"> <img src="src/assets/Juniper_Logo_150px.png" alt="Juniper" align="right" valign="top" width="150px" /></div>
<br /> <br /> <br /> <br />

# Juniper: Dynamic Neural Network Research Platform

Juniper is an AI/ML research platform for investigating dynamic neural network architectures and novel learning paradigms.  The project emphasizes ground-up implementations from primary literature, enabling a more transparent exploration of fundamental algorithms.
```

That preamble is to be reused **verbatim** at the top of every in-scope README, with the single exception of the image path, which is substituted per §5. After the preamble, every README is then expected to introduce its **application** in the form:

```markdown
## <Application Name>

<Three-to-five sentence description of the specific application: what it does,
who it is for, where it sits in the stack, and what makes it distinct from
its siblings.>
```

The application heading uses the human-readable form (`Juniper Canopy`, `Juniper Cascor`, `Juniper Data`, `Juniper Data Client`, `Juniper Cascor Client`, `Juniper Cascor Worker`, `Juniper ML`, `Juniper Observability`, `Juniper Doc Tools`, `Juniper Deploy`). Each application description is written in declarative prose; no bullet lists, no badges, no calls to action.

After the application heading, every README continues with the section order specified in §4.

---

## 4. Canonical Section Order

Every in-scope README is to present its sections in the following order. Sections marked **Required** must appear in every README; sections marked **Conditional** appear only where the per-repository notes in §10 indicate that the section is applicable.

| #  | Section                                                  | Status      | Notes                                                                                                     |
|----|----------------------------------------------------------|-------------|-----------------------------------------------------------------------------------------------------------|
| 1  | Project preamble (title + logo + project description)    | Required    | Verbatim per §3                                                                                           |
| 2  | Application title + 3–5 sentence application description | Required    | Per §3                                                                                                    |
| 3  | Distribution (PyPI link + meta-package link)             | Required    | §6                                                                                                        |
| 4  | Ecosystem Compatibility                                  | Required    | §7.1                                                                                                      |
| 5  | Architecture                                             | Required    | §7.2                                                                                                      |
| 6  | Related Services                                         | Required    | §7.3                                                                                                      |
| 7  | Service Configuration                                    | Conditional | §7.4 — services and worker only                                                                           |
| 8  | Docker Deployment                                        | Conditional | §7.5 — applications shipped in `juniper-deploy` only                                                      |
| 9  | Dependency Lockfile                                      | Conditional | §7.6 — repositories with `requirements.lock`/`uv.lock` only                                               |
| 10 | Active Research Components                               | Required*   | §7.7 — *see §10.8, §10.9, and §10.10 for sanctioned substitutions in `juniper-deploy`, `juniper-observability`, and `juniper-doc-tools`* |
| 11 | Quick Start Guide                                        | Required    | §8 (extensively rewritten)                                                                                |
| 12 | Research Philosophy                                      | Required    | §9 (rewritten ecosystem-wide)                                                                             |
| 13 | Documentation                                            | Required    | §10.x and §10-validation procedure                                                                        |
| 14 | License                                                  | Required    | Existing per-repo content retained                                                                        |

Sections that are not applicable to a given repository are omitted entirely rather than rendered as empty stubs. No README is to introduce new top-level sections outside this list without an explicit deviation note recorded in §10.

---

## 5. Project Image Distribution Strategy

The canonical image asset is `Juniper_Logo_150px.png`, currently held at:

- `/home/pcalnon/Development/python/Juniper/juniper-canopy/src/assets/Juniper_Logo_150px.png`

This file does not currently exist in `juniper-ml/images/`; that directory contains the source logos (`Juniper_Logo_0.png` through `Juniper_Logo_9.png`) but not the 150-pixel rendering. The distribution strategy is therefore:

1. **Promote the 150 px asset into `juniper-ml/images/`.** A pull request against `juniper-ml` copies the file from `juniper-canopy/src/assets/Juniper_Logo_150px.png` to `juniper-ml/images/Juniper_Logo_150px.png` and the corresponding `.xcf` source. This makes `juniper-ml` the authoritative source for the project image, consistent with its role as the public face of the project.

2. **Per-repository asset placement.** Each in-scope repository receives a local copy of `Juniper_Logo_150px.png` in a stable location:

   | Repository              | Asset Path                                           |
   |-------------------------|------------------------------------------------------|
   | `juniper-ml`            | `images/Juniper_Logo_150px.png`                      |
   | `juniper-canopy`        | `src/assets/Juniper_Logo_150px.png` *(unchanged)*    |
   | `juniper-cascor`        | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-data`          | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-data-client`   | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-cascor-client` | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-cascor-worker` | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-deploy`        | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-observability` | `images/Juniper_Logo_150px.png` *(create directory)* |
   | `juniper-doc-tools`     | `images/Juniper_Logo_150px.png` *(create directory)* |

   Per-repository copies are preferred to remote `https://raw.githubusercontent.com/...` references because GitHub-hosted raw assets are cache-fragile and break when a repository is renamed, made private, or transferred. PyPI's README renderer additionally refuses some forms of remote-image embed.

3. **`.gitattributes` (LFS) handling.** Repositories that already track images via Git LFS (per `juniper-ml/.gitattributes`) must add their new `images/` path to the LFS tracking patterns. Repositories without LFS configuration may either adopt LFS or commit the file directly; the asset is approximately 15 KB and either choice is acceptable. The chosen approach is to be recorded in the PR description.

4. **Image markup form.** The image is rendered with the exact `<div>`/`<img>` block reproduced in §3, modified only in the `src=` attribute to point at the per-repository asset path.

---

## 6. PyPI Distribution Linking

Every in-scope README must include a **Distribution** subsection — placed immediately below the application description — that links to the package's PyPI listing and, separately, to the `juniper-ml` meta-package.

The block is to be rendered as follows (substituting the repository's own PyPI name and version):

````markdown
## Distribution

`<package-name>` is published on PyPI as **[`<package-name>`](https://pypi.org/project/<package-name>/)**.
The package is also surfaced through the platform meta-distribution
**[`juniper-ml`](https://pypi.org/project/juniper-ml/)**, which aggregates
every Juniper PyPI package -- servers, client libraries, distributed worker,
and shared tooling -- and installs them in one step via
`pip install juniper-ml[all]`. Per-component extras
(`[clients]`, `[worker]`, `[servers]`, `[tools]`, `[doc-tools]`) are
also available for finer-grained installs; see the
[`juniper-ml` README](https://github.com/pcalnon/juniper-ml#extras)
for the full table.

```bash
pip install <package-name>
```
````

The exact PyPI names and current versions are:

| Repository              | PyPI Name               | Current Version                        |
|-------------------------|-------------------------|----------------------------------------|
| `juniper-ml`            | `juniper-ml`            | 0.4.1                                  |
| `juniper-canopy`        | `juniper-canopy`        | 0.4.0                                  |
| `juniper-cascor`        | `juniper-cascor`        | 0.4.0                                  |
| `juniper-data`          | `juniper-data`          | 0.6.0                                  |
| `juniper-data-client`   | `juniper-data-client`   | 0.4.1                                  |
| `juniper-cascor-client` | `juniper-cascor-client` | 0.4.0                                  |
| `juniper-cascor-worker` | `juniper-cascor-worker` | 0.3.0                                  |
| `juniper-observability` | `juniper-observability` | 0.2.0 (or later — verify at edit time) |
| `juniper-doc-tools`     | `juniper-doc-tools`     | 0.1.0 (or later — verify at edit time) |
| `juniper-deploy`        | *not published*         | —                                      |

For `juniper-deploy`, the **Distribution** section becomes:

```markdown
## Distribution

`juniper-deploy` is not distributed as a Python package. The repository is
consumed directly via `git clone` and orchestrates the published Juniper
service images through Docker Compose. The platform meta-package
[`juniper-ml`](https://pypi.org/project/juniper-ml/) provides the Python
client libraries used in standalone client work.
```

For `juniper-ml` itself, the section adopts the meta-package phrasing:

````markdown
## Distribution

`juniper-ml` is the **public face of the Juniper platform on PyPI**. It is
published as **[`juniper-ml`](https://pypi.org/project/juniper-ml/)** and
provides a single installation entry point for every Juniper PyPI package --
the three service distributions (canopy, cascor, data), the two client
libraries (data-client, cascor-client), the distributed worker, and the three
shared tooling packages (ci-tools, doc-tools, observability):

```bash
pip install juniper-ml[all]
```

Individual components — `juniper-data-client`, `juniper-cascor-client`,
`juniper-cascor-worker`, `juniper-observability`, and `juniper-doc-tools` —
remain installable in isolation for callers that require finer control
over their dependency surface.
````

Version numbers are not to be hard-coded into prose. The link text is the package name; PyPI itself displays the current version on the linked page.

---

## 7. Per-Section Normalization Rules

### 7.1 Ecosystem Compatibility

The current canopy phrasing — a single sentence followed by a verified-versions table — is adopted as the standard. Every README contains a table whose columns are `juniper-data | juniper-cascor | juniper-canopy | data-client | cascor-client | cascor-worker` and whose row reports the version ranges with which the repository has been integration-tested.

Two cleanup items apply to existing tables:

- The canopy table currently lists `0.4.x | 0.3.x | 0.2.x | >=0.3.1 | >=0.1.0 | >=0.1.0`; this is materially out-of-date relative to the §6 version inventory and must be refreshed against the latest CI run at edit time.
- Repositories without prior compatibility tables (`juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-observability`, `juniper-doc-tools`) populate the table from the same source.

The single sentence preceding the table reads:

> This component is part of the [Juniper](https://github.com/pcalnon/juniper-ml) ecosystem. Verified compatible versions:

### 7.2 Architecture

Every README must contain an Architecture section.
For services (`juniper-canopy`, `juniper-cascor`, `juniper-data`), the section retains the existing ASCII diagram, refreshed to reflect any port or relationship changes.
For client libraries (`juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker`), the Architecture section is a two-to-four sentence description of where the library sits in the request graph plus a small ASCII diagram showing `Caller → Library → Service`.
For the meta-package (`juniper-ml`), the Architecture section reproduces the parent CLAUDE.md dependency graph, edited for prose-readability.

The Architecture section is not a tutorial; it does not include code. Its purpose is to make the component's position in the platform visible at a glance.

### 7.3 Related Services

The existing canopy three-column table — `Service | Relationship | Notes` — is the standard. Every README populates this table with the components it directly interacts with at runtime (not the full ecosystem). Links target the GitHub repository for that component.

### 7.4 Service Configuration

Required for `juniper-canopy`, `juniper-cascor`, `juniper-data`, and `juniper-cascor-worker`.
The format is the existing canopy `Variable | Required | Default | Description` table.
Variables are listed in the same order as they appear in the corresponding settings module (Pydantic `BaseSettings` for services, `argparse` for the worker).
Legacy fallback variables are explicitly marked as such in the Description column.

Client libraries (`juniper-data-client`, `juniper-cascor-client`) omit this section; they have no service-level configuration.

### 7.5 Docker Deployment

Required for the four repositories whose images appear in `juniper-deploy/docker-compose.yml`: `juniper-canopy`, `juniper-cascor`, `juniper-data`, `juniper-cascor-worker`. The section provides:

- A two-sentence statement that the canonical orchestration lives in `juniper-deploy`.
- A minimal local-build invocation (`docker build -t <name>:dev .` plus `docker run` with the required env-vars).
- A reference to the relevant profile in `juniper-deploy` (e.g. `make demo`, `make full`).

Client libraries and the meta-package omit this section. `juniper-deploy`'s own README expands this section significantly — it is the section of record for the Docker stack.

### 7.6 Dependency Lockfile

Required only for repositories that ship a lockfile: `juniper-cascor` (`requirements.lock`, `uv.lock`), `juniper-canopy` (`requirements.lock`), and `juniper-cascor-worker` (`requirements.lock`, `requirements-cpu.lock`). Each section documents:

- The lockfile path(s).
- The regeneration command (typically `uv pip compile --constraint requirements.lock pyproject.toml -o requirements.lock`).
- The CI lane that enforces freshness (constraint-mode + sorted-pins-diff per [`project_lockfile_freshness_constraint_model`]).
- Any repository-specific gotchas — for `juniper-cascor`, the §-3 footgun history is summarized in one paragraph with a link to the relevant notes file.

Repositories without lockfiles omit the section. The plan does not introduce lockfiles to repositories that do not currently have one.

### 7.7 Active Research Components

Required in every README. The section names the research artifacts the repository contains or supports, in declarative prose. For example:

- `juniper-cascor`'s entry names the Cascade-Correlation implementation (Fahlman & Lebiere, 1990), the candidate-pool training protocol, and the WebSocket-based distributed worker.
- `juniper-canopy`'s entry names the real-time training-dynamics visualisation, the dataset previewer, and the live network-topology renderer.
- `juniper-data`'s entry names the ARC-AGI dataset family and the named-version dataset registry.
- Client libraries cite the research components they expose rather than implement.
- `juniper-observability`'s entry names the `register_or_reuse` family of idempotent collector helpers.
- `juniper-ml`'s entry summarises the platform-level research components by reference.

This section replaces the ad-hoc "About" and "Overview" paragraphs that appear in several existing READMEs.

---

## 8. Quick Start Guide — Rewrite Specification

The current Quick Start sections range from extensive in `juniper-canopy` and `juniper-cascor` to absent in `juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-ml`, and `juniper-observability`. The plan replaces all of them with a uniform structure:

```markdown
## Quick Start Guide

### Prerequisites

- Python ≥ <version from pyproject.toml>
- <conda environment name, if applicable>
- <upstream service requirement, if applicable, with port>

### Installation

```bash
pip install <package-name>            # release
pip install <package-name>[<extras>]  # with optional extras, where applicable
```

For service repositories, an equivalent conda activation is also shown:

````bash
conda activate <env-name>
pip install -e ".[dev]"
```

### Verification

<minimal invocation that proves the install worked: a curl to `/v1/health`
for services, an importable smoke test for libraries, a `docker compose up`
for juniper-deploy.>

### Next Steps

A short paragraph pointing the reader at the per-repo `docs/QUICK_START.md`,
`docs/USER_MANUAL.md`, and the parent `juniper-ml` README.
````

Specific rewrites required:

| Repository              | Quick Start gap to close                                                                                                                                                           |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `juniper-ml`            | Currently no Quick Start; add full block above with `pip install juniper-ml[all]` and a one-line Python import sanity check                                                        |
| `juniper-data`          | Currently minimal (two API examples); replace with the standard block and move the API examples into `docs/USER_MANUAL.md` (or retain a single representative `curl /v1/datasets`) |
| `juniper-data-client`   | Currently library-code-only; add Prerequisites and Verification blocks                                                                                                             |
| `juniper-cascor-client` | Currently library-code-only; same treatment as data-client                                                                                                                         |
| `juniper-cascor-worker` | Currently CLI-only; add Prerequisites including the upstream cascor service URL, retain the CLI invocation as Verification                                                         |
| `juniper-observability` | Currently absent; add the standard block with the import smoke test                                                                                                                |
| `juniper-deploy`        | Already extensive; trim Quick Start to "Prerequisites → `make demo` → verify ports → see Profiles" and push details into the existing Profiles section                             |
| `juniper-canopy`        | Restructure existing content into the standard headings; demo-mode and service-mode become two `Verification` subsections                                                          |
| `juniper-cascor`        | Restructure existing content into the standard headings; preserve the Basic Usage code under `Verification`                                                                        |

Prerequisites lines that refer to a conda environment use the canonical names — `JuniperCanopy`, `JuniperCascor`, `JuniperData` — and explicitly note where `JuniperCanopy1`/`JuniperCascor1` are the active rebuilt environments (per the memory entries on torch and LIBTORCH-strip hooks).

---

## 9. Research Philosophy — Ecosystem-Wide Rewrite Specification

The current Research Philosophy text appears in only three READMEs and varies in framing. The plan adopts a single canonical paragraph, edited per repository only to reflect the component's particular research role. The canonical phrasing is to be drafted as part of the implementation work; the constraints on that draft are:

1. **Tone.** Declarative; written for a post-doctoral audience. The reader is assumed to know what a feed-forward network is, what supervised learning is, what an HTTP service is. No glosses of standard terminology.

2. **Length.** Two paragraphs. The first describes the *research direction*; the second describes the *current functionality and the direction of future work*.

3. **Substantive content required.** The rewrite is not a re-skin of the existing "transparency over convenience" phrasing. It must reflect, accurately and without overstatement:

   - The platform's commitment to first-principles, primary-literature implementations of dynamic-architecture algorithms (Cascade-Correlation as the present anchor).
   - The platform's *current* capabilities: a CasCor backend exposing a REST + WebSocket interface, a dataset service with named-version registry support including ARC-AGI families, a real-time monitoring dashboard, and a distributed worker for candidate-pool training.
   - The platform's *near-term direction*: extension to additional dynamic-architecture algorithms beyond CasCor, multi-network orchestration (per the existing Phase 6E design notes), and tighter integration of the dataset/training/monitoring loop into a reproducible research workbench.
   - The platform's *longer-term direction*: framed as a research workbench for the systematic study of constructive and architecture-growing learning algorithms, with explicit empirical infrastructure for ablation and comparison across algorithms and datasets.

4. **Forbidden constructions.** The rewrite avoids the words "powerful", "robust", "comprehensive", "cutting-edge", "next-generation", and "state-of-the-art". It does not address the reader in the second person. It does not contain bullet-point lists. It does not contain hedging modal verbs ("might", "may", "could") when describing current behaviour.

5. **Per-component variation.** The base two paragraphs are identical across all READMEs. A *third*, optional paragraph — one to three sentences — may follow, describing the component's specific role in the research direction (e.g. "Within this programme, `juniper-canopy` is the visualisation surface…"). This third paragraph is omitted where it would merely repeat the application description in §3.

6. **Source of truth.** The canonical two paragraphs are drafted once, reviewed under the dedicated planning issue, and then inlined into every README via the same pull request that updates the README. They are *not* extracted into a shared file that is `INCLUDE`d at render time — README rendering does not support that, and the duplication is intentional so each README remains standalone.

The drafting and review of the canonical paragraphs is the most opinion-load-bearing step in this plan. It is to be performed in a dedicated draft PR against `juniper-ml/notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-XX.md` before any README edits begin, so that ecosystem alignment is reached once and then mechanically applied.

---

## 10. Per-Repository Work Breakdown

Each repository's PR carries the same shape: preamble + application heading + Distribution + canonical sections in the §4 order + rewritten Quick Start + rewritten Research Philosophy + audited Documentation. The per-repository notes below capture only the *deltas* from that uniform shape.

### 10.1 `juniper-ml` (public face)

- Add preamble and 150 px logo (place asset at `images/Juniper_Logo_150px.png`).
- Application heading: `## Juniper ML`. Description: three-to-five sentences positioning the package as the **public face** of the platform — the single installable entry point that aggregates the **full Juniper PyPI surface** (servers, clients, worker, and shared tooling) into per-component extras, the meta-distribution that anchors version compatibility across components, and the canonical home for project-level documentation cross-references.
- Distribution section uses the meta-package phrasing in §6.
- Architecture: reproduce the parent-CLAUDE.md dependency graph; place at the top of the Architecture section.
- Active Research Components: summarises the platform-level components by reference and links to each repository's README.
- Quick Start: `pip install juniper-ml[all]`, followed by a single-line Python import smoke test of one client (`from juniper_data_client import JuniperDataClient`).
- Research Philosophy: the canonical two paragraphs; the optional third paragraph frames `juniper-ml` as the integration surface for the platform.
- Documentation: link to `docs/DOCUMENTATION_OVERVIEW.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`, and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`. All four are verified by `util/check_doc_links.py`.

### 10.2 `juniper-canopy`

- Preamble retained verbatim; only the image path is unchanged (already `src/assets/Juniper_Logo_150px.png`).
- Application heading: `## Juniper Canopy`. Description: three-to-five sentences naming this as the real-time monitoring dashboard, naming its Dash/FastAPI stack, naming the WebSocket and REST channels it consumes, and stating that it is the operator-facing surface of the platform.
- Distribution section added (currently absent).
- Service Configuration: retain the existing variable table; verify against the current `JuniperCanopySettings`.
- Quick Start: restructure the existing content into the §8 standard headings.
- Active Research Components: name the live network-topology renderer, the dataset previewer, the training-history viewer, and the WebSocket control surface (Phase D §S10, shipped 2026-04-14 per `[[project_phase_d_control_buttons_shipped]]`).
- Research Philosophy: replaced.

### 10.3 `juniper-cascor`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Cascor`. Description: three-to-five sentences naming this as the Cascade-Correlation training service, naming the REST + WebSocket interface, naming the candidate-pool training protocol, and stating its relationship to `juniper-cascor-worker`.
- Distribution section added.
- Dependency Lockfile section retained and refreshed; reference the constraint-mode freshness gate and the `/tmp/`-and-`mv` regeneration footgun captured in memory.
- Active Research Components: name the CasCor reference implementation, the distributed candidate-pool training, and the multi-network orchestration (see `juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_PHASE-6E-DESIGN.md` and `JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_PHASE-6E-MULTI-NETWORK-DESIGN.md`). The METRICS-MON R3.7 macOS CI integration soak completed 2026-05-15 and is mentioned only insofar as it enables cross-platform reproducibility claims.
- Quick Start, Research Philosophy: replaced per §8 and §9.

### 10.4 `juniper-data`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Data`. Description: three-to-five sentences naming this as the dataset-generation FastAPI service, naming the NPZ artifact contract, naming the named-version registry, and stating its role as the upstream of both `juniper-cascor` and `juniper-canopy`.
- Distribution section added.
- Service Configuration: extracted from existing prose into a table.
- Active Research Components: name the ARC-AGI dataset families, the named-version registry, and the dataset-API surface; the implementation of these is not research, but the **availability** of curated dataset families is itself a research artifact and is named as such.
- Quick Start, Research Philosophy: replaced per §8 and §9. The existing 24-endpoint API table is pushed entirely into `docs/api/` (a single decision, not an open choice); the README's Documentation section then links to that file. This keeps the README scannable and concentrates the endpoint reference where it can be regenerated against the OpenAPI schema.

### 10.5 `juniper-data-client`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Data Client`. Description: three-to-five sentences naming this as the Python HTTP client for `juniper-data`, naming its consumers (`juniper-cascor`, `juniper-canopy`), naming the NPZ schema it serializes, and stating its position in the dependency graph.
- Distribution section added.
- Architecture: small `Caller → JuniperDataClient → JuniperData` diagram plus prose.
- Quick Start: standard block with the existing client usage example as Verification.
- Research Philosophy: replaced; the optional third paragraph notes the client's role as the canonical integration boundary between training and data services.

### 10.6 `juniper-cascor-client`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Cascor Client`. Description: three-to-five sentences naming this as the HTTP/WebSocket client for `juniper-cascor`, naming the two WebSocket channels (training stream and control stream), and noting the reconnection-handling contract.
- Distribution section added.
- Architecture: small `Caller → JuniperCascorClient → JuniperCascor (REST+WS)` diagram.
- Active Research Components: name the WebSocket training-stream and control-stream protocols as research artifacts in their own right (the protocols are non-trivial and worth referring to).
- Existing API Reference table retained under Documentation.

### 10.7 `juniper-cascor-worker`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Cascor Worker`. Description: three-to-five sentences naming this as the distributed candidate-training worker, naming the WebSocket and legacy modes, and stating that it is managed by `juniper-cascor` rather than imported by it.
- Distribution section added.
- Service Configuration: the existing 15-variable env-var section is restructured into the canonical `Variable | Required | Default | Description` table; WebSocket-mode and legacy-mode variables are grouped.
- Docker Deployment: small section pointing at `juniper-deploy`'s `juniper-cascor-worker` service.
- Dependency Lockfile: documents both `requirements.lock` and `requirements-cpu.lock`.

### 10.8 `juniper-deploy`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Deploy`. Description: three-to-five sentences naming this as the Docker Compose orchestration for the full Juniper stack, naming the profile set (full, demo, dev, test, observability), and stating that it is not distributed via PyPI.
- Distribution section uses the no-PyPI variant in §6.
- Service Configuration: covers the env-var surface across all orchestrated services (consolidating what is currently spread across multiple subsections).
- Docker Deployment: this is the section of record; existing 447-line content is retained with editorial trimming for the new section order.
- Active Research Components: omitted, replaced by a "Stack Composition" subsection at the same place in the order; this is the only sanctioned per-repo deviation from §4, and the deviation is recorded here.
- Quick Start: trimmed per §8; reader is directed at the existing Profiles table for detail.

### 10.9 `juniper-observability`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Observability`. Description: three-to-five sentences naming this as the shared observability primitives package, naming the `register_or_reuse` collector helpers, naming the `juniper_observability.testing.reset_prometheus_registry` test fixture, and stating that it is published from the `juniper-ml` repository on a separate tag pattern.
- Distribution section added.
- Ecosystem Compatibility: minimum-pin row (`juniper-observability>=0.2.0`) and consumer compatibility table.
- Architecture: short ASCII diagram showing the consumer services that import the package.
- Active Research Components: omitted (infrastructure library); a `## Design Notes` subsection at the same position in the order points at `notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md`. This deviation, like §10.8's, is recorded here.
- Quick Start: standard block.

### 10.10 `juniper-doc-tools`

- Preamble added; logo asset placed at `images/Juniper_Logo_150px.png`.
- Application heading: `## Juniper Doc Tools`. Description: three-to-five sentences naming this as the shared markdown link-validator library and `juniper-check-doc-links` CLI, naming its role as the long-term replacement for the per-repo `scripts/check_doc_links.py` script, naming its support for cross-repo and ecosystem-root link classification (the `--cross-repo {skip,warn,check}` flag), and stating that it is published from the `juniper-ml` repository on a separate tag pattern (`juniper-doc-tools-v*`) analogous to `juniper-observability`.
- Distribution section added.
- Ecosystem Compatibility: minimum-pin row (`juniper-doc-tools>=0.1.0`) and a consumer-compatibility table that lists which repositories have completed the migration from the legacy `scripts/check_doc_links.py` to the packaged CLI.
- Architecture: short ASCII diagram showing the CI lanes that invoke `juniper-check-doc-links` and the consumer repositories that import `juniper_doc_tools` as a library.
- Service Configuration, Docker Deployment, Dependency Lockfile: omitted (library package; no service, no Docker image, no lockfile).
- Active Research Components: omitted (infrastructure library); a `## Design Notes` subsection at the same position in the order points at `notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md`. This deviation, like §10.8's and §10.9's, is recorded here.
- Quick Start: standard block; Verification is `juniper-check-doc-links --version` (zero-runtime-dependencies, no network).
- Documentation: link to the migration-plan note above and to the parent `juniper-ml/docs/REFERENCE.md` entry for the CLI; cross-link from `juniper-observability`'s Documentation section because the two packages travel together.

The §10.9 phrasing about a separately-versioned sibling library applies verbatim to this repository; the two libraries (observability + doc-tools) are the only two PyPI distributions published from the `juniper-ml` source tree under independent tag patterns. This shared shape is reflected in §12 by placing the two PRs together in the sequencing.

---

## 11. Documentation Audit Procedure

Every README's Documentation section is to be regenerated as part of its PR; no link is to be carried over from the prior version without explicit verification. The audit procedure for each README is:

1. **Inventory** the current Documentation section's targets.
2. **Validate internally** by running `juniper-check-doc-links --exclude templates --exclude history --exclude legacy` from the repository root (or, in repositories that have not yet completed the migration from the legacy script, `python util/check_doc_links.py …` with the same flags). Every link from the new Documentation section must resolve.
3. **Validate cross-repository** by running `juniper-check-doc-links --exclude templates --exclude history --exclude legacy --cross-repo check` against the populated parent directory; cross-repo links to other Juniper repositories' `docs/` files must resolve.
4. **Validate external** links (PyPI, GitHub) with a single `curl -sIL <url> | head -1` per link, expecting `HTTP/2 200`. Stale links are replaced or removed; redirects are followed and updated to the canonical URL.
5. **Verify rendering** by previewing the README on GitHub (push to a draft branch and inspect) before merging.

The `juniper-check-doc-links` CLI shipped with `juniper-doc-tools` (§10.10) is the canonical tool for steps 2 and 3 across the ecosystem; the legacy `util/check_doc_links.py` script is accepted only as a transitional fallback in repositories that have not yet migrated. Steps 2 and 3 are enforced by the existing CI lanes for the meta-package; they are run manually for the other repositories until equivalent CI is added.

---

## 12. Implementation Sequencing

The plan is executed in the order below. Each step is one pull request unless explicitly stated otherwise.

1. **Asset PR (`juniper-ml`).** Promote `Juniper_Logo_150px.png` and its `.xcf` source into `juniper-ml/images/`.
2. **Canonical Research Philosophy draft PR (`juniper-ml/notes/`).** Draft and review the canonical two paragraphs in `notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-XX.md`. No README edits in this PR.
3. **`juniper-ml` README PR.** Implement the full normalization for the meta-package. This becomes the reference implementation of the new layout.
4. **`juniper-canopy` README PR.** Update the existing template-bearing README to the new layout. (Order chosen second because the preamble is already in place.)
5. **Service READMEs (parallelizable).** Three independent PRs against `juniper-cascor`, `juniper-data`, and `juniper-cascor-worker`. May proceed in parallel once §3 is merged.
6. **Client-library READMEs (parallelizable).** Two independent PRs against `juniper-data-client` and `juniper-cascor-client`.
7. **Sibling-library READMEs (parallelizable).** Two independent PRs against `juniper-observability` and `juniper-doc-tools` (both live under `juniper-ml/`, both published as independently-tagged sibling packages, and both follow the same §10.9/§10.10 shape).
8. **`juniper-deploy` README PR.** Last because the trim-and-restructure operation on the 447-line file is the largest editorial step.

Step 3 (`juniper-ml` README) must merge before steps 5–8 open, because the downstream READMEs link to the `juniper-ml` README's Distribution and Documentation sections in their Ecosystem-Compatibility and Documentation blocks; opening steps 5–8 against a non-normalized `juniper-ml` README would produce link-audit failures in §11.

Each PR must include, in its description: a checklist mapping the §4 canonical-section table to the resulting file, the output of the §11 link-audit steps, and confirmation that the canonical Research-Philosophy paragraphs were inlined without modification.

---

## 13. Acceptance Criteria (Per README)

A README is considered normalized when **all** of the following hold:

1. The preamble in §3 appears verbatim except for the image `src` attribute.
2. An application title and a three-to-five-sentence application description appear immediately below the preamble.
3. A Distribution section appears immediately below the application description, with a working PyPI link to the package and a working PyPI link to `juniper-ml` (or, for `juniper-deploy`, the no-PyPI variant).
4. The project logo is present, references a local asset path, and renders both on GitHub and on PyPI.
5. The sections in §4 appear in the prescribed order; conditional sections appear only where the per-repo notes in §10 require them; no other top-level sections appear.
6. Ecosystem Compatibility, Architecture, Related Services, Service Configuration (where applicable), Docker Deployment (where applicable), Dependency Lockfile (where applicable), and Active Research Components are present and reflect the current state of the repository (no stale tables, no removed env-vars, no defunct ports).
7. The Quick Start Guide follows the §8 structure.
8. The Research Philosophy section contains the canonical two paragraphs, verbatim, with an optional third paragraph only where §10 sanctions one.
9. The Documentation section has been audited per §11; all link checks pass.
10. The README renders correctly on both GitHub and the PyPI project page (for repositories that publish to PyPI).

A normalization PR that does not meet all ten criteria for the repository it touches is not eligible to merge.

---

## 14. Out of Scope

The following are explicitly **not** part of this plan and are to be tracked separately if pursued:

- Changes to per-repository `docs/` directories beyond link-audit fixes.
- Introduction of new CI lanes (the existing `util/check_doc_links.py`-based lanes are sufficient for §11).
- Rewriting `CHANGELOG.md` files.
- Adding or removing PyPI extras.
- Adopting a shared README templating engine (rejected in §9.6).
- Re-keying the project logo (the existing `Juniper_Logo_150px.png` is the chosen asset).
- Changes to the parent `Juniper/CLAUDE.md` ecosystem documentation; that file remains the authority for cross-repo conventions and is referenced, not duplicated, from the normalized READMEs.

---

## 15. Validation Notes

This plan was developed against ground-truth audits of all ten in-scope READMEs and their supporting metadata (lockfiles, Dockerfiles, `pyproject.toml` files, conda environment manifests, and the parent `Juniper/CLAUDE.md`) collected on 2026-05-19. The initial audit covered nine repositories; `juniper-doc-tools` was added in a follow-up pass on the same day, after the parent had been re-checked for sibling libraries under `juniper-ml/`.
Three independent exploration passes assembled the inventory in §2, the section presence/absence data underpinning §4, and the per-repository deltas in §10.
Three additional independent validation passes — one factual, one coverage-against-original-requirements, one editorial — were run against this plan after its first draft, and the corrections surfaced by those passes have been applied.

Before any implementation PR is opened, a further independent validation pass is required, and it is to cover **every section of this plan**, not only the items listed in earlier drafts. The pre-implementation checklist for that pass is:

1. **§2 inventory** — re-confirm README line counts for all ten repositories, in case any has been edited since 2026-05-19.
2. **§3 reference template** — re-verify the canopy preamble lines are unchanged.
3. **§4 canonical section order** — confirm no new top-level sections have appeared in any in-scope README that the order would suppress.
4. **§5 image asset distribution** — confirm `Juniper_Logo_150px.png` and its `.xcf` source can be promoted into `juniper-ml/images/` without binary collisions or LFS gating problems.
5. **§6 Distribution / PyPI** — re-confirm package names and current versions against `pyproject.toml`.
6. **§7.1 Ecosystem Compatibility table** — confirm the version row to be inserted against the latest CI integration run.
7. **§7.2–7.7 per-section rules** — sanity-check that each rule still matches the corresponding existing-README content for at least one repository.
8. **§8 Quick Start table** — re-confirm the per-repository gap-closures against any recently merged Quick Start edits.
9. **§9 Research Philosophy constraints** — confirm the canonical-paragraph draft PR has landed before any README PR proceeds.
10. **§10 per-repository deltas** — confirm each repository's settings module, env-var surface, lockfile path set, and Docker presence have not drifted.
11. **§11 documentation audit** — run a dry pass of `util/check_doc_links.py` (both internal and cross-repo modes) against each repository's existing README to establish the link-audit baseline that the normalized README must clear.
12. **§12 sequencing** — re-confirm that no in-flight PR against a target repository would conflict with the README PR's diff.
13. **§13 acceptance criteria** — re-confirm each criterion remains measurable as written.

The validation pass is itself to be executed using specialized sub-agents (factual audit, coverage audit, editorial audit) in the same shape used to produce this plan. Findings from that pass are recorded as an appendix to this file rather than as silent edits, so the audit history is preserved.
