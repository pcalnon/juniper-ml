#!/usr/bin/env python3
"""Hermetic gate for util/find_encryption_readme_notes.bash (turing bring-up plan task B9).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The first version of this script rode the unsigned branch of juniper-ml#2222. It built
``ls -Fla ${i}`` from ``find`` output and ran the string through ``eval``, so a file NAMED
``$(:>x)encryption.bash`` was executed rather than listed (plan
``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` task B9, regression
R-B9). The rewrite passes paths NUL-delimited and never evaluates one.

``InjectionRegressionTest`` carries a negative control. The same fixture, run through a faithful copy
of the eval loop, DOES execute its payload. That proves the fixture is a live injection, so the pass
on the real script is not vacuous.

Every case runs under ``/bin/bash``, which is bash 3.2 on macOS (the plan's portability floor) and
the system bash on Linux CI.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "find_encryption_readme_notes.bash"
TIMEOUT_SECONDS = 30

# Shell metacharacter payloads, each a legal file name (no '/', no NUL). Each one creates a marker
# file in the current directory if anything ever evaluates the name. They are whitespace-free on
# purpose: the original word-split find output first, so a payload with a space reached eval in
# two harmless halves, and a control built that way never fires (observed while writing this).
PAYLOADS = {
    "MARK_DOLLAR": "$(:>MARK_DOLLAR)encryption.bash",
    "MARK_BACKTICK": "`:>MARK_BACKTICK`encryption.bash",
    "MARK_SEMICOLON": "x;:>MARK_SEMICOLON;encryption.bash",
    "MARK_OR": "x||:>MARK_OR||encryption.bash",
    "MARK_PIPE": "x|:>MARK_PIPE|encryption.bash",
}

# The loop of the original script (juniper-ml#2222, commit e3476d78), with its hard-coded
# WORKING_DIR made an argument. Used only as the negative control.
ORIGINAL_EVAL_LOOP = textwrap.dedent("""\
    FILENAME="encryption.bash"
    WORKING_DIR="$1"
    cd "${WORKING_DIR}" || exit 1
    for i in $(find . | grep "${FILENAME}"); do
        CMD="ls -Fla ${i}"
        eval "${CMD}" >/dev/null 2>&1
    done
    exit 0
    """)


def _run(args: list[str], *, cwd: Path, home: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    # PWD names cwd the way Python does. Without it bash falls back to the physical path, and on
    # macOS a temp dir under /var resolves through the /private/var symlink.
    env = RedactedEnv(os.environ, HOME=str(home), PWD=str(cwd))
    env.pop("CDPATH", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["/bin/bash", str(SCRIPT_PATH), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )


def _lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line]


class _Fixture(unittest.TestCase):
    """A scratch tree: ``root`` to search, ``cwd`` to run from, ``home`` for HOME."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.root = base / "root"
        self.cwd = base / "cwd"
        self.home = base / "home"
        for d in (self.root, self.cwd, self.home):
            d.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def touch(self, rel: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
        return path

    def run_script(self, *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return _run(list(args), cwd=self.cwd, home=self.home, extra_env=extra_env)

    def root_abs(self) -> str:
        """The root as the script prints it: absolute, through bash's logical pwd."""
        return str(self.root)


class HappyPathTest(_Fixture):
    def test_regular_files_are_listed_absolute_and_valid_exit_0(self) -> None:
        first = self.touch("a/encryption.bash")
        second = self.touch("b/c/old-encryption.bash.bak")
        self.touch("b/c/unrelated.txt")
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            sorted(_lines(proc.stdout)),
            sorted([f"{first}\t==> Valid", f"{second}\t==> Valid"]),
        )
        self.assertIn("2 match(es), 0 invalid", proc.stderr)

    def test_name_option_changes_the_pattern(self) -> None:
        wanted = self.touch("notes/ENCRYPTION_README.md")
        self.touch("a/encryption.bash")
        proc = self.run_script("--root", str(self.root), "--name", "ENCRYPTION_README")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{wanted}\t==> Valid"])

    def test_default_root_is_home_development(self) -> None:
        target = self.home / "Development" / "proj" / "encryption.bash"
        target.parent.mkdir(parents=True)
        target.write_text("x\n", encoding="utf-8")
        proc = self.run_script()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{target}\t==> Valid"])

    def test_relative_root_prints_absolute_paths(self) -> None:
        target = self.touch("encryption.bash")
        proc = _run(["--root", "root"], cwd=self.root.parent, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{target}\t==> Valid"])

    def test_root_named_with_a_leading_dash_is_a_directory_not_an_option(self) -> None:
        dashed = self.root / "-weird"
        (dashed / "sub").mkdir(parents=True)
        target = dashed / "sub" / "encryption.bash"
        target.write_text("x\n", encoding="utf-8")
        proc = _run(["--root", "-weird"], cwd=self.root, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{target}\t==> Valid"])

    def test_cdpath_does_not_leak_into_the_root(self) -> None:
        # With CDPATH set, a plain `cd rel` resolves through it and prints the directory, which a
        # $(cd ... && pwd) capture would then carry as a second line.
        decoy = self.cwd / "decoy" / "root"
        decoy.mkdir(parents=True)
        target = self.touch("encryption.bash")
        proc = _run(["--root", "root"], cwd=self.root.parent, home=self.home, extra_env={"CDPATH": str(self.cwd / "decoy")})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{target}\t==> Valid"])

    def test_help_exits_0(self) -> None:
        proc = self.run_script("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Usage:", proc.stdout)
        self.assertIn("--root", proc.stdout)


class ExitCodeTest(_Fixture):
    def test_no_match_exits_1(self) -> None:
        self.touch("a/unrelated.txt")
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("no name containing 'encryption.bash'", proc.stderr)

    def test_directory_match_is_invalid_exit_1(self) -> None:
        (self.root / "encryption.bash.d").mkdir()
        good = self.touch("ok/encryption.bash")
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(
            sorted(_lines(proc.stdout)),
            sorted([f"{self.root / 'encryption.bash.d'}\t==> Invalid", f"{good}\t==> Valid"]),
        )
        self.assertIn("2 match(es), 1 invalid", proc.stderr)

    def test_dangling_symlink_is_invalid_exit_1(self) -> None:
        link = self.root / "encryption.bash"
        link.symlink_to(self.root / "does-not-exist")
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(_lines(proc.stdout), [f"{link}\t==> Invalid"])

    def test_symlink_to_a_regular_file_is_valid(self) -> None:
        real = self.touch("real.txt")
        link = self.root / "encryption.bash"
        link.symlink_to(real)
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{link}\t==> Valid"])

    def test_missing_root_exits_2(self) -> None:
        proc = self.run_script("--root", str(self.root / "nope"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not a directory", proc.stderr)

    def test_root_that_is_a_file_exits_2(self) -> None:
        f = self.touch("plain.txt")
        proc = self.run_script("--root", str(f))
        self.assertEqual(proc.returncode, 2)

    def test_unknown_argument_exits_2(self) -> None:
        proc = self.run_script("--frobnicate")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown argument", proc.stderr)

    def test_root_without_value_exits_2(self) -> None:
        proc = self.run_script("--root")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--root needs a directory", proc.stderr)

    def test_name_without_value_exits_2(self) -> None:
        proc = self.run_script("--name")
        self.assertEqual(proc.returncode, 2)

    def test_empty_name_exits_2(self) -> None:
        proc = self.run_script("--name", "")
        self.assertEqual(proc.returncode, 2)

    def test_name_with_slash_exits_2(self) -> None:
        proc = self.run_script("--root", str(self.root), "--name", "a/encryption.bash")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("cannot contain '/'", proc.stderr)


class InjectionRegressionTest(_Fixture):
    """R-B9: a file name containing shell syntax is listed, never executed."""

    def _plant_payloads(self) -> dict[str, Path]:
        return {marker: self.touch(name) for marker, name in PAYLOADS.items()}

    def _markers_created(self) -> list[str]:
        found = []
        for place in (self.cwd, self.root, self.home):
            for marker in PAYLOADS:
                if (place / marker).exists():
                    found.append(f"{place.name}/{marker}")
        return found

    def test_control_the_original_eval_loop_executes_every_payload(self) -> None:
        # Without this control a fixture that could never execute would make the real test vacuous.
        self._plant_payloads()
        env = RedactedEnv(os.environ, HOME=str(self.home))
        subprocess.run(
            ["/bin/bash", "-c", ORIGINAL_EVAL_LOOP, "original", str(self.root)],
            cwd=self.cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=True,
        )
        # The original cd'd into the search root, so that is where its payloads land.
        missing = [marker for marker in PAYLOADS if not (self.root / marker).exists()]
        self.assertEqual(missing, [], "control: the eval loop should have executed every payload")

    def test_shell_syntax_in_names_is_listed_literally_and_never_run(self) -> None:
        planted = self._plant_payloads()
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._markers_created(), [], "a file name was executed")
        self.assertEqual(
            sorted(_lines(proc.stdout)),
            sorted(f"{path}\t==> Valid" for path in planted.values()),
        )

    def test_space_in_a_name_stays_one_path(self) -> None:
        spaced = self.touch("dir with space/my encryption.bash copy")
        proc = self.run_script("--root", str(self.root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_lines(proc.stdout), [f"{spaced}\t==> Valid"])

    def test_find_output_is_consumed_nul_delimited(self) -> None:
        # A stub find emits one path that contains a newline. NUL-delimited reading keeps it whole;
        # line- or word-splitting would report two (or more) bogus paths.
        tricky = self.root / "line1\nline2encryption.bash"
        tricky.write_text("x\n", encoding="utf-8")
        argv_log = self.cwd / "find.argv"
        stub = self.cwd / "find-stub"
        # Built line by line: the path's own newline would defeat textwrap.dedent and indent the shebang.
        stub.write_text(
            "#!/bin/bash\n" f"printf '%s\\n' \"$@\" > '{argv_log}'\n" f"printf '%s\\0' '{tricky}'\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        proc = self.run_script("--root", str(self.root), extra_env={"FIND": str(stub)})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, f"{tricky}\t==> Valid\n")
        self.assertIn("1 match(es), 0 invalid", proc.stderr)
        self.assertEqual(
            argv_log.read_text(encoding="utf-8").splitlines(),
            [self.root_abs(), "-name", "*encryption.bash*", "-print0"],
        )


class SourceContractTest(unittest.TestCase):
    """Static pins on the script text. Comment lines are excluded; they may name the old defect."""

    text: str
    code: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.text.splitlines() if not line.lstrip().startswith("#"))

    def test_no_eval_in_code(self) -> None:
        self.assertIsNone(re.search(r"\beval\b", self.code), "eval re-parses data as code (R-B9)")

    def test_no_host_specific_home_literal(self) -> None:
        self.assertNotRegex(self.text, r"/Users/|/home/", "use a $HOME-relative path (plan D12)")

    def test_strict_mode_and_overridable_find(self) -> None:
        self.assertIn("set -euo pipefail", self.code)
        self.assertIn('FIND="${FIND:-find}"', self.code)
        self.assertIn("-print0", self.code)
        self.assertIn("read -r -d ''", self.code)

    def test_shellcheck_clean_when_available(self) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            self.skipTest("shellcheck not installed (CI's pre-commit runs it)")
        proc = subprocess.run([shellcheck, str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
