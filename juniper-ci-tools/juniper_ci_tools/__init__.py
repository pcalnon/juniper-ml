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
- :class:`LintResult` / :class:`LintFinding` -- structured outcome of the
  workflow-script-path lint added in 0.2.0.
- :func:`lint_workflow_paths` -- ergonomic library entry point for the lint.
- :class:`AgentsMdLintResult` -- structured outcome of the AGENTS.md
  ``**Version**:`` drift lint added in 0.3.0.
- :func:`lint_agents_md_version` -- ergonomic library entry point for the
  AGENTS.md drift lint.

For CLI usage, install the package and run :program:`juniper-generate-dep-docs`
(dep-docs generator), :program:`juniper-lint-workflow-paths` (workflow-script-
path lint), :program:`juniper-lint-agents-md-version` (AGENTS.md version
drift lint), or ``python -m juniper_ci_tools`` (dep-docs generator). The CLI
surfaces are in :mod:`cli`, :mod:`cli_lint_workflow_paths`, and
:mod:`cli_lint_agents_md_version`.

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
from juniper_ci_tools.lint_agents_md_version import (
    AgentsMdLintResult,
    MultipleVersionHeadersError,
    RepoRootNotFoundError,
    find_agents_md_repo_root,
    lint_agents_md_version,
)
from juniper_ci_tools.lint_workflow_paths import (
    DEFAULT_ECOSYSTEM_SIBLING_PREFIXES,
    LintFinding,
    LintResult,
    extract_script_paths,
    find_repo_root,
    is_validatable,
    lint_workflow_paths,
)

__all__ = [
    "__version__",
    "GenerateResult",
    "generate_dep_docs",
    "render_header",
    "DEFAULT_ECOSYSTEM_SIBLING_PREFIXES",
    "LintFinding",
    "LintResult",
    "extract_script_paths",
    "find_repo_root",
    "is_validatable",
    "lint_workflow_paths",
    "AgentsMdLintResult",
    "MultipleVersionHeadersError",
    "RepoRootNotFoundError",
    "find_agents_md_repo_root",
    "lint_agents_md_version",
]
