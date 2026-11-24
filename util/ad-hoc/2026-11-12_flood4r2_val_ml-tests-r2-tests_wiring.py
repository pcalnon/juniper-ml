"""
Re-derive the wiring facts of the ml-tests carrier from the workflows and documents of a tree (check C and D).

For --tree (the landed tree) and --main (a clean worktree of the same main):
  * ci.yml's regression list (job `tests`, step "Run Python regression tests"): count, duplicates, where each of the
    new suites stands (index, the suite before and after it);
  * main-verify.yml's battery: which of ci.yml's suites it mirrors, in each tree, and the order of the shared ones;
  * docs/REFERENCE.md's ordered "Running every suite" list against ci.yml's order;
  * ci.yml's HOST_TOOLING_SUITES against tests/test_claude_agent_guard*.py on disk;
  * AGENTS.md's count line.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --tree <landed tree> --main <clean main worktree> --out <json>
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

LINE_RE = re.compile(r"^\s*python3 -m unittest -v (tests/test_[A-Za-z0-9_]+\.py)\s*$")
DOC_RE = re.compile(r"^\s*python3 -m unittest -v\s+(tests/test_[A-Za-z0-9_]+\.py)\s*$")


def step_suites(workflow_path, job, step_name):
    with open(workflow_path, encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    found = []
    for step in workflow["jobs"][job]["steps"]:
        if step.get("name") == step_name:
            for line in step["run"].splitlines():
                match = LINE_RE.match(line)
                if match:
                    found.append(match.group(1))
    return found


def every_job_suites(workflow_path):
    """Every `python3 -m unittest -v tests/...` line of every step of every job, as (job, step, suite)."""
    with open(workflow_path, encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    rows = []
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            for line in str(step.get("run", "")).splitlines():
                match = LINE_RE.match(line)
                if match:
                    rows.append((job_name, step.get("name"), match.group(1)))
    return rows


def doc_list(reference_path):
    """Suites in docs/REFERENCE.md's fenced blocks, in order, with the heading each stands under."""
    rows = []
    heading = None
    in_fence = False
    for line in Path(reference_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            heading = line.strip()
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            match = DOC_RE.match(line)
            if match:
                rows.append((heading, match.group(1)))
    return rows


def facts(tree):
    tree = Path(tree)
    ci = tree / ".github" / "workflows" / "ci.yml"
    mv = tree / ".github" / "workflows" / "main-verify.yml"
    ci_list = step_suites(ci, "tests", "Run Python regression tests")
    mv_rows = every_job_suites(mv)
    mv_list = [suite for _, _, suite in mv_rows]
    docs = doc_list(tree / "docs" / "REFERENCE.md")
    doc_suites = [suite for _, suite in docs]
    with open(ci, encoding="utf-8") as fh:
        host = yaml.safe_load(fh)["jobs"]["host-tooling-macos"]["env"]["HOST_TOOLING_SUITES"].split()
    guard_on_disk = sorted(path.stem[len("test_") :] for path in (tree / "tests").glob("test_claude_agent_guard*.py"))
    agents = [line for line in (tree / "AGENTS.md").read_text(encoding="utf-8").splitlines() if "full ordered list of" in line]
    on_disk = sorted("tests/" + path.name for path in (tree / "tests").glob("test_*.py"))
    return {
        "ci_list": ci_list,
        "ci_count": len(ci_list),
        "ci_duplicates": sorted({name for name in ci_list if ci_list.count(name) > 1}),
        "on_disk_count": len(on_disk),
        "on_disk_not_in_ci": sorted(set(on_disk) - set(ci_list)),
        "ci_not_on_disk": sorted(set(ci_list) - set(on_disk)),
        "main_verify_rows": mv_rows,
        "main_verify_count": len(mv_list),
        "main_verify_distinct": len(set(mv_list)),
        "main_verify_not_in_ci": sorted(set(mv_list) - set(ci_list)),
        "ci_not_in_main_verify": sorted(set(ci_list) - set(mv_list)),
        "main_verify_order_follows_ci": [s for s in ci_list if s in set(mv_list)] == list(dict.fromkeys(mv_list)),
        "doc_headings": sorted({heading for heading, _ in docs}),
        "doc_count": len(doc_suites),
        "doc_order_equals_ci": doc_suites == ci_list,
        "doc_minus_ci": sorted(set(doc_suites) - set(ci_list)),
        "ci_minus_doc": sorted(set(ci_list) - set(doc_suites)),
        "host_tooling": host,
        "host_tooling_count": len(host),
        "guard_suites_on_disk": guard_on_disk,
        "guard_on_disk_not_listed": sorted(set(guard_on_disk) - set(host)),
        "host_not_in_ci_list": sorted(name for name in host if "tests/test_%s.py" % name not in ci_list),
        "agents_count_lines": agents,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    landed, main_facts = facts(args.tree), facts(args.main)
    new = [name for name in landed["ci_list"] if name not in set(main_facts["ci_list"])]
    placement = []
    for name in new:
        index = landed["ci_list"].index(name)
        placement.append(
            {
                "suite": name,
                "index": index,
                "after": landed["ci_list"][index - 1] if index else None,
                "before": landed["ci_list"][index + 1] if index + 1 < len(landed["ci_list"]) else None,
                "in_main_verify": name in {suite for _, _, suite in landed["main_verify_rows"]},
                "doc_index": [suite for _, suite in doc_list(Path(args.tree) / "docs" / "REFERENCE.md")].index(name) if name in landed["ci_list"] and not landed["ci_minus_doc"] else None,
            }
        )
    main_order_kept = [name for name in landed["ci_list"] if name in set(main_facts["ci_list"])] == main_facts["ci_list"]
    new_host = [name for name in landed["host_tooling"] if name not in set(main_facts["host_tooling"])]
    host_order_kept = [name for name in landed["host_tooling"] if name in set(main_facts["host_tooling"])] == main_facts["host_tooling"]
    summary = {
        "landed": {key: value for key, value in landed.items() if key not in ("ci_list", "main_verify_rows")},
        "main": {key: value for key, value in main_facts.items() if key not in ("ci_list", "main_verify_rows")},
        "new_ci_suites": new,
        "new_ci_suite_count": len(new),
        "placement": placement,
        "main_ci_order_kept_in_landed": main_order_kept,
        "main_verify_share_on_main": "%d of %d" % (main_facts["ci_count"] - len(main_facts["ci_not_in_main_verify"]), main_facts["ci_count"]),
        "main_verify_share_on_landed": "%d of %d" % (landed["ci_count"] - len(landed["ci_not_in_main_verify"]), landed["ci_count"]),
        "main_verify_jobs_steps": sorted({"%s / %s" % (job, step) for job, step, _ in landed["main_verify_rows"]}),
        "new_in_main_verify": [name for name in new if name in {suite for _, _, suite in landed["main_verify_rows"]}],
        "new_not_in_main_verify": [name for name in new if name not in {suite for _, _, suite in landed["main_verify_rows"]}],
        "new_host_tooling": new_host,
        "host_order_kept": host_order_kept,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    for key in ("new_ci_suite_count", "main_ci_order_kept_in_landed", "main_verify_share_on_main", "main_verify_share_on_landed", "main_verify_jobs_steps", "new_in_main_verify", "new_not_in_main_verify", "new_host_tooling", "host_order_kept"):
        print(key, "=", summary[key])
    for label, block in (("landed", landed), ("main", main_facts)):
        print(label, {key: block[key] for key in ("ci_count", "ci_duplicates", "on_disk_count", "on_disk_not_in_ci", "ci_not_on_disk", "main_verify_count", "main_verify_distinct", "main_verify_not_in_ci", "main_verify_order_follows_ci", "doc_count", "doc_order_equals_ci", "doc_minus_ci", "ci_minus_doc", "host_tooling_count", "guard_suites_on_disk", "guard_on_disk_not_listed", "host_not_in_ci_list", "agents_count_lines", "doc_headings")})
    for row in placement:
        print("  %-55s idx %3d after %-52s mv=%s" % (row["suite"], row["index"], row["after"], row["in_main_verify"]))
    print("main ci_not_in_main_verify (%d):" % len(main_facts["ci_not_in_main_verify"]), main_facts["ci_not_in_main_verify"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
