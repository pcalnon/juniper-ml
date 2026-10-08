"""Hermetic coverage for the Yamaguchi pre-backup guard.

util/yamaguchi-pre-backup-guard.bash is Duplicati's --run-script-before-required hook.
Exit 0 lets the backup touch the destination. Exit 5 aborts it. Duplicati parses the
script's stdout as job-option overrides, so a message on stdout can change the running
job. Duplicati also exports every job option, passphrase included, as DUPLICATI__*
and the unit inherits SETTINGS_ENCRYPTION_KEY; both must be gone before any child
(mountpoint, find, id) runs.

The script is committed 0644, so this suite runs it with bash, the same way
util/install_duplicati_service.bash syntax-checks it. mountpoint is a PATH stub.
find is the real utility except in the one test that makes the scan fail. No
Duplicati, no mount, no credential file.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO = Path(__file__).resolve().parents[1]
GUARD = REPO / "util" / "yamaguchi-pre-backup-guard.bash"
# Stand-in for the job passphrase Duplicati exports as DUPLICATI__PASSPHRASE: a fixture value,
# never a credential, named as a marker so the scanners do not read it as a hardcoded password.
JOB_PHRASE_MARKER = "job-phrase-marker-not-real"
SETTINGS_KEY = "settings-encryption-key-not-a-real-secret"
SENTINEL = "guard-sentinel-kept"

# What `tr -cd 'A-Za-z0-9._-' | cut -c1-64` keeps of a basename.
_SAFE = re.compile(r"[^A-Za-z0-9._-]")


def _sanitised(name: str) -> str:
    return _SAFE.sub("", name)[:64]


def _touch(directory: Path, name: str) -> None:
    """Create one directory entry. pathlib treats '/' as a separator, and a newline in a name is legal on Linux."""
    fd = os.open(os.path.join(str(directory), name), os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, b"x")
    finally:
        os.close(fd)


class PreBackupGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stub_bin = self.root / "bin"
        self.stub_bin.mkdir()
        self.mounts = self.root / "mounts"
        self.mounts.write_text("")
        self.env_dump = self.root / "child.env"
        self.find_marker = self.root / "find-ran"
        self._write_mountpoint()

    def _write_mountpoint(self) -> None:
        script = self.stub_bin / "mountpoint"
        lines = ("#!/bin/bash", "set -u", 'env > "$GUARD_CHILD_ENV"', 'target="${2-}"', 'grep -F -x -q -- "$target" "$GUARD_MOUNTS"')
        script.write_text("\n".join(lines) + "\n")
        script.chmod(0o755)

    def _mark_mounted(self, path: Path) -> None:
        with self.mounts.open("a", encoding="utf-8") as fh:
            fh.write(str(path) + "\n")

    def _run(
        self,
        dest: Path,
        *,
        mounted: bool = True,
        remote_url: str | None = "",
        operation: str = "Backup",
        extra_path: Path | None = None,
        make_dest: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        if make_dest:
            dest.mkdir(parents=True, exist_ok=True)
        mount = dest.parent
        if mounted:
            self._mark_mounted(mount)
        env = RedactedEnv(os.environ)
        env.update(
            {
                "PATH": f"{extra_path}:{self.stub_bin}:{env.get('PATH', '')}" if extra_path else f"{self.stub_bin}:{env.get('PATH', '')}",
                "GUARD_CHILD_ENV": str(self.env_dump),
                "GUARD_MOUNTS": str(self.mounts),
                "YAMAGUCHI_DEST_MOUNT": str(mount),
                "YAMAGUCHI_DEST_DIR": str(dest),
                "GUARD_SENTINEL": SENTINEL,
                "DUPLICATI__PASSPHRASE": JOB_PHRASE_MARKER,
                "DUPLICATI__JWT_CONFIG": "jwt-signing-key-not-real",
                "DUPLICATI__OPERATIONNAME": operation,
                "SETTINGS_ENCRYPTION_KEY": SETTINGS_KEY,
            }
        )
        # None means UNSET: drop a value leaked from the parent environment, if any.
        if remote_url is None:
            env.pop("DUPLICATI__REMOTEURL", None)
        else:
            env["DUPLICATI__REMOTEURL"] = remote_url
        return subprocess.run(
            ["/bin/bash", str(GUARD)],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
            check=False,
        )

    def _child_env(self) -> str:
        self.assertTrue(self.env_dump.is_file(), "mountpoint never ran, so the child environment was not observed")
        return self.env_dump.read_text(encoding="utf-8", errors="replace")

    def test_a_clean_destination_exits_0_and_children_do_not_see_secrets(self) -> None:
        dest = self.root / "dest"
        url = f"file://{dest}"
        for name in (
            "duplicati-abc.dblock.zip.aes",
            "duplicati-abc.dindex.zip.aes",
            "duplicati-abc.dlist.zip.aes",
            "duplicati-verification.json",
        ):
            dest_parent_ready = dest
            dest_parent_ready.mkdir(parents=True, exist_ok=True)
            (dest / name).write_text("volume", encoding="utf-8")
        result = self._run(dest, remote_url=url)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        child = self._child_env()
        self.assertIn(f"GUARD_SENTINEL={SENTINEL}\n", child)
        for secret in (JOB_PHRASE_MARKER, SETTINGS_KEY, "jwt-signing-key-not-real", url):
            self.assertNotIn(secret, child)
        self.assertNotIn("DUPLICATI__", child)
        self.assertNotIn("SETTINGS_ENCRYPTION_KEY", child)

    def test_an_unmounted_destination_exits_5_with_an_empty_stdout(self) -> None:
        dest = self.root / "dest"
        result = self._run(dest, mounted=False, remote_url=f"file://{dest}")
        self.assertEqual(result.returncode, 5)
        self.assertEqual(result.stdout, "")
        self.assertIn("GUARD(Backup):", result.stderr)
        self.assertIn("is not a mountpoint", result.stderr)
        self.assertNotIn(JOB_PHRASE_MARKER, result.stderr)
        self.assertNotIn(SETTINGS_KEY, result.stderr)
        child = self._child_env()
        self.assertNotIn(JOB_PHRASE_MARKER, child)
        self.assertNotIn("DUPLICATI__", child)

    def test_a_missing_directory_refuses_before_the_stray_scan(self) -> None:
        find_bin = self.root / "findbin"
        find_bin.mkdir()
        finder = find_bin / "find"
        finder.write_text('#!/bin/bash\ntouch "$GUARD_FIND_MARKER"\nexit 0\n')
        finder.chmod(0o755)
        dest = self.root / "missing-dest"
        self._mark_mounted(dest.parent)
        env = RedactedEnv(os.environ)
        env.update(
            {
                "PATH": f"{find_bin}:{self.stub_bin}:{env.get('PATH', '')}",
                "GUARD_CHILD_ENV": str(self.env_dump),
                "GUARD_MOUNTS": str(self.mounts),
                "GUARD_FIND_MARKER": str(self.find_marker),
                "YAMAGUCHI_DEST_MOUNT": str(dest.parent),
                "YAMAGUCHI_DEST_DIR": str(dest),
                "DUPLICATI__OPERATIONNAME": "Backup",
                "DUPLICATI__REMOTEURL": f"file://{dest}",
                "DUPLICATI__PASSPHRASE": JOB_PHRASE_MARKER,
            }
        )
        result = subprocess.run(["/bin/bash", str(GUARD)], capture_output=True, text=True, env=env, timeout=15, check=False)
        self.assertEqual(result.returncode, 5, msg=result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("does not exist", result.stderr)
        self.assertNotIn(JOB_PHRASE_MARKER, result.stderr)
        self.assertFalse(self.find_marker.exists(), "a missing destination must not be scanned")

    def test_an_unwritable_directory_exits_5(self) -> None:
        # Root bypasses the mode bits `test -w` reads, so this arm is the non-root one.
        if os.geteuid() == 0:
            self.skipTest("root's test -w ignores mode 0500; the refusal is checked as the backup user")
        dest = self.root / "dest"
        dest.mkdir()
        # Owner read + search only: `-x` still passes, so the refusal is the missing write bit.
        os.chmod(dest, 0o500)
        self.addCleanup(lambda: os.chmod(dest, 0o700))
        result = self._run(dest, remote_url=f"file://{dest}")
        self.assertEqual(result.returncode, 5, msg=result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("is not writable", result.stderr)
        self.assertNotIn(JOB_PHRASE_MARKER, result.stderr)

    def test_a_credential_url_is_refused_without_being_printed(self) -> None:
        dest = self.root / "dest"
        url = f"s3://AKIAIOSFODNN7EXAMPLE:{JOB_PHRASE_MARKER}@bucket/yamaguchi"
        result = self._run(dest, remote_url=url)
        self.assertEqual(result.returncode, 5, msg=result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("scheme='s3'", result.stderr)
        self.assertIn(f"length={len(url)}", result.stderr)
        digest = hashlib.sha256(url.encode()).hexdigest()[:8]
        self.assertIn(f"sha256-8={digest}", result.stderr)
        combined = result.stdout + result.stderr
        self.assertNotIn(JOB_PHRASE_MARKER, combined)
        self.assertNotIn(url, combined)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", combined)

    def test_one_trailing_slash_matches_and_a_second_does_not(self) -> None:
        dest = self.root / "dest"
        ok = self._run(dest, remote_url=f"file://{dest}/")
        self.assertEqual(ok.returncode, 0, msg=ok.stderr)
        self.assertEqual(ok.stdout, "")
        self.env_dump.unlink(missing_ok=True)
        self.mounts.write_text("")
        refused = self._run(dest, remote_url=f"file://{dest}//")
        self.assertEqual(refused.returncode, 5, msg=refused.stderr)
        self.assertEqual(refused.stdout, "")
        self.assertNotIn(f"file://{dest}//", refused.stderr)
        self.env_dump.unlink(missing_ok=True)
        self.mounts.write_text("")
        segment = self._run(dest, remote_url=f"file://{dest}/extra")
        self.assertEqual(segment.returncode, 5, msg=segment.stderr)
        self.assertNotIn("/extra", segment.stderr)

    def test_an_empty_remote_url_does_not_skip_the_destination_checks(self) -> None:
        dest = self.root / "dest"
        # Unset, not empty: Duplicati may simply not export the variable.
        result = self._run(dest, remote_url=None, mounted=False)
        self.assertEqual(result.returncode, 5)
        self.assertEqual(result.stdout, "")
        self.assertIn("is not a mountpoint", result.stderr)

    def test_a_foreign_name_is_refused_and_sanitised(self) -> None:
        dest = self.root / "dest"
        # '/' cannot be a filename on Linux. Newline, ';', '$', '(', ')' and spaces can, and tr drops all of them.
        nasty = "evil\nname;rm -rf $(echo hi)"
        long_secret = ("B" * 70) + "\nSECRETLEAK"
        dest.mkdir()
        _touch(dest, nasty)
        result = self._run(dest, remote_url=f"file://{dest}")
        self.assertEqual(result.returncode, 5, msg=result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn(f"name sanitised: {_sanitised(nasty)}", result.stderr)
        self.assertNotIn("\nname", result.stderr)
        self.assertNotIn("$(", result.stderr)
        self.assertNotIn(JOB_PHRASE_MARKER, result.stderr)
        # A second run with only the over-long name: the leak sits past the 64-character cut.
        for child in dest.iterdir():
            child.unlink()
        _touch(dest, long_secret)
        self.env_dump.unlink(missing_ok=True)
        self.mounts.write_text("")
        capped = self._run(dest, remote_url=f"file://{dest}")
        self.assertEqual(capped.returncode, 5, msg=capped.stderr)
        self.assertEqual(capped.stdout, "")
        self.assertIn("name sanitised: " + ("B" * 64), capped.stderr)
        self.assertNotIn("SECRETLEAK", capped.stderr)

    def test_a_failed_destination_scan_exits_5_rather_than_proceeding(self) -> None:
        find_bin = self.root / "findbin"
        find_bin.mkdir()
        finder = find_bin / "find"
        finder.write_text("#!/bin/bash\nexit 1\n")
        finder.chmod(0o755)
        dest = self.root / "dest"
        result = self._run(dest, remote_url=f"file://{dest}", extra_path=find_bin)
        self.assertEqual(result.returncode, 5, msg=result.stderr + result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(JOB_PHRASE_MARKER, result.stderr)


if __name__ == "__main__":
    unittest.main()
