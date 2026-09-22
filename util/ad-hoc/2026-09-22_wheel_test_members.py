"""
Count the members of a wheel that sit under a ``tests/`` package -- published or local.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md
         item 3 (juniper-data's PyPI wheel ships its test suite)

Why this exists
---------------
``juniper_data-0.14.0-py3-none-any.whl`` carries its own test suite, because
``[tool.setuptools.packages.find] include = ["juniper_data*"]`` also matches
``juniper_data.tests``. A ``.dockerignore`` cannot fix that -- it governs Docker
build contexts, not wheels -- so the check has to open the wheel itself.

It answers the question from the ARTIFACT, never from ``pyproject.toml``: a fixed
``include``/``exclude`` pair proves nothing until a built wheel omits the members.

Usage
-----
    python util/ad-hoc/2026-09-22_wheel_test_members.py --pypi juniper-data
    python util/ad-hoc/2026-09-22_wheel_test_members.py --pypi juniper-data --version 0.14.0
    python util/ad-hoc/2026-09-22_wheel_test_members.py --wheel dist/juniper_data-0.15.0-py3-none-any.whl
    ... --fail-on-tests      # exit 1 when any member sits under a tests/ package
    ... --wheel FIXED.whl --baseline ORIGINAL.whl
                             # prove the fix removed ONLY the test members: every other
                             # member present in both, byte-identical (dist-info RECORD aside)

Exit 0 = measured (and, with ``--fail-on-tests``, no test members; with ``--baseline``,
the difference is exactly the baseline's test members); 1 = test members found under
``--fail-on-tests``, or a ``--baseline`` difference that is anything else; 2 = a wheel
could not be obtained or opened. A wheel that cannot be read is never reported as clean.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
import zipfile


def is_test_member(name: str) -> bool:
    """True when a wheel member sits under a ``tests`` (or ``test``) package directory.

    Matches on a PATH COMPONENT, not a substring, so ``contest/`` or ``tests_util.py``
    at a package root do not count, and a top-level ``tests/`` does.
    """
    parts = name.split("/")[:-1]
    return any(p in ("tests", "test") for p in parts)


def fetch_pypi_wheel(dist: str, version: "str | None") -> "tuple[str, str, bytes]":
    url = f"https://pypi.org/pypi/{dist}/json" if version is None else f"https://pypi.org/pypi/{dist}/{version}/json"
    # Both urlopen calls fetch fixed-scheme https URLs: PyPI's JSON API, then the wheel URL it returns.
    with urllib.request.urlopen(url, timeout=60) as resp:  # nosec B310
        meta = json.load(resp)
    wheels = [u for u in meta["urls"] if u["filename"].endswith(".whl")]
    if not wheels:
        raise RuntimeError(f"{dist} {meta['info']['version']}: no wheel among {[u['filename'] for u in meta['urls']]}")
    if len(wheels) > 1:
        raise RuntimeError(f"{dist} {meta['info']['version']}: {len(wheels)} wheels; pass --wheel with the one you mean")
    w = wheels[0]
    with urllib.request.urlopen(w["url"], timeout=120) as resp:  # nosec B310
        return meta["info"]["version"], w["filename"], resp.read()


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pypi", metavar="DIST", help="distribution name on PyPI")
    src.add_argument("--wheel", metavar="PATH", help="a local .whl file")
    ap.add_argument("--version", help="with --pypi: a specific release (default: the latest)")
    ap.add_argument("--fail-on-tests", action="store_true", help="exit 1 when any member sits under a tests/ package")
    ap.add_argument("--list", action="store_true", help="print every test member, not just the count")
    ap.add_argument("--baseline", metavar="PATH", help="with --wheel: a wheel built WITHOUT the fix; assert the difference is exactly its test members")
    args = ap.parse_args(argv)
    if args.baseline and not args.wheel:
        ap.error("--baseline needs --wheel")

    try:
        if args.pypi:
            version, filename, blob = fetch_pypi_wheel(args.pypi, args.version)
        else:
            with open(args.wheel, "rb") as fh:
                blob = fh.read()
            filename = args.wheel.rsplit("/", 1)[-1]
            version = filename.split("-")[1] if filename.count("-") >= 2 else "?"
        zf = zipfile.ZipFile(io.BytesIO(blob))
        names = zf.namelist()
        base_zf = None
        if args.baseline:
            with open(args.baseline, "rb") as fh:
                base_zf = zipfile.ZipFile(io.BytesIO(fh.read()))
    except Exception as exc:  # noqa: BLE001 -- any failure to obtain the artifact is exit 2, never "clean"
        print(f"ERROR: could not read the wheel: {exc}", file=sys.stderr)
        return 2

    tests = [n for n in names if is_test_member(n)]
    tops = sorted({n.split("/")[0] for n in names})
    print(f"wheel      : {filename}")
    print(f"version    : {version}")
    print(f"members    : {len(names)}")
    print(f"test       : {len(tests)}")
    print(f"top-level  : {', '.join(tops)}")
    if args.list:
        for n in tests:
            print(f"  {n}")
    rc = 0
    if args.fail_on_tests and tests:
        print(f"FAIL: {len(tests)} of {len(names)} members sit under a tests/ package", file=sys.stderr)
        rc = 1
    if base_zf is not None:
        rc = max(rc, compare_to_baseline(zf, base_zf))
    return rc


def compare_to_baseline(fixed: zipfile.ZipFile, base: zipfile.ZipFile) -> int:
    """Return 0 when ``fixed`` is ``base`` minus exactly ``base``'s test members.

    The removal alone is not the claim; the claim is that NOTHING ELSE moved. So every
    member the two share must be byte-identical, apart from dist-info ``RECORD`` -- which
    lists the removed files and so must differ. A baseline with no test members is refused:
    it cannot discriminate a fix from a no-op.
    """
    new, old = set(fixed.namelist()), set(base.namelist())
    removed, added = sorted(old - new), sorted(new - old)
    base_tests = sorted(n for n in old if is_test_member(n))
    compared = sorted(n for n in old & new if not n.endswith(".dist-info/RECORD"))
    changed = [n for n in compared if fixed.read(n) != base.read(n)]
    print(f"baseline   : {len(old)} members, {len(base_tests)} test")
    print(f"removed    : {len(removed)}")
    print(f"added      : {len(added)}")
    print(f"changed    : {len(changed)} (shared members whose bytes differ, RECORD excluded)")
    for label, rows in (("added", added), ("changed", changed), ("removed-but-not-test", sorted(set(removed) - set(base_tests)))):
        for n in rows:
            print(f"  {label}: {n}")
    if not base_tests:
        print("FAIL: the baseline carries no test members, so it cannot discriminate a fix from a no-op", file=sys.stderr)
        return 1
    if removed != base_tests or added or changed:
        print("FAIL: the difference is not exactly the baseline's test members", file=sys.stderr)
        return 1
    print(f"OK: removed exactly the baseline's {len(base_tests)} test members; the other {len(compared)} members are byte-identical (RECORD excluded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
