#!/usr/bin/env python3
"""Survey, then remove, the canopy selection arc's worktrees, with every gate read live.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc tooling (canopy selection arc cleanup, W5 of the 2026-09-24 handoffs)
Author:      Paul Calnon
License:     MIT License

Why not ``2026-08-28_p5_worktree_cleanup.py`` as-is. Its gates are the right ones and this
reuses their shape, but three of this arc's worktree kinds cannot pass a "the PR on this head
is MERGED" gate, and one of its checks is blind to a config it does not force:

* **detached verify trees** have no branch, so no PR. Their gate is reachability: HEAD must be
  an ancestor of ``origin/main`` or contained in some remote ref, or nothing is lost only if
  the commit is a PR head GitHub still serves.
* **a CLOSED PR** (canopy#666) and **a local-only superseded tree** (the nn-model mirror v1,
  whose staged diff went out as #674) have no merge. Their gate is content: every path the
  tree changed must be byte-identical on ``origin/main`` today, or a human accepts the diff.
* ``git status --porcelain`` returns empty under ``status.showUntrackedFiles=no`` even when
  untracked files exist (ml#734). Every status call here forces ``=normal``.

For a MERGED PR the content gate still runs. Squash merging means no local SHA is ever an
ancestor of ``main``, so "merged" alone does not prove the tree holds nothing more; an
unpushed local commit (the x8 tree carries one) would be lost silently.

**Most of this arc's PR trees are DIRTY by construction**, and that is the finding the first
survey run made: the sessions pushed through signed API commits (``createCommitOnBranch``), so
the PR's content was never committed locally and still sits in the working tree. "Dirty" is
therefore not evidence of unshipped work here, and "clean" was never going to be reachable.
The content gate is what decides: every path the tree changed -- committed OR dirty OR
untracked -- must be

* byte-identical to the squash commit's copy, or to ``origin/main``'s; or
* **contained** in one of them: ``git merge-file`` of the tree's delta (against the base it
  started from) into that copy changes nothing. This is the case where the PR later took a
  review-round API commit, or ``main`` moved the same file on, so the local copy is BEHIND
  what shipped rather than ahead of it.

Anything else is listed for review and needs ``--accept NAME``. A tree that passes while dirty
is removed with ``--force`` -- which git needs for any dirty tree -- after its full diff is
written to the harvest directory.

Gates, ALL of which must hold, re-checked immediately before each removal (TOCTOU):

1. the kind-specific gate above;
2. **not in use**: no process has its cwd, or an open file, inside the tree (STRONG). A
   process that only NAMES the path in its argv is WEAK, reported, never blocking;
3. **clean**, except for a superseded tree whose every dirty path passed the content gate;
4. **not locked** (a lock is somebody's deliberate "keep");
5. **ignored payload**: ``worktree remove`` deletes ignored files and nothing reports them.
   Anything outside the disposable list is copied to ``--harvest DIR`` before removal, and
   removal is refused without ``--harvest``. ``.env*`` is never copied: it blocks outright.

Removal passes ``--force`` only for a dirty tree whose content gate passed (or was accepted),
and only after its full diff is written to the harvest directory.

Usage:
    python3 util/ad-hoc/2026-09-24_canopy_arc_worktree_cleanup.py                 # report only
    python3 util/ad-hoc/2026-09-24_canopy_arc_worktree_cleanup.py --execute --harvest DIR \
        [--accept NAME ...] [--delete-remote] [--only NAME ...]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import os
import shutil
import subprocess  # nosec B404 -- fixed-argv git/gh calls; nothing is shell-interpolated
import sys
from pathlib import Path

JUNIPER = Path("/home/pcalnon/Development/python/Juniper")
WORKTREES = JUNIPER / "worktrees"

# (directory name, kind, PR number). kind: pr | detached | closed-pr | superseded.
# A PR number of None means "discover it from the head branch".
INVENTORY = [
    ("juniper-canopy--feat--nn-model-mirror-restart-and-live-swap--20260923-0125--7950bf9e", "superseded", 674),
    ("juniper-canopy--feat--nn-model-mirror-restart-and-live-swap-v2--20260923-1410--48074653", "pr", 674),
    ("juniper-canopy--feat--request-nn-model-mirror--20260923-0230--2f973ca2", "pr", None),
    # #666 was CLOSED, superseded by #667 ("the same change as a single commit" carrying the
    # Allow-Symbol-Loss waivers), so its content is judged against #667's squash.
    ("juniper-canopy--feat--selection-bottom-at-mount--20260923-0200--36ae276b", "superseded", 667),
    ("juniper-canopy--feat--selection-hydration-both-axes--20260922-2355--886147b5", "pr", None),
    ("juniper-canopy--fix--e2e-test-three-partition-contract--20260923-0130--2f973ca2", "pr", None),
    ("juniper-canopy--fix--fixed-sleep-lower-bounds-followup--20260923-0112--2f973ca2", "pr", None),
    ("juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f", "pr", None),
    ("juniper-canopy--fix--restart-restage-seed--20260923-0115--2f973ca2", "pr", None),
    ("juniper-canopy--fix--selection-stale-comments-and-restart-regate-test--20260923-1420--48074653", "pr", 675),
    ("juniper-canopy--fix--selection-summary-unknown-liveness--20260924-0259--e9053227", "pr", 680),
    ("juniper-canopy--fix--selection-ui-y4-y7-y8--20260922-2022--26e0546f", "pr", None),
    ("juniper-canopy--fix--stale-availability-and-seed-count-comments--20260923-1508--0254a7ec", "pr", 677),
    ("juniper-canopy--fix--start-refusal-points-at-start-fresh--20260924-0356--1463f29a", "pr", 681),
    ("juniper-canopy--fix--test-timing-flakes--20260922-2022--26e0546f", "pr", None),
    ("juniper-canopy--test--x8-task-type-agrees-with-juniper-data--20260924-0401--6c4ad9a9", "pr", 682),
    ("juniper-canopy--verify--a-n2-loop--20260923-1415--48074653", "detached", None),
    ("juniper-canopy--verify--m1-m6-mutations--20260923-1416--48074653", "detached", None),
    ("juniper-canopy--verify--main-ui-baseline--20260923-0045--2f973ca2", "detached", None),
    ("juniper-canopy--verify--pr671-codeql--20260923-1000--c7553cff", "detached", 671),
    ("juniper-cascor--feat--status-current-dataset--20260923-0110--0d2d826b", "pr", 676),
    ("juniper-cascor--fix--start-fresh-keeps-applied-params--20260924-0310--0e016a7c", "pr", 685),
    ("juniper-cascor--fix--start-refuses-wider-dataset-before-binding--20260924-0355--33c965b3", "pr", 687),
    ("juniper-cascor--verify--a-n2-loop--20260923-1415--f7a6d573", "detached", None),
    ("juniper-data--fix--equities-seq-task-type-regression--20260924-0355--39d1cab2", "pr", 437),
    ("juniper-data--verify--a-n2-loop--20260923-1415--ce436819", "detached", None),
]

# Regenerated on demand, never authored. `*.log` and `logs/` are deliberately ABSENT: the
# 2026-08-29 sweep lost the only surviving copy of a run log that way (P5 tool docstring).
DISPOSABLE = [
    "*__pycache__/", "*.pyc", "*.pytest_cache/", "*.ruff_cache/", "*.mypy_cache/", "*.egg-info/",
    "*.coverage", "*.coverage.*", "*htmlcov/", "build/", "dist/", "*.tox/", "*node_modules/",
    "*.venv/", "*venv/", "*.DS_Store", "*.hypothesis/", "*.benchmarks/",
]
# `.env*` files: never copied anywhere, and they block removal outright. Only their NAMES are ever
# printed. The identifiers avoid the word CodeQL's clear-text-logging heuristic keys on, which
# would otherwise taint every printed survey row (restructure, never suppress).
ENV_FILE_GLOBS = [".env", "*/.env", ".env.*", "*/.env.*", "*.env"]


def run(argv, cwd=None):
    return subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True, text=True)  # nosec B603


def git(wt, *args):
    return run(["git", "-c", "status.showUntrackedFiles=normal", "-C", str(wt), *args])


def in_use(wt: Path) -> tuple[list[str], list[str]]:
    """(STRONG, WEAK) holders. STRONG = cwd or an open fd inside the tree; WEAK = argv mentions it."""
    strong, weak, me = [], [], {str(os.getpid()), str(os.getppid())}
    prefix = str(wt) + "/"
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or entry.name in me:
            continue
        try:
            cwd = os.readlink(entry / "cwd")
            if cwd == str(wt) or cwd.startswith(prefix):
                strong.append(f"{entry.name}(cwd)")
                continue
        except OSError:
            continue
        try:
            for fd in (entry / "fd").iterdir():
                try:
                    tgt = os.readlink(fd)
                except OSError:
                    continue
                if tgt == str(wt) or tgt.startswith(prefix):
                    strong.append(f"{entry.name}(fd)")
                    break
        except OSError:
            # fd/ is unreadable (another user's process, or it exited mid-scan). Its cwd was
            # already checked above and its argv is checked below; this is the documented
            # unprivileged blind spot, not a silent pass.
            pass
        try:
            argv = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if str(wt) in argv and f"{entry.name}(fd)" not in strong:
            weak.append(entry.name)
    return strong, weak


def porcelain(wt: Path, ignored: bool = False) -> tuple[list[str] | None, str]:
    """Porcelain lines, or (None, error) -- a failed status is NEVER read as clean (fails closed)."""
    args = ["status", "--porcelain"] + (["--ignored"] if ignored else [])
    p = git(wt, *args)
    if p.returncode != 0:
        return None, (p.stderr or p.stdout).strip()[:200]
    return [ln for ln in p.stdout.splitlines() if ln], ""


def describe(wt: Path, rel: str) -> str:
    p, total, files, newest = wt / rel, 0, 0, 0.0
    walk = os.walk(p) if p.is_dir() else [(str(p.parent), [], [p.name])] if p.is_file() else []
    for root, _d, names in walk:
        for n in names:
            try:
                st = os.stat(os.path.join(root, n))
            except OSError:
                continue
            total, files, newest = total + st.st_size, files + 1, max(newest, st.st_mtime)
    when = dt.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M") if newest else "?"
    size = f"{total / 1e6:.1f} MB" if total >= 1e6 else f"{total / 1e3:.1f} KB" if total else "empty"
    return f"{rel} ({files} file{'s' if files != 1 else ''}, {size}, newest {when})"


def matches(rel: str, pats: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel.rstrip("/") + "/", p) for p in pats)


def at(ref: str, path: str, repo_dir: Path) -> bytes | None:
    """The bytes of ``path`` at ``ref``, or None when the path does not exist there."""
    p = subprocess.run(["git", "-C", str(repo_dir), "cat-file", "blob", f"{ref}:{path}"], capture_output=True)  # nosec B603 B607 -- fixed-argv git from PATH
    return p.stdout if p.returncode == 0 else None


def on_disk(wt: Path, path: str) -> bytes | None:
    f = wt / path
    return f.read_bytes() if f.is_file() else None


def contained(base: bytes | None, shipped: bytes, local: bytes) -> bool:
    """True when merging local's delta (against ``base``) into ``shipped`` changes nothing.

    That is: whatever this tree changed is already in what shipped. It is how a local copy
    that is BEHIND the shipped one (a later review-round API commit, or main moving the same
    file) is told apart from one that is AHEAD of it.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        cur, bas, oth = Path(d, "shipped"), Path(d, "base"), Path(d, "local")
        cur.write_bytes(shipped)
        bas.write_bytes(base or b"")
        oth.write_bytes(local)
        p = subprocess.run(["git", "merge-file", "-p", "--quiet", str(cur), str(bas), str(oth)], capture_output=True)  # nosec B603 B607 -- fixed-argv git from PATH
    return p.returncode == 0 and p.stdout == shipped


def content_gate(wt: Path, head: str, dirty: list[str], refs: list[tuple[str, str]]) -> tuple[dict, list[str]]:
    """Classify every path the tree changed -- committed, dirty or untracked -- against ``refs``."""
    committed, mb = changed_paths(wt)
    dpaths = [ln[3:].split(" -> ")[-1].strip('"') for ln in dirty]
    base_ref = mb or head
    tally: dict[str, int] = {}
    differ = []
    for p in sorted(set(committed) | set(dpaths)):
        local, base = on_disk(wt, p), at(base_ref, p, wt)
        verdict = None
        for label, ref in refs:
            shipped = at(ref, p, wt)
            if local == shipped:
                verdict = f"identical to {label}"
            elif local is not None and shipped is not None and contained(base, shipped, local):
                verdict = f"contained in {label}"
            if verdict:
                break
        if verdict is None:
            differ.append(p)
            verdict = "DIFFERS"
        tally[verdict] = tally.get(verdict, 0) + 1
    return tally, differ


def primary_of(repo: str) -> Path:
    return JUNIPER / repo


def primary_holders(primary: Path) -> list[str]:
    """Live processes that hold a PRIMARY checkout (cwd, argv, environ, open fd or mapping).

    ``util/ad-hoc/cascor_freeze_tell.py``'s probes, for any repo. A stack running from a
    primary's ``src`` re-imports from it in every new forkserver child, so fast-forwarding that
    primary changes the code under a live stack -- silently. 2026-09-24: the peer's isolated
    stack held both the cascor and the canopy primaries. Pure-Python imports through an
    editable finder leave none of these traces once the file is closed, so a clean result means
    "no VISIBLE holder", which is why ``--no-primary-ff`` exists too.
    """
    roots = (str(WORKTREES), str(primary / ".claude" / "worktrees"))
    base = str(primary)

    def inside(raw: str) -> bool:
        n = os.path.normpath(raw) if raw else ""
        if not n or any(n == r or n.startswith(r + os.sep) for r in roots):
            return False
        return n == base or n.startswith(base + os.sep)

    hits = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or entry.name in (str(os.getpid()), str(os.getppid())):
            continue
        why = ""
        try:
            if inside(os.readlink(entry / "cwd")):
                why = "cwd"
        except OSError:
            # Unreadable cwd (another user, or the pid exited): fall through to argv, environ
            # and fds, which can still betray a holder -- the same policy as cascor_freeze_tell.py.
            pass
        for label, fname in (("argv", "cmdline"), ("env", "environ")):
            if why:
                break
            try:
                parts = (entry / fname).read_bytes().decode(errors="replace").split("\0")
            except OSError:
                continue
            for part in parts:
                value = part.partition("=")[2] if label == "env" else part
                if any(inside(v) for v in value.split(os.pathsep)):
                    why = label
                    break
        if not why:
            try:
                for fd in (entry / "fd").iterdir():
                    try:
                        if inside(os.readlink(fd)):
                            why = "fd"
                            break
                    except OSError:
                        continue
            except OSError:
                # fd/ unreadable: another user's process, or it exited mid-scan. Recorded as
                # the unprivileged blind spot in this function's docstring.
                pass
        if why:
            hits.append(f"{entry.name}({why})")
    return hits


def locked(primary: Path, wt: Path) -> bool:
    out = run(["git", "-C", str(primary), "worktree", "list", "--porcelain"]).stdout
    block = None
    for ln in out.splitlines() + [""]:
        if ln.startswith("worktree "):
            block = ln[9:]
        elif ln.startswith("locked") and block == str(wt):
            return True
    return False


def prs_on_head(repo: str, branch: str) -> tuple[list[dict] | None, str]:
    import json

    last = ""
    for _ in range(3):
        p = run(["gh", "pr", "list", "--repo", f"pcalnon/{repo}", "--head", branch, "--state", "all",
                 "--json", "number,state,mergedAt,headRefName,headRefOid,mergeCommit"])
        if p.returncode == 0:
            return json.loads(p.stdout or "[]"), ""
        last = (p.stderr or p.stdout).strip()[:200]
    return None, last


def pr_view(repo: str, num: int) -> tuple[dict | None, str]:
    import json

    p = run(["gh", "pr", "view", str(num), "--repo", f"pcalnon/{repo}",
             "--json", "number,state,mergedAt,headRefName,headRefOid,mergeCommit,closedAt"])
    if p.returncode != 0:
        return None, (p.stderr or p.stdout).strip()[:200]
    return json.loads(p.stdout), ""


def changed_paths(wt: Path) -> tuple[list[str], str]:
    """Paths the local branch changed since it left origin/main (committed only)."""
    mb = git(wt, "merge-base", "HEAD", "origin/main").stdout.strip()
    if not mb:
        return [], ""
    out = git(wt, "diff", "--name-only", "--no-renames", mb, "HEAD").stdout
    return [ln for ln in out.splitlines() if ln], mb


def survey(name: str, kind: str, prnum: int | None, accepted: set[str]) -> dict:
    wt = WORKTREES / name
    repo = name.split("--")[0]
    primary = primary_of(repo)
    r = {"name": name, "wt": wt, "repo": repo, "primary": primary, "kind": kind, "reasons": [], "notes": [],
         "branch": "", "remote_branch": False, "harvest": [], "dirty": [], "force": False, "pr": None}
    if not wt.is_dir():
        r["reasons"].append("MISSING -- already removed?")
        return r
    head = git(wt, "rev-parse", "HEAD").stdout.strip()
    branch = git(wt, "symbolic-ref", "-q", "--short", "HEAD").stdout.strip()
    r["branch"], r["head"] = branch, head
    if locked(primary, wt):
        r["reasons"].append("LOCKED")

    strong, weak = in_use(wt)
    if strong:
        r["reasons"].append(f"IN USE (STRONG): {', '.join(strong)}")
    if weak:
        r["notes"].append(f"weak argv mention by pid(s) {', '.join(weak)}")

    dirty, err = porcelain(wt)
    if dirty is None:
        r["reasons"].append(f"STATUS FAILED (fail closed): {err}")
        dirty = []
    r["dirty"] = dirty

    ign, err = porcelain(wt, ignored=True)
    if ign is None:
        r["reasons"].append(f"IGNORED-STATUS FAILED (fail closed): {err}")
        ign = []
    ignored = [ln[3:] for ln in ign if ln.startswith("!!")]
    env_files = [e for e in ignored if matches(e, ENV_FILE_GLOBS)]
    if env_files:
        r["reasons"].append(f"ignored .env-class file(s), never harvested -- a human must look: {len(env_files)}")
    r["harvest"] = [e for e in ignored if not matches(e, DISPOSABLE) and e not in env_files]
    r["ignored_disposable"] = len(ignored) - len(r["harvest"]) - len(env_files)

    # --- kind-specific gate: merged, reachable, closed, or superseded ----------------------
    sq = ""
    if kind == "pr":
        if not branch:
            r["reasons"].append("expected a branch, found detached HEAD")
            return r
        prs, err = prs_on_head(repo, branch)
        if prs is None:
            r["reasons"].append(f"PR LOOKUP FAILED (not the same as 'no PR'): {err}")
            return r
        open_ = [p["number"] for p in prs if p["state"] == "OPEN"]
        merged = [p for p in prs if p["state"] == "MERGED" and p.get("mergedAt")]
        if open_:
            r["reasons"].append(f"OPEN PR(s) on this head: {open_}")
        if prnum is not None and not any(p["number"] == prnum for p in merged):
            r["reasons"].append(f"expected PR #{prnum} MERGED on head {branch}; found {[(p['number'], p['state']) for p in prs]}")
        if not merged:
            r["reasons"].append(f"no MERGED PR on head {branch}: {[(p['number'], p['state']) for p in prs]}")
            return r
        pr = next((p for p in merged if p["number"] == prnum), merged[0])
        r["pr"] = pr
        sq = (pr.get("mergeCommit") or {}).get("oid", "")
        r["notes"].append(f"PR #{pr['number']} MERGED {pr['mergedAt']} squash={sq[:8]} head==PR-head:{head == pr['headRefOid']}")
    else:
        pr, err = pr_view(repo, prnum) if prnum else (None, "")
        if prnum and pr is None:
            r["reasons"].append(f"PR #{prnum} lookup failed: {err}")
        elif pr:
            sq = (pr.get("mergeCommit") or {}).get("oid", "") if pr["state"] == "MERGED" else ""
            r["notes"].append(f"PR #{pr['number']} {pr['state']} head={pr['headRefName']} mergedAt={pr.get('mergedAt')}")
            if pr["state"] == "OPEN":
                r["reasons"].append(f"PR #{prnum} is OPEN")
            if kind == "superseded" and pr["state"] != "MERGED":
                r["reasons"].append(f"superseding PR #{prnum} is not MERGED")
        if kind == "detached":
            if branch:
                r["reasons"].append(f"expected detached HEAD, found branch {branch}")
            anc = run(["git", "-C", str(primary), "merge-base", "--is-ancestor", head, "origin/main"]).returncode == 0
            pulls = run(["gh", "api", f"repos/pcalnon/{repo}/commits/{head}/pulls", "--jq", "[.[] | .number]"])
            if anc:
                r["notes"].append(f"HEAD {head[:8]} is an ancestor of origin/main")
            elif pulls.returncode == 0 and pulls.stdout.strip() not in ("", "[]"):
                r["notes"].append(f"HEAD {head[:8]} is a commit of PR(s) {pulls.stdout.strip()} on GitHub")
            elif name not in accepted:
                r["reasons"].append(f"HEAD {head[:8]} is on neither origin/main nor any PR -- review, then --accept")

    # --- content gate: nothing this tree holds is missing from what shipped ------------------
    refs = ([("squash", sq)] if sq else []) + [("main", "origin/main")]
    tally, differ = content_gate(wt, head, dirty, refs)
    r["notes"].append("content: " + (", ".join(f"{v} {k}" for k, v in sorted(tally.items())) or "no changed paths"))
    for p in differ:
        loc, shp = on_disk(wt, p), at(refs[0][1], p, wt)
        r["notes"].append(f"  DIFFERS: {p} (local {len(loc) if loc is not None else 'absent'} B, {refs[0][0]} {len(shp) if shp is not None else 'absent'} B)")
    if differ:
        if name in accepted:
            r["notes"].append("  differing paths ACCEPTED on review")
        else:
            r["reasons"].append(f"{len(differ)} path(s) not in what shipped -- review, then --accept {name}")
    if dirty:
        r["force"] = True  # git refuses a dirty tree without it; the content gate is what licenses it

    if branch:
        lr = run(["git", "-C", str(primary), "ls-remote", "--heads", "origin", branch])
        r["remote_branch"] = lr.returncode == 0 and bool(lr.stdout.strip())
    return r


def harvest(r: dict, dest: Path) -> list[str]:
    saved, wt = [], r["wt"]
    for rel in r["harvest"]:
        src = wt / rel
        if not src.exists():
            continue
        dst = dest / wt.name / rel.rstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
        else:
            shutil.copy2(src, dst)
        saved.append(rel)
    if r["force"]:
        # A dirty tree's own content, kept even though the content gate passed. `git diff HEAD`
        # does not carry untracked files, so those are copied as files.
        d = dest / wt.name / "_uncommitted"
        d.mkdir(parents=True, exist_ok=True)
        (d / "worktree-vs-HEAD.patch").write_text(git(wt, "diff", "HEAD", "--binary").stdout)
        (d / "local-commits-vs-origin-main.patch").write_text(git(wt, "log", "-p", "--binary", "origin/main..HEAD").stdout)
        (d / "status.txt").write_text("\n".join(r["dirty"]) + "\n")
        for ln in r["dirty"]:
            if ln.startswith("?? "):
                rel = ln[3:].strip('"')
                src, dst = wt / rel, d / "untracked" / rel.rstrip("/")
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
                elif src.is_file():
                    shutil.copy2(src, dst)
        saved.append("_uncommitted/ (diff, local commits, status, untracked files)")
    return saved


def digest(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--execute", action="store_true", help="actually remove (default: report only)")
    ap.add_argument("--harvest", type=Path, default=None, help="copy non-disposable ignored payload here first")
    ap.add_argument("--accept", action="append", default=[], help="worktree NAME whose reviewed content diff is accepted")
    ap.add_argument("--delete-remote", action="store_true", help="also delete the remote head of a MERGED/closed-and-shipped branch")
    ap.add_argument("--only", action="append", default=[], help="restrict to these worktree NAMEs")
    ap.add_argument("--no-primary-ff", action="store_true", help="never fast-forward a primary checkout (Phase 7)")
    ns = ap.parse_args(argv)
    accepted = set(ns.accept)

    for repo in sorted({n.split("--")[0] for n, _k, _p in INVENTORY}):
        f = run(["git", "-C", str(primary_of(repo)), "fetch", "origin", "--quiet"])
        print(f"fetch {repo}: {'ok' if f.returncode == 0 else 'FAILED ' + f.stderr.strip()[:120]}")
    print()

    rows = [survey(n, k, p, accepted) for n, k, p in INVENTORY if not ns.only or n in ns.only]
    for r in rows:
        mark = "REMOVE " if not r["reasons"] else "BLOCKED"
        print(f"{mark} {r['name']}")
        print(f"        kind={r['kind']} branch={r['branch'] or '(detached)'} remote-branch={r['remote_branch']}"
              f" ignored-disposable={r.get('ignored_disposable', 0)}{' FORCE-after-content-gate' if r['force'] else ''}")
        for n in r["notes"]:
            print(f"        {n}")
        for h in r["harvest"]:
            print(f"        harvest: {describe(r['wt'], h)}")
        for why in r["reasons"]:
            print(f"        !! {why}")
    ok = [r for r in rows if not r["reasons"]]
    print(f"\n{len(ok)} removable, {len(rows) - len(ok)} blocked   [{'EXECUTE' if ns.execute else 'REPORT ONLY'}]")
    for repo in sorted({r["repo"] for r in rows}):
        print(f"primary {repo}: visible holders {primary_holders(primary_of(repo)) or 'none'}")
    if not ns.execute:
        return 0
    needs = [r for r in ok if r["harvest"] or r["force"]]
    if needs and ns.harvest is None:
        print(f"refusing: {len(needs)} removable tree(s) carry payload to harvest; pass --harvest DIR")
        return 2

    touched = set()
    for r in ok:
        wt, primary = r["wt"], r["primary"]
        print(f"\n== {r['name']}")
        strong, _weak = in_use(wt)  # TOCTOU re-check
        now, err = porcelain(wt)
        if strong or now is None or digest(now) != digest(r["dirty"]):
            print(f"   SKIP: state moved since the survey (in-use={strong} status-err={err!r})")
            continue
        if r["harvest"] or r["force"]:
            saved = harvest(r, ns.harvest.resolve())
            print(f"   harvested {len(saved)} -> {ns.harvest.resolve() / wt.name}")
        cmd = ["git", "-C", str(primary), "worktree", "remove"] + (["--force"] if r["force"] else []) + [str(wt)]
        rm = run(cmd)
        if rm.returncode != 0:
            print(f"   !! remove failed: {rm.stderr.strip()[:200]}")
            continue
        touched.add(r["repo"])
        print("   worktree removed")
        run(["git", "-C", str(primary), "worktree", "prune"])
        if r["branch"]:
            d = run(["git", "-C", str(primary), "branch", "-D", r["branch"]])
            print(f"   local branch: {(d.stdout or d.stderr).strip()}")
        if ns.delete_remote and r["branch"] and r["remote_branch"]:
            prs, _e = prs_on_head(r["repo"], r["branch"])
            if prs is None or any(p["state"] == "OPEN" for p in prs):
                print("   remote branch KEPT: open PR or lookup failed (fail closed)")
            else:
                d = run(["gh", "api", "-X", "DELETE", f"repos/pcalnon/{r['repo']}/git/refs/heads/{r['branch']}"])
                print(f"   remote branch: {'deleted' if d.returncode == 0 else 'DELETE FAILED ' + d.stderr.strip()[:120]}")

    for repo in sorted(touched):  # Phase 7: the primary returns to an up-to-date main
        primary = primary_of(repo)
        cur = run(["git", "-C", str(primary), "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        pdirty, _ = porcelain(primary)
        held = primary_holders(primary)
        if ns.no_primary_ff:
            print(f"\nprimary {repo}: not pulled (--no-primary-ff); visible holders: {held or 'none'}")
        elif held:
            print(f"\nprimary {repo} is HELD by live process(es) {held} -- not pulling (frozen while imported)")
        elif cur != "main":
            print(f"\nprimary {repo} is on {cur!r}, not main -- not pulling (owner's call)")
        elif pdirty is None or pdirty:
            print(f"\nprimary {repo} is dirty or unreadable -- not pulling (F-6 guard)")
        else:
            ff = run(["git", "-C", str(primary), "merge", "--ff-only", "origin/main"])
            sha = run(["git", "-C", str(primary), "rev-parse", "--short=8", "HEAD"]).stdout.strip()
            print(f"\nprimary {repo}: {'fast-forwarded' if ff.returncode == 0 else 'FF FAILED ' + ff.stderr.strip()[:120]} -> {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
