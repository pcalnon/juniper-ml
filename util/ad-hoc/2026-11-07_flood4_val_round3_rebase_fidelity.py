"""
Round-3 validation of the juniper-ml flood-4 docs carrier: rebase fidelity.

For each of the seven carrier files, diff the working tree (the frozen carrier
copy) against bbdeb758, classify every line the carrier removes (was it already
on 303ccc0b, the carrier's original base, or did main / the tests carrier add
it since?), and check that every line #2510, #2516, #2517 and #2518 added to
these files is still present, count-aware.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier, round-3 validation (session 7ceca543)
"""

import collections
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = "bbdeb75823c011e780058f20d4df902a79f436ba"
OLD_BASE = "303ccc0b"
FILES = [
    "CHANGELOG.md",
    "docs/REFERENCE.md",
    "docs/QUICK_START.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "juniper-config-tools/README.md",
    "juniper-service-core/README.md",
]
# (label, from, to): the commits whose additions to FILES must survive
PRS = [
    ("#2510", "4be0b0fb^", "4be0b0fb"),
    ("#2511", "58397dbb^", "58397dbb"),
    ("#2516", "147263ec^", "147263ec"),
    ("#2518", "a1ab41af^", "a1ab41af"),
    ("#2517", "a1ab41af", BASE),
]


def run(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout


def show(rev, path):
    try:
        return run("show", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return ""


def diff_lines(text, sign):
    out = []
    for line in text.splitlines():
        if line.startswith(sign * 3):
            continue
        if line.startswith(sign):
            out.append(line[1:])
    return out


def main():
    scratch = Path(sys.argv[1])
    scratch.mkdir(parents=True, exist_ok=True)
    report = {"removed": {}, "pr_presence": {}, "added_count": {}}
    for path in FILES:
        tag = path.replace("/", "_")
        d3 = run("diff", BASE, "--", path)
        d0 = run("diff", "-U0", BASE, "--", path)
        (scratch / f"diff_{tag}.txt").write_text(d3)
        (scratch / f"diff_u0_{tag}.txt").write_text(d0)
        old = collections.Counter(show(OLD_BASE, path).splitlines())
        removed = diff_lines(d0, "-")
        added = diff_lines(d0, "+")
        report["added_count"][path] = len(added)
        rows = []
        for line in removed:
            rows.append({"on_303ccc0b": old[line] > 0, "line": line[:400]})
        report["removed"][path] = rows
        carrier = collections.Counter((REPO / path).read_text().splitlines())
        for label, a, b in PRS:
            pd = run("diff", "-U0", a, b, "--", path)
            plus = diff_lines(pd, "+")
            if not plus:
                continue
            need = collections.Counter(plus)
            missing = []
            for line, n in need.items():
                if carrier[line] < n:
                    missing.append({"need": n, "have": carrier[line], "line": line[:400]})
            report["pr_presence"].setdefault(label, {})[path] = {"added": len(plus), "missing": missing}
    with open(scratch / "rebase_fidelity.json", "w") as fh:
        json.dump(report, fh, indent=1)
    for path, rows in report["removed"].items():
        new = [r for r in rows if not r["on_303ccc0b"]]
        print(f"{path}: +{report['added_count'][path]} -{len(rows)} (removed lines NOT on 303ccc0b: {len(new)})")
        for r in new:
            print("   NEW-ON-MAIN REMOVED:", r["line"][:220])
    for label, files in report["pr_presence"].items():
        for path, info in files.items():
            print(f"{label} {path}: added {info['added']}, missing {len(info['missing'])}")
            for m in info["missing"]:
                print("   MISSING:", m)


if __name__ == "__main__":
    main()
