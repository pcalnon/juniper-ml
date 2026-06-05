"""Drift-guard for the juniper-cascor-core candidate-core extraction (CW-05 plan §5/§7).

``juniper-cascor-core`` is extracted verbatim from ``juniper-cascor/src`` and consumed by
``juniper-cascor-worker``, while ``juniper-cascor`` itself keeps its inline copies until it
adopts the package (plan Wave 2, deferred). The only correctness risk of that deferral is
**drift** between the worker's package copy and the cascor server's src copy. This test
fails if any extracted candidate-core module diverges from its ``juniper-cascor/src``
counterpart, so divergence is a conscious choice (re-extract, or extend the allowlist).

Four files intentionally diverge -- the deployment-agnostic logging fix (CW-05 gap #3)
and the worker activation tuple compatibility fix -- and are allowlisted in
``_INTENTIONAL_DIVERGENCE``; they are to be backported to cascor in Wave 2.

Skips when the sibling ``juniper-cascor`` repo is not on disk (per-PR / isolated CI),
mirroring ``test_doc_tools_drift.py``. Set ``JUNIPER_ECOSYSTEM_ROOT`` to point at the
directory holding the ``juniper-cascor`` checkout (useful from a worktree).
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

# The candidate-core module trees extracted into juniper-cascor-core/ (top-level names,
# CW-05 plan §3.1 option (i)).
_EXTRACTED_DIRS = ("candidate_unit", "utils", "log_config", "cascor_constants")

# Files intentionally modified in the package vs cascor src. NOT byte-checked; to be
# backported to cascor in Wave 2.
_INTENTIONAL_DIVERGENCE = frozenset(
    {
        Path("log_config/logger/logger.py"),
        Path("cascor_constants/constants.py"),
        Path("candidate_unit/candidate_unit.py"),
        Path("utils/activation.py"),
    }
)

_SIBLING_REPOS = ("juniper-cascor", "juniper-data", "juniper-canopy", "juniper-cascor-worker")


def _find_ecosystem_root(juniper_ml_root: Path) -> Path | None:
    """Locate the directory that holds the juniper-X sibling checkouts.

    Honors ``JUNIPER_ECOSYSTEM_ROOT`` first (needed from a ``.claude/worktrees`` worktree,
    where the parent-dir heuristic does not reach the ecosystem root), then falls back to
    the same parent / grandparent heuristic as ``test_doc_tools_drift.py``.
    """
    override = os.environ.get("JUNIPER_ECOSYSTEM_ROOT")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates += [juniper_ml_root.parent, juniper_ml_root.parent.parent]
    for candidate in candidates:
        try:
            present = sum(1 for s in _SIBLING_REPOS if (candidate / s).is_dir())
        except OSError:
            continue
        if present >= 3 or (override and (candidate / "juniper-cascor" / "src").is_dir()):
            return candidate
    return None


class JuniperCascorCoreDriftTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.core_root = cls.juniper_ml_root / "juniper-cascor-core"
        eco = _find_ecosystem_root(cls.juniper_ml_root)
        cls.cascor_src = (eco / "juniper-cascor" / "src") if eco else None

    def test_core_package_present(self):
        self.assertTrue(self.core_root.is_dir(), f"juniper-cascor-core not found at {self.core_root}")

    def test_extracted_modules_match_cascor_src(self):
        if not self.core_root.is_dir():
            self.skipTest("juniper-cascor-core not present")
        if self.cascor_src is None or not self.cascor_src.is_dir():
            self.skipTest("sibling juniper-cascor/src not on disk -- drift check skipped (per-PR / isolated CI)")

        missing: list[str] = []
        mismatches: list[str] = []
        checked = 0
        for d in _EXTRACTED_DIRS:
            for pkg_file in sorted((self.core_root / d).rglob("*.py")):
                rel = pkg_file.relative_to(self.core_root)
                src_file = self.cascor_src / rel
                if rel in _INTENTIONAL_DIVERGENCE:
                    if not src_file.is_file():
                        missing.append(f"{rel} (allowlisted, but missing upstream)")
                    continue
                if not src_file.is_file():
                    missing.append(str(rel))
                    continue
                checked += 1
                if pkg_file.read_bytes() != src_file.read_bytes():
                    mismatches.append(str(rel))

        problems: list[str] = []
        if missing:
            problems.append("missing upstream counterpart: " + ", ".join(missing))
        if mismatches:
            problems.append("DRIFT -- these juniper-cascor-core files differ from juniper-cascor/src " "(re-extract them, or add to _INTENTIONAL_DIVERGENCE if the change is deliberate): " + ", ".join(mismatches))
        self.assertEqual([], problems, "\n".join(problems))
        self.assertGreater(checked, 0, "no files were drift-checked -- extraction set may be empty")

    def test_intentional_divergences_actually_differ(self):
        """Sanity: allowlisted files SHOULD differ from cascor src; else the allowlist is stale."""
        if not self.core_root.is_dir() or self.cascor_src is None or not self.cascor_src.is_dir():
            self.skipTest("core or sibling cascor src not present")
        for rel in _INTENTIONAL_DIVERGENCE:
            pkg_file = self.core_root / rel
            src_file = self.cascor_src / rel
            if pkg_file.is_file() and src_file.is_file():
                self.assertNotEqual(
                    pkg_file.read_bytes(),
                    src_file.read_bytes(),
                    f"{rel} is allowlisted as intentionally-diverged but is byte-identical to " "cascor src -- remove it from _INTENTIONAL_DIVERGENCE.",
                )


if __name__ == "__main__":
    unittest.main()
