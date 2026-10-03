"""Hermetic coverage for the tier-2 USB archive lane (recovery plan B6 / I-20; backup design §7.8, §8 P3).

Tier 2 could not find its drives from 2026-09-07: udisks2 2.10.91 moved removable-media automounts from
/media/<user> to /run/media/<user>, while util/juniper-backup.bash still forced /media/pcalnon/<name>. Its
scheduler, util/juniper-backup-scheduled.bash, already looked under /run/media, so every run the scheduler
judged due would have ended in the runner's "no usable destination". This suite pins the fix and the lane's
two new artifacts:

* the runner's mount root: JUNIPER_BACKUP_MEDIA_ROOT (default /run/media/$USER), read under the same name
  and default as the scheduler; an absolute JUNIPER_BACKUP_DEVICES entry used verbatim; the mount guard
  applying to both forms; and the bound the mount guard cannot provide -- every device's mount root must lie
  under /mnt, /media or /run/media, because ``mountpoint -q`` is true of /, /home, /tmp and /run/user/<uid> too;
* scheduler -> runner agreement, end to end through the copies the installer puts in ~/.local/bin, including
  the acceptance run: result=OK needs EVERY configured stick, and one of two is rc 4 -> FAILED, no stamp;
* juniper-backup-failure.service: the shared reporter records into THIS lane's state directory and titles its
  notification with this lane's unit;
* util/install_juniper_backup_timer.bash: --dry-run writes nothing and still prints the acceptance notes,
  root is refused, a refusal leaves nothing half-installed, copies never symlinks, and the timer and the
  path unit are enabled.

No real drive is ever touched. ``mountpoint`` is a PATH stub that answers from a list of scratch paths and
stats nothing; gpg / uuidgen / bc / systemctl / loginctl / journalctl / notify-send are stubs; every HOME,
source tree and "drive" is a directory under a TemporaryDirectory. Runner invocations are --dry-run, refused
before they build, or -- in the acceptance test only -- a full run whose gpg stub writes a marker file into a
scratch drive.

THE STAGED LANE. Scratch drives live under /tmp, which the runner's DRIVE_PARENTS bound (/mnt /media
/run/media) refuses, correctly, and the bound is deliberately not a setting. So the fixture stages a copy of
the lane whose runner differs from the repository's by ONE line: DRIVE_PARENTS gains the fixture's scratch
``drives`` directory. Tests that need a scratch drive run the staged lane; the bound itself, the defaults,
validation and the installer run the repository's files. ``test_the_stage_differs_from_the_repo_by_one_line``
keeps that difference honest. util/ is outside every pre-commit Python hook, so this unittest is the gate.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import pwd
import re
import shlex
import shutil
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
DEFAULT_STICKS = ("EBC5-F0A3", "DFF3-2782")

# Repository file under util/ -> the name the installer gives it in ~/.local/bin.
INSTALLED_SCRIPTS = {
    "juniper-backup.bash": "juniper-backup.bash",
    "juniper-backup-scheduled.bash": "juniper-backup-scheduled.bash",
    "duplicati_backup_failure.bash": "duplicati-backup-failure.bash",
}
INSTALLED_UNITS = ("juniper-backup.timer", "juniper-backup.path", "juniper-backup.service", "juniper-backup-failure.service")
ENABLE_LINE = "--user enable --now juniper-backup.timer juniper-backup.path"

# The lane as the fixture stages it, and the one line it changes in the staged runner.
LANE_FILES = (
    "util/juniper-backup.bash",
    "util/juniper-backup-scheduled.bash",
    "util/duplicati_backup_failure.bash",
    "util/install_juniper_backup_timer.bash",
    "util/systemd/juniper-backup.timer",
    "util/systemd/juniper-backup.path",
    "util/systemd/juniper-backup.service",
    "util/systemd/juniper-backup-failure.service",
)
DRIVE_PARENTS_LINE = 'DRIVE_PARENTS=( "/mnt" "/media" "/run/media" )'
BOUND_MESSAGE = "is not strictly under /mnt /media /run/media"

# A gpg that "encrypts": it consumes the tar stream and writes a marker where -o points, and answers
# --list-packets with the two recipient packets verify_archive counts. Used by the acceptance test only.
ENCRYPTING_GPG = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >> "${GPG_LOG:-/dev/null}"
case "${1:-}" in
    --list-keys) exit 0 ;;
    --list-packets) printf ':pubkey enc packet: a\n:pubkey enc packet: b\n'; exit 0 ;;
esac
out=""
while (( $# > 0 )); do
    [[ "$1" == "-o" ]] && out="$2"
    shift
done
[[ -n "${out}" ]] || { echo "gpg stub: no -o" >&2; exit 97; }
cat > /dev/null
printf 'stub-ciphertext\n' > "${out}"
"""


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
    """A scratch HOME, a one-repo source tree, scratch "drives", PATH stubs and a staged lane. Nothing real is touched."""

    def __init__(self, tmpdir: str) -> None:
        self.root = Path(tmpdir)
        self.stub_bin = self.root / "stubs"
        self.home = self.root / "home"
        self.source = self.root / "source"
        self.drives = self.root / "drives"  # stands in for /run/media, /mnt and /media: the staged runner's extra parent
        self.stage = self.root / "lane"
        self.mounts_file = self.root / "fake-mounts.txt"
        self.linger_file = self.root / "linger.txt"
        self.mountpoint_log = self.root / "mountpoint.log"
        self.gpg_log = self.root / "gpg.log"
        self.systemctl_log = self.root / "systemctl.log"
        self.notify_log = self.root / "notify-send.log"
        self.stub_bin.mkdir()
        self.home.mkdir()
        self.drives.mkdir()
        (self.source / REPO).mkdir(parents=True)
        (self.source / REPO / "README.md").write_text("scratch repository\n", encoding="utf-8")
        self.mounts_file.write_text("", encoding="utf-8")
        self.set_linger("yes")
        self._write_stubs()
        self._stage_lane()

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

    @property
    def staged_runner(self) -> Path:
        return self.stage / "util" / "juniper-backup.bash"

    # --- the staged lane ---------------------------------------------------------------------------------
    def _stage_lane(self) -> None:
        """Copy the lane; the staged runner's DRIVE_PARENTS also accepts self.drives, and nothing else differs.

        A runner without the line (the pre-change runner under the mutation check) is staged unpatched, so the
        suite fails on its behaviour rather than here; the text pin below asserts the line in the real file.
        """
        for rel in LANE_FILES:
            target = self.stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / rel, target)
        text = self.staged_runner.read_text(encoding="utf-8")
        count = text.count(DRIVE_PARENTS_LINE)
        if count > 1:
            raise AssertionError(f"{DRIVE_PARENTS_LINE!r} appears {count} times in the runner")
        if count == 1:
            widened = DRIVE_PARENTS_LINE[: -len(")")] + f'"{self.drives}" )'
            self.staged_runner.write_text(text.replace(DRIVE_PARENTS_LINE, widened), encoding="utf-8")

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
            # Every argument on its own line, so a test can see the title it was given.
            printf '%s\\n' "$@" >> "${NOTIFY_LOG:-/dev/null}"
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

    def stub_encrypting_gpg(self) -> None:
        _write_executable(self.stub_bin / "gpg", ENCRYPTING_GPG)

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
        env["NOTIFY_LOG"] = str(self.notify_log)
        for key, value in overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def run(self, argv: list[str], env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(argv, capture_output=True, text=True, env=self.env() if env is None else env, timeout=TIMEOUT_SECONDS, cwd=str(self.root))

    def run_runner(self, *extra: str, env: RedactedEnv | None = None, staged: bool = False) -> subprocess.CompletedProcess[str]:
        """The runner, ALWAYS with --dry-run. The repository's file unless ``staged`` (scratch drives need the stage)."""
        runner = self.staged_runner if staged else RUNNER
        return self.run(["bash", str(runner), "--dry-run", "--source", str(self.source), "--repos", REPO, *extra], env)

    def run_installer(self, *extra: str, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        """The repository's installer: it installs the repository's files."""
        return self.run(["bash", str(INSTALLER), *extra], env)

    def install(self, *, staged: bool = False) -> None:
        """Install the lane; ``staged`` installs the staged copy, whose runner accepts the scratch drives."""
        installer = self.stage / "util" / "install_juniper_backup_timer.bash" if staged else INSTALLER
        result = self.run(["bash", str(installer)])
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

    def test_drive_parents_is_one_literal_of_the_design_roots(self) -> None:
        """The bound is a literal list assigned once -- not a setting the environment could widen."""
        self.assertEqual(RUNNER_TEXT.count(DRIVE_PARENTS_LINE), 1)
        self.assertEqual([line for line in _code_lines(RUNNER_TEXT) if "DRIVE_PARENTS=" in line or "DRIVE_PARENTS+=" in line], [DRIVE_PARENTS_LINE])

    def test_the_stage_differs_from_the_repo_by_one_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            for rel in LANE_FILES:
                repo_lines = (REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
                staged_lines = (fx.stage / rel).read_text(encoding="utf-8").splitlines()
                changed = [line for line in difflib.unified_diff(repo_lines, staged_lines, lineterm="", n=0) if line[:1] in "+-" and line[:3] not in ("+++", "---")]
                with self.subTest(file=rel):
                    if rel == "util/juniper-backup.bash":
                        self.assertEqual(changed, [f"-{DRIVE_PARENTS_LINE}", f'+DRIVE_PARENTS=( "/mnt" "/media" "/run/media" "{fx.drives}" )'])
                    else:
                        self.assertEqual(changed, [])


class TestRunnerMountRoot(unittest.TestCase):
    def test_default_root_is_run_media_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_runner()
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertIn(f"mount root /run/media/{FAKE_USER};", out)
            for device in DEFAULT_STICKS:
                self.assertIn(f"SKIP {device}: /run/media/{FAKE_USER}/{device} is not a mount point", out)
            self.assertIn("FATAL: no usable destination", out)
            self.assertNotIn("/media/pcalnon", out)
            probed = fx.mountpoint_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(probed, [f"-q /run/media/{FAKE_USER}/EBC5-F0A3", f"-q /run/media/{FAKE_USER}/DFF3-2782"])

    def test_default_root_falls_back_to_id_when_user_is_unset(self) -> None:
        try:
            real_name = pwd.getpwuid(os.getuid()).pw_name
        except KeyError as exc:
            # raise, not self.skipTest(): the same SkipTest, but a path CodeQL can see ends here.
            raise unittest.SkipTest("this uid has no passwd entry, so `id -un` has no name to return") from exc
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
            media_root = fx.drives / "run-media"
            drive = fx.make_drive(media_root / "EBC5-F0A3")
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root)), staged=True)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn("OK   EBC5-F0A3", out)
            self.assertIn(f"SKIP DFF3-2782: {media_root}/DFF3-2782 is not a mount point", out)
            self.assertIn(_build_line(drive), out)
            self.assertNotIn("/run/media", out)

    def test_absolute_entry_is_its_own_mount_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.drives / "run-media"
            archive_root = fx.drives / "mnt" / "JuniperArchive"
            stick = fx.make_drive(media_root / "EBC5-F0A3")
            archive = fx.make_drive(archive_root)
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES=f"EBC5-F0A3 {archive_root}")
            result = fx.run_runner(env=env, staged=True)
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
            archive_root = fx.drives / "mnt" / "JuniperArchive"
            archive = fx.make_drive(archive_root)
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DEVICES=str(archive_root)), staged=True)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(_build_line(archive), out)
            self.assertNotIn("/run/media/", fx.mountpoint_log.read_text(encoding="utf-8"))

    def test_absolute_entry_inside_the_bound_is_still_mount_checked(self) -> None:
        """Inside the bound the mount guard still applies: an unmounted drive directory is skipped, not written."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            archive_root = fx.drives / "mnt" / "JuniperArchive"
            fx.make_drive(archive_root, mounted=False)
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DEVICES=str(archive_root)), staged=True)
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertIn(f"SKIP {archive_root}: {archive_root} is not a mount point", out)
            self.assertIn("FATAL: no usable destination", out)

    def test_mounted_root_without_the_backup_dir_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.drives / "run-media"
            (media_root / "EBC5-F0A3").mkdir(parents=True)
            fx.mount(media_root / "EBC5-F0A3")
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES="EBC5-F0A3"), staged=True)
            out = _out(result)
            self.assertEqual(result.returncode, 1, msg=out)
            self.assertIn(f"SKIP EBC5-F0A3: {media_root}/EBC5-F0A3/{BACKUP_DIR} does not exist", out)

    def test_backup_dir_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.drives / "run-media"
            drive = fx.make_drive(media_root / "EBC5-F0A3", backup_dir="Juniper-9.0.0.python")
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES="EBC5-F0A3", JUNIPER_BACKUP_DIR="Juniper-9.0.0.python")
            result = fx.run_runner(env=env, staged=True)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(_build_line(drive), out)

    def test_dry_run_writes_nothing_and_never_encrypts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            media_root = fx.drives / "run-media"
            archive_root = fx.drives / "mnt" / "JuniperArchive"
            fx.make_drive(media_root / "EBC5-F0A3")
            fx.make_drive(archive_root)
            before = (_snapshot(fx.drives), _snapshot(fx.source))
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root), JUNIPER_BACKUP_DEVICES=f"EBC5-F0A3 {archive_root}")
            result = fx.run_runner(env=env, staged=True)
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn("[dry-run] no archives were written.", result.stdout)
            self.assertEqual((_snapshot(fx.drives), _snapshot(fx.source)), before)
            gpg_calls = fx.gpg_log.read_text(encoding="utf-8").splitlines()
            self.assertTrue(gpg_calls)
            self.assertTrue(all(call.startswith("--list-keys ") for call in gpg_calls), msg=gpg_calls)


class TestDriveBound(unittest.TestCase):
    """The repository's runner: every device's mount root must lie strictly under /mnt, /media or /run/media.

    `mountpoint -q` is TRUE of /, /home, /tmp, /run and /run/user/<uid> on an ordinary host, so the mount
    guard cannot keep an archive off the system disk. Validation is lexical and runs before any probe, so
    naming a system path here touches nothing.
    """

    REFUSED = {
        "the root filesystem": {"JUNIPER_BACKUP_DEVICES": "/"},
        "/home": {"JUNIPER_BACKUP_DEVICES": "/home"},
        "/tmp": {"JUNIPER_BACKUP_DEVICES": "/tmp"},
        "a user runtime tmpfs": {"JUNIPER_BACKUP_DEVICES": "/run/user/1000"},
        "a design root itself, not under it": {"JUNIPER_BACKUP_DEVICES": "/mnt"},
        "a walk out of /mnt": {"JUNIPER_BACKUP_DEVICES": "/mnt/../home"},
        "a padded path": {"JUNIPER_BACKUP_DEVICES": "/mnt//JuniperArchive"},
        "a dot component": {"JUNIPER_BACKUP_DEVICES": "/mnt/./JuniperArchive"},
        "a lookalike parent": {"JUNIPER_BACKUP_DEVICES": "/mediax/stick"},
        "a trailing slash": {"JUNIPER_BACKUP_DEVICES": "/mnt/JuniperArchive/"},
        "the relative form through root /": {"JUNIPER_BACKUP_MEDIA_ROOT": "/", "JUNIPER_BACKUP_DEVICES": "tmp"},
        "the relative form through /run/user": {"JUNIPER_BACKUP_MEDIA_ROOT": "/run/user", "JUNIPER_BACKUP_DEVICES": "1000"},
        "the relative form through /home": {"JUNIPER_BACKUP_MEDIA_ROOT": "/home", "JUNIPER_BACKUP_DEVICES": "pcalnon"},
    }

    def test_system_paths_and_walks_out_are_refused_before_any_probe(self) -> None:
        for label, overrides in self.REFUSED.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier2Fixture(tmp)
                result = fx.run_runner(env=fx.env(**overrides))
                self.assertEqual(result.returncode, 2, msg=_out(result))
                self.assertIn(BOUND_MESSAGE, result.stderr)
                self.assertFalse(fx.mountpoint_log.exists(), msg="a device was probed before the bound")
                self.assertFalse(fx.gpg_log.exists(), msg="preflight ran before the bound")

    def test_a_mounted_system_path_with_a_ready_backup_dir_is_refused(self) -> None:
        """The review's case: the guard says mounted, the directory exists and is writable -- still refused."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            system_mount = fx.root / "system-mount"  # under the scratch /tmp: a system tmpfs, outside the bound
            fx.make_drive(system_mount)  # mounted per the stub, with a writable Juniper-8.0.0.python
            before = _snapshot(system_mount)
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DEVICES=str(system_mount)))
            self.assertEqual(result.returncode, 2, msg=_out(result))
            self.assertIn(f"device {system_mount}: mount root {system_mount} {BOUND_MESSAGE}", result.stderr)
            self.assertNotIn("[dry-run]", result.stdout)
            self.assertFalse(fx.mountpoint_log.exists())
            self.assertEqual(_snapshot(system_mount), before)

    def test_the_design_roots_are_accepted(self) -> None:
        """Inside the bound, validation passes and the mount guard decides (the stub says nothing is mounted)."""
        cases = {
            "an fstab drive under /mnt (design §7.9)": ({"JUNIPER_BACKUP_DEVICES": "/mnt/JuniperArchive"}, "/mnt/JuniperArchive"),
            "a hand mount under /media": ({"JUNIPER_BACKUP_DEVICES": "/media/b6/stick"}, "/media/b6/stick"),
            "an absolute udisks2 path": ({"JUNIPER_BACKUP_DEVICES": f"/run/media/{FAKE_USER}/EBC5-F0A3"}, f"/run/media/{FAKE_USER}/EBC5-F0A3"),
            "the scheduler-compatible fstab form": ({"JUNIPER_BACKUP_MEDIA_ROOT": "/mnt", "JUNIPER_BACKUP_DEVICES": "JuniperArchive"}, "/mnt/JuniperArchive"),
        }
        for label, (overrides, mount_root) in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier2Fixture(tmp)
                result = fx.run_runner(env=fx.env(**overrides))
                self.assertEqual(result.returncode, 1, msg=_out(result))
                self.assertNotIn(BOUND_MESSAGE, result.stderr)
                self.assertIn(f"{mount_root} is not a mount point", result.stderr)
                self.assertEqual(fx.mountpoint_log.read_text(encoding="utf-8").splitlines(), [f"-q {mount_root}"])


class TestRunnerDeviceValidation(unittest.TestCase):
    """Environment values land in paths, so a malformed one is misuse (exit 2) before any probe."""

    CASES = {
        "relative device with a slash": {"JUNIPER_BACKUP_DEVICES": "EBC5-F0A3 media/DFF3-2782"},
        "dot-dot device": {"JUNIPER_BACKUP_DEVICES": ".."},
        "blank device list": {"JUNIPER_BACKUP_DEVICES": "   "},
        "a newline in the device list": {"JUNIPER_BACKUP_DEVICES": "EBC5-F0A3\nDFF3-2782"},
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

    def test_a_newline_is_refused_by_name(self) -> None:
        """`read -r -a` keeps the first line only; the scheduler would silently skip the rest."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DEVICES="EBC5-F0A3\nDFF3-2782"))
            self.assertEqual(result.returncode, 2, msg=_out(result))
            self.assertIn("must be ONE line", result.stderr)

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
            for text in ("JUNIPER_BACKUP_MEDIA_ROOT", "JUNIPER_BACKUP_DEVICES", "JUNIPER_BACKUP_DIR", "/run/media/$USER", "/mnt/, /media/", "ONE line", "exits 4 (PARTIAL)"):
                self.assertIn(text, result.stdout)
            self.assertNotIn("Exit codes:", result.stdout)


class TestSchedulerRunnerAgreement(unittest.TestCase):
    """End to end through the INSTALLED copies: the scheduler's due run reaches the runner, under one root."""

    def test_due_run_reaches_the_installed_runner_under_the_same_root(self) -> None:
        """Asserts on the RUNNER's output. A --dry-run through the scheduler also stamps a success (the scheduler
        stamps on rc 0), which is why the docs say never to do it by hand; this test does not bless that stamp."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            fx.install(staged=True)
            media_root = fx.drives / "run-media"
            drive = fx.make_drive(media_root / "EBC5-F0A3")
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root))
            result = fx.run_installed_scheduler("--dry-run", "--source", str(fx.source), "--repos", REPO, env=env)
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(f"running {fx.bin_dir}/juniper-backup.bash: mounted=EBC5-F0A3 due=EBC5-F0A3", out)
            self.assertIn("OK   EBC5-F0A3", out)
            self.assertIn(_build_line(drive), out)
            self.assertIn("[dry-run] no archives were written.", out)
            self.assertEqual(list(drive.iterdir()), [])

    def test_the_ok_run_needs_every_configured_stick(self) -> None:
        """BLOCKER-1 of the review, as an executable spec of the acceptance instruction. A FULL run through the
        installed copies, with a gpg stub that writes the archive into the scratch drive:
        one of the two default sticks -> the runner writes it and exits 4 (PARTIAL), the scheduler records FAILED
        and stamps nothing; both sticks -> OK, both stamped."""
        for mounted, expected_rc in ((DEFAULT_STICKS[:1], 4), (DEFAULT_STICKS, 0)):
            with self.subTest(mounted=mounted), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier2Fixture(tmp)
                fx.stub_encrypting_gpg()
                fx.install(staged=True)
                media_root = fx.drives / "run-media"
                drives = [fx.make_drive(media_root / name) for name in mounted]
                env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(media_root))
                result = fx.run_installed_scheduler("--source", str(fx.source), "--repos", REPO, env=env)
                out = _out(result)
                self.assertEqual(result.returncode, expected_rc, msg=out)
                status = _parse_status(fx.state_dir / "last-run.status")
                stamps = sorted(p.name for p in fx.state_dir.glob("last-success.*"))
                for drive in drives:
                    self.assertEqual(len(list(drive.iterdir())), 1, msg=f"{drive}: {out}")
                if expected_rc == 0:
                    self.assertEqual(status["result"], "OK")
                    self.assertEqual(stamps, sorted(f"last-success.{name}" for name in DEFAULT_STICKS))
                    self.assertIn("COMPLETE: every configured device holds a verified archive", out)
                else:
                    self.assertEqual((status["result"], status["reason"]), ("FAILED", "runner rc=4"))
                    self.assertEqual(stamps, [])
                    self.assertIn("PARTIAL: redundancy is degraded -- 1 of 2 expected archive copies were written.", out)

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

    def test_unit_as_written_records_and_announces_this_lane(self) -> None:
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
            # The announce half names this lane, not the Duplicati one (review DEFECT-3).
            notification = fx.notify_log.read_text(encoding="utf-8").splitlines()
            self.assertIn("Backup FAILED: juniper-backup.service", notification)
            self.assertFalse([line for line in notification if "Duplicati" in line], msg=notification)

    def test_the_default_caller_is_titled_for_its_own_unit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            state = fx.root / "duplicati-state"
            result = fx.run(["bash", str(REPORTER)], fx.env(DUPLICATI_STATE_DIR=str(state)))
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn("Backup FAILED: duplicati-backup.service", fx.notify_log.read_text(encoding="utf-8").splitlines())


class TestInstaller(unittest.TestCase):
    ACCEPTANCE_NOTES = (
        "Do the OK run FIRST, with BOTH configured sticks mounted (by default EBC5-F0A3 and DFF3-2782).",
        "the runner writes it and exits 4 (PARTIAL), the scheduler records",
        "Never run juniper-backup-scheduled.bash with --dry-run by hand.",
    )

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

    def test_dry_run_prints_the_acceptance_notes_too(self) -> None:
        """The preview an operator reads first carries the order and the two-stick requirement (review NIT-4)."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier2Fixture(tmp)
            result = fx.run_installer("--dry-run")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            for note in self.ACCEPTANCE_NOTES:
                self.assertIn(note, result.stdout)

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
            for note in self.ACCEPTANCE_NOTES:
                self.assertIn(note, result.stdout)

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
