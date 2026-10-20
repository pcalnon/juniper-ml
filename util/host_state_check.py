#!/usr/bin/env python3
"""Evaluate the turing bring-up host gates against this host's state probe (task G1, plan §9.3).

Project: juniper-ml
Sub-Project: host tooling (turing bring-up)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: permanent utility
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1; the gates in §9.3, as
         revised by §16.3 E-D6 and §19.2 E-G-SIGN; regression R-G1; integration I-G1); util/host_state_probe.bash,
         the collector; conf/hosts/<host>/expected.yaml, the target; tests/test_host_state_check.py

Why this exists
---------------
The bring-up plan judges turing by ten host gates (§9.3). Seven of them are measurable on the host
without a credential, and this script evaluates those seven. util/host_state_probe.bash collects raw
command output, read-only. This script parses it and compares it with the host's
``conf/hosts/<host>/expected.yaml``. The probe holds no judgement, so a saved probe (``--probe-json``) can
be evaluated again later or against a revised target. The script is Python so that it needs no ``yq``
(plan §6, task G1).

The gates
---------
Each gate is a list of conditions. A condition is PASS, FAIL, UNKNOWN (its input could not be measured),
OPERATOR (owner-run; this script cannot measure it) or INFO (reported, never judged). A gate FAILs if any
condition fails. Otherwise it is UNKNOWN if any condition is unknown, OPERATOR if any condition is
owner-run, and PASS when every condition passes.

G-ALIAS (probe section ``git``)
    ``alias-check``: util/git_remote_alias_check.py (task G2) exits 0. That covers 10/10 alias-form
    origins, each key at mode 600, and ``AddKeysToAgent no``.
G-SIGN (``signing``), as §19.2 E-G-SIGN revises it
    ``git-config``: util/configure_commit_signing.py --check (signing plan K2) exits 0. It judges every
    checkout, with an agent session's D11 override set aside.
    ``pinentry``, ``agent-socket``, ``external-cache``: these lines of util/headless_signing_preflight.bash
    (task B7) PASS. Its ``signing-key`` and ``commit-gpgsign`` lines are not judged here. ``git-config``
    covers both per checkout, and ``commit-gpgsign`` fails by construction in an agent session (D11).
    ``i-sign``: OPERATOR. A signed commit verifies from every commit path (signing plan I-SIGN T1-T5,
    bring-up B5).
G-SEC (``security``)
    ``sip`` and ``authenticated-root``: csrutil reports each enabled. ``filevault``: FileVault is On.
    ``firewall``: the application firewall's State is 1 or more. ``key-material``: no name under ~/.ssh or
    ~/.gnupg matches ``*.asc`` or ``*recovery*``. ``key-perms``: no file under ~/.ssh, other than
    ``*.pub`` and ``known_hosts*``, is open to group or others. Stealth mode is INFO (task C2).
G-TOOLS (``toolchain``), as §16.3 E-D6 revises it
    ``local-bin``: each ``tools.local_bin`` entry resolves to ``~/.local/bin/<tool>``, as the PATH lookup
    ``command -v`` makes. ``homebrew``: each ``tools.homebrew`` entry resolves to its path (D6's one
    Homebrew exception). ``kubectl``: the client's minor is within ``max_skew`` of ``cluster_minor``; a
    missing kubectl fails.
G-ENV (``env``)
    ``conda-envs``: ``conda env list`` names every ``conda_envs`` entry. ``parent-agents-md``: the parent
    ``<root>/AGENTS.md`` exists and its sha256 equals ``parent_agents_md.sha256``. A null hash fails,
    because nothing has been recorded to match yet (task E4).
G-NET (``network``)
    ``link``: the ``bridge_nic`` device exists, has the expected MAC, and is active with ``media`` in its
    media line. ``address``: its IPv4 address equals ``reserved_ip``. A null address fails, because
    task A6 has not recorded one. ``throughput``: OPERATOR, iperf3 to yamaguchi.
G-MEM (``hardware``, ``memory``, ``docker``, ``hypervisor``)
    The VM size is the larger of ``vm.memory_gib`` and the VM's configured memory, read from VirtualBox
    once the VM exists. That is util/macvm_ctl.bash's rule.
    ``vm-fits`` (regression R-G1, the X2 class): the VM size plus ``reserve_gib`` is at most hw.memsize,
    and ``vm.vcpus`` is at most hw.physicalcpu. The primer's 44 GiB VM fails it on a 16 GiB machine.
    ``memory``, ``swap`` and ``docker`` are util/macvm_ctl.bash's three G-MEM conditions, with the same
    arithmetic and the same text: free + speculative + inactive pages, rounded down to MiB, of at least
    the VM size plus the reserve; swap used, rounded up to MiB, of at most ``max_swap_gib``; no
    com.docker.backend, "Docker Desktop" or Docker process.

Not evaluated here: G-AUTH (the owner-run auth matrix), G-PATH (util/home_path_literal_check.py, in
pre-commit and CI) and G-AGENT (the agent contract tests). The report names them.

Usage
-----
    python3 util/host_state_check.py [--check] [--json] [--section GATE]... [--host NAME] [--expected FILE]
        [--probe-json FILE | --probe SCRIPT [--root DIR] [--timeout SECONDS]]

``--check``
    Gate mode (plan §9.2, I-G1): exit 1 when a gate fails, 2 when one is UNKNOWN. Without it the script
    reports and exits 0.
``--json``
    Print one JSON object instead of the report (schema below).
``--section GATE``
    Evaluate only this gate; repeatable. ``G-MEM``, ``g-mem`` and ``mem`` all name G-MEM. Each section of
    the report is one gate, and the probe collects only the sections the chosen gates read.
``--host NAME``
    The host whose expected.yaml applies. Default: the probe's host, or this machine's short host name
    when the script runs the probe.
``--expected FILE``
    Default: ``conf/hosts/<host>/expected.yaml`` in this checkout.
``--probe-json FILE``
    Evaluate a saved ``host_state_probe.bash --json`` document (``-`` reads stdin) instead of running the
    probe.
``--probe SCRIPT``, ``--root DIR``, ``--timeout SECONDS``
    The probe to run (default: util/host_state_probe.bash next to this script), its Juniper root, and its
    per-capture limit (default 60). The probe also gets ``--tool`` for every tool expected.yaml names and
    ``--vm`` for its VM.

Output
------
A header names the host, the expected file and the probe. Then each gate prints as
``<gate>  <STATUS>  <target>``, followed by one line per condition, ``<STATUS>  <name>  <message>``, with
any detail lines indented below it. A readiness line closes the report.

Exit codes
----------
0  the report printed; with ``--check``, every evaluated gate is PASS or OPERATOR.
1  ``--check`` only: at least one gate FAILs and none is UNKNOWN.
2  usage or environment. That covers a bad argument; a missing or malformed expected.yaml; no PyYAML;
   a probe that would not run or printed no schema-1 JSON; and a probe from another host than
   expected.yaml describes. With ``--check``, a gate that is UNKNOWN exits 2 as well, so 2 wins over 1.
   Usage and environment errors print to stderr only.

Environment
-----------
``PROBE_BASH``  the bash that runs the probe (default ``bash``; tests use ``/bin/bash``, bash 3.2 on macOS)

JSON schema (``--json``)
------------------------
``schema`` is bumped on any incompatible change.

    {
      "schema": 1,
      "tool": "util/host_state_check.py",
      "mode": "report" | "check",
      "host": str,
      "expected": str,                    # the expected.yaml evaluated
      "probe": {"source": "run" | "file", "path": str, "host": str, "collected_at": str,
                "bash_version": str},
      "gates": [{"gate": "G-ALIAS" | ..., "status": STATUS, "target": str, "sections": [str],
                 "conditions": [{"name": str, "status": STATUS, "message": str, "detail": [str]}]}],
      "readiness": {"evaluated": int, "pass": int, "operator": int, "fail": int, "unknown": int},
      "not_evaluated": {"G-AUTH": str, "G-PATH": str, "G-AGENT": str},
      "ok": bool,                         # exit_code == 0
      "exit_code": 0 | 1 | 2,
      "summary": str                      # the readiness line
    }

STATUS is "pass", "fail", "unknown" or "operator"; a condition may also be "info".
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import socket
import subprocess  # nosec B404 -- runs the probe with a fixed argv, never a shell
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROBE = REPO_ROOT / "util" / "host_state_probe.bash"
SCHEMA = 1
PROBE_SCHEMA = 1
EXPECTED_SCHEMA = 1
MIB = 1048576
LABEL = {"pass": "PASS", "fail": "FAIL", "unknown": "UNKNOWN", "operator": "OPERATOR", "info": "INFO"}
SECTION_ORDER = ("hardware", "memory", "docker", "hypervisor", "disk", "power", "network", "security", "toolchain", "env", "git", "signing")
DOCKER_NAMES = ("com.docker.backend", "Docker Desktop", "Docker")
PREFLIGHT_JUDGED = ("pinentry", "agent-socket", "external-cache")
NOT_EVALUATED = {
    "G-AUTH": "the owner-run auth matrix: ssh -T, ls-remote and push --dry-run per repo (plan §14.1, task A3)",
    "G-PATH": "util/home_path_literal_check.py, in pre-commit and ci.yml (task G5)",
    "G-AGENT": "the agent frontmatter and contract tests (tasks H2, H3)",
}


class EnvError(Exception):
    """A usage or environment problem: exit 2."""


@dataclass(frozen=True)
class GateSpec:
    gate: str
    key: str
    target: str
    sections: tuple[str, ...]


GATES = (
    GateSpec("G-ALIAS", "alias", "10/10 alias-form origins; keys at mode 600; AddKeysToAgent no", ("git",)),
    GateSpec("G-SIGN", "sign", "every checkout signs with the pinned key; GUI pinentry; agent socket; no-allow-external-cache; I-SIGN verified", ("signing",)),
    GateSpec("G-SEC", "sec", "SIP and authenticated root enabled; FileVault on; firewall on; no *.asc or recovery file; no key open to group or others", ("security",)),
    GateSpec("G-TOOLS", "tools", "each host tool resolves from ~/.local/bin (E-D6); kubectl within one minor of the cluster", ("toolchain",)),
    GateSpec("G-ENV", "env", "conda envs include the AGENTS.md list; the parent AGENTS.md hash matches", ("env",)),
    GateSpec("G-NET", "net", "the bridge NIC at 1000baseT with the reserved address; iperf3 throughput to yamaguchi", ("network",)),
    GateSpec("G-MEM", "mem", "the VM fits; free + inactive >= VM + reserve; swap used <= limit; Docker Desktop not running", ("hardware", "memory", "docker", "hypervisor")),
)
GATE_BY_KEY = {spec.key: spec for spec in GATES}


@dataclass
class Condition:
    name: str
    status: str
    message: str
    detail: list[str] = field(default_factory=list)


@dataclass
class GateResult:
    spec: GateSpec
    conditions: list[Condition]

    @property
    def status(self) -> str:
        judged = [c.status for c in self.conditions if c.status != "info"]
        for status in ("fail", "unknown", "operator"):
            if status in judged:
                return status
        return "pass"


# ---------------------------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------------------------
def gate_spec(name: str) -> GateSpec:
    key = name.strip().lower()
    key = key[2:] if key.startswith("g-") else key
    if key not in GATE_BY_KEY:
        raise argparse.ArgumentTypeError(f"unknown gate {name!r} (expected one of: {', '.join(spec.gate for spec in GATES)})")
    return GATE_BY_KEY[key]


def short_host(name: str) -> str:
    return name.strip().split(".")[0].lower()


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # PyYAML; imported here so --help works without it
    except ImportError:
        raise EnvError("PyYAML is required to read expected.yaml (pip install pyyaml)") from None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise EnvError(f"{path} not found") from None
    except (OSError, yaml.YAMLError) as exc:
        raise EnvError(f"{path} is unreadable: {exc}") from exc


def _need(doc: dict, key: str, kind: type | tuple, where: str, *, nullable: bool = False) -> Any:
    value = doc.get(key)
    if value is None and nullable:
        return None
    if not isinstance(value, kind) or isinstance(value, bool) and kind is not bool:
        raise EnvError(f"{where}.{key} is missing or not {getattr(kind, '__name__', kind)}")
    return value


def load_expected(path: Path) -> dict:
    """Load and validate expected.yaml, schema 1. An unknown key is an error, so a typo cannot pass silently."""
    doc = load_yaml(path)
    where = str(path)
    if not isinstance(doc, dict) or doc.get("schema") != EXPECTED_SCHEMA:
        raise EnvError(f"{where} is not an expected.yaml of schema {EXPECTED_SCHEMA}")
    allowed = {"schema", "host", "vm", "tools", "conda_envs", "parent_agents_md", "network"}
    if set(doc) - allowed:
        raise EnvError(f"{where}: unknown keys {sorted(set(doc) - allowed)}")
    _need(doc, "host", str, where)
    vm = _need(doc, "vm", dict, where)
    _need(vm, "name", str, where + ".vm")
    for key in ("memory_gib", "vcpus", "reserve_gib", "max_swap_gib"):
        if not isinstance(vm.get(key), int) or isinstance(vm.get(key), bool) or vm[key] < (1 if key in ("memory_gib", "vcpus") else 0):
            raise EnvError(f"{where}.vm.{key} is missing or not a whole number")
    tools = _need(doc, "tools", dict, where)
    local_bin = _need(tools, "local_bin", list, where + ".tools")
    homebrew = _need(tools, "homebrew", dict, where + ".tools")
    kubectl = _need(tools, "kubectl", dict, where + ".tools")
    names = list(local_bin) + list(homebrew)
    if not all(isinstance(t, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", t) for t in names):
        raise EnvError(f"{where}.tools names a tool that is not a plain command name")
    if not all(isinstance(p, str) and p.startswith("/") for p in homebrew.values()):
        raise EnvError(f"{where}.tools.homebrew maps a tool to a path that is not absolute")
    if not re.fullmatch(r"\d+\.\d+", str(_need(kubectl, "cluster_minor", str, where + ".tools.kubectl"))):
        raise EnvError(f"{where}.tools.kubectl.cluster_minor is not MAJOR.MINOR")
    _need(kubectl, "max_skew", int, where + ".tools.kubectl")
    envs = _need(doc, "conda_envs", list, where)
    if not all(isinstance(e, str) and e for e in envs):
        raise EnvError(f"{where}.conda_envs holds a name that is not a string")
    sha = _need(_need(doc, "parent_agents_md", dict, where), "sha256", str, where + ".parent_agents_md", nullable=True)
    if sha is not None and not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise EnvError(f"{where}.parent_agents_md.sha256 is not 64 lowercase hex digits")
    net = _need(doc, "network", dict, where)
    nic = _need(net, "bridge_nic", dict, where + ".network")
    for key in ("device", "mac", "media"):
        _need(nic, key, str, where + ".network.bridge_nic")
    ip = _need(net, "reserved_ip", str, where + ".network", nullable=True)
    if ip is not None and not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip):
        raise EnvError(f"{where}.network.reserved_ip is not an IPv4 address")
    _need(net, "iperf3_min_mbps", int, where + ".network")
    return doc


def validate_probe(doc: Any, origin: str) -> dict:
    if not isinstance(doc, dict) or doc.get("schema") != PROBE_SCHEMA or not isinstance(doc.get("captures"), list):
        raise EnvError(f"{origin} is not a host_state_probe.bash --json document of schema {PROBE_SCHEMA}")
    for cap in doc["captures"]:
        ok = isinstance(cap, dict) and all(isinstance(cap.get(k), str) for k in ("section", "name", "command", "stdout", "stderr"))
        ok = ok and isinstance(cap.get("timed_out"), bool) and (cap.get("exit_code") is None or isinstance(cap.get("exit_code"), int))
        if not ok or not (cap.get("skipped") is None or isinstance(cap.get("skipped"), str)):
            raise EnvError(f"{origin} holds a malformed capture: {str(cap)[:200]}")
    return doc


def read_probe_json(arg: str) -> dict:
    try:
        data = sys.stdin.buffer.read() if arg == "-" else Path(arg).read_bytes()
    except OSError as exc:
        raise EnvError(f"cannot read the probe JSON {arg}: {exc}") from exc
    try:
        doc = json.loads(data.decode("utf-8", "replace"))
    except ValueError as exc:
        raise EnvError(f"{arg} is not JSON: {exc}") from exc
    return validate_probe(doc, arg)


def run_probe(probe: Path, sections: list[str], expected: dict, root: str | None, timeout: int) -> dict:
    argv = [os.environ.get("PROBE_BASH", "bash"), str(probe), "--json", "--timeout", str(timeout), "--vm", expected["vm"]["name"]]
    for section in sections:
        argv += ["--section", section]
    for tool in list(expected["tools"]["local_bin"]) + list(expected["tools"]["homebrew"]):
        argv += ["--tool", tool]
    if root is not None:
        argv += ["--root", root]
    try:
        proc = subprocess.run(argv, capture_output=True, check=False, timeout=max(600, 20 * timeout))  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EnvError(f"cannot run the probe {probe}: {exc}") from exc
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        raise EnvError(f"the probe {probe} exited {proc.returncode}: {err[0] if err else '(no stderr)'}")
    try:
        doc = json.loads(proc.stdout.decode("utf-8", "replace"))
    except ValueError as exc:
        raise EnvError(f"the probe {probe} printed no JSON: {exc}") from exc
    return validate_probe(doc, str(probe))


# ---------------------------------------------------------------------------------------------
# Capture helpers
# ---------------------------------------------------------------------------------------------
class Probe:
    def __init__(self, doc: dict) -> None:
        self.doc = doc
        self.home = doc.get("home") or ""
        self._caps = {(c["section"], c["name"]): c for c in doc["captures"]}

    def capture(self, section: str, name: str) -> dict | None:
        return self._caps.get((section, name))


def first_line(text: str) -> str:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return lines[0].strip() if lines else "(no output)"


def unmeasured(cap: dict | None, what: str, section: str) -> str | None:
    """Why ``cap`` holds no measurement, or None when its command ran to the end (whatever its exit code)."""
    if cap is None:
        return f"the probe holds no {what} capture; collect section '{section}'"
    if cap["skipped"] is not None:
        return f"{what}: skipped: {cap['skipped']}"
    if cap["timed_out"]:
        return f"{what}: timed out: {cap['command']}"
    if cap["exit_code"] in (126, 127):
        return f"{what}: cannot run {cap['command']}: {first_line(cap['stderr'])}"
    return None


def tilde(path: str, home: str) -> str:
    return "~" + path[len(home) :] if home and (path == home or path.startswith(home.rstrip("/") + "/")) else path


def parse_json(text: str) -> dict | None:
    try:
        doc = json.loads(text)
    except ValueError:
        return None
    return doc if isinstance(doc, dict) else None


def schema1_tool_condition(cap: dict | None, name: str, what: str, section: str) -> Condition:
    """One condition from a sibling tool's --json verdict (schema 1 with exit_code, ok and summary)."""
    why = unmeasured(cap, what, section)
    if why:
        return Condition(name, "unknown", why)
    doc = parse_json(cap["stdout"])
    if doc is None or doc.get("schema") != 1:
        return Condition(name, "unknown", f"{what} printed no schema-1 JSON (exit {cap['exit_code']}): {first_line(cap['stderr'])}")
    summary = re.sub(r"^summary:\s*", "", str(doc.get("summary", "")).strip())
    if doc.get("exit_code") == 0 and doc.get("ok") is True:
        return Condition(name, "pass", f"{what}: {summary}")
    if doc.get("exit_code") != 1:
        return Condition(name, "unknown", f"{what} could not evaluate (exit {doc.get('exit_code')}): {summary or first_line(cap['stderr'])}")
    detail = []
    if isinstance(doc.get("repos"), list):  # git_remote_alias_check.py
        for repo in doc["repos"]:
            for check, verdict in (repo.get("checks") or {}).items():
                if isinstance(verdict, dict) and verdict.get("status") in ("fail", "error"):
                    fix = f" -- fix: {verdict['remediation']}" if verdict.get("remediation") else ""
                    detail.append(f"{repo.get('repo')} {check}: {verdict.get('message')}{fix}")
    for check in doc.get("checks") or []:  # configure_commit_signing.py
        if isinstance(check, dict) and check.get("status") in ("fail", "error"):
            fix = f" -- fix: {check['remediation']}" if check.get("remediation") else ""
            detail.append(f"{check.get('id')}: {check.get('message')}{fix}")
    return Condition(name, "fail", f"{what}: {summary}", detail)


# ---------------------------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------------------------
def gate_alias(probe: Probe, expected: dict) -> list[Condition]:
    return [schema1_tool_condition(probe.capture("git", "git-remote-alias-check"), "alias-check", "git_remote_alias_check.py", "git")]


def gate_sign(probe: Probe, expected: dict) -> list[Condition]:
    conditions = [schema1_tool_condition(probe.capture("signing", "configure-commit-signing"), "git-config", "configure_commit_signing.py --check", "signing")]
    cap = probe.capture("signing", "headless-signing-preflight")
    why = unmeasured(cap, "headless_signing_preflight.bash", "signing")
    lines = {}
    if cap is not None and why is None:
        for line in cap["stdout"].splitlines():
            match = re.match(r"^(PASS|FAIL|INFO)\s+(\S+)\s+(.*)$", line)
            if match:
                lines.setdefault(match.group(2), (match.group(1), match.group(3).strip()))
    for name in PREFLIGHT_JUDGED:
        if why:
            conditions.append(Condition(name, "unknown", why))
        elif name not in lines:
            conditions.append(Condition(name, "unknown", f"the preflight printed no '{name}' line (exit {cap['exit_code']}): {first_line(cap['stderr'] or cap['stdout'])}"))
        else:
            status, text = lines[name]
            conditions.append(Condition(name, "pass" if status == "PASS" else "fail", text))
    conditions.append(Condition("i-sign", "operator", "a signed commit verifies from the terminal, both Source Control views and both integrated terminals (signing plan I-SIGN T1-T5, bring-up B5): owner-run, after B2 and B3"))
    return conditions


def _security_text(probe: Probe, name: str) -> tuple[str | None, str | None]:
    """(stdout, None) when the capture ran and exited 0, else (None, why it holds no measurement)."""
    cap = probe.capture("security", name)
    why = unmeasured(cap, name, "security")
    if why:
        return None, why
    if cap["exit_code"] != 0:
        return None, f"{cap['command']} exited {cap['exit_code']}: {first_line(cap['stderr'])}"
    return cap["stdout"], None


def _name_list(probe: Probe, cname: str, label: str, clean: str, absent: str, fix: str) -> Condition:
    cap = probe.capture("security", cname)
    if cap is not None and cap["skipped"] is not None and cap["skipped"].startswith("absent:"):
        return Condition(label, "pass", absent)
    why = unmeasured(cap, cname, "security")
    if why:
        return Condition(label, "unknown", why)
    names = [tilde(line.strip(), probe.home) for line in cap["stdout"].splitlines() if line.strip()]
    if names:
        return Condition(label, "fail", f"{len(names)} found; {fix}", names)
    if cap["exit_code"] != 0:
        return Condition(label, "unknown", f"{cap['command']} exited {cap['exit_code']}: {first_line(cap['stderr'])}")
    return Condition(label, "pass", clean)


def gate_sec(probe: Probe, expected: dict) -> list[Condition]:
    conditions = []
    text, why = _security_text(probe, "csrutil-status")
    match = re.search(r"System Integrity Protection status:\s*(.+?)\.?\s*$", text or "", re.M)
    if why or not match:
        conditions.append(Condition("sip", "unknown", why or f"no SIP status in: {first_line(text or '')}"))
    else:
        value = match.group(1)
        conditions.append(Condition("sip", "pass" if value == "enabled" else "fail", f"SIP is {value}" + ("" if value == "enabled" else "; csrutil enable from recoveryOS (C1)")))
    text, why = _security_text(probe, "csrutil-authenticated-root")
    match = re.search(r"Authenticated Root status:\s*(\S+?)\.?\s*$", text or "", re.M)
    if why or not match:
        conditions.append(Condition("authenticated-root", "unknown", why or f"no authenticated-root status in: {first_line(text or '')}"))
    else:
        value = match.group(1)
        conditions.append(Condition("authenticated-root", "pass" if value == "enabled" else "fail", f"authenticated root is {value}" + ("" if value == "enabled" else " (C1)")))
    text, why = _security_text(probe, "fdesetup-status")
    match = re.search(r"^FileVault is (On|Off)\b", text or "", re.M)
    if why or not match:
        conditions.append(Condition("filevault", "unknown", why or f"no FileVault status in: {first_line(text or '')}"))
    else:
        conditions.append(Condition("filevault", "pass" if match.group(1) == "On" else "fail", f"FileVault is {match.group(1)}"))
    text, why = _security_text(probe, "firewall-globalstate")
    match = re.search(r"State = (\d+)", text or "")
    if why or not match:
        conditions.append(Condition("firewall", "unknown", why or f"no firewall State in: {first_line(text or '')}"))
    elif int(match.group(1)) >= 1:
        conditions.append(Condition("firewall", "pass", f"the application firewall is on (State = {match.group(1)})"))
    else:
        conditions.append(Condition("firewall", "fail", "the application firewall is off (State = 0); turn it on with stealth mode (C2)"))
    conditions.append(
        _name_list(
            probe,
            "key-material-names",
            "key-material",
            "no *.asc or *recovery* name under ~/.ssh or ~/.gnupg",
            "neither ~/.ssh nor ~/.gnupg exists",
            "back these up offline, test-decrypt, then delete them (C3, decision D4)",
        )
    )
    conditions.append(
        _name_list(
            probe,
            "ssh-loose-files",
            "key-perms",
            "no file under ~/.ssh, other than *.pub and known_hosts*, is open to group or others",
            "~/.ssh does not exist",
            "chmod 600 each of them (C4)",
        )
    )
    text, why = _security_text(probe, "firewall-stealthmode")
    match = re.search(r"stealth mode is (on|off)", text or "", re.I)
    if match:
        conditions.append(Condition("stealth-mode", "info", f"stealth mode is {match.group(1).lower()} (C2 turns it on)"))
    return conditions


def _resolved(probe: Probe, tool: str) -> tuple[str | None, bool]:
    """(the path the PATH lookup found or None, whether the probe looked the tool up at all)."""
    cap = probe.capture("toolchain", f"command-v:{tool}")
    if cap is None:
        return None, False
    path = cap["stdout"].strip()
    return (path if cap["exit_code"] == 0 and path else None), True


def gate_tools(probe: Probe, expected: dict) -> list[Condition]:
    conditions = []
    local_dir = os.path.normpath(os.path.join(probe.home, ".local", "bin")) if probe.home else ""
    problems, missing_caps = [], []
    for tool in expected["tools"]["local_bin"]:
        path, looked = _resolved(probe, tool)
        want = os.path.join(local_dir, tool)
        if not looked:
            missing_caps.append(tool)
        elif path is None:
            problems.append(f"{tool}: not found on PATH")
        elif os.path.normpath(path) != want:
            problems.append(f"{tool}: resolves to {path}, not {tilde(want, probe.home)}")
    count = len(expected["tools"]["local_bin"])
    if missing_caps:
        conditions.append(Condition("local-bin", "unknown", f"the probe did not look up {', '.join(missing_caps)}; rerun it with --tool for each"))
    elif problems:
        conditions.append(Condition("local-bin", "fail", f"{len(problems)} of {count} tools do not resolve from ~/.local/bin (conf/hosts/turing/hosttools-environment.yml gives the recreate steps)", problems))
    else:
        conditions.append(Condition("local-bin", "pass", f"all {count} tools resolve from ~/.local/bin"))
    problems, missing_caps = [], []
    for tool, want in expected["tools"]["homebrew"].items():
        path, looked = _resolved(probe, tool)
        if not looked:
            missing_caps.append(tool)
        elif path != want:
            problems.append(f"{tool}: {'not found on PATH' if path is None else 'resolves to ' + path}, not {want}")
    if missing_caps:
        conditions.append(Condition("homebrew", "unknown", f"the probe did not look up {', '.join(missing_caps)}; rerun it with --tool for each"))
    elif problems:
        conditions.append(Condition("homebrew", "fail", "D6's Homebrew exception is not where B1 put it", problems))
    else:
        conditions.append(Condition("homebrew", "pass", ", ".join(f"{tool} -> {want}" for tool, want in expected["tools"]["homebrew"].items()) or "none expected"))
    conditions.append(_kubectl(probe, expected["tools"]["kubectl"]))
    return conditions


def _kubectl(probe: Probe, want: dict) -> Condition:
    cap = probe.capture("toolchain", "kubectl-version")
    cluster = want["cluster_minor"]
    if cap is not None and cap["skipped"] is None and not cap["timed_out"] and cap["exit_code"] in (126, 127):
        return Condition("kubectl", "fail", f"kubectl not found ({cap['command']}); D4 installs a {cluster}.x client")
    why = unmeasured(cap, "kubectl-version", "toolchain")
    if why:
        return Condition("kubectl", "unknown", why)
    doc = parse_json(cap["stdout"]) or {}
    client = doc.get("clientVersion") if isinstance(doc.get("clientVersion"), dict) else {}
    major = re.sub(r"\D", "", str(client.get("major", "")))
    minor = re.sub(r"\D", "", str(client.get("minor", "")))
    if cap["exit_code"] != 0 or not major or not minor:
        return Condition("kubectl", "unknown", f"no client version from {cap['command']} (exit {cap['exit_code']}): {first_line(cap['stderr'] or cap['stdout'])}")
    want_major, want_minor = (int(part) for part in cluster.split("."))
    version = client.get("gitVersion") or f"v{major}.{minor}"
    path, _ = _resolved(probe, "kubectl")
    where = f" at {path}" if path else ""
    skew = abs(int(minor) - want_minor)
    if int(major) == want_major and skew <= want["max_skew"]:
        return Condition("kubectl", "pass", f"kubectl {version}{where} is within {want['max_skew']} minor of the cluster's {cluster}")
    gap = f"{skew} minors {'behind' if int(minor) < want_minor else 'ahead of'}" if int(major) == want_major else "a different major version from"
    return Condition("kubectl", "fail", f"kubectl {version}{where} is {gap} the cluster's {cluster}; D4 installs {cluster}.x")


def gate_env(probe: Probe, expected: dict) -> list[Condition]:
    conditions = []
    cap = probe.capture("env", "conda-env-list")
    why = unmeasured(cap, "conda-env-list", "env")
    if why is None and cap is not None and cap["exit_code"] != 0:
        why = f"{cap['command']} exited {cap['exit_code']}: {first_line(cap['stderr'])}"
    if why:
        conditions.append(Condition("conda-envs", "unknown", why))
    else:
        names = set()
        for line in cap["stdout"].splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            tokens = line.split()
            if not line[0].isspace() and tokens[0] not in ("*", "+"):
                names.add(tokens[0])
            parent, base = os.path.split(tokens[-1].rstrip("/"))
            if os.path.basename(parent) == "envs" and base:
                names.add(base)
        want = expected["conda_envs"]
        missing = [name for name in want if name not in names]
        if missing:
            conditions.append(Condition("conda-envs", "fail", f"missing: {', '.join(missing)} (E2 creates them from conf/hosts/turing/conda-envs/)"))
        else:
            conditions.append(Condition("conda-envs", "pass", f"all {len(want)} present: {', '.join(want)}"))
    conditions.append(_parent_agents(probe, expected["parent_agents_md"]["sha256"]))
    return conditions


def _parent_agents(probe: Probe, want: str | None) -> Condition:
    cap = probe.capture("env", "parent-agents-md")
    if cap is not None and cap["skipped"] is not None and cap["skipped"].startswith("absent:"):
        return Condition("parent-agents-md", "fail", f"{cap['skipped']}; E4 copies yamaguchi's file and records its sha256 in expected.yaml")
    why = unmeasured(cap, "parent-agents-md", "env")
    if why:
        return Condition("parent-agents-md", "unknown", why)
    match = re.match(r"^([0-9a-fA-F]{64})\s", cap["stdout"] + " ")
    if cap["exit_code"] != 0 or not match:
        return Condition("parent-agents-md", "unknown", f"no sha256 from {cap['command']} (exit {cap['exit_code']}): {first_line(cap['stderr'] or cap['stdout'])}")
    have = match.group(1).lower()
    if want is None:
        return Condition("parent-agents-md", "fail", f"present, sha256 {have}, but expected.yaml records no hash yet (E4)")
    if have != want:
        return Condition("parent-agents-md", "fail", f"sha256 {have}, expected {want}: it differs from yamaguchi's recorded copy (D9)")
    return Condition("parent-agents-md", "pass", f"sha256 {have} matches")


def interfaces(text: str) -> dict[str, dict[str, str]]:
    """``ifconfig -a``, one dict per interface: ether, inet (the first IPv4), media, status."""
    found: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for line in text.splitlines():
        head = re.match(r"^([A-Za-z0-9.]+): flags=", line)
        if head:
            current = found.setdefault(head.group(1), {})
            continue
        if current is None:
            continue
        stripped = line.strip()
        for key, pattern in (("ether", r"^ether (\S+)"), ("inet", r"^inet (\d+\.\d+\.\d+\.\d+)"), ("media", r"^media: (.*)$"), ("status", r"^status: (\S+)")):
            match = re.match(pattern, stripped)
            if match and key not in current:
                current[key] = match.group(1)
    return found


def gate_net(probe: Probe, expected: dict) -> list[Condition]:
    net = expected["network"]
    nic = net["bridge_nic"]
    device = nic["device"]
    operator = Condition("throughput", "operator", f"iperf3 from turing to yamaguchi over {device} reaches >= {net['iperf3_min_mbps']} Mb/s: owner-run (§9.3, F2)")
    cap = probe.capture("network", "ifconfig")
    why = unmeasured(cap, "ifconfig", "network")
    if why is None and cap is not None and cap["exit_code"] != 0:
        why = f"{cap['command']} exited {cap['exit_code']}: {first_line(cap['stderr'])}"
    if why:
        return [Condition("link", "unknown", why), Condition("address", "unknown", why), operator]
    info = interfaces(cap["stdout"]).get(device)
    if info is None:
        return [Condition("link", "fail", f"{device} is not present; is the dongle ({nic['mac']}) plugged in? (F2)"), Condition("address", "fail", f"{device} is not present"), operator]
    conditions = []
    ether = info.get("ether", "").lower()
    media = info.get("media", "(no media line)")
    status = info.get("status", "(no status line)")
    if ether != nic["mac"].lower():
        conditions.append(Condition("link", "fail", f"{device} is {ether or 'an interface with no MAC'}, not the dongle {nic['mac']}; its name moved, so update expected.yaml"))
    elif status == "active" and nic["media"] in media:
        conditions.append(Condition("link", "pass", f"{device} ({ether}): media {media}, status {status}"))
    else:
        conditions.append(Condition("link", "fail", f"{device} ({ether}): media {media}, status {status}; F2 needs {nic['media']} and active"))
    inet = info.get("inet")
    have = inet or "no IPv4 address"
    if net["reserved_ip"] is None:
        conditions.append(Condition("address", "fail", f"no reserved address recorded yet; A6 reserves one and records it in expected.yaml ({device} has {have})"))
    elif inet == net["reserved_ip"]:
        conditions.append(Condition("address", "pass", f"{device} has the reserved {inet}"))
    else:
        conditions.append(Condition("address", "fail", f"{device} has {have}, not the reserved {net['reserved_ip']} (A6)"))
    conditions.append(operator)
    return conditions


def _sysctl_values(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            values.setdefault(key.strip(), value.strip())
    return values


def _vm_stat(text: str) -> tuple[int, int, int, int] | None:
    """(page size, free, speculative, inactive) from vm_stat, as util/macvm_ctl.bash reads it, or None."""
    size = re.search(r"^Mach Virtual Memory Statistics:.*\(page size of ([1-9][0-9]{0,5}) bytes\)", text, re.M)
    counts = []
    for row in ("Pages free", "Pages speculative", "Pages inactive"):
        match = re.search(rf"^{row}:\s+([0-9]{{1,11}})\.?\s*$", text, re.M)
        if not match:
            return None
        counts.append(int(match.group(1)))
    return (int(size.group(1)), *counts) if size else None


def _swap_used_mib(text: str) -> tuple[int, str] | None:
    """(MiB used, rounded up; the raw token) from sysctl vm.swapusage, or None."""
    match = re.search(r"\bused = (\S+)", text)
    if not match:
        return None
    token = match.group(1)
    parts = re.fullmatch(r"([0-9]{1,9})(?:\.([0-9]{1,6}))?([KMG])", token)
    if not parts:
        return None
    value = Fraction(f"{parts.group(1)}.{parts.group(2) or 0}")
    mib = {"K": value / 1024, "M": value, "G": value * 1024}[parts.group(3)]
    return math.ceil(mib), token


def gate_mem(probe: Probe, expected: dict) -> list[Condition]:
    vm = expected["vm"]
    vm_mib = vm["memory_gib"] * 1024
    reserve_mib = vm["reserve_gib"] * 1024
    max_swap_mib = vm["max_swap_gib"] * 1024
    conditions, info = [], []

    cap = probe.capture("hypervisor", "vboxmanage-showvminfo")
    if cap is not None and cap["skipped"] is None and not cap["timed_out"]:
        if cap["exit_code"] == 0:
            conf = re.search(r"^memory=(\d+)\s*$", cap["stdout"], re.M)
            state = re.search(r'^VMState="([^"]*)"', cap["stdout"], re.M)
            if conf and int(conf.group(1)) > vm_mib:
                vm_mib = int(conf.group(1))
                info.append(Condition("vm", "info", f"{vm['name']} is configured with {vm_mib} MiB, more than vm.memory_gib {vm['memory_gib']}; the gate uses the larger"))
            if state:
                running = state.group(1) == "running"
                info.append(Condition("vm-state", "info", f"{vm['name']}: VMState={state.group(1)}" + ("; G-MEM gates its start, so its own memory is not counted as available" if running else "")))
        elif "Could not find a registered machine" in cap["stderr"]:
            info.append(Condition("vm-state", "info", f"{vm['name']} is not registered yet (F4 creates it); the gate uses vm.memory_gib"))

    cap = probe.capture("hardware", "sysctl")
    why = unmeasured(cap, "sysctl", "hardware")
    values = _sysctl_values(cap["stdout"]) if cap is not None and why is None else {}
    memsize, cores = values.get("hw.memsize", ""), values.get("hw.physicalcpu", "")
    if why or not memsize.isdigit() or not cores.isdigit():
        conditions.append(Condition("vm-fits", "unknown", why or "sysctl printed no hw.memsize or hw.physicalcpu"))
    else:
        memsize_mib = int(memsize) // MIB
        problems = []
        if vm_mib + reserve_mib > memsize_mib:
            problems.append(f"VM {vm_mib} MiB + reserve {reserve_mib} MiB > hw.memsize {memsize_mib} MiB: a VM this size can never start (the X2 class; D1 sizes it at 6 GiB)")
        if vm["vcpus"] > int(cores):
            problems.append(f"{vm['vcpus']} vCPU > hw.physicalcpu {cores} (the X2 class; D1 gives it 4)")
        if problems:
            conditions.append(Condition("vm-fits", "fail", "; ".join(problems)))
        else:
            conditions.append(Condition("vm-fits", "pass", f"VM {vm_mib} MiB + reserve {reserve_mib} MiB <= hw.memsize {memsize_mib} MiB; {vm['vcpus']} vCPU <= {cores} cores"))

    cap = probe.capture("memory", "vm_stat")
    why = unmeasured(cap, "vm_stat", "memory")
    parsed = _vm_stat(cap["stdout"]) if cap is not None and why is None and cap["exit_code"] == 0 else None
    need_mib = vm_mib + reserve_mib
    if parsed is None:
        reason = why or (f"'{cap['command']}' exited {cap['exit_code']}" if cap is not None and cap["exit_code"] != 0 else "no page size header or no free, speculative or inactive count in vm_stat")
        conditions.append(Condition("memory", "unknown", f"cannot measure free + inactive: {reason}"))
    else:
        size, free, spec, inactive = parsed
        avail_mib = (free + spec + inactive) * size // MIB
        sign, status = (">=", "pass") if avail_mib >= need_mib else ("<", "fail")
        conditions.append(Condition("memory", status, f"free + inactive {avail_mib} MiB {sign} {need_mib} MiB required (VM {vm_mib} MiB + reserve {reserve_mib} MiB)"))

    cap = probe.capture("memory", "swapusage")
    why = unmeasured(cap, "swapusage", "memory")
    swap = _swap_used_mib(cap["stdout"]) if cap is not None and why is None and cap["exit_code"] == 0 else None
    if swap is None:
        reason = why or (f"'{cap['command']}' exited {cap['exit_code']}" if cap is not None and cap["exit_code"] != 0 else "no 'used = <number>K|M|G' in vm.swapusage")
        conditions.append(Condition("swap", "unknown", f"cannot measure swap used: {reason}"))
    else:
        used, _ = swap
        sign, status = ("<=", "pass") if used <= max_swap_mib else (">", "fail")
        conditions.append(Condition("swap", status, f"used {used} MiB {sign} {max_swap_mib} MiB allowed"))

    hits, problem = [], None
    for name in DOCKER_NAMES:
        cap = probe.capture("docker", f"pgrep:{name}")
        why = unmeasured(cap, f"pgrep:{name}", "docker")
        if why:
            problem = why
            break
        if cap["exit_code"] == 0:
            hits.append(f"{name} (pid {' '.join(cap['stdout'].split())})")
        elif cap["exit_code"] != 1:
            problem = f"'{cap['command']}' exited {cap['exit_code']}"
            break
    if problem:
        conditions.append(Condition("docker", "unknown", f"cannot tell whether Docker Desktop is running: {problem}"))
    elif hits:
        conditions.append(Condition("docker", "fail", f"Docker Desktop is running: {', '.join(hits)}; quit it before node mode (D7)"))
    else:
        conditions.append(Condition("docker", "pass", "Docker Desktop is not running"))
    return conditions + info


EVALUATORS = {"G-ALIAS": gate_alias, "G-SIGN": gate_sign, "G-SEC": gate_sec, "G-TOOLS": gate_tools, "G-ENV": gate_env, "G-NET": gate_net, "G-MEM": gate_mem}


# ---------------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------------
def evaluate(probe: Probe, expected: dict, specs: list[GateSpec]) -> list[GateResult]:
    results = []
    collected = set(probe.doc.get("sections") or [])
    for spec in specs:
        absent = [section for section in spec.sections if section not in collected]
        if absent:
            results.append(GateResult(spec, [Condition("probe", "unknown", f"the probe did not collect section(s) {', '.join(absent)}")]))
        else:
            results.append(GateResult(spec, EVALUATORS[spec.gate](probe, expected)))
    return results


def readiness(results: list[GateResult]) -> dict[str, int]:
    counts = {"evaluated": len(results), "pass": 0, "operator": 0, "fail": 0, "unknown": 0}
    for result in results:
        counts[result.status] += 1
    return counts


def summary_line(counts: dict[str, int]) -> str:
    return f"readiness: {counts['pass']} of {counts['evaluated']} gates pass ({counts['operator']} pending owner-run checks, {counts['fail']} failing, {counts['unknown']} unknown)"


def exit_code(counts: dict[str, int], check: bool) -> int:
    if not check:
        return 0
    if counts["unknown"]:
        return 2
    return 1 if counts["fail"] else 0


def render_text(header: list[str], results: list[GateResult], summary: str) -> str:
    out = list(header)
    for result in results:
        out.append("")
        out.append(f"{result.spec.gate:<8} {LABEL[result.status]:<8} {result.spec.target}")
        for cond in result.conditions:
            out.append(f"  {LABEL[cond.status]:<8} {cond.name:<18} {cond.message}")
            out.extend(f"           {line}" for line in cond.detail)
    out.append("")
    out.append(summary)
    out.append("not evaluated here:")
    out.extend(f"  {gate:<8} {why}" for gate, why in NOT_EVALUATED.items())
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when a gate fails, 2 when one is unknown (I-G1)")
    parser.add_argument("--json", action="store_true", help="print one JSON object (schema in the docstring)")
    parser.add_argument("--section", action="append", type=gate_spec, metavar="GATE", help="evaluate only this gate, e.g. G-MEM or mem; repeatable")
    parser.add_argument("--host", help="the host whose expected.yaml applies (default: the probe's host)")
    parser.add_argument("--expected", type=Path, help="default: conf/hosts/<host>/expected.yaml")
    parser.add_argument("--probe-json", metavar="FILE", help="evaluate a saved probe document ('-' for stdin) instead of running the probe")
    parser.add_argument("--probe", type=Path, default=DEFAULT_PROBE, help="the probe script to run (default: util/host_state_probe.bash)")
    parser.add_argument("--root", help="the Juniper root, passed to the probe")
    parser.add_argument("--timeout", type=int, default=60, help="the probe's per-capture limit in seconds (default 60)")
    args = parser.parse_args(argv)
    if args.probe_json is not None and (args.root is not None or args.probe != DEFAULT_PROBE):
        parser.error("--probe and --root apply only when the script runs the probe; drop them with --probe-json")
    if not 1 <= args.timeout <= 9999:
        parser.error("--timeout must be from 1 to 9999 seconds")
    specs = [spec for spec in GATES if args.section is None or spec in args.section]
    try:
        if args.probe_json is not None:
            doc = read_probe_json(args.probe_json)
            host = short_host(args.host or doc.get("host") or "")
            if not host:
                raise EnvError("the probe names no host; pass --host")
            expected_path = args.expected or REPO_ROOT / "conf" / "hosts" / host / "expected.yaml"
            expected = load_expected(expected_path)
            source, probe_path = "file", args.probe_json
        else:
            host = short_host(args.host or socket.gethostname())
            expected_path = args.expected or REPO_ROOT / "conf" / "hosts" / host / "expected.yaml"
            expected = load_expected(expected_path)
            sections = [section for section in SECTION_ORDER if any(section in spec.sections for spec in specs)]
            doc = run_probe(args.probe, sections, expected, args.root, args.timeout)
            source, probe_path = "run", str(args.probe)
        if short_host(expected["host"]) != host:
            raise EnvError(f"{expected_path} describes host {expected['host']!r}, not {host!r}")
        probe_host = short_host(doc.get("host") or "")
        if probe_host and probe_host != host:
            raise EnvError(f"the probe ran on {probe_host!r}, but {expected_path} describes {host!r}")
    except EnvError as exc:
        print(f"host_state_check: {exc}", file=sys.stderr)
        return 2

    results = evaluate(Probe(doc), expected, specs)
    counts = readiness(results)
    summary = summary_line(counts)
    code = exit_code(counts, args.check)
    shown = os.path.relpath(expected_path, REPO_ROOT) if str(Path(expected_path).resolve()).startswith(str(REPO_ROOT) + os.sep) else str(expected_path)
    if args.json:
        payload = {
            "schema": SCHEMA,
            "tool": "util/host_state_check.py",
            "mode": "check" if args.check else "report",
            "host": host,
            "expected": shown,
            "probe": {"source": source, "path": probe_path, "host": doc.get("host", ""), "collected_at": doc.get("collected_at", ""), "bash_version": doc.get("bash_version", "")},
            "gates": [
                {
                    "gate": r.spec.gate,
                    "status": r.status,
                    "target": r.spec.target,
                    "sections": list(r.spec.sections),
                    "conditions": [{"name": c.name, "status": c.status, "message": c.message, "detail": c.detail} for c in r.conditions],
                }
                for r in results
            ],
            "readiness": counts,
            "not_evaluated": NOT_EVALUATED,
            "ok": code == 0,
            "exit_code": code,
            "summary": summary,
        }
        print(json.dumps(payload, indent=2))
    else:
        header = [
            f"host state check: {host} against {shown} ({'check' if args.check else 'report'} mode)",
            f"probe: {probe_path} ({source}), collected {doc.get('collected_at', '?')} on {doc.get('host') or '?'} under bash {doc.get('bash_version', '?')}",
        ]
        sys.stdout.write(render_text(header, results, summary))
    return code


if __name__ == "__main__":
    sys.exit(main())
