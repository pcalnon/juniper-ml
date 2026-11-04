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
[`juniper-doc-tools` PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md)
(2026-05-18 doc-link validator incident) and the
[`juniper-ci-tools` PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md)
(2026-05-20 dep-docs generator divergence).

The full design and rollout plan lives at
[`notes/JUNIPER_2026-05-22_JUNIPER-ML_CONFIG-TOOLS-PYPI-MIGRATION-PLAN.md`](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-05-22_JUNIPER-ML_CONFIG-TOOLS-PYPI-MIGRATION-PLAN.md)
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
| canonical set to `""`                   | `""` (legacy is not read)              | none        |
| only `CASCOR_SERVER_URL` set            | its value                              | one DepW    |
| only the legacy name set to `""`        | `""`                                   | one DepW    |
| both set                                | `JUNIPER_CASCOR_WORKER_SERVER_URL` val | none        |
| neither set                             | `""` (the `default`)                   | none        |

`""` is a set value. `os.environ.get` returns it, and the helper treats
any non-`None` result as present, so an empty canonical name does not
fall through to the legacy name or to `default`.

The `DeprecationWarning` text is
`"{legacy_name} is deprecated; use {new_name} instead."`.
It is emitted with `stacklevel=2`, so the reported location is the
caller's, not this package's internals.

## Pitfalls

- **The warning is hidden in library code.** Python's default filters
  show `DeprecationWarning` only when it is attributed to `__main__`,
  and ignore it everywhere else. `stacklevel=2` attributes this warning
  to the caller, so a service or library call returns the legacy value
  and prints nothing. A script (`__main__`) does print it. The default
  action is also once per call site. The tests force
  `warnings.simplefilter("always")`. To see the warning from a service,
  run with `python -W default` or set `PYTHONWARNINGS=default`.
- **Both names set is silent.** The canonical value wins, and the
  legacy name is ignored with no warning.
- **One legacy name.** A multi-hop migration is two calls. Do not join
  them with `or` when `""` is a real value: `""` is falsy, so an
  explicit empty canonical name still runs the next call, which can
  return a further legacy value and warn about the wrong pair.
  Chain on `is not None` instead. There is no variadic form.
- **No environment mapping.** The helper reads `os.environ` only.

The operator write-up, including the published-wheel typing gap, is in
[`docs/REFERENCE.md`](../docs/REFERENCE.md#juniper-config-tools).

## Typing

The source is annotated, and the tree ships a PEP 561 marker:
`juniper_config_tools/py.typed` is declared in
`[tool.setuptools.package-data]`, and the classifiers include
`Typing :: Typed`. The marker file has to be package data. There is
no `MANIFEST.in`, so an undeclared `py.typed` never reaches a wheel
(`tests/test_subpackage_py_typed.py`).

The wheel published as `juniper-config-tools==0.1.1` contains
`py.typed` (PyPI file list, checked 2026-11-04) and its classifiers
include `Typing :: Typed`. The `0.1.0` wheel, still on the index, does
not contain `py.typed`. A type checker skips that older package
(`import-untyped`) and `env_with_legacy_alias` is `Any`. A fresh
`pip install` resolves `0.1.1`. An editable install includes the marker
because the file is already in the package directory.

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
The 0.1 public API is a single function: `env_with_legacy_alias`.
Consumers pin with `juniper-config-tools>=0.1.0,<0.2.0` to opt out of
future API growth that may add new functions without breaking changes.

## License

MIT — see [LICENSE](LICENSE).
