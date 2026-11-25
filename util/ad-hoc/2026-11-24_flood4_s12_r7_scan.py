#!/usr/bin/env python3
"""Read every worktree's git metadata, and every repository's worktree registry, by plain FILE READS (flood-4 session 12, ruling 7).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 7 and its "Still open"
    bullet); tmp/flood4/session12/briefs/R7_inventory.txt; the model it follows,
    util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash

A worktree-isolated session may not run git in another checkout, so this reads the files git itself reads: a linked
worktree's ``.git`` FILE (``gitdir: <repo>/.git/worktrees/<name>``), and in that gitdir ``HEAD`` (``ref: refs/heads/<b>``
or a sha), ``locked`` (present when locked; its text is the reason) and ``gitdir`` (the back-pointer to the worktree's
``.git`` file). Each repository's ``.git/worktrees/`` lists every registration, so one whose back-pointer names a
missing path is a stale registration (what ``git worktree prune`` would drop).

Then it finds every mention of each worktree's name (and of each ``agent-a<hex>`` id) in the given log trees with GNU
grep -F (fixed strings, one pass), and writes file:line evidence.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_scan.py --out DIR [--corpus PATH ...]
Writes <out>/scan_worktrees.json, <out>/scan_registries.json, <out>/mentions.tsv and <out>/scan_summary.txt.
It runs no git, changes nothing it reads, and writes only under --out.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 -- runs GNU grep only, with an argument list
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ROOTS = [
    ("worktrees/", JUNIPER / "worktrees"),
    ("juniper-ml/.claude/worktrees/", JUNIPER / "juniper-ml" / ".claude" / "worktrees"),
    ("juniper-canopy/.claude/worktrees/", JUNIPER / "juniper-canopy" / ".claude" / "worktrees"),
]
AGENT_RE = re.compile(r"agent-a[0-9a-f]{16}")


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _head(gitdir: Path) -> dict:
    text = _read(gitdir / "HEAD")
    if text is None:
        return {"head_raw": None, "branch": None, "detached_sha": None}
    if text.startswith("ref: "):
        ref = text[5:].strip()
        return {"head_raw": text, "branch": ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref, "detached_sha": None}
    return {"head_raw": text, "branch": None, "detached_sha": text}


def scan_worktree(location: str, path: Path) -> dict:
    row: dict = {"name": path.name, "path": str(path), "location": location, "is_dir": path.is_dir(), "is_symlink": path.is_symlink()}
    dotgit = path / ".git"
    if dotgit.is_file():
        text = _read(dotgit) or ""
        m = re.match(r"gitdir:\s*(.+)", text)
        gitdir = Path(m.group(1).strip()) if m else None
        row["kind"] = "linked-worktree" if gitdir else "dotgit-file-unparsed"
        row["gitdir"] = str(gitdir) if gitdir else None
        if gitdir is not None:
            # <repo>/.git/worktrees/<name>
            repo_dir = gitdir.parent.parent.parent if gitdir.parent.name == "worktrees" else None
            row["repo"] = repo_dir.name if repo_dir else None
            row["repo_dir"] = str(repo_dir) if repo_dir else None
            row["gitdir_exists"] = gitdir.is_dir()
            if gitdir.is_dir():
                row.update(_head(gitdir))
                back = _read(gitdir / "gitdir")
                row["backpointer"] = back
                row["backpointer_matches"] = back is not None and os.path.normpath(back) == os.path.normpath(str(dotgit))
                locked = gitdir / "locked"
                row["locked"] = locked.exists()
                row["locked_reason"] = (_read(locked) or "") if locked.exists() else None
                row["registered"] = bool(row["backpointer_matches"])
            else:
                row.update({"head_raw": None, "branch": None, "detached_sha": None, "backpointer": None, "backpointer_matches": False, "locked": False, "locked_reason": None, "registered": False})
    elif dotgit.is_dir():
        row["kind"] = "full-clone"
    else:
        row["kind"] = "not-a-git-checkout"
    return row


def scan_registries() -> list[dict]:
    rows = []
    for repo_dir in sorted(p for p in JUNIPER.iterdir() if (p / ".git").is_dir()):
        reg = repo_dir / ".git" / "worktrees"
        if not reg.is_dir():
            continue
        for g in sorted(reg.iterdir()):
            if not g.is_dir():
                continue
            back = _read(g / "gitdir")
            wt_path = str(Path(back).parent) if back else None
            row = {"repo": repo_dir.name, "registry_name": g.name, "gitdir": str(g), "backpointer": back, "worktree_path": wt_path,
                   "path_exists": bool(wt_path and Path(wt_path).exists()), "locked": (g / "locked").exists(),
                   "locked_reason": (_read(g / "locked") or "") if (g / "locked").exists() else None}
            row.update(_head(g))
            rows.append(row)
    return rows


def mentions(names: list[str], corpus: list[Path], out: Path) -> list[tuple[str, str, int]]:
    pat_file = out / "mention_patterns.txt"
    pat_file.write_text("\n".join(sorted(set(names))) + "\n", encoding="utf-8")
    found: set[tuple[str, str, int]] = set()
    for root in corpus:
        if not root.exists():
            print(f"corpus path absent, skipped: {root}", file=sys.stderr)
            continue
        cmd = ["/usr/bin/grep", "-r", "-I", "-n", "-o", "-F", "-f", str(pat_file), str(root)]
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False)  # nosec B603 -- fixed argv, no shell
        if proc.returncode not in (0, 1):
            print(f"grep exit {proc.returncode} on {root}: {proc.stderr[:400]}", file=sys.stderr)
        for line in proc.stdout.splitlines():
            # path:line:match -- split from the right: a match and a line number hold no ':'
            parts = line.rsplit(":", 2)
            if len(parts) != 3 or not parts[1].isdigit():
                continue
            found.add((parts[2], parts[0], int(parts[1])))
    return sorted(found)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--corpus", action="append", default=[], type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    wts = []
    for location, root in ROOTS:
        if not root.is_dir():
            continue
        for p in sorted(root.iterdir()):
            wts.append(scan_worktree(location, p))
    regs = scan_registries()
    (a.out / "scan_worktrees.json").write_text(json.dumps(wts, indent=1) + "\n", encoding="utf-8")
    (a.out / "scan_registries.json").write_text(json.dumps(regs, indent=1) + "\n", encoding="utf-8")
    names = [w["name"] for w in wts if w.get("is_dir")] + [r["registry_name"] for r in regs]
    names = [n for n in names if len(n) >= 12]  # every worktree name here is long; this drops nothing distinctive
    # logs often cite an agent by its bare id (a + 16 hex), without the worktree's "agent-" prefix
    names += [n[len("agent-"):] for n in names if AGENT_RE.fullmatch(n)]
    if a.corpus:
        ms = mentions(names, a.corpus, a.out)
        with (a.out / "mentions.tsv").open("w", encoding="utf-8") as fh:
            fh.write("name\tfile\tline\n")
            for n, f, ln in ms:
                fh.write(f"{n}\t{f}\t{ln}\n")
    kinds: dict[str, int] = {}
    for w in wts:
        key = f"{w['location']} {w.get('kind')}"
        kinds[key] = kinds.get(key, 0) + 1
    stale = [r for r in regs if not r["path_exists"]]
    lines = [f"worktree entries: {len(wts)}"] + [f"  {k}: {v}" for k, v in sorted(kinds.items())]
    lines.append(f"registrations: {len(regs)} in {len({r['repo'] for r in regs})} repositories; stale (path missing): {len(stale)}")
    for r in stale:
        lines.append(f"  STALE {r['repo']} {r['registry_name']} -> {r['worktree_path']}")
    unreg = [w for w in wts if w.get("kind") == "linked-worktree" and not w.get("registered")]
    lines.append(f"worktree dirs whose registration is missing or does not point back: {len(unreg)}")
    for w in unreg:
        lines.append(f"  UNREGISTERED {w['location']}{w['name']} gitdir={w.get('gitdir')} exists={w.get('gitdir_exists')} back={w.get('backpointer')}")
    (a.out / "scan_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
