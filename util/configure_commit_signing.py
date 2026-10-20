#!/usr/bin/env python3
"""Install and verify the owner's commit signing for the Juniper tree: terminal and IDEs alike.

Project: juniper-ml
Sub-Project: host tooling (commit signing)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: permanent utility
Related: notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md (§7 design,
         §8 this tool, regressions R-S1..R-S19); notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md
         (D3, D11, tasks B4/B5, gate G-SIGN); tests/test_configure_commit_signing.py

Why this exists
---------------
The Juniper repos carry ``required_signatures``: one unsigned commit makes a branch unmergeable. The
owner commits from a terminal, from the Source Control view of Cursor or VS Code, and from either
IDE's integrated terminal, and signing has to hold for every one of those paths. Both IDEs run the
system git with the user's config. Their git extension adds ``-S`` only when
``git.enableCommitSigning`` is true, and it never passes ``--no-gpg-sign``. So git's config is the
single source of truth, provided it needs neither a TTY nor the shell's PATH (plan §1, S3, S5).

What it installs (``--apply``)
------------------------------
1. ``~/.config/git/juniper-signing.gitconfig``, which holds only yamaguchi's four signing values.
   ``gpg.program`` is the exception: here it is an absolute path to a known GnuPG install (plan R9,
   S2, S3, S4)::

       [user]   signingkey = B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!
       [commit] gpgsign = true
       [tag]    gpgsign = true
       [gpg]    program = /usr/local/bin/gpg

2. One conditional include in the global config::

       [includeIf "gitdir/i:~/Development/python/Juniper/"]
           path = ~/.config/git/juniper-signing.gitconfig

   Both paths are rendered from realpaths. When the target is under ``realpath($HOME)`` the path is
   written ``~/`` plus the relative path; otherwise it is written absolute. git realpaths ``$HOME``
   when it expands ``~``, and it compares the pattern against the physical ``.git`` location. So a
   root spelled through a symlink still matches. ``gitdir/i`` ignores case. A linked worktree's git
   directory is ``<main>/.git/worktrees/<name>``, so a worktree signs wherever it is checked out. A
   repository outside the root gains nothing (plan S1, R2).

   Position in the file is not the guarantee: an owner section with the same pattern, or a later
   global entry, can still win. The guarantee is that ``--check`` judges the deciding value in
   every checkout.

3. Backups made before a file's first change: ``<file>.bak-<YYYY-MM-DD>-pre-commit-signing`` for
   the global config, and the same suffix for an existing include file. The date is local; tests
   pin it with ``COMMIT_SIGNING_TODAY``. A backup is never overwritten.

Each value is written with ``git config``, and only when it differs, so a second run writes nothing.
``--apply`` never edits IDE settings or a repository's ``.git/config``, never runs gpg, and never
reads ``~/.gnupg`` or ``~/.ssh``. Nothing is written when any of these holds; each exits 2:

- an unpinned or malformed key;
- an unsound ``gpg.program``;
- a root that is ``$HOME`` or an ancestor of it;
- an include file under the root or inside a git work tree;
- an existing include file, or its directory, that fails the ``include`` check below. git's
  ``--file`` writer follows a symlink, so a link would send the keys elsewhere.

``--apply --dry-run`` prints the planned writes and the checks as they stand. It writes nothing,
and it exits like ``--check``.

``--remove`` undoes exactly what ``--apply`` adds:

- It unsets the include's ``path`` value with ``--fixed-value``, which leaves an owner include of the
  same pattern alone, and drops the section if that leaves it empty.
- It deletes the include file only if the file is byte for byte what ``--apply`` writes and no other
  global include still points at it. Deleting it in that case would make the other include fail open.
- It removes ``~/.config/git`` if that leaves it empty.
- It refuses to delete an edited include, and it never restores a backup, because that would discard
  later edits.

What it checks (``--check``, the default)
-----------------------------------------
``--check`` only reads. Every git call runs without the variables ``git rev-parse --local-env-vars``
lists, so a hook's ``GIT_DIR`` cannot redirect a read. The same scrub removes an agent session's D11
override (``GIT_CONFIG_COUNT`` with ``commit.gpgsign=false``, which keeps agent commits unsigned by
construction), so the override cannot mask the owner's values. The override is reported on its own
INFO line.

``include``
    Judged when the global config wires the include in, or when the file exists. FAIL when:

    - the file is missing while wired: git then skips it silently, and commits land unsigned;
    - it is a symlink, not a regular file, not the user's, unreadable, or writable by group or
      others;
    - its directory is not the user's, or is writable by group or others;
    - it holds any key beyond the four managed ones, because an include is a place to hide
      ``core.sshCommand`` and the like.
``repo:juniper-<name>``, one check per active checkout present under the root
    FAIL unless all of the following hold:

    - the owner-effective ``commit.gpgsign`` and ``tag.gpgsign`` are true;
    - ``user.signingkey`` is the expected pinned spec;
    - ``gpg.format`` is unset or ``openpgp``;
    - ``user.email`` is set (the IDEs commit with ``user.useConfigOnly=true``);
    - the deciding ``gpg.program`` (or ``gpg.openpgp.program``) is sound.

    A sound program is absolute, executable, and owned by the user or root; neither it nor any
    link on the way to it is writable by group or others; and it resolves to a known GnuPG install:

    - ``gnupg/<version>/bin/gpg`` in Homebrew's Cellar (``/usr/local``, ``/opt/homebrew`` or
      ``/home/linuxbrew/.linuxbrew``);
    - ``/usr/local/MacGPG2/bin/gpg[2]``;
    - ``/usr/bin/gpg[2]``.

    ``--gpg-program`` vouches for one other program.

    The deciding value of a key is the last one git lists, and the message names its scope and
    file. Also FAIL on any of these at local or worktree scope, in the checkout or in any of its
    linked worktrees (where agents work):

    - ``gpg.program``, ``gpg.openpgp.program``, ``include.*``, ``includeIf.*`` or ``core.sshCommand``;
    - a ``core.fsmonitor`` that names a program;
    - a ``core.hooksPath`` other than the checkout's own hooks directory.

    Those scopes outrank the include and are writable by any agent (plan S9).
``ide:<label>``, one check per IDE settings file found
    FAIL when any of the following holds:

    - the file cannot be parsed, even as JSONC;
    - an integrated-terminal environment injects ``GIT_CONFIG_COUNT``, ``GIT_CONFIG_PARAMETERS``,
      ``GIT_CONFIG_GLOBAL``, ``GNUPGHOME`` or ``HOME``. That covers ``terminal.integrated.env.*``
      and the ``env`` of terminal profiles, automation profiles and the chat terminal profile; a
      ``null`` value unsets and is fine;
    - a user-level ``git.path`` names no executable (``git.path`` is machine-scoped, so the IDE
      ignores it in workspace files);
    - ``chat.tools.global.autoApprove`` is on, which approves every agent action before any rule
      is consulted.

    ``git.enableCommitSigning`` is reported, not judged (plan S5).
INFO only
    - the include layout;
    - executable hooks per checkout, with sha256. A hooks path inside a credential directory is
      never listed;
    - hook, monitor, ssh and include settings at global or system scope, which apply to every
      repository;
    - the session's D11 override, and environment variables that redirect git's config files;
    - VS Code's ``chat.tools.terminal.autoApprove``, merged with the legacy
      ``chat.agent.terminal.autoApprove`` and honouring ``enableAutoApprove``. The line says whether
      an agent's plain ``git commit``, or one of the bypass spellings in ``AGENT_PROBES``, runs
      unprompted, and it names any catch-all allow rule. Rules are evaluated as VS Code 1.108.2
      evaluates them:

      - deny entries first;
      - ``/pattern/flags`` keys, with ``g`` dropped;
      - a pattern that matches the empty string becomes never-match, except ``.*`` and the bare anchors;
      - plain keys as ``^<key>\\b``;
      - case-sensitive, except a regex with ``i``.

      VS Code's built-in default rules are not modelled. They allow only read-only git commands, so
      leaving them out can only over-report;
    - the same verdicts for Amp's legacy ``amp.permissions`` (first match wins), naming any
      unconditional ``Bash allow``;
    - for Cursor, a reminder that its run mode is not in settings.json and must be attested;
    - missing checkouts.

Usage
-----
    python3 util/configure_commit_signing.py [--check | --apply [--dry-run] | --remove [--dry-run]]
        [--json] [--root DIR] [--signing-key KEYSPEC] [--gpg-program PATH] [--include-file PATH]
        [--ide-settings FILE]...

``--root DIR``
    The Juniper root. Default: ``$JUNIPER_ROOT``, then ``$HOME/Development/python/Juniper``.
``--signing-key KEYSPEC``
    The pinned key spec, with headless_signing_preflight.bash's grammar: an optional ``0x``, a 16-hex
    key id or a 40- or 64-hex fingerprint, then ``!``. It is normalised (no ``0x``, upper case) before
    it is written or compared. Default: ``B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!``, the 3c card's
    signing subkey.
``--gpg-program PATH``
    The absolute gpg to write and to expect. It must be sound apart from the known-install rule,
    which this flag vouches for. Without it:

    - ``--check`` accepts any sound program;
    - ``--apply`` keeps the include's existing sound value, or else takes the first sound candidate
      among ``/opt/homebrew/bin/gpg``, ``/usr/local/bin/gpg`` and ``/usr/bin/gpg``.

    ``COMMIT_SIGNING_GPG_CANDIDATES`` (colon-separated) replaces that list; the soundness rule still
    applies to every candidate.
``--include-file PATH``
    Default: ``~/.config/git/juniper-signing.gitconfig``. It must not be under the root or inside a
    git work tree.
``--ide-settings FILE``
    Check this IDE settings.json instead of the default user-level locations. Repeatable. The
    defaults are ``User/settings.json`` and ``User/profiles/*/settings.json`` of Code, Cursor,
    Code - Insiders and VSCodium, under both ``~/Library/Application Support`` and
    ``$XDG_CONFIG_HOME`` (``~/.config``), whatever the platform. ``<root>/*.code-workspace``,
    ``<root>/.vscode/settings.json`` and each present checkout's ``.vscode/settings.json`` are always
    checked.

Output
------
One line per check, ``STATUS  ID  detail``, where STATUS is PASS, FAIL, INFO or ERROR. A
``RESULT:`` line follows.

- ``--apply`` and ``--remove`` first print one ``WRITE`` line per change, or ``PLAN`` under
  ``--dry-run``.
- ``--apply`` then prints the rollback command.
- A failing line ends with `` -- fix: <remediation>``.

Exit codes
----------
0  every check passed. For ``--remove``: the layout is removed, or there was nothing to remove.
1  at least one check failed, and every failure is listed. ``--apply --dry-run`` changes nothing, so
   it exits 1 while anything is still failing. ``--remove`` exits 1 when it refuses to delete an
   include file the owner has edited.
2  usage or environment. That covers:

   - a bad argument;
   - git not found;
   - an unusable root;
   - no active checkout under the root;
   - an unusable key spec, gpg program or include path;
   - an ``--ide-settings`` file that does not exist;
   - a git call that failed or timed out (an ERROR line).

   2 wins over 1.

Environment
-----------
``JUNIPER_ROOT``                    the Juniper root (see ``--root``)
``GIT``                             the git program (default ``git``); tests override it
``COMMIT_SIGNING_GPG_CANDIDATES``   the ``--apply`` default gpg candidates (see ``--gpg-program``)
``COMMIT_SIGNING_TODAY``            the backup date, ``YYYY-MM-DD`` (default: today, local)
``COMMIT_SIGNING_GNUPG_CELLARS``    replaces the Homebrew Cellar list of the known-install rule (tests)
``HOME``                            locates ``~``; git honours ``GIT_CONFIG_GLOBAL`` and ``XDG_CONFIG_HOME``, and so does this tool

JSON schema (``--json``)
------------------------
``schema`` is bumped on any incompatible change.

    {
      "schema": 1,
      "mode": "check" | "apply" | "apply-dry-run" | "remove" | "remove-dry-run",
      "root": str, "include_file": str, "global_config": str,
      "expected": {"signing_key": str, "gpg_program": str | null},
      "writes": [{"action": "mkdir" | "create" | "set" | "backup" | "add" | "unset"
                            | "remove-section" | "delete" | "rmdir",
                  "file": str, "key": str | null, "from": str | null, "to": str | null,
                  "applied": bool}],
      "rollback": [str],          # commands that undo this run's writes (--apply only)
      "checks": [{"id": str, "status": "pass" | "fail" | "info" | "error",
                  "message": str, "remediation": str | null}],
      "ok": bool,                 # exit_code == 0
      "exit_code": 0 | 1 | 2,
      "summary": str
    }
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess  # nosec B404 - runs git with list arguments, never a shell
import sys
from dataclasses import dataclass, field
from typing import Any, NamedTuple, NoReturn

ACTIVE_REPOS = ("canopy", "cascor", "cascor-client", "cascor-worker", "data", "data-client", "deploy", "k8s", "ml", "recurrence")
DEFAULT_SIGNING_KEY = "B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!"
DEFAULT_INCLUDE = "~/.config/git/juniper-signing.gitconfig"
DEFAULT_GPG_CANDIDATES = ("/opt/homebrew/bin/gpg", "/usr/local/bin/gpg", "/usr/bin/gpg")
# Where a real GnuPG lives, matched against the realpath (plan S3): Homebrew's Cellar under its three
# prefixes, GPG Suite's MacGPG2, or the distribution's /usr/bin. COMMIT_SIGNING_GNUPG_CELLARS
# (colon-separated Cellar directories) replaces the Cellar list; it exists for the hermetic tests.
DEFAULT_GNUPG_CELLARS = ("/usr/local/Cellar", "/opt/homebrew/Cellar", "/home/linuxbrew/.linuxbrew/Cellar")
OTHER_GNUPG_RE = re.compile(r"/usr/local/MacGPG2/bin/gpg2?|/usr/bin/gpg2?")
IDE_APPS = ("Code", "Cursor", "Code - Insiders", "VSCodium")
PLAN_NOTE = "notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md"
TOOL = "util/configure_commit_signing.py"
SCHEMA_VERSION = 1
TIMEOUT_SECONDS = 30

# The grammar of headless_signing_preflight.bash: a key id or fingerprint, pinned with '!'.
KEYSPEC_RE = re.compile(r"(?:0[xX])?(?P<hex>[0-9A-Fa-f]{16}|[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})!")
SIGNING_KEYS = ("user.signingkey", "commit.gpgsign", "tag.gpgsign", "gpg.program")
# Keys that outrank the include from local or worktree scope and that no agent should plant (plan S9).
LOCAL_FORBIDDEN = ("gpg.program", "gpg.openpgp.program", "core.sshcommand")
LOCAL_FORBIDDEN_PREFIXES = ("include.", "includeif.")
# What an IDE's integrated-terminal env could inject to defeat the git config (plan S5).
DEFEATING_ENV = ("GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_GLOBAL", "GNUPGHOME", "HOME")
CONFIG_REDIRECT_ENV = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM", "XDG_CONFIG_HOME")
OS_KEYS = ("osx", "linux", "windows")
# An agent's plain commit (owner-signed once a card is learned), then the bypass spellings (plan S7).
PLAIN_PROBE = "git commit -m probe"
AGENT_PROBES = (
    "git commit --no-gpg-sign -m probe",
    "git -c commit.gpgsign=false commit -m probe",
    "git --config-env=commit.gpgsign=PROBE commit -m probe",
    "git -c include.path=/tmp/probe commit -m probe",
    "/usr/local/bin/git commit --no-gpg-sign -m probe",
    "GIT commit --no-gpg-sign -m probe",
    "env git commit --no-gpg-sign -m probe",
    "command git commit --no-gpg-sign -m probe",
    'sh -c "git commit --no-gpg-sign -m probe"',
    "xargs git commit --no-gpg-sign -m probe",
    "git config --local gpg.program /tmp/probe",
    "git commit --no-gpg -m probe",
    "git -c alias.c=commit c --no-gpg -m probe",
    "git config gpg.openpgp.program /tmp/probe",
    "git config core.hooksPath /tmp/probe",
    "git -c help.autocorrect=immediate comit --no-gpg -m probe",
    "git config core.fsmonitor /tmp/probe",
)
INCLUDE_HEADER = (
    "# Managed by util/configure_commit_signing.py (juniper-ml): the owner's commit signing for the Juniper tree.\n"
    "# The global git config includes this file through an includeIf on the Juniper root.\n"
    f"# Plan: {PLAN_NOTE}\n"
)

# What `git rev-parse --local-env-vars` prints (git 2.51). The installed git's own list is added at
# run time, as util/git_remote_alias_check.py does, so a variable a later git adds is dropped too.
GIT_LOCAL_ENV_VARS = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
        "GIT_OBJECT_DIRECTORY",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_GRAFT_FILE",
        "GIT_INDEX_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_REPLACE_REF_BASE",
        "GIT_PREFIX",
        "GIT_SHALLOW_FILE",
        "GIT_COMMON_DIR",
    }
)


class UsageError(Exception):
    """A bad command line or an unusable environment (exit 2)."""


class GitError(Exception):
    """A git call failed or timed out (an ERROR line, exit 2)."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


class Entry(NamedTuple):
    """One ``git config --list`` entry. ``value`` is None for a bare key, which git reads as true."""

    scope: str
    origin: str
    key: str
    value: str | None

    @property
    def where(self) -> str:
        return f"{self.scope} {self.origin}"


@dataclass
class Check:
    id: str
    status: str
    message: str
    remediation: str | None = None

    def as_json(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "message": self.message, "remediation": self.remediation}


@dataclass
class Write:
    action: str
    file: str
    key: str | None = None
    old: str | None = None
    new: str | None = None
    applied: bool = False

    def describe(self) -> str:
        if self.action in ("mkdir", "create", "delete", "rmdir"):
            return f"{self.action} {self.file}"
        if self.action == "backup":
            return f"back up {self.old} to {self.file}"
        if self.action == "add":
            return f"{self.file}: add {self.key} = {self.new}"
        if self.action == "unset":
            return f"{self.file}: unset {self.key} = {self.old}"
        if self.action == "remove-section":
            return f"{self.file}: remove the empty section [{self.key}]"
        return f"{self.file}: {self.key} {self.old if self.old is not None else '(unset)'} -> {self.new}"

    def as_json(self) -> dict[str, Any]:
        return {"action": self.action, "file": self.file, "key": self.key, "from": self.old, "to": self.new, "applied": self.applied}


@dataclass
class Report:
    mode: str
    root: str
    include_file: str
    global_config: str
    signing_key: str
    gpg_program: str | None
    writes: list[Write] = field(default_factory=list)
    rollback: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)

    def add(self, check_id: str, status: str, message: str, remediation: str | None = None) -> None:
        self.checks.append(Check(check_id, status, message, remediation))

    def exit_code(self) -> int:
        statuses = {c.status for c in self.checks}
        if "error" in statuses:
            return 2
        if "fail" in statuses:
            return 1
        return 0

    def summary(self) -> str:
        judged = [c for c in self.checks if c.status != "info"]
        bad = [c.id for c in judged if c.status != "pass"]
        if bad:
            text = f"FAILED -- {len(bad)} of {plural(len(judged), 'check')} did not pass: {', '.join(bad)}"
        else:
            text = f"OK -- all {plural(len(judged), 'check')} passed"
        if self.mode.endswith("dry-run"):
            text += f"; DRY-RUN: {plural(len(self.writes), 'planned write')}, nothing written"
        elif self.mode in ("apply", "remove"):
            text += f"; --{self.mode} wrote {plural(sum(w.applied for w in self.writes), 'change')}"
        return text

    def as_json(self) -> dict[str, Any]:
        code = self.exit_code()
        return {
            "schema": SCHEMA_VERSION,
            "mode": self.mode,
            "root": self.root,
            "include_file": self.include_file,
            "global_config": self.global_config,
            "expected": {"signing_key": self.signing_key, "gpg_program": self.gpg_program},
            "writes": [w.as_json() for w in self.writes],
            "rollback": self.rollback,
            "checks": [c.as_json() for c in self.checks],
            "ok": code == 0,
            "exit_code": code,
            "summary": self.summary(),
        }


def plural(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "no output"


def run(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_SECONDS, check=False)  # nosec B603 - list argv, no shell
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"{' '.join(argv)} timed out after {TIMEOUT_SECONDS}s") from exc


def git_environment(git_program: str) -> dict[str, str]:
    """``os.environ`` without git's repository-local variables (see the module docstring)."""
    names = set(GIT_LOCAL_ENV_VARS)
    try:
        listed = run([git_program, "rev-parse", "--local-env-vars"], {k: v for k, v in os.environ.items() if k not in names})
    except GitError:
        listed = None
    if listed is not None and listed.returncode == 0:
        names.update(listed.stdout.split())
    return {k: v for k, v in os.environ.items() if k not in names}


@dataclass
class Git:
    program: str
    env: dict[str, str]

    def __call__(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run([self.program, *args], self.env)

    def checked(self, *args: str) -> subprocess.CompletedProcess[str]:
        proc = self(*args)
        if proc.returncode != 0:
            raise GitError(f"git {' '.join(args)} failed (exit {proc.returncode}): {first_line(proc.stderr)}")
        return proc

    def listing(self, *args: str) -> list[Entry]:
        """Every config entry ``git <args> config --list`` shows, in git's order, includes followed."""
        out = self.checked(*args, "config", "--includes", "--show-scope", "--show-origin", "--list", "-z").stdout
        fields = out.split("\0")
        entries = []
        for i in range(0, len(fields) - 2, 3):
            key, sep, value = fields[i + 2].partition("\n")
            entries.append(Entry(fields[i], fields[i + 1], key, value if sep else None))
        return entries

    def values(self, *args: str) -> list[str]:
        """``git config <args> --get-all``: [] when the key is unset."""
        proc = self("config", *args)
        if proc.returncode == 1:
            return []
        if proc.returncode != 0:
            raise GitError(f"git config {' '.join(args)} failed (exit {proc.returncode}): {first_line(proc.stderr)}")
        return proc.stdout.splitlines()

    def file_keys(self, path: str) -> list[tuple[str, str | None]]:
        """``(key, value)`` pairs of one config file, includes not followed."""
        out = self.checked("config", "--file", path, "--no-includes", "--list", "-z").stdout
        pairs = []
        for item in out.split("\0"):
            if item:
                key, sep, value = item.partition("\n")
                pairs.append((key, value if sep else None))
        return pairs


# ---------------------------------------------------------------------------------------------- paths


def expand(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def real_home() -> str:
    return os.path.realpath(expand("~"))


def render(path: str) -> str:
    """How git should see ``path``: ``~/`` plus the relative path under ``realpath($HOME)``, else the realpath."""
    real, home = os.path.realpath(path), real_home()
    if real == home:
        return "~"
    if real.startswith(home.rstrip(os.sep) + os.sep):
        return "~/" + os.path.relpath(real, home)
    return real


def include_pattern(root: str) -> str:
    return "gitdir/i:" + render(root).rstrip("/") + "/"


def global_config_path() -> str:
    """The file ``git config --global`` writes to, by git's own rule."""
    forced = os.environ.get("GIT_CONFIG_GLOBAL")
    if forced:
        return expand(forced)
    dotfile = expand("~/.gitconfig")
    xdg = os.path.join(os.environ.get("XDG_CONFIG_HOME") or expand("~/.config"), "git", "config")
    if not os.path.exists(dotfile) and os.path.exists(xdg):
        return xdg
    return dotfile


def resolve_include_value(value: str, including_file: str) -> str:
    """Where git looks for an include ``path`` value: ``~`` expanded, relative to the including file."""
    expanded = os.path.expanduser(value)
    if not os.path.isabs(expanded):
        expanded = os.path.join(os.path.dirname(including_file), expanded)
    return os.path.realpath(expanded)


def under(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory.rstrip(os.sep) + os.sep)


def today() -> str:
    pinned = os.environ.get("COMMIT_SIGNING_TODAY")
    if pinned:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pinned):
            raise UsageError(f"COMMIT_SIGNING_TODAY must be YYYY-MM-DD (got {pinned!r})")
        return pinned
    return datetime.date.today().isoformat()


# --------------------------------------------------------------------------------------------- values


def git_bool(value: str | None) -> bool | None:
    """Read a value the way git reads a boolean. A bare key is true; None means not a boolean."""
    if value is None:
        return True
    text = value.strip().lower()
    if text in ("true", "yes", "on"):
        return True
    if text in ("false", "no", "off", ""):
        return False
    if re.fullmatch(r"[+-]?[0-9]+", text):
        return int(text) != 0
    return None


def normalize_keyspec(spec: str) -> str | None:
    match = KEYSPEC_RE.fullmatch(spec.strip())
    return match.group("hex").upper() + "!" if match else None


def writable_by_others(mode: int) -> bool:
    return bool(mode & (stat.S_IWGRP | stat.S_IWOTH))


def program_problem(path: str, vouched: str | None = None) -> str | None:
    """Why ``path`` is not a sound gpg program, or None. Only paths and modes are checked; nothing runs.

    This catches another user's tampering, mode drift and a program planted outside a GnuPG
    install. It cannot stop an agent running as the owner, who owns the Homebrew prefix; the C8
    guard and K12 do that (plan S3, S9).
    """
    if not os.path.isabs(path):
        return f"'{path}' is not an absolute path, so each process finds its own on PATH (an IDE launched from the Dock has its own)"
    if not os.path.exists(path):
        return f"{path} does not exist"
    hop, seen = path, 0
    while os.path.islink(hop) and seen < 40:
        info = os.lstat(hop)
        if info.st_uid not in (os.getuid(), 0):
            return f"the link {hop} is owned by uid {info.st_uid}, neither this user nor root"
        target = os.readlink(hop)
        hop = target if os.path.isabs(target) else os.path.join(os.path.dirname(hop), target)
        seen += 1
    target = os.path.realpath(path)
    if not os.path.isfile(target):
        return f"{path} is not a regular file"
    if not os.access(target, os.X_OK):
        return f"{path} is not executable"
    info = os.stat(target)
    if info.st_uid not in (os.getuid(), 0):
        return f"{target} is owned by uid {info.st_uid}, neither this user nor root"
    if writable_by_others(info.st_mode):
        return f"{target} is writable by group or others (mode {stat.S_IMODE(info.st_mode):o})"
    if vouched is not None and os.path.abspath(path) == os.path.abspath(vouched):
        return None
    if not known_gnupg(target):
        return f"{path} resolves to {target}, which is not a known GnuPG install (Homebrew's Cellar, MacGPG2 or /usr/bin); pass --gpg-program to vouch for it"
    return None


def known_gnupg(target: str) -> bool:
    override = os.environ.get("COMMIT_SIGNING_GNUPG_CELLARS")
    cellars = [c for c in override.split(":") if c] if override is not None else list(DEFAULT_GNUPG_CELLARS)
    for cellar in cellars:
        if re.fullmatch(re.escape(cellar.rstrip("/")) + r"/gnupg/[^/]+/bin/gpg2?", target):
            return True
    return OTHER_GNUPG_RE.fullmatch(target) is not None


def gpg_candidates() -> list[str]:
    override = os.environ.get("COMMIT_SIGNING_GPG_CANDIDATES")
    if override is not None:
        return [p for p in override.split(":") if p]
    return list(DEFAULT_GPG_CANDIDATES)


def file_problem(path: str, what: str) -> str | None:
    """Why the include file (or its directory) is not safe to rely on, or None."""
    if os.path.islink(path):
        return f"the {what} {path} is a symlink"
    info = os.stat(path)
    kind_ok = stat.S_ISDIR(info.st_mode) if what == "directory" else stat.S_ISREG(info.st_mode)
    if not kind_ok:
        return f"the {what} {path} is not a {'directory' if what == 'directory' else 'regular file'}"
    if info.st_uid != os.getuid():
        return f"the {what} {path} is owned by uid {info.st_uid}, not this user"
    if writable_by_others(info.st_mode):
        return f"the {what} {path} is writable by group or others (mode {stat.S_IMODE(info.st_mode):o})"
    if not os.access(path, os.R_OK):
        return f"the {what} {path} is not readable, which makes every git command in the tree fail"
    return None


# ---------------------------------------------------------------------------------------------- JSONC


def strip_jsonc(text: str) -> str:
    """JSONC to JSON: drop ``//`` and ``/* */`` comments and trailing commas, never inside a string."""
    out: list[str] = []
    i, n, in_str = 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            in_str = c != '"'
            i += 1
        elif c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated /* comment")
            out.append(" ")
            i = end + 2
        else:
            out.append(c)
            i += 1
    stripped = "".join(out)
    result: list[str] = []
    i, n, in_str = 0, len(stripped), False
    while i < n:
        c = stripped[i]
        if in_str:
            result.append(c)
            if c == "\\" and i + 1 < n:
                result.append(stripped[i + 1])
                i += 2
                continue
            in_str = c != '"'
        elif c == '"':
            in_str = True
            result.append(c)
        elif c == ",":
            j = i + 1
            while j < n and stripped[j] in " \t\r\n":
                j += 1
            if j < n and stripped[j] not in "}]":
                result.append(c)
        else:
            result.append(c)
        i += 1
    return "".join(result)


def load_jsonc(path: str) -> Any:
    with open(path, encoding="utf-8-sig") as fh:
        return json.loads(strip_jsonc(fh.read()))


# -------------------------------------------------------------------------------- IDE agent approvals

UNKNOWN = "cannot evaluate"
NEVER = re.compile(r"(?!)")
# Commands from unrelated families: an allow rule that approves all of them approves everything.
CATCH_ALL_SENTINELS = ("rm -rf /tmp/probe", "curl https://example.invalid/probe", "git push --force origin probe")


def vscode_rule(key: str) -> re.Pattern[str] | str:
    """A VS Code auto-approve key as a Python regex. VS Code's own parse:

    ``^/(?<pattern>.+)/(?<flags>[dgimsuvy]*)$``, with ``g`` dropped and ``.*`` taken as written.
    A plain key becomes ``^<escaped key>\\b``. Returns UNKNOWN for a JS regex Python cannot read
    (flags ``d``, ``u``, ``v`` or ``y``, or syntax that will not compile), so a verdict never rests
    on a guess.
    """
    match = re.fullmatch(r"/(?P<pattern>.+)/(?P<flags>[dgimsuvy]*)", key, re.DOTALL)
    if match is None:
        return re.compile("^" + re.escape(key) + r"\b")
    flags = match.group("flags").replace("g", "")
    if set(flags) & set("duvy"):
        return UNKNOWN
    py_flags = (re.IGNORECASE if "i" in flags else 0) | (re.MULTILINE if "m" in flags else 0) | (re.DOTALL if "s" in flags else 0)
    body = re.sub(r"\(\?<([A-Za-z_][A-Za-z0-9_]*)>", r"(?P<\1>", match.group("pattern"))
    try:
        pattern = re.compile(body, py_flags)
    except re.error:
        return UNKNOWN
    # VS Code replaces a rule that matches the empty string with one that never matches, except
    # ".*" and the bare anchors. A stray "|" in a deny entry therefore disarms it.
    if body not in (".*", "^", "$") and pattern.search("") is not None:
        return NEVER
    return pattern


def vscode_rules(settings: dict[str, Any]) -> tuple[list[str], list[str]]:
    """``(deny keys, allow keys)``: the current key merged with the legacy one, which wins on a clash."""
    rules: dict[str, Any] = {}
    for key in ("chat.tools.terminal.autoApprove", "chat.agent.terminal.autoApprove"):
        value = settings.get(key)
        if isinstance(value, dict):
            rules.update(value)
    deny, allow = [], []
    for key, value in rules.items():
        approve = value.get("approve") if isinstance(value, dict) else value
        if approve is True:
            allow.append(key)
        elif approve is False:
            deny.append(key)
    return deny, allow


def vscode_catch_all(settings: dict[str, Any]) -> list[str]:
    """Allow keys that approve every command (they approve all of CATCH_ALL_SENTINELS)."""
    _, allow = vscode_rules(settings)
    found = []
    for key in allow:
        pattern = vscode_rule(key)
        if not isinstance(pattern, str) and all(pattern.search(s) for s in CATCH_ALL_SENTINELS):
            found.append(key)
    return found


def vscode_approval(settings: dict[str, Any], command: str) -> tuple[str, str]:
    """``("unprompted" | "needs approval" | UNKNOWN, reason)`` for ``command`` under VS Code's rules.

    Deny (``false``) entries are evaluated before allow entries, so a matching deny wins wherever it
    sits (plan §3, S7).
    """
    if settings.get("chat.tools.terminal.enableAutoApprove") is False:
        return "needs approval", "chat.tools.terminal.enableAutoApprove is false"
    deny, allow = vscode_rules(settings)
    unknown_deny = None
    for key in deny:
        pattern = vscode_rule(key)
        if isinstance(pattern, str):
            unknown_deny = key
        elif pattern.search(command):
            return "needs approval", f"deny rule {key!r}"
    if unknown_deny is not None:
        return UNKNOWN, f"deny rule {unknown_deny!r} is a JavaScript regex this tool cannot evaluate"
    for key in allow:
        pattern = vscode_rule(key)
        if isinstance(pattern, str):
            return UNKNOWN, f"allow rule {key!r} is a JavaScript regex this tool cannot evaluate"
        if pattern.search(command):
            return "unprompted", f"allow rule {key!r}"
    return "needs approval", "no rule matches"


def amp_approval(rules: list[Any], command: str) -> tuple[str, str]:
    """Amp's legacy ``amp.permissions``: the first rule whose tool and ``matches.cmd`` fit decides."""
    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict) or not fnmatch.fnmatchcase("Bash", str(rule.get("tool", ""))):
            continue
        matches = rule.get("matches")
        if isinstance(matches, dict) and "cmd" in matches:
            patterns = matches["cmd"] if isinstance(matches["cmd"], list) else [matches["cmd"]]
            hit = False
            for pattern in patterns:
                text = str(pattern)
                regex = re.fullmatch(r"/(?P<body>.+)/(?P<flags>[a-z]*)", text)
                if regex is not None:
                    try:
                        hit = re.search(regex.group("body"), command, re.IGNORECASE if "i" in regex.group("flags") else 0) is not None
                    except re.error:
                        return UNKNOWN, f"rule {index} has a regex this tool cannot evaluate"
                else:
                    hit = fnmatch.fnmatchcase(command, text)
                if hit:
                    break
            if not hit:
                continue
        elif matches not in (None, {}):
            return UNKNOWN, f"rule {index} matches on something other than cmd"
        action = rule.get("action")
        if action == "allow":
            return "unprompted", f"rule {index}: Bash allow"
        if action in ("ask", "reject"):
            return "needs approval", f"rule {index}: Bash {action}"
        return UNKNOWN, f"rule {index}: action {action!r}"
    return UNKNOWN, "no rule matches, so Amp's bundled defaults decide (not modelled)"


def describe_agents(verdict_of) -> tuple[str, list[str]]:
    plain, _ = verdict_of(PLAIN_PROBE)
    loose = [p for p in AGENT_PROBES if verdict_of(p)[0] == "unprompted"]
    unknown = [p for p in AGENT_PROBES if verdict_of(p)[0] == UNKNOWN]
    parts = [f"a plain '{PLAIN_PROBE}' {'runs unprompted' if plain == 'unprompted' else 'needs approval' if plain == 'needs approval' else 'cannot be evaluated'} ({verdict_of(PLAIN_PROBE)[1]})"]
    if loose:
        parts.append(f"{len(loose)} of {len(AGENT_PROBES)} bypass spellings run unprompted, e.g. '{loose[0]}' ({verdict_of(loose[0])[1]})")
    else:
        parts.append(f"none of {len(AGENT_PROBES)} bypass spellings runs unprompted")
    if unknown:
        parts.append(f"{len(unknown)} cannot be evaluated ({verdict_of(unknown[0])[1]})")
    return "; ".join(parts), loose


# --------------------------------------------------------------------------------------------- checks


def find_checkouts(git: Git, root: str) -> tuple[list[tuple[str, str]], list[str]]:
    present, missing = [], []
    for name in ACTIVE_REPOS:
        repo, checkout = f"juniper-{name}", os.path.join(root, f"juniper-{name}")
        if not os.path.isdir(checkout):
            missing.append(repo)
            continue
        top = git("-C", checkout, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or os.path.realpath(top.stdout.strip()) != os.path.realpath(checkout):
            missing.append(f"{repo} (not its own git checkout)")
            continue
        present.append((repo, checkout))
    return present, missing


def deciding(entries: list[Entry], *keys: str) -> Entry | None:
    """The entry that decides: git applies the last one it lists."""
    hits = [e for e in entries if e.key in keys]
    return hits[-1] if hits else None


def hooks_dir(git: Git, checkout: str) -> str:
    common = git.checked("-C", checkout, "rev-parse", "--git-common-dir").stdout.strip()
    common = common if os.path.isabs(common) else os.path.join(checkout, common)
    return os.path.realpath(os.path.join(common, "hooks"))


def check_repo(git: Git, repo: str, checkout: str, signing_key: str, gpg_program: str | None, report: Report) -> None:
    entries = git.listing("-C", checkout)
    problems: list[str] = []
    fixes: list[str] = []

    def local_fix(entry: Entry) -> None:
        if entry.scope in ("local", "worktree"):
            fixes.append(f"git -C {shlex.quote(checkout)} config --{entry.scope} --unset-all {entry.key}")

    for key in ("commit.gpgsign", "tag.gpgsign"):
        hit = deciding(entries, key)
        if hit is None:
            problems.append(f"{key} is unset")
        elif git_bool(hit.value) is not True:
            problems.append(f"{key}={hit.value} ({hit.where})")
            local_fix(hit)
    key_hit = deciding(entries, "user.signingkey")
    if key_hit is None:
        problems.append("user.signingkey is unset")
    elif normalize_keyspec(key_hit.value or "") != signing_key:
        problems.append(f"user.signingkey={key_hit.value} ({key_hit.where}); expected {signing_key}")
        local_fix(key_hit)
    fmt = deciding(entries, "gpg.format")
    if fmt is not None and (fmt.value or "").strip().lower() != "openpgp":
        problems.append(f"gpg.format={fmt.value} ({fmt.where}); the signing key is an OpenPGP key")
        local_fix(fmt)
    program = deciding(entries, "gpg.program", "gpg.openpgp.program")
    if program is None:
        problems.append("gpg.program is unset, so gpg is whatever each process finds on its PATH")
    else:
        problem = program_problem(program.value or "", gpg_program)
        if problem is not None:
            problems.append(f"{program.key}: {problem} ({program.where})")
        elif gpg_program is not None and os.path.abspath(program.value or "") != os.path.abspath(gpg_program):
            problems.append(f"{program.key}={program.value} ({program.where}); expected {gpg_program}")
    email = deciding(entries, "user.email")
    if email is None or not (email.value or "").strip():
        problems.append("user.email is unset; the IDEs commit with user.useConfigOnly=true, so their commits would fail")
    own_hooks = hooks_dir(git, checkout)
    for entry in planted_entries(entries, checkout, own_hooks, ("local", "worktree")):
        problems.append(f"{entry.key}={entry.value} is set at {entry.where}, which outranks the include and is writable by any agent")
        local_fix(entry)
    # A linked worktree is where an agent works; its own config.worktree outranks the include too.
    for worktree in linked_worktrees(git, checkout):
        for entry in planted_entries(git.listing("-C", worktree), worktree, own_hooks, ("worktree",)):
            problems.append(f"in the worktree {worktree}, {entry.key}={entry.value} is set at {entry.where}")
            fixes.append(f"git -C {shlex.quote(worktree)} config --worktree --unset-all {entry.key}")
    hooks_entry = deciding(entries, "core.hookspath")
    active_hooks = hooks_path(hooks_entry.value, checkout) if hooks_entry is not None else own_hooks
    listable = os.path.isdir(active_hooks) and not any(part.casefold() in (".ssh", ".gnupg") for part in active_hooks.split(os.sep))
    hook_names = sorted(n for n in (os.listdir(active_hooks) if listable else []) if not n.endswith(".sample") and os.path.isfile(os.path.join(active_hooks, n)) and os.access(os.path.join(active_hooks, n), os.X_OK))
    if hook_names:
        digests = []
        for name in hook_names:
            with open(os.path.join(active_hooks, name), "rb") as fh:
                digests.append(f"{name} {hashlib.sha256(fh.read()).hexdigest()[:12]}")
        report.add(f"hooks:{repo}", "info", f"executable hooks in {active_hooks}: " + ", ".join(digests))
    if problems or key_hit is None or program is None:
        report.add(f"repo:{repo}", "fail", "; ".join(problems), "; ".join(dict.fromkeys(fixes)) if fixes else f"python3 {TOOL} --apply")
        return
    origin = key_hit.origin[len("file:"):] if key_hit.origin.startswith("file:") else key_hit.origin
    report.add(f"repo:{repo}", "pass", f"signs with {key_hit.value} through {program.value} (signing key from {origin})")


def hooks_path(value: str | None, base: str) -> str:
    """Where git looks for hooks under ``core.hooksPath = value``; a relative path is relative to the work tree."""
    hooks = os.path.expanduser(value or "")
    return os.path.realpath(hooks if os.path.isabs(hooks) else os.path.join(base, hooks))


def planted_entries(entries: list[Entry], base: str, own_hooks: str, scopes: tuple[str, ...]) -> list[Entry]:
    """Signing-sensitive keys set at ``scopes``: they outrank the include and any agent can write them (plan S9)."""
    found = []
    for entry in entries:
        if entry.scope not in scopes:
            continue
        planted = entry.key in LOCAL_FORBIDDEN or entry.key.startswith(LOCAL_FORBIDDEN_PREFIXES)
        if entry.key == "core.hookspath":
            planted = hooks_path(entry.value, base) != own_hooks
        elif entry.key == "core.fsmonitor":
            planted = git_bool(entry.value) is None
        if planted:
            found.append(entry)
    return found


def linked_worktrees(git: Git, checkout: str) -> list[str]:
    """The checkout's linked worktrees that still exist; the main worktree is the checkout itself."""
    out = git.checked("-C", checkout, "worktree", "list", "--porcelain").stdout
    paths = [line[len("worktree "):] for line in out.splitlines() if line.startswith("worktree ")]
    main = os.path.realpath(checkout)
    return [p for p in paths if os.path.realpath(p) != main and os.path.isdir(p)]


def check_wider_scopes(git: Git, checkout: str, include_file: str, report: Report) -> None:
    """INFO: hook, monitor, ssh or include settings in the global or system config apply to every repository."""
    gcfg = global_config_path()
    notes = []
    for entry in git.listing("-C", checkout):
        if entry.scope not in ("global", "system"):
            continue
        if entry.key in ("include.path",) or (entry.key.startswith("includeif.") and entry.key.endswith(".path")):
            if resolve_include_value(entry.value or "", gcfg) == os.path.realpath(include_file):
                continue
            notes.append(f"{entry.key}={entry.value} ({entry.where})")
        elif entry.key in ("core.hookspath", "core.sshcommand") or (entry.key == "core.fsmonitor" and git_bool(entry.value) is None):
            notes.append(f"{entry.key}={entry.value} ({entry.where})")
    if notes:
        report.add("wider-scopes", "info", "set at global or system scope, so they apply to every repository: " + "; ".join(notes) + " (plan S9)")


def wired_values(git: Git, root: str, include_file: str) -> list[str]:
    """The global config's include ``path`` values under our pattern that point at ``include_file``."""
    gcfg = global_config_path()
    values = git.values("--global", "--get-all", f"includeIf.{include_pattern(root)}.path")
    return [v for v in values if resolve_include_value(v, gcfg) == os.path.realpath(include_file)]


def check_include(git: Git, root: str, include_file: str, report: Report) -> None:
    pattern = include_pattern(root)
    wired = wired_values(git, root, include_file)
    gcfg = global_config_path()
    if not wired and not os.path.lexists(include_file):
        report.add("include", "info", f"{include_file} is absent and {gcfg} has no [includeIf \"{pattern}\"] for it: signing, if any, comes from elsewhere (the repo checks judge it)")
        return
    if not os.path.lexists(include_file):
        report.add("include", "fail", f"{gcfg} includes {include_file}, which is missing: git skips a missing include silently, so commits in the tree land unsigned", f"python3 {TOOL} --apply")
        return
    problems = [p for p in (file_problem(include_file, "include file"), file_problem(os.path.dirname(include_file), "directory")) if p]
    if not problems:
        extra = sorted({k for k, _ in git.file_keys(include_file)} - set(SIGNING_KEYS))
        if extra:
            problems.append(f"{include_file} holds {', '.join(extra)}, beyond the four signing keys it manages")
    if problems:
        report.add("include", "fail", "; ".join(problems), f"inspect the file, then python3 {TOOL} --apply")
        return
    link = f'[includeIf "{pattern}"] in {gcfg} includes it' if wired else f"nothing in {gcfg} includes it yet"
    report.add("include", "pass", f"{include_file} holds only the signing keys; {link}")


def ide_settings_files(ide_settings: list[str] | None, root: str, checkouts: list[tuple[str, str]]) -> list[tuple[str, str, str]]:
    """``(label, path, scope)`` for every IDE settings file to check; scope is user, workspace or folder."""
    files: list[tuple[str, str, str]] = []
    if ide_settings is not None:
        for path in ide_settings:
            parent = os.path.dirname(path)
            label = os.path.basename(os.path.dirname(parent)) if os.path.basename(parent) == "User" else os.path.basename(path)
            files.append((label, path, "user"))
    else:
        bases = [expand("~/Library/Application Support"), os.environ.get("XDG_CONFIG_HOME") or expand("~/.config")]
        for base in dict.fromkeys(bases):
            for app in IDE_APPS:
                user = os.path.join(base, app, "User")
                for path in [os.path.join(user, "settings.json"), *sorted(glob.glob(os.path.join(glob.escape(user), "profiles", "*", "settings.json")))]:
                    if os.path.isfile(path):
                        profile = os.path.basename(os.path.dirname(path)) if "profiles" in path[len(user):] else None
                        files.append((f"{app} profile {profile}" if profile else app, path, "user"))
    for path in sorted(glob.glob(os.path.join(glob.escape(root), "*.code-workspace"))):
        files.append((os.path.basename(path), path, "workspace"))
    for label, folder in [("root/.vscode", root), *[(f"{repo}/.vscode", checkout) for repo, checkout in checkouts]]:
        path = os.path.join(folder, ".vscode", "settings.json")
        if os.path.isfile(path):
            files.append((label, path, "folder"))
    return files


def terminal_envs(settings: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every environment an integrated terminal (or the agent's) is started with, by settings key."""
    found = []
    for os_key in OS_KEYS:
        env = settings.get(f"terminal.integrated.env.{os_key}")
        if isinstance(env, dict):
            found.append((f"terminal.integrated.env.{os_key}", env))
        profiles = settings.get(f"terminal.integrated.profiles.{os_key}")
        if isinstance(profiles, dict):
            for name, profile in profiles.items():
                if isinstance(profile, dict) and isinstance(profile.get("env"), dict):
                    found.append((f"terminal.integrated.profiles.{os_key}.{name}.env", profile["env"]))
        for key in (f"terminal.integrated.automationProfile.{os_key}", f"chat.tools.terminal.terminalProfile.{os_key}"):
            profile = settings.get(key)
            if isinstance(profile, dict) and isinstance(profile.get("env"), dict):
                found.append((f"{key}.env", profile["env"]))
    return found


def check_ide_file(label: str, path: str, scope: str, report: Report) -> None:
    check_id = f"ide:{label}"
    try:
        data = load_jsonc(path)
    except (OSError, ValueError) as exc:
        report.add(check_id, "fail", f"{path} cannot be parsed, even as JSONC ({exc})", "repair the file; an IDE ignores settings it cannot parse")
        return
    settings = data.get("settings", {}) if scope == "workspace" and isinstance(data, dict) else data
    if not isinstance(settings, dict):
        report.add(check_id, "fail", f"{path}: the settings are not a JSON object", "repair the file")
        return
    problems = []
    for key, env in terminal_envs(settings):
        injected = sorted(name for name, value in env.items() if name in DEFEATING_ENV and value is not None)
        if injected:
            problems.append(f"{key} injects {', '.join(injected)} into a terminal, over the signing config")
    git_path = settings.get("git.path")
    paths = [git_path] if isinstance(git_path, str) else [p for p in git_path if isinstance(p, str)] if isinstance(git_path, list) else []
    if scope == "user" and paths and not any(os.path.isfile(expand(p)) and os.access(expand(p), os.X_OK) for p in paths):
        problems.append(f"git.path names no executable ({', '.join(paths)}), so the IDE cannot run git")
    if settings.get("chat.tools.global.autoApprove"):
        problems.append("chat.tools.global.autoApprove is on: every agent action is approved before any rule is consulted (plan S7)")
    if problems:
        report.add(check_id, "fail", f"{path}: " + "; ".join(problems), f"remove those settings (plan {PLAN_NOTE} S5, S7)")
    elif settings.get("git.enableCommitSigning") is True:
        report.add(check_id, "pass", f"{path}: git.enableCommitSigning is true, so this IDE passes -S on every commit, in every repository it opens")
    else:
        report.add(check_id, "pass", f"{path}: git.enableCommitSigning is unset or false, so the IDE's commits follow git's commit.gpgsign")
    if any(k in settings for k in ("chat.tools.terminal.autoApprove", "chat.agent.terminal.autoApprove", "chat.tools.terminal.enableAutoApprove")):
        text, loose = describe_agents(lambda c: vscode_approval(settings, c))
        catch_all = vscode_catch_all(settings) if settings.get("chat.tools.terminal.enableAutoApprove") is not False else []
        if catch_all:
            text += "; catch-all allow rule " + ", ".join(repr(k) for k in catch_all)
        report.add(f"agents:{label}", "info", f"VS Code agent: {text}" + (" -- plan S7 / K13" if loose or catch_all else ""))
    amp = settings.get("amp.permissions")
    if isinstance(amp, list):
        text, loose = describe_agents(lambda c: amp_approval(amp, c))
        catch_all = [str(i) for i, r in enumerate(amp, start=1) if isinstance(r, dict) and r.get("action") == "allow" and fnmatch.fnmatchcase("Bash", str(r.get("tool", ""))) and r.get("matches") in (None, {})]
        if catch_all:
            text += "; catch-all Bash allow rule " + ", ".join(catch_all)
        report.add(f"agents:{label} amp", "info", f"Amp agent: {text}" + (" -- plan S7 / K13" if loose or catch_all else ""))
    if label.startswith("Cursor") and scope == "user":
        report.add(f"agents:{label}", "info", "Cursor keeps its agent run mode outside settings.json; attest Allowlist with the sandbox on, and history-writing git commands off the allowlist (plan S7 / K13)")


def check_environment(report: Report) -> None:
    """INFO for this run's environment: D11's override, and variables that redirect git's config files."""
    hits = []
    count = os.environ.get("GIT_CONFIG_COUNT", "")
    if count.isdigit():
        for i in range(int(count)):
            key, value = os.environ.get(f"GIT_CONFIG_KEY_{i}", ""), os.environ.get(f"GIT_CONFIG_VALUE_{i}", "")
            if key.lower() in ("commit.gpgsign", "tag.gpgsign") and git_bool(value) is False:
                hits.append(f"GIT_CONFIG_KEY_{i}={key}, GIT_CONFIG_VALUE_{i}={value}")
    if re.search(r"commit\.gpgsign'?=\s*'?(false|no|off|0)\b", os.environ.get("GIT_CONFIG_PARAMETERS", ""), re.IGNORECASE):
        hits.append("GIT_CONFIG_PARAMETERS sets commit.gpgsign false")
    if hits:
        report.add("session", "info", "this session cannot sign, by construction (D11): " + "; ".join(hits) + ". The repo checks judge an owner session, which this override does not reach. It does not stop an explicit -S (the C8 guard does) or -c include.path= / --config-env (the K12 rules do)")
    redirects = [f"{name}={os.environ[name]}" for name in CONFIG_REDIRECT_ENV if os.environ.get(name)]
    if redirects:
        report.add("environment", "info", "this run's environment redirects git's config files (" + ", ".join(redirects) + "), so an owner session without them may differ")


# --------------------------------------------------------------------------------------- apply, remove


def resolve_gpg_program(git: Git, include_file: str, explicit: str | None) -> str:
    if explicit is not None:
        return explicit
    if os.path.isfile(include_file):
        current = git.values("--file", include_file, "--get-all", "gpg.program")
        if current and program_problem(current[-1]) is None:
            return current[-1]
    for candidate in gpg_candidates():
        if program_problem(candidate) is None:
            return candidate
    raise UsageError(f"no sound gpg program among {', '.join(gpg_candidates()) or '(none)'}; pass --gpg-program PATH")


def plan_apply(git: Git, root: str, include_file: str, signing_key: str, gpg_program: str) -> list[Write]:
    writes: list[Write] = []
    stamp = today()
    parent = os.path.dirname(include_file)
    exists = os.path.isfile(include_file)
    if not os.path.isdir(parent):
        writes.append(Write("mkdir", parent))
    if not exists:
        writes.append(Write("create", include_file))
    desired = {"user.signingkey": signing_key, "commit.gpgsign": "true", "tag.gpgsign": "true", "gpg.program": gpg_program}
    sets = []
    for key in SIGNING_KEYS:
        current = git.values("--file", include_file, "--get-all", key) if exists else []
        if current != [desired[key]]:
            sets.append(Write("set", include_file, key, current[-1] if current else None, desired[key]))
    backup = f"{include_file}.bak-{stamp}-pre-commit-signing"
    if exists and sets and not os.path.exists(backup):
        writes.append(Write("backup", backup, old=include_file))
    writes.extend(sets)
    if not wired_values(git, root, include_file):
        gcfg = global_config_path()
        backup = f"{gcfg}.bak-{stamp}-pre-commit-signing"
        if os.path.isfile(gcfg) and not os.path.exists(backup):
            writes.append(Write("backup", backup, old=gcfg))
        writes.append(Write("add", gcfg, f"includeIf.{include_pattern(root)}.path", None, render(include_file)))
    return writes


def canonical_include(signing_key: str, gpg_program: str) -> str:
    """The exact text --apply leaves: the header, then git's own layout of the four keys, in order."""
    return INCLUDE_HEADER + f"[user]\n\tsigningkey = {signing_key}\n[commit]\n\tgpgsign = true\n[tag]\n\tgpgsign = true\n[gpg]\n\tprogram = {gpg_program}\n"


def managed_only(git: Git, include_file: str) -> bool:
    """Is the include byte for byte what --apply writes, so that deleting it loses no owner edit?"""
    with open(include_file, encoding="utf-8") as fh:
        text = fh.read()
    values = dict(git.file_keys(include_file))
    key, program = values.get("user.signingkey") or "", values.get("gpg.program") or ""
    return normalize_keyspec(key) is not None and text == canonical_include(key, program)


def plan_remove(git: Git, root: str, include_file: str, report: Report) -> list[Write]:
    writes: list[Write] = []
    gcfg = global_config_path()
    section = f"includeIf.{include_pattern(root)}"
    wired = wired_values(git, root, include_file)
    for value in wired:
        writes.append(Write("unset", gcfg, f"{section}.path", value))
    # git lower-cases the section name but keeps the subsection (the pattern) as written.
    prefix = f"includeif.{include_pattern(root)}."
    global_keys = git.file_keys(gcfg) if os.path.isfile(gcfg) else []
    others = [v for k, v in global_keys if k == prefix + "path" and v not in wired]
    if wired and not others and not [k for k, _ in global_keys if k.startswith(prefix) and k != prefix + "path"]:
        writes.append(Write("remove-section", gcfg, section))
    # Another include (another root, or the owner's own) may still point at the file: deleting it
    # then would make that include fail open (plan R6).
    still = [k for k, v in global_keys if (k == "include.path" or (k.startswith("includeif.") and k.endswith(".path"))) and not (k == prefix + "path" and v in wired) and resolve_include_value(v or "", gcfg) == os.path.realpath(include_file)]
    if os.path.isfile(include_file) and not os.path.islink(include_file):
        if still:
            report.add("remove", "info", f"{include_file} was kept: {', '.join(still)} in {gcfg} still includes it")
        elif managed_only(git, include_file):
            writes.append(Write("delete", include_file))
            parent = os.path.dirname(include_file)
            if sorted(os.listdir(parent)) == [os.path.basename(include_file)]:
                writes.append(Write("rmdir", parent))
        else:
            report.add("remove", "fail", f"{include_file} differs from what --apply writes (edited by hand?); it was left in place", "inspect it and delete it yourself")
    return writes


def perform(git: Git, writes: list[Write]) -> None:
    """Apply ``writes`` in order. For --apply that means the include is complete before anything wires it in."""
    for write in writes:
        if write.action == "mkdir":
            os.makedirs(write.file, mode=0o700, exist_ok=True)
        elif write.action == "create":
            fd = os.open(write.file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(INCLUDE_HEADER)
        elif write.action == "set":
            git.checked("config", "--file", write.file, "--replace-all", write.key or "", write.new or "")
        elif write.action == "backup":
            shutil.copy2(write.old or "", write.file)
        elif write.action == "add":
            git.checked("config", "--global", "--add", write.key or "", write.new or "")
        elif write.action == "unset":
            git.checked("config", "--global", "--fixed-value", "--unset-all", write.key or "", write.old or "")
        elif write.action == "remove-section":
            # git 2.51 drops a section with its last key, so "no such section" means it is gone already.
            proc = git("config", "--global", "--remove-section", write.key or "")
            if proc.returncode != 0 and "no such section" not in proc.stderr:
                raise GitError(f"git config --global --remove-section {write.key} failed (exit {proc.returncode}): {first_line(proc.stderr)}")
        elif write.action == "delete":
            os.unlink(write.file)
        elif write.action == "rmdir":
            os.rmdir(write.file)
        write.applied = True


def rollback_for(writes: list[Write]) -> list[str]:
    if not any(w.applied for w in writes):
        return []
    lines = [f"python3 {TOOL} --remove   # or, by hand, in this order:"]
    for write in reversed(writes):
        if write.applied and write.action == "add":
            lines.append(f"git config --global --fixed-value --unset-all {shlex.quote(write.key or '')} {shlex.quote(write.new or '')}")
        if write.applied and write.action == "create":
            lines.append(f"rm {shlex.quote(write.file)}")
        if write.applied and write.action == "mkdir":
            lines.append(f"rmdir {shlex.quote(write.file)}")
    return lines


# ----------------------------------------------------------------------------------------------- main


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = _Parser(prog="configure_commit_signing.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only verification (the default)")
    mode.add_argument("--apply", action="store_true", help="install the include and its global wiring, then check")
    mode.add_argument("--remove", action="store_true", help="undo exactly what --apply adds, then check")
    parser.add_argument("--dry-run", action="store_true", help="with --apply or --remove: print the planned writes, write nothing")
    parser.add_argument("--json", action="store_true", help="print one JSON object (schema in the docstring)")
    parser.add_argument("--root", help="the Juniper root (default: $JUNIPER_ROOT, then ~/Development/python/Juniper)")
    parser.add_argument("--signing-key", default=DEFAULT_SIGNING_KEY, help=f"the pinned key spec (default {DEFAULT_SIGNING_KEY})")
    parser.add_argument("--gpg-program", help="the absolute gpg to write and expect (vouches for a non-standard install)")
    parser.add_argument("--include-file", default=DEFAULT_INCLUDE, help=f"the include file (default {DEFAULT_INCLUDE})")
    parser.add_argument("--ide-settings", action="append", metavar="FILE", help="an IDE settings.json to check instead of the defaults (repeatable)")
    args = parser.parse_args(argv)
    if args.dry_run and not (args.apply or args.remove):
        raise UsageError("--dry-run needs --apply or --remove")
    return args


def validate_paths(git: Git, root: str, include_file: str) -> None:
    if not os.path.isdir(root):
        raise UsageError(f"the Juniper root {root} is not a directory")
    if any(c in render(root) for c in "*?[]\\"):
        raise UsageError(f"the Juniper root {root} contains a glob character, which an includeIf pattern would misread")
    if under(real_home(), os.path.realpath(root)):
        raise UsageError(f"the Juniper root {root} is $HOME or an ancestor of it, so the include would sign every repository there")
    real_include = os.path.realpath(include_file)
    if under(real_include, os.path.realpath(root)):
        raise UsageError(f"the include file {include_file} is under the Juniper root; a branch could then rewrite the owner's signing config")
    probe = os.path.dirname(real_include)
    while not os.path.isdir(probe) and os.path.dirname(probe) != probe:
        probe = os.path.dirname(probe)
    inside = git("-C", probe, "rev-parse", "--is-inside-work-tree")
    if inside.returncode == 0 and inside.stdout.strip() == "true":
        raise UsageError(f"the include file {include_file} is inside a git work tree ({probe}); keep it outside every work tree (plan S1)")


def print_text(report: Report) -> None:
    print("commit signing: the owner's signing for the Juniper tree, terminal and IDEs. No credential is read or used.")
    print(f"root           {report.root}")
    print(f"include file   {report.include_file}")
    print(f"global config  {report.global_config}")
    print(f"expected key   {report.signing_key}")
    print(f"gpg program    {report.gpg_program or '(any sound program in a known GnuPG install)'}")
    print()
    for write in report.writes:
        print(f"{'PLAN ' if report.mode.endswith('dry-run') else 'WRITE'}  {write.describe()}")
    if report.rollback:
        print("rollback:")
        for line in report.rollback:
            print(f"  {line}")
    if report.writes or report.rollback:
        print()
    for check in report.checks:
        line = f"{check.status.upper():<5}  {check.id:<30}  {check.message}"
        if check.status in ("fail", "error") and check.remediation:
            line += f" -- fix: {check.remediation}"
        print(line)
    print()
    print(f"RESULT: {report.summary()}")


def run_checks(git: Git, root: str, include_file: str, signing_key: str, gpg_program: str | None, ide_settings: list[str] | None, checkouts: list[tuple[str, str]], missing: list[str], report: Report) -> None:
    try:
        check_include(git, root, include_file, report)
    except GitError as exc:
        report.add("include", "error", str(exc))
    for repo, checkout in checkouts:
        try:
            check_repo(git, repo, checkout, signing_key, gpg_program, report)
        except GitError as exc:
            report.add(f"repo:{repo}", "error", str(exc))
    try:
        check_wider_scopes(git, checkouts[0][1], include_file, report)
    except GitError as exc:
        report.add("wider-scopes", "error", str(exc))
    for name in missing:
        report.add("missing", "info", f"{name}: no checkout under {root}, nothing to check")
    found = ide_settings_files(ide_settings, root, checkouts)
    for label, path, scope in found:
        check_ide_file(label, path, scope, report)
    if not found:
        report.add("ide", "info", "no IDE settings file found")
    check_environment(report)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        git_program = shutil.which(os.environ.get("GIT", "git"))
        if git_program is None:
            raise UsageError(f"git not found (GIT={os.environ.get('GIT', 'git')})")
        git = Git(git_program, git_environment(git_program))
        root = expand(args.root or os.environ.get("JUNIPER_ROOT") or "~/Development/python/Juniper")
        include_file = expand(args.include_file)
        validate_paths(git, root, include_file)
        signing_key = normalize_keyspec(args.signing_key)
        if signing_key is None:
            raise UsageError(f"--signing-key must be an optional 0x, a 16-hex key id or a 40- or 64-hex fingerprint, then '!' (got {args.signing_key!r})")
        gpg_program = args.gpg_program
        if gpg_program is not None:
            problem = program_problem(gpg_program, gpg_program)
            if problem is not None:
                raise UsageError(f"--gpg-program: {problem}")
        for path in args.ide_settings or []:
            if not os.path.isfile(path):
                raise UsageError(f"--ide-settings: {path} does not exist")
        checkouts, missing = find_checkouts(git, root)
        if not checkouts:
            raise UsageError(f"no active Juniper checkout under {root}")
        mode = "apply" if args.apply else "remove" if args.remove else "check"
        if args.dry_run:
            mode += "-dry-run"
        report = Report(mode, root, include_file, global_config_path(), signing_key, gpg_program)
        if args.apply:
            # git's --file writer follows a symlink, so an unsafe include or directory is refused up front.
            for path, what in ((include_file, "include file"), (os.path.dirname(include_file), "directory")):
                if os.path.lexists(path):
                    problem = file_problem(path, what)
                    if problem is not None:
                        raise UsageError(f"--apply will not write through it: {problem}")
            report.gpg_program = resolve_gpg_program(git, include_file, gpg_program)
            report.writes = plan_apply(git, root, include_file, signing_key, report.gpg_program)
        elif args.remove:
            report.writes = plan_remove(git, root, include_file, report)
        if (args.apply or args.remove) and not args.dry_run:
            try:
                perform(git, report.writes)
            except (GitError, OSError) as exc:
                report.add(mode, "error", f"stopped after {plural(sum(w.applied for w in report.writes), 'write')}: {exc}", "fix the cause, then re-run; finished writes are kept and are not repeated")
            if args.apply:
                report.rollback = rollback_for(report.writes)
        if not args.remove:
            run_checks(git, root, include_file, signing_key, report.gpg_program, args.ide_settings, checkouts, missing, report)
        else:
            check_include(git, root, include_file, report)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Run with --help for usage.", file=sys.stderr)
        return 2
    except GitError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report.as_json(), indent=2))
    else:
        print_text(report)
    return report.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
