"""Run the extracted record and dist-check steps on a real build, as the runner would, then `sha256sum --check` the result.

Usage: python3 -I run_record_and_verify.py WORKSPACE RECORD_SCRIPT VERIFY_SCRIPT

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    workspace, record, verify = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    env = {"PATH": "/usr/bin:/bin", "GITHUB_WORKSPACE": str(workspace), "PUBLISH_DIST_DIR": "dist"}
    for label, argv, cwd in (("record", ["python3", record], workspace), ("verify", ["python3", verify], workspace), ("sha256sum", ["sha256sum", "--check", "--strict", str(workspace / "SHA256SUMS")], workspace / "dist")):
        proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, check=False)
        print(f"== {label}: exit {proc.returncode}")
        print(proc.stdout.rstrip())
        if proc.stderr.strip():
            print(proc.stderr.rstrip())
        if proc.returncode != 0:
            return proc.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
