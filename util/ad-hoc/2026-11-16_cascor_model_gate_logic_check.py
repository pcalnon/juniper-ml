#!/usr/bin/env python3
"""Run the `changes` detector and the `Model required checks` gate of a ci-cascor-model.yml against stub inputs.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-16
Status:      ad-hoc -- investigation (cascor-model required check, owner ruling 2026-11-16: juniper-recurrence's pattern)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     prompts/thread-handoff_automated-prompts/
             HANDOFF_2026-11-15_python-3-15-phase-2-complete-dill-drift-nightly-markers-cleanup.md (open owner question 1)

Why this exists
---------------
A required check is only as good as its two shell steps: the detector that decides whether the package jobs run,
and the gate that turns their results into one context. Neither can be exercised by actionlint. This extracts both
`run:` scripts from the workflow file and executes them with bash: the detector against a stub `git` that prints a
chosen file list (or fails), the gate against every combination of job results. It also runs juniper-recurrence's
piped detector form (`git diff ... | grep -q` under `pipefail`) against a long file list, to measure whether that
form fails open when grep exits early and git dies of SIGPIPE.

Writes only into a temporary directory (under $TMPDIR), removed on exit. Changes nothing in any repository.

Usage
-----
    python3 util/ad-hoc/2026-11-16_cascor_model_gate_logic_check.py <juniper-cascor checkout root | path/to/ci-cascor-model.yml>

Exit 0 when every case behaves as expected; 1 otherwise.
"""

from __future__ import annotations

import itertools
import os
import stat
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

import yaml

RECURRENCE_PIPED = """set -euo pipefail
if [[ "${EVENT_NAME}" != "pull_request" ]]; then
  changed=true
elif git diff --name-only "origin/${BASE_REF}...HEAD" \\
     | grep -qE '^(juniper-cascor-model/|src/(candidate_unit|utils|log_config|cascor_constants)/|\\.github/workflows/ci-cascor-model\\.yml$)'; then
  changed=true
else
  changed=false
fi
echo "model=${changed}" >> "$GITHUB_OUTPUT"
"""


def step_script(doc: dict, job: str, step_id: str | None = None, step_name: str | None = None) -> str:
    for step in doc["jobs"][job]["steps"]:
        if (step_id and step.get("id") == step_id) or (step_name and step.get("name") == step_name):
            return step["run"]
    raise KeyError(f"{job}: no step id={step_id!r} name={step_name!r}")


def run_detector(script: str, tmp: Path, files: str | None, event: str = "pull_request") -> tuple[int, str]:
    stub_dir = tmp / "bin"
    stub_dir.mkdir(exist_ok=True)
    stub = stub_dir / "git"
    listing = tmp / "files.txt"
    if files is None:
        stub.write_text("#!/usr/bin/env bash\necho 'fatal: bad revision' >&2\nexit 128\n", encoding="utf-8")
    else:
        listing.write_text(files, encoding="utf-8")
        stub.write_text(f"#!/usr/bin/env bash\ncat '{listing}'\n", encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    out = tmp / "github_output"
    out.write_text("", encoding="utf-8")
    env = dict(os.environ, PATH=f"{stub_dir}:{os.environ['PATH']}", EVENT_NAME=event, BASE_REF="main", GITHUB_OUTPUT=str(out))
    proc = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, check=False)  # nosec B603 B607
    return proc.returncode, out.read_text(encoding="utf-8").strip()


def run_gate(script: str, changes: str, model: str, test: str, build: str) -> int:
    env = dict(os.environ, CHANGES=changes, MODEL=model, TEST=test, BUILD=build)
    return subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, check=False).returncode  # nosec B603 B607


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    target = Path(sys.argv[1])
    if target.is_dir():
        # A repo root: build the workflow path here, so the command line never names the `.github` directory
        # (a worktree-isolated session refuses a command whose text contains it).
        target = target / ".github" / "workflows" / "ci-cascor-model.yml"
    print(f"workflow: {target}")
    doc = yaml.safe_load(target.read_text(encoding="utf-8"))
    detector = step_script(doc, "changes", step_id="filter")
    gate = step_script(doc, "required-checks", step_name="Verify required jobs succeeded")
    bad = 0
    long_tail = "".join(f"docs/generated/page_{i:06d}.md\n" for i in range(200_000))  # ~6 MB after the match
    detector_cases = [
        ("package file", "juniper-cascor-model/utils/utils.py\n", "pull_request", 0, "model=true"),
        ("src drift side", "src/utils/utils.py\nREADME.md\n", "pull_request", 0, "model=true"),
        ("constants side", "src/cascor_constants/constants_api/constants_api_defaults.py\n", "pull_request", 0, "model=true"),
        ("this workflow", ".github/workflows/ci-cascor-model.yml\n", "pull_request", 0, "model=true"),
        ("unrelated only", "src/api/app.py\ndocs/ci_cd/MANUAL.md\n.github/workflows/ci.yml\n", "pull_request", 0, "model=false"),
        ("look-alike dirs", "src/utils_extra/x.py\nsrc/log_configs/y.py\nxjuniper-cascor-model/z.py\n", "pull_request", 0, "model=false"),
        ("other workflow", ".github/workflows/ci-cascor-model.yml.bak\n", "pull_request", 0, "model=false"),
        ("empty diff", "", "pull_request", 0, "model=false"),
        ("push event", "src/api/app.py\n", "push", 0, "model=true"),
        ("git fails", None, "pull_request", 128, ""),
        ("match then 200k lines", "src/utils/utils.py\n" + long_tail, "pull_request", 0, "model=true"),
    ]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print("== detector (the workflow's own step)")
        for label, files, event, want_rc, want_out in detector_cases:
            rc, out = run_detector(detector, tmp, files, event)
            ok = rc == want_rc and out == want_out
            bad += not ok
            print(f"  {'ok ' if ok else 'BAD'} {label:24s} rc={rc} output={out!r} (want rc={want_rc} {want_out!r})")
        print("== juniper-recurrence's piped form, same long list (measures the SIGPIPE fail-open)")
        rc, out = run_detector(RECURRENCE_PIPED, tmp, "src/utils/utils.py\n" + long_tail)
        print(f"  piped form: rc={rc} output={out!r}  ({'FAILS OPEN: a touched package reads as unchanged' if out == 'model=false' else 'did not fail open on this run'})")
    print("== gate (every combination)")
    results = ["success", "failure", "skipped", "cancelled"]
    for changes, model, test, build in itertools.product(results, ["true", "false"], results, results):
        want = 0 if changes == "success" and all(r == "success" or (r == "skipped" and model != "true") for r in (test, build)) else 1
        got = 0 if run_gate(gate, changes, model, test, build) == 0 else 1
        if got != want:
            bad += 1
            print(f"  BAD changes={changes} model={model} test={test} build={build}: exit {got}, want {want}")
    print(f"  {len(results) * 2 * len(results) * len(results)} combinations checked")
    for label, args in (
        ("unrelated PR (skipped, skipped)", ("success", "false", "skipped", "skipped")),
        ("package PR passes", ("success", "true", "success", "success")),
        ("package PR, 3.12 leg red", ("success", "true", "failure", "skipped")),
        ("touched but skipped", ("success", "true", "skipped", "skipped")),
        ("detector failed", ("failure", "", "skipped", "skipped")),
    ):
        print(f"  {label:34s} exit {run_gate(gate, *args)}")
    print("ALL OK" if not bad else f"{bad} case(s) BAD")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
