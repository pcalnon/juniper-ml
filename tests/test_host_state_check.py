#!/usr/bin/env python3
"""Hermetic gate for util/host_state_check.py (turing bring-up plan task G1, regression R-G1).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

The check evaluates ``util/host_state_probe.bash``'s captures against ``conf/hosts/<host>/expected.yaml``
(``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` task G1: gates G-ALIAS,
G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM of §9.3). The suite pins:

- an all-green host: the report and ``--check`` both exit 0, and the JSON carries the documented keys;
- every condition's failure, and its error when its capture is missing, failed or unparseable. A
  failure exits 1 under ``--check`` and 0 in the report; an error exits 2 under ``--check``;
- expected.yaml's validation, which exits 2 before anything runs. That includes R-G1, the X2 class: a
  VM that cannot fit the machine (vm.mem_gib plus G-MEM's reserve over hw.memsize, or more vCPUs than
  cores), checked on a synthetic file and on the committed turing file;
- C2's block-all form (owner ruling 2026-10-25): G-SEC's firewall condition passes only when the firewall
  is on (state 1 or 2) and ``socketfilterfw --getblockall`` reports block all, in the sentence turing's
  getter printed once the owner applied C2 (2026-10-26). ``--setblockall``'s confirmation sentence and an
  unknown block-all state cannot be judged, unless the firewall is off, which fails anyway. The fix names
  only the missing steps, and stealth mode is reported, not gated;
- identity: a probe of another machine exits 2;
- G-MEM's verdicts equal ``util/macvm_ctl.bash status``'s on the same vm_stat, swap and pgrep output,
  rounding included, because the gate is that script's gate;
- the probe contract: the check runs the real ``util/host_state_probe.bash`` (its tools stubbed) and
  passes it the sections, tools, VM and root the selected gates need;
- the committed ``conf/hosts/turing/expected.yaml``: it validates, it agrees with ``util/macvm_ctl.bash``
  on the VM and G-MEM thresholds, with ``hosttools-environment.yml`` on the tools (erratum E-D6), and
  with ``conf/hosts/turing/conda-envs/`` on the envs.

The probe fixtures are synthetic dicts, except where a test names a capture from turing (2026-10-20).
Most cases call ``main()`` in-process; the CLI contract cases run the script.
"""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import yaml

from tests.redacted_env import RedactedEnv
from tests.test_host_state_probe import ProbeHarness

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "host_state_check.py"
PROBE_PATH = REPO_ROOT / "util" / "host_state_probe.bash"
MACVM_CTL = REPO_ROOT / "util" / "macvm_ctl.bash"
TURING_EXPECTED = REPO_ROOT / "conf" / "hosts" / "turing" / "expected.yaml"
TIMEOUT_SECONDS = 120


def load_module():
    spec = importlib.util.spec_from_file_location("host_state_check", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    return module


HSC = load_module()

HOME = "/Users/tester"
ROOT = f"{HOME}/Development/python/Juniper"
LOCAL_BIN = f"{HOME}/.local/bin"
REPOS = ("canopy", "cascor", "cascor-client", "cascor-worker", "data", "data-client", "deploy", "k8s", "ml", "recurrence")
TOOLS = ["timeout", "shellcheck", "yq", "sops"]
ENVS = ["JuniperPython", "JuniperHostTools", "JuniperCascor1", "JuniperData", "JuniperCanopy1"]
SHA = "0123456789abcdef" * 4
MAC = "00:e0:4c:68:06:b1"
RESERVED = "192.168.50.222"

# Captures from turing, 2026-10-20.
TURING_PREFLIGHT = """\
headless signing preflight: non-credential checks only (card and PIN checks are owner-run; see --help)
repo       /Users/pcalnon/Development/python/Juniper/juniper-ml
gnupghome  /Users/pcalnon/.gnupg (from gpgconf --list-dirs homedir)

PASS  signing-key     user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A! (pinned)
FAIL  commit-gpgsign  signing disabled by construction (D11): GIT_CONFIG_KEY_0=commit.gpgsign, GIT_CONFIG_VALUE_0=false. This session cannot sign; agent sessions land commits through util/open_signed_pr.py
INFO  tag-gpgsign     tag.gpgsign=false (disabled by construction, D11: GIT_CONFIG_KEY_1=tag.gpgsign, GIT_CONFIG_VALUE_1=false)
PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor 'mac' (pinentry-program in /Users/pcalnon/.gnupg/gpg-agent.conf)
PASS  agent-socket    /Users/pcalnon/.gnupg/S.gpg-agent is a socket
PASS  external-cache  no-allow-external-cache is set in /Users/pcalnon/.gnupg/gpg-agent.conf
INFO  head-signature  HEAD 5e8e8747 %G?=E: a signature that cannot be checked, for example because its key is not in the keyring, key B5690EEEBB952194

"""
TURING_CSRUTIL = "System Integrity Protection status: unknown (Custom Configuration).\n\nConfiguration:\n\tKext Signing: disabled\n"
TURING_CONDA = """\
# conda environments:
#
# *  -> active
# + -> frozen
                         /Users/pcalnon/opt/anaconda3
                         /Users/pcalnon/opt/anaconda3/envs/dynet
base                     /usr/local/miniforge3
JuniperCanopy1           /usr/local/miniforge3/envs/JuniperCanopy1
JuniperCascor1           /usr/local/miniforge3/envs/JuniperCascor1
JuniperData              /usr/local/miniforge3/envs/JuniperData
JuniperHostTools         /usr/local/miniforge3/envs/JuniperHostTools
JuniperPython        *   /usr/local/miniforge3/envs/JuniperPython
"""
TURING_KUBECTL = json.dumps({"clientVersion": {"major": "1", "minor": "22", "gitVersion": "v1.22.4", "platform": "darwin/amd64"}})
TURING_EN7 = f"en7: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500\n\tether {MAC}\n\tmedia: autoselect (none)\n\tstatus: inactive\n"
# socketfilterfw: turing's captures, the firewall off with block all disabled (2026-10-25) and on, blocking all
# incoming connections (2026-10-26, once the owner applied C2); and the binary's "set to block all" sentence, which
# sits beside "Block all DISABLED!" in its strings as --setblockall's confirmation.
TURING_FIREWALL = "Firewall is disabled. (State = 0)\n"
TURING_BLOCKALL = "Firewall has block all state set to disabled.\n"
FIREWALL_BLOCKING = "Firewall is blocking all non-essential incoming connections. (State = 2)\n"
BLOCKALL_ON = "Firewall is blocking all non-essential incoming connections.\n"
BLOCKALL_SET = "Firewall is set to block all non-essential incoming connections\n"


def cap(stdout: str = "", rc: int = 0, *, argv: tuple[str, ...] = ("tool",), found: bool = True, timed_out: bool = False, stderr: str = "") -> dict:
    return {"argv": list(argv), "found": found, "rc": rc if found else None, "timed_out": timed_out, "stdout": stdout, "stderr": stderr}


def vm_stat(free: int, inactive: int, speculative: int = 0, page: int = 4096) -> str:
    return f"Mach Virtual Memory Statistics: (page size of {page} bytes)\n" f"Pages free:                         {free:>10}.\n" f"Pages active:                          1352631.\n" f"Pages inactive:                     {inactive:>10}.\n" f"Pages speculative:                  {speculative:>10}.\n" f"Pages wired down:                       896534.\n"


def swap(used: str) -> str:
    return f"vm.swapusage: total = 11264.00M  used = {used}  free = 1274.50M  (encrypted)\n"


def alias_doc(fail: tuple = (), error: tuple = (), skipped: bool = False) -> dict:
    repos = []
    for name in REPOS:
        checks = {}
        for check in ("origin", "alias", "key"):
            status = "error" if (name, check) in error else "fail" if (name, check) in fail else "pass"
            checks[check] = {"status": status, "ok": status == "pass", "message": f"{check} of juniper-{name} is {status}", "remediation": None if status == "pass" else f"fix the {check} of juniper-{name}"}
        repos.append({"repo": f"juniper-{name}", "checkout": f"{ROOT}/juniper-{name}", "alias": f"github_juniper-{name}", "ok": all(c["ok"] for c in checks.values()), "checks": checks})
    code = 2 if error else 1 if fail else 0
    return {"schema": 1, "mode": "check", "root": ROOT, "ssh_config": f"{HOME}/.ssh/config", "skipped": skipped, "skip_reason": "no github_juniper-* Host alias in x" if skipped else None, "ok": code == 0, "exit_code": code, "summary": "summary", "failures": [], "repos": [] if skipped else repos}


def signing_doc(fail: tuple = (), error: tuple = ()) -> dict:
    checks = [{"id": "include", "status": "pass", "message": "include holds only the signing keys", "remediation": None}]
    for name in REPOS:
        cid = f"repo:juniper-{name}"
        status = "error" if cid in error else "fail" if cid in fail else "pass"
        checks.append({"id": cid, "status": status, "message": f"{cid} is {status}", "remediation": None if status == "pass" else f"fix {cid}"})
    checks.append({"id": "session", "status": "info", "message": "this session cannot sign, by construction (D11)", "remediation": None})
    code = 2 if error else 1 if fail else 0
    return {"schema": 1, "mode": "check", "checks": checks, "ok": code == 0, "exit_code": code, "summary": "OK -- all 11 checks passed" if code == 0 else "FAILED"}


def ifconfig(en7: str = "") -> str:
    en7 = en7 or f"en7: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500\n\tether {MAC}\n\tinet {RESERVED} netmask 0xffffff00 broadcast 192.168.50.255\n\tmedia: autoselect (1000baseT <full-duplex>)\n\tstatus: active\n"
    return "lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384\n\tinet 127.0.0.1 netmask 0xff000000\nen0: flags=8863<UP,BROADCAST> mtu 1500\n\tether ac:bc:32:00:00:01\n\tinet 192.168.50.180 netmask 0xffffff00\n\tmedia: autoselect\n\tstatus: active\n" + en7


def green_probe() -> dict:
    """A host on which every gate passes."""
    return {
        "schema": 1,
        "probe": "util/host_state_probe.bash",
        "collected_at": "2026-10-20T12:00:00Z",
        "node": "testhost.example",
        "kernel": "Darwin",
        "home": HOME,
        "root": ROOT,
        "repo": f"{ROOT}/juniper-ml",
        "timeout_seconds": 60,
        "sections": ["hardware", "memory", "vm", "network", "power", "security", "tools", "env", "alias", "signing"],
        "hardware": {"arch": cap("x86_64\n"), "memsize": cap("17179869184\n"), "physicalcpu": cap("6\n"), "ncpu": cap("12\n")},
        "memory": {
            "vm_stat": cap(vm_stat(free=2000000, inactive=1000000)),
            "swapusage": cap(swap("0.00M")),
            "docker": [{"name": n, "pgrep": cap("", rc=1)} for n in ("com.docker.backend", "Docker Desktop", "Docker")],
        },
        "vm": {"name": "juniper-macvm", "showvminfo": cap("", rc=1, stderr="VBoxManage: error: Could not find a registered machine named 'juniper-macvm'\n")},
        "network": {"ifconfig": cap(ifconfig())},
        "power": {},
        "security": {
            "sip": cap("System Integrity Protection status: enabled.\n"),
            "authenticated_root": cap("Authenticated Root status: enabled\n"),
            "firewall": cap("Firewall is enabled. (State = 1)\n"),
            "blockall": cap(BLOCKALL_ON),
            "stealth": cap("Firewall stealth mode is on\n"),
            "filevault": cap("FileVault is On.\n"),
            "key_exports": {"dirs": [f"{HOME}/.ssh", f"{HOME}/.gnupg"], "find": cap("")},
            "ssh_loose": {"dir": f"{HOME}/.ssh", "find": cap("")},
        },
        "tools": {
            "local_bin": LOCAL_BIN,
            "resolved": {t: {"path": f"{LOCAL_BIN}/{t}", "local_bin": {"exists": True, "executable": True, "link": None}} for t in TOOLS},
            "kubectl_version": cap(json.dumps({"clientVersion": {"major": "1", "minor": "36", "gitVersion": "v1.36.2"}})),
        },
        "env": {
            "conda": cap(TURING_CONDA),
            "parent_agents_md": {"path": f"{ROOT}/AGENTS.md", "exists": True, "sha256": cap(f"{SHA}  {ROOT}/AGENTS.md\n")},
        },
        "alias": {"check": cap(json.dumps(alias_doc()))},
        "signing": {"config": cap(json.dumps(signing_doc())), "preflight": cap(TURING_PREFLIGHT, rc=1)},
    }


def green_expected() -> dict:
    return {
        "schema": 1,
        "host": "testhost",
        "identity": {"arch": "x86_64", "memsize_bytes": 17179869184, "physicalcpu": 6, "ncpu": 12},
        "vm": {"name": "juniper-macvm", "mem_gib": 6, "vcpus": 4},
        "gates": {
            "G-ALIAS": {},
            "G-SIGN": {"integration": {"date": "2026-10-27", "record": "reports/i-sign.md"}},
            "G-SEC": {},
            "G-TOOLS": {"local_bin": list(TOOLS), "kubectl": {"cluster": "1.36", "max_minor_skew": 1}},
            "G-ENV": {"conda_envs": list(ENVS), "parent_agents_md": {"sha256": SHA}},
            "G-NET": {"interface": "en7", "mac": MAC, "media": "1000baseT", "reserved_ip": RESERVED, "min_mbps": 800, "throughput": {"date": "2026-10-27", "mbps": 941, "record": "reports/iperf3.txt"}},
            "G-MEM": {"reserve_gib": 4, "max_swap_gib": 2},
        },
    }


class CheckTestCase(unittest.TestCase):
    """A temp repository with conf/hosts/testhost/expected.yaml and its two record files."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.repo = self.tmp / "repo"
        self.expected_path = self.repo / "conf" / "hosts" / "testhost" / "expected.yaml"
        self.expected_path.parent.mkdir(parents=True)
        (self.repo / "reports").mkdir()
        for name in ("i-sign.md", "iperf3.txt"):
            (self.repo / "reports" / name).write_text("record\n", encoding="utf-8")
        self.probe_path = self.tmp / "probe.json"
        self.probe = green_probe()
        self.expected = green_expected()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self) -> None:
        self.expected_path.write_text(yaml.safe_dump(self.expected, sort_keys=False), encoding="utf-8")
        self.probe_path.write_text(json.dumps(self.probe), encoding="utf-8")

    def main(self, *args: str, write: bool = True) -> tuple[int, str, str]:
        if write:
            self.write()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = HSC.main(["--expected", str(self.expected_path), "--probe-json", str(self.probe_path), *args])
        return code, out.getvalue(), err.getvalue()

    def result(self, *args: str) -> tuple[int, dict]:
        code, out, err = self.main("--json", *args)
        self.assertEqual(err, "")
        return code, json.loads(out)

    def condition(self, result: dict, gate: str, cid: str) -> dict:
        gates = {g["id"]: g for g in result["gates"]}
        return {c["id"]: c for c in gates[gate]["conditions"]}[cid]

    def assertStartupError(self, message: str, *args: str, write: bool = True) -> None:
        code, out, err = self.main(*args, write=write)
        self.assertEqual(code, 2, out + err)
        self.assertEqual(out, "")
        self.assertIn("ERROR:", err)
        self.assertIn(message, err)


class GreenHostTest(CheckTestCase):
    def test_every_gate_passes_in_both_modes(self) -> None:
        code, out, err = self.main()
        self.assertEqual((code, err), (0, ""))
        for gate in HSC.GATES:
            self.assertIn(f"PASS  {gate}  all ", out)
        self.assertIn("readiness: 7 of 7 gates pass", out)
        self.assertIn("not evaluated here:", out)
        self.assertEqual(self.main("--check")[0], 0)

    def test_the_json_carries_the_documented_keys(self) -> None:
        code, result = self.result("--check")
        self.assertEqual(code, 0)
        self.assertEqual(set(result), {"schema", "mode", "host", "expected", "probe", "identity", "gates", "not_evaluated", "readiness", "ok", "exit_code", "summary"})
        self.assertEqual((result["schema"], result["mode"], result["host"], result["ok"], result["exit_code"]), (1, "check", "testhost", True, 0))
        self.assertEqual(result["expected"], str(self.expected_path))
        self.assertEqual(result["probe"], {"source": "file", "path": str(self.probe_path), "collected_at": "2026-10-20T12:00:00Z", "node": "testhost.example"})
        self.assertEqual(result["identity"], "x86_64, 6 cores / 12 threads, hw.memsize 17179869184 (16 GiB)")
        self.assertEqual([g["id"] for g in result["gates"]], list(HSC.GATES))
        self.assertEqual([n["id"] for n in result["not_evaluated"]], ["G-AUTH", "G-PATH", "G-AGENT"])
        self.assertEqual(result["readiness"], {"passed": 7, "evaluated": 7})
        conditions = {g["id"]: [c["id"] for c in g["conditions"]] for g in result["gates"]}
        self.assertEqual(
            conditions,
            {
                "G-ALIAS": ["origins", "aliases", "keys"],
                "G-SIGN": ["signing-config", "pinentry", "agent-socket", "external-cache", "integration"],
                "G-SEC": ["sip", "authenticated-root", "firewall", "filevault", "key-exports", "key-modes"],
                "G-TOOLS": ["local-bin", "kubectl"],
                "G-ENV": ["conda-envs", "parent-agents-md"],
                "G-NET": ["link", "address", "throughput"],
                "G-MEM": ["memory", "swap", "docker"],
            },
        )
        for gate in result["gates"]:
            for cond in gate["conditions"]:
                self.assertEqual(set(cond), {"id", "status", "message", "remediation"})

    def test_an_origin_rewritten_by_fix_counts_as_passed(self) -> None:
        doc = alias_doc()
        doc["repos"][7]["checks"]["origin"]["status"] = "fixed"
        set_path(self.probe, "alias.check", cap(json.dumps(doc)))
        _, result = self.result("--check")
        self.assertEqual(self.condition(result, "G-ALIAS", "origins")["status"], "pass")
        self.assertIn("10 of 10 checkouts", self.condition(result, "G-ALIAS", "origins")["message"])

    def test_the_agent_session_preflight_still_passes_its_three_lines(self) -> None:
        # turing's preflight exits 1 in an agent session (D11 fails commit-gpgsign); G-SIGN reads only
        # pinentry, agent-socket and external-cache from it.
        _, result = self.result()
        self.assertEqual(self.condition(result, "G-SIGN", "pinentry")["status"], "pass")
        self.assertIn("pinentry-mac reports flavor 'mac'", self.condition(result, "G-SIGN", "pinentry")["message"])


def set_path(doc: dict, path: str, value) -> None:
    keys = path.split(".")
    for key in keys[:-1]:
        doc = doc[int(key)] if isinstance(doc, list) else doc[key]
    if isinstance(doc, list):
        doc[int(keys[-1])] = value
    else:
        doc[keys[-1]] = value


# (description, probe changes {dotted path: value}, expected changes, gate, condition, status, message part)
FAILURES: list[tuple[str, dict[str, Any], dict[str, Any], str, str, str, str]] = [
    ("R-G2a/b: two origins bypass the alias", {"alias.check": cap(json.dumps(alias_doc(fail=(("k8s", "origin"), ("recurrence", "origin")))), rc=1)}, {}, "G-ALIAS", "origins", "fail", "8 of 10 checkouts use their per-repo alias"),
    ("R-G2c: AddKeysToAgent yes", {"alias.check": cap(json.dumps(alias_doc(fail=(("ml", "alias"),))), rc=1)}, {}, "G-ALIAS", "aliases", "fail", "juniper-ml: alias of juniper-ml is fail"),
    ("a key at mode 644", {"alias.check": cap(json.dumps(alias_doc(fail=(("ml", "key"),))), rc=1)}, {}, "G-ALIAS", "keys", "fail", "9 of 10 deploy keys"),
    ("no alias configured at all", {"alias.check": cap(json.dumps(alias_doc(skipped=True)))}, {}, "G-ALIAS", "origins", "fail", "skipped"),
    ("ssh -G could not evaluate", {"alias.check": cap(json.dumps(alias_doc(error=(("ml", "alias"),))), rc=2)}, {}, "G-ALIAS", "aliases", "error", "could not evaluate"),
    ("the alias tool printed no JSON", {"alias.check": cap("", rc=2, stderr="ERROR: git not found\n")}, {}, "G-ALIAS", "keys", "error", "printed no JSON (exit 2): ERROR: git not found"),
    ("the alias tool timed out", {"alias.check": cap("", rc=143, timed_out=True)}, {}, "G-ALIAS", "origins", "error", "timed out"),
    ("a repo-local signing key", {"signing.config": cap(json.dumps(signing_doc(fail=("repo:juniper-ml",))), rc=1)}, {}, "G-SIGN", "signing-config", "fail", "repo:juniper-ml is fail"),
    ("the signing check errored", {"signing.config": cap(json.dumps(signing_doc(error=("repo:juniper-ml",))), rc=2)}, {}, "G-SIGN", "signing-config", "error", "could not evaluate"),
    ("R-B7b: a curses pinentry", {"signing.preflight": cap(TURING_PREFLIGHT.replace("PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor 'mac'", "FAIL  pinentry        /usr/local/bin/pinentry is the 'curses' pinentry"), rc=1)}, {}, "G-SIGN", "pinentry", "fail", "'curses' pinentry"),
    ("no external-cache line", {"signing.preflight": cap(TURING_PREFLIGHT.replace("PASS  external-cache  no-allow-external-cache is set", "FAIL  external-cache  no no-allow-external-cache line"), rc=1)}, {}, "G-SIGN", "external-cache", "fail", "no no-allow-external-cache line"),
    ("gpg-agent not running", {"signing.preflight": cap(TURING_PREFLIGHT.replace("PASS  agent-socket", "FAIL  agent-socket"), rc=1)}, {}, "G-SIGN", "agent-socket", "fail", "is a socket"),
    ("the preflight could not run", {"signing.preflight": cap("", rc=2, stderr="ERROR: gpgconf not found\n")}, {}, "G-SIGN", "pinentry", "error", "gpgconf not found"),
    ("a preflight line is missing", {"signing.preflight": cap("PASS  pinentry        x\n", rc=0)}, {}, "G-SIGN", "agent-socket", "error", "no agent-socket line"),
    ("no I-SIGN record", {}, {"gates.G-SIGN.integration": None}, "G-SIGN", "integration", "fail", "no I-SIGN record"),
    ("the I-SIGN record file is missing", {}, {"gates.G-SIGN.integration": {"date": "2026-10-27", "record": "reports/absent.md"}}, "G-SIGN", "integration", "fail", "reports/absent.md (dated 2026-10-27) does not exist"),
    ("SIP in a custom configuration (turing)", {"security.sip": cap(TURING_CSRUTIL)}, {}, "G-SEC", "sip", "fail", "unknown (Custom Configuration)"),
    ("SIP disabled", {"security.sip": cap("System Integrity Protection status: disabled.\n")}, {}, "G-SEC", "sip", "fail", "disabled"),
    ("csrutil printed no status", {"security.sip": cap("garbage\n")}, {}, "G-SEC", "sip", "error", "no status"),
    ("authenticated root disabled", {"security.authenticated_root": cap("Authenticated Root status: disabled\n")}, {}, "G-SEC", "authenticated-root", "fail", "disabled"),
    ("the firewall is off (turing)", {"security.firewall": cap(TURING_FIREWALL), "security.blockall": cap(TURING_BLOCKALL)}, {}, "G-SEC", "firewall", "fail", "State = 0"),
    ("C2: the firewall on, but not blocking all", {"security.firewall": cap("Firewall is enabled. (State = 1)\n"), "security.blockall": cap(TURING_BLOCKALL)}, {}, "G-SEC", "firewall", "fail", "Firewall is enabled. (State = 1); Firewall has block all state set to disabled."),
    ("an unknown block-all state", {"security.blockall": cap("Firewall has unknown block all state.\n")}, {}, "G-SEC", "firewall", "error", "no block-all state in 'Firewall has unknown block all state.'"),
    ("socketfilterfw --getblockall failed", {"security.blockall": cap("", rc=1, stderr="socketfilterfw: boom\n")}, {}, "G-SEC", "firewall", "error", "socketfilterfw: boom"),
    ("FileVault off", {"security.filevault": cap("FileVault is Off.\n")}, {}, "G-SEC", "filevault", "fail", "FileVault is Off."),
    ("fdesetup missing", {"security.filevault": cap(found=False, argv=("/usr/bin/fdesetup", "status"))}, {}, "G-SEC", "filevault", "error", "/usr/bin/fdesetup not found"),
    ("key exports at rest (task C3)", {"security.key_exports.find": cap(f"{HOME}/.ssh/priv.asc\n{HOME}/.ssh/github-recovery-codes.txt\n")}, {}, "G-SEC", "key-exports", "fail", "2 key-export or recovery file(s): ~/.ssh/github-recovery-codes.txt, ~/.ssh/priv.asc"),
    ("a key open to others (task C4)", {"security.ssh_loose.find": cap(f"{HOME}/.ssh/id-turing-aws-ec2.pem\n")}, {}, "G-SEC", "key-modes", "fail", "~/.ssh/id-turing-aws-ec2.pem"),
    ("find was refused a directory", {"security.key_exports.find": cap("", rc=1, stderr="find: /Users/tester/.gnupg/x: Permission denied\n")}, {}, "G-SEC", "key-exports", "error", "Permission denied"),
    ("E-D6: a tool shadowed on PATH", {"tools.resolved.yq.path": "/usr/local/bin/yq"}, {}, "G-TOOLS", "local-bin", "fail", "yq: command -v finds /usr/local/bin/yq, ahead of ~/.local/bin/yq"),
    ("a dangling local-bin link", {"tools.resolved.sops.local_bin": {"exists": True, "executable": False, "link": "/gone/sops"}}, {}, "G-TOOLS", "local-bin", "fail", "sops: ~/.local/bin/sops is a dangling or non-executable link to /gone/sops"),
    ("a missing local-bin entry", {"tools.resolved.timeout": {"path": "/usr/bin/timeout", "local_bin": {"exists": False, "executable": False, "link": None}}}, {}, "G-TOOLS", "local-bin", "fail", "timeout: ~/.local/bin/timeout is missing"),
    ("local-bin is not on PATH", {"tools.resolved.yq.path": None}, {}, "G-TOOLS", "local-bin", "fail", "yq: ~/.local/bin is not on PATH"),
    ("a tool the probe did not resolve", {}, {"gates.G-TOOLS.local_bin": TOOLS + ["age"]}, "G-TOOLS", "local-bin", "error", "run it with --tool age"),
    ("kubectl 1.22 (turing)", {"tools.kubectl_version": cap(TURING_KUBECTL)}, {}, "G-TOOLS", "kubectl", "fail", "v1.22.4 is 14 minors behind the cluster's 1.36 (allowed: 1)"),
    ("kubectl two minors ahead", {"tools.kubectl_version": cap(json.dumps({"clientVersion": {"major": "1", "minor": "38+", "gitVersion": "v1.38.0"}}))}, {}, "G-TOOLS", "kubectl", "fail", "2 minors ahead of"),
    ("kubectl missing", {"tools.kubectl_version": cap(found=False, argv=("kubectl", "version"))}, {}, "G-TOOLS", "kubectl", "fail", "kubectl not found"),
    ("kubectl printed no version", {"tools.kubectl_version": cap("{}")}, {}, "G-TOOLS", "kubectl", "error", "no clientVersion"),
    ("a conda env is missing", {"env.conda": cap(TURING_CONDA.replace("JuniperData              /usr/local/miniforge3/envs/JuniperData\n", ""))}, {}, "G-ENV", "conda-envs", "fail", "missing: JuniperData"),
    ("conda missing", {"env.conda": cap(found=False, argv=("conda", "env", "list"))}, {}, "G-ENV", "conda-envs", "fail", "conda not found"),
    ("the parent AGENTS.md is absent (task E4)", {"env.parent_agents_md": {"path": f"{ROOT}/AGENTS.md", "exists": False, "sha256": None}}, {}, "G-ENV", "parent-agents-md", "fail", "~/Development/python/Juniper/AGENTS.md is absent"),
    ("no hash is recorded", {}, {"gates.G-ENV.parent_agents_md.sha256": None}, "G-ENV", "parent-agents-md", "fail", "but no hash is recorded"),
    ("the parent AGENTS.md drifted", {"env.parent_agents_md.sha256": cap(f"{'f' * 64}  {ROOT}/AGENTS.md\n")}, {}, "G-ENV", "parent-agents-md", "fail", f"has sha256 {'f' * 64}, not the recorded {SHA}"),
    ("no carrier on en7 (turing)", {"network.ifconfig": cap(ifconfig(TURING_EN7))}, {}, "G-NET", "link", "fail", "en7: media autoselect (none), status inactive"),
    ("a 100baseTX link", {"network.ifconfig": cap(ifconfig(TURING_EN7.replace("(none)", "(100baseTX <full-duplex>)").replace("inactive", "active")))}, {}, "G-NET", "link", "fail", "100baseTX"),
    ("the dongle renumbered", {"network.ifconfig": cap(ifconfig(TURING_EN7.replace("en7:", "en8:")))}, {}, "G-NET", "link", "fail", "en7 does not exist; the dongle 00:e0:4c:68:06:b1 is en8"),
    ("another adapter on en7", {"network.ifconfig": cap(ifconfig(TURING_EN7.replace(MAC, "11:22:33:44:55:66")))}, {}, "G-NET", "link", "fail", "en7 is 11:22:33:44:55:66, not the dongle"),
    ("no reserved address (task A6)", {}, {"gates.G-NET.reserved_ip": None}, "G-NET", "address", "fail", "no reserved address is recorded for en7"),
    ("the wrong address", {}, {"gates.G-NET.reserved_ip": "192.168.50.60"}, "G-NET", "address", "fail", f"en7 holds {RESERVED}, not the reserved 192.168.50.60"),
    ("no throughput record (task F2)", {}, {"gates.G-NET.throughput": None}, "G-NET", "throughput", "fail", "not measured"),
    ("a slow link", {}, {"gates.G-NET.throughput.mbps": 412.5}, "G-NET", "throughput", "fail", "412.5 Mb/s on 2026-10-27 is below 800 Mb/s"),
    ("ifconfig failed", {"network.ifconfig": cap("", rc=1, stderr="ifconfig: boom\n")}, {}, "G-NET", "link", "error", "ifconfig: boom"),
    ("too little memory", {"memory.vm_stat": cap(vm_stat(free=4241, inactive=1335016, speculative=16843))}, {}, "G-MEM", "memory", "fail", "free + inactive 5297 MiB < 10240 MiB required"),
    ("swap in use (turing)", {"memory.swapusage": cap(swap("9989.50M"))}, {}, "G-MEM", "swap", "fail", "swap used 9990 MiB > 2048 MiB allowed (used = 9989.50M)"),
    ("Docker Desktop running (turing)", {"memory.docker.0.pgrep": cap("682\n"), "memory.docker.2.pgrep": cap("674\n")}, {}, "G-MEM", "docker", "fail", "com.docker.backend (pid 682), Docker (pid 674)"),
    ("pgrep failed", {"memory.docker.1.pgrep": cap("", rc=3, stderr="pgrep: boom\n")}, {}, "G-MEM", "docker", "error", "pgrep: boom"),
    ("vm_stat lacks a count", {"memory.vm_stat": cap("Mach Virtual Memory Statistics: (page size of 4096 bytes)\nPages free: 10.\n")}, {}, "G-MEM", "memory", "error", "lacks a 'Pages free', 'Pages speculative' or 'Pages inactive' count"),
    ("a larger registered VM", {"vm.showvminfo": cap('VMState="poweroff"\nmemory=9216\n')}, {}, "G-MEM", "memory", "fail", "VM 9216 MiB from the VM's configured memory"),
]


class FailureTest(CheckTestCase):
    def test_each_condition_fails_or_errors_on_its_own(self) -> None:
        for description, probe_changes, expected_changes, gate, cid, status, part in FAILURES:
            with self.subTest(description):
                self.probe = green_probe()
                self.expected = green_expected()
                for path, value in probe_changes.items():
                    set_path(self.probe, path, copy.deepcopy(value))
                for path, value in expected_changes.items():
                    set_path(self.expected, path, copy.deepcopy(value))
                code, result = self.result("--check")
                cond = self.condition(result, gate, cid)
                self.assertEqual(cond["status"], status, cond)
                self.assertIn(part, cond["message"])
                if status == "fail":
                    self.assertIsNotNone(cond["remediation"], cond)
                self.assertEqual(code, 1 if status == "fail" else 2)
                gates = {g["id"]: g for g in result["gates"]}
                self.assertEqual(gates[gate]["status"], status)
                others = [g["id"] for g in result["gates"] if g["id"] != gate and g["status"] != "pass"]
                self.assertEqual(others, [], "one change should move one gate")
                self.assertEqual(self.main()[0], 0, "the report exits 0 whatever the gates say")

    def test_a_failure_wins_the_gate_over_an_error(self) -> None:
        set_path(self.probe, "security.sip", cap("System Integrity Protection status: disabled.\n"))
        set_path(self.probe, "security.filevault", cap("", rc=1))
        code, result = self.result("--check")
        gate = next(g for g in result["gates"] if g["id"] == "G-SEC")
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["summary"], "1 of 6 fail: sip; 1 could not be evaluated: filevault")
        self.assertEqual(code, 2, "under --check an error anywhere exits 2, which wins over 1")

    def test_the_text_report_names_each_fix(self) -> None:
        set_path(self.probe, "security.firewall", cap(TURING_FIREWALL))
        set_path(self.probe, "security.blockall", cap(TURING_BLOCKALL))
        code, out, _ = self.main()
        self.assertEqual(code, 0)
        self.assertIn("FAIL  G-SEC  1 of 6 fail: firewall", out)
        self.assertIn("  FAIL  firewall           Firewall is disabled. (State = 0); Firewall has block all state set to disabled.; Firewall stealth mode is on -- fix: task C2 (owner)", out)
        self.assertIn("readiness: 6 of 7 gates pass (G-ALIAS, G-SIGN, G-TOOLS, G-ENV, G-NET, G-MEM); 1 fail: G-SEC", out)


class FirewallTest(CheckTestCase):
    """G-SEC's firewall condition under C2's block-all form (owner ruling 2026-10-25)."""

    def firewall(self, globalstate: str, blockall=None, stealth: str | None = None) -> dict:
        set_path(self.probe, "security.firewall", cap(globalstate))
        if blockall is not None:
            set_path(self.probe, "security.blockall", blockall if isinstance(blockall, dict) else cap(blockall))
        if stealth is not None:
            set_path(self.probe, "security.stealth", cap(stealth))
        _, result = self.result("--check")
        return self.condition(result, "G-SEC", "firewall")

    def test_block_all_passes_in_either_state(self) -> None:
        # Block all left turing's global state at 2 (2026-10-26), but the gate judges block all by its own
        # capture, so 1 passes too (G1's C12).
        for globalstate in (FIREWALL_BLOCKING, "Firewall is enabled. (State = 1)\n"):
            with self.subTest(globalstate=globalstate):
                cond = self.firewall(globalstate, BLOCKALL_ON)
                self.assertEqual(cond["status"], "pass", cond)
                self.assertIn(BLOCKALL_ON.strip(), cond["message"])

    def test_turing_with_c2_applied_passes(self) -> None:
        cond = self.firewall(FIREWALL_BLOCKING, BLOCKALL_ON, stealth="Firewall stealth mode is on\n")
        self.assertEqual(cond["status"], "pass", cond)
        self.assertEqual(cond["message"], "Firewall is blocking all non-essential incoming connections. (State = 2); Firewall is blocking all non-essential incoming connections.; Firewall stealth mode is on")

    def test_the_setters_sentence_cannot_be_judged(self) -> None:
        # --getblockall never prints --setblockall's confirmation, so a capture holding it is not the getter's.
        for globalstate in (FIREWALL_BLOCKING, "Firewall is enabled. (State = 1)\n"):
            with self.subTest(globalstate=globalstate):
                cond = self.firewall(globalstate, BLOCKALL_SET)
                self.assertEqual(cond["status"], "error", cond)
                self.assertIn("no block-all state in 'Firewall is set to block all non-essential incoming connections'", cond["message"])

    def test_the_fix_names_only_the_missing_steps(self) -> None:
        off = self.firewall(TURING_FIREWALL, TURING_BLOCKALL)
        self.assertEqual(off["status"], "fail")
        for step in ("--setglobalstate on", "--setblockall on", "--setstealthmode on"):
            self.assertIn(step, off["remediation"])
        on = self.firewall("Firewall is enabled. (State = 1)\n", TURING_BLOCKALL)
        self.assertEqual(on["status"], "fail")
        self.assertIn("--setblockall on", on["remediation"])
        self.assertNotIn("--setglobalstate", on["remediation"])
        for cond in (off, on):
            self.assertIn("/usr/libexec/ApplicationFirewall/socketfilterfw", cond["remediation"])
            self.assertNotIn("signed software", cond["remediation"], "C2's block-all form replaced 'allow signed software'")

    def test_an_off_firewall_fails_even_when_block_all_cannot_be_read(self) -> None:
        for blockall in (cap("Firewall is in undefined block all state.\n"), cap(BLOCKALL_SET), cap(found=False, argv=("/usr/libexec/ApplicationFirewall/socketfilterfw", "--getblockall"))):
            with self.subTest(blockall=blockall):
                cond = self.firewall(TURING_FIREWALL, blockall)
                self.assertEqual(cond["status"], "fail", cond)
                self.assertIn("--setblockall on", cond["remediation"])

    def test_a_probe_without_the_block_all_capture_cannot_pass(self) -> None:
        # A probe from before 2026-10-25 has no blockall capture: a firewall that is on cannot be judged.
        del self.probe["security"]["blockall"]
        cond = self.firewall("Firewall is enabled. (State = 1)\n")
        self.assertEqual(cond["status"], "error", cond)
        self.assertIn("the probe recorded no socketfilterfw --getblockall", cond["message"])

    def test_stealth_mode_is_reported_not_gated(self) -> None:
        cond = self.firewall(FIREWALL_BLOCKING, BLOCKALL_ON, stealth="Firewall stealth mode is off\n")
        self.assertEqual(cond["status"], "pass", cond)
        self.assertIn("Firewall stealth mode is off", cond["message"])


class SectionTest(CheckTestCase):
    def test_a_section_evaluates_only_its_gate(self) -> None:
        for spelling in ("G-MEM", "g-mem", "mem", " Mem "):
            with self.subTest(spelling=spelling):
                code, result = self.result("--section", spelling)
                self.assertEqual(code, 0)
                self.assertEqual([g["id"] for g in result["gates"]], ["G-MEM"])
                self.assertEqual(result["not_evaluated"], [])
                self.assertEqual(result["readiness"], {"passed": 1, "evaluated": 1})

    def test_sections_keep_the_canonical_order(self) -> None:
        _, result = self.result("--section", "net", "--section", "alias", "--section", "G-NET")
        self.assertEqual([g["id"] for g in result["gates"]], ["G-ALIAS", "G-NET"])

    def test_a_saved_probe_needs_only_the_sections_asked_for(self) -> None:
        self.probe["sections"] = ["hardware", "memory", "vm"]
        for section in ("network", "security", "tools", "env", "alias", "signing"):
            del self.probe[section]
        self.assertEqual(self.main("--section", "G-MEM", "--check")[0], 0)
        self.assertStartupError("lacks section(s) security; collect them with: bash util/host_state_probe.bash --json --section hardware --section security", "--section", "G-SEC")

    def test_unknown_and_elsewhere_gates_are_usage_errors(self) -> None:
        self.assertStartupError("unknown gate 'disk'", "--section", "disk")
        self.assertStartupError("G-AUTH is not evaluated here: operator-run", "--section", "auth")
        self.assertStartupError("G-PATH is not evaluated here", "--section", "G-PATH")


# (description, expected change {dotted path: value}, message part)
INVALID: list[tuple[str, dict[str, Any], str]] = [
    ("R-G1 / X2: a 44 GiB VM on a 16 GiB host", {"vm.mem_gib": 44}, "vm.mem_gib 44 cannot fit: hw.memsize 17179869184 is 16 GiB, and less G-MEM's 4 GiB reserve that leaves 12 GiB for the VM (regression R-G1, the X2 class"),
    ("R-G1: one GiB over", {"vm.mem_gib": 13}, "vm.mem_gib 13 cannot fit"),
    ("R-G1: the reserve pushes it over", {"gates.G-MEM.reserve_gib": 11}, "vm.mem_gib 6 cannot fit"),
    ("R-G1 / X2: 8 vCPU on 6 cores", {"vm.vcpus": 8}, "vm.vcpus 8 exceeds identity.physicalcpu 6 (regression R-G1, the X2 class"),
    ("schema", {"schema": 2}, "schema: want 1, got 2"),
    ("schema as a boolean", {"schema": True}, "schema: want 1"),
    ("an unknown key", {"extra": 1}, "unknown key(s) extra"),
    ("a missing gate", {"gates.G-MEM": "__delete__"}, "gates: missing key(s) G-MEM"),
    ("an unknown gate", {"gates.G-AUTH": {}}, "unknown key(s) G-AUTH"),
    ("memsize as a string", {"identity.memsize_bytes": "16GiB"}, "identity.memsize_bytes: want a whole number"),
    ("a boolean count", {"identity.physicalcpu": True}, "identity.physicalcpu: want a whole number"),
    ("ncpu below physicalcpu", {"identity.ncpu": 4}, "identity.ncpu: want a whole number of at least 6"),
    ("an unquoted cluster version", {"gates.G-TOOLS.kubectl.cluster": 1.3}, 'a quoted "MAJOR.MINOR" string (an unquoted 1.30 reads as 1.3)'),
    ("a duplicate tool", {"gates.G-TOOLS.local_bin": ["yq", "yq"]}, "local_bin: want no duplicates"),
    ("a tool path, not a name", {"gates.G-TOOLS.local_bin": ["/usr/bin/yq"]}, "local_bin[0]: want tool names"),
    ("an empty env list", {"gates.G-ENV.conda_envs": []}, "conda_envs: want a non-empty list"),
    ("a short sha256", {"gates.G-ENV.parent_agents_md.sha256": "abc"}, "64 lower-case hex digits"),
    ("an upper-case sha256", {"gates.G-ENV.parent_agents_md.sha256": SHA.upper()}, "64 lower-case hex digits"),
    ("a bad IPv4", {"gates.G-NET.reserved_ip": "192.168.50.256"}, "reserved_ip: want an IPv4 address or null"),
    ("an upper-case MAC", {"gates.G-NET.mac": MAC.upper()}, "a quoted lower-case MAC"),
    ("a record outside the repo", {"gates.G-SIGN.integration.record": "../x.md"}, "a path relative to the repository, without '..'"),
    ("an absolute record", {"gates.G-NET.throughput.record": "/tmp/x"}, "a path relative to the repository"),
    ("a bad date", {"gates.G-SIGN.integration.date": "27 Oct"}, "a YYYY-MM-DD date"),
    ("throughput without mbps", {"gates.G-NET.throughput": {"date": "2026-10-27", "record": "reports/iperf3.txt"}}, "missing key(s) mbps"),
    ("a negative swap limit", {"gates.G-MEM.max_swap_gib": -1}, "max_swap_gib: want a whole number of at least 0"),
    ("a VM name with a space", {"vm.name": "juniper macvm"}, "vm.name: want a VM name"),
]


class ExpectedValidationTest(CheckTestCase):
    def test_an_invalid_expected_file_exits_2_before_the_probe(self) -> None:
        self.probe_path.write_text("not read", encoding="utf-8")
        for description, changes, part in INVALID:
            with self.subTest(description):
                self.expected = green_expected()
                for path, value in changes.items():
                    if value == "__delete__":
                        keys = path.split(".")
                        del self.expected[keys[0]][keys[1]]
                    else:
                        set_path(self.expected, path, value)
                self.expected_path.write_text(yaml.safe_dump(self.expected, sort_keys=False), encoding="utf-8")
                code, out, err = self.main(write=False)
                self.assertEqual((code, out), (2, ""), err)
                self.assertIn(part, err)

    def test_a_vm_that_exactly_fills_the_headroom_fits(self) -> None:
        set_path(self.expected, "vm.mem_gib", 12)
        set_path(self.expected, "vm.vcpus", 6)
        set_path(self.probe, "memory.vm_stat", cap(vm_stat(free=3000000, inactive=1194304)))
        self.assertEqual(self.main("--check")[0], 0)

    def test_unquoted_yaml_dates_are_accepted(self) -> None:
        self.write()
        text = self.expected_path.read_text(encoding="utf-8").replace("'2026-10-27'", "2026-10-27")
        self.assertIn("date: 2026-10-27\n", text)
        self.expected_path.write_text(text, encoding="utf-8")
        code, out, _ = self.main("--json", write=False)
        self.assertEqual(code, 0)
        self.assertIn("I-SIGN recorded 2026-10-27: reports/i-sign.md", out)

    def test_missing_malformed_and_mismatched_files_exit_2(self) -> None:
        self.write()
        self.expected_path.write_text("schema: [1\n", encoding="utf-8")
        self.assertStartupError("is not valid YAML", write=False)
        self.assertStartupError("no expected state:", "--expected", str(self.tmp / "absent.yaml"))
        self.assertStartupError("describes host 'testhost', not 'otherhost'", "--host", "otherhost")
        self.assertStartupError("not a host name: 'Bad_Host'", "--host", "Bad_Host")

    def test_records_resolve_against_the_repository_that_holds_expected_yaml(self) -> None:
        loose = self.tmp / "elsewhere" / "expected.yaml"
        loose.parent.mkdir()
        self.write()
        loose.write_text(self.expected_path.read_text(encoding="utf-8"), encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            HSC.main(["--expected", str(loose), "--probe-json", str(self.probe_path), "--json", "--section", "G-SIGN"])
        result = json.loads(out.getvalue())
        self.assertEqual(self.condition(result, "G-SIGN", "integration")["status"], "fail", "outside conf/hosts/<host>/ a record resolves against the file's own directory")
        (loose.parent / "reports").mkdir()
        (loose.parent / "reports" / "i-sign.md").write_text("record\n", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            HSC.main(["--expected", str(loose), "--probe-json", str(self.probe_path), "--json", "--section", "G-SIGN"])
        self.assertEqual(self.condition(json.loads(out.getvalue()), "G-SIGN", "integration")["status"], "pass")


class ProbeDocumentTest(CheckTestCase):
    def test_a_probe_of_another_machine_exits_2(self) -> None:
        set_path(self.probe, "hardware.memsize", cap("8589934592\n"))
        self.assertStartupError("describes another machine than testhost's expected.yaml: memsize_bytes 8589934592, expected 17179869184")
        self.probe = green_probe()
        set_path(self.probe, "hardware.arch", cap("arm64\n"))
        self.assertStartupError("arch 'arm64', expected 'x86_64'")

    def test_an_unmeasurable_identity_exits_2(self) -> None:
        set_path(self.probe, "hardware.memsize", cap("", rc=1, stderr="sysctl: unknown oid 'hw.memsize'\n"))
        self.assertStartupError("cannot establish this host's identity")

    def test_a_document_that_is_not_the_probe_exits_2(self) -> None:
        self.write()
        for text, part in (("{not json", "is not the probe's JSON"), ("[]", "is not util/host_state_probe.bash output"), ('{"probe": "other"}', "is not util/host_state_probe.bash output"), ('{"probe": "util/host_state_probe.bash", "schema": 2}', "has probe schema 2; this check reads schema 1")):
            with self.subTest(text=text):
                self.probe_path.write_text(text, encoding="utf-8")
                self.assertStartupError(part, write=False)
        self.assertStartupError("cannot read", "--probe-json", str(self.tmp / "absent.json"))


class ParserTest(unittest.TestCase):
    def test_conda_env_list_names_named_and_unnamed_envs(self) -> None:
        names = HSC.parse_conda_envs(TURING_CONDA)
        self.assertEqual(names, {"dynet", "base", "JuniperCanopy1", "JuniperCascor1", "JuniperData", "JuniperHostTools", "JuniperPython"})

    def test_ifconfig_blocks(self) -> None:
        parsed = HSC.parse_ifconfig(ifconfig(TURING_EN7))
        self.assertEqual(parsed["en7"], {"ether": MAC, "inet": [], "media": "autoselect (none)", "status": "inactive"})
        self.assertEqual(parsed["en0"]["inet"], ["192.168.50.180"])
        self.assertEqual(parsed["lo0"]["inet"], ["127.0.0.1"])

    def test_swap_rounds_up_to_whole_mib(self) -> None:
        cases = {"0.00M": 0, "2048.00M": 2048, "2048.01M": 2049, "2.00G": 2048, "1.5G": 1536, "2097152.00K": 2048, "2097153.00K": 2049, "9989.50M": 9990}
        for token, mib in cases.items():
            with self.subTest(token=token):
                self.assertEqual(HSC.parse_swap_used_mib(swap(token)), (mib, token))
        for bad in ("vm.swapusage: total = 1M used = 2T", "used=2M", ""):
            with self.subTest(bad=bad), self.assertRaises(HSC.DataError):
                HSC.parse_swap_used_mib(bad)

    def test_vm_stat_follows_macvm_ctl(self) -> None:
        self.assertEqual(HSC.parse_vm_stat(vm_stat(free=4241, inactive=1335016, speculative=16843)), (4096, 4241, 16843, 1335016))
        self.assertEqual(HSC.parse_vm_stat(vm_stat(free=10, inactive=20, page=16384))[0], 16384)
        repeated = vm_stat(free=10, inactive=20) + "Pages free:  99.\n"
        self.assertEqual(HSC.parse_vm_stat(repeated)[1], 99, "a repeated row wins, as in macvm_ctl's awk")
        for bad in ("Pages free: 1.\n", vm_stat(free=10, inactive=20).replace("page size of 4096", "page size of 0")):
            with self.subTest(bad=bad[:40]), self.assertRaises(HSC.DataError):
                HSC.parse_vm_stat(bad)


MACVM_STUB = """\
#!/bin/bash
case "${0##*/}" in
    vm_stat) cat "$STUB_VM_STAT" ;;
    sysctl) cat "$STUB_SWAP" ;;
    pgrep)
        case "$2" in
            com.docker.backend) [ -n "${STUB_BACKEND:-}" ] && { echo 682; exit 0; } ;;
        esac
        exit 1
        ;;
esac
"""


class MacvmParityTest(unittest.TestCase):
    """G-MEM must reach the same verdict as util/macvm_ctl.bash status on the same output."""

    CASES = [
        ("plenty", vm_stat(free=2000000, inactive=1000000), "0.00M", False),
        ("one MiB short", vm_stat(free=2621184, inactive=0), "0.00M", False),
        ("exactly enough", vm_stat(free=2621440, inactive=0), "0.00M", False),
        ("speculative counts", vm_stat(free=2621000, inactive=0, speculative=440), "0.00M", False),
        ("arm64 pages", vm_stat(free=655360, inactive=0, page=16384), "0.00M", False),
        ("swap at the limit", vm_stat(free=2000000, inactive=1000000), "2048.00M", False),
        ("swap just over", vm_stat(free=2000000, inactive=1000000), "2048.01M", False),
        ("swap in G", vm_stat(free=2000000, inactive=1000000), "2.00G", False),
        ("swap in K, over", vm_stat(free=2000000, inactive=1000000), "2097153.00K", False),
        ("turing 2026-10-20", vm_stat(free=4241, inactive=1335016, speculative=16843), "9989.50M", True),
    ]

    def macvm_verdicts(self, tmp: Path, vm_text: str, used: str, docker: bool) -> dict[str, str]:
        stub = tmp / "stub"
        stub.write_text(MACVM_STUB, encoding="utf-8")
        stub.chmod(0o755)
        for name in ("vm_stat", "sysctl", "pgrep"):
            target = tmp / name
            if not target.exists():
                os.symlink(stub, target)
        (tmp / "vm_stat.txt").write_text(vm_text, encoding="utf-8")
        (tmp / "swap.txt").write_text(swap(used), encoding="utf-8")
        env = RedactedEnv(
            {k: v for k, v in os.environ.items() if k not in ("VBOXMANAGE", "VM_STAT", "SYSCTL", "PGREP", "POLL_INTERVAL")},
            VBOXMANAGE=str(tmp / "no-vboxmanage"),
            VM_STAT=str(tmp / "vm_stat"),
            SYSCTL=str(tmp / "sysctl"),
            PGREP=str(tmp / "pgrep"),
            STUB_VM_STAT=str(tmp / "vm_stat.txt"),
            STUB_SWAP=str(tmp / "swap.txt"),
        )
        if docker:
            env["STUB_BACKEND"] = "1"
        proc = subprocess.run(["/bin/bash", str(MACVM_CTL), "status"], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 2, "VirtualBox is absent, so status exits 2 after printing the gate")
        verdicts = {m.group(2): m.group(1) for m in re.finditer(r"(?m)^\s+(PASS|FAIL|UNKNOWN)\s+(memory|swap|docker):", proc.stdout)}
        self.assertEqual(set(verdicts), {"memory", "swap", "docker"}, proc.stdout)
        return verdicts

    def test_g_mem_matches_macvm_ctl_status(self) -> None:
        expected = green_expected()
        for name, vm_text, used, docker in self.CASES:
            with self.subTest(name), tempfile.TemporaryDirectory() as raw:
                tmp = Path(raw)
                want = self.macvm_verdicts(tmp, vm_text, used, docker)
                probe = green_probe()
                probe["memory"]["vm_stat"] = cap(vm_text)
                probe["memory"]["swapusage"] = cap(swap(used))
                probe["memory"]["docker"][0]["pgrep"] = cap("682\n") if docker else cap("", rc=1)
                probe["vm"]["showvminfo"] = cap(found=False, argv=("VBoxManage",))
                ctx = HSC.Context(host="testhost", expected=HSC.validate_expected(copy.deepcopy(expected), "test"), record_base=tmp, probe=probe)
                have = {c.id: c.status.upper() for c in HSC.gate_mem(ctx)}
                self.assertEqual(have, want)


class ProbeContractTest(unittest.TestCase):
    """The CLI: the check runs the probe it ships with, or a stand-in, and passes what the gates need."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.expected_path = self.tmp / "repo" / "conf" / "hosts" / "testhost" / "expected.yaml"
        self.expected_path.parent.mkdir(parents=True)
        self.expected_path.write_text(yaml.safe_dump(green_expected(), sort_keys=False), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str, env: RedactedEnv) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT_PATH), "--expected", str(self.expected_path), *args], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def stand_in(self, body: str) -> RedactedEnv:
        probe = self.tmp / "probe.bash"
        probe.write_text(body, encoding="utf-8")
        (self.tmp / "doc.json").write_text(json.dumps(green_probe()), encoding="utf-8")
        return RedactedEnv(os.environ, HOST_STATE_PROBE=str(probe), HOST_STATE_BASH="/bin/bash", ARGV_LOG=str(self.tmp / "argv.log"), DOC=str(self.tmp / "doc.json"))

    def test_the_probe_is_asked_for_exactly_what_the_gates_read(self) -> None:
        env = self.stand_in('printf "%s\\n" "$@" > "$ARGV_LOG"\ncat "$DOC"\n')
        proc = self.run_cli("--section", "tools", "--section", "mem", "--root", str(self.tmp / "jroot"), "--check", env=env)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        argv = (self.tmp / "argv.log").read_text(encoding="utf-8").splitlines()
        want = ["--json", "--root", str(self.tmp / "jroot"), "--vm", "juniper-macvm", "--section", "hardware", "--section", "memory", "--section", "vm", "--section", "tools"]
        self.assertEqual(argv, want + [x for t in TOOLS for x in ("--tool", t)])
        self.assertIn("readiness: 2 of 2 gates pass", proc.stdout)

    def test_a_failing_or_garbled_probe_exits_2(self) -> None:
        for body, part in (('echo "ERROR: boom" >&2\nexit 2\n', "the probe exited 2: ERROR: boom"), ("echo hello\n", "is not the probe's JSON")):
            with self.subTest(part=part):
                proc = self.run_cli("--check", env=self.stand_in(body))
                self.assertEqual((proc.returncode, proc.stdout), (2, ""))
                self.assertIn(part, proc.stderr)
        env = self.stand_in('cat "$DOC"\n')
        env["HOST_STATE_BASH"] = str(self.tmp / "no-bash")
        proc = self.run_cli(env=env)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not found (set HOST_STATE_BASH)", proc.stderr)

    def test_the_real_probe_feeds_the_check(self) -> None:
        harness = ProbeHarness(self.tmp / "harness")
        env = harness.env(HOST_STATE_BASH="/bin/bash")
        env.pop("HOST_STATE_PROBE", None)
        proc = self.run_cli("--section", "G-SEC", "--section", "G-MEM", "--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["probe"]["source"], "run")
        self.assertEqual(result["probe"]["path"], str(PROBE_PATH))
        self.assertEqual(result["probe"]["node"], "turing.midcoip.net")
        verdicts = {g["id"]: {c["id"]: c["status"] for c in g["conditions"]} for g in result["gates"]}
        self.assertEqual(
            verdicts,
            {
                "G-SEC": {"sip": "fail", "authenticated-root": "pass", "firewall": "fail", "filevault": "pass", "key-exports": "pass", "key-modes": "pass"},
                "G-MEM": {"memory": "fail", "swap": "fail", "docker": "fail"},
            },
        )
        self.assertEqual(harness.trip_log.read_text(encoding="utf-8"), "")
        self.assertEqual(self.run_cli("--section", "G-SEC", "--check", env=env).returncode, 1)


class ThisCheckoutTest(unittest.TestCase):
    """The committed turing file, against the plan and the files it must agree with."""

    expected: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.expected = HSC.load_expected(TURING_EXPECTED)

    def test_it_validates_and_describes_turing(self) -> None:
        self.assertEqual(self.expected["host"], "turing")
        self.assertEqual(self.expected["identity"], {"arch": "x86_64", "memsize_bytes": 17179869184, "physicalcpu": 6, "ncpu": 12})
        self.assertEqual(self.expected["vm"], {"name": "juniper-macvm", "mem_gib": 6, "vcpus": 4})

    def test_r_g1_the_primer_sizing_is_refused_on_this_file(self) -> None:
        raw = yaml.safe_load(TURING_EXPECTED.read_text(encoding="utf-8"))
        raw["vm"]["mem_gib"] = 44
        with self.assertRaisesRegex(HSC.ExpectedError, "R-G1, the X2 class"):
            HSC.validate_expected(raw, "turing")
        raw["vm"]["mem_gib"] = 6
        raw["vm"]["vcpus"] = 8
        with self.assertRaisesRegex(HSC.ExpectedError, "8 vCPU on 6 cores"):
            HSC.validate_expected(raw, "turing")

    def test_the_vm_and_g_mem_agree_with_macvm_ctl(self) -> None:
        text = MACVM_CTL.read_text(encoding="utf-8")

        def default(name: str) -> str:
            match = re.search(rf'(?m)^{name}="?([^"\n]+)"?$', text)
            self.assertIsNotNone(match, name)
            return match.group(1)

        self.assertEqual(self.expected["vm"]["name"], default("VM"))
        self.assertEqual(self.expected["vm"]["mem_gib"], int(default("VM_MEM_GIB")))
        self.assertEqual(self.expected["gates"]["G-MEM"]["reserve_gib"], int(default("RESERVE_GIB")))
        self.assertEqual(self.expected["gates"]["G-MEM"]["max_swap_gib"], int(default("MAX_SWAP_GIB")))

    def test_g_tools_is_the_host_tools_file(self) -> None:
        text = (REPO_ROOT / "conf" / "hosts" / "turing" / "hosttools-environment.yml").read_text(encoding="utf-8")
        linked = re.search(r"for t in ([^;]+); do", text)
        self.assertIsNotNone(linked)
        listed = self.expected["gates"]["G-TOOLS"]["local_bin"]
        self.assertLessEqual(set(linked.group(1).split()), set(listed))
        for tool in listed:
            self.assertIn(tool, text)
        self.assertNotIn("pinentry-mac", listed, "pinentry-mac is the Homebrew exception; G-SIGN covers it")
        for tool in ("markdownlint-cli2", "sops", "ykman"):
            self.assertIn(tool, listed)

    def test_g_env_is_juniperpython_plus_every_turing_env_spec(self) -> None:
        names = {"JuniperPython"}
        specs = sorted((REPO_ROOT / "conf" / "hosts" / "turing" / "conda-envs").glob("*.yml")) + [REPO_ROOT / "conf" / "hosts" / "turing" / "hosttools-environment.yml"]
        for spec in specs:
            match = re.search(r"(?m)^name: (\S+)$", spec.read_text(encoding="utf-8"))
            self.assertIsNotNone(match, spec)
            names.add(match.group(1))
        self.assertEqual(set(self.expected["gates"]["G-ENV"]["conda_envs"]), names)

    def test_g_net_names_the_dongle_of_the_plan(self) -> None:
        net = self.expected["gates"]["G-NET"]
        self.assertEqual((net["interface"], net["mac"], net["media"], net["min_mbps"]), ("en7", "00:e0:4c:68:06:b1", "1000baseT", 800))


if __name__ == "__main__":
    unittest.main()
