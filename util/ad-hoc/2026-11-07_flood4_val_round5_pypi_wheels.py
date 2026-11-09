#!/usr/bin/env python3
"""
Round-5 validator probe: every PyPI release (with upload time) of juniper-service-core, juniper-observability and
juniper-data, and the key-compare / Sentry-locals source of each wheel, read in memory as zip DATA (never imported,
never written to disk as a wheel).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 5 (findings: tmp/flood4/ml-docs/val-round5/)

Usage: python3 -I 2026-11-07_flood4_val_round5_pypi_wheels.py <out_dir>
Writes <out_dir>/pypi_releases.json and <out_dir>/wheel_snippets.txt.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile

PKGS = {
    "juniper-service-core": ["juniper_service_core/security.py", "juniper_service_core/middleware.py", "juniper_service_core/websocket/"],
    "juniper-observability": ["juniper_observability/sentry.py"],
    "juniper-data": ["juniper_data/api/security.py", "juniper_data/api/middleware.py", "juniper_data/api/app.py"],
}
PATTERNS = re.compile(r"compare_digest|surrogatepass|for candidate|for k in|include_local_variables|\"vars\"|'vars'|pop\(|sentry_sdk\.init|def _strip_sensitive_headers|def validate|record_failure|status_code == 401|HTTP_401|4001|def ws_authenticate|auth\.validate|def configure_sentry|EventScrubber")


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "juniper-ml-flood4-validator/1"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310 - fixed https PyPI URLs
        return resp.read()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    out_dir = argv[1]
    report: dict = {}
    lines: list[str] = []
    for pkg, members in PKGS.items():
        meta = json.loads(_get(f"https://pypi.org/pypi/{pkg}/json"))
        rels = []
        for ver, files in meta["releases"].items():
            for f in files:
                rels.append({"version": ver, "filename": f["filename"], "packagetype": f["packagetype"], "upload": f["upload_time_iso_8601"], "yanked": f.get("yanked", False), "sha256": f["digests"]["sha256"], "url": f["url"]})
        rels.sort(key=lambda r: r["upload"])
        report[pkg] = {"latest": meta["info"]["version"], "files": [{k: v for k, v in r.items() if k != "url"} for r in rels]}
        wheels = [r for r in rels if r["packagetype"] == "bdist_wheel"]
        if pkg == "juniper-data":
            wheels = [r for r in wheels if r["version"].startswith(("0.15", "0.16", "0.17", "0.18"))]
        else:
            wheels = [r for r in wheels if r["version"].startswith(("0.3", "0.4", "0.5", "0.6", "0.7", "0.8"))]
        for r in wheels:
            blob = _get(r["url"])
            ok = hashlib.sha256(blob).hexdigest() == r["sha256"]
            lines.append(f"===== {pkg} {r['version']} {r['filename']} uploaded {r['upload']} sha256_ok={ok}")
            zf = zipfile.ZipFile(io.BytesIO(blob))
            for name in zf.namelist():
                if name.endswith("METADATA") and ".dist-info/" in name:
                    for mline in zf.read(name).decode("utf-8", "replace").splitlines():
                        if mline.startswith("Requires-Dist:") and ("juniper" in mline or "sentry" in mline):
                            lines.append(f"  META {mline}")
            for name in sorted(zf.namelist()):
                if not any(name == m or (m.endswith("/") and name.startswith(m) and name.endswith(".py")) for m in members):
                    continue
                text = zf.read(name).decode("utf-8", "replace").splitlines()
                for i, t in enumerate(text, 1):
                    if PATTERNS.search(t):
                        lines.append(f"  {name}:{i}: {t.rstrip()[:220]}")
    with open(f"{out_dir}/pypi_releases.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    with open(f"{out_dir}/wheel_snippets.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out_dir}/pypi_releases.json and {out_dir}/wheel_snippets.txt ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
