#!/usr/bin/env python3
"""
Archive, then remove, the Cursor flood-4 arc's worktrees and local branches, as ruling 7 and the 2026-11-25 rulings say.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 7: the arc's worktree cleanup, session 13)
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- one-off (the Overtoad runs it from a terminal: a dry run, then --execute)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 7);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_flood4-session12-ruling-26-landed-ruling-7-ruled-cleanup-script-next.md;
         util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash (the model this follows)

Why
---
Ruling 7 ("All, after record merges"): the arc's worktrees go once its record has merged (first as juniper-ml#2530,
2026-11-09; with rulings 15-48 as juniper-ml#2635, 2026-11-24), each only after its PR is confirmed merged and its
tmp/ is checked under the retention rule (the record's words; here, moved into the archive). Flood-4
session 12's read-only inventory (worktree hidden-scribbling-toast, tmp/flood4/session12/r7/: inventory.json and
plan.txt, steps R1-R10) found 282 candidates. The Overtoad ruled on 2026-11-25 at 01:46Z (labels verbatim):

  R7-Q1  "You run the script (Recommended)"         this script: a dry run first, then --execute, from a terminal
  R7-Q2  "9 session launch worktrees", "3 ruling-37 marker trees", "6 inferred-provenance trees",
         "Delete the 13 sim dirs"                   all of batch B goes with batch A; the 13 plain directories are
                                                    deleted, keeping only a file list -- 12 ml-propose simulation trees;
                                                    the 13th (juniper-ml--val--flood4r2-n4-claims) is the N-4 claims
                                                    lens's fix tree, which the question did not describe: held
                                                    (PLAIN_HOLD) until the Overtoad rules on it
  R7-Q3  "juniper-ml/tmp/ (Recommended)"            the archive: juniper-ml/tmp/worktree-archive-2026-11-24-flood4/
  R7-Q4  "Delete branches, keep refs (Recommended)" the 87 local branches go, each full sha recorded first; the
                                                    refs/flood4/* refs stay

What it does
------------
Selection: batch A (265 entries, 13 of them plain directories: 12 simulation trees and the N-4 claims lens's fix tree), batch B (13) and, LAST,
humming-stargazing-papert. It refuses to start unless those counts and the 87 branches match the ruling (override:
--ruled-counts), and it never touches curious-plotting-hummingbird, hidden-scribbling-toast or
playful-scribbling-kite. Order (plan.txt ORDER): A1 the seven other repos' trees, one repo at a time; A2 juniper-ml's
trees under worktrees/ (the 11-06 five first, the 13 plain directories last); A3 the agent worktrees (the
carriers a handoff said to keep, last); B; then humming, only when nothing else this run was skipped (other than
"absent" or PLAIN_HOLD's hold) or failed (unless --only names it). Humming is live while the Overtoad's terminal tab
in it (pid 39566, pts/11) is open: close it first. Every precondition is re-read at run time; an entry whose state
moved since the inventory is SKIPPED and reported, never forced.

For each linked worktree (dry run: everything up to the first change, printed):
  R1  present, a linked worktree whose .git points into the expected primary, registered there, not locked, not
      prunable, holding no other registered worktree.
  R2  not live: no process has its cwd, root or an open file inside, and no file in it is newer than --quiet-hours
      (6); every entry is owned by this user.
  R3  HEAD and branch equal the inventory's.
  R4  every path `git status` lists outside tmp/ is compared, by blob, with origin/main, HEAD, the commit its name records (only when it is on origin/main's or HEAD's history) and the
      merge and head commits of its related PRs (and, for humming, session 9's HEAD 734aab58): equal bytes, or the
      2026-11-20..22 substitution of a base's bytes ("Owner" -> "The Overtoad", then "owner" -> "Overtoad"), or a
      symlink the substitution turned into a copy of its target, is on a base. Anything else is SAVED into
      saved/ (copied; untracked directories moved), tracked ones also as saved/uncommitted.patch (in batch B's trees the substitution did not reach, every tracked change, as 2026-11-23's juniper-data patch), and staged content
      that is on no base as saved/<path>.staged-index. A sha256 of every saved file goes into MANIFEST.txt.
  R5  ignored entries outside tmp/ that are not caches are moved to ignored/.
  R6  commits of HEAD that are not on origin/main, and commits only the worktree's or its branch's reflog holds, go into
      commits.bundle (verified; the reflog-only ones through temporary refs refs/r7-archive/<run>/<n>, deleted after),
      listed in MANIFEST.txt.
  R7  tmp/ is moved (a rename on one filesystem) into the archive as NAME/tmp/, its entry count checked after.
  R8  `git worktree remove --force` (the worktree's admin directory, which it deletes -- HEAD, index, logs/HEAD, any
      in-progress operation -- is copied to NAME/worktree-admin/ first), then the registration is confirmed gone.
For each of the 13 plain directories (PLAIN_HOLD's one is skipped until the Overtoad rules): R1 (no .git anywhere in
it, no registered worktree inside), R2, then a FILELIST.tsv.gz (path, type, size, mtime) and deletion.
R9  after each wave, `git worktree prune -n -v` in each touched primary, as a REPORT: `git worktree remove` already drops
    each removed tree's registration (R8 confirms it), so a real prune could only drop registrations this run never
    touched -- another session's moved or unmounted tree, with its HEAD, index and reflog. A departure from plan.txt's
    R9 ("prune per primary after each wave"), for that reason; anything stale is listed, never pruned.
R10 branches (after their worktrees are gone): the tip still equals the inventory's HEAD, checked out nowhere, no
    remote branch of that name; the line goes into deleted_branches.txt (flushed to disk) before `git branch -D`.
The archive gets README.md, INDEX.tsv, runs/ (each execute run's log and JSON) and provenance/ (the inputs).

Usage
-----
    python3 util/ad-hoc/2026-11-25_flood4_r7_cleanup.py --inventory INV.json --pr-commits PRS.jsonl [--fetch]
    python3 util/ad-hoc/2026-11-25_flood4_r7_cleanup.py --inventory INV.json --pr-commits PRS.jsonl [--fetch] --execute

--fetch runs `git fetch origin main` and fetches the related PRs' heads (refs/pull/N/head, into FETCH_HEAD only) in
each primary first: the only write a dry run then makes, and it lets more files be recognised as landed. --only NAME
(repeatable) restricts the run to those entries. --list checks the selection and prints it in run order, running no
git and writing nothing. --held keep|archive|delete says what happens to PLAIN_HOLD's directory (default keep: it
stays, skipped without holding humming back). --json PATH writes the per-entry results. Exit 0: done; 1: some entry
failed or was left partial; 2: refused to start.

Version 1.1.0 (2026-11-25) is 1.0.0 after the two validation lenses of flood-4 session 13 (code: C1-C13; claims:
K1-K15; tmp/flood4/session13/val_code/ and val_claims/ in worktree hidden-scribbling-toast), and --held.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess  # nosec B404 - runs git with fixed argument lists, never through a shell
import sys
import time
from pathlib import Path

SCRIPT = "util/ad-hoc/2026-11-25_flood4_r7_cleanup.py"
VERSION = "1.1.0"
ARCHIVE_NAME = "worktree-archive-2026-11-24-flood4"
PRIMARIES = (
    "juniper-ml",
    "juniper-data",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
)
NEVER = frozenset({"curious-plotting-hummingbird", "hidden-scribbling-toast", "playful-scribbling-kite"})
LAST = "humming-stargazing-papert"
LAST_EXTRA_BASE = ("session-9 HEAD", "734aab58")
PROTECTED_BRANCHES = frozenset(
    {
        "main",
        "master",
        "worktree-humming-stargazing-papert",
        "worktree-hidden-scribbling-toast",
        "worktree-playful-scribbling-kite",
        "worktree-curious-plotting-hummingbird",
        "fix/handoff-passphrase-resolved",
    }
)
KEEP_CARRIERS = (
    "agent-a7aa0806f2312b786",
    "agent-a0f16311d9dabda6f",
    "agent-a5303a15bb4329057",
    "agent-a4cd1de89c2b57ea3",
    "agent-a89a668e6d43bcee2",
    "agent-a9898bd52fb78c449",
    "agent-aa1160aea3f9c907d",
)
RULED_COUNTS = "265:13:13:87:1"  # batch A entries : batch B entries : simulation dirs : local branches : humming
RULED_INVENTORY_SHA256 = "2cfe9f61f718e51afac2a0382611dea990ae263f0e2e993a731b5183afbab995"  # tmp/flood4/session12/r7/inventory.json: the file the 2026-11-25 rulings were asked on
CACHE_RE = re.compile(r"(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.hypothesis|[^/]*\.egg-info|\.coverage[^/]*|htmlcov)/?$")
SUBST_WORD = b"Overtoad"
BIG = 64 * 1024 * 1024
LARGE_SAVE_FILES = 200
LARGE_SAVE_BYTES = 100 * 1024 * 1024
PR_RE = re.compile(r"^(juniper-[a-z-]+)#(\d+)\b")
SHA_LINE_RE = re.compile(r"^([0-9a-f]{40}) (\w+)$")
GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE")
# R7-Q2's "Delete the 13 sim dirs" was asked as "The ml-propose validation runs' simulation trees" (tmp/flood4/session13/r7_dialog.json:47);
# this one is not one: it is the N-4 claims lens's fix tree (humming-stargazing-papert/tmp/flood4r2-val/n4-claims-lens/findings.json:6
# names it "fix_tree") and holds the only unsubstituted copy of the set that lens validated. It is held (skipped, reported, not
# blocking) until the Overtoad rules on it: --held archive moves it whole into the archive, --held delete deletes it with the
# other twelve, and the default --held keep leaves it where it is.
PLAIN_HOLD = frozenset({"juniper-ml--val--flood4r2-n4-claims--20261109-0958--f85fbc8b"})
HOLD_REASON = "held for the Overtoad's word: the N-4 claims lens's fix tree, not an ml-propose simulation tree (PLAIN_HOLD)"
BLOCKING_SKIP_EXEMPT = ("absent", HOLD_REASON)


class GitError(RuntimeError):
    """A git command exited non-zero where the script needs it to succeed."""


class Refusal(RuntimeError):
    """The run cannot start: the inputs or the host do not match what the ruling covers."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1000 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1000.0
    return f"{n:.2f} TB"


class Out:
    """Prints to stdout and, during --execute, to the run's log in the archive."""

    def __init__(self) -> None:
        self.fh = None
        self.early: list[str] = []

    def __call__(self, msg: str = "") -> None:
        print(msg, flush=True)
        if self.fh is None:
            self.early.append(msg)
        else:
            self.fh.write(msg + "\n")
            self.fh.flush()


OUT = Out()


def _git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
    return env


GIT_ENV = _git_env()


def git(where: Path, *args: str, stdin: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run `git -C <where> <args>` (argv list, no shell) and capture bytes."""
    proc = subprocess.run(["git", "-C", str(where), *args], input=stdin, capture_output=True, env=GIT_ENV, check=False)  # nosec B603 B607
    if check and proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git -C {where} {' '.join(args[:6])}: exit {proc.returncode}: {err[:400]}")
    return proc


def git_text(where: Path, *args: str, check: bool = True) -> str:
    return git(where, *args, check=check).stdout.decode("utf-8", "surrogateescape").strip()


def substitute(data: bytes) -> bytes:
    """The 2026-11-20..22 pass as util/ad-hoc/2026-11-23_flood4_s10_verify_recover.py records it: "Owner" -> "The Overtoad", then "owner" -> "Overtoad"."""
    return data.replace(b"Owner", b"The Overtoad").replace(b"owner", SUBST_WORD)


def inverses(data: bytes) -> list[tuple[str, bytes]]:
    """The plain and two-step inverses: reconstructions only, used to annotate a saved file, never to discard one."""
    return [
        ("plain inverse", data.replace(SUBST_WORD, b"owner")),
        ("two-step inverse", data.replace(b"The Overtoad", b"Owner").replace(SUBST_WORD, b"owner")),
    ]


def blob_sha(data: bytes) -> str:
    digest = hashlib.sha1(b"blob %d\0" % len(data), usedforsecurity=False)
    digest.update(data)
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    """sha256 of a file's bytes, or of a symlink's target text (prefixed 'symlink:')."""
    if path.is_symlink():
        return "symlink:" + hashlib.sha256(os.readlink(os.fsencode(path))).hexdigest()
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_entry(path: Path) -> tuple[str, bytes | None, int, str]:
    """(kind, bytes or None, size, git blob sha) of a worktree path; kind is file, symlink, dir, absent or other."""
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return "absent", None, 0, ""
    if stat.S_ISLNK(st.st_mode):
        data = os.readlink(os.fsencode(path))
        return "symlink", data, len(data), blob_sha(data)
    if stat.S_ISDIR(st.st_mode):
        return "dir", None, 0, ""
    if not stat.S_ISREG(st.st_mode):
        return "other", None, st.st_size, ""
    if st.st_size <= BIG:
        data = path.read_bytes()
        return "file", data, len(data), blob_sha(data)
    digest = hashlib.sha1(b"blob %d\0" % st.st_size, usedforsecurity=False)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return "file", None, st.st_size, digest.hexdigest()


def walk(root: Path, cutoff: float, uid: int, keep: int = 5) -> dict:
    """One pass over a tree, never following symlinks: counts, bytes, the tmp/ subtree's share, the newest mtime, entries
    newer than the cutoff, entries not owned by uid, and .git entries below the top."""
    res = {"entries": 0, "bytes": 0, "tmp_entries": 0, "tmp_bytes": 0, "newest": 0.0, "recent": 0, "recent_eg": [], "foreign": 0, "foreign_eg": [], "nested_git": [], "errors": []}
    stack = [(str(root), 0, False)]
    while stack:
        d, depth, in_tmp = stack.pop()
        try:
            it = os.scandir(d)
        except OSError as exc:
            res["errors"].append(f"{d}: {exc}")
            continue
        with it:
            for e in it:
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError as exc:
                    res["errors"].append(f"{e.path}: {exc}")
                    continue
                rel = os.path.relpath(e.path, root)
                sub_tmp = in_tmp or (depth == 0 and e.name == "tmp")
                res["entries"] += 1
                if in_tmp:
                    res["tmp_entries"] += 1
                if stat.S_ISREG(st.st_mode):
                    res["bytes"] += st.st_size
                    if in_tmp:
                        res["tmp_bytes"] += st.st_size
                res["newest"] = max(res["newest"], st.st_mtime)
                if st.st_mtime > cutoff:
                    res["recent"] += 1
                    if len(res["recent_eg"]) < keep:
                        res["recent_eg"].append(f"{rel} ({iso(st.st_mtime)})")
                if st.st_uid != uid:
                    res["foreign"] += 1
                    if len(res["foreign_eg"]) < keep:
                        res["foreign_eg"].append(f"{rel} (uid {st.st_uid})")
                if e.name == ".git" and depth > 0:
                    res["nested_git"].append(rel)
                if stat.S_ISDIR(st.st_mode):
                    stack.append((e.path, depth + 1, sub_tmp))
    return res


def count_entries(root: Path) -> int:
    n = 0
    stack = [str(root)]
    while stack:
        with os.scandir(stack.pop()) as it:
            for e in it:
                n += 1
                if e.is_dir(follow_symlinks=False):
                    stack.append(e.path)
    return n


def proc_links() -> list[tuple[int, str]]:
    """(pid, target) for every process's cwd and root, and every other process's open files."""
    me = os.getpid()
    links: list[tuple[int, str]] = []
    with os.scandir("/proc") as procs:
        for p in procs:
            if not p.name.isdigit():
                continue
            pid = int(p.name)
            for name in ("cwd", "root", "exe"):
                try:
                    links.append((pid, os.readlink(f"/proc/{pid}/{name}").removesuffix(" (deleted)")))
                except OSError:
                    continue  # the process exited, or belongs to another user
            if pid == me:
                continue
            try:
                with open(f"/proc/{pid}/maps", encoding="utf-8", errors="surrogateescape") as fh:
                    for line in fh:
                        parts = line.rstrip("\n").split(None, 5)
                        if len(parts) == 6 and parts[5].startswith("/"):
                            links.append((pid, parts[5].removesuffix(" (deleted)")))
                with open(f"/proc/{pid}/cmdline", "rb") as fh:
                    links.extend((pid, os.fsdecode(arg)) for arg in fh.read().split(b"\0") if arg.startswith(b"/"))
            except OSError:
                pass  # the process exited, or belongs to another user
            try:
                with os.scandir(f"/proc/{pid}/fd") as fds:
                    for fd in fds:
                        try:
                            links.append((pid, os.readlink(fd.path)))
                        except OSError:
                            continue  # the descriptor closed while being read
            except OSError:
                continue  # another user's process: its descriptors are not readable
    return links


def holders(path: Path) -> list[int]:
    p = str(path)
    pre = p + "/"
    return sorted({pid for pid, target in proc_links() if target == p or target.startswith(pre)})


def inside(child: Path, parent: Path) -> bool:
    return child != parent and str(child).startswith(str(parent) + "/")


def within(root: Path, target: Path) -> bool:
    """True when target's parent, every symlink resolved, is root or below it (nothing is written through a link)."""
    real_root = os.path.realpath(root)
    parent = os.path.realpath(target.parent)
    return parent == real_root or parent.startswith(real_root + "/")


def safe_rel(rel: str) -> bool:
    parts = rel.split("/")
    return bool(rel) and not rel.startswith("/") and ".." not in parts and "" not in parts[:-1]


def fsync_append(path: Path, *lines: str) -> None:
    """Append lines and force them to disk before returning (a record must exist before the act it records)."""
    with path.open("a", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write("".join(line + "\n" for line in lines))
        fh.flush()
        os.fsync(fh.fileno())


class Primary:
    """One primary checkout: its registrations, origin/main and remote branch names, read once and refreshed on demand."""

    def __init__(self, root: Path, name: str) -> None:
        self.name = name
        self.path = root / name
        self._records: list[dict] | None = None
        self._remote_heads: set[str] | None = None
        self._remote_read = False
        self.origin_main: str | None = None
        self.shallow = False
        self.fetch_note = ""

    def setup(self, fetch: bool, pr_heads: list[str]) -> None:
        if not (self.path / ".git").is_dir():
            raise Refusal(f"{self.path} is not a primary checkout (no .git directory)")
        fmt = git_text(self.path, "rev-parse", "--show-object-format", check=False) or "sha1"
        if fmt != "sha1":
            raise Refusal(f"{self.path}: object format {fmt}; this script computes sha1 blob ids")
        self.shallow = git_text(self.path, "rev-parse", "--is-shallow-repository") == "true"
        if fetch:
            p = git(self.path, "fetch", "--quiet", "--no-tags", "origin", "+refs/heads/main:refs/remotes/origin/main", check=False)
            self.fetch_note = "fetched origin main" if p.returncode == 0 else f"fetch of main FAILED ({p.stderr.decode('utf-8', 'replace').strip()[:160]})"
            if pr_heads:
                q = git(self.path, "fetch", "--quiet", "--no-tags", "origin", *pr_heads, check=False)
                self.fetch_note += f"; {len(pr_heads)} PR head ref(s) " + ("fetched" if q.returncode == 0 else "NOT fetched (" + q.stderr.decode("utf-8", "replace").strip()[:160] + ")")
        self.origin_main = git_text(self.path, "rev-parse", "--verify", "-q", "refs/remotes/origin/main^{commit}", check=False) or None

    def records(self, refresh: bool = False) -> list[dict]:
        if self._records is None or refresh:
            raw = git(self.path, "worktree", "list", "--porcelain", "-z").stdout.decode("utf-8", "surrogateescape")
            recs: list[dict] = []
            cur: dict = {}
            for field in raw.split("\0"):
                if field == "":
                    if cur:
                        recs.append(cur)
                        cur = {}
                    continue
                key, _, val = field.partition(" ")
                cur[key] = val if val else True
            if cur:
                recs.append(cur)
            self._records = recs
        return self._records

    def record_for(self, path: Path, refresh: bool = False) -> dict | None:
        for rec in self.records(refresh):
            if rec.get("worktree") == str(path):
                return rec
        return None

    def registered_paths(self) -> list[Path]:
        return [Path(r["worktree"]) for r in self.records() if isinstance(r.get("worktree"), str)]

    def remote_heads(self) -> set[str] | None:
        if not self._remote_read:
            self._remote_read = True
            p = git(self.path, "ls-remote", "--heads", "origin", check=False)
            if p.returncode == 0:
                names = set()
                for line in p.stdout.decode("utf-8", "surrogateescape").splitlines():
                    parts = line.split("\t")
                    if len(parts) == 2 and parts[1].startswith("refs/heads/"):
                        names.add(parts[1][len("refs/heads/") :])
                self._remote_heads = names
        return self._remote_heads


class Context:
    def __init__(self, args: argparse.Namespace, root: Path, archive: Path, prs: dict) -> None:
        self.args = args
        self.root = root
        self.archive = archive
        self.prs = prs
        self.execute = args.execute
        self.cutoff = time.time() - args.quiet_hours * 3600
        self.uid = os.getuid()
        self.run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.primaries: dict[str, Primary] = {}

    def primary(self, name: str) -> Primary:
        return self.primaries[name]

    def all_registered(self) -> list[Path]:
        out: list[Path] = []
        for prim in self.primaries.values():
            out.extend(prim.registered_paths())
        return out


def pr_keys(row: dict) -> list[tuple[str, int]]:
    keys = []
    for s in list(row.get("related_prs") or []) + list(row.get("own_prs") or []):
        m = PR_RE.match(s)
        if m:
            keys.append((m.group(1), int(m.group(2))))
    return keys


def resolve(wt: Path, rev: str) -> str | None:
    return git_text(wt, "rev-parse", "--verify", "-q", rev + "^{commit}", check=False) or None


def bases_for(ctx: Context, row: dict, wt: Path, prim: Primary, head: str) -> tuple[list[tuple[str, str]], list[str]]:
    """The commits a worktree file is compared with, and notes on the ones that are not available here."""
    bases: list[tuple[str, str]] = []
    notes: list[str] = []
    if prim.origin_main:
        bases.append(("origin/main", prim.origin_main))
    bases.append(("HEAD", head))
    if row.get("name_sha"):
        sha = resolve(wt, row["name_sha"])
        tips = ([prim.origin_main] if prim.origin_main else []) + [head]
        if sha and any(git(wt, "merge-base", "--is-ancestor", sha, tip, check=False).returncode == 0 for tip in tips):
            bases.append(("creation", sha))
        elif sha:
            notes.append(f"creation sha {sha[:8]} is on neither origin/main's nor HEAD's history: not a base, so its files are saved")
        else:
            notes.append(f"creation sha {row['name_sha']} not found here")
    for repo, number in pr_keys(row):
        if repo != row["repo"]:
            notes.append(f"{repo}#{number} is another repository's PR: not a base here")
            continue
        info = ctx.prs.get(f"{repo}#{number}") or {}
        for kind in ("merge", "head"):
            sha = info.get(kind)
            if not sha:
                continue
            if git(wt, "cat-file", "-e", sha + "^{commit}", check=False).returncode == 0:
                bases.append((f"{repo}#{number} {kind}", sha))
            else:
                notes.append(f"{repo}#{number} {kind} {sha[:8]} not in this object store" + ("" if ctx.args.fetch else " (--fetch brings it)"))
    if row["name"] == LAST:
        extra = ctx.args.last_extra_base
        sha = resolve(wt, extra)
        if sha:
            bases.append((f"{LAST_EXTRA_BASE[0]} {extra}", sha))
        else:
            notes.append(f"{LAST_EXTRA_BASE[0]} {extra} not found here")
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for label, sha in bases:
        if sha not in seen:
            seen.add(sha)
            unique.append((label, sha))
    return unique, notes


def status_entries(wt: Path) -> list[tuple[str, str]]:
    """Every path `git status` lists, outside tmp/: tmp/ moves whole (R7), ignored or not, so it is not compared file by file."""
    raw = git(wt, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames", "--ignore-submodules=none", "--", ".", ":(exclude,top)tmp").stdout
    out = []
    for field in raw.split(b"\0"):
        if field:
            path = field[3:].decode("utf-8", "surrogateescape")
            if path.rstrip("/") != "tmp" and not path.startswith("tmp/"):
                out.append((field[:2].decode("ascii", "replace"), path))
    return out


def index_blobs(wt: Path) -> dict[str, str]:
    raw = git(wt, "ls-files", "-s", "-z").stdout
    out: dict[str, str] = {}
    for rec in raw.split(b"\0"):
        if not rec or b"\t" not in rec:
            continue
        meta, path = rec.split(b"\t", 1)
        parts = meta.split(b" ")
        if len(parts) >= 3 and parts[2] == b"0":
            out[path.decode("utf-8", "surrogateescape")] = parts[1].decode("ascii")
    return out


def batch_check(wt: Path, specs: list[str]) -> list[str | None]:
    """The blob sha each '<commit>:<path>' names, or None (absent, or not a blob)."""
    if not specs:
        return []
    data = "".join(s + "\n" for s in specs).encode("utf-8", "surrogateescape")
    lines = git(wt, "cat-file", "--batch-check=%(objectname) %(objecttype)", stdin=data).stdout.decode("utf-8", "surrogateescape").split("\n")
    out: list[str | None] = []
    for i in range(len(specs)):
        m = SHA_LINE_RE.match(lines[i]) if i < len(lines) else None
        out.append(m.group(1) if m and m.group(2) == "blob" else None)
    return out


def blob_contents(wt: Path, shas: list[str]) -> dict[str, bytes]:
    shas = sorted(set(shas))
    if not shas:
        return {}
    raw = git(wt, "cat-file", "--batch", stdin="".join(s + "\n" for s in shas).encode("ascii")).stdout
    out: dict[str, bytes] = {}
    pos = 0
    for sha in shas:
        nl = raw.index(b"\n", pos)
        header = raw[pos:nl].decode("ascii", "replace").split(" ")
        pos = nl + 1
        if len(header) == 3 and header[1] == "blob":
            size = int(header[2])
            out[sha] = raw[pos : pos + size]
            pos += size + 1
    return out


def head_mode(wt: Path, path: str) -> tuple[str, str] | None:
    raw = git(wt, "--literal-pathspecs", "ls-tree", "-z", "HEAD", "--", path, check=False).stdout
    for rec in raw.split(b"\0"):
        if rec and b"\t" in rec:
            meta = rec.split(b"\t", 1)[0].decode("ascii", "replace").split(" ")
            if len(meta) == 3:
                return meta[0], meta[2]
    return None


def classify(wt: Path, entries: list[tuple[str, str]], bases: list[tuple[str, str]]) -> list[dict]:
    """R4: one item per status path (plus one per staged-only content), each with a category and whether it is saved."""
    items: list[dict] = []
    for xy, raw_path in entries:
        path = raw_path.rstrip("/")
        kind, data, size, wsha = read_entry(wt / path)
        items.append({"xy": xy, "path": path, "kind": kind, "size": size, "wsha": wsha, "data": data, "tracked": xy != "??", "category": "", "save": False, "detail": ""})
    checkable = [it for it in items if it["kind"] in ("file", "symlink") and "\n" not in it["path"] and not it["path"].endswith("\r")]
    specs = [f"{sha}:{it['path']}" for it in checkable for _, sha in bases]
    found = batch_check(wt, specs)
    per_item: dict[int, list[str | None]] = {}
    for n, it in enumerate(checkable):
        per_item[id(it)] = found[n * len(bases) : (n + 1) * len(bases)]
    # The substitution test needs base bytes: fetched one base at a time, and only for files still unexplained,
    # so memory holds one base's blobs at once (a rename-touched tree lists ~2,450 rewritten files).
    subst_hit: dict[int, str] = {}
    pending = [it for it in checkable if it["wsha"] not in per_item[id(it)] and it["data"] is not None and SUBST_WORD in it["data"]]
    for b, (label, _) in enumerate(bases):
        todo = [it for it in pending if id(it) not in subst_hit and per_item[id(it)][b]]
        contents = blob_contents(wt, [per_item[id(it)][b] for it in todo])
        for it in todo:
            blob = contents.get(per_item[id(it)][b])
            if blob is not None and substitute(blob) == it["data"]:
                subst_hit[id(it)] = label
    idx = index_blobs(wt) if any(it["tracked"] and it["xy"][0] not in " ?D" for it in items) else {}
    extra: list[dict] = []
    for it in items:
        if it["kind"] == "absent":
            it["category"] = "deleted" if it["tracked"] else "vanished"
            it["detail"] = "absent from the worktree; its last committed copy is in git" if it["tracked"] else "listed by git status, gone when read"
        elif it["kind"] == "dir":
            it.update(category="untracked-directory" if not it["tracked"] else "tracked-directory", save=True, detail="moved whole into saved/")
        elif it["kind"] == "other":
            it.update(category="special-file", detail="not a regular file, symlink or directory: listed, not saved")
        elif "\n" in it["path"] or it["path"].endswith("\r"):
            it.update(category="unclassifiable-path", save=True, detail="a newline in the path: saved without comparison")
        else:
            _classify_one(wt, it, bases, per_item[id(it)], subst_hit.get(id(it)))
        if it["tracked"] and it["xy"][0] not in " ?D" and it["path"] in idx:
            isha = idx[it["path"]]
            on_base = per_item.get(id(it)) or []
            if isha != it["wsha"] and isha not in on_base:
                extra.append({"xy": it["xy"], "path": it["path"], "kind": "staged", "size": 0, "wsha": isha, "data": None, "tracked": True, "category": "staged-only", "save": True, "detail": f"index blob {isha[:12]} differs from the worktree file and from every base"})
    return items + extra


def _classify_one(wt: Path, it: dict, bases: list[tuple[str, str]], base_shas: list[str | None], subst_label: str | None) -> None:
    for (label, _), bsha in zip(bases, base_shas):
        if bsha and bsha == it["wsha"]:
            it.update(category="on-base", detail=label)
            return
    if subst_label:
        it.update(category="substitution-of-base", detail=subst_label)
        return
    data = it["data"]
    if "T" in it["xy"] and it["kind"] == "file" and data is not None:
        mode = head_mode(wt, it["path"])
        if mode and mode[0] == "120000":
            link = blob_contents(wt, [mode[1]]).get(mode[1], b"").decode("utf-8", "surrogateescape")
            target = posixpath.normpath(posixpath.join(posixpath.dirname(it["path"]), link))
            if link and not link.startswith("/") and safe_rel(target):
                tshas = batch_check(wt, [f"{sha}:{target}" for _, sha in bases])
                tcont = blob_contents(wt, [s for s in tshas if s])
                for (label, _), tsha in zip(bases, tshas):
                    if tsha and (tsha == it["wsha"] or (tsha in tcont and substitute(tcont[tsha]) == data)):
                        it.update(category="symlink-copy", detail=f"HEAD has a symlink to {target}; the file equals {target} at {label}" + ("" if tsha == it["wsha"] else " after the substitution"))
                        return
    note = ""
    if data is not None and SUBST_WORD in data:
        for name, inv in inverses(data):
            isha = blob_sha(inv)
            hits = [label for (label, _), bsha in zip(bases, base_shas) if bsha == isha]
            if hits:
                note = f"the {name} equals {hits[0]}: saved anyway (an inverse is a reconstruction)"
                break
    if it["kind"] == "file" and data is None:
        it.update(category="large-not-on-any-base", save=True, detail=f"{human(it['size'])}, not compared beyond its blob id")
    else:
        it.update(category="not-on-any-base", save=True, detail=note or "on no base")


def ignored_entries(wt: Path) -> list[str]:
    raw = git(wt, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory").stdout
    out = []
    for field in raw.split(b"\0"):
        if not field:
            continue
        e = field.decode("utf-8", "surrogateescape")
        if e.rstrip("/") == "tmp" or e.startswith("tmp/"):
            continue
        out.append(e)
    return out


def whole_patch(row: dict, items: list[dict]) -> bool:
    """R7-Q2 ("The worker one's uncommitted edits saved as a patch first"): batch B's trees the substitution did not reach
    get the whole tracked diff as their patch; every other tree, the diff of its saved tracked paths only."""
    return row["batch"] == "B" and "RENAME-TOUCHED" not in (row.get("flags") or []) and any(it["tracked"] for it in items)


def new_result(row: dict, wave: str) -> dict:
    return {
        "name": row["name"],
        "repo": row["repo"],
        "wave": wave,
        "batch": row["batch"],
        "kind": row["kind"],
        "path": row["path"],
        "branch": row.get("branch", ""),
        "inventory_head": row.get("head_sha", ""),
        "outcome": "",
        "reasons": [],
        "notes": [],
        "saved": [],
        "saved_count": 0,
        "saved_bytes": 0,
        "ignored_moved": [],
        "tmp_entries": 0,
        "tmp_bytes": 0,
        "bytes": 0,
        "bundle_commits": 0,
        "whole_patch": False,
        "head": "",
    }


def skip(res: dict, reason: str) -> dict:
    res["outcome"] = "skip"
    res["reasons"].append(reason)
    OUT(f"   => SKIP: {reason}")
    return res


def fail(res: dict, reason: str, partial: bool = False) -> dict:
    res["outcome"] = "partial" if partial else "fail"
    res["reasons"].append(reason)
    OUT(f"   => {'PARTIAL' if partial else 'FAILED'}: {reason}")
    return res


def blocking(res: dict) -> bool:
    if res["outcome"] in ("fail", "partial"):
        return True
    return res["outcome"] == "skip" and not all(r in BLOCKING_SKIP_EXEMPT for r in res["reasons"])


def check_live(res: dict, path: Path, ctx: Context) -> dict | None:
    """R2. Returns the walk, or None after recording a skip."""
    pids = holders(path)
    if pids:
        skip(res, f"processes inside: pid(s) {', '.join(map(str, pids[:8]))}")
        return None
    w = walk(path, ctx.cutoff, ctx.uid)
    if w["errors"]:
        skip(res, f"{len(w['errors'])} unreadable entries, e.g. {w['errors'][0]}")
        return None
    if w["recent"]:
        skip(res, f"{w['recent']} entries modified in the last {ctx.args.quiet_hours} h, e.g. {', '.join(w['recent_eg'][:3])}")
        return None
    if w["foreign"]:
        skip(res, f"{w['foreign']} entries not owned by uid {ctx.uid}, e.g. {', '.join(w['foreign_eg'][:3])}")
        return None
    return w


def process_linked(row: dict, wave: str, ctx: Context) -> dict:
    res = new_result(row, wave)
    wt = Path(row["path"])
    prim = ctx.primary(row["repo"])
    OUT(f"== [{wave}] {row['name']}  ({row['repo']}, batch {row['batch']}, {'branch ' + row['branch'] if row.get('branch') else 'detached'})")
    if not wt.exists() and not wt.is_symlink():
        return skip(res, "absent")
    if wt.is_symlink() or not wt.is_dir():
        return skip(res, "the path is a symlink or not a directory")
    dotgit = wt / ".git"
    if dotgit.is_symlink() or not dotgit.is_file():
        return skip(res, ".git is not a file: not a linked worktree")
    line = dotgit.read_text(encoding="utf-8", errors="replace").strip()
    admin = Path(line[len("gitdir: ") :]) if line.startswith("gitdir: ") else None
    if admin is None or admin.parent != prim.path / ".git" / "worktrees":
        return skip(res, f".git points at {line[:160]!r}, not into {prim.path}/.git/worktrees/")
    rec = prim.record_for(wt, refresh=True)
    if rec is None:
        return skip(res, f"not registered in {prim.path}")
    if rec.get("locked"):
        return skip(res, f"locked ({rec.get('locked')})")
    if rec.get("prunable"):
        return skip(res, f"git calls it prunable ({rec.get('prunable')})")
    top = git_text(wt, "rev-parse", "--show-toplevel", check=False)
    if top != str(wt):
        return skip(res, f"git resolves its top level to {top!r}, not this path")
    nested = [str(p) for p in ctx.all_registered() if inside(p, wt)]
    if nested:
        return skip(res, f"holds registered worktree(s): {', '.join(nested[:3])}")
    head = git_text(wt, "rev-parse", "--verify", "HEAD^{commit}")
    res["head"] = head
    if not row.get("head_sha") or not head.startswith(row["head_sha"]):
        return skip(res, f"HEAD moved: now {head[:12]}, inventory {row.get('head_sha')}")
    branch = git_text(wt, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if branch != (row.get("branch") or ""):
        return skip(res, f"branch moved: now {branch or '(detached)'}, inventory {row.get('branch') or '(detached)'}")
    w = check_live(res, wt, ctx)
    if w is None:
        return res
    busy = [n for n in ("HEAD", "logs/HEAD", "ORIG_HEAD", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG", "rebase-merge", "rebase-apply", "index.lock", "HEAD.lock") if os.path.lexists(admin / n) and (n in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG", "rebase-merge", "rebase-apply", "index.lock", "HEAD.lock") or os.lstat(admin / n).st_mtime > ctx.cutoff)]
    if busy:
        return skip(res, f"git state in {admin}: {', '.join(busy)} (an operation in progress, or changed in the last {ctx.args.quiet_hours} h)")
    res.update(bytes=w["bytes"], tmp_entries=w["tmp_entries"], tmp_bytes=w["tmp_bytes"])
    tmp = wt / "tmp"
    if tmp.is_symlink():
        return skip(res, "tmp/ is a symlink")
    if tmp.exists() and not tmp.is_dir():
        return skip(res, "tmp is not a directory")
    dest = ctx.archive / row["name"]
    if dest.exists() or dest.is_symlink():
        return skip(res, f"the archive already holds {dest}")
    if prim.origin_main is None:
        return skip(res, f"{prim.name} has no refs/remotes/origin/main to compare against")
    hidden = [rec[2:].decode("utf-8", "surrogateescape") for rec in git(wt, "ls-files", "-v", "-z").stdout.split(b"\0") if rec[:1].islower() or rec[:2] == b"S "]
    if hidden:
        return skip(res, f"{len(hidden)} index entr{'y is' if len(hidden) == 1 else 'ies are'} marked assume-unchanged or skip-worktree, so git status cannot see an edit there: e.g. {hidden[0]}")
    bases, base_notes = bases_for(ctx, row, wt, prim, head)
    res["notes"].extend(base_notes)
    items = classify(wt, status_entries(wt), bases)
    saves = [it for it in items if it["save"]]
    res["saved"] = [{"path": it["path"], "category": it["category"], "detail": it["detail"], "size": it["size"]} for it in saves]
    res["saved_count"] = len(saves)
    res["saved_bytes"] = sum(it["size"] for it in saves)
    own = {it["path"] for it in saves if it["kind"] != "staged"}
    reserved = {it["path"] + ".staged-index" for it in saves if it["kind"] == "staged"}
    res["whole_patch"] = whole_patch(row, items)
    if res["whole_patch"] or any(it["tracked"] and it["kind"] in ("file", "symlink") for it in saves):
        reserved.add("uncommitted.patch")
    clash = sorted(own & reserved)
    if clash:
        return skip(res, f"a saved worktree path is also a name the script writes into saved/ (it would be overwritten): {', '.join(clash[:3])}")
    ign = ignored_entries(wt)
    moves = [e for e in ign if not CACHE_RE.search(e)]
    res["ignored_moved"] = moves
    anc = git(wt, "merge-base", "--is-ancestor", head, prim.origin_main, check=False).returncode
    if anc not in (0, 1):
        return skip(res, "cannot tell whether HEAD is on origin/main (merge-base failed)")
    ahead_log: list[str] = []
    if anc == 1:
        res["bundle_commits"] = int(git_text(wt, "rev-list", "--count", head, "--not", prim.origin_main) or "0")
        ahead_log = git_text(wt, "log", "--oneline", "--no-decorate", "-n", "200", head, "--not", prim.origin_main).splitlines()
    cats: dict[str, int] = {}
    for it in items:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    OUT(f"   checks: registered, unlocked, no holders, nothing newer than {ctx.args.quiet_hours} h (newest {iso(w['newest']) if w['newest'] else '-'}), HEAD {head[:12]} and branch as inventoried")
    OUT(f"   bases: {', '.join(f'{label} {sha[:8]}' for label, sha in bases)}")
    for note in base_notes:
        OUT(f"     note: {note}")
    OUT(f"   status: {len(items)} item(s): " + (", ".join(f"{k} {v}" for k, v in sorted(cats.items())) or "clean"))
    for it in saves[:40]:
        OUT(f"     SAVE {it['category']:<24} {it['path']}  ({it['detail']})")
    if len(saves) > 40:
        OUT(f"     ... and {len(saves) - 40} more saved path(s)")
    if len(saves) > LARGE_SAVE_FILES or res["saved_bytes"] > LARGE_SAVE_BYTES:
        res["notes"].append(f"LARGE SAVE: {len(saves)} files, {human(res['saved_bytes'])}")
        OUT(f"     LARGE SAVE: {len(saves)} files, {human(res['saved_bytes'])}")
    OUT(f"   ignored outside tmp/: {len(ign)} (caches {len(ign) - len(moves)}, to ignored/: {len(moves)}{': ' + ', '.join(moves[:6]) if moves else ''})")
    OUT("   tmp/: " + (f"{w['tmp_entries']} entries, {human(w['tmp_bytes'])} -> <archive>/{row['name']}/tmp" if tmp.is_dir() else "none"))
    OUT("   HEAD: " + ("on origin/main" if anc == 0 else f"{res['bundle_commits']} commit(s) not on origin/main -> commits.bundle"))
    if not ctx.execute:
        res["outcome"] = "would-remove"
        OUT("   => WOULD REMOVE")
        return res
    return execute_linked(row, res, ctx, wt, prim, dest, items, bases, moves, anc, ahead_log, w)


def write_manifest_header(row: dict, res: dict, ctx: Context, wt: Path, prim: Primary, bases: list[tuple[str, str]], items: list[dict], ahead_log: list[str]) -> list[str]:
    stat_line = git_text(wt, "diff", "HEAD", "--shortstat", check=False)
    lines = [
        f"worktree: {wt}",
        f"repo: {row['repo']}   primary: {prim.path}   location: {row.get('location', '')}",
        f"batch: {row['batch']}   wave: {res['wave']}   identified by: {row.get('identified_by', '')}   item: {row.get('item', '')}",
        f"evidence: {row.get('evidence', '')}",
        f"flags: {', '.join(row.get('flags') or []) or '-'}",
        f"branch: {row.get('branch') or '(detached)'}",
        f"head: {res['head']}",
        f"creation sha (from the name): {row.get('name_sha') or '-'}",
        f"related PRs: {'; '.join(row.get('related_prs') or []) or '-'}",
        f"own PRs: {'; '.join(row.get('own_prs') or []) or '-'}",
        f"archived: {utc_now()} by {SCRIPT} {VERSION} (run {ctx.run_id})",
        "bases compared: " + ", ".join(f"{label}={sha}" for label, sha in bases),
        f"tracked diff stat vs HEAD: {stat_line or 'none'}",
        f"status items: {len(items)}; saved: {res['saved_count']} ({human(res['saved_bytes'])}); ignored moved: {len(res['ignored_moved'])}",
        "HEAD vs origin/main: " + ("an ancestor" if not ahead_log else f"{res['bundle_commits']} commit(s) not on origin/main, in commits.bundle:"),
    ]
    lines.extend("    " + line for line in ahead_log)
    if res["bundle_commits"] > len(ahead_log):
        lines.append(f"    ... and {res['bundle_commits'] - len(ahead_log)} more, not listed here (all are in commits.bundle)")
    if "RENAME-TOUCHED" in (row.get("flags") or []):
        lines.append("note: files in this worktree carry mtimes inside 2026-11-20..22, the blind owner->Overtoad pass (mtime evidence only); read")
        lines.append("      tmp/, saved/ and ignored/ as possibly that rewritten text, not the original. Landed files' originals are in git; transcripts")
        lines.append("      hold the rest." + (" Its 17 STATE*/BRIEF* logs under tmp/flood4/ carry no window mtime: sessions 1-9's logs are the originals." if row["name"] == LAST else ""))
    lines.append("per-path classification: STATUS.tsv")
    lines.append("--- sha256 ---")
    return lines


def execute_linked(row: dict, res: dict, ctx: Context, wt: Path, prim: Primary, dest: Path, items: list[dict], bases: list[tuple[str, str]], moves: list[str], anc: int, ahead_log: list[str], w: dict) -> dict:
    pids = holders(wt)
    if pids:
        return skip(res, f"processes inside at execute time: pid(s) {', '.join(map(str, pids[:8]))}")
    dest.mkdir(parents=True)
    manifest = dest / "MANIFEST.txt"
    manifest.write_text("\n".join(write_manifest_header(row, res, ctx, wt, prim, bases, items, ahead_log)) + "\n", encoding="utf-8", errors="surrogateescape")
    with (dest / "STATUS.tsv").open("w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write("xy\tcategory\tsaved\tdetail\tpath\n")
        for it in items:
            p = it["path"] if "\t" not in it["path"] and "\n" not in it["path"] else repr(it["path"])
            fh.write(f"{it['xy']}\t{it['category']}\t{'yes' if it['save'] else 'no'}\t{it['detail']}\t{p}\n")
    saved_root = dest / "saved"
    patch_paths: list[str] = []
    moved: list[str] = []
    try:
        for it in items:
            if not it["save"]:
                continue
            if not safe_rel(it["path"]):
                raise OSError(f"unsafe path {it['path']!r}")
            src = wt / it["path"]
            if it["kind"] == "staged":
                target = saved_root / (it["path"] + ".staged-index")
                if not within(saved_root, target):
                    raise OSError(f"saved/{it['path']}.staged-index would be written through a symlink saved earlier, outside {saved_root}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(git(wt, "cat-file", "blob", it["wsha"]).stdout)
                fsync_append(manifest, f"{sha256_path(target)}  saved/{it['path']}.staged-index  (staged-only)")
                continue
            inner = next((m for m in moved if it["path"].startswith(m + "/")), None)
            if inner is not None:
                fsync_append(manifest, f"saved/{it['path']}: inside saved/{inner}/, which was moved whole above")
                continue
            target = saved_root / it["path"]
            if not within(saved_root, target):
                raise OSError(f"saved/{it['path']} would be written through a symlink saved earlier, outside {saved_root}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if it["kind"] == "dir":
                os.rename(src, target)
                moved.append(it["path"])
                subs = sorted(p for p in target.rglob("*") if p.is_file() or p.is_symlink())
                fsync_append(manifest, f"saved/{it['path']}/: an untracked directory, moved whole ({len(subs)} files)", *(f"{sha256_path(sub)}  saved/{sub.relative_to(saved_root)}" for sub in subs))
                continue
            if it["kind"] in ("file", "symlink"):
                shutil.copy2(src, target, follow_symlinks=False)
                fsync_append(manifest, f"{sha256_path(target)}  saved/{it['path']}  ({it['category']})")
                if it["tracked"]:
                    patch_paths.append(it["path"])
        if res["whole_patch"]:
            # R7-Q2: "The worker one's uncommitted edits saved as a patch first" -- every tracked change outside tmp/,
            # deletions included, as 2026-11-23's juniper-data patch (pathspec magic needed here, so no --literal-pathspecs)
            saved_root.mkdir(parents=True, exist_ok=True)
            (saved_root / "uncommitted.patch").write_bytes(git(wt, "diff", "--binary", "--no-ext-diff", "--no-textconv", "--no-color", "--src-prefix=a/", "--dst-prefix=b/", "HEAD", "--", ".", ":(exclude,top)tmp").stdout)
            fsync_append(manifest, f"{sha256_path(saved_root / 'uncommitted.patch')}  saved/uncommitted.patch  (git diff --binary HEAD of every tracked change outside tmp/, deletions included)")
        elif patch_paths:
            with (saved_root / "uncommitted.patch").open("wb") as fh:
                for i in range(0, len(patch_paths), 200):
                    fh.write(git(wt, "--literal-pathspecs", "diff", "--binary", "--no-ext-diff", "--no-textconv", "--no-color", "--src-prefix=a/", "--dst-prefix=b/", "HEAD", "--", *patch_paths[i : i + 200]).stdout)
            fsync_append(manifest, f"{sha256_path(saved_root / 'uncommitted.patch')}  saved/uncommitted.patch  (git diff --binary HEAD of the {len(patch_paths)} saved tracked path(s))")
        admin = Path(git_text(wt, "rev-parse", "--absolute-git-dir"))
        shutil.copytree(admin, dest / "worktree-admin", symlinks=True)
        fsync_append(manifest, f"worktree-admin/: a copy of {admin} (HEAD, index, logs/HEAD and any in-progress operation)")
        logged = git_text(wt, "log", "-g", "--format=%H", "HEAD", check=False).split()
        if row.get("branch"):
            logged += git_text(prim.path, "log", "-g", "--format=%H", f"refs/heads/{row['branch']}", check=False).split()
        logged = [s for s in dict.fromkeys(logged) if re.fullmatch(r"[0-9a-f]{40}", s) and git(wt, "cat-file", "-e", s + "^{commit}", check=False).returncode == 0]
        orphan = set(git_text(wt, "rev-list", *logged, "--not", prim.origin_main, res["head"]).split()) if logged else set()
        tips = [s for s in logged if s in orphan]
        temp = [f"refs/r7-archive/{ctx.run_id}/{i}" for i in range(len(tips))]
        if anc == 1 or tips:
            bundle = dest / "commits.bundle"
            try:
                for ref, sha in zip(temp, tips):
                    git(wt, "update-ref", ref, sha)
                # a bundle records named refs only; in a linked worktree HEAD names this worktree's HEAD (R3 pinned its sha)
                git(wt, "bundle", "create", str(bundle), *(["HEAD"] if anc == 1 else []), *temp, "--not", prim.origin_main)
                git(wt, "bundle", "verify", str(bundle))
            finally:
                for ref in temp:
                    git(wt, "update-ref", "-d", ref, check=False)
            fsync_append(manifest, f"{sha256_path(bundle)}  commits.bundle  ({res['bundle_commits']} commit(s) of HEAD; {len(tips)} reflog-only tip(s){': ' + ', '.join(tips) if tips else ''}; git bundle verify passed)")
    except (OSError, GitError) as exc:
        if moved:
            fsync_append(manifest, f"ABORTED at {utc_now()} AFTER moving {len(moved)} director{'y' if len(moved) == 1 else 'ies'} into saved/ ({', '.join(moved[:5])}): {exc}")
            return fail(res, f"saving failed AFTER {len(moved)} director{'y was' if len(moved) == 1 else 'ies were'} moved into {saved_root} ({', '.join(moved[:3])}); the worktree was NOT removed; keep {dest}: {exc}", partial=True)
        fsync_append(manifest, f"ABORTED at {utc_now()} before anything was moved: {exc}")
        return fail(res, f"saving failed, nothing moved, worktree left as it was: {exc}")
    for e in moves:
        rel = e.rstrip("/")
        src = wt / rel
        if not src.exists() and not src.is_symlink():
            fsync_append(manifest, f"ignored entry {e} no longer present (moved with a saved directory?)")
            continue
        target = dest / "ignored" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.rename(src, target)
        except OSError as exc:
            return fail(res, f"moving ignored entry {e} failed: {exc}", partial=True)
        hashed = [target] if not target.is_dir() or target.is_symlink() else sorted(p for p in target.rglob("*") if p.is_file() or p.is_symlink())
        fsync_append(manifest, *(f"{sha256_path(sub)}  ignored/{sub.relative_to(dest / 'ignored')}" for sub in hashed))
    tmp = wt / "tmp"
    if tmp.is_dir() and not tmp.is_symlink():
        if os.stat(tmp).st_dev != os.stat(dest).st_dev:
            return fail(res, "tmp/ is on another filesystem than the archive: not moved", partial=True)
        before = count_entries(tmp)
        try:
            os.rename(tmp, dest / "tmp")
        except OSError as exc:
            return fail(res, f"moving tmp/ failed: {exc}", partial=True)
        after = count_entries(dest / "tmp")
        fsync_append(manifest, f"tmp/: moved {tmp} -> {dest / 'tmp'}; entries before {before}, after {after}")
        if before != after:
            return fail(res, f"tmp/ entry count changed in the move ({before} -> {after}); worktree not removed", partial=True)
    pids = holders(wt)
    if pids:
        return fail(res, f"processes appeared inside before removal: pid(s) {', '.join(map(str, pids[:8]))}; saved files and tmp/ are in {dest}", partial=True)
    p = git(prim.path, "worktree", "remove", "--force", str(wt), check=False)
    if p.returncode != 0:
        return fail(res, f"git worktree remove failed: {p.stderr.decode('utf-8', 'replace').strip()[:300]}; saved files and tmp/ are in {dest}", partial=True)
    if wt.exists() or prim.record_for(wt, refresh=True) is not None:
        return fail(res, "the worktree directory or its registration is still there after removal", partial=True)
    fsync_append(manifest, f"removed: git -C {prim.path} worktree remove --force {wt} at {utc_now()}")
    res["outcome"] = "removed"
    OUT("   => REMOVED")
    return res


def process_plain(row: dict, wave: str, ctx: Context) -> dict:
    res = new_result(row, wave)
    d = Path(row["path"])
    held = row["name"] in PLAIN_HOLD
    OUT(f"== [{wave}] {row['name']}  (plain directory, batch {row['batch']}: " + (f"HELD, not a simulation tree; --held {ctx.args.held})" if held else "R7-Q2 \"Delete the 13 sim dirs\")"))
    if held and ctx.args.held == "keep":
        return skip(res, HOLD_REASON)
    archive_whole = held and ctx.args.held == "archive"
    if not d.exists() and not d.is_symlink():
        return skip(res, "absent")
    if d.is_symlink() or not d.is_dir():
        return skip(res, "the path is a symlink or not a directory")
    if os.path.ismount(d):
        return skip(res, "a mount point")
    if (d / ".git").exists() or (d / ".git").is_symlink():
        return skip(res, "has a .git: not a plain directory")
    nested = [str(p) for p in ctx.all_registered() if p == d or inside(p, d)]
    if nested:
        return skip(res, f"holds registered worktree(s): {', '.join(nested[:3])}")
    w = check_live(res, d, ctx)
    if w is None:
        return res
    if w["nested_git"]:
        return skip(res, f"{len(w['nested_git'])} .git entries inside (e.g. {w['nested_git'][0]}): not deleted unseen")
    dest = ctx.archive / row["name"]
    if dest.exists() or dest.is_symlink():
        return skip(res, f"the archive already holds {dest}")
    res["bytes"] = w["bytes"]
    OUT(f"   checks: no .git, no registered worktree inside, no holders, nothing newer than {ctx.args.quiet_hours} h (newest {iso(w['newest']) if w['newest'] else '-'})")
    if archive_whole:
        OUT(f"   contents: {w['entries']} entries, {human(w['bytes'])}; --held archive: moved whole to <archive>/{row['name']}/tree (a rename), with a FILELIST.tsv.gz")
    else:
        OUT(f"   contents: {w['entries']} entries, {human(w['bytes'])}; keep only <archive>/{row['name']}/FILELIST.tsv.gz")
    if not ctx.execute:
        res["outcome"] = "would-archive" if archive_whole else "would-delete"
        OUT("   => WOULD ARCHIVE WHOLE" if archive_whole else "   => WOULD DELETE")
        return res
    if holders(d):
        return skip(res, "processes inside at execute time")
    dest.mkdir(parents=True)
    if archive_whole and os.stat(d).st_dev != os.stat(dest).st_dev:
        return fail(res, f"{d} is on another filesystem than the archive: not moved (the archive folder {dest} is empty)", partial=True)
    filelist = dest / "FILELIST.tsv.gz"
    n = 0
    with gzip.open(filelist, "wt", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write("path\ttype\tsize\tmtime\n")
        stack = [str(d)]
        while stack:
            with os.scandir(stack.pop()) as it:
                for e in it:
                    st = e.stat(follow_symlinks=False)
                    kind = "dir" if stat.S_ISDIR(st.st_mode) else "symlink" if stat.S_ISLNK(st.st_mode) else "file" if stat.S_ISREG(st.st_mode) else "other"
                    rel = os.path.relpath(e.path, d)
                    fh.write(f"{rel if chr(9) not in rel and chr(10) not in rel else repr(rel)}\t{kind}\t{st.st_size if kind == 'file' else ''}\t{iso(st.st_mtime)}\n")
                    n += 1
                    if kind == "dir":
                        stack.append(e.path)
    lines = [
        f"directory: {d}",
        f"what: a plain directory (no .git), {'an ml-propose simulation tree' if 'ml-propose' in row['name'] else 'not a simulation tree (see PLAIN_HOLD)'}; "
        + ("held, then archived whole on the Overtoad's word (--held archive): tree/ is the directory itself, moved by rename" if archive_whole else "R7-Q2 \"Delete the 13 sim dirs\": deleted, file list kept"),
        f"flags: {', '.join(row.get('flags') or [])}   item: {row.get('item', '')}   related PRs: {'; '.join(row.get('related_prs') or []) or '-'}",
        f"entries: {n} (walk before: {w['entries']}); bytes in regular files: {w['bytes']}",
        f"file list: FILELIST.tsv.gz sha256 {sha256_path(filelist)}",
        f"archived: {utc_now()} by {SCRIPT} {VERSION} (run {ctx.run_id})",
    ]
    (dest / "MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if archive_whole:
        try:
            os.rename(d, dest / "tree")
        except OSError as exc:
            return fail(res, f"moving it whole into {dest / 'tree'} failed: {exc}", partial=True)
        fsync_append(dest / "MANIFEST.txt", f"moved whole: {d} -> {dest / 'tree'} at {utc_now()}; entries after: {count_entries(dest / 'tree')}")
        res["outcome"] = "archived"
        OUT("   => ARCHIVED WHOLE (moved by rename)")
        return res
    try:
        shutil.rmtree(d)
    except OSError as exc:
        return fail(res, f"deletion stopped part-way: {exc}", partial=True)
    if d.exists():
        return fail(res, "the directory is still there after deletion", partial=True)
    fsync_append(dest / "MANIFEST.txt", f"deleted: {utc_now()}")
    res["outcome"] = "deleted"
    OUT("   => DELETED (file list kept)")
    return res


def branch_phase(ctx: Context, rows: list[dict], results: dict[str, dict]) -> list[dict]:
    """R10: the local branches of the removed worktrees."""
    OUT("")
    OUT("== BRANCHES (R7-Q4 \"Delete branches, keep refs (Recommended)\"; refs/flood4/* are not touched)")
    out: list[dict] = []
    deleted_file = ctx.archive / "deleted_branches.txt"
    for row in rows:
        b = row.get("branch") or ""
        if not b or row["batch"] not in ("A", "B"):
            continue
        prim = ctx.primary(row["repo"])
        rec = {"repo": row["repo"], "branch": b, "worktree": row["name"], "outcome": "", "reason": "", "sha": ""}
        out.append(rec)
        wt_outcome = (results.get(row["name"]) or {}).get("outcome", "")
        gone_now = not Path(row["path"]).exists() and prim.record_for(Path(row["path"]), refresh=True) is None
        going = wt_outcome in ("removed", "would-remove")
        if not (gone_now or going):
            rec.update(outcome="keep", reason=f"its worktree was not removed ({wt_outcome or 'not processed'})")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        if b in PROTECTED_BRANCHES:
            rec.update(outcome="keep", reason="a protected name")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        sha = git_text(prim.path, "rev-parse", "--verify", "-q", f"refs/heads/{b}^{{commit}}", check=False)
        rec["sha"] = sha
        if not sha:
            rec.update(outcome="absent", reason="no such local branch")
            OUT(f"   ABSENT {row['repo']} {b}")
            continue
        if not row.get("head_sha") or not sha.startswith(row["head_sha"]):
            rec.update(outcome="keep", reason=f"tip moved: {sha[:12]}, inventory {row.get('head_sha')}")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        users = [r.get("worktree") for r in prim.records(refresh=True) if r.get("branch") == f"refs/heads/{b}" and r.get("worktree") != row["path"]]
        if users:
            rec.update(outcome="keep", reason=f"checked out in {users[0]}")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        remote = prim.remote_heads()
        if remote is None:
            rec.update(outcome="keep", reason="could not list origin's branches")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        if b in remote:
            rec.update(outcome="keep", reason="origin has a branch of that name")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        if not ctx.execute:
            rec["outcome"] = "would-delete"
            OUT(f"   WOULD DELETE {row['repo']} {b} {sha}")
            continue
        if not gone_now:
            rec.update(outcome="keep", reason="its worktree is still registered")
            OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
            continue
        if not (ctx.archive / row["name"] / "commits.bundle").exists() and (prim.origin_main is None or git(prim.path, "merge-base", "--is-ancestor", sha, prim.origin_main, check=False).returncode != 0):
            bfile = ctx.archive / "branch-bundles" / f"{row['repo']}--{b.replace('/', '--')}.bundle"
            bfile.parent.mkdir(parents=True, exist_ok=True)
            made = prim.origin_main is not None and git(prim.path, "bundle", "create", str(bfile), f"refs/heads/{b}", "--not", prim.origin_main, check=False).returncode == 0
            if not made or git(prim.path, "bundle", "verify", str(bfile), check=False).returncode != 0:
                rec.update(outcome="keep", reason="its tip is not on origin/main and no bundle of it could be made")
                OUT(f"   KEEP  {row['repo']} {b}: {rec['reason']}")
                continue
            fsync_append(bfile.parent / "INDEX.txt", f"{row['repo']} {b} {sha} {bfile.name}")
        fsync_append(deleted_file, f"{row['repo']} {b} {sha}")
        p = git(prim.path, "branch", "-D", b, check=False)
        if p.returncode != 0:
            fsync_append(deleted_file, f"# the line above was NOT deleted: {p.stderr.decode('utf-8', 'replace').strip()[:200]}")
            rec.update(outcome="fail", reason=p.stderr.decode("utf-8", "replace").strip()[:200])
            OUT(f"   FAILED {row['repo']} {b}: {rec['reason']}")
            continue
        rec["outcome"] = "deleted"
        OUT(f"   DELETED {row['repo']} {b} {sha}")
    return out


def prune(ctx: Context, names: list[str]) -> None:
    """R9 as a report: `git worktree remove` already deletes the registration of every tree this run removes, so a real
    prune could only drop registrations this run never touched (another session's moved or unmounted tree, with its
    HEAD, index and reflog). Those are listed, never pruned."""
    for name in names:
        prim = ctx.primary(name)
        p = git(prim.path, "worktree", "prune", "-n", "-v", check=False)
        msg = (p.stdout + p.stderr).decode("utf-8", "replace").strip()
        OUT(f"   prune {name}: " + (f"NOT pruned, stale registration(s) this run did not create: {msg[:300]}" if msg else "nothing stale"))
        prim.records(refresh=True)


def load_inputs(args: argparse.Namespace) -> tuple[dict, dict]:
    with args.inventory.open(encoding="utf-8") as fh:
        inventory = json.load(fh)
    prs: dict[str, dict] = {}
    with args.pr_commits.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rec = json.loads(line)
                prs[f"{rec['repo']}#{rec['number']}"] = rec
    return inventory, prs


def select(inventory: dict, prs: dict, args: argparse.Namespace, root: Path, archive: Path) -> list[dict]:
    rows = inventory.get("rows")
    if not isinstance(rows, list):
        raise Refusal("the inventory has no 'rows' list")
    names = [r.get("name") for r in rows]
    if len(names) != len(set(names)):
        raise Refusal("the inventory repeats a name")
    sel = [r for r in rows if r.get("batch") in ("A", "B")]
    last = [r for r in rows if r.get("name") == LAST]
    sel.extend(last)
    allowed_parents = {"worktrees/": root / "worktrees", "juniper-ml/.claude/worktrees/": root / "juniper-ml" / ".claude" / "worktrees"}
    for r in sel:
        name = r.get("name") or ""
        if name in NEVER:
            raise Refusal(f"{name} is selected, but it is never to be touched")
        if r.get("repo") not in PRIMARIES:
            raise Refusal(f"{name}: repo {r.get('repo')!r} is not one of the eight primaries")
        path = Path(r.get("path") or "")
        parent = allowed_parents.get(r.get("location") or "")
        if parent is None or not path.is_absolute() or path.parent != parent or path.name != name or os.path.realpath(path.parent) != str(path.parent):
            raise Refusal(f"{name}: path {path} is not <{r.get('location')}>{name} under {root}")
        if r.get("kind") == "not-a-git-checkout":
            if "PLAIN-DIR" not in (r.get("flags") or []) or r.get("location") != "worktrees/" or r.get("batch") != "A":
                raise Refusal(f"{name}: a non-checkout outside batch A's simulation directories")
        elif r.get("kind") != "linked-worktree":
            raise Refusal(f"{name}: kind {r.get('kind')!r}")
        if inside(archive, path) or archive == path:
            raise Refusal(f"the archive {archive} lies inside {path}")
        for key in pr_keys(r):
            if f"{key[0]}#{key[1]}" not in prs:
                raise Refusal(f"{name}: {key[0]}#{key[1]} is missing from --pr-commits")
            if prs[f"{key[0]}#{key[1]}"].get("state") != "MERGED":
                raise Refusal(f"{name}: {key[0]}#{key[1]} is not MERGED in --pr-commits")
    a = [r for r in sel if r["batch"] == "A"]
    b = [r for r in sel if r["batch"] == "B"]
    plain = [r for r in a if r["kind"] == "not-a-git-checkout"]
    branches = {(r["repo"], r["branch"]) for r in a + b if r.get("branch")}
    counts = f"{len(a)}:{len(b)}:{len(plain)}:{len(branches)}:{len(last)}"
    OUT(f"selection: batch A {len(a)} (simulation dirs {len(plain)}), batch B {len(b)}, branches {len(branches)}, humming {len(last)}  [ruled {args.ruled_counts}]")
    if counts != args.ruled_counts:
        raise Refusal(f"the selection counts {counts} differ from the ruled {args.ruled_counts} (A:B:sim:branches:humming)")
    if args.only:
        by_name = {r["name"]: r for r in sel}
        missing = [n for n in args.only if n not in by_name]
        if missing:
            raise Refusal(f"--only names entries that are not selectable: {', '.join(missing)}")
        sel = [r for r in sel if r["name"] in set(args.only)]
    return sel


def order(sel: list[dict]) -> list[tuple[str, list[dict], list[str]]]:
    """(wave, rows, primaries to prune after) in plan.txt's ORDER."""
    rank = {n: i for i, n in enumerate(PRIMARIES)}
    groups: list[tuple[str, list[dict], list[str]]] = []
    a1 = [r for r in sel if r["batch"] == "A" and r["location"] == "worktrees/" and r["repo"] != "juniper-ml"]
    for repo in sorted({r["repo"] for r in a1}, key=lambda x: rank[x]):
        groups.append(("A1", sorted((r for r in a1 if r["repo"] == repo), key=lambda r: r["name"]), [repo]))
    a2 = [r for r in sel if r["batch"] == "A" and r["location"] == "worktrees/" and r["repo"] == "juniper-ml"]
    a2_rows = sorted((r for r in a2 if r.get("identified_by") == "five"), key=lambda r: r["name"])
    a2_rows += sorted((r for r in a2 if r.get("identified_by") != "five" and r["kind"] == "linked-worktree"), key=lambda r: r["name"])
    a2_rows += sorted((r for r in a2 if r["kind"] == "not-a-git-checkout"), key=lambda r: r["name"])
    if a2_rows:
        groups.append(("A2", a2_rows, ["juniper-ml"]))
    a3 = [r for r in sel if r["batch"] == "A" and r["location"] == "juniper-ml/.claude/worktrees/"]
    keep_rank = {n: i for i, n in enumerate(KEEP_CARRIERS)}
    a3_rows = sorted(a3, key=lambda r: (r["name"] in keep_rank, keep_rank.get(r["name"], -1), r["name"]))
    if a3_rows:
        groups.append(("A3", a3_rows, ["juniper-ml"]))
    b_rows = sorted((r for r in sel if r["batch"] == "B"), key=lambda r: (r["location"] != "juniper-ml/.claude/worktrees/", rank[r["repo"]], r["name"]))
    if b_rows:
        groups.append(("B", b_rows, sorted({r["repo"] for r in b_rows}, key=lambda x: rank[x])))
    h_rows = [r for r in sel if r["name"] == LAST]
    if h_rows:
        groups.append(("H", h_rows, ["juniper-ml"]))
    return groups


def write_index(ctx: Context, results: list[dict]) -> None:
    index = ctx.archive / "INDEX.tsv"
    new = not index.exists()
    with index.open("a", encoding="utf-8") as fh:
        if new:
            fh.write("name\trepo\twave\tbatch\tkind\tbranch\thead\toutcome\trun\tsaved_files\tsaved_bytes\tignored_moved\ttmp_entries\ttmp_new_path\tbundle_commits\n")
        for r in results:
            if r["outcome"] not in ("removed", "deleted", "archived"):
                continue
            tmp_new = f"tmp/{ARCHIVE_NAME}/{r['name']}/tmp" if r["outcome"] == "removed" and r["tmp_entries"] else ""
            fh.write(f"{r['name']}\t{r['repo']}\t{r['wave']}\t{r['batch']}\t{r['kind']}\t{r['branch']}\t{r['head']}\t{r['outcome']}\t{ctx.run_id}\t{r['saved_count']}\t{r['saved_bytes']}\t{len(r['ignored_moved'])}\t{r['tmp_entries']}\t{tmp_new}\t{r['bundle_commits']}\n")


def write_readme(ctx: Context, inv_sha: str, prs_sha: str) -> None:
    rows = []
    index = ctx.archive / "INDEX.tsv"
    if index.exists():
        with index.open(encoding="utf-8") as fh:
            rows = [line.rstrip("\n").split("\t") for line in fh][1:]
    removed = sum(1 for r in rows if len(r) > 7 and r[7] == "removed")
    deleted = sum(1 for r in rows if len(r) > 7 and r[7] == "deleted")
    archived_whole = sum(1 for r in rows if len(r) > 7 and r[7] == "archived")
    branches = 0
    dfile = ctx.archive / "deleted_branches.txt"
    if dfile.exists():
        with dfile.open(encoding="utf-8") as fh:
            lines = [line for line in fh if line.strip()]
        branches = sum(1 for line in lines if not line.startswith("#")) - sum(1 for line in lines if line.startswith("#"))
    runs = sorted(p.name for p in (ctx.archive / "runs").glob("*-execute.log")) if (ctx.archive / "runs").is_dir() else []
    text = f"""# Worktree archive, 2026-11-24 (Cursor flood-4, ruling 7)

The Cursor flood-4 arc's worktrees, removed on ruling 7 of
`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` section 8 ("All, after record merges") and the
Overtoad's rulings of 2026-11-25 at 01:46Z: R7-Q1 "You run the script (Recommended)"; R7-Q2 "9 session launch
worktrees", "3 ruling-37 marker trees", "6 inferred-provenance trees", "Delete the 13 sim dirs"; R7-Q3 "juniper-ml/tmp/
(Recommended)"; R7-Q4 "Delete branches, keep refs (Recommended)". Removed by `{SCRIPT}` {VERSION}; execute runs:
{', '.join(f'`runs/{r}`' for r in runs) or 'none yet'}. Kept here under the retention rule of juniper-ml `AGENTS.md`
section Temporary files.

NAME below is a worktree's or a plain directory's name.

| Entry | What |
| --- | --- |
| `INDEX.tsv` | one row per archived worktree or plain directory: repo, wave, branch, HEAD, run, counts saved and moved, the new path of its `tmp/` (its location, PRs and archive time are in its `MANIFEST.txt`) |
| `NAME/MANIFEST.txt` | worktree path, repo, branch, HEAD, the bases its files were compared with, the diff stat, the commits not on `origin/main`, the sha256 of every saved and ignored file, the `tmp/` move with entry counts before and after |
| `NAME/STATUS.tsv` | every path `git status` listed outside `tmp/` (which moved whole), with its classification: `on-base`, `substitution-of-base`, `symlink-copy`, `deleted`, `vanished` and `special-file` were not saved; every other category was |
| `NAME/tmp/` | the worktree's gitignored `tmp/`, moved (a rename on one filesystem), not copied |
| `NAME/saved/` | its files that matched no base: copied (untracked directories moved), tracked ones also as `uncommitted.patch` (in batch B's trees the substitution did not reach, the whole tracked diff), staged-only content as `<path>.staged-index` |
| `NAME/ignored/` | its ignored entries outside `tmp/` that are not caches, moved |
| `NAME/commits.bundle` | HEAD's commits that are not on `origin/main`, and any commit only the worktree's or its branch's reflog held (`git bundle verify` passed) |
| `NAME/worktree-admin/` | a copy of the worktree's admin directory: `HEAD`, `index`, `logs/HEAD`, any in-progress operation |
| `branch-bundles/` | for a deleted branch whose worktree was already gone: its commits not on `origin/main` (`INDEX.txt` names them) |
| `NAME/FILELIST.tsv.gz`, `NAME/MANIFEST.txt` (plain directories) | each plain directory deleted on R7-Q2 (the 12 ml-propose simulation trees, and the N-4 claims lens's fix tree only if the Overtoad rules it deleted): path, type, size and mtime of each entry, and the deletion record; no file contents |
| `NAME/tree/` (the held directory) | the N-4 claims lens's fix tree itself, moved whole by rename, if the Overtoad rules it archived (`--held archive`); its `FILELIST.tsv.gz` and `MANIFEST.txt` beside it |
| `deleted_branches.txt` | repo, branch, full sha of each local branch, written before its `git branch -D` (a `#` line after one says that deletion failed): `git -C <repo> branch <name> <sha>` restores one while its objects last; its worktree's `commits.bundle` keeps any commits not on `origin/main` beyond that |
| `runs/` | each execute run's log and JSON |
| `provenance/` | the first execute run's inventory (sha256 `{inv_sha}`) and PR commit list (sha256 `{prs_sha}`); a later run's differing copy carries its run id in its name |

**Path map.** A citation of `.claude/worktrees/NAME/tmp/...` or `Juniper/worktrees/NAME/tmp/...` now resolves at
`tmp/{ARCHIVE_NAME}/NAME/tmp/...` in juniper-ml.

**Caution: possibly substituted text.** The blind "owner -> Overtoad" pass of 2026-11-20..22 rewrote files in the
worktrees under `juniper-ml/.claude/worktrees/` that existed then (the evidence is file mtimes): 61 of the inventory's
64 candidates there have files modified in that window, and the other 3 were born after it (vectorized-crunching-ritchie,
archived here; hidden-scribbling-toast and playful-scribbling-kite, not removed). humming-stargazing-papert has 246,363
of its 379,593 `tmp/` regular files in it (53 of round 2's 344 triage files; its 17 STATE/BRIEF logs none). Read
`tmp/`, `saved/` and `ignored/` there as possibly substituted, and prefer `gh`, `git` or the session transcripts. No
`Juniper/worktrees/` candidate shows the window (0 of 218).

**Not removed.** The `refs/flood4/*` refs (R7-Q4); the batch C worktrees curious-plotting-hummingbird (do not sweep),
hidden-scribbling-toast (sessions 10-13's logs and briefs; plan Q9 leaves it, and juniper-ml's own `tmp/val-a-m1/`, to a
later pass) and playful-scribbling-kite; humming-stargazing-papert's branch `worktree-humming-stargazing-papert` (not
among the 87 ruled); any entry a run skipped and any branch a run kept (its run log says why).

**Counts at {utc_now()}**: {removed} worktrees removed, {deleted} plain directories deleted, {archived_whole} held
directory archived whole, {branches} local branches deleted.

**Retention**: keep until the Overtoad rules the flood-4 evidence no longer needed.
"""
    (ctx.archive / "README.md").write_text(text, encoding="utf-8")


def summary(ctx: Context, results: list[dict], branches: list[dict]) -> None:
    OUT("")
    OUT(f"== SUMMARY ({'EXECUTE' if ctx.execute else 'DRY RUN'}, run {ctx.run_id}, finished {utc_now()})")
    by: dict[str, int] = {}
    for r in results:
        by[r["outcome"]] = by.get(r["outcome"], 0) + 1
    OUT("   entries: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))
    waves: dict[str, int] = {}
    for r in results:
        waves[r["wave"]] = waves.get(r["wave"], 0) + 1
    OUT("   by wave: " + ", ".join(f"{k} {v}" for k, v in waves.items()))
    done = [r for r in results if r["outcome"] in ("removed", "would-remove")]
    plain = [r for r in results if r["outcome"] in ("deleted", "would-delete")]
    whole = [r for r in results if r["outcome"] in ("archived", "would-archive")]
    OUT(f"   worktrees: {len(done)}; their tmp/: {sum(r['tmp_entries'] for r in done)} entries, {human(sum(r['tmp_bytes'] for r in done))} (moved, not copied)")
    OUT(f"   saved: {sum(r['saved_count'] for r in done)} file(s) in {sum(1 for r in done if r['saved_count'])} worktree(s), {human(sum(r['saved_bytes'] for r in done))}")
    OUT(f"   bundles: {sum(1 for r in done if r['bundle_commits'])} worktree(s), {sum(r['bundle_commits'] for r in done)} commit(s); ignored entries moved: {sum(len(r['ignored_moved']) for r in done)}")
    OUT(f"   plain directories deleted: {len(plain)}, {human(sum(r['bytes'] for r in plain))}; held and archived whole: {len(whole)}, {human(sum(r['bytes'] for r in whole))}")
    OUT(f"   space freed: at most about {human(sum(r['bytes'] - r['tmp_bytes'] for r in done) + sum(r['bytes'] for r in plain))} (saved/ copies and ignored/ moves stay in the archive)")
    for r in results:
        if r["outcome"] in ("skip", "fail", "partial"):
            OUT(f"   {r['outcome'].upper():<8} {r['name']}: {'; '.join(r['reasons'])}")
    for r in results:
        for note in r["notes"]:
            if note.startswith("LARGE SAVE"):
                OUT(f"   REVIEW   {r['name']}: {note}")
    bby: dict[str, int] = {}
    for b in branches:
        bby[b["outcome"]] = bby.get(b["outcome"], 0) + 1
    OUT("   branches: " + (", ".join(f"{k} {v}" for k, v in sorted(bby.items())) or "none processed"))
    for b in branches:
        if b["outcome"] in ("keep", "fail"):
            OUT(f"   BRANCH {b['outcome'].upper():<5} {b['repo']} {b['branch']}: {b['reason']}")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--inventory", type=Path, required=True, help="session 12's tmp/flood4/session12/r7/inventory.json")
    parser.add_argument("--pr-commits", type=Path, required=True, help="JSON lines: repo, number, state, merge, head for every related PR")
    parser.add_argument("--juniper-root", type=Path, default=Path.home() / "Development" / "python" / "Juniper")
    parser.add_argument("--archive", type=Path, default=None, help=f"default: <juniper-root>/juniper-ml/tmp/{ARCHIVE_NAME}")
    parser.add_argument("--execute", action="store_true", help="act; without it nothing is changed")
    parser.add_argument("--yes", action="store_true", help="with --execute: do not ask for confirmation")
    parser.add_argument("--fetch", action="store_true", help="fetch origin main and the related PRs' heads in each primary first")
    parser.add_argument("--only", action="append", default=[], metavar="NAME", help="restrict to this entry (repeatable)")
    parser.add_argument("--no-branches", action="store_true", help="leave every branch for a later run")
    parser.add_argument("--quiet-hours", type=float, default=6.0, help="an entry with a file newer than this is live (default 6)")
    parser.add_argument("--ruled-counts", default=RULED_COUNTS, help="A:B:sim:branches:humming the selection must have (default %(default)s)")
    parser.add_argument("--ruled-inventory-sha256", default=RULED_INVENTORY_SHA256, help="the sha256 the inventory must have (default: the file the rulings were asked on)")
    parser.add_argument("--last-extra-base", default=LAST_EXTRA_BASE[1], help=f"the extra commit {LAST}'s files are compared with (default %(default)s, session 9's HEAD)")
    parser.add_argument("--json", type=Path, default=None, help="write the per-entry results here")
    parser.add_argument("--list", action="store_true", help="check the selection, print it in run order with its branches, and stop: no git, no writes")
    parser.add_argument("--held", choices=("keep", "archive", "delete"), default="keep", help="PLAIN_HOLD's directory: keep it in place (default, until the Overtoad rules), archive it whole (a rename), or delete it with the twelve")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    if not sys.platform.startswith("linux") or not os.path.isdir("/proc/self/fd"):
        raise Refusal("this host has no /proc: the liveness check (R2) cannot run")
    if os.geteuid() == 0:
        raise Refusal("do not run as root")
    root = Path(os.path.realpath(args.juniper_root))
    archive = Path(os.path.realpath(args.archive)) if args.archive else root / "juniper-ml" / "tmp" / ARCHIVE_NAME
    if not inside(archive, root / "juniper-ml" / "tmp"):
        raise Refusal(f"the archive {archive} is not under {root / 'juniper-ml' / 'tmp'}")
    inventory, prs = load_inputs(args)
    OUT(f"{SCRIPT} {VERSION}  mode: {'LIST' if args.list else 'EXECUTE' if args.execute else 'DRY RUN'}  {utc_now()}")
    OUT(f"juniper root: {root}   archive: {archive}")
    OUT(f"inventory: {args.inventory} (generated {inventory.get('generated_utc')}, sha256 {sha256_path(args.inventory)[:16]}); PR commits: {len(prs)}")
    sel = select(inventory, prs, args, root, archive)
    inv_sha = sha256_path(args.inventory)
    if inv_sha != args.ruled_inventory_sha256:
        raise Refusal(f"the inventory's sha256 {inv_sha[:16]} is not the ruled file's {args.ruled_inventory_sha256[:16]} (override: --ruled-inventory-sha256)")
    if args.list:
        for wave, rows, prune_after in order(sel):
            OUT(f"wave {wave} ({', '.join(prune_after)}): {len(rows)}")
            for r in rows:
                OUT(f"   {r['name']}  [{r['kind']}; {r.get('branch') or 'detached'}; {', '.join(r.get('flags') or []) or '-'}]")
        branches = sorted({(r["repo"], r["branch"]) for r in sel if r.get("branch") and r["batch"] in ("A", "B")})
        OUT(f"branches ({len(branches)}):")
        for repo, b in branches:
            OUT(f"   {repo} {b}")
        return 0
    ctx = Context(args, root, archive, prs)
    heads_by_repo: dict[str, list[str]] = {}
    for r in sel:
        for repo, number in pr_keys(r):
            if repo == r["repo"]:
                heads_by_repo.setdefault(repo, [])
                ref = f"refs/pull/{number}/head"
                if ref not in heads_by_repo[repo]:
                    heads_by_repo[repo].append(ref)
    for name in PRIMARIES:
        prim = Primary(root, name)
        prim.setup(args.fetch, heads_by_repo.get(name, []))
        ctx.primaries[name] = prim
        OUT(f"primary {name:<22} origin/main {prim.origin_main[:12] if prim.origin_main else 'NONE'}  {'shallow' if prim.shallow else 'full'}  registered {len(prim.records())}{('  ' + prim.fetch_note) if prim.fetch_note else ''}")
    if args.execute:
        if not args.yes:
            if not sys.stdin.isatty():
                raise Refusal("--execute without --yes needs a terminal to confirm")
            answer = input(f"Archive and remove {len(sel)} entries (and their branches{', not now' if args.no_branches else ''})? Type 'execute' to go on: ")
            if answer.strip() != "execute":
                raise Refusal("not confirmed")
        (archive / "runs").mkdir(parents=True, exist_ok=True)
        prov = archive / "provenance"
        prov.mkdir(exist_ok=True)
        for src, dst in ((args.inventory, prov / "inventory.json"), (args.pr_commits, prov / "pr_commits.jsonl")):
            if dst.exists() and sha256_path(dst) != sha256_path(src):
                dst = dst.with_name(f"{dst.stem}-{ctx.run_id}{dst.suffix}")
            if not dst.exists():
                shutil.copy2(src, dst)
        with (archive / "runs" / f"{ctx.run_id}-execute.log").open("w", encoding="utf-8", errors="surrogateescape") as log:
            log.write("".join(line + "\n" for line in OUT.early))
            OUT.fh = log
            try:
                code = main_loop(ctx, sel)
            finally:
                OUT.fh = None
        return code
    return main_loop(ctx, sel)


def main_loop(ctx: Context, sel: list[dict]) -> int:
    results: list[dict] = []
    by_name: dict[str, dict] = {}
    for wave, rows, prune_after in order(sel):
        OUT("")
        OUT(f"######## wave {wave}: {len(rows)} entr{'y' if len(rows) == 1 else 'ies'} ({', '.join(prune_after)})")
        for row in rows:
            if row["name"] == LAST and not ctx.args.only:
                blockers = [r for r in results if blocking(r)]
                if blockers:
                    res = new_result(row, wave)
                    OUT(f"== [{wave}] {row['name']}")
                    skip(res, f"goes last, after everything else is archived: {len(blockers)} entr{'y' if len(blockers) == 1 else 'ies'} were skipped or failed this run (rerun with --only {LAST} once they are settled)")
                    results.append(res)
                    by_name[row["name"]] = res
                    continue
            try:
                res = process_plain(row, wave, ctx) if row["kind"] == "not-a-git-checkout" else process_linked(row, wave, ctx)
            except (GitError, OSError, UnicodeError) as exc:
                started = ctx.execute and (ctx.archive / row["name"]).exists()
                note = f"; {ctx.archive / row['name']} exists, so something may already have been moved there: check it and the worktree before any rerun" if started else ""
                res = fail(new_result(row, wave), f"{type(exc).__name__}: {exc}{note}", partial=started)
            results.append(res)
            by_name[row["name"]] = res
        prune(ctx, prune_after)
    branches: list[dict] = []
    if not ctx.args.no_branches:
        branches = branch_phase(ctx, sel, by_name)
    if ctx.execute:
        prune(ctx, list(PRIMARIES))
        write_index(ctx, results)
        write_readme(ctx, sha256_path(ctx.archive / "provenance" / "inventory.json"), sha256_path(ctx.archive / "provenance" / "pr_commits.jsonl"))
    summary(ctx, results, branches)
    payload = {"script": SCRIPT, "version": VERSION, "run": ctx.run_id, "execute": ctx.execute, "results": results, "branches": branches}
    targets = [ctx.archive / "runs" / f"{ctx.run_id}-execute.json"] if ctx.execute else []
    if ctx.args.json:
        targets.append(ctx.args.json)
    for target in targets:
        with target.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, default=str)
    bad = any(r["outcome"] in ("fail", "partial") for r in results) or any(b["outcome"] == "fail" for b in branches)
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            continue  # a stream that cannot be reconfigured (not a TextIOWrapper) keeps its own error handler
    args = parse_args(argv)
    try:
        return run(args)
    except Refusal as exc:
        OUT(f"REFUSED: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
