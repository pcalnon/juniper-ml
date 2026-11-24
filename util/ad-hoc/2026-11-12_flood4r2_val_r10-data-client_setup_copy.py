"""
Build the validator's own copy of the juniper-data-client ruling-10 carrier, and dump the reference blobs it is compared with.

Read-only on the carrier worktree. It copies the carrier's six files into the validator's worktree (made from
origin/main beforehand), records every sha256, and writes juniper-data's and juniper-data-client's origin/main
versions of the compared files into the validator's scratch directory.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_setup_copy.py [--check-only]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-data-client--ci--gitleaks-pr-commit-scan--20261111-1914--3cd855d1"
COPY = JUNIPER / "worktrees" / "juniper-data-client--val--r10-port--20261112-0225--3cd855d1"
SCRATCH = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "r10-data-client-s5"
CLIENT = JUNIPER / "juniper-data-client"
DATA = JUNIPER / "juniper-data"

SIX = [
    ".github/workflows/ci.yml",
    "docs/REFERENCE.md",
    "CHANGELOG.md",
    "tests/test_gitleaks_pr_scan.py",
    "util/ad-hoc/2026-11-11_reproduce_gitleaks_pr_commit_window.py",
    "util/ad-hoc/2026-11-11_verify_gitleaks_pr_scan_tests_are_not_vacuous.py",
]
CLIENT_MAIN = [".github/workflows/ci.yml", "docs/REFERENCE.md", "CHANGELOG.md", ".github/workflows/security-scan.yml", ".pre-commit-config.yaml"]
DATA_MAIN = [
    ".github/workflows/ci.yml",
    "juniper_data/tests/unit/test_gitleaks_config.py",
    "util/ad-hoc/2026-11-08_reproduce_gitleaks_pr_commit_window.py",
    "util/ad-hoc/2026-11-08_verify_gitleaks_pr_scan_tests_are_not_vacuous.py",
    "CHANGELOG.md",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if res.returncode != 0:
        raise SystemExit(f"git -C {repo} {' '.join(args)} exited {res.returncode}: {res.stderr.decode(errors='replace')}")
    return res.stdout


def dump(repo: Path, rels: list[str], dest: Path) -> dict[str, str]:
    out = {}
    for rel in rels:
        blob = git(repo, "show", f"origin/main:{rel}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        out[rel] = hashlib.sha256(blob).hexdigest()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--check-only", action="store_true", help="copy nothing; compare the carrier's six files with the recorded sha256s and with the copy")
    args = parser.parse_args()

    record_path = SCRATCH / "copy_sha256.json"
    carrier_now = {rel: sha256(CARRIER / rel) for rel in SIX}
    if args.check_only:
        with open(record_path, encoding="utf-8") as fh:
            record = json.load(fh)
        drift = {rel: (record["carrier"][rel], digest) for rel, digest in carrier_now.items() if record["carrier"][rel] != digest}
        copy_now = {rel: sha256(COPY / rel) for rel in SIX}
        dirty = {rel: (carrier_now[rel], digest) for rel, digest in copy_now.items() if carrier_now[rel] != digest}
        print(json.dumps({"carrier_changed_since_copy": drift, "copy_differs_from_carrier": dirty}, indent=2))
        return 1 if drift or dirty else 0

    client_main = git(CLIENT, "rev-parse", "origin/main").decode().strip()
    data_main = git(DATA, "rev-parse", "origin/main").decode().strip()
    copy_head = git(COPY, "rev-parse", "HEAD").decode().strip()
    carrier_head = git(CARRIER, "rev-parse", "HEAD").decode().strip()
    if not client_main == copy_head == carrier_head:
        raise SystemExit(f"bases differ: client origin/main {client_main}, copy {copy_head}, carrier {carrier_head}")
    for rel in SIX:
        target = COPY / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CARRIER / rel, target)
    record = {
        "client_origin_main": client_main,
        "data_origin_main": data_main,
        "carrier": carrier_now,
        "copy": {rel: sha256(COPY / rel) for rel in SIX},
        "client_main_blobs": dump(CLIENT, CLIENT_MAIN, SCRATCH / "ref" / f"client_main_{client_main[:8]}"),
        "data_main_blobs": dump(DATA, DATA_MAIN, SCRATCH / "ref" / f"data_main_{data_main[:8]}"),
    }
    with open(record_path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
        fh.write("\n")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
