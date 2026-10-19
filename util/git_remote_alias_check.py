#!/usr/bin/env python3
"""Check that every Juniper checkout reaches GitHub through its own per-repo ssh alias (gate G-ALIAS).

Project: juniper-ml
Sub-Project: host tooling (turing bring-up)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: permanent utility
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G2, gate
         G-ALIAS, regressions R-G2a/b/c, §4.1; task G6 runs it from a pre-push hook);
         tests/test_git_remote_alias_check.py

Why this exists
---------------
Each Juniper repo has its own deploy key, reached through a ``Host github_juniper-<repo>`` block with
``IdentitiesOnly yes``, so ssh offers exactly one key: that repo's. On turing, git auth failed on
exactly the two checkouts whose origin skipped the alias (plan §4.1). juniper-k8s had
``git@github.com:pcalnon/juniper-k8s.git`` (R-G2a) and juniper-recurrence had
``https://github.com/pcalnon/juniper-recurrence.git`` (R-G2b). An alias with no ``Host`` block, or
one with ``AddKeysToAgent yes``, is the same failure one layer down (R-G2c). ``AddKeysToAgent yes``
hands a passphrase-less deploy key to gpg-agent and its pinentry.

The checks, per active repo
---------------------------
The 10 active repos are canopy, cascor, cascor-client, cascor-worker, data, data-client, deploy,
k8s, ml and recurrence. juniper-legacy is an archive, not a git checkout, and is never checked.

``origin``
    ``git -C <root>/juniper-<repo> config --get remote.origin.url`` must match
    ``^git@github_juniper-<repo>:pcalnon/juniper-<repo>\\.git$``. That reads the persisted value;
    ``git remote get-url`` expands insteadOf and could show alias form over a bypass URL. Every
    ``remote.origin.pushurl`` must match too, or pushes bypass the alias. A missing checkout, a
    directory that is not its own git checkout, and a missing origin are each a named failure.
``alias``
    ``ssh -G github_juniper-<repo>`` evaluates the client configuration, Include and Match blocks
    included, and opens no connection. It must report:

    - ``hostname github.com``. ``ssh.github.com``, GitHub's port-443 endpoint, is also accepted,
      because util/juniper_clone.bash accepts it;
    - exactly one ``identityfile``, equal to ``~/.ssh/id_ed25519_github_juniper-<repo>`` once
      expanded;
    - ``identitiesonly yes``;
    - ``addkeystoagent false``.

    A missing Host block shows up as ``hostname`` equal to the alias itself. ``AddKeysToAgent yes``
    shows up as ``addkeystoagent true``, and any value but ``false`` fails.
``key``
    ``~/.ssh/id_ed25519_github_juniper-<repo>`` exists, is a regular file and is exactly mode 600.
    The check uses ``os.stat`` only, which follows a symlink. The script never opens a key.

Usage
-----
    python3 util/git_remote_alias_check.py [--root DIR] [--repo NAME]... [--json]
        [--check | --fix [--dry-run]] [--if-configured [--ssh-config FILE]]

``--root DIR``
    The Juniper root. Without it the script uses ``$JUNIPER_ROOT``, then
    ``$HOME/Development/python/Juniper``.
``--repo NAME``
    Check only this repo. Repeatable; ``k8s`` and ``juniper-k8s`` both work. An unknown name exits 2.
``--json``
    Print one JSON object on stdout instead of the report (schema below).
``--check``
    Check only. This is the default; the flag exists so a hook can spell it out.
``--fix``
    Rewrite a non-alias origin that names the same GitHub repository with
    ``git -C <checkout> remote set-url origin <alias URL>``, then re-read it.
``--dry-run``
    With ``--fix``: print the planned rewrites and change nothing.
``--if-configured``
    Exit 0 with ``skipped: no github_juniper-* Host alias in <path>`` when the ssh config file has no
    ``Host github_juniper-...`` line or does not exist.
``--ssh-config FILE``
    The file ``--if-configured`` looks in. Default: ``~/.ssh/config``.

``--fix`` changes nothing else. It never edits the ssh config, never chmods and never creates a key.
For those failures the report carries the owner's remediation instead:

- ``bash util/juniper_repo_ssh_setup.bash <repo>`` for a missing Host block or key;
- ``chmod 600 <key>`` for a bad mode;
- the ``AddKeysToAgent no`` edit.

It also refuses an origin that names a different repository (another owner, another repo, a
non-GitHub host): it rewrites the transport, never the destination. It does not add a missing origin.

``--if-configured`` exists for task G6's pre-push hook, so CI and hosts without the aliases pass:
``python3 util/git_remote_alias_check.py --check --if-configured``. It is the only place the script
reads the ssh config's text, and it reads it only to match that line. The match is line-based:
comments are skipped, a token that starts with ``#`` ends the line as it does in ssh_config, and
``Include`` is not followed. A host that keeps its blocks in an included file passes
``--ssh-config FILE``. The ``alias`` check always asks ``ssh -G``, which is what git's ssh uses.

A hook inherits git's repository variables. From a linked worktree, git exports
``GIT_DIR=<main>/.git/worktrees/<wt>`` to pre-push; ``git -C <other checkout>`` would then read the
pushing repository's config, and ``--fix`` would rewrite it. So every git call runs without the
variables ``git rev-parse --local-env-vars`` lists, as git itself does before it enters a submodule.

Output
------
One line per check per repo, ``STATUS  juniper-<repo>  CHECK  detail``, then a summary line.
STATUS is one of:

- PASS;
- FAIL;
- FIXED, rewritten by ``--fix`` and re-read;
- ERROR, the check could not be evaluated.

A failing line ends with `` -- fix: <remediation>``, or under ``--dry-run`` with
`` -- DRY-RUN: would run: <command>``. The userinfo of an http(s) URL prints as ``***``, because it
can hold a token.

Exit codes
----------
0  every check passed (FIXED counts as passed), or ``--if-configured`` found no alias to check.
1  at least one check failed; every failure is listed. ``--fix --dry-run`` changes nothing, so it
   exits 1 while anything is still failing.
2  usage or environment. That covers a bad argument or unknown repo; git or ssh not found; a root
   that is not a directory; an ssh config that cannot be read (with ``--if-configured``); and
   ``ssh -G`` failing to evaluate an alias (an ERROR line). 2 wins over 1. Usage and startup errors
   print to stderr only.

Environment
-----------
``JUNIPER_ROOT``  parent directory of the checkouts (see ``--root``)
``GIT``, ``SSH``  the git and ssh programs (default ``git``, ``ssh``); tests override them
``HOME``          locates ``~/.ssh``

JSON schema (``--json``)
------------------------
``schema`` is bumped on any incompatible change. ``repos`` is in canonical order and is ``[]`` when
the run is skipped.

    {
      "schema": 1,
      "mode": "check" | "fix" | "fix-dry-run",
      "root": str,                # absolute Juniper root
      "ssh_config": str,          # absolute path that --if-configured reads
      "skipped": bool,            # true only for the --if-configured skip
      "skip_reason": str | null,  # "no github_juniper-* Host alias in <path>"
      "ok": bool,                 # exit_code == 0
      "exit_code": 0 | 1 | 2,
      "summary": str,             # the human summary line
      "failures": [{"repo": str, "check": "origin" | "alias" | "key", "status": "fail" | "error"}],
      "repos": [{"repo": "juniper-<repo>", "checkout": str, "alias": "github_juniper-<repo>",
                 "ok": bool, "checks": {"origin": ORIGIN, "alias": ALIAS, "key": KEY}}]
    }

Every check object has these fields:

    "status": "pass" | "fail" | "fixed" | "error"
    "ok": bool                    # status is pass or fixed
    "message": str                # the human line's detail
    "remediation": str | null     # the owner's next step when the check does not pass

Each check adds its own fields:

    ORIGIN  "expected_url": str, "url": str | null (persisted remote.origin.url),
            "pushurls": [str],
            "fix": null | {"from": str, "to": str, "applied": bool, "error": str | null}
    ALIAS   "hostname": str | null, "identityfile": [str] (as ssh -G prints them),
            "identitiesonly": str | null, "addkeystoagent": str | null,
            "expected_identityfile": str
    KEY     "path": str, "exists": bool, "regular_file": bool | null,
            "mode": str | null (octal, e.g. "600")
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, NoReturn

OWNER = "pcalnon"
ACTIVE_REPOS = ("canopy", "cascor", "cascor-client", "cascor-worker", "data", "data-client", "deploy", "k8s", "ml", "recurrence")
ARCHIVED_REPOS = ("legacy",)
GITHUB_HOSTNAMES = ("github.com", "ssh.github.com")
SETUP_SCRIPT = "util/juniper_repo_ssh_setup.bash"
CLONE_SCRIPT = "util/juniper_clone.bash"
SCHEMA_VERSION = 1
TIMEOUT_SECONDS = 30
STATUS_LABEL = {status: status.upper() for status in ("pass", "fail", "fixed", "error")}

# What `git rev-parse --local-env-vars` prints (git 2.51). The installed git's own list is added at
# run time, so a variable a later git adds is dropped too.
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

# A Host line: the keyword, then whitespace or one "=", then the patterns.
_HOST_LINE_RE = re.compile(r"host(?:\s*=\s*|\s+)(?P<patterns>.*)", re.IGNORECASE)
# Remote URL shapes, for the same-repository test that guards --fix.
_URL_RE = re.compile(r"(?:ssh|git|https?)://(?:[^@/]*@)?(?P<host>[^/:@]+)(?::\d*)?/(?P<path>.+)", re.IGNORECASE)
_SCP_RE = re.compile(r"(?:[^@/:]+@)?(?P<host>[^/:@]+):(?P<path>[^/].*)")
_HTTP_USERINFO_RE = re.compile(r"^(?P<scheme>https?://)[^@/]*@", re.IGNORECASE)


class UsageError(Exception):
    """A bad command line (exit 2)."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


@dataclass
class Check:
    """One check's verdict; ``data`` holds the check-specific JSON fields."""

    name: str
    data: dict[str, Any]
    status: str = "pass"
    message: str = ""
    remediation: str | None = None
    plan: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in ("pass", "fixed")

    def fail(self, message: str, remediation: str | None) -> Check:
        self.status, self.message, self.remediation = "fail", message, remediation
        return self

    def error(self, message: str, remediation: str | None = None) -> Check:
        self.status, self.message, self.remediation = "error", message, remediation
        return self

    def as_json(self) -> dict[str, Any]:
        return {"status": self.status, "ok": self.ok, "message": self.message, "remediation": self.remediation, **self.data}


@dataclass
class RepoResult:
    name: str
    checkout: str
    checks: list[Check]

    @property
    def repo(self) -> str:
        return f"juniper-{self.name}"

    def as_json(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "checkout": self.checkout,
            "alias": f"github_juniper-{self.name}",
            "ok": all(c.ok for c in self.checks),
            "checks": {c.name: c.as_json() for c in self.checks},
        }


@dataclass
class Report:
    mode: str
    root: str
    ssh_config: str
    skip_reason: str | None = None
    repos: list[RepoResult] = field(default_factory=list)

    def all_checks(self) -> list[tuple[RepoResult, Check]]:
        return [(r, c) for r in self.repos for c in r.checks]

    def exit_code(self) -> int:
        statuses = {c.status for _, c in self.all_checks()}
        if "error" in statuses:
            return 2
        if "fail" in statuses:
            return 1
        return 0

    def summary(self) -> str:
        if self.skip_reason is not None:
            return f"skipped: {self.skip_reason}"
        checks = self.all_checks()
        text = f"summary: {sum(c.ok for _, c in checks)} of {len(checks)} checks passed"
        failed = [f"{r.repo} {c.name}" for r, c in checks if c.status == "fail"]
        errors = [f"{r.repo} {c.name}" for r, c in checks if c.status == "error"]
        if failed:
            text += f"; {len(failed)} failed: {', '.join(failed)}"
        if errors:
            text += f"; {len(errors)} could not be evaluated: {', '.join(errors)}"
        fixed = sum(c.status == "fixed" for _, c in checks)
        if fixed:
            text += f"; --fix rewrote {plural(fixed, 'origin')}"
        planned = sum(c.plan is not None for _, c in checks)
        if planned:
            text += f"; DRY-RUN: would rewrite {plural(planned, 'origin')}, nothing written"
        return text

    def as_json(self) -> dict[str, Any]:
        code = self.exit_code()
        return {
            "schema": SCHEMA_VERSION,
            "mode": self.mode,
            "root": self.root,
            "ssh_config": self.ssh_config,
            "skipped": self.skip_reason is not None,
            "skip_reason": self.skip_reason,
            "ok": code == 0,
            "exit_code": code,
            "summary": self.summary(),
            "failures": [{"repo": r.repo, "check": c.name, "status": c.status} for r, c in self.all_checks() if not c.ok],
            "repos": [r.as_json() for r in self.repos],
        }


def plural(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "no output"


def absolute(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def alias_url(name: str) -> str:
    return f"git@github_juniper-{name}:{OWNER}/juniper-{name}.git"


def is_alias_origin(url: str, name: str) -> bool:
    """The plan's ``^git@github_juniper-<repo>:pcalnon/juniper-<repo>\\.git$``, over the whole value."""
    n = re.escape(name)
    return re.fullmatch(rf"git@github_juniper-{n}:{OWNER}/juniper-{n}\.git", url) is not None


def same_repository(url: str, name: str) -> bool:
    """Does ``url`` name ``pcalnon/juniper-<name>`` on GitHub, in any transport form?"""
    match = _URL_RE.fullmatch(url) or _SCP_RE.fullmatch(url)
    if match is None:
        return False
    host = match.group("host").lower()
    if host not in (*GITHUB_HOSTNAMES, "www.github.com") and not host.startswith("github_juniper-"):
        return False
    path = match.group("path").strip("/").removesuffix(".git")
    return path.lower() == f"{OWNER}/juniper-{name}"


def redact(url: str) -> str:
    """Print an http(s) URL's userinfo as ``***``: an https origin can carry a token."""
    return _HTTP_USERINFO_RE.sub(r"\g<scheme>***@", url, count=1)


def expected_key(home: str, name: str) -> str:
    return os.path.normpath(os.path.join(home, ".ssh", f"id_ed25519_github_juniper-{name}"))


def run(argv: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_SECONDS, check=False)


def _without(names: set[str] | frozenset[str]) -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in names}


def git_environment(git_program: str) -> dict[str, str]:
    """``os.environ`` without git's repository-local variables (see the module docstring)."""
    names = set(GIT_LOCAL_ENV_VARS)
    try:
        listed = run([git_program, "rev-parse", "--local-env-vars"], env=_without(names))
    except subprocess.TimeoutExpired:
        listed = None
    if listed is not None and listed.returncode == 0:
        names.update(listed.stdout.split())
    return _without(names)


@dataclass
class Git:
    program: str
    env: dict[str, str]

    def __call__(self, checkout: str, *args: str) -> subprocess.CompletedProcess[str]:
        return run([self.program, "-C", checkout, *args], env=self.env)

    def origin_url(self, checkout: str) -> subprocess.CompletedProcess[str]:
        # The persisted value. `git remote get-url` expands insteadOf and could show alias form over a bypass URL.
        return self(checkout, "config", "--get", "remote.origin.url")


def check_origin(git: Git, checkout: str, name: str, *, fix: bool, dry_run: bool) -> Check:
    expected = alias_url(name)
    check = Check("origin", {"expected_url": expected, "url": None, "pushurls": [], "fix": None})
    if not os.path.isdir(checkout):
        if os.path.lexists(checkout):
            return check.fail(f"no checkout: {checkout} is not a directory", f"move {shlex.quote(checkout)} aside, then: bash {CLONE_SCRIPT} {name}")
        return check.fail(f"no checkout: {checkout} does not exist", f"bash {CLONE_SCRIPT} {name}")
    try:
        return _check_origin(git, check, checkout, name, expected, fix=fix, dry_run=dry_run)
    except subprocess.TimeoutExpired as exc:
        return check.error(f"git timed out after {TIMEOUT_SECONDS}s: {shlex.join(str(a) for a in exc.cmd)}")


def _check_origin(git: Git, check: Check, checkout: str, name: str, expected: str, *, fix: bool, dry_run: bool) -> Check:
    move_aside = f"move {shlex.quote(checkout)} aside, then: bash {CLONE_SCRIPT} {name}"
    top = git(checkout, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return check.fail(f"{checkout} is not a git checkout ({first_line(top.stderr)})", move_aside)
    toplevel = top.stdout.strip()
    if os.path.realpath(toplevel) != os.path.realpath(checkout):
        return check.fail(f"{checkout} is not a git checkout; it is a directory inside {toplevel}", move_aside)

    got = git.origin_url(checkout)
    if got.returncode == 1:
        return check.fail("no origin remote (remote.origin.url is unset)", f"git -C {shlex.quote(checkout)} remote add origin {expected}")
    if got.returncode != 0:
        return check.fail(f"cannot read remote.origin.url: {first_line(got.stderr)}", None)
    url = got.stdout.strip()
    pushed = git(checkout, "config", "--get-all", "remote.origin.pushurl")
    if pushed.returncode not in (0, 1):
        return check.fail(f"cannot read remote.origin.pushurl: {first_line(pushed.stderr)}", None)
    pushurls = pushed.stdout.split() if pushed.returncode == 0 else []
    check.data.update(url=redact(url), pushurls=[redact(p) for p in pushurls])

    rewritten = False
    if not is_alias_origin(url, name):
        set_url = f"git -C {shlex.quote(checkout)} remote set-url origin {expected}"
        bypass = f"origin {redact(url)!r} bypasses the alias; want {expected!r}"
        if not same_repository(url, name):
            refused = "; --fix refused: it rewrites the transport, never the repository" if fix else ""
            return check.fail(f"origin {redact(url)!r} is not {expected!r} and names another repository{refused}", f"confirm the repository by hand, then: {set_url}")
        if not fix:
            return check.fail(bypass, f"{set_url} (or rerun with --fix)")
        check.data["fix"] = {"from": redact(url), "to": expected, "applied": False, "error": None}
        if dry_run:
            check.plan = set_url
            return check.fail(bypass, set_url)
        proc = git(checkout, "remote", "set-url", "origin", expected)
        if proc.returncode != 0:
            check.data["fix"]["error"] = first_line(proc.stderr)
            return check.fail(f"{bypass}; --fix: git remote set-url failed (exit {proc.returncode}): {first_line(proc.stderr)}", set_url)
        reread = git.origin_url(checkout)
        after = reread.stdout.strip() if reread.returncode == 0 else ""
        if after != expected:
            return check.fail(f"{bypass}; --fix ran git remote set-url, but the persisted origin is {redact(after) or '<unset>'!r}", set_url)
        check.data["fix"]["applied"] = True
        check.data["url"] = after
        rewritten = True

    bad_push = [p for p in pushurls if not is_alias_origin(p, name)]
    if bad_push:
        return check.fail(f"pushurl {redact(bad_push[0])!r} bypasses the alias for pushes", f"git -C {shlex.quote(checkout)} config --unset-all remote.origin.pushurl")
    if rewritten:
        check.status = "fixed"
        check.message = f"rewrote {check.data['fix']['from']!r} -> {expected!r} (persisted value re-read)"
    else:
        check.message = expected
    return check


def parse_ssh_g(text: str) -> dict[str, list[str]]:
    """``ssh -G`` prints one ``keyword value`` per line; keywords such as identityfile repeat."""
    parsed: dict[str, list[str]] = {}
    for line in text.splitlines():
        parts = line.strip().split(None, 1)
        if parts:
            parsed.setdefault(parts[0].lower(), []).append(parts[1] if len(parts) > 1 else "")
    return parsed


def check_alias(ssh: str, name: str, home: str, ssh_config: str) -> Check:
    alias = f"github_juniper-{name}"
    want_key = expected_key(home, name)
    check = Check("alias", {"hostname": None, "identityfile": [], "identitiesonly": None, "addkeystoagent": None, "expected_identityfile": want_key})
    try:
        proc = run([ssh, "-G", alias])
    except subprocess.TimeoutExpired:
        return check.error(f"'ssh -G {alias}' timed out after {TIMEOUT_SECONDS}s")
    if proc.returncode != 0:
        return check.error(f"'ssh -G {alias}' could not evaluate the ssh configuration (exit {proc.returncode}): {first_line(proc.stderr)}", "fix the ssh client configuration, then rerun")
    resolved = parse_ssh_g(proc.stdout)
    hostname = (resolved.get("hostname") or [None])[0]
    identityfiles = resolved.get("identityfile", [])
    identitiesonly = (resolved.get("identitiesonly") or [None])[0]
    addkeystoagent = (resolved.get("addkeystoagent") or [None])[0]
    check.data.update(hostname=hostname, identityfile=identityfiles, identitiesonly=identitiesonly, addkeystoagent=addkeystoagent)
    if hostname is None:
        return check.error(f"'ssh -G {alias}' reported no hostname")
    if hostname.lower() == alias:
        return check.fail(f"no Host block for {alias} (hostname resolves to the alias itself)", f"bash {SETUP_SCRIPT} {name}")

    problems: list[str] = []
    edits: list[str] = []
    if hostname.lower() not in GITHUB_HOSTNAMES:
        problems.append(f"hostname {hostname}, want github.com")
        edits.append("HostName github.com")
    offered = [os.path.normpath(os.path.expanduser(p.strip('"'))) for p in identityfiles]
    if offered != [want_key]:
        problems.append(f"identityfile {', '.join(identityfiles) or '<none>'}, want only ~/.ssh/id_ed25519_{alias}")
        edits.append(f"IdentityFile ~/.ssh/id_ed25519_{alias} (and no other)")
    if identitiesonly != "yes":
        problems.append(f"identitiesonly {identitiesonly or '<unset>'}, want yes")
        edits.append("IdentitiesOnly yes")
    if addkeystoagent != "false":
        problems.append(f"addkeystoagent {addkeystoagent or '<unset>'}, want false")
        edits.append("AddKeysToAgent no")
    if problems:
        return check.fail("; ".join(problems), f"in the Host {alias} block of {ssh_config}, set {'; '.join(edits)}")
    check.message = f"{alias} -> {hostname}; identityfile {identityfiles[0]}; identitiesonly yes; addkeystoagent false"
    return check


def check_key(home: str, name: str) -> Check:
    path = expected_key(home, name)
    check = Check("key", {"path": path, "exists": False, "regular_file": None, "mode": None})
    try:
        info = os.stat(path)
    except FileNotFoundError:
        return check.fail(f"{path} is missing", f"bash {SETUP_SCRIPT} {name}")
    except OSError as exc:
        return check.fail(f"cannot stat {path}: {exc.strerror or exc}", None)
    mode = stat.S_IMODE(info.st_mode)
    regular = stat.S_ISREG(info.st_mode)
    check.data.update(exists=True, regular_file=regular, mode=f"{mode:03o}")
    if not regular:
        return check.fail(f"{path} is not a regular file", f"move {shlex.quote(path)} aside, then: bash {SETUP_SCRIPT} {name}")
    if mode != 0o600:
        return check.fail(f"{path} is mode {mode:03o}, want 600", f"chmod 600 {shlex.quote(path)}")
    check.message = f"{path} (regular file, mode 600)"
    return check


def ssh_config_has_alias(path: str) -> bool:
    """True when ``path`` has a non-comment ``Host`` line with a ``github_juniper-*`` pattern.

    This is the only place the script reads the ssh config's text, and only for this match.
    """
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            # A line that starts with "#" is a comment: it cannot match, because the keyword comes first.
            match = _HOST_LINE_RE.fullmatch(raw.strip())
            if match is None:
                continue
            for pattern in match.group("patterns").split():
                if pattern.startswith("#"):
                    break  # as in ssh_config, a token that starts with "#" begins a trailing comment
                if pattern.strip('"').lower().startswith("github_juniper-"):
                    return True
    return False


def select_repos(values: list[str] | None) -> list[str]:
    if not values:
        return list(ACTIVE_REPOS)
    wanted = set()
    for value in values:
        name = value.removeprefix("juniper-")
        if name in ARCHIVED_REPOS:
            raise UsageError(f"juniper-{name} is an archive, not a git checkout; it is never checked")
        if name not in ACTIVE_REPOS:
            raise UsageError(f"unknown repo {value!r}; known: {', '.join(ACTIVE_REPOS)}")
        wanted.add(name)
    return [name for name in ACTIVE_REPOS if name in wanted]


def build_parser() -> _Parser:
    parser = _Parser(
        prog="git_remote_alias_check.py",
        description="Check that each Juniper checkout's origin, ssh alias and deploy key follow the per-repo alias design (gate G-ALIAS).",
        epilog="Exit codes: 0 all checks pass (or --if-configured skipped), 1 a check failed, 2 usage or environment error.",
    )
    parser.add_argument("--root", metavar="DIR", help="the Juniper root (default: $JUNIPER_ROOT, else $HOME/Development/python/Juniper)")
    parser.add_argument("--repo", action="append", metavar="NAME", help="check only this repo (k8s or juniper-k8s); repeatable")
    parser.add_argument("--json", action="store_true", help="print one JSON object instead of the report")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check only (the default)")
    mode.add_argument("--fix", action="store_true", help="rewrite a non-alias origin of the same repository to the alias URL, then re-read it")
    parser.add_argument("--dry-run", action="store_true", help="with --fix: print the planned rewrites, change nothing")
    parser.add_argument("--if-configured", action="store_true", help="exit 0 (skipped) when the ssh config has no 'Host github_juniper-*' line")
    parser.add_argument("--ssh-config", metavar="FILE", help="the file --if-configured looks in (default: ~/.ssh/config)")
    return parser


def startup_error(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def emit(report: Report, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.as_json(), indent=2))
        return
    if report.skip_reason is None:
        for repo in report.repos:
            for check in repo.checks:
                line = f"{STATUS_LABEL[check.status]:<5} {repo.repo:<21} {check.name:<6} {check.message}"
                if check.plan is not None:
                    line += f" -- DRY-RUN: would run: {check.plan}"
                elif not check.ok and check.remediation:
                    line += f" -- fix: {check.remediation}"
                print(line)
    print(report.summary())


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        names = select_repos(args.repo)
        if args.dry_run and not args.fix:
            raise UsageError("--dry-run only applies with --fix")
        if args.ssh_config is not None and not args.if_configured:
            raise UsageError("--ssh-config only applies with --if-configured; the alias check always asks ssh -G")
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Run with --help for usage.", file=sys.stderr)
        return 2

    home = os.path.expanduser("~")
    root = absolute(args.root or os.environ.get("JUNIPER_ROOT") or os.path.join(home, "Development", "python", "Juniper"))
    ssh_config = absolute(args.ssh_config or os.path.join(home, ".ssh", "config"))
    mode = "fix-dry-run" if args.dry_run else "fix" if args.fix else "check"
    report = Report(mode=mode, root=root, ssh_config=ssh_config)

    if args.if_configured:
        try:
            configured = ssh_config_has_alias(ssh_config)
        except OSError as exc:
            return startup_error(f"cannot read the ssh config {ssh_config}: {exc.strerror or exc}")
        if not configured:
            report.skip_reason = f"no github_juniper-* Host alias in {ssh_config}"
            emit(report, args.json)
            return 0

    git_name = os.environ.get("GIT") or "git"
    ssh_name = os.environ.get("SSH") or "ssh"
    git_program = shutil.which(git_name)
    ssh_program = shutil.which(ssh_name)
    if git_program is None:
        return startup_error(f"git not found (GIT={git_name})")
    if ssh_program is None:
        return startup_error(f"ssh not found (SSH={ssh_name})")
    if not os.path.isdir(root):
        return startup_error(f"the Juniper root {root} is not a directory (pass --root or set JUNIPER_ROOT)")

    git = Git(git_program, git_environment(git_program))
    for name in names:
        checkout = os.path.join(root, f"juniper-{name}")
        checks = [
            check_origin(git, checkout, name, fix=args.fix, dry_run=args.dry_run),
            check_alias(ssh_program, name, home, ssh_config),
            check_key(home, name),
        ]
        report.repos.append(RepoResult(name, checkout, checks))
    emit(report, args.json)
    return report.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
