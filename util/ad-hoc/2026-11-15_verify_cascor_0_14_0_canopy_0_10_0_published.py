#!/usr/bin/env python3
"""Verify the PUBLISHED juniper-cascor 0.14.0 and juniper-canopy 0.10.0: on PyPI, equal to TestPyPI, floors and round-up inside.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (post-publication check of the two R-OBS-SC-2 consumer cuts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py (the pattern: read the wheel the index serves,
         never a git tree); notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md and
         notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md; juniper-cascor#758 and juniper-canopy#818 (the proposals)

Why
---
A checkout is not a deployment, and a Release is not a publish: the two releases wait at the Overtoad's ``pypi`` gates
after TestPyPI took the same files. Once the Overtoad approves them, this reads what PyPI serves and checks, per release:

1. the version's JSON answers, it lists exactly one wheel, and the wheel's bytes hash to the sha256 the JSON gives;
2. PyPI's wheel and sdist equal TestPyPI's (``--index pypi`` only), so the gate published what was tested: by sha256,
   or, where the archives differ, member by member. juniper-cascor's publish run has no shared build job (each publish
   job builds its own files), so its 0.13.0 archives differ from TestPyPI's while, if this check passes, every file in
   them is the same;
3. the wheel's ``METADATA`` floors ``juniper-observability>=0.4.2`` and ``juniper-service-core>=0.7.2,<0.8.0``, the
   floors the release PRs raised (round 1's ruling 1 of 2026-11-09: in release PRs);
4. every module in the wheel that defines ``_seconds_until_reset`` also holds ``max(1, math.ceil(``, the round-up of
   juniper-cascor#757 and juniper-canopy#817 (``APD-ECO-016``), which the fork-drift guard matches.

Nothing is installed, imported or written: the wheel is read in memory. ``--control`` checks the previous releases
(cascor 0.13.0, canopy 0.9.0) instead, which must FAIL checks 3 and 4: both were cut before those changes.

    python3 -I util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py                  # after the gates
    python3 -I util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py --index testpypi # before them
    python3 -I util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py --control        # must exit 1

Exit status: 0 when every check passes; 1 when a check ran and failed; 2 when something could not be read (a JSON that
does not answer, other than one wheel, a download whose sha256 differs from its index's). 1 always means a check ran.
"""

from __future__ import annotations

import argparse
import email.parser
import hashlib
import io
import json
import re
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile

INDEXES = {"pypi": "https://pypi.org/pypi/{pkg}/{version}/json", "testpypi": "https://test.pypi.org/pypi/{pkg}/{version}/json"}
RELEASES = {"juniper-cascor": ("0.14.0", "0.13.0"), "juniper-canopy": ("0.10.0", "0.9.0")}
#: requirement name -> the specifiers each release's Requires-Dist must carry
FLOORS = {"juniper-observability": (">=0.4.2",), "juniper-service-core": (">=0.7.2", "<0.8.0")}
ROUND_UP = "max(1, math.ceil("
DEFINES_RESET = re.compile(r"^\s*def _seconds_until_reset\(", re.MULTILINE)
FAILS: list[str] = []


def check(ok: bool, label: str, seen: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'} {label}: {seen}")
    if not ok:
        FAILS.append(label)


def refuse(message: str) -> None:
    print(f"REFUSED: {message}")
    sys.exit(2)


def index_json(index: str, pkg: str, version: str) -> dict:
    url = INDEXES[index].format(pkg=pkg, version=version)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310 - fixed https URL
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        refuse(f"{url} answered {exc.code}")
    except Exception as exc:  # noqa: BLE001 - any fetch failure is a refusal, never a check's failure
        refuse(f"cannot read {url}: {exc}")
    return {}


def files_by_kind(meta: dict) -> dict[str, dict]:
    out = {}
    for kind, suffix in (("wheel", ".whl"), ("sdist", ".tar.gz")):
        hits = [u for u in meta["urls"] if u["filename"].endswith(suffix)]
        if len(hits) != 1:
            refuse(f"the index lists {len(hits)} {kind}s for {meta['info']['name']} {meta['info']['version']}, expected 1")
        out[kind] = hits[0]
    return out


def download(entry: dict) -> bytes:
    try:
        with urllib.request.urlopen(entry["url"], timeout=180) as resp:  # nosec B310 - an https URL from the index's JSON
            data = resp.read()
    except Exception as exc:  # noqa: BLE001 - a failed download must not read as a failed check
        refuse(f"cannot download {entry['filename']}: {exc}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry["digests"]["sha256"]:
        refuse(f"{entry['filename']} downloaded with sha256 {digest}, the index says {entry['digests']['sha256']}")
    return data


def members(kind: str, blob: bytes) -> dict[str, bytes]:
    if kind == "wheel":
        archive = zipfile.ZipFile(io.BytesIO(blob))
        return {n: archive.read(n) for n in archive.namelist() if not n.endswith("/")}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        return {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}


def member_diff(kind: str, a: bytes, b: bytes) -> list[str]:
    """Names present in one archive only, or whose bytes differ: an empty list means the two archives hold the same files."""
    ma, mb = members(kind, a), members(kind, b)
    return sorted(n for n in ma.keys() | mb.keys() if ma.get(n) != mb.get(n))


def requires(metadata: str) -> dict[str, str]:
    msg = email.parser.Parser().parsestr(metadata)
    out = {}
    for line in msg.get_all("Requires-Dist") or []:
        m = re.match(r"^\s*([A-Za-z0-9_.\-]+)", line)
        if m:
            out[m.group(1).lower().replace("_", "-")] = line.strip()
    return out


def verify(index: str, pkg: str, version: str) -> None:
    print(f"== {pkg} {version} ({index})")
    meta = index_json(index, pkg, version)
    files = files_by_kind(meta)
    data = download(files["wheel"])
    print(f"  wheel {files['wheel']['filename']}: {len(data)} bytes, sha256 {files['wheel']['digests']['sha256']} (uploaded {files['wheel']['upload_time_iso_8601']})")
    if index == "pypi":
        test = files_by_kind(index_json("testpypi", pkg, version))
        for kind in ("wheel", "sdist"):
            ours, theirs = files[kind]["digests"]["sha256"], test[kind]["digests"]["sha256"]
            if ours == theirs:
                check(True, f"{kind} equals TestPyPI's", f"sha256 {ours[:16]}… on both")
                continue
            # juniper-cascor's publish run has no shared build job: each publish job builds its own files, so the
            # archives differ (timestamps) even when every member is the same. Compare the members' bytes instead.
            mine = data if kind == "wheel" else download(files[kind])
            diff = member_diff(kind, mine, download(test[kind]))
            seen = f"sha256 PyPI {ours[:16]}…, TestPyPI {theirs[:16]}…; " + ("every member identical (the archives alone differ)" if not diff else f"{len(diff)} member(s) differ: {diff[:6]}")
            check(not diff, f"{kind} contents equal TestPyPI's", seen)
    wheel = zipfile.ZipFile(io.BytesIO(data))
    metadata_name = next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA"))
    metadata = wheel.read(metadata_name).decode("utf-8")
    declared = email.parser.Parser().parsestr(metadata).get("Version")
    check(declared == version, "METADATA Version", str(declared))
    reqs = requires(metadata)
    for name, specs in FLOORS.items():
        line = reqs.get(name, "(absent)")
        spec_part = line.split(";", 1)[0]
        check(all(s in spec_part.replace(" ", "") for s in specs), f"Requires-Dist floors {name} {','.join(specs)}", line)
    reset_modules = []
    for name in wheel.namelist():
        if name.endswith(".py"):
            text = wheel.read(name).decode("utf-8", errors="replace")
            if DEFINES_RESET.search(text):
                reset_modules.append((name, text.count(ROUND_UP)))
    check(bool(reset_modules), "modules defining _seconds_until_reset", ", ".join(n for n, _ in reset_modules) or "(none)")
    for name, count in reset_modules:
        check(count >= 1, f"{name} holds {ROUND_UP!r}", f"{count} occurrence(s)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--index", choices=sorted(INDEXES), default="pypi")
    ap.add_argument("--control", action="store_true", help="check the previous releases instead; they must fail")
    args = ap.parse_args()
    for pkg, (version, previous) in RELEASES.items():
        verify(args.index, pkg, previous if args.control else version)
    print(f"{len(FAILS)} failed check(s)" + (f": {FAILS}" if FAILS else ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
