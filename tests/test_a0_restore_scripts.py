#!/usr/bin/env python3
"""Procedure A0's two scripts hand duplicati-cli a COPY of the frozen job index -- with its -wal/-journal.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-09-22_confirm_a0_premise.bash`` and ``util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash``
copy the frozen job index (``YAMAGUCHI_JOB_DB``) to a disposable ``--dbpath``. A ``-wal`` or hot ``-journal``
beside the index holds pages the main file lacks, and SQLite applies it only if it sits beside the copy under
the copy's own name (round 4, R4B N-8). Round 5 (R5A NIT-4, mutants F22 and F23) found that no suite ran
either script, so removing that copy, or copying under the wrong name, survived.

Pins, for each script:

* duplicati-cli sees the main copy AND each sibling the index has, byte-identical, beside ``--dbpath`` under
  the copy's name -- and nothing when the index has none;
* every temporary file is gone afterwards (main, -wal, -shm, -journal);
* the passphrase reaches duplicati-cli through the ENVIRONMENT only: parsed (never sourced) from a value
  holding ``$ & @ # ^``, never in argv, never printed;
* the restore script refuses a restore directory inside the backup Source before anything runs.

Hermetic: ``duplicati-cli`` is a PATH stub that records what it saw; every path comes through the scripts'
own ``YAMAGUCHI_*`` overrides and points into a temporary directory. No Duplicati binary, no
``/usr/lib/duplicati``, no ``/mnt/Backups``, no real credential file.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
PREMISE = REPO_ROOT / "util" / "ad-hoc" / "2026-09-22_confirm_a0_premise.bash"
RESTORE = REPO_ROOT / "util" / "ad-hoc" / "2026-09-22_restore_server_db_from_fileset.bash"
# A shell-hostile probe value standing in for the passphrase; named *_MARKER so bandit B105 does not read it as a credential.
PROBE_VALUE_MARKER: str = "fake$pass&not@a#secret^x"

CLI_STUB = r"""#!/usr/bin/env bash
# duplicati-cli stub: records the verb, argv, what sits beside --dbpath, and whether PASSPHRASE matched.
db=""
for a in "$@"; do case "$a" in --dbpath=*) db="${a#--dbpath=}" ;; esac; done
{
    echo "verb=$1"
    for s in "" -wal -journal; do
        if [[ -n "$db" && -e "$db$s" ]]; then echo "beside$s=$(cat "$db$s")"; else echo "beside$s=absent"; fi
    done
    printf 'arg=%s\n' "$@"
    if [[ "${PASSPHRASE:-}" == "${STUB_EXPECT_PASSPHRASE}" ]]; then echo "passphrase=match"; else echo "passphrase=mismatch"; fi
} > "${STUB_REPORT}"
exit "${STUB_CLI_EXIT:-0}"
"""


if TYPE_CHECKING:  # the mixin is typed as a TestCase for mypy only; at runtime it is a plain object
    _MixinBase = unittest.TestCase
else:
    _MixinBase = object


class _A0(_MixinBase):
    SCRIPT: Path

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="a0-scripts-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        (self.bin / "duplicati-cli").write_text(CLI_STUB)
        (self.bin / "duplicati-cli").chmod(0o755)
        # Safety net: if a regressed refusal let a real-home path through, `install -d` must not create it.
        (self.bin / "install").write_text('#!/usr/bin/env bash\nfor a in "$@"; do case "$a" in /home/*) echo "install stub REFUSES a host path: $a" >&2; exit 97 ;; esac; done\nexec /usr/bin/install "$@"\n')
        (self.bin / "install").chmod(0o755)
        self.env_file = self.tmp / "env"
        self.env_file.write_text(f"# comment\nOTHER=x\nPASSPHRASE={PROBE_VALUE_MARKER}\n")
        self.env_file.chmod(0o600)
        self.jobdb = self.tmp / "frozen" / "BMXWPAOGLP.sqlite"
        self.jobdb.parent.mkdir()
        self.jobdb.write_bytes(b"MAIN-INDEX")
        self.workdir = self.tmp / "work"
        self.report = self.tmp / "report"
        self.source_root = self.tmp / "home-src"
        self.source_root.mkdir()

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        env = RedactedEnv(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            YAMAGUCHI_ENV_FILE=str(self.env_file),
            YAMAGUCHI_DEST_URL=f"file://{self.tmp / 'dest'}",
            YAMAGUCHI_WORKDIR=str(self.workdir),
            YAMAGUCHI_JOB_DB=str(self.jobdb),
            # The backup Source the restore refuses: a scratch root, never the real home (R6 DEFECT-2).
            YAMAGUCHI_SOURCE_ROOT=str(self.source_root),
            STUB_REPORT=str(self.report),
            STUB_EXPECT_PASSPHRASE=PROBE_VALUE_MARKER,
        )
        env.pop("PASSPHRASE", None)
        if self.source_root is None:  # the production default decides
            env.pop("YAMAGUCHI_SOURCE_ROOT", None)
        r = subprocess.run(["bash", str(self.SCRIPT), *args], env=env, capture_output=True, text=True, timeout=60, check=False)
        self.assertNotIn(PROBE_VALUE_MARKER, r.stdout + r.stderr, "the passphrase was printed")
        return r

    def seen(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for ln in self.report.read_text().splitlines():
            k, _, v = ln.partition("=")
            if k == "arg":
                out.setdefault("argv", "")
                out["argv"] += v + "\n"
            else:
                out[k] = v
        return out

    def args(self) -> list[str]:
        return []

    def test_siblings_are_copied_beside_the_copy_under_its_name(self):
        """F22 / F23: without the copy, or under another name, SQLite opens the copy without the WAL's pages."""
        (self.jobdb.parent / (self.jobdb.name + "-wal")).write_bytes(b"WAL-PAGES")
        (self.jobdb.parent / (self.jobdb.name + "-journal")).write_bytes(b"HOT-JOURNAL")
        r = self.run_script(*self.args())
        self.assertEqual(r.returncode, 0, r.stderr)
        seen = self.seen()
        self.assertEqual(seen["beside"], "MAIN-INDEX")
        self.assertEqual(seen["beside-wal"], "WAL-PAGES")
        self.assertEqual(seen["beside-journal"], "HOT-JOURNAL")
        self.assertEqual(list(self.workdir.iterdir()), [], "every temporary copy is removed afterwards")
        self.assertEqual(self.jobdb.read_bytes(), b"MAIN-INDEX", "the frozen index is never written")

    def test_no_sibling_when_the_index_has_none(self):
        r = self.run_script(*self.args())
        self.assertEqual(r.returncode, 0, r.stderr)
        seen = self.seen()
        self.assertEqual((seen["beside"], seen["beside-wal"], seen["beside-journal"]), ("MAIN-INDEX", "absent", "absent"))
        self.assertEqual(list(self.workdir.iterdir()), [])

    def test_passphrase_reaches_the_cli_by_environment_only(self):
        r = self.run_script(*self.args())
        self.assertEqual(r.returncode, 0, r.stderr)
        seen = self.seen()
        self.assertEqual(seen["passphrase"], "match", "parsed verbatim, $ & @ # ^ included")
        self.assertNotIn(PROBE_VALUE_MARKER, seen["argv"])
        self.assertIn(f"--dbpath={self.workdir}/", seen["argv"])
        self.assertNotIn(str(self.jobdb) + "\n", seen["argv"].replace("--dbpath=", ""), "duplicati-cli must get the COPY, never the frozen index")

    def test_refuses_without_an_index(self):
        self.jobdb.unlink()
        r = self.run_script(*self.args())
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("no job index", r.stderr)
        self.assertFalse(self.report.exists(), "duplicati-cli must not run")


class ConfirmA0Premise(_A0, unittest.TestCase):
    SCRIPT = PREMISE

    def test_lists_the_snapshot_path_in_version_0(self):
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        seen = self.seen()
        self.assertEqual(seen["verb"], "list")
        self.assertIn("--version=0\n", seen["argv"])
        self.assertIn("*duplicati-server-db*\n", seen["argv"])


class RestoreServerDbFromFileset(_A0, unittest.TestCase):
    SCRIPT = RESTORE

    def args(self) -> list[str]:
        return [str(self.tmp / "restore-out")]

    def test_restores_into_the_named_directory(self):
        r = self.run_script(*self.args())
        self.assertEqual(r.returncode, 0, r.stderr)
        seen = self.seen()
        self.assertEqual(seen["verb"], "restore")
        self.assertIn(f"--restore-path={self.tmp / 'restore-out'}\n", seen["argv"])
        self.assertEqual(oct((self.tmp / "restore-out").stat().st_mode & 0o777), "0o700")

    def assert_refused(self, out: Path, made: Path) -> None:
        r = self.run_script(str(out))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("inside the backup Source", r.stderr)
        self.assertFalse(self.report.exists(), "duplicati-cli must not run")
        self.assertFalse(made.exists(), f"{made} must not be created")

    def test_refuses_a_restore_directory_inside_the_backup_source(self):
        """Through YAMAGUCHI_SOURCE_ROOT, so the test never stats or creates anything in the real home and holds
        on a host without /home/pcalnon (R6 DEFECT-2: CI)."""
        self.assert_refused(self.source_root / "a0-out", self.source_root / "a0-out")

    def test_refuses_two_or_more_new_levels_under_the_source(self):
        """R6 DEFECT-2: `readlink -f` printed nothing for a path whose parent was missing, so this passed."""
        self.assert_refused(self.source_root / "a0" / "out", self.source_root / "a0")
        self.assert_refused(self.source_root / "x" / "y" / "z", self.source_root / "x")

    def test_refuses_the_source_root_itself_and_dot_dot_paths_into_it(self):
        self.assert_refused(self.source_root, self.source_root / "nothing-made")
        self.assert_refused(self.tmp / "elsewhere" / ".." / "home-src" / "new" / "sub", self.source_root / "new")

    def test_refuses_a_symlink_into_the_source(self):
        """A restore path OUTSIDE the Source that is (or runs through) a symlink pointing into it."""
        (self.tmp / "link-to-src").symlink_to(self.source_root)
        self.assert_refused(self.tmp / "link-to-src" / "new" / "sub", self.source_root / "new")
        (self.source_root / "existing").mkdir()
        (self.tmp / "link-to-dir").symlink_to(self.source_root / "existing")
        self.assert_refused(self.tmp / "link-to-dir", self.source_root / "existing" / "nothing-made")

    def run_with_default_root(self, out: str) -> subprocess.CompletedProcess:
        """YAMAGUCHI_SOURCE_ROOT UNSET, so the script's production default decides."""
        saved = self.source_root
        try:
            self.source_root = None
            return self.run_script(out)
        finally:
            self.source_root = saved

    def test_the_production_default_root_is_the_real_home(self):
        """R7 NIT-1 (mutants Q01, Q02): with the override unset, a path under /home/pcalnon is refused and a
        path elsewhere is not. `realpath -m` creates nothing, so this is hermetic on CI too; the PATH `install`
        stub refuses /home/* in case the refusal ever regresses."""
        probe = Path("/home/pcalnon/a0-r7-probe-must-not-exist")
        existed = probe.exists()
        r = self.run_with_default_root(str(probe / "x" / "y"))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("inside the backup Source (/home/pcalnon)", r.stderr)
        self.assertFalse(self.report.exists(), "duplicati-cli must not run")
        if not existed:
            self.assertFalse(probe.exists(), "nothing may be created under the real home")
        out = self.tmp / "outside" / "out"
        r = self.run_with_default_root(str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.is_dir())
        self.assertIn("${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}", RESTORE.read_text(encoding="utf-8"))

    def test_a_source_root_given_through_a_symlink_is_canonicalised(self):
        """R7 Q07: the root is resolved too, so a root named through a symlink still matches the real OUT path."""
        link = self.tmp / "root-link"
        link.symlink_to(self.source_root)
        real_root, self.source_root = self.source_root, link
        try:
            self.assert_refused(real_root / "new" / "sub", real_root / "new")
        finally:
            self.source_root = real_root

    def test_a_sibling_whose_name_extends_the_source_is_not_refused(self):
        """The prefix match is on a path component: `<root>-other` is outside `<root>`."""
        out = self.tmp / "home-src-other" / "out"
        r = self.run_script(str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.is_dir())


if __name__ == "__main__":
    unittest.main()
