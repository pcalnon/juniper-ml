#!/usr/bin/env python3
"""
Rewrite the decorative file-header ``Version:`` fields under a tree to one version.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — one-off (W1.13 release train: the juniper-data-client 0.6.0 proposal, juniper-data-client#232)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (W1.13)

Why this exists
---------------
juniper-data-client's ``tests/test_file_header_versions.py`` (APD-DCLIENT-005) requires every
file-header ``Version:`` field under ``juniper_data_client/`` and ``tests/`` to equal
``juniper_data_client.__version__``. The release-train proposal (``util/release_train/propose.py``)
bumps ``pyproject.toml`` and, by file presence, a ``_version.py`` dunder. It moves neither this
package's ``__init__.py`` dunder nor these header copies. So a version bump fails the test until
every header follows.

This mirrors that test exactly: the same regex, over the same first 4096 characters of every
``*.py`` under the given scan roots. It rewrites only the version token of the FIRST match in each
file, which is the one the test reads. Point it at an extracted copy of the branch; it never
touches a git checkout's index or history.

    python3 util/ad-hoc/2026-10-10_bump_file_header_versions.py --root <extracted tree> \\
        --scan juniper_data_client --scan tests --to 0.6.0 [--check]

Exit status: 0 when every header already matched or was rewritten (or, with --check, when none
lag); 1 with --check when any header lags; 2 on a usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Identical to tests/test_file_header_versions.py's _HEADER_VERSION in juniper-data-client.
HEADER_VERSION = re.compile(r"^(?:# )?Version:\s+(\S+)\s*$", re.MULTILINE)
SCAN_CHARS = 4096


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", required=True, type=Path, help="the extracted tree to rewrite")
    parser.add_argument("--scan", action="append", required=True, help="a directory under --root to scan (repeatable)")
    parser.add_argument("--to", required=True, help="the version every header must carry")
    parser.add_argument("--check", action="store_true", help="report lagging headers and change nothing")
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.to):
        print(f"--to must be X.Y.Z, got {args.to!r}", file=sys.stderr)
        return 2

    matched = lagging = 0
    for scan in args.scan:
        base = args.root / scan
        if not base.is_dir():
            print(f"scan root missing: {base}", file=sys.stderr)
            return 2
        for path in sorted(base.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            match = HEADER_VERSION.search(text[:SCAN_CHARS])
            if not match:
                continue
            matched += 1
            if match.group(1) == args.to:
                continue
            lagging += 1
            rel = path.relative_to(args.root)
            print(f"{'LAGS' if args.check else 'bump'} {rel}: {match.group(1)} -> {args.to}")
            if not args.check:
                start, end = match.span(1)
                path.write_text(text[:start] + args.to + text[end:], encoding="utf-8")
    print(f"{matched} header(s) matched; {lagging} {'lag' if args.check else 'rewritten'}")
    return 1 if (args.check and lagging) else 0


if __name__ == "__main__":
    sys.exit(main())
