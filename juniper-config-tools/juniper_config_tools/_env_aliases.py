"""Env-var alias-with-deprecation resolver.

The single public helper :func:`env_with_legacy_alias` reads an
environment variable's canonical (new) name first, and if that is
unset, falls back to a legacy alias while emitting one
:class:`DeprecationWarning` whose message names both old and new
variables.

Ecosystem context. Every Juniper service that's gone through an env-var
prefix convergence (juniper-cascor CFG-03/05, juniper-canopy CFG-04/16,
juniper-cascor-worker CFG-06) has independently re-implemented this
exact two-step lookup. This module is the shared replacement.

Design properties (kept narrow on purpose for 0.1.0):

- **Stdlib-only.** ``os`` + ``warnings``. No pydantic, no settings
  framework, no validation. The cascor-worker pydantic-at-runtime
  invariant (see juniper-ml#168) makes any heavier dep a no-go for
  the most-constrained consumer.
- **Single legacy alias.** Multi-hop migrations (new → middle → old)
  chain explicit calls: ``env_with_legacy_alias("NEW", "MID") or
  env_with_legacy_alias("MID", "OLD")``. Variadic support is deferred
  to 0.2.0 if a real consumer needs it.
- **Once-per-location warnings.** Uses Python's default warning
  filter (once per file:line), so callers that loop don't spam.
  ``stacklevel=2`` so the warning reports the caller's location,
  not this module's.

See ``notes/JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md``
in the juniper-ml repo for the design discussion that motivated the
package boundary and the API surface choices.
"""

from __future__ import annotations

import os
import warnings


def env_with_legacy_alias(
    new_name: str,
    legacy_name: str | None = None,
    default: str | None = None,
) -> str | None:
    """Read ``new_name`` from the environment; fall back to ``legacy_name``.

    Args:
        new_name: Canonical env-var name. Always checked first.
        legacy_name: Optional legacy env-var name. If ``new_name`` is unset
            and ``legacy_name`` is set, returns its value and emits one
            :class:`DeprecationWarning`. Pass ``None`` to disable the fallback.
        default: Value returned when neither env var is set. ``None`` means
            "absent" (mirrors :func:`os.environ.get`).

    Returns:
        The resolved env-var value, or ``default`` if neither name is set.

    Behaviour matrix:

    +------------------------+----------------------------+-----------------+
    | Environment state      | Returns                    | Warning?        |
    +========================+============================+=================+
    | ``new_name`` set       | ``os.environ[new_name]``   | no              |
    +------------------------+----------------------------+-----------------+
    | only ``legacy_name``   | ``os.environ[legacy_name]``| one             |
    | set                    |                            | DeprecationW.   |
    +------------------------+----------------------------+-----------------+
    | both set               | ``os.environ[new_name]``   | no (legacy      |
    |                        |                            | silently        |
    |                        |                            | ignored)        |
    +------------------------+----------------------------+-----------------+
    | neither set            | ``default``                | no              |
    +------------------------+----------------------------+-----------------+

    Warning text: ``f"{legacy_name} is deprecated; use {new_name} instead."``
    Warning is emitted with ``stacklevel=2`` so the caller's file:line
    is reported.
    """
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
