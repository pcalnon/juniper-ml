#!/usr/bin/env python3
"""Mutation-check the breaking-marker / heading-key / version-prefix fixes: every part must be load-bearing.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release-train verification
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (companion to 2026-09-22_breaking_marker_corpus_diff.py)

Why this exists
---------------
The first ``_is_breaking`` fix shipped with five tests drawn from the instances it was built for,
so they encoded its blind spot. A test that passes proves little until the code it guards is
removed and the test FAILS. Each mutation below reverts one part of the fix; the run prints
KILLED (some test failed -- the part is guarded) or SURVIVED (nothing noticed -- a gap).

Each source file is restored in a ``finally`` and its SHA-256 re-checked at the end, so an
interrupted run cannot leave a mutant behind. Tests run with ``-B`` and
``PYTHONDONTWRITEBYTECODE=1`` so a stale ``.pyc`` cannot mask a mutant, and the verdict comes from
the subprocess return code directly, never through a pipe.

Usage
-----
    python3 util/ad-hoc/2026-09-22_breaking_marker_mutation_check.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_NR = "util/release_train/notes_render.py"
_CE = "util/release_train/ceremony.py"
_TESTS = [
    "tests.test_release_train_ceremony.BreakingFieldTest",
    "tests.test_release_train_ceremony.HeadingKeyTest",
    "tests.test_release_train_ceremony.VersionSectionPrefixTest",
]

#: (name, file, exact original text, mutant text)
_MUTATIONS: list[tuple[str, str, str, str]] = [
    ("M1 label position ignored", _NR, "    if any(_LABEL_RE.match(line.strip()) for line in text.splitlines()):\n        return True\n    return _says_breaking(text, case_sensitive=True)", "    return _says_breaking(text, case_sensitive=True)"),
    ("M2 negation ignored", _NR, "return any(not _NEGATED_RE.search(text[: m.start()]) for m in pattern.finditer(text))", "return any(True for m in pattern.finditer(text))"),
    ("M3 negation without word boundary", _NR, 'r"(?:^|[^A-Za-z])(?:non-|not\\s|no\\s)$"', 'r"(?:non-|not\\s|no\\s)$"'),
    ("M4 heading_key back to first word", _NR, "    return line.strip()[3:].strip()\n", "    return m.group(1)\n"),
    ("M5 heading qualifier not read", _NR, "    if any(_says_breaking(k[len(category_word(k)) :], case_sensitive=False) for k in sections):", "    if False:"),
    ("M6 Breaking category not read", _NR, '    if "removed" in words or "breaking" in words:', '    if "removed" in words:'),
    ("M7 version prefix-match restored", _CE, 'r"(?:\\]|\\s|$)"', 'r"\\]?"'),
    ("M8 security check on raw key", _NR, "return any(category_word(str(k)).lower() == SECURITY_CATEGORY for k in keys)", "return any(str(k).lower() == SECURITY_CATEGORY for k in keys)"),
    ("M9 focus on raw key", _NR, "_FOCUS.get(category_word(k).lower(), category_word(k).lower())", "_FOCUS.get(k.lower(), k.lower())"),
    ("M10 final parser keys by first word", _CE, "        key = notes_render.heading_key(line)", '        key = (lambda hm: hm.group(1) if hm else None)(re.match(r"^###\\s+([A-Za-z]+)", line.strip()))'),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_tests() -> int:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", *_TESTS], cwd=_REPO, env=env, capture_output=True, text=True)
    return proc.returncode


def main() -> int:
    originals = {rel: (_REPO / rel).read_text(encoding="utf-8") for rel in {m[1] for m in _MUTATIONS}}
    hashes = {rel: _sha(_REPO / rel) for rel in originals}

    if _run_tests() != 0:
        print("ERROR: the suite is not green on the unmutated tree -- fix that first")
        return 2

    survived = 0
    try:
        for name, rel, old, new in _MUTATIONS:
            src = originals[rel]
            if src.count(old) != 1:
                print(f"ERROR  {name}: expected exactly one occurrence of the original text in {rel}, found {src.count(old)}")
                return 2
            (_REPO / rel).write_text(src.replace(old, new, 1), encoding="utf-8")
            try:
                rc = _run_tests()
            finally:
                (_REPO / rel).write_text(src, encoding="utf-8")
            verdict = "KILLED" if rc != 0 else "SURVIVED"
            survived += rc == 0
            print(f"{verdict:8} {name}")
    finally:
        for rel, src in originals.items():
            (_REPO / rel).write_text(src, encoding="utf-8")

    for rel, digest in hashes.items():
        if _sha(_REPO / rel) != digest:
            print(f"ERROR: {rel} was not restored byte-for-byte")
            return 2
    print(f"\n{len(_MUTATIONS) - survived}/{len(_MUTATIONS)} mutants killed; sources restored and hash-verified.")
    return 1 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
