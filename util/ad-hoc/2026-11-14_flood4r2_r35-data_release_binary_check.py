#!/usr/bin/env python3
"""Check that a binary on disk is byte-for-byte the named member of a release tarball, and the tarball its digest.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     juniper-data#530, juniper-data-client#260
Version:     0.1.0
License:     MIT License

The member is hashed as a stream from the archive; nothing is extracted and nothing is written.

Usage:
    python3 -I util/ad-hoc/2026-11-14_flood4r2_r35-data_release_binary_check.py <tarball> <member> <binary> <expected tarball sha256>

Exit 0 when the tarball's SHA-256 is the expected one and the member's equals the binary's; 1 otherwise.
"""

from __future__ import annotations

import hashlib
import sys
import tarfile
from pathlib import Path


def _digest(stream) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1 << 20), b""):
        digest.update(block)
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    """Compare the three digests and print them."""
    if len(argv) != 4:
        print("usage: <tarball> <member> <binary> <expected tarball sha256>", file=sys.stderr)
        return 2
    tarball, member, binary, expected = Path(argv[0]), argv[1], Path(argv[2]), argv[3]
    with tarball.open("rb") as handle:
        tarball_sha = _digest(handle)
    with tarfile.open(tarball, "r:gz") as archive:
        extracted = archive.extractfile(member)
        if extracted is None:
            print(f"{member} is not a regular file in {tarball}", file=sys.stderr)
            return 1
        with extracted:
            member_sha = _digest(extracted)
    with binary.open("rb") as handle:
        binary_sha = _digest(handle)
    print(f"tarball {tarball_sha} (expected {expected}): {'OK' if tarball_sha == expected else 'MISMATCH'}")
    print(f"member  {member_sha}")
    print(f"binary  {binary_sha}: {'the same bytes' if member_sha == binary_sha else 'DIFFERENT'}")
    return 0 if tarball_sha == expected and member_sha == binary_sha else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
