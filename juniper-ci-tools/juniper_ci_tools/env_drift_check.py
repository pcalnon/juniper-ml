"""Environment floor-drift checker — do the ``juniper-*`` distributions installed
in the active environment satisfy the floors a target repo's ``pyproject.toml``
declares (and, optionally, the pins in its ``requirements.lock``)?

This module is the library implementation behind the ``juniper-env-drift-check``
console script. It is the **shared, ecosystem-reusable** form of the
dependency-satisfaction guard described in the test-suite audit plan §10.1
(``notes/JUNIPER_2026-06-26_JUNIPER-ECOSYSTEM_TEST-SUITE-AUDIT-PLAN.md``): any Juniper
repo can ``pip install juniper-ci-tools`` and assert that its active environment
satisfies its declared client floors.

Incident motivating it (2026-06-26)
-----------------------------------

Canopy's unit/CI suite was green while the running app was broken at runtime: the
``JuniperCanopy1`` conda env held ``juniper-data-client==0.4.0`` and
``juniper-cascor-client==0.3.0`` — both *below* the code's ``pyproject.toml``
floors (``>=0.4.1`` / ``>=0.5.0``). The suite stayed green because the clients
are mocked session-wide in ``conftest.py``, so the real (stale) constructor
signatures were never exercised. The breakage lived only at the real-client call
seam, which no test touched.

What it generalizes (and the gap it closes)
-------------------------------------------

It generalizes ``juniper-canopy``'s proven
``src/tests/unit/test_client_version_floors.py`` (which reads installed versions
via :mod:`importlib.metadata` — bypassing any conftest mocks — and compares them
against floors parsed with :mod:`tomllib` + :mod:`packaging`). Two differences
make it the durable, reusable form:

* It is a ``juniper-ci-tools`` console script (not a single repo's test), so
  every service repo can run it in CI + a local preflight (plan §11 D-tool).
* ``--check-lock`` additionally asserts the repo's ``requirements.lock`` pins
  satisfy those floors — catching lock-below-floor drift before an environment is
  built from the lock.

**Plain wheels are covered.** Unlike ``util/editable_install_drift_check.py``
(which inspects only *editable* installs via ``direct_url.json`` and therefore
misses the canopy incident class), this checker reads installed versions through
:mod:`importlib.metadata`, which is install-type-agnostic: a plain wheel and an
editable install both expose a ``*.dist-info`` with ``METADATA`` and are read
identically.

Classification
--------------

Each ``juniper-*`` floor the target repo declares is classified against the
installed environment:

* ``OK``           installed version satisfies the declared specifier.
* ``BELOW_FLOOR``  installed version violates it (the env-drift incident class —
  realistically, a wheel below its ``>=`` floor).
* ``MISSING``      the package is not installed in the scanned environment.

A ``MISSING`` is a soft note by default (an optional client legitimately absent
in a minimal install — canopy's own guard skips it); ``--strict`` promotes it to
a failure. With ``--check-lock`` the lock pins are classified ``OK`` /
``BELOW_FLOOR`` / ``ABSENT`` the same way.

Library API
-----------

::

    from juniper_ci_tools.env_drift_check import (
        check_env_drift,
        DriftResult,
        DriftCheckError,
        parse_floors,
        installed_juniper_versions,
        parse_lock_pins,
    )

    result = check_env_drift(repo_root)            # scans the active interpreter
    if not result.ok:
        for f in result.below_floor:
            print(f"{f.name}=={f.installed} violates {f.name}{f.specifier}")

Exit codes (as surfaced by the console script)
----------------------------------------------

* ``0`` — no ``BELOW_FLOOR`` (and, under ``--strict``, no ``MISSING`` / ``ABSENT``).
* ``1`` — at least one ``BELOW_FLOOR`` (or a ``--strict`` ``MISSING`` / ``ABSENT``).
* ``2`` — invocation error (no ``pyproject.toml``, no ``juniper-*`` floors
  declared, or ``--check-lock`` with no ``requirements.lock``).
"""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 backport (ci-tools requires-python >=3.11)
    import tomli as tomllib  # type: ignore[no-redef]

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

JUNIPER_PREFIX = "juniper-"

# Installed-vs-floor classification.
STATUS_OK = "OK"
STATUS_BELOW = "BELOW_FLOOR"
STATUS_MISSING = "MISSING"

# requirements.lock-vs-floor classification.
LOCK_OK = "OK"
LOCK_BELOW = "BELOW_FLOOR"
LOCK_ABSENT = "ABSENT"

# A ``name[extras]==version`` pin line in a pip-style lockfile. An optional
# ``[extras]`` is tolerated (so ``juniper-x[grpc]==0.4.0`` still matches). The
# version is captured up to the first whitespace / marker / comment, so trailing
# ``\`` line continuations, ``--hash=...`` fragments, and ``; python_version<...``
# markers are all tolerated.
_LOCK_PIN_RE = re.compile(r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*==\s*(?P<version>[^\s;#\\]+)")


class DriftCheckError(Exception):
    """A usage-level failure (maps to console-script exit code 2)."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class FloorFinding:
    """Classification of one declared ``juniper-*`` floor against the env."""

    name: str
    specifier: str
    installed: "str | None"
    status: str  # OK | BELOW_FLOOR | MISSING

    def as_dict(self) -> dict:
        return {"name": self.name, "specifier": self.specifier, "installed": self.installed, "status": self.status}


@dataclass(frozen=True)
class LockFinding:
    """Classification of one declared floor against the repo's lockfile pin."""

    name: str
    specifier: str
    locked: "str | None"
    status: str  # OK | BELOW_FLOOR | ABSENT

    def as_dict(self) -> dict:
        return {"name": self.name, "specifier": self.specifier, "locked": self.locked, "status": self.status}


def _version_lt(a: str, b: str) -> bool:
    """True when version ``a`` sorts strictly below version ``b``.

    Uses :class:`packaging.version.Version`; on an unparseable operand both sides
    fall back to a plain string comparison so the two are never compared across
    types.
    """
    try:
        return Version(a) < Version(b)
    except InvalidVersion:
        return str(a) < str(b)


def _satisfies(spec: SpecifierSet, version: str) -> bool:
    """True when ``version`` satisfies ``spec``.

    An unparseable version is treated as **not** satisfying — fail-safe: a garbage
    version (in the env or the lockfile) is flagged as drift rather than crashing
    the run or being silently accepted. This makes the check robust across
    ``packaging`` releases (older ``contains`` could raise on a bad operand).
    """
    try:
        return spec.contains(version, prereleases=True)
    except InvalidVersion:  # pragma: no cover - packaging>=22 returns False here; net for older packaging
        return False


# ── floor extraction (the target repo's pyproject) ───────────────────────────


def parse_floors(pyproject: Path) -> "dict[str, SpecifierSet]":
    """Return ``{canonical-name: SpecifierSet}`` for every version-floored
    ``juniper-*`` requirement in ``pyproject.toml``.

    Generalizes canopy's ``_juniper_requirements``: requirements are gathered
    from ``[project].dependencies`` and every ``[project.optional-dependencies]``
    group. A requirement is kept only when its canonical name starts with
    ``juniper-``, it is not the project's own name (the meta-package's
    ``[all]`` self-reference), and it carries a version specifier. When a name
    appears in more than one group the specifiers are intersected (so the most
    restrictive floor wins).
    """
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DriftCheckError(f"could not read {pyproject}: {exc}") from exc

    project = data.get("project", {}) if isinstance(data, dict) else {}
    self_name = canonicalize_name(project.get("name", "")) if isinstance(project.get("name"), str) else ""

    deps = project.get("dependencies", [])
    req_strings: list = list(deps) if isinstance(deps, list) else []
    optional = project.get("optional-dependencies", {})
    if isinstance(optional, dict):
        for group in optional.values():
            if isinstance(group, list):
                req_strings.extend(group)

    floors: dict[str, SpecifierSet] = {}
    for raw in req_strings:
        if not isinstance(raw, str):
            continue
        try:
            req = Requirement(raw)
        except InvalidRequirement:
            continue
        name = canonicalize_name(req.name)
        if not name.startswith(JUNIPER_PREFIX):
            continue
        if name == self_name:  # the project's own self-reference (e.g. an [all] extra)
            continue
        if not req.specifier:
            continue
        floors[name] = floors.get(name, SpecifierSet()) & req.specifier
    return floors


# ── installed-version reading (interpreter or explicit site-packages) ─────────


def installed_juniper_versions(
    *,
    paths: "Optional[list[Path]]" = None,
    distributions: "Optional[Callable[..., Iterable]]" = None,
) -> "dict[str, str]":
    """Map canonical ``juniper-*`` distribution name -> the **lowest** installed
    version found, read via :mod:`importlib.metadata` (install-type-agnostic —
    plain wheels and editable installs alike).

    With ``paths`` the lookup scans exactly those ``site-packages`` directories;
    without it, the active interpreter's search path is scanned. ``distributions``
    overrides :func:`importlib.metadata.distributions` for testing.

    When a dist is discoverable at **more than one** version across the scanned
    path (duplicate ``dist-info``: user-site + venv-site, an editable + a wheel
    install of the same package, or a leftover ``dist-info`` from a failed
    upgrade) the **lowest** version is kept. A floor guard must fail safe — if any
    installed copy is below the floor that is drift — and importlib import
    resolution is first-on-path, not highest-version, so keeping the highest could
    hide the very copy that loads at runtime (the 2026-06-26 incident class).
    """
    discover = distributions or importlib_metadata.distributions
    dists = discover(path=[str(p) for p in paths]) if paths is not None else discover()

    found: dict[str, str] = {}
    for dist in dists:
        try:
            raw_name = dist.metadata["Name"]
        except (KeyError, TypeError):  # pragma: no cover - defensive; a dist with no parseable metadata
            raw_name = None
        if not raw_name:
            continue
        name = canonicalize_name(raw_name)
        if not name.startswith(JUNIPER_PREFIX):
            continue
        ver = dist.version
        if not ver:
            continue
        if name not in found or _version_lt(ver, found[name]):
            found[name] = ver
    return found


def classify_floors(floors: "Mapping[str, SpecifierSet]", installed: "Mapping[str, str]") -> "list[FloorFinding]":
    """Classify every declared floor against the installed environment."""
    findings: list[FloorFinding] = []
    for name in sorted(floors):
        spec = floors[name]
        have = installed.get(name)
        if have is None:
            status = STATUS_MISSING
        elif _satisfies(spec, have):
            status = STATUS_OK
        else:
            status = STATUS_BELOW
        findings.append(FloorFinding(name, str(spec), have, status))
    return findings


# ── requirements.lock pins ────────────────────────────────────────────────────


def parse_lock_pins(lock: Path) -> "dict[str, str]":
    """Return ``{canonical-name: version}`` for every ``juniper-*`` ``name==X``
    pin in a pip-style ``requirements.lock`` (comments, ``-r``/``--option``
    lines, hashes, markers, and ``\\`` continuations tolerated)."""
    try:
        text = lock.read_text(encoding="utf-8")
    except OSError as exc:
        raise DriftCheckError(f"could not read {lock}: {exc}") from exc

    pins: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        m = _LOCK_PIN_RE.match(stripped)
        if not m:
            continue
        name = canonicalize_name(m.group("name"))
        if not name.startswith(JUNIPER_PREFIX):
            continue
        pins[name] = m.group("version")
    return pins


def classify_lock(floors: "Mapping[str, SpecifierSet]", lock_pins: "Mapping[str, str]") -> "list[LockFinding]":
    """Classify every declared floor against the repo's lockfile pins."""
    findings: list[LockFinding] = []
    for name in sorted(floors):
        spec = floors[name]
        locked = lock_pins.get(name)
        if locked is None:
            status = LOCK_ABSENT
        elif _satisfies(spec, locked):
            status = LOCK_OK
        else:
            status = LOCK_BELOW
        findings.append(LockFinding(name, str(spec), locked, status))
    return findings


# ── orchestration + reporting ──────────────────────────────────────────────────


def _count(items: Iterable, attr: str, *keys: str) -> dict:
    counts = {k: 0 for k in keys}
    total = 0
    for item in items:
        total += 1
        value = getattr(item, attr)
        counts[value] = counts.get(value, 0) + 1
    counts["total"] = total
    return counts


@dataclass(frozen=True)
class DriftResult:
    """Aggregate result of an environment floor-drift check."""

    repo_root: Path
    pyproject: Path
    scanned_label: str
    floors: "dict[str, SpecifierSet]"
    findings: "tuple[FloorFinding, ...]"
    strict: bool
    lock_path: "Path | None" = None
    lock_findings: "tuple[LockFinding, ...] | None" = None

    @property
    def below_floor(self) -> "tuple[FloorFinding, ...]":
        return tuple(f for f in self.findings if f.status == STATUS_BELOW)

    @property
    def missing(self) -> "tuple[FloorFinding, ...]":
        return tuple(f for f in self.findings if f.status == STATUS_MISSING)

    @property
    def lock_below(self) -> "tuple[LockFinding, ...]":
        return tuple(f for f in (self.lock_findings or ()) if f.status == LOCK_BELOW)

    @property
    def lock_absent(self) -> "tuple[LockFinding, ...]":
        return tuple(f for f in (self.lock_findings or ()) if f.status == LOCK_ABSENT)

    @property
    def ok(self) -> bool:
        """True when nothing fails. ``BELOW_FLOOR`` (and ``--check-lock``
        lock-below-floor) always fail; ``MISSING`` / lock-``ABSENT`` fail only
        under ``--strict``."""
        if self.below_floor:
            return False
        if self.lock_below:
            return False
        if self.strict and (self.missing or self.lock_absent):
            return False
        return True

    def floor_summary(self) -> dict:
        return _count(self.findings, "status", STATUS_OK, STATUS_BELOW, STATUS_MISSING)

    def lock_summary(self) -> "dict | None":
        if self.lock_findings is None:
            return None
        return _count(self.lock_findings, "status", LOCK_OK, LOCK_BELOW, LOCK_ABSENT)

    def report(self) -> str:
        lines = [
            "juniper-env-drift-check: environment floor-drift report",
            f"  repo:    {self.repo_root}",
            f"  scanned: {self.scanned_label}",
            "",
        ]
        lines.append(f"  {'PACKAGE':<30} {'FLOOR':<16} {'INSTALLED':<14} STATUS")
        lines.append(f"  {'-' * 30} {'-' * 16} {'-' * 14} {'-' * 12}")
        for f in self.findings:
            lines.append(f"  {f.name:<30} {f.specifier:<16} {(f.installed or '-'):<14} {f.status}")
        fs = self.floor_summary()
        lines.append("")
        lines.append(f"  {fs['total']} floor(s): {fs[STATUS_OK]} OK, {fs[STATUS_BELOW]} BELOW_FLOOR, {fs[STATUS_MISSING]} MISSING")

        if self.lock_findings is not None:
            lines.append("")
            lines.append(f"  requirements.lock: {self.lock_path}")
            lines.append(f"  {'PACKAGE':<30} {'FLOOR':<16} {'LOCKED':<14} STATUS")
            lines.append(f"  {'-' * 30} {'-' * 16} {'-' * 14} {'-' * 12}")
            for f in self.lock_findings:
                lines.append(f"  {f.name:<30} {f.specifier:<16} {(f.locked or '-'):<14} {f.status}")
            ls = self.lock_summary() or {}
            lines.append("")
            lines.append(f"  {ls.get('total', 0)} lock pin(s): {ls.get(LOCK_OK, 0)} OK, {ls.get(LOCK_BELOW, 0)} BELOW_FLOOR, {ls.get(LOCK_ABSENT, 0)} ABSENT")

        lines.append("")
        lines.append(f"  RESULT: {'OK' if self.ok else 'DRIFT'}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        payload: dict = {
            "repo_root": str(self.repo_root),
            "pyproject": str(self.pyproject),
            "scanned": self.scanned_label,
            "strict": self.strict,
            "ok": self.ok,
            "findings": [f.as_dict() for f in self.findings],
            "summary": self.floor_summary(),
            "lock": None,
        }
        if self.lock_findings is not None:
            payload["lock"] = {
                "path": str(self.lock_path),
                "findings": [f.as_dict() for f in self.lock_findings],
                "summary": self.lock_summary(),
            }
        return payload


def check_env_drift(
    repo_root: Path,
    *,
    site_packages: "Optional[list[Path]]" = None,
    check_lock: bool = False,
    lock_path: "Optional[Path]" = None,
    strict: bool = False,
    installed: "Optional[Mapping[str, str]]" = None,
    lock_pins: "Optional[Mapping[str, str]]" = None,
    distributions: "Optional[Callable[..., Iterable]]" = None,
) -> DriftResult:
    """Run the full check for ``repo_root`` and return a :class:`DriftResult`.

    ``installed`` / ``lock_pins`` let callers (and tests) inject the scanned
    state directly; otherwise it is read from the environment / lockfile.

    Raises :class:`DriftCheckError` (exit code 2) when ``pyproject.toml`` is
    absent, declares no ``juniper-*`` floors, or — with ``check_lock`` — when the
    ``requirements.lock`` is absent.
    """
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        raise DriftCheckError(f"no pyproject.toml at {pyproject}")

    floors = parse_floors(pyproject)
    if not floors:
        raise DriftCheckError(f"no version-floored juniper-* requirements declared in {pyproject}")

    injected = installed is not None
    if installed is None:
        installed = installed_juniper_versions(paths=site_packages, distributions=distributions)
    findings = tuple(classify_floors(floors, installed))

    if site_packages:
        scanned_label = "site-packages: " + ", ".join(str(p) for p in site_packages)
    elif injected:
        scanned_label = "injected environment"
    else:
        scanned_label = f"active interpreter ({sys.executable})"

    resolved_lock: "Path | None" = None
    lock_findings: "tuple[LockFinding, ...] | None" = None
    if check_lock:
        resolved_lock = lock_path if lock_path is not None else repo_root / "requirements.lock"
        if not resolved_lock.is_file():
            raise DriftCheckError(f"--check-lock requested but no lockfile at {resolved_lock}")
        if lock_pins is None:
            lock_pins = parse_lock_pins(resolved_lock)
        lock_findings = tuple(classify_lock(floors, lock_pins))

    return DriftResult(
        repo_root=repo_root,
        pyproject=pyproject,
        scanned_label=scanned_label,
        floors=floors,
        findings=findings,
        strict=strict,
        lock_path=resolved_lock,
        lock_findings=lock_findings,
    )


__all__ = [
    "DriftCheckError",
    "DriftResult",
    "FloorFinding",
    "LockFinding",
    "STATUS_OK",
    "STATUS_BELOW",
    "STATUS_MISSING",
    "LOCK_OK",
    "LOCK_BELOW",
    "LOCK_ABSENT",
    "check_env_drift",
    "classify_floors",
    "classify_lock",
    "installed_juniper_versions",
    "parse_floors",
    "parse_lock_pins",
]
