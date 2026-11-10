#!/usr/bin/env python3
"""
Download and extract each named Juniper repository's ``main`` tarball, so an edit is made against GitHub's ``main`` and not a lagging local checkout.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-03
Status: ad-hoc — one-off (flood-3: SHA-pin agents-md-touch-up.yml's checkout in seven repositories, owner ruling 2026-11-03)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§9); juniper-data#503 (the first pin)

    python3 -I util/ad-hoc/2026-11-03_fetch_main_tarballs.py <dest-dir> <repo> [<repo> ...]

Each repository lands in ``<dest-dir>/<repo>/`` (the tarball's top directory stripped), and its ``main`` SHA is
written to ``<dest-dir>/<repo>.sha``. Runs only ``gh api`` GETs. Exit 0 on success, 1 on any failure.
"""

from __future__ import annotations

import io
import subprocess  # nosec B404 - fixed gh argv, no shell
import sys
import tarfile
from pathlib import Path


def fetch(dest: Path, repo: str) -> None:
    sha = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/commits/main", "--jq", ".sha"], check=True, capture_output=True, text=True).stdout.strip()  # nosec B603 B607
    blob = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/tarball/{sha}"], check=True, capture_output=True).stdout  # nosec B603 B607
    out = dest / repo
    out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for member in tar.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts or member.issym() or member.islnk() or ".." in parts:
                continue
            member.name = str(Path(*parts))
            tar.extract(member, out, filter="data")
    (dest / f"{repo}.sha").write_text(sha + "\n")
    print(f"{repo}\t{sha[:8]}")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 1
    dest = Path(argv[1])
    for repo in argv[2:]:
        fetch(dest, repo)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
