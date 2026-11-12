#!/usr/bin/env python3
"""Hermetic gate for util/host_state_probe.bash (turing bring-up plan task G1).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The probe collects a macOS host's state as raw command captures for ``util/host_state_check.py``
(``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` task G1, the gates of
§9.3). It must:

- emit one JSON object in the documented schema, with every CAPTURE's argv, found flag, exit code,
  timed-out flag, stdout and stderr;
- record a missing, failing or hung command and carry on (exit 0), killing a hung one at ``--timeout``;
- collect only the sections asked for, in canonical order;
- under ``~/.ssh`` and ``~/.gnupg``, test names and permission bits only: the security fixtures are
  mode 000, so a read would fail where a name or mode test does not;
- run no credential probe. Tripwire ``gpg``, ``ssh``, ``ssh-add``, ``gh``, ``git`` and friends lead
  ``PATH``, and ``tearDown`` fails any case in which one ran;
- exit 2 on a bad argument before running anything.

Every external program is a stub reached through the probe's tool variables. Each stub answers from a
response table keyed by its exact argv, logs every call, and refuses any argv it has no answer for.
The fixture outputs are captures from turing (2026-10-20). ``find`` is the real one, on a temp
``HOME``, so the suite also pins the probe's ``find`` predicates under BSD find (macOS) and GNU find
(Linux CI).

Every case runs under ``/bin/bash``, which is bash 3.2 on macOS (the plan's portability floor).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "host_state_probe.bash"
TIMEOUT_SECONDS = 120
SECTIONS = ["hardware", "memory", "vm", "network", "power", "security", "tools", "env", "alias", "signing"]
CAPTURE_KEYS = {"argv", "found", "rc", "timed_out", "stdout", "stderr"}

# The probe's tool variables, each pointed at a stub of this name.
TOOL_VARS = {
    "SYSCTL": "sysctl",
    "SW_VERS": "sw_vers",
    "UNAME": "uname",
    "VM_STAT": "vm_stat",
    "PGREP": "pgrep",
    "VBOXMANAGE": "VBoxManage",
    "IFCONFIG": "ifconfig",
    "NETWORKSETUP": "networksetup",
    "PMSET": "pmset",
    "FDESETUP": "fdesetup",
    "SOCKETFILTERFW": "socketfilterfw",
    "CSRUTIL": "csrutil",
    "KUBECTL": "kubectl",
    "CONDA": "conda",
    "SHASUM": "shasum",
    "PYTHON": "python3",
}
# Inherited values of these must never reach a case.
SCRUBBED = tuple(TOOL_VARS) + ("FIND", "ALIAS_CHECK", "SIGNING_CHECK", "SIGNING_PREFLIGHT", "JUNIPER_ROOT")
TRIPWIRES = ("gpg", "gpg2", "gpgconf", "gpg-agent", "gpg-connect-agent", "ssh", "ssh-add", "ssh-keygen", "gh", "git", "security", "ykman", "docker", "sudo", "defaults")

# A stub: log the call, then answer from the response table (id<TAB>argv), or refuse.
STUB = """\
#!/bin/bash
want="${0##*/}${*:+ $*}"
printf '%s\\n' "$want" >> "$STUB_LOG"
while IFS=$'\\t' read -r id args; do
    if [ "$args" = "$want" ]; then
        if [ -f "$STUB_DIR/$id.sleep" ]; then sleep "$(cat "$STUB_DIR/$id.sleep")"; fi
        cat "$STUB_DIR/$id.out"
        cat "$STUB_DIR/$id.err" >&2
        exit "$(cat "$STUB_DIR/$id.rc")"
    fi
done < "$STUB_DIR/index.tsv"
echo "stub: no response for: $want" >&2
exit 99
"""

TRIPWIRE = """\
#!/bin/bash
printf '%s %s\\n' "${0##*/}" "$*" >> "$STUB_TRIPWIRE_LOG"
exit 97
"""

# Captures from turing, 2026-10-20.
TURING_VM_STAT = """\
Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                                4241.
Pages active:                           1352631.
Pages inactive:                         1335016.
Pages speculative:                        16843.
Pages throttled:                              0.
Pages wired down:                        896534.
"""
TURING_SWAP = "vm.swapusage: total = 11264.00M  used = 9989.50M  free = 1274.50M  (encrypted)\n"
TURING_CSRUTIL = """\
System Integrity Protection status: unknown (Custom Configuration).

Configuration:
\tApple Internal: disabled
\tKext Signing: disabled
\tFilesystem Protections: disabled
\tDebugging Restrictions: disabled
\tDTrace Restrictions: disabled
\tNVRAM Protections: disabled
\tBaseSystem Verification: enabled

This is an unsupported configuration, likely to break in the future and leave your machine in an unknown state.
"""
TURING_IFCONFIG = """\
lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384
\tinet 127.0.0.1 netmask 0xff000000
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
\tinet 192.168.50.180 netmask 0xffffff00 broadcast 192.168.50.255
\tmedia: autoselect
\tstatus: active
en7: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
\toptions=6464<VLAN_MTU,TSO4,TSO6,CHANNEL_IO,PARTIAL_CSUM,ZEROINVERT_CSUM>
\tether 00:e0:4c:68:06:b1
\tmedia: autoselect (none)
\tstatus: inactive
"""
TURING_KUBECTL = '{\n  "clientVersion": {\n    "major": "1",\n    "minor": "22",\n    "gitVersion": "v1.22.4",\n    "platform": "darwin/amd64"\n  }\n}\n'
TURING_CONDA = """\
# conda environments:
#
# *  -> active
# + -> frozen
                         /Users/pcalnon/opt/anaconda3
base                     /usr/local/miniforge3
JuniperPython        *   /usr/local/miniforge3/envs/JuniperPython
"""
VBOX_UNREGISTERED = "VBoxManage: error: Could not find a registered machine named 'juniper-macvm'\n"
ALIAS_JSON = '{\n  "schema": 1,\n  "mode": "check",\n  "ok": false,\n  "exit_code": 1\n}\n'
SIGNING_JSON = '{\n  "schema": 1,\n  "mode": "check",\n  "ok": true,\n  "exit_code": 0\n}\n'
PREFLIGHT_TEXT = "PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor 'mac'\n"


class ProbeHarness:
    """A temp tree: stub programs, a response table, a fake HOME and a fake Juniper root."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.bin = tmp / "stubs"
        self.trip = tmp / "tripwires"
        self.responses = tmp / "responses"
        self.home = tmp / "home"
        self.root = tmp / "juniper"
        self.log = tmp / "stub.log"
        self.trip_log = tmp / "tripwire.log"
        for path in (self.bin, self.trip, self.responses, self.home, self.root):
            path.mkdir(parents=True)
        self.log.touch()
        self.trip_log.touch()
        self.index: list[str] = []
        for name in set(TOOL_VARS.values()) | {"alias_check.py", "signing_check.py", "preflight.bash"}:
            self._write_exe(self.bin / name, STUB)
        for name in TRIPWIRES:
            self._write_exe(self.trip / name, TRIPWIRE)
        self.alias = self.bin / "alias_check.py"
        self.signing = self.bin / "signing_check.py"
        self.preflight = self.bin / "preflight.bash"
        self.default_responses()

    @staticmethod
    def _write_exe(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
        path.chmod(0o755)

    def respond(self, argv: str, out: str = "", rc: int = 0, err: str = "", sleep: str | None = None) -> None:
        """Answer the stub call ``argv`` (program name, then its arguments, space-joined)."""
        rid = str(len(self.index))
        (self.responses / f"{rid}.out").write_text(out, encoding="utf-8")
        (self.responses / f"{rid}.err").write_text(err, encoding="utf-8")
        (self.responses / f"{rid}.rc").write_text(str(rc), encoding="utf-8")
        if sleep is not None:
            (self.responses / f"{rid}.sleep").write_text(sleep, encoding="utf-8")
        # A later answer for the same argv wins: it goes first in the table.
        self.index.insert(0, f"{rid}\t{argv}")
        (self.responses / "index.tsv").write_text("".join(f"{line}\n" for line in self.index), encoding="utf-8")

    def default_responses(self) -> None:
        r = self.respond
        r("uname -n", "turing.midcoip.net\n")
        r("uname -s", "Darwin\n")
        r("uname -m", "x86_64\n")
        r("sysctl -n machdep.cpu.brand_string", "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz\n")
        r("sysctl -n hw.ncpu", "12\n")
        r("sysctl -n hw.physicalcpu", "6\n")
        r("sysctl -n hw.memsize", "17179869184\n")
        r("sysctl -n kern.hv_support", "1\n")
        r("sw_vers -productVersion", "15.7.1\n")
        r("sw_vers -buildVersion", "24G231\n")
        r("vm_stat", TURING_VM_STAT)
        r("sysctl vm.swapusage", TURING_SWAP)
        r("pgrep -x com.docker.backend", "682\n")
        r("pgrep -x Docker Desktop", "", rc=1)
        r("pgrep -x Docker", "674\n")
        r("VBoxManage --version", "7.2.0r170228\n")
        r("VBoxManage list vms", '"<inaccessible>" {39b5dc60-bb1f-47e6-b2f8-59f63e529b25}\n')
        r("VBoxManage showvminfo juniper-macvm --machinereadable", "", rc=1, err=VBOX_UNREGISTERED)
        r("ifconfig -a", TURING_IFCONFIG)
        r("networksetup -listallhardwareports", "Hardware Port: USB 10/100/1000 LAN\nDevice: en7\nEthernet Address: 00:e0:4c:68:06:b1\n")
        r("pmset -g", "System-wide power settings:\nCurrently in use:\n standby              1\n sleep                0\n")
        r("fdesetup status", "FileVault is On.\n")
        r("socketfilterfw --getglobalstate", "Firewall is disabled. (State = 0)\n")
        r("socketfilterfw --getblockall", "Firewall has block all state set to disabled.\n")  # turing, 2026-10-25
        r("socketfilterfw --getstealthmode", "Firewall stealth mode is off\n")
        r("csrutil status", TURING_CSRUTIL)
        r("csrutil authenticated-root status", "Authenticated Root status: enabled\n")
        r("kubectl version --client -o json", TURING_KUBECTL)
        r("conda env list", TURING_CONDA)
        r(f"shasum -a 256 {self.root}/AGENTS.md", f"{'ab' * 32}  {self.root}/AGENTS.md\n")
        r(f"python3 {self.alias} --json --root {self.root}", ALIAS_JSON, rc=1)
        r(f"python3 {self.signing} --check --json --root {self.root}", SIGNING_JSON)
        r(f"preflight.bash --repo {REPO_ROOT}", PREFLIGHT_TEXT, rc=1, err="RESULT: FAILED -- 1 of 5 checks failed:\n")

    def env(self, **overrides: str) -> RedactedEnv:
        env = RedactedEnv({k: v for k, v in os.environ.items() if k not in SCRUBBED and not k.startswith(("GIT_", "STUB_"))})
        env.update({var: str(self.bin / name) for var, name in TOOL_VARS.items()})
        env.update(
            HOME=str(self.home),
            PATH=f"{self.trip}:{self.home / '.local' / 'bin'}:/usr/bin:/bin:/usr/sbin:/sbin",
            JUNIPER_ROOT=str(self.root),
            ALIAS_CHECK=str(self.alias),
            SIGNING_CHECK=str(self.signing),
            SIGNING_PREFLIGHT=str(self.preflight),
            STUB_DIR=str(self.responses),
            STUB_LOG=str(self.log),
            STUB_TRIPWIRE_LOG=str(self.trip_log),
            TMPDIR=str(self.tmp),
        )
        env.update(overrides)
        return env

    def run(self, *args: str, env: RedactedEnv | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["/bin/bash", str(SCRIPT_PATH), *args], env=env or self.env(), cwd=self.tmp, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_SECONDS)

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines()


class ProbeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.h = ProbeHarness(Path(self._tmp.name).resolve())

    def tearDown(self) -> None:
        tripped = self.h.trip_log.read_text(encoding="utf-8")
        modes = [p for p in self.h.home.rglob("*") if not p.is_symlink() and stat.S_IMODE(p.stat().st_mode) == 0]
        for path in modes:
            path.chmod(0o600)
        self._tmp.cleanup()
        self.assertEqual(tripped, "", "a credential or forbidden program ran")

    def run_json(self, *args: str, env: RedactedEnv | None = None) -> dict:
        proc = self.h.run("--json", *args, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        return json.loads(proc.stdout)

    def assertCapture(self, cap: dict, argv: list[str], stdout: str | None = None, rc: int | None = 0) -> None:
        self.assertEqual(set(cap), CAPTURE_KEYS)
        self.assertEqual(cap["argv"], argv)
        self.assertTrue(cap["found"])
        self.assertFalse(cap["timed_out"])
        self.assertEqual(cap["rc"], rc)
        if stdout is not None:
            self.assertEqual(cap["stdout"], stdout)


class UsageTest(ProbeTestCase):
    def test_help_names_every_section_and_the_never_list(self) -> None:
        proc = self.h.run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for section in SECTIONS:
            self.assertIn(f"  {section} ", proc.stdout)
        self.assertIn("No credential probe runs", proc.stdout)
        self.assertEqual(self.h.calls(), [])

    def test_bad_arguments_exit_2_before_anything_runs(self) -> None:
        cases = [
            (["--bogus"], "unknown option: --bogus"),
            (["extra"], "unexpected argument: extra"),
            (["--section", "disk"], "unknown section: 'disk'"),
            (["--section"], "--section needs a name"),
            (["--tool", "a/b"], "not a tool name: 'a/b'"),
            (["--tool", "-x"], "not a tool name: '-x'"),
            (["--timeout", "0"], "--timeout needs whole seconds"),
            (["--timeout", "abc"], "--timeout needs whole seconds"),
            (["--timeout", "3601"], "--timeout needs whole seconds"),
            (["--vm", "bad name"], "not a VM name or UUID"),
            (["--root"], "--root needs a directory"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                proc = self.h.run(*args)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(message, proc.stderr)
                self.assertEqual(proc.stdout, "")
        self.assertEqual(self.h.calls(), [])

    def test_an_unset_home_exits_2(self) -> None:
        env = self.h.env()
        del env["HOME"]
        proc = self.h.run("--json", env=env)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("HOME is not set", proc.stderr)


class DocumentTest(ProbeTestCase):
    def test_a_full_run_is_one_json_object_in_the_documented_schema(self) -> None:
        (self.h.root / "AGENTS.md").write_text("parent\n", encoding="utf-8")
        doc = self.run_json()
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["probe"], "util/host_state_probe.bash")
        self.assertRegex(doc["collected_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual((doc["node"], doc["kernel"]), ("turing.midcoip.net", "Darwin"))
        self.assertEqual((doc["home"], doc["root"], doc["repo"]), (str(self.h.home), str(self.h.root), str(REPO_ROOT)))
        self.assertEqual(doc["timeout_seconds"], 60)
        self.assertEqual(doc["sections"], SECTIONS)
        self.assertEqual(set(doc) - {"schema", "probe", "collected_at", "node", "kernel", "home", "root", "repo", "timeout_seconds", "sections"}, set(SECTIONS))
        hw = doc["hardware"]
        self.assertEqual(set(hw), {"cpu_brand", "ncpu", "physicalcpu", "memsize", "hv_support", "os_version", "os_build", "arch"})
        self.assertCapture(hw["memsize"], [str(self.h.bin / "sysctl"), "-n", "hw.memsize"], "17179869184\n")
        self.assertCapture(hw["os_version"], [str(self.h.bin / "sw_vers"), "-productVersion"], "15.7.1\n")
        self.assertCapture(hw["arch"], [str(self.h.bin / "uname"), "-m"], "x86_64\n")
        mem = doc["memory"]
        self.assertCapture(mem["vm_stat"], [str(self.h.bin / "vm_stat")], TURING_VM_STAT)
        self.assertCapture(mem["swapusage"], [str(self.h.bin / "sysctl"), "vm.swapusage"], TURING_SWAP)
        self.assertEqual([d["name"] for d in mem["docker"]], ["com.docker.backend", "Docker Desktop", "Docker"])
        self.assertCapture(mem["docker"][1]["pgrep"], [str(self.h.bin / "pgrep"), "-x", "Docker Desktop"], "", rc=1)
        vm = doc["vm"]
        self.assertEqual(vm["name"], "juniper-macvm")
        self.assertCapture(vm["showvminfo"], [str(self.h.bin / "VBoxManage"), "showvminfo", "juniper-macvm", "--machinereadable"], "", rc=1)
        self.assertEqual(vm["showvminfo"]["stderr"], VBOX_UNREGISTERED)
        self.assertCapture(doc["network"]["ifconfig"], [str(self.h.bin / "ifconfig"), "-a"], TURING_IFCONFIG)
        self.assertCapture(doc["power"]["pmset"], [str(self.h.bin / "pmset"), "-g"])
        sec = doc["security"]
        self.assertCapture(sec["sip"], [str(self.h.bin / "csrutil"), "status"], TURING_CSRUTIL)
        self.assertCapture(sec["authenticated_root"], [str(self.h.bin / "csrutil"), "authenticated-root", "status"])
        self.assertCapture(sec["firewall"], [str(self.h.bin / "socketfilterfw"), "--getglobalstate"])
        self.assertCapture(sec["blockall"], [str(self.h.bin / "socketfilterfw"), "--getblockall"], "Firewall has block all state set to disabled.\n")
        self.assertCapture(sec["stealth"], [str(self.h.bin / "socketfilterfw"), "--getstealthmode"])
        self.assertCapture(sec["filevault"], [str(self.h.bin / "fdesetup"), "status"], "FileVault is On.\n")
        self.assertCapture(doc["tools"]["kubectl_version"], [str(self.h.bin / "kubectl"), "version", "--client", "-o", "json"], TURING_KUBECTL)
        env = doc["env"]
        self.assertCapture(env["conda"], [str(self.h.bin / "conda"), "env", "list"], TURING_CONDA)
        self.assertEqual(env["parent_agents_md"]["path"], f"{self.h.root}/AGENTS.md")
        self.assertTrue(env["parent_agents_md"]["exists"])
        self.assertCapture(env["parent_agents_md"]["sha256"], [str(self.h.bin / "shasum"), "-a", "256", f"{self.h.root}/AGENTS.md"])

    def test_alias_and_signing_run_the_repo_tools_with_the_root(self) -> None:
        doc = self.run_json("--section", "alias", "--section", "signing")
        self.assertCapture(doc["alias"]["check"], [str(self.h.bin / "python3"), str(self.h.alias), "--json", "--root", str(self.h.root)], ALIAS_JSON, rc=1)
        self.assertCapture(doc["signing"]["config"], [str(self.h.bin / "python3"), str(self.h.signing), "--check", "--json", "--root", str(self.h.root)], SIGNING_JSON)
        preflight = doc["signing"]["preflight"]
        self.assertEqual(preflight["argv"][1:], [str(self.h.preflight), "--repo", str(REPO_ROOT)])
        self.assertTrue(preflight["argv"][0].endswith("bash"), preflight["argv"])
        self.assertEqual((preflight["rc"], preflight["stdout"]), (1, PREFLIGHT_TEXT))
        self.assertIn("RESULT: FAILED", preflight["stderr"])

    def test_sections_are_collected_in_canonical_order_and_alone(self) -> None:
        doc = self.run_json("--section", "memory", "--section", "hardware", "--section", "memory")
        self.assertEqual(doc["sections"], ["hardware", "memory"])
        self.assertNotIn("vm", doc)
        self.assertNotIn("security", doc)
        programs = sorted({call.split()[0] for call in self.h.calls()})
        self.assertEqual(programs, ["pgrep", "sw_vers", "sysctl", "uname", "vm_stat"])

    def test_the_vm_name_and_timeout_flags_reach_the_document(self) -> None:
        self.h.respond("VBoxManage showvminfo other-vm --machinereadable", 'VMState="poweroff"\nmemory=8192\n')
        doc = self.run_json("--section", "vm", "--vm", "other-vm", "--timeout", "7")
        self.assertEqual(doc["vm"]["name"], "other-vm")
        self.assertEqual(doc["timeout_seconds"], 7)
        self.assertCapture(doc["vm"]["showvminfo"], [str(self.h.bin / "VBoxManage"), "showvminfo", "other-vm", "--machinereadable"], 'VMState="poweroff"\nmemory=8192\n')

    def test_the_root_defaults_to_juniper_root_and_is_made_absolute(self) -> None:
        doc = self.run_json("--section", "env")
        self.assertEqual(doc["root"], str(self.h.root))
        (self.h.tmp / "rel").mkdir()
        doc = self.run_json("--section", "env", "--root", "rel")
        self.assertEqual(doc["root"], f"{self.h.tmp}/rel")
        self.assertFalse(doc["env"]["parent_agents_md"]["exists"])
        self.assertIsNone(doc["env"]["parent_agents_md"]["sha256"])


class CaptureTest(ProbeTestCase):
    def test_a_failing_command_is_recorded_with_its_exit_code_and_stderr(self) -> None:
        self.h.respond("pmset -g", "partial\n", rc=3, err="pmset: boom\n")
        doc = self.run_json("--section", "power")
        cap = doc["power"]["pmset"]
        self.assertEqual((cap["rc"], cap["stdout"], cap["stderr"], cap["found"], cap["timed_out"]), (3, "partial\n", "pmset: boom\n", True, False))

    def test_a_missing_program_is_recorded_not_fatal(self) -> None:
        doc = self.run_json("--section", "vm", env=self.h.env(VBOXMANAGE=str(self.h.tmp / "no" / "VBoxManage")))
        for key in ("version", "list_vms", "showvminfo"):
            cap = doc["vm"][key]
            self.assertEqual((cap["found"], cap["rc"], cap["stdout"], cap["stderr"], cap["timed_out"]), (False, None, "", "", False), key)
        self.assertNotIn("VBoxManage", " ".join(self.h.calls()))

    def test_a_non_executable_program_counts_as_missing(self) -> None:
        (self.h.bin / "pmset").chmod(0o644)
        doc = self.run_json("--section", "power")
        self.assertFalse(doc["power"]["pmset"]["found"])

    def test_a_hung_command_is_killed_at_the_timeout(self) -> None:
        self.h.respond("pmset -g", "never\n", sleep="60")
        started = time.monotonic()
        doc = self.run_json("--section", "power", "--timeout", "1")
        elapsed = time.monotonic() - started
        cap = doc["power"]["pmset"]
        self.assertTrue(cap["timed_out"])
        self.assertNotEqual(cap["rc"], 0)
        self.assertLess(elapsed, 30)

    def test_output_round_trips_through_json_less_control_characters(self) -> None:
        tricky = 'quote " back\\slash \ttab\r\nnew\x01\x07\x1b[0m\x1f\x7f caf\u00e9 \U0001f680 & %s \\n\n\n'
        self.h.respond("pmset -g", tricky, err="e\x02rr\n")
        doc = self.run_json("--section", "power")
        cap = doc["power"]["pmset"]
        self.assertEqual(cap["stdout"], 'quote " back\\slash \ttab\r\nnew[0m\x7f caf\u00e9 \U0001f680 & %s \\n\n\n')
        self.assertEqual(cap["stderr"], "err\n")

    def test_an_argument_with_spaces_and_quotes_is_one_argv_word(self) -> None:
        root = self.h.tmp / 'odd "root" dir'
        root.mkdir()
        (root / "AGENTS.md").write_text("x\n", encoding="utf-8")
        self.h.respond(f"shasum -a 256 {root}/AGENTS.md", "cd" * 32 + "\n")
        doc = self.run_json("--section", "env", "--root", str(root))
        self.assertEqual(doc["env"]["parent_agents_md"]["sha256"]["argv"][-1], f"{root}/AGENTS.md")
        self.assertEqual(doc["env"]["parent_agents_md"]["sha256"]["rc"], 0)


class SecurityTest(ProbeTestCase):
    def make(self, rel: str, mode: int) -> Path:
        path = self.h.home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture: no key material\n", encoding="utf-8")
        path.chmod(mode)
        return path

    def test_key_exports_and_loose_files_are_found_by_name_and_mode_only(self) -> None:
        # Mode 000 throughout: a read of any of these would fail; name and mode tests do not.
        self.make(".ssh/priv.asc", 0o000)
        self.make(".ssh/pub.asc", 0o000)
        self.make(".ssh/github-recovery-codes.txt", 0o000)
        self.make(".gnupg/gen3/0xCC413455A72974D0.priv.asc", 0o000)
        self.make(".gnupg/gen3/deep/er/than/four/x.asc", 0o000)
        self.make(".gnupg/private-keys-v1.d/ABC.key", 0o000)
        self.make(".ssh/id_ed25519_github_juniper-ml", 0o600)
        self.make(".ssh/id-turing-aws-ec2.pem", 0o644)
        self.make(".ssh/config", 0o640)
        self.make(".ssh/world", 0o601)
        self.make(".ssh/id_ed25519_github_juniper-ml.pub", 0o644)
        self.make(".ssh/known_hosts", 0o644)
        self.make(".ssh/known_hosts.old", 0o644)
        self.make(".ssh/authorized_keys", 0o644)
        self.make(".ssh/sub/nested-key", 0o644)
        os.symlink(self.h.home / ".ssh" / "priv.asc", self.h.home / ".ssh" / "linked.asc")
        doc = self.run_json("--section", "security")
        exports = doc["security"]["key_exports"]
        self.assertEqual(exports["dirs"], [f"{self.h.home}/.ssh", f"{self.h.home}/.gnupg"])
        self.assertEqual(exports["find"]["rc"], 0, exports["find"]["stderr"])
        found = sorted(p.replace(str(self.h.home), "~") for p in exports["find"]["stdout"].splitlines())
        self.assertEqual(found, ["~/.gnupg/gen3/0xCC413455A72974D0.priv.asc", "~/.ssh/github-recovery-codes.txt", "~/.ssh/linked.asc", "~/.ssh/priv.asc", "~/.ssh/pub.asc"])
        loose = doc["security"]["ssh_loose"]
        self.assertEqual(loose["dir"], f"{self.h.home}/.ssh")
        self.assertEqual(sorted(p.replace(str(self.h.home), "~") for p in loose["find"]["stdout"].splitlines()), ["~/.ssh/config", "~/.ssh/id-turing-aws-ec2.pem", "~/.ssh/world"])

    def test_missing_directories_record_no_search(self) -> None:
        doc = self.run_json("--section", "security")
        self.assertEqual(doc["security"]["key_exports"], {"dirs": [], "find": None})
        self.assertEqual(doc["security"]["ssh_loose"], {"dir": f"{self.h.home}/.ssh", "find": None})
        self.make(".gnupg/a.asc", 0o600)
        doc = self.run_json("--section", "security")
        self.assertEqual(doc["security"]["key_exports"]["dirs"], [f"{self.h.home}/.gnupg"])
        self.assertIsNone(doc["security"]["ssh_loose"]["find"])

    def test_the_text_report_names_files_without_reading_them(self) -> None:
        self.make(".ssh/priv.asc", 0o000)
        proc = self.h.run("--section", "security")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"{self.h.home}/.ssh/priv.asc", proc.stdout)
        self.assertNotIn("fixture: no key material", proc.stdout)


class ToolsTest(ProbeTestCase):
    def test_each_tool_records_command_v_and_its_local_bin_entry(self) -> None:
        local = self.h.home / ".local" / "bin"
        local.mkdir(parents=True)
        target = self.h.tmp / "opt" / "yq"
        target.parent.mkdir()
        target.write_text("#!/bin/sh\n", encoding="utf-8")
        target.chmod(0o755)
        os.symlink(target, local / "yq")
        (local / "sops").write_text("#!/bin/sh\n", encoding="utf-8")
        (local / "sops").chmod(0o755)
        os.symlink(self.h.tmp / "gone", local / "age")
        (local / "ykman").write_text("#!/bin/sh\n", encoding="utf-8")
        (local / "ykman").chmod(0o644)
        proc = self.h.run("--json", "--section", "tools", "--tool", "yq", "--tool", "extra-tool", "--tool", "extra-tool")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # json.loads keeps one of two duplicate keys, so the raw text is what shows a tool once.
        self.assertEqual(proc.stdout.count('"extra-tool":'), 1)
        self.assertEqual(proc.stdout.count('"yq":'), 1)
        doc = json.loads(proc.stdout)
        tools = doc["tools"]
        self.assertEqual(tools["local_bin"], str(local))
        resolved = tools["resolved"]
        self.assertEqual(list(resolved).count("yq"), 1)
        self.assertEqual(list(resolved)[-1], "extra-tool")
        self.assertEqual(resolved["yq"], {"path": str(local / "yq"), "local_bin": {"exists": True, "executable": True, "link": str(target)}})
        self.assertEqual(resolved["sops"], {"path": str(local / "sops"), "local_bin": {"exists": True, "executable": True, "link": None}})
        # command -v skips a dangling link and a non-executable file, so those two may resolve to a
        # host's own copy further along PATH; only the ~/.local/bin entries are pinned.
        self.assertEqual(resolved["age"]["local_bin"], {"exists": True, "executable": False, "link": str(self.h.tmp / "gone")})
        self.assertNotEqual(resolved["age"]["path"], str(local / "age"))
        self.assertEqual(resolved["ykman"]["local_bin"], {"exists": True, "executable": False, "link": None})
        self.assertNotEqual(resolved["ykman"]["path"], str(local / "ykman"))
        self.assertEqual(resolved["extra-tool"], {"path": None, "local_bin": {"exists": False, "executable": False, "link": None}})
        # A tripwire leads PATH, so command -v finds it first; command -v never runs it.
        self.assertEqual(resolved["gpg"]["path"], str(self.h.trip / "gpg"))

    def test_an_earlier_path_entry_shadows_local_bin(self) -> None:
        local = self.h.home / ".local" / "bin"
        local.mkdir(parents=True)
        for directory in (local, self.h.tmp / "early"):
            directory.mkdir(exist_ok=True)
            (directory / "shellcheck").write_text("#!/bin/sh\n", encoding="utf-8")
            (directory / "shellcheck").chmod(0o755)
        env = self.h.env()
        env["PATH"] = f"{self.h.tmp / 'early'}:{env['PATH']}"
        doc = self.run_json("--section", "tools", env=env)
        rec = doc["tools"]["resolved"]["shellcheck"]
        self.assertEqual(rec["path"], str(self.h.tmp / "early" / "shellcheck"))
        self.assertTrue(rec["local_bin"]["executable"])


class TextModeTest(ProbeTestCase):
    def test_the_text_report_shows_each_section_and_each_outcome(self) -> None:
        self.h.respond("pmset -g", "", rc=4, err="boom\n")
        env = self.h.env(VBOXMANAGE=str(self.h.tmp / "absent"))
        proc = self.h.run("--section", "power", "--section", "vm", "--section", "hardware", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("== hardware\n", proc.stdout)
        self.assertIn("== vm\n", proc.stdout)
        self.assertIn("== power\n", proc.stdout)
        self.assertLess(proc.stdout.index("== hardware"), proc.stdout.index("== vm"))
        self.assertIn("17179869184\n", proc.stdout)
        self.assertIn("-- pmset: ", proc.stdout)
        self.assertIn("[exit 4]", proc.stdout)
        self.assertIn("stderr: boom", proc.stdout)
        self.assertIn("[not found]", proc.stdout)
        self.assertNotIn('"schema"', proc.stdout)


class ScratchDirTest(ProbeTestCase):
    """The 2026-10-26 repo tmp/ rule: without TMPDIR the run's scratch dir is this checkout's tmp/, removed on exit."""

    def test_without_tmpdir_the_scratch_dir_is_the_checkouts_tmp_and_is_removed(self) -> None:
        log = self.h.tmp / "mktemp.log"
        wrap = self.h.tmp / "wrap"
        wrap.mkdir()
        real = shutil.which("mktemp")
        self.assertIsNotNone(real)
        (wrap / "mktemp").write_text(f'#!/bin/sh\nd=$("{real}" "$@") || exit $?\nprintf \'%s\\n\' "$d" >> "{log}"\nprintf \'%s\\n\' "$d"\n', encoding="utf-8")
        (wrap / "mktemp").chmod(0o755)
        env = self.h.env(TMPDIR="")
        env["PATH"] = f"{wrap}:{env['PATH']}"
        proc = self.h.run("--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        made = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(made), 1, made)
        self.assertEqual(Path(made[0]).parent.resolve(), (REPO_ROOT / "tmp").resolve())
        self.assertFalse(Path(made[0]).exists(), "the scratch dir must be removed on exit")


@unittest.skipUnless(sys.platform == "darwin", "the real macOS tools exist only on macOS")
class RealHostTest(unittest.TestCase):
    def test_the_hardware_section_on_this_mac(self) -> None:
        env = RedactedEnv({k: v for k, v in os.environ.items() if k not in SCRUBBED})
        proc = subprocess.run(["/bin/bash", str(SCRIPT_PATH), "--json", "--section", "hardware"], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        doc = json.loads(proc.stdout)
        memsize = doc["hardware"]["memsize"]
        self.assertEqual(memsize["rc"], 0, memsize["stderr"])
        self.assertGreater(int(memsize["stdout"]), 0)
        self.assertEqual(doc["kernel"], "Darwin")
        self.assertIsNotNone(shutil.which("find"))


if __name__ == "__main__":
    unittest.main()
