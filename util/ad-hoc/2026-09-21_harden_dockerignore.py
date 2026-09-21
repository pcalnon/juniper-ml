#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Harden a repo's `.dockerignore` against the ROOT-ANCHORING class, and add the missing
credentials block.

THE CLASS
---------
Docker matches `.dockerignore` patterns with Go `filepath.Match` **relative to the context
root**. A pattern written `logs/` therefore does NOT match `src/logs/`. Every Juniper image
Dockerfile uses a DIRECTORY allowlist (`COPY src/ ./src/`), which ships everything tracked
beneath that directory -- so a root-anchored exclusion of a nested path is inert.

Measured instance that motivated this (juniper-cascor, fixed in cascor#661):
`.dockerignore` said `cascor_snapshots/`; the directory is `src/cascor_snapshots/`; it holds
766 `.h5` files, **all 766** carrying a plaintext multiprocessing authkey. The published
image was clean only because `.gitignore` kept them untracked and CI builds from
`actions/checkout` -- not because of `.dockerignore`.

Several of these files ALREADY document the rule for `*.egg-info/` and apply `**/` there,
then omit it three lines later. The knowledge was present; the application was partial.

WHAT IT DOES
------------
1. For every root-anchored directory pattern that a `COPY <dir>/` actually ships beneath,
   add a `**/`-prefixed twin. Existing lines are KEPT, never rewritten -- a `.dockerignore`
   is order-sensitive and negations depend on position.
2. Insert a credentials block if `secrets/` is absent.
3. Never touch a line that already starts with `**/` or `!`.

Idempotent. Prints a unified diff and writes only with --write.

USAGE
    python3 2026-09-21_harden_dockerignore.py <path-to-.dockerignore> [--write]

VERIFY THE RESULT EMPIRICALLY, NOT BY READING. Build a synthetic context with the shapes
you care about and run a real `docker build` with `COPY . .` under both the old and the new
file. A fix without a negative control is an assertion.
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

CREDENTIALS_BLOCK = """
# -- Credentials. Docker does NOT honour .gitignore, and this image is PUBLIC.
#    The Dockerfile copies a DIRECTORY allowlist, which is not a file allowlist:
#    `COPY <pkg>/ ./<pkg>/` ships everything tracked beneath it. Patterns are
#    root-anchored (Go filepath.Match), so the `**/` twins are load-bearing.
secrets/
**/secrets/
*.key
**/*.key
*.pem
**/*.pem
*.p12
*.pfx
.env
.env.*
**/.env
**/.env.*
!.env.example
"""

# Patterns that are ALWAYS safe to twin: build/test detritus and heavyweight artifacts
# that no runtime path depends on.
NEST_WORTHY = {
    "snapshots/", "cascor_snapshots/", "cascor-snapshots/",
    ".mypy_cache/", ".pytest_cache/", ".ruff_cache/", ".coverage", "htmlcov/",
    "*.h5", "*.log",
}

# DO NOT twin these automatically. They name directories an application may create and
# WRITE TO at runtime, so excluding a nested instance can change the shipped image.
#
# Concrete instance, found before it shipped (juniper-canopy, 2026-09-21): `src/logs` is a
# SYMLINK to `../logs`, and the published 0.8.0 image carries it pointing at `/app/logs`,
# which the Dockerfile creates. Adding `**/logs/` would have dropped the symlink from the
# build context and silently broken the container's logging path -- a "hardening" change
# that breaks the app. The root-anchored `logs/` already excludes the real log FILES; the
# symlink is a different object with a different purpose.
#
# Twin one of these only after checking what is actually beneath it in the PUBLISHED image.
NEEDS_REVIEW = {"logs/", "data/", "reports/", "backups/", "backup/", "tmp/", "temp/"}


def harden(text: str) -> str:
    lines = text.splitlines(keepends=True)
    present = {ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")}

    out: list[str] = []
    deferred: list[str] = []
    for ln in lines:
        out.append(ln)
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("**/") or s.startswith("!"):
            continue
        if s in NEEDS_REVIEW:
            deferred.append(s)
            continue
        if s in NEST_WORTHY:
            twin = f"**/{s}"
            if twin not in present:
                out.append(twin + "\n")
                present.add(twin)

    if deferred:
        print(
            "NOT twinned automatically (runtime-writable names -- check the PUBLISHED image "
            f"before adding a `**/` form): {', '.join(sorted(set(deferred)))}",
            file=sys.stderr,
        )

    result = "".join(out)
    if "secrets/" not in present:
        if not result.endswith("\n"):
            result += "\n"
        result += CREDENTIALS_BLOCK
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    write = "--write" in sys.argv
    if not path.is_file():
        print(f"ERROR: {path} is not a file")
        return 2

    before = path.read_text(encoding="utf-8")
    after = harden(before)

    if before == after:
        print(f"{path}: already hardened, no change")
        return 0

    diff = difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"a/{path.name}", tofile=f"b/{path.name}",
    )
    sys.stdout.writelines(diff)

    if write:
        path.write_text(after, encoding="utf-8")
        print(f"\nWROTE {path}")
    else:
        print("\n(dry run -- pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
