"""Generate `conf/requirements_ci.txt` and `conf/conda_environment_ci.yaml`.

Python port of the historical ``scripts/generate_dep_docs.sh`` that lived in
every Juniper repo. The canonical pre-port behavior was the cascor 2026-05-20
variant (cascor#276), which switched the conda-dependency extraction from
``sed`` to ``awk`` to avoid emitting a trailing top-level key (``prefix:`` /
``variables:``) that broke YAML validation under some setup-miniconda
configurations.

The semantics of this module preserve that fix exactly:

- We invoke ``conda env export --no-builds`` and slice out the block of lines
  that follow ``^dependencies:$`` up to (but not including) the next line that
  begins with an ASCII letter at column 0. This is the awk fix translated to
  Python; the previous sed-range form has been deliberately abandoned.
- The output is fed through :func:`yaml.safe_load` before being declared
  successful; a parse failure raises :class:`YamlValidationError` so the CLI
  can exit non-zero in CI.

Public surface:

- :class:`GenerateResult` -- dataclass summarizing one generation run.
- :func:`generate_dep_docs` -- ergonomic library entry point (kwargs all
  optional, sensible defaults match the bash script's behavior).
- :func:`render_header` -- placeholder substitution helper exposed for tests
  and ad-hoc callers; uses the same ``<X.Y.Z ...>``, ``<YYYY-MM-dd ...>``,
  ``<Python Version>``, ``<Pip Version>`` placeholders the original sed
  pipeline understood.
"""

from __future__ import annotations

import datetime as _dt
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

try:
    import tomllib as _tomllib  # Python 3.11+
except ImportError:  # pragma: no cover - 3.10 fallback only
    import tomli as _tomllib  # type: ignore[no-redef]

import yaml


# ── Errors ────────────────────────────────────────────────────────────────────


class GenerateDepDocsError(RuntimeError):
    """Base class for generate-dep-docs failures."""


class PyprojectError(GenerateDepDocsError):
    """The repo's pyproject.toml is missing, unreadable, or has no version."""


class YamlValidationError(GenerateDepDocsError):
    """The generated conda_environment_ci.yaml failed PyYAML parse."""


# ── Result ────────────────────────────────────────────────────────────────────


@dataclass
class GenerateResult:
    """Structured outcome of one :func:`generate_dep_docs` run."""

    repo_version: str
    python_version: str
    pip_version: str
    timestamp: str
    pip_file: Path
    conda_file: Optional[Path]
    pip_backup: Optional[Path]
    conda_backup: Optional[Path]
    conda_skipped_reason: Optional[str]
    yaml_validated: bool
    notes: list[str] = field(default_factory=list)


# ── Placeholder substitution ──────────────────────────────────────────────────


# Substitutions match the historical sed pipeline. The two date-case variants
# ("Current date" vs "current date", "Current Year" vs "current year") were
# both present in the original script for header drift across repos, so we
# preserve case-insensitive matching for those.
def render_header(template: str, *, repo_version: str, date: str, year: str, conda_date: str, python_version: str, pip_version: str) -> str:
    """Substitute the historical ``<...>`` placeholders in a header template.

    Returns the rendered text. Unknown placeholders are left intact, matching
    the original sed pipeline's behavior. Placeholder matching is intentionally
    case-insensitive on the "current"/"Current" axis to absorb header drift
    across repos without re-introducing it.
    """

    substitutions: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"<X\.Y\.Z\s+Major, Minor, Point Version for [^>]+>"), repo_version),
        (re.compile(r"<YYYY-MM-dd for (?:Current|current) date>"), date),
        (re.compile(r"<YYYY for (?:Current|current) [Yy]ear>"), year),
        (re.compile(r"<YYYY\.MM\.dd for (?:Current|current) date>"), conda_date),
        (re.compile(r"<Python Version>"), python_version),
        (re.compile(r"<Pip Version>"), pip_version),
    ]
    out = template
    for pattern, replacement in substitutions:
        out = pattern.sub(replacement, out)
    return out


# ── Conda extraction (the 2026-05-20 awk fix, in Python) ──────────────────────


_DEPENDENCIES_LINE = "dependencies:"
_TOP_LEVEL_KEY = re.compile(r"^[a-zA-Z]")


def _extract_conda_dependency_block(env_export: str) -> str:
    """Return the dependency-list lines from ``conda env export --no-builds``.

    Mirrors the awk pipeline in cascor#276:
    ``awk '/^dependencies:$/{flag=1; next} flag && /^[a-zA-Z]/{flag=0} flag'``.
    That is: start collecting after the literal ``dependencies:`` line, stop
    *before* the next line that begins with an ASCII letter at column 0
    (which is the next top-level key like ``prefix:`` or ``variables:``).
    The terminator line is NOT included, which is the bug the awk fix
    addressed versus the previous sed-range form.
    """

    out: list[str] = []
    collecting = False
    for line in env_export.splitlines():
        if not collecting:
            if line == _DEPENDENCIES_LINE:
                collecting = True
            continue
        if _TOP_LEVEL_KEY.match(line):
            collecting = False
            continue
        out.append(line)
    return "\n".join(out)


# ── Subprocess helpers ────────────────────────────────────────────────────────


def _run(cmd: Sequence[str], *, check: bool = True) -> str:
    """Run *cmd* and return stdout as text. Raises on non-zero exit when *check*."""

    proc = subprocess.run(  # noqa: S603 - cmd controlled by this module
        list(cmd),
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise GenerateDepDocsError("command failed: {} (rc={})\nstderr: {}".format(" ".join(cmd), proc.returncode, proc.stderr.strip()))
    return proc.stdout


def _read_pyproject_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        raise PyprojectError("pyproject.toml not found at {}".format(pyproject))
    try:
        data = _tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PyprojectError("pyproject.toml at {} could not be parsed: {}".format(pyproject, exc)) from exc
    try:
        version = data["project"]["version"]
    except KeyError as exc:
        raise PyprojectError("pyproject.toml at {} has no [project].version".format(pyproject)) from exc
    if not isinstance(version, str):
        raise PyprojectError("pyproject.toml at {} has non-string [project].version".format(pyproject))
    return version


def _detect_python_version() -> str:
    # Mirrors `python --version 2>&1 | awk '{print $2}'` from the bash script.
    return platform.python_version()


def _detect_pip_version() -> str:
    # Mirrors `pip --version 2>&1 | awk '{print $2}'`. We invoke pip via the
    # current interpreter so that the version returned matches the environment
    # we're freezing from.
    out = _run([sys.executable, "-m", "pip", "--version"])
    parts = out.split()
    return parts[1] if len(parts) >= 2 else "unknown"


def _pip_list_freeze() -> str:
    return _run([sys.executable, "-m", "pip", "list", "--format=freeze"])


def _conda_env_export(conda_cmd: str) -> str:
    return _run([conda_cmd, "env", "export", "--no-builds"])


# ── Public entry point ────────────────────────────────────────────────────────


def _now() -> _dt.datetime:
    return _dt.datetime.now()


def _default_header(kind: str, date: str, python_version: str) -> str:
    fname = "requirements_ci.txt" if kind == "pip" else "conda_environment_ci.yaml"
    return ("# {fname} - Generated {date}\n# Python: {pyv}\n\n".format(fname=fname, date=date, pyv=python_version))


def generate_dep_docs(
    *,
    repo_root: Optional[Path] = None,
    conf_dir: str = "conf",
    notes_dir: str = "notes",
    pip_header_name: str = "PIP_DEPENDENCY_FILE_HEADER.md",
    conda_header_name: str = "CONDA_DEPENDENCY_FILE_HEADER.md",
    pip_filename: str = "requirements_ci.txt",
    conda_filename: str = "conda_environment_ci.yaml",
    include_conda: bool = True,
    validate_yaml: bool = True,
    conda_command: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    now: Optional[_dt.datetime] = None,
) -> GenerateResult:
    """Generate dependency documentation files for the repo rooted at *repo_root*.

    All arguments default to the values used by the original bash script. The
    ``conda_command`` and ``now`` parameters exist for tests; production callers
    should leave them at their defaults.

    Returns a :class:`GenerateResult` summarizing what was written, including
    any backup paths. Raises :class:`YamlValidationError` if conda output is
    requested and the resulting file fails PyYAML parse (matches the original
    script's hard-fail).
    """

    del env  # reserved for future use; kept in the signature for stability
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    now_dt = now if now is not None else _now()

    timestamp = now_dt.strftime("%Y-%m-%d_%H-%M-%S")
    date = now_dt.strftime("%Y-%m-%d")
    year = now_dt.strftime("%Y")
    conda_date = now_dt.strftime("%Y.%m.%d")

    repo_version = _read_pyproject_version(root)
    python_version = _detect_python_version()
    pip_version = _detect_pip_version()

    conf_path = root / conf_dir
    conf_path.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []

    # ── Pip requirements ─────────────────────────────────────────────────────
    pip_file = conf_path / pip_filename
    pip_backup: Optional[Path] = None
    if pip_file.is_file():
        pip_backup = conf_path / "{}_{}.txt".format(Path(pip_filename).stem, timestamp)
        shutil.copy2(pip_file, pip_backup)
        notes.append("backed up existing {} to {}".format(pip_file, pip_backup))

    pip_header_path = root / notes_dir / pip_header_name
    if pip_header_path.is_file():
        rendered = render_header(
            pip_header_path.read_text(encoding="utf-8"),
            repo_version=repo_version,
            date=date,
            year=year,
            conda_date=conda_date,
            python_version=python_version,
            pip_version=pip_version,
        )
    else:
        rendered = _default_header("pip", date, python_version)
        notes.append("no {} header found; wrote minimal fallback".format(pip_header_name))

    pip_freeze_output = _pip_list_freeze()
    pip_file.write_text(rendered + pip_freeze_output, encoding="utf-8")

    # ── Conda environment ────────────────────────────────────────────────────
    conda_file: Optional[Path] = None
    conda_backup: Optional[Path] = None
    conda_skipped_reason: Optional[str] = None
    yaml_validated = False

    if include_conda:
        conda_cmd = conda_command if conda_command is not None else shutil.which("conda")
        if conda_cmd is None:
            conda_skipped_reason = "conda not on PATH; skipping conda_environment_ci.yaml"
            notes.append(conda_skipped_reason)
        else:
            conda_file = conf_path / conda_filename
            if conda_file.is_file():
                conda_backup = conf_path / "{}_{}.yaml".format(Path(conda_filename).stem, timestamp)
                shutil.copy2(conda_file, conda_backup)
                notes.append("backed up existing {} to {}".format(conda_file, conda_backup))

            conda_header_path = root / notes_dir / conda_header_name
            if conda_header_path.is_file():
                conda_rendered = render_header(
                    conda_header_path.read_text(encoding="utf-8"),
                    repo_version=repo_version,
                    date=date,
                    year=year,
                    conda_date=conda_date,
                    python_version=python_version,
                    pip_version=pip_version,
                )
            else:
                conda_rendered = _default_header("conda", date, python_version)
                notes.append("no {} header found; wrote minimal fallback".format(conda_header_name))

            env_export = _conda_env_export(conda_cmd)
            dep_block = _extract_conda_dependency_block(env_export)

            # Ensure exactly one newline between header and dep block. The
            # header conventionally ends with `dependencies:` already.
            body = conda_rendered
            if not body.endswith("\n"):
                body += "\n"
            body += dep_block
            if not body.endswith("\n"):
                body += "\n"
            conda_file.write_text(body, encoding="utf-8")

            if validate_yaml:
                try:
                    yaml.safe_load(conda_file.read_text(encoding="utf-8"))
                    yaml_validated = True
                except yaml.YAMLError as exc:
                    raise YamlValidationError("generated {} has invalid YAML syntax: {}".format(conda_file, exc)) from exc

    return GenerateResult(
        repo_version=repo_version,
        python_version=python_version,
        pip_version=pip_version,
        timestamp=timestamp,
        pip_file=pip_file,
        conda_file=conda_file,
        pip_backup=pip_backup,
        conda_backup=conda_backup,
        conda_skipped_reason=conda_skipped_reason,
        yaml_validated=yaml_validated,
        notes=notes,
    )
