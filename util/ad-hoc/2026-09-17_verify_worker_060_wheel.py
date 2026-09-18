#!/usr/bin/env python3
"""Verify juniper-cascor-worker 0.6.0 AS PUBLISHED against the claim made for it.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release verification
Author:      Paul Calnon
Created:     2026-09-17
Version:     0.1.0
License:     MIT License
Status:      single-use (container-registry arc, worker 0.6.0 post-publish check)

Why this exists
---------------
The worker's v0.6.0 Release was cut **for the image**, not for a code change, and the
container-registry plan records a precise, falsifiable claim about the wheel it also
produced:

    "the 0.6.0 wheel is byte-identical to 0.5.0's apart from the version string:
     43 commits and 23 files across v0.5.0...main with ZERO in juniper_cascor_worker/
     or pyproject.toml"

That claim was made from a **git diff of the checkout**. A checkout is not a deployment --
juniper-model-core 0.3.1 shipped a stale docstring under an unchanged version while the repo
was already correct -- so the claim is worth re-testing against the artifact PyPI actually
serves. If it holds, `util/release_train/detect.py` classifying the package UP_TO_DATE is
confirmed correct by the shipped bytes rather than by the diff that predicted it.

What it checks, and why each half matters
-----------------------------------------
1. Every member of BOTH wheels is hashed and compared by name. A name-only comparison
   would pass on two wheels that share a file list and differ in content -- which is the
   whole failure mode here.
2. Members are partitioned into PACKAGE (juniper_cascor_worker/**) and METADATA
   (*.dist-info/**). The claim is specifically that the PACKAGE half is unchanged; the
   metadata half MUST differ, because it carries the version. A run where the metadata is
   also identical would mean the two downloads are the same file, so that is failed too.
3. RECORD is excluded from the metadata comparison only for reporting -- it is a manifest
   of hashes and necessarily differs whenever anything else does.

Usage:
    python3 util/ad-hoc/2026-09-17_verify_worker_060_wheel.py
    python3 util/ad-hoc/2026-09-17_verify_worker_060_wheel.py --old 0.5.0 --new 0.6.0

Exit status:
    0  the claim holds -- package payload identical, metadata differs
    1  the claim does NOT hold (a package file changed, or the wheels are indistinguishable)
    2  could not fetch or read a wheel
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile

PKG = "juniper-cascor-worker"
IMPORT_NAME = "juniper_cascor_worker"


def wheel_url(version: str) -> str:
    url = f"https://pypi.org/pypi/{PKG}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 - fixed https host
            data = json.load(resp)
    except (urllib.error.URLError, ValueError) as exc:
        print(f"could not read the PyPI record for {PKG} {version}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None

    wheels = [u for u in data["urls"] if u["packagetype"] == "bdist_wheel"]
    if not wheels:
        print(f"{PKG} {version} publishes no wheel", file=sys.stderr)
        raise SystemExit(2)
    if len(wheels) > 1:
        print(f"note: {version} has {len(wheels)} wheels; using {wheels[0]['filename']}")
    return wheels[0]["url"]


def members(version: str) -> tuple[str, dict[str, str]]:
    url = wheel_url(version)
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 - PyPI CDN
            blob = resp.read()
    except urllib.error.URLError as exc:
        print(f"could not download {url}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None

    out: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            out[info.filename] = hashlib.sha256(zf.read(info)).hexdigest()
    return url.rsplit("/", 1)[-1], out


def strip_version(name: str, version: str) -> str:
    """Normalise a dist-info path so the two versions' metadata files pair up."""
    return name.replace(f"-{version}.dist-info/", "-<VER>.dist-info/")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--old", default="0.5.0")
    ap.add_argument("--new", default="0.6.0")
    args = ap.parse_args()

    print(f"comparing PUBLISHED wheels: {PKG} {args.old} -> {args.new}\n")
    old_file, old = members(args.old)
    new_file, new = members(args.new)
    print(f"  old: {old_file}  ({len(old)} members)")
    print(f"  new: {new_file}  ({len(new)} members)\n")

    old_n = {strip_version(k, args.old): v for k, v in old.items()}
    new_n = {strip_version(k, args.new): v for k, v in new.items()}

    def is_pkg(name: str) -> bool:
        return name.startswith(f"{IMPORT_NAME}/")

    all_names = sorted(set(old_n) | set(new_n))
    pkg_diff, pkg_same, meta_diff, meta_same, only_old, only_new = [], [], [], [], [], []

    for name in all_names:
        a, b = old_n.get(name), new_n.get(name)
        if a is None:
            (only_new).append(name)
            continue
        if b is None:
            (only_old).append(name)
            continue
        same = a == b
        if is_pkg(name):
            (pkg_same if same else pkg_diff).append(name)
        else:
            (meta_same if same else meta_diff).append(name)

    print(f"  PACKAGE ({IMPORT_NAME}/):  {len(pkg_same)} identical, {len(pkg_diff)} differing")
    print(f"  METADATA (.dist-info/):    {len(meta_same)} identical, {len(meta_diff)} differing")
    if only_old:
        print(f"  only in {args.old}: {only_old}")
    if only_new:
        print(f"  only in {args.new}: {only_new}")

    failures = []

    if pkg_diff:
        print(f"\n  !! package payload CHANGED in {len(pkg_diff)} file(s):")
        for n in pkg_diff:
            print(f"       {n}")
        failures.append("the package payload is not identical")
    if only_old or only_new:
        failures.append("the two wheels do not carry the same file set")

    # The metadata MUST differ -- it carries the version. If it does not, the two
    # downloads are the same artifact and this check proved nothing.
    meaningful_meta = [n for n in meta_diff if not n.endswith("RECORD")]
    if not meaningful_meta:
        print("\n  !! metadata is identical apart from RECORD -- the two wheels are")
        print("     indistinguishable, so this comparison is vacuous.")
        failures.append("metadata did not differ; the comparison is vacuous")
    else:
        print(f"\n  metadata differs in: {meaningful_meta}  (expected -- carries the version)")

    print()
    if failures:
        for f in failures:
            print(f"  FAIL: {f}", file=sys.stderr)
        return 1

    print(f"  OK: {PKG} {args.new} is byte-identical to {args.old} across all "
          f"{len(pkg_same)} packaged module files; only the version metadata moved.")
    print("      The Release was cut for the IMAGE, and the wheel confirms it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
