"""``juniper-config-tools`` -- stdlib-only config helpers for the Juniper ecosystem.

Single-source-of-truth Python package for the env-var alias-with-
deprecation helper that has been independently re-implemented across
juniper-cascor (CFG-03/05), juniper-canopy (CFG-04/16), and is being
added in juniper-cascor-worker (CFG-06).

The public API is intentionally narrow in 0.1.0:

- :func:`env_with_legacy_alias` -- read an env var's canonical name with
  optional legacy-alias fallback that emits a DeprecationWarning.

See ``notes/JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md`` in
the juniper-ml repo for the design rationale, the constraint that
forced the package boundary (juniper-cascor-worker's pydantic-at-runtime
invariant), and the wave plan.
"""

from juniper_config_tools._env_aliases import env_with_legacy_alias
from juniper_config_tools._version import __version__

__all__ = [
    "__version__",
    "env_with_legacy_alias",
]
