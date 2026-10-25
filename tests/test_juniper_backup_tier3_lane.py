"""Hermetic coverage for the tier-3 full-set lane (backup design §7.9; owner ruling D-5, 2026-10-25).

Tier 3 writes a monthly ``full`` set -- the ten application repos, ``juniper-legacy`` and the parent-level
``notes prompts util backups`` directories -- to the offline drive "Blackbox Part 1" (fstab UUID
dee46823-4119-4914-ac15-08194ee27d81) under ``Juniper/Backups/``. It runs tier 2's runner and scheduler from its
own units, ``util/systemd/juniper-backup-full.{timer,path,service}`` and ``juniper-backup-full-failure.service``,
installed by ``util/install_juniper_backup_timer.bash --lane full``. This suite pins:

* the backup-dir rule both scripts now share: ``JUNIPER_BACKUP_DIR`` may be a relative path of
  ``[A-Za-z0-9._-]+`` components (``Juniper/Backups`` is two); no empty, ``.`` or ``..`` component, no leading
  slash. Every one-component value is judged exactly as before. The scheduler checks it too (it checked
  nothing before), with a function whose body is byte-identical to the runner's, so the two agree on every value;
* the full lane's units, as text and as systemd would run them: their Environment=, the ``--label full --repos``
  the scheduler hands the runner unchanged, the 30-day period and the 45-day staleness limit;
* that the lanes are independent: separate state directories, so separate locks, statuses and stamps. Holding
  one lane's lock never makes the other skip, one lane's success never hides the other's staleness, and with
  every drive mounted each lane writes only its own drives;
* the installer's ``--lane full``: dry run, copies, enable, refusals, acceptance notes, and that it touches no
  tier-2 unit, while no ``--lane`` (or ``--lane usb``) is the tier-2 install exactly.

It reuses ``tests/test_juniper_backup_tier2_lane.py``'s fixture: PATH stubs for ``mountpoint`` / ``gpg`` /
``systemctl`` / ``loginctl`` / ``journalctl`` / ``notify-send``, scratch HOME, source tree and drives, and a staged
lane whose runner's ``DRIVE_PARENTS`` gains the scratch drives directory (that suite pins the one-line difference;
this one stages the four full units beside it, unchanged). No real drive, unit or keyring is touched.
"""

from __future__ import annotations

import fcntl
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import time
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from tests.test_juniper_backup_tier2_lane import DEFAULT_STICKS, FAKE_UUID, INSTALLED_SCRIPTS, INSTALLED_UNITS, REPO, _out, _parse_status, _snapshot, _Tier2Fixture, _unit_values

REPO_ROOT = Path(__file__).resolve().parent.parent
UTIL = REPO_ROOT / "util"
UNIT_SRC = UTIL / "systemd"
RUNNER = UTIL / "juniper-backup.bash"
SCHEDULER = UTIL / "juniper-backup-scheduled.bash"
INSTALLER = UTIL / "install_juniper_backup_timer.bash"

RUNNER_TEXT = RUNNER.read_text(encoding="utf-8")
SCHEDULER_TEXT = SCHEDULER.read_text(encoding="utf-8")
INSTALLER_TEXT = INSTALLER.read_text(encoding="utf-8")

FULL_DEVICE = "dee46823-4119-4914-ac15-08194ee27d81"  # "Ext WD Passport, Blackbox Part 1" in the owner's /etc/fstab
FULL_BACKUP_DIR = "Juniper/Backups"
FULL_LABEL = "full"
EXTRA_CONTENT = ("juniper-legacy", "notes", "prompts", "util", "backups")
FULL_UNITS = ("juniper-backup-full.timer", "juniper-backup-full.path", "juniper-backup-full.service", "juniper-backup-full-failure.service")
FULL_LANE_FILES = tuple(f"util/systemd/{unit}" for unit in FULL_UNITS)
FULL_ENABLE_LINE = "--user enable --now juniper-backup-full.timer juniper-backup-full.path"
FULL_SERVICE_TEXT = (UNIT_SRC / "juniper-backup-full.service").read_text(encoding="utf-8")
FULL_FAILURE_TEXT = (UNIT_SRC / "juniper-backup-full-failure.service").read_text(encoding="utf-8")
FULL_PATH_TEXT = (UNIT_SRC / "juniper-backup-full.path").read_text(encoding="utf-8")
FULL_TIMER_TEXT = (UNIT_SRC / "juniper-backup-full.timer").read_text(encoding="utf-8")
TIER2_SERVICE_TEXT = (UNIT_SRC / "juniper-backup.service").read_text(encoding="utf-8")
TIER2_PATH_TEXT = (UNIT_SRC / "juniper-backup.path").read_text(encoding="utf-8")
TIER2_TIMER_TEXT = (UNIT_SRC / "juniper-backup.timer").read_text(encoding="utf-8")
DAY = 86400

# The backup-dir rule, as cases. Accepted values pass both scripts' validation; refused ones are exit 2 in both.
ACCEPTED_DIRS = ("Juniper/Backups", "Juniper-8.0.0.python", "a/b/c", ".hidden/Backups", "Backups..", "...", "x")
REFUSED_DIRS = {
    "a leading slash": "/Juniper/Backups",
    "a trailing slash": "Juniper/Backups/",
    "a doubled slash": "Juniper//Backups",
    "a dot component": "Juniper/./Backups",
    "a dot-dot component": "Juniper/../Backups",
    "a leading dot-dot": "../Backups",
    "a trailing dot-dot": "Juniper/..",
    "dot-dot alone": "..",
    "dot alone": ".",
    "a lone slash": "/",
    "a space": "Juniper/My Backups",
    "a newline": "Juniper\nBackups",
    "a glob": "Juniper/*",
    "a tilde": "~/Backups",
    "a backslash": "Juniper\\Backups",
}
# One-component strings, for the "judged exactly as before" pin (no slash, so the old rule applies to each).
ONE_COMPONENT = ("Juniper-8.0.0.python", ".", "..", "...", ".x", "x.", "-rf", "a b", "", "a\n", "_", "Juniper$", "a*", "~")


def _runner_application_repos() -> list[str]:
    match = re.search(r"^APPLICATION_REPOS=\( (.*) \)$", RUNNER_TEXT, flags=re.M)
    if match is None:
        raise AssertionError("the runner's APPLICATION_REPOS line was not found")
    return re.findall(r'"([^"]+)"', match.group(1))


FULL_CONTENT = (*_runner_application_repos(), *EXTRA_CONTENT)


def _function_body(text: str, name: str) -> str:
    """The body of a bash function, ``name() {`` or ``function name() {`` through the first ``}`` alone on a line."""
    match = re.search(r"^(?:function )?" + re.escape(name) + r"\(\) \{\n(.*?)\n\}$", text, flags=re.M | re.S)
    if match is None:
        raise AssertionError(f"function {name} not found")
    return match.group(1)


def _unit_environment(text: str, home: str) -> dict[str, str]:
    """A unit's Environment= assignments with %h expanded, as systemd sets them: one unquoted NAME=VALUE per line."""
    parsed: dict[str, str] = {}
    for value in _unit_values(text, "Environment"):
        if any(ch in value for ch in " \"'\\$") or value.count("%") != value.count("%h"):
            raise AssertionError(f"Environment={value} needs systemd's quoting rules, which this parser does not model")
        key, sep, assigned = value.partition("=")
        if not sep or key in parsed:
            raise AssertionError(f"Environment={value} is not one new NAME=VALUE")
        parsed[key] = assigned.replace("%h", home)
    return parsed


def _exec_argv(text: str, home: str) -> list[str]:
    """A unit's single ExecStart= as argv, %h expanded. shlex models systemd only without escapes, $ or other %."""
    (value,) = _unit_values(text, "ExecStart")
    if any(ch in value for ch in "\\$'") or value.count("%") != value.count("%h"):
        raise AssertionError(f"ExecStart={value} needs systemd's quoting rules, which shlex does not model")
    return shlex.split(value.replace("%h", home))


def _bash_verdicts(body: str, values: tuple[str, ...]) -> list[bool]:
    """Run the extracted is_backup_dir body over ``values`` in one bash: True where it accepts."""
    script = "is_backup_dir() {\n" + body + '\n}\nfor value in "$@"; do if is_backup_dir "${value}"; then echo 1; else echo 0; fi; done\n'
    result = subprocess.run(["bash", "-c", script, "verdicts", *values], capture_output=True, text=True, timeout=60, check=True)
    verdicts = result.stdout.split()
    if len(verdicts) != len(values):
        raise AssertionError(f"{len(verdicts)} verdict(s) for {len(values)} value(s): {result.stdout!r} {result.stderr!r}")
    return [verdict == "1" for verdict in verdicts]


def _age(path: Path, days: float) -> None:
    then = time.time() - days * DAY
    os.utime(path, (then, then))


@contextmanager
def _holding(lock: Path) -> Iterator[None]:
    """Hold ``lock`` with flock(2), as a running scheduler does: its ``flock -n 9`` then fails."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class _Tier3Fixture(_Tier2Fixture):
    """The tier-2 fixture, with the full lane's four units staged beside its own (unchanged)."""

    def _stage_lane(self) -> None:
        super()._stage_lane()
        for rel in FULL_LANE_FILES:
            shutil.copy2(REPO_ROOT / rel, self.stage / rel)

    @property
    def full_state_dir(self) -> Path:
        return self.home / ".local" / "state" / "juniper-backup-full"

    @property
    def media_root(self) -> Path:
        return self.drives / "run-media"

    def make_full_source(self) -> None:
        for name in FULL_CONTENT:
            (self.source / name).mkdir(exist_ok=True)
            (self.source / name / "content.txt").write_text(f"{name}\n", encoding="utf-8")

    def make_passport(self, *, backup_dir: str = FULL_BACKUP_DIR) -> Path:
        return self.make_drive(self.media_root / FULL_DEVICE, backup_dir=backup_dir)

    def make_sticks(self) -> list[Path]:
        return [self.make_drive(self.media_root / name) for name in DEFAULT_STICKS]

    def installer_path(self, *, staged: bool) -> Path:
        return self.stage / "util" / "install_juniper_backup_timer.bash" if staged else INSTALLER

    def install_lane(self, *args: str, staged: bool = False) -> subprocess.CompletedProcess[str]:
        return self.run(["bash", str(self.installer_path(staged=staged)), *args])

    def install_full(self, *, staged: bool = True) -> None:
        result = self.install_lane("--lane", "full", staged=staged)
        if result.returncode != 0:
            raise AssertionError(f"installer --lane full failed (rc {result.returncode}):\n{_out(result)}")

    def run_full_service(self, *extra: str, **overrides: str | None) -> subprocess.CompletedProcess[str]:
        """The INSTALLED juniper-backup-full.service, as systemd starts it: its Environment=, then its ExecStart=.

        The scratch drives stand under ``media_root``, so the media root is the one value the test supplies; the unit
        itself relies on the default (``/run/media/$USER``), which TestFullUnits pins.
        """
        unit = (self.unit_dir / "juniper-backup-full.service").read_text(encoding="utf-8")
        values: dict[str, str | None] = dict(_unit_environment(unit, str(self.home)))
        values["JUNIPER_BACKUP_MEDIA_ROOT"] = str(self.media_root)
        values.update(overrides)
        return self.run([*_exec_argv(unit, str(self.home)), *extra], self.env(**values))

    def run_tier2_service(self, *extra: str, **overrides: str | None) -> subprocess.CompletedProcess[str]:
        """The installed juniper-backup.service: no Environment= of its own, so the scheduler's defaults."""
        values: dict[str, str | None] = {"JUNIPER_BACKUP_MEDIA_ROOT": str(self.media_root)}
        values.update(overrides)
        return self.run_installed_scheduler(*extra, env=self.env(**values))

    def write_stub_runner(self) -> Path:
        stub = self.root / "stub-runner.bash"
        stub.write_text('#!/usr/bin/env bash\nprintf \'ran %s\\n\' "$*" >> "${STUB_RUNNER_LOG}"\nexit 0\n', encoding="utf-8")
        stub.chmod(0o755)
        return stub

    def run_repo_scheduler(self, *, backup_dir: str, devices: str = "EBC5-F0A3") -> tuple[subprocess.CompletedProcess[str], Path, Path]:
        """The REPOSITORY scheduler with a stub runner: (result, its state dir, the stub's log)."""
        state = self.root / "scheduler-state"
        log = self.root / "stub-runner.log"
        env = self.env(
            JUNIPER_BACKUP_RUNNER=str(self.write_stub_runner()),
            JUNIPER_BACKUP_STATE_DIR=str(state),
            JUNIPER_BACKUP_MEDIA_ROOT=str(self.media_root),
            JUNIPER_BACKUP_DEVICES=devices,
            JUNIPER_BACKUP_DIR=backup_dir,
            STUB_RUNNER_LOG=str(log),
        )
        return self.run(["bash", str(SCHEDULER)], env), state, log


def _archives(directory: Path) -> list[str]:
    return sorted(path.name for path in directory.iterdir())


def _full_archive(name: str) -> re.Pattern[str]:
    return re.compile(r"Juniper_" + FULL_LABEL + "_" + re.escape(name) + "_" + FAKE_UUID + r"_\d{8}_\d{6}\.\d+-\S+\.tbz2\.gpg")


class TestBackupDirRule(unittest.TestCase):
    """The rule, as code: one function, the same body in the runner and the scheduler."""

    def test_the_function_body_is_byte_identical_in_the_runner_and_the_scheduler(self) -> None:
        runner_body = _function_body(RUNNER_TEXT, "is_backup_dir")
        self.assertTrue(runner_body.strip())
        self.assertEqual(_function_body(SCHEDULER_TEXT, "is_backup_dir"), runner_body)

    def test_each_script_calls_it_on_its_backup_dir(self) -> None:
        for text, name in ((RUNNER_TEXT, "runner"), (SCHEDULER_TEXT, "scheduler")):
            with self.subTest(script=name):
                self.assertEqual(len(re.findall(r'^\s*is_backup_dir "\$\{BACKUP_DIR\}" \|\| \{', text, flags=re.M)), 1)

    def test_accepted_and_refused_forms(self) -> None:
        body = _function_body(RUNNER_TEXT, "is_backup_dir")
        self.assertEqual(_bash_verdicts(body, ACCEPTED_DIRS), [True] * len(ACCEPTED_DIRS))
        refused = tuple(REFUSED_DIRS.values())
        for label, verdict in zip(REFUSED_DIRS, _bash_verdicts(body, refused), strict=True):
            with self.subTest(case=label):
                self.assertFalse(verdict)

    def test_one_component_values_are_judged_exactly_as_before(self) -> None:
        """Tier 2's rule was ``^[A-Za-z0-9._-]+$`` and not ``.`` or ``..``: on a value with no slash, nothing moved."""
        body = _function_body(RUNNER_TEXT, "is_backup_dir")
        for value, verdict in zip(ONE_COMPONENT, _bash_verdicts(body, ONE_COMPONENT), strict=True):
            old = re.fullmatch(r"[A-Za-z0-9._-]+", value) is not None and value not in (".", "..")
            with self.subTest(value=value):
                self.assertEqual(verdict, old)


class TestRunnerBackupDir(unittest.TestCase):
    """The repository's runner, and the staged runner where a scratch drive is needed."""

    def test_refused_forms_exit_2_before_any_probe(self) -> None:
        for label, value in REFUSED_DIRS.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DIR=value))
                self.assertEqual(result.returncode, 2, msg=_out(result))
                self.assertIn("FATAL: JUNIPER_BACKUP_DIR must be a relative path", result.stderr)
                self.assertFalse(fx.mountpoint_log.exists(), msg="a device was probed before validation")
                self.assertFalse(fx.gpg_log.exists(), msg="preflight ran before validation")

    def test_accepted_forms_pass_validation(self) -> None:
        for value in ACCEPTED_DIRS:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                result = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DIR=value))
                self.assertEqual(result.returncode, 1, msg=_out(result))
                self.assertNotIn("JUNIPER_BACKUP_DIR", result.stderr)
                self.assertIn("FATAL: no usable destination", result.stderr)
                self.assertTrue(fx.mountpoint_log.exists(), msg="validation refused an accepted value")

    def test_a_two_component_dir_is_the_build_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            target = fx.make_passport()
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(fx.media_root), JUNIPER_BACKUP_DEVICES=FULL_DEVICE, JUNIPER_BACKUP_DIR=FULL_BACKUP_DIR)
            result = fx.run_runner(env=env, staged=True)
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertEqual(target, fx.media_root / FULL_DEVICE / "Juniper" / "Backups")
            self.assertIn(f"[dry-run]   build  -> {target}/Juniper_{REPO}_{FAKE_UUID}_", result.stdout)

    def test_a_missing_nested_dir_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.make_passport(backup_dir="Juniper")  # the parent exists; Backups does not
            env = fx.env(JUNIPER_BACKUP_MEDIA_ROOT=str(fx.media_root), JUNIPER_BACKUP_DEVICES=FULL_DEVICE, JUNIPER_BACKUP_DIR=FULL_BACKUP_DIR)
            result = fx.run_runner(env=env, staged=True)
            self.assertEqual(result.returncode, 1, msg=_out(result))
            self.assertIn(f"SKIP {FULL_DEVICE}: {fx.media_root / FULL_DEVICE}/{FULL_BACKUP_DIR} does not exist", result.stderr)

    def test_dest_override_ignores_the_backup_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            dest = fx.root / "explicit-dest"
            dest.mkdir()
            result = fx.run_runner("--dest", str(dest), env=fx.env(JUNIPER_BACKUP_DIR="/not/a/relative/path/"))
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn(f"[dry-run]   build  -> {dest}/Juniper_{REPO}_{FAKE_UUID}_", result.stdout)

    def test_help_documents_the_path_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            result = fx.run(["bash", str(RUNNER), "--help"])
            self.assertEqual(result.returncode, 0, msg=_out(result))
            for text in ("JUNIPER_BACKUP_DIR", "joined by single slashes", "none of them . or ..", "Juniper/Backups"):
                self.assertIn(text, result.stdout)


class TestSchedulerBackupDir(unittest.TestCase):
    """The repository's scheduler, with a stub runner that records whether it ran."""

    def test_refused_forms_are_failed_exit_2_before_any_probe(self) -> None:
        for label, value in REFUSED_DIRS.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                result, state, log = fx.run_repo_scheduler(backup_dir=value)
                self.assertEqual(result.returncode, 2, msg=_out(result))
                self.assertIn("FATAL: JUNIPER_BACKUP_DIR must be a relative path", result.stdout)
                status = _parse_status(state / "last-run.status")
                self.assertEqual((status["result"], status["reason"]), ("FAILED", "malformed JUNIPER_BACKUP_DIR"))
                self.assertFalse(fx.mountpoint_log.exists(), msg="a drive was probed before validation")
                self.assertFalse(log.exists(), msg="the runner ran")

    def test_a_two_component_dir_is_judged_usable_and_due(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.make_passport()
            result, state, log = fx.run_repo_scheduler(backup_dir=FULL_BACKUP_DIR, devices=FULL_DEVICE)
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertIn(f"mounted={FULL_DEVICE} due={FULL_DEVICE}", result.stdout)
            self.assertEqual(log.read_text(encoding="utf-8").splitlines(), ["ran "])
            self.assertEqual(_parse_status(state / "last-run.status")["result"], "OK")
            self.assertTrue((state / f"last-success.{FULL_DEVICE}").exists())

    def test_a_missing_nested_dir_is_unusable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.make_passport(backup_dir="Juniper")
            result, _state, log = fx.run_repo_scheduler(backup_dir=FULL_BACKUP_DIR, devices=FULL_DEVICE)
            self.assertEqual(result.returncode, 1, msg=_out(result))  # never succeeded: FAILED, not SKIPPED
            self.assertIn(f"mounted but {FULL_BACKUP_DIR} missing or read-only", result.stdout)
            self.assertIn(f"mounted but unusable: {FULL_DEVICE}", result.stdout)
            self.assertFalse(log.exists())

    def test_runner_and_scheduler_agree_on_every_value(self) -> None:
        for value in (*ACCEPTED_DIRS, *REFUSED_DIRS.values()):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                runner = fx.run_runner(env=fx.env(JUNIPER_BACKUP_DIR=value))
                scheduler, _state, _log = fx.run_repo_scheduler(backup_dir=value)
                self.assertEqual(scheduler.returncode == 2, runner.returncode == 2, msg=_out(runner) + _out(scheduler))


class TestFullUnits(unittest.TestCase):
    """The units as written."""

    def test_service_environment_is_the_lane(self) -> None:
        self.assertEqual(
            _unit_environment(FULL_SERVICE_TEXT, "%h"),
            {
                "JUNIPER_BACKUP_STATE_DIR": "%h/.local/state/juniper-backup-full",
                "JUNIPER_BACKUP_DEVICES": FULL_DEVICE,
                "JUNIPER_BACKUP_DIR": FULL_BACKUP_DIR,
                "JUNIPER_BACKUP_PERIOD_DAYS": "30",
                "JUNIPER_BACKUP_STALE_DAYS": "45",
            },
        )

    def test_service_relies_on_the_default_media_root(self) -> None:
        """The relative device form under /run/media/$USER, which the runner and the scheduler both default to."""
        self.assertNotIn("JUNIPER_BACKUP_MEDIA_ROOT", _unit_environment(FULL_SERVICE_TEXT, "%h"))
        self.assertIn("${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER}}", SCHEDULER_TEXT)
        self.assertIn("${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER:-$(id -un)}}", RUNNER_TEXT)
        self.assertFalse(FULL_DEVICE.startswith("/"))

    def test_service_passes_the_label_and_the_whole_content(self) -> None:
        argv = _exec_argv(FULL_SERVICE_TEXT, "%h")
        self.assertEqual(argv[:4], ["%h/.local/bin/juniper-backup-scheduled.bash", "--label", FULL_LABEL, "--repos"])
        self.assertEqual(len(argv), 5)
        self.assertEqual(argv[4].split(" "), list(FULL_CONTENT))

    def test_the_content_is_the_runners_ten_repos_and_the_five_parent_entries(self) -> None:
        self.assertEqual(len(_runner_application_repos()), 10)
        self.assertEqual(FULL_CONTENT[-5:], EXTRA_CONTENT)
        self.assertEqual(len(set(FULL_CONTENT)), 15)

    def test_stale_days_is_at_least_period_days_in_both_lanes(self) -> None:
        env = _unit_environment(FULL_SERVICE_TEXT, "%h")
        self.assertGreaterEqual(int(env["JUNIPER_BACKUP_STALE_DAYS"]), int(env["JUNIPER_BACKUP_PERIOD_DAYS"]))
        period = re.search(r"\$\{JUNIPER_BACKUP_PERIOD_DAYS:-(\d+)\}", SCHEDULER_TEXT)
        stale = re.search(r"\$\{JUNIPER_BACKUP_STALE_DAYS:-(\d+)\}", SCHEDULER_TEXT)
        self.assertIsNotNone(period)
        self.assertIsNotNone(stale)
        self.assertGreaterEqual(int(stale.group(1)), int(period.group(1)))

    def test_the_drive_and_the_state_dir_are_the_lanes_own(self) -> None:
        env = _unit_environment(FULL_SERVICE_TEXT, "%h")
        self.assertNotIn(env["JUNIPER_BACKUP_DEVICES"], DEFAULT_STICKS)
        default_state = re.search(r'STATE_DIR="\$\{JUNIPER_BACKUP_STATE_DIR:-\$\{HOME\}/([^}"]+)\}"', SCHEDULER_TEXT)
        self.assertIsNotNone(default_state)
        self.assertNotEqual(env["JUNIPER_BACKUP_STATE_DIR"], f"%h/{default_state.group(1)}")
        self.assertEqual(_unit_environment(TIER2_SERVICE_TEXT, "%h"), {})

    def test_service_runs_as_tier_2s_does_apart_from_its_lane(self) -> None:
        def service_keys(text: str) -> list[str]:
            ignored = ("Description=", "OnFailure=", "Environment=", "ExecStart=")
            return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#") and not line.strip().startswith(ignored)]

        self.assertEqual(service_keys(FULL_SERVICE_TEXT), service_keys(TIER2_SERVICE_TEXT))
        self.assertEqual(_unit_values(FULL_SERVICE_TEXT, "Type"), ["oneshot"])
        self.assertEqual(_unit_values(FULL_SERVICE_TEXT, "TimeoutStartSec"), ["infinity"])

    def test_service_fails_to_its_own_reporter(self) -> None:
        self.assertEqual(_unit_values(FULL_SERVICE_TEXT, "OnFailure"), ["juniper-backup-full-failure.service"])

    def test_failure_unit_routes_the_shared_reporter_to_this_lane(self) -> None:
        self.assertEqual(_unit_values(FULL_FAILURE_TEXT, "Type"), ["oneshot"])
        self.assertEqual(_unit_environment(FULL_FAILURE_TEXT, "%h"), {"DUPLICATI_STATE_DIR": "%h/.local/state/juniper-backup-full"})
        self.assertEqual(_unit_values(FULL_FAILURE_TEXT, "ExecStart"), ["%h/.local/bin/duplicati-backup-failure.bash juniper-backup-full.service"])
        self.assertEqual(_unit_values(FULL_FAILURE_TEXT, "OnFailure"), [])

    def test_failure_unit_reads_the_status_the_service_writes(self) -> None:
        self.assertEqual(_unit_environment(FULL_FAILURE_TEXT, "%h")["DUPLICATI_STATE_DIR"], _unit_environment(FULL_SERVICE_TEXT, "%h")["JUNIPER_BACKUP_STATE_DIR"])

    def test_path_unit_watches_tier_2s_directory_with_pathchanged(self) -> None:
        self.assertEqual(_unit_values(FULL_PATH_TEXT, "PathChanged"), _unit_values(TIER2_PATH_TEXT, "PathChanged"))
        self.assertEqual(_unit_values(FULL_PATH_TEXT, "PathChanged"), ["/run/media/pcalnon"])
        self.assertEqual(_unit_values(FULL_PATH_TEXT, "PathExists"), [])
        self.assertEqual(_unit_values(FULL_PATH_TEXT, "Unit"), ["juniper-backup-full.service"])
        self.assertEqual(_unit_values(FULL_PATH_TEXT, "WantedBy"), ["default.target"])

    def test_timer_is_monthly_and_persistent(self) -> None:
        self.assertEqual(_unit_values(FULL_TIMER_TEXT, "OnCalendar"), ["*-*-01 04:00:00"])
        self.assertNotEqual(_unit_values(FULL_TIMER_TEXT, "OnCalendar"), _unit_values(TIER2_TIMER_TEXT, "OnCalendar"))
        self.assertEqual(_unit_values(FULL_TIMER_TEXT, "Persistent"), ["true"])
        self.assertEqual(_unit_values(FULL_TIMER_TEXT, "Unit"), ["juniper-backup-full.service"])
        self.assertEqual(_unit_values(FULL_TIMER_TEXT, "WantedBy"), ["timers.target"])

    def test_every_name_the_full_units_reference_is_the_full_lanes(self) -> None:
        installed_names = set(INSTALLED_SCRIPTS.values())
        for unit in FULL_UNITS:
            text = (UNIT_SRC / unit).read_text(encoding="utf-8")
            for value in _unit_values(text, "ExecStart"):
                executable = shlex.split(value)[0]
                with self.subTest(unit=unit, exec=executable):
                    self.assertTrue(executable.startswith("%h/.local/bin/"), msg=executable)
                    self.assertIn(executable.rsplit("/", 1)[1], installed_names)
            for key in ("OnFailure", "Unit"):
                for value in _unit_values(text, key):
                    with self.subTest(unit=unit, reference=value):
                        self.assertIn(value, FULL_UNITS)


class TestFullLaneEndToEnd(unittest.TestCase):
    """The installed copies, run as systemd runs juniper-backup-full.service."""

    def test_the_ok_run_writes_one_full_archive_per_entry_into_the_nested_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.stub_encrypting_gpg()
            fx.make_full_source()
            fx.install_full()
            target = fx.make_passport()
            result = fx.run_full_service("--source", str(fx.source))
            out = _out(result)
            self.assertEqual(result.returncode, 0, msg=out)
            self.assertIn(f"mounted={FULL_DEVICE} due={FULL_DEVICE}", out)
            self.assertIn("COMPLETE: every configured device holds a verified archive of every repo.", out)
            names = _archives(target)
            self.assertEqual(len(names), len(FULL_CONTENT), msg=names)
            for name in FULL_CONTENT:
                with self.subTest(entry=name):
                    self.assertEqual(len([n for n in names if _full_archive(name).fullmatch(n)]), 1, msg=names)
            status = _parse_status(fx.full_state_dir / "last-run.status")
            self.assertEqual((status["result"], status["reason"]), ("OK", f"devices {FULL_DEVICE}"))
            self.assertEqual(sorted(p.name for p in fx.full_state_dir.glob("last-success.*")), [f"last-success.{FULL_DEVICE}"])
            self.assertFalse(fx.state_dir.exists(), msg="tier 2's state directory was written")

    def test_unplugged_run_is_failed_until_the_first_success_then_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.install_full()
            first = fx.run_full_service()
            self.assertEqual(first.returncode, 1, msg=_out(first))
            status = _parse_status(fx.full_state_dir / "last-run.status")
            self.assertEqual(status["result"], "FAILED")
            self.assertIn(f"no configured drive usable under {fx.media_root} (wanted: {FULL_DEVICE};", status["reason"])
            self.assertIn("stale 100000d", status["reason"])
            (fx.full_state_dir / f"last-success.{FULL_DEVICE}").touch()
            second = fx.run_full_service()
            self.assertEqual(second.returncode, 0, msg=_out(second))
            self.assertEqual(_parse_status(fx.full_state_dir / "last-run.status")["result"], "SKIPPED")

    def test_the_unit_sets_a_45_day_staleness_limit(self) -> None:
        for days, expected in ((45.5, "SKIPPED"), (46.5, "FAILED")):
            with self.subTest(stamp_age_days=days), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                fx.install_full()
                fx.full_state_dir.mkdir(parents=True)
                stamp = fx.full_state_dir / f"last-success.{FULL_DEVICE}"
                stamp.touch()
                _age(stamp, days)
                result = fx.run_full_service()
                self.assertEqual(result.returncode, 0 if expected == "SKIPPED" else 1, msg=_out(result))
                self.assertEqual(_parse_status(fx.full_state_dir / "last-run.status")["result"], expected)

    def test_the_unit_sets_a_30_day_period(self) -> None:
        for days, due in ((29.5, False), (30.5, True)):
            with self.subTest(stamp_age_days=days), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                fx.make_full_source()
                fx.install_full()
                fx.make_passport()
                fx.full_state_dir.mkdir(parents=True)
                stamp = fx.full_state_dir / f"last-success.{FULL_DEVICE}"
                stamp.touch()
                _age(stamp, days)
                result = fx.run_full_service("--dry-run", "--source", str(fx.source))
                out = _out(result)
                self.assertEqual(result.returncode, 0, msg=out)
                if due:
                    self.assertIn(f"due={FULL_DEVICE}", out)
                    self.assertIn("[dry-run] no archives were written.", out)
                else:
                    self.assertIn(f"SKIPPED: mounted ({FULL_DEVICE}) but none due within 30 days", out)
                    self.assertFalse(fx.gpg_log.exists(), msg="the runner ran")

    def test_failure_unit_as_written_records_and_announces_this_lane(self) -> None:
        """Execute the installed failure unit's ExecStart= with its Environment=, %h expanded, as systemd would."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.install_full()
            unit = (fx.unit_dir / "juniper-backup-full-failure.service").read_text(encoding="utf-8")
            fx.full_state_dir.mkdir(parents=True)
            (fx.full_state_dir / "last-run.status").write_text("result=FAILED\nwhen=now\nreason=tier-3-reason-marker\n", encoding="utf-8")
            fx.state_dir.mkdir(parents=True)
            (fx.state_dir / "last-run.status").write_text("result=OK\nwhen=then\nreason=tier-2-marker\n", encoding="utf-8")
            before_tier2 = _snapshot(fx.state_dir)
            result = fx.run(_exec_argv(unit, str(fx.home)), fx.env(**_unit_environment(unit, str(fx.home))))
            self.assertEqual(result.returncode, 0, msg=_out(result))
            record = (fx.full_state_dir / "failures.log").read_text(encoding="utf-8")
            self.assertIn("FAILURE  unit=juniper-backup-full.service", record)
            self.assertIn("reason=tier-3-reason-marker", record)
            self.assertIn("journal-stub-line --user -u juniper-backup-full.service", record)
            self.assertNotIn("tier-2-marker", record)
            self.assertEqual(_snapshot(fx.state_dir), before_tier2)
            self.assertIn("Backup FAILED: juniper-backup-full.service", fx.notify_log.read_text(encoding="utf-8").splitlines())


class TestLaneIndependence(unittest.TestCase):
    """Both path units watch /run/media/<user>, so every mount event starts both lanes: neither may block or skip the other."""

    def test_each_lane_has_its_own_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.stub_encrypting_gpg()
            fx.make_full_source()
            fx.install(staged=True)
            fx.install_full()
            target = fx.make_passport()
            full_lock = fx.full_state_dir / "run.lock"
            with _holding(fx.state_dir / "run.lock"):
                ran = fx.run_full_service("--source", str(fx.source))
            self.assertEqual(ran.returncode, 0, msg=_out(ran))
            self.assertNotIn("another run holds", _out(ran))
            self.assertEqual(len(_archives(target)), len(FULL_CONTENT))
            with _holding(full_lock):
                held = fx.run_full_service("--source", str(fx.source))
                tier2 = fx.run_tier2_service()
            self.assertEqual(held.returncode, 0, msg=_out(held))  # a success stamp is fresh, so SKIPPED
            self.assertEqual(_parse_status(fx.full_state_dir / "last-run.status")["reason"], f"another run holds {full_lock}")
            self.assertEqual(len(_archives(target)), len(FULL_CONTENT), msg="a second set was written under a held lock")
            self.assertNotIn("another run holds", _out(tier2))
            self.assertIn("no configured drive usable", _out(tier2))

    def test_one_lanes_success_never_hides_the_others_staleness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.install(staged=True)
            fx.install_full()
            fx.full_state_dir.mkdir(parents=True)
            (fx.full_state_dir / f"last-success.{FULL_DEVICE}").touch()
            tier2 = fx.run_tier2_service()
            self.assertEqual(tier2.returncode, 1, msg=_out(tier2))
            self.assertIn("stale 100000d", _parse_status(fx.state_dir / "last-run.status")["reason"])
            for path in fx.full_state_dir.glob("last-success.*"):
                path.unlink()
            for stick in DEFAULT_STICKS:
                (fx.state_dir / f"last-success.{stick}").touch()
            full = fx.run_full_service()
            self.assertEqual(full.returncode, 1, msg=_out(full))
            self.assertIn("stale 100000d", _parse_status(fx.full_state_dir / "last-run.status")["reason"])

    def test_with_every_drive_mounted_each_lane_writes_only_its_own(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.stub_encrypting_gpg()
            fx.make_full_source()
            fx.install(staged=True)
            fx.install_full()
            sticks = fx.make_sticks()
            passport = fx.make_passport()
            tier2 = fx.run_tier2_service("--source", str(fx.source), "--repos", REPO)
            full = fx.run_full_service("--source", str(fx.source))
            self.assertEqual((tier2.returncode, full.returncode), (0, 0), msg=_out(tier2) + _out(full))
            for stick in sticks:
                with self.subTest(drive=stick.parent.name):
                    (only,) = _archives(stick)
                    self.assertTrue(only.startswith(f"Juniper_{REPO}_{FAKE_UUID}_"), msg=only)
            names = _archives(passport)
            self.assertEqual(len(names), len(FULL_CONTENT))
            self.assertTrue(all(name.startswith(f"Juniper_{FULL_LABEL}_") for name in names), msg=names)
            self.assertEqual(sorted(p.name for p in fx.state_dir.glob("last-success.*")), sorted(f"last-success.{s}" for s in DEFAULT_STICKS))
            self.assertEqual(sorted(p.name for p in fx.full_state_dir.glob("last-success.*")), [f"last-success.{FULL_DEVICE}"])

    def test_the_full_drive_alone_runs_tier_3_and_leaves_tier_2_to_its_own_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.stub_encrypting_gpg()
            fx.make_full_source()
            fx.install(staged=True)
            fx.install_full()
            passport = fx.make_passport()
            tier2 = fx.run_tier2_service("--source", str(fx.source), "--repos", REPO)
            full = fx.run_full_service("--source", str(fx.source))
            self.assertEqual(tier2.returncode, 1, msg=_out(tier2))  # tier 2 never succeeded and has no stick: FAILED
            self.assertIn("no configured drive usable", _parse_status(fx.state_dir / "last-run.status")["reason"])
            self.assertEqual(full.returncode, 0, msg=_out(full))
            self.assertEqual(_parse_status(fx.full_state_dir / "last-run.status")["result"], "OK")
            self.assertTrue(all(name.startswith(f"Juniper_{FULL_LABEL}_") for name in _archives(passport)))


class TestInstallerLanes(unittest.TestCase):
    FULL_NOTES = (
        "Acceptance (design AC-11, §8 P3 step 3) reads",
        f"{FULL_DEVICE} and hold {FULL_BACKUP_DIR}/",
        "systemctl --user start --no-block juniper-backup-full.service",
        "If the drive was already mounted when you installed, no mount event comes at all",
        "Disconnect the drive only after last-run.status reads result=OK",
        "Retention is MANUAL: keep the last three full sets",
        "Never run juniper-backup-scheduled.bash with --dry-run by hand.",
    )

    def _would_run(self, stdout: str) -> list[str]:
        return [line[len("[dry-run] would run: ") :] for line in stdout.splitlines() if line.startswith("[dry-run] would run: ")]

    def test_full_dry_run_prints_every_action_and_touches_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            before = _snapshot(fx.home)
            result = fx.install_lane("--lane", "full", "--dry-run")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertEqual(_snapshot(fx.home), before)
            self.assertFalse(fx.systemctl_log.exists(), msg="--dry-run called systemctl")
            expected = [f"install -d -m 0755 {fx.bin_dir}"]
            expected += [f"install -m 0755 {UTIL / src} {fx.bin_dir / dst}" for src, dst in INSTALLED_SCRIPTS.items()]
            expected += [f"install -d -m 0755 {fx.unit_dir}"]
            expected += [f"install -m 0644 {UNIT_SRC / unit} {fx.unit_dir / unit}" for unit in FULL_UNITS]
            expected += ["systemctl --user daemon-reload", f"systemctl {FULL_ENABLE_LINE}"]
            self.assertEqual(self._would_run(result.stdout), expected)

    def test_full_install_copies_reloads_and_enables_only_the_full_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            result = fx.install_lane("--lane", "full")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            for src, dst in INSTALLED_SCRIPTS.items():
                installed = fx.bin_dir / dst
                with self.subTest(script=dst):
                    self.assertTrue(installed.is_file() and not installed.is_symlink())
                    self.assertEqual(installed.read_bytes(), (UTIL / src).read_bytes())
                    self.assertEqual(stat.S_IMODE(installed.stat().st_mode), 0o755)
            self.assertEqual(sorted(p.name for p in fx.unit_dir.iterdir()), sorted(FULL_UNITS))
            for unit in FULL_UNITS:
                installed = fx.unit_dir / unit
                with self.subTest(unit=unit):
                    self.assertTrue(installed.is_file() and not installed.is_symlink())
                    self.assertEqual(installed.read_bytes(), (UNIT_SRC / unit).read_bytes())
                    self.assertEqual(stat.S_IMODE(installed.stat().st_mode), 0o644)
            self.assertEqual(fx.systemctl_log.read_text(encoding="utf-8").splitlines(), ["--user daemon-reload", FULL_ENABLE_LINE])

    def test_full_install_leaves_tier_2s_units_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            fx.unit_dir.mkdir(parents=True)
            for unit in INSTALLED_UNITS:
                (fx.unit_dir / unit).write_text(f"# the owner's tier-2 {unit}\n", encoding="utf-8")
            before = {unit: (fx.unit_dir / unit).read_bytes() for unit in INSTALLED_UNITS}
            result = fx.install_lane("--lane", "full")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            self.assertEqual({unit: (fx.unit_dir / unit).read_bytes() for unit in INSTALLED_UNITS}, before)
            self.assertNotIn("juniper-backup.timer", fx.systemctl_log.read_text(encoding="utf-8"))

    def test_usb_is_the_default_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            default = fx.install_lane("--dry-run")
            usb = fx.install_lane("--lane", "usb", "--dry-run")
            self.assertEqual((default.returncode, usb.returncode), (0, 0), msg=_out(default) + _out(usb))
            self.assertEqual((usb.stdout, usb.stderr), (default.stdout, default.stderr))
            self.assertNotIn("juniper-backup-full", default.stdout)
            self.assertNotIn("AC-11", default.stdout)

    def test_unknown_or_missing_lane_is_misuse_and_writes_nothing(self) -> None:
        for args in (("--lane", "tier3"), ("--lane", "FULL"), ("--lane",), ("--lane", ""), ("--lane", "full", "--lane", "nope")):
            with self.subTest(args=args), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                before = _snapshot(fx.home)
                result = fx.install_lane(*args)
                self.assertEqual(result.returncode, 2, msg=_out(result))
                self.assertRegex(result.stderr, r"(unknown lane|--lane requires)")
                self.assertEqual(_snapshot(fx.home), before)
                self.assertFalse(fx.systemctl_log.exists())

    def test_full_acceptance_notes_print_in_both_modes(self) -> None:
        for args in (("--lane", "full", "--dry-run"), ("--lane", "full")):
            with self.subTest(args=args), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                result = fx.install_lane(*args)
                self.assertEqual(result.returncode, 0, msg=_out(result))
                for note in self.FULL_NOTES:
                    self.assertIn(note, result.stdout)
                self.assertIn(f"reads {fx.full_state_dir}/last-run.status", result.stdout)
                self.assertNotIn("EBC5-F0A3", result.stdout)

    def test_the_notes_name_the_units_drive_and_dir(self) -> None:
        env = _unit_environment(FULL_SERVICE_TEXT, "%h")
        self.assertIn(f"/{env['JUNIPER_BACKUP_DEVICES']} and hold {env['JUNIPER_BACKUP_DIR']}/", INSTALLER_TEXT)
        self.assertIn(f"due {env['JUNIPER_BACKUP_PERIOD_DAYS']} days after the last success", INSTALLER_TEXT)

    def test_full_lane_refuses_root_and_missing_linger_before_writing(self) -> None:
        for refusal in ("root", "linger"):
            with self.subTest(refusal=refusal), tempfile.TemporaryDirectory() as tmp:
                fx = _Tier3Fixture(tmp)
                if refusal == "root":
                    fx.stub_root_id()
                else:
                    fx.set_linger("no")
                before = _snapshot(fx.home)
                result = fx.install_lane("--lane", "full")
                self.assertEqual(result.returncode, 1, msg=_out(result))
                self.assertIn("refusing to run as root" if refusal == "root" else "Linger is NOT enabled", result.stderr)
                self.assertEqual(_snapshot(fx.home), before)
                self.assertFalse(fx.systemctl_log.exists())

    def test_full_lane_refuses_a_missing_unit_source_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            (fx.stage / "util" / "systemd" / "juniper-backup-full-failure.service").unlink()
            before = _snapshot(fx.home)
            result = fx.install_lane("--lane", "full", staged=True)
            self.assertEqual(result.returncode, 1, msg=_out(result))
            self.assertIn("source missing:", result.stderr)
            self.assertIn("juniper-backup-full-failure.service", result.stderr)
            self.assertEqual(_snapshot(fx.home), before)
            usb = fx.install_lane("--dry-run", staged=True)
            self.assertEqual(usb.returncode, 0, msg=_out(usb))  # tier 2 does not need the full lane's files

    def test_help_documents_the_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            result = fx.install_lane("--help")
            self.assertEqual(result.returncode, 0, msg=_out(result))
            for text in ("--lane usb|full", "--lane usb", "--lane full", "--dry-run"):
                self.assertIn(text, result.stdout)
            self.assertNotIn("Exit codes:", result.stdout)


class TestStageFidelity(unittest.TestCase):
    def test_the_full_units_are_staged_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Tier3Fixture(tmp)
            for rel in FULL_LANE_FILES:
                with self.subTest(file=rel):
                    self.assertEqual((fx.stage / rel).read_bytes(), (REPO_ROOT / rel).read_bytes())


if __name__ == "__main__":
    unittest.main()
