#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. Reproduces, on Linux, the macOS-lane failure of juniper-data-client#221's
# tests/test_lockfile_signed_commit.py: a base64 that rejects GNU `-w` (as BSD/macOS base64
# does) placed first on the step's PATH. The step still exits 0 and builds the
# createCommitOnBranch mutation with EMPTY `contents`, because a failing `$(...)` used as a
# command ARGUMENT is invisible to `set -e`. Runs in temp dirs only; the gh binary is stubbed.
"""Usage: 2026-10-08_flood3_bsd_base64_repro.py <juniper-data-client worktree>"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main(argv: list[str]) -> int:
    repo_root = Path(argv[1]).resolve()
    spec = importlib.util.spec_from_file_location("lockfile_test", repo_root / "tests" / "test_lockfile_signed_commit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _doc, _step, script = mod._load_step()
    success = {"data": {"createCommitOnBranch": {"commit": {"oid": "x", "url": "https://example.invalid/c/x"}}}}
    for label, fake_base64 in (("GNU (host)", None), ("BSD-like (-w rejected)", "#!/bin/sh\necho 'base64: invalid option -- w' >&2\nexit 64\n")):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            mod._init_repo(repo, "pinned==1\n")
            (repo / "requirements.lock").write_text("pinned==2\n", encoding="utf-8")
            (bin_dir / "gh").write_text(mod.GH_STUB, encoding="utf-8")
            (bin_dir / "gh").chmod(0o755)
            if fake_base64:
                (bin_dir / "base64").write_text(fake_base64, encoding="utf-8")
                (bin_dir / "base64").chmod(0o755)
            env = mod._child_env(bin_dir, GH_BODY=json.dumps(success))
            proc = subprocess.run(["bash", "-c", script], cwd=repo, capture_output=True, text=True, env=env, check=False)
            mutation = json.loads(mod.COMMIT_JSON.read_text(encoding="utf-8"))
            contents = mutation["variables"]["input"]["fileChanges"]["additions"][0]["contents"]
            print(f"{label:24s} step rc={proc.returncode} contents={contents!r} stderr={proc.stderr.strip()[:60]!r}")
            mod._clean_api_files()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
