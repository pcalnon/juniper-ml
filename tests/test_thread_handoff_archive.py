"""Drift tests for archived thread-handoff prompt filenames and references.

The handoff archive is documentation, but stale or non-canonical names make
future handoff prompts hard to locate and easy to reference incorrectly.

Handoffs are filed by month, one level below the archive root:
``HANDOFF_YYYY-MM/HANDOFF_YYYY-MM-DD_subject.md``. Any not yet filed sit at the
root. Every check below therefore walks the whole archive -- a top-level glob
would silently stop examining every handoff that has been filed.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_HANDOFF_DIR = _REPO_ROOT / "prompts" / "thread-handoff_automated-prompts"
_CANONICAL_NAME = re.compile(r"^HANDOFF_\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_CANONICAL_REFERENCE = re.compile(r"\b(HANDOFF_\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9._-]*\.md)\b")
_MONTH_DIR = re.compile(r"^HANDOFF_(\d{4}-\d{2})$")


def _archived_handoffs() -> list[Path]:
    return sorted(_HANDOFF_DIR.rglob("*.md"))


class ThreadHandoffArchiveTest(unittest.TestCase):
    def test_archived_thread_handoff_filenames_are_canonical(self):
        names = sorted(path.name for path in _archived_handoffs())
        self.assertGreater(names, [], "thread-handoff archive should contain prompt files")

        bad_names = []
        for name in names:
            try:
                name.encode("ascii")
            except UnicodeEncodeError:
                bad_names.append(name)
                continue
            if not _CANONICAL_NAME.fullmatch(name):
                bad_names.append(name)

        self.assertEqual(
            bad_names,
            [],
            "Archive filenames must follow HANDOFF_YYYY-MM-DD_subject.md with ASCII subject text",
        )

    def test_filed_handoffs_sit_in_their_own_month_directory(self):
        misplaced = []
        for path in _archived_handoffs():
            parts = path.relative_to(_HANDOFF_DIR).parts
            if len(parts) == 1:
                continue
            month = _MONTH_DIR.fullmatch(parts[0])
            if len(parts) != 2 or month is None or not path.name.startswith(f"HANDOFF_{month.group(1)}-"):
                misplaced.append("/".join(parts))

        self.assertEqual(
            misplaced,
            [],
            "A filed handoff must sit directly in the HANDOFF_YYYY-MM/ directory for its own month",
        )

    def test_archived_thread_handoff_names_are_unique(self):
        # References name a handoff by its filename alone, so one name filed twice
        # (say, at the root and in its month directory) would be ambiguous.
        seen: dict[str, list[str]] = {}
        for path in _archived_handoffs():
            seen.setdefault(path.name, []).append(path.relative_to(_HANDOFF_DIR).as_posix())

        duplicates = {name: paths for name, paths in seen.items() if len(paths) > 1}
        self.assertEqual(duplicates, {}, "Each archived handoff filename must appear exactly once in the archive")

    def test_top_level_note_references_to_thread_handoffs_resolve(self):
        archived = {path.name for path in _archived_handoffs()}
        references = {}
        for path in sorted((_REPO_ROOT / "notes").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in _CANONICAL_REFERENCE.finditer(text):
                references.setdefault(match.group(1), []).append(path.relative_to(_REPO_ROOT).as_posix())

        self.assertTrue(references, "expected at least one top-level note to reference an archived handoff")

        missing = {name: sources for name, sources in sorted(references.items()) if name not in archived}

        self.assertEqual(missing, {}, "top-level note handoff references must resolve to archived prompt files")


if __name__ == "__main__":
    unittest.main()
