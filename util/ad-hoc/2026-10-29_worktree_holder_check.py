#!/usr/bin/env python3
"""
Report every live process that holds a path inside a cleanup target, by cwd, root, exe, cmdline, environ, open fd or mapping.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — one-off (flood-3 cleanup of 2026-10-29)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§6: the cleanup's gates);
         util/ad-hoc/2026-08-20_worktree_liveness_probe.py (cwd only; this widens it);
         util/ad-hoc/2026-10-26_worktree_blob_classify.py and 2026-10-26_worktree_preserve_unique.py (the other two gates)

Why this exists
---------------
The 2026-10-27 cleanup gated each removal on "no process held it (cwd, cmdline, environ, fds, maps)".
The liveness probe this repo already has reads only ``/proc/<pid>/cwd``. A process can hold a worktree
without sitting in it: a service launched with ``--app-dir <worktree>/src``, an interpreter that maps
an extension module from the worktree's venv, or an environment variable such as
``JUNIPER_EXP_CASCOR_SRC_DIR`` that a later restart would follow. So this walks all seven views of
every readable process.

    python3 -I util/ad-hoc/2026-10-29_worktree_holder_check.py <target> [<target> ...]

A target matches a value when the value is the target path or a path beneath it (component-wise, so
``…/foo`` does not match ``…/foo-bar``). Run one call with a positive control among the targets, such as
the directory the calling shell sits in: its own shell must be reported, or the check is blind.

Exit status: 0 when no target is held, 1 when any is held, 2 on bad arguments. Processes this user
cannot read are counted and reported, never silently treated as clear.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _under(value: str, target: str) -> bool:
    return value == target or value.startswith(target + os.sep)


def _scan_text_paths(text: str, target: str) -> bool:
    for token in text.replace("=", " ").replace(":", " ").split():
        if _under(token.rstrip("/"), target):
            return True
    return False


def _ancestors(pid: int) -> set[int]:
    """Every ancestor of ``pid`` up to init, read from ``/proc/<pid>/stat`` (field 4 is the parent)."""
    chain: set[int] = set()
    while pid > 1:
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            break
        # The command name (field 2) is parenthesised and may hold spaces, so split after its last ")".
        parent = int(stat.rsplit(")", 1)[1].split()[1])
        if parent in chain or parent <= 0:
            break
        chain.add(parent)
        pid = parent
    return chain


def holders(targets: list[str]) -> tuple[dict[str, list[tuple[int, str, str]]], int]:
    hits: dict[str, list[tuple[int, str, str]]] = dict()
    for target in targets:
        hits[target] = []
    unreadable = 0
    me = os.getpid()
    # The shell that launched this check carries the targets in its own argv, so its cmdline would
    # report every target as held. Skip the cmdline of every ancestor, and of every process whose
    # cmdline is IDENTICAL to an ancestor's: piped into grep, the shell forks a subshell that keeps
    # the launcher's cmdline but is not an ancestor of this process (measured 2026-10-29: `| cat`
    # read clear, `| grep` read HELD by that fork). Every other view (a cwd inside a target) counts.
    launchers = _ancestors(me)
    launcher_cmdlines = set()
    for ancestor in launchers:
        try:
            launcher_cmdlines.add(Path(f"/proc/{ancestor}/cmdline").read_bytes())
        except OSError:
            continue
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == me:
            continue
        pid = int(entry.name)
        views: list[tuple[str, str]] = []
        try:
            for link in ("cwd", "root", "exe"):
                try:
                    views.append((link, os.readlink(entry / link)))
                except FileNotFoundError:
                    continue
            raw_cmdline = (entry / "cmdline").read_bytes()
            if pid not in launchers and raw_cmdline not in launcher_cmdlines:
                views.append(("cmdline", raw_cmdline.replace(b"\0", b" ").decode(errors="replace")))
            environ = (entry / "environ").read_bytes().replace(b"\0", b"\n").decode(errors="replace")
            views.append(("environ", environ))
            fd_dir = entry / "fd"
            for fd in fd_dir.iterdir():
                try:
                    views.append((f"fd/{fd.name}", os.readlink(fd)))
                except OSError:
                    continue
            for line in (entry / "maps").read_text(errors="replace").splitlines():
                parts = line.split(None, 5)
                if len(parts) == 6:
                    views.append(("maps", parts[5]))
        except PermissionError:
            unreadable += 1
            continue
        except (FileNotFoundError, ProcessLookupError):
            continue  # the process exited mid-scan
        try:
            label = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()[:110]
        except OSError:
            label = "<exited>"
        for target in targets:
            for kind, value in views:
                matched = _scan_text_paths(value, target) if kind in ("cmdline", "environ") else _under(value.replace(" (deleted)", ""), target)
                if matched:
                    hits[target].append((pid, kind, label))
                    break
    return hits, unreadable


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    targets = [str(Path(a).resolve()) for a in sys.argv[1:]]
    hits, unreadable = holders(targets)
    held = 0
    for target in targets:
        found = hits[target]
        if found:
            held += 1
            print(f"HELD   {target}")
            for pid, kind, label in found:
                print(f"         pid {pid} via {kind}: {label}")
        else:
            print(f"clear  {target}")
    print(f"unreadable processes (other users / kernel threads): {unreadable}")
    return 1 if held else 0


if __name__ == "__main__":
    sys.exit(main())
