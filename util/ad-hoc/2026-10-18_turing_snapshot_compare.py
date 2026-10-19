"""
Compare worktree files with the last entry of the same name in the durable Session 1 staged-code.tar snapshot.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-18
Status: ad-hoc — one-off (confirming the files about to land are the reviewed ones)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md;
         ~/.local/state/juniper/turing-session1/staged-code.tar (host-local, not in the repo)

Why: the six Session 1 tasks were written and reviewed in agent worktrees, copied into one staging worktree,
and snapshotted to a tar outside any worktree before a context compaction. Before landing them, this proved
the staging copies were byte-identical to the snapshot. The tar was appended to as files changed, so the last
member of each name wins, as it does when tar extracts.

Usage:
    python3 -I util/ad-hoc/2026-10-18_turing_snapshot_compare.py SNAPSHOT.tar PATH [PATH ...]

Exit 0 when every path matches; 1 when any differs or is missing from the tar.
"""
import hashlib
import sys
import tarfile
from pathlib import Path

tar_path, *paths = sys.argv[1:]
last = {}
with tarfile.open(tar_path) as tf:
    for m in tf.getmembers():
        if m.isfile():
            last[m.name] = tf.extractfile(m).read()

bad = 0
for p in paths:
    local = Path(p).read_bytes()
    snap = last.get(p)
    if snap is None:
        print(f"NOT-IN-TAR  {p}")
        bad += 1
        continue
    same = hashlib.sha256(local).digest() == hashlib.sha256(snap).digest()
    bad += not same
    print(f"{'SAME' if same else 'DIFF'}  {p}  {hashlib.sha256(local).hexdigest()[:12]}")
sys.exit(1 if bad else 0)
