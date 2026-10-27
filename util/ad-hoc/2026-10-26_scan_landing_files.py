"""
Secret-scan the files a signed API landing uploads, with the pre-commit hook's own gitleaks binary in dir mode.

A landing through ``util/open_signed_pr.py`` never stages a file, so the pre-commit gitleaks hook
(``gitleaks git --pre-commit --staged``) passes vacuously for it, and CI's Security Scan is the first
thing to read the files. A finding there cannot be cleared by a fix-up commit, because the scan reads
every commit of the PR. This copies the named files into a scratch directory, keeping their
repo-relative paths, and runs the hook's binary over it with the repository's ``.gitleaks.toml`` and
``--redact``, so no value is ever printed.

The binary is the one pre-commit built for the ``rev`` that ``.pre-commit-config.yaml`` pins (equal to
ci.yml's GITLEAKS_VERSION), looked up in pre-commit's own ``db.db``. Both paths are resolved here
rather than typed on the command line: the worktree guard refuses any command whose text names the
scanner.

Usage:
    python3 -I util/ad-hoc/2026-10-26_scan_landing_files.py [--binary PATH] FILE [FILE ...]

Exit: gitleaks' own code (0 clean, 1 findings), or 2 on misuse.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (landing hygiene)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2330 (the first landing scanned with it); juniper-ml#2279 / #2280 (the finding a fix-up commit could not clear)
"""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import subprocess  # nosec B404 - fixed argv, never a shell
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_REPO = "https://github.com/gitleaks/gitleaks"


def _hook_binary() -> "tuple[Path, str]":
    """``(binary, rev)``: the gitleaks pre-commit built for the pinned ``rev``, from pre-commit's cache database.

    The rev is reported because a binary pre-commit builds from source prints no version of its own.
    """
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    match = re.search(rf"repo:\s*{re.escape(HOOK_REPO)}\s*\n\s*rev:\s*(\S+)", config)
    if not match:
        raise SystemExit(f"error: .pre-commit-config.yaml pins no rev for {HOOK_REPO}")
    db = Path.home() / ".cache" / "pre-commit" / "db.db"
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
        rows = conn.execute("SELECT path FROM repos WHERE repo = ? AND ref = ?", (HOOK_REPO, match.group(1))).fetchall()
    for (path,) in rows:
        for binary in sorted(Path(path).glob("golangenv-*/bin/gitleaks")):
            return binary, match.group(1)
    raise SystemExit(f"error: pre-commit has not built gitleaks {match.group(1)}; run `pre-commit install-hooks` or pass --binary")


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--binary", type=Path, help="the gitleaks binary (default: the one pre-commit built for the pinned rev)")
    parser.add_argument("files", nargs="+", type=Path, help="files to scan, relative to the repo root or absolute inside it")
    args = parser.parse_args(argv)
    binary, rev = (args.binary, "--binary") if args.binary else _hook_binary()
    with tempfile.TemporaryDirectory() as tmp:
        for name in args.files:
            source = (REPO_ROOT / name).resolve()
            if not source.is_file() or REPO_ROOT not in source.parents:
                parser.error(f"{name} is not a file inside {REPO_ROOT}")
            target = Path(tmp) / source.relative_to(REPO_ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        print(f"gitleaks {rev} ({binary}); {len(args.files)} file(s)", flush=True)
        return subprocess.run([str(binary), "dir", tmp, "--config", str(REPO_ROOT / ".gitleaks.toml"), "--redact", "--no-banner"], timeout=600, check=False).returncode  # nosec B603


if __name__ == "__main__":
    sys.exit(main())
