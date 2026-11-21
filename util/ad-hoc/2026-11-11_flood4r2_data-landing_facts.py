#!/usr/bin/env python3
"""
Re-derive, on juniper-data's current main and the three stage trees, the facts the carriers' PR texts cite.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (the texts were validated on 4f04fc8d; every number and line reference is re-read on M0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-fix/{data-tests,data-docs,data-code}/pr_body.txt; tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt

Usage:
    python3 <this> --repo <juniper-data primary> --base <carrier base sha> --m0 <origin/main sha>
                   --stage1 <worktree> --stage2 <worktree> --stage3 <worktree> --out <facts.json>

Facts:
  - how many test files declare a module-level ``pytestmark`` at the carrier base, at M0 and in each stage tree;
  - whether each file a text cites by line is byte-identical at the carrier base and at M0 (so the line numbers the
    validators checked still hold), and for the one that is not (publish-image.yml) whether each cited range is;
  - the text now standing on each cited line, in the tree the citation is about;
  - the action pin the docs carrier's metadata-action claims were checked against.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only git queries
import sys
from pathlib import Path

PYTESTMARK = re.compile(r"^pytestmark\b", re.MULTILINE)
CITED_FILES = ("juniper_data/api/security.py", "juniper_data/api/middleware.py", ".github/workflows/publish-image.yml", ".github/workflows/publish.yml", "scripts/check_module_coverage.py", "juniper_data/tests/unit/test_middleware.py")
WORKFLOW_RANGES = {"369-374": (369, 374), "395-431": (395, 431), "434": (434, 434), "81-83": (81, 83), "320-322": (320, 322)}


def _git(repo: Path, *argv: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *argv], capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def _lines(text: str, first: int, last: int) -> list[str]:
    return text.split("\n")[first - 1 : last]


def _pytestmark_files(root: Path) -> list[str]:
    hits = []
    for path in sorted((root / "juniper_data" / "tests").rglob("test_*.py")):
        if PYTESTMARK.search(path.read_text(encoding="utf-8")):
            hits.append(str(path.relative_to(root)))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--m0", required=True)
    ap.add_argument("--stage1", type=Path, required=True)
    ap.add_argument("--stage2", type=Path, required=True)
    ap.add_argument("--stage3", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    facts: dict = {"base": args.base, "m0": args.m0}

    grep = {}
    for label, sha in (("base", args.base), ("m0", args.m0)):
        listed = _git(repo, "grep", "-l", "-E", "^pytestmark", sha, "--", "juniper_data/tests").splitlines()
        grep[label] = {"count": len(listed), "files": [line.split(":", 1)[1] for line in listed]}
    facts["pytestmark_files"] = {
        "at_base": grep["base"]["count"],
        "at_m0": grep["m0"]["count"],
        "added_on_main_since_base": sorted(set(grep["m0"]["files"]) - set(grep["base"]["files"])),
        "removed_on_main_since_base": sorted(set(grep["base"]["files"]) - set(grep["m0"]["files"])),
    }
    for label, wt in (("stage1", args.stage1), ("stage2", args.stage2), ("stage3", args.stage3)):
        files = _pytestmark_files(wt.resolve())
        facts["pytestmark_files"][label] = {"count": len(files), "beyond_m0": sorted(set(files) - set(grep["m0"]["files"]))}

    blobs = {}
    for path in CITED_FILES:
        at_base = _git(repo, "rev-parse", f"{args.base}:{path}").strip()
        at_m0 = _git(repo, "rev-parse", f"{args.m0}:{path}").strip()
        blobs[path] = {"base": at_base, "m0": at_m0, "identical": at_base == at_m0}
    facts["cited_files_base_vs_m0"] = blobs

    wf = ".github/workflows/publish-image.yml"
    base_wf, m0_wf = _git(repo, "show", f"{args.base}:{wf}"), _git(repo, "show", f"{args.m0}:{wf}")
    facts["publish_image_cited_ranges"] = {name: {"identical_at_base_and_m0": _lines(base_wf, a, b) == _lines(m0_wf, a, b), "first_line_at_m0": _lines(m0_wf, a, a)[0].strip()} for name, (a, b) in WORKFLOW_RANGES.items()}
    facts["publish_image_line_count"] = {"base": base_wf.count("\n"), "m0": m0_wf.count("\n")}
    facts["metadata_action_pins_at_m0"] = sorted({line.strip() for line in m0_wf.splitlines() if "docker/metadata-action@" in line})

    m0_security = _git(repo, "show", f"{args.m0}:juniper_data/api/security.py")
    facts["security_py_at_m0"] = {str(n): _lines(m0_security, n, n)[0].strip() for n in (250, 254, 427)}
    stage3 = args.stage3.resolve()
    s3_security = (stage3 / "juniper_data/api/security.py").read_text(encoding="utf-8")
    s3_middleware = (stage3 / "juniper_data/api/middleware.py").read_text(encoding="utf-8")
    facts["stage3_cited_lines"] = {
        "security.py:327": _lines(s3_security, 327, 327)[0].strip(),
        "security.py:328": _lines(s3_security, 328, 328)[0].strip(),
        "security.py:243": _lines(s3_security, 243, 243)[0].strip(),
        "security.py:458": _lines(s3_security, 458, 458)[0].strip(),
        "middleware.py:233": _lines(s3_middleware, 233, 233)[0].strip(),
        "middleware.py:121": _lines(s3_middleware, 121, 121)[0].strip(),
        "middleware.py:122": _lines(s3_middleware, 122, 122)[0].strip(),
    }
    coverage_script = _git(repo, "show", f"{args.m0}:scripts/check_module_coverage.py")
    facts["check_module_coverage_128_132_at_m0"] = [line.rstrip() for line in _lines(coverage_script, 128, 132)]
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(facts, fh, indent=1)
        fh.write("\n")
    print(json.dumps(facts, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
