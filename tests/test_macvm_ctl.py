#!/usr/bin/env python3
"""Hermetic gate for util/macvm_ctl.bash (turing bring-up plan task F5a, regression R-F5).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``start`` must refuse, and never call ``VBoxManage startvm``, unless gate G-MEM passes
(``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` §9.3): free + inactive
memory of at least the VM's size plus 4 GiB, at most 2 GiB of swap in use, and Docker Desktop not
running. turing was 13.7 GB into swap at probe time (plan §2.1); that shape is the R-F5 fixture.

Every external tool is a stub reached through the script's tool variables (``VBOXMANAGE``,
``VM_STAT``, ``SYSCTL``, ``PGREP``). So the suite runs the same on macOS and on Linux CI, where neither
``vm_stat`` nor VirtualBox exists, and it never touches a real VirtualBox. The VBoxManage stub logs
every argv, refuses any argv the script must not send, and keeps the VM state in a file, so
``startvm`` and ``controlvm`` change what the next ``showvminfo`` reports. The ``vm_stat`` fixtures use
the real layout; a test pins the generator byte for byte against a capture from turing.

Every case runs under ``/bin/bash``, which is bash 3.2 on macOS (the plan's portability floor).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "macvm_ctl.bash"
TIMEOUT_SECONDS = 60

VM = "juniper-macvm"
SHOWVMINFO = f"showvminfo {VM} --machinereadable"
STARTVM = f"startvm {VM} --type headless"
ACPI = f"controlvm {VM} acpipowerbutton"
POWEROFF = f"controlvm {VM} poweroff"

# The script's tool and tuning variables. Inherited values must never reach a case.
TOOL_VARS = ("VBOXMANAGE", "VM_STAT", "SYSCTL", "PGREP", "POLL_INTERVAL")

# sysctl vm.swapusage. The first is the plan's probe-time capture (§2.1), the second this session's.
SWAP_PROBE_2026_10_15 = "vm.swapusage: total = 15360.00M  used = 13684.00M  free = 1676.00M  (encrypted)"
SWAP_TURING_2026_10_17 = "vm.swapusage: total = 19456.00M  used = 18069.75M  free = 1386.25M  (encrypted)"
SWAP_NONE = "vm.swapusage: total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)"

DOCKER_ALL = "com.docker.backend|Docker Desktop|Docker"

# `vm_stat` on turing, 2026-10-17 (Intel, 4096-byte pages), verbatim.
TURING_VM_STAT_2026_10_17 = """\
Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                              360513.
Pages active:                            740663.
Pages inactive:                          738059.
Pages speculative:                         1361.
Pages throttled:                              0.
Pages wired down:                       1098314.
Pages purgeable:                            462.
"Translation faults":               17884376367.
Pages copy-on-write:                   82928664.
Pages zero filled:                   9255217932.
Pages reactivated:                   2922892599.
Pages purged:                          30477270.
File-backed pages:                       341945.
Anonymous pages:                        1138138.
Pages stored in compressor:            15394166.
Pages occupied by compressor:           1254629.
Decompressions:                      4373079219.
Compressions:                        4506827517.
Pageins:                               61514099.
Pageouts:                               8085828.
Swapins:                             9912608786.
Swapouts:                            9921273021.
"""

# Every row of that capture, in order. The three the gate reads are overridden per fixture.
_TURING_ROWS = (
    ("Pages free", 360513),
    ("Pages active", 740663),
    ("Pages inactive", 738059),
    ("Pages speculative", 1361),
    ("Pages throttled", 0),
    ("Pages wired down", 1098314),
    ("Pages purgeable", 462),
    ('"Translation faults"', 17884376367),
    ("Pages copy-on-write", 82928664),
    ("Pages zero filled", 9255217932),
    ("Pages reactivated", 2922892599),
    ("Pages purged", 30477270),
    ("File-backed pages", 341945),
    ("Anonymous pages", 1138138),
    ("Pages stored in compressor", 15394166),
    ("Pages occupied by compressor", 1254629),
    ("Decompressions", 4373079219),
    ("Compressions", 4506827517),
    ("Pageins", 61514099),
    ("Pageouts", 8085828),
    ("Swapins", 9912608786),
    ("Swapouts", 9921273021),
)


def vm_stat_text(*, free: int, inactive: int, speculative: int = 0, page_size: int = 4096, header: bool = True, omit: str = "") -> str:
    """vm_stat output in the real layout: printf("%-30s %16llu.") rows under the page-size header."""
    chosen = {"Pages free": free, "Pages inactive": inactive, "Pages speculative": speculative}
    lines = [f"Mach Virtual Memory Statistics: (page size of {page_size} bytes)"] if header else []
    for label, value in _TURING_ROWS:
        if label != omit:
            lines.append(f"{label + ':':<30} {chosen.get(label, value):>16}.")
    return "\n".join(lines) + "\n"


def pages(mib: int, page_size: int = 4096) -> int:
    return mib * 1024 * 1024 // page_size


# 8 GiB free + 4 GiB inactive: passes the default 6 + 4 GiB requirement with room to spare.
VM_STAT_PASS = vm_stat_text(free=pages(8192), inactive=pages(4096))
# Exactly 10240 MiB of free + speculative + inactive: the default requirement, to the byte.
VM_STAT_AT_THRESHOLD = vm_stat_text(free=pages(6144), speculative=pages(1024), inactive=pages(3072))
VM_STAT_ONE_PAGE_SHORT = vm_stat_text(free=pages(6144), speculative=pages(1024), inactive=pages(3072) - 1)

VBOX_STUB = r"""#!/bin/bash
# VBoxManage stub. Appends each argv to $STUB_VBOX_LOG and keeps the VM state in
# $STUB_VBOX_DIR/state, so startvm and controlvm change what the next showvminfo reports.
# Only ${STUB_VBOX_VM:-juniper-macvm} is registered. Refuses (exit 99) any argv the script must not send.
printf '%s\n' "$*" >> "$STUB_VBOX_LOG"
dir="$STUB_VBOX_DIR"
vm="${STUB_VBOX_VM:-juniper-macvm}"
refuse() {
    echo "VBoxManage stub: refusing argv: $*" >&2
    exit 99
}
case "$1" in
    showvminfo)
        { [ "$#" -eq 3 ] && [ "$3" = "--machinereadable" ]; } || refuse "$@"
        if [ -n "${STUB_VBOX_SHOWVMINFO_FAIL:-}" ]; then
            echo "VBoxManage: error: Failed to create the VirtualBox object!" >&2
            exit "$STUB_VBOX_SHOWVMINFO_FAIL"
        fi
        # The VM drops out of the registry once acpipowerbutton has been sent.
        if [ -n "${STUB_VBOX_GONE_AFTER_ACPI:-}" ] && [ -f "$dir/polls" ]; then
            vm="(unregistered mid-stop)"
        fi
        if [ "$2" != "$vm" ]; then
            echo "VBoxManage: error: Could not find a registered machine named '$2'" >&2
            echo "VBoxManage: error: Details: code VBOX_E_OBJECT_NOT_FOUND (0x80bb0001), component VirtualBoxWrap, interface IVirtualBox, callee nsISupports" >&2
            exit 1
        fi
        if [ -n "${STUB_VBOX_NO_STATE:-}" ]; then
            printf 'name="%s"\nmemory=6144\n' "$vm"
            exit 0
        fi
        # Stateful stop: after acpipowerbutton the first STUB_VBOX_OFF_AFTER_POLLS polls still see
        # the old state and the next one sees poweroff. "never" keeps the guest up.
        if [ -f "$dir/polls" ]; then
            n=$(( $(cat "$dir/polls") + 1 ))
            echo "$n" > "$dir/polls"
            limit="${STUB_VBOX_OFF_AFTER_POLLS:-never}"
            if [ "$limit" != never ] && [ "$n" -gt "$limit" ]; then
                echo poweroff > "$dir/state"
            fi
        fi
        state="$(cat "$dir/state")"
        cat <<EOF
name="$vm"
Encryption="disabled"
groups="/"
ostype="Ubuntu (64-bit)"
UUID="7c1e5a90-3b2d-4f6e-9a18-0d4b6c2e8f31"
memory=${STUB_VBOX_MEMORY:-6144}
pagefusion="off"
vram=16
cpus=4
VMState="$state"
VMStateChangeTime="2026-10-17T09:00:00.000000000"
EOF
        ;;
    startvm)
        { [ "$#" -eq 4 ] && [ "$2" = "$vm" ] && [ "$3" = "--type" ] && [ "$4" = "headless" ]; } || refuse "$@"
        if [ -n "${STUB_VBOX_STARTVM_FAIL:-}" ]; then
            echo "VBoxManage: error: The virtual machine '$vm' has terminated unexpectedly during startup" >&2
            exit "$STUB_VBOX_STARTVM_FAIL"
        fi
        echo running > "$dir/state"
        echo "Waiting for VM \"$vm\" to power on..."
        echo "VM \"$vm\" has been successfully started."
        ;;
    controlvm)
        { [ "$#" -eq 3 ] && [ "$2" = "$vm" ]; } || refuse "$@"
        case "$3" in
            acpipowerbutton)
                if [ -n "${STUB_VBOX_ACPI_FAIL:-}" ]; then
                    echo "VBoxManage: error: Invalid machine state: Paused" >&2
                    exit "$STUB_VBOX_ACPI_FAIL"
                fi
                echo 0 > "$dir/polls"
                ;;
            poweroff)
                if [ -n "${STUB_VBOX_POWEROFF_FAIL:-}" ]; then
                    echo "VBoxManage: error: Could not power off the machine" >&2
                    exit "$STUB_VBOX_POWEROFF_FAIL"
                fi
                [ -n "${STUB_VBOX_POWEROFF_IGNORED:-}" ] || echo poweroff > "$dir/state"
                echo "0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%"
                ;;
            *) refuse "$@" ;;
        esac
        ;;
    *) refuse "$@" ;;
esac
"""

VM_STAT_STUB = r"""#!/bin/bash
printf 'vm_stat %s\n' "$*" >> "$STUB_PROBE_LOG"
[ "$#" -eq 0 ] || { echo "vm_stat stub: refusing argv: $*" >&2; exit 99; }
cat "$STUB_VM_STAT_FILE"
exit "${STUB_VM_STAT_RC:-0}"
"""

SYSCTL_STUB = r"""#!/bin/bash
printf 'sysctl %s\n' "$*" >> "$STUB_PROBE_LOG"
{ [ "$#" -eq 1 ] && [ "$1" = "vm.swapusage" ]; } || { echo "sysctl stub: refusing argv: $*" >&2; exit 99; }
printf '%s\n' "$STUB_SWAPUSAGE"
exit "${STUB_SYSCTL_RC:-0}"
"""

# STUB_PGREP_RUNNING: '|'-separated names of running processes; the Nth one has pid 680 + N.
PGREP_STUB = r"""#!/bin/bash
printf 'pgrep %s\n' "$*" >> "$STUB_PROBE_LOG"
{ [ "$#" -eq 2 ] && [ "$1" = "-x" ]; } || { echo "pgrep stub: refusing argv: $*" >&2; exit 99; }
[ -z "${STUB_PGREP_RC:-}" ] || exit "$STUB_PGREP_RC"
pid=680
IFS='|'
for name in ${STUB_PGREP_RUNNING:-}; do
    pid=$((pid + 1))
    if [ "$name" = "$2" ]; then
        echo "$pid"
        exit 0
    fi
done
exit 1
"""


# First on PATH under each tool's bare name. The script must reach every tool through its variable
# (absolute by default); a bare call lands here, fails, and -- on a Mac with VirtualBox installed,
# like turing -- can never reach the real VBoxManage.
BARE_NAME_STUB = r"""#!/bin/bash
printf '%s %s\n' "$0" "$*" >> "$STUB_BARE_LOG"
echo "bare-name tool call: $0 $*" >&2
exit 97
"""


def _write_exe(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


class _Fixture(unittest.TestCase):
    """Four tool stubs, a registered VM that is powered off, and a host that passes G-MEM
    (12 GiB free + inactive, no swap in use, no Docker). Each case changes one thing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.cwd = base / "cwd"
        self.bin = base / "bin"
        self.shadow = base / "shadow"
        self.vbox_dir = base / "vbox"
        for d in (self.cwd, self.bin, self.shadow, self.vbox_dir):
            d.mkdir()
        self.vbox_log = base / "vbox.log"
        self.probe_log = base / "probe.log"
        self.bare_log = base / "bare.log"
        self.vm_stat_file = base / "vm_stat.txt"
        self.vbox = _write_exe(self.bin / "VBoxManage", VBOX_STUB)
        for name in ("VBoxManage", "vm_stat", "sysctl", "pgrep"):
            _write_exe(self.shadow / name, BARE_NAME_STUB)
        self.absent = self.bin / "absent"
        self.set_state("poweroff")
        self.set_vm_stat(VM_STAT_PASS)
        self.env = RedactedEnv({k: v for k, v in os.environ.items() if k not in TOOL_VARS and not k.startswith("STUB_")})
        self.env.update(
            PATH=f"{self.shadow}{os.pathsep}{os.environ.get('PATH', '')}",
            STUB_BARE_LOG=str(self.bare_log),
            VBOXMANAGE=str(self.vbox),
            VM_STAT=str(_write_exe(self.bin / "vm_stat", VM_STAT_STUB)),
            SYSCTL=str(_write_exe(self.bin / "sysctl", SYSCTL_STUB)),
            PGREP=str(_write_exe(self.bin / "pgrep", PGREP_STUB)),
            POLL_INTERVAL="0",
            STUB_VBOX_LOG=str(self.vbox_log),
            STUB_VBOX_DIR=str(self.vbox_dir),
            STUB_PROBE_LOG=str(self.probe_log),
            STUB_VM_STAT_FILE=str(self.vm_stat_file),
            STUB_SWAPUSAGE=SWAP_NONE,
            STUB_PGREP_RUNNING="",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def set_state(self, state: str) -> None:
        (self.vbox_dir / "state").write_text(state + "\n", encoding="utf-8")

    def state(self) -> str:
        return (self.vbox_dir / "state").read_text(encoding="utf-8").strip()

    def set_vm_stat(self, text: str) -> None:
        self.vm_stat_file.write_text(text, encoding="utf-8")

    def run_script(self, *args: str, **env_overrides: str) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env.update(env_overrides)
        proc = subprocess.run(
            ["/bin/bash", str(SCRIPT_PATH), *args],
            cwd=self.cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        bare = self.bare_log.read_text(encoding="utf-8") if self.bare_log.exists() else ""
        self.assertEqual(bare, "", "a tool was called by its bare name, bypassing its variable")
        return proc

    def vbox_calls(self) -> list[str]:
        return self.vbox_log.read_text(encoding="utf-8").splitlines() if self.vbox_log.exists() else []

    def probe_calls(self) -> list[str]:
        return self.probe_log.read_text(encoding="utf-8").splitlines() if self.probe_log.exists() else []

    def assert_condition(self, output: str, verdict: str, name: str, text: str) -> None:
        self.assertRegex(output, re.compile(rf"^  {verdict} +{name}: {re.escape(text)}", re.M))

    def assert_read_only(self, state: str = "poweroff") -> None:
        """Only showvminfo reached VirtualBox, and the VM is where it started."""
        self.assertEqual([c for c in self.vbox_calls() if not c.startswith("showvminfo ")], [])
        self.assertEqual(self.state(), state)


class StartGateTest(_Fixture):
    def test_r_f5_swap_over_the_gate_refuses_and_never_calls_startvm(self) -> None:
        # R-F5: the plan's probe-time swap (13684 MiB used) with memory and Docker both passing.
        proc = self.run_script("start", STUB_SWAPUSAGE=SWAP_PROBE_2026_10_15)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO])
        self.assert_read_only()
        self.assertIn("swap: used 13684 MiB > 2048 MiB allowed", proc.stderr)
        self.assertIn("startvm was not called", proc.stderr)
        self.assertNotIn("memory:", proc.stderr)
        self.assertNotIn("docker:", proc.stderr)
        self.assertIn("sysctl vm.swapusage", self.probe_calls())

    def test_free_plus_inactive_below_10_gib_refuses(self) -> None:
        self.set_vm_stat(vm_stat_text(free=pages(4096), inactive=pages(5120)))
        proc = self.run_script("start")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("memory: free + inactive 9216 MiB < 10240 MiB required (VM 6144 MiB + reserve 4096 MiB)", proc.stderr)
        self.assert_read_only()

    def test_exactly_the_required_memory_passes_and_one_page_less_refuses(self) -> None:
        self.set_vm_stat(VM_STAT_ONE_PAGE_SHORT)
        proc = self.run_script("start")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("free + inactive 10239 MiB < 10240 MiB required", proc.stderr)
        self.assert_read_only()
        self.set_vm_stat(VM_STAT_AT_THRESHOLD)
        proc = self.run_script("start")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_condition(proc.stdout, "PASS", "memory", "free + inactive 10240 MiB >= 10240 MiB required")
        self.assertEqual(self.vbox_calls()[-1], STARTVM)

    def test_docker_desktop_running_refuses(self) -> None:
        for name, pid in (("com.docker.backend", 681), ("Docker Desktop", 682), ("Docker", 683)):
            with self.subTest(name):
                self.vbox_log.unlink(missing_ok=True)
                # Only `name` is running; the other names hold its place so the pid is stable.
                running = "|".join(n if n == name else "not-running" for n in DOCKER_ALL.split("|"))
                proc = self.run_script("start", STUB_PGREP_RUNNING=running)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn(f"docker: Docker Desktop is running: {name} (pid {pid}); quit it before node mode (D7)", proc.stderr)
                self.assert_read_only()

    def test_the_vmnetd_helper_alone_is_not_docker_running(self) -> None:
        # com.docker.vmnetd is a privileged launchd helper that outlives Docker Desktop.
        proc = self.run_script("start", STUB_PGREP_RUNNING="com.docker.vmnetd")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_condition(proc.stdout, "PASS", "docker", "Docker Desktop is not running")
        self.assertEqual(
            [c for c in self.probe_calls() if c.startswith("pgrep ")],
            ["pgrep -x com.docker.backend", "pgrep -x Docker Desktop", "pgrep -x Docker"],
        )

    def test_every_failing_condition_is_listed_with_its_value_and_threshold(self) -> None:
        # turing as measured in this session: all three conditions fail at once.
        self.set_vm_stat(TURING_VM_STAT_2026_10_17)
        proc = self.run_script("start", STUB_SWAPUSAGE=SWAP_TURING_2026_10_17, STUB_PGREP_RUNNING=DOCKER_ALL)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        for reason in (
            "  memory: free + inactive 4296 MiB < 10240 MiB required (VM 6144 MiB + reserve 4096 MiB)",
            "  swap: used 18070 MiB > 2048 MiB allowed",
            "  docker: Docker Desktop is running: com.docker.backend (pid 681), Docker Desktop (pid 682), Docker (pid 683)",
        ):
            self.assertIn(reason, proc.stderr)
        self.assertIn("G-MEM: FAIL (3 of 3 conditions failed)", proc.stdout)
        self.assert_read_only()

    def test_all_pass_starts_the_vm_headless(self) -> None:
        proc = self.run_script("start")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, STARTVM])
        self.assertEqual(self.state(), "running")
        self.assertIn("G-MEM: PASS", proc.stdout)
        self.assertIn("has been successfully started", proc.stdout)

    def test_saved_and_aborted_vms_start_through_the_gate(self) -> None:
        for state in ("saved", "aborted", "aborted-saved", "teleported"):
            with self.subTest(state):
                self.vbox_log.unlink(missing_ok=True)
                self.probe_log.unlink(missing_ok=True)
                self.set_state(state)
                proc = self.run_script("start")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(self.vbox_calls(), [SHOWVMINFO, STARTVM])
                self.assertTrue(self.probe_calls(), "the gate must be evaluated")

    def test_already_running_exits_0_without_the_gate(self) -> None:
        # Idempotent for F7's LaunchDaemon: a failing gate is not even measured.
        self.set_state("running")
        proc = self.run_script("start", STUB_SWAPUSAGE=SWAP_PROBE_2026_10_15, STUB_PGREP_RUNNING=DOCKER_ALL)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("already running", proc.stdout)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO])
        self.assertEqual(self.probe_calls(), [], "G-MEM must not be evaluated for a running VM")

    def test_a_vm_neither_running_nor_stopped_exits_2_unstarted(self) -> None:
        for state in ("paused", "gurumeditation", "starting", "stopping", "saving", "restoring"):
            with self.subTest(state):
                self.vbox_log.unlink(missing_ok=True)
                self.set_state(state)
                proc = self.run_script("start")
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(f"is in state '{state}'", proc.stderr)
                self.assert_read_only(state)
                self.assertEqual(self.probe_calls(), [])

    def test_startvm_failure_maps_to_exit_1(self) -> None:
        for rc in ("1", "3", "126"):
            with self.subTest(rc=rc):
                proc = self.run_script("start", STUB_VBOX_STARTVM_FAIL=rc)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("startvm failed", proc.stderr)
                self.assertEqual(self.vbox_calls()[-1], STARTVM)

    def test_a_configured_vm_larger_than_the_option_raises_the_bar(self) -> None:
        # A VM resized to 8 GiB must not pass on the 6 GiB default.
        self.set_vm_stat(VM_STAT_AT_THRESHOLD)
        proc = self.run_script("start", STUB_VBOX_MEMORY="8192")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("memory: free + inactive 10240 MiB < 12288 MiB required (VM 8192 MiB + reserve 4096 MiB)", proc.stderr)
        self.assertIn("the VM's configured memory, larger than --vm-mem-gib 6", proc.stdout)
        self.assert_read_only()

    def test_a_configured_vm_smaller_than_the_option_does_not_lower_the_bar(self) -> None:
        self.set_vm_stat(VM_STAT_ONE_PAGE_SHORT)
        proc = self.run_script("start", STUB_VBOX_MEMORY="2048")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("free + inactive 10239 MiB < 10240 MiB required (VM 6144 MiB + reserve 4096 MiB)", proc.stderr)

    def test_threshold_options(self) -> None:
        # 2 GiB VM + 1 GiB reserve = 3072 MiB; 14 GiB of swap allowed covers the probe-time 13684 MiB.
        self.set_vm_stat(vm_stat_text(free=pages(2048), inactive=pages(1024)))
        args = ("start", "--vm-mem-gib", "2", "--reserve-gib", "1", "--max-swap-gib", "14")
        proc = self.run_script(*args, STUB_VBOX_MEMORY="2048", STUB_SWAPUSAGE=SWAP_PROBE_2026_10_15)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_condition(proc.stdout, "PASS", "memory", "free + inactive 3072 MiB >= 3072 MiB required (VM 2048 MiB + reserve 1024 MiB)")
        self.assert_condition(proc.stdout, "PASS", "swap", "used 13684 MiB <= 14336 MiB allowed")
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, STARTVM])

    def test_zero_swap_limit_and_zero_reserve(self) -> None:
        self.set_vm_stat(vm_stat_text(free=pages(6144), inactive=0))
        proc = self.run_script("start", "--reserve-gib", "0", "--max-swap-gib", "0", STUB_SWAPUSAGE="vm.swapusage: total = 1024.00M  used = 0.01M  free = 1023.99M  (encrypted)")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assert_condition(proc.stdout, "PASS", "memory", "free + inactive 6144 MiB >= 6144 MiB required (VM 6144 MiB + reserve 0 MiB)")
        self.assertIn("swap: used 1 MiB > 0 MiB allowed", proc.stderr)

    def test_vm_option_names_the_vm(self) -> None:
        proc = self.run_script("start", "--vm", "k8s-worker-2", STUB_VBOX_VM="k8s-worker-2")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), ["showvminfo k8s-worker-2 --machinereadable", "startvm k8s-worker-2 --type headless"])


class MeasurementTest(_Fixture):
    def test_fixture_generator_reproduces_the_turing_capture(self) -> None:
        self.assertEqual(vm_stat_text(free=360513, inactive=738059, speculative=1361), TURING_VM_STAT_2026_10_17)

    def test_page_size_comes_from_the_header(self) -> None:
        # 655360 pages are exactly 10 GiB at arm64's 16384 bytes, but only 2.5 GiB at 4096.
        self.set_vm_stat(vm_stat_text(page_size=16384, free=400000, speculative=55360, inactive=200000))
        proc = self.run_script("start")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("16384 B (vm_stat header)", proc.stdout)
        self.assert_condition(proc.stdout, "PASS", "memory", "free + inactive 10240 MiB >= 10240 MiB required")
        self.set_state("poweroff")
        self.set_vm_stat(vm_stat_text(page_size=4096, free=400000, speculative=55360, inactive=200000))
        proc = self.run_script("start")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("free + inactive 2560 MiB < 10240 MiB required", proc.stderr)

    def test_speculative_pages_count_as_free(self) -> None:
        self.set_vm_stat(vm_stat_text(free=pages(5120), speculative=pages(1024), inactive=pages(4096)))
        proc = self.run_script("status")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"{pages(6144)} pages = 6144 MiB (Pages free {pages(5120)} + Pages speculative {pages(1024)})", proc.stdout)
        self.assert_condition(proc.stdout, "PASS", "memory", "free + inactive 10240 MiB >= 10240 MiB required")

    def test_inactive_pages_count(self) -> None:
        self.set_vm_stat(vm_stat_text(free=pages(1024), inactive=pages(9216)))
        proc = self.run_script("status")
        self.assertIn(f"{pages(9216)} pages = 9216 MiB (Pages inactive)", proc.stdout)
        self.assert_condition(proc.stdout, "PASS", "memory", "free + inactive 10240 MiB >= 10240 MiB required")

    def test_swap_in_megabytes_rounds_up(self) -> None:
        for used, verdict, text in (
            ("2048.00M", "PASS", "used 2048 MiB <= 2048 MiB allowed"),
            ("2048.01M", "FAIL", "used 2049 MiB > 2048 MiB allowed"),
            ("18069.75M", "FAIL", "used 18070 MiB > 2048 MiB allowed"),
            ("0.00M", "PASS", "used 0 MiB <= 2048 MiB allowed"),
        ):
            with self.subTest(used):
                proc = self.run_script("status", STUB_SWAPUSAGE=f"vm.swapusage: total = 19456.00M  used = {used}  free = 1.00M  (encrypted)")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assert_condition(proc.stdout, verdict, "swap", text)

    def test_swap_in_gigabytes(self) -> None:
        for used, verdict, text in (
            ("2.00G", "PASS", "used 2048 MiB <= 2048 MiB allowed"),
            ("1.50G", "PASS", "used 1536 MiB <= 2048 MiB allowed"),
            ("2.01G", "FAIL", "used 2059 MiB > 2048 MiB allowed"),
            ("13.36G", "FAIL", "used 13681 MiB > 2048 MiB allowed"),
            ("3G", "FAIL", "used 3072 MiB > 2048 MiB allowed"),
        ):
            with self.subTest(used):
                proc = self.run_script("status", STUB_SWAPUSAGE=f"vm.swapusage: total = 15.00G  used = {used}  free = 1.00G  (encrypted)")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assert_condition(proc.stdout, verdict, "swap", text)

    def test_swap_in_kilobytes(self) -> None:
        for used, verdict, text in (
            ("2097152.00K", "PASS", "used 2048 MiB <= 2048 MiB allowed"),
            ("2097152.50K", "FAIL", "used 2049 MiB > 2048 MiB allowed"),
        ):
            with self.subTest(used):
                proc = self.run_script("status", STUB_SWAPUSAGE=f"vm.swapusage: total = 4194304.00K  used = {used}  free = 0.00K  (encrypted)")
                self.assert_condition(proc.stdout, verdict, "swap", text)

    def test_value_only_sysctl_output_is_read_too(self) -> None:
        # `sysctl -n vm.swapusage` drops the name; the parser keys on "used =" either way.
        proc = self.run_script("status", STUB_SWAPUSAGE="total = 15360.00M  used = 13684.00M  free = 1676.00M  (encrypted)")
        self.assert_condition(proc.stdout, "FAIL", "swap", "used 13684 MiB > 2048 MiB allowed")

    def test_an_input_that_cannot_be_measured_fails_closed(self) -> None:
        cases = {
            "vm_stat fails": {"STUB_VM_STAT_RC": "1"},
            "vm_stat missing": {"VM_STAT": "ABSENT"},
            "vm_stat without the page-size header": {"VM_STAT_TEXT": vm_stat_text(free=pages(8192), inactive=pages(4096), header=False)},
            "vm_stat without Pages inactive": {"VM_STAT_TEXT": vm_stat_text(free=pages(8192), inactive=pages(4096), omit="Pages inactive")},
            "vm_stat without Pages speculative": {"VM_STAT_TEXT": vm_stat_text(free=pages(8192), inactive=pages(4096), omit="Pages speculative")},
            "sysctl fails": {"STUB_SYSCTL_RC": "1"},
            "sysctl missing": {"SYSCTL": "ABSENT"},
            "swap used unreadable": {"STUB_SWAPUSAGE": "vm.swapusage: total = 0.00M  used = n/a  free = 0.00M"},
            "swap used in an unknown unit": {"STUB_SWAPUSAGE": "vm.swapusage: total = 0.00M  used = 1048576B  free = 0.00M"},
            "pgrep error": {"STUB_PGREP_RC": "2"},
            "pgrep missing": {"PGREP": "ABSENT"},
        }
        for label, overrides in cases.items():
            with self.subTest(label):
                self.vbox_log.unlink(missing_ok=True)
                env = dict(overrides)
                self.set_vm_stat(env.pop("VM_STAT_TEXT", VM_STAT_PASS))
                env = {k: (str(self.absent) if v == "ABSENT" else v) for k, v in env.items()}
                proc = self.run_script("start", **env)
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertIn("G-MEM: UNKNOWN (1 of 3 conditions could not be measured; start fails closed)", proc.stdout)
                self.assertIn("cannot ", proc.stderr)
                self.assert_read_only()
                status = self.run_script("status", **env)
                self.assertEqual(status.returncode, 2, f"{label}: {status.stdout}{status.stderr}")
                self.assertIn("UNKNOWN", status.stdout)


class StopTest(_Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.set_state("running")

    def test_a_stopped_vm_exits_0_untouched(self) -> None:
        for state in ("poweroff", "saved", "aborted", "aborted-saved"):
            with self.subTest(state):
                self.vbox_log.unlink(missing_ok=True)
                self.set_state(state)
                proc = self.run_script("stop")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertIn("is not running", proc.stdout)
                self.assertEqual(self.vbox_calls(), [SHOWVMINFO])

    def test_graceful_stop_polls_until_poweroff(self) -> None:
        proc = self.run_script("stop", STUB_VBOX_OFF_AFTER_POLLS="2")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, SHOWVMINFO, SHOWVMINFO, SHOWVMINFO])
        self.assertIn("stopped (VMState=poweroff)", proc.stdout)
        self.assertEqual(self.state(), "poweroff")
        self.assertEqual(self.probe_calls(), [], "stop has no gate")

    def test_timeout_without_force_exits_1_and_only_prints_the_poweroff(self) -> None:
        proc = self.run_script("stop", "--timeout", "0", STUB_VBOX_OFF_AFTER_POLLS="never")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, SHOWVMINFO])
        self.assertNotIn(POWEROFF, self.vbox_calls())
        self.assertIn(f"{self.vbox} {POWEROFF}", proc.stderr)
        self.assertIn("still running after 0 s", proc.stderr)
        self.assertEqual(self.state(), "running")

    def test_timeout_with_force_powers_off_and_exits_0_once_off(self) -> None:
        proc = self.run_script("stop", "--timeout", "0", "--force", STUB_VBOX_OFF_AFTER_POLLS="never")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, SHOWVMINFO, POWEROFF, SHOWVMINFO])
        self.assertIn("is off (VMState=poweroff)", proc.stdout)

    def test_force_is_not_used_when_the_guest_shuts_down_in_time(self) -> None:
        proc = self.run_script("stop", "--force", STUB_VBOX_OFF_AFTER_POLLS="1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, SHOWVMINFO, SHOWVMINFO])

    def test_a_failed_forced_poweroff_exits_1(self) -> None:
        proc = self.run_script("stop", "--timeout", "0", "--force", STUB_VBOX_OFF_AFTER_POLLS="never", STUB_VBOX_POWEROFF_FAIL="1")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("poweroff failed", proc.stderr)

    def test_a_poweroff_that_does_not_take_exits_1(self) -> None:
        # Success is the VM being off, not poweroff's exit status.
        proc = self.run_script("stop", "--timeout", "0", "--force", STUB_VBOX_OFF_AFTER_POLLS="never", STUB_VBOX_POWEROFF_IGNORED="1")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("still running 0 s after poweroff", proc.stderr)

    def test_acpi_failure_exits_1_without_waiting(self) -> None:
        proc = self.run_script("stop", STUB_VBOX_ACPI_FAIL="1")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI])
        self.assertIn("acpipowerbutton failed", proc.stderr)
        self.assertIn(f"{self.vbox} {POWEROFF}", proc.stderr)

    def test_acpi_failure_with_force_powers_off(self) -> None:
        proc = self.run_script("stop", "--force", STUB_VBOX_ACPI_FAIL="1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, POWEROFF, SHOWVMINFO])

    def test_a_paused_vm_is_stopped_through_the_same_path(self) -> None:
        self.set_state("paused")
        proc = self.run_script("stop", STUB_VBOX_OFF_AFTER_POLLS="0")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, SHOWVMINFO])

    def test_the_wait_is_paced_by_poll_interval_and_bounded_by_timeout(self) -> None:
        started = time.monotonic()
        proc = self.run_script("stop", "--timeout", "2", POLL_INTERVAL="1", STUB_VBOX_OFF_AFTER_POLLS="never")
        elapsed = time.monotonic() - started
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        polls = self.vbox_calls()[2:]
        self.assertTrue(2 <= len(polls) <= 4, f"{len(polls)} polls in {elapsed:.1f} s")
        self.assertEqual(set(polls), {SHOWVMINFO})
        self.assertGreaterEqual(elapsed, 1.0)

    def test_a_state_read_failure_while_waiting_exits_2(self) -> None:
        proc = self.run_script("stop", STUB_VBOX_OFF_AFTER_POLLS="never", STUB_VBOX_GONE_AFTER_ACPI="1")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO, ACPI, SHOWVMINFO])
        self.assertIn("is not registered", proc.stderr)
        self.assertNotIn(POWEROFF, self.vbox_calls())


class DryRunTest(_Fixture):
    def test_start_dry_run_on_a_passing_gate_prints_the_command_and_calls_nothing_mutating(self) -> None:
        proc = self.run_script("start", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"DRY-RUN: G-MEM passed; would run: {self.vbox} {STARTVM}", proc.stdout)
        self.assertIn("G-MEM: PASS", proc.stdout)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO])
        self.assert_read_only()

    def test_start_dry_run_on_a_failing_gate_exits_1(self) -> None:
        proc = self.run_script("start", "--dry-run", STUB_SWAPUSAGE=SWAP_PROBE_2026_10_15)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("DRY-RUN: start would refuse", proc.stderr)
        self.assertIn("swap: used 13684 MiB > 2048 MiB allowed", proc.stderr)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO])

    def test_stop_dry_run_prints_the_plan_with_the_defaults(self) -> None:
        self.set_state("running")
        del self.env["POLL_INTERVAL"]
        proc = self.run_script("stop", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"would run: {self.vbox} {ACPI}", proc.stdout)
        self.assertIn("poll VMState every 5 s for up to 120 s", proc.stdout)
        self.assertIn(f"exit 1 without powering off (--force would run: {self.vbox} {POWEROFF})", proc.stdout)
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO])
        self.assert_read_only("running")

    def test_stop_dry_run_with_force_and_timeout(self) -> None:
        self.set_state("running")
        proc = self.run_script("stop", "--dry-run", "--force", "--timeout", "30")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("for up to 30 s", proc.stdout)
        self.assertIn(f"and on timeout run: {self.vbox} {POWEROFF}", proc.stdout)
        self.assert_read_only("running")


class StatusTest(_Fixture):
    def test_status_prints_the_state_and_every_input_and_exits_0_when_the_gate_fails(self) -> None:
        self.set_vm_stat(TURING_VM_STAT_2026_10_17)
        proc = self.run_script("status", STUB_SWAPUSAGE=SWAP_TURING_2026_10_17, STUB_PGREP_RUNNING=DOCKER_ALL)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        docker = "com.docker.backend (pid 681), Docker Desktop (pid 682), Docker (pid 683)"
        self.assertEqual(
            proc.stdout,
            "VM juniper-macvm: VMState=poweroff\n"
            "G-MEM inputs:\n"
            "  page size       4096 B (vm_stat header)\n"
            "  free            361874 pages = 1413 MiB (Pages free 360513 + Pages speculative 1361)\n"
            "  inactive        738059 pages = 2883 MiB (Pages inactive)\n"
            "  VM memory       6144 MiB (--vm-mem-gib 6)\n"
            "  reserve         4096 MiB (--reserve-gib 4)\n"
            "  swap used       18070 MiB (vm.swapusage used = 18069.75M, rounded up)\n"
            "  swap limit      2048 MiB (--max-swap-gib 2)\n"
            f"  Docker Desktop  running: {docker}\n"
            "G-MEM conditions:\n"
            "  FAIL    memory: free + inactive 4296 MiB < 10240 MiB required (VM 6144 MiB + reserve 4096 MiB)\n"
            "  FAIL    swap: used 18070 MiB > 2048 MiB allowed\n"
            f"  FAIL    docker: Docker Desktop is running: {docker}; quit it before node mode (D7)\n"
            "G-MEM: FAIL (3 of 3 conditions failed)\n",
        )
        self.assertEqual(self.vbox_calls(), [SHOWVMINFO])

    def test_status_on_a_passing_host(self) -> None:
        self.set_state("running")
        proc = self.run_script("status")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("VM juniper-macvm: VMState=running", proc.stdout)
        self.assertIn("G-MEM: PASS", proc.stdout)
        self.assert_read_only("running")

    def test_dry_run_is_accepted_and_changes_nothing(self) -> None:
        proc = self.run_script("status", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_read_only()


class EnvironmentTest(_Fixture):
    def test_missing_vboxmanage_exits_2(self) -> None:
        for command in ("start", "stop", "status"):
            with self.subTest(command):
                proc = self.run_script(command, VBOXMANAGE=str(self.absent))
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(f"VBoxManage not found or not executable: {self.absent}", proc.stderr)
                self.assertEqual(self.vbox_calls(), [])
        # status still prints the whole G-MEM evaluation.
        self.assertIn(f"VM juniper-macvm: unknown (VBoxManage not found: {self.absent})", proc.stdout)
        self.assertIn("G-MEM: PASS", proc.stdout)

    def test_an_unregistered_vm_exits_2(self) -> None:
        # turing today: VirtualBox 7.2 is installed, juniper-macvm does not exist yet (F4).
        for command in ("start", "stop", "status"):
            with self.subTest(command):
                self.vbox_log.unlink(missing_ok=True)
                proc = self.run_script(command, STUB_VBOX_VM="some-other-vm")
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("ERROR: VM 'juniper-macvm' is not registered with VirtualBox for user", proc.stderr)
                self.assertIn("Could not find a registered machine named 'juniper-macvm'", proc.stderr)
                self.assertEqual(self.vbox_calls(), [SHOWVMINFO])
        self.assertIn("VM juniper-macvm: not registered for user", proc.stdout)
        self.assertIn("G-MEM: PASS", proc.stdout)

    def test_other_showvminfo_failures_exit_2(self) -> None:
        for label, overrides in {"VBoxSVC down": {"STUB_VBOX_SHOWVMINFO_FAIL": "1"}, "no VMState line": {"STUB_VBOX_NO_STATE": "1"}}.items():
            for command in ("start", "stop", "status"):
                with self.subTest(f"{label}: {command}"):
                    self.vbox_log.unlink(missing_ok=True)
                    proc = self.run_script(command, **overrides)
                    self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                    self.assertIn("showvminfo", proc.stderr)
                    self.assertEqual(self.vbox_calls(), [SHOWVMINFO])


class UsageTest(_Fixture):
    def test_help_exits_0(self) -> None:
        for flag in ("--help", "-h"):
            with self.subTest(flag):
                proc = self.run_script(flag)
                self.assertEqual(proc.returncode, 0)
                self.assertIn("Usage: macvm_ctl.bash {start|stop|status}", proc.stdout)
        self.assertEqual(self.vbox_calls(), [])
        self.assertEqual(self.probe_calls(), [])

    def test_bad_arguments_exit_2_before_any_tool(self) -> None:
        cases = {
            "no command": [],
            "unknown command": ["restart"],
            "two commands": ["start", "stop"],
            "unknown option": ["status", "--frobnicate"],
            "vm without value": ["status", "--vm"],
            "vm with a space": ["status", "--vm", "juniper macvm"],
            "vm with shell syntax": ["status", "--vm", "vm;id"],
            "vm with a leading dash": ["status", "--vm", "-macvm"],
            "vm-mem-gib zero": ["status", "--vm-mem-gib", "0"],
            "vm-mem-gib word": ["status", "--vm-mem-gib", "six"],
            "vm-mem-gib leading zero": ["status", "--vm-mem-gib", "06"],
            "vm-mem-gib negative": ["status", "--vm-mem-gib", "-1"],
            "reserve-gib fraction": ["status", "--reserve-gib", "1.5"],
            "max-swap-gib without value": ["status", "--max-swap-gib"],
            "max-swap-gib too large": ["status", "--max-swap-gib", "10000000"],
            "timeout with start": ["start", "--timeout", "10"],
            "force with start": ["start", "--force"],
            "force with status": ["status", "--force"],
            "timeout with a unit": ["stop", "--timeout", "2m"],
            "timeout without value": ["stop", "--timeout"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                proc = self.run_script(*argv)
                self.assertEqual(proc.returncode, 2, f"{label}: {proc.stdout}{proc.stderr}")
                self.assertIn("ERROR:", proc.stderr)
        self.assertEqual(self.vbox_calls(), [], "argument errors must be caught before VBoxManage runs")
        self.assertEqual(self.probe_calls(), [])

    def test_bad_poll_interval_exits_2(self) -> None:
        for value in ("abc", "-1", "0.5", "05"):
            with self.subTest(value):
                proc = self.run_script("stop", POLL_INTERVAL=value)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("POLL_INTERVAL", proc.stderr)
        self.assertEqual(self.vbox_calls(), [])


class SourceContractTest(unittest.TestCase):
    """Static pins. Comment lines are excluded."""

    text: str
    code: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.text.splitlines() if not line.lstrip().startswith("#"))

    def test_strict_mode_and_overridable_absolute_tool_paths(self) -> None:
        # Absolute defaults: F7's LaunchDaemon PATH lacks /usr/local/bin; tests override them all.
        self.assertIn("set -euo pipefail", self.code)
        for line in (
            'VBOXMANAGE="${VBOXMANAGE:-/usr/local/bin/VBoxManage}"',
            'VM_STAT="${VM_STAT:-/usr/bin/vm_stat}"',
            'SYSCTL="${SYSCTL:-/usr/sbin/sysctl}"',
            'PGREP="${PGREP:-/usr/bin/pgrep}"',
            'POLL_INTERVAL="${POLL_INTERVAL:-5}"',
        ):
            self.assertIn(line, self.code)

    def test_no_bash4_constructs_and_no_timeout_binary(self) -> None:
        for construct in ("declare -A", "mapfile", "readarray", ",,}", "^^}", "&>>", "|&", "coproc"):
            self.assertNotIn(construct, self.code, f"bash 3.2 has no {construct}")
        self.assertIsNone(re.search(r"(^\s*|[;&|(]\s*|\$\(\s*)g?timeout\s", self.code, re.M), "stock macOS has no timeout(1) (D0 is pending)")

    def test_no_host_specific_home_literal(self) -> None:
        self.assertNotRegex(self.text, r"/Users/|/home/", "use no home-directory literal (plan D12)")

    def test_shellcheck_clean_when_available(self) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            self.skipTest("shellcheck not installed (CI's pre-commit runs it)")
        proc = subprocess.run([shellcheck, str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
