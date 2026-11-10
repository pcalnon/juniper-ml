#!/usr/bin/env python3
"""
List every SARIF upload step in the Juniper repos' workflows on origin/main, with its continue-on-error value and line.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — investigation (flood-3 record, ninth update)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§4: cascor `ci.yml:659`, canopy's Bandit SARIF)

Why this exists
---------------
The owner ruled on 2026-10-29 that juniper-cascor's Bandit SARIF upload fails on pull requests
(``continue-on-error: ${{ github.event_name != 'pull_request' }}``). Whether the other repositories
follow is the owner's next call, and this lists where the old ``continue-on-error: true`` still stands.
It reads each sibling's ``origin/main`` after a fetch, never a working tree.

    python3 -I util/ad-hoc/2026-10-29_sarif_upload_continue_on_error_census.py <Juniper ecosystem root>

One line per upload step: repo, workflow, the ``uses:`` line, and the ``continue-on-error`` line and value
(``absent`` when the step has none, so a failed upload fails the job). The whole step is scanned, from its
``- `` line to the next step's. Exit 0 always; it reports.

Run of record (2026-10-30, ``origin/main``): ``continue-on-error: true`` at juniper-data ``ci.yml:606``,
juniper-canopy ``:581``, juniper-data-client ``:611``, juniper-cascor-client ``:529`` and juniper-cascor-worker
``:590``; juniper-cascor ``:664`` reads ``${{ github.event_name != 'pull_request' }}`` (juniper-cascor#735);
juniper-deploy's ``security-scan.yml:55`` has none. juniper-ml and juniper-recurrence upload no SARIF.
"""

import subprocess
import sys

REPOS = ["juniper-ml", "juniper-data", "juniper-canopy", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-deploy", "juniper-recurrence"]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = sys.argv[1].rstrip("/")
    for repo in REPOS:
        path = f"{root}/{repo}"
        subprocess.run(["git", "-C", path, "fetch", "origin", "--quiet"], check=False)
        names = subprocess.run(["git", "-C", path, "ls-tree", "--name-only", "origin/main", ".github/workflows/"], capture_output=True, text=True).stdout.split()
        for name in names:
            if not name.endswith((".yml", ".yaml")):
                continue
            lines = subprocess.run(["git", "-C", path, "show", f"origin/main:{name}"], capture_output=True, text=True).stdout.splitlines()
            for i, line in enumerate(lines):
                if "upload-sarif" not in line or "uses:" not in line:
                    continue
                # The step runs from its "- " line (this one, or the nearest one above) to the next step's.
                start = i
                while start > 0 and not lines[start].lstrip().startswith("- "):
                    start -= 1
                end = i + 1
                while end < len(lines) and not lines[end].lstrip().startswith("- "):
                    end += 1
                coe, coe_line = "absent", "-"
                for j in range(start, end):
                    # The YAML key only: a comment that mentions continue-on-error is not the setting.
                    if lines[j].strip().startswith("continue-on-error:"):
                        coe, coe_line = lines[j].split(":", 1)[1].strip(), str(j + 1)
                        break
                print(f"{repo}\t{name}\tuses:{i + 1}\tcontinue-on-error:{coe_line}={coe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
