"""
For each carried draft, list the tests its head adds and which of them the landed tree does not hold.

For every draft: the merge base with origin/main, the paths its head changes against that base, and for each test
file among them the test functions (class.name) at the base, at the draft's head and in the landed tree. A test the
draft adds that the landed tree lacks is a DROPPED test, to be read against the manifest's reason.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --repo <own worktree> --landed <landed tree> --out <json> --prs 2469 2472 ...
"""

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path


def vcs(repo, *argv, check=True):
    done = subprocess.run(["git", *argv], cwd=str(repo), capture_output=True, text=True, check=False)
    if check and done.returncode != 0:
        raise SystemExit("git %s: exit %d: %s" % (" ".join(argv), done.returncode, done.stderr.strip()))
    return done


def test_names(source):
    """class.test and module-level test function names of a Python source; None when it does not parse."""
    if source is None:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            names.add(node.name)
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    names.add("%s.%s" % (node.name, item.name))
    return names


def blob(repo, rev, path):
    done = vcs(repo, "show", "%s:%s" % (rev, path), check=False)
    return done.stdout if done.returncode == 0 else None


def is_test_file(path):
    name = path.rsplit("/", 1)[-1]
    return name.startswith("test_") and name.endswith(".py")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--landed", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prs", nargs="+", required=True)
    args = parser.parse_args(argv)

    repo, landed = Path(args.repo), Path(args.landed)
    report = []
    for number in args.prs:
        head = "refs/flood4r2v/pr/%s" % number
        head_sha = vcs(repo, "rev-parse", head).stdout.strip()
        base = vcs(repo, "merge-base", "origin/main", head).stdout.strip()
        changed = [line.split("\t") for line in vcs(repo, "diff", "--name-status", base, head).stdout.splitlines() if line]
        commits = vcs(repo, "log", "--format=%h %an %s", "%s..%s" % (base, head)).stdout.splitlines()
        row = {"pr": int(number), "head": head_sha, "merge_base": base, "commits": commits, "changed": changed, "test_files": []}
        for entry in changed:
            path = entry[-1]
            if not is_test_file(path):
                continue
            at_base = test_names(blob(repo, base, path))
            at_head = test_names(blob(repo, head, path))
            landed_file = landed / path
            in_landed = test_names(landed_file.read_text(encoding="utf-8")) if landed_file.is_file() else None
            added = sorted((at_head or set()) - (at_base or set()))
            removed_by_draft = sorted((at_base or set()) - (at_head or set()))
            dropped = sorted(name for name in added if in_landed is None or name not in in_landed)
            head_text = blob(repo, head, path)
            landed_text = landed_file.read_text(encoding="utf-8") if landed_file.is_file() else None
            row["test_files"].append(
                {
                    "path": path,
                    "status": entry[0],
                    "tests_at_base": None if at_base is None else len(at_base),
                    "tests_at_head": None if at_head is None else len(at_head),
                    "tests_in_landed": None if in_landed is None else len(in_landed),
                    "added_by_draft": added,
                    "removed_by_draft": removed_by_draft,
                    "dropped_from_landed": dropped,
                    "landed_only": sorted((in_landed or set()) - (at_head or set())) if in_landed is not None and entry[0] == "A" else [],
                    "head_blob_equals_landed": head_text == landed_text,
                }
            )
        report.append(row)
        print("#%s head %s base %s: %d commits, %d paths" % (number, head_sha[:8], base[:8], len(commits), len(changed)))
        for entry in changed:
            print("   %s" % " ".join(entry))
        for item in row["test_files"]:
            print("   TEST %s: base %s head %s landed %s; added %d; DROPPED %s; landed-only %s; identical=%s" % (item["path"], item["tests_at_base"], item["tests_at_head"], item["tests_in_landed"], len(item["added_by_draft"]), item["dropped_from_landed"], item["landed_only"], item["head_blob_equals_landed"]))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
