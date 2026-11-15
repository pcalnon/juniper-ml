#!/usr/bin/env python3
"""Run a Juniper repo's own test wrapper under another Python version, in a venv kept at a fixed path.

Project: juniper-ml
Sub-Project: ecosystem tooling (the Python 3.15 migration, phase 1)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-15
Status: permanent utility
Related: conf/python_versions.yaml (the version lists and each repo's recipe);
         tests/test_python_version_check.py (this script); tests/test_python_version_matrix_drift.py (CI's
         matrices against the lists); juniper-ml#2567 (the CI half: informational Python 3.15 legs)

Why this exists
---------------
The owner's request of 2026-11-14: add Python 3.15 to the tested versions, in the local test infrastructure
and in CI, and at this stage let its checks report results without blocking a commit, a merge or a
deployment. CI got its informational legs in juniper-ml#2567, and each sibling repo gets its own PR. Locally
there was no version list to extend. No repo has a tox or nox file, and every local runner (``make coverage``,
``util/run_coverage.bash``, canopy's ``make test``) uses whatever ``python`` is active. No conda env on the
host carries 3.15, and ``/usr/bin/python3`` must stay 3.14: switching it to 3.15 host-wide on 2026-11-14
broke the backup drills and the conda env links, and the owner deferred that switch.

So, for each repo and version, this builds one venv from ``/usr/bin/python<version>``, installs the repo into
it with its CI's install commands, and runs the repo's EXISTING wrapper with the venv first on PATH. The
version lists and the recipes are data, in conf/python_versions.yaml. The owner's ruling: 3.12, 3.13 and 3.14
are blocking, 3.15 is informational, and a run with no ``--python`` runs the informational versions.

What one check does
-------------------
For a repo and a version:

1. The interpreter is ``/usr/bin/python<version>``, else ``python<version>`` on PATH. It must report that
   version (``platform.python_version()`` under ``-I``). If it is missing or reports another version, the
   result is ``unavailable``; the run does not crash. So is a check whose primary checkout ``{root}/{repo}``
   or ``--checkout`` directory does not exist: the helper never creates a checkout.
2. The venv is ``{root}/{repo}/tmp/pyvenv/py{version}/``: the repo's primary checkout's gitignored ``tmp/``,
   whatever ``--checkout`` names and whatever TMPDIR is. It is kept between runs and reused while its own
   interpreter reports the version. ``--recreate`` rebuilds it. A path there that is a symlink, or a
   directory with no ``pyvenv.cfg``, is never removed: the check fails and names it.
3. ``{root}/{repo}/tmp/pyvenv/py{version}.lock`` is held (``flock``) from the venv step to the last test,
   so two runs never install into one venv at once. A lock another run holds makes the result
   ``unavailable``.
4. Each ``install`` command of the recipe runs in order, then every ``test`` command, each as
   ``bash -e -o pipefail -c <command>`` from the checkout's root. A failed install step stops the check
   before the tests. Every test step runs, so a repo with several packages reports each one.

Each child process gets the venv's ``bin/`` first on PATH and ``VIRTUAL_ENV`` set to the venv (what
``activate`` does), so ``python`` and ``pip`` in a recipe are the venv's. ``TMPDIR`` is ``{root}/{repo}/tmp``,
and that directory is prepended to ``GIT_CEILING_DIRECTORIES``, so a test's "not a git repo" directory under
``tmp_path`` stays one. ``PYTHONPATH``, ``PYTHONHOME`` and the recipe's ``env_unset`` names are removed;
``PIP_DISABLE_PIP_VERSION_CHECK=1`` is set. A step's output goes to its log only, not to the console.

What it writes, and what it never touches
-----------------------------------------
- the venv and its lock file, both under ``{root}/{repo}/tmp/pyvenv/``;
- one run directory, ``{root}/juniper-ml/tmp/python-version-checks/<UTC stamp>/``, holding ``summary.json``
  and ``{repo}/py{version}/{venv,install-<n>,test-<name>}.log``. It is never pruned: the 2026-10-26
  retention rule applies (keep a file until nothing needs it).

It writes nothing under the system temp directory, and nothing in a checkout. The repo's own install and
wrapper leave what they always leave there (``*.egg-info``, ``__pycache__/``, ``.coverage``, ``reports/``),
all of it ignored by git. It never touches a conda env or ``/usr/bin/python3``, and it is not a pre-commit hook:
tests/test_python_version_check.py fails if ``.pre-commit-config.yaml`` names it.

Usage
-----
    python3 util/python_version_check.py (--repo NAME... | --all) [--python X.Y]... [--checkout PATH]
        [--root DIR] [--config FILE] [--recreate] [--dry-run] [--strict]
    python3 util/python_version_check.py --list [--repo NAME... | --all] [--root DIR] [--config FILE]

``--repo NAME``
    A repo of conf/python_versions.yaml. Repeatable; ``data-client`` and ``juniper-data-client`` both work.
``--all``
    Every repo of the config, in its order.
``--python X.Y``
    A version from the config's ``blocking`` or ``informational`` list. Repeatable. Default: every
    informational version.
``--checkout PATH``
    Run the wrapper in this checkout (a worktree, say) instead of ``{root}/{repo}``. One ``--repo`` only.
    The venv stays in the primary's ``tmp/``.
``--root DIR``
    The Juniper root. Default: ``$JUNIPER_ROOT``, then ``~/Development/python/Juniper``.
``--config FILE``
    Default: ``conf/python_versions.yaml`` in the checkout that holds this script.
``--recreate``
    Remove each venv (only a directory holding ``pyvenv.cfg``) and build it again.
``--list``
    Print the version lists, each version's interpreter, and each repo's venv and recipe. Runs nothing.
``--dry-run``
    Print what each check would run. Runs nothing and writes nothing; an interpreter is checked for
    existence only.
``--strict``
    Exit 1 when any check failed or was unavailable.

Output
------
One line per check, ``STATUS  <repo> <version> (<class>)  <detail>``, where STATUS is PASSED, FAILED or
UNAVAILABLE (PLAN under ``--dry-run``), then the summary path and the counts. Progress goes to stderr.

Exit codes
----------
0    the run finished, whatever its results: the checks are informational. Also ``--list`` and ``--dry-run``.
1    ``--strict`` only: at least one check failed or was unavailable.
2    usage or configuration: a bad argument, an unknown repo or version, ``--checkout`` without exactly one
     ``--repo``, a root that is not a directory, an invalid or unreadable config, PyYAML not installed.
130  interrupted; the summary holds the checks that finished.

Environment
-----------
``JUNIPER_ROOT``                      the Juniper root (see ``--root``)
``PYTHON_VERSION_CHECK_SYSTEM_BIN``   where ``python<version>`` is looked for first (default ``/usr/bin``);
                                      tests point it at a stub directory

summary.json
------------
``schema`` is bumped on any incompatible change. Written after every check, so an interrupted run keeps
what it finished.

    {
      "schema": 1,
      "tool": "util/python_version_check.py",
      "started": str, "finished": str | null,  # UTC, ISO 8601
      "root": str, "config": str, "config_sha256": str, "run_dir": str,
      "strict": bool, "interrupted": bool,
      "counts": {"passed": int, "failed": int, "unavailable": int},
      "exit_code": int | null,                  # null until the run ends
      "results": [{
        "repo": str, "python": str, "class": "blocking" | "informational",
        "status": "passed" | "failed" | "unavailable",
        "reason": str | null,                   # why it failed or was unavailable
        "failed_phase": "venv" | "install" | "test" | null,
        "interpreter": str | null, "interpreter_version": str | null,
        "checkout": str, "venv": str, "venv_action": "created" | "reused" | "recreated" | null,
        "seconds": float,
        "steps": [{"phase": "venv" | "install" | "test", "name": str, "command": str,
                   "returncode": int, "seconds": float, "log": str}]
      }]
    }
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess  # nosec B404 - runs the interpreter, venv, pip and each repo's own wrapper with fixed argv
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
DEFAULT_CONFIG = SCRIPT.parents[1] / "conf" / "python_versions.yaml"
CONFIG_SCHEMA = 1
SUMMARY_SCHEMA = 1
TOOL = "util/python_version_check.py"
DEFAULT_ROOT = os.path.join("~", "Development", "python", "Juniper")
DEFAULT_SYSTEM_BIN = "/usr/bin"
VENV_DIR = "pyvenv"
LOG_DIR = "python-version-checks"
LOG_REPO = "juniper-ml"

VERSION_RE = re.compile(r"3\.(?:0|[1-9][0-9]?)")
REPO_RE = re.compile(r"juniper-[a-z0-9]+(?:-[a-z0-9]+)*")
STEP_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ENV_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
TOP_KEYS = ("schema", "blocking", "informational", "repos")
RECIPE_KEYS = ("install", "test", "env_unset")

#: Removed from every child's environment. PYTHONHOME points an interpreter at another prefix, and
#: PYTHONPATH puts another environment's packages ahead of the venv's.
SCRUBBED_ENV = ("PYTHONHOME", "PYTHONPATH")
VERSION_PROBE = "import platform; print(platform.python_version())"
PROBE_TIMEOUT_SECONDS = 60


class UsageError(Exception):
    """A bad argument or an invalid config (exit 2)."""


@dataclass(frozen=True)
class Recipe:
    install: tuple[str, ...]
    test: tuple[tuple[str, str], ...]
    env_unset: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    path: Path
    sha256: str
    blocking: tuple[str, ...]
    informational: tuple[str, ...]
    repos: dict[str, Recipe]

    def version_class(self, version: str) -> str:
        return "blocking" if version in self.blocking else "informational"


# ── config ────────────────────────────────────────────────────────────────────────────────────────


def _versions(doc: dict[str, Any], key: str, where: str) -> tuple[str, ...]:
    value = doc.get(key)
    if not isinstance(value, list):
        raise UsageError(f'{where}: `{key}` must be a list of quoted versions such as "3.15"')
    seen: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise UsageError(f"{where}: `{key}` holds {item!r}, which is not a string; quote it (YAML reads an unquoted 3.10 as the float 3.1)")
        if not VERSION_RE.fullmatch(item):
            raise UsageError(f"{where}: `{key}` holds {item!r}, which is not a 3.X version")
        if item in seen:
            raise UsageError(f"{where}: `{key}` lists {item} twice")
        seen.append(item)
    return tuple(seen)


def _string_list(value: Any, what: str, pattern: re.Pattern[str] | None = None) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise UsageError(f"{what} must be a list")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise UsageError(f"{what} holds {item!r}; each entry must be a non-empty string")
        if pattern is not None and not pattern.fullmatch(item):
            raise UsageError(f"{what} holds {item!r}, which is not a valid name")
    return tuple(value)


def _recipe(repo: str, value: Any, where: str) -> Recipe:
    what = f"{where}: repos.{repo}"
    if not isinstance(value, dict):
        raise UsageError(f"{what} must be a mapping with `install` and `test`")
    unknown = sorted(str(k) for k in value if k not in RECIPE_KEYS)
    if unknown:
        raise UsageError(f"{what} has unknown key(s) {', '.join(unknown)}; allowed: {', '.join(RECIPE_KEYS)}")
    if "install" not in value or "test" not in value:
        raise UsageError(f"{what} needs both `install` and `test`")
    install = _string_list(value["install"], f"{what}.install")
    test = value["test"]
    if not isinstance(test, dict) or not test:
        raise UsageError(f"{what}.test must be a non-empty mapping of step name to command")
    steps: list[tuple[str, str]] = []
    for name, command in test.items():
        if not isinstance(name, str) or not STEP_RE.fullmatch(name):
            raise UsageError(f"{what}.test has step name {name!r}; use lower-case letters, digits and hyphens")
        if not isinstance(command, str) or not command.strip():
            raise UsageError(f"{what}.test.{name} must be a non-empty command string")
        steps.append((name, command))
    env_unset = _string_list(value.get("env_unset", []), f"{what}.env_unset", ENV_NAME_RE)
    return Recipe(install=install, test=tuple(steps), env_unset=env_unset)


def validate_config(doc: Any, path: Path, sha256: str) -> Config:
    """Check a parsed config against the schema the module docstring and conf/python_versions.yaml describe."""
    where = str(path)
    if not isinstance(doc, dict):
        raise UsageError(f"{where}: the top level must be a mapping")
    unknown = sorted(str(k) for k in doc if k not in TOP_KEYS)
    if unknown:
        raise UsageError(f"{where}: unknown top-level key(s) {', '.join(unknown)}; allowed: {', '.join(TOP_KEYS)}")
    schema = doc.get("schema")
    if isinstance(schema, bool) or schema != CONFIG_SCHEMA:
        raise UsageError(f"{where}: `schema` must be {CONFIG_SCHEMA}, got {schema!r}")
    blocking = _versions(doc, "blocking", where)
    informational = _versions(doc, "informational", where)
    if not blocking:
        raise UsageError(f"{where}: `blocking` must name at least one version")
    both = [v for v in informational if v in blocking]
    if both:
        raise UsageError(f"{where}: {', '.join(both)} is in both `blocking` and `informational`; a version is one or the other")
    repos = doc.get("repos")
    if not isinstance(repos, dict) or not repos:
        raise UsageError(f"{where}: `repos` must be a non-empty mapping of repo name to recipe")
    recipes: dict[str, Recipe] = {}
    for repo, value in repos.items():
        if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
            raise UsageError(f"{where}: repo name {repo!r} is not of the form juniper-<name>")
        recipes[repo] = _recipe(repo, value, where)
    return Config(path=path, sha256=sha256, blocking=blocking, informational=informational, repos=recipes)


def load_config(path: Path) -> Config:
    try:
        import yaml
    except ImportError:
        raise UsageError("PyYAML is needed to read the version list: python3 -m pip install pyyaml") from None
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UsageError(f"cannot read {path}: {exc.strerror or exc}") from None
    try:
        doc = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise UsageError(f"{path} is not valid YAML: {exc}") from None
    return validate_config(doc, path, hashlib.sha256(raw).hexdigest())


# ── paths ─────────────────────────────────────────────────────────────────────────────────────────


def juniper_root(arg: str | None) -> Path:
    return Path(os.path.abspath(os.path.expanduser(arg or os.environ.get("JUNIPER_ROOT") or DEFAULT_ROOT)))


def repo_tmp(root: Path, repo: str) -> Path:
    """The repo's temp root: its PRIMARY checkout's gitignored tmp/ (the 2026-10-26 rule)."""
    return root / repo / "tmp"


def venv_path(root: Path, repo: str, version: str) -> Path:
    """FIXED: derived from the root, the repo and the version only -- never from TMPDIR or --checkout."""
    return repo_tmp(root, repo) / VENV_DIR / f"py{version}"


def lock_path(root: Path, repo: str, version: str) -> Path:
    return repo_tmp(root, repo) / VENV_DIR / f"py{version}.lock"


def log_root(root: Path) -> Path:
    return repo_tmp(root, LOG_REPO) / LOG_DIR


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_run_dir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    for n in range(1000):
        candidate = base / (stamp if n == 0 else f"{stamp}-{n}")
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise OSError(f"no free run directory for {stamp} under {base}")


# ── interpreters and environments ────────────────────────────────────────────────────────────────


def system_bin() -> Path:
    return Path(os.environ.get("PYTHON_VERSION_CHECK_SYSTEM_BIN") or DEFAULT_SYSTEM_BIN)


def find_interpreter(version: str) -> Path | None:
    name = f"python{version}"
    candidate = system_bin() / name
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate
    found = shutil.which(name)
    return Path(found) if found else None


def reported_version(interpreter: Path, env: dict[str, str]) -> str | None:
    """What the interpreter says it is, or None when it cannot be run."""
    try:
        proc = subprocess.run([str(interpreter), "-I", "-c", VERSION_PROBE], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS, check=False)  # nosec B603
    except (OSError, subprocess.TimeoutExpired):
        return None
    reported = proc.stdout.strip()
    return reported if proc.returncode == 0 and reported else None


def same_minor(reported: str | None, version: str) -> bool:
    return reported is not None and reported.split(".")[:2] == version.split(".")


def base_env(root: Path, repo: str, recipe: Recipe) -> dict[str, str]:
    env = dict(os.environ)
    for name in (*SCRUBBED_ENV, *recipe.env_unset):
        env.pop(name, None)
    tmp = str(repo_tmp(root, repo))
    env["TMPDIR"] = tmp
    ceilings = [tmp, *(p for p in env.get("GIT_CEILING_DIRECTORIES", "").split(os.pathsep) if p and p != tmp)]
    env["GIT_CEILING_DIRECTORIES"] = os.pathsep.join(ceilings)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def venv_env(env: dict[str, str], venv: Path) -> dict[str, str]:
    activated = dict(env)
    activated["VIRTUAL_ENV"] = str(venv)
    path = activated.get("PATH", "")
    activated["PATH"] = os.pathsep.join([str(venv / "bin"), path]) if path else str(venv / "bin")
    return activated


# ── one check ────────────────────────────────────────────────────────────────────────────────────


def progress(message: str) -> None:
    print(f"==> {message}", file=sys.stderr, flush=True)


def run_step(argv: list[str], cwd: Path, env: dict[str, str], log: Path) -> tuple[int, float]:
    """Run argv with its output appended to log (O_APPEND, so the child's writes and ours interleave in order)."""
    start = time.monotonic()
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"# started:  {utc_now()}\n# cwd:      {cwd}\n# command:  {shlex.join(argv)}\n\n")
        fh.flush()
        try:
            proc = subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT, check=False)  # nosec B603
            returncode = proc.returncode
        except OSError as exc:
            fh.write(f"could not start: {exc}\n")
            returncode = 127
        fh.write(f"\n# exit status: {returncode}\n")
    return returncode, round(time.monotonic() - start, 3)


def new_result(config: Config, repo: str, version: str, checkout: Path, venv: Path) -> dict[str, Any]:
    return {
        "repo": repo,
        "python": version,
        "class": config.version_class(version),
        "status": None,
        "reason": None,
        "failed_phase": None,
        "interpreter": None,
        "interpreter_version": None,
        "checkout": str(checkout),
        "venv": str(venv),
        "venv_action": None,
        "seconds": 0.0,
        "steps": [],
    }


def prepare_venv(result: dict[str, Any], interpreter: Path, version: str, venv: Path, recreate: bool, env: dict[str, str], log: Path) -> bool:
    """Reuse, create or rebuild the venv. False (with reason and failed_phase set) when it cannot be had."""
    if venv.is_symlink():
        result.update(failed_phase="venv", reason=f"{venv} is a symlink; it is never used or removed")
        return False
    config_file = venv / "pyvenv.cfg"
    if venv.exists() and not config_file.is_file():
        result.update(failed_phase="venv", reason=f"{venv} exists and holds no pyvenv.cfg, so it is not removed; move it aside by hand")
        return False
    action = "created"
    if config_file.is_file():
        if not recreate:
            reported = reported_version(venv / "bin" / "python", env)
            if same_minor(reported, version):
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text(f"# {utc_now()}: reused {venv}; its interpreter reports {reported}\n", encoding="utf-8")
                result["venv_action"] = "reused"
                return True
        shutil.rmtree(venv)
        action = "recreated"
    venv.parent.mkdir(parents=True, exist_ok=True)
    argv = [str(interpreter), "-m", "venv", str(venv)]
    returncode, seconds = run_step(argv, venv.parent, env, log)
    result["steps"].append({"phase": "venv", "name": "venv", "command": shlex.join(argv), "returncode": returncode, "seconds": seconds, "log": str(log)})
    if returncode != 0:
        result.update(failed_phase="venv", reason=f"`python{version} -m venv` exited {returncode}")
        return False
    result["venv_action"] = action
    return True


def acquire_lock(path: Path) -> Any:
    """An flock on path, or None when another run holds it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a", encoding="utf-8")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        return None
    return fh


def run_check(config: Config, root: Path, repo: str, version: str, checkout: Path, run_dir: Path, recreate: bool) -> dict[str, Any]:
    recipe = config.repos[repo]
    venv = venv_path(root, repo, version)
    result = new_result(config, repo, version, checkout, venv)
    started = time.monotonic()
    try:
        _run_check(result, recipe, root, repo, version, checkout, venv, run_dir / repo / f"py{version}", recreate)
    finally:
        result["seconds"] = round(time.monotonic() - started, 3)
    return result


def missing_checkout(root: Path, repo: str, checkout: Path) -> str | None:
    """Why the check cannot start for want of a directory, or None. The venv lives in the PRIMARY's tmp/, so
    the primary must exist even when --checkout names another checkout: the helper never creates one."""
    if not (root / repo).is_dir():
        return f"no primary checkout at {root / repo} (the venv lives in its tmp/)"
    if not checkout.is_dir():
        return f"no checkout at {checkout}"
    return None


def _run_check(result: dict[str, Any], recipe: Recipe, root: Path, repo: str, version: str, checkout: Path, venv: Path, logs: Path, recreate: bool) -> None:
    missing = missing_checkout(root, repo, checkout)
    if missing:
        result.update(status="unavailable", reason=missing)
        return
    interpreter = find_interpreter(version)
    if interpreter is None:
        result.update(status="unavailable", reason=f"no python{version} in {system_bin()} or on PATH")
        return
    result["interpreter"] = str(interpreter)
    env = base_env(root, repo, recipe)
    repo_tmp(root, repo).mkdir(parents=True, exist_ok=True)
    reported = reported_version(interpreter, env)
    result["interpreter_version"] = reported
    if not same_minor(reported, version):
        result.update(status="unavailable", reason=f"{interpreter} reports {reported or 'nothing'}, not {version}")
        return
    lock = acquire_lock(lock_path(root, repo, version))
    if lock is None:
        result.update(status="unavailable", reason=f"another run holds {lock_path(root, repo, version)}")
        return
    try:
        progress(f"{repo} {version}: venv {venv}")
        if not prepare_venv(result, interpreter, version, venv, recreate, env, logs / "venv.log"):
            result["status"] = "failed"
            return
        activated = venv_env(env, venv)
        for n, command in enumerate(recipe.install, 1):
            log = logs / f"install-{n}.log"
            progress(f"{repo} {version}: install {n}/{len(recipe.install)}: {command}  (log: {log})")
            returncode, seconds = run_step(["bash", "-e", "-o", "pipefail", "-c", command], checkout, activated, log)
            result["steps"].append({"phase": "install", "name": f"install-{n}", "command": command, "returncode": returncode, "seconds": seconds, "log": str(log)})
            if returncode != 0:
                result.update(status="failed", failed_phase="install", reason=f"install step {n} exited {returncode}")
                return
        failed: list[str] = []
        for name, command in recipe.test:
            log = logs / f"test-{name}.log"
            progress(f"{repo} {version}: test {name}: {command}  (log: {log})")
            returncode, seconds = run_step(["bash", "-e", "-o", "pipefail", "-c", command], checkout, activated, log)
            result["steps"].append({"phase": "test", "name": name, "command": command, "returncode": returncode, "seconds": seconds, "log": str(log)})
            if returncode != 0:
                failed.append(f"`{name}` exited {returncode}")
        if failed:
            result.update(status="failed", failed_phase="test", reason="test " + ", ".join(failed))
        else:
            result["status"] = "passed"
    finally:
        lock.close()


# ── output ───────────────────────────────────────────────────────────────────────────────────────


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(partial, path)


def counts(results: list[dict[str, Any]]) -> dict[str, int]:
    return {status: sum(1 for r in results if r["status"] == status) for status in ("passed", "failed", "unavailable")}


def result_line(result: dict[str, Any], logs: Path | None) -> str:
    head = f"{result['status'].upper():<12} {result['repo']} {result['python']} ({result['class']})"
    if result["status"] == "passed":
        phases = [step["phase"] for step in result["steps"]]
        detail = f"venv {result['venv_action']}, {phases.count('install')} install and {phases.count('test')} test steps in {result['seconds']:.0f}s"
    else:
        detail = result["reason"] or ""
    tail = f"  logs: {logs}" if logs is not None and result["steps"] else ""
    return f"{head}  {detail}{tail}"


def venv_plan(venv: Path, recreate: bool) -> str:
    if venv.is_symlink() or (venv.exists() and not (venv / "pyvenv.cfg").is_file()):
        return "exists and is not a venv: the check would fail and leave it"
    if (venv / "pyvenv.cfg").is_file():
        return "would be removed and rebuilt (--recreate)" if recreate else "exists: reused if its interpreter reports the version, else rebuilt"
    return "would be created"


def print_plan(config: Config, root: Path, repo: str, version: str, checkout: Path, recreate: bool) -> str:
    """Print one dry-run check and return its status: planned or unavailable."""
    recipe = config.repos[repo]
    head = f"{repo} {version} ({config.version_class(version)})"
    missing = missing_checkout(root, repo, checkout)
    if missing:
        print(f"{'UNAVAILABLE':<12} {head}  {missing}")
        return "unavailable"
    interpreter = find_interpreter(version)
    if interpreter is None:
        print(f"{'UNAVAILABLE':<12} {head}  no python{version} in {system_bin()} or on PATH")
        return "unavailable"
    venv = venv_path(root, repo, version)
    print(f"{'PLAN':<12} {head}")
    print(f"    interpreter  {interpreter} (its version is checked before a real run)")
    print(f"    checkout     {checkout}")
    print(f"    venv         {venv} -- {venv_plan(venv, recreate)}")
    print(f"    lock         {lock_path(root, repo, version)}")
    for n, command in enumerate(recipe.install, 1):
        print(f"    install {n}    {command}")
    for name, command in recipe.test:
        print(f"    test         {name}: {command}")
    print(f"    env          VIRTUAL_ENV={venv}, PATH={venv / 'bin'}:..., TMPDIR={repo_tmp(root, repo)}; unset {', '.join((*SCRUBBED_ENV, *recipe.env_unset))}")
    print(f"    logs         {log_root(root)}/<UTC stamp>/{repo}/py{version}/")
    return "planned"


def print_list(config: Config, root: Path, repos: list[str]) -> None:
    print(f"config         {config.path} (schema {CONFIG_SCHEMA}, sha256 {config.sha256[:12]})")
    print(f"blocking       {' '.join(config.blocking)}")
    print(f"informational  {' '.join(config.informational) or '(none)'}")
    for version in (*config.blocking, *config.informational):
        interpreter = find_interpreter(version)
        print(f"python{version:<8} {interpreter if interpreter else f'unavailable: not in {system_bin()} or on PATH'}")
    print(f"logs           {log_root(root)}/<UTC stamp>/")
    for repo in repos:
        recipe = config.repos[repo]
        print(f"\n{repo}")
        print(f"    checkout     {root / repo}")
        print(f"    venv         {repo_tmp(root, repo) / VENV_DIR}/py<version>")
        for n, command in enumerate(recipe.install, 1):
            print(f"    install {n}    {command}")
        for name, command in recipe.test:
            print(f"    test         {name}: {command}")
        if recipe.env_unset:
            print(f"    env_unset    {' '.join(recipe.env_unset)}")


# ── command line ─────────────────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python_version_check.py", description=__doc__.splitlines()[0], epilog="Full reference: the module docstring, and docs/REFERENCE.md § Utility Script Reference.")
    which = parser.add_mutually_exclusive_group()
    which.add_argument("--repo", action="append", default=[], metavar="NAME", help="a repo of the config (repeatable; the juniper- prefix is optional)")
    which.add_argument("--all", action="store_true", help="every repo of the config")
    parser.add_argument("--python", action="append", default=[], metavar="X.Y", help="a version of the config (repeatable; default: the informational versions)")
    parser.add_argument("--checkout", metavar="PATH", help="run in this checkout instead of the primary (one --repo only)")
    parser.add_argument("--root", metavar="DIR", help="the Juniper root (default: $JUNIPER_ROOT, else ~/Development/python/Juniper)")
    parser.add_argument("--config", metavar="FILE", type=Path, default=DEFAULT_CONFIG, help="the version list (default: conf/python_versions.yaml beside this script)")
    parser.add_argument("--recreate", action="store_true", help="rebuild each venv")
    parser.add_argument("--list", action="store_true", help="print the versions, interpreters and recipes; run nothing")
    parser.add_argument("--dry-run", action="store_true", help="print what would run; run and write nothing")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any check failed or was unavailable")
    return parser.parse_args(argv)


def select_repos(config: Config, args: argparse.Namespace) -> list[str]:
    if args.all or (args.list and not args.repo):
        return list(config.repos)
    if not args.repo:
        raise UsageError("name a repo with --repo, or pass --all or --list")
    chosen: list[str] = []
    for name in args.repo:
        repo = name if name.startswith("juniper-") else f"juniper-{name}"
        if repo not in config.repos:
            raise UsageError(f"unknown repo {name!r}; {config.path} has: {', '.join(config.repos)}")
        if repo not in chosen:
            chosen.append(repo)
    return chosen


def select_versions(config: Config, requested: list[str]) -> list[str]:
    if not requested:
        return list(config.informational)
    chosen: list[str] = []
    for version in requested:
        if version not in config.blocking and version not in config.informational:
            raise UsageError(f"Python {version} is in neither list of {config.path} (blocking: {', '.join(config.blocking)}; informational: {', '.join(config.informational) or 'none'})")
        if version not in chosen:
            chosen.append(version)
    return chosen


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        repos = select_repos(config, args)
        versions = select_versions(config, args.python)
        root = juniper_root(args.root)
        if not root.is_dir():
            raise UsageError(f"the Juniper root {root} is not a directory (pass --root or set JUNIPER_ROOT)")
        if args.checkout and (args.all or len(repos) != 1):
            raise UsageError("--checkout needs exactly one --repo")
    except UsageError as exc:
        print(f"python_version_check: {exc}", file=sys.stderr)
        return 2
    if args.list:
        print_list(config, root, repos)
        return 0
    checkouts = {repo: Path(os.path.abspath(args.checkout)) if args.checkout else root / repo for repo in repos}
    if not versions:
        print(f"nothing to run: {config.path} lists no informational version; pass --python")
        return 0
    if args.dry_run:
        statuses = [print_plan(config, root, repo, version, checkouts[repo], args.recreate) for repo in repos for version in versions]
        print("dry run: nothing was run or written")
        return 1 if args.strict and "unavailable" in statuses else 0
    return run_all(config, root, repos, versions, checkouts, args)


def run_all(config: Config, root: Path, repos: list[str], versions: list[str], checkouts: dict[str, Path], args: argparse.Namespace) -> int:
    run_dir = make_run_dir(log_root(root))
    summary_path = run_dir / "summary.json"
    results: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "schema": SUMMARY_SCHEMA,
        "tool": TOOL,
        "started": utc_now(),
        "finished": None,
        "root": str(root),
        "config": str(config.path),
        "config_sha256": config.sha256,
        "run_dir": str(run_dir),
        "strict": args.strict,
        "interrupted": False,
        "counts": counts(results),
        "exit_code": None,
        "results": results,
    }
    write_summary(summary_path, summary)
    exit_code = 0
    try:
        for repo in repos:
            for version in versions:
                result = run_check(config, root, repo, version, checkouts[repo], run_dir, args.recreate)
                results.append(result)
                summary["counts"] = counts(results)
                write_summary(summary_path, summary)
                print(result_line(result, run_dir / repo / f"py{version}"), flush=True)
    except KeyboardInterrupt:
        summary["interrupted"] = True
        exit_code = 130
    tally = counts(results)
    if exit_code == 0 and args.strict and (tally["failed"] or tally["unavailable"]):
        exit_code = 1
    summary.update(finished=utc_now(), counts=tally, exit_code=exit_code)
    write_summary(summary_path, summary)
    print(f"summary: {summary_path}")
    note = "" if args.strict else " (the checks are informational; --strict exits 1 on a failed or unavailable check)"
    print(f"python_version_check: {tally['passed']} passed, {tally['failed']} failed, {tally['unavailable']} unavailable; exit {exit_code}{note}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
