# `juniper-config-tools` PyPI Migration Plan

**Date:** 2026-05-22
**Author:** Paul Calnon (drafted by Claude)
**Status:** Shipped — `juniper-config-tools` v0.1.0 on PyPI (2026-05-22)
**Estimated effort:** 1–2 working days, single owner

---

## 1. Motivation

The Juniper ecosystem now contains **three** repos that re-implement the same
"read canonical env var; fall back to legacy with `DeprecationWarning`"
helper, with a fourth (cascor-worker) about to add it as CFG-06:

| Repo | Helper location | Shape | Status |
|---|---|---|---|
| juniper-cascor | `src/api/settings.py` — `_check_legacy_*` field validators | Pydantic `@field_validator("…", mode="before")` | Shipped (CFG-03, CFG-05) |
| juniper-canopy | `src/settings.py` — `_check_legacy_*` field validators | Pydantic `@field_validator("…", mode="before")` | Shipped (CFG-04 / CFG-16) |
| juniper-cascor-worker | `juniper_cascor_worker/config.py::WorkerConfig.from_env()` (planned) | Standalone helper (no pydantic, see §3.1) | In design ([cascor-worker#84](https://github.com/pcalnon/juniper-cascor-worker/pull/84), CFG-06) |
| juniper-data | (none yet) | n/a | Future candidate |

Each repo currently inlines the deprecation logic with the same shape: check
new-prefix env, fall back to legacy-prefix env with a `DeprecationWarning`
that names both old + new vars. The fourth implementation in cascor-worker
prompted the question — does this belong in a shared package?

This is **the same incident class** as:

- The 2026-05-18 doc-link validator incident → solved by `juniper-doc-tools`
- The 2026-05-20 dep-docs generator divergence → solved by `juniper-ci-tools`

This plan applies the proven pattern: ship a small focused PyPI package,
land it in the most-constrained consumer first, allow other repos to
migrate at their own cadence.

## 2. Goals & non-goals

### Goals

1. **Single source of truth** for the alias-with-deprecation helper —
   one canonical implementation, one test suite, one behaviour to reason
   about.
2. **Stdlib-only runtime deps** — `os` + `warnings` only. Cascor-worker's
   `tests/test_no_pydantic_at_runtime.py` invariant (see §3.1) makes this
   non-negotiable for the worker; making it the package-wide policy keeps
   the door open for the most-constrained consumer to adopt.
3. **Versioned PyPI releases** so each consumer can pin a specific
   behaviour and roll forward independently.
4. **Drift detection** (§5) — a CI lint in juniper-ml that fails when a
   consumer repo's pin excludes the current published version, mirroring
   `tests/test_doc_tools_drift.py` and `tests/test_ci_tools_drift.py`.

### Non-goals

- **No migration wave 3+ in this plan.** The Pydantic-validator-based
  helpers in cascor + canopy are a different shape (bound to a Settings
  field) and won't migrate to the standalone helper cleanly. Lifting
  them is a separate item once the standalone helper has shipped and
  proven itself. This plan covers Waves 0–2 only: scaffold, publish,
  and cascor-worker consumption.
- **No "all Juniper env-var helpers" abstraction.** This package starts
  with one function. Resist the temptation to design a Settings-adjacent
  framework. Add functions only when a real second consumer needs them.
- **No replacement of `pydantic-settings`.** Repos that already use
  `pydantic-settings` (canopy, cascor, data) keep doing so. juniper-
  config-tools serves the constrained-runtime case (cascor-worker), not
  the general case.
- **No CHANGELOG synchronisation across repos.** Each consumer manages
  its own CHANGELOG; juniper-config-tools manages its own.

## 3. Inventory

### 3.1 Cascor-worker pydantic-at-runtime constraint (load-bearing)

`juniper_cascor_worker/tests/test_no_pydantic_at_runtime.py` (in cascor-
worker `0.3.0`) pins three subprocess-isolated invariants:

```text
test_worker_constants_does_not_load_pydantic
test_worker_module_does_not_load_pydantic
test_full_worker_package_does_not_load_pydantic
```

Each runs `python -c "import …; assert 'pydantic' not in sys.modules"`
in a fresh subprocess. The runtime dependency graph today:

| Cascor-worker runtime dep | Pulls pydantic? |
|---|---|
| numpy>=1.24.0 | no |
| torch>=2.0.0 | no |
| websockets>=11.0 | no |
| juniper-cascor-protocol>=0.1.0 | yes on disk (envelope subpackage), never imported by worker |

R2 exit-gate decision (juniper-ml#168) committed to this constraint.
Any shared package the worker consumes must therefore not pull pydantic
at import time. **juniper-observability requires `pydantic>=2.0`** in
its core deps and is therefore not a viable home for the helper.

This constraint is what forces juniper-config-tools into a separate
package rather than reuse of juniper-observability.

### 3.2 Existing helper shapes

**Pydantic-validator shape (cascor, canopy):**

```python
@field_validator("demo_mode", mode="before")
@classmethod
def _check_legacy_demo_mode(cls, v):
    if os.getenv("JUNIPER_CANOPY_DEMO_MODE") is not None:
        return v
    legacy = os.getenv("CASCOR_DEMO_MODE")
    if legacy is not None:
        warnings.warn(
            "CASCOR_DEMO_MODE is deprecated. Use JUNIPER_CANOPY_DEMO_MODE instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy.lower() in ("1", "true", "yes")
    return v
```

**Standalone-helper shape (cascor-worker, planned per CFG-06 design):**

```python
def env_with_legacy_alias(
    new_name: str,
    legacy_name: str | None,
    default: str | None = None,
) -> str | None:
    val = os.environ.get(new_name)
    if val is not None:
        return val
    if legacy_name is not None:
        legacy_val = os.environ.get(legacy_name)
        if legacy_val is not None:
            warnings.warn(
                f"{legacy_name} is deprecated; use {new_name} instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return legacy_val
    return default
```

The standalone shape is what juniper-config-tools ships. The
pydantic-validator shape stays in-place at each Settings-using repo —
it can call the standalone helper internally if it wants, but that's
optional and tracked separately.

## 4. Package scope (juniper-config-tools 0.1.0)

**Single public function**:

```python
juniper_config_tools.env_with_legacy_alias(
    new_name: str,
    legacy_name: str | None = None,
    default: str | None = None,
) -> str | None
```

Behaviour:

| Env state | Returns | Warning |
|---|---|---|
| `new_name` set | `os.environ[new_name]` | none |
| `new_name` unset, `legacy_name` set | `os.environ[legacy_name]` | one `DeprecationWarning` |
| both set | `os.environ[new_name]` | none (legacy silently ignored) |
| neither set | `default` | none |

Warning text: `f"{legacy_name} is deprecated; use {new_name} instead."`

Warning frequency: **once-per-location** (Python `warnings` default).
This was the explicit CFG-06 design-doc resolution by Paul.

`stacklevel=2` so the warning reports the caller's file:line, not
juniper-config-tools' internal site.

**That's it.** No second function in 0.1.0. No `EnvAlias` class. No
`SettingsMixin`. No magic. Single function, single behaviour.

## 5. Package layout

Mirrors `juniper-doc-tools/` and `juniper-ci-tools/` exactly:

```text
juniper-ml/
└── juniper-config-tools/
    ├── pyproject.toml            # name=juniper-config-tools, version=0.1.0, no runtime deps
    ├── README.md                 # PyPI landing page
    ├── CHANGELOG.md              # Keep a Changelog format
    ├── LICENSE                   # MIT (symlink to juniper-ml/LICENSE? see §8.2)
    ├── juniper_config_tools/
    │   ├── __init__.py           # re-exports env_with_legacy_alias
    │   └── _env_aliases.py       # the helper itself (private module)
    └── tests/
        ├── conftest.py           # pytest config
        └── test_env_with_legacy_alias.py
```

The pyproject pin contract:

```toml
[project]
name = "juniper-config-tools"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []           # stdlib only

[project.optional-dependencies]
test = ["pytest>=8.0", "pytest-cov>=4.0"]
```

`>=3.10` (rather than 3.12 like juniper-observability) so cascor-worker
(>=3.12), cascor (>=3.12), data (>=3.12), canopy (>=3.11), data-client
(>=3.12), cascor-client (>=3.11), and any future older-Python consumer
can all adopt without floor-raise.

## 6. Wave plan

### Wave 0 — Package scaffold (PR to juniper-ml)

- Add `juniper-config-tools/` subdirectory with pyproject, README,
  CHANGELOG, `juniper_config_tools/{__init__.py, _env_aliases.py}`,
  `tests/test_env_with_legacy_alias.py`.
- Tests cover 4 env states × handful of name shapes; assert
  warning fires exactly once per `stacklevel=2` location.
- Add `.github/workflows/publish-config-tools.yml` mirroring
  `publish-doc-tools.yml` and `publish-ci-tools.yml` — TestPyPI then
  PyPI on `juniper-config-tools-v*` tags, OIDC trusted publishing.
- Add `.github/workflows/ci.yml` job lane `juniper-config-tools` that
  runs the test suite when the subdir changes.
- Add `tests/test_pyproject_extras.py`-style sanity if juniper-ml's
  top-level pyproject `[tools]` extra needs a new entry (TBD — see
  §8.3).
- No drift-detection lint yet (Wave 2 deferred until there's a real
  consumer pin to drift against).

### Wave 1 — Publish 0.1.0 to PyPI

- Create GitHub release `juniper-config-tools-v0.1.0` → triggers
  publish workflow → TestPyPI install verification → PyPI.
- Manual smoke: `pip install juniper-config-tools` in a fresh venv,
  `python -c "from juniper_config_tools import env_with_legacy_alias"`.

### Wave 2 — CFG-06 cascor-worker implementation (PR to cascor-worker)

- Add `juniper-config-tools>=0.1.0,<0.2.0` to cascor-worker pyproject
  `dependencies`.
- Rename all 15 `ENV_*` constants in `constants.py` to canonical
  `JUNIPER_CASCOR_WORKER_*` names; add `LEGACY_ENV_*` pairs.
- `WorkerConfig.from_env(env: Mapping[str, str] | None = None)` —
  the Mapping-injection contract Paul requested in the CFG-06 design
  doc resolution. Default to `os.environ` when `env is None`. Calls
  `env_with_legacy_alias` for each field, but **substitutes** `env`
  for `os.environ.get` when the parameter is provided.
- New regression suite mirrors the CFG-06 design doc §8 plan
  (parametrized 15 × 4 cases + source-level scope guard +
  integration smoke).
- Re-runs `tests/test_no_pydantic_at_runtime.py` — must still pass
  with the new juniper-config-tools dep on disk.
- Update juniper-ml's `[tools]` extra to include `juniper-config-tools`
  (only if Wave 0 didn't already).

### Wave 3+ — Other-repo adoption (deferred, not in this plan)

Pydantic-validator-style helpers in cascor + canopy remain as-is.
They may internally call `env_with_legacy_alias` later — that's a
trivial cleanup PR per repo when there's appetite. Not blocking and
not on this plan's critical path.

## 7. CI / release pipeline

Wave 0 adds:

- `juniper-ml/.github/workflows/ci.yml` — new `juniper-config-tools`
  job lane: install editable + run pytest. Triggered on changes
  under `juniper-config-tools/**`.
- `juniper-ml/.github/workflows/publish-config-tools.yml` — copy of
  `publish-ci-tools.yml` (which was itself a copy of
  `publish-doc-tools.yml`). Single source-of-truth file edit: pkg
  name, subdir, tag pattern.

Workflow tag pattern: `juniper-config-tools-v*` (matches the
`juniper-X-tools-v*` precedent for both sibling packages).

## 8. Open questions

### 8.1 Should `env_with_legacy_alias` accept a list of legacy aliases?

Some real-world cases have multiple legacy names (e.g. `CASCOR_*` →
`CASCOR_WORKER_*` → `JUNIPER_CASCOR_WORKER_*`). Signature options:

- **A**: single `legacy_name: str | None` (this plan). Caller chains:
  `env_with_legacy_alias("NEW", "MID") or env_with_legacy_alias("MID", "OLD")`.
  Verbose but explicit.
- **B**: `legacy_names: Sequence[str] | None` (variadic). Cleaner for
  multi-hop migrations.

**Recommendation**: ship single-legacy (option A) in 0.1.0. Add
variadic in 0.2.0 only when a real consumer needs it. Avoids
over-design on a single function.

### 8.2 License file: copy or symlink to juniper-ml/LICENSE?

`juniper-doc-tools/LICENSE` and `juniper-ci-tools/LICENSE` are both
**regular files** (verified in the repo on `origin/main`), not
symlinks. Stick with regular file copy for consistency and to avoid
sdist symlink-resolution edge cases.

### 8.3 Should juniper-ml's `[tools]` extra include juniper-config-tools?

The `[tools]` extra (juniper-ml 0.5.0) currently includes
juniper-doc-tools, juniper-ci-tools, juniper-observability. Adding
juniper-config-tools as a fourth makes `pip install juniper-ml[tools]`
self-consistent. Recommendation: **yes**, add in Wave 0 alongside the
scaffold.

`tests/test_pyproject_extras.py` is the lint that pins the `[tools]`
membership — it'll need a one-line update in the same PR.

### 8.4 Drift-detection lint (§5.1 equivalent)

`tests/test_doc_tools_drift.py` and `tests/test_ci_tools_drift.py`
already exist in juniper-ml; both extract consumer-repo pins of
`juniper-doc-tools` / `juniper-ci-tools` and assert the range still
admits the current published version.

For juniper-config-tools, the analogue would walk consumer repos
(cascor-worker primarily) and validate the pin. **Recommendation**:
add `tests/test_config_tools_drift.py` in Wave 2 (the PR that adds
the cascor-worker pin), not Wave 0 (no pin to drift against yet).

## 9. Acceptance criteria

This plan is "complete" when:

- [ ] Wave 0 PR merged: juniper-config-tools/ scaffold in juniper-ml,
      CI lane green, pyproject `[tools]` extra updated.
- [ ] Wave 1: juniper-config-tools 0.1.0 visible on PyPI; install
      verification done.
- [ ] Wave 2 PR merged: cascor-worker CFG-06 implementation consumes
      juniper-config-tools>=0.1.0,<0.2.0; all CFG-06 acceptance
      criteria (per cascor-worker design doc §11) also satisfied;
      `test_no_pydantic_at_runtime.py` still passes.
- [ ] v7 roadmap §2.2 status pass updated: CFG-06 marked ✅ shipped.

Wave 3+ adoption by other repos is not part of this plan's
acceptance — those are tracked as separate items.

## 10. References

- **Sibling-package plans (precedent)**:
  - [`notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](./JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)
  - [`notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md`](./JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md)
- **CFG-06 design doc (consumer of this package)**:
  - [`juniper-cascor-worker/notes/CFG_06_ENV_PREFIX_CONVERGENCE_DESIGN_2026-05-22.md`](https://github.com/pcalnon/juniper-cascor-worker/blob/main/notes/CFG_06_ENV_PREFIX_CONVERGENCE_DESIGN_2026-05-22.md) (merged via [cascor-worker#84](https://github.com/pcalnon/juniper-cascor-worker/pull/84))
- **Cascor-worker pydantic-at-runtime invariant**:
  - `juniper-cascor-worker/tests/test_no_pydantic_at_runtime.py`
  - R2 exit-gate decision: [juniper-ml#168](https://github.com/pcalnon/juniper-ml/pull/168)
- **Pydantic-validator-style helper precedent (NOT migrating in Waves 0–2)**:
  - cascor `src/api/settings.py::_check_legacy_log_level` (CFG-05)
  - canopy `src/settings.py::_check_legacy_demo_mode` (CFG-04 / CFG-16)
- **Roadmap reference**:
  - v7 §20 [CFG-06](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md#cfg-06-cascor_-env-prefix-inconsistent-with-juniper_-convention)
  - v7 §2.2 [status pass](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md#22-v701--v702-status-pass--configuration--api-contract-items-2026-05-22) (merged via [juniper-ml#317](https://github.com/pcalnon/juniper-ml/pull/317))
