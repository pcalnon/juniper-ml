"""Tests for the :mod:`juniper_ci_tools.cli` module-form / console-script."""

from __future__ import annotations

import pytest

from juniper_ci_tools import __version__
from juniper_ci_tools.cli import main


class TestCliVersion:
    def test_version_flag_prints_and_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(["--version"])
        assert excinfo.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out


class TestCliHelp:
    def test_help_flag_lists_known_options(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        for opt in ["--repo-root", "--conf-dir", "--notes-dir", "--no-conda", "--no-yaml-validation"]:
            assert opt in out


class TestCliExitCodes:
    def test_happy_path_returns_zero(self, temp_repo, fake_pip, fake_conda, capsys):
        fake_pip("pkg==1.0\n", "26.1.1")
        fake_conda("dependencies:\n  - python\n")
        rc = main(["--repo-root", str(temp_repo)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Generate Dependency Documentation" in out
        assert "Generated:" in out

    def test_invalid_yaml_returns_one(self, temp_repo, fake_pip, fake_conda, capsys):
        fake_pip("pkg==1.0\n", "26.1.1")
        fake_conda("dependencies:\n  : : : nope\n")
        rc = main(["--repo-root", str(temp_repo)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "ERROR" in err

    def test_missing_pyproject_returns_one(self, tmp_path, capsys):
        rc = main(["--repo-root", str(tmp_path)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "pyproject.toml" in err


class TestCliFlags:
    def test_no_conda_flag_skips_conda_generation(self, temp_repo, fake_pip, fake_conda, capsys):
        fake_pip("pkg==1.0\n", "26.1.1")
        fake_conda("dependencies:\n  - python\n")
        rc = main(["--repo-root", str(temp_repo), "--no-conda"])
        assert rc == 0
        # The conda file must not have been written
        assert not (temp_repo / "conf" / "conda_environment_ci.yaml").exists()
        # But pip still must
        assert (temp_repo / "conf" / "requirements_ci.txt").is_file()

    def test_no_yaml_validation_lets_unsafe_output_pass(self, temp_repo, fake_pip, fake_conda):
        fake_pip("pkg==1.0\n", "26.1.1")
        fake_conda("dependencies:\n  : nope\n")
        # Without validation this should be rc=0 even though the YAML is iffy;
        # the file gets written either way.
        rc = main(["--repo-root", str(temp_repo), "--no-yaml-validation"])
        assert rc == 0
        assert (temp_repo / "conf" / "conda_environment_ci.yaml").is_file()
