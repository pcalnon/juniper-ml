"""Extract every `shell: python3 {0}` run block from the given workflows into OUT_DIR, one file per step.

Usage: python3 -I extract_python_steps.py OUT_DIR WORKFLOW.yml [WORKFLOW.yml ...]
Prints one line per extracted step: <file> <workflow>:<job>:<step name> sha256=<digest of the run text>.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import hashlib
import pathlib
import re
import sys

import yaml


def main() -> int:
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for wf_path in sys.argv[2:]:
        doc = yaml.safe_load(pathlib.Path(wf_path).read_text(encoding="utf-8"))
        for job_id, job in (doc.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                if str(step.get("shell") or "").strip() != "python3 {0}":
                    continue
                count += 1
                slug = re.sub(r"[^a-z0-9]+", "-", f"{pathlib.Path(wf_path).stem}-{job_id}-{step.get('name')}".lower()).strip("-")
                target = out / f"{count:02d}-{slug}.py"
                target.write_text(step["run"], encoding="utf-8")
                digest = hashlib.sha256(step["run"].encode("utf-8")).hexdigest()[:16]
                print(f"{target.name} {pathlib.Path(wf_path).name}:{job_id}:{step.get('name')} sha256={digest}")
    print(f"{count} step(s) extracted")
    return 0 if count else 1


if __name__ == "__main__":
    sys.exit(main())
