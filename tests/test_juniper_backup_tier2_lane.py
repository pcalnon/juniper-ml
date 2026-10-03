"""Hermetic coverage for the tier-2 USB archive lane (recovery plan B6 / I-20; backup design §7.8, §8 P3).

Tier 2 could not find its drives from 2026-09-07: udisks2 2.10.91 moved removable-media automounts from
/media/<user> to /run/media/<user>, while util/juniper-backup.bash still forced /media/pcalnon/<name>. Its
scheduler, util/juniper-backup-scheduled.bash, already looked under /run/media, so every run the scheduler
judged due would have ended in the runner's "no usable destination". This suite pins the fix and the lane's
two new artifacts:

* the runner's mount root: JUNIPER_BACKUP_MEDIA_ROOT (default /run/media/$USER), read under the same name
  and default as the scheduler; an absolute JUNIPER_BACKUP_DEVICES entry used verbatim; and the mount guard
  applying to both forms;
* scheduler -> runner agreement, end to end through the copies the installer puts in ~/.local/bin;
* juniper-backup-failure.service: the shared reporter writes into THIS lane's state directory;
* util/install_juniper_backup_timer.bash: --dry-run writes nothing, root is refused, a refusal leaves
  nothing half-installed, copies never symlinks, and the timer and the path unit are enabled.

No real drive is ever touched. ``mountpoint`` is a PATH stub that answers from a list of scratch paths and
stats nothing; gpg / uuidgen / bc / systemctl / loginctl / journalctl / notify-send are stubs; every runner
invocation is --dry-run (or refused before it builds); every HOME, source tree and "drive" is a directory
under a TemporaryDirectory. util/ is outside every pre-commit Python hook, so this unittest is the gate.
"""

from __future__ import annotations

import hashlib
import os
import pwd
import re
import shlex
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
UTIL = REPO_ROOT / "util"
RUNNER = UTIL / "juniper-backup.bash"
SCHEDULER = UTIL / "juniper-backup-scheduled.bash"
REPORTER = UTIL / "duplicati_backup_failure.bash"
INSTALLER = UTIL / "install_juniper_backup_timer.bash"
UNIT_SRC = UTIL / "systemd"
SERVICE = UNIT_SRC / "juniper-backup.service"
FAILURE_SERVICE = UNIT_SRC / "juniper-backup-failure.service"

RUNNER_TEXT = RUNNER.read_text(encoding="utf-8")
SCHEDULER_TEXT = SCHEDULER.read_text(encoding="utf-8")
INSTALLER_TEXT = INSTALLER.read_text(encoding="utf-8")
SERVICE_TEXT = SERVICE.read_text(encoding="utf-8")
FAILURE_SERVICE_TEXT = FAILURE_SERVICE.read_text(encoding="utf-8")

TIMEOUT_SECONDS = 60
FAKE_USER = "b6-tier2-user"  # synthetic: no host has a /run/media/b6-tier2-user to probe
FAKE_UUID = "00000000-0000-4000-8000-0000000000b6"
BACKUP_DIR = "Juniper-8.0.0.python"
REPO = "juniper-ml"  # the one repository in the scratch --source tree

# Repository file under util/ -> the name the installer gives it in ~/.local/bin.
INSTALLED_SCRIPTS = {
    "juniper-backup.bash": "juniper-backup.bash",
    "juniper-backup-scheduled.bash": "juniper-backup-scheduled.bash",
    "duplicati_backup_failure.bash": "duplicati-backup-failure.bash",
}
INSTALLED_UNITS = ("juniper-backup.timer", "juniper-backup.path", "juniper-backup.service", "juniper-backup-failure.service")
ENABLE_LINE = "--user enable --now juniper-backup.timer juniper-backup.path"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


def _parse_status(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            parsed[key] = value
    return parsed


def _snapshot(root: Path) -> list[str]:
    """Every entry under ``root`` with its type, mode and content hash: a before/after witness."""
    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_symlink():
            entries.append(f"L {rel} -> {os.readlink(path)}")
        elif path.is_dir():
            entries.append(f"D {rel} {stat.S_IMODE(path.stat().st_mode):o}")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"F {rel} {stat.S_IMODE(path.stat().st_mode):o} {digest}")
    return entries


def _code_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def _unit_values(text: str, key: str) -> list[str]:
    prefix = f"{key}="
    return [line.strip()[len(prefix) :] for line in text.splitlines() if line.strip().startswith(prefix)]


class _Tier2Fixture:
    """A scratch HOME, a one-repo source tree, scratch "drives" and PATH stubs. Nothing real is touched."""

    def __init__(self, tmpdir: str) -> None:
        self.root = Path(tmpdir)
        self.stub_bin = self.root / "stubs"
        self.home = self.root / "home"
        self.source = self.root / "source"
        self.mounts_file = self.root / "fake-mounts.txt"
        self.linger_file = self.root / "linger.txt"
        self.mountpoint_log = self.root / "mountpoint.log"
        self.gpg_log = self.root / "gpg.log"
        self.systemctl_log = self.root / "systemctl.log"
        self.stub_bin.mkdir()
        self.home.mkdir()
        (self.source / REPO).mkdir(parents=True)
        (self.source / REPO / "README.md").write_text("scratch repository\n", encoding="utf-8")
        self.mounts_file.write_text("", encoding="utf-8")
        self.set_linger("yes")
        self._write_stubs()

    # --- paths -------------------------------------------------------------------------------------------
    @property
    def bin_dir(self) -> Path:
        return self.home / ".local" / "bin"

    @property
    def unit_dir(self) -> Path:
        return self.home / ".config" / "systemd" / "user"

    @property
    def state_dir(self) -> Path:
        return self.home / ".local" / "state" / "juniper-backup"

    # --- stubs -------------------------------------------------------------------------------------------
    def _write_stubs(self) -> None:
        _write_executable(
            self.stub_bin / "mountpoint",
            """\
            #!/usr/bin/env bash
            # A path is a mount point iff it is listed in $FAKE_MOUNTS. Stats nothing: no drive is probed.
            printf '%s\\n' "$*" >> "${MOUNTPOINT_LOG:-/dev/null}"
            target="${!#}"
            while IFS= read -r listed; do
                [[ "${listed}" == "${target}" ]] && exit 0
            done < "${FAKE_MOUNTS:-/dev/null}"
            exit 1
            """,
        )
        _write_executable(
            self.stub_bin / "gpg",
            """\
            #!/usr/bin/env bash
            # Recipients resolve; anything else (an encryption) is refused loudly.
            printf '%s\\n' "$*" >> "${GPG_LOG:-/dev/null}"
            [[ "${1:-}" == "--list-keys" ]] && exit 0
            echo "gpg stub: unexpected call: $*" >&2
            exit 97
            """,
        )
        _write_executable(
            self.stub_bin / "uuidgen",
            f"""\
            #!/usr/bin/env bash
            printf '%s\\n' "{FAKE_UUID}"
            """,
        )
        _write_executable(
            self.stub_bin / "bc",
            """\
            #!/usr/bin/env bash
            # The one form the runner pipes in: "<int> / <int>".
            read -r lhs op rhs
            [[ "${op}" == "/" ]] || { echo "bc stub: unsupported expression" >&2; exit 1; }
            echo $(( lhs / rhs ))
            """,
        )
        _write_executable(
            self.stub_bin / "systemctl",
            """\
            #!/usr/bin/env bash
            printf '%s\\n' "$*" >> "${SYSTEMCTL_LOG:-/dev/null}"
            exit 0
            """,
        )
        _write_executable(
            self.stub_bin / "loginctl",
            """\
            #!/usr/bin/env bash
            # `loginctl show-user <user> --property=Linger --value` -> the fixture's value.
            cat "${FAKE_LINGER_FILE:-/dev/null}"
            """,
        )
        _write_executable(
            self.stub_bin / "journalctl",
            """\
            #!/usr/bin/env bash
            printf 'journal-stub-line %s\\n' "$*"
            """,
        )
        _write_executable(
            self.stub_bin / "notify-send",
            """\
            #!/usr/bin/env bash
            exit 0
            """,
        )

    def stub_root_id(self) -> None:
        _write_executable(
            self.stub_bin / "id",
            """\
            #!/usr/bin/env bash
            case "${1:-}" in
                -u) echo 0 ;;
                -un) echo root ;;
                *) echo "uid=0(root) gid=0(root) groups=0(root)" ;;
            esac
            """,
        )

    def set_linger(self, value: str) -> None:
        self.linger_file.write_text(value + "\n", encoding="utf-8")

    # --- drives ------------------------------------------------------------------------------------------
    def mount(self, mount_root: Path) -> None:
        with self.mounts_file.open("a", encoding="utf-8") as handle:
            handle.write(f"{mount_root}\n")

    def make_drive(self, mount_root: Path, *, mounted: bool = True, backup_dir: str = BACKUP_DIR) -> Path:
        target = mount_root / backup_dir
        target.mkdir(parents=True)
        if mounted:
            self.mount(mount_root)
        return target

    # --- processes ---------------------------------------------------------------------------------------
    def env(self, **overrides: str | None) -> RedactedEnv:
        env = RedactedEnv(os.environ)
        for key in list(env):
            if key.startswith(("JUNIPER_BACKUP_", "DUPLICATI_")):
                env.pop(key, None)
        env["PATH"] = f"{self.stub_bin}{os.pathsep}/usr/bin{os.pathsep}/bin"
        env["HOME"] = str(self.home)
        env["USER"] = FAKE_USER
        env["FAKE_MOUNTS"] = str(self.mounts_file)
        env["FAKE_LINGER_FILE"] = str(self.linger_file)
        env["MOUNTPOINT_LOG"] = str(self.mountpoint_log)
        env["GPG_LOG"] = str(self.gpg_log)
        env["SYSTEMCTL_LOG"] = str(self.systemctl_log)
        for key, value in overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def run(self, argv: list[str], env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(argv, capture_output=True, text=True, env=self.env() if env is None else env, timeout=TIMEOUT_SECONDS, cwd=str(self.root))

    def run_runner(self, *extra: str, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        """The repository runner, ALWAYS with --dry-run: no test ever builds an archive."""
        return self.run(["bash", str(RUNNER), "--dry-run", "--source", str(self.source), "--repos", REPO, *extra], env)

    def run_installer(self, *extra: str, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        return self.run(["bash", str(INSTALLER), *extra], env)

    def install(self) -> None:
        result = self.run_installer()
        if result.returncode != 0:
            raise AssertionError(f"installer failed (rc {result.returncode}):\n{result.stdout}{result.stderr}")

    def run_installed_scheduler(self, *extra: str, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        """Executed directly, as systemd's ExecStart= does: the installed copy must be executable."""
        return self.run([str(self.bin_dir / "juniper-backup-scheduled.bash"), *extra], env)


def _out(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def _build_line(drive_backup_dir: Path) -> str:
    return f"[dry-run]   build  -> {drive_backup_dir}/Juniper_{REPO}_{FAKE_UUID}_"


def _copy_line(drive_backup_dir: Path) -> str:
    return f"[dry-run]   copy   -> {drive_backup_dir}/Juniper_{REPO}_{FAKE_UUID}_"


class TestSyntax(unittest.TestCase):
    def test_bash_syntax(self) -> None:
        for script in (RUNNER, SCHEDULER, REPORTER, INSTALLER):
            with self.subTest(script=script.name):
                result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
                self.assertEqual(result.returncode, 0, msg=result.stderr)


class TestOneSettingTwoReaders(unittest.TestCase):
    """The runner reads the scheduler's three location settings under the same names and defaults."""

    def test_device_list_and_backup_dir_defaults_match_the_scheduler(self) -> None:
        for name in ("JUNIPER_BACKUP_DEVICES", "JUNIPER_BACKUP_DIR"):
            pattern = re.compile(r"\$\{" + name + r":-([^}]*)\}")
            with self.subTest(setting=name):
                scheduler_defaults = pattern.findall(SCHEDULER_TEXT)
                runner_defaults = pattern.findall(RUNNER_TEXT)
                self.assertEqual(len(scheduler_defaults), 1, msg=scheduler_defaults)
                self.assertEqual(runner_defaults, scheduler_defaults)

    def test_media_root_default_is_run_media_user_in_both(self) -> None:
        self.assertIn("${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER}}", SCHEDULER_TEXT)
        self.assertIn("${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER:-$(id -un)}}", RUNNER_TEXT)

    def test_no_code_line_of_the_runner_names_the_retired_media_root(self) -> None:
        offenders = [line for line in _code_lines(RUNNER_TEXT) if re.search(r"(?<!/run)/media/", line) or "MOUNT_NAME" in line or "USER_NAME" in line]
        self.assertEqual(offenders, [])


class TestRunnerMountRoot(unittest.TestCase):
    def test_default_root_is_run_media_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_runner()
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertIn(f"mount root /run/media/{FAKE_USER};", out)
            for device in ("EBC5-F0A3", "DFF3-2782"):
                self.assertIn(f"SKIP {device}: /run/media/{FAKE_USER}/{device} is not a mount point", out)
            self.assertIn("FATAL: no usable destination", out)
            self.assertNotIn("/media/pcalnon", out)
            probed = fx.mountpoint_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(probed, [f"-q /run/media/{FAKE_USER}/EBC5-F0A3", f"-q /run/media/{FAKE_USER}/DFF3-2782"])

    def test_default_root_falls_back_to_id_when_user_is_unset(self) -> None:
        try:
            real_name = pwd.getpwuid(os.getuid()).pw_name
        except KeyError:
            self.skipTest("this uid has no passwd entry, so `id -un` has no name to return")
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_runner(env=fx.env(USER=None))
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertNotIn("unbound variable", out)
            self.assertIn(f"SKIP EBC5-F0A3: /run/media/{real_name}/EBC5-F0A3 is not a mount point", out)

    def test_env_override_moves_the_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.root / "media-root"
            drive = fx.make_drive(media_root / "EBC5-F0A3")
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root)))
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn("OK   EBC5-F0A3", out)
            self.assertIn(f"SKIP DFF3-2782: {media_root}/DFF3-2782 is not a mount point", out)
            self.assertIn(_build_line(drive), out)
            self.assertNotIn("/run/media", out)

    def test_absolute_entry_is_its_own_mount_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.root / "media-root"
            archive_root = fx.root / "mnt" / "JuniperArchive"
            stick = fx.make_drive(media_root / "EBC5-F0A3")
            archive = fx.make_drive(archive_root)
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES=f"EBC5-F0A3 {archive_root}")
            result = fx.run_runner(env=env)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(_build_line(stick), out)
            self.assertIn(_copy_line(archive), out)
            self.assertIn(f"OK   {archive_root}", out)
            probed = fx.mountpoint_log.read_text(encoding="utf-8").splitlines()
            self.assertIn(f"-q {archive_root}", probed)
            # Verbatim, never prefixed with the root.
            self.assertFalse([line for line in probed if line.startswith(f"-q {media_root}/") and str(archive_root) in line], msg=probed)

    def test_absolute_entry_ignores_the_default_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            archive_root = fx.root / "mnt" / "JuniperArchive"
            archive = fx.make_drive(archive_root)
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DEVICES=str(archive_root)))
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(_build_line(archive), out)
            self.assertNotIn("/run/media/", fx.mountpoint_log.read_text(encoding="utf-8"))

    def test_absolute_entry_is_still_mount_checked(self) -> None:
        """The drive's directory exists and is writable; only the guard stands between it and the system disk."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            archive_root = fx.root / "mnt" / "JuniperArchive"
            fx.make_drive(archive_root, mounted=False)
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DEVICES=str(archive_root)))
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertIn(f"SKIP {archive_root}: {archive_root} is not a mount point", out)
            self.assertIn("FATAL: no usable destination", out)

    def test_mounted_root_without_the_backup_dir_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.root / "media-root"
            (media_root / "EBC5-F0A3").mkdir(parents=True)
            fx.mount(media_root / "EBC5-F0A3")
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES="EBC5-F0A3"))
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertIn(f"SKIP EBC5-F0A3: {media_root}/EBC5-F0A3/{BACKUP_DIR} does not exist", out)

    def test_backup_dir_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.root / "media-root"
            drive = fx.make_drive(media_root / "EBC5-F0A3", backup_dir="Juniper-9.0.0.python")
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES="EBC5-F0A3", JUNIPER_BACKUP_DIR="Juniper-9.0.0.python")
            result = fx.run_runner(env=env)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(_build_line(drive), out)

    def test_dry_run_writes_nothing_and_never_encrypts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.root / "media-root"
            archive_root = fx.root / "mnt" / "JuniperArchive"
            fx.make_drive(media_root / "EBC5-F0A3")
            fx.make_drive(archive_root)
            before = (_snapshot(media_root), _snapshot(archive_root), _snapshot(fx.source))
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES=f"EBC5-F0A3 {archive_root}")
            result = fx.run_runner(env=env)
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn("[dry-run] no archives were written.", result.stdout)
            self.assertEqual((_snapshot(media_root), _snapshot(archive_root), _snapshot(fx.source)), before)
            gpg_calls = fx.gpg_log.read_text(encoding="utf-8").splitlines()
            self.assertTrue(gpg_calls)
            self.assertTrue(all(call.startswith("--list-keys ") for call in gpg_calls), msg=gpg_calls)


class TestRunnerDeviceValidation(unittest.TestCase):
    """Environment values land in paths, so a malformed one is misuse (exit 2) before any probe."""

    CASES = {
        "relative device with a slash": {"JUNIPER_BACKUP_DEVICES": "EBC5-F0A3 media/DFF3-2782"},
        "dot-dot device": {"JUNIPER_BACKUP_DEVICES": ".."},
        "blank device list": {"JUNIPER_BACKUP_DEVICES": "   "},
        "relative media root": {"JUNIPER_BACKUP_MEDIA_ROOT": "run/media/somebody"},
        "backup dir escaping the drive": {"JUNIPER_BACKUP_DIR": "../escape"},
    }

    def test_malformed_settings_exit_2_before_any_probe(self) -> None:
        for label, overrides in self.CASES.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier2Fixture(tmp)
                result = fx.run_runner(env=fx.env(**overrides))
                self.assertEqual(result.returncode, 2, msg=_out(result))
                self.assertIn("FATAL:", result.stderr)
                self.assertFalse(fx.mountpoint_log.exists(), msg="a device was probed before validation")
                self.assertFalse(fx.gpg_log.exists(), msg="preflight ran before validation")

    def test_dest_override_ignores_the_device_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            dest = fx.root / "explicit-dest"
            dest.mkdir()
            result = fx.run_runner("--dest", str(dest), env=fx.env(JUNIPER_BACKUP_DEVICES="not/a/name"))
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn(_build_line(dest), result.stdout)
            self.assertFalse(fx.mountpoint_log.exists())


class TestRunnerHelp(unittest.TestCase):
    def test_help_documents_the_shared_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run(["bash", str(RUNNER), "--help"])
            self.assertEqual(result.returncode, 0, msg=_out(result))
            for name in ("JUNIPER_BACKUP_MEDIA_ROOT", "JUNIPER_BACKUP_DEVICES", "JUNIPER_BACKUP_DIR", "/run/media/$USER"):
                self.assertIn(name, result.stdout)
            self.assertNotIn("Exit codes:", result.stdout)


class TestSchedulerRunnerAgreement(unittest.TestCase):
    """End to end through the INSTALLED copies: the scheduler's due run reaches the runner, under one root."""

    def test_due_run_reaches_the_installed_runner_under_the_same_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.install()
            media_root = fx.root / "media-root"
            drive = fx.make_drive(media_root / "EBC5-F0A3")
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root))
            result = fx.run_installed_scheduler("--dry-run", "--source", str(fx.source), "--repos", REPO, env=env)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(f"running {fx.bin_dir}/juniper-backup.bash: mounted=EBC5-F0A3 due=EBC5-F0A3", out)
            self.assertIn(_build_line(drive), out)
            self.assertEqual(_parse_status(fx.state_dir / "last-run.status")["result"], "OK")
            self.assertEqual(list(drive.iterdir()), [])

    def test_both_default_to_run_media_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.install()
            scheduled = fx.run_installed_scheduler()
            self.assertIn(f"no configured drive usable under /run/media/{FAKE_USER}", _out(scheduled))
            runner = fx.run([str(fx.bin_dir / "juniper-backup.bash"), "--dry-run", "--source", str(fx.source), "--repos", REPO])
            self.assertIn(f"SKIP EBC5-F0A3: /run/media/{FAKE_USER}/EBC5-F0A3 is not a mount point", _out(runner))

    def test_unplugged_run_is_failed_until_the_first_success_then_skipped(self) -> None:
        """AC-10's order matters: 'never succeeded' counts as older than STALE_DAYS, so OnFailure= fires."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.install()
            first = fx.run_installed_scheduler()
            self.assertEqual(first.returncode, 1, msg=_out(first))
            status = _parse_status(fx.state_dir / "last-run.status")
            self.assertEqual(status["result"], "FAILED")
            self.assertIn("stale 100000d", status["reason"])
            (fx.state_dir / "last-success.EBC5-F0A3").touch()
            second = fx.run_installed_scheduler()
            self.assertEqual(second.returncode, 0, msg=_out(second))
            self.assertEqual(_parse_status(fx.state_dir / "last-run.status")["result"], "SKIPPED")


class TestFailureUnit(unittest.TestCase):
    def test_unit_routes_the_shared_reporter_to_this_lane(self) -> None:
        self.assertEqual(_unit_values(FAILURE_SERVICE_TEXT, "Type"), ["oneshot"])
        self.assertEqual(_unit_values(FAILURE_SERVICE_TEXT, "Environment"), ["DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup"])
        self.assertEqual(_unit_values(FAILURE_SERVICE_TEXT, "ExecStart"), ["%h/.local/bin/duplicati-backup-failure.bash juniper-backup.service"])

    def test_reporter_does_not_chain_another_onfailure(self) -> None:
        self.assertEqual(_unit_values(FAILURE_SERVICE_TEXT, "OnFailure"), [])

    def test_lane_service_names_this_unit_as_its_onfailure(self) -> None:
        self.assertEqual(_unit_values(SERVICE_TEXT, "OnFailure"), ["juniper-backup-failure.service"])

    def test_state_dir_is_where_the_scheduler_writes_its_status(self) -> None:
        match = re.search(r'STATE_DIR="\$\{JUNIPER_BACKUP_STATE_DIR:-\$\{HOME\}/([^}"]+)\}"', SCHEDULER_TEXT)
        self.assertIsNotNone(match, msg="scheduler STATE_DIR default not found")
        self.assertEqual(_unit_values(FAILURE_SERVICE_TEXT, "Environment"), [f"DUPLICATI_STATE_DIR=%h/{match.group(1)}"])

    def test_unit_as_written_records_into_this_lanes_state_dir(self) -> None:
        """Execute the installed unit's ExecStart= with its Environment=, %h expanded, as systemd would."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.install()
            installed_unit = (fx.unit_dir / "juniper-backup-failure.service").read_text(encoding="utf-8")
            home = str(fx.home)
            (env_value,) = _unit_values(installed_unit, "Environment")
            (exec_value,) = _unit_values(installed_unit, "ExecStart")
            env_key, _, env_path = env_value.replace("%h", home).partition("=")
            argv = shlex.split(exec_value.replace("%h", home))
            fx.state_dir.mkdir(parents=True)
            (fx.state_dir / "last-run.status").write_text("result=FAILED\nwhen=now\nreason=tier-2-reason-marker\n", encoding="utf-8")
            other_lane = fx.home / ".local" / "state" / "duplicati"
            other_lane.mkdir(parents=True)
            (other_lane / "last-run.status").write_text("result=OK\nwhen=then\nreason=duplicati-lane-marker\n", encoding="utf-8")
            (other_lane / "failures.log").write_text("duplicati lane history\n", encoding="utf-8")
            before_other = _snapshot(other_lane)
            result = fx.run(argv, fx.env(**{env_key: env_path}))
            self.assertEqual(result.returncode, 0, msg=_out(result))
            record = (fx.state_dir / "failures.log").read_text(encoding="utf-8")
            self.assertIn("FAILURE  unit=juniper-backup.service", record)
            self.assertIn("reason=tier-2-reason-marker", record)
            self.assertIn("journal-stub-line --user -u juniper-backup.service", record)
            self.assertNotIn("duplicati-lane-marker", record)
            self.assertEqual(_snapshot(other_lane), before_other)


class TestInstaller(unittest.TestCase):
    def _would_run(self, stdout: str) -> list[str]:
        return [line[len("[dry-run] would run: ") :] for line in stdout.splitlines() if line.startswith("[dry-run] would run: ")]

    def test_dry_run_prints_every_action_and_touches_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            before = _snapshot(fx.home)
            result = fx.run_installer("--dry-run")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertEqual(_snapshot(fx.home), before)
            self.assertFalse(fx.systemctl_log.exists(), msg="--dry-run called systemctl")
            actions = self._would_run(result.stdout)
            expected = [f"install -d -m 0755 {fx.bin_dir}"]
            expected += [f"install -m 0755 {UTIL / src} {fx.bin_dir / dst}" for src, dst in INSTALLED_SCRIPTS.items()]
            expected += [f"install -d -m 0755 {fx.unit_dir}"]
            expected += [f"install -m 0644 {UNIT_SRC / unit} {fx.unit_dir / unit}" for unit in INSTALLED_UNITS]
            expected += ["systemctl --user daemon-reload", f"systemctl {ENABLE_LINE}"]
            self.assertEqual(actions, expected)
            self.assertIn("[dry-run] nothing was written.", result.stdout)

    def test_dry_run_reports_what_each_copy_would_replace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.bin_dir.mkdir(parents=True)
            (fx.bin_dir / "juniper-backup.bash").write_text("an older runner\n", encoding="utf-8")
            (fx.bin_dir / "duplicati-backup-failure.bash").write_bytes(REPORTER.read_bytes())
            decoy = fx.root / "checkout-scheduler.bash"
            decoy.write_text("a checkout's file\n", encoding="utf-8")
            (fx.bin_dir / "juniper-backup-scheduled.bash").symlink_to(decoy)
            before = (_snapshot(fx.home), decoy.read_text(encoding="utf-8"))
            result = fx.run_installer("--dry-run")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn("juniper-backup.bash  (changed)", result.stdout)
            self.assertIn("juniper-backup-scheduled.bash  (replaces a symlink)", result.stdout)
            self.assertIn("duplicati-backup-failure.bash  (unchanged)", result.stdout)
            self.assertIn(f"{fx.bin_dir} exists", result.stdout)
            self.assertEqual((_snapshot(fx.home), decoy.read_text(encoding="utf-8")), before)

    def test_install_copies_reloads_and_enables_the_timer_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_installer()
            self.assertEqual(result.returncode, 0, msg=_out(result))
            for src, dst in INSTALLED_SCRIPTS.items():
                installed = fx.bin_dir / dst
                with self.subTest(script=dst):
                    self.assertTrue(installed.is_file() and not installed.is_symlink())
                    self.assertEqual(installed.read_bytes(), (UTIL / src).read_bytes())
                    self.assertEqual(stat.S_IMODE(installed.stat().st_mode), 0o755)
            for unit in INSTALLED_UNITS:
                installed = fx.unit_dir / unit
                with self.subTest(unit=unit):
                    self.assertTrue(installed.is_file() and not installed.is_symlink())
                    self.assertEqual(installed.read_bytes(), (UNIT_SRC / unit).read_bytes())
                    self.assertEqual(stat.S_IMODE(installed.stat().st_mode), 0o644)
            self.assertEqual(fx.systemctl_log.read_text(encoding="utf-8").splitlines(), ["--user daemon-reload", ENABLE_LINE])
            self.assertIn("Do the OK run FIRST", result.stdout)

    def test_install_replaces_a_symlink_without_writing_through_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.bin_dir.mkdir(parents=True)
            decoy = fx.root / "checkout-runner.bash"
            decoy.write_text("a checkout's file\n", encoding="utf-8")
            (fx.bin_dir / "juniper-backup.bash").symlink_to(decoy)
            result = fx.run_installer()
            self.assertEqual(result.returncode, 0, msg=_out(result))
            installed = fx.bin_dir / "juniper-backup.bash"
            self.assertFalse(installed.is_symlink())
            self.assertEqual(installed.read_bytes(), RUNNER.read_bytes())
            self.assertEqual(decoy.read_text(encoding="utf-8"), "a checkout's file\n")

    def test_refuses_root_before_anything(self) -> None:
        for mode in ((), ("--dry-run",)):
            with self.subTest(args=mode), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier2Fixture(tmp)
                fx.stub_root_id()
                before = _snapshot(fx.home)
                result = fx.run_installer(*mode)
                self.assertEqual(result.returncode, 1, msg=_out(result))
                self.assertIn("refusing to run as root", result.stderr)
                self.assertEqual(_snapshot(fx.home), before)
                self.assertFalse(fx.systemctl_log.exists())

    def test_refuses_without_linger_before_writing_anything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.set_linger("no")
            before = _snapshot(fx.home)
            result = fx.run_installer()
            self.assertEqual(result.returncode, 1, msg=_out(result))
            self.assertIn("Linger is NOT enabled", result.stderr)
            self.assertEqual(_snapshot(fx.home), before)
            self.assertFalse(fx.systemctl_log.exists())

    def test_unknown_argument_is_misuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_installer("--now")
            self.assertEqual(result.returncode, 2, msg=_out(result))
            self.assertIn("unknown argument: --now", result.stderr)

    def test_help_prints_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_installer("--help")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn("--dry-run", result.stdout)
            self.assertNotIn("Exit codes:", result.stdout)

    def test_every_name_a_unit_or_the_scheduler_executes_is_installed(self) -> None:
        installed_names = set(INSTALLED_SCRIPTS.values())
        for unit in INSTALLED_UNITS:
            text = (UNIT_SRC / unit).read_text(encoding="utf-8")
            for value in _unit_values(text, "ExecStart"):
                executable = shlex.split(value)[0]
                with self.subTest(unit=unit, exec=executable):
                    self.assertTrue(executable.startswith("%h/.local/bin/"), msg=executable)
                    self.assertIn(executable.rsplit("/", 1)[1], installed_names)
            for key in ("OnFailure", "Unit"):
                for value in _unit_values(text, key):
                    with self.subTest(unit=unit, reference=value):
                        self.assertIn(value, INSTALLED_UNITS)
        runner_default = re.search(r'RUNNER="\$\{JUNIPER_BACKUP_RUNNER:-\$\{HOME\}/\.local/bin/([^}"]+)\}"', SCHEDULER_TEXT)
        self.assertIsNotNone(runner_default, msg="scheduler RUNNER default not found")
        self.assertIn(runner_default.group(1), installed_names)

    def test_installer_never_symlinks(self) -> None:
        self.assertEqual([line for line in _code_lines(INSTALLER_TEXT) if re.search(r"\bln\s+-s", line)], [])


if __name__ == "__main__":
    unittest.main()
