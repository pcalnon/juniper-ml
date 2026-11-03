#!/usr/bin/env python3
"""
Report which Juniper repositories hold a CODECOV_TOKEN secret, in the Actions and the Dependabot stores.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — investigation (flood-3 record, ninth update)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§4, the Codecov row)

Why this exists
---------------
The owner added ``CODECOV_TOKEN`` "to all repos via the GitHub GUI" on 2026-10-29. A Dependabot-triggered
run reads the Dependabot store, not the Actions one, so the two are reported separately. ``gh secret list``
returns names and update times only; a secret's value is never readable, and this prints none.

    python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py

One line per repository: ``actions=<updatedAt or ->`` and ``dependabot=<updatedAt or ->``. Exit 0 always.
Run of record (2026-10-29): all nine Actions stores held it (updated 22:08-22:16Z); no Dependabot store did.
"""

import json
import subprocess
import sys

REPOS = ["juniper-ml", "juniper-data", "juniper-canopy", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-deploy", "juniper-recurrence"]


def main() -> int:
    for repo in REPOS:
        row = [repo]
        for app in ("actions", "dependabot"):
            out = subprocess.run(["gh", "secret", "list", "--repo", f"pcalnon/{repo}", "--app", app, "--json", "name,updatedAt"], capture_output=True, text=True)
            if out.returncode != 0:
                row.append(f"{app}=ERROR({out.stderr.strip()[:60]})")
                continue
            names = dict()
            for secret in json.loads(out.stdout):
                names[secret["name"]] = secret["updatedAt"]
            row.append(f"{app}={names.get('CODECOV_TOKEN', '-')}")
        print("\t".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
