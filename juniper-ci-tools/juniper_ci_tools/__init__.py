"""``juniper-ci-tools`` -- shared CI / build tooling for the Juniper ecosystem.

Single-source-of-truth Python package for the dependency-documentation
generator that historically lived as a standalone
``scripts/generate_dep_docs.sh`` in every Juniper repo. Three variants drifted
on origin/main; the cascor 2026-05-20 bug fix (sed -> awk for YAML extraction)
shipped to 1 of 8 repos. This package replaces all of them with a single
PyPI-distributed implementation that survives single-repo CI checkouts and
cannot drift.

The public API is:

- :class:`GenerateResult` -- structured outcome of a generation run.
- :func:`generate_dep_docs` -- ergonomic library entry point.

For CLI usage, install the package and run :program:`juniper-generate-dep-docs`
or ``python -m juniper_ci_tools``; the CLI surface is in :mod:`cli`.

See ``notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md`` in the
juniper-ml repo for the design rationale, the incident-class motivation
(mirroring the 2026-05-18 doc-link validator incident), and the wave plan.
"""

from juniper_ci_tools._version import __version__
from juniper_ci_tools.generate_dep_docs import (
    GenerateResult,
    generate_dep_docs,
    render_header,
)

__all__ = [
    "__version__",
    "GenerateResult",
    "generate_dep_docs",
    "render_header",
]
