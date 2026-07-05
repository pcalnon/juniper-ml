"""Advisory per-file coverage-gap mapper for Juniper repos.

This module is the logic half of the ``juniper-coverage-gap-map`` console
script (the CLI wrapper lives in
:mod:`juniper_ci_tools.cli_coverage_gap_mapper`). It answers the systemic
gap surfaced by the 2026-06-26 ecosystem test-suite audit: *no per-file
coverage gate exists anywhere* across the Juniper repos -- several CIs run a
bare ``python -m pytest`` (e.g. ``cascor-model``) with no ``--cov`` floor at
all, so a module can rot to single-digit coverage without any signal.

Posture: **advisory-first, enforcing opt-in**. The mapper is a read-only
*reporter* and the CLI stays advisory **by default** -- it exits ``0`` whenever
it produces a report, regardless of how bad the coverage is (see
:mod:`juniper_ci_tools.cli_coverage_gap_mapper` for the exit-code contract).
An opt-in ``--enforce`` mode (work-unit C-0 of the per-file coverage rollout,
``notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md``)
turns findings into a blocking gate -- exit ``1`` when any source file or
sub-module is under its floor -- but promoting a *specific repo's CI* to the
blocking gate stays a separate, per-repo, owner-signed decision.

The two enforcing bases (deliberately different from the advisory display)
------------------------------------------------------------------------
The advisory report and the enforcing gate measure the same coverage two
different ways, because the ratified gate basis is cross-unit-consistent while
the advisory display mirrors coverage.py:

* **Per-file gate = statement coverage** (:attr:`FileCoverage.statement_percent`
  = ``covered_statements / num_statements``), **not** the branch-inclusive
  :attr:`FileCoverage.percent_covered` the advisory report shows. A repo that
  sets ``branch = true`` reports a branch-inclusive ``summary.percent_covered``;
  gating on statements keeps the floor apples-to-apples across units.
* **Sub-module gate = pooled coverage** (:attr:`SubmoduleCoverage.pooled_percent`
  = ``Sigma covered / Sigma statements``), **not** the mean-of-files
  :attr:`SubmoduleCoverage.average_percent` the advisory report shows. The two
  diverge for small files and can flip outcomes, so the gate uses the
  statement-weighted aggregate.

Exclusions (``--omit``) are applied to the parsed report **before** either the
report or the gate is computed (:func:`parse_coverage_json`'s ``omit=`` /
the CLI's repeatable ``--omit`` glob) -- the tool is the single source of
truth for what counts, rather than trusting coverage's own ``[report] omit``.
Zero-statement files already score 100% (a re-export ``__init__.py`` never
false-positives), so ``--omit`` is for thin ``__main__.py`` / CLI shims,
generated code, and similar per the scoping doc's excluded-files policy.

What it emits
-------------
Given coverage data it produces three views:

* **(a) the per-file coverage distribution** -- every measured file with its
  statement count and percent covered, plus a histogram bucketing of those
  percentages (:meth:`CoverageReport.distribution`).
* **(b) the list of files below the file threshold** -- default ``90`` %
  (:meth:`CoverageReport.files_below_threshold`).
* **(c) each sub-module's average coverage vs the sub-module bar** -- default
  ``95`` % (:meth:`CoverageReport.submodules_below_bar`). A *sub-module* is the
  directory a file lives in (the POSIX dirname of its coverage path).

Two inputs, one primary
-----------------------
The mapper supports **both** a pre-generated ``coverage.json`` (parse it
directly -- :func:`load_coverage_json` / :func:`parse_coverage_json`) **and**
running a repo's real test command under coverage first
(:func:`run_coverage`). The JSON-parsing path is the **primary,
fixture-testable** one; the run-coverage path is a thin convenience that
shells out and then parses the JSON it produced.

The numpy-2.x dotted ``--cov`` shim
-----------------------------------
:func:`run_coverage` builds its coverage invocation through
:func:`package_cov_pytest_args`, which deliberately uses the **package-form**
``--cov=<package>`` and scopes any narrowing through a ``[report] include=``
coverage config (:func:`write_include_coverage_config`) rather than the dotted
``--cov=pkg.submodule`` form. See those two functions' docstrings for the full
gotcha write-up: dotted ``--cov`` trips numpy 2.x's "cannot load module more
than once per process" guard at pytest-cov startup.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

# Spec thresholds (enhancement E-4, plan §6.7). Files strictly below
# ``DEFAULT_FILE_THRESHOLD`` are reported as gaps; a sub-module whose average
# coverage is below ``DEFAULT_SUBMODULE_BAR`` is reported as under the bar.
DEFAULT_FILE_THRESHOLD = 90.0
DEFAULT_SUBMODULE_BAR = 95.0

# Histogram buckets for the per-file distribution. Each entry is
# ``(label, lower_inclusive, upper_exclusive)`` except the final ``[95,100]``
# bucket which is inclusive of 100.0.
_DISTRIBUTION_BUCKETS: tuple[tuple[str, float, float], ...] = (
    ("[0,50)", 0.0, 50.0),
    ("[50,70)", 50.0, 70.0),
    ("[70,80)", 70.0, 80.0),
    ("[80,90)", 80.0, 90.0),
    ("[90,95)", 90.0, 95.0),
    ("[95,100]", 95.0, 100.0),
)


def _round2(value: float) -> float:
    """Round to two decimals (coverage.py's own display precision)."""
    return round(float(value), 2)


def _safe_percent(covered: int, num_statements: int) -> float:
    """Percent covered, defining a zero-statement file as fully covered.

    coverage.py reports ``100`` % for files with no measurable statements;
    we mirror that so an ``__init__.py`` shim does not look like a gap.
    """
    if num_statements <= 0:
        return 100.0
    return 100.0 * covered / num_statements


def _submodule_of(path: str) -> str:
    """Return the sub-module key for a coverage path: its POSIX dirname.

    Top-level files (no directory component) group under ``"."``. Windows
    separators are normalised so the grouping is stable across platforms.
    """
    normalised = path.replace("\\", "/")
    head, sep, _tail = normalised.rpartition("/")
    return head if sep else "."


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    """``True`` when ``path`` matches any ``fnmatch`` glob in ``patterns``.

    Used by :func:`parse_coverage_json`'s ``omit=`` filter (the CLI's repeatable
    ``--omit``). ``fnmatch`` treats ``*`` as spanning ``/`` too, so a pattern
    like ``*/__main__.py`` or ``*__main__.py`` excludes a thin CLI shim wherever
    it sits in the tree. Paths are already normalised to forward slashes.
    """
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _bucket_label(percent: float) -> str:
    """Map a percentage to its :data:`_DISTRIBUTION_BUCKETS` label."""
    for label, lower, upper in _DISTRIBUTION_BUCKETS[:-1]:
        if lower <= percent < upper:
            return label
    # Anything >= 95 (including exactly 100) falls in the final inclusive bucket.
    return _DISTRIBUTION_BUCKETS[-1][0]


@dataclass(frozen=True)
class FileCoverage:
    """Coverage of a single measured file.

    Attributes:
        path: The file path exactly as it appears in the coverage data
            (normalised to forward slashes).
        num_statements: Measurable statements in the file.
        covered_statements: Statements that were executed.
        missing_statements: Statements that were not executed.
        percent_covered: The **advisory display** percentage -- it mirrors
            coverage.py's ``summary.percent_covered`` when present, which is
            **branch-inclusive** when the measured repo sets ``branch = true``
            (it otherwise equals ``covered / num_statements``). A zero-statement
            file is reported as ``100.0``. The enforcing gate does NOT use this;
            it uses :attr:`statement_percent`.
    """

    path: str
    num_statements: int
    covered_statements: int
    missing_statements: int
    percent_covered: float

    @property
    def submodule(self) -> str:
        """The sub-module (directory) this file belongs to."""
        return _submodule_of(self.path)

    @property
    def statement_percent(self) -> float:
        """Statement-only coverage (``covered_statements / num_statements``), 0-100.

        This is the **enforcing** per-file basis (work-unit C-0). It is distinct
        from :attr:`percent_covered`, which mirrors coverage.py's branch-inclusive
        ``summary.percent_covered`` when the measured repo runs ``branch = true``
        -- gating on statements keeps the floor apples-to-apples across units
        regardless of each unit's branch setting. A zero-statement file is
        ``100.0`` (same auto-full-coverage rule the advisory display uses).
        """
        return _round2(_safe_percent(self.covered_statements, self.num_statements))

    def to_dict(self) -> dict:
        """JSON-friendly mapping for the ``--json`` reporter."""
        return {
            "path": self.path,
            "submodule": self.submodule,
            "num_statements": self.num_statements,
            "covered_statements": self.covered_statements,
            "missing_statements": self.missing_statements,
            "percent_covered": self.percent_covered,
            "statement_percent": self.statement_percent,
        }


@dataclass(frozen=True)
class SubmoduleCoverage:
    """Aggregated coverage for one sub-module (directory).

    Two figures are carried because they answer different questions:

    * :attr:`average_percent` -- the arithmetic mean of the per-file
      ``percent_covered`` values in the sub-module. This is the headline
      *"sub-module average"* the spec compares against the bar; it weights
      every file equally (a tiny, uncovered helper drags it as hard as a
      large module).
    * :attr:`pooled_percent` -- the statement-weighted figure
      (``sum(covered) / sum(statements)``), i.e. the sub-module's coverage as
      coverage.py's own totals would compute it. Reported for context.
    """

    name: str
    num_files: int
    total_statements: int
    covered_statements: int
    average_percent: float
    pooled_percent: float

    def below_bar(self, bar: float = DEFAULT_SUBMODULE_BAR) -> bool:
        """``True`` when the mean-of-files average is strictly under ``bar`` (advisory basis)."""
        return self.average_percent < bar

    def below_pooled_bar(self, bar: float = DEFAULT_SUBMODULE_BAR) -> bool:
        """``True`` when the pooled (statement-weighted) coverage is strictly under ``bar``.

        This is the **enforcing** sub-module basis (work-unit C-0). It gates on
        :attr:`pooled_percent` (``Sigma covered / Sigma statements``), not the
        mean-of-files :attr:`average_percent` that :meth:`below_bar` (the
        advisory basis) uses; the two diverge for small files and can flip a
        sub-module's outcome.
        """
        return self.pooled_percent < bar

    def to_dict(self, bar: float = DEFAULT_SUBMODULE_BAR) -> dict:
        """JSON-friendly mapping; ``below_bar`` is resolved against ``bar``."""
        return {
            "name": self.name,
            "num_files": self.num_files,
            "total_statements": self.total_statements,
            "covered_statements": self.covered_statements,
            "average_percent": self.average_percent,
            "pooled_percent": self.pooled_percent,
            "below_bar": self.below_bar(bar),
        }


@dataclass(frozen=True)
class CoverageReport:
    """The parsed, self-contained coverage report.

    Carries the thresholds it was built with so every downstream view
    (``files_below_threshold``, ``submodules_below_bar``, ``to_dict``,
    ``render``) is unambiguous.
    """

    files: tuple[FileCoverage, ...]
    submodules: tuple[SubmoduleCoverage, ...]
    overall_percent: float
    file_threshold: float
    submodule_bar: float

    def files_below_threshold(self) -> list[FileCoverage]:
        """Files whose ADVISORY coverage is strictly below :attr:`file_threshold`.

        Uses the branch-inclusive :attr:`FileCoverage.percent_covered` (the
        advisory display basis). The enforcing gate uses
        :meth:`files_below_statement_threshold` instead.
        """
        return [f for f in self.files if f.percent_covered < self.file_threshold]

    def submodules_below_bar(self) -> list[SubmoduleCoverage]:
        """Sub-modules whose mean-of-files average is strictly below :attr:`submodule_bar`.

        Uses the advisory mean-of-files :attr:`SubmoduleCoverage.average_percent`.
        The enforcing gate uses :meth:`submodules_below_pooled_bar` instead.
        """
        return [s for s in self.submodules if s.below_bar(self.submodule_bar)]

    def files_below_statement_threshold(self, threshold: float = DEFAULT_FILE_THRESHOLD) -> list[FileCoverage]:
        """Files whose STATEMENT coverage is strictly below ``threshold`` (enforcing basis).

        The enforcing per-file check (work-unit C-0): gates on
        :attr:`FileCoverage.statement_percent` (``covered_statements /
        num_statements``), not the branch-inclusive advisory
        :meth:`files_below_threshold`. ``threshold`` is the enforcing floor
        (the CLI's ``--fail-under-file``), kept independent of the advisory
        :attr:`file_threshold` display cut.
        """
        return [f for f in self.files if f.statement_percent < threshold]

    def submodules_below_pooled_bar(self, bar: float = DEFAULT_SUBMODULE_BAR) -> list[SubmoduleCoverage]:
        """Sub-modules whose POOLED coverage is strictly below ``bar`` (enforcing basis).

        The enforcing per-sub-module check (work-unit C-0): gates on the
        statement-weighted :attr:`SubmoduleCoverage.pooled_percent`, not the
        mean-of-files advisory :meth:`submodules_below_bar`. ``bar`` is the
        enforcing bar (the CLI's ``--fail-under-submodule``), kept independent
        of the advisory :attr:`submodule_bar` display bar.
        """
        return [s for s in self.submodules if s.below_pooled_bar(bar)]

    def distribution(self) -> dict[str, int]:
        """Histogram of per-file coverage percentages (ordered, all buckets)."""
        counts = {label: 0 for label, _lo, _hi in _DISTRIBUTION_BUCKETS}
        for file_cov in self.files:
            counts[_bucket_label(file_cov.percent_covered)] += 1
        return counts

    def to_dict(self) -> dict:
        """Full machine-readable mapping for the ``--json`` reporter."""
        return {
            "overall_percent": self.overall_percent,
            "file_threshold": self.file_threshold,
            "submodule_bar": self.submodule_bar,
            "num_files": len(self.files),
            "distribution": self.distribution(),
            "files": [f.to_dict() for f in self.files],
            "files_below_threshold": [f.to_dict() for f in self.files_below_threshold()],
            "submodules": [s.to_dict(self.submodule_bar) for s in self.submodules],
            "submodules_below_bar": [s.name for s in self.submodules_below_bar()],
        }

    def render(self) -> str:
        """Human-readable advisory report (never raises; always exit-0 caller)."""
        lines: list[str] = []
        lines.append("Coverage gap map (ADVISORY -- exit 0 regardless of findings)")
        lines.append(f"  overall: {self.overall_percent:.2f}%  files: {len(self.files)}  file-threshold: {self.file_threshold:.1f}%  submodule-bar: {self.submodule_bar:.1f}%")
        lines.append("")
        lines.append("Per-file distribution:")
        for label, _lo, _hi in _DISTRIBUTION_BUCKETS:
            lines.append(f"  {label:>9}: {self.distribution()[label]}")
        lines.append("")
        below = self.files_below_threshold()
        if below:
            lines.append(f"Files below {self.file_threshold:.1f}% ({len(below)}):")
            for file_cov in below:
                lines.append(f"  {file_cov.percent_covered:6.2f}%  {file_cov.path}  ({file_cov.covered_statements}/{file_cov.num_statements})")
        else:
            lines.append(f"Files below {self.file_threshold:.1f}%: none")
        lines.append("")
        lines.append(f"Sub-module averages (bar {self.submodule_bar:.1f}%):")
        for submodule in self.submodules:
            flag = "UNDER" if submodule.below_bar(self.submodule_bar) else "ok"
            lines.append(f"  [{flag:>5}] {submodule.average_percent:6.2f}% avg  {submodule.pooled_percent:6.2f}% pooled  {submodule.name}  ({submodule.num_files} files)")
        return "\n".join(lines)


def parse_coverage_json(data: dict, *, file_threshold: float = DEFAULT_FILE_THRESHOLD, submodule_bar: float = DEFAULT_SUBMODULE_BAR, omit: Optional[Sequence[str]] = None) -> CoverageReport:
    """Parse a loaded ``coverage json`` mapping into a :class:`CoverageReport`.

    This is the **primary, fixture-testable** entry point. ``data`` is the
    structure coverage.py writes for ``coverage json`` / pytest-cov
    ``--cov-report=json``: a ``"files"`` mapping of path -> ``{"summary":
    {...}}`` and an optional ``"totals"`` summary. For ergonomic fixtures a
    file entry may also be a flat summary dict (no ``"summary"`` wrapper).

    Args:
        data: The loaded coverage-json mapping.
        file_threshold: Percentage below which a file is reported as a gap.
        submodule_bar: Percentage a sub-module average must reach.
        omit: Optional ``fnmatch`` globs; any file whose path matches one is
            dropped from the parsed report **before** aggregation, distribution,
            and gating. The tool is the single source of truth for what counts
            (it does not trust coverage's own ``[report] omit``). When any
            ``omit`` is given the overall figure is recomputed from the retained
            files rather than trusting the (unfiltered) ``totals``.

    Returns:
        A :class:`CoverageReport`. Files are sorted by path for stable output.
    """
    files_raw = data.get("files", {})
    files: list[FileCoverage] = []
    for path, entry in sorted(files_raw.items()):
        summary = entry.get("summary", entry) if isinstance(entry, dict) else {}
        num_statements = int(summary.get("num_statements", 0))
        covered = int(summary.get("covered_lines", summary.get("covered_statements", 0)))
        missing = int(summary.get("missing_lines", max(num_statements - covered, 0)))
        if "percent_covered" in summary:
            percent = float(summary["percent_covered"])
        else:
            percent = _safe_percent(covered, num_statements)
        files.append(
            FileCoverage(
                path=path.replace("\\", "/"),
                num_statements=num_statements,
                covered_statements=covered,
                missing_statements=missing,
                percent_covered=_round2(percent),
            )
        )

    # Apply --omit exclusions to the PARSED report, before aggregation/gating.
    if omit:
        files = [f for f in files if not _matches_any(f.path, omit)]

    submodules = _aggregate_submodules(files)

    totals = data.get("totals", {})
    # Trust coverage's own totals only when nothing was omitted; an omit makes
    # the file-level totals stale, so recompute the pooled overall from the
    # retained files.
    if not omit and isinstance(totals, dict) and "percent_covered" in totals:
        overall = float(totals["percent_covered"])
    else:
        total_statements = sum(f.num_statements for f in files)
        total_covered = sum(f.covered_statements for f in files)
        overall = _safe_percent(total_covered, total_statements)

    return CoverageReport(
        files=tuple(files),
        submodules=tuple(submodules),
        overall_percent=_round2(overall),
        file_threshold=float(file_threshold),
        submodule_bar=float(submodule_bar),
    )


def _aggregate_submodules(files: Sequence[FileCoverage]) -> list[SubmoduleCoverage]:
    """Group files by sub-module and compute mean + pooled coverage."""
    groups: dict[str, list[FileCoverage]] = {}
    for file_cov in files:
        groups.setdefault(file_cov.submodule, []).append(file_cov)

    submodules: list[SubmoduleCoverage] = []
    for name in sorted(groups):
        group = groups[name]
        total_statements = sum(f.num_statements for f in group)
        covered = sum(f.covered_statements for f in group)
        average = sum(f.percent_covered for f in group) / len(group)
        pooled = _safe_percent(covered, total_statements)
        submodules.append(
            SubmoduleCoverage(
                name=name,
                num_files=len(group),
                total_statements=total_statements,
                covered_statements=covered,
                average_percent=_round2(average),
                pooled_percent=_round2(pooled),
            )
        )
    return submodules


def load_coverage_json(path: Path, *, file_threshold: float = DEFAULT_FILE_THRESHOLD, submodule_bar: float = DEFAULT_SUBMODULE_BAR, omit: Optional[Sequence[str]] = None) -> CoverageReport:
    """Read a ``coverage.json`` file from disk and parse it.

    Args:
        path: The ``coverage.json`` to read.
        file_threshold: Forwarded to :func:`parse_coverage_json`.
        submodule_bar: Forwarded to :func:`parse_coverage_json`.
        omit: Forwarded to :func:`parse_coverage_json` (``fnmatch`` exclusion
            globs applied to the parsed report before aggregation/gating).

    Raises:
        FileNotFoundError: When ``path`` does not exist.
        json.JSONDecodeError: When the file is not valid JSON.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return parse_coverage_json(data, file_threshold=file_threshold, submodule_bar=submodule_bar, omit=omit)


def package_cov_pytest_args(package: str, *, json_path: str = "coverage.json", cov_config: Optional[str] = None, fail_under: Optional[float] = None, term_missing: bool = True) -> list[str]:
    """Build pytest-cov arguments using the numpy-2.x-safe **package-form** ``--cov``.

    numpy-2.x gotcha (documented; hit 2026-06-25, juniper-recurrence #70).
    pytest-cov's dotted ``--cov=pkg.submodule`` form imports the dotted target
    at startup to resolve its filesystem path. When that submodule
    (transitively) imports numpy 2.x, the early/partial import collides with
    numpy 2.x's stricter single-initialisation guard on ``_multiarray_umath``
    and aborts *collection* with::

        ImportError: cannot load module more than once per process

    It reproduced in both a conda env and a clean venv (numpy 2.5.0), with an
    empty ``PYTHONPATH`` -- it is the dotted ``--cov`` form itself, not an
    env/path leak, and ``COVERAGE_CORE=sysmon`` does not fix it. The robust
    workaround is to measure with the **package-form** ``--cov=<package>`` (the
    same form the green base job already proves safe) and to **scope the
    report** to specific modules through a ``[report] include=`` coverage
    config (see :func:`write_include_coverage_config`) -- never a dotted
    ``--cov`` target.

    This helper enforces that contract: it refuses a dotted ``package`` and
    emits ``--cov=<package> --cov-report=json:<json_path>`` plus optional
    ``--cov-config`` / ``--cov-fail-under`` / term-missing report.

    Args:
        package: Top-level importable package name (must not be dotted).
        json_path: Destination for the JSON coverage report.
        cov_config: Optional ``--cov-config`` path (the ``[report] include=``
            scoping config that replaces a dotted ``--cov`` target).
        fail_under: Optional ``--cov-fail-under`` floor. Off by default: the
            mapper is advisory, so the caller normally omits it.
        term_missing: Append a ``term-missing`` report for human runs.

    Raises:
        ValueError: When ``package`` contains a ``.`` (dotted form), the exact
            shape this shim exists to prevent.
    """
    if "." in package:
        raise ValueError(f"package-form --cov requires a top-level package, got dotted {package!r}; scope to a submodule via a [report] include= coverage config instead (numpy-2.x dotted --cov gotcha)")
    args = [f"--cov={package}", f"--cov-report=json:{json_path}"]
    if term_missing:
        args.append("--cov-report=term-missing")
    if cov_config is not None:
        args.append(f"--cov-config={cov_config}")
    if fail_under is not None:
        args.append(f"--cov-fail-under={fail_under}")
    return args


def write_include_coverage_config(path: Path, include: Sequence[str], *, branch: bool = True) -> Path:
    """Write a coverage config that scopes the **report** via ``[report] include=``.

    This is the numpy-2.x-safe alternative to a dotted ``--cov`` target (see
    :func:`package_cov_pytest_args`): coverage is *measured* with the
    package-form ``--cov=<package>`` and the *report* is narrowed here to the
    ``include`` globs, so a single torch/numpy-importing submodule can be
    gated without the dotted-``--cov`` import collision.

    Args:
        path: Destination config path (passed to pytest as ``--cov-config``).
        include: Report-scoping globs (e.g. ``["*/_readout_mlp.py"]``). When
            empty, no ``include`` stanza is written (report covers the whole
            measured package).
        branch: Enable branch coverage in the generated ``[run]`` section.

    Returns:
        The written config path.
    """
    path = Path(path)
    lines = ["[run]", f"branch = {'true' if branch else 'false'}", "", "[report]"]
    if include:
        lines.append("include =")
        for pattern in include:
            lines.append(f"    {pattern}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_coverage(test_command: Sequence[str], *, repo_root: Path, package: str, json_path: Optional[Path] = None, include: Optional[Sequence[str]] = None, cov_config: Optional[Path] = None, file_threshold: float = DEFAULT_FILE_THRESHOLD, submodule_bar: float = DEFAULT_SUBMODULE_BAR, omit: Optional[Sequence[str]] = None, env: Optional[dict] = None) -> CoverageReport:
    """Run a repo's real pytest command under coverage, then parse the JSON.

    Secondary path (the JSON-parsing path is primary). ``test_command`` must be
    a pytest invocation (e.g. ``["python", "-m", "pytest"]``); this function
    appends the numpy-2.x-safe package-form coverage args from
    :func:`package_cov_pytest_args` and runs it in ``repo_root``.

    Advisory: the spawned test command's own exit code is **not** raised as a
    failure here -- a failing/again-low test run still yields whatever
    coverage.json it produced. The only errors surfaced are structural
    (no coverage.json written, unparseable JSON, dotted ``package``).

    Args:
        test_command: The pytest command to run (already split into argv).
        repo_root: Working directory for the run and default JSON location.
        package: Top-level package to measure (package-form ``--cov``).
        json_path: Where the JSON report is written (default
            ``<repo_root>/coverage.json``).
        include: Optional ``[report] include=`` scoping globs; when given and
            ``cov_config`` is not, a temporary config is generated.
        cov_config: Explicit coverage config path (overrides ``include``).
        file_threshold: Forwarded to :func:`parse_coverage_json`.
        submodule_bar: Forwarded to :func:`parse_coverage_json`.
        omit: Post-parse ``fnmatch`` exclusion globs forwarded to
            :func:`load_coverage_json` / :func:`parse_coverage_json`. Distinct
            from ``include``: ``include`` is a measurement-time ``[report]
            include=`` scoping glob, whereas ``omit`` drops files from the
            already-parsed report before aggregation/gating.
        env: Optional environment mapping for the subprocess.

    Returns:
        The parsed :class:`CoverageReport`.
    """
    repo_root = Path(repo_root)
    json_path = Path(json_path) if json_path is not None else repo_root / "coverage.json"

    config_path = Path(cov_config) if cov_config is not None else None
    if include and config_path is None:
        config_path = repo_root / ".coveragerc.gapmap"
        write_include_coverage_config(config_path, include)

    cov_args = package_cov_pytest_args(package, json_path=str(json_path), cov_config=str(config_path) if config_path is not None else None)
    command = list(test_command) + cov_args
    subprocess.run(command, cwd=str(repo_root), env=env, check=False)

    return load_coverage_json(json_path, file_threshold=file_threshold, submodule_bar=submodule_bar, omit=omit)


__all__ = [
    "DEFAULT_FILE_THRESHOLD",
    "DEFAULT_SUBMODULE_BAR",
    "FileCoverage",
    "SubmoduleCoverage",
    "CoverageReport",
    "parse_coverage_json",
    "load_coverage_json",
    "package_cov_pytest_args",
    "write_include_coverage_config",
    "run_coverage",
]
