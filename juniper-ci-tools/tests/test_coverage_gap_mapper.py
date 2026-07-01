"""Tests for :mod:`juniper_ci_tools.coverage_gap_mapper` and the
:program:`juniper-coverage-gap-map` CLI.

Everything here drives **synthetic ``coverage.json`` fixtures** -- no real
coverage run -- so the suite is deterministic and fast. The run-coverage
secondary path is exercised with a monkeypatched ``subprocess.run`` that
writes a fixture JSON, which also lets us assert the numpy-2.x-safe
package-form ``--cov`` shim is what gets invoked.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import juniper_ci_tools.coverage_gap_mapper as cgm
from juniper_ci_tools.cli_coverage_gap_mapper import main as cli_main
from juniper_ci_tools.coverage_gap_mapper import (
    CoverageReport,
    load_coverage_json,
    package_cov_pytest_args,
    parse_coverage_json,
    write_include_coverage_config,
)


def _cov_json(files: dict, *, totals_percent: float | None = None) -> dict:
    """Build a coverage-json mapping from ``path -> (num_statements, covered)``."""
    out_files = {}
    for path, (num, covered) in files.items():
        pct = 100.0 if num == 0 else 100.0 * covered / num
        out_files[path] = {
            "summary": {
                "num_statements": num,
                "covered_lines": covered,
                "missing_lines": max(num - covered, 0),
                "percent_covered": pct,
            }
        }
    data: dict = {"files": out_files}
    if totals_percent is not None:
        data["totals"] = {"percent_covered": totals_percent}
    return data


# A mixed fixture used by several tests:
#   pkg/a.py     90% (boundary -- not a gap under the strict <90 rule)
#   pkg/b.py     50% (gap)
#   pkg/sub/c.py 100%
#   top.py       25% (gap; groups under the "." root sub-module)
_MIXED = _cov_json(
    {
        "pkg/a.py": (10, 9),
        "pkg/b.py": (10, 5),
        "pkg/sub/c.py": (10, 10),
        "top.py": (4, 1),
    }
)


# --------------------------------------------------------------------------- #
# parse_coverage_json: distribution, <threshold list, sub-module averages
# --------------------------------------------------------------------------- #
def test_per_file_distribution_buckets() -> None:
    report = parse_coverage_json(_MIXED)
    assert report.distribution() == {
        "[0,50)": 1,  # top.py 25%
        "[50,70)": 1,  # b.py 50%
        "[70,80)": 0,
        "[80,90)": 0,
        "[90,95)": 1,  # a.py 90%
        "[95,100]": 1,  # c.py 100%
    }


def test_files_below_threshold_is_strict() -> None:
    report = parse_coverage_json(_MIXED)
    below = [f.path for f in report.files_below_threshold()]
    # a.py is exactly 90.0 -> NOT below (strict <90); b.py and top.py are.
    assert below == ["pkg/b.py", "top.py"]


def test_submodule_average_vs_bar() -> None:
    report = parse_coverage_json(_MIXED)
    by_name = {s.name: s for s in report.submodules}
    assert set(by_name) == {".", "pkg", "pkg/sub"}

    # pkg: mean(90, 50) = 70.0; pooled (9+5)/(10+10) = 70.0; under the 95 bar.
    assert by_name["pkg"].average_percent == 70.0
    assert by_name["pkg"].pooled_percent == 70.0
    assert by_name["pkg"].below_bar(95.0) is True

    # pkg/sub: single 100% file -> meets the bar.
    assert by_name["pkg/sub"].average_percent == 100.0
    assert by_name["pkg/sub"].below_bar(95.0) is False

    # "." root: top.py 25% -> under the bar.
    assert by_name["."].average_percent == 25.0

    under = [s.name for s in report.submodules_below_bar()]
    assert under == [".", "pkg"]


def test_overall_prefers_totals_then_computes() -> None:
    with_totals = parse_coverage_json(_cov_json({"pkg/a.py": (10, 4)}, totals_percent=77.0))
    assert with_totals.overall_percent == 77.0

    # No totals -> pooled over all files: (9+5+10+1)/(10+10+10+4) = 25/34.
    computed = parse_coverage_json(_MIXED)
    assert computed.overall_percent == round(2500 / 34, 2)


def test_zero_statement_file_is_full_coverage() -> None:
    report = parse_coverage_json(_cov_json({"pkg/__init__.py": (0, 0)}))
    assert report.files[0].percent_covered == 100.0
    assert report.files_below_threshold() == []


def test_custom_thresholds_reclassify() -> None:
    # Raise the file threshold to 95 -> a.py (90%) becomes a gap; lower the
    # sub-module bar to 60 -> pkg (70% avg) now meets it.
    report = parse_coverage_json(_MIXED, file_threshold=95.0, submodule_bar=60.0)
    assert "pkg/a.py" in [f.path for f in report.files_below_threshold()]
    by_name = {s.name: s for s in report.submodules}
    assert by_name["pkg"].below_bar(report.submodule_bar) is False


def test_flat_summary_entry_supported() -> None:
    # A fixture entry without the "summary" wrapper still parses.
    flat = {"files": {"pkg/a.py": {"num_statements": 8, "covered_lines": 6}}}
    report = parse_coverage_json(flat)
    assert report.files[0].percent_covered == 75.0
    assert report.files[0].missing_statements == 2


# --------------------------------------------------------------------------- #
# helpers: bucket boundaries + sub-module dirname
# --------------------------------------------------------------------------- #
def test_bucket_label_boundaries() -> None:
    assert cgm._bucket_label(0.0) == "[0,50)"
    assert cgm._bucket_label(49.99) == "[0,50)"
    assert cgm._bucket_label(50.0) == "[50,70)"
    assert cgm._bucket_label(89.99) == "[80,90)"
    assert cgm._bucket_label(90.0) == "[90,95)"
    assert cgm._bucket_label(95.0) == "[95,100]"
    assert cgm._bucket_label(100.0) == "[95,100]"


def test_submodule_of() -> None:
    assert cgm._submodule_of("pkg/sub/mod.py") == "pkg/sub"
    assert cgm._submodule_of("pkg/mod.py") == "pkg"
    assert cgm._submodule_of("mod.py") == "."
    # Windows separators normalise.
    assert cgm._submodule_of("pkg\\sub\\mod.py") == "pkg/sub"


# --------------------------------------------------------------------------- #
# load_coverage_json (file path)
# --------------------------------------------------------------------------- #
def test_load_coverage_json_roundtrip(tmp_path) -> None:
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(_MIXED), encoding="utf-8")
    report = load_coverage_json(path)
    assert isinstance(report, CoverageReport)
    assert len(report.files) == 4


def test_load_missing_file_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_coverage_json(tmp_path / "nope.json")


# --------------------------------------------------------------------------- #
# numpy-2.x dotted --cov shim
# --------------------------------------------------------------------------- #
def test_package_cov_args_use_package_form() -> None:
    args = package_cov_pytest_args("my_pkg", json_path="cov.json", cov_config="cfg", fail_under=90)
    assert "--cov=my_pkg" in args
    assert "--cov-report=json:cov.json" in args
    assert "--cov-report=term-missing" in args
    assert "--cov-config=cfg" in args
    assert "--cov-fail-under=90" in args
    # Crucially: no dotted --cov target anywhere.
    assert not any(a.startswith("--cov=") and "." in a.split("=", 1)[1] for a in args)


def test_package_cov_args_reject_dotted() -> None:
    with pytest.raises(ValueError, match="dotted"):
        package_cov_pytest_args("my_pkg.submodule")


def test_write_include_coverage_config(tmp_path) -> None:
    cfg = write_include_coverage_config(tmp_path / "rc", ["*/_readout_mlp.py", "*/b.py"])
    text = cfg.read_text(encoding="utf-8")
    assert "[run]" in text
    assert "branch = true" in text
    assert "[report]" in text
    assert "include =" in text
    assert "*/_readout_mlp.py" in text
    assert "*/b.py" in text


def test_write_include_coverage_config_no_include(tmp_path) -> None:
    cfg = write_include_coverage_config(tmp_path / "rc", [], branch=False)
    text = cfg.read_text(encoding="utf-8")
    assert "branch = false" in text
    assert "include =" not in text


# --------------------------------------------------------------------------- #
# run_coverage (secondary path) via monkeypatched subprocess
# --------------------------------------------------------------------------- #
def test_run_coverage_uses_package_form_shim(tmp_path, monkeypatch) -> None:
    json_path = tmp_path / "coverage.json"
    captured: dict = {}

    def fake_run(command, cwd=None, env=None, check=False):
        captured["command"] = command
        captured["cwd"] = cwd
        json_path.write_text(json.dumps(_cov_json({"pkg/a.py": (10, 4)})), encoding="utf-8")
        return SimpleNamespace(returncode=1)  # advisory: nonzero is ignored

    monkeypatch.setattr(cgm.subprocess, "run", fake_run)
    report = cgm.run_coverage(["python", "-m", "pytest"], repo_root=tmp_path, package="pkg", json_path=json_path)

    command = captured["command"]
    assert command[:3] == ["python", "-m", "pytest"]
    assert "--cov=pkg" in command
    assert not any(a.startswith("--cov=") and "." in a.split("=", 1)[1] for a in command)
    assert captured["cwd"] == str(tmp_path)
    assert report.files[0].percent_covered == 40.0


def test_run_coverage_generates_include_config(tmp_path, monkeypatch) -> None:
    json_path = tmp_path / "coverage.json"
    captured: dict = {}

    def fake_run(command, cwd=None, env=None, check=False):
        captured["command"] = command
        json_path.write_text(json.dumps(_cov_json({"pkg/a.py": (10, 10)})), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cgm.subprocess, "run", fake_run)
    cgm.run_coverage(["pytest"], repo_root=tmp_path, package="pkg", json_path=json_path, include=["*/a.py"])

    generated = tmp_path / ".coveragerc.gapmap"
    assert generated.exists()
    text = generated.read_text(encoding="utf-8")
    assert "[report]" in text and "include =" in text and "*/a.py" in text
    assert any(a.startswith("--cov-config=") for a in captured["command"])


# --------------------------------------------------------------------------- #
# CLI: exit-code contract + reporters
# --------------------------------------------------------------------------- #
def _write(tmp_path, data) -> str:
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_cli_text_report(tmp_path, capsys) -> None:
    rc = cli_main(["--coverage-json", _write(tmp_path, _MIXED)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Coverage gap map" in out
    assert "pkg/b.py" in out  # a listed gap
    assert "UNDER" in out  # at least one sub-module under the bar
    assert "[90,95)" in out  # a distribution bucket label


def test_cli_json_shape(tmp_path, capsys) -> None:
    rc = cli_main(["--coverage-json", _write(tmp_path, _MIXED), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["file_threshold"] == 90.0
    assert payload["submodule_bar"] == 95.0
    assert payload["num_files"] == 4
    assert set(payload["distribution"]) == {"[0,50)", "[50,70)", "[70,80)", "[80,90)", "[90,95)", "[95,100]"}
    assert [f["path"] for f in payload["files_below_threshold"]] == ["pkg/b.py", "top.py"]
    assert payload["submodules_below_bar"] == [".", "pkg"]
    # Each sub-module dict carries a resolved below_bar flag.
    pkg = next(s for s in payload["submodules"] if s["name"] == "pkg")
    assert pkg["below_bar"] is True


def test_cli_exit_zero_even_with_gaps(tmp_path) -> None:
    # The advisory contract: a 0%-covered file and a far-below-bar sub-module
    # must STILL exit 0.
    data = _cov_json({"pkg/dead.py": (20, 0)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data)])
    assert rc == 0


def test_cli_no_input_is_usage_error(capsys) -> None:
    rc = cli_main([])
    assert rc == 2
    assert "no input" in capsys.readouterr().err


def test_cli_test_command_without_package_is_error(capsys) -> None:
    rc = cli_main(["--test-command", "pytest"])
    assert rc == 2
    assert "--package is required" in capsys.readouterr().err


def test_cli_test_command_happy_path(tmp_path, capsys, monkeypatch) -> None:
    # Drive the secondary --test-command path end-to-end through the CLI with a
    # monkeypatched subprocess that writes the coverage.json run_coverage parses.
    json_path = tmp_path / "coverage.json"

    def fake_run(command, cwd=None, env=None, check=False):
        json_path.write_text(json.dumps(_cov_json({"pkg/a.py": (10, 7)})), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cgm.subprocess, "run", fake_run)
    rc = cli_main(["--repo-root", str(tmp_path), "--package", "pkg", "--test-command", "python -m pytest", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["num_files"] == 1
    assert payload["files"][0]["percent_covered"] == 70.0


def test_cli_missing_file_is_error(tmp_path, capsys) -> None:
    rc = cli_main(["--coverage-json", str(tmp_path / "absent.json")])
    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_cli_malformed_json_is_error(tmp_path, capsys) -> None:
    bad = tmp_path / "coverage.json"
    bad.write_text("{not json", encoding="utf-8")
    rc = cli_main(["--coverage-json", str(bad)])
    assert rc == 2
    assert "malformed" in capsys.readouterr().err


def test_cli_custom_thresholds_flags(tmp_path, capsys) -> None:
    rc = cli_main(["--coverage-json", _write(tmp_path, _MIXED), "--file-threshold", "95", "--submodule-bar", "60", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["file_threshold"] == 95.0
    assert payload["submodule_bar"] == 60.0
    # pkg (70% avg) now clears the lowered 60 bar.
    assert "pkg" not in payload["submodules_below_bar"]


def test_cli_version_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli_main(["--version"])
    assert excinfo.value.code == 0
    assert "juniper-coverage-gap-map" in capsys.readouterr().out


def test_render_reports_no_gaps_when_all_above() -> None:
    report = parse_coverage_json(_cov_json({"pkg/a.py": (10, 10), "pkg/b.py": (10, 10)}))
    text = report.render()
    assert "Files below 90.0%: none" in text


# --------------------------------------------------------------------------- #
# ENFORCING MODE (work-unit C-0): opt-in --enforce blocking gate.
#   * per-file basis = STATEMENT   (covered_statements / num_statements)
#   * sub-module basis = POOLED    (statement-weighted; NOT mean-of-files)
#   * --omit excludes files from the parsed report BEFORE gating
#   * advisory (no --enforce) stays exit 0 always -- default unchanged
# --------------------------------------------------------------------------- #
def _branch_file(num: int, covered: int, percent_covered: float) -> dict:
    """A coverage-json file entry whose branch-inclusive ``percent_covered`` is
    set INDEPENDENTLY of ``covered_lines / num_statements`` -- the shape a repo
    with ``branch = true`` produces, used to prove the statement-vs-branch basis.
    """
    return {"summary": {"num_statements": num, "covered_lines": covered, "missing_lines": max(num - covered, 0), "percent_covered": percent_covered}}


# ---- library-level: the new statement / pooled bases + omit ---- #
def test_statement_percent_is_branch_independent() -> None:
    # A file coverage.py reports at 80% branch-inclusive but 100% on statements.
    data = {"files": {"pkg/a.py": _branch_file(10, 10, 80.0)}}
    report = parse_coverage_json(data)
    file_cov = report.files[0]
    assert file_cov.percent_covered == 80.0  # advisory display (branch-inclusive) unchanged
    assert file_cov.statement_percent == 100.0  # enforcing basis: 10/10


def test_files_below_statement_threshold_uses_statements() -> None:
    data = {"files": {"pkg/branchy.py": _branch_file(10, 10, 70.0), "pkg/real.py": _cov_json({"x": (10, 8)})["files"]["x"]}}
    report = parse_coverage_json(data)
    # Advisory (branch-inclusive) flags branchy.py (70 < 90).
    assert "pkg/branchy.py" in [f.path for f in report.files_below_threshold()]
    # Enforcing (statement) does NOT flag branchy.py (100 statement); it flags
    # real.py (80 statement < 90).
    below = [f.path for f in report.files_below_statement_threshold(90.0)]
    assert below == ["pkg/real.py"]


def test_submodules_below_pooled_bar_uses_pooled_not_mean() -> None:
    # pkg: mean-of-files 97.67 (>=95) but pooled 93.14 (<95) -- the divergence.
    report = parse_coverage_json(_cov_json({"pkg/big.py": (200, 186), "pkg/a.py": (2, 2), "pkg/b.py": (2, 2)}))
    pkg = next(s for s in report.submodules if s.name == "pkg")
    assert pkg.average_percent == 97.67
    assert pkg.pooled_percent == 93.14
    # Advisory mean basis: NOT below the bar.
    assert pkg.below_bar(95.0) is False
    assert [s.name for s in report.submodules_below_bar()] == []
    # Enforcing pooled basis: below the bar.
    assert pkg.below_pooled_bar(95.0) is True
    assert [s.name for s in report.submodules_below_pooled_bar(95.0)] == ["pkg"]


def test_matches_any_glob() -> None:
    assert cgm._matches_any("pkg/__main__.py", ["*/__main__.py"]) is True
    assert cgm._matches_any("pkg/sub/__main__.py", ["*/__main__.py"]) is True
    assert cgm._matches_any("pkg/main.py", ["*/__main__.py"]) is False
    assert cgm._matches_any("pkg/cli.py", ["*/__main__.py", "*/cli.py"]) is True


def test_omit_filters_files_and_recomputes_overall() -> None:
    data = _cov_json({"pkg/main.py": (10, 10), "pkg/__main__.py": (4, 0)}, totals_percent=71.43)
    # Without omit: both files present; overall trusts the (stale) totals.
    full = parse_coverage_json(data)
    assert {f.path for f in full.files} == {"pkg/main.py", "pkg/__main__.py"}
    assert full.overall_percent == 71.43
    # With omit: __main__.py dropped BEFORE aggregation; overall recomputed from
    # the retained file (10/10 = 100), not the stale totals.
    omitted = parse_coverage_json(data, omit=["*/__main__.py"])
    assert {f.path for f in omitted.files} == {"pkg/main.py"}
    assert omitted.overall_percent == 100.0


# ---- CLI: the --enforce exit-code contract ---- #
def test_cli_enforce_clean_exits_zero(tmp_path) -> None:
    data = _cov_json({"pkg/a.py": (10, 10), "pkg/b.py": (10, 10)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data), "--enforce"])
    assert rc == 0


def test_cli_enforce_file_below_statement_exits_one_and_names_it(tmp_path, capsys) -> None:
    # pkg pooled 99.50 (>=95, sub-module PASS) but tiny.py statement 50 (<90).
    data = _cov_json({"pkg/big.py": (1000, 1000), "pkg/tiny.py": (10, 5)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data), "--enforce"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "Enforcing gate: FAIL" in out
    assert "pkg/tiny.py" in out


def test_cli_enforce_file_below_statement_json_isolates_basis(tmp_path, capsys) -> None:
    data = _cov_json({"pkg/big.py": (1000, 1000), "pkg/tiny.py": (10, 5)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data), "--enforce", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    enforcement = payload["enforcement"]
    assert enforcement["passed"] is False
    assert [f["path"] for f in enforcement["files_below"]] == ["pkg/tiny.py"]
    # Sub-module pooled PASSES (99.50) even though mean-of-files (75) does not:
    assert enforcement["submodules_below"] == []
    # ... and the advisory (mean-of-files) view WOULD have flagged pkg -- proving
    # the enforcing gate is on pooled, not mean.
    assert payload["submodules_below_bar"] == ["pkg"]


def test_cli_enforce_submodule_pooled_below_exits_one(tmp_path, capsys) -> None:
    # All files >=90 statement (no per-file failure) but pkg pooled 93.14 (<95).
    data = _cov_json({"pkg/big.py": (200, 186), "pkg/a.py": (2, 2), "pkg/b.py": (2, 2)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data), "--enforce", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    enforcement = payload["enforcement"]
    assert enforcement["files_below"] == []  # per-file statement gate is clean
    assert [s["name"] for s in enforcement["submodules_below"]] == ["pkg"]
    # Advisory mean basis would NOT have flagged pkg (mean 97.67 >= 95).
    assert payload["submodules_below_bar"] == []


def test_cli_enforce_statement_basis_passes_when_branch_below(tmp_path, capsys) -> None:
    # Statement 100 (>=90) but branch-inclusive percent_covered 80 (<90).
    data = {"files": {"pkg/a.py": _branch_file(10, 10, 80.0)}}
    rc = cli_main(["--coverage-json", _write(tmp_path, data), "--enforce", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0  # statement basis: PASS
    assert payload["enforcement"]["passed"] is True
    assert payload["enforcement"]["files_below"] == []
    # The advisory (branch-inclusive) view WOULD flag it -- proving the gate is
    # on statements, not the branch-inclusive display percent.
    assert [f["path"] for f in payload["files_below_threshold"]] == ["pkg/a.py"]


def test_cli_enforce_omit_excludes_offender(tmp_path, capsys) -> None:
    data = _cov_json({"pkg/main.py": (10, 10), "pkg/__main__.py": (4, 0)})
    path = _write(tmp_path, data)
    # Without omit: __main__.py (statement 0) fails the gate.
    assert cli_main(["--coverage-json", path, "--enforce"]) == 1
    capsys.readouterr()
    # With --omit: the shim is dropped before gating -> clean -> exit 0.
    rc = cli_main(["--coverage-json", path, "--enforce", "--omit", "*/__main__.py", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert [f["path"] for f in payload["files"]] == ["pkg/main.py"]
    assert payload["enforcement"]["passed"] is True


def test_cli_enforce_custom_file_threshold(tmp_path) -> None:
    # a.py statement 92, plus a big 100% file so pkg pooled is 99.27 (>=95) --
    # this isolates the per-file threshold from the sub-module pooled gate.
    data = _cov_json({"pkg/a.py": (100, 92), "pkg/big.py": (1000, 1000)})
    path = _write(tmp_path, data)
    # Default --fail-under-file 90: a.py (92) clears it -> exit 0.
    assert cli_main(["--coverage-json", path, "--enforce"]) == 0
    # Raised --fail-under-file 95: a.py (92) now fails; pooled still passes.
    assert cli_main(["--coverage-json", path, "--enforce", "--fail-under-file", "95"]) == 1


def test_cli_enforce_custom_submodule_threshold(tmp_path) -> None:
    # pkg pooled 96, every file >=90 statement -> the per-file gate never fires,
    # so this isolates the --fail-under-submodule bar.
    data = _cov_json({"pkg/a.py": (100, 96)})
    path = _write(tmp_path, data)
    # Default --fail-under-submodule 95: pooled 96 clears it -> exit 0.
    assert cli_main(["--coverage-json", path, "--enforce"]) == 0
    # Raised --fail-under-submodule 97: pooled 96 now fails.
    assert cli_main(["--coverage-json", path, "--enforce", "--fail-under-submodule", "97"]) == 1


def test_cli_advisory_default_exits_zero_and_omits_enforcement_block(tmp_path, capsys) -> None:
    # A 0%-covered file with NO --enforce: exit 0 (advisory contract) and the
    # enforcement verdict block is not printed.
    data = _cov_json({"pkg/dead.py": (20, 0)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Enforcing gate" not in out


def test_cli_advisory_default_json_has_no_enforcement_key(tmp_path, capsys) -> None:
    rc = cli_main(["--coverage-json", _write(tmp_path, _cov_json({"pkg/dead.py": (20, 0)})), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert "enforcement" not in payload


def test_cli_omit_filters_advisory_report(tmp_path, capsys) -> None:
    # --omit without --enforce still filters the report (single source of truth).
    data = _cov_json({"pkg/main.py": (10, 9), "pkg/__main__.py": (4, 0)})
    rc = cli_main(["--coverage-json", _write(tmp_path, data), "--omit", "*/__main__.py", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0  # advisory: exit 0 always
    assert [f["path"] for f in payload["files"]] == ["pkg/main.py"]
