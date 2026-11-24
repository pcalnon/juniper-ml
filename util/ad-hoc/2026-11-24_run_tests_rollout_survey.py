#!/usr/bin/env python3
"""
Survey each active Juniper repo's CI test jobs and local test wrappers: the input to rolling util/run_tests.py out.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — investigation (the handoff's cross-repo rollout section)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629 (util/run_tests.py); its follow-up PRs and handoff of 2026-11-24

Read-only, and plain file reads only: it runs no git command in a sibling repo, so it reads each sibling's PRIMARY
checkout as it is on disk, which can lag that repo's main. Re-survey from the repo's own ``origin/main`` before
building on it.

For each repo it prints:

* every workflow job that runs tests: its name, Python matrix, working directory, and each ``run:`` line that
  invokes pytest, unittest, coverage, make, tox, nox or a bash test script;
* the local wrappers present (``util/run_coverage.bash``, ``util/run_tests.*``, ``scripts/*test*``, Makefile test
  targets, ``tox.ini``, ``noxfile.py``, cascor's ``src/tests/scripts/run_tests.bash``);
* its recipe in juniper-ml's ``conf/python_versions.yaml``.

Usage: ``python3 util/ad-hoc/2026-11-24_run_tests_rollout_survey.py [--out FILE]``.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - one git call, in this checkout only
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REPOS = ["juniper-cascor", "juniper-data", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy", "juniper-deploy", "juniper-recurrence", "juniper-harcot"]
TEST_WORDS = re.compile(r"\b(pytest|unittest|coverage|make\s+\S*test|tox|nox|run_tests|run_coverage|test_[\w-]+\.bash)\b")
WRAPPER_GLOBS = ["util/run_coverage.bash", "util/run_tests*", "scripts/*test*", "src/tests/scripts/run_tests.bash", "tox.ini", "noxfile.py", "Makefile"]


def juniper_root() -> Path:
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    return Path(common).parent.parent


def run_lines(step: dict) -> list[str]:
    text = step.get("run") or ""
    return [line.strip() for line in str(text).splitlines() if line.strip() and not line.strip().startswith("#")]


def survey_workflows(repo: Path) -> list[str]:
    out: list[str] = []
    wf_dir = repo / ".github" / "workflows"
    for wf in sorted(wf_dir.glob("*.y*ml")) if wf_dir.is_dir() else []:
        try:
            data = yaml.safe_load(wf.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            out.append(f"  {wf.name}: unparsable ({exc.__class__.__name__})")
            continue
        for job_id, job in (data.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            hits = [line for step in job.get("steps") or [] if isinstance(step, dict) for line in run_lines(step) if TEST_WORDS.search(line)]
            if not hits:
                continue
            matrix = ((job.get("strategy") or {}).get("matrix") or {}) if isinstance(job.get("strategy"), dict) else {}
            versions = matrix.get("python-version") if isinstance(matrix, dict) else None
            wd = ((job.get("defaults") or {}).get("run") or {}).get("working-directory") if isinstance(job.get("defaults"), dict) else None
            out.append(f"  {wf.name} :: {job_id} ({job.get('name', '')})  python={versions}  wd={wd}")
            out.extend(f"      {line[:200]}" for line in hits[:8])
            if len(hits) > 8:
                out.append(f"      ... {len(hits) - 8} more")
    return out


def survey_wrappers(repo: Path) -> list[str]:
    found: list[str] = []
    for pattern in WRAPPER_GLOBS:
        for path in sorted(repo.glob(pattern)):
            if path.name == "Makefile":
                targets = sorted({m.group(1) for m in re.finditer(r"^([\w.-]*test[\w.-]*)\s*:", path.read_text(encoding="utf-8", errors="replace"), re.M)})
                if targets:
                    found.append(f"Makefile targets {', '.join(targets)}")
            elif path.is_file():
                found.append(path.relative_to(repo).as_posix())
    return found


def recipe(name: str) -> list[str]:
    config = yaml.safe_load((ROOT / "conf" / "python_versions.yaml").read_text(encoding="utf-8"))
    entry = (config.get("repos") or {}).get(name)
    if not entry:
        return ["  (no recipe)"]
    return [f"  test {key}: {value}" for key, value in (entry.get("test") or {}).items()]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--out", type=Path, help="also write the report here")
    args = parser.parse_args(argv)
    base = juniper_root()
    lines: list[str] = [f"Juniper root: {base}"]
    for name in REPOS:
        repo = base / name
        lines.append("")
        lines.append(f"=== {name}" + ("" if repo.is_dir() else "  (no checkout)"))
        if not repo.is_dir():
            continue
        lines.append(" CI test jobs:")
        lines.extend(survey_workflows(repo) or ["  (none found)"])
        lines.append(" local wrappers: " + ("; ".join(survey_wrappers(repo)) or "(none)"))
        lines.append(" python_versions.yaml recipe:")
        lines.extend(recipe(name))
    report = "\n".join(lines) + "\n"
    print(report, end="")
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
