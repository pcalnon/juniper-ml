#!/usr/bin/env python3
"""
Drive the technical-owner sweep across the sibling repos, the way juniper-ml#2632 swept juniper-ml.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — migration (the technical-owner sweep that follows the 2026-11-20..23 rename PRs)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2632 (the juniper-ml sweep); util/ad-hoc/2026-11-24_technical_owner_candidates.py (the
    candidate list); util/ad-hoc/2026-11-24_technical_owner_restore.py and _verify.py (the restore and its check)

Why this exists
---------------
The sibling repos' rename PRs were repaired with the same ``classify``
(``util/ad-hoc/2026-11-23_overtoad_rename_repair.py``) that missed 340 technical owners in juniper-ml. This
runs the same candidate tool in each sibling repo, base = the rename merge's parent, head = the rename merge,
and then reads each candidate against the repo's CURRENT ``origin/main``: a token a later repair PR (deploy#285,
recurrence#238) or a later edit already put back, or a line main has since rewritten, is not a token to restore.
The command guard refuses git loops in a Bash command, so the loops live here.

Subcommands
-----------
state       fetch each primary's ``origin/main``; check that each PR's merge commit is the listed sha and that
            the merge's parent is present
setup       make one worktree per repo at ``origin/main`` under ``Juniper/worktrees/`` (branch ``--branch``)
candidates  run the candidate tool per repo, then label every row against ``origin/main``:
            LIVE (the head line is on main with the token still renamed), RESTORED (main carries the line with
            "owner" back), GONE (main no longer has the line)
upload      one GitHub-signed commit of a worktree's tracked edits on a new branch made at the worktree's HEAD
            (refused if main has since changed a carried file), a blob-by-blob check, then the pull request
wrap        the LINE-WRAP pass: every LIVE row whose token starts or ends its line, printed with the neighbouring
            line from the rename merge. ``classify`` reads one line, so "away from its real" + "# owner." on the
            next line read as the person; this is the pass that found cascor's coordinator and canopy's
            "the deployment" / "owner has verified"
shapes      an independent net over each repo's CURRENT ``origin/main``, not the rename diff: ``git grep`` for
            shapes where "Overtoad" is unlikely to be the person (an indefinite article, a qualifier such as
            "its" / "real" / "deployment", a placeholder or identifier, an attribute list, a possessive, a slug);
            it also catches renamed text that a later PR copied forward

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_sibling_sweep.py state
    python3 util/ad-hoc/2026-11-24_technical_owner_sibling_sweep.py setup --branch fix/technical-owner-sweep
    python3 util/ad-hoc/2026-11-24_technical_owner_sibling_sweep.py candidates --out tmp/tech-owner-siblings
    python3 util/ad-hoc/2026-11-24_technical_owner_sibling_sweep.py wrap --out tmp/tech-owner-siblings
    python3 util/ad-hoc/2026-11-24_technical_owner_sibling_sweep.py shapes
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

JUNIPER = os.environ.get("JUNIPER_ROOT") or os.path.join(os.path.expanduser("~"), "Development", "python", "Juniper")
WORKTREES = os.path.join(JUNIPER, "worktrees")
HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = os.path.join(HERE, "2026-11-24_technical_owner_candidates.py")
# repo, rename merge (short sha), rename PR, the later repair PR that merged on its own (or None)
REPOS = (
    ("juniper-cascor", "e9c86f83", 772, None),
    ("juniper-data", "2ad7b7b5", 547, None),
    ("juniper-data-client", "246b3a4d", 267, None),
    ("juniper-cascor-client", "a17109c2", 201, None),
    ("juniper-cascor-worker", "dcd2c2a9", 234, None),
    ("juniper-canopy", "1e504572", 830, None),
    ("juniper-harcot", "dd3b0bd3", 28, None),
    ("juniper-deploy", "552756a1", 281, 285),
    ("juniper-recurrence", "93a28202", 237, 238),
)
SEP = re.compile(r"(Owner|owner)")


def run(cmd: list[str], check: bool = True) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(cmd[:6])}: {(proc.stdout + proc.stderr).strip()[-800:]}")
    return proc.stdout


def git(repo: str, *args: str, check: bool = True) -> str:
    return run(["git", "-C", repo, *args], check=check)


def primary(name: str) -> str:
    return os.path.join(JUNIPER, name)


def cmd_state(args) -> int:
    for name, merge, pr, repair in REPOS:
        repo = primary(name)
        git(repo, "fetch", "-q", "origin", "main")
        main = git(repo, "rev-parse", "origin/main").strip()
        view = json.loads(run(["gh", "pr", "view", str(pr), "-R", f"pcalnon/{name}", "--json", "state,mergeCommit,mergedAt"]))
        oid = (view.get("mergeCommit") or {}).get("oid", "")
        parent_ok = subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{merge}^"], capture_output=True).returncode == 0
        shallow = git(repo, "rev-parse", "--is-shallow-repository").strip()
        line = f"{name:24} main {main[:8]}  #{pr} {view['state']} {view.get('mergedAt', '')} merge {oid[:8]} " + ("OK" if oid.startswith(merge) else f"MISMATCH (listed {merge})")
        line += f"  parent {'present' if parent_ok else 'MISSING'}  shallow={shallow}"
        if repair:
            rv = json.loads(run(["gh", "pr", "view", str(repair), "-R", f"pcalnon/{name}", "--json", "state,mergeCommit,mergedAt"]))
            line += f"  repair #{repair} {rv['state']} {(rv.get('mergeCommit') or {}).get('oid', '')[:8]}"
        print(line)
    return 0


def cmd_setup(args) -> int:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    for name, _merge, _pr, _repair in REPOS:
        if args.repos and name not in args.repos:
            continue
        repo = primary(name)
        main = git(repo, "rev-parse", "origin/main").strip()
        path = os.path.join(WORKTREES, f"{name}--{args.branch.replace('/', '--')}--{stamp}--{main[:8]}")
        if git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{args.branch}", check=False).strip():
            print(f"{name}: branch {args.branch} exists locally; skipped")
            continue
        git(repo, "worktree", "add", "-q", "-b", args.branch, path, main)
        print(f"{name}: {path}")
    return 0


def find_worktree(name: str, branch: str) -> str | None:
    out = git(primary(name), "worktree", "list", "--porcelain")
    current = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            current = line[len("worktree ") :]
        elif line == f"branch refs/heads/{branch}":
            return current
    return None


def head_column(base_line: str, head_line: str, occurrence: int) -> int | None:
    pieces = SEP.split(base_line)
    pattern = "".join(re.escape(p) if k % 2 == 0 else "(Owner|owner|The Overtoad|Overtoad)" for k, p in enumerate(pieces))
    match = re.fullmatch(pattern, head_line)
    if not match:
        return None
    pos = len(pieces[0])
    for k in range(1, len(pieces), 2):
        if (k + 1) // 2 == occurrence:
            return pos
        pos += len(match.group((k + 1) // 2)) + len(pieces[k + 1])
    return None


def file_lines(repo: str, ref: str, path: str, cache: dict) -> list[str] | None:
    """The lines of PATH at REF (None if it does not exist there), read once per (ref, path)."""
    key = (ref, path)
    if key not in cache:
        proc = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"], capture_output=True, text=True)
        cache[key] = proc.stdout.split("\n") if proc.returncode == 0 else None
    return cache[key]


def cmd_candidates(args) -> int:
    os.makedirs(args.out, exist_ok=True)
    for name, merge, _pr, _repair in REPOS:
        repo = primary(name)
        out_dir = os.path.join(args.out, name)
        os.makedirs(out_dir, exist_ok=True)
        tsv = os.path.join(out_dir, "all.tsv")
        print(f"== {name}")
        sys.stdout.write(run([sys.executable, CANDIDATES, "--repo", repo, "--base", f"{merge}^", "--head", merge, "--out", tsv]))
        main = git(repo, "rev-parse", "origin/main").strip()
        cache: dict[tuple[str, str], list[str] | None] = {}
        labelled, counts = [], {}
        with open(tsv, encoding="utf-8") as handle:
            for raw in handle:
                row = raw.rstrip("\n").split("\t")
                status, where, occurrence = row[0], row[1], int(row[2])
                path, number = where.rsplit(":", 1)
                head_lines = file_lines(repo, merge, path, cache)
                head_line = head_lines[int(number) - 1]
                base_lines = file_lines(repo, f"{merge}^", path, cache) if status == "M" else None
                if base_lines is None:
                    base_line = head_line.replace("The Overtoad", "Owner").replace("Overtoad", "owner")
                else:
                    base_line = base_lines[int(number) - 1]
                main_lines = file_lines(repo, main, path, cache)
                col = head_column(base_line, head_line, occurrence)
                label = "GONE"
                if main_lines is not None and col is not None:
                    restored = head_line[:col] + row[3] + head_line[col + len(row[4]) :]
                    if int(number) <= len(main_lines) and main_lines[int(number) - 1] == head_line or main_lines.count(head_line) == 1:
                        label = "LIVE"
                    elif restored in main_lines:
                        label = "RESTORED"
                counts[label] = counts.get(label, 0) + 1
                labelled.append(label + "\t" + raw.rstrip("\n"))
        with open(os.path.join(out_dir, "labelled.tsv"), "w", encoding="utf-8") as handle:
            handle.write("\n".join(labelled) + ("\n" if labelled else ""))
        print(f"   against origin/main {main[:8]}: " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


LINE_LEAD = re.compile(r"^[\s#/*>\-|\"'`(]*$")
LINE_TAIL = re.compile(r"[\s.,;:)\"'`*]*")


def cmd_wrap(args) -> int:
    for name, merge, _pr, _repair in REPOS:
        tsv = os.path.join(args.out, name, "labelled.tsv")
        if not os.path.isfile(tsv):
            continue
        repo, cache = primary(name), {}
        with open(tsv, encoding="utf-8") as handle:
            for raw in handle:
                label, _status, where, occurrence, orig, _got, _nets, _kind, window = raw.rstrip("\n").split("\t")
                if label != "LIVE":
                    continue
                path, number = where.rsplit(":", 1)
                lines = file_lines(repo, merge, path, cache) or []
                n = int(number)
                mark = window.index("[[")
                before, after = window[:mark], window[mark + len(orig) + 4 :]
                if LINE_LEAD.match(before) and len(before) < 70 and n > 1:
                    print(f"START {name}|{where}#{occurrence}| prev: ...{lines[n - 2][-75:]} || {window[:100]}")
                if LINE_TAIL.fullmatch(after) and len(after) < 70 and n < len(lines):
                    print(f"END   {name}|{where}#{occurrence}| {window[-90:]} || next: {lines[n][:75]}...")
    return 0


# Shapes where "Overtoad" is unlikely to be the person; every hit is a candidate to read, not a verdict.
SHAPES = (
    r"\b[Aa]n Overtoad\b",
    r"(its|their|whose|real|deployment|product|code|repo|repository|file|process|lock|slot|task|each|every|no|any) Overtoad\b",
    r"Overtoad(ship|s\b|_|\(|\)|\}|>|=|:\s*[a-z_]+\b)",
    r"[{<$/_.]Overtoad",
    r"Overtoad[-_](only|id|name|uid|gid|repo|email|login|key|field)",
    r"(mode|group|uid|chown|perm\w*)\s*(,|and|or|/)\s*Overtoad",
    r"Overtoad\s*(,|and|or|/)\s*(mode|group|uid|perm\w*)",
    r"[a-z]'s Overtoad",
    r"-Overtoad-",
)


def cmd_shapes(args) -> int:
    for name, _merge, _pr, _repair in REPOS:
        cmd = ["grep", "-n", "-E", "-I"]
        for shape in SHAPES:
            cmd += ["-e", shape]
        cmd += ["origin/main", "--", ".", ":!*.lock", ":!**/requirements*.txt"]
        hits = git(primary(name), *cmd, check=False).splitlines()
        print(f"== {name}: {len(hits)} hit(s)")
        for hit in hits:
            print("   " + hit.replace("origin/main:", "", 1)[:230])
    return 0


PUSH = os.path.join(HERE, "..", "push_signed_commit.py")


def gh_json(*args: str):
    return json.loads(run(["gh", "api", *args]))


def cmd_upload(args) -> int:
    """One GitHub-signed commit of the worktree's tracked edits, on a new branch made at the worktree's HEAD (the main
    the edits were built on), never at the live main: a merge that lands meanwhile can only leave the PR behind."""
    wt, slug = os.path.abspath(args.worktree), f"pcalnon/{args.repo}"
    base = git(wt, "rev-parse", "HEAD").strip()
    if git(wt, "diff", "--cached", "--name-only").strip():
        raise SystemExit("REFUSED: something is staged")
    if git(wt, "ls-files", "--others", "--exclude-standard").strip():
        raise SystemExit("REFUSED: untracked files in the worktree")
    paths = [p for p in git(wt, "diff", "--name-only").split("\n") if p]
    if not paths:
        raise SystemExit("REFUSED: nothing changed")
    for path in paths:
        if os.path.islink(os.path.join(wt, path)) or git(wt, "ls-tree", "HEAD", "--", path).split()[0] not in ("100644", "100755"):
            raise SystemExit(f"REFUSED: {path} is not a regular file")
    live = gh_json(f"repos/{slug}/git/ref/heads/main")["object"]["sha"]
    moved = []
    if live != base:
        for path in paths:
            at_live = gh_json(f"repos/{slug}/contents/{path}?ref={live}")["sha"]
            if at_live != git(wt, "rev-parse", f"{base}:{path}").strip():
                moved.append(path)
    print(f"{args.repo}: base {base[:8]}, live main {live[:8]}" + ("" if live == base else f" (moved; files changed on main since: {moved or 'none'})"))
    if moved:
        raise SystemExit("REFUSED: main changed a file this upload carries; rebuild on the new main")
    for path in paths:
        print(f"   {path}")
    if not args.execute:
        print("(dry run)")
        return 0
    if subprocess.run(["gh", "api", f"repos/{slug}/git/ref/heads/{args.branch}"], capture_output=True).returncode == 0:
        raise SystemExit(f"REFUSED: branch {args.branch} exists on {slug}")
    run(["gh", "api", "-X", "POST", f"repos/{slug}/git/refs", "-f", f"ref=refs/heads/{args.branch}", "-f", f"sha={base}"])
    cmd = [sys.executable, PUSH, "--repo", args.repo, "--branch", args.branch, "--expected-head", base, "--message", args.message, "--commit-body-file", args.commit_body_file]
    for path in paths:
        cmd += ["--add", f"{os.path.join(wt, path)}:{path}"]
    print(run(cmd).strip().splitlines()[-1])
    tip = gh_json(f"repos/{slug}/git/ref/heads/{args.branch}")["object"]["sha"]
    bad = [p for p in paths if gh_json(f"repos/{slug}/contents/{p}?ref={tip}")["sha"] != git(wt, "hash-object", p).strip()]
    listed = sorted(f["filename"] for f in gh_json(f"repos/{slug}/compare/{base}...{tip}")["files"])
    if bad or listed != sorted(paths):
        raise SystemExit(f"VERIFY FAILED: blob mismatch {bad}; the compare lists {listed}")
    print(f"VERIFIED: {len(paths)} blob(s) equal the local files; the compare lists exactly them. head {tip}")
    url = run(["gh", "pr", "create", "-R", slug, "--head", args.branch, "--base", "main", "--title", args.title, "--body-file", args.body_file]).strip()
    print(url)
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("state")
    p = sub.add_parser("setup")
    p.add_argument("--branch", required=True)
    p.add_argument("--repos", nargs="*", default=[], help="only these repos (default: all)")
    p = sub.add_parser("candidates")
    p.add_argument("--out", required=True)
    p = sub.add_parser("upload")
    for name in ("--repo", "--worktree", "--branch", "--message", "--commit-body-file", "--title", "--body-file"):
        p.add_argument(name, required=True)
    p.add_argument("--execute", action="store_true")
    p = sub.add_parser("wrap")
    p.add_argument("--out", required=True, help="the directory ``candidates`` wrote")
    sub.add_parser("shapes")
    args = ap.parse_args(argv)
    commands = {"state": cmd_state, "setup": cmd_setup, "candidates": cmd_candidates, "upload": cmd_upload, "wrap": cmd_wrap, "shapes": cmd_shapes}
    return commands[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
