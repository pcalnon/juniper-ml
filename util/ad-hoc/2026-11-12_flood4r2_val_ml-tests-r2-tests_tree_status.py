"""
Compare a landed tree with its HEAD and with the ml-tests carrier's manifest (the tests-lens validator's check A).

It reports, for the tree: HEAD; the change list (porcelain, untracked files included) against the manifest's paths;
for every modified tracked file the added / removed line counts; every REMOVED line of the tracked files (a landing
that reverts main's content shows here); and, with --diff-dir, the unified diff of each modified file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --tree <landed worktree> --manifest <manifest.json> --out <json> [--diff-dir <dir>]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def vcs(tree, *argv):
    done = subprocess.run(["git", *argv], cwd=str(tree), capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise SystemExit("git %s: exit %d: %s" % (" ".join(argv), done.returncode, done.stderr.strip()))
    return done.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--diff-dir")
    args = parser.parse_args(argv)

    tree = Path(args.tree).resolve()
    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    expected = {entry["path"]: entry for entry in manifest["files"]}

    head = vcs(tree, "rev-parse", "HEAD").strip()
    porcelain = [line for line in vcs(tree, "status", "--porcelain", "--untracked-files=all").splitlines() if line]
    changed = {line[3:]: line[:2] for line in porcelain}
    only_tree = sorted(set(changed) - set(expected))
    only_manifest = sorted(set(expected) - set(changed))
    status_mismatch = []
    for path, code in sorted(changed.items()):
        want = expected.get(path, {}).get("status")
        got = "added" if code == "??" else "modified" if code.strip() == "M" else code
        if want and want != got:
            status_mismatch.append({"path": path, "manifest": want, "tree": got})

    numstat = {}
    for line in vcs(tree, "diff", "--numstat", "HEAD").splitlines():
        added, removed, path = line.split("\t")
        numstat[path] = {"added": added, "removed": removed}

    removed_lines = {}
    for path in numstat:
        diff = vcs(tree, "diff", "-U0", "HEAD", "--", path)
        minus = [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
        plus = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
        removed_lines[path] = {"removed": minus, "added_count": len(plus)}
        if args.diff_dir:
            target = Path(args.diff_dir)
            target.mkdir(parents=True, exist_ok=True)
            (target / (path.replace("/", "__") + ".diff")).write_text(vcs(tree, "diff", "HEAD", "--", path), encoding="utf-8")

    result = {
        "tree": str(tree),
        "head": head,
        "changed_paths": len(changed),
        "manifest_paths": len(expected),
        "only_in_tree": only_tree,
        "only_in_manifest": only_manifest,
        "status_mismatch": status_mismatch,
        "modified": numstat,
        "untracked": sorted(path for path, code in changed.items() if code == "??"),
        "removed_lines": removed_lines,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print("head=%s changed=%d manifest=%d only_in_tree=%s only_in_manifest=%s status_mismatch=%s" % (head[:8], len(changed), len(expected), only_tree, only_manifest, status_mismatch))
    for path, counts in sorted(numstat.items()):
        print("  M %-45s +%s -%s" % (path, counts["added"], counts["removed"]))
    print("  untracked: %d" % len(result["untracked"]))
    return 0 if not (only_tree or only_manifest or status_mismatch) else 1


if __name__ == "__main__":
    sys.exit(main())
