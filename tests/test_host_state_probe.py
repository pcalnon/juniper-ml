#!/usr/bin/env python3
"""Hermetic gate for util/host_state_probe.bash (turing bring-up plan task G1).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The probe collects the host state that ``util/host_state_check.py`` judges against the plan's §9.3 gates
(``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md``). It judges nothing, so this
suite pins the collection contract:

- every documented capture, in its section, in the documented order, with the documented argv;
- each command's stdout and stderr round-trip through the JSON byte for byte, including backslashes,
  quotes, tabs, CRs and UTF-8. C0 control characters are dropped, and trailing newlines are removed;
- a failing, missing or hung command is recorded in its capture, never an error. A hung one is
  killed at ``--timeout``;
- ``--section`` filters and keeps the canonical order; a bad argument exits 2; the probe never exits 1;
- names and modes only. key-material-names and ssh-loose-files list names under a temp HOME. A
  canary token inside every key-shaped file never reaches the output, and no credential command
  (ssh, ssh-add, gpg, gh, ykman, security) runs.

Every external command is a stub reached through the script's tool variables, or through PATH for the
``type -P`` lookups, so the suite runs the same on macOS and on Linux CI. The stubs log every argv and
refuse any argv they were not told about. Every case runs under ``/bin/bash``, which is bash 3.2 on macOS
(the plan's portability floor).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess  # nosec B404 - drives the probe under /bin/bash with stub tools
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "host_state_probe.bash"
BASH = os.environ.get("HOST_STATE_TEST_BASH", "/bin/bash")  # set it to run the suite under another bash
TIMEOUT_SECONDS = 120

SECTIONS = ["hardware", "memory", "docker", "hypervisor", "disk", "power", "network", "security", "toolchain", "env", "git", "signing"]
DEFAULT_TOOLS = "brew git gh gpg gpg-agent pinentry-mac ykman conda mamba python3 uv pre-commit gitleaks shellcheck markdownlint-cli2 yamllint actionlint sops age age-keygen yq jq node timeout iperf3 VBoxManage docker kubectl helm claude".split()
CANARY = "CANARY-host-state-probe-7f3a9c"  # written inside every key-shaped fixture; must never be printed

# turing, 2026-10-20 (Intel, macOS 15.7.1), as the probe captured them; trimmed where long.
SYSCTL_HW = "machdep.cpu.brand_string: Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz\nhw.ncpu: 12\nhw.physicalcpu: 6\nhw.memsize: 17179869184\nkern.hv_support: 1\n"
SW_VERS = "ProductName:\t\tmacOS\nProductVersion:\t\t15.7.1\nBuildVersion:\t\t24G231\n"
VM_STAT = """\
Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                                5194.
Pages active:                           1128871.
Pages inactive:                         1095529.
Pages speculative:                        32127.
Pages throttled:                              0.
Pages wired down:                        931471.
"""
SWAP = "vm.swapusage: total = 12288.00M  used = 9440.00M  free = 2848.00M  (encrypted)\n"
SHOWVMINFO_ERR = "VBoxManage: error: Could not find a registered machine named 'juniper-macvm'\nVBoxManage: error: Details: code VBOX_E_OBJECT_NOT_FOUND (0x80bb0001)\n"
IFCONFIG = """\
lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384
\tinet 127.0.0.1 netmask 0xff000000
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
\tether 3e:ac:bd:89:1d:30
\tinet 192.168.50.180 netmask 0xffffff00 broadcast 192.168.50.255
\tmedia: autoselect
\tstatus: active
en7: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
\tether 00:e0:4c:68:06:b1
\tmedia: autoselect (none)
\tstatus: inactive
"""
CSRUTIL_STATUS = "System Integrity Protection status: unknown (Custom Configuration).\n\nConfiguration:\n\tKext Signing: disabled\n\tBaseSystem Verification: enabled\n"
KUBECTL_JSON = '{\n  "clientVersion": {\n    "major": "1",\n    "minor": "22",\n    "gitVersion": "v1.22.4"\n  }\n}\n'
CONDA_LIST = "\n# conda environments:\n#\n                         /opt/anaconda3/envs/dynet\nbase                     /usr/local/miniforge3\nJuniperData              /usr/local/miniforge3/envs/JuniperData\nJuniperPython        *   /usr/local/miniforge3/envs/JuniperPython\n"
# The argv round trip: backslashes, quotes, a tab, a CR, '&' (bash 5.2 patsub_replacement), UTF-8, and
# controls that must be dropped (\x01, ESC).
NASTY = 'back\\slash \\\\two "quoted" tab\there cr\rend & amp \\n not-a-newline caf\u00e9 \x01ctl \x1b[0m ok'
NASTY_CLEAN = 'back\\slash \\\\two "quoted" tab\there cr\rend & amp \\n not-a-newline caf\u00e9 ctl [0m ok'


class Harness:
    """A temp HOME, Juniper root and stub bin dir; ``run`` drives the probe under /bin/bash."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.home = tmp / "home"
        self.root = self.home / "Development" / "python" / "Juniper"
        self.bin = tmp / "bin"
        self.fixtures = tmp / "fixtures"
        self.log = tmp / "stub.log"
        self.workdir = tmp / "work"
        for d in (self.home, self.root / "juniper-ml", self.bin, self.fixtures, self.workdir, self.home / ".local" / "bin"):
            d.mkdir(parents=True, exist_ok=True)
        self.log.touch()
        self.vars: dict[str, str] = {}
        self.install_defaults()

    # -- stubs -----------------------------------------------------------------------------------
    def stub(self, var: str | None, name: str, cases: dict[tuple[str, ...], tuple[str, str, int]], *, sleep: int = 0) -> Path:
        """A bash stub that logs its argv, then prints the (stdout, stderr, exit) recorded for that argv."""
        d = self.fixtures / name
        d.mkdir(parents=True, exist_ok=True)
        lines = ["#!/bin/bash", f'printf "%s\\n" "{name} $*" >> {shlex.quote(str(self.log))}', 'case "$*" in']
        for n, (argv, (out, err, rc)) in enumerate(cases.items()):
            (d / f"{n}.out").write_text(out, encoding="utf-8")
            (d / f"{n}.err").write_text(err, encoding="utf-8")
            lines.append(f"  {shlex.quote(' '.join(argv))}) n={n}; rc={rc} ;;")
        lines.append(f'  *) echo "stub {name}: unexpected argv: $*" >&2; exit 99 ;;')
        lines.append("esac")
        if sleep:
            lines.append(f"exec sleep {sleep}")
        lines.append(f'cat {shlex.quote(str(d))}/"$n".out')
        lines.append(f'cat {shlex.quote(str(d))}/"$n".err >&2')
        lines.append('exit "$rc"')
        path = self.bin / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        path.chmod(0o700)
        if var:
            self.vars[var] = str(path)
        return path

    def install_defaults(self) -> None:
        root = str(self.root)
        self.stub("SYSCTL", "sysctl", {("machdep.cpu.brand_string", "hw.ncpu", "hw.physicalcpu", "hw.memsize", "kern.hv_support"): (SYSCTL_HW, "", 0), ("vm.swapusage",): (SWAP, "", 0)})
        self.stub("SW_VERS", "sw_vers", {(): (SW_VERS, "", 0)})
        self.stub("UNAME", "uname", {("-m",): ("x86_64\n", "", 0)})
        self.stub("VM_STAT", "vm_stat", {(): (VM_STAT, "", 0)})
        self.stub("PGREP", "pgrep", {("-x", "com.docker.backend"): ("682\n", "", 0), ("-x", "Docker Desktop"): ("", "", 1), ("-x", "Docker"): ("674\n", "", 0)})
        self.stub(
            "VBOXMANAGE",
            "VBoxManage",
            {
                ("--version",): ("7.2.0r170228\n", "", 0),
                ("list", "vms"): ('"<inaccessible>" {39b5dc60-bb1f-47e6-b2f8-59f63e529b25}\n', "", 0),
                ("showvminfo", "juniper-macvm", "--machinereadable"): ("", SHOWVMINFO_ERR, 1),
            },
        )
        self.stub("DF", "df", {("-k", "/"): ("Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/disk1s1 488245288 10 20 1% /\n", "", 0), ("-k", "/", "/System/Volumes/Data"): ("Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/disk1s5 488245288 30 40 1% /System/Volumes/Data\n", "", 0)})
        self.stub("PMSET", "pmset", {("-g",): ("System-wide power settings:\n standby              1\n sleep                0\n", "", 0)})
        self.stub("IFCONFIG", "ifconfig", {("-a",): (IFCONFIG, "", 0)})
        self.stub("CSRUTIL", "csrutil", {("status",): (CSRUTIL_STATUS, "", 0), ("authenticated-root", "status"): ("Authenticated Root status: enabled\n", "", 0)})
        self.stub("FDESETUP", "fdesetup", {("status",): ("FileVault is On.\n", "", 0)})
        self.stub("SOCKETFILTERFW", "socketfilterfw", {("--getglobalstate",): ("Firewall is disabled. (State = 0)\n", "", 0), ("--getstealthmode",): ("Firewall stealth mode is off\n", "", 0)})
        self.stub("KUBECTL", "kubectl-stub", {("version", "--client", "-o", "json"): (KUBECTL_JSON, "", 0)})
        self.stub("CONDA", "conda-stub", {("env", "list"): (CONDA_LIST, "", 0)})
        self.stub("SHASUM", "shasum-stub", {("-a", "256", f"{root}/AGENTS.md"): ("ab" * 32 + f"  {root}/AGENTS.md\n", "", 0)})
        self.stub("HOSTNAME_BIN", "hostname-stub", {("-s",): ("turing\n", "", 0)})
        # Credential-bearing commands: logged if anything ever runs them.
        for name in ("ssh", "ssh-add", "gpg", "gpg-connect-agent", "gh", "ykman", "security"):
            self.stub(None, name, {})
        self.vars["PYTHON"] = sys.executable
        self.vars["ALIAS_CHECK"] = str(self.sibling("alias_check.py", '{"schema": 1, "exit_code": 0, "ok": true, "summary": "summary: 30 of 30 checks passed"}'))
        self.vars["SIGNING_CHECK"] = str(self.sibling("signing_check.py", '{"schema": 1, "exit_code": 0, "ok": true, "summary": "OK -- all 16 checks passed"}'))
        preflight = self.tmp / "preflight.bash"
        preflight.write_text(f'#!/bin/bash\nprintf "%s\\n" "preflight $*" >> {shlex.quote(str(self.log))}\necho "PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor \'mac\'"\necho "RESULT: OK" >&2\nexit 0\n', encoding="utf-8")
        self.vars["SIGNING_PREFLIGHT"] = str(preflight)

    def sibling(self, name: str, payload: str) -> Path:
        """A stand-in for a sibling Python tool: logs its argv and prints ``payload``."""
        path = self.tmp / name
        path.write_text(f"import sys\nwith open({str(self.log)!r}, 'a', encoding='utf-8') as fh:\n    fh.write({name!r} + ' ' + ' '.join(sys.argv[1:]) + '\\n')\nprint({payload!r})\n", encoding="utf-8")
        return path

    # -- runs ------------------------------------------------------------------------------------
    def env(self, **overrides: str) -> RedactedEnv:
        base = {key: os.environ[key] for key in ("LANG", "LC_ALL", "LC_CTYPE") if key in os.environ}
        env = RedactedEnv(base, HOME=str(self.home), TMPDIR=str(self.tmp), PATH=f"{self.home}/.local/bin:{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin", JUNIPER_ROOT=str(self.root))
        env.update(self.vars)
        env.update(overrides)
        return env

    def run(self, *args: str, **overrides: str) -> subprocess.CompletedProcess:
        return subprocess.run([BASH, str(SCRIPT_PATH), *args], cwd=self.workdir, env=self.env(**overrides), capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def run_json(self, *args: str, **overrides: str) -> dict:
        proc = self.run("--json", *args, **overrides)
        if proc.returncode != 0:
            raise AssertionError(f"probe exited {proc.returncode}: {proc.stderr}")
        return json.loads(proc.stdout)

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines()


def captures(doc: dict, section: str | None = None) -> dict[str, dict]:
    return {c["name"]: c for c in doc["captures"] if section is None or c["section"] == section}


def setUpModule() -> None:
    if not os.access(BASH, os.X_OK):
        raise unittest.SkipTest(f"{BASH} not found")


class ProbeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.h = Harness(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()


class JsonContractTest(ProbeTestCase):
    def test_the_document_carries_every_section_and_capture_in_order(self) -> None:
        doc = self.h.run_json()
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["tool"], "util/host_state_probe.bash")
        self.assertEqual(doc["host"], "turing")
        self.assertRegex(doc["collected_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(doc["sections"], SECTIONS)
        self.assertEqual((doc["home"], doc["root"], doc["vm"], doc["timeout_seconds"]), (str(self.h.home), str(self.h.root), "juniper-macvm", 60))
        self.assertTrue(doc["bash_version"])
        self.assertIn(str(self.h.bin), doc["path"])
        order = [(c["section"], c["name"]) for c in doc["captures"]]
        self.assertEqual([s for s, _ in order], sorted((s for s, _ in order), key=SECTIONS.index), "captures follow the section order")
        expected = {
            "hardware": ["sysctl", "sw_vers", "uname-m"],
            "memory": ["vm_stat", "swapusage"],
            "docker": ["pgrep:com.docker.backend", "pgrep:Docker Desktop", "pgrep:Docker"],
            "hypervisor": ["vboxmanage-version", "vboxmanage-list-vms", "vboxmanage-showvminfo"],
            "disk": ["df"],
            "power": ["pmset"],
            "network": ["ifconfig"],
            "security": ["csrutil-status", "csrutil-authenticated-root", "fdesetup-status", "firewall-globalstate", "firewall-stealthmode", "key-material-names", "ssh-loose-files"],
            "toolchain": [f"command-v:{t}" for t in DEFAULT_TOOLS] + ["kubectl-version"],
            "env": ["conda-env-list", "parent-agents-md"],
            "git": ["git-remote-alias-check"],
            "signing": ["configure-commit-signing", "headless-signing-preflight"],
        }
        for section in SECTIONS:
            with self.subTest(section=section):
                self.assertEqual([n for s, n in order if s == section], expected[section])
        for cap in doc["captures"]:
            self.assertEqual(set(cap), {"section", "name", "command", "exit_code", "timed_out", "skipped", "stdout", "stderr"})

    def test_stub_output_round_trips_verbatim(self) -> None:
        doc = self.h.run_json()
        caps = captures(doc)
        self.assertEqual(caps["sysctl"]["stdout"], SYSCTL_HW.rstrip("\n"))
        self.assertEqual(caps["vm_stat"]["stdout"], VM_STAT.rstrip("\n"))
        self.assertEqual(caps["swapusage"]["stdout"], SWAP.rstrip("\n"))
        self.assertEqual(caps["ifconfig"]["stdout"], IFCONFIG.rstrip("\n"))
        self.assertEqual(caps["csrutil-status"]["stdout"], CSRUTIL_STATUS.rstrip("\n"))
        self.assertEqual(caps["kubectl-version"]["stdout"], KUBECTL_JSON.rstrip("\n"))
        self.assertEqual(caps["conda-env-list"]["stdout"], CONDA_LIST.rstrip("\n"), "a leading blank line is kept; only trailing newlines go")
        self.assertEqual(caps["sw_vers"]["stdout"], SW_VERS.rstrip("\n"), "tabs survive")
        showvminfo = caps["vboxmanage-showvminfo"]
        self.assertEqual((showvminfo["exit_code"], showvminfo["stdout"], showvminfo["stderr"]), (1, "", SHOWVMINFO_ERR.rstrip("\n")))
        self.assertEqual((caps["pgrep:Docker Desktop"]["exit_code"], caps["pgrep:Docker"]["stdout"]), (1, "674"))

    def test_hard_characters_survive_and_controls_are_dropped(self) -> None:
        self.h.stub("SW_VERS", "sw_vers", {(): (NASTY + "\n\n", NASTY + "\n", 3)})
        for env in ({}, {"LC_ALL": "C"}):
            with self.subTest(env=env):
                proc = self.h.run("--json", "--section", "hardware", **env)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                cap = captures(json.loads(proc.stdout))["sw_vers"]
                self.assertEqual((cap["stdout"], cap["stderr"], cap["exit_code"]), (NASTY_CLEAN, NASTY_CLEAN, 3))

    def test_every_command_is_the_documented_argv(self) -> None:
        doc = self.h.run_json()
        caps = captures(doc)
        root = str(self.h.root)
        want = {
            "sysctl": [self.h.vars["SYSCTL"], "machdep.cpu.brand_string", "hw.ncpu", "hw.physicalcpu", "hw.memsize", "kern.hv_support"],
            "swapusage": [self.h.vars["SYSCTL"], "vm.swapusage"],
            "pgrep:Docker Desktop": [self.h.vars["PGREP"], "-x", "Docker Desktop"],
            "vboxmanage-showvminfo": [self.h.vars["VBOXMANAGE"], "showvminfo", "juniper-macvm", "--machinereadable"],
            "csrutil-authenticated-root": [self.h.vars["CSRUTIL"], "authenticated-root", "status"],
            "firewall-stealthmode": [self.h.vars["SOCKETFILTERFW"], "--getstealthmode"],
            "kubectl-version": [self.h.vars["KUBECTL"], "version", "--client", "-o", "json"],
            "conda-env-list": [self.h.vars["CONDA"], "env", "list"],
            "git-remote-alias-check": [sys.executable, "-I", self.h.vars["ALIAS_CHECK"], "--json", "--root", root],
            "configure-commit-signing": [sys.executable, "-I", self.h.vars["SIGNING_CHECK"], "--check", "--json", "--root", root],
            "headless-signing-preflight": [BASH, self.h.vars["SIGNING_PREFLIGHT"], "--repo", f"{root}/juniper-ml"],
        }
        for name, argv in want.items():
            with self.subTest(name=name):
                self.assertEqual(shlex.split(caps[name]["command"]), argv)
        logged = self.h.calls()
        self.assertIn(f"alias_check.py --json --root {root}", logged)
        self.assertIn(f"signing_check.py --check --json --root {root}", logged)
        self.assertIn(f"preflight --repo {root}/juniper-ml", logged)

    def test_the_vm_option_reaches_showvminfo(self) -> None:
        self.h.stub("VBOXMANAGE", "VBoxManage", {("--version",): ("7.2.4\n", "", 0), ("list", "vms"): ("", "", 0), ("showvminfo", "other-vm", "--machinereadable"): ('VMState="poweroff"\nmemory=6144\n', "", 0)})
        doc = self.h.run_json("--section", "hypervisor", "--vm", "other-vm")
        self.assertEqual(doc["vm"], "other-vm")
        self.assertEqual(captures(doc)["vboxmanage-showvminfo"]["stdout"], 'VMState="poweroff"\nmemory=6144')


class FailureCaptureTest(ProbeTestCase):
    def test_a_missing_tool_is_recorded_not_fatal(self) -> None:
        doc = self.h.run_json("--section", "memory", VM_STAT=str(self.h.tmp / "no-such-vm_stat"))
        cap = captures(doc)["vm_stat"]
        self.assertEqual(cap["exit_code"], 127)
        self.assertFalse(cap["timed_out"])
        self.assertIsNone(cap["skipped"])
        self.assertIn("no-such-vm_stat", cap["stderr"])
        self.assertEqual(captures(doc)["swapusage"]["exit_code"], 0, "the next capture still runs")

    def test_a_hung_command_is_killed_at_the_timeout(self) -> None:
        self.h.stub("VM_STAT", "vm_stat", {(): ("", "", 0)}, sleep=60)
        started = time.monotonic()
        doc = self.h.run_json("--section", "memory", "--timeout", "1")
        elapsed = time.monotonic() - started
        cap = captures(doc)["vm_stat"]
        self.assertTrue(cap["timed_out"])
        self.assertNotEqual(cap["exit_code"], 0)
        self.assertLess(elapsed, 30, "the probe must not wait out a hung command")
        self.assertFalse(captures(doc)["swapusage"]["timed_out"])

    def test_text_mode_marks_a_timeout_and_prefixes_stderr(self) -> None:
        self.h.stub("VM_STAT", "vm_stat", {(): ("", "", 0)}, sleep=60)
        proc = self.h.run("--section", "memory", "--section", "hypervisor", "--timeout", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"(?m)^-- vm_stat: .*vm_stat \(timed out after 1s; exit \d+\)$")
        self.assertIn("stderr: VBoxManage: error: Could not find a registered machine named 'juniper-macvm'", proc.stdout)

    def test_absent_sibling_tools_and_files_are_skipped_with_a_reason(self) -> None:
        missing = str(self.h.tmp / "absent")
        doc = self.h.run_json("--section", "env", "--section", "git", "--section", "signing", ALIAS_CHECK=missing + ".py", SIGNING_CHECK=missing + "2.py", SIGNING_PREFLIGHT=missing + ".bash")
        caps = captures(doc)
        self.assertEqual(caps["parent-agents-md"]["skipped"], f"absent: {self.h.root}/AGENTS.md")
        self.assertEqual(caps["git-remote-alias-check"]["skipped"], f"absent: {missing}.py")
        self.assertEqual(caps["configure-commit-signing"]["skipped"], f"absent: {missing}2.py")
        self.assertEqual(caps["headless-signing-preflight"]["skipped"], f"absent: {missing}.bash")
        for cap in (caps["parent-agents-md"], caps["git-remote-alias-check"]):
            self.assertIsNone(cap["exit_code"])
            self.assertFalse(cap["timed_out"])
        self.assertFalse([line for line in self.h.calls() if line.startswith(("shasum-stub", "alias_check.py", "signing_check.py", "preflight"))])

    def test_the_preflight_is_skipped_without_a_juniper_ml_checkout(self) -> None:
        shutil.rmtree(self.h.root / "juniper-ml")
        doc = self.h.run_json("--section", "signing")
        self.assertEqual(captures(doc)["headless-signing-preflight"]["skipped"], f"absent: {self.h.root}/juniper-ml")

    def test_the_parent_agents_md_is_hashed_when_present(self) -> None:
        (self.h.root / "AGENTS.md").write_text("# parent\n", encoding="utf-8")
        cap = captures(self.h.run_json("--section", "env"))["parent-agents-md"]
        self.assertEqual((cap["exit_code"], cap["stdout"]), (0, "ab" * 32 + f"  {self.h.root}/AGENTS.md"))


class CredentialSafetyTest(ProbeTestCase):
    def make_key_tree(self) -> None:
        ssh, gnupg = self.h.home / ".ssh", self.h.home / ".gnupg"
        (gnupg / "gen3").mkdir(parents=True)
        ssh.mkdir()
        files = {
            ssh / "priv.asc": 0o600,
            ssh / "github-recovery-codes.txt": 0o600,
            ssh / "id_ed25519_github_juniper-ml": 0o600,
            ssh / "id_ed25519_github_juniper-ml.pub": 0o644,
            ssh / "known_hosts": 0o644,
            ssh / "config": 0o644,
            ssh / "id-turing-aws-ec2.pem": 0o640,
            gnupg / "gen3" / "0xCC413455A72974D0.sub_priv.asc": 0o600,
            gnupg / "Recovery-Notes.TXT": 0o600,
            gnupg / "pubring.kbx": 0o600,
        }
        for path, mode in files.items():
            path.write_text(f"{CANARY} {path.name}\n", encoding="utf-8")
            path.chmod(mode)
        (ssh / "sub").mkdir()
        nested = ssh / "sub" / "nested_key"
        nested.write_text(CANARY, encoding="utf-8")
        nested.chmod(0o604)

    def test_key_material_names_lists_asc_and_recovery_names_only(self) -> None:
        self.make_key_tree()
        cap = captures(self.h.run_json("--section", "security"))["key-material-names"]
        self.assertEqual(cap["exit_code"], 0)
        found = sorted(Path(line).relative_to(self.h.home).as_posix() for line in cap["stdout"].splitlines())
        self.assertEqual(found, [".gnupg/Recovery-Notes.TXT", ".gnupg/gen3/0xCC413455A72974D0.sub_priv.asc", ".ssh/github-recovery-codes.txt", ".ssh/priv.asc"])

    def test_ssh_loose_files_lists_files_open_to_group_or_others(self) -> None:
        self.make_key_tree()
        cap = captures(self.h.run_json("--section", "security"))["ssh-loose-files"]
        found = sorted(Path(line).relative_to(self.h.home).as_posix() for line in cap["stdout"].splitlines())
        self.assertEqual(found, [".ssh/config", ".ssh/id-turing-aws-ec2.pem", ".ssh/sub/nested_key"], "*.pub and known_hosts are exempt; 600 passes")

    def test_no_key_content_and_no_credential_command_ever_appears(self) -> None:
        self.make_key_tree()
        for args in (("--json",), ()):
            with self.subTest(args=args):
                proc = self.h.run(*args)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertNotIn(CANARY, proc.stdout + proc.stderr)
        credential = [line for line in self.h.calls() if line.split()[0] in ("ssh", "ssh-add", "gpg", "gpg-connect-agent", "gh", "ykman", "security")]
        self.assertEqual(credential, [])

    def test_missing_key_directories_are_skipped(self) -> None:
        caps = captures(self.h.run_json("--section", "security"))
        self.assertEqual(caps["key-material-names"]["skipped"], f"absent: {self.h.home}/.ssh and {self.h.home}/.gnupg")
        self.assertEqual(caps["ssh-loose-files"]["skipped"], f"absent: {self.h.home}/.ssh")

    def test_the_script_never_names_a_credential_command_or_reads_key_files(self) -> None:
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
        for needle in (r"\bssh-add\b", r"\bssh\s+-T\b", r"--card-status", r"\bgpg\s+-K\b", r"\bgh\s+auth\b", r"\bcat\b[^\n]*\.ssh", r"\bstat\s+-[fc]\b"):
            with self.subTest(needle=needle):
                self.assertNotRegex(code, needle)
        self.assertNotRegex(text, r"/Users/|/home/", "use a $HOME-relative path (plan D12)")


class ToolchainTest(ProbeTestCase):
    def test_lookups_follow_path_and_extra_tools_are_added_once(self) -> None:
        local = self.h.home / ".local" / "bin" / "shellcheck"
        local.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        local.chmod(0o700)
        doc = self.h.run_json("--section", "toolchain", "--tool", "my-extra-tool", "--tool", "shellcheck", "--tool", "my-extra-tool")
        caps = captures(doc, "toolchain")
        names = [c["name"] for c in doc["captures"]]
        self.assertEqual(names, [f"command-v:{t}" for t in DEFAULT_TOOLS] + ["command-v:my-extra-tool", "kubectl-version"])
        self.assertEqual((caps["command-v:shellcheck"]["exit_code"], caps["command-v:shellcheck"]["stdout"]), (0, str(local)))
        self.assertEqual((caps["command-v:my-extra-tool"]["exit_code"], caps["command-v:my-extra-tool"]["stdout"]), (1, ""))
        self.assertEqual(caps["command-v:my-extra-tool"]["command"], "type -P my-extra-tool")


class OptionsTest(ProbeTestCase):
    def test_sections_filter_and_keep_the_canonical_order(self) -> None:
        doc = self.h.run_json("--section", "signing", "--section", "hardware", "--section", "signing")
        self.assertEqual(doc["sections"], ["hardware", "signing"])
        self.assertEqual({c["section"] for c in doc["captures"]}, {"hardware", "signing"})
        self.assertFalse([line for line in self.h.calls() if line.startswith(("vm_stat", "pgrep", "VBoxManage", "ifconfig", "csrutil", "conda-stub"))])

    def test_text_mode_prints_sections_and_captures(self) -> None:
        proc = self.h.run("--section", "hardware", "--section", "docker")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("host state probe (read-only): turing at "))
        self.assertIn("sections  hardware docker\n", proc.stdout)
        self.assertIn("\n== hardware\n-- sysctl: ", proc.stdout)
        self.assertIn("hw.memsize: 17179869184\n", proc.stdout)
        self.assertRegex(proc.stdout, r"(?m)^-- pgrep:Docker Desktop: .* \(exit 1\)$")
        self.assertEqual(proc.stderr, "")

    def test_bad_arguments_exit_2_and_print_nothing_on_stdout(self) -> None:
        cases = {
            ("--section", "bogus"): "unknown section: 'bogus'",
            ("--section", "Hardware"): "unknown section",
            ("--section",): "--section needs a name",
            ("--tool", "a b"): "not a tool name",
            ("--tool", "-x"): "not a tool name",
            ("--vm", "bad;vm"): "not a VM name",
            ("--timeout", "0"): "--timeout needs whole seconds",
            ("--timeout", "10000"): "--timeout needs whole seconds",
            ("--timeout", "1.5"): "--timeout needs whole seconds",
            ("--root",): "--root needs a directory",
            ("--check",): "unknown argument: --check",
            ("extra",): "unknown argument: extra",
        }
        for args, message in cases.items():
            with self.subTest(args=args):
                proc = self.h.run(*args)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")
                self.assertIn(message, proc.stderr)
        self.assertEqual(self.h.calls(), [], "a usage error runs nothing")

    def test_help_exits_0_and_names_every_section(self) -> None:
        proc = self.h.run("--help")
        self.assertEqual(proc.returncode, 0)
        for section in SECTIONS:
            self.assertIn(section, proc.stdout)

    def test_root_option_and_juniper_root_variable(self) -> None:
        other = self.h.tmp / "other-root"
        (other / "juniper-ml").mkdir(parents=True)
        self.assertEqual(self.h.run_json("--section", "hardware", "--root", str(other))["root"], str(other))
        self.assertEqual(self.h.run_json("--section", "hardware", JUNIPER_ROOT=str(other))["root"], str(other))
        env = self.h.env()
        del env["JUNIPER_ROOT"]
        proc = subprocess.run([BASH, str(SCRIPT_PATH), "--json", "--section", "hardware"], cwd=self.h.workdir, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(json.loads(proc.stdout)["root"], f"{self.h.home}/Development/python/Juniper")

    def test_the_temporary_directory_is_removed(self) -> None:
        self.h.run_json("--section", "memory")
        self.assertEqual(sorted(p.name for p in self.h.tmp.glob("host_state_probe.*")), [])


class StaticTest(unittest.TestCase):
    text: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SCRIPT_PATH.read_text(encoding="utf-8")

    def test_the_header_documents_the_contract(self) -> None:
        for needle in ("set -euo pipefail", "Exit codes:", "JSON (--json), schema 1", "names and modes, never contents", "util/host_state_check.py", "2026-10-15_turing_host_state_probe.bash"):
            self.assertIn(needle, self.text)
        for section in SECTIONS:
            self.assertRegex(self.text, rf"(?m)^#   {section}\s")

    def test_every_macos_tool_is_an_overridable_variable(self) -> None:
        for var in ("SYSCTL", "SW_VERS", "UNAME", "VM_STAT", "PGREP", "VBOXMANAGE", "DF", "PMSET", "IFCONFIG", "CSRUTIL", "FDESETUP", "SOCKETFILTERFW", "FIND", "KUBECTL", "CONDA", "SHASUM", "HOSTNAME_BIN", "PYTHON", "ALIAS_CHECK", "SIGNING_CHECK", "SIGNING_PREFLIGHT"):
            with self.subTest(var=var):
                self.assertRegex(self.text, rf'(?m)^{var}="\$\{{{var}:-')
        code = [line for line in self.text.splitlines() if not line.lstrip().startswith("#") and not re.match(r"^[A-Z_]+=", line)]
        for line in code:
            self.assertNotRegex(line, r"(?<![\w$])/(usr|sbin|bin)/\w", f"call the tool through its variable: {line}")

    def test_the_shell_parses_under_bin_bash(self) -> None:
        proc = subprocess.run([BASH, "-n", str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_shellcheck_clean_when_available(self) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            self.skipTest("shellcheck not installed (the pre-commit hook covers util/*.bash)")
        proc = subprocess.run([shellcheck, str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
