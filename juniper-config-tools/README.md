<!-- markdownlint-disable -->

# juniper-config-tools

Stdlib-only config helpers for the [Juniper ML platform](https://github.com/pcalnon/juniper-ml).

This package is the **single source of truth** for the env-var
alias-with-deprecation helper that has been independently re-implemented
across:

- `juniper-cascor` (CFG-03, CFG-05) — as pydantic `@field_validator`s
- `juniper-canopy` (CFG-04, CFG-16) — as pydantic `@field_validator`s
- `juniper-cascor-worker` (CFG-06, in flight) — as a standalone helper

The fourth repo's CFG-06 design surfaced the pattern as worth lifting.
Cascor-worker's strict "no Pydantic at runtime" invariant (pinned by
`tests/test_no_pydantic_at_runtime.py`, juniper-ml#168) ruled out
`juniper-observability` (which requires `pydantic>=2.0`), so this
package exists with a **stdlib-only** dependency policy.

This work mirrors the
[`juniper-doc-tools` PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)
(2026-05-18 doc-link validator incident) and the
[`juniper-ci-tools` PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md)
(2026-05-20 dep-docs generator divergence).

The full design and rollout plan lives at
[`notes/JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md)
in the juniper-ml repo.

## Installation

```bash
pip install juniper-config-tools
```

Runtime dependencies: **none** (stdlib only — `os`, `warnings`).

## Quick start

```python
from juniper_config_tools import env_with_legacy_alias

# Canonical name first; legacy alias triggers a DeprecationWarning when
# used.
server_url = env_with_legacy_alias(
    "JUNIPER_CASCOR_WORKER_SERVER_URL",  # new canonical name
    "CASCOR_SERVER_URL",                  # legacy alias (deprecated)
    default="",                           # returned if neither is set
)
```

Behaviour:

| env state                               | returns                                | warning?    |
|-----------------------------------------|----------------------------------------|-------------|
| `JUNIPER_CASCOR_WORKER_SERVER_URL` set  | its value                              | none        |
| only `CASCOR_SERVER_URL` set            | its value                              | one DepW    |
| both set                                | `JUNIPER_CASCOR_WORKER_SERVER_URL` val | none        |
| neither set                             | `""` (the `default`)                   | none        |

The `DeprecationWarning` text names both env-var names so operators can
mechanically fix configuration. The warning is emitted with
`stacklevel=2` so the warning's reported location is the caller's,
not this package's internals.

## API

### `env_with_legacy_alias(new_name, legacy_name=None, default=None)`

| Parameter      | Type             | Default  | Meaning                                            |
|----------------|------------------|----------|----------------------------------------------------|
| `new_name`     | `str`            | required | Canonical env-var name. Always checked first.       |
| `legacy_name`  | `str \| None`    | `None`   | Optional legacy alias. Pass `None` to disable.      |
| `default`      | `str \| None`    | `None`   | Value when neither env var is set.                  |

Returns `str | None`.

## Why a separate package?

This package exists because `juniper-cascor-worker` cannot adopt
`juniper-observability` (which requires pydantic) without breaking its
load-bearing no-Pydantic-at-runtime invariant.

For consumers that already use `pydantic-settings` (`juniper-cascor`,
`juniper-canopy`, `juniper-data`), this package is **not a replacement** —
the pydantic field-validator pattern in their `Settings` classes is the
right shape there. This package serves the constrained-runtime case.

## Versioning

`juniper-config-tools` follows [Semantic Versioning](https://semver.org/).
Public API surface in 0.1.0 is a single function: `env_with_legacy_alias`.
Consumers pin with `juniper-config-tools>=0.1.0,<0.2.0` to opt out of
future API growth that may add new functions without breaking changes.

## License

MIT — see [LICENSE](LICENSE).
