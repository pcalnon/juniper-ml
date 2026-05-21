"""Tests for :mod:`juniper_ci_tools.generate_dep_docs`."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from juniper_ci_tools.generate_dep_docs import (
    GenerateDepDocsError,
    PyprojectError,
    YamlValidationError,
    _extract_conda_dependency_block,
    generate_dep_docs,
    render_header,
)


# ── Critical regression: the 2026-05-20 awk fix (cascor#276) ──────────────────


class TestCondaDependencyExtractionAwkFix:
    """Regression coverage for the cascor 2026-05-20 sed->awk fix.

    The old sed pipeline emitted the next top-level key (`prefix:` / `variables:`)
    as the range terminator, which broke YAML validation. The awk form is
    end-exclusive. These tests pin that behavior.
    """

    def test_trailing_prefix_key_is_excluded(self):
        env_export = textwrap.dedent(
            """\
            name: my-env
            channels:
              - conda-forge
            dependencies:
              - python=3.12
              - numpy=1.26
              - pip:
                - juniper-ml
            prefix: /opt/miniforge3/envs/my-env
            """
        )
        block = _extract_conda_dependency_block(env_export)
        assert "prefix:" not in block
        assert "  - python=3.12" in block
        assert "  - juniper-ml" in block

    def test_trailing_variables_key_is_excluded(self):
        # variables: is the other terminator setup-miniconda may emit
        env_export = textwrap.dedent(
            """\
            name: my-env
            dependencies:
              - python=3.13
              - pyyaml=6.0
            variables:
              CUDA_HOME: /usr/local/cuda
            prefix: /opt/miniforge3/envs/my-env
            """
        )
        block = _extract_conda_dependency_block(env_export)
        assert "variables:" not in block
        assert "prefix:" not in block
        assert "  - python=3.13" in block

    def test_uppercase_top_level_key_terminates(self):
        # The awk pattern is /^[a-zA-Z]/ — uppercase counts as a terminator.
        env_export = textwrap.dedent(
            """\
            dependencies:
              - python=3.14
            Prefix: /weird/casing
            """
        )
        block = _extract_conda_dependency_block(env_export)
        assert "Prefix:" not in block
        assert "  - python=3.14" in block

    def test_no_terminator_collects_to_eof(self):
        # If conda only emits dependencies and nothing follows, collect them all
        env_export = textwrap.dedent(
            """\
            dependencies:
              - python=3.12
              - numpy=1.26
            """
        )
        block = _extract_conda_dependency_block(env_export)
        assert "  - python=3.12" in block
        assert "  - numpy=1.26" in block

    def test_indented_subkeys_under_pip_are_preserved(self):
        # `- pip:` and its nested entries are indented (start with whitespace
        # in column 0), so the awk pattern must NOT terminate on them.
        env_export = textwrap.dedent(
            """\
            dependencies:
              - python=3.12
              - pip:
                - juniper-data-client>=0.4.0
                - juniper-cascor-client>=0.3.0
              - numpy
            prefix: /opt/miniforge3/envs/x
            """
        )
        block = _extract_conda_dependency_block(env_export)
        assert "  - pip:" in block
        assert "    - juniper-data-client>=0.4.0" in block
        assert "    - juniper-cascor-client>=0.3.0" in block
        assert "  - numpy" in block
        assert "prefix:" not in block

    def test_no_dependencies_line_yields_empty(self):
        env_export = "name: empty\nchannels:\n  - conda-forge\n"
        assert _extract_conda_dependency_block(env_export) == ""

    def test_empty_input_yields_empty(self):
        assert _extract_conda_dependency_block("") == ""

    def test_only_dependencies_line_yields_empty(self):
        assert _extract_conda_dependency_block("dependencies:\n") == ""


# ── Header rendering ──────────────────────────────────────────────────────────


class TestRenderHeader:
    def test_substitutes_all_placeholders(self):
        tpl = (
            "Version: <X.Y.Z  Major, Minor, Point Version for Repo>\n"
            "Date: <YYYY-MM-dd for Current date>\n"
            "Year: <YYYY for Current Year>\n"
            "Conda Date: <YYYY.MM.dd for current date>\n"
            "Python: <Python Version>\n"
            "Pip: <Pip Version>\n"
        )
        out = render_header(
            tpl,
            repo_version="9.9.9",
            date="2026-05-20",
            year="2026",
            conda_date="2026.05.20",
            python_version="3.14.0",
            pip_version="26.1.1",
        )
        assert "9.9.9" in out
        assert "2026-05-20" in out
        assert "2026.05.20" in out
        assert "2026" in out
        assert "3.14.0" in out
        assert "26.1.1" in out
        assert "<" not in out  # all placeholders replaced

    def test_handles_repo_specific_version_label(self):
        tpl = "V: <X.Y.Z  Major, Minor, Point Version for juniper-cascor>"
        out = render_header(tpl, repo_version="0.5.0", date="d", year="y", conda_date="c", python_version="p", pip_version="pp")
        assert out == "V: 0.5.0"

    def test_case_insensitive_date_variants(self):
        # historical headers vary between "Current" and "current"
        tpl = "<YYYY-MM-dd for Current date> <YYYY-MM-dd for current date>"
        out = render_header(tpl, repo_version="v", date="D", year="y", conda_date="c", python_version="p", pip_version="pp")
        assert out == "D D"

    def test_unknown_placeholders_left_intact(self):
        tpl = "<Something Else>"
        out = render_header(tpl, repo_version="v", date="d", year="y", conda_date="c", python_version="p", pip_version="pp")
        assert out == "<Something Else>"


# ── End-to-end generate_dep_docs ──────────────────────────────────────────────


class TestGenerateDepDocsHappyPath:
    def test_writes_pip_and_conda_files(self, temp_repo, fake_pip, fake_conda, fixed_now):
        fake_pip("numpy==1.26.0\nrequests==2.32.0\n", "26.1.1")
        fake_conda("name: e\ndependencies:\n  - python=3.12\n  - numpy\nprefix: /opt/env\n")

        result = generate_dep_docs(repo_root=temp_repo, now=fixed_now)

        assert result.pip_file == temp_repo / "conf" / "requirements_ci.txt"
        assert result.conda_file == temp_repo / "conf" / "conda_environment_ci.yaml"
        assert result.yaml_validated is True
        assert result.repo_version == "1.2.3"
        assert result.pip_version == "26.1.1"
        assert result.pip_backup is None
        assert result.conda_backup is None
        assert result.conda_skipped_reason is None

        pip_text = result.pip_file.read_text(encoding="utf-8")
        # Header was rendered, then pip freeze was appended
        assert "1.2.3" in pip_text
        assert "numpy==1.26.0" in pip_text
        assert "requests==2.32.0" in pip_text

        conda_text = result.conda_file.read_text(encoding="utf-8")
        assert "  - python=3.12" in conda_text
        assert "  - numpy" in conda_text
        assert "prefix:" not in conda_text  # awk fix applied
        # Validated as YAML by the function; double-check structurally here
        loaded = yaml.safe_load(conda_text)
        assert isinstance(loaded, dict)
        assert "dependencies" in loaded

    def test_backs_up_existing_files_with_timestamp(self, temp_repo, fake_pip, fake_conda, fixed_now):
        fake_pip("pkg==1.0\n", "24.0")
        fake_conda("dependencies:\n  - python\n")

        # Pre-existing files
        conf = temp_repo / "conf"
        conf.mkdir()
        (conf / "requirements_ci.txt").write_text("OLD PIP\n", encoding="utf-8")
        (conf / "conda_environment_ci.yaml").write_text("dependencies:\n  - old\n", encoding="utf-8")

        result = generate_dep_docs(repo_root=temp_repo, now=fixed_now)

        # Backups should exist with the timestamp infix from fixed_now
        ts = "2026-05-20_14-30-45"
        assert result.pip_backup == conf / "requirements_ci_{}.txt".format(ts)
        assert result.conda_backup == conf / "conda_environment_ci_{}.yaml".format(ts)
        assert result.pip_backup.read_text(encoding="utf-8") == "OLD PIP\n"
        assert result.conda_backup.read_text(encoding="utf-8") == "dependencies:\n  - old\n"


class TestGenerateDepDocsCondaSkipped:
    def test_skips_when_conda_not_on_path(self, temp_repo, fake_pip, no_conda, fixed_now):
        fake_pip("pkg==1.0\n", "24.0")
        result = generate_dep_docs(repo_root=temp_repo, now=fixed_now)
        assert result.conda_file is None
        assert result.yaml_validated is False
        assert result.conda_skipped_reason is not None
        assert "conda" in result.conda_skipped_reason.lower()
        # pip file should still be written
        assert result.pip_file.is_file()

    def test_no_conda_flag_skips_even_with_conda_available(self, temp_repo, fake_pip, fake_conda, fixed_now):
        fake_pip("pkg==1.0\n", "24.0")
        fake_conda("dependencies:\n  - python\n")
        result = generate_dep_docs(repo_root=temp_repo, now=fixed_now, include_conda=False)
        assert result.conda_file is None
        assert result.conda_skipped_reason is None  # not skipped due to missing, but due to flag


class TestGenerateDepDocsValidation:
    def test_invalid_yaml_raises(self, temp_repo, fake_pip, fake_conda, fixed_now, monkeypatch):
        fake_pip("pkg==1.0\n", "24.0")
        # Inject a payload that, after our extraction, will produce invalid YAML.
        # The header ends with `dependencies:` so a content body of `: invalid`
        # creates a malformed key-only mapping.
        fake_conda("dependencies:\n  : : : not valid yaml here\n")
        with pytest.raises(YamlValidationError) as excinfo:
            generate_dep_docs(repo_root=temp_repo, now=fixed_now)
        assert "invalid YAML" in str(excinfo.value)

    def test_no_yaml_validation_flag_allows_skip(self, temp_repo, fake_pip, fake_conda, fixed_now):
        fake_pip("pkg==1.0\n", "24.0")
        fake_conda("dependencies:\n  - python\n")
        result = generate_dep_docs(repo_root=temp_repo, now=fixed_now, validate_yaml=False)
        assert result.conda_file is not None
        assert result.yaml_validated is False


class TestGenerateDepDocsErrors:
    def test_missing_pyproject_raises(self, tmp_path, fake_pip):
        with pytest.raises(PyprojectError):
            generate_dep_docs(repo_root=tmp_path)

    def test_pyproject_without_version_raises(self, tmp_path, fake_pip):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
        with pytest.raises(PyprojectError):
            generate_dep_docs(repo_root=tmp_path)

    def test_pyproject_unparseable_raises(self, tmp_path, fake_pip):
        (tmp_path / "pyproject.toml").write_text("not valid toml = = =\n[", encoding="utf-8")
        with pytest.raises(PyprojectError):
            generate_dep_docs(repo_root=tmp_path)

    def test_generate_dep_docs_error_is_runtime_error(self):
        assert issubclass(GenerateDepDocsError, RuntimeError)


class TestGenerateDepDocsFallbackHeaders:
    def test_missing_pip_header_writes_minimal_fallback(self, tmp_path, fake_pip, no_conda, fixed_now):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.1"\n', encoding="utf-8")
        fake_pip("pkg==1.0\n", "24.0")
        result = generate_dep_docs(repo_root=tmp_path, now=fixed_now)
        text = result.pip_file.read_text(encoding="utf-8")
        assert "# requirements_ci.txt - Generated 2026-05-20" in text
        assert "pkg==1.0" in text
        # The notes telling us a fallback was used
        assert any("PIP_DEPENDENCY_FILE_HEADER" in n for n in result.notes)

    def test_missing_conda_header_writes_minimal_fallback(self, tmp_path, fake_pip, fake_conda, fixed_now):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.1"\n', encoding="utf-8")
        fake_pip("pkg==1.0\n", "24.0")
        fake_conda("dependencies:\n  - python\n")
        result = generate_dep_docs(repo_root=tmp_path, now=fixed_now)
        assert result.conda_file is not None
        text = result.conda_file.read_text(encoding="utf-8")
        assert "# conda_environment_ci.yaml - Generated 2026-05-20" in text
        assert "  - python" in text
        assert any("CONDA_DEPENDENCY_FILE_HEADER" in n for n in result.notes)


class TestGenerateDepDocsCustomization:
    def test_custom_filenames_and_dirs(self, tmp_path, fake_pip, fake_conda, fixed_now):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.1"\n', encoding="utf-8")
        fake_pip("pkg==1.0\n", "24.0")
        fake_conda("dependencies:\n  - python\n")
        result = generate_dep_docs(
            repo_root=tmp_path,
            conf_dir="build",
            pip_filename="reqs.txt",
            conda_filename="env.yaml",
            now=fixed_now,
        )
        assert result.pip_file == tmp_path / "build" / "reqs.txt"
        assert result.conda_file == tmp_path / "build" / "env.yaml"
        assert (tmp_path / "build").is_dir()
