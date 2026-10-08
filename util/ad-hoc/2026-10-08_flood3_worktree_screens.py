#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. The flood-3 evaluators may not commit, so the Sequence Safety screens
# (which compare two COMMITS) cannot be run on prepared, uncommitted changes. This drives the
# same juniper-ci-tools library classifiers (juniper-ml's juniper-ci-tools/ source, identical to
# the published 0.9.0 for these modules) over BASE-ref blobs vs WORKING-TREE files instead.
# It does not evaluate trailer waivers (there are no commits) or cross-file relocation.
"""Usage: 2026-10-08_flood3_worktree_screens.py <repo> <base-ref> [--scope GLOB ...] -- <path> [<path> ...]

.md paths go to the docs deletion-magnitude classifier; .py / .bash paths to the symbol-loss
classifier (the caller passes only paths inside the repo's --scope). Exit 1 on any FAIL.
"""
import subprocess
import sys
from pathlib import Path

_CI_TOOLS = Path(__file__).resolve().parents[2] / "juniper-ci-tools"
sys.path.insert(0, str(_CI_TOOLS))

from juniper_ci_tools import docs_additions_check as docs  # noqa: E402
from juniper_ci_tools import symbol_loss_check as sym  # noqa: E402


def _base_text(repo: str, ref: str, path: str) -> "str | None":
    proc = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"], capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def main(argv: list[str]) -> int:
    if "--" not in argv or len(argv) < 4:
        print(__doc__)
        return 2
    split = argv.index("--")
    repo, ref = argv[1], argv[2]
    paths = argv[split + 1:]
    fails = 0
    for path in paths:
        if path.endswith(".md"):
            diff = subprocess.run(["git", "-C", repo, "diff", "--unified=0", "--no-color", ref, "--", path], capture_output=True, text=True).stdout
            findings = docs.classify_file(path, docs.parse_hunks(diff), docs.DEFAULT_MIN_RUN)
            for f in findings:
                print(f"docs   {f.severity:5s} {path}: {f.reason} {f.detail}")
                fails += f.severity == "FAIL"
            if not findings:
                print(f"docs   CLEAN {path}")
        elif path.endswith(".py") or path.endswith(".bash"):
            base_src = _base_text(repo, ref, path)
            head_src = (Path(repo) / path).read_text(encoding="utf-8")
            base_inv = sym.symbols_for(path, base_src)[0] if base_src is not None else {}
            head_inv, ok = sym.symbols_for(path, head_src)
            findings = sym.classify_file(path, base_inv or {}, head_inv or {}, path.endswith(".bash"))
            for f in findings:
                print(f"symbol {f.severity:5s} {path}: {f.verdict} {f.symbol} {f.detail}")
                fails += f.severity == "FAIL"
            if not findings:
                print(f"symbol CLEAN {path} ({'new file' if base_src is None else 'modified'}, {len(head_inv or {})} symbols, parse_ok={ok})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
