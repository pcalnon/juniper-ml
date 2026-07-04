"""``juniper-doc-tools`` -- shared documentation tooling for the Juniper ecosystem.

Single-source-of-truth Python package for the markdown link validator that
historically lived as a standalone ``scripts/check_doc_links.py`` in every
Juniper repo. The 2026-05-18 incident proved that filesystem-based
centralization (symlinks, renames) does not survive single-repo CI checkouts;
this package is the long-term replacement.

The public API is:

- :class:`ValidationResult` -- structured outcome of a validation run.
- :func:`validate_directory` -- ergonomic library entry point.
- :func:`validate_file` -- single-file validator (lower level).

For CLI usage, install the package and run :program:`juniper-check-doc-links`
or ``python -m juniper_doc_tools``; the CLI surface is in :mod:`cli`.

See ``notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md`` in the
juniper-ml repo for the design rationale and migration plan.
"""

from juniper_doc_tools._version import __version__
from juniper_doc_tools.check_doc_links import (
    ValidationResult,
    discover_ecosystem_root,
    validate_directory,
    validate_file,
)

__all__ = [
    "__version__",
    "ValidationResult",
    "discover_ecosystem_root",
    "validate_directory",
    "validate_file",
]
