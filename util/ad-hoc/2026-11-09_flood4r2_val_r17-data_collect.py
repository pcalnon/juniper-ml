"""
Collect juniper-data's CI test lanes (collect-only) for a tree and compare two trees' selections.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, Cursor flood-4 round 2)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 ("data: 44 unrun tests"); independent validation of the r17-data-unit-marks carrier

Subcommands:
  collect  --tree T --python P --out F   collect every CI lane in tree T with interpreter P, write JSON F
  compare  --before F1 --after F2 --out F3   per-lane deltas, the no-lane census, and the 44's lane membership
  marks    --tree T --out F               AST census of module-level ``pytestmark`` in tests/unit/test_*.py

The lanes are the pytest invocations of juniper-data's workflows at 272ff615: ci.yml unit-tests,
integration-tests, the security job's gitleaks self-test, slow-tests, and scheduled-tests.yml. Each is
collected with ``--collect-only`` and the workflow's own marker expression and path. pytest's addopts
already carry ``-q``, so no extra ``-q`` is passed (a second one prints per-file counts, not node ids).
"""

import argparse
import ast
import json
import os
import re
import subprocess  # nosec B404 - runs pytest --collect-only with a caller-chosen interpreter
import sys
from collections import Counter
from pathlib import Path

LANES = {
    "unit": ["-m", "unit and not slow", "juniper_data/tests/unit"],
    "integration": ["-m", "integration and not slow", "juniper_data/tests/integration"],
    "gitleaks": ["juniper_data/tests/unit/test_gitleaks_config.py"],
    "slow": ["-m", "slow"],
    "scheduled": ["-m", "slow or integration"],
    "all": [],
    "unit_dir": ["juniper_data/tests/unit"],
}
CI_LANES = ("unit", "integration", "gitleaks", "slow", "scheduled")
SUMMARY_RE = re.compile(r"^(\d+)(?:/(\d+))? tests? collected(?: \((\d+) deselected\))?")
NODE_RE = re.compile(r"^juniper_data/\S+::\S")


def collect_lane(tree: Path, python: str, extra: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [python, "-m", "pytest", "--collect-only", "-p", "no:cacheprovider", *extra]
    proc = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True, check=False)  # nosec B603
    nodes = [line.strip() for line in proc.stdout.splitlines() if NODE_RE.match(line.strip())]
    summary = ""
    for line in proc.stdout.splitlines():
        if SUMMARY_RE.match(line.strip()):
            summary = line.strip()
    return {"cmd": cmd[1:], "rc": proc.returncode, "summary": summary, "nodes": nodes, "stderr_tail": proc.stderr[-800:]}


def cmd_collect(args: argparse.Namespace) -> int:
    tree = Path(args.tree).resolve()
    out: dict = {"tree": str(tree), "python": args.python, "lanes": {}}
    probe = subprocess.run(  # nosec B603
        [args.python, "-c", "import sys, juniper_data, pytest; print(sys.version.split()[0]); print(juniper_data.__file__); print(pytest.__version__)"],
        cwd=tree,
        capture_output=True,
        text=True,
        check=False,
    )
    out["probe"] = probe.stdout.strip().splitlines()
    for name, extra in LANES.items():
        res = collect_lane(tree, args.python, extra)
        out["lanes"][name] = res
        print(f"{name:12s} rc={res['rc']} nodes={len(res['nodes'])} summary={res['summary']!r}")
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


def _file_of(node: str) -> str:
    return node.split("::", 1)[0]


def _class_of(node: str) -> str:
    parts = node.split("::")
    return parts[1] if len(parts) > 2 else "<module>"


def cmd_compare(args: argparse.Namespace) -> int:
    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    after = json.loads(Path(args.after).read_text(encoding="utf-8"))
    report: dict = {"lanes": {}}
    for name in LANES:
        b = set(before["lanes"][name]["nodes"])
        a = set(after["lanes"][name]["nodes"])
        report["lanes"][name] = {
            "before": len(b),
            "after": len(a),
            "added": sorted(a - b),
            "removed": sorted(b - a),
            "summary_before": before["lanes"][name]["summary"],
            "summary_after": after["lanes"][name]["summary"],
        }
        print(f"{name:12s} before={len(b)} after={len(a)} added={len(a - b)} removed={len(b - a)}")
    added_unit = report["lanes"]["unit"]["added"]
    sec = "juniper_data/tests/unit/test_security.py"
    all_sec = {n for n in after["lanes"]["unit_dir"]["nodes"] if _file_of(n) == sec}
    before_sec_unit = {n for n in before["lanes"]["unit"]["nodes"] if _file_of(n) == sec}
    report["security_file"] = {
        "collected_in_unit_dir": len(all_sec),
        "unit_lane_before": len(before_sec_unit),
        "unit_lane_after": len({n for n in after["lanes"]["unit"]["nodes"] if _file_of(n) == sec}),
        "previously_deselected": len(all_sec - before_sec_unit),
        "added_equals_previously_deselected": set(added_unit) == (all_sec - before_sec_unit),
        "added_all_in_security_file": all(_file_of(n) == sec for n in added_unit),
        "added_by_class": dict(Counter(_class_of(n) for n in added_unit)),
    }
    # Which OTHER lanes now (after) contain any of the 44 -- they should be in the unit lane only.
    report["added_also_in"] = {name: len(set(added_unit) & set(after["lanes"][name]["nodes"])) for name in CI_LANES if name != "unit"}
    # No-lane census on the AFTER tree: every collected test not selected by any CI lane.
    for tag, data in (("before", before), ("after", after)):
        union: set = set()
        for name in CI_LANES:
            union |= set(data["lanes"][name]["nodes"])
        everything = set(data["lanes"]["all"]["nodes"])
        no_lane = sorted(everything - union)
        per_file = Counter(_file_of(n) for n in no_lane)
        collected_per_file = Counter(_file_of(n) for n in everything)
        report[f"no_lane_{tag}"] = {
            "count": len(no_lane),
            "files": len(per_file),
            "per_file": {f: f"{c}/{collected_per_file[f]}" for f, c in sorted(per_file.items())},
            "in_union_not_in_all": len(union - everything),
        }
        print(f"no-lane ({tag}): {len(no_lane)} tests in {len(per_file)} files; lane nodes outside 'all': {len(union - everything)}")
    print(json.dumps(report["security_file"], indent=1))
    print("44 also in:", report["added_also_in"])
    print(json.dumps(report["no_lane_after"], indent=1))
    Path(args.out).write_text(json.dumps(report, indent=1), encoding="utf-8")
    return 0


def _mark_value(node: ast.expr) -> str:
    return ast.unparse(node)


def cmd_marks(args: argparse.Namespace) -> int:
    unit_dir = Path(args.tree).resolve() / "juniper_data" / "tests" / "unit"
    modules = sorted(p for p in unit_dir.glob("test_*.py"))
    with_mark: dict[str, str] = {}
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for stmt in tree.body:
            targets: list[ast.expr] = []
            value = None
            if isinstance(stmt, ast.Assign):
                targets, value = stmt.targets, stmt.value
            elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                targets, value = [stmt.target], stmt.value
            if value is not None and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in targets):
                with_mark[path.name] = _mark_value(value)
    kinds = Counter(with_mark.values())
    out = {"unit_modules": len(modules), "with_module_pytestmark": len(with_mark), "values": dict(kinds), "modules": with_mark}
    print(f"unit modules (tests/unit/test_*.py): {len(modules)}; with module-level pytestmark: {len(with_mark)}")
    for value, count in kinds.most_common():
        print(f"  {count:3d}  {value}")
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("collect")
    p.add_argument("--tree", required=True)
    p.add_argument("--python", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("compare")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("marks")
    p.add_argument("--tree", required=True)
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    handlers = {"collect": cmd_collect, "compare": cmd_compare, "marks": cmd_marks}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
