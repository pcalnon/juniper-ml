"""
Survey the flood-4 round-2 ml-tests drafts: each draft's OWN hunks, and the ml-code carrier's delta.

For every draft head fetched as refs/flood4r2/pr/<N>, list the commits that origin/main lacks and keep
the ones the Cursor fleet authored (author name "Cursor Agent" or "cursor[bot]"). The draft's OWN diff
is the diff from the first parent of its earliest Cursor commit to its head, which leaves out the
owner's commits a draft was stacked on (those reached main as their own PRs). Each own diff is written
as <scratch>/own/own-<N>.diff.txt with a one-line file summary in <scratch>/own/summary.json, and its
sha256 is compared with the round-2 triage's own-ml-<N>.diff.txt when that file is given.

With --mlcode-tree and --mlcode-base, also write the ml-code carrier's delta: for each path its manifest
lists, the base blob (git show <base>:<path>) and a unified diff against the carrier's working copy,
under <scratch>/mlcode/. Reads only; never writes to the ml-code tree.

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_survey.py --scratch <dir> [--triage <dir>]
        [--mlcode-tree <abs path> --mlcode-base <sha> --mlcode-manifest <path>] N [N ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, ruling 14)
"""

import argparse
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

CURSOR_AUTHORS = ("Cursor Agent", "cursor[bot]")


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _own(n: int) -> dict:
    head = f"refs/flood4r2/pr/{n}"
    rows = _git("log", "--format=%H%x09%P%x09%an%x09%s", f"origin/main..{head}").splitlines()
    commits = []
    for row in rows:
        sha, parents, author, subject = row.split("\t", 3)
        commits.append({"sha": sha, "parents": parents.split(), "author": author, "subject": subject})
    cursor = [c for c in commits if c["author"] in CURSOR_AUTHORS]
    if not cursor:
        return {"pr": n, "error": "no Cursor commit"}
    # git log lists newest first; the earliest Cursor commit is the last one listed.
    earliest = cursor[-1]
    base = earliest["parents"][0]
    # Every commit above `base` must be a Cursor commit, or the own diff would sweep in someone else's.
    above = commits[: commits.index(earliest) + 1]
    foreign = [c for c in above if c["author"] not in CURSOR_AUTHORS]
    diff = _git("diff", "--full-index", base, head)
    files = _git("diff", "--name-status", base, head).splitlines()
    return {
        "pr": n,
        "head": _git("rev-parse", head).strip(),
        "own_base": base,
        "cursor_commits": [c["sha"][:10] + " " + c["subject"] for c in cursor],
        "foreign_above_base": [c["sha"][:10] + " " + c["author"] for c in foreign],
        "owner_commits_below": [c["sha"][:10] + " " + c["author"] + " " + c["subject"] for c in commits if c not in above],
        "files": files,
        "diff": diff,
    }


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--triage")
    ap.add_argument("--mlcode-tree")
    ap.add_argument("--mlcode-base")
    ap.add_argument("--mlcode-manifest")
    ap.add_argument("prs", nargs="+", type=int)
    args = ap.parse_args()
    scratch = Path(args.scratch)
    (scratch / "own").mkdir(parents=True, exist_ok=True)
    summary = []
    for n in args.prs:
        rec = _own(n)
        if "error" in rec:
            print(f"#{n}: {rec['error']}")
            summary.append(rec)
            continue
        diff = rec.pop("diff")
        (scratch / "own" / f"own-{n}.diff.txt").write_text(diff, encoding="utf-8")
        rec["own_sha256"] = _sha(diff)
        if args.triage:
            tri = Path(args.triage) / f"own-ml-{n}.diff.txt"
            if tri.is_file():
                rec["triage_sha256"] = _sha(tri.read_text(encoding="utf-8"))
                rec["matches_triage"] = rec["triage_sha256"] == rec["own_sha256"]
        summary.append(rec)
        print(f"#{n} head={rec['head'][:10]} own_base={rec['own_base'][:10]} matches_triage={rec.get('matches_triage')} " f"foreign={rec['foreign_above_base']} files={[f.replace(chr(9), ' ') for f in rec['files']]}")
    with open(scratch / "own" / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    if args.mlcode_tree and args.mlcode_base and args.mlcode_manifest:
        out = scratch / "mlcode"
        (out / "base").mkdir(parents=True, exist_ok=True)
        (out / "diffs").mkdir(parents=True, exist_ok=True)
        with open(args.mlcode_manifest, encoding="utf-8") as fh:
            manifest = json.load(fh)
        rows = []
        for f in manifest["files"]:
            path = f["path"]
            carrier_file = Path(args.mlcode_tree) / path
            new = carrier_file.read_text(encoding="utf-8") if carrier_file.is_file() else ""
            if f["status"] == "added":
                old = ""
            else:
                old = _git("show", f"{args.mlcode_base}:{path}")
            flat = path.replace("/", "__")
            (out / "base" / flat).write_text(old, encoding="utf-8")
            udiff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), f"a/{path}", f"b/{path}"))
            (out / "diffs" / f"{flat}.diff.txt").write_text(udiff, encoding="utf-8")
            # Has main moved this path since ml-code's base? A three-way merge is needed for those.
            try:
                main_now = _git("show", f"origin/main:{path}")
            except RuntimeError:
                main_now = ""
            rows.append({"path": path, "status": f["status"], "carrier_sha256": hashlib.sha256(new.encode("utf-8")).hexdigest(), "manifest_sha256": f.get("sha256"), "main_moved_since_base": main_now != old})
        with open(out / "mlcode_delta.json", "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2)
        for r in rows:
            print(f"ml-code {r['status']:8} {r['path']} sha_ok={r['carrier_sha256'] == r['manifest_sha256']} main_moved={r['main_moved_since_base']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
