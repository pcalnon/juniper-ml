#!/usr/bin/env python3
"""Fail when a script or workflow gains a new hard-coded Linux home path (task G5, gate G-PATH).

Project: juniper-ml
Sub-Project: host tooling (turing bring-up)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: permanent utility
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G5, gate G-PATH,
         decision D12); conf/home_path_literal_baseline.json; tests/test_home_path_literal_check.py

Why this exists
---------------
Scripts written on the Linux hosts hard-code the owner's home directory there: ``/home/`` followed by
the owner's user name, held in ``NEEDLE`` below. On turing the home directory is under ``/Users``, so
each such literal is a path that does not exist. Decision D12 rewrites executable literals to paths
derived from ``$HOME``, and docs to ``~/``. This gate stops a *new* literal from landing while the
existing ones are rewritten.

What it checks
--------------
The scope is every tracked file under ``util/``, ``scripts/`` and ``.github/`` whose name ends in
``.bash``, ``.sh``, ``.py`` or ``.yml``. A symlink is skipped; its target is checked under its own
path. A *literal line* is a line that contains ``NEEDLE`` and does not contain the pragma
``home-path-literal: allow``.

``conf/home_path_literal_baseline.json`` records, per file, how many literal lines it held when the
gate landed. A file fails when it holds more literal lines than its baseline allows. A file the
baseline does not list allows none. The count is per file, not per line, so line numbers can shift
freely; replacing one literal line with another in the same file passes.

A file that holds fewer literal lines than its baseline allows passes with a NOTE. Lower the
baseline with ``--update-baseline``, so the count cannot climb back.

Usage
-----
    python3 util/home_path_literal_check.py [--root DIR] [--baseline FILE] [FILE ...]
    python3 util/home_path_literal_check.py [--root DIR] [--baseline FILE] --update-baseline [--dry-run]

``FILE ...``
    Check only these files. This is the pre-commit hook's form. A path outside the scope is
    ignored, and so is one that no longer exists. If the baseline file itself is named, the whole
    scope is checked, so a baseline edit is checked against the tree it describes.
(no FILE)
    Check the whole scope. This is the CI step's form.
``--update-baseline``
    Recount the whole scope and write the baseline. The file is rewritten only when its content
    changes, so a second run leaves it untouched.
``--dry-run``
    With ``--update-baseline``: print the changes and write nothing.
``--root DIR``
    The repository root. Default: the checkout this script lives in.
``--baseline FILE``
    Default: ``<root>/conf/home_path_literal_baseline.json``.

Output
------
``FAIL  <path>  <n> literal lines; the baseline allows <m>``, followed by each literal line of that
file as ``<path>:<line>: <text>``. ``NOTE  <path>  ...`` marks a count below its baseline. A summary
line follows. On a failure, a ``fix:`` block names the remedies:

- derive the path from ``$HOME``;
- end a line that must carry the literal with ``# home-path-literal: allow`` (the needle in this
  file, a test fixture, a string a script searches for);
- re-baseline a moved file, which carries its count to its new path.

Exit codes
----------
0  no file is over its baseline, or ``--update-baseline`` finished.
1  at least one file is over its baseline; every such file is listed.
2  usage or environment: a bad argument, a root that is not a git checkout (whole-scope modes), or
   a baseline that is missing, unreadable or malformed. The message goes to stderr.

Environment
-----------
``GIT``  the git program (default ``git``).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 -- runs `git ls-files` with a fixed argv
import sys
from pathlib import Path

NEEDLE = "/home/pcalnon"  # home-path-literal: allow -- the needle itself
PRAGMA = "home-path-literal: allow"
SCOPE_DIRS = ("util", "scripts", ".github")
SCOPE_SUFFIXES = (".bash", ".sh", ".py", ".yml")
BASELINE_REL = "conf/home_path_literal_baseline.json"
SCHEMA = 1
ABOUT = (
    "Task G5, gate G-PATH (util/home_path_literal_check.py): per file, the number of lines that carry the "
    "Linux home-path literal. A file may not exceed its count, and a file not listed may carry none. "
    "Regenerate with: python3 util/home_path_literal_check.py --update-baseline"
)
FIX = (
    "fix: derive the path from $HOME (bash \"$HOME/...\", Python Path.home()), per decision D12.\n"
    "     A line that must carry the literal (a needle, a fixture) ends with \"# home-path-literal: allow\".\n"
    "     A moved file carries its count to its new path: python3 util/home_path_literal_check.py --update-baseline"
)


class EnvError(Exception):
    """A usage or environment problem: exit 2."""


def in_scope(rel: str) -> bool:
    parts = rel.split("/")
    return len(parts) > 1 and parts[0] in SCOPE_DIRS and rel.endswith(SCOPE_SUFFIXES)


def literal_lines(data: bytes) -> list[tuple[int, str]]:
    needle, pragma = NEEDLE.encode(), PRAGMA.encode()
    return [(number, raw.decode("utf-8", "replace").strip()) for number, raw in enumerate(data.split(b"\n"), 1) if needle in raw and pragma not in raw]


def tracked(root: Path) -> list[str]:
    git = os.environ.get("GIT", "git")
    try:
        proc = subprocess.run([git, "-C", str(root), "ls-files", "-z", "--", *SCOPE_DIRS], capture_output=True, check=False)  # nosec B603
    except OSError as exc:
        raise EnvError(f"cannot run {git}: {exc}") from exc
    if proc.returncode != 0:
        raise EnvError(f"git ls-files failed in {root}: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return sorted(rel for rel in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if rel and in_scope(rel))


def readable(root: Path, rels: list[str]) -> list[str]:
    """The paths that are regular files, not symlinks; a deleted file or a symlink holds nothing to count."""
    return [rel for rel in rels if not (root / rel).is_symlink() and (root / rel).is_file()]


def scan(root: Path, rels: list[str]) -> dict[str, list[tuple[int, str]]]:
    found = {}
    for rel in rels:
        hits = literal_lines((root / rel).read_bytes())
        if hits:
            found[rel] = hits
    return found


def relative(arg: str, root: Path) -> str | None:
    """``arg`` relative to ``root`` in POSIX form, or None outside it. Directory symlinks are resolved; the file's own name is not."""
    path = os.path.abspath(arg)
    real = os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))
    rel = os.path.relpath(real, os.path.realpath(root))
    if rel == os.curdir or rel.startswith(os.pardir + os.sep) or rel == os.pardir:
        return None
    return Path(rel).as_posix()


def load_baseline(path: Path) -> dict[str, int]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise EnvError(f"baseline {path} not found; create it with --update-baseline") from None
    except (OSError, ValueError) as exc:
        raise EnvError(f"baseline {path} is unreadable: {exc}") from exc
    files = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not isinstance(files, dict) or not all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in files.values()):
        raise EnvError(f'baseline {path} is malformed: want {{"schema": {SCHEMA}, "files": {{"<path>": <positive int>, ...}}}}')
    return files


def render_baseline(counts: dict[str, int]) -> str:
    return json.dumps({"schema": SCHEMA, "about": ABOUT, "files": dict(sorted(counts.items()))}, indent=2) + "\n"


def update_baseline(root: Path, baseline: Path, dry_run: bool) -> int:
    counts = {rel: len(hits) for rel, hits in scan(root, readable(root, tracked(root))).items()}
    try:
        old = load_baseline(baseline)
    except EnvError:
        old = {}
    changes = [(rel, old.get(rel, 0), counts.get(rel, 0)) for rel in sorted(set(old) | set(counts)) if old.get(rel, 0) != counts.get(rel, 0)]
    for rel, was, now in changes:
        print(f"{'DRY-RUN ' if dry_run else ''}{rel}: {was} -> {now}")
    text = render_baseline(counts)
    current = baseline.read_text(encoding="utf-8") if baseline.is_file() else None
    verdict = f"{len(counts)} files, {sum(counts.values())} literal lines, {len(changes)} entries changed"
    if text == current:
        print(f"baseline: {baseline} is current ({verdict})")
    elif dry_run:
        print(f"DRY-RUN: would write {baseline} ({verdict})")
    else:
        # A sibling temp file then a rename: a reader never sees half a file, and the new file takes the
        # process umask like any other file written into the checkout.
        baseline.parent.mkdir(parents=True, exist_ok=True)
        tmp = baseline.with_name(baseline.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, baseline)
        print(f"baseline: wrote {baseline} ({verdict})")
    return 0


def check(root: Path, baseline: Path, files: list[str]) -> int:
    allowed = load_baseline(baseline)
    named = {rel for rel in (relative(arg, root) for arg in files) if rel is not None}
    whole = not files or relative(str(baseline), root) in named
    rels = readable(root, tracked(root) if whole else sorted(rel for rel in named if in_scope(rel)))
    found = scan(root, rels)
    over = [(rel, hits) for rel, hits in sorted(found.items()) if len(hits) > allowed.get(rel, 0)]
    pool = allowed if whole else {rel: allowed[rel] for rel in rels if rel in allowed}
    under = [(rel, len(found.get(rel, ())), n) for rel, n in sorted(pool.items()) if len(found.get(rel, ())) < n]
    for rel, hits in over:
        print(f"FAIL  {rel}  {len(hits)} literal lines; the baseline allows {allowed.get(rel, 0)}")
        for number, text in hits:
            print(f"        {rel}:{number}: {text[:200]}")
    for rel, count, n in under:
        print(f"NOTE  {rel}  {count} literal lines; the baseline allows {n} -- lower it with --update-baseline")
    lines = sum(len(hits) for hits in found.values())
    scope = "the whole scope" if whole else "the named files"
    if over:
        print(f"summary: FAIL -- {len(over)} of {len(rels)} files over their baseline ({scope}; {lines} literal lines)")
        print(FIX)
        return 1
    print(f"summary: PASS -- no file over its baseline ({scope}: {len(rels)} files, {lines} literal lines)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", metavar="FILE", help="check only these files (the pre-commit form)")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="repository root")
    parser.add_argument("--baseline", type=Path, help=f"default: <root>/{BASELINE_REL}")
    parser.add_argument("--update-baseline", action="store_true", help="recount the whole scope and write the baseline")
    parser.add_argument("--dry-run", action="store_true", help="with --update-baseline: write nothing")
    args = parser.parse_args(argv)
    if args.dry_run and not args.update_baseline:
        parser.error("--dry-run only applies to --update-baseline")
    if args.update_baseline and args.files:
        parser.error("--update-baseline always recounts the whole scope; drop the FILE arguments")
    root = args.root
    baseline = args.baseline if args.baseline is not None else root / BASELINE_REL
    try:
        if not root.is_dir():
            raise EnvError(f"root {root} is not a directory")
        if args.update_baseline:
            return update_baseline(root, baseline, args.dry_run)
        return check(root, baseline, args.files)
    except EnvError as exc:
        print(f"home_path_literal_check: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
