# Meta-Package Extras Surface — Requirements Source Doc

**Date**: 2026-05-21
**Author**: Paul Calnon
**Status**: Source document (awaiting JR-ID assignment in next snapshot refresh)
**Applies to**: `juniper-ml` meta-package (`pyproject.toml` extras)

---

## 1. Purpose

This document specifies the requirements governing the `juniper-ml` meta-package's optional-dependency surface: the set of `[project.optional-dependencies]` groups declared in `pyproject.toml` that determine which Juniper packages a caller installs via `pip install juniper-ml[<group>]`.

The extras surface is a public PyPI contract. Adding, removing, or renaming an extra is observable by every external caller; consequently it warrants explicit requirement tracking rather than being managed only as ad-hoc `pyproject.toml` edits.

The document is written in the style of source notes docs that feed the snapshot consolidation pipeline (`REQUIREMENTS_IDENTIFICATION_PLAN_2026-05-11.md` Phase 4). HTML `<!-- requirement: JR-* -->` markers are intentionally omitted because no IDs have yet been assigned; the next refresh that processes this file is expected to allocate IDs in the `JR-ML-DEP-*` family (or a new `META` family if introduced).

---

## 2. Scope

In scope:

- The set of extras names declared in `juniper-ml/pyproject.toml`.
- The packages aggregated under each extra and their version pins.
- The behavior of the `[all]` aggregate extra.
- Documentation surfaces that must remain consistent with the pyproject (`AGENTS.md`, `README.md`, `docs/REFERENCE.md`, `docs/QUICK_START.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `CHANGELOG.md`).
- Regression coverage (`tests/test_pyproject_extras.py`).

Out of scope:

- Version bump policy for the underlying child packages (governed by each child repo's own requirements).
- The Docker-orchestration surface (`juniper-deploy`); the deploy repo's `docker-compose.yml` references images, not PyPI extras.

---

## 3. Requirements

### 3.1 Extras surface — declared groups

The meta-package MUST declare the following optional-dependency groups, with at minimum the following member packages and pins. Stricter pins or additional members are permitted; missing groups or missing members are not.

| Group       | Member packages and minimum pins                                                                                          |
|-------------|---------------------------------------------------------------------------------------------------------------------------|
| `clients`   | `juniper-data-client>=0.4.0`, `juniper-cascor-client>=0.3.0`                                                              |
| `worker`    | `juniper-cascor-worker>=0.3.0`                                                                                            |
| `servers`   | `juniper-canopy>=0.3.0`, `juniper-cascor>=0.3.17`, `juniper-data>=0.6.0`                                                  |
| `tools`     | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-observability>=0.2.0` |
| `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` — retained as a back-compat alias for the same dependency listed in `tools`             |
| `all`       | Recursive reference of the form `juniper-ml[<group1>,<group2>,...]` that aggregates every non-alias group exactly once    |

**Rationale.** The four functional groups (`clients`, `worker`, `servers`, `tools`) partition the Juniper package set into install-cohort categories. The `doc-tools` alias preserves the install path callers used before the `tools` aggregate was introduced (juniper-ml v0.5.0); removing it would be a breaking change visible to downstream users on PyPI.

### 3.2 `[all]` aggregate semantics

The `[all]` extra MUST:

- Be expressed as a single recursive reference to the other extras using PEP-508 self-referential syntax (`juniper-ml[a,b,c]`), not as a flat list of packages.
- Aggregate every functional group exactly once.
- Exclude the `doc-tools` alias from the recursive reference, because `doc-tools` is a subset of `tools` and including both would create a redundant entry in the resolved dependency graph.

**Rationale.** Recursive aggregation guarantees that updates to a constituent group propagate to `[all]` automatically. Flat aggregation was used in earlier juniper-ml versions and produced drift between `[all]` and the underlying groups when authors forgot to update both.

### 3.3 Version bump policy

Adding a new extra group or expanding an existing group's membership is a SemVer **minor** bump.

Removing an extra group, removing a package from a group, or tightening a version pin in a way that excludes previously-resolved versions is a SemVer **major** bump.

Adding a new package version constraint that admits all previously-resolved versions (e.g. raising the lower bound from `>=0.4.0` to `>=0.4.1` when no caller is known to have `0.4.0` installed) is a SemVer **minor** bump, unless the upgrade is strictly additive and the affected package's own release notes confirm no API surface change, in which case **patch** is acceptable.

### 3.4 Documentation consistency

The following documentation surfaces MUST reflect the same extras structure as `pyproject.toml`:

- `README.md` — "Related Services" table, "Extras" table, "Install" code block, "Ecosystem Compatibility" table.
- `AGENTS.md` — "Dependency extras reference" table, editable-install code block.
- `docs/REFERENCE.md` — "Available Extras" table, "Installation Commands" code block, "Package Descriptions" table, "Ecosystem Compatibility" table.
- `docs/QUICK_START.md` — "What Each Extra Installs" table, install commands, expected `pip list` output.
- `docs/DOCUMENTATION_OVERVIEW.md` — "What It Installs" diagram block, "Compatibility" table.
- `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` — per-extra editable-install rows.
- `CHANGELOG.md` — entry under the next `[Unreleased]` heading describing the extras change.

**Rationale.** The documentation surface is the user-facing specification for callers who do not read `pyproject.toml`. Drift between the two has occurred (e.g. the `0.4.x` Ecosystem Compatibility row remained after `[doc-tools]` and `[ci-tools]` were added in v0.4.1, was rewritten in v0.5.0).

### 3.5 Regression coverage

`tests/test_pyproject_extras.py` MUST exist and MUST assert at least:

- The exact set of extras declared.
- The exact membership of each extra.
- That `[all]` aggregates every non-alias extra exactly once.
- That `[project].version` is in semver-ish (`X.Y.Z[...]`) form.

The test MUST be wired into `.github/workflows/ci.yml` so the contract is enforced on every PR.

**Rationale.** Without the lint, a PR that drops a package from `[all]` or mistypes an extra name ships silently. The lint converts that class of error from "discovered by a user via `pip install` warning" to "discovered by CI before merge".

### 3.6 Install-size advisory

`docs/QUICK_START.md` and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` SHOULD include an advisory note that `pip install juniper-ml[all]` transitively pulls a multi-GB dependency tree (notably `torch`, brought in via `juniper-cascor-worker` and `juniper-cascor`). Callers who do not need the worker or server distributions SHOULD use a narrower extra (`[clients]`, `[tools]`, or `[doc-tools]`).

**Rationale.** The size jump between v0.4.x `[all]` (clients + worker only) and v0.5.x `[all]` (clients + worker + servers + tools) is the difference between roughly 30 MB of wheels and approximately 5 GB on disk after install (measured on Python 3.13 + Linux x86_64 against PyPI on 2026-05-21; the original v0.5.0 estimate of "roughly 2 GB" was wheel-size-only and understated the resolved disk footprint by ~2.5x).
Users who learn this only after running `pip install` in a constrained environment lose minutes per attempt.

---

## 4. Acceptance criteria (for the next snapshot refresh)

When this document is processed by the next snapshot consolidation pass:

1. Each numbered requirement in §3 should be allocated a `JR-ML-*` ID. The natural category code is `DEP` (deployment-config — Docker, Compose, K8s, Helm, image build) — extras surface is a build-and-distribute concern — or a new `META` family if the maintainers decide the meta-package distribution surface deserves its own area code.
2. The resulting IDs should be referenced from `juniper-ml#295` (the v0.5.0 introduction of `[servers]` + `[tools]`), `juniper-ml#293` (`[ci-tools]`), and `juniper-ml#299` (the docs-polish + lint PR) using `Closes JR-*` / `Partially closes JR-*` verbs per `REQUIREMENTS_NEXT_STEPS.md` §4.
3. After IDs are assigned, this document can be amended with inline `<!-- requirement: JR-* -->` markers per `REQUIREMENTS_NEXT_STEPS.md` §5 to enable bidirectional mapping from prose to ID.

---

## 5. References

- `REQUIREMENTS_IDENTIFICATION_PLAN_2026-05-11.md` — Phase 4 consolidation methodology that this document is shaped for.
- `REQUIREMENTS_NEXT_STEPS.md` §4 — JR-ID PR-reference convention.
- `REQUIREMENTS_NEXT_STEPS.md` §5 — Author-side `<!-- requirement: JR-* -->` markers in source docs.
- `juniper-ml/pyproject.toml` — Authoritative extras declaration.
- `juniper-ml/tests/test_pyproject_extras.py` — Lint test enforcing §3.1 + §3.2 + §3.5.
- `juniper-ml#293`, `#295`, `#299` — PRs that established and refined the extras surface this document describes.
