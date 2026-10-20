#!/usr/bin/env python3
"""Gate for util/host_state_check.py and conf/hosts/turing/expected.yaml (turing bring-up task G1, R-G1).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``util/host_state_check.py`` evaluates the seven host gates that §9.3 of
``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` assigns it: G-ALIAS, G-SIGN, G-SEC,
G-TOOLS, G-ENV, G-NET and G-MEM. It reads util/host_state_probe.bash's captures and compares them with
``conf/hosts/<host>/expected.yaml``. The suite pins:

- every condition of every gate, from probe documents built here. turing's state on 2026-10-20 is the
  base fixture, and each case changes one capture;
- R-G1: an expected.yaml that asks for more VM memory than hw.memsize minus the reserve fails G-MEM's
  ``vm-fits``. The primer's 44 GiB VM is the X2 class;
- G-MEM agrees with util/macvm_ctl.bash, its implementation of record. On the same vm_stat, swap,
  pgrep and VirtualBox fixtures, ``macvm_ctl.bash status`` and this checker print the same verdict
  and the same text for memory, swap and docker;
- the exit codes (report 0; check 1 on a failure, 2 on an unknown; 2 on usage and environment errors)
  and the JSON schema;
- the committed expected.yaml. It loads; its G-MEM numbers equal macvm_ctl.bash's defaults; its
  ``local_bin`` tools are the ones conf/hosts/turing/hosttools-environment.yml installs (E-D6); and its
  conda envs include every spec under conf/hosts/turing/conda-envs/;
- the probe contract, end to end: the checker runs the real probe under ``/bin/bash`` with stub tools
  and passes it ``--section``, ``--tool`` and ``--vm``.
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import re
import shlex
import subprocess  # nosec B404 - drives the checker, the probe and macvm_ctl.bash with stub tools
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "host_state_check.py"
PROBE_PATH = REPO_ROOT / "util" / "host_state_probe.bash"
MACVM_CTL = REPO_ROOT / "util" / "macvm_ctl.bash"
EXPECTED_PATH = REPO_ROOT / "conf" / "hosts" / "turing" / "expected.yaml"
HOSTTOOLS = REPO_ROOT / "conf" / "hosts" / "turing" / "hosttools-environment.yml"
CONDA_SPECS = REPO_ROOT / "conf" / "hosts" / "turing" / "conda-envs"
PLAN = REPO_ROOT / "notes" / "JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
BASH = os.environ.get("HOST_STATE_TEST_BASH", "/bin/bash")  # set it to run the suite under another bash
TIMEOUT_SECONDS = 120

HOME = "/Users/owner"
ROOT = f"{HOME}/Development/python/Juniper"
GIB = 1073741824
PARENT_SHA = "5f" * 32
GATES = ["G-ALIAS", "G-SIGN", "G-SEC", "G-TOOLS", "G-ENV", "G-NET", "G-MEM"]
SECTIONS = ["hardware", "memory", "docker", "hypervisor", "disk", "power", "network", "security", "toolchain", "env", "git", "signing"]


def load_module():
    spec = importlib.util.spec_from_file_location("host_state_check", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve the string annotations through sys.modules
    spec.loader.exec_module(module)
    return module


hsc = load_module()


# ---------------------------------------------------------------------------------------------
# Fixtures: turing on 2026-10-20, as util/host_state_probe.bash captured it (trimmed)
# ---------------------------------------------------------------------------------------------
def sysctl_hw(memsize: int = 16 * GIB, cores: int = 6) -> str:
    return f"machdep.cpu.brand_string: Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz\nhw.ncpu: 12\nhw.physicalcpu: {cores}\nhw.memsize: {memsize}\nkern.hv_support: 1"


def vm_stat(free: int, inactive: int, speculative: int = 0, page_size: int = 4096) -> str:
    """The real vm_stat layout: printf("%-30s %16llu.") rows under the page-size header."""
    rows = [("Pages free", free), ("Pages active", 1128871), ("Pages inactive", inactive), ("Pages speculative", speculative), ("Pages throttled", 0), ("Pages wired down", 931471)]
    return "\n".join([f"Mach Virtual Memory Statistics: (page size of {page_size} bytes)"] + [f"{label + ':':<30} {value:>16}." for label, value in rows])


VM_STAT_TODAY = vm_stat(free=5194, inactive=1095529, speculative=32127)
SWAP_TODAY = "vm.swapusage: total = 12288.00M  used = 9440.00M  free = 2848.00M  (encrypted)"
SWAP_NONE = "vm.swapusage: total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)"
NOT_REGISTERED = "VBoxManage: error: Could not find a registered machine named 'juniper-macvm'\nVBoxManage: error: Details: code VBOX_E_OBJECT_NOT_FOUND (0x80bb0001)"


def ifconfig(en7_media: str = "autoselect (none)", en7_status: str = "inactive", en7_inet: str | None = None, en7_mac: str = "00:e0:4c:68:06:b1") -> str:
    inet = f"\n\tinet {en7_inet} netmask 0xffffff00 broadcast 192.168.50.255" if en7_inet else ""
    return (
        "lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384\n\tinet 127.0.0.1 netmask 0xff000000\n"
        "en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500\n\tether 3e:ac:bd:89:1d:30\n\tinet 192.168.50.180 netmask 0xffffff00 broadcast 192.168.50.255\n\tmedia: autoselect\n\tstatus: active\n"
        f"en7: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500\n\tether {en7_mac}{inet}\n\tmedia: {en7_media}\n\tstatus: {en7_status}\n"
        "bridge0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500\n\tether 82:23:5a:c8:2c:01\n\tmedia: <unknown type>\n\tstatus: inactive"
    )


CSRUTIL_CUSTOM = "System Integrity Protection status: unknown (Custom Configuration).\n\nConfiguration:\n\tKext Signing: disabled\n\tBaseSystem Verification: enabled\n\nThis is an unsupported configuration."
CSRUTIL_ENABLED = "System Integrity Protection status: enabled."
CONDA_LIST = (
    "\n# conda environments:\n#\n# *  -> active\n# + -> frozen\n"
    f"                         {HOME}/opt/anaconda3/envs/dynet\n"
    "base                     /usr/local/miniforge3\n"
    "JuniperCanopy1           /usr/local/miniforge3/envs/JuniperCanopy1\n"
    "JuniperCascor1           /usr/local/miniforge3/envs/JuniperCascor1\n"
    "JuniperData              /usr/local/miniforge3/envs/JuniperData\n"
    "JuniperHostTools         /usr/local/miniforge3/envs/JuniperHostTools\n"
    "JuniperPython        *   /usr/local/miniforge3/envs/JuniperPython"
)


def kubectl_json(minor: str, major: str = "1") -> str:
    return json.dumps({"clientVersion": {"major": major, "minor": minor, "gitVersion": f"v{major}.{re.sub(r'[^0-9]', '', minor)}.4"}}, indent=2)


def alias_json(failing: tuple[str, ...] = ("k8s", "recurrence"), exit_code: int | None = None) -> str:
    repos = []
    for repo in ("canopy", "cascor", "k8s", "ml", "recurrence"):
        bad = repo in failing
        origin = {"status": "fail" if bad else "pass", "ok": not bad, "message": f"origin 'git@github.com:pcalnon/juniper-{repo}.git' bypasses the alias" if bad else "ok", "remediation": f"git -C {ROOT}/juniper-{repo} remote set-url origin git@github_juniper-{repo}:pcalnon/juniper-{repo}.git" if bad else None}
        key = {"status": "pass", "ok": True, "message": "mode 600", "remediation": None}
        repos.append({"repo": f"juniper-{repo}", "ok": not bad, "checks": {"origin": origin, "alias": {"status": "pass", "ok": True, "message": "ok", "remediation": None}, "key": key}})
    code = (1 if failing else 0) if exit_code is None else exit_code
    summary = f"summary: {30 - len(failing)} of 30 checks passed; {len(failing)} failed: " + ", ".join(f"juniper-{r} origin" for r in failing) if failing else "summary: all 30 checks passed"
    return json.dumps({"schema": 1, "mode": "check", "root": ROOT, "skipped": False, "ok": code == 0, "exit_code": code, "summary": summary, "failures": [{"repo": f"juniper-{r}", "check": "origin", "status": "fail"} for r in failing], "repos": repos}, indent=2)


def signing_json(failing: tuple[str, ...] = ()) -> str:
    checks = [{"id": "include", "status": "pass", "message": "the include is wired", "remediation": None}]
    checks += [{"id": f"repo:juniper-{r}", "status": "fail" if r in failing else "pass", "message": "commit.gpgsign is false" if r in failing else "signs", "remediation": "python3 util/configure_commit_signing.py --apply" if r in failing else None} for r in ("ml", "cascor")]
    checks.append({"id": "session", "status": "info", "message": "D11", "remediation": None})
    code = 1 if failing else 0
    return json.dumps({"schema": 1, "mode": "check", "checks": checks, "ok": code == 0, "exit_code": code, "summary": f"FAILED -- {len(failing)} of 4 checks failed" if failing else "OK -- all 4 checks passed"})


PREFLIGHT_D11 = (
    "headless signing preflight: non-credential checks only\n\n"
    "PASS  signing-key     user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A! (pinned)\n"
    "FAIL  commit-gpgsign  signing disabled by construction (D11): GIT_CONFIG_KEY_0=commit.gpgsign, GIT_CONFIG_VALUE_0=false\n"
    "INFO  tag-gpgsign     tag.gpgsign=false (disabled by construction, D11)\n"
    "PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor 'mac'\n"
    f"PASS  agent-socket    {HOME}/.gnupg/S.gpg-agent is a socket\n"
    f"PASS  external-cache  no-allow-external-cache is set in {HOME}/.gnupg/gpg-agent.conf\n"
    "INFO  head-signature  HEAD ad6013f4 %G?=E"
)


def cap(section: str, name: str, stdout: str = "", *, exit_code: int = 0, stderr: str = "", skipped: str | None = None, timed_out: bool = False, command: str | None = None) -> dict:
    return {"section": section, "name": name, "command": command or name, "exit_code": None if skipped else exit_code, "timed_out": timed_out, "skipped": skipped, "stdout": stdout, "stderr": stderr}


def expected_doc() -> dict:
    return yaml.safe_load(EXPECTED_PATH.read_text(encoding="utf-8"))


def today_captures(expected: dict) -> list[dict]:
    caps = [
        cap("hardware", "sysctl", sysctl_hw()),
        cap("hardware", "sw_vers", "ProductName:\t\tmacOS\nProductVersion:\t\t15.7.1"),
        cap("memory", "vm_stat", VM_STAT_TODAY),
        cap("memory", "swapusage", SWAP_TODAY),
        cap("docker", "pgrep:com.docker.backend", "682"),
        cap("docker", "pgrep:Docker Desktop", exit_code=1),
        cap("docker", "pgrep:Docker", "674"),
        cap("hypervisor", "vboxmanage-version", "7.2.0r170228"),
        cap("hypervisor", "vboxmanage-showvminfo", exit_code=1, stderr=NOT_REGISTERED),
        cap("network", "ifconfig", ifconfig()),
        cap("security", "csrutil-status", CSRUTIL_CUSTOM),
        cap("security", "csrutil-authenticated-root", "Authenticated Root status: enabled"),
        cap("security", "fdesetup-status", "FileVault is On."),
        cap("security", "firewall-globalstate", "Firewall is disabled. (State = 0)"),
        cap("security", "firewall-stealthmode", "Firewall stealth mode is off"),
        cap("security", "key-material-names", f"{HOME}/.ssh/priv.asc\n{HOME}/.ssh/github-recovery-codes.txt"),
        cap("security", "ssh-loose-files", ""),
    ]
    for tool in expected["tools"]["local_bin"]:
        caps.append(cap("toolchain", f"command-v:{tool}", f"{HOME}/.local/bin/{tool}"))
    caps.append(cap("toolchain", "command-v:pinentry-mac", "/usr/local/bin/pinentry-mac"))
    caps.append(cap("toolchain", "command-v:kubectl", "/usr/local/bin/kubectl"))
    caps.append(cap("toolchain", "kubectl-version", kubectl_json("22")))
    caps += [
        cap("env", "conda-env-list", CONDA_LIST),
        cap("env", "parent-agents-md", skipped=f"absent: {ROOT}/AGENTS.md"),
        cap("git", "git-remote-alias-check", alias_json(), exit_code=1),
        cap("signing", "configure-commit-signing", signing_json()),
        cap("signing", "headless-signing-preflight", PREFLIGHT_D11, exit_code=1),
    ]
    return caps


def probe_doc(captures: list[dict], *, host: str = "turing", sections: list[str] | None = None) -> dict:
    return {
        "schema": 1,
        "tool": "util/host_state_probe.bash",
        "host": host,
        "collected_at": "2026-10-20T11:03:07Z",
        "bash_version": "3.2.57(1)-release",
        "home": HOME,
        "path": f"{HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin",
        "root": ROOT,
        "vm": "juniper-macvm",
        "timeout_seconds": 60,
        "sections": SECTIONS if sections is None else sections,
        "captures": captures,
    }


def replace(captures: list[dict], *new: dict) -> list[dict]:
    keys = {(c["section"], c["name"]) for c in new}
    return [c for c in captures if (c["section"], c["name"]) not in keys] + list(new)


def ready_captures(expected: dict) -> list[dict]:
    """turing once every owner step is done: each measurable condition passes."""
    return replace(
        today_captures(expected),
        cap("memory", "vm_stat", vm_stat(free=2_000_000, inactive=1_000_000)),
        cap("memory", "swapusage", SWAP_NONE),
        cap("docker", "pgrep:com.docker.backend", exit_code=1),
        cap("docker", "pgrep:Docker", exit_code=1),
        cap("network", "ifconfig", ifconfig("autoselect (1000baseT <full-duplex>)", "active", "192.168.50.60")),
        cap("security", "csrutil-status", CSRUTIL_ENABLED),
        cap("security", "firewall-globalstate", "Firewall is enabled. (State = 1)"),
        cap("security", "key-material-names", ""),
        cap("toolchain", "kubectl-version", kubectl_json("36")),
        cap("env", "parent-agents-md", f"{PARENT_SHA}  {ROOT}/AGENTS.md"),
        cap("git", "git-remote-alias-check", alias_json(())),
    )


def ready_expected() -> dict:
    doc = expected_doc()
    doc["parent_agents_md"]["sha256"] = PARENT_SHA
    doc["network"]["reserved_ip"] = "192.168.50.60"
    return doc


def conditions(results, gate: str) -> dict:
    """The named conditions of one gate's result (host_state_check.Condition objects)."""
    result = next(r for r in results if r.spec.gate == gate)
    return {c.name: c for c in result.conditions}


class CheckerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_json(self, doc: dict, name: str = "probe.json") -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(doc), encoding="utf-8")
        return path

    def write_expected(self, doc: dict, name: str = "expected.yaml") -> Path:
        path = self.tmp / name
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        return path

    def main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = hsc.main(list(args))
            except SystemExit as exc:  # argparse
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def evaluate(self, captures: list[dict], expected: dict | None = None, *, sections: list[str] | None = None):
        expected = expected_doc() if expected is None else expected
        return hsc.evaluate(hsc.Probe(probe_doc(captures, sections=sections)), expected, list(hsc.GATES))

    def statuses(self, results) -> dict[str, str]:
        return {r.spec.gate: r.status for r in results}


# ---------------------------------------------------------------------------------------------
# The whole picture
# ---------------------------------------------------------------------------------------------
class TuringTodayTest(CheckerTestCase):
    def test_turing_on_2026_10_20(self) -> None:
        results = self.evaluate(today_captures(expected_doc()))
        self.assertEqual(self.statuses(results), {"G-ALIAS": "fail", "G-SIGN": "operator", "G-SEC": "fail", "G-TOOLS": "fail", "G-ENV": "fail", "G-NET": "fail", "G-MEM": "fail"})
        self.assertEqual(hsc.readiness(results), {"evaluated": 7, "pass": 0, "operator": 1, "fail": 6, "unknown": 0})  # nosec B105 - "pass" is a gate status

    def test_a_ready_turing_passes_check_mode(self) -> None:
        results = self.evaluate(ready_captures(expected_doc()), ready_expected())
        self.assertEqual(self.statuses(results), {"G-ALIAS": "pass", "G-SIGN": "operator", "G-SEC": "pass", "G-TOOLS": "pass", "G-ENV": "pass", "G-NET": "operator", "G-MEM": "pass"})
        code, out, err = self.main("--check", "--probe-json", str(self.write_json(probe_doc(ready_captures(expected_doc())))), "--expected", str(self.write_expected(ready_expected())))
        self.assertEqual((code, err), (0, ""))
        self.assertIn("readiness: 5 of 7 gates pass (2 pending owner-run checks, 0 failing, 0 unknown)", out)

    def test_report_mode_exits_0_and_check_mode_1_on_failures(self) -> None:
        probe = str(self.write_json(probe_doc(today_captures(expected_doc()))))
        self.assertEqual(self.main("--probe-json", probe)[0], 0)
        code, out, _ = self.main("--check", "--probe-json", probe)
        self.assertEqual(code, 1)
        self.assertIn("check mode", out.splitlines()[0])

    def test_the_report_lists_gates_conditions_and_what_is_evaluated_elsewhere(self) -> None:
        code, out, _ = self.main("--probe-json", str(self.write_json(probe_doc(today_captures(expected_doc())))))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("host state check: turing against conf/hosts/turing/expected.yaml (report mode)\n"))
        for gate in GATES:
            self.assertRegex(out, rf"(?m)^{gate}\s+(PASS|FAIL|UNKNOWN|OPERATOR)\s")
        self.assertRegex(out, r"(?m)^  FAIL     alias-check\s+git_remote_alias_check\.py: 28 of 30 checks passed; 2 failed: juniper-k8s origin, juniper-recurrence origin$")
        self.assertRegex(out, r"(?m)^           juniper-k8s origin: .* -- fix: git -C ")
        self.assertRegex(out, r"(?m)^  OPERATOR i-sign\s")
        for gate in ("G-AUTH", "G-PATH", "G-AGENT"):
            self.assertRegex(out, rf"(?m)^  {gate}\s+\S")


# ---------------------------------------------------------------------------------------------
# Gates, one condition at a time
# ---------------------------------------------------------------------------------------------
class AliasGateTest(CheckerTestCase):
    def test_pass_fail_and_unknown(self) -> None:
        base = today_captures(expected_doc())
        ok = conditions(self.evaluate(replace(base, cap("git", "git-remote-alias-check", alias_json(())))), "G-ALIAS")["alias-check"]
        self.assertEqual((ok.status, ok.message), ("pass", "git_remote_alias_check.py: all 30 checks passed"))
        bad = conditions(self.evaluate(base), "G-ALIAS")["alias-check"]
        self.assertEqual(bad.status, "fail")
        self.assertEqual(len(bad.detail), 2)
        self.assertTrue(bad.detail[0].startswith("juniper-k8s origin: origin 'git@github.com:pcalnon/juniper-k8s.git' bypasses the alias -- fix: git -C "))
        for case in (
            cap("git", "git-remote-alias-check", alias_json(exit_code=2), exit_code=2),
            cap("git", "git-remote-alias-check", "Traceback (most recent call last):", exit_code=1, stderr="boom"),
            cap("git", "git-remote-alias-check", skipped="absent: util/git_remote_alias_check.py"),
            cap("git", "git-remote-alias-check", timed_out=True, exit_code=137),
            cap("git", "git-remote-alias-check", exit_code=127, stderr="python3: command not found"),
            cap("git", "git-remote-alias-check", json.dumps({"schema": 2, "exit_code": 0, "ok": True})),
        ):
            with self.subTest(case=case["stdout"][:30] or case["skipped"] or case["exit_code"]):
                self.assertEqual(conditions(self.evaluate(replace(base, case)), "G-ALIAS")["alias-check"].status, "unknown")


class SignGateTest(CheckerTestCase):
    def test_the_d11_failure_line_is_not_judged(self) -> None:
        conds = conditions(self.evaluate(today_captures(expected_doc())), "G-SIGN")
        self.assertEqual({name: c.status for name, c in conds.items()}, {"git-config": "pass", "pinentry": "pass", "agent-socket": "pass", "external-cache": "pass", "i-sign": "operator"})

    def test_failures_and_unknowns(self) -> None:
        base = today_captures(expected_doc())
        conds = conditions(self.evaluate(replace(base, cap("signing", "configure-commit-signing", signing_json(("cascor",)), exit_code=1))), "G-SIGN")
        self.assertEqual(conds["git-config"].status, "fail")
        self.assertEqual(conds["git-config"].detail, ["repo:juniper-cascor: commit.gpgsign is false -- fix: python3 util/configure_commit_signing.py --apply"])
        curses = PREFLIGHT_D11.replace("PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor 'mac'", "FAIL  pinentry        /usr/local/bin/pinentry reports flavor 'curses'")
        conds = conditions(self.evaluate(replace(base, cap("signing", "headless-signing-preflight", curses, exit_code=1))), "G-SIGN")
        self.assertEqual((conds["pinentry"].status, conds["pinentry"].message), ("fail", "/usr/local/bin/pinentry reports flavor 'curses'"))
        conds = conditions(self.evaluate(replace(base, cap("signing", "headless-signing-preflight", "", exit_code=2, stderr="ERROR: gpgconf not found"))), "G-SIGN")
        self.assertEqual([conds[n].status for n in ("pinentry", "agent-socket", "external-cache")], ["unknown"] * 3)
        self.assertIn("gpgconf not found", conds["pinentry"].message)
        result = next(r for r in self.evaluate(replace(base, cap("signing", "headless-signing-preflight", skipped="absent: x"))) if r.spec.gate == "G-SIGN")
        self.assertEqual(result.status, "unknown")


class SecGateTest(CheckerTestCase):
    def sec(self, *caps: dict) -> dict:
        return conditions(self.evaluate(replace(today_captures(expected_doc()), *caps)), "G-SEC")

    def test_today(self) -> None:
        conds = self.sec()
        self.assertEqual({n: c.status for n, c in conds.items()}, {"sip": "fail", "authenticated-root": "pass", "filevault": "pass", "firewall": "fail", "key-material": "fail", "key-perms": "pass", "stealth-mode": "info"})
        self.assertEqual(conds["sip"].message, "SIP is unknown (Custom Configuration); csrutil enable from recoveryOS (C1)")
        self.assertEqual(conds["key-material"].detail, ["~/.ssh/priv.asc", "~/.ssh/github-recovery-codes.txt"])

    def test_each_condition_both_ways(self) -> None:
        self.assertEqual(self.sec(cap("security", "csrutil-status", CSRUTIL_ENABLED))["sip"].status, "pass")
        self.assertEqual(self.sec(cap("security", "csrutil-status", "System Integrity Protection status: disabled."))["sip"].message, "SIP is disabled; csrutil enable from recoveryOS (C1)")
        self.assertEqual(self.sec(cap("security", "csrutil-authenticated-root", "Authenticated Root status: disabled"))["authenticated-root"].status, "fail")
        self.assertEqual(self.sec(cap("security", "fdesetup-status", "FileVault is Off."))["filevault"].status, "fail")
        for state, status in (("Firewall is enabled. (State = 1)", "pass"), ("Firewall is set to block all non-essential incoming connections. (State = 2)", "pass"), ("Firewall is disabled. (State = 0)", "fail")):
            with self.subTest(state=state):
                self.assertEqual(self.sec(cap("security", "firewall-globalstate", state))["firewall"].status, status)
        self.assertEqual(self.sec(cap("security", "key-material-names", ""))["key-material"].status, "pass")
        loose = self.sec(cap("security", "ssh-loose-files", f"{HOME}/.ssh/id-turing-aws-ec2.pem"))["key-perms"]
        self.assertEqual((loose.status, loose.detail), ("fail", ["~/.ssh/id-turing-aws-ec2.pem"]))
        self.assertIn("chmod 600", loose.message)

    def test_absent_directories_pass_and_broken_inputs_are_unknown(self) -> None:
        conds = self.sec(cap("security", "key-material-names", skipped=f"absent: {HOME}/.ssh and {HOME}/.gnupg"), cap("security", "ssh-loose-files", skipped=f"absent: {HOME}/.ssh"))
        self.assertEqual((conds["key-material"].status, conds["key-perms"].status), ("pass", "pass"))
        conds = self.sec(
            cap("security", "csrutil-status", exit_code=127, stderr="csrutil: command not found"),
            cap("security", "fdesetup-status", "Some new wording"),
            cap("security", "firewall-globalstate", timed_out=True, exit_code=137),
            cap("security", "key-material-names", "", exit_code=1, stderr="find: permission denied"),
        )
        self.assertEqual([conds[n].status for n in ("sip", "filevault", "firewall", "key-material")], ["unknown"] * 4)
        conds = self.sec(cap("security", "key-material-names", f"{HOME}/.gnupg/x.asc", exit_code=1, stderr="find: permission denied"))
        self.assertEqual(conds["key-material"].status, "fail", "a partial listing that already found a name fails")


class ToolsGateTest(CheckerTestCase):
    def tools(self, *caps: dict) -> dict:
        return conditions(self.evaluate(replace(today_captures(expected_doc()), *caps)), "G-TOOLS")

    def test_today(self) -> None:
        conds = self.tools()
        self.assertEqual({n: c.status for n, c in conds.items()}, {"local-bin": "pass", "homebrew": "pass", "kubectl": "fail"})
        self.assertEqual(conds["kubectl"].message, "kubectl v1.22.4 at /usr/local/bin/kubectl is 14 minors behind the cluster's 1.36; D4 installs 1.36.x")

    def test_a_tool_elsewhere_or_missing_fails_local_bin(self) -> None:
        conds = self.tools(cap("toolchain", "command-v:yq", "/opt/local/bin/yq"), cap("toolchain", "command-v:sops", exit_code=1))
        self.assertEqual(conds["local-bin"].status, "fail")
        self.assertEqual(conds["local-bin"].detail, ["yq: resolves to /opt/local/bin/yq, not ~/.local/bin/yq", "sops: not found on PATH"])
        unlooked = [c for c in today_captures(expected_doc()) if c["name"] != "command-v:ykman"]
        self.assertEqual(conditions(self.evaluate(unlooked), "G-TOOLS")["local-bin"].status, "unknown")

    def test_pinentry_mac_must_be_the_homebrew_bottle(self) -> None:
        conds = self.tools(cap("toolchain", "command-v:pinentry-mac", "/opt/local/bin/pinentry-mac"))
        self.assertEqual((conds["homebrew"].status, conds["homebrew"].detail), ("fail", ["pinentry-mac: resolves to /opt/local/bin/pinentry-mac, not /usr/local/bin/pinentry-mac"]))

    def test_kubectl_skew(self) -> None:
        for minor, status in (("35", "pass"), ("36", "pass"), ("37", "pass"), ("34", "fail"), ("38", "fail"), ("36+", "pass"), ("22", "fail")):
            with self.subTest(minor=minor):
                self.assertEqual(self.tools(cap("toolchain", "kubectl-version", kubectl_json(minor)))["kubectl"].status, status)
        self.assertIn("ahead of", self.tools(cap("toolchain", "kubectl-version", kubectl_json("38")))["kubectl"].message)
        self.assertEqual(self.tools(cap("toolchain", "kubectl-version", kubectl_json("36", major="2")))["kubectl"].status, "fail")

    def test_kubectl_missing_fails_and_garbage_is_unknown(self) -> None:
        conds = self.tools(cap("toolchain", "kubectl-version", exit_code=127, stderr="kubectl: command not found"))
        self.assertEqual(conds["kubectl"].status, "fail")
        self.assertIn("kubectl not found", conds["kubectl"].message)
        self.assertEqual(self.tools(cap("toolchain", "kubectl-version", "error: unknown flag: --client", exit_code=1))["kubectl"].status, "unknown")


class EnvGateTest(CheckerTestCase):
    def env(self, *caps: dict, sha: str | None = None) -> dict:
        expected = expected_doc()
        expected["parent_agents_md"]["sha256"] = sha
        return conditions(self.evaluate(replace(today_captures(expected), *caps), expected), "G-ENV")

    def test_conda_envs(self) -> None:
        self.assertEqual(self.env()["conda-envs"].message, "all 5 present: JuniperCanopy1, JuniperCascor1, JuniperData, JuniperPython, JuniperHostTools")
        missing = CONDA_LIST.replace("JuniperCanopy1           /usr/local/miniforge3/envs/JuniperCanopy1\n", "")
        cond = self.env(cap("env", "conda-env-list", missing))["conda-envs"]
        self.assertEqual((cond.status, cond.message), ("fail", "missing: JuniperCanopy1 (E2 creates them from conf/hosts/turing/conda-envs/)"))
        unnamed = missing + "\n                         /opt/other-install/envs/JuniperCanopy1"
        self.assertEqual(self.env(cap("env", "conda-env-list", unnamed))["conda-envs"].status, "pass", "an env named only by its path counts")
        self.assertEqual(self.env(cap("env", "conda-env-list", exit_code=127))["conda-envs"].status, "unknown")

    def test_parent_agents_md(self) -> None:
        absent = self.env()["parent-agents-md"]
        self.assertEqual((absent.status, absent.message), ("fail", f"absent: {ROOT}/AGENTS.md; E4 copies yamaguchi's file and records its sha256 in expected.yaml"))
        present = cap("env", "parent-agents-md", f"{PARENT_SHA}  {ROOT}/AGENTS.md")
        unrecorded = self.env(present)["parent-agents-md"]
        self.assertEqual((unrecorded.status, unrecorded.message), ("fail", f"present, sha256 {PARENT_SHA}, but expected.yaml records no hash yet (E4)"))
        self.assertEqual(self.env(present, sha=PARENT_SHA)["parent-agents-md"].status, "pass")
        drift = self.env(present, sha="0" * 64)["parent-agents-md"]
        self.assertEqual(drift.status, "fail")
        self.assertIn("(D9)", drift.message)
        self.assertEqual(self.env(cap("env", "parent-agents-md", "shasum: error", exit_code=1))["parent-agents-md"].status, "unknown")


class NetGateTest(CheckerTestCase):
    def net(self, text: str, ip: str | None = None) -> dict:
        expected = expected_doc()
        expected["network"]["reserved_ip"] = ip
        return conditions(self.evaluate(replace(today_captures(expected), cap("network", "ifconfig", text)), expected), "G-NET")

    def test_today(self) -> None:
        conds = self.net(ifconfig())
        self.assertEqual({n: c.status for n, c in conds.items()}, {"link": "fail", "address": "fail", "throughput": "operator"})
        self.assertEqual(conds["link"].message, "en7 (00:e0:4c:68:06:b1): media autoselect (none), status inactive; F2 needs 1000baseT and active")
        self.assertIn("A6 reserves one", conds["address"].message)

    def test_link_and_address(self) -> None:
        good = ifconfig("autoselect (1000baseT <full-duplex>)", "active", "192.168.50.60")
        conds = self.net(good, "192.168.50.60")
        self.assertEqual((conds["link"].status, conds["address"].status), ("pass", "pass"))
        self.assertEqual(self.net(ifconfig("autoselect (100baseTX <full-duplex>)", "active"))["link"].status, "fail")
        self.assertEqual(self.net(good, "192.168.50.61")["address"].message, "en7 has 192.168.50.60, not the reserved 192.168.50.61 (A6)")
        moved = self.net(ifconfig(en7_mac="aa:bb:cc:dd:ee:ff"))["link"]
        self.assertIn("not the dongle 00:e0:4c:68:06:b1", moved.message)
        gone = self.net(ifconfig().replace("en7:", "en9:"))
        self.assertEqual((gone["link"].status, gone["address"].status), ("fail", "fail"))
        self.assertIn("not present", gone["link"].message)

    def test_interfaces_parser(self) -> None:
        found = hsc.interfaces(ifconfig("autoselect (1000baseT <full-duplex>)", "active", "192.168.50.60"))
        self.assertEqual(found["en7"], {"ether": "00:e0:4c:68:06:b1", "inet": "192.168.50.60", "media": "autoselect (1000baseT <full-duplex>)", "status": "active"})
        self.assertEqual(found["en0"]["inet"], "192.168.50.180")
        self.assertNotIn("inet", found["bridge0"])


class MemGateTest(CheckerTestCase):
    def mem(self, *caps: dict, expected: dict | None = None) -> dict:
        expected = expected_doc() if expected is None else expected
        return conditions(self.evaluate(replace(today_captures(expected), *caps), expected), "G-MEM")

    def test_today(self) -> None:
        conds = self.mem()
        self.assertEqual({n: c.status for n, c in conds.items()}, {"vm-fits": "pass", "memory": "fail", "swap": "fail", "docker": "fail", "vm-state": "info"})
        # (5194 free + 32127 speculative + 1095529 inactive pages) x 4096 B = 4425.1 MiB, rounded down
        self.assertEqual(conds["memory"].message, "free + inactive 4425 MiB < 10240 MiB required (VM 6144 MiB + reserve 4096 MiB)")
        self.assertEqual(conds["swap"].message, "used 9440 MiB > 2048 MiB allowed")
        self.assertEqual(conds["docker"].message, "Docker Desktop is running: com.docker.backend (pid 682), Docker (pid 674); quit it before node mode (D7)")
        self.assertEqual(conds["vm-fits"].message, "VM 6144 MiB + reserve 4096 MiB <= hw.memsize 16384 MiB; 4 vCPU <= 6 cores")

    def test_r_g1_the_x2_class_fails_vm_fits(self) -> None:
        cases = ((44, 4, "fail"), (12, 4, "pass"), (13, 4, "fail"), (6, 8, "fail"), (6, 6, "pass"))
        for memory_gib, vcpus, status in cases:
            with self.subTest(memory_gib=memory_gib, vcpus=vcpus):
                expected = expected_doc()
                expected["vm"].update(memory_gib=memory_gib, vcpus=vcpus)
                cond = self.mem(expected=expected)["vm-fits"]
                self.assertEqual(cond.status, status, cond.message)
        expected = expected_doc()
        expected["vm"]["memory_gib"] = 44
        message = self.mem(expected=expected)["vm-fits"].message
        self.assertEqual(message, "VM 45056 MiB + reserve 4096 MiB > hw.memsize 16384 MiB: a VM this size can never start (the X2 class; D1 sizes it at 6 GiB)")

    def test_a_configured_vm_larger_than_expected_wins(self) -> None:
        conds = self.mem(cap("hypervisor", "vboxmanage-showvminfo", 'name="juniper-macvm"\nmemory=13312\nVMState="poweroff"'))
        self.assertEqual(conds["vm-fits"].status, "fail")
        self.assertIn("VM 13312 MiB", conds["memory"].message)
        self.assertIn("13312 MiB, more than vm.memory_gib 6", conds["vm"].message)
        running = self.mem(cap("hypervisor", "vboxmanage-showvminfo", 'memory=6144\nVMState="running"'))["vm-state"]
        self.assertIn("its own memory is not counted", running.message)

    def test_swap_rounds_up_and_memory_rounds_down(self) -> None:
        for token, used in (("2048.00M", 2048), ("2048.01M", 2049), ("2.00G", 2048), ("2097152.00K", 2048), ("2097153.00K", 2049), ("0.00M", 0)):
            with self.subTest(token=token):
                self.assertEqual(hsc._swap_used_mib(f"vm.swapusage: total = 4096.00M  used = {token}  free = 0.00M"), (used, token))
        self.assertIsNone(hsc._swap_used_mib("vm.swapusage: total = 4096.00M  used = lots"))
        self.assertEqual(self.mem(cap("memory", "swapusage", "vm.swapusage: total = 4096.00M  used = 2048.01M  free = 0M"))["swap"].status, "fail")
        exact = vm_stat(free=262144 * 10, inactive=0)  # 10 GiB in 4 KiB pages: exactly the 10240 MiB required
        self.assertEqual(self.mem(cap("memory", "vm_stat", exact))["memory"].status, "pass")
        self.assertEqual(self.mem(cap("memory", "vm_stat", vm_stat(free=262144 * 10 - 1, inactive=0)))["memory"].status, "fail")

    def test_unmeasurable_inputs_are_unknown(self) -> None:
        conds = self.mem(cap("memory", "vm_stat", exit_code=127, stderr="vm_stat: command not found"), cap("memory", "swapusage", "garbage"), cap("docker", "pgrep:Docker", exit_code=3))
        self.assertEqual([conds[n].status for n in ("memory", "swap", "docker")], ["unknown"] * 3)
        self.assertEqual(self.mem(cap("hardware", "sysctl", "hw.ncpu: 12"))["vm-fits"].status, "unknown")
        self.assertEqual(self.mem(cap("memory", "vm_stat", vm_stat(1, 1).replace("Pages inactive", "Pages idle")))["memory"].status, "unknown")


# ---------------------------------------------------------------------------------------------
# G-MEM against util/macvm_ctl.bash, its implementation of record
# ---------------------------------------------------------------------------------------------
class MacvmCtlAgreementTest(CheckerTestCase):
    def stub(self, name: str, body: str) -> str:
        path = self.tmp / name
        path.write_text("#!/bin/bash\n" + body, encoding="utf-8")
        path.chmod(0o700)
        return str(path)

    def macvm_status(self, vm_stat_text: str, swap: str, running: tuple[str, ...], showvminfo: tuple[str, str, int]) -> dict[str, tuple[str, str]]:
        fixtures = self.tmp / "fx"
        fixtures.mkdir(exist_ok=True)
        (fixtures / "vm_stat").write_text(vm_stat_text + "\n", encoding="utf-8")
        (fixtures / "swap").write_text(swap + "\n", encoding="utf-8")
        (fixtures / "showvminfo.out").write_text(showvminfo[0], encoding="utf-8")
        (fixtures / "showvminfo.err").write_text(showvminfo[1], encoding="utf-8")
        pgrep_cases = "".join(f"  {shlex.quote(name)}) echo 4242; exit 0 ;;\n" for name in running)
        env = RedactedEnv(
            {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ},
            VM_STAT=self.stub("vm_stat", f"cat {shlex.quote(str(fixtures / 'vm_stat'))}\n"),
            SYSCTL=self.stub("sysctl", f'[ "$1" = vm.swapusage ] || exit 9\ncat {shlex.quote(str(fixtures / "swap"))}\n'),
            PGREP=self.stub("pgrep", f'[ "$1" = -x ] || exit 9\ncase "$2" in\n{pgrep_cases}  *) exit 1 ;;\nesac\n'),
            VBOXMANAGE=self.stub("VBoxManage", f"cat {shlex.quote(str(fixtures / 'showvminfo.out'))}\ncat {shlex.quote(str(fixtures / 'showvminfo.err'))} >&2\nexit {showvminfo[2]}\n"),
        )
        proc = subprocess.run([BASH, str(MACVM_CTL), "status"], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        found = {m.group(2): (m.group(1).lower(), m.group(3)) for m in re.finditer(r"(?m)^\s+(PASS|FAIL|UNKNOWN)\s+(memory|swap|docker): (.*)$", proc.stdout)}
        self.assertEqual(set(found), {"memory", "swap", "docker"}, proc.stdout + proc.stderr)
        return found

    def test_both_tools_print_the_same_verdicts_and_text(self) -> None:
        unregistered = ("", NOT_REGISTERED, 1)
        cases = [
            (VM_STAT_TODAY, SWAP_TODAY, ("com.docker.backend", "Docker"), unregistered),
            (vm_stat(free=2_000_000, inactive=1_000_000, speculative=31337), SWAP_NONE, (), unregistered),
            (vm_stat(free=262144 * 10, inactive=0), "vm.swapusage: total = 4096.00M  used = 2048.01M  free = 0.00M  (encrypted)", ("Docker Desktop",), unregistered),
            (vm_stat(free=900_000, inactive=900_000, page_size=16384), "vm.swapusage: total = 1024.00M  used = 1.50G  free = 0.00M  (encrypted)", (), ('name="juniper-macvm"\nmemory=8192\nVMState="poweroff"\n', "", 0)),
        ]
        for n, (vm_stat_text, swap, running, showvminfo) in enumerate(cases):
            with self.subTest(case=n):
                ours = replace(
                    today_captures(expected_doc()),
                    cap("memory", "vm_stat", vm_stat_text),
                    cap("memory", "swapusage", swap),
                    *(cap("docker", f"pgrep:{name}", "4242" if name in running else "", exit_code=0 if name in running else 1) for name in ("com.docker.backend", "Docker Desktop", "Docker")),
                    cap("hypervisor", "vboxmanage-showvminfo", showvminfo[0].rstrip("\n"), stderr=showvminfo[1], exit_code=showvminfo[2]),
                )
                conds = conditions(self.evaluate(ours), "G-MEM")
                theirs = self.macvm_status(vm_stat_text, swap, running, showvminfo)
                for name in ("memory", "swap", "docker"):
                    self.assertEqual((conds[name].status, conds[name].message), theirs[name], name)


# ---------------------------------------------------------------------------------------------
# Command line, exit codes, JSON
# ---------------------------------------------------------------------------------------------
class CommandLineTest(CheckerTestCase):
    def test_sections_select_gates_by_any_spelling(self) -> None:
        probe = str(self.write_json(probe_doc(today_captures(expected_doc()))))
        code, out, _ = self.main("--json", "--probe-json", probe, "--section", "G-MEM", "--section", "tools", "--section", "g-mem")
        doc = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual([g["gate"] for g in doc["gates"]], ["G-TOOLS", "G-MEM"])
        code, _, err = self.main("--probe-json", probe, "--section", "G-AUTH")
        self.assertEqual(code, 2)
        self.assertIn("unknown gate 'G-AUTH'", err)

    def test_a_partial_probe_makes_its_gates_unknown_and_check_exits_2(self) -> None:
        caps = [c for c in today_captures(expected_doc()) if c["section"] != "memory"]
        probe = str(self.write_json(probe_doc(caps, sections=[s for s in SECTIONS if s != "memory"])))
        code, out, _ = self.main("--check", "--json", "--probe-json", probe)
        doc = json.loads(out)
        self.assertEqual(code, 2, "unknown wins over fail")
        mem = next(g for g in doc["gates"] if g["gate"] == "G-MEM")
        self.assertEqual((mem["status"], mem["conditions"][0]["message"]), ("unknown", "the probe did not collect section(s) memory"))

    def test_a_known_failure_outranks_an_unknown_in_its_gate(self) -> None:
        caps = replace(today_captures(expected_doc()), cap("memory", "swapusage", "garbage"))
        mem = next(r for r in self.evaluate(caps) if r.spec.gate == "G-MEM")
        self.assertEqual(({c.name: c.status for c in mem.conditions}["swap"], mem.status), ("unknown", "fail"))
        code, _, _ = self.main("--check", "--section", "mem", "--probe-json", str(self.write_json(probe_doc(caps))))
        self.assertEqual(code, 1, "the gate fails on what was measured; no gate is unknown")

    def test_the_json_document(self) -> None:
        code, out, err = self.main("--check", "--json", "--probe-json", str(self.write_json(probe_doc(today_captures(expected_doc())))))
        doc = json.loads(out)
        self.assertEqual((code, err), (1, ""))
        self.assertEqual(set(doc), {"schema", "tool", "mode", "host", "expected", "probe", "gates", "readiness", "not_evaluated", "ok", "exit_code", "summary"})
        self.assertEqual((doc["schema"], doc["tool"], doc["mode"], doc["host"], doc["expected"]), (1, "util/host_state_check.py", "check", "turing", "conf/hosts/turing/expected.yaml"))
        self.assertEqual((doc["ok"], doc["exit_code"]), (False, 1))
        self.assertEqual(doc["probe"]["source"], "file")
        self.assertEqual([g["gate"] for g in doc["gates"]], GATES)
        self.assertEqual(set(doc["not_evaluated"]), {"G-AUTH", "G-PATH", "G-AGENT"})
        self.assertEqual(doc["readiness"], {"evaluated": 7, "pass": 0, "operator": 1, "fail": 6, "unknown": 0})  # nosec B105 - "pass" is a gate status
        self.assertEqual(doc["summary"], "readiness: 0 of 7 gates pass (1 pending owner-run checks, 6 failing, 0 unknown)")
        for gate in doc["gates"]:
            self.assertEqual(set(gate), {"gate", "status", "target", "sections", "conditions"})
            for cond in gate["conditions"]:
                self.assertEqual(set(cond), {"name", "status", "message", "detail"})
                self.assertIn(cond["status"], ("pass", "fail", "unknown", "operator", "info"))

    def test_environment_errors_exit_2(self) -> None:
        probe = self.write_json(probe_doc(today_captures(expected_doc())))
        bad_expected = expected_doc()
        bad_expected["typo_key"] = 1
        cases = {
            ("--probe-json", str(self.tmp / "missing.json")): "cannot read the probe JSON",
            ("--probe-json", str(self.write_json({"schema": 9}, "s9.json"))): "is not a host_state_probe.bash --json document",
            ("--probe-json", str(self.write_json(probe_doc([{"section": "x"}]), "bad.json"))): "malformed capture",
            ("--probe-json", str(self.write_json(probe_doc([], host="yamaguchi"), "y.json")), "--expected", str(EXPECTED_PATH)): "describes host 'turing', not 'yamaguchi'",
            ("--probe-json", str(self.write_json(probe_doc([], host="yamaguchi.local"), "y2.json")), "--host", "turing"): "the probe ran on 'yamaguchi', but",
            ("--probe-json", str(probe), "--host", "yamaguchi", "--expected", str(EXPECTED_PATH)): "describes host 'turing', not 'yamaguchi'",
            ("--probe-json", str(probe), "--expected", str(self.tmp / "nope.yaml")): "not found",
            ("--probe-json", str(probe), "--expected", str(self.write_expected(bad_expected))): "unknown keys ['typo_key']",
            ("--probe-json", str(self.write_json(probe_doc([], host=""), "nohost.json"))): "the probe names no host; pass --host",
        }
        for args, message in cases.items():
            with self.subTest(args=args[:2]):
                code, out, err = self.main(*args)
                self.assertEqual((code, out), (2, ""))
                self.assertIn(message, err)

    def test_expected_yaml_validation(self) -> None:
        mutations = {
            "vm.memory_gib": lambda d: d["vm"].update(memory_gib="six"),
            "vm.vcpus": lambda d: d["vm"].update(vcpus=0),
            "vm.max_swap_gib": lambda d: d["vm"].update(max_swap_gib=True),
            "tools.local_bin": lambda d: d["tools"].update(local_bin=["ok", "bad name"]),
            "tools.homebrew": lambda d: d["tools"]["homebrew"].update({"pinentry-mac": "relative/path"}),
            "cluster_minor": lambda d: d["tools"]["kubectl"].update(cluster_minor="1.36.2"),
            "sha256": lambda d: d["parent_agents_md"].update(sha256="ABC"),
            "reserved_ip": lambda d: d["network"].update(reserved_ip="turing.local"),
            "bridge_nic": lambda d: d["network"]["bridge_nic"].pop("mac"),
            "schema": lambda d: d.update(schema=2),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                doc = copy.deepcopy(expected_doc())
                mutate(doc)
                with self.assertRaises(hsc.EnvError):
                    hsc.load_expected(self.write_expected(doc))

    def test_probe_options_need_a_probe_run(self) -> None:
        code, _, err = self.main("--probe-json", "x.json", "--root", "/tmp")
        self.assertEqual(code, 2)
        self.assertIn("--probe and --root apply only when the script runs the probe", err)
        self.assertEqual(self.main("--timeout", "0")[0], 2)


class ProbeRunTest(CheckerTestCase):
    """The checker runs the probe: a recording fake for the argv, then the real probe with stub tools."""

    def fake_probe(self, payload: str, rc: int = 0) -> tuple[Path, Path]:
        log = self.tmp / "probe-argv.log"
        doc = self.tmp / "payload.json"
        doc.write_text(payload, encoding="utf-8")
        path = self.tmp / "fake_probe.bash"
        path.write_text(f'#!/bin/bash\nprintf "%s\\n" "$@" > {shlex.quote(str(log))}\ncat {shlex.quote(str(doc))}\nexit {rc}\n', encoding="utf-8")
        return path, log

    def run_checker(self, *args: str, **env_vars: str) -> subprocess.CompletedProcess:
        env = RedactedEnv({key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "HOME", "TMPDIR") if key in os.environ}, PROBE_BASH=BASH, **env_vars)
        return subprocess.run([sys.executable, str(SCRIPT_PATH), *args], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def test_the_probe_gets_sections_tools_vm_root_and_timeout(self) -> None:
        probe, log = self.fake_probe(json.dumps(probe_doc(today_captures(expected_doc()))))
        proc = self.run_checker("--probe", str(probe), "--host", "turing", "--section", "mem", "--section", "tools", "--root", "/srv/juniper", "--timeout", "30")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        argv = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(argv[:6], ["--json", "--timeout", "30", "--vm", "juniper-macvm", "--section"])
        sections = [argv[i + 1] for i, word in enumerate(argv) if word == "--section"]
        self.assertEqual(sections, ["hardware", "memory", "docker", "hypervisor", "toolchain"])
        tools = [argv[i + 1] for i, word in enumerate(argv) if word == "--tool"]
        self.assertEqual(tools, expected_doc()["tools"]["local_bin"] + ["pinentry-mac"])
        self.assertEqual(argv[-2:], ["--root", "/srv/juniper"])
        self.assertIn(f"probe: {probe} (run)", proc.stdout)

    def test_a_failing_or_garbled_probe_exits_2(self) -> None:
        for payload, rc, message in (("", 2, "exited 2"), ("not json", 0, "printed no JSON"), ('{"schema": 1}', 0, "is not a host_state_probe.bash --json document")):
            with self.subTest(message=message):
                probe, _ = self.fake_probe(payload, rc)
                proc = self.run_checker("--probe", str(probe), "--host", "turing")
                self.assertEqual((proc.returncode, proc.stdout), (2, ""))
                self.assertIn(message, proc.stderr)

    def test_end_to_end_with_the_real_probe(self) -> None:
        if not os.access(BASH, os.X_OK):
            self.skipTest(f"{BASH} not found")
        fx = self.tmp / "fx"
        fx.mkdir()
        (fx / "vm_stat").write_text(vm_stat(free=2_000_000, inactive=1_000_000) + "\n", encoding="utf-8")
        tools = {
            "SYSCTL": 'case "$1" in vm.swapusage) echo "' + SWAP_NONE + '" ;; *) printf "%s\\n" "hw.physicalcpu: 6" "hw.memsize: 17179869184" ;; esac\n',
            "VM_STAT": f"cat {shlex.quote(str(fx / 'vm_stat'))}\n",
            "PGREP": "exit 1\n",
            "VBOXMANAGE": "echo \"VBoxManage: error: Could not find a registered machine named 'juniper-macvm'\" >&2\nexit 1\n",
            "SW_VERS": "echo ProductVersion: 15.7.1\n",
            "UNAME": "echo x86_64\n",
            "HOSTNAME_BIN": "echo turing\n",
        }
        env = {}
        for var, body in tools.items():
            path = self.tmp / var.lower()
            path.write_text("#!/bin/bash\n" + body, encoding="utf-8")
            path.chmod(0o700)
            env[var] = str(path)
        proc = self.run_checker("--check", "--json", "--host", "turing", "--section", "mem", **env)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(doc["probe"]["source"], "run")
        conds = {c["name"]: (c["status"], c["message"]) for c in doc["gates"][0]["conditions"]}
        self.assertEqual(conds["memory"], ("pass", "free + inactive 11718 MiB >= 10240 MiB required (VM 6144 MiB + reserve 4096 MiB)"))
        self.assertEqual(conds["swap"], ("pass", "used 0 MiB <= 2048 MiB allowed"))
        self.assertEqual(conds["docker"], ("pass", "Docker Desktop is not running"))
        self.assertEqual(conds["vm-fits"][0], "pass")


# ---------------------------------------------------------------------------------------------
# The committed expected.yaml and the script itself
# ---------------------------------------------------------------------------------------------
class CommittedExpectedTest(unittest.TestCase):
    def test_it_loads_and_names_its_own_host(self) -> None:
        doc = hsc.load_expected(EXPECTED_PATH)
        self.assertEqual(doc["host"], EXPECTED_PATH.parent.name)

    def test_g_mem_numbers_equal_macvm_ctl_defaults(self) -> None:
        text = MACVM_CTL.read_text(encoding="utf-8")
        defaults = {key: re.search(rf"(?m)^{key}=\"?([^\"\n]+)\"?$", text).group(1) for key in ("VM", "VM_MEM_GIB", "RESERVE_GIB", "MAX_SWAP_GIB")}
        vm = expected_doc()["vm"]
        self.assertEqual((vm["name"], str(vm["memory_gib"]), str(vm["reserve_gib"]), str(vm["max_swap_gib"])), (defaults["VM"], defaults["VM_MEM_GIB"], defaults["RESERVE_GIB"], defaults["MAX_SWAP_GIB"]))
        self.assertEqual(vm["vcpus"], 4, "D1 option b")

    def test_local_bin_is_what_the_hosttools_environment_installs(self) -> None:
        text = HOSTTOOLS.read_text(encoding="utf-8")
        loop = re.search(r"for t in ([^;]+); do", text)
        self.assertIsNotNone(loop, "the recreate loop moved; update this pin")
        installed = set(loop.group(1).split()) | {"markdownlint-cli2", "sops", "ykman"}
        tools = expected_doc()["tools"]
        self.assertEqual(set(tools["local_bin"]), installed)
        for tool in ("markdownlint-cli2", "sops", "ykman", "pinentry-mac"):
            self.assertIn(tool, text)
        self.assertEqual(tools["homebrew"], {"pinentry-mac": "/usr/local/bin/pinentry-mac"})

    def test_conda_envs_cover_every_turing_spec(self) -> None:
        specs = {yaml.safe_load(path.read_text(encoding="utf-8"))["name"] for path in CONDA_SPECS.glob("*.yml")}
        self.assertTrue(specs)
        self.assertLessEqual(specs | {"JuniperPython", "JuniperHostTools"}, set(expected_doc()["conda_envs"]))

    def test_the_bridge_nic_is_the_plans_dongle(self) -> None:
        nic = expected_doc()["network"]["bridge_nic"]
        self.assertIn(f"`{nic['device']}`", PLAN.read_text(encoding="utf-8"))
        self.assertIn(nic["mac"], PLAN.read_text(encoding="utf-8"))
        self.assertEqual(nic["media"], "1000baseT")


class ScriptTest(unittest.TestCase):
    def test_the_docstring_carries_the_contract(self) -> None:
        doc = hsc.__doc__ or ""
        for needle in ("R-G1", "X2", "E-D6", "E-G-SIGN", "I-G1", "Exit codes", "JSON schema", "G-AUTH", "G-PATH", "G-AGENT", "util/macvm_ctl.bash"):
            self.assertIn(needle, doc)
        for gate in GATES:
            self.assertIn(gate, doc)

    def test_no_home_path_literal(self) -> None:
        self.assertNotRegex(SCRIPT_PATH.read_text(encoding="utf-8"), r"/Users/|/home/", "use a $HOME-relative path (plan D12)")

    def test_flake8_clean_when_available(self) -> None:
        if importlib.util.find_spec("flake8") is None:
            self.skipTest("flake8 not installed (util/ is outside the pre-commit Python hooks, so this is the lint gate where it runs)")
        proc = subprocess.run([sys.executable, "-m", "flake8", "--max-line-length=512", "--extend-ignore=E203,W503", str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_help_works_without_running_anything(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT_PATH), "--help"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--section GATE", proc.stdout)


if __name__ == "__main__":
    unittest.main()
