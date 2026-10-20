#!/usr/bin/env python3
"""Hermetic gate for util/home_path_literal_check.py (turing bring-up task G5, gate G-PATH).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

Decision D12 of ``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` rewrites
``/home/pcalnon`` literals in scripts, CI and configs to ``$HOME``-derived paths. Gate G-PATH (G5) keeps
a *new* literal from landing meanwhile. Every tracked ``.bash``/``.sh``/``.py``/``.yml`` file under
``util/``, ``scripts/`` and ``.github/`` may hold no more literal lines than
``conf/home_path_literal_baseline.json`` allows it.

How the suite stays hermetic:

- Each case builds a temp git repo and runs the script with ``--root`` pointing at it. Every ``GIT_*``
  variable is scrubbed, the session's ``GIT_CONFIG_COUNT`` signing guard included.
  ``GIT_CONFIG_NOSYSTEM=1``, an isolated ``GIT_CONFIG_GLOBAL`` and a temp ``HOME`` make git behave the
  same here and on Linux CI.
- The baseline is written as literal JSON, never through the script's own renderer.
- Two cases read this checkout: the committed baseline must match it, and the pre-commit hook's
  ``files`` pattern must select exactly the script's scope.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess  # nosec B404 - drives the checker and real git on temp repos
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "home_path_literal_check.py"
BASELINE_REL = "conf/home_path_literal_baseline.json"
TIMEOUT_SECONDS = 120

LITERAL = "/home/pcalnon"
PRAGMA = "home-path-literal: allow"
SCOPE_DIRS = ("util", "scripts", ".github")
SCOPE_SUFFIXES = (".bash", ".sh", ".py", ".yml")

GITCONFIG = "[init]\n\tdefaultBranch = main\n[user]\n\tname = G5 Test\n\temail = g5-test@example.invalid\n[commit]\n\tgpgsign = false\n"


def hermetic_env(home: Path, gitconfig: Path, **overrides: str) -> RedactedEnv:
    """The caller's environment without any GIT_* variable (the session's GIT_CONFIG_COUNT guard included)."""
    env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "GIT"})
    env.update(HOME=str(home), GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(gitconfig), GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1")
    env.update(overrides)
    return env


def load_module():
    spec = importlib.util.spec_from_file_location("home_path_literal_check", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setUpModule() -> None:
    if shutil.which("git") is None:
        raise unittest.SkipTest("git not installed")


class _Fixture(unittest.TestCase):
    """A temp git repo, empty but for what each case writes, and an empty baseline."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        (self.base / "home").mkdir()
        gitconfig = self.base / "gitconfig"
        gitconfig.write_text(GITCONFIG, encoding="utf-8")
        self.env = hermetic_env(self.base / "home", gitconfig)
        self.root = self.base / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.baseline_path = self.root / BASELINE_REL
        self.set_baseline({})

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(self.root), *args], env=self.env, check=True, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def write(self, rel: str, text: str | bytes, *, track: bool = True) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")
        if track:
            self.git("add", "--", rel)
        return path

    def set_baseline(self, files: dict[str, int], **extra: object) -> None:
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        self.baseline_path.write_text(json.dumps({"schema": 1, "files": files, **extra}), encoding="utf-8")

    def run_check(self, *args: str, cwd: Path | None = None, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT_PATH), "--root", str(self.root), *args], cwd=cwd or self.base, env=RedactedEnv(self.env, **env), capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def assert_exit(self, proc: subprocess.CompletedProcess[str], code: int) -> None:
        self.assertEqual(proc.returncode, code, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")

    def failing(self, proc: subprocess.CompletedProcess[str]) -> set[str]:
        return {line.split()[1] for line in proc.stdout.splitlines() if line.startswith("FAIL  ")}

    def noted(self, proc: subprocess.CompletedProcess[str]) -> set[str]:
        return {line.split()[1] for line in proc.stdout.splitlines() if line.startswith("NOTE  ")}


class TestCheck(_Fixture):
    def test_a_clean_tree_passes(self) -> None:
        self.write("util/clean.bash", 'echo "$HOME/Development"\n')
        proc = self.run_check()
        self.assert_exit(proc, 0)
        self.assertIn("summary: PASS", proc.stdout)
        self.assertEqual(proc.stderr, "")

    def test_a_new_literal_fails_and_is_shown(self) -> None:
        self.write("util/new.bash", f"#!/usr/bin/env bash\ncd {LITERAL}/Development\n")
        proc = self.run_check()
        self.assert_exit(proc, 1)
        self.assertEqual(self.failing(proc), {"util/new.bash"})
        self.assertIn("util/new.bash  1 literal lines; the baseline allows 0", proc.stdout)
        self.assertIn(f"util/new.bash:2: cd {LITERAL}/Development", proc.stdout)
        self.assertIn("summary: FAIL -- 1 of 1 files over their baseline", proc.stdout)
        self.assertIn("fix: derive the path from $HOME", proc.stdout)
        self.assertIn(PRAGMA, proc.stdout)
        self.assertIn("--update-baseline", proc.stdout)

    def test_a_count_equal_to_its_baseline_passes(self) -> None:
        self.write("util/old.py", f'A = "{LITERAL}/a"\nB = "{LITERAL}/b"\n')
        self.set_baseline({"util/old.py": 2})
        self.assert_exit(self.run_check(), 0)

    def test_one_line_over_its_baseline_fails_and_lists_every_literal_line(self) -> None:
        self.write("util/old.py", f'A = "{LITERAL}/a"\nB = "{LITERAL}/b"\nok = 1\nC = "{LITERAL}/c"\n')
        self.set_baseline({"util/old.py": 2})
        proc = self.run_check()
        self.assert_exit(proc, 1)
        self.assertIn("util/old.py  3 literal lines; the baseline allows 2", proc.stdout)
        for number in (1, 2, 4):
            self.assertIn(f"util/old.py:{number}: ", proc.stdout)
        self.assertNotIn("util/old.py:3: ", proc.stdout)

    def test_a_line_counts_once_however_many_literals_it_holds(self) -> None:
        self.write("util/twice.bash", f"cp {LITERAL}/a {LITERAL}/b\n")
        self.set_baseline({"util/twice.bash": 1})
        self.assert_exit(self.run_check(), 0)

    def test_a_swapped_literal_line_in_the_same_file_passes(self) -> None:
        self.write("util/old.bash", f"cd {LITERAL}/elsewhere\n")
        self.set_baseline({"util/old.bash": 1})
        self.assert_exit(self.run_check(), 0)

    def test_every_scope_directory_and_suffix_is_checked(self) -> None:
        for directory in SCOPE_DIRS:
            for suffix in SCOPE_SUFFIXES:
                rel = f"{directory}/deep/er/x{suffix}"
                with self.subTest(rel=rel):
                    self.write(rel, f"{LITERAL}\n")
                    proc = self.run_check()
                    self.assert_exit(proc, 1)
                    self.assertEqual(self.failing(proc), {rel})
                    self.git("rm", "-q", "--cached", "--", rel)
                    (self.root / rel).unlink()

    def test_files_outside_the_scope_are_ignored(self) -> None:
        for rel in ("tests/x.py", "docs/x.md", "util/x.md", "util/x.yaml", "util/x.service", "util/x.json", "conf/x.yml", "x.py", "notes/x.sh", "utility/x.py", "util.py", "docs/util/x.py", "tests/scripts/x.bash"):
            self.write(rel, f"{LITERAL}\n")
        self.assert_exit(self.run_check(), 0)

    def test_the_pragma_exempts_its_line(self) -> None:
        self.write("util/needle.py", f'NEEDLE = "{LITERAL}"  # {PRAGMA}\n')
        self.write("util/fixture.bash", f"echo {LITERAL}  # {PRAGMA} -- a fixture\n")
        self.assert_exit(self.run_check(), 0)

    def test_the_pragma_exempts_only_its_own_line(self) -> None:
        self.write("util/needle.py", f'NEEDLE = "{LITERAL}"  # {PRAGMA}\nOTHER = "{LITERAL}/x"\n')
        proc = self.run_check()
        self.assert_exit(proc, 1)
        self.assertIn("util/needle.py  1 literal lines", proc.stdout)
        self.assertIn("util/needle.py:2: ", proc.stdout)

    def test_untracked_files_are_ignored_in_whole_scope_mode(self) -> None:
        self.write("util/scratch.py", f'P = "{LITERAL}"\n', track=False)
        self.assert_exit(self.run_check(), 0)

    def test_a_staged_file_is_checked_in_whole_scope_mode(self) -> None:
        self.write("util/staged.py", f'P = "{LITERAL}"\n')
        self.assertEqual(self.failing(self.run_check()), {"util/staged.py"})

    def test_a_symlink_is_skipped_and_its_target_is_checked(self) -> None:
        self.write("util/real.bash", f"cd {LITERAL}\n")
        (self.root / "util" / "link.bash").symlink_to("real.bash")
        self.git("add", "--", "util/link.bash")
        self.set_baseline({"util/real.bash": 1})
        self.assert_exit(self.run_check(), 0)
        self.set_baseline({})
        self.assertEqual(self.failing(self.run_check()), {"util/real.bash"})

    def test_crlf_and_undecodable_bytes_still_count(self) -> None:
        self.write("util/odd.bash", b"echo ok\r\n\xff\xfe cd " + LITERAL.encode() + b"\r\n")
        proc = self.run_check()
        self.assert_exit(proc, 1)
        self.assertIn("util/odd.bash:2: �� cd " + LITERAL, proc.stdout)

    def test_a_count_below_its_baseline_passes_with_a_note(self) -> None:
        self.write("util/better.py", f'P = "{LITERAL}"\n')
        self.set_baseline({"util/better.py": 3})
        proc = self.run_check()
        self.assert_exit(proc, 0)
        self.assertEqual(self.noted(proc), {"util/better.py"})
        self.assertIn("util/better.py  1 literal lines; the baseline allows 3 -- lower it with --update-baseline", proc.stdout)

    def test_a_baseline_entry_for_a_deleted_file_is_a_note(self) -> None:
        self.set_baseline({"util/gone.py": 1})
        proc = self.run_check()
        self.assert_exit(proc, 0)
        self.assertEqual(self.noted(proc), {"util/gone.py"})

    def test_a_moved_file_does_not_carry_its_count(self) -> None:
        self.write("util/new_home.py", f'P = "{LITERAL}"\n')
        self.set_baseline({"util/old_home.py": 1})
        proc = self.run_check()
        self.assert_exit(proc, 1)
        self.assertEqual(self.failing(proc), {"util/new_home.py"})
        self.assertEqual(self.noted(proc), {"util/old_home.py"})


class TestNamedFiles(_Fixture):
    """The pre-commit hook's form: the staged paths are named on the command line."""

    def test_only_the_named_files_are_checked(self) -> None:
        self.write("util/a.py", f'P = "{LITERAL}"\n')
        self.write("util/b.py", f'P = "{LITERAL}"\n')
        proc = self.run_check("util/a.py", cwd=self.root)
        self.assert_exit(proc, 1)
        self.assertEqual(self.failing(proc), {"util/a.py"})
        self.assertIn("1 of 1 files over their baseline (the named files", proc.stdout)

    def test_an_untracked_named_file_is_checked(self) -> None:
        self.write("util/new.py", f'P = "{LITERAL}"\n', track=False)
        self.assertEqual(self.failing(self.run_check("util/new.py", cwd=self.root)), {"util/new.py"})

    def test_out_of_scope_and_missing_paths_are_ignored(self) -> None:
        self.write("docs/x.md", f"{LITERAL}\n")
        self.write("docs/util/x.py", f'P = "{LITERAL}"\n')
        self.write("util/b.py", f'P = "{LITERAL}"\n')
        proc = self.run_check("docs/x.md", "docs/util/x.py", "util/gone.py", "../outside.py", cwd=self.root)
        self.assert_exit(proc, 0)
        self.assertIn("the named files: 0 files", proc.stdout)

    def test_absolute_and_dot_relative_paths_are_understood(self) -> None:
        self.write("util/a.py", f'P = "{LITERAL}"\n')
        alias = self.base / "alias"
        alias.symlink_to(self.root)
        for arg in (str(self.root / "util" / "a.py"), "./util/a.py", "util/../util/a.py", str(alias / "util" / "a.py")):
            with self.subTest(arg=arg):
                self.assertEqual(self.failing(self.run_check(arg, cwd=self.root)), {"util/a.py"})

    def test_a_path_relative_to_a_subdirectory_is_understood(self) -> None:
        self.write("util/sub/a.py", f'P = "{LITERAL}"\n')
        self.assertEqual(self.failing(self.run_check("a.py", cwd=self.root / "util" / "sub")), {"util/sub/a.py"})

    def test_a_named_file_under_its_baseline_is_a_note_and_others_are_not(self) -> None:
        self.write("util/a.py", "ok = 1\n")
        self.set_baseline({"util/a.py": 1, "util/elsewhere.py": 1})
        proc = self.run_check("util/a.py", cwd=self.root)
        self.assert_exit(proc, 0)
        self.assertEqual(self.noted(proc), {"util/a.py"})

    def test_naming_the_baseline_checks_the_whole_scope(self) -> None:
        self.write("util/a.py", f'P = "{LITERAL}"\n')
        self.write("util/b.py", "ok = 1\n")
        self.assert_exit(self.run_check("util/b.py", cwd=self.root), 0)
        proc = self.run_check(BASELINE_REL, cwd=self.root)
        self.assert_exit(proc, 1)
        self.assertEqual(self.failing(proc), {"util/a.py"})
        self.assertIn("the whole scope", proc.stdout)

    def test_naming_a_custom_baseline_checks_the_whole_scope(self) -> None:
        self.write("util/a.py", f'P = "{LITERAL}"\n')
        custom = self.root / "conf" / "other.json"
        custom.write_text(json.dumps({"schema": 1, "files": {}}), encoding="utf-8")
        proc = self.run_check("--baseline", str(custom), "conf/other.json", cwd=self.root)
        self.assertEqual(self.failing(proc), {"util/a.py"})


class TestEnvironment(_Fixture):
    def test_a_missing_baseline_exits_2(self) -> None:
        self.baseline_path.unlink()
        proc = self.run_check()
        self.assert_exit(proc, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("not found; create it with --update-baseline", proc.stderr)

    def test_a_malformed_baseline_exits_2(self) -> None:
        cases = {
            "not json": "{",
            "a list": "[]",
            "schema 2": json.dumps({"schema": 2, "files": {}}),
            "no files": json.dumps({"schema": 1}),
            "files a list": json.dumps({"schema": 1, "files": []}),
            "a zero count": json.dumps({"schema": 1, "files": {"util/a.py": 0}}),
            "a string count": json.dumps({"schema": 1, "files": {"util/a.py": "1"}}),
            "a boolean count": json.dumps({"schema": 1, "files": {"util/a.py": True}}),
            "a float count": json.dumps({"schema": 1, "files": {"util/a.py": 1.0}}),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                self.baseline_path.write_text(text, encoding="utf-8")
                proc = self.run_check()
                self.assert_exit(proc, 2)
                self.assertIn(str(self.baseline_path), proc.stderr)

    def test_a_root_that_is_not_a_git_checkout_exits_2(self) -> None:
        plain = self.base / "plain"
        (plain / "conf").mkdir(parents=True)
        (plain / BASELINE_REL).write_text(json.dumps({"schema": 1, "files": {}}), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPT_PATH), "--root", str(plain)], cwd=self.base, env=RedactedEnv(self.env, GIT_CEILING_DIRECTORIES=str(self.base)), capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assert_exit(proc, 2)
        self.assertIn("git ls-files failed", proc.stderr)

    def test_a_root_that_is_not_a_directory_exits_2(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT_PATH), "--root", str(self.base / "nowhere")], cwd=self.base, env=self.env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assert_exit(proc, 2)
        self.assertIn("is not a directory", proc.stderr)

    def test_a_missing_git_program_exits_2(self) -> None:
        proc = self.run_check(GIT=str(self.base / "no-such-git"))
        self.assert_exit(proc, 2)
        self.assertIn("cannot run", proc.stderr)

    def test_usage_errors_exit_2(self) -> None:
        for args in (("--dry-run",), ("--update-baseline", "util/a.py"), ("--no-such-flag",)):
            with self.subTest(args=args):
                self.assert_exit(self.run_check(*args), 2)


class TestUpdateBaseline(_Fixture):
    def baseline_files(self) -> dict[str, int]:
        return json.loads(self.baseline_path.read_text(encoding="utf-8"))["files"]

    def populate(self) -> None:
        self.write("util/b.py", f'P = "{LITERAL}"\nQ = "{LITERAL}"\n')
        self.write("scripts/a.bash", f"cd {LITERAL}\n")
        self.write("util/clean.py", "ok = 1\n")
        self.write("util/allowed.py", f'P = "{LITERAL}"  # {PRAGMA}\n')
        self.write("util/untracked.py", f'P = "{LITERAL}"\n', track=False)
        self.write("docs/x.md", f"{LITERAL}\n")

    def test_it_writes_the_count_of_every_tracked_file_in_scope(self) -> None:
        self.populate()
        proc = self.run_check("--update-baseline")
        self.assert_exit(proc, 0)
        doc = json.loads(self.baseline_path.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["files"], {"scripts/a.bash": 1, "util/b.py": 2})
        self.assertEqual(list(doc["files"]), sorted(doc["files"]))
        self.assertIn("scripts/a.bash: 0 -> 1", proc.stdout)
        self.assertIn("baseline: wrote", proc.stdout)
        self.assert_exit(self.run_check(), 0)

    def test_it_keeps_one_entry_per_line(self) -> None:
        self.populate()
        self.run_check("--update-baseline")
        lines = self.baseline_path.read_text(encoding="utf-8").splitlines()
        self.assertIn('    "scripts/a.bash": 1,', lines)
        self.assertIn('    "util/b.py": 2', lines)
        self.assertTrue(self.baseline_path.read_text(encoding="utf-8").endswith("}\n"))

    def test_a_second_run_leaves_the_file_untouched(self) -> None:
        self.populate()
        self.run_check("--update-baseline")
        os.utime(self.baseline_path, ns=(1_000_000_000, 1_000_000_000))
        before = self.baseline_path.read_bytes()
        proc = self.run_check("--update-baseline")
        self.assert_exit(proc, 0)
        self.assertIn("is current", proc.stdout)
        self.assertEqual(self.baseline_path.read_bytes(), before)
        self.assertEqual(self.baseline_path.stat().st_mtime_ns, 1_000_000_000)

    def test_dry_run_writes_nothing(self) -> None:
        self.populate()
        before = self.baseline_path.read_bytes()
        proc = self.run_check("--update-baseline", "--dry-run")
        self.assert_exit(proc, 0)
        self.assertIn("DRY-RUN util/b.py: 0 -> 2", proc.stdout)
        self.assertIn("DRY-RUN: would write", proc.stdout)
        self.assertEqual(self.baseline_path.read_bytes(), before)
        self.baseline_path.unlink()
        self.assert_exit(self.run_check("--update-baseline", "--dry-run"), 0)
        self.assertFalse(self.baseline_path.exists())
        self.assertEqual(sorted(p.name for p in self.baseline_path.parent.iterdir()), [])

    def test_it_lowers_a_count_and_drops_a_deleted_file(self) -> None:
        self.populate()
        self.set_baseline({"util/b.py": 5, "util/gone.py": 1, "scripts/a.bash": 1})
        proc = self.run_check("--update-baseline")
        self.assertIn("util/b.py: 5 -> 2", proc.stdout)
        self.assertIn("util/gone.py: 1 -> 0", proc.stdout)
        self.assertEqual(self.baseline_files(), {"scripts/a.bash": 1, "util/b.py": 2})

    def test_it_creates_a_missing_baseline_and_replaces_a_malformed_one(self) -> None:
        self.populate()
        for setup in ("missing", "malformed"):
            with self.subTest(setup=setup):
                if setup == "missing":
                    self.baseline_path.unlink()
                else:
                    self.baseline_path.write_text("{", encoding="utf-8")
                self.assert_exit(self.run_check("--update-baseline"), 0)
                self.assertEqual(self.baseline_files(), {"scripts/a.bash": 1, "util/b.py": 2})

    def test_the_written_file_is_world_readable(self) -> None:
        self.populate()
        self.run_check("--update-baseline")
        self.assertEqual(self.baseline_path.stat().st_mode & 0o777, 0o644)
        self.assertEqual([p.name for p in self.baseline_path.parent.iterdir()], ["home_path_literal_baseline.json"])


class TestThisCheckout(unittest.TestCase):
    def test_the_committed_baseline_matches_this_checkout(self) -> None:
        env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG")})
        proc = subprocess.run([sys.executable, str(SCRIPT_PATH)], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")

    def test_the_committed_baseline_is_the_rendered_form(self) -> None:
        module = load_module()
        text = (REPO_ROOT / BASELINE_REL).read_text(encoding="utf-8")
        self.assertEqual(module.render_baseline(json.loads(text)["files"]), text)

    def test_the_script_holds_no_literal_line_of_its_own(self) -> None:
        module = load_module()
        self.assertEqual(module.literal_lines(SCRIPT_PATH.read_bytes()), [])
        self.assertEqual((module.NEEDLE, module.PRAGMA), (LITERAL, PRAGMA))

    def test_the_pre_commit_hook_selects_exactly_the_scope(self) -> None:
        config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
        hooks = [hook for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == "home-path-literal"]
        self.assertEqual(len(hooks), 1)
        hook = hooks[0]
        self.assertEqual(hook["entry"], "python3 util/home_path_literal_check.py")
        self.assertEqual(hook["language"], "system")
        self.assertNotIn("pass_filenames", hook)
        pattern = re.compile(hook["files"])
        module = load_module()
        samples = [f"{d}/{sub}x{s}" for d in (*SCOPE_DIRS, "tests", "docs", "conf", "utility") for sub in ("", "a/b/") for s in (*SCOPE_SUFFIXES, ".yaml", ".md", ".json", ".service")]
        samples += ["x.py", "util.py", "scripts", BASELINE_REL, "conf/home_path_literal_baseline.jsonx", "a/conf/home_path_literal_baseline.json"]
        for rel in samples:
            with self.subTest(rel=rel):
                self.assertEqual(bool(pattern.search(rel)), module.in_scope(rel) or rel == BASELINE_REL)

    def test_ci_runs_the_whole_scope_step(self) -> None:
        workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        steps = [step for step in workflow["jobs"]["pre-commit"]["steps"] if step.get("run", "").strip() == "python3 util/home_path_literal_check.py"]
        self.assertEqual(len(steps), 1)


if __name__ == "__main__":
    unittest.main()
