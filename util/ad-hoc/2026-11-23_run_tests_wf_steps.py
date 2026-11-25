"""
Print the run steps of the named workflows: the runner's design survey.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: print the non-comment run-steps of the named workflows (design survey only).
"""
import pathlib
import sys

import yaml

for name in sys.argv[1:]:
    p = pathlib.Path(".github/workflows") / f"{name}.yml"
    d = yaml.safe_load(p.read_text())
    print(f"=== {name}")
    for jn, job in d["jobs"].items():
        wd = (job.get("defaults") or {}).get("run", {}).get("working-directory")
        mx = ((job.get("strategy") or {}).get("matrix") or {}).get("python-version")
        print(f"  job {jn} (wd={wd}) matrix={mx}")
        for s in job.get("steps") or []:
            if "run" not in s or "Report the informational" in (s.get("name") or ""):
                continue
            body = [ln for ln in s["run"].splitlines() if not ln.strip().startswith("#")]
            print(f"    - {s.get('name')}: wd={s.get('working-directory')}")
            for ln in body:
                print("        " + ln)
