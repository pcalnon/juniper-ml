#!/usr/bin/env python3
"""Regression tests for util/env_floor_drift_check.py (gap I-2 / Phase-1 PR-2).

Builds a SYNTHETIC site-packages directory (``*.dist-info/METADATA`` files) plus a
synthetic target repo (``pyproject.toml`` with juniper-* floors), then asserts the
OK / BELOW_FLOOR / MISSING classification, floor parsing, version comparison, exit
codes, and JSON shape. No real pip / no real conda is invoked -- which is also why
the CI gate is STRUCTURAL: ubuntu CI has no conda environment, so a live env scan
(``--env JuniperCanopy1``) is a documented manual-verify step, not a CI criterion.

``util/`` is not a package, so the module is imported via the house
``sys.path.insert`` idiom (matching tests/test_editable_install_drift_check.py).

Run: python3 -m unittest -v tests/test_env_floor_drift_check.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-06-27
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

UTIL_DIR = Path(__file__).resolve().parents[1] / "util"
sys.path.insert(0, str(UTIL_DIR))

import env_floor_drift_check as mod  # noqa: E402


def write_dist(site_pkgs: Path, dist_name: str, version: str) -> None:
    """Create a <dist>-<ver>.dist-info/METADATA (a plain installed distribution)."""
    dist_info = site_pkgs / f"{dist_name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {dist_name}\nVersion: {version}\n\nbody\n")


_PYPROJECT = """\
[project]
name = "juniper-thing"
dependencies = [
  "juniper-data-client>=0.4.1",
  "juniper-cascor-client>=0.5.0,<0.6.0",
  "requests>=2.0",
]
[project.optional-dependencies]
extra = ["juniper-observability>=0.2.0"]
"""


class FloorParsingTest(unittest.TestCase):
    def test_parse_floor_juniper_with_lower_bound(self) -> None:
        self.assertEqual(mod.parse_floor("juniper-data-client>=0.4.1"), ("juniper-data-client", "0.4.1"))
        # An upper bound does not change the floor.
        self.assertEqual(mod.parse_floor("juniper-doc-tools>=0.1.0,<0.2.0"), ("juniper-doc-tools", "0.1.0"))

    def test_parse_floor_skips_non_juniper_floorless_and_extra_ref(self) -> None:
        self.assertIsNone(mod.parse_floor("requests>=2.0"))  # not juniper
        self.assertIsNone(mod.parse_floor("juniper-cascor"))  # no floor
        self.assertIsNone(mod.parse_floor("juniper-ml[clients,worker]"))  # self extra-ref, no floor

    def test_declared_floors_dedup_keeps_highest(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            py = Path(d) / "pyproject.toml"
            py.write_text('[project]\nname = "juniper-x"\n' "[project.optional-dependencies]\n" 'a = ["juniper-data>=0.5.0"]\n' 'b = ["juniper-data>=0.6.0"]\n')
            floors = mod.declared_floors(py)
            self.assertEqual(floors["juniper-data"], "0.6.0")  # most restrictive wins

    def test_declared_floors_skips_self_package(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            py = Path(d) / "pyproject.toml"
            py.write_text('[project]\nname = "juniper-ml"\n' "[project.optional-dependencies]\n" 'all = ["juniper-ml[clients]"]\n' 'clients = ["juniper-data-client>=0.4.1"]\n')
            floors = mod.declared_floors(py)
            self.assertIn("juniper-data-client", floors)
            self.assertNotIn("juniper-ml", floors)


class VersionCompareTest(unittest.TestCase):
    def test_version_lt_basic_and_multidigit(self) -> None:
        self.assertTrue(mod.version_lt("0.3.0", "0.4.1"))
        self.assertFalse(mod.version_lt("0.4.1", "0.4.1"))
        self.assertFalse(mod.version_lt("0.5.0", "0.4.1"))
        # Numeric, not lexical: 0.10.0 must be greater than 0.9.0.
        self.assertFalse(mod.version_lt("0.10.0", "0.9.0"))
        self.assertTrue(mod.version_lt("0.9.0", "0.10.0"))

    def test_vtuple_fallback_handles_suffixes(self) -> None:
        self.assertEqual(mod._vtuple("0.4.1"), (0, 4, 1))
        self.assertEqual(mod._vtuple("1.2.3.post1"), (1, 2, 3))
        self.assertEqual(mod._vtuple("2.0.0+local"), (2, 0, 0))


class ClassificationCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "pyproject.toml").write_text(_PYPROJECT)
        self.sp = self.root / "sp"
        self.sp.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_main(self, *argv: str) -> "tuple[int, str]":
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = mod.main(["--repo-root", str(self.repo), "--site-packages", str(self.sp), *argv])
        return code, buf.getvalue()

    def test_below_floor_exits_one(self) -> None:
        write_dist(self.sp, "juniper-data-client", "0.3.0")  # < 0.4.1
        write_dist(self.sp, "juniper-cascor-client", "0.5.0")  # == floor -> OK
        write_dist(self.sp, "juniper-observability", "0.3.1")  # > floor -> OK
        code, out = self.run_main("--json")
        payload = json.loads(out)
        by_pkg = {f["package"]: f["status"] for f in payload["findings"]}
        self.assertEqual(by_pkg["juniper-data-client"], mod.STATUS_BELOW)
        self.assertEqual(by_pkg["juniper-cascor-client"], mod.STATUS_OK)
        self.assertEqual(by_pkg["juniper-observability"], mod.STATUS_OK)
        self.assertEqual(code, 1)  # any BELOW_FLOOR -> exit 1

    def test_all_ok_exits_zero(self) -> None:
        write_dist(self.sp, "juniper-data-client", "0.4.1")
        write_dist(self.sp, "juniper-cascor-client", "0.5.2")
        write_dist(self.sp, "juniper-observability", "0.2.0")
        code, _ = self.run_main()
        self.assertEqual(code, 0)

    def test_missing_is_soft_unless_strict(self) -> None:
        # Only one of three floors installed -> two MISSING, none below.
        write_dist(self.sp, "juniper-data-client", "0.4.1")
        code_default, out = self.run_main("--json")
        self.assertEqual(code_default, 0, "MISSING alone is a soft note by default")
        self.assertEqual(json.loads(out)["summary"][mod.STATUS_MISSING], 2)
        code_strict, _ = self.run_main("--strict")
        self.assertEqual(code_strict, 1, "--strict fails on MISSING")

    def test_non_juniper_install_ignored(self) -> None:
        write_dist(self.sp, "requests", "2.31.0")  # not tracked
        write_dist(self.sp, "juniper-data-client", "0.4.1")
        write_dist(self.sp, "juniper-cascor-client", "0.5.0")
        write_dist(self.sp, "juniper-observability", "0.2.0")
        code, out = self.run_main("--json")
        names = {f["package"] for f in json.loads(out)["findings"]}
        self.assertNotIn("requests", names)
        self.assertEqual(code, 0)

    def test_json_shape(self) -> None:
        write_dist(self.sp, "juniper-data-client", "0.4.1")
        _, out = self.run_main("--json")
        payload = json.loads(out)
        self.assertIn("repo_root", payload)
        self.assertIn("scanned", payload)
        self.assertEqual(payload["summary"]["total"], 3)
        self.assertEqual(set(payload["findings"][0]), {"package", "floor", "installed", "status"})


class InvocationErrorTest(unittest.TestCase):
    def run_main(self, *argv: str) -> int:
        buf = io.StringIO()
        with redirect_stdout(buf):
            return mod.main(list(argv))

    def test_exit_two_when_no_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.run_main("--repo-root", d, "--site-packages", d), 2)

    def test_exit_two_when_no_floors(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["requests>=2"]\n')
            self.assertEqual(self.run_main("--repo-root", d, "--site-packages", d), 2)

    def test_exit_two_when_site_packages_missing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["juniper-data>=0.6.0"]\n')
            self.assertEqual(self.run_main("--repo-root", d, "--site-packages", str(Path(d) / "nope")), 2)


class InstalledVersionsTest(unittest.TestCase):
    """Direct coverage for installed_juniper_versions (multi-site / malformed).

    ClassificationCliTest always feeds a single synthetic site-packages dir via
    --site-packages, so the highest-across-dirs and skip-malformed arms never ran.
    """

    def test_keeps_highest_across_site_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sp_old = root / "old"
            sp_new = root / "new"
            sp_old.mkdir()
            sp_new.mkdir()
            write_dist(sp_old, "juniper-data-client", "0.3.0")
            write_dist(sp_new, "juniper-data-client", "0.4.1")
            write_dist(sp_old, "juniper-observability", "0.2.0")
            # Later lower version must not clobber an earlier higher one.
            write_dist(sp_new, "juniper-observability", "0.1.9")

            found = mod.installed_juniper_versions([sp_old, sp_new])

            self.assertEqual(found["juniper-data-client"], "0.4.1")
            self.assertEqual(found["juniper-observability"], "0.2.0")

    def test_skips_malformed_metadata_and_non_juniper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sp = Path(tmp) / "sp"
            sp.mkdir()
            write_dist(sp, "juniper-data-client", "0.4.1")
            write_dist(sp, "requests", "2.31.0")

            # Name present, Version missing -> skip (would poison classify if kept).
            bad = sp / "juniper_cascor_client-0.5.0.dist-info"
            bad.mkdir()
            (bad / "METADATA").write_text("Metadata-Version: 2.1\nName: juniper-cascor-client\n\nbody\n")

            # Unreadable METADATA -> OSError in _read_name_version -> skip.
            # Mock read_text (chmod 000 is a no-op for root in many CI images).
            unread = sp / "juniper_observability-0.2.0.dist-info"
            unread.mkdir()
            meta = unread / "METADATA"
            meta.write_text("Metadata-Version: 2.1\nName: juniper-observability\nVersion: 0.2.0\n\n")
            real_read = Path.read_text

            def _read_text(self: Path, *args, **kwargs):
                if self == meta:
                    raise OSError("permission denied")
                return real_read(self, *args, **kwargs)

            with mock.patch.object(Path, "read_text", _read_text):
                found = mod.installed_juniper_versions([sp])

            self.assertEqual(found, {"juniper-data-client": "0.4.1"})
            self.assertNotIn("juniper-cascor-client", found)
            self.assertNotIn("juniper-observability", found)
            self.assertNotIn("requests", found)

    def test_normalizes_underscore_dist_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sp = Path(tmp) / "sp"
            sp.mkdir()
            write_dist(sp, "juniper_data_client", "0.4.2")
            found = mod.installed_juniper_versions([sp])
            self.assertEqual(found["juniper-data-client"], "0.4.2")


class NoHardcodedEnvNameTest(unittest.TestCase):
    """The I-2 review requirement: the tool must never hardcode an environment name."""

    def test_source_has_no_literal_env_name(self) -> None:
        source = (UTIL_DIR / "env_floor_drift_check.py").read_text(encoding="utf-8")
        for literal in ("JuniperCanopy1", "JuniperCascor1", "JuniperData"):
            self.assertNotIn(literal, source, f"env name '{literal}' must not be hardcoded")


class ResolveSiteDirsTest(unittest.TestCase):
    """Behavioral pins for ``resolve_site_dirs`` env-selection precedence.

    ClassificationCliTest always passes ``--site-packages``, so the ``--env`` and
    ecosystem.yaml ``used_by`` arms (and their exit-2 failure reasons) were never
    exercised. A broken precedence or mapping silently scans the wrong env — or
    exits 2 with a misleading reason — on the operator's host-mode floor check.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "pyproject.toml").write_text('[project]\nname = "juniper-thing"\ndependencies = ["juniper-data-client>=0.4.1"]\n')
        self.conda = self.root / "miniforge3"
        self.conda.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _args(self, *argv: str):
        return mod.parse_args(["--repo-root", str(self.repo), "--conda-dir", str(self.conda), *argv])

    def _stage_env_sp(self, env_name: str, *pythons: str) -> list[Path]:
        dirs: list[Path] = []
        for py in pythons or ("python3.13",):
            sp = self.conda / "envs" / env_name / "lib" / py / "site-packages"
            sp.mkdir(parents=True)
            dirs.append(sp)
        return sorted(dirs)

    def _write_ecosystem(self, mapping: dict[str, str]) -> Path:
        data_dir = self.repo / "prompts" / "agent_templates" / "data"
        data_dir.mkdir(parents=True)
        lines = ["version: 1", "conda_envs:"]
        for env_name, used_by in mapping.items():
            lines.append(f'  {env_name}: {{python: "3.13", used_by: {used_by}}}')
        path = data_dir / "ecosystem.yaml"
        path.write_text("\n".join(lines) + "\n")
        return path

    def test_site_packages_wins_over_env(self) -> None:
        explicit = self.root / "explicit-sp"
        explicit.mkdir()
        self._stage_env_sp("SomeEnv")
        args = self._args("--site-packages", str(explicit), "--env", "SomeEnv")
        dirs, label = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, [explicit])
        self.assertTrue(label.startswith("site-packages:"))
        self.assertIn(str(explicit), label)

    def test_site_packages_missing_returns_empty_with_reason(self) -> None:
        missing = self.root / "nope"
        args = self._args("--site-packages", str(missing))
        dirs, reason = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, [])
        self.assertIn("no --site-packages dir exists", reason)
        self.assertIn(str(missing), reason)

    def test_env_resolves_site_packages_under_conda_dir(self) -> None:
        staged = self._stage_env_sp("EnvA", "python3.13", "python3.14t")
        args = self._args("--env", "EnvA")
        dirs, label = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, staged)
        self.assertEqual(label, "env(s): EnvA")

    def test_env_missing_site_packages_returns_empty(self) -> None:
        (self.conda / "envs").mkdir()
        args = self._args("--env", "GhostEnv")
        dirs, reason = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, [])
        self.assertIn("no site-packages under", reason)
        self.assertIn("GhostEnv", reason)

    def test_ecosystem_used_by_maps_project_name_to_env(self) -> None:
        staged = self._stage_env_sp("MappedEnv")
        self._write_ecosystem({"MappedEnv": "juniper-thing", "OtherEnv": "juniper-other"})
        args = self._args()  # neither --site-packages nor --env
        dirs, label = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, staged)
        self.assertEqual(label, "env 'MappedEnv' (ecosystem.yaml used_by=juniper-thing)")

    def test_ecosystem_missing_mapping_returns_empty(self) -> None:
        self._write_ecosystem({"MappedEnv": "juniper-other"})
        args = self._args()
        dirs, reason = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, [])
        self.assertIn("no conda env maps to 'juniper-thing'", reason)

    def test_ecosystem_mapped_env_without_site_packages_returns_empty(self) -> None:
        self._write_ecosystem({"MappedEnv": "juniper-thing"})
        (self.conda / "envs" / "MappedEnv").mkdir(parents=True)  # env dir, no lib/.../site-packages
        args = self._args()
        dirs, reason = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, [])
        self.assertIn("ecosystem env 'MappedEnv' has no site-packages", reason)

    def test_ecosystem_cannot_read_project_name_returns_empty(self) -> None:
        (self.repo / "pyproject.toml").write_text("# no project table\n")
        self._write_ecosystem({"MappedEnv": "juniper-thing"})
        args = self._args()
        dirs, reason = mod.resolve_site_dirs(args, self.repo)
        self.assertEqual(dirs, [])
        self.assertIn("cannot read [project].name", reason)

    def test_main_exit_two_when_env_unresolvable(self) -> None:
        """CLI surfaces resolve_site_dirs failure as exit 2 (not a silent empty scan)."""
        err = io.StringIO()
        with redirect_stderr(err):
            code = mod.main(
                [
                    "--repo-root",
                    str(self.repo),
                    "--conda-dir",
                    str(self.conda),
                    "--env",
                    "GhostEnv",
                ]
            )
        self.assertEqual(code, 2)
        self.assertIn("no site-packages under", err.getvalue())

    def test_load_ecosystem_envs_maps_used_by(self) -> None:
        path = self._write_ecosystem({"EnvOne": "juniper-alpha", "EnvTwo": "juniper_beta"})
        mapping = mod._load_ecosystem_envs(path)
        self.assertEqual(mapping["juniper-alpha"], "EnvOne")
        self.assertEqual(mapping["juniper-beta"], "EnvTwo")  # underscore normalized

    def test_load_ecosystem_envs_degrades_on_missing_file(self) -> None:
        self.assertEqual(mod._load_ecosystem_envs(self.root / "absent.yaml"), {})


class MalformedOperatorInputGuardTest(unittest.TestCase):
    """A truthy NON-mapping from an operator-authored file must degrade, not raise.

    ``x.get(k) or {}`` guards ABSENCE, not TYPE: a value that is truthy and not a mapping
    passes straight through to the next ``.get()`` / ``.values()`` / ``.items()`` and raises
    ``AttributeError``. Both of this tool's inputs are hand-authored -- a target repo's
    ``pyproject.toml`` and ``prompts/agent_templates/data/ecosystem.yaml`` -- so a list
    where a table belongs is reachable **by typing**, which is the one provenance class
    ``notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md`` §3 names as
    reachable without a version skew.

    The file already believed this -- in ONE place. ``_load_ecosystem_envs`` guards the
    INNER value with ``isinstance(meta, dict)`` while leaving its container bare. That is
    the audit-every-call-site failure ml#1914 fixed in ``run_experiment.py``, recurring in
    a second file.

    ``declared_floors`` is NOT a second precedent, and reading it as one was wrong:
    ``project = data.get("project", {}) if isinstance(data, dict) else {}`` guards ``data``
    -- the parsed document -- and ``_pyproject_data`` returns ``tomllib.load`` (always a
    dict) or ``{}``. The test could never be False. It was a **vacuous guard beside the
    defect**, not evidence against it, and the read one line later crashed on exactly the
    input it appears to screen. Found by adversarial validation, 2026-09-22.

    Reachability is NOT uniform across the three, and the tests do not pretend otherwise:
    the ``ecosystem.yaml`` arm is the operative one -- that file exists in juniper-ml only,
    ``resolve_site_dirs`` falls back to it for every sibling-repo check, nothing else in the
    repo consumes ``conda_envs``, and yamllint checks syntax, not structure. The two
    ``pyproject.toml`` arms are weaker: a sibling's pyproject that malformed would already
    fail ``pip install`` / ``python -m build``, so they are reachable mainly mid-edit or
    against a scratch root. Both are worth pinning; only one is likely.

    ``_load_ecosystem_envs`` is the sharpest of the three because its own docstring states
    the contract it broke -- *"empty on any failure -- PyYAML missing, file absent, or
    malformed; the caller degrades"* -- while its ``except`` catches only
    ``(OSError, yaml.YAMLError)``. An ``AttributeError`` escapes the documented contract and
    reaches the operator as a traceback instead of the exit-2 resolution failure that
    ``docs/REFERENCE.md`` promises.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _toml(self, body: str) -> Path:
        path = self.root / "pyproject.toml"
        path.write_text(body, encoding="utf-8")
        return path

    def _yaml(self, body: str) -> Path:
        path = self.root / "ecosystem.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    # --- the three defects -------------------------------------------------------------

    def test_project_name_degrades_when_project_table_is_an_array(self) -> None:
        """``project = ["x"]`` is valid TOML and yields a list, not a table.

        Pinned at the FUNCTION level deliberately. ``main`` calls ``declared_floors`` before
        ``resolve_site_dirs`` -> ``_project_name``, and both read the same file, so the
        sibling site shadows this one and an end-to-end test would never reach it. A guard
        is still owed here: the shadowing is an ordering accident, not a design.
        """
        path = self._toml('project = ["not-a-table"]\n')
        self.assertIsNone(mod._project_name(path))

    def test_project_name_degrades_when_project_is_a_string(self) -> None:
        path = self._toml('project = "oops"\n')
        self.assertIsNone(mod._project_name(path))

    def test_declared_floors_degrades_when_optional_dependencies_is_an_array(self) -> None:
        """``optional-dependencies`` as an array reached ``.values()``."""
        path = self._toml('[project]\nname = "juniper-thing"\ndependencies = []\noptional-dependencies = ["oops"]\n')
        self.assertEqual(mod.declared_floors(path), {})

    def test_declared_floors_still_reads_dependencies_when_extras_are_malformed(self) -> None:
        """Degrading on a bad ``optional-dependencies`` must not discard the GOOD table.

        A guard that returns ``{}`` for the whole document would pass the test above while
        silently dropping every floor the operator declared correctly -- a false OK from a
        drift checker, which is worse than the crash it replaced.
        """
        path = self._toml('[project]\nname = "juniper-thing"\ndependencies = ["juniper-data-client>=0.4.1"]\noptional-dependencies = ["oops"]\n')
        self.assertEqual(mod.declared_floors(path), {"juniper-data-client": "0.4.1"})

    def test_load_ecosystem_envs_degrades_when_conda_envs_is_a_list(self) -> None:
        """``conda_envs:`` written as a YAML sequence reached ``.items()``.

        The docstring promises empty-on-malformed; this pins that promise.
        """
        path = self._yaml("version: 1\nconda_envs:\n  - JuniperData\n  - JuniperCascor1\n")
        self.assertEqual(mod._load_ecosystem_envs(path), {})

    def test_load_ecosystem_envs_degrades_when_document_is_a_sequence(self) -> None:
        """The whole document, not just ``conda_envs``, can be a sequence.

        ``yaml.safe_load(...) or {}`` did not help: a non-empty list is TRUTHY, so it passed
        the falsy guard and reached ``.get``.
        """
        path = self._yaml("- JuniperData\n- JuniperCascor1\n")
        self.assertEqual(mod._load_ecosystem_envs(path), {})

    def test_load_ecosystem_envs_degrades_on_non_utf8_bytes(self) -> None:
        """``UnicodeDecodeError`` is a ``ValueError``, not an ``OSError``.

        It therefore escaped ``except (OSError, yaml.YAMLError)`` and broke the same
        empty-on-malformed contract by a second route -- the one the first pass missed.
        """
        path = self.root / "ecosystem.yaml"
        path.write_bytes(b"conda_envs:\n  Env\xff\xfe: {used_by: juniper-alpha}\n")
        self.assertEqual(mod._load_ecosystem_envs(path), {})

    def test_load_ecosystem_envs_skips_a_non_string_env_name(self) -> None:
        """A YAML key is not necessarily a string.

        ``NO:`` parses as the boolean ``False`` (the "Norway problem") and ``3:`` as an int.
        Both used to reach ``site_packages_for_env``, where ``conda_dir / "envs" / env_name``
        raises ``TypeError`` on a non-str. The well-formed sibling entry must survive -- a
        guard that drops the whole mapping would hide a working configuration.
        """
        # Joined explicitly rather than written as adjacent literals: black (line length
        # 512) collapses those onto one line, producing implicit string concatenation --
        # the pattern CodeQL flags and that has blocked merges in this repo.
        path = self._yaml(
            "\n".join(
                [
                    "conda_envs:",
                    '  NO: {python: "3.13", used_by: juniper-norway}',
                    '  3: {python: "3.13", used_by: juniper-three}',
                    '  EnvOne: {python: "3.13", used_by: juniper-alpha}',
                ]
            )
            + "\n"
        )
        self.assertEqual(mod._load_ecosystem_envs(path), {"juniper-alpha": "EnvOne"})

    def test_malformed_ecosystem_reaches_the_cli_as_exit_two(self) -> None:
        """The operator-visible contract: exit 2 with a reason, never a traceback.

        ``docs/REFERENCE.md`` and the cheatsheet both document exit 2 as "resolution
        failed". An ``AttributeError`` out of ``_load_ecosystem_envs`` bypassed ``main``'s
        own error handling entirely.
        """
        repo = self.root / "repo"
        (repo / "prompts" / "agent_templates" / "data").mkdir(parents=True)
        (repo / "pyproject.toml").write_text('[project]\nname = "juniper-thing"\ndependencies = ["juniper-data-client>=0.4.1"]\n')
        (repo / "prompts" / "agent_templates" / "data" / "ecosystem.yaml").write_text("version: 1\nconda_envs:\n  - JuniperData\n")
        conda = self.root / "miniforge3"
        conda.mkdir()
        err = io.StringIO()
        with redirect_stderr(err):
            code = mod.main(["--repo-root", str(repo), "--conda-dir", str(conda)])
        self.assertEqual(code, 2)

    # --- negative controls: these pass BEFORE the fix and must keep passing -------------

    def test_wellformed_pyproject_still_reads_its_name(self) -> None:
        path = self._toml('[project]\nname = "juniper-thing"\n')
        self.assertEqual(mod._project_name(path), "juniper-thing")

    def test_wellformed_extras_floors_are_still_collected(self) -> None:
        path = self._toml(_PYPROJECT)
        floors = mod.declared_floors(path)
        self.assertEqual(floors.get("juniper-observability"), "0.2.0")
        self.assertEqual(floors.get("juniper-data-client"), "0.4.1")

    def test_wellformed_ecosystem_still_maps_used_by(self) -> None:
        path = self._yaml('version: 1\nconda_envs:\n  EnvOne: {python: "3.13", used_by: juniper-alpha}\n')
        self.assertEqual(mod._load_ecosystem_envs(path), {"juniper-alpha": "EnvOne"})


if __name__ == "__main__":
    unittest.main()
