#!/usr/bin/env python3
"""Round-4 validator helper: re-probe PyPI and read published wheels as zip DATA.

Project: Juniper
Sub-Project: juniper-ml
Application: flood-4 docs-carrier round-4 validation (ad hoc, single use)
Author: Paul Calnon
Version: 0.1.0
License: MIT License
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 4 (findings: tmp/flood4/ml-docs/val-round4/)

Fetches the PyPI JSON for juniper-service-core and juniper-observability, records upload times,
downloads the named wheels into fresh empty directories (sha256-checked against PyPI's digest),
and prints the API-key compare / Sentry frame-locals source out of each wheel WITHOUT importing
or executing anything from it (zipfile reads only).

Usage: python3 -I <this> <out_dir>
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

PKGS = {
    "juniper-service-core": ["0.7.0", "0.7.1"],
    "juniper-observability": ["0.4.0", "0.4.1"],
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "juniper-flood4-val-round4"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310 - fixed https PyPI URLs
        return resp.read()


def show(src: str, pattern: str, before: int, after: int, label: str) -> list[str]:
    out: list[str] = []
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if re.search(pattern, line):
            lo, hi = max(0, i - before), min(len(lines), i + after + 1)
            out.append(f"--- {label} :{i + 1} ---")
            out.extend(f"{j + 1}: {lines[j]}" for j in range(lo, hi))
    return out


def main() -> int:
    out_dir = Path(sys.argv[1]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {}
    text: list[str] = []
    for pkg, versions in PKGS.items():
        meta = json.loads(fetch(f"https://pypi.org/pypi/{pkg}/json"))
        report[pkg] = {"latest": meta["info"]["version"], "versions": {}}
        text.append(f"=== {pkg}: latest {meta['info']['version']}")
        for ver in versions:
            files = meta["releases"].get(ver, [])
            wheels = [f for f in files if f["filename"].endswith(".whl")]
            if not wheels:
                text.append(f"{pkg} {ver}: NO WHEEL")
                continue
            whl = wheels[0]
            report[pkg]["versions"][ver] = {"filename": whl["filename"], "upload_time_iso_8601": whl["upload_time_iso_8601"], "sha256": whl["digests"]["sha256"]}
            dest_dir = out_dir / f"{pkg}-{ver}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / whl["filename"]
            data = fetch(whl["url"])
            got = hashlib.sha256(data).hexdigest()
            dest.write_bytes(data)
            ok = got == whl["digests"]["sha256"]
            report[pkg]["versions"][ver]["sha256_ok"] = ok
            text.append(f"{pkg} {ver}: {whl['filename']} uploaded {whl['upload_time_iso_8601']} sha256_ok={ok}")
            with zipfile.ZipFile(dest) as zf:
                names = zf.namelist()
                if pkg == "juniper-service-core":
                    for member in ("juniper_service_core/security.py",):
                        if member in names:
                            src = zf.read(member).decode("utf-8")
                            text.extend(show(src, r"compare_digest|surrogatepass|encode\(|candidate|for k in|def validate", 3, 6, f"{ver} {member}"))
                        else:
                            text.append(f"{ver}: {member} absent; members with security: {[n for n in names if 'security' in n]}")
                else:
                    hits = [n for n in names if n.endswith(".py")]
                    for member in hits:
                        src = zf.read(member).decode("utf-8")
                        if "include_local_variables" in src or "def configure_sentry" in src:
                            text.extend(show(src, r"include_local_variables|def configure_sentry", 2, 4, f"{ver} {member}"))
    (out_dir / "pypi_report.json").write_text(json.dumps(report, indent=1) + "\n")
    (out_dir / "wheel_sources.txt").write_text("\n".join(text) + "\n")
    print("\n".join(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
