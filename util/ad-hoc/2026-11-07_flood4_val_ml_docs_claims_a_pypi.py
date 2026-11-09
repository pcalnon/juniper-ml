"""
Re-probe PyPI for the flood-4 juniper-ml docs carrier's packaging claims (claims lens, slice A: #2409).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-ml docs carrier validation, claims lens slice A (draft #2409, paired tests draft #2410)

Usage: python3 -I 2026-11-07_flood4_val_ml_docs_claims_a_pypi.py <out_dir>

Reads https://pypi.org/pypi/<pkg>/json and /pypi/<pkg>/<ver>/json for juniper-config-tools (0.1.0, 0.1.1) and
juniper-ml (0.5.0, 0.6.0, latest); downloads each juniper-config-tools wheel into <out_dir>/wheels/ (a new,
empty directory) and lists it with zipfile (no code from the wheel is imported or run). Writes
<out_dir>/pypi_probe.json and prints a summary. Network reads only.
"""

import hashlib
import io
import json
import os
import sys
import urllib.request
import zipfile


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:  # nosec B310 -- fixed https PyPI URLs
        return json.load(resp)


def get_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resp:  # nosec B310 -- fixed https PyPI URLs
        return resp.read()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    out_dir = argv[1]
    wheel_dir = os.path.join(out_dir, "wheels")
    os.makedirs(wheel_dir, exist_ok=True)
    report: dict = {}

    top = get_json("https://pypi.org/pypi/juniper-config-tools/json")
    report["config_tools_latest"] = top["info"]["version"]
    report["config_tools_releases"] = {v: [(f["filename"], f.get("upload_time_iso_8601")) for f in files] for v, files in top["releases"].items()}
    for ver in ("0.1.0", "0.1.1"):
        meta = get_json(f"https://pypi.org/pypi/juniper-config-tools/{ver}/json")
        row = {"classifiers": meta["info"].get("classifiers"), "requires_python": meta["info"].get("requires_python"), "requires_dist": meta["info"].get("requires_dist"), "wheels": {}}
        for f in meta["urls"]:
            if not f["filename"].endswith(".whl"):
                row.setdefault("sdists", []).append(f["filename"])
                continue
            data = get_bytes(f["url"])
            sha = hashlib.sha256(data).hexdigest()
            path = os.path.join(wheel_dir, f["filename"])
            with open(path, "wb") as fh:
                fh.write(data)
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = zf.namelist()
            row["wheels"][f["filename"]] = {"sha256": sha, "sha256_matches_pypi": sha == f["digests"]["sha256"], "upload_time": f.get("upload_time_iso_8601"), "files": names}
        report[f"config_tools_{ver}"] = row

    ml = get_json("https://pypi.org/pypi/juniper-ml/json")
    report["ml_latest"] = ml["info"]["version"]
    for ver in ("0.5.0", "0.6.0", ml["info"]["version"]):
        meta = get_json(f"https://pypi.org/pypi/juniper-ml/{ver}/json")
        rd = meta["info"].get("requires_dist") or []
        report[f"ml_{ver}"] = {"config_tools_requirements": [r for r in rd if "config-tools" in r or "config_tools" in r], "upload": [f.get("upload_time_iso_8601") for f in meta["urls"]][:1]}

    with open(os.path.join(out_dir, "pypi_probe.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("config-tools latest:", report["config_tools_latest"])
    print("config-tools releases:", json.dumps(report["config_tools_releases"]))
    for ver in ("0.1.0", "0.1.1"):
        row = report[f"config_tools_{ver}"]
        print(f"== config-tools {ver}: requires_python={row['requires_python']} requires_dist={row['requires_dist']}")
        print("   classifiers:", [c for c in (row["classifiers"] or []) if "Typing" in c or "Python ::" in c])
        for name, w in row["wheels"].items():
            print("   wheel", name, "sha-ok", w["sha256_matches_pypi"], "uploaded", w["upload_time"])
            print("   files:", w["files"])
    print("juniper-ml latest:", report["ml_latest"])
    for key in [k for k in report if k.startswith("ml_0")]:
        print(" ", key, report[key])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
