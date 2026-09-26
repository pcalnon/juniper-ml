#!/usr/bin/env python3
"""Lane A helper: `git archive <rev> [paths...]` from a repo dir, extracted into <outdir>. Read-only on the repo.

usage: garchive.py <repo_dir> <rev> <outdir> [<pathspec> ...]
"""
import io
import os
import subprocess
import sys
import tarfile

repo, rev, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
specs = sys.argv[4:]
os.makedirs(outdir, exist_ok=True)
data = subprocess.run(["git", "archive", "--format=tar", rev, *specs], cwd=repo, check=True, capture_output=True).stdout
with tarfile.open(fileobj=io.BytesIO(data)) as tf:
    members = tf.getmembers()
    tf.extractall(outdir, filter="tar")
print(f"extracted {len(members)} members of {rev} into {outdir} ({len(data)} tar bytes)")
