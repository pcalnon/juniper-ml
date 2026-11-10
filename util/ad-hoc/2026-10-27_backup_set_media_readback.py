#!/usr/bin/env python3
"""
Read every copy of one backup set back FROM THE MEDIA (O_DIRECT, past the page cache) and confirm the copies are
complete and identical -- prints names, sizes, byte counts and sha256[:16] only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-27
Status: ad-hoc -- backup arc, Tier 2 acceptance (AC-10) step 3; reusable for Tier 3 (AC-11)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/juniper-backup.bash (verify_archive);
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.8, §7.9;
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_backup-phase-c-lines-0-8-done-drives-then-phase-d.md
         Remaining §1 step 3

WHY O_DIRECT
    util/juniper-backup.bash verifies each copy (`gpg --list-packets`, the recipient count) moments after writing it,
    so the kernel serves that read from the page cache: it proves what was handed to the drive, not what the drive
    stored, and a failing or counterfeit-capacity stick passes it. Dropping the cache needs root; opening the file
    with O_DIRECT does not, and the blocks then come from the device. If O_DIRECT is refused, this script says so and
    exits 2. It never falls back to a cached read, which would pass vacuously.

WHAT IS CHECKED, for every archive of the set (a file whose name contains the set UUID):
    1. every directory holds the same names: a name missing from any directory is a failure;
    2. each copy reads back in full: the bytes read from the media equal its st_size;
    3. all copies of one name have the same SHA-256.
    Exit 0 only when all three hold for every name, at least one archive was found, and --expect (when given)
    matches the count; 1 on any failure; 2 on a usage error, an unreadable directory, or O_DIRECT refused.
    The archives are ciphertext and nothing is decrypted. One directory is allowed (Tier 3's single drive):
    check 3 is then trivially true, and checks 1 and 2 still hold.

Usage:
    python3 util/ad-hoc/2026-10-27_backup_set_media_readback.py --uuid SET_UUID [--expect N] DIR [DIR ...]

    Tier 2, both sticks:
    python3 util/ad-hoc/2026-10-27_backup_set_media_readback.py --uuid 801a3ef5-57b8-48ec-9d07-767193ce97da \\
        --expect 10 /run/media/pcalnon/EBC5-F0A3/Juniper-8.0.0.python /run/media/pcalnon/DFF3-2782/Juniper-8.0.0.python
"""

import argparse
import hashlib
import mmap
import os
import re
import sys

# 8 MiB: a multiple of every logical block size O_DIRECT can require, and an mmap of it is page-aligned.
CHUNK = 8 * 1024 * 1024
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class DirectReadRefused(Exception):
    """O_DIRECT was refused for a path; a cached read would prove nothing, so the run stops."""


def read_back(path: str) -> tuple[int, int, str]:
    """Return (st_size, bytes read from the media, sha256 hex) for one file, read with O_DIRECT."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
    except OSError as exc:
        raise DirectReadRefused(f"{path}: open with O_DIRECT failed: {exc.strerror}") from exc
    buf = mmap.mmap(-1, CHUNK)
    view = memoryview(buf)
    try:
        size = os.fstat(fd).st_size
        digest = hashlib.sha256()
        total = 0
        # Stop at st_size rather than reading on to a zero-length read: after the short tail read the file offset
        # is no longer block-aligned, and an O_DIRECT read at an unaligned offset fails with EINVAL, not EOF.
        while total < size:
            try:
                n = os.readv(fd, [buf])
            except OSError as exc:
                raise DirectReadRefused(f"{path}: O_DIRECT read failed at byte {total}: {exc.strerror}") from exc
            if n == 0:
                break
            digest.update(view[:n])
            total += n
        return size, total, digest.hexdigest()
    finally:
        view.release()
        buf.close()
        os.close(fd)


def main() -> int:
    ap = argparse.ArgumentParser(description="Read one backup set back from the media and compare its copies.")
    ap.add_argument("--uuid", required=True, help="the set UUID every archive name of the set carries")
    ap.add_argument("--expect", type=int, default=None, help="the number of archives the set must hold")
    ap.add_argument("dirs", nargs="+", help="each directory holding one copy of the set")
    args = ap.parse_args()

    if not UUID_RE.match(args.uuid):
        print(f"usage error: --uuid is not a lowercase UUID: {args.uuid!r}", file=sys.stderr)
        return 2

    names_by_dir = {}
    for d in args.dirs:
        try:
            names_by_dir[d] = sorted(n for n in os.listdir(d) if args.uuid in n)
        except OSError as exc:
            print(f"cannot list {d}: {exc.strerror}", file=sys.stderr)
            return 2

    all_names = sorted(set().union(*names_by_dir.values()))
    problems = 0
    for d, names in names_by_dir.items():
        for missing in sorted(set(all_names) - set(names)):
            print(f"MISSING  {missing}  in {d}")
            problems += 1

    total_bytes = copies = 0
    for name in all_names:
        results = []
        for d in args.dirs:
            if name not in names_by_dir[d]:
                continue
            try:
                size, got, sha = read_back(os.path.join(d, name))
            except DirectReadRefused as exc:
                print(f"REFUSED  {exc}", file=sys.stderr)
                return 2
            copies += 1
            total_bytes += got
            if got != size:
                print(f"SHORT    {name}  in {d}: read {got} of {size} bytes")
                problems += 1
            results.append((d, size, sha))
        if len({sha for _, _, sha in results}) == 1:
            # PARTIAL, not SAME, when a directory lacks the name: its MISSING line above already counted it.
            label = "SAME" if len(results) == len(args.dirs) else "PARTIAL"
            print(f"{label:<8} {results[0][1]:>12}  {results[0][2][:16]}  x{len(results)}  {name}")
        else:
            problems += 1
            print(f"DIFF     {name}")
            for d, size, sha in results:
                print(f"           {size:>12}  {sha[:16]}  {d}")

    print()
    print(f"{len(all_names)} archive(s), {copies} copies read back from the media, {total_bytes} bytes")
    if args.expect is not None and len(all_names) != args.expect:
        print(f"expected {args.expect} archive(s) in the set, found {len(all_names)}")
        problems += 1
    if not all_names:
        print(f"no archive name contains {args.uuid}")
        problems += 1
    if problems:
        print(f"RESULT: FAILED ({problems} problem(s))")
        return 1
    print("RESULT: every copy read back in full from the media, and the copies are identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
