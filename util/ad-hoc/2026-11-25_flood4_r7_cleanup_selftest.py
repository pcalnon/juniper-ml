#!/usr/bin/env python3
"""
Self-test of util/ad-hoc/2026-11-25_flood4_r7_cleanup.py on a synthetic fixture built under a new directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 7: the cleanup script's fixture test, session 13)
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation (the cleanup script is tested ONLY on this fixture, never on the real trees)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-25_flood4_r7_cleanup.py;
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_flood4-session12-ruling-26-landed-ruling-7-ruled-cleanup-script-next.md

What it does
------------
Builds, under --dir (which must not exist yet), a stand-in for the Juniper root: eight bare "origin" repositories
(a PR's head under refs/pull/N/head and its squash on main, a remote branch), the eight primaries (juniper-ml shallow,
as on the host), and 22 inventory rows (20 worktrees and directories and 2 absent entries, plus one nested worktree), one or more for every branch of the cleanup script's logic:
local commits (a bundle), a tracked edit that only a PR's head holds (--fetch), landed and new untracked files, the
blind owner->Overtoad substitution of tracked files and of a symlink, staged-only content, ignored caches and a
.venv, two simulation directories (one with a .git inside), live (a process inside), recent, moved, locked and
nesting worktrees, absent entries whose branches did or did not move, a remote branch of the same name, humming
(moved HEAD, extra base, goes last) and two never-touched names. Every git call carries a private global config
(no signing, no hooks) and a ceiling directory, so nothing reaches a real repository.

It then runs the script: four refusals; a dry run, asserting that it changes no file under the root; a --fetch dry
run; the --execute run; a second --execute run for humming alone; and a last dry run, which must find every removed entry absent. It asserts every outcome, the archive's
layout and every sha256 line, the deleted and kept branches, the wave order, and that the skipped and never-touched
trees are intact. Prints PASS/FAIL per check; exit 0 when all pass.

Usage
-----
    python3 util/ad-hoc/2026-11-25_flood4_r7_cleanup_selftest.py --dir tmp/flood4/session13/fixture-1
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess  # nosec B404 - runs git and the script under test with fixed argument lists
import sys
import time
from pathlib import Path

CLEANUP = Path(__file__).resolve().parent / "2026-11-25_flood4_r7_cleanup.py"
ARCHIVE_NAME = "worktree-archive-2026-11-24-flood4"
PRIMARIES = ("juniper-ml", "juniper-data", "juniper-cascor", "juniper-canopy", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-deploy")
TWO_DAYS = 2 * 24 * 3600
RESULTS: list[tuple[bool, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((bool(ok), name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not ok else ""), flush=True)


def substitute(data: bytes) -> bytes:
    return data.replace(b"Owner", b"The Overtoad").replace(b"owner", b"Overtoad")


def sha256(path: Path) -> str:
    if path.is_symlink():
        return "symlink:" + hashlib.sha256(os.readlink(os.fsencode(path))).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Fixture:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.root = base / "J"
        self.remotes = self.root / "remotes"
        self.scratch = base / "scratch"
        self.logs = base / "logs"
        cfg = base / "gitconfig"
        hooks = base / "nohooks"
        for d in (self.root, self.remotes, self.scratch, self.logs, hooks):
            d.mkdir(parents=True)
        cfg.write_text(
            "[user]\n\tname = Fixture\n\temail = fixture@example.invalid\n[init]\n\tdefaultBranch = main\n"
            f"[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n[core]\n\thooksPath = {hooks}\n",
            encoding="utf-8",
        )
        drop = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR")
        self.env = {k: v for k, v in os.environ.items() if k not in drop}
        self.env.update({"GIT_CONFIG_GLOBAL": str(cfg), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CEILING_DIRECTORIES": str(base), "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
        self.sha: dict[str, str] = {}
        self.rows: list[dict] = []
        self.sleeper: subprocess.Popen | None = None

    def git(self, cwd: Path, *args: str) -> str:
        p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, env=self.env, check=False)  # nosec B603 B607
        if p.returncode != 0:
            raise RuntimeError(f"git -C {cwd} {' '.join(args)}: {p.stderr.decode('utf-8', 'replace')}")
        return p.stdout.decode("utf-8", "replace").strip()

    @staticmethod
    def write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, repo: Path, msg: str) -> str:
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", msg)
        return self.git(repo, "rev-parse", "HEAD")

    # ------------------------------------------------------------------ remotes and primaries
    def build_remotes(self) -> None:
        for name in PRIMARIES:
            bare = self.remotes / f"{name}.git"
            self.git(self.remotes, "init", "-q", "--bare", str(bare))
            work = self.scratch / name
            self.git(self.scratch, "clone", "-q", str(bare), str(work))
            if name == "juniper-ml":
                self.write(work / ".gitignore", "/tmp/\n.claude/\n__pycache__/\n.venv/\n.pytest_cache/\n")  # tmp-path-literal: allow (the fixture's .gitignore, as the real one)
                self.write(work / "README.md", "the owner of this repo\n")
                self.sha["ml_c0"] = self.commit(work, "c0")
                self.write(work / "AGENTS.md", "Owner: Paul\nrules\n")
                os.symlink("AGENTS.md", work / "CLAUDE.md")
                self.write(work / "util" / "x.py", "owner = 1\n")
                self.write(work / "util" / "y.py", "y = 2\n")
                self.write(work / "docs" / "a.md", "A\n")
                self.sha["ml_c1"] = self.commit(work, "c1")
                self.git(work, "checkout", "-q", "-b", "pr101")
                self.write(work / "docs" / "a.md", "A\nPR\n")
                self.write(work / "util" / "ad-hoc" / "helper.py", "# Owner: the fixture\nprint('helper')\n")
                self.sha["ml_h101"] = self.commit(work, "pr 101 head")
                self.git(work, "push", "-q", "origin", "pr101:refs/pull/101/head")
                self.git(work, "checkout", "-q", "main")
                self.write(work / "docs" / "a.md", "A main\n")
                self.sha["ml_c1b"] = self.commit(work, "c1b")
                self.write(work / "docs" / "a.md", "A main\nPR\n")
                self.write(work / "util" / "ad-hoc" / "helper.py", "# Owner: the fixture\nprint('helper')\n")
                self.sha["ml_m101"] = self.commit(work, "squash of pr 101 (#101)")
                self.write(work / "docs" / "b.md", "b\n")
                self.sha["ml_c2"] = self.commit(work, "c2")
                self.write(work / "README.md", "the Overtoad of this repository\n")
                self.sha["ml_c3"] = self.commit(work, "c3: the careful rename")
                self.git(work, "push", "-q", "origin", "main")
                self.git(work, "checkout", "-q", "-b", "rename-pr", self.sha["ml_c1"])
                self.write(work / "README.md", "the Overtoad of this repo (pr)\n")
                self.sha["ml_r"] = self.commit(work, "a rename PR's commit")
                self.git(work, "push", "-q", "origin", "rename-pr")
            elif name == "juniper-cascor":
                self.write(work / "README.md", "cascor owner\n")
                self.write(work / "src" / "core.py", "core = 1\n")
                self.sha["cc_c0"] = self.commit(work, "c0")
                self.write(work / "src" / "util.py", "util = 1\n")
                self.sha["cc_c1"] = self.commit(work, "c1")
                self.git(work, "push", "-q", "origin", "main")
                self.git(work, "push", "-q", "origin", "main:refs/heads/fix/remote-kept")
                self.git(work, "checkout", "-q", "-b", "pr201")
                self.write(work / "src" / "feature.py", "feature v1\n")
                self.sha["cc_h201"] = self.commit(work, "pr 201 head")
                self.git(work, "push", "-q", "origin", "pr201:refs/pull/201/head")
                self.git(work, "checkout", "-q", "main")
                self.write(work / "src" / "feature.py", "feature v1\n")
                self.sha["cc_m201"] = self.commit(work, "squash of pr 201 (#201)")
                self.git(work, "push", "-q", "origin", "main")
            elif name == "juniper-data":
                self.write(work / "README.md", "data\n")
                self.sha["jd_c0"] = self.commit(work, "c0")
                self.write(work / "a.txt", "a\n")
                self.sha["jd_c1"] = self.commit(work, "c1")
                self.write(work / "b.txt", "b\n")
                self.sha["jd_c2"] = self.commit(work, "c2")
                self.git(work, "push", "-q", "origin", "main")
            else:
                self.write(work / "README.md", f"{name}\n")
                self.commit(work, "c0")
                self.git(work, "push", "-q", "origin", "main")

    def build_primaries(self) -> None:
        for name in PRIMARIES:
            url = f"file://{self.remotes / (name + '.git')}"
            args = ["clone", "-q"] + (["--depth", "5"] if name == "juniper-ml" else []) + [url, str(self.root / name)]
            self.git(self.root, *args)
        ml = self.root / "juniper-ml"
        check("fixture: juniper-ml primary is shallow, as on the host", (ml / ".git" / "shallow").exists())
        self.git(self.root / "juniper-data", "branch", "fix/gone", self.sha["jd_c2"])
        self.git(self.root / "juniper-data", "branch", "fix/gone-ok", self.sha["jd_c1"])

    # ------------------------------------------------------------------ worktrees
    def add_row(self, name: str, path: Path, repo: str, batch: str, branch: str, head: str, **kw) -> dict:
        location = "juniper-ml/.claude/worktrees/" if path.relative_to(self.root).parts[:3] == ("juniper-ml", ".claude", "worktrees") else "worktrees/"
        row = {
            "name": name,
            "path": str(path),
            "location": location,
            "repo": repo,
            "kind": kw.pop("kind", "linked-worktree"),
            "branch": branch,
            "head_sha": head[:12] if head else "",
            "name_sha": kw.pop("name_sha", ""),
            "batch": batch,
            "flags": kw.pop("flags", []),
            "identified_by": kw.pop("identified_by", "name"),
            "related_prs": kw.pop("related_prs", []),
            "own_prs": kw.pop("own_prs", []),
            "item": kw.pop("item", "fixture"),
            "evidence": "fixture",
        }
        row.update(kw)
        self.rows.append(row)
        return row

    def worktree(self, repo: str, path: Path, commit: str, branch: str = "") -> None:
        prim = self.root / repo
        if branch:
            self.git(prim, "worktree", "add", "-q", "-b", branch, str(path), commit)
        else:
            self.git(prim, "worktree", "add", "-q", "--detach", str(path), commit)

    def build_worktrees(self) -> None:
        s = self.sha
        ml = self.root / "juniper-ml"
        wts = self.root / "worktrees"
        cl = ml / ".claude" / "worktrees"
        wts.mkdir()
        cl.mkdir(parents=True)
        pr101 = ["juniper-ml#101 MERGED 2026-11-10T00:00:00Z"]
        pr201 = ["juniper-cascor#201 MERGED 2026-11-10T00:00:00Z"]
        # A1, juniper-cascor: a local commit (bundle), an untracked new file, tmp/
        p = wts / f"juniper-cascor--fix--a1-one--20261108-1815--{s['cc_c1'][:8]}"
        self.worktree("juniper-cascor", p, s["cc_c1"], "fix/a1-one")
        self.write(p / "src" / "feature.py", "feature v1\n")
        s["cc_l2"] = self.commit(p, "local commit, uploaded as #201 through the API")
        self.write(p / "notes.txt", "my notes\n")
        self.write(p / "tmp" / "run.log", "run log\n")
        self.add_row(p.name, p, "juniper-cascor", "A", "fix/a1-one", s["cc_l2"], name_sha=s["cc_c1"][:8], related_prs=pr201, flags=["HEAD-MOVED"])
        # A1, juniper-cascor: its branch also exists on origin -> branch kept
        p = wts / f"juniper-cascor--fix--remote-kept--20261108-1816--{s['cc_c1'][:8]}"
        self.worktree("juniper-cascor", p, s["cc_c1"], "fix/remote-kept")
        self.add_row(p.name, p, "juniper-cascor", "A", "fix/remote-kept", s["cc_c1"], name_sha=s["cc_c1"][:8], related_prs=pr201)
        # A1, juniper-data: clean, detached, tmp/
        p = wts / f"juniper-data--test--clean--20261112-1832--{s['jd_c1'][:8]}"
        self.worktree("juniper-data", p, s["jd_c1"])
        self.write(p / "tmp" / "x.txt", "x\n")
        self.add_row(p.name, p, "juniper-data", "A", "", s["jd_c1"], name_sha=s["jd_c1"][:8], flags=["ITEM-CODE-ONLY"], identified_by="item-code")
        # A1, juniper-data: absent worktrees; one branch moved since the inventory, one did not
        p = wts / f"juniper-data--fix--gone--20261112-1846--{s['jd_c1'][:8]}"
        self.add_row(p.name, p, "juniper-data", "A", "fix/gone", s["jd_c1"], name_sha=s["jd_c1"][:8])
        p = wts / f"juniper-data--fix--gone-ok--20261112-1847--{s['jd_c1'][:8]}"
        self.add_row(p.name, p, "juniper-data", "A", "fix/gone-ok", s["jd_c1"], name_sha=s["jd_c1"][:8])
        # A2, the 11-06 five: a local commit, and a tracked edit only PR #101's head holds
        p = wts / f"juniper-ml--fix--five-one--20261104-0331--{s['ml_c1'][:8]}"
        self.worktree("juniper-ml", p, s["ml_c1"], "fix/five-one")
        self.write(p / "notes" / "local.md", "local\n")
        s["ml_l1"] = self.commit(p, "a local commit")
        self.write(p / "docs" / "a.md", "A\nPR\n")
        self.add_row(p.name, p, "juniper-ml", "A", "fix/five-one", s["ml_l1"], name_sha=s["ml_c1"][:8], related_prs=pr101, identified_by="five", flags=["HEAD-MOVED"])
        # A2, linked: untracked landed + new files, tmp/, ignored .venv (moved) and __pycache__ (a cache)
        p = wts / f"juniper-ml--test--landed-untracked--20261112-1815--{s['ml_c2'][:8]}"
        self.worktree("juniper-ml", p, s["ml_c2"])
        self.write(p / "util" / "ad-hoc" / "helper.py", "# Owner: the fixture\nprint('helper')\n")
        self.write(p / "util" / "ad-hoc" / "new_work.py", "print('new work')\n")
        self.write(p / "tmp" / "sub" / "evidence.txt", "evidence\n")
        self.write(p / "tmp" / "a.txt", "a\n")
        self.write(p / ".venv" / "bin" / "python", "fake interpreter\n")
        self.write(p / ".venv" / "pyvenv.cfg", "home = x\n")
        self.write(p / "util" / "__pycache__" / "x.cpython-314.pyc", "pyc\n")
        self.add_row(p.name, p, "juniper-ml", "A", "", s["ml_c2"], name_sha=s["ml_c2"][:8], related_prs=pr101)
        # A2, simulation directories: one plain, one with a .git inside (skipped)
        p = wts / "juniper-ml--sims--fixture-s1--20261114-1805"
        for sub in ("landed--minor/README.md", "landed--minor/util/a.py", "main--patch/x.txt", "main--patch/deep/er/y.txt"):
            self.write(p / sub, "sim\n")
        self.add_row(p.name, p, "juniper-ml", "A", "", "", kind="not-a-git-checkout", flags=["PLAIN-DIR"])
        p = wts / "juniper-ml--sims--fixture-s2--20261114-2004"
        self.write(p / "copy" / "README.md", "sim\n")
        self.write(p / "copy" / ".git" / "HEAD", "ref: refs/heads/main\n")
        self.add_row(p.name, p, "juniper-ml", "A", "", "", kind="not-a-git-checkout", flags=["PLAIN-DIR"])
        # A2, the held plain directory (PLAIN_HOLD's real name): kept by default, archived whole on --held archive
        p = wts / "juniper-ml--val--flood4r2-n4-claims--20261109-0958--f85fbc8b"
        self.write(p / "util" / "ad-hoc" / "2026-11-09_flood4r2_n4_manifest.py", "print('the only original copy')\n")
        self.write(p / "docs" / "REFERENCE.md", "a validated carrier file\n")
        self.add_row(p.name, p, "juniper-ml", "A", "", "", kind="not-a-git-checkout", flags=["PLAIN-DIR"])
        # A3, rename-touched: tracked files and a symlink substituted, a genuine edit, staged-only content
        p = cl / "agent-afixture00000000001"
        self.worktree("juniper-ml", p, s["ml_c1"], "worktree-agent-afixture00000000001")
        for rel in ("README.md", "AGENTS.md", "util/x.py"):
            (p / rel).write_bytes(substitute((p / rel).read_bytes()))
        target = (p / "AGENTS.md").read_bytes()
        (p / "CLAUDE.md").unlink()
        (p / "CLAUDE.md").write_bytes(target)
        self.write(p / "docs" / "a.md", substitute(b"A\nmy own edit by the owner\n").decode())
        self.write(p / "util" / "ad-hoc" / "helper.py", substitute(b"# Owner: the fixture\nprint('helper')\n").decode())
        self.write(p / "util" / "y.py", "y = 'staged version'\n")
        self.git(p, "add", "util/y.py")
        self.write(p / "util" / "y.py", "y = 'worktree version'\n")
        self.write(p / "tmp" / "s" / "log.txt", "a log by the Overtoad\n")
        self.add_row(p.name, p, "juniper-ml", "A", "worktree-agent-afixture00000000001", s["ml_c1"], related_prs=pr101, flags=["RENAME-TOUCHED"], identified_by="curated")
        # A3, a carrier a handoff said to keep: processed last in its wave
        p = cl / "agent-a7aa0806f2312b786"
        self.worktree("juniper-ml", p, s["ml_c2"], "worktree-agent-a7aa0806f2312b786")
        self.write(p / "tmp" / "keep.txt", "keep\n")
        self.add_row(p.name, p, "juniper-ml", "A", "worktree-agent-a7aa0806f2312b786", s["ml_c2"], related_prs=pr101, identified_by="curated")
        # A3, live (a process inside), recent, moved, locked, nesting
        for tag, num in (("live", 2), ("recent", 3), ("moved", 4), ("locked", 5), ("nested", 6)):
            name = f"agent-afixture{tag}{num:0{11 - len(tag)}d}"
            p = cl / name
            self.worktree("juniper-ml", p, s["ml_c1"], f"worktree-{name}")
            inv_head = s["ml_c2"] if tag == "moved" else s["ml_c1"]
            self.add_row(name, p, "juniper-ml", "A", f"worktree-{name}", inv_head, related_prs=pr101, identified_by="curated", tag=tag)
        live = next(r for r in self.rows if r.get("tag") == "live")
        recent = next(r for r in self.rows if r.get("tag") == "recent")
        self.write(Path(recent["path"]) / "tmp" / "new.txt", "written just now\n")
        self.recent_file = Path(recent["path"]) / "tmp" / "new.txt"
        locked = next(r for r in self.rows if r.get("tag") == "locked")
        self.git(ml, "worktree", "lock", "--reason", "fixture", locked["path"])
        nested = next(r for r in self.rows if r.get("tag") == "nested")
        self.git(ml, "worktree", "add", "-q", "--detach", str(Path(nested["path"]) / ".claude" / "worktrees" / "inner"), s["ml_c1"])
        self.live_path = Path(live["path"])
        # B: a launch worktree, a ruling-37 marker with uncommitted edits, a detached cascor tree
        p = cl / "joyful-fixture-kahan"
        self.worktree("juniper-ml", p, s["ml_c2"], "worktree-joyful-fixture-kahan")
        self.add_row(p.name, p, "juniper-ml", "B", "worktree-joyful-fixture-kahan", s["ml_c2"], flags=["NO-PR", "RENAME-TOUCHED"], identified_by="curated")
        p = wts / f"juniper-cascor--fix--marker--20261115-0540--{s['cc_c1'][:8]}"
        self.worktree("juniper-cascor", p, s["cc_c1"], "fix/marker")
        self.write(p / "src" / "core.py", "core = 2  # the marker\n")
        self.write(p / "README.md", "cascor owner, marked\n")
        (p / "src" / "util.py").unlink()
        self.add_row(p.name, p, "juniper-cascor", "B", "fix/marker", s["cc_c1"], name_sha=s["cc_c1"][:8], flags=["NO-PR"])
        p = wts / f"juniper-cascor--detached-origin-main--20261109-1004--{s['cc_m201'][:8]}"
        self.worktree("juniper-cascor", p, s["cc_m201"])
        self.add_row(p.name, p, "juniper-cascor", "B", "", s["cc_m201"], name_sha=s["cc_m201"][:8], flags=["NO-PR", "PROVENANCE-INFERRED"], identified_by="inferred")
        # H: humming. On the host its own HEAD moved (its reflog: commits, rebases and a pull, 2026-11-21..23), so its index matches
        # HEAD; this fixture moves only the branch ref (a stale index), the harder case. Compared with session 9's HEAD as well
        p = cl / "humming-stargazing-papert"
        self.worktree("juniper-ml", p, s["ml_c1"], "worktree-humming-stargazing-papert")
        for rel in ("README.md", "AGENTS.md", "util/x.py"):
            (p / rel).write_bytes(substitute((p / rel).read_bytes()))
        self.write(p / "util" / "ad-hoc" / "s9_helper.py", "print('session 9 work')\n")
        self.write(p / "tmp" / "flood4" / "STATE.txt", "state log\n")
        self.git(ml, "fetch", "-q", "origin", "rename-pr")
        self.git(ml, "update-ref", "refs/heads/worktree-humming-stargazing-papert", s["ml_r"])
        self.add_row(p.name, p, "juniper-ml", "C", "worktree-humming-stargazing-papert", s["ml_r"], related_prs=pr101, flags=["LIVE", "ARCHIVE-LAST", "RENAME-TOUCHED"], identified_by="curated")
        # regression trees for the session-13 code lens: a tracked file turned into a directory (C2), a saved
        # uncommitted.patch (C1), an assume-unchanged edit (C4), a file name that is not UTF-8 (C3)
        p = wts / f"juniper-ml--test--file-to-dir--20261112-1816--{s['ml_c2'][:8]}"
        self.worktree("juniper-ml", p, s["ml_c2"])
        (p / "docs" / "b.md").unlink()
        self.write(p / "docs" / "b.md" / "notes.txt", "notes in a directory that replaced a tracked file\n")
        self.add_row(p.name, p, "juniper-ml", "A", "", s["ml_c2"], related_prs=pr101)
        p = wts / f"juniper-data--test--patch-name--20261112-1833--{s['jd_c1'][:8]}"
        self.worktree("juniper-data", p, s["jd_c1"])
        self.write(p / "uncommitted.patch", "a patch a session left here\n")
        self.write(p / "a.txt", "a edited\n")
        self.add_row(p.name, p, "juniper-data", "A", "", s["jd_c1"])
        p = wts / f"juniper-data--test--assume-unchanged--20261112-1834--{s['jd_c1'][:8]}"
        self.worktree("juniper-data", p, s["jd_c1"])
        self.write(p / "a.txt", "an edit git status cannot see\n")
        self.git(p, "update-index", "--assume-unchanged", "a.txt")
        self.add_row(p.name, p, "juniper-data", "A", "", s["jd_c1"])
        p = wts / f"juniper-cascor--test--latin1--20261108-1817--{s['cc_c1'][:8]}"
        self.worktree("juniper-cascor", p, s["cc_c1"])
        with open(os.fsencode(str(p)) + b"/caf\xe9.txt", "wb") as fh:
            fh.write(b"a latin-1 file name\n")
        self.add_row(p.name, p, "juniper-cascor", "A", "", s["cc_c1"], related_prs=pr201)
        # C: names the script must never touch
        for name in ("playful-scribbling-kite", "curious-plotting-hummingbird"):
            p = cl / name
            self.worktree("juniper-ml", p, s["ml_c2"], f"worktree-{name}")
            self.write(p / "tmp" / "mine.txt", "not yours\n")
            self.add_row(name, p, "juniper-ml", "C", f"worktree-{name}", s["ml_c2"], flags=["EXCLUDED"])

    def age(self) -> None:
        old = time.time() - TWO_DAYS
        for dirpath, dirnames, filenames in os.walk(self.root, topdown=False):
            for n in filenames + dirnames:
                path = os.path.join(dirpath, n)
                if path != str(self.recent_file):
                    os.utime(path, (old, old), follow_symlinks=False)
            os.utime(dirpath, (old, old))

    def write_inputs(self) -> tuple[Path, Path]:
        inv = self.base / "inventory.json"
        rows = [{k: v for k, v in r.items() if k != "tag"} for r in self.rows]
        inv.write_text(json.dumps({"generated_utc": "fixture", "count": len(rows), "rows": rows}, indent=1), encoding="utf-8")
        prs = self.base / "pr_commits.jsonl"
        lines = [
            {"repo": "juniper-ml", "number": 101, "state": "MERGED", "merge": self.sha["ml_m101"], "head": self.sha["ml_h101"]},
            {"repo": "juniper-cascor", "number": 201, "state": "MERGED", "merge": self.sha["cc_m201"], "head": self.sha["cc_h201"]},
        ]
        prs.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        return inv, prs

    def snapshot(self) -> dict[str, tuple]:
        snap: dict[str, tuple] = {}
        for dirpath, dirnames, filenames in os.walk(self.root):
            for n in dirnames + filenames:
                path = os.path.join(dirpath, n)
                st = os.lstat(path)
                digest = ""
                if os.path.isfile(path) and not os.path.islink(path) and st.st_size < (1 << 20):
                    with open(path, "rb") as fh:
                        digest = hashlib.sha256(fh.read()).hexdigest()
                snap[os.path.relpath(path, self.root)] = (st.st_mode, st.st_size, st.st_mtime_ns, digest)
        return snap

    def run_script(self, label: str, *args: str) -> tuple[int, str]:
        p = subprocess.run([sys.executable, str(CLEANUP), "--juniper-root", str(self.root), *args], capture_output=True, env=self.env, stdin=subprocess.DEVNULL, check=False)  # nosec B603
        out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
        (self.logs / f"{label}.log").write_text(out, encoding="utf-8")
        return p.returncode, out


def results_by_name(path: Path) -> tuple[dict[str, dict], list[dict]]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return {r["name"]: r for r in payload["results"]}, payload["branches"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--dir", type=Path, required=True, help="a directory that does not exist yet")
    args = parser.parse_args()
    base = args.dir.resolve()
    if base.exists():
        print(f"{base} exists: give a new directory")
        return 2
    fx = Fixture(base)
    try:
        return run_checks(fx)
    finally:
        if fx.sleeper is not None:
            fx.sleeper.kill()
            fx.sleeper.wait()


def run_checks(fx: Fixture) -> int:
    fx.build_remotes()
    fx.build_primaries()
    fx.build_worktrees()
    inv, prs = fx.write_inputs()
    rows = {r["name"]: r for r in fx.rows}
    a = [r for r in fx.rows if r["batch"] == "A"]
    b = [r for r in fx.rows if r["batch"] == "B"]
    counts = f"{len(a)}:{len(b)}:{sum(1 for r in a if r['kind'] != 'linked-worktree')}:{len({(r['repo'], r['branch']) for r in a + b if r['branch']})}:1"
    fx.age()
    fx.sleeper = subprocess.Popen(["sleep", "900"], cwd=str(fx.live_path))  # nosec B603 B607
    common = ["--inventory", str(inv), "--pr-commits", str(prs), "--ruled-counts", counts, "--last-extra-base", fx.sha["ml_c1"], "--ruled-inventory-sha256", sha256(inv)]
    archive = fx.root / "juniper-ml" / "tmp" / ARCHIVE_NAME

    # refusals
    code, out = fx.run_script("refuse-counts", "--inventory", str(inv), "--pr-commits", str(prs))
    check("refuses a selection whose counts differ from the ruling's", code == 2 and "differ from the ruled" in out, out[-300:])
    code, out = fx.run_script("refuse-confirm", *common, "--execute")
    check("refuses --execute without --yes when stdin is not a terminal", code == 2 and "needs a terminal" in out, out[-300:])
    bad = json.loads(inv.read_text(encoding="utf-8"))
    bad["rows"].append(dict(bad["rows"][0], name="hidden-scribbling-toast", path=str(fx.root / "juniper-ml" / ".claude" / "worktrees" / "hidden-scribbling-toast"), location="juniper-ml/.claude/worktrees/"))
    bad_inv = fx.base / "inventory-never.json"
    bad_inv.write_text(json.dumps(bad), encoding="utf-8")
    code, out = fx.run_script("refuse-never", "--inventory", str(bad_inv), "--pr-commits", str(prs), "--ruled-counts", counts)
    check("refuses an inventory that selects a never-touched name", code == 2 and "never to be touched" in out, out[-300:])
    bad = json.loads(inv.read_text(encoding="utf-8"))
    bad["rows"][0]["path"] = str(fx.base / "elsewhere" / bad["rows"][0]["name"])
    bad_inv = fx.base / "inventory-outside.json"
    bad_inv.write_text(json.dumps(bad), encoding="utf-8")
    code, out = fx.run_script("refuse-outside", "--inventory", str(bad_inv), "--pr-commits", str(prs), "--ruled-counts", counts)
    check("refuses an entry whose path is not under the root", code == 2 and "is not <" in out, out[-300:])

    # --list and the dry run: no change at all
    before = fx.snapshot()
    code, out = fx.run_script("list", *common, "--list")
    check("--list exits 0 and prints the waves and the 14 branches", code == 0 and "wave A1" in out and "branches (14):" in out, out[-300:])
    code, out = fx.run_script("dry", *common, "--json", str(fx.base / "dry.json"))
    after = fx.snapshot()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    check("dry run exits 0", code == 0, out[-500:])
    check("dry run changes no file under the root (incl. every .git)", not changed, ", ".join(changed[:8]))
    check("dry run creates no archive", not archive.exists())
    dry, _ = results_by_name(fx.base / "dry.json")
    five = rows[next(n for n in rows if "five-one" in n)]["name"]
    check("dry run (no --fetch): the edit only PR #101's head holds is SAVED", any(s["path"] == "docs/a.md" for s in dry[five]["saved"]), json.dumps(dry[five]["saved"]))
    code, out = fx.run_script("dry-fetch", *common, "--fetch", "--json", str(fx.base / "dry-fetch.json"))
    dryf, _ = results_by_name(fx.base / "dry-fetch.json")
    check("--fetch dry run exits 0", code == 0, out[-500:])
    check("--fetch: that edit is recognised as juniper-ml#101's head", not any(s["path"] == "docs/a.md" for s in dryf[five]["saved"]) and "#101 head" in (fx.logs / "dry-fetch.log").read_text(encoding="utf-8"), json.dumps(dryf[five]["saved"]))
    check("dry run: humming waits for the others", dry["humming-stargazing-papert"]["outcome"] == "skip" and "goes last" in " ".join(dry["humming-stargazing-papert"]["reasons"]))

    # execute
    code, out = fx.run_script("execute", *common, "--fetch", "--execute", "--yes", "--json", str(fx.base / "exec.json"))
    check("execute exits 0 (nothing failed or partial)", code == 0, out[-800:])
    ex, br = results_by_name(fx.base / "exec.json")
    expect = {
        "removed": [n for n in rows if any(t in n for t in ("a1-one", "remote-kept", "test--clean", "five-one", "landed-untracked", "afixture00000000001", "a7aa0806", "joyful", "fix--marker", "detached-origin-main", "file-to-dir", "latin1"))],
        "deleted": [n for n in rows if "fixture-s1" in n],
        "skip": [n for n in rows if any(t in n for t in ("fix--gone", "fixture-s2", "live", "recent", "moved", "locked", "nested", "humming-stargazing", "patch-name", "assume-unchanged", "n4-claims"))],
    }
    for outcome, names in expect.items():
        for n in names:
            check(f"outcome {outcome}: {n}", ex.get(n, {}).get("outcome") == outcome, f"got {ex.get(n, {}).get('outcome')} {ex.get(n, {}).get('reasons')}")
    reasons = {n: " ".join(ex[n]["reasons"]) for n in ex}
    for tag, needle in (("live", "processes inside"), ("recent", "modified in the last"), ("moved", "HEAD moved"), ("locked", "locked"), ("nested", "holds registered worktree"), ("fixture-s2", ".git entries inside"), ("fix--gone", "absent"), ("patch-name", "would be overwritten"), ("assume-unchanged", "assume-unchanged"), ("n4-claims", "held for the Overtoad's word")):
        n = next(k for k in reasons if tag in k)
        check(f"skip reason for {tag}: {needle!r}", needle in reasons[n], reasons[n])
    for n in ("playful-scribbling-kite", "curious-plotting-hummingbird"):
        check(f"never-touched {n} is not processed and is intact", n not in ex and (Path(rows[n]["path"]) / "tmp" / "mine.txt").exists())
    for n in expect["skip"]:
        if "fix--gone" not in n:
            check(f"skipped {n} is intact", Path(rows[n]["path"]).is_dir() and (rows[n]["kind"] != "linked-worktree" or (Path(rows[n]["path"]) / ".git").is_file()))
    for n in expect["removed"] + expect["deleted"]:
        check(f"gone from disk: {n}", not Path(rows[n]["path"]).exists())
    registered = fx.git(fx.root / "juniper-ml", "worktree", "list", "--porcelain")
    check("removed juniper-ml worktrees are no longer registered", all(rows[n]["path"] not in registered for n in expect["removed"] if rows[n]["repo"] == "juniper-ml"))

    # archive contents
    def saved_set(n: str) -> set[str]:
        d = archive / n / "saved"
        return {str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() or p.is_symlink()} if d.exists() else set()

    lu = next(n for n in rows if "landed-untracked" in n)
    check("landed-untracked: saved only the new file", saved_set(lu) == {"util/ad-hoc/new_work.py"}, str(saved_set(lu)))
    check("landed-untracked: tmp/ moved intact", (archive / lu / "tmp" / "sub" / "evidence.txt").read_text(encoding="utf-8") == "evidence\n")
    check("landed-untracked: .venv moved to ignored/, __pycache__ left as a cache", (archive / lu / "ignored" / ".venv" / "bin" / "python").exists() and not (archive / lu / "ignored" / "util").exists())
    rn = "agent-afixture00000000001"
    check("rename-touched: saved exactly the genuine edit, the worktree file and the staged-only content", saved_set(rn) == {"docs/a.md", "util/y.py", "util/y.py.staged-index", "uncommitted.patch"}, str(saved_set(rn)))
    status = (archive / rn / "STATUS.tsv").read_text(encoding="utf-8")
    for path, cat in (("README.md", "substitution-of-base"), ("AGENTS.md", "substitution-of-base"), ("util/x.py", "substitution-of-base"), ("CLAUDE.md", "symlink-copy"), ("util/ad-hoc/helper.py", "substitution-of-base")):
        check(f"rename-touched: {path} is {cat}", any(line.split("\t")[1] == cat and line.split("\t")[-1] == path for line in status.splitlines()[1:]), status)
    check("rename-touched: the staged-only blob is the staged text", (archive / rn / "saved" / "util" / "y.py.staged-index").read_text(encoding="utf-8") == "y = 'staged version'\n")
    a1 = next(n for n in rows if "a1-one" in n)
    check("a1-one (a repo that does not ignore tmp/): saved only notes.txt, none of tmp/", saved_set(a1) == {"notes.txt"} and (archive / a1 / "tmp" / "run.log").exists(), str(saved_set(a1)))
    dc = next(n for n in rows if "test--clean" in n)
    check("data clean (tmp/ not ignored either): nothing saved, tmp/ moved", not saved_set(dc) and (archive / dc / "tmp" / "x.txt").exists(), str(saved_set(dc)))
    in_tmp = [f"{d.name}: {line}" for d in archive.iterdir() if (d / "STATUS.tsv").exists() for line in (d / "STATUS.tsv").read_text(encoding="utf-8", errors="surrogateescape").splitlines()[1:] if line.split("\t")[-1].startswith("tmp/")]
    ftd = next(n for n in rows if "file-to-dir" in n)
    check("file-to-dir: the directory that replaced a tracked file is saved whole, nothing else", saved_set(ftd) == {"docs/b.md/notes.txt"}, str(saved_set(ftd)))
    l1 = next(n for n in rows if "latin1" in n)
    check("latin1: a non-UTF-8 file name is saved under its own bytes", os.path.isfile(os.fsencode(str(archive / l1 / "saved")) + b"/caf\xe9.txt"))
    check("no STATUS.tsv lists a tmp/ path (tmp/ moves whole)", not in_tmp, "; ".join(in_tmp[:4]))
    mk = next(n for n in rows if "fix--marker" in n)
    check("marker: saved both uncommitted edits and the patch", saved_set(mk) == {"src/core.py", "README.md", "uncommitted.patch"}, str(saved_set(mk)))
    check("marker: the patch holds both edits", all(x in (archive / mk / "saved" / "uncommitted.patch").read_text(encoding="utf-8") for x in ("core = 2", "marked")))
    check("marker (batch B, not substituted): the patch is the WHOLE tracked diff, its deletion included", "deleted file mode" in (archive / mk / "saved" / "uncommitted.patch").read_text(encoding="utf-8") and "src/util.py" in (archive / mk / "saved" / "uncommitted.patch").read_text(encoding="utf-8"))
    blockers = [n for n in expect["skip"] if not any(t in n for t in ("fix--gone", "n4-claims", "humming-stargazing"))]
    check(f"humming's gate counts {len(blockers)} blocking skips: not the absent entries, not the held directory", f"{len(blockers)} entries were skipped or failed" in reasons["humming-stargazing-papert"], reasons["humming-stargazing-papert"])
    held = next(n for n in rows if "n4-claims" in n)
    check("the held directory is intact after the run (--held keep is the default)", (Path(rows[held]["path"]) / "util" / "ad-hoc" / "2026-11-09_flood4r2_n4_manifest.py").exists() and not (archive / held).exists())
    for n, repo in ((next(k for k in rows if "a1-one" in k), "juniper-cascor"), (five, "juniper-ml")):
        bundle = archive / n / "commits.bundle"
        ok = bundle.exists()
        heads = fx.git(fx.root / repo, "bundle", "list-heads", str(bundle)) if ok else ""
        check(f"bundle of {n}'s local commit exists and lists HEAD (shallow primary: {repo == 'juniper-ml'})", ok and "HEAD" in heads and fx.sha["cc_l2" if repo == "juniper-cascor" else "ml_l1"] in heads, heads)
    bad_sha = []
    for manifest in archive.glob("*/MANIFEST.txt"):
        for line in manifest.read_text(encoding="utf-8", errors="surrogateescape").splitlines():
            parts = line.split("  ")
            if len(parts) >= 2 and len(parts[0]) in (64, 72) and (parts[0].startswith("symlink:") or all(c in "0123456789abcdef" for c in parts[0])):
                target = manifest.parent / parts[1]
                if not target.exists() and not target.is_symlink() or sha256(target) != parts[0]:
                    bad_sha.append(f"{manifest.parent.name}: {parts[1]}")
    check("every sha256 line in every MANIFEST.txt verifies", not bad_sha, ", ".join(bad_sha[:5]))
    check("saved copies hold the worktree's own bytes", (archive / lu / "saved" / "util" / "ad-hoc" / "new_work.py").read_bytes() == b"print('new work')\n" and (archive / mk / "saved" / "src" / "core.py").read_bytes() == b"core = 2  # the marker\n" and (archive / rn / "saved" / "docs" / "a.md").read_bytes() == substitute(b"A\nmy own edit by the owner\n"))
    s1 = next(n for n in rows if "fixture-s1" in n)
    with gzip.open(archive / s1 / "FILELIST.tsv.gz", "rt", encoding="utf-8") as fh:
        flist = fh.read().splitlines()
    check("simulation directory: FILELIST lists every entry (4 files, 5 dirs)", len(flist) == 1 + 9, str(len(flist)))
    index = (archive / "INDEX.tsv").read_text(encoding="utf-8").splitlines()
    check("INDEX.tsv: one row per removed worktree or deleted directory", len(index) == 1 + len(expect["removed"]) + len(expect["deleted"]), str(len(index)))
    check("README.md, runs/ log and JSON, provenance/ copies exist", (archive / "README.md").exists() and len(list((archive / "runs").glob("*-execute.log"))) == 1 and (archive / "provenance" / "inventory.json").exists())

    # branches
    deleted = (archive / "deleted_branches.txt").read_text(encoding="utf-8").splitlines()
    want_deleted = {
        ("juniper-cascor", "fix/a1-one", fx.sha["cc_l2"]),
        ("juniper-data", "fix/gone-ok", fx.sha["jd_c1"]),
        ("juniper-ml", "fix/five-one", fx.sha["ml_l1"]),
        ("juniper-ml", "worktree-agent-afixture00000000001", fx.sha["ml_c1"]),
        ("juniper-ml", "worktree-agent-a7aa0806f2312b786", fx.sha["ml_c2"]),
        ("juniper-ml", "worktree-joyful-fixture-kahan", fx.sha["ml_c2"]),
        ("juniper-cascor", "fix/marker", fx.sha["cc_c1"]),
    }
    got = {tuple(line.split(" ")) for line in deleted if not line.startswith("#")}
    check("deleted_branches.txt holds exactly the seven deletable branches with full shas", got == want_deleted, str(got ^ want_deleted))
    for repo, b, _ in want_deleted:
        p = subprocess.run(["git", "-C", str(fx.root / repo), "rev-parse", "--verify", "-q", f"refs/heads/{b}"], capture_output=True, env=fx.env, check=False)  # nosec B603 B607
        check(f"branch deleted: {repo} {b}", p.returncode != 0)
    keep = {("juniper-cascor", "fix/remote-kept", "origin has a branch"), ("juniper-data", "fix/gone", "tip moved")}
    keep |= {("juniper-ml", f"worktree-{n}", "was not removed") for n in rows if any(t in n for t in ("live", "recent", "moved", "locked", "nested"))}
    brmap = {(x["repo"], x["branch"]): x for x in br}
    for repo, b, why in keep:
        x = brmap.get((repo, b), {})
        p = subprocess.run(["git", "-C", str(fx.root / repo), "rev-parse", "--verify", "-q", f"refs/heads/{b}"], capture_output=True, env=fx.env, check=False)  # nosec B603 B607
        check(f"branch kept: {repo} {b} ({why})", x.get("outcome") == "keep" and why in x.get("reason", "") and p.returncode == 0, json.dumps(x))
    log = (fx.logs / "execute.log").read_text(encoding="utf-8")
    pos = [log.find(f"== [{w}]") for w in ("A1", "A2", "A3", "B", "H")]
    check("waves run in order A1, A2, A3, B, H", all(p >= 0 for p in pos) and pos == sorted(pos), str(pos))
    a3 = [line for line in log.splitlines() if line.startswith("== [A3]")]
    check("A3: the kept carrier goes last in its wave", bool(a3) and "agent-a7aa0806f2312b786" in a3[-1], a3[-1] if a3 else "")
    a2 = [line for line in log.splitlines() if line.startswith("== [A2]")]
    n_plain = sum(1 for r in fx.rows if r["kind"] != "linked-worktree" and r["repo"] == "juniper-ml" and r["batch"] == "A")
    check(f"A2: the five first, the {n_plain} plain directories last", bool(a2) and "five-one" in a2[0] and all("plain directory" in line for line in a2[-n_plain:]) and not any("plain directory" in line for line in a2[:-n_plain]), " | ".join(a2))

    # humming, alone, last
    code, out = fx.run_script("execute-humming", *common, "--fetch", "--execute", "--yes", "--only", "humming-stargazing-papert", "--json", str(fx.base / "exec-h.json"))
    exh, brh = results_by_name(fx.base / "exec-h.json")
    hum = exh.get("humming-stargazing-papert", {})
    check("humming alone: removed", code == 0 and hum.get("outcome") == "removed", out[-800:])
    check("humming: saved only session 9's untracked helper", saved_set("humming-stargazing-papert") == {"util/ad-hoc/s9_helper.py"}, str(saved_set("humming-stargazing-papert")))
    check("humming: its moved HEAD is bundled", (archive / "humming-stargazing-papert" / "commits.bundle").exists())
    check("humming: tmp/ moved", (archive / "humming-stargazing-papert" / "tmp" / "flood4" / "STATE.txt").exists())
    p = subprocess.run(["git", "-C", str(fx.root / "juniper-ml"), "rev-parse", "--verify", "-q", "refs/heads/worktree-humming-stargazing-papert"], capture_output=True, env=fx.env, check=False)  # nosec B603 B607
    check("humming: its branch is kept (not among the ruled branches)", p.returncode == 0 and not brh)
    index = (archive / "INDEX.tsv").read_text(encoding="utf-8").splitlines()
    check("INDEX.tsv gained humming's row", len(index) == 2 + len(expect["removed"]) + len(expect["deleted"]) and index[-1].startswith("humming-stargazing-papert\t"))
    code, out = fx.run_script("execute-held-archive", *common, "--execute", "--yes", "--only", held, "--held", "archive", "--json", str(fx.base / "exec-held.json"))
    exa, _ = results_by_name(fx.base / "exec-held.json")
    check("--held archive: the held directory is ARCHIVED, moved whole", code == 0 and exa.get(held, {}).get("outcome") == "archived", out[-600:])
    check("--held archive: its bytes are in <archive>/NAME/tree, gone from worktrees/", (archive / held / "tree" / "util" / "ad-hoc" / "2026-11-09_flood4r2_n4_manifest.py").read_text(encoding="utf-8") == "print('the only original copy')\n" and not Path(rows[held]["path"]).exists())
    check("--held archive: FILELIST and MANIFEST beside it; INDEX gained an 'archived' row", (archive / held / "FILELIST.tsv.gz").exists() and "archived whole" in (archive / held / "MANIFEST.txt").read_text(encoding="utf-8") and (archive / "INDEX.tsv").read_text(encoding="utf-8").splitlines()[-1].split("\t")[7] == "archived")
    code, out = fx.run_script("dry-after", *common, "--json", str(fx.base / "dry-after.json"))
    dra, _ = results_by_name(fx.base / "dry-after.json")
    check("a dry run afterwards reports the removed entries absent", code == 0 and all(dra[n]["outcome"] == "skip" and dra[n]["reasons"] == ["absent"] for n in expect["removed"] + expect["deleted"]))

    fails = [r for r in RESULTS if not r[0]]
    print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} checks passed; fixture and logs under {fx.base}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
