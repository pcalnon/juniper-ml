"""
Scratch-worktree helpers for the tests-lens validator: an unsigned, never-pushed probe commit, and a CHANGELOG check.

`commit` stages everything in a DETACHED scratch worktree the validator made, writes the tree, makes a plumbing-only
commit object on top of HEAD (commit-tree: no hook, no signature, no branch) and points the detached HEAD at it, so
that a landing tool that wants a clean worktree can run on "main + another carrier".

`changelog` reports where an entry stands in a tree's CHANGELOG.md: the line of `## [Unreleased]`, of the next
`## [` heading, of the entry's first line, and the `###` subsection the entry is under.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> commit --tree <scratch worktree> --message <text>
    python3 <this file> changelog --tree <tree> --entry <changelog_entry.txt> --out <json>
    python3 <this file> status --tree <tree>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def vcs(tree, *argv, stdin=None):
    done = subprocess.run(["git", *argv], cwd=str(tree), capture_output=True, text=True, check=False, input=stdin)
    if done.returncode != 0:
        raise SystemExit("git %s: exit %d: %s" % (" ".join(argv), done.returncode, done.stderr.strip()))
    return done.stdout.strip()


def do_commit(args):
    tree = Path(args.tree).resolve()
    if "--val--flood4r2-ml-tests-r2-tests" not in tree.name:
        raise SystemExit("refusing: %s is not one of this validator's scratch worktrees" % tree)
    if vcs(tree, "rev-parse", "--abbrev-ref", "HEAD") != "HEAD":
        raise SystemExit("refusing: %s is not detached" % tree)
    parent = vcs(tree, "rev-parse", "HEAD")
    vcs(tree, "add", "-A")
    tree_id = vcs(tree, "write-tree")
    commit = vcs(tree, "commit-tree", tree_id, "-p", parent, "-m", args.message)
    vcs(tree, "update-ref", "--no-deref", "HEAD", commit, parent)
    left = vcs(tree, "status", "--porcelain", "--untracked-files=all")
    print(json.dumps({"tree": str(tree), "parent": parent, "probe_commit": commit, "status_after": left.splitlines()}, indent=1))
    return 0 if not left else 1


def do_status(args):
    tree = Path(args.tree).resolve()
    head = vcs(tree, "rev-parse", "HEAD")
    lines = vcs(tree, "status", "--porcelain", "--untracked-files=all").splitlines()
    print(json.dumps({"tree": str(tree), "head": head, "changed": len(lines), "paths": [line[3:] for line in lines]}, indent=1))
    return 0


def do_changelog(args):
    text = (Path(args.tree) / "CHANGELOG.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    entry_lines = Path(args.entry).read_text(encoding="utf-8").splitlines()
    first = next(line for line in entry_lines if line.strip())
    headings = [(number, line) for number, line in enumerate(lines, 1) if line.startswith("## [")]
    unreleased = next((number for number, line in headings if line.startswith("## [Unreleased]")), None)
    next_release = next(((number, line) for number, line in headings if unreleased is not None and number > unreleased), (None, None))
    where = [number for number, line in enumerate(lines, 1) if line == first]
    whole = text.count("\n".join(entry_lines))
    subsection = None
    section = None
    if where:
        for number in range(where[0], 0, -1):
            line = lines[number - 1]
            if subsection is None and line.startswith("### "):
                subsection = (number, line)
            if line.startswith("## ["):
                section = (number, line)
                break
    result = {
        "unreleased_line": unreleased,
        "next_release_heading": next_release,
        "entry_first_line_at": where,
        "entry_whole_text_occurrences": whole,
        "entry_lines": len(entry_lines),
        "entry_section": section,
        "entry_subsection": subsection,
        "under_unreleased": bool(where) and unreleased is not None and section is not None and section[0] == unreleased and (next_release[0] is None or where[0] < next_release[0]),
        "token_left": "<ML-PROPOSE-PR>" in text,
        "first_line": first[:160],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(json.dumps(result, indent=1))
    return 0 if result["under_unreleased"] and len(where) == 1 and whole == 1 else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="verb", required=True)
    commit = sub.add_parser("commit")
    commit.add_argument("--tree", required=True)
    commit.add_argument("--message", required=True)
    status = sub.add_parser("status")
    status.add_argument("--tree", required=True)
    changelog = sub.add_parser("changelog")
    changelog.add_argument("--tree", required=True)
    changelog.add_argument("--entry", required=True)
    changelog.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    return {"commit": do_commit, "status": do_status, "changelog": do_changelog}[args.verb](args)


if __name__ == "__main__":
    sys.exit(main())
