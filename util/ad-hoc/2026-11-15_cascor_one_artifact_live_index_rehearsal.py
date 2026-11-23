#!/usr/bin/env python3
"""Run the one-artifact JSON check, as a publish.yml carries it, against the LIVE indexes with juniper-cascor 0.14.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (evidence for the juniper-cascor one-artifact publish pull request)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (writes the publish.yml this reads);
         util/ad-hoc/2026-11-15_verify_cascor_0_14_0_canopy_0_10_0_published.py (measured the two builds' sha256)

Why
---
The test file rehearses the check against a stand-in index; this runs the same Python against the real JSON API, so
the response shape it parses is the one the indexes serve. juniper-cascor 0.14.0 went out under the old workflow, as
two builds: TestPyPI holds one, PyPI the other. Three cases, each a ``SHA256SUMS`` written into a scratch workspace:

1. TestPyPI's own files, checked on TestPyPI: must PASS (the check reads the live response correctly);
2. the same files, checked on PyPI: must FAIL at once (the post-upload PyPI check would have flagged 0.14.0);
3. PyPI's files (the second build), checked on TestPyPI: must FAIL at once (the pre-upload TestPyPI check in the PyPI
   job would have refused to publish them).

Read-only: three or so GETs of public JSON; nothing is uploaded. The workspace goes under ``--scratch``.

    python3 -I util/ad-hoc/2026-11-15_cascor_one_artifact_live_index_rehearsal.py --publish-yml <publish.yml> --scratch <dir>

Exit status: 0 when all three cases come out as stated; 1 otherwise; 2 when the step cannot be found.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 -- runs the extracted step with a fixed argv
import sys
from pathlib import Path

import yaml

STEP = "Verify TestPyPI serves exactly these files"
WHEEL = "juniper_cascor-0.14.0-py3-none-any.whl"
SDIST = "juniper_cascor-0.14.0.tar.gz"
#: The sha256 each index serves for 0.14.0 (read 2026-11-15 from /pypi/juniper-cascor/0.14.0/json on each).
TESTPYPI_FILES = {WHEEL: "c5c9a5dc299c3b940a374f223e43cdc9e6df08b007e201f089b07cca913567cf", SDIST: "92f0b146cd1b1e20e11bca917a755d7b2d07143a7b3485fb4469d018e2986295"}
PYPI_FILES = {WHEEL: "b70f3d39e9187ccb7f424ccfea51fd06302da6daf872b9c7b4094831fd22bdf7", SDIST: "79cc0da301c1de0255e2e54ee6e739799bd33f6d6c0080f7a553e12dada523f5"}
CASES = (
    ("TestPyPI's files on TestPyPI", TESTPYPI_FILES, "https://test.pypi.org", 0),
    ("TestPyPI's files on PyPI (the post-upload PyPI check)", TESTPYPI_FILES, "https://pypi.org", 1),
    ("PyPI's rebuild on TestPyPI (the pre-upload check in the PyPI job)", PYPI_FILES, "https://test.pypi.org", 1),
)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--publish-yml", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    args = parser.parse_args(argv)
    doc = yaml.safe_load(args.publish_yml.read_text(encoding="utf-8"))
    steps = [s for s in doc["jobs"]["testpypi"]["steps"] if s.get("name") == STEP]
    if len(steps) != 1:
        print(f"REFUSED: {len(steps)} steps named {STEP!r}")
        return 2
    script = args.scratch / "index_check.py"
    args.scratch.mkdir(parents=True, exist_ok=True)
    script.write_text(steps[0]["run"], encoding="utf-8")
    wrong = 0
    for n, (label, files, index, want) in enumerate(CASES, 1):
        workspace = args.scratch / f"case{n}"
        workspace.mkdir(exist_ok=True)
        (workspace / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(files.items())), encoding="utf-8")
        env = {"PATH": "/usr/bin:/bin", "GITHUB_WORKSPACE": str(workspace), "PUBLISH_PACKAGE": "juniper-cascor", "INDEX_URL": index, "HASH_CHECK_ATTEMPTS": "3", "HASH_CHECK_INTERVAL": "5"}
        proc = subprocess.run([sys.executable, "-I", str(script)], env=env, capture_output=True, text=True, timeout=300, check=False)  # nosec B603 -- fixed argv
        verdict = "as stated" if proc.returncode == want else "WRONG"
        wrong += proc.returncode != want
        print(f"case {n}: {label}: exit {proc.returncode} (want {want}) -- {verdict}")
        for line in proc.stdout.splitlines():
            print(f"    {line}")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
