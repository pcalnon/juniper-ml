#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Round-2: run a carrier's test files read-only, under two git configs, with strace.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#797 tests carrier, validation round 2, item 3: the carried test files' runs (findings: tmp/flood4/canopy/val-round2/)

From <carrier>/src: `conda run -n JuniperCanopy1 python -m pytest <files>` with
PYTHONDONTWRITEBYTECODE=1, -p no:cacheprovider, --basetemp in the scratch dir, TMPDIR in the
scratch dir. Config A: GIT_CONFIG_GLOBAL=/dev/null. Config B: the host's real global config
(GIT_CONFIG_GLOBAL removed from the env). Each run is wrapped in `strace -f` (file syscalls);
afterwards the trace is searched for any path under the system temp dirs opened for writing or
created, and for every open of a lockfile-commit*.json path. Also: a listing of the system temp dirs' lockfile
entries before/after, and every file under the carrier newer than a marker taken before the run.

Usage: python3 <this> <carrier> <scratch dir> <file> [<file> ...]
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time

WRITE_FLAGS = re.compile(r"O_WRONLY|O_RDWR|O_CREAT|O_TRUNC")


def tmp_lockfiles() -> list[str]:
    out = []
    for root in ("/tmp", "/var/tmp"):  # tmp-path-literal: allow (detector: reads the system temp dir, never writes it)
        try:
            out += [f"{root}/{n}" for n in os.listdir(root) if "lockfile" in n.lower()]
        except OSError as exc:
            out.append(f"{root}: {exc}")
    return sorted(out)


def newer_than(root: pathlib.Path, t0: float) -> list[str]:
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "/.git" in dirpath or dirpath.endswith("/.git"):
            continue
        for name in filenames + dirnames:
            p = pathlib.Path(dirpath) / name
            try:
                if p.lstat().st_mtime > t0 or p.lstat().st_ctime > t0:
                    hits.append(str(p.relative_to(root)))
            except OSError:
                pass  # gone or unreadable since os.walk listed it: there is no time to compare, so it is skipped
    return sorted(hits)


def analyse_trace(trace: pathlib.Path) -> dict:
    tmp_writes, lockfile_opens = [], []
    for line in trace.read_text(errors="replace").splitlines():
        m = re.search(r'(open|openat|creat|mkdir|mkdirat|rename|renameat2?|unlink|unlinkat)\((?:[^,]*, )?"([^"]+)"', line)
        if not m:
            continue
        path = m.group(2)
        if "lockfile-commit" in path:
            lockfile_opens.append(line.strip()[:300])
        if (path.startswith("/tmp/") or path.startswith("/var/tmp/")) and (WRITE_FLAGS.search(line) or m.group(1) in ("creat", "mkdir", "mkdirat", "rename", "renameat", "renameat2", "unlink", "unlinkat")):  # tmp-path-literal: allow (detector: reads the system temp dir, never writes it)
            if "= -1" not in line:
                tmp_writes.append(line.strip()[:300])
    return {"tmp_writes": tmp_writes, "lockfile_commit_path_opens": lockfile_opens}


def main() -> int:
    carrier, scratch = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    files = sys.argv[3:]
    out_dir = scratch / "tests_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for label, devnull in (("devnull", True), ("host_global", False)):
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["TMPDIR"] = str(out_dir)
        if devnull:
            env["GIT_CONFIG_GLOBAL"] = os.devnull
        else:
            env.pop("GIT_CONFIG_GLOBAL", None)
        before = tmp_lockfiles()
        t0 = time.time()
        time.sleep(1.1)
        trace = out_dir / f"strace_{label}.log"
        cmd = ["timeout", "900", "strace", "-f", "-qq", "-e", "signal=none", "-e", "trace=open,openat,creat,mkdir,mkdirat,rename,renameat,renameat2,unlink,unlinkat", "-o", str(trace),
               "/opt/miniforge3/bin/conda", "run", "--no-capture-output", "-n", "JuniperCanopy1", "python", "-m", "pytest", "-p", "no:cacheprovider", f"--basetemp={out_dir / ('bt_' + label)}", "-q", "-rA", "--timeout=120", *files]
        p = subprocess.run(cmd, cwd=carrier / "src", env=env, capture_output=True, text=True)
        log = out_dir / f"pytest_{label}.log"
        log.write_text(p.stdout + "\n--- stderr ---\n" + p.stderr)
        tail = [ln for ln in p.stdout.splitlines() if re.search(r"passed|failed|error|skipped", ln)][-3:]
        summary[label] = {
            "exit": p.returncode,
            "tail": tail,
            "tmp_lockfiles_before": before,
            "tmp_lockfiles_after": tmp_lockfiles(),
            "carrier_files_written": newer_than(carrier, t0),
            **analyse_trace(trace),
            "log": str(log),
        }
    (scratch / "tests_runs_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
