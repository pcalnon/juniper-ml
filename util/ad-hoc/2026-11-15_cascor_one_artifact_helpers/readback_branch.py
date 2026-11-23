"""Read back a pushed branch: each uploaded file's blob sha must equal the local file's, and the commit must be verified.

Usage: python3 -I readback_branch.py ARGS.json

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def gh(path: str) -> dict:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec B324 -- git's object id, not security


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    repo, branch, tree = spec["repo"], spec["branch"], Path(spec["tree"])
    head = gh(f"repos/pcalnon/{repo}/commits/{branch}")
    verification = head["commit"]["verification"]
    print(f"head {head['sha']} verified={verification['verified']} reason={verification['reason']} parents={[p['sha'][:8] for p in head['parents']]}")
    print(f"message last lines: {head['commit']['message'].splitlines()[-2:]}")
    bad = 0 if verification["verified"] else 1
    for rel in spec["paths"]:
        remote = gh(f"repos/pcalnon/{repo}/contents/{rel}?ref={branch}")["sha"]
        local = blob_sha((tree / rel).read_bytes())
        same = remote == local
        bad += not same
        print(f"{'same' if same else 'DIFFERENT'} {remote[:12]} {rel}")
    compare = gh(f"repos/pcalnon/{repo}/compare/{head['parents'][0]['sha']}...{head['sha']}")
    names = sorted(f["filename"] for f in compare["files"])
    print(f"commit touches {len(names)} file(s); expected {len(spec['paths'])}; extra={sorted(set(names) - set(spec['paths']))} missing={sorted(set(spec['paths']) - set(names))}")
    bad += set(names) != set(spec["paths"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
