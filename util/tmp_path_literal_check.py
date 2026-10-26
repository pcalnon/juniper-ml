#!/usr/bin/env python3
"""Fail when a script, test or config gains a new system temp-directory path literal (gate G-TMP).

Project: juniper-ml
Sub-Project: harness tooling (the 2026-10-26 repo tmp/ rule)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: permanent utility
Related: notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md (gate G-TMP);
         conf/tmp_path_literal_baseline.json; tests/test_tmp_path_literal_check.py

Why this exists
---------------
On the Linux host the system temp directory is a tmpfs that ``systemd-tmpfiles-clean`` ages daily: a
file untouched for ten days is deleted while it is still in use, and a reboot erases the rest. In the
week to 2026-10-26 that emptied a live E2E stack's pid files and venv three times. The owner's rule
(2026-10-26): no file is ever written there; each repo writes its temp files to its own gitignored
``tmp/``. This gate stops a *new* temp-directory literal from landing while the existing ones are
rewritten.

What it checks
--------------
The scope is every tracked file under the directories in ``SCOPE_DIRS`` below (``util/``, ``scripts/``,
``tests/``, ``conf/``, ``.claude/`` and the six sub-package directories) whose name ends in ``.bash``,
``.sh``, ``.py``, ``.yml``, ``.yaml``, ``.toml``, ``.service`` or ``.timer``. ``.github/`` is out of
scope: its workflows run on GitHub's ephemeral runner disk. A symlink is skipped; its target is checked
under its own path. A *literal line* is a line that ``PATTERN`` matches and that does not contain the
pragma ``tmp-path-literal: allow``.

``PATTERN`` matches an absolute path to the temp directory or to anything under it, in its Linux, its
``var/tmp`` and its macOS ``private/tmp`` forms, wherever it starts: a quote, a space, ``=``, ``:-``.
It does not match a ``tmp`` that follows a name, a variable, ``.``, ``~``, ``)`` or ``]`` (a repo's
own ``$REPO/tmp``, ``${ROOT}/tmp``, ``./tmp``, ``~/tmp``, a URL path), nor a longer name such as
``tmpfs``, ``tmp_dir`` or ``tmp-foo``.

``conf/tmp_path_literal_baseline.json`` records, per file, how many literal lines it held when the
gate landed. A file fails when it holds more literal lines than its baseline allows. A file the
baseline does not list allows none. The count is per file, not per line, so line numbers can shift
freely; replacing one literal line with another in the same file passes.

A file that holds fewer literal lines than its baseline allows passes with a NOTE. Lower the
baseline with ``--update-baseline``, so the count cannot climb back.

Usage
-----
    python3 util/tmp_path_literal_check.py [--root DIR] [--baseline FILE] [FILE ...]
    python3 util/tmp_path_literal_check.py [--root DIR] [--baseline FILE] --update-baseline [--dry-run]

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
    Default: ``<root>/conf/tmp_path_literal_baseline.json``.

Output
------
``FAIL  <path>  <n> literal lines; the baseline allows <m>``, followed by each literal line of that
file as ``<path>:<line>: <text>``. ``NOTE  <path>  ...`` marks a count below its baseline. A summary
line follows. On a failure, a ``fix:`` block names the remedies:

- write under the repo's gitignored ``tmp/`` instead;
- end a line that must carry the literal with ``# tmp-path-literal: allow`` (a test fixture, a
  string a script searches for, a legacy path a guard still protects read-only);
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
import re
import subprocess  # nosec B404 -- runs `git ls-files` with a fixed argv
import sys
from pathlib import Path

PATTERN = re.compile(r"(?<![\w.~$})\]/])/(?:var/|private/)?tmp(?![\w-])")
PRAGMA = "tmp-path-literal: allow"
SCOPE_DIRS = ("util", "scripts", "tests", "conf", ".claude", "juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core")
SCOPE_SUFFIXES = (".bash", ".sh", ".py", ".yml", ".yaml", ".toml", ".service", ".timer")
BASELINE_REL = "conf/tmp_path_literal_baseline.json"
SCHEMA = 1
ABOUT = (
    "Gate G-TMP (util/tmp_path_literal_check.py): per file, the number of lines that carry a path literal "
    "under the system temp directory. A file may not exceed its count, and a file not listed may carry none. "
    "Regenerate with: python3 util/tmp_path_literal_check.py --update-baseline"
)
FIX = (
    "fix: write under the repo's gitignored tmp/ (tempfile, mktemp and pytest's tmp_path follow TMPDIR; a fixed path another process must find: bash util/juniper_repo_tmp.bash), per the 2026-10-26 rule.\n"
    "     A line that must carry the literal (a fixture, a string a script searches for) ends with \"# tmp-path-literal: allow\".\n"
    "     A moved file carries its count to its new path: python3 util/tmp_path_literal_check.py --update-baseline"
)


class EnvError(Exception):
    """A usage or environment problem: exit 2."""


def in_scope(rel: str) -> bool:
    parts = rel.split("/")
    return len(parts) > 1 and parts[0] in SCOPE_DIRS and rel.endswith(SCOPE_SUFFIXES)


def literal_lines(data: bytes) -> list[tuple[int, str]]:
    found = []
    for number, raw in enumerate(data.split(b"\n"), 1):
        if b"tmp" not in raw:
            continue
        text = raw.decode("utf-8", "replace")
        if PATTERN.search(text) and PRAGMA not in text:
            found.append((number, text.strip()))
    return found


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
        print(f"tmp_path_literal_check: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
