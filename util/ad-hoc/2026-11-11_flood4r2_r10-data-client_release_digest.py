#!/usr/bin/env python3
"""
Check a gitleaks release tarball's SHA-256 against the release's own checksums file and a pinned digest, then unpack the binary.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-data-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
The pull-request install step pins GITLEAKS_SHA256. A port must not copy that digest on trust: it downloads the
release's `gitleaks_<version>_checksums.txt` and the `linux_x64` tarball itself, hashes the tarball, and requires
three values to agree -- the hash of the bytes, the checksums file's line for the asset, and the digest the workflow
pins. It also fetches the tarball from the legacy `zricethezav` URL gitleaks-action downloads from, to show the action
and the install step get the same bytes. Only then does it copy the one regular member named `gitleaks` into a new
directory, so the real-engine tests can run against the official build. Downloads are plain HTTPS GETs with no
credentials; nothing is piped into a shell; nothing is unpacked with `extractall`.

Usage:
    python3 <this> --version 8.24.3 --pinned <sha256> --downloads <new empty dir> --bin <new empty dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - runs the unpacked binary with the fixed argument `version`
import sys
import tarfile
import urllib.request
from pathlib import Path

CANONICAL = "https://github.com/gitleaks/gitleaks/releases/download"
LEGACY = "https://github.com/zricethezav/gitleaks/releases/download"


def fetch(url: str, dest: Path) -> str:
    """GET ``url`` (https only) into ``dest``; return the SHA-256 of the bytes written."""
    if not url.startswith("https://github.com/"):
        raise SystemExit(f"refusing to fetch {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "release-digest-check"})
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=120) as response, open(dest, "wb") as fh:  # nosec B310 - https://github.com/ only, checked above
        for chunk in iter(lambda: response.read(1 << 16), b""):
            digest.update(chunk)
            fh.write(chunk)
    return digest.hexdigest()


def new_empty_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise SystemExit(f"{path} is not empty; give a new directory")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--pinned", required=True, help="the digest the workflow pins")
    ap.add_argument("--downloads", type=Path, required=True)
    ap.add_argument("--bin", type=Path, required=True)
    args = ap.parse_args()
    downloads, bindir = new_empty_dir(args.downloads.resolve()), new_empty_dir(args.bin.resolve())
    asset = f"gitleaks_{args.version}_linux_x64.tar.gz"
    sums_name = f"gitleaks_{args.version}_checksums.txt"
    sums_sha = fetch(f"{CANONICAL}/v{args.version}/{sums_name}", downloads / sums_name)
    tar_sha = fetch(f"{CANONICAL}/v{args.version}/{asset}", downloads / asset)
    legacy_sha = fetch(f"{LEGACY}/v{args.version}/{asset}", downloads / ("legacy_" + asset))
    listed = [line.split() for line in (downloads / sums_name).read_text(encoding="utf-8").splitlines() if line.strip()]
    published = [digest for digest, name in (pair for pair in listed if len(pair) == 2) if name.lstrip("*") == asset]
    result = {
        "version": args.version,
        "asset": asset,
        "sha256_of_downloaded_tarball": tar_sha,
        "sha256_of_legacy_url_tarball": legacy_sha,
        "checksums_file_line": published,
        "sha256_of_checksums_file": sums_sha,
        "pinned": args.pinned,
    }
    agree = published == [tar_sha] and tar_sha == args.pinned and legacy_sha == tar_sha
    result["all_agree"] = agree
    if agree:
        with tarfile.open(downloads / asset, "r:gz") as tar:
            members = [m for m in tar.getmembers() if m.name == "gitleaks" and m.isreg()]
            if len(members) != 1:
                raise SystemExit(f"expected exactly one regular member named gitleaks, found {len(members)}")
            source = tar.extractfile(members[0])
            if source is None:
                raise SystemExit("the gitleaks member could not be read")
            with source, open(bindir / "gitleaks", "wb") as out:
                shutil.copyfileobj(source, out)
            result["tarball_members"] = sorted(m.name for m in tar.getmembers())
        (bindir / "gitleaks").chmod(0o755)
        result["sha256_of_binary"] = hashlib.sha256((bindir / "gitleaks").read_bytes()).hexdigest()
        proc = subprocess.run([str(bindir / "gitleaks"), "version"], capture_output=True, text=True, timeout=60, check=False)  # nosec B603
        result["binary_version_output"] = (proc.stdout + proc.stderr).strip()
        result["binary"] = str(bindir / "gitleaks")
    print(json.dumps(result, indent=1))
    return 0 if agree and result.get("binary_version_output") == args.version else 1


if __name__ == "__main__":
    sys.exit(main())
