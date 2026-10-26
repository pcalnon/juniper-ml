#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_session_tmpdir_hook_probe.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-10-26
# Last Modified: 2026-10-26
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#   The user-level Claude Code SessionStart hook that gives every session on a host the TMPDIR of
#   the Juniper repo it runs in (2026-10-26 /tmp rule), its known answers, and an idempotent
#   installer for ~/.claude/settings.json.
#
#   The hook appends `export TMPDIR=... TMP=... TEMP=...` to $CLAUDE_ENV_FILE, which Claude Code
#   sources before every Bash command. The value is the gitignored tmp/ of the PRIMARY checkout of
#   the Juniper repo holding $CLAUDE_PROJECT_DIR (a linked worktree resolves to its primary, so the
#   files outlive it), and juniper-ml's tmp/ for a project outside every Juniper repo. TMPDIR must
#   not go in settings `env`: that overrides the process environment, so it would give every repo
#   one path (measured 2026-10-26 with CLAUDE_CODE_TMPDIR). Claude Code's own files go under
#   settings `env.CLAUDE_CODE_TMPDIR`, which it reads in place of /tmp (measured the same day).
#
#   It also exports GIT_CEILING_DIRECTORIES. A TMPDIR inside a checkout makes git, run anywhere under
#   it, find the ENCLOSING checkout, so a "not a git repository" test fixture built under tmp_path
#   stops being one (juniper-deploy hit two; measured: without the ceiling `git -C <tmp>/a/b rev-parse
#   --show-toplevel` printed the checkout, with it git said "not a git repository"). The ceiling is
#   the primary's tmp/, plus the project's own top-level tmp/ when that is a linked worktree under a
#   Juniper repo (.claude/worktrees/) or under Juniper/worktrees/, then any inherited value; the
#   `${GIT_CEILING_DIRECTORIES:+...}` suffix is written literally and expands when the file is sourced.
#
# Usage:
#   python3 util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py              # run the known answers
#   python3 util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py --install    # merge into ~/.claude/settings.json
#####################################################################################################################################################################################################
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOOK_COMMAND = (
    'f="${CLAUDE_ENV_FILE:-}"; [ -n "$f" ] || exit 0; j="$HOME/Development/python/Juniper"; p="${CLAUDE_PROJECT_DIR:-$PWD}"; '
    'c=$(git -C "$p" rev-parse --path-format=absolute --git-common-dir 2>/dev/null); '
    'r="${c%/.git}"; case "$c" in */.git) ;; *) r="$j/juniper-ml";; esac; '
    'case "$r" in "$j"/juniper-*) ;; *) r="$j/juniper-ml";; esac; '
    'w=$(git -C "$p" rev-parse --show-toplevel 2>/dev/null); g="$r/tmp"; '
    'case "$w" in "$j"/juniper-*|"$j"/worktrees/*) [ "$w/tmp" = "$g" ] || g="$g:$w/tmp";; esac; '
    'mkdir -p "$r/tmp" && printf \'export TMPDIR="%s" TMP="%s" TEMP="%s" GIT_CEILING_DIRECTORIES="%s${GIT_CEILING_DIRECTORIES:+:$GIT_CEILING_DIRECTORIES}"\\n\' '
    '"$r/tmp" "$r/tmp" "$r/tmp" "$g" >> "$f"; exit 0'
)
MARKER = "juniper-repo-tmpdir"  # identifies the hook entry on re-install
CEILING_SUFFIX = "${GIT_CEILING_DIRECTORIES:+:$GIT_CEILING_DIRECTORIES}"  # written literally; expands when sourced

JUNIPER = Path.home() / "Development/python/Juniper"
HARNESS_TMP = JUNIPER / "juniper-ml/tmp"


def run_hook(project_dir: Path, env_file: Path) -> str:
    env_file.write_text("", encoding="utf-8")
    # No inherited GIT_* variable: the answer must not depend on the caller's GIT_DIR or ceiling.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(CLAUDE_ENV_FILE=str(env_file), CLAUDE_PROJECT_DIR=str(project_dir))
    subprocess.run(["sh", "-c", HOOK_COMMAND], env=env, check=True)
    return env_file.read_text(encoding="utf-8").strip()


def known_answers() -> int:
    worktree = Path(__file__).resolve().parents[2]
    primary_ml = JUNIPER / "juniper-ml"
    # A linked worktree resolves to its primary's tmp/ and adds its own tmp/ to the ceiling; run from the
    # primary itself, this file's checkout adds nothing.
    own = [worktree / "tmp"] if worktree != primary_ml else []
    cases = [
        (worktree, HARNESS_TMP, [HARNESS_TMP, *own]),
        (JUNIPER / "juniper-cascor/src", JUNIPER / "juniper-cascor/tmp", [JUNIPER / "juniper-cascor/tmp"]),
        (JUNIPER, HARNESS_TMP, [HARNESS_TMP]),  # the ecosystem parent is no git checkout
        (Path.home(), HARNESS_TMP, [HARNESS_TMP]),
    ]
    # A Juniper/worktrees/ linked worktree, named <repo>--..., when this host has one.
    linked_root = JUNIPER / "worktrees"
    linked = next((d for d in sorted(linked_root.glob("juniper-*--*")) if (d / ".git").is_file() and (JUNIPER / d.name.split("--")[0]).is_dir()), None) if linked_root.is_dir() else None
    if linked is not None:
        primary = JUNIPER / linked.name.split("--")[0]
        cases.append((linked, primary / "tmp", [primary / "tmp", linked / "tmp"]))
    env_file = HARNESS_TMP / "session-tmpdir-hook-probe.env"
    failures = 0
    for project, want, ceiling in cases:
        got = run_hook(project, env_file)
        expect = f'export TMPDIR="{want}" TMP="{want}" TEMP="{want}" GIT_CEILING_DIRECTORIES="{":".join(str(c) for c in ceiling)}{CEILING_SUFFIX}"'
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {project} -> {got}")
    env_file.unlink(missing_ok=True)
    unset = subprocess.run(["sh", "-c", HOOK_COMMAND], env={k: v for k, v in os.environ.items() if k != "CLAUDE_ENV_FILE"}, check=False)
    print(f"{'PASS' if unset.returncode == 0 else 'FAIL'}  no CLAUDE_ENV_FILE -> exit {unset.returncode}")
    failures += unset.returncode != 0
    print(f"{len(cases) + 1 - failures} of {len(cases) + 1} pass")
    return 1 if failures else 0


def install(settings_path: Path) -> int:
    data = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    backup = settings_path.with_name(settings_path.name + ".bak-2026-10-26")
    if settings_path.exists() and not backup.exists():
        shutil.copy2(settings_path, backup)
    data.setdefault("env", {})["CLAUDE_CODE_TMPDIR"] = str(HARNESS_TMP)
    starts = data.setdefault("hooks", {}).setdefault("SessionStart", [])
    starts[:] = [m for m in starts if not any(MARKER in h.get("command", "") for h in m.get("hooks", []))]
    starts.append({"hooks": [{"type": "command", "command": f": {MARKER}; {HOOK_COMMAND}"}]})
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"installed into {settings_path} (backup: {backup})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Known answers and installer for the Juniper session TMPDIR hook.")
    ap.add_argument("--install", action="store_true", help="merge the hook and CLAUDE_CODE_TMPDIR into the settings file")
    ap.add_argument("--settings", default=str(Path.home() / ".claude/settings.json"))
    args = ap.parse_args()
    if known_answers():
        return 1
    return install(Path(args.settings)) if args.install else 0


if __name__ == "__main__":
    sys.exit(main())
