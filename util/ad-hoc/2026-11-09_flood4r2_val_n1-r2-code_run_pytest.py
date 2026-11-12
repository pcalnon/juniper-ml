"""
Run one pytest invocation in a juniper-cascor validator worktree, logged, with JUNIPER_CASCOR_LOG_DIR unset.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, n1 r2 code lens)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 11, cascor paused-fit wedge)

Usage: python3 <this> <label> <worktree> <out-dir> [pytest args ...]

Runs ``JuniperCascor1``'s python ``-m pytest <args>`` with cwd=<worktree>. The environment is the
caller's minus ``JUNIPER_CASCOR_LOG_DIR`` (cascor's AGENTS.md: six tests assert the unset
fallback), with the validator's plugin directory prepended to PYTHONPATH and
N1R2_PROVENANCE_OUT pointed at <out-dir>/provenance_<label>.txt. TMPDIR is left exactly as given.
Output goes to <out-dir>/<label>.log with the command, start/end UTC stamps and the exit status.
No environment variable is printed.
"""

import datetime
import os
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
PLUGINS = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n1-r2-code-lens" / "plugins"


def _utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    label, worktree, out_dir = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    args = sys.argv[4:]
    # Leading ``--set N1R2_NAME=VALUE`` options set validator-plugin variables (N1R2_* only).
    extra = {}
    while len(args) >= 2 and args[0] == "--set" and args[1].startswith("N1R2_") and "=" in args[1]:
        name, value = args[1].split("=", 1)
        extra[name] = value
        args = args[2:]
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel in ("logs", "src/logs", "reports/junit", "src/tests/reports"):
        (worktree / rel).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONPATH"] = os.pathsep.join([str(PLUGINS)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["N1R2_PROVENANCE_OUT"] = str(out_dir / f"provenance_{label}.txt")
    env.update(extra)
    cmd = [PYTHON, "-m", "pytest", *args]
    log_path = out_dir / f"{label}.log"
    with open(log_path, "w") as log:
        log.write(f"$ (cwd={worktree}) {' '.join(cmd)}\n# start {_utc()}; JUNIPER_CASCOR_LOG_DIR unset; TMPDIR length {len(env.get('TMPDIR', ''))} (untouched)\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=worktree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        log.write(f"\n# end {_utc()} exit {proc.returncode}\n")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
