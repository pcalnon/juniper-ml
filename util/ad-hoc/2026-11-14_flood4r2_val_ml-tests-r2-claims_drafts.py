"""
Read the 18 ml-tests drafts against the landed tree: each draft's own diff from its merge base, its live state,
and, file by file, how the draft's copy differs from the landed tree's copy (claims lens, session 8).

For every pull request number given: resolves refs/flood4r2v/pr/<N> (fetched beforehand), its merge base with
--main, the draft's name-status list, and for each path the draft adds or changes: whether the landed tree (--tree)
holds that path, and a unified diff (draft copy -> landed copy) written to <out>/<N>/<path with / as __>.diff. The
draft's whole diff goes to <out>/<N>/draft.diff, the added lines of every shared document to <out>/<N>/shared_adds.txt,
and `gh pr view` to <out>/<N>/gh.json. A summary goes to <out>/summary.json and stdout.

Read-only: git runs in --repo (a worktree of this validator's own), gh only reads.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import difflib
import json
import subprocess  # nosec B404 - fixed argv, read-only plumbing in the validator's own worktree
import sys
from pathlib import Path

SHARED = (
    ".github/workflows/ci.yml",
    ".github/workflows/main-verify.yml",
    "docs/REFERENCE.md",
    "AGENTS.md",
    "CHANGELOG.md",
)


def git(repo: Path, *argv: str) -> str:
    done = subprocess.run(["git", *argv], cwd=str(repo), capture_output=True, check=False)  # nosec B603 B607
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(argv)}: {done.stderr.decode(errors='replace')}")
    return done.stdout.decode(errors="replace")


def blob(repo: Path, rev: str, path: str) -> str:
    done = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=str(repo), capture_output=True, check=False)  # nosec B603 B607
    return done.stdout.decode(errors="replace") if done.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Read the drafts against the landed tree.")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--main", default="origin/main")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--gh-repo", default="pcalnon/juniper-ml")
    parser.add_argument("prs", nargs="+", type=int)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summary = []
    for number in args.prs:
        ref = f"refs/flood4r2v/pr/{number}"
        head = git(args.repo, "rev-parse", ref).strip()
        base = git(args.repo, "merge-base", args.main, head).strip()
        names = [line.split("\t") for line in git(args.repo, "diff", "--name-status", base, head).splitlines() if line]
        commits = git(args.repo, "log", "--format=%h %an %s", f"{base}..{head}").splitlines()
        pdir = args.out / str(number)
        pdir.mkdir(exist_ok=True)
        with (pdir / "draft.diff").open("w") as handle:
            handle.write(git(args.repo, "diff", base, head))
        shared_adds = []
        files = []
        for row in names:
            status, path = row[0], row[-1]
            draft_text = blob(args.repo, head, path)
            landed_path = args.tree / path
            landed_text = landed_path.read_text(errors="replace") if landed_path.exists() else None
            entry = {"status": status, "path": path, "in_landed_tree": landed_text is not None}
            if path in SHARED:
                diff = git(args.repo, "diff", "-U0", base, head, "--", path)
                adds = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
                dels = [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
                shared_adds.append({"path": path, "added": adds, "removed": dels})
                entry["shared"] = True
                entry["added_lines"] = len(adds)
                entry["added_lines_present_verbatim_in_landed"] = sum(1 for line in adds if landed_text is not None and line in landed_text.splitlines())
            elif landed_text is not None:
                same = draft_text == landed_text
                entry["identical_to_landed"] = same
                if not same:
                    udiff = list(difflib.unified_diff(draft_text.splitlines(), landed_text.splitlines(), f"draft/{path}", f"landed/{path}", lineterm="", n=1))
                    entry["diff_lines"] = len(udiff)
                    with (pdir / (path.replace("/", "__") + ".diff")).open("w") as handle:
                        handle.write("\n".join(udiff) + "\n")
            files.append(entry)
        with (pdir / "shared_adds.json").open("w") as handle:
            json.dump(shared_adds, handle, indent=1)
        gh = subprocess.run(  # nosec B603 B607
            ["gh", "pr", "view", str(number), "--repo", args.gh_repo, "--json", "number,state,isDraft,title,headRefOid,headRefName,baseRefName,updatedAt,body,mergedAt,closedAt"],
            capture_output=True,
            check=False,
        )
        gh_json = json.loads(gh.stdout.decode() or "{}") if gh.returncode == 0 else {"error": gh.stderr.decode(errors="replace")}
        with (pdir / "gh.json").open("w") as handle:
            json.dump(gh_json, handle, indent=1)
        row = {
            "pr": number,
            "head": head,
            "gh_head": gh_json.get("headRefOid"),
            "state": gh_json.get("state"),
            "is_draft": gh_json.get("isDraft"),
            "base_ref": gh_json.get("baseRefName"),
            "title": gh_json.get("title"),
            "merge_base": base,
            "commits": commits,
            "files": files,
        }
        summary.append(row)
        print(f"#{number} head {head[:8]} gh {str(gh_json.get('headRefOid'))[:8]} {gh_json.get('state')} draft={gh_json.get('isDraft')} base={gh_json.get('baseRefName')} commits={len(commits)}")
        for entry in files:
            print("   ", json.dumps(entry))
    with (args.out / "summary.json").open("w") as handle:
        json.dump(summary, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
