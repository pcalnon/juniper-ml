"""
Write fix N-1's round-3 manifest.json: base sha, per-file status and sha256, and what changed since round 2.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge)

Usage: python3 <this>

Reads tmp/flood4-fix/n1-r3/manifest_facts.json in the N-1 worktree (the hand-recorded checks,
mutants, decisions and open questions) and adds what git and the files themselves say: HEAD,
origin/main, the branch, every carrier file's status (``git status --porcelain``, tmp/ excluded)
and sha256, and whether that sha256 differs from round 2's manifest. Refuses (exit 1) when HEAD
is not origin/main, or when the carrier has a staged change, a deletion or a rename.
Writes tmp/flood4-fix/n1-r3/manifest.json.
"""

import hashlib
import json
import subprocess  # nosec B404 -- fixed-argv git reads
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
TREE = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
R2 = TREE / "tmp" / "flood4-fix" / "n1-r2"
R3 = TREE / "tmp" / "flood4-fix" / "n1-r3"
STATUS = {" M": "modified", "??": "added"}


def git(*args: str) -> str:
    """Raw stdout: never strip it, or porcelain's leading-space status code (' M') is lost."""
    return subprocess.run(["git", "-C", str(TREE), *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607


def main() -> int:
    with open(R3 / "manifest_facts.json", encoding="utf-8") as fh:
        facts = json.load(fh)
    with open(R2 / "manifest.json", encoding="utf-8") as fh:
        round2 = {entry["path"]: entry["sha256"] for entry in json.load(fh)["files_changed"]}

    head, origin_main = git("rev-parse", "HEAD").strip(), git("rev-parse", "origin/main").strip()
    if head != origin_main:
        print(f"refusing: HEAD {head} is not origin/main {origin_main}")
        return 1
    files = []
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        code, rel = line[:2], line[3:]
        if rel.startswith("tmp/"):
            continue
        if code not in STATUS:
            print(f"refusing: {rel} has status {code!r}; expected an unstaged modification or an untracked file")
            return 1
        digest = hashlib.sha256((TREE / rel).read_bytes()).hexdigest()
        files.append({"path": rel, "status": STATUS[code], "sha256": digest, "changed_since_round_2": digest != round2.get(rel)})

    manifest = {
        "repo": "pcalnon/juniper-cascor",
        "carrier": "N-1 (juniper-cascor paused-fit wedge), round 3",
        "base_sha": head,
        "previous_base_sha": facts.pop("previous_base_sha"),
        "worktree": str(TREE),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "committed": False,
        "pushed": False,
        "files": files,
    }
    manifest.update(facts)
    with open(R3 / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"manifest: base {head}, {len(files)} files ({sum(f['changed_since_round_2'] for f in files)} changed since round 2) -> {R3 / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
