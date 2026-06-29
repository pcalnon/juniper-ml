"""Tests for the environment floor-drift checker.

Covers the library (``env_drift_check``) and the console-script CLI
(``cli_env_drift_check``). Everything is driven by synthetic fixtures —
``*.dist-info/METADATA`` files (read via the real :mod:`importlib.metadata` with
``--site-packages`` / ``paths=``), synthetic ``pyproject.toml`` floors, and a
synthetic ``requirements.lock`` — so no real pip / conda is involved.

The plain-wheel-equals-editable property (the gap this tool closes vs
``util/editable_install_drift_check.py``) is asserted explicitly: a dist-info
*with* an editable ``direct_url.json`` and one *without* are read identically.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from juniper_ci_tools.cli_env_drift_check import main as cli_main
from juniper_ci_tools.env_drift_check import (
    LOCK_ABSENT,
    LOCK_BELOW,
    LOCK_OK,
    STATUS_BELOW,
    STATUS_MISSING,
    STATUS_OK,
    DriftCheckError,
    DriftResult,
    FloorFinding,
    LockFinding,
    _version_lt,
    check_env_drift,
    classify_floors,
    classify_lock,
    installed_juniper_versions,
    parse_floors,
    parse_lock_pins,
)

# ── fixture helpers ───────────────────────────────────────────────────────────


def _make_dist_info(site_dir: Path, name: str, version: str, *, editable: bool = False) -> None:
    """Create ``<name>-<version>.dist-info/METADATA`` (+ an editable
    ``direct_url.json`` when requested) under ``site_dir``."""
    dist_info = site_dir / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n", encoding="utf-8")
    if editable:
        (dist_info / "direct_url.json").write_text(json.dumps({"url": "file:///src/" + name, "dir_info": {"editable": True}}), encoding="utf-8")


def _write_pyproject(tmp: Path, *, name: str = "test-repo", dependencies: "list[str] | None" = None, optional: "dict[str, list[str]] | None" = None) -> Path:
    lines = ["[project]", f'name = "{name}"', 'version = "1.0.0"']
    deps = dependencies or []
    lines.append("dependencies = [")
    for d in deps:
        lines.append(f'    "{d}",')
    lines.append("]")
    if optional:
        lines.append("[project.optional-dependencies]")
        for group, items in optional.items():
            lines.append(f"{group} = [")
            for it in items:
                lines.append(f'    "{it}",')
            lines.append("]")
    pyproject = tmp / "pyproject.toml"
    pyproject.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return pyproject


def _write_lock(tmp: Path, lines: "list[str]") -> Path:
    lock = tmp / "requirements.lock"
    lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lock


class _FakeDist:
    """Minimal stand-in for an importlib.metadata Distribution."""

    def __init__(self, name: "str | None", version: "str | None") -> None:
        self.metadata = {"Name": name} if name is not None else {}
        self.version = version


class _FakeDistributions:
    """Callable stub for ``importlib.metadata.distributions`` accepting ``path=``."""

    def __init__(self, dists: "list[_FakeDist]") -> None:
        self._dists = dists
        self.calls: list = []

    def __call__(self, path=None):  # noqa: ANN001 - mirrors importlib.metadata signature
        self.calls.append(path)
        return list(self._dists)


# ── parse_floors ──────────────────────────────────────────────────────────────


class ParseFloorsTest(unittest.TestCase):
    def test_gathers_floors_from_dependencies_and_extras(self):
        with TemporaryDirectory() as tmp:
            py = _write_pyproject(
                Path(tmp),
                dependencies=["juniper-data-client>=0.4.1", "requests>=2.0"],
                optional={"servers": ["juniper-cascor>=0.5.0"]},
            )
            floors = parse_floors(py)
            self.assertEqual(set(floors), {"juniper-data-client", "juniper-cascor"})
            self.assertTrue(floors["juniper-data-client"].contains("0.4.1", prereleases=True))
            self.assertFalse(floors["juniper-data-client"].contains("0.4.0", prereleases=True))

    def test_skips_non_juniper_and_floorless_and_self(self):
        with TemporaryDirectory() as tmp:
            py = _write_pyproject(
                Path(tmp),
                name="juniper-meta",
                dependencies=["requests>=2.0", "juniper-bare", "juniper-meta>=1.0"],
                optional={"all": ["juniper-meta[servers]"]},
            )
            floors = parse_floors(py)
            # requests filtered (non-juniper); juniper-bare has no specifier;
            # juniper-meta is the self name; the self-extra ref has no specifier.
            self.assertEqual(floors, {})

    def test_intersects_duplicate_names_to_most_restrictive(self):
        with TemporaryDirectory() as tmp:
            py = _write_pyproject(
                Path(tmp),
                dependencies=["juniper-data-client>=0.4.0"],
                optional={"extra": ["juniper-data-client>=0.4.1"]},
            )
            floors = parse_floors(py)
            self.assertFalse(floors["juniper-data-client"].contains("0.4.0", prereleases=True))
            self.assertTrue(floors["juniper-data-client"].contains("0.4.1", prereleases=True))

    def test_skips_unparseable_requirement(self):
        with TemporaryDirectory() as tmp:
            py = _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1", "this is !! not a requirement"])
            floors = parse_floors(py)
            self.assertEqual(set(floors), {"juniper-data-client"})

    def test_skips_non_string_dependency_entry(self):
        # A non-string dependency entry (e.g. a TOML number) must be skipped, not
        # crash the parser.
        with TemporaryDirectory() as tmp:
            py = Path(tmp) / "pyproject.toml"
            py.write_text('[project]\nname = "r"\nversion = "1.0"\ndependencies = [123, "juniper-a>=1.0"]\n', encoding="utf-8")
            self.assertEqual(set(parse_floors(py)), {"juniper-a"})

    def test_tolerates_malformed_optional_dependencies(self):
        # A non-table [project.optional-dependencies] (or a non-list group) must
        # not crash the parser -- floors come from [project].dependencies.
        with TemporaryDirectory() as tmp:
            py = Path(tmp) / "pyproject.toml"
            py.write_text('[project]\nname = "r"\nversion = "1.0"\ndependencies = ["juniper-a>=1.0"]\noptional-dependencies = "oops-not-a-table"\n', encoding="utf-8")
            self.assertEqual(set(parse_floors(py)), {"juniper-a"})

    def test_raises_on_unreadable_pyproject(self):
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope" / "pyproject.toml"
            with self.assertRaises(DriftCheckError):
                parse_floors(missing)


# ── installed_juniper_versions ────────────────────────────────────────────────


class InstalledVersionsTest(unittest.TestCase):
    def test_reads_dist_info_from_explicit_site_packages(self):
        with TemporaryDirectory() as tmp:
            sp = Path(tmp)
            _make_dist_info(sp, "juniper-data-client", "0.4.0")
            _make_dist_info(sp, "requests", "2.31.0")  # non-juniper, ignored
            found = installed_juniper_versions(paths=[sp])
            self.assertEqual(found, {"juniper-data-client": "0.4.0"})

    def test_plain_wheel_and_editable_read_identically(self):
        with TemporaryDirectory() as plain, TemporaryDirectory() as edit:
            _make_dist_info(Path(plain), "juniper-cascor-client", "0.5.0", editable=False)
            _make_dist_info(Path(edit), "juniper-cascor-client", "0.5.0", editable=True)
            self.assertEqual(
                installed_juniper_versions(paths=[Path(plain)]),
                installed_juniper_versions(paths=[Path(edit)]),
            )

    def test_keeps_lowest_version_across_paths_failsafe(self):
        # Fail-safe dedup: when a dist is installed at two versions across path
        # entries (a duplicate dist-info -- e.g. a leftover from a failed upgrade,
        # or an editable + wheel double-install), the LOWEST is kept so a
        # coexisting below-floor copy is never masked. Keeping the highest would
        # re-admit the 2026-06-26 incident (importlib loads first-on-path, not the
        # highest version).
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            _make_dist_info(Path(a), "juniper-data-client", "0.4.0")
            _make_dist_info(Path(b), "juniper-data-client", "0.4.2")
            found = installed_juniper_versions(paths=[Path(a), Path(b)])
            self.assertEqual(found, {"juniper-data-client": "0.4.0"})

    def test_duplicate_install_below_floor_is_drift_not_false_ok(self):
        # End-to-end guard for the false-OK the adversarial review caught: a
        # below-floor copy coexisting with an above-floor copy must classify
        # BELOW_FLOOR (not OK).
        with TemporaryDirectory() as repo, TemporaryDirectory() as a, TemporaryDirectory() as b:
            _write_pyproject(Path(repo), dependencies=["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(a), "juniper-data-client", "0.4.0")
            _make_dist_info(Path(b), "juniper-data-client", "0.4.2")
            result = check_env_drift(Path(repo), site_packages=[Path(a), Path(b)])
            self.assertFalse(result.ok)
            self.assertEqual(result.below_floor[0].installed, "0.4.0")

    def test_default_scan_uses_injected_distributions(self):
        fake = _FakeDistributions([_FakeDist("juniper-data-client", "0.4.1"), _FakeDist("flask", "3.0")])
        found = installed_juniper_versions(distributions=fake)
        self.assertEqual(found, {"juniper-data-client": "0.4.1"})
        self.assertEqual(fake.calls, [None])  # discover() called with no path

    def test_path_scan_uses_injected_distributions(self):
        fake = _FakeDistributions([_FakeDist("juniper-cascor", "0.5.0")])
        found = installed_juniper_versions(paths=[Path("/x")], distributions=fake)
        self.assertEqual(found, {"juniper-cascor": "0.5.0"})
        self.assertEqual(fake.calls, [["/x"]])

    def test_skips_dist_with_no_name_or_version(self):
        fake = _FakeDistributions([_FakeDist(None, "1.0"), _FakeDist("juniper-x", None), _FakeDist("juniper-ok", "1.2.3")])
        found = installed_juniper_versions(distributions=fake)
        self.assertEqual(found, {"juniper-ok": "1.2.3"})


class VersionLtTest(unittest.TestCase):
    def test_semantic_comparison(self):
        self.assertTrue(_version_lt("0.4.0", "0.4.1"))
        self.assertFalse(_version_lt("0.5.0", "0.4.1"))
        self.assertFalse(_version_lt("1.0", "1.0"))

    def test_falls_back_to_string_on_invalid_version(self):
        # An unparseable operand must not raise.
        self.assertTrue(_version_lt("not-a-version", "zzz-also-not"))


# ── classify ───────────────────────────────────────────────────────────────────


class ClassifyTest(unittest.TestCase):
    def test_classify_floors_ok_below_missing(self):
        floors = parse_floors(_write_pyproject(Path(self._tmp()), dependencies=["juniper-a>=1.0", "juniper-b>=2.0", "juniper-c>=3.0"]))
        installed = {"juniper-a": "1.0", "juniper-b": "1.9"}
        by = {f.name: f for f in classify_floors(floors, installed)}
        self.assertEqual(by["juniper-a"].status, STATUS_OK)
        self.assertEqual(by["juniper-b"].status, STATUS_BELOW)
        self.assertEqual(by["juniper-c"].status, STATUS_MISSING)

    def test_classify_lock_ok_below_absent(self):
        floors = parse_floors(_write_pyproject(Path(self._tmp()), dependencies=["juniper-a>=1.0", "juniper-b>=2.0", "juniper-c>=3.0"]))
        lock = {"juniper-a": "1.5", "juniper-b": "1.0"}
        by = {f.name: f for f in classify_lock(floors, lock)}
        self.assertEqual(by["juniper-a"].status, LOCK_OK)
        self.assertEqual(by["juniper-b"].status, LOCK_BELOW)
        self.assertEqual(by["juniper-c"].status, LOCK_ABSENT)

    def test_unparseable_installed_version_is_drift_not_crash(self):
        # _satisfies fail-safe: a garbage installed version must classify
        # BELOW_FLOOR, never raise.
        floors = parse_floors(_write_pyproject(Path(self._tmp()), dependencies=["juniper-a>=1.0"]))
        by = {f.name: f for f in classify_floors(floors, {"juniper-a": "not-a-pep440-version"})}
        self.assertEqual(by["juniper-a"].status, STATUS_BELOW)

    def _tmp(self) -> str:
        d = TemporaryDirectory()
        self.addCleanup(d.cleanup)
        return d.name


# ── parse_lock_pins ────────────────────────────────────────────────────────────


class ParseLockPinsTest(unittest.TestCase):
    def test_parses_pins_and_tolerates_noise(self):
        with TemporaryDirectory() as tmp:
            lock = _write_lock(
                Path(tmp),
                [
                    "# a comment",
                    "-r base.txt",
                    "--hash=sha256:deadbeef",
                    "requests==2.31.0",
                    "juniper-data-client==0.4.1 \\",
                    "juniper-cascor-client==0.5.0 ; python_version >= '3.11'",
                    "juniper-canopy==0.5.0 --hash=sha256:abc123",
                    "juniper-thing>=1.0",  # no '==' pin -> not matched
                    "plain-text-no-version",  # non-pin line -> not matched
                    "juniper-extra[grpc]==0.7.0",  # optional [extras] tolerated
                    "",
                ],
            )
            pins = parse_lock_pins(lock)
            self.assertEqual(pins, {"juniper-data-client": "0.4.1", "juniper-cascor-client": "0.5.0", "juniper-canopy": "0.5.0", "juniper-extra": "0.7.0"})

    def test_raises_on_unreadable_lock(self):
        with self.assertRaises(DriftCheckError):
            parse_lock_pins(Path("/no/such/requirements.lock"))


# ── DriftResult ─────────────────────────────────────────────────────────────────


def _result(findings, *, strict=False, lock_findings=None):
    return DriftResult(
        repo_root=Path("/repo"),
        pyproject=Path("/repo/pyproject.toml"),
        scanned_label="injected environment",
        floors={},
        findings=tuple(findings),
        strict=strict,
        lock_path=Path("/repo/requirements.lock") if lock_findings is not None else None,
        lock_findings=tuple(lock_findings) if lock_findings is not None else None,
    )


class DriftResultTest(unittest.TestCase):
    def test_ok_when_all_satisfied(self):
        r = _result([FloorFinding("juniper-a", ">=1.0", "1.0", STATUS_OK)])
        self.assertTrue(r.ok)

    def test_not_ok_with_below_floor(self):
        r = _result([FloorFinding("juniper-a", ">=2.0", "1.0", STATUS_BELOW)])
        self.assertFalse(r.ok)
        self.assertEqual(len(r.below_floor), 1)

    def test_missing_soft_by_default_strict_fails(self):
        findings = [FloorFinding("juniper-a", ">=1.0", None, STATUS_MISSING)]
        self.assertTrue(_result(findings).ok)
        self.assertFalse(_result(findings, strict=True).ok)

    def test_lock_below_always_fails(self):
        r = _result(
            [FloorFinding("juniper-a", ">=1.0", "1.0", STATUS_OK)],
            lock_findings=[LockFinding("juniper-a", ">=1.0", "0.9", LOCK_BELOW)],
        )
        self.assertFalse(r.ok)
        self.assertEqual(len(r.lock_below), 1)

    def test_lock_absent_soft_by_default_strict_fails(self):
        lf = [LockFinding("juniper-a", ">=1.0", None, LOCK_ABSENT)]
        ok = [FloorFinding("juniper-a", ">=1.0", "1.0", STATUS_OK)]
        self.assertTrue(_result(ok, lock_findings=lf).ok)
        self.assertFalse(_result(ok, strict=True, lock_findings=lf).ok)

    def test_report_lists_every_dist_and_lock_block(self):
        r = _result(
            [FloorFinding("juniper-a", ">=2.0", "1.0", STATUS_BELOW), FloorFinding("juniper-b", ">=1.0", "1.0", STATUS_OK)],
            lock_findings=[LockFinding("juniper-a", ">=2.0", "1.0", LOCK_BELOW)],
        )
        report = r.report()
        self.assertIn("juniper-a", report)
        self.assertIn("juniper-b", report)  # the OK dist is listed too (no truncation)
        self.assertIn("BELOW_FLOOR", report)
        self.assertIn("requirements.lock", report)
        self.assertIn("RESULT: DRIFT", report)

    def test_report_without_lock_says_ok(self):
        r = _result([FloorFinding("juniper-a", ">=1.0", "1.0", STATUS_OK)])
        report = r.report()
        self.assertNotIn("requirements.lock", report)
        self.assertIn("RESULT: OK", report)

    def test_as_dict_shape(self):
        r = _result(
            [FloorFinding("juniper-a", ">=2.0", "1.0", STATUS_BELOW)],
            lock_findings=[LockFinding("juniper-a", ">=2.0", "1.0", LOCK_BELOW)],
        )
        d = r.as_dict()
        self.assertFalse(d["ok"])
        self.assertEqual(d["findings"][0]["status"], STATUS_BELOW)
        self.assertEqual(d["summary"][STATUS_BELOW], 1)
        self.assertEqual(d["lock"]["findings"][0]["status"], LOCK_BELOW)

    def test_as_dict_lock_none_when_not_checked(self):
        r = _result([FloorFinding("juniper-a", ">=1.0", "1.0", STATUS_OK)])
        self.assertIsNone(r.as_dict()["lock"])

    def test_lock_summary_none_without_lock(self):
        r = _result([FloorFinding("juniper-a", ">=1.0", "1.0", STATUS_OK)])
        self.assertIsNone(r.lock_summary())


# ── check_env_drift orchestration ──────────────────────────────────────────────


class CheckEnvDriftTest(unittest.TestCase):
    def test_happy_path_with_injected_installed(self):
        with TemporaryDirectory() as tmp:
            _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1"])
            r = check_env_drift(Path(tmp), installed={"juniper-data-client": "0.4.1"})
            self.assertTrue(r.ok)
            self.assertEqual(r.scanned_label, "injected environment")

    def test_detects_drift_with_injected_installed(self):
        with TemporaryDirectory() as tmp:
            _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1"])
            r = check_env_drift(Path(tmp), installed={"juniper-data-client": "0.4.0"})
            self.assertFalse(r.ok)
            self.assertEqual(r.below_floor[0].name, "juniper-data-client")

    def test_site_packages_label_and_real_scan(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.0")
            r = check_env_drift(Path(tmp), site_packages=[Path(sp)])
            self.assertFalse(r.ok)
            self.assertIn("site-packages", r.scanned_label)

    def test_check_lock_with_injected_pins(self):
        with TemporaryDirectory() as tmp:
            _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1"])
            _write_lock(Path(tmp), ["juniper-data-client==0.4.0"])
            r = check_env_drift(Path(tmp), installed={"juniper-data-client": "0.4.1"}, check_lock=True, lock_pins={"juniper-data-client": "0.4.0"})
            self.assertFalse(r.ok)  # env ok, but lock below floor
            self.assertEqual(r.lock_below[0].name, "juniper-data-client")

    def test_check_lock_reads_lockfile_from_disk(self):
        with TemporaryDirectory() as tmp:
            _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1"])
            _write_lock(Path(tmp), ["juniper-data-client==0.4.1"])
            r = check_env_drift(Path(tmp), installed={"juniper-data-client": "0.4.1"}, check_lock=True)
            self.assertTrue(r.ok)

    def test_raises_when_no_pyproject(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(DriftCheckError) as ctx:
                check_env_drift(Path(tmp))
            self.assertEqual(ctx.exception.exit_code, 2)

    def test_raises_when_no_juniper_floors(self):
        with TemporaryDirectory() as tmp:
            _write_pyproject(Path(tmp), dependencies=["requests>=2.0"])
            with self.assertRaises(DriftCheckError):
                check_env_drift(Path(tmp))

    def test_raises_when_check_lock_but_no_lockfile(self):
        with TemporaryDirectory() as tmp:
            _write_pyproject(Path(tmp), dependencies=["juniper-data-client>=0.4.1"])
            with self.assertRaises(DriftCheckError):
                check_env_drift(Path(tmp), installed={"juniper-data-client": "0.4.1"}, check_lock=True)


# ── CLI (end-to-end via main(argv)) ────────────────────────────────────────────


class CliTest(unittest.TestCase):
    def _run(self, args: "list[str]") -> "tuple[int, str, str]":
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli_main(args)
        return rc, out.getvalue(), err.getvalue()

    def _repo(self, tmp: str, floors: "list[str]") -> Path:
        _write_pyproject(Path(tmp), dependencies=floors)
        return Path(tmp)

    def test_help_exits_zero(self):
        with self.assertRaises(SystemExit) as ctx:
            cli_main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_version_exits_zero(self):
        with self.assertRaises(SystemExit) as ctx:
            cli_main(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_clean_env_exits_zero(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")
            rc, out, _ = self._run(["--repo-root", str(repo), "--site-packages", sp])
            self.assertEqual(rc, 0)
            self.assertIn("RESULT: OK", out)

    def test_drift_exits_one_and_names_dist(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.0")
            rc, out, _ = self._run(["--repo-root", str(repo), "--site-packages", sp])
            self.assertEqual(rc, 1)
            self.assertIn("juniper-data-client", out)
            self.assertIn("0.4.0", out)
            self.assertIn(STATUS_BELOW, out)

    def test_plain_wheel_below_floor_detected_like_editable(self):
        # The gap util/editable_install_drift_check.py misses: a PLAIN wheel
        # below its floor must be flagged exactly as an editable one would be.
        for editable in (False, True):
            with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
                repo = self._repo(tmp, ["juniper-cascor-client>=0.5.0"])
                _make_dist_info(Path(sp), "juniper-cascor-client", "0.3.0", editable=editable)
                rc, out, _ = self._run(["--repo-root", str(repo), "--site-packages", sp])
                self.assertEqual(rc, 1, f"editable={editable}")
                self.assertIn(STATUS_BELOW, out)

    def test_json_output_shape(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.0")
            rc, out, _ = self._run(["--repo-root", str(repo), "--site-packages", sp, "--json"])
            payload = json.loads(out)
            self.assertEqual(rc, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["findings"][0]["name"], "juniper-data-client")
            self.assertEqual(payload["findings"][0]["status"], STATUS_BELOW)
            self.assertIsNone(payload["lock"])

    def test_check_lock_below_exits_one(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")  # env OK
            _write_lock(repo, ["juniper-data-client==0.4.0"])  # lock below floor
            rc, out, _ = self._run(["--repo-root", str(repo), "--site-packages", sp, "--check-lock"])
            self.assertEqual(rc, 1)
            self.assertIn("requirements.lock", out)

    def test_check_lock_consistent_exits_zero(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")
            _write_lock(repo, ["juniper-data-client==0.4.1"])
            rc, _, _ = self._run(["--repo-root", str(repo), "--site-packages", sp, "--check-lock"])
            self.assertEqual(rc, 0)

    def test_lock_file_override(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")
            alt = Path(tmp) / "alt.lock"
            alt.write_text("juniper-data-client==0.4.0\n", encoding="utf-8")
            rc, _, _ = self._run(["--repo-root", str(repo), "--site-packages", sp, "--check-lock", "--lock-file", str(alt)])
            self.assertEqual(rc, 1)

    def test_default_scan_missing_is_soft_strict_fails(self):
        # No --site-packages: scans the active interpreter. The floor targets a
        # package that is certainly absent -> MISSING (soft) -> rc 0; --strict -> 1.
        with TemporaryDirectory() as tmp:
            repo = self._repo(tmp, ["juniper-nonexistent-xyz-pkg>=99.0"])
            rc, out, _ = self._run(["--repo-root", str(repo)])
            self.assertEqual(rc, 0)
            self.assertIn(STATUS_MISSING, out)
            rc_strict, _, _ = self._run(["--repo-root", str(repo), "--strict"])
            self.assertEqual(rc_strict, 1)

    def test_repo_root_not_a_directory_exits_two(self):
        rc, _, err = self._run(["--repo-root", "/nonexistent/path/asdf-xyz"])
        self.assertEqual(rc, 2)
        self.assertIn("not a directory", err)

    def test_no_pyproject_exits_two(self):
        with TemporaryDirectory() as tmp:
            rc, _, err = self._run(["--repo-root", tmp])
            self.assertEqual(rc, 2)
            self.assertIn("pyproject.toml", err)

    def test_no_floors_exits_two(self):
        with TemporaryDirectory() as tmp:
            self._repo(tmp, ["requests>=2.0"])
            rc, _, err = self._run(["--repo-root", tmp])
            self.assertEqual(rc, 2)
            self.assertIn("juniper-", err)

    def test_check_lock_missing_lockfile_exits_two(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as sp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            _make_dist_info(Path(sp), "juniper-data-client", "0.4.1")
            rc, _, err = self._run(["--repo-root", str(repo), "--site-packages", sp, "--check-lock"])
            self.assertEqual(rc, 2)
            self.assertIn("lockfile", err)

    def test_site_packages_none_exist_exits_two(self):
        with TemporaryDirectory() as tmp:
            repo = self._repo(tmp, ["juniper-data-client>=0.4.1"])
            rc, _, err = self._run(["--repo-root", str(repo), "--site-packages", "/no/such/dir-xyz"])
            self.assertEqual(rc, 2)
            self.assertIn("site-packages", err)


if __name__ == "__main__":
    unittest.main()
