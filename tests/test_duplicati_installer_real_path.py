#!/usr/bin/env python3
"""The Duplicati installer's REAL path (not ``--dry-run``), and the server-DB snapshot's WAL residue.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License
Created:     2026-10-08 (Phase B round-3 fold-in, lane C1; R3C D-5, N-7, N-8)

Why this suite exists. Round 3's lane C mutated the fold-in's code and found that the suites never
ran ``util/install_duplicati_service.bash`` without ``--dry-run``: the dry run prints each
``act`` DESCRIPTION, so replacing the drift copy-aside's real ``cp -p`` with ``true`` (its M20)
survived every suite while ``docs/REFERENCE.md`` said the suite "pins" that drift is kept as
evidence. Here the installer runs for real, as a non-root user, against a scratch install prefix
(``DUPLICATI_INSTALL_PREFIX``), with PATH stubs in place of the commands that need root or touch
the host:

* ``id`` answers ``-u`` with 0 (so the root check passes) and is the real ``id`` otherwise;
* ``install`` drops ``-o``/``-g`` (ownership needs root), refuses any path outside the scratch root, and runs the real
  ``install`` on scratch paths -- modes are kept and asserted;
* ``systemctl`` and ``systemd-analyze`` only log their argv (nothing is reloaded or verified);
* ``stat -c %U:%a`` (and ``%U:%G:%a``) answers for the scratch data folder, credential and env file only (their real owner
  is the test user), and is the real ``stat`` otherwise.

Hermetic, including on the owner's host after the installer has really run there (R3C D-4's
class): every path is under the scratch prefix, and nothing under ``/etc`` or ``/usr/local`` is
read. The snapshot class runs the snapshot script on a scratch WAL-mode database it creates.
"""

from __future__ import annotations

import getpass
import hashlib
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO_ROOT / "util" / "ad-hoc" / "yamaguchi_server_db_snapshot.py"

# Everything the installer reads from the repository (REPO_DIR = installer/..).
INSTALLER_SOURCES = (
    "util/install_duplicati_service.bash",
    "scripts/duplicati-wrapper.bash",
    "util/systemd/duplicati.service",
    "util/systemd/duplicati.default",
    "util/yamaguchi-pre-backup-guard.bash",
    "util/systemd/duplicati-env.contract",
    "util/ad-hoc/yamaguchi_server_db_snapshot.py",
    "util/systemd/yamaguchi-server-db-snapshot.service",
    "util/systemd/yamaguchi-server-db-snapshot.timer",
)
# (source, destination relative to the prefix, mode) in the installer's PAIRS order.
BLESSED = (
    ("scripts/duplicati-wrapper.bash", "usr/local/lib/duplicati/duplicati-wrapper.bash", 0o755),
    ("util/systemd/duplicati.service", "etc/systemd/system/duplicati.service", 0o644),
    ("util/systemd/duplicati.default", "etc/default/duplicati", 0o644),
    ("util/yamaguchi-pre-backup-guard.bash", "usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash", 0o755),
    ("util/ad-hoc/yamaguchi_server_db_snapshot.py", "usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py", 0o755),
    ("util/systemd/yamaguchi-server-db-snapshot.service", "etc/systemd/system/yamaguchi-server-db-snapshot.service", 0o644),
    ("util/systemd/yamaguchi-server-db-snapshot.timer", "etc/systemd/system/yamaguchi-server-db-snapshot.timer", 0o644),
)
DEFAULTS_DST = "etc/default/duplicati"
ENV_DST = "etc/duplicati/env"
DATA_FOLDER = "home/duplicati/.config/Duplicati"
CRED_DST = "etc/credstore/duplicati-settings-key"
SNAP_DEST_DIR = "home/pcalnon/.local/state/duplicati-server-db"

STUBS = {
    "id": """#!/usr/bin/env bash
if [[ "$#" -eq 1 && "$1" == "-u" ]]; then echo 0; exit 0; fi
exec {real_id} "$@"
""",
    "install": """#!/usr/bin/env bash
printf 'INSTALL %s\\n' "$*" >> "${{STUB_LOG:?}}"
args=()
while (( $# )); do
    case "$1" in
        -o|-g) shift 2 ;;
        *) args+=("$1"); shift ;;
    esac
done
for a in "${{args[@]}}"; do
    if [[ "$a" == /* && "$a" != "${{STUB_ROOT:?}}"/* ]]; then echo "INSTALL STUB REFUSES a path outside the scratch root: $a" >&2; exit 97; fi
done
exec {real_install} "${{args[@]}}"
""",
    "systemctl": """#!/usr/bin/env bash
printf 'SYSTEMCTL %s\\n' "$*" >> "${{STUB_LOG:?}}"
exit 0
""",
    "systemd-analyze": """#!/usr/bin/env bash
printf 'SYSTEMD-ANALYZE %s\\n' "$*" >> "${{STUB_LOG:?}}"
exit 0
""",
    "stat": """#!/usr/bin/env bash
if [[ "$#" -eq 3 && "$1" == "-c" && "$2" == "%U:%a" ]]; then
    if [[ "$3" == "${{STUB_DATA_FOLDER:-}}" ]]; then echo "${{STUB_DATA_STAT:-duplicati:700}}"; exit 0; fi
    if [[ "$3" == "${{STUB_CRED:-}}" ]]; then echo "${{STUB_CRED_STAT:-root:600}}"; exit 0; fi
fi
if [[ "$#" -eq 3 && "$1" == "-c" && "$2" == "%U:%G:%a" && "$3" == "${{STUB_ENV:-}}" ]]; then echo "${{STUB_ENV_STAT:-root:duplicati:640}}"; exit 0; fi
exec {real_stat} "$@"
""",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> dict[str, str]:
    """Every regular file under root -> its sha256 (the "nothing was written" witness)."""
    return {str(p.relative_to(root)): _sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


class InstallerRealPath(unittest.TestCase):
    """The installer without --dry-run, as a non-root user, against a scratch prefix and PATH stubs."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="installer-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.prefix = self.tmp / "prefix"
        self.prefix.mkdir()
        # Directories every systemd host has; the installer (rightly) does not create them.
        for d in ("etc/systemd/system", "etc/default"):
            (self.prefix / d).mkdir(parents=True)
        self.blessed = self.tmp / "blessed.sha256"
        self.log = self.tmp / "stub.log"
        self.repo = self._scratch_repo()
        bindir = self.tmp / "bin"
        bindir.mkdir()
        real = {"real_id": shutil.which("id"), "real_install": shutil.which("install"), "real_stat": shutil.which("stat")}
        for name, body in STUBS.items():
            path = bindir / name
            path.write_text(body.format(**real), encoding="utf-8")
            path.chmod(0o755)
        self.path = f"{bindir}:{os.environ.get('PATH', '/usr/bin:/bin')}"

    def _scratch_repo(self) -> Path:
        """A copy of every file the installer reads, so a test can change a source without touching the tree."""
        repo = self.tmp / "repo"
        for rel in INSTALLER_SOURCES:
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / rel, dst)
        return repo

    def run_installer(self, *argv: str, **stub_env: str) -> subprocess.CompletedProcess:
        env = RedactedEnv(
            os.environ,
            PATH=self.path,
            STUB_LOG=str(self.log),
            STUB_ROOT=str(self.tmp),
            STUB_DATA_FOLDER=str(self.prefix / DATA_FOLDER),
            STUB_CRED=str(self.prefix / CRED_DST),
            STUB_ENV=str(self.prefix / ENV_DST),
            DUPLICATI_INSTALL_PREFIX=str(self.prefix),
            DUPLICATI_INSTALL_BLESSED=str(self.blessed),
            PYTHONDONTWRITEBYTECODE="1",
            **stub_env,
        )
        return subprocess.run(["bash", str(self.repo / "util/install_duplicati_service.bash"), *argv], env=env, capture_output=True, text=True, check=False)

    def install_and_bless_current(self):
        """A host where installed == blessed == the scratch repository, for all seven files."""
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.log.unlink()

    def asides(self, rel: str, kind: str) -> list[Path]:
        target = self.prefix / rel
        return sorted(target.parent.glob(f"{target.name}.{kind}-*"))

    def blessed_map(self) -> dict[str, str]:
        out = {}
        for line in self.blessed.read_text(encoding="utf-8").splitlines():
            digest, path = line.split("  ", 1)
            out[path] = digest
        return out

    @unittest.skipIf(os.geteuid() == 0, "as root the unstubbed installer would really run; this test is for the non-root refusal")
    def test_refuses_to_run_for_real_without_root(self):
        env = RedactedEnv(os.environ, DUPLICATI_INSTALL_PREFIX=str(self.prefix), DUPLICATI_INSTALL_BLESSED=str(self.blessed))
        r = subprocess.run(["bash", str(self.repo / "util/install_duplicati_service.bash")], env=env, capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("run with sudo", r.stderr)
        self.assertEqual(_tree(self.prefix), {})

    def test_first_install_writes_every_file_byte_for_byte_and_blesses_what_it_wrote(self):
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        for src, dst, mode in BLESSED:
            target = self.prefix / dst
            with self.subTest(dst=dst):
                self.assertEqual(target.read_bytes(), (self.repo / src).read_bytes())
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), mode)
        env = self.prefix / ENV_DST
        self.assertEqual(env.read_bytes(), (self.repo / "util/systemd/duplicati-env.contract").read_bytes())
        self.assertEqual(stat.S_IMODE(env.stat().st_mode), 0o640)
        self.assertEqual(stat.S_IMODE((self.prefix / DATA_FOLDER).stat().st_mode), 0o700)
        expected = {str(self.prefix / dst): _sha256(self.repo / src) for src, dst, _m in BLESSED}
        self.assertEqual(self.blessed_map(), expected)
        self.assertEqual(stat.S_IMODE(self.blessed.stat().st_mode), 0o644)
        self.assertFalse(Path(f"{self.blessed}.new").exists())
        log = self.log.read_text(encoding="utf-8")
        self.assertIn("SYSTEMCTL daemon-reload", log)
        units = " ".join(str(self.prefix / d) for d in ("etc/systemd/system/duplicati.service", "etc/systemd/system/yamaguchi-server-db-snapshot.service", "etc/systemd/system/yamaguchi-server-db-snapshot.timer"))
        self.assertIn(f"SYSTEMD-ANALYZE verify {units}", log)
        for verb in ("start", "restart", "enable", "stop", "disable"):
            self.assertNotIn(f"SYSTEMCTL {verb}", log, "the installer never starts, stops, enables or disables a unit")
        self.assertIn("is absent or empty", r.stderr, "an absent settings key gets the NOTE")
        self.assertIn(f"NOTE: {self.prefix / SNAP_DEST_DIR} is absent", r.stderr)
        self.assertEqual(self.asides(DEFAULTS_DST, "pre-install"), [], "an empty prefix has nothing to keep")

    def assert_same_metadata(self, aside: Path, mode: int, mtime: int):
        """R4C X15: the copy aside is `cp -p` -- the evidence keeps its mode and mtime."""
        st = aside.stat()
        self.assertEqual(stat.S_IMODE(st.st_mode), mode)
        self.assertEqual(int(st.st_mtime), mtime)

    def test_a_never_blessed_differing_file_needs_the_switch_and_is_then_kept(self):
        """R3C N-7 (kept) and R4C N-5 (needs the switch): with no blessed file, an installed file that differs from the
        repository was overwritten as a quiet "first install" -- an edited wrapper included."""
        defaults = self.prefix / DEFAULTS_DST
        defaults.write_text('DAEMON_OPTS="--set-by-an-earlier-hand"\n', encoding="utf-8")
        defaults.chmod(0o600)
        os.utime(defaults, (1_600_000_000, 1_600_000_000))
        original = defaults.read_bytes()
        wrapper = self.prefix / BLESSED[0][1]
        wrapper.parent.mkdir(parents=True)
        shutil.copy2(self.repo / BLESSED[0][0], wrapper)
        before = _tree(self.prefix)
        for blessed_state in ("absent", "empty"):
            with self.subTest(blessed=blessed_state):
                if blessed_state == "empty":
                    self.blessed.write_text("", encoding="utf-8")
                r = self.run_installer()
                self.assertEqual(r.returncode, 4, r.stderr)
                self.assertIn(f"UNBLESSED: installed {defaults}", r.stderr)
                self.assertNotIn(f"UNBLESSED: installed {wrapper}", r.stderr, "a file identical to the repository is not a finding")
                self.assertEqual(_tree(self.prefix), before, "a refused run must write nothing")
        r = self.run_installer("--update-backup-behavior")
        self.assertEqual(r.returncode, 0, r.stderr)
        asides = self.asides(DEFAULTS_DST, "pre-install")
        self.assertEqual(len(asides), 1, list(defaults.parent.iterdir()))
        self.assertEqual(asides[0].read_bytes(), original, "the copy aside must hold the ORIGINAL bytes (taken before the install)")
        self.assert_same_metadata(asides[0], 0o600, 1_600_000_000)
        self.assertIn(f"kept the never-blessed {defaults} as {asides[0]}", r.stdout, "R4C N-3: a real run says where the copy went")
        self.assertEqual(defaults.read_bytes(), (self.repo / "util/systemd/duplicati.default").read_bytes())
        self.assertEqual(self.asides(BLESSED[0][1], "pre-install"), [], "a file identical to the repository needs no copy")

    def test_an_installed_but_never_blessed_file_identical_to_the_repository_installs_quietly(self):
        for src, dst, _mode in BLESSED:
            (self.prefix / dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.repo / src, self.prefix / dst)
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("UNBLESSED", r.stderr)

    def test_drift_is_refused_untouched_then_kept_as_evidence_under_the_switch(self):
        """R3C D-5 / M20: the copy-aside must really copy the drifted bytes, before the install overwrites them."""
        self.install_and_bless_current()
        defaults = self.prefix / DEFAULTS_DST
        defaults.write_text('DAEMON_OPTS="--edited-by-hand-DRIFT-MARKER"\n', encoding="utf-8")
        defaults.chmod(0o640)
        os.utime(defaults, (1_600_000_000, 1_600_000_000))
        drifted = defaults.read_bytes()
        before = _tree(self.prefix)
        r = self.run_installer()
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn(f"DRIFT: installed {defaults}", r.stderr)
        self.assertEqual(_tree(self.prefix), before, "a refused run must write nothing")
        self.assertFalse(self.log.exists() and "SYSTEMCTL" in self.log.read_text(encoding="utf-8"))
        r2 = self.run_installer("--update-backup-behavior")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        asides = self.asides(DEFAULTS_DST, "drifted")
        self.assertEqual(len(asides), 1)
        self.assertEqual(asides[0].read_bytes(), drifted, "the drifted bytes are the evidence; they must survive")
        self.assert_same_metadata(asides[0], 0o640, 1_600_000_000)
        self.assertIn(f"kept the drifted {defaults} as {asides[0]}", r2.stdout, "R4C N-3: a real run says where the copy went")
        self.assertEqual(defaults.read_bytes(), (self.repo / "util/systemd/duplicati.default").read_bytes())
        self.assertEqual(self.blessed_map()[str(defaults)], _sha256(defaults))
        r3 = self.run_installer()
        self.assertEqual(r3.returncode, 0, r3.stderr)
        self.assertNotIn("DRIFT", r3.stderr)
        self.assertEqual(len(self.asides(DEFAULTS_DST, "drifted")), 1, "a clean re-run copies nothing aside")

    def test_behaviour_change_is_refused_untouched_then_installed_without_an_aside(self):
        self.install_and_bless_current()
        src = self.repo / "util/systemd/duplicati.default"
        src.write_text(src.read_text(encoding="utf-8") + "# an intended change\n", encoding="utf-8")
        before = _tree(self.prefix)
        r = self.run_installer()
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("BEHAVIOUR CHANGE", r.stderr)
        self.assertNotIn("DRIFT", r.stderr)
        self.assertEqual(_tree(self.prefix), before)
        r2 = self.run_installer("--update-backup-behavior")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        defaults = self.prefix / DEFAULTS_DST
        self.assertEqual(defaults.read_bytes(), src.read_bytes())
        self.assertEqual(self.blessed_map()[str(defaults)], _sha256(src))
        self.assertEqual(self.asides(DEFAULTS_DST, "drifted") + self.asides(DEFAULTS_DST, "pre-install"), [])

    def test_an_existing_env_file_is_kept_byte_for_byte(self):
        env = self.prefix / ENV_DST
        env.parent.mkdir(parents=True)
        env.write_text("--webservice-port=8311\n", encoding="utf-8")
        original = env.read_bytes()
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(env.read_bytes(), original)
        self.assertIn(f"kept existing {env}", r.stdout)

    def test_an_existing_env_file_the_new_wrapper_refuses_stops_the_install(self):
        """The wrapper being installed reads it at the next start; installing it over a file it refuses is a dead unit."""
        env = self.prefix / ENV_DST
        env.parent.mkdir(parents=True)
        env.write_text("--Parameters-File=/home/duplicati/.config/Duplicati/opts\n", encoding="utf-8")
        r = self.run_installer()
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("REFUSING: the wrapper being installed refuses the existing", r.stderr)
        self.assertEqual(_tree(self.prefix), {str(Path(ENV_DST)): _sha256(env)}, "nothing else may be written")

    ACCEPTED_FORMS = "root:duplicati 0640 or duplicati:duplicati 0600"

    def test_an_existing_env_file_must_be_one_of_o12s_two_forms(self):
        """R4C N-4 (the service reads it as duplicati), R5A DEFECT-2 (O-12 is OPEN: either documented form passes -- the
        installer does not settle it) and R5A NIT-1 (nothing other-readable: the file may carry the key)."""
        env = self.prefix / ENV_DST
        env.parent.mkdir(parents=True)
        env.write_text("--webservice-port=8311\n", encoding="utf-8")
        refused = ("root:root:640", "root:duplicati:644", "root:root:600", "root:duplicati:600", "root:duplicati:660", "root:duplicati:642", "duplicati:duplicati:640", "duplicati:duplicati:644", "duplicati:duplicati:660", "duplicati:root:600", "pcalnon:duplicati:640")
        for meta in refused:
            with self.subTest(meta=meta):
                r = self.run_installer(STUB_ENV_STAT=meta)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn(f"REFUSING: {env} is {meta}", r.stderr)
                self.assertIn(self.ACCEPTED_FORMS, r.stderr, "the refusal names BOTH accepted forms")
                self.assertEqual(_tree(self.prefix), {str(Path(ENV_DST)): _sha256(env)}, "nothing else may be written")
        for meta in ("root:duplicati:640", "duplicati:duplicati:600"):
            with self.subTest(meta=meta):
                r = self.run_installer(STUB_ENV_STAT=meta)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(env.read_text(encoding="utf-8"), "--webservice-port=8311\n")

    def test_an_existing_env_file_that_is_a_symlink_is_refused_by_name(self):
        """R5A DEFECT-2: stat judged the link's own 0777 and the refusal prescribed a chmod that cannot work."""
        target = self.tmp / "elsewhere-env"
        target.write_text("--webservice-port=8311\n", encoding="utf-8")
        env = self.prefix / ENV_DST
        env.parent.mkdir(parents=True)
        env.symlink_to(target)
        r = self.run_installer()
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn(f"REFUSING: {env} is a symlink", r.stderr)
        self.assertIn(self.ACCEPTED_FORMS, r.stderr)
        self.assertTrue(env.is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), "--webservice-port=8311\n")

    def test_an_absent_backup_mount_is_not_a_contract_fault(self):
        """R4A D-1: the installer's contract gate ran the wrapper's mount check (an empty override was ignored), so an
        unmounted drive read as "the wrapper refuses the contract". Simulated by pointing the wrapper's default mount at a
        path that does not exist, in the scratch repository."""
        wrapper = self.repo / "scripts/duplicati-wrapper.bash"
        text = wrapper.read_text(encoding="utf-8")
        pattern = r'"\$\{DUPLICATI_REQUIRE_MOUNT(:?-)[^}]*\}"'  # only the default PATH changes; the operator stays as shipped
        self.assertEqual(len(re.findall(pattern, text)), 1)
        wrapper.write_text(re.sub(pattern, lambda m: f'"${{DUPLICATI_REQUIRE_MOUNT{m.group(1)}{self.tmp}/no-such-mount}}"', text), encoding="utf-8")
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("REFUSING", r.stderr)

    def test_a_contract_the_wrapper_refuses_installs_nothing(self):
        """R3A D-1 / R3C D-3 through the real path: one --parameters-file line and nothing is installed."""
        contract = self.repo / "util/systemd/duplicati-env.contract"
        contract.write_text(contract.read_text(encoding="utf-8") + "--parameterfile=/x\n", encoding="utf-8")
        r = self.run_installer()
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("REFUSING: the wrapper refuses", r.stderr)
        self.assertIn("may not be set from the env file", r.stderr)
        self.assertEqual(_tree(self.prefix), {})
        self.assertFalse(self.log.exists())

    def test_a_data_folder_that_is_not_duplicati_0700_fails(self):
        r = self.run_installer(STUB_DATA_STAT="root:755")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("must be duplicati-owned mode 0700", r.stderr)
        self.assertFalse(self.blessed.exists(), "no bless after a failed data-folder check")

    def test_the_settings_key_file_must_be_root_0600_and_is_never_read(self):
        cred = self.prefix / CRED_DST
        cred.parent.mkdir(parents=True)
        cred.write_text("not-a-real-key-0123456789", encoding="utf-8")
        r = self.run_installer(STUB_CRED_STAT="root:644")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("must be root-owned mode 0600", r.stderr)
        r2 = self.run_installer()
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertNotIn("is absent or empty", r2.stderr)
        self.assertNotIn("not-a-real-key", r.stdout + r.stderr + r2.stdout + r2.stderr)

    def test_snapshot_destination_present_gets_no_note(self):
        (self.prefix / SNAP_DEST_DIR).mkdir(parents=True)
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("snapshot unit fails until it exists", r.stderr)

    # The design's P0 step 10 guard block, verbatim (D at a0ff619c; the guard path is the prefix's).
    GUARD_BLOCK = """unset url id
id=<id>
case "$id" in ''|*[!0-9]*) echo "REFUSE: set id to the job's number" >&2; false ;; esac &&
url="$(python3 util/ad-hoc/yamaguchi_server_api.py export "$id" \\
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["Backup"]["TargetURL"])')"
test -n "$url" || { echo "REFUSE: export $id gave no TargetURL" >&2; false; } &&
sudo -u duplicati env DUPLICATI__REMOTEURL="$url" \\
  {guard}; echo "guard exit=$?"
"""

    def test_the_next_steps_print_the_prerequisites_then_step_10s_guard_block_verbatim(self):
        """R3B N-1, R4A N-1, R4B N-7: the hint had a hand-typed URL, then lacked `unset url id` and the numeric id check
        (a stale `url` reached the guard), and printed the start without step 8's prerequisites."""
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        guard = self.prefix / "usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash"
        self.assertIn(self.GUARD_BLOCK.replace("{guard}", str(guard)), out)
        self.assertNotIn("DUPLICATI__REMOTEURL=file://", out)
        start = out.index("sudo systemctl start duplicati.service")
        for prerequisite in ("paused-until = 0", "DUPLICATI_WEB_CREDENTIAL=<password>", "settings key is in place"):
            self.assertLess(out.index(prerequisite), start, f"{prerequisite!r} must come before the start")
        self.assertLess(start, out.index("serverstate   must exit 2"))
        self.assertLess(start, out.index("unset url id"), "the guard check comes after the start")
        self.assertNotIn("restart duplicati.service", out)
        # R5A DEFECT-1 / R5B N-1: on Running, STOP -- `pause` only suspends a job that may already be running.
        flat = " ".join(out.split())
        self.assertNotIn("pause at once", flat)
        self.assertIn("If it reads Running, stop the unit at once (sudo systemctl stop duplicati.service) and record it; do not pause", flat)
        # ... and step 10's restart sits between the guard block and resume.
        # R6 NIT-3 (mutant N08): the reason is part of the rule, and so is what follows the stop.
        stop = flat.index("If it reads Running, stop the unit at once")
        reason = flat.index("pause only suspends a job that may already be running, and step 10's resume would continue it with the options it started with.")
        then = flat.index("Then read the stored paused-until (step 8's read-back) before starting again.")
        self.assertLess(stop, reason)
        self.assertLess(reason, then)
        self.assertLess(then, flat.index("unset url id"), "the stop rule belongs to the first start, before the guard block")
        # Exact ordering (raised in round 6's first draft report): both positions taken in the same flattened text.
        guard_end = flat.index('echo "guard exit=$?"')
        restart = flat.index("restart the unit before resume (step 10): sudo systemctl stop duplicati.service, then sudo systemctl start duplicati.service; serverstate must exit 2 again; read the edits back with export <id>")
        self.assertLess(guard_end, restart, "the restart comes after the guard block")
        self.assertIn("and only then resume", flat[restart:])

    def test_the_key_note_is_the_designs_never_overwrite_form(self):
        """R4A N-6: the NOTE wrote with `test ! -s` and no sudo; the design writes with `sudo test ! -e … | sudo tee`.
        R5A NIT-2: on Procedure A the NOTE names the random …-key.new that D step 8 also requires."""
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        cred = self.prefix / CRED_DST
        self.assertIn(f"sudo test ! -e {cred} && {{ umask 077; openssl rand -base64 48 | tr -d '\\n' | sudo tee {cred} >/dev/null; }}", r.stderr)
        self.assertIn(f"on Procedure A, place the accepted 09-18 key here instead, and a random one at {cred}.new, which P0.5b swaps in", " ".join(r.stderr.split()))


class SnapshotWalResidue(unittest.TestCase):
    """R3C N-8: a snapshot of a WAL-mode database left root-owned -wal/-shm files beside it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="snapshot-wal-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_snapshot_of_a_live_wal_database_leaves_only_the_snapshot(self):
        src = self.tmp / "data" / "Duplicati-server.sqlite"
        src.parent.mkdir()
        writer = sqlite3.connect(src)
        self.addCleanup(writer.close)
        self.assertEqual(writer.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
        writer.execute("CREATE TABLE Option (Name TEXT, Value TEXT)")
        writer.execute("INSERT INTO Option VALUES ('encrypted-fields', 'True')")
        writer.commit()
        dest_dir = self.tmp / "dest"
        dest_dir.mkdir()
        # Residue of an earlier (1.1.0) run must be cleared too.
        (dest_dir / "Duplicati-server.sqlite.tmp-shm").write_bytes(b"\0" * 16)
        (dest_dir / "Duplicati-server.sqlite-shm").write_bytes(b"\0" * 16)
        r = subprocess.run(["python3", str(SNAPSHOT), "--src", str(src), "--dest-dir", str(dest_dir), "--owner", getpass.getuser()], env=RedactedEnv(os.environ, PYTHONDONTWRITEBYTECODE="1"), capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(p.name for p in dest_dir.iterdir()), ["Duplicati-server.sqlite"])
        snap = sqlite3.connect(f"file:{dest_dir / 'Duplicati-server.sqlite'}?mode=ro", uri=True)
        try:
            self.assertEqual(snap.execute("SELECT Value FROM Option WHERE Name='encrypted-fields'").fetchone()[0], "True")
            self.assertEqual(snap.execute("PRAGMA journal_mode").fetchone()[0], "delete")
        finally:
            snap.close()
        self.assertEqual(sorted(p.name for p in dest_dir.iterdir()), ["Duplicati-server.sqlite"], "reading the snapshot read-only must not need a -wal either")


if __name__ == "__main__":
    unittest.main()
