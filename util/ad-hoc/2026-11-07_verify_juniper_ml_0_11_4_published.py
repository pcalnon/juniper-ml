#!/usr/bin/env python3
"""
Probe the PUBLISHED juniper-ml release for its ``[recurrence]`` floor, and check PyPI serves the build TestPyPI took.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (post-publication check of juniper-ml 0.11.4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/releases/RELEASE_NOTES_v0.11.4.md (the release this checks; archived by ml#2497);
         ml#2473 (the floor this release carries); publish run 42230617125;
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.14 records this probe);
         util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py (the pattern this follows)

Why this exists
---------------
juniper-ml 0.11.4 exists to carry one floor, ``juniper-recurrence>=0.8.1,<0.9.0`` under ``[recurrence]``
(ml#2473): recurrence 0.8.0 admits juniper-model-core 0.2.0, on which every ``POST /v1/crossval`` answers 500.
A checkout is not a deployment, so this reads what PyPI serves and never a git tree:

1. PyPI's VERSION endpoint (``/pypi/juniper-ml/<version>/json``; the aggregate endpoint lags after a
   publish) names the version, and its ``requires_dist`` carries the expected requirement;
2. PyPI lists exactly one wheel and one sdist, and the wheel downloads with the sha256 PyPI states;
3. the wheel's own ``METADATA`` names the same version and the same ``Requires-Dist`` set as PyPI's JSON;
4. TestPyPI's wheel and sdist for the version carry the same sha256 as PyPI's, so PyPI serves the build
   the workflow verified on TestPyPI, not a second build.

``--resolve`` adds a consumer's view: ``pip install --dry-run`` of ``juniper-ml[<extra>]==<version>`` against
real PyPI per Python version (Linux x86_64 wheels only, so nothing is built or installed), and reports the
juniper-recurrence and juniper-model-core versions it picks. That check does not discriminate between
releases (any of them resolves the newest recurrence today); it shows the published metadata resolves.

The 0.11.3 run is the control: it must FAIL check 1, since 0.11.3 floors ``juniper-recurrence>=0.8.0``.

    python3 -I util/ad-hoc/2026-11-07_verify_juniper_ml_0_11_4_published.py --version 0.11.4 [--resolve recurrence --resolve all]
    python3 -I util/ad-hoc/2026-11-07_verify_juniper_ml_0_11_4_published.py --version 0.11.3   # the control: fails

Exit status: 0 when every check passes, 1 when any check fails, and 2 on anything else: a JSON or file that
cannot be fetched, a download whose sha256 differs from the index's, or an unexpected error. So 1 always
means a check ran and failed.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path

PYPI_JSON = "https://pypi.org/pypi/juniper-ml/{version}/json"
TESTPYPI_JSON = "https://test.pypi.org/pypi/juniper-ml/{version}/json"
EXPECTED = 'juniper-recurrence<0.9.0,>=0.8.1; extra == "recurrence"'
# pip treats --platform as an EXACT tag list (util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py explains why every minor is named).
PLATFORMS = [f"manylinux_2_{minor}_x86_64" for minor in range(39, 16, -1)] + ["manylinux2014_x86_64", "manylinux_2_5_x86_64", "manylinux1_x86_64"]
WATCHED = ("juniper-recurrence", "juniper-model-core")


def refuse(message: str) -> None:
    print(f"REFUSED: {message}")
    sys.exit(2)


def fetch(url: str, timeout: int = 60) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310 - fixed https index URLs and URLs from their JSON
            return resp.read()
    except Exception as exc:  # noqa: BLE001 - a failed fetch must not exit 1, the control's failing status
        refuse(f"cannot fetch {url}: {exc}")
        raise  # unreachable; refuse() exits


def files_by_kind(meta: dict, index: str) -> dict[str, dict]:
    kinds: dict[str, list[dict]] = {"wheel": [], "sdist": []}
    for item in meta["urls"]:
        kinds["wheel" if item["filename"].endswith(".whl") else "sdist"].append(item)
    for kind, items in kinds.items():
        if len(items) != 1:
            refuse(f"{index} lists {len(items)} {kind} file(s), expected 1")
    return {kind: items[0] for kind, items in kinds.items()}


def wheel_metadata(data: bytes) -> tuple[str, set[str]]:
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        names = [n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            refuse(f"the wheel holds {len(names)} METADATA files, expected 1")
        message = Parser().parsestr(wheel.read(names[0]).decode("utf-8"))
    return message["Version"], set(message.get_all("Requires-Dist") or [])


def resolve(extra: str, version: str, python: str) -> tuple[bool, dict[str, str], str]:
    with tempfile.TemporaryDirectory(prefix="ml-0-11-4-resolve-") as tmp:  # under TMPDIR, the repo's tmp/
        report = Path(tmp) / "report.json"
        cmd = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--no-cache-dir", "--quiet", "--disable-pip-version-check", "--resume-retries", "10", "--report", str(report), "--python-version", python, "--only-binary=:all:", "--target", str(Path(tmp) / "target")]
        for platform in PLATFORMS:
            cmd += ["--platform", platform]
        proc = subprocess.run(cmd + [f"juniper-ml[{extra}]=={version}"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()
            return False, {}, tail[-1] if tail else f"pip exit {proc.returncode}"
        data = json.loads(report.read_text(encoding="utf-8"))
        return True, {item["metadata"]["name"].lower().replace("_", "-"): item["metadata"]["version"] for item in data["install"]}, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True, help="the juniper-ml version to read, e.g. 0.11.4")
    ap.add_argument("--expect", default=EXPECTED, help=f"a requires_dist entry that must be present (default: {EXPECTED!r})")
    ap.add_argument("--resolve", action="append", default=[], metavar="EXTRA", help="also dry-run resolve juniper-ml[EXTRA]==VERSION against PyPI (repeatable)")
    ap.add_argument("--python", action="append", default=[], help="Python versions for --resolve (default: 3.12, 3.13, 3.14)")
    ap.add_argument("--list", metavar="PREFIX", help="with --resolve, also print every resolved package whose name starts with PREFIX (e.g. juniper-)")
    args = ap.parse_args()
    failures = 0

    def check(ok: bool, message: str) -> None:
        nonlocal failures
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        failures += 0 if ok else 1

    pypi = json.loads(fetch(PYPI_JSON.format(version=args.version)))
    check(pypi["info"]["version"] == args.version, f"PyPI's version endpoint names {pypi['info']['version']}")
    requires = set(pypi["info"].get("requires_dist") or [])
    check(args.expect in requires, f"PyPI's requires_dist carries {args.expect!r}" if args.expect in requires else f"PyPI's requires_dist lacks {args.expect!r} (recurrence entries: {sorted(r for r in requires if r.startswith('juniper-recurrence'))})")

    pypi_files = files_by_kind(pypi, "PyPI")
    wheel = pypi_files["wheel"]
    data = fetch(wheel["url"], timeout=120)
    digest = hashlib.sha256(data).hexdigest()
    if digest != wheel["digests"]["sha256"]:
        refuse(f"{wheel['filename']} downloaded with sha256 {digest}, PyPI says {wheel['digests']['sha256']}")
    print(f"wheel: {wheel['filename']} ({len(data)} bytes; sha256 {digest} = PyPI's; uploaded {wheel['upload_time_iso_8601']})")
    print(f"sdist: {pypi_files['sdist']['filename']} (sha256 {pypi_files['sdist']['digests']['sha256']}; uploaded {pypi_files['sdist']['upload_time_iso_8601']})")

    meta_version, meta_requires = wheel_metadata(data)
    check(meta_version == args.version, f"the wheel's METADATA names Version {meta_version}")
    check(meta_requires == requires, f"the wheel's METADATA Requires-Dist equals PyPI's requires_dist ({len(meta_requires)} entries)" if meta_requires == requires else f"the wheel's METADATA and PyPI's JSON differ: only in METADATA {sorted(meta_requires - requires)}, only in JSON {sorted(requires - meta_requires)}")

    test = json.loads(fetch(TESTPYPI_JSON.format(version=args.version)))
    test_files = files_by_kind(test, "TestPyPI")
    for kind in ("wheel", "sdist"):
        ours, theirs = pypi_files[kind], test_files[kind]
        same = ours["digests"]["sha256"] == theirs["digests"]["sha256"] and ours["filename"] == theirs["filename"]
        check(same, f"TestPyPI's {kind} {theirs['filename']} carries PyPI's sha256 (TestPyPI upload {theirs['upload_time_iso_8601']})" if same else f"TestPyPI's {kind} {theirs['filename']} ({theirs['digests']['sha256']}) differs from PyPI's {ours['filename']} ({ours['digests']['sha256']})")

    for extra in args.resolve:
        for python in args.python or ["3.12", "3.13", "3.14"]:
            ok, pins, error = resolve(extra, args.version, python)
            if ok:
                watched = ", ".join(f"{name} {pins.get(name, 'absent')}" for name in WATCHED)
                check(pins.get("juniper-ml") == args.version, f"juniper-ml[{extra}]=={args.version} resolves on Python {python} in {len(pins)} packages ({watched})")
                if args.list:
                    listed = sorted((name, ver) for name, ver in pins.items() if name.startswith(args.list))
                    print(f"  {len(listed)} {args.list}* packages: " + ", ".join(f"{name} {ver}" for name, ver in listed))
            else:
                check(False, f"juniper-ml[{extra}]=={args.version} does not resolve on Python {python}: {error}")

    print(f"{'PASS' if not failures else 'FAIL'}: juniper-ml {args.version}, {failures} failed check(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        status = main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - an unexpected error must not exit 1, which means a failed check
        print(f"ERROR: {type(exc).__name__}: {exc}")
        status = 2
    raise SystemExit(status)
