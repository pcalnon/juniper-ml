#!/usr/bin/env python3
"""
Check that the pre-commit doc-link hook skips the repo's tmp/ and still checks everything else.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — validation of the doc-link hook's `--exclude tmp` (test and test-efficacy evidence)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: .pre-commit-config.yaml (hook `juniper-check-doc-links`); juniper-ml#2360, which carries the same
         hunk with the rest of the 2026-10-26 tmp/ rule; juniper-doc-tools/juniper_doc_tools/check_doc_links.py
         (`_find_markdown_files` skips any path component named in --exclude)

The hook runs `juniper-check-doc-links` with `pass_filenames: false`, so the checker walks the whole
checkout -- the gitignored tmp/ included -- and the scratch copies of notes kept there fail it. On
2026-11-08 the primary checkout failed with 2,424 broken-link lines, every one under tmp/; with
`--exclude tmp` added it passed, 2,365 markdown files and every link valid.

This builds a small tree in a fresh directory under the repo's tmp/ directory and runs the checker there,
with that tree as the working directory (as the hook runs at the repo root), using the hook's own
arguments as read from .pre-commit-config.yaml:

  C0  the hook passes `--exclude tmp`
  C1  a broken link in tmp/notes/ is skipped                               -> exit 0  (the fix works)
  C2  the same tree, run without `--exclude tmp`                            -> exit 1  (the tree reproduces the bug)
  C3  the C1 tree plus a broken link in notes/                              -> exit 1  (everything else is still checked)
  C4  the C1 tree plus a broken link in tmp-archive/, a name that only
      STARTS with tmp                                                      -> exit 1  (only an exact `tmp` component is skipped)

Usage: python3 util/ad-hoc/2026-11-08_doc_links_tmp_exclusion_check.py
Exit: 0 every case behaves as stated; 1 otherwise.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / ".pre-commit-config.yaml"
HOOK_ID = "juniper-check-doc-links"

BASE_TREE = {
    "README.md": "# Fixture\n\n[a note](notes/OK.md)\n",
    "notes/OK.md": "# OK\n",
    # A scratch copy of a note whose link target was not copied with it: the shape that fails in tmp/.
    "tmp/notes/JUNIPER_SCRATCH-COPY.md": "# Scratch copy\n\n[a sibling note](JUNIPER_NOT-COPIED.md)\n",
}
BROKEN_IN_NOTES = {"notes/BROKEN.md": "# Broken\n\n[missing](NOPE.md)\n"}
BROKEN_IN_TMP_PREFIXED_DIR = {"tmp-archive/notes/BROKEN.md": "# Broken\n\n[missing](NOPE.md)\n"}


def hook_args() -> list[str]:
    """Return the args .pre-commit-config.yaml gives the doc-link hook."""
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if hook.get("id") == HOOK_ID:
                return [str(arg) for arg in hook.get("args", [])]
    raise SystemExit(f"no hook with id {HOOK_ID!r} in {CONFIG}")


def without_exclude(args: list[str], name: str) -> list[str]:
    """Return ARGS with the `--exclude NAME` pair removed."""
    out: list[str] = []
    skip_next = False
    for index, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg == "--exclude" and index + 1 < len(args) and args[index + 1] == name:
            skip_next = True
            continue
        out.append(arg)
    return out


def build(root: Path, *extras: dict[str, str]) -> Path:
    """Write the base tree, plus EXTRAS, under ROOT, and return ROOT."""
    for files in (BASE_TREE, *extras):
        for relative, text in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return root


def run(checker: str, args: list[str], root: Path) -> tuple[int, str]:
    proc = subprocess.run([checker, *args], cwd=root, capture_output=True, text=True, timeout=120, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    checker = shutil.which(HOOK_ID)
    if checker is None:
        print(f"{HOOK_ID} is not on PATH (pip install 'juniper-doc-tools>=0.1.1,<0.2.0', as the hook does)")
        return 1
    version = subprocess.run([checker, "--version"], capture_output=True, text=True, check=False).stdout.strip()
    args = hook_args()
    print(f"# doc-link hook tmp/ exclusion check, run {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
    print(f"# checker: {version}")
    print(f"# hook args from {CONFIG.name}: {' '.join(args)}")

    failures = 0

    def report(case: str, ok: bool, detail: str) -> None:
        nonlocal failures
        print(f"[{'PASS' if ok else 'FAIL'}] {case}  ({detail})")
        failures += not ok

    pairs = list(zip(args, args[1:]))
    report("C0 the hook passes --exclude tmp", ("--exclude", "tmp") in pairs, "found" if ("--exclude", "tmp") in pairs else "absent")

    tmp_root = Path(os.environ.get("TMPDIR") or (REPO / "tmp"))
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root, prefix="doc_links_tmp_check_") as work_name:
        work = Path(work_name)

        code, out = run(checker, args, build(work / "c1"))
        report("C1 a broken link in tmp/notes/ is skipped", code == 0, f"exit {code}")

        code, out = run(checker, without_exclude(args, "tmp"), build(work / "c2"))
        named = "tmp/notes/JUNIPER_SCRATCH-COPY.md" in out
        report("C2 without --exclude tmp the same tree fails", code == 1 and named, f"exit {code}, names the scratch copy: {named}")

        code, out = run(checker, args, build(work / "c3", BROKEN_IN_NOTES))
        named = "notes/BROKEN.md" in out
        report("C3 a broken link in notes/ still fails", code == 1 and named, f"exit {code}, names notes/BROKEN.md: {named}")

        code, out = run(checker, args, build(work / "c4", BROKEN_IN_TMP_PREFIXED_DIR))
        named = "tmp-archive/notes/BROKEN.md" in out
        report("C4 a broken link in tmp-archive/ still fails", code == 1 and named, f"exit {code}, names tmp-archive/notes/BROKEN.md: {named}")

    print(f"== {'PASS' if failures == 0 else f'FAIL ({failures})'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
