"""
Verify the pinned SHA-256 of the gitleaks 8.24.3 linux_x64 release tarball against the release's own checksums file.

Downloads the checksums file and the tarball (two GETs, written to a directory given on the command line, nothing
executed and nothing piped), hashes the tarball, compares the three values (pinned in ci.yml, published in the
checksums file, computed here), then lists the tarball's members and hashes the ``gitleaks`` member so a local binary
can be compared with it. With ``--binary`` it also hashes that local file.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_release_digest.py <ci.yml> <download dir> [--binary <path>]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

import yaml

VERSION = "8.24.3"
BASE = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}"
ASSET = f"gitleaks_{VERSION}_linux_x64.tar.gz"
CHECKSUMS = f"gitleaks_{VERSION}_checksums.txt"


def fetch(name: str, dest: Path) -> Path:
    target = dest / name
    if not target.is_file():
        with urllib.request.urlopen(f"{BASE}/{name}", timeout=180) as response:  # nosec B310 -- a fixed https URL
            target.write_bytes(response.read())
    return target


def main() -> int:
    workflow, dest = Path(sys.argv[1]), Path(sys.argv[2])
    binary = Path(sys.argv[sys.argv.index("--binary") + 1]) if "--binary" in sys.argv else None
    dest.mkdir(parents=True, exist_ok=True)
    steps = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    install = next(step for step in steps if step.get("name") == "Install Gitleaks (pull request)")
    pinned = str(install["env"]["GITLEAKS_SHA256"])
    pinned_version = str(install["env"]["GITLEAKS_VERSION"])

    checksums = fetch(CHECKSUMS, dest).read_text(encoding="utf-8")
    published = {line.split()[1]: line.split()[0] for line in checksums.splitlines() if line.strip()}
    tarball = fetch(ASSET, dest)
    computed = hashlib.sha256(tarball.read_bytes()).hexdigest()

    with tarfile.open(tarball, "r:gz") as archive:
        members = [(member.name, member.size, member.isfile()) for member in archive.getmembers()]
        engine = archive.extractfile("gitleaks")
        engine_sha = hashlib.sha256(engine.read()).hexdigest() if engine else None

    report = {
        "pinned_version": pinned_version,
        "pinned_sha256": pinned,
        "published_linux_x64": published.get(ASSET),
        "computed_from_download": computed,
        "pinned_equals_published": pinned == published.get(ASSET),
        "published_equals_computed": published.get(ASSET) == computed,
        "checksums_file_lines": len(published),
        "tarball_bytes": tarball.stat().st_size,
        "tarball_members": members,
        "engine_member_sha256": engine_sha,
    }
    if binary is not None:
        report["local_binary"] = str(binary)
        report["local_binary_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        report["local_binary_is_the_release_engine"] = report["local_binary_sha256"] == engine_sha
    print(json.dumps(report, indent=2))
    ok = report["pinned_equals_published"] and report["published_equals_computed"] and pinned_version == VERSION
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
