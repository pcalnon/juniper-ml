#!/usr/bin/env python3
"""
Run another session's Retry-After mutation script on a juniper-data tree without editing it, as a second opinion.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (its own mutant list and its own kill rule, against this carrier's test module)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_mutants.py (this arc's own runner, whose results are the ones reported);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 -B <this> --script <the other mutation script> --repo-root <juniper-data tree> --python <interpreter>
                      --test <test module, repo-relative> --scratch <dir> [--with-middleware]
                      [--pre-fix-allowed-test <test name>]

Why a wrapper. That script's ``data`` target cannot finish as written: two of its wire mutants look for the 429's
headers spelled as string literals (``"Retry-After": str(reset_in),``), which is how the sibling services write
them, and juniper-data writes them with constants (``HEADER_RETRY_AFTER: str(reset_in),``). Its own rule is that a
missing anchor is a script error, so it stops while it builds its list, before any mutant runs. It is not ours to
edit. This wrapper loads it as a module (bytecode writing off, so nothing is written beside it), and in memory only:
  - replaces the anchors of those two mutants with juniper-data's own lines, keeping each mutant's meaning (the
    429's ``Retry-After`` / ``X-RateLimit-Reset`` one second short, never below 1);
  - with --with-middleware, names juniper-data's middleware file for the ``data`` target, so the two middleware
    mutants it otherwise skips are run too (their anchors do occur in juniper-data's middleware);
  - with --pre-fix-allowed-test, names THIS module's test for the one failure the script lets the pre-fix file show
    that is not an assertion. From 2026-11-13 00:49Z the script allows that failure by test name (the test that calls
    the new helper directly and meets an ``AttributeError`` on main), and the name it holds is the sibling services'.
    juniper-data's module has the same test under another name, so without this option the pre-fix case reads
    SURVIVED for the name alone. The exception type the script requires is kept as the script has it.
Then it calls the script's own ``main`` with the given arguments. The mutants, the runner, the kill rule and the
restore are that script's, unchanged. The sha256 of the tree's security.py and middleware.py is taken before and
after and printed; the exit status is 0 only when the script returned 0 and both files are unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SOURCE = "juniper_data/api/security.py"
MIDDLEWARE = "juniper_data/api/middleware.py"
ADAPTED = {
    "W3 retry-after-one-short": ("source", "                    HEADER_RETRY_AFTER: str(reset_in),\n", "                    HEADER_RETRY_AFTER: str(max(1, reset_in - 1)),\n", True),
    "W4 reset-header-one-short": ("source", "                    HEADER_X_RATELIMIT_RESET: str(reset_in),\n", "                    HEADER_X_RATELIMIT_RESET: str(max(1, reset_in - 1)),\n", True),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _call(module, argv: list[str]) -> int | str:
    """The script's ``main``; a ``SystemExit`` it raises (its way of reporting a script error) becomes the status."""
    try:
        return module.main(argv)
    except SystemExit as stop:
        print(f"the script stopped with SystemExit: {stop.code}")
        return stop.code if stop.code is not None else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--with-middleware", action="store_true")
    ap.add_argument("--pre-fix-allowed-test", help="this module's test that calls the new helper directly")
    args = ap.parse_args()
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("second_opinion_script", args.script)
    if spec is None or spec.loader is None:
        print(f"cannot load {args.script}")
        return 2
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    absent = sorted(name for name in ADAPTED if name not in module.WIRE_MUTANTS)
    if absent:
        print(f"the script has no wire mutant named {absent}: it has changed since this wrapper was written")
        return 2
    as_written = {name: list(module.WIRE_MUTANTS[name][:3]) for name in ADAPTED}
    module.WIRE_MUTANTS.update(ADAPTED)
    if args.with_middleware:
        module.TARGETS["data"]["middleware"] = MIDDLEWARE
    allowance = {"as_written": None, "used": None}
    if args.pre_fix_allowed_test:
        held = getattr(module, "PRE_FIX_ALLOWED", None)
        if not (isinstance(held, tuple) and len(held) == 2):
            print("the script has no two-part PRE_FIX_ALLOWED: it has changed since this wrapper was written")
            return 2
        module.PRE_FIX_ALLOWED = (args.pre_fix_allowed_test, held[1])
        allowance = {"as_written": list(held), "used": list(module.PRE_FIX_ALLOWED)}
    watched = {name: args.repo_root / name for name in (SOURCE, MIDDLEWARE)}
    before = {name: _sha(path) for name, path in watched.items()}
    print(json.dumps({"script": str(args.script), "script_sha256": _sha(args.script), "anchors_as_written": as_written, "anchors_used": {name: list(value[:3]) for name, value in ADAPTED.items()}, "middleware_named_for_data": args.with_middleware, "pre_fix_allowed_failure": allowance, "sha256_before": before}, indent=1))
    sys.stdout.flush()
    status = _call(module, ["--target", "data", "--repo-root", str(args.repo_root), "--python", args.python, "--test", args.test, "--scratch", str(args.scratch)])
    after = {name: _sha(path) for name, path in watched.items()}
    print(json.dumps({"script_exit": status, "sha256_after": after, "unchanged": before == after}, indent=1))
    return 0 if status == 0 and before == after else 1


if __name__ == "__main__":
    sys.exit(main())
