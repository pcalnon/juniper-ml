<!-- markdownlint-disable MD013 MD033 MD041 -->
<!--
  MD013 (line-length): README contains prose paragraphs that intentionally
                       exceed the 512-char ecosystem limit. Disabled file-wide
                       since wrapping mid-sentence harms PyPI rendering.
  MD033 (no-inline-html): The right-aligned logo + spacing rely on HTML.
  MD041 (first-line-heading): The HTML logo is the first line by design.
-->
<div align="right" width="150px" height="150px" align="right" valign="top"> <img src="images/Juniper_Logo_150px.png" alt="Juniper" align="right" valign="top" width="150px" /></div>
<br /> <br /> <br /> <br />

# Juniper: Dynamic Neural Network Research Platform

Juniper is an AI/ML research platform for investigating dynamic neural network architectures and novel learning paradigms.  The project emphasizes ground-up implementations from primary literature, enabling a more transparent exploration of fundamental algorithms.

## Juniper Doc Tools

`juniper-doc-tools` is the **shared markdown link-validator library and CLI** for the Juniper platform. It ships the `juniper-check-doc-links` console script (also invocable as `python -m juniper_doc_tools`) and the underlying `juniper_doc_tools` Python module, both of which validate relative file links, same-file anchors, cross-repo links into sibling Juniper repositories, and ecosystem-root links into the parent `Juniper/` directory — with a `--cross-repo {skip,warn,check}` flag that selects how cross-repo references are handled in CI. The package is the long-term replacement for the per-repository `scripts/check_doc_links.py` validator that historically lived in every Juniper repo. It is hosted in the `juniper-ml` repository under `juniper-doc-tools/` but published to PyPI on its own tag pattern (`juniper-doc-tools-v*`), independently of the meta-package release cadence and analogous to the publishing model used by [`juniper-observability`](../juniper-observability/README.md).

## Distribution

`juniper-doc-tools` is published on PyPI as **[`juniper-doc-tools`](https://pypi.org/project/juniper-doc-tools/)**.
The package is also surfaced through the platform meta-distribution
**[`juniper-ml`](https://pypi.org/project/juniper-ml/)** under the `[doc-tools]` and `[all]` extras, so `pip install juniper-ml[all]` brings it in along with the rest of the client stack:

```bash
pip install juniper-doc-tools                  # direct install
pip install "juniper-ml[doc-tools]"            # via the meta-package
```

`juniper-doc-tools` has **no runtime dependencies** — it is pure stdlib. This keeps the package safe to install into the slimmest CI images.

## Ecosystem Compatibility

This shared-tooling package is part of the [Juniper](https://github.com/pcalnon/juniper-ml) ecosystem.
Minimum compatible version for consumer repositories:

| Consumer | Minimum `juniper-doc-tools` pin | Migration status |
|----------|----------------------------------|------------------|
| `juniper-ml` | `>=0.1.0,<0.2.0` (via `[doc-tools]` extra) | Migrated — inline `util/check_doc_links.py` deleted (Wave 4) |
| `juniper-data` | `>=0.1.0,<0.2.0` | Migrated — `scripts/check_doc_links.py` deleted |
| `juniper-cascor` | `>=0.1.0,<0.2.0` | Migrated |
| `juniper-canopy` | `>=0.1.0,<0.2.0` | Migrated |
| `juniper-data-client` | `>=0.1.0,<0.2.0` | Migrated |
| `juniper-cascor-client` | `>=0.1.0,<0.2.0` | Migrated |
| `juniper-cascor-worker` | `>=0.1.0,<0.2.0` | Migrated |
| `juniper-deploy` | `>=0.1.0,<0.2.0` | Migrated |

The full migration sequence, including the four-wave structure and the per-repo PR references, is documented in [`../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md).

## Architecture

`juniper-doc-tools` is a shared infrastructure library — it has no service of its own, no Docker image, and no lockfile. It is consumed at CI time (via the `juniper-check-doc-links` CLI) and at library-import time (via `from juniper_doc_tools import validate_directory`) by every Juniper repository's documentation-link gate.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                            juniper-doc-tools                        │
│  juniper-check-doc-links  ·  python -m juniper_doc_tools  ·  API    │
└──────────┬────────────┬─────────────┬─────────────┬─────────────────┘
           │ CI lane    │ CI lane     │ CI lane     │ CI lane (×8)
           ▼            ▼             ▼             ▼
   ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐
   │ juniper-ml  │ │ juniper- │ │ juniper- │ │ juniper-{data,     │
   │ docs job    │ │ canopy   │ │ cascor   │ │ data-client, ... } │
   └─────────────┘ └──────────┘ └──────────┘ └────────────────────┘
```

Validated link classes (per file class `.md` / `.markdown` / `.rst` / `.txt`):

- **Relative file links** — `[text](path/to/file.md)`; the target must exist on disk.
- **Same-file anchors** — `[text](#some-heading)`; the heading must exist in the source file.
- **Cross-repo links** — `../juniper-<repo>/path/in/sibling.md`; classified by regex against the known Juniper ecosystem repo set, subject to the `--cross-repo` policy.
- **Ecosystem-root links** — `../../CLAUDE.md`, `../../notes/...`; paths into the Juniper parent directory; also subject to `--cross-repo` policy unless `--strict-repo-boundary` is set.

External URLs (`http://`, `https://`, `mailto:`) and embedded images (`data:`, `//`) are skipped.

## Related Services

| Component | Relationship | Notes |
|-----------|-------------|-------|
| Every Juniper repository's docs CI lane | Invokes `juniper-check-doc-links` in `--cross-repo skip` mode | Wave-1/2 migration completed; legacy `scripts/check_doc_links.py` deleted in Wave 4 |
| [juniper-ml](https://pypi.org/project/juniper-ml/) | Aggregates this package under `[doc-tools]` and `[all]` | `juniper-ml[all]` installs the full client stack including `juniper-doc-tools` |
| [juniper-observability](../juniper-observability/README.md) | Sibling library published from the same repository on an independent tag pattern (`juniper-observability-v*`) | Cross-link |

## Design Notes

> **Note** — per §10.10 of [`../notes/README_NORMALIZATION_PLAN_2026-05-19.md`](../notes/README_NORMALIZATION_PLAN_2026-05-19.md), the **Active Research Components** section is replaced by **Design Notes** for this repository, because `juniper-doc-tools` is an infrastructure library rather than a research component. This is the same substitution applied to the sibling [`juniper-observability`](../juniper-observability/README.md) README per §10.9. The substituted heading sits at the §4 slot #10 position (between Related Services and Quick Start Guide), per the plan's "same position in the order" stipulation.

| Document | Purpose |
|----------|---------|
| [`../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md) | Full migration plan: four-wave structure, per-repo PR references, deprecation of the per-repo `scripts/check_doc_links.py` validator |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | Parent `juniper-ml` reference: extras (including `[doc-tools]`), compatibility matrix, environment variables |

## Quick Start Guide

### Prerequisites

- Python ≥ 3.12

The package has no runtime dependencies. It is safe to install into the slimmest CI image without pulling in transitive packages.

### Installation

```bash
pip install juniper-doc-tools
```

For development:

```bash
pip install "juniper-doc-tools[test]"
```

### Verification

```bash
juniper-check-doc-links --version
```

A typical CI invocation (matching the pattern used across every Juniper repo's docs lane):

```bash
juniper-check-doc-links \
  --exclude templates --exclude history --exclude legacy \
  --cross-repo skip
```

The equivalent library-mode invocation:

```python
from pathlib import Path
from juniper_doc_tools import validate_directory

result = validate_directory(
    Path("."),
    exclude_dirs={"templates", "history"},
    cross_repo_mode="skip",
)
if not result.ok:
    for error in result.errors:
        print(error)
    raise SystemExit(1)
print(f"All {result.scanned_files} files OK ({result.cross_repo_skipped} cross-repo links skipped)")
```

Exit codes: `0` if all links are valid, `1` if broken links are found or arguments are invalid.

### Next Steps

- [`../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md) — full migration plan, four-wave structure, per-repo PR references
- [`../docs/REFERENCE.md`](../docs/REFERENCE.md) — parent `juniper-ml` reference (extras, compatibility, environment variables)
- [`juniper-ml`](https://pypi.org/project/juniper-ml/) — platform meta-package on PyPI
- [`juniper-observability`](../juniper-observability/README.md) — sibling library on a separate tag pattern

## Research Philosophy

The Juniper platform exists to study learning algorithms whose network architecture is not fixed in advance. Its initial anchor is the Cascade-Correlation algorithm of Fahlman and Lebiere (1990), implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail. The organizing commitment is that algorithm implementations remain inspectable at the level at which they were originally specified: candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper. This permits comparative work — across algorithms, datasets, and hyperparameter regimes — to be conducted on a known and reproducible substrate.

The current platform comprises a Cascade-Correlation training service exposing a REST and WebSocket interface, a dataset-generation service with a named-version registry that includes the ARC-AGI families, a real-time monitoring dashboard for inspecting training dynamics as they occur, and a distributed worker that parallelizes candidate-unit training across hosts. Near-term work extends the architectural-growth catalogue beyond Cascade-Correlation, introduces multi-network orchestration for comparative experiments at the level of network populations rather than individual runs, and tightens the dataset–training–monitoring loop into a reproducible research workbench. The longer-term direction is the systematic empirical study of constructive and architecture-growing learning algorithms, with first-class infrastructure for the ablation, comparison, and replication that such a study requires.

## Documentation

| Document | Purpose |
|----------|---------|
| [`../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](../notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md) | Full migration plan: four-wave structure, per-repo PR references, deprecation of the per-repo `scripts/check_doc_links.py` validator |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | Parent `juniper-ml` reference: extras (including `[doc-tools]`), compatibility matrix, environment variables |
| [`../README.md`](../README.md) | Parent `juniper-ml` meta-package README |
| [`../juniper-observability/README.md`](../juniper-observability/README.md) | Sibling library README — shared infrastructure published on an independent tag pattern |

### Release Workflow

`juniper-doc-tools` is versioned and published independently of the root `juniper-ml` meta-package.

| Package | Tag pattern | Workflow | Build root |
|---------|-------------|----------|------------|
| `juniper-ml` | `v*` GitHub releases | `.github/workflows/publish.yml` | repository root |
| `juniper-observability` | `juniper-observability-v*` tag pushes | `.github/workflows/publish-observability.yml` | `juniper-observability/` |
| `juniper-doc-tools` | `juniper-doc-tools-v*` tag pushes | `.github/workflows/publish-doc-tools.yml` | `juniper-doc-tools/` |

The doc-tools workflow builds an sdist and wheel from this subdirectory, publishes first to TestPyPI through OIDC trusted publishing, retries installation from TestPyPI to tolerate index lag, runs the CLI's `--version` check as the smoke test, then promotes the same artifact to PyPI after the `pypi` environment gate.

## License

MIT — see [`LICENSE`](LICENSE).
