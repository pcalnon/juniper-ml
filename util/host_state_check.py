#!/usr/bin/env python3
"""Evaluate a host against conf/hosts/<host>/expected.yaml: the host gates of turing bring-up task G1.

Project: juniper-ml
Sub-Project: host tooling (turing bring-up)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: permanent utility
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1; the host gates
         of §9.3 and the readiness metric of §9.4; regression R-G1; integration test I-G1; errata E-D6 and
         E-G-SIGN); util/host_state_probe.bash (the collector); conf/hosts/turing/expected.yaml;
         tests/test_host_state_check.py

Why this exists
---------------
The plan measures turing's readiness as the number of its ten host gates that pass (§9.4). Before G1 each
gate was a hand-run command and a hand-kept table, and the tables drifted from the host (errata X1-X10).
This script makes the measurement repeatable. ``util/host_state_probe.bash`` captures the host's raw
output, and this script judges those captures against the host's expected state, one condition at a
time, naming the plan task that fixes each failure.

How a run works
---------------
1. Load ``conf/hosts/<host>/expected.yaml`` and validate it. An invalid file exits 2 before anything
   runs. That includes regression R-G1, the X2 class: a VM whose ``vm.mem_gib`` plus G-MEM's
   ``reserve_gib`` exceeds ``identity.memsize_bytes``, or whose ``vm.vcpus`` exceeds
   ``identity.physicalcpu`` (the primer's "8 vCPU and 44 GB" on a 6-core, 16 GiB machine).
2. Get the probe's JSON. Either run ``bash util/host_state_probe.bash --json`` with the sections the
   selected gates read (plus ``hardware``), or read ``--probe-json FILE``, a saved run such as the one
   task H3 compares agent reports against.
3. Check identity: the probe's ``uname -m`` and sysctl ``hw.memsize``, ``hw.physicalcpu`` and ``hw.ncpu``
   must equal ``identity``. If they do not, the file describes another machine, and the run exits 2.
4. Evaluate each gate's conditions. A condition is ``pass``, ``fail``, or ``error`` when its input is
   missing, failed, timed out or cannot be parsed. A gate fails when any condition fails, and is
   ``error`` when none fails but one could not be evaluated.

The gates (probe sections in brackets)
--------------------------------------
G-ALIAS [alias]
    ``util/git_remote_alias_check.py --json`` (task G2). ``origins``, ``aliases`` and ``keys``: every
    checkout's origin uses its per-repo alias (R-G2a/b), every alias resolves to github.com with
    exactly its key, ``IdentitiesOnly yes`` and ``AddKeysToAgent no`` (R-G2c), and every deploy key is a
    regular file at mode 600.
G-SIGN [signing]
    Erratum E-G-SIGN. ``signing-config``: ``util/configure_commit_signing.py --check`` passes in every
    checkout. ``pinentry``, ``agent-socket`` and ``external-cache``: those lines of
    ``util/headless_signing_preflight.bash``, which do not depend on an agent session's D11 override.
    ``integration``: the I-SIGN record (signing plan K10, recorded by K11), a file that must exist.
G-SEC [security]
    ``sip`` and ``authenticated-root`` (csrutil), ``firewall`` (socketfilterfw state 1 or 2, blocking all
    incoming connections: task C2's block-all form, owner ruling 2026-10-25; stealth mode is reported only),
    ``filevault`` (fdesetup), ``key-exports`` (no ``*.asc`` or ``*recovery*`` file under ``~/.ssh`` or
    ``~/.gnupg``: task C3) and ``key-modes`` (no non-public file directly in ``~/.ssh`` open to group or
    others: task C4).
G-TOOLS [tools]
    Erratum E-D6. ``local-bin``: each listed tool resolves, through ``command -v``, to
    ``~/.local/bin/<tool>``, which is executable. ``kubectl``: the client is within ``max_minor_skew``
    minors of the cluster.
G-ENV [env]
    ``conda-envs``: ``conda env list`` holds every listed env. ``parent-agents-md``: ``<root>/AGENTS.md``
    exists and its sha256 equals the recorded one (decision D9, task E4).
G-NET [network]
    ``link``: the interface exists, carries the expected MAC, is active and reports the expected media.
    ``address``: it holds the reserved IPv4 address (task A6). ``throughput``: the recorded iperf3 run
    reached ``min_mbps``, and its record file exists (task F2).
G-MEM [memory, vm]
    The arithmetic of ``util/macvm_ctl.bash`` (task F5a), to the MiB. ``memory``: vm_stat's free +
    speculative + inactive pages, rounded down to MiB, are at least the VM's memory plus
    ``reserve_gib``. The VM's memory is the larger of ``vm.mem_gib`` and the registered VM's configured
    memory. ``swap``: swap used, rounded up to MiB, is at most ``max_swap_gib``. ``docker``: Docker
    Desktop is not running (``pgrep -x`` for com.docker.backend, "Docker Desktop" and Docker).

G-AUTH (operator-run, plan §14.1), G-PATH (task G5's hook and CI step) and G-AGENT (task H2's tests
and H3's denials) are evaluated elsewhere. The report names them.

A record that does not exist yet is ``null`` in expected.yaml. Its condition fails and names the task
that creates it. A record's ``record`` path is relative to the repository that holds expected.yaml (the
directory three levels above ``conf/hosts/<host>/expected.yaml``), or to expected.yaml's own directory
when the file lives elsewhere.

Usage
-----
    python3 util/host_state_check.py [--host NAME] [--expected FILE] [--probe-json FILE] [--root DIR]
        [--section GATE]... [--check] [--json]

``--host NAME``
    The host whose ``conf/hosts/<NAME>/expected.yaml`` to read. Default: this machine's short hostname,
    lower case. With ``--expected``, the file's own ``host`` decides, and ``--host`` must agree.
``--expected FILE``
    Read this expected-state file instead.
``--probe-json FILE``
    Evaluate this saved probe output instead of running the probe. It must hold every section the
    selected gates read, plus ``hardware``.
``--root DIR``
    The Juniper root, passed to the probe. Default: ``$JUNIPER_ROOT``, then
    ``$HOME/Development/python/Juniper``.
``--section GATE``
    Evaluate only this gate. Repeatable. ``G-MEM``, ``g-mem`` and ``mem`` all name G-MEM.
``--check``
    Gate mode: exit 1 while a selected gate fails (below). Without it the report always exits 0.
``--json``
    Print one JSON object instead of the report (schema below).

Exit codes
----------
Without ``--check`` (the report): 0 whenever the report is produced, whatever the gates say.

With ``--check``: 0 every selected gate passed; 1 a gate failed, and every failure is listed; 2 a
condition could not be evaluated, even inside a gate that also failed. 2 wins over 1.

Either way, 2 for usage or environment. That covers a bad argument; a missing, unreadable or invalid
expected.yaml, R-G1 included; PyYAML not installed; a probe that fails, times out or prints anything
but its JSON; and a probe whose hardware does not match ``identity``. These print to stderr only.

Environment
-----------
``HOST_STATE_PROBE``  the probe script (default: ``host_state_probe.bash`` next to this file)
``HOST_STATE_BASH``   the bash that runs it (default: ``bash`` from PATH)
``JUNIPER_ROOT``      the Juniper root (see ``--root``)

JSON schema (``--json``)
------------------------
``schema`` is bumped on any incompatible change. The probe's own schema is in the header of
``util/host_state_probe.bash``.

    {
      "schema": 1,
      "mode": "report" | "check",
      "host": str,
      "expected": str,                    # absolute path of expected.yaml
      "probe": {"source": "run" | "file", "path": str,   # the probe script, or the --probe-json file
                "collected_at": str, "node": str},
      "identity": str,                    # the matched hardware, one line
      "gates": [{"id": "G-ALIAS" | ..., "status": "pass" | "fail" | "error", "summary": str,
                 "conditions": [{"id": str, "status": "pass" | "fail" | "error",
                                 "message": str, "remediation": str | null}]}],
      "not_evaluated": [{"id": "G-AUTH" | "G-PATH" | "G-AGENT", "where": str}],  # [] with --section
      "readiness": {"passed": int, "evaluated": int},
      "ok": bool,                         # exit_code == 0
      "exit_code": 0 | 1 | 2,
      "summary": str
    }
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import re
import socket
import subprocess  # nosec B404 - runs the probe with list arguments, never a shell
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, NoReturn

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
SCHEMA_VERSION = 1
PROBE_SCHEMA_VERSION = 1
PROBE_TIMEOUT_SECONDS = 900
GIB = 1024**3
MIB = 1024**2

GATES = ("G-ALIAS", "G-SIGN", "G-SEC", "G-TOOLS", "G-ENV", "G-NET", "G-MEM")
GATE_SECTIONS = {
    "G-ALIAS": ("alias",),
    "G-SIGN": ("signing",),
    "G-SEC": ("security",),
    "G-TOOLS": ("tools",),
    "G-ENV": ("env",),
    "G-NET": ("network",),
    "G-MEM": ("memory", "vm"),
}
# The probe's section order, which the probe also uses.
PROBE_SECTIONS = ("hardware", "memory", "vm", "network", "power", "security", "tools", "env", "alias", "signing")
NOT_EVALUATED = (
    ("G-AUTH", "operator-run: the A3 auth matrix of ssh -T, ls-remote and push --dry-run per repo (plan §14.1)"),
    ("G-PATH", "util/home_path_literal_check.py: task G5's pre-commit hook and its CI step"),
    ("G-AGENT", "tests/test_agents_frontmatter.py and each agent's contract test (task H2), and H3's denials"),
)
STATUS_LABEL = {"pass": "PASS", "fail": "FAIL", "error": "ERROR"}

_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
_VM_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_TOOL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}")
_IFACE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_MAC_RE = re.compile(r"[0-9a-f]{2}(?::[0-9a-f]{2}){5}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_IPV4_RE = re.compile(r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}")
_MINOR_RE = re.compile(r"(\d+)\.(\d+)")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_PREFLIGHT_RE = re.compile(r"(PASS|FAIL|INFO)\s+(\S+)\s+(.*)")
_IFCONFIG_HEAD_RE = re.compile(r"([A-Za-z0-9._-]+): flags=")
_CONDA_RE = re.compile(r"(?P<name>\S+)?\s+(?:[*+]\s+)*(?P<path>/.*?)\s*")
# util/macvm_ctl.bash's limits: a page size of up to 6 digits, page counts of up to 11, and a swap token
# of up to 9 integer and 6 fraction digits.
_PAGE_SIZE_RE = re.compile(r"[1-9]\d{0,5}")
_COUNT_RE = re.compile(r"\d{1,11}")
_SWAP_TOKEN_RE = re.compile(r"(\d{1,9}(?:\.\d{1,6})?)([KMG])")


class UsageError(Exception):
    """A bad command line (exit 2)."""


class ExpectedError(Exception):
    """expected.yaml is missing, unreadable, malformed or inconsistent (exit 2)."""


class ProbeError(Exception):
    """The probe failed, or its output is not the probe's JSON (exit 2)."""


class IdentityError(Exception):
    """The probe's hardware does not match expected.yaml's identity (exit 2)."""


class DataError(Exception):
    """A condition's probe input is missing, failed, timed out or unparseable: the condition is an error."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


@dataclass
class Condition:
    id: str
    status: str
    message: str
    remediation: str | None = None

    def as_json(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "message": self.message, "remediation": self.remediation}


@dataclass
class GateResult:
    id: str
    conditions: list[Condition]

    @property
    def status(self) -> str:
        statuses = {c.status for c in self.conditions}
        if "fail" in statuses:
            return "fail"
        if "error" in statuses:
            return "error"
        return "pass"

    def summary(self) -> str:
        total = len(self.conditions)
        failed = [c.id for c in self.conditions if c.status == "fail"]
        errors = [c.id for c in self.conditions if c.status == "error"]
        if not failed and not errors:
            return f"all {total} conditions pass"
        parts = []
        if failed:
            parts.append(f"{len(failed)} of {total} fail: {', '.join(failed)}")
        if errors:
            parts.append(f"{len(errors)} could not be evaluated: {', '.join(errors)}")
        return "; ".join(parts)

    def as_json(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "summary": self.summary(), "conditions": [c.as_json() for c in self.conditions]}


@dataclass
class Context:
    """What the gates need besides their own config."""

    host: str
    expected: dict[str, Any]
    record_base: Path
    probe: dict[str, Any]
    gates: list[GateResult] = field(default_factory=list)


# ---------------------------------------------------------------------------------------------------------
# expected.yaml
# ---------------------------------------------------------------------------------------------------------
def _fail(where: str, want: str, got: Any) -> NoReturn:
    raise ExpectedError(f"{where}: want {want}, got {got!r}")


def _mapping(value: Any, where: str, keys: tuple[str, ...], optional: tuple[str, ...] = ()) -> dict[str, Any]:
    if value is None and not keys:
        return {}
    if not isinstance(value, dict):
        _fail(where, "a mapping", value)
    unknown = sorted(set(value) - set(keys) - set(optional))
    if unknown:
        raise ExpectedError(f"{where}: unknown key(s) {', '.join(map(str, unknown))}; known: {', '.join(keys + optional) or 'none'}")
    missing = [k for k in keys if k not in value]
    if missing:
        raise ExpectedError(f"{where}: missing key(s) {', '.join(missing)}")
    return value


def _int(value: Any, where: str, minimum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        _fail(where, f"a whole number of at least {minimum}", value)
    return value


def _str(value: Any, where: str, pattern: re.Pattern[str] | None = None, want: str = "a string") -> str:
    if not isinstance(value, str) or not value or (pattern is not None and pattern.fullmatch(value) is None):
        _fail(where, want, value)
    return value


def _names(value: Any, where: str, pattern: re.Pattern[str], want: str) -> list[str]:
    if not isinstance(value, list) or not value:
        _fail(where, f"a non-empty list of {want}", value)
    for i, item in enumerate(value):
        _str(item, f"{where}[{i}]", pattern, want)
    if len(set(value)) != len(value):
        _fail(where, "no duplicates", value)
    return value


def _date(value: Any, where: str) -> str:
    # PyYAML reads an unquoted 2026-10-27 as a date.
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value.isoformat()
    return _str(value, where, _DATE_RE, "a YYYY-MM-DD date")


def _record_path(value: Any, where: str) -> str:
    path = _str(value, where, None, "a relative path")
    if path.startswith("/") or ".." in Path(path).parts:
        _fail(where, "a path relative to the repository, without '..'", value)
    return path


def _record(value: Any, where: str, extra: tuple[str, ...] = ()) -> dict[str, Any] | None:
    if value is None:
        return None
    rec = _mapping(value, where, ("date", "record") + extra)
    rec["date"] = _date(rec["date"], f"{where}.date")
    rec["record"] = _record_path(rec["record"], f"{where}.record")
    return rec


def validate_expected(data: Any, where: str) -> dict[str, Any]:
    """Check expected.yaml's shape and consistency; return it with dates normalised to strings."""
    doc = _mapping(data, where, ("schema", "host", "identity", "vm", "gates"))
    if doc["schema"] != SCHEMA_VERSION or isinstance(doc["schema"], bool):
        _fail(f"{where}: schema", str(SCHEMA_VERSION), doc["schema"])
    _str(doc["host"], f"{where}: host", _NAME_RE, "a lower-case host name")
    ident = _mapping(doc["identity"], f"{where}: identity", ("arch", "memsize_bytes", "physicalcpu", "ncpu"))
    _str(ident["arch"], f"{where}: identity.arch")
    memsize = _int(ident["memsize_bytes"], f"{where}: identity.memsize_bytes", 1)
    physical = _int(ident["physicalcpu"], f"{where}: identity.physicalcpu", 1)
    _int(ident["ncpu"], f"{where}: identity.ncpu", physical)
    vm = _mapping(doc["vm"], f"{where}: vm", ("name", "mem_gib", "vcpus"))
    _str(vm["name"], f"{where}: vm.name", _VM_RE, "a VM name")
    mem_gib = _int(vm["mem_gib"], f"{where}: vm.mem_gib", 1)
    vcpus = _int(vm["vcpus"], f"{where}: vm.vcpus", 1)

    gates = _mapping(doc["gates"], f"{where}: gates", GATES)
    g = f"{where}: gates"
    gates["G-ALIAS"] = _mapping(gates["G-ALIAS"], f"{g}.G-ALIAS", ())
    sign = gates["G-SIGN"] = _mapping(gates["G-SIGN"], f"{g}.G-SIGN", ("integration",))
    sign["integration"] = _record(sign["integration"], f"{g}.G-SIGN.integration")
    gates["G-SEC"] = _mapping(gates["G-SEC"], f"{g}.G-SEC", ())
    tools = _mapping(gates["G-TOOLS"], f"{g}.G-TOOLS", ("local_bin", "kubectl"))
    _names(tools["local_bin"], f"{g}.G-TOOLS.local_bin", _TOOL_RE, "tool names")
    kubectl = _mapping(tools["kubectl"], f"{g}.G-TOOLS.kubectl", ("cluster", "max_minor_skew"))
    if not isinstance(kubectl["cluster"], str):
        _fail(f"{g}.G-TOOLS.kubectl.cluster", 'a quoted "MAJOR.MINOR" string (an unquoted 1.30 reads as 1.3)', kubectl["cluster"])
    _str(kubectl["cluster"], f"{g}.G-TOOLS.kubectl.cluster", re.compile(r"\d+\.\d+"), 'a quoted "MAJOR.MINOR" string')
    _int(kubectl["max_minor_skew"], f"{g}.G-TOOLS.kubectl.max_minor_skew", 0)
    env = _mapping(gates["G-ENV"], f"{g}.G-ENV", ("conda_envs", "parent_agents_md"))
    _names(env["conda_envs"], f"{g}.G-ENV.conda_envs", re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*"), "conda env names")
    agents = _mapping(env["parent_agents_md"], f"{g}.G-ENV.parent_agents_md", ("sha256",))
    if agents["sha256"] is not None:
        _str(agents["sha256"], f"{g}.G-ENV.parent_agents_md.sha256", _SHA256_RE, "64 lower-case hex digits or null")
    net = _mapping(gates["G-NET"], f"{g}.G-NET", ("interface", "mac", "media", "reserved_ip", "min_mbps", "throughput"))
    _str(net["interface"], f"{g}.G-NET.interface", _IFACE_RE, "an interface name")
    if net["mac"] is not None:
        _str(net["mac"], f"{g}.G-NET.mac", _MAC_RE, 'a quoted lower-case MAC such as "00:e0:4c:68:06:b1", or null')
    _str(net["media"], f"{g}.G-NET.media", re.compile(r"\S+"), "a media word such as 1000baseT")
    if net["reserved_ip"] is not None:
        _str(net["reserved_ip"], f"{g}.G-NET.reserved_ip", _IPV4_RE, "an IPv4 address or null")
    _int(net["min_mbps"], f"{g}.G-NET.min_mbps", 1)
    net["throughput"] = _record(net["throughput"], f"{g}.G-NET.throughput", ("mbps",))
    if net["throughput"] is not None:
        mbps = net["throughput"]["mbps"]
        if not isinstance(mbps, (int, float)) or isinstance(mbps, bool) or mbps < 0:
            _fail(f"{g}.G-NET.throughput.mbps", "a number of Mb/s", mbps)
    mem = _mapping(gates["G-MEM"], f"{g}.G-MEM", ("reserve_gib", "max_swap_gib"))
    reserve = _int(mem["reserve_gib"], f"{g}.G-MEM.reserve_gib", 0)
    _int(mem["max_swap_gib"], f"{g}.G-MEM.max_swap_gib", 0)

    # R-G1, the X2 class: a VM that cannot fit this machine.
    if (mem_gib + reserve) * GIB > memsize:
        left = Fraction(memsize - reserve * GIB, GIB)
        raise ExpectedError(
            f"{where}: vm.mem_gib {mem_gib} cannot fit: hw.memsize {memsize} is {_gib(memsize)} GiB, and less G-MEM's "
            f"{reserve} GiB reserve that leaves {float(left):g} GiB for the VM (regression R-G1, the X2 class: the primer's "
            "44 GB VM on a 16 GiB host)"
        )
    if vcpus > physical:
        raise ExpectedError(f"{where}: vm.vcpus {vcpus} exceeds identity.physicalcpu {physical} (regression R-G1, the X2 class: the primer's 8 vCPU on 6 cores)")
    return doc


def _gib(n: int) -> str:
    return f"{n / GIB:g}"


def load_expected(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        raise ExpectedError("PyYAML is needed to read expected.yaml: python3 -m pip install pyyaml") from None
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ExpectedError(f"no expected state: {display(path)} does not exist") from None
    except OSError as exc:
        raise ExpectedError(f"cannot read {path}: {exc.strerror or exc}") from None
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ExpectedError(f"{path} is not valid YAML: {exc}") from None
    return validate_expected(data, display(path))


def record_base(expected_path: Path) -> Path:
    """The repository that holds conf/hosts/<host>/expected.yaml, else expected.yaml's directory."""
    parents = expected_path.resolve().parents
    if len(parents) > 3 and parents[1].name == "hosts" and parents[2].name == "conf":
        return parents[3]
    return expected_path.resolve().parent


def display(path: Path | str) -> str:
    """A path relative to this checkout when it is inside it."""
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------------------------------------
# The probe
# ---------------------------------------------------------------------------------------------------------
def parse_probe(raw: bytes | str, source: str) -> dict[str, Any]:
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
    try:
        doc = json.loads(text)
    except ValueError as exc:
        raise ProbeError(f"{source} is not the probe's JSON: {exc}") from None
    if not isinstance(doc, dict) or doc.get("probe") != "util/host_state_probe.bash":
        raise ProbeError(f"{source} is not util/host_state_probe.bash output")
    if doc.get("schema") != PROBE_SCHEMA_VERSION:
        raise ProbeError(f"{source} has probe schema {doc.get('schema')!r}; this check reads schema {PROBE_SCHEMA_VERSION}")
    return doc


def run_probe(sections: list[str], tools: list[str], vm: str, root: str) -> tuple[dict[str, Any], str]:
    probe = os.environ.get("HOST_STATE_PROBE") or str(HERE / "host_state_probe.bash")
    bash = os.environ.get("HOST_STATE_BASH") or "bash"
    argv = [bash, probe, "--json", "--root", root, "--vm", vm]
    for section in sections:
        argv += ["--section", section]
    for tool in tools:
        argv += ["--tool", tool]
    try:
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=PROBE_TIMEOUT_SECONDS, check=False)
    except FileNotFoundError:
        raise ProbeError(f"cannot run the probe: {bash} not found (set HOST_STATE_BASH)") from None
    except subprocess.TimeoutExpired:
        raise ProbeError(f"the probe ran longer than {PROBE_TIMEOUT_SECONDS} s: {' '.join(argv)}") from None
    if proc.returncode != 0:
        err = first_line(proc.stderr.decode("utf-8", "replace"))
        raise ProbeError(f"the probe exited {proc.returncode}: {err}")
    return parse_probe(proc.stdout, f"the output of {display(probe)}"), probe


def require_sections(doc: dict[str, Any], sections: list[str], source: str) -> None:
    have = doc.get("sections") if isinstance(doc.get("sections"), list) else []
    missing = [s for s in sections if s not in have or not isinstance(doc.get(s), dict)]
    if missing:
        raise ProbeError(f"{source} lacks section(s) {', '.join(missing)}; collect them with: bash util/host_state_probe.bash --json " + " ".join(f"--section {s}" for s in sections))


# ---------------------------------------------------------------------------------------------------------
# Reading captures
# ---------------------------------------------------------------------------------------------------------
def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "no output"


def get_capture(section: dict[str, Any], key: str, what: str) -> dict[str, Any] | None:
    """The CAPTURE at ``key``, or None when the probe recorded null there."""
    if key not in section:
        raise DataError(f"the probe recorded no {what}")
    cap = section[key]
    if cap is None:
        return None
    if not isinstance(cap, dict) or not isinstance(cap.get("argv"), list):
        raise DataError(f"the probe's {what} is not a command capture")
    return cap


def command_of(cap: dict[str, Any]) -> str:
    return " ".join(str(a) for a in cap.get("argv", []))


def stdout_of(cap: dict[str, Any] | None, what: str, ok_rcs: tuple[int, ...] = (0,)) -> str:
    """The capture's stdout, or DataError when its command was missing, timed out or exited otherwise."""
    if cap is None:
        raise DataError(f"the probe recorded no {what}")
    if not cap.get("found"):
        argv = cap.get("argv") or ["?"]
        raise DataError(f"{what}: {argv[0]} not found")
    if cap.get("timed_out"):
        raise DataError(f"{what}: '{command_of(cap)}' timed out")
    if cap.get("rc") not in ok_rcs:
        raise DataError(f"{what}: '{command_of(cap)}' exited {cap.get('rc')}: {first_line(str(cap.get('stderr', '')))}")
    return str(cap.get("stdout", ""))


def tilde(path: str, home: str) -> str:
    if home and (path == home or path.startswith(home.rstrip("/") + "/")):
        return "~" + path[len(home.rstrip("/")) :]
    return path


def evaluate(cid: str, fn: Callable[[], Condition]) -> Condition:
    try:
        return fn()
    except DataError as exc:
        return Condition(cid, "error", str(exc))


def failing_remediations(items: list[str | None]) -> str | None:
    seen: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.append(item)
    return "; ".join(seen) or None


# ---------------------------------------------------------------------------------------------------------
# G-ALIAS
# ---------------------------------------------------------------------------------------------------------
ALIAS_CONDITIONS = (
    ("origins", "origin", "checkouts use their per-repo alias as origin"),
    ("aliases", "alias", "aliases resolve to github.com with only their key, IdentitiesOnly yes and AddKeysToAgent no"),
    ("keys", "key", "deploy keys are regular files at mode 600"),
)


def gate_alias(ctx: Context) -> list[Condition]:
    try:
        cap = get_capture(ctx.probe["alias"], "check", "util/git_remote_alias_check.py run")
        text = stdout_of(cap, "util/git_remote_alias_check.py --json", (0, 1, 2))
        try:
            doc = json.loads(text)
        except ValueError:
            raise DataError(f"util/git_remote_alias_check.py printed no JSON (exit {cap['rc']}): {first_line(str(cap.get('stderr', '')))}") from None
        if not isinstance(doc, dict) or doc.get("schema") != 1 or not isinstance(doc.get("repos"), list):
            raise DataError("util/git_remote_alias_check.py printed JSON of an unknown schema")
    except DataError as exc:
        return [Condition(cid, "error", str(exc)) for cid, _, _ in ALIAS_CONDITIONS]
    if doc.get("skipped"):
        return [Condition(cid, "fail", f"util/git_remote_alias_check.py skipped: {doc.get('skip_reason')}", "bash util/juniper_repo_ssh_setup.bash <repo> for each repo (task A5)") for cid, _, _ in ALIAS_CONDITIONS]
    conditions = []
    repos = doc["repos"]
    for cid, check_name, what in ALIAS_CONDITIONS:
        ok, failed, errors, fixes = 0, [], [], []
        for repo in repos:
            check = (repo.get("checks") or {}).get(check_name) or {}
            status = check.get("status")
            if status in ("pass", "fixed"):
                ok += 1
            elif status == "error":
                errors.append(f"{repo.get('repo')}: {check.get('message')}")
            else:
                failed.append(f"{repo.get('repo')}: {check.get('message')}")
                fixes.append(check.get("remediation"))
        head = f"{ok} of {len(repos)} {what}"
        if errors:
            conditions.append(Condition(cid, "error", f"{head}; could not evaluate {'; '.join(errors)}"))
        elif failed or not repos:
            conditions.append(Condition(cid, "fail", f"{head}; {'; '.join(failed) or 'no repo was checked'}", failing_remediations(fixes)))
        else:
            conditions.append(Condition(cid, "pass", head))
    return conditions


# ---------------------------------------------------------------------------------------------------------
# G-SIGN
# ---------------------------------------------------------------------------------------------------------
PREFLIGHT_CONDITIONS = (
    ("pinentry", "plan task B1 (owner since erratum E-C8): pinentry-program /usr/local/bin/pinentry-mac in gpg-agent.conf"),
    ("agent-socket", "start gpg-agent: gpgconf --launch gpg-agent"),
    ("external-cache", "plan task B1, D11 item 3 (owner since erratum E-C8): add no-allow-external-cache to gpg-agent.conf"),
)


def _signing_config(ctx: Context) -> Condition:
    cap = get_capture(ctx.probe["signing"], "config", "util/configure_commit_signing.py run")
    text = stdout_of(cap, "util/configure_commit_signing.py --check --json", (0, 1, 2))
    try:
        doc = json.loads(text)
    except ValueError:
        raise DataError(f"util/configure_commit_signing.py printed no JSON (exit {cap['rc']}): {first_line(str(cap.get('stderr', '')))}") from None
    if not isinstance(doc, dict) or doc.get("schema") != 1 or not isinstance(doc.get("checks"), list):
        raise DataError("util/configure_commit_signing.py printed JSON of an unknown schema")
    checks = doc["checks"]
    errors = [f"{c.get('id')}: {c.get('message')}" for c in checks if c.get("status") == "error"]
    failed = [c for c in checks if c.get("status") == "fail"]
    if errors or doc.get("exit_code") == 2:
        return Condition("signing-config", "error", f"util/configure_commit_signing.py --check could not evaluate: {'; '.join(errors) or doc.get('summary')}")
    if failed or doc.get("exit_code") != 0:
        detail = "; ".join(f"{c.get('id')}: {c.get('message')}" for c in failed) or str(doc.get("summary"))
        return Condition("signing-config", "fail", f"util/configure_commit_signing.py --check: {detail}", failing_remediations([c.get("remediation") for c in failed]) or "python3 util/configure_commit_signing.py --apply (task B4a; owner, from a real terminal)")
    return Condition("signing-config", "pass", f"util/configure_commit_signing.py --check: {doc.get('summary')}")


def gate_sign(ctx: Context) -> list[Condition]:
    conditions = [evaluate("signing-config", lambda: _signing_config(ctx))]
    try:
        cap = get_capture(ctx.probe["signing"], "preflight", "util/headless_signing_preflight.bash run")
        # Exit 1 is expected in an agent session: D11 fails commit-gpgsign there by design.
        text = stdout_of(cap, "util/headless_signing_preflight.bash", (0, 1))
        lines: dict[str, tuple[str, str]] = {}
        for line in text.splitlines():
            match = _PREFLIGHT_RE.fullmatch(line.strip())
            if match:
                lines[match.group(2)] = (match.group(1), match.group(3))
        for cid, fix in PREFLIGHT_CONDITIONS:
            if cid not in lines:
                conditions.append(Condition(cid, "error", f"util/headless_signing_preflight.bash reported no {cid} line"))
            elif lines[cid][0] == "PASS":
                conditions.append(Condition(cid, "pass", lines[cid][1]))
            else:
                conditions.append(Condition(cid, "fail", lines[cid][1], fix))
    except DataError as exc:
        conditions += [Condition(cid, "error", str(exc)) for cid, _ in PREFLIGHT_CONDITIONS]
    conditions.append(evaluate("integration", lambda: _integration(ctx)))
    return conditions


def _integration(ctx: Context) -> Condition:
    rec = ctx.expected["gates"]["G-SIGN"]["integration"]
    if rec is None:
        return Condition(
            "integration",
            "fail",
            "no I-SIGN record: T1-T5 verified (signing plan K10, which widens B5) is not recorded in expected.yaml",
            "after B2 and B3, the owner runs the I-SIGN matrix (K10); K11 records it as G-SIGN.integration",
        )
    if not (ctx.record_base / rec["record"]).is_file():
        return Condition("integration", "fail", f"the I-SIGN record {rec['record']} (dated {rec['date']}) does not exist", "add the record file, or correct G-SIGN.integration.record")
    return Condition("integration", "pass", f"I-SIGN recorded {rec['date']}: {rec['record']}")


# ---------------------------------------------------------------------------------------------------------
# G-SEC
# ---------------------------------------------------------------------------------------------------------
def _status_word(text: str, pattern: str, what: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        raise DataError(f"{what}: no status in {first_line(text)!r}")
    return match.group(1)


def _sip(sec: dict[str, Any]) -> Condition:
    text = stdout_of(get_capture(sec, "sip", "csrutil status"), "csrutil status")
    word = _status_word(text, r"System Integrity Protection status:\s*([A-Za-z]+)", "csrutil status")
    if word == "enabled":
        return Condition("sip", "pass", first_line(text))
    return Condition("sip", "fail", first_line(text), "task C1 (owner): csrutil enable from recoveryOS, then approve the VirtualBox extensions; never csrutil disable (D5)")


def _authenticated_root(sec: dict[str, Any]) -> Condition:
    text = stdout_of(get_capture(sec, "authenticated_root", "csrutil authenticated-root status"), "csrutil authenticated-root status")
    word = _status_word(text, r"Authenticated Root status:\s*([A-Za-z]+)", "csrutil authenticated-root status")
    if word == "enabled":
        return Condition("authenticated-root", "pass", first_line(text))
    return Condition("authenticated-root", "fail", first_line(text), "task C1 (owner): csrutil authenticated-root enable from recoveryOS")


# socketfilterfw --getblockall prints "Firewall <state>." with one of the binary's four block-all states: "is blocking
# all non-essential incoming connections" when on (turing, 2026-10-26, once the owner applied C2), "has block all state
# set to disabled" when off (turing, 2026-10-25), "has unknown block all state" or "is in undefined block all state".
# "Firewall is set to block all non-essential incoming connections" sits beside "Block all DISABLED!" in the strings,
# the shape of --setblockall's on/off confirmations, and turing's getter never printed it: it is not judged.
_BLOCKALL_ON = "is blocking all non-essential incoming connections"
_BLOCKALL_OFF = "has block all state set to disabled"
_C2_FIX = "task C2 (owner): sudo /usr/libexec/ApplicationFirewall/socketfilterfw {steps} (block all incoming connections while nothing inbound is needed; owner ruling 2026-10-25)"


def _blocks_all(text: str) -> bool:
    if _BLOCKALL_ON in text:
        return True
    if _BLOCKALL_OFF in text:
        return False
    raise DataError(f"socketfilterfw --getblockall: no block-all state in {first_line(text)!r}")


def _firewall(sec: dict[str, Any]) -> Condition:
    text = stdout_of(get_capture(sec, "firewall", "socketfilterfw --getglobalstate"), "socketfilterfw --getglobalstate")
    state = _status_word(text, r"State = (\d+)", "socketfilterfw --getglobalstate")
    parts, blocks_all = [first_line(text)], False
    try:
        blockall = stdout_of(get_capture(sec, "blockall", "socketfilterfw --getblockall"), "socketfilterfw --getblockall")
        parts.append(first_line(blockall))
        blocks_all = _blocks_all(blockall)
    except DataError:
        if int(state) != 0:
            raise
        # the firewall is off, so the condition fails whatever the block-all capture says
    try:
        parts.append(first_line(stdout_of(get_capture(sec, "stealth", "socketfilterfw --getstealthmode"), "socketfilterfw --getstealthmode")))
    except DataError:
        pass  # stealth mode is reported only; the gate reads the global and block-all states
    message = "; ".join(parts)
    if int(state) >= 1:
        if blocks_all:
            return Condition("firewall", "pass", message)
        return Condition("firewall", "fail", message, _C2_FIX.format(steps="--setblockall on"))
    return Condition("firewall", "fail", message, _C2_FIX.format(steps="--setglobalstate on, then --setblockall on and --setstealthmode on"))


def _filevault(sec: dict[str, Any]) -> Condition:
    text = stdout_of(get_capture(sec, "filevault", "fdesetup status"), "fdesetup status")
    word = _status_word(text, r"FileVault is (On|Off)", "fdesetup status")
    if word == "On":
        return Condition("filevault", "pass", first_line(text))
    return Condition("filevault", "fail", first_line(text), "turn FileVault on (System Settings > Privacy & Security)")


def _listed(entry: Any, what: str) -> list[str] | None:
    """The paths a find capture printed, or None when the probe had no directory to search."""
    if not isinstance(entry, dict) or "find" not in entry:
        raise DataError(f"the probe recorded no {what}")
    cap = get_capture(entry, "find", what)
    if cap is None:
        return None
    return sorted(line for line in stdout_of(cap, what).splitlines() if line.strip())


def _key_exports(sec: dict[str, Any], home: str) -> Condition:
    paths = _listed(sec.get("key_exports"), "key-export search")
    if paths is None:
        return Condition("key-exports", "pass", "neither ~/.ssh nor ~/.gnupg exists")
    if not paths:
        return Condition("key-exports", "pass", "no *.asc or *recovery* file under ~/.ssh or ~/.gnupg")
    names = ", ".join(tilde(p, home) for p in paths)
    return Condition(
        "key-exports",
        "fail",
        f"{len(paths)} key-export or recovery file(s): {names}",
        "task C3 (owner): plan D4 steps 1-6 (an offline encrypted backup and a test decrypt before any delete; regenerate the GitHub recovery codes; an exposure assessment)",
    )


def _key_modes(sec: dict[str, Any], home: str) -> Condition:
    paths = _listed(sec.get("ssh_loose"), "~/.ssh permission search")
    if paths is None:
        return Condition("key-modes", "pass", "~/.ssh does not exist")
    if not paths:
        return Condition("key-modes", "pass", "no non-public file in ~/.ssh is open to group or others")
    shown = [tilde(p, home) for p in paths]
    return Condition("key-modes", "fail", f"open to group or others: {', '.join(shown)}", "task C4: chmod 600 " + " ".join(shown))


def gate_sec(ctx: Context) -> list[Condition]:
    sec = ctx.probe["security"]
    home = str(ctx.probe.get("home", ""))
    return [
        evaluate("sip", lambda: _sip(sec)),
        evaluate("authenticated-root", lambda: _authenticated_root(sec)),
        evaluate("firewall", lambda: _firewall(sec)),
        evaluate("filevault", lambda: _filevault(sec)),
        evaluate("key-exports", lambda: _key_exports(sec, home)),
        evaluate("key-modes", lambda: _key_modes(sec, home)),
    ]


# ---------------------------------------------------------------------------------------------------------
# G-TOOLS
# ---------------------------------------------------------------------------------------------------------
def _local_bin(ctx: Context) -> Condition:
    tools = ctx.probe["tools"]
    wanted = ctx.expected["gates"]["G-TOOLS"]["local_bin"]
    home = str(ctx.probe.get("home", ""))
    local_bin = str(tools.get("local_bin") or os.path.join(home, ".local", "bin"))
    resolved = tools.get("resolved")
    if not isinstance(resolved, dict):
        raise DataError("the probe resolved no tools")
    problems = []
    for tool in wanted:
        rec = resolved.get(tool)
        if not isinstance(rec, dict) or not isinstance(rec.get("local_bin"), dict):
            raise DataError(f"the probe did not resolve {tool}; run it with --tool {tool}")
        entry = os.path.join(local_bin, tool)
        lb = rec["local_bin"]
        if not lb.get("exists"):
            problems.append(f"{tool}: {tilde(entry, home)} is missing")
        elif not lb.get("executable"):
            link = lb.get("link")
            problems.append(f"{tool}: {tilde(entry, home)} " + (f"is a dangling or non-executable link to {link}" if link else "is not an executable file"))
        elif rec.get("path") != entry:
            where = rec.get("path")
            problems.append(f"{tool}: command -v finds {where}, ahead of {tilde(entry, home)}" if where else f"{tool}: {tilde(local_bin, home)} is not on PATH")
    head = f"{len(wanted) - len(problems)} of {len(wanted)} tools resolve from {tilde(local_bin, home)}"
    if problems:
        return Condition("local-bin", "fail", f"{head}; {'; '.join(problems)}", f"recreate them with the Recreate lines of conf/hosts/{ctx.host}/hosttools-environment.yml (erratum E-D6)")
    return Condition("local-bin", "pass", head)


def _kubectl(ctx: Context) -> Condition:
    cfg = ctx.expected["gates"]["G-TOOLS"]["kubectl"]
    cluster = cfg["cluster"]
    skew = cfg["max_minor_skew"]
    # Decision D7: Docker Desktop installs its own /usr/local/bin/kubectl (turing's 1.22.4 is Docker.app's), so task D3,
    # its upgrade, runs before task D4 (erratum E-H3).
    fix = f"task D3 (owner) first: upgrade Docker Desktop, which installs its own /usr/local/bin/kubectl (decision D7); then task D4: kubectl {cluster}.x, which needs re-planning under the D6 ruling (erratum E-D6)"
    cap = get_capture(ctx.probe["tools"], "kubectl_version", "kubectl version")
    if cap is not None and not cap.get("found"):
        return Condition("kubectl", "fail", "kubectl not found", fix)
    text = stdout_of(cap, "kubectl version --client -o json")
    try:
        client = json.loads(text)["clientVersion"]
        major = int(re.sub(r"\D", "", str(client["major"])))
        minor = int(re.sub(r"\D", "", str(client["minor"])))
    except (ValueError, KeyError, TypeError):
        raise DataError(f"kubectl version --client -o json: no clientVersion major and minor in {first_line(text)!r}") from None
    git_version = client.get("gitVersion") or f"v{major}.{minor}"
    want_major, want_minor = (int(x) for x in _MINOR_RE.fullmatch(cluster).groups())
    if major != want_major:
        return Condition("kubectl", "fail", f"kubectl {git_version} is not major version {want_major}", fix)
    gap = minor - want_minor
    if abs(gap) <= skew:
        return Condition("kubectl", "pass", f"kubectl {git_version} is within {skew} minor of the cluster's {cluster}")
    direction = "behind" if gap < 0 else "ahead of"
    return Condition("kubectl", "fail", f"kubectl {git_version} is {abs(gap)} minors {direction} the cluster's {cluster} (allowed: {skew})", fix)


def gate_tools(ctx: Context) -> list[Condition]:
    return [evaluate("local-bin", lambda: _local_bin(ctx)), evaluate("kubectl", lambda: _kubectl(ctx))]


# ---------------------------------------------------------------------------------------------------------
# G-ENV
# ---------------------------------------------------------------------------------------------------------
def parse_conda_envs(text: str) -> set[str]:
    """Env names in ``conda env list``: the name column, else the directory name of an env under envs/."""
    names = set()
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = _CONDA_RE.fullmatch(line)
        if match is None:
            continue
        if match.group("name"):
            names.add(match.group("name"))
        path = Path(match.group("path"))
        if path.parent.name == "envs":
            names.add(path.name)
    return names


def _conda_envs(ctx: Context) -> Condition:
    wanted = ctx.expected["gates"]["G-ENV"]["conda_envs"]
    cap = get_capture(ctx.probe["env"], "conda", "conda env list")
    fix = f"create each from its spec under conf/hosts/{ctx.host}/ (task E2, decision D8)"
    if cap is not None and not cap.get("found"):
        return Condition("conda-envs", "fail", "conda not found", fix)
    names = parse_conda_envs(stdout_of(cap, "conda env list"))
    missing = [env for env in wanted if env not in names]
    if missing:
        return Condition("conda-envs", "fail", f"{len(wanted) - len(missing)} of {len(wanted)} conda envs exist; missing: {', '.join(missing)}", fix)
    return Condition("conda-envs", "pass", f"all {len(wanted)} conda envs exist: {', '.join(wanted)}")


def _parent_agents_md(ctx: Context) -> Condition:
    rec = ctx.probe["env"].get("parent_agents_md")
    if not isinstance(rec, dict) or "exists" not in rec:
        raise DataError("the probe recorded nothing for the parent AGENTS.md")
    want = ctx.expected["gates"]["G-ENV"]["parent_agents_md"]["sha256"]
    path = tilde(str(rec.get("path")), str(ctx.probe.get("home", "")))
    if not rec["exists"]:
        return Condition("parent-agents-md", "fail", f"{path} is absent", "task E4 (owner): copy yamaguchi's file and record its sha256 here and in HOST.md (decision D9)")
    text = stdout_of(get_capture(rec, "sha256", "parent AGENTS.md sha256"), "shasum -a 256")
    digest = text.split()[0].lower() if text.split() else ""
    if _SHA256_RE.fullmatch(digest) is None:
        raise DataError(f"shasum -a 256 printed no digest: {first_line(text)!r}")
    if want is None:
        return Condition("parent-agents-md", "fail", f"{path} exists (sha256 {digest}), but no hash is recorded", "task E4: record yamaguchi's sha256 as G-ENV.parent_agents_md.sha256 (decision D9)")
    if digest != want:
        return Condition("parent-agents-md", "fail", f"{path} has sha256 {digest}, not the recorded {want}", "re-copy it from yamaguchi, or record the new hash once the change is reviewed (decision D9)")
    return Condition("parent-agents-md", "pass", f"{path} matches the recorded sha256 {want[:12]}...")


def gate_env(ctx: Context) -> list[Condition]:
    return [evaluate("conda-envs", lambda: _conda_envs(ctx)), evaluate("parent-agents-md", lambda: _parent_agents_md(ctx))]


# ---------------------------------------------------------------------------------------------------------
# G-NET
# ---------------------------------------------------------------------------------------------------------
def parse_ifconfig(text: str) -> dict[str, dict[str, Any]]:
    interfaces: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        head = _IFCONFIG_HEAD_RE.match(line)
        if head:
            current = interfaces.setdefault(head.group(1), {"ether": None, "inet": [], "media": None, "status": None})
            continue
        if current is None:
            continue
        words = line.split()
        if not words:
            continue
        if words[0] == "ether" and len(words) > 1:
            current["ether"] = words[1].lower()
        elif words[0] == "inet" and len(words) > 1:
            current["inet"].append(words[1])
        elif words[0] == "media:":
            current["media"] = line.strip()[len("media:") :].strip()
        elif words[0] == "status:":
            current["status"] = line.strip()[len("status:") :].strip()
    return interfaces


def gate_net(ctx: Context) -> list[Condition]:
    cfg = ctx.expected["gates"]["G-NET"]
    name = cfg["interface"]
    conditions: list[Condition] = []
    try:
        interfaces = parse_ifconfig(stdout_of(get_capture(ctx.probe["network"], "ifconfig", "ifconfig -a"), "ifconfig -a"))
    except DataError as exc:
        interfaces = None
        conditions.append(Condition("link", "error", str(exc)))
    iface = interfaces.get(name) if interfaces is not None else None
    if interfaces is not None:
        conditions.append(_link(cfg, name, iface, interfaces))
    conditions.append(_address(cfg, name, iface, interfaces is not None))
    conditions.append(_throughput(ctx, cfg))
    return conditions


def _link(cfg: dict[str, Any], name: str, iface: dict[str, Any] | None, interfaces: dict[str, dict[str, Any]]) -> Condition:
    fix = f"task F2 (owner): a cable, switch port or dongle that links {name} at {cfg['media']}"
    mac = cfg["mac"]
    owner = next((n for n, i in interfaces.items() if mac and i.get("ether") == mac), None)
    if iface is None:
        moved = f"; the dongle {mac} is {owner}: update G-NET.interface" if owner else ""
        return Condition("link", "fail", f"{name} does not exist{moved}", fix)
    if mac and iface.get("ether") != mac:
        moved = f"; the dongle {mac} is {owner}" if owner else f"; no interface has {mac}"
        return Condition("link", "fail", f"{name} is {iface.get('ether')}, not the dongle {mac}{moved}", "find the dongle with networksetup -listallhardwareports, then update G-NET")
    state = f"{name}: media {iface.get('media') or '<none>'}, status {iface.get('status') or '<none>'}"
    if iface.get("status") == "active" and cfg["media"] in (iface.get("media") or ""):
        return Condition("link", "pass", state)
    return Condition("link", "fail", state, fix)


def _address(cfg: dict[str, Any], name: str, iface: dict[str, Any] | None, measured: bool) -> Condition:
    want = cfg["reserved_ip"]
    if want is None:
        return Condition("address", "fail", f"no reserved address is recorded for {name}", "task A6 (owner): a DHCP reservation for the dongle's MAC, recorded as G-NET.reserved_ip and in HOST.md")
    if not measured:
        return Condition("address", "error", "ifconfig -a was not captured")
    have = (iface or {}).get("inet") or []
    if want in have:
        return Condition("address", "pass", f"{name} holds the reserved {want}")
    return Condition("address", "fail", f"{name} holds {', '.join(have) or 'no IPv4 address'}, not the reserved {want}", "check the DHCP reservation (task A6) and the link (task F2)")


def _throughput(ctx: Context, cfg: dict[str, Any]) -> Condition:
    rec = cfg["throughput"]
    floor = cfg["min_mbps"]
    if rec is None:
        return Condition("throughput", "fail", f"not measured: iperf3 to yamaguchi must reach {floor} Mb/s", "task F2: once the link is up, run iperf3 to yamaguchi and record it as G-NET.throughput")
    if not (ctx.record_base / rec["record"]).is_file():
        return Condition("throughput", "fail", f"the throughput record {rec['record']} (dated {rec['date']}) does not exist", "add the record file, or correct G-NET.throughput.record")
    if rec["mbps"] < floor:
        return Condition("throughput", "fail", f"{rec['mbps']:g} Mb/s on {rec['date']} is below {floor} Mb/s ({rec['record']})", "task F2: find the slow hop, then measure again")
    return Condition("throughput", "pass", f"{rec['mbps']:g} Mb/s on {rec['date']} ({rec['record']})")


# ---------------------------------------------------------------------------------------------------------
# G-MEM: util/macvm_ctl.bash's arithmetic
# ---------------------------------------------------------------------------------------------------------
def parse_vm_stat(text: str) -> tuple[int, int, int, int]:
    """(page size, free, speculative, inactive), read by util/macvm_ctl.bash's awk rules.

    The page size is the word after "of" in the first "Mach Virtual Memory Statistics:" line; a count
    is the third word of its "Pages <name>:" row, less one trailing ".", and a repeated row wins.
    """
    page = ""
    counts: dict[str, str] = {}
    for line in text.splitlines():
        words = line.split()
        if not page and line.startswith("Mach Virtual Memory Statistics:"):
            for i in range(len(words) - 1):
                if words[i] == "of":
                    page = words[i + 1]
        if len(words) >= 3 and words[0] == "Pages" and words[1] in ("free:", "speculative:", "inactive:"):
            counts[words[1][:-1]] = words[2].removesuffix(".")
    if _PAGE_SIZE_RE.fullmatch(page) is None:
        raise DataError("vm_stat: no 'page size of N bytes' header")
    if any(_COUNT_RE.fullmatch(counts.get(name, "")) is None for name in ("free", "speculative", "inactive")):
        raise DataError("vm_stat output lacks a 'Pages free', 'Pages speculative' or 'Pages inactive' count")
    return int(page), int(counts["free"]), int(counts["speculative"]), int(counts["inactive"])


def parse_swap_used_mib(text: str) -> tuple[int, str]:
    """Swap used, rounded up to whole MiB, and the token it came from: the word after the first 'used ='."""
    words = text.split()
    token = next((words[i + 2] for i in range(len(words) - 2) if words[i] == "used" and words[i + 1] == "="), "")
    match = _SWAP_TOKEN_RE.fullmatch(token)
    if match is None:
        raise DataError(f"sysctl vm.swapusage: no 'used = <number>K|M|G' in {first_line(text)!r}")
    value = Fraction(match.group(1))
    factor = {"K": Fraction(1, 1024), "M": Fraction(1), "G": Fraction(1024)}[match.group(2)]
    return math.ceil(value * factor), token


def _vm_memory(ctx: Context) -> tuple[int, str]:
    """The VM size the gate uses, MiB: the larger of vm.mem_gib and the registered VM's configured memory."""
    vm_cfg = ctx.expected["vm"]
    mib = vm_cfg["mem_gib"] * 1024
    source = f"vm.mem_gib {vm_cfg['mem_gib']}"
    try:
        cap = get_capture(ctx.probe["vm"], "showvminfo", "VBoxManage showvminfo")
    except DataError:
        return mib, f"{source}; the probe has no showvminfo"
    if cap is None or not cap.get("found"):
        return mib, f"{source}; VirtualBox not found"
    if cap.get("rc") != 0:
        if "Could not find a registered machine" in str(cap.get("stderr", "")):
            return mib, f"{source}; {vm_cfg['name']} is not registered (task F4 creates it)"
        return mib, f"{source}; showvminfo exited {cap.get('rc')}"
    conf = re.search(r"(?m)^memory=(\d+)\s*$", str(cap.get("stdout", "")))
    state = re.search(r'(?m)^VMState="([^"]*)"', str(cap.get("stdout", "")))
    note = f"; {vm_cfg['name']} is {state.group(1)}" if state else ""
    if conf and int(conf.group(1)) > mib:
        return int(conf.group(1)), f"the VM's configured memory, larger than vm.mem_gib {vm_cfg['mem_gib']}{note}"
    return mib, f"{source}{note}"


def gate_mem(ctx: Context) -> list[Condition]:
    mem = ctx.probe["memory"]
    cfg = ctx.expected["gates"]["G-MEM"]
    headroom = "quit applications until macOS has headroom: node mode (task F3); D1 keeps the host admin-only while G-MEM fails"

    def memory() -> Condition:
        page, free, spec, inactive = parse_vm_stat(stdout_of(get_capture(mem, "vm_stat", "vm_stat"), "vm_stat"))
        avail = (free + spec + inactive) * page // MIB
        vm_mib, source = _vm_memory(ctx)
        reserve = cfg["reserve_gib"] * 1024
        need = vm_mib + reserve
        detail = f"(VM {vm_mib} MiB from {source}; reserve {reserve} MiB)"
        if avail >= need:
            return Condition("memory", "pass", f"free + speculative + inactive {avail} MiB >= {need} MiB required {detail}")
        return Condition("memory", "fail", f"free + speculative + inactive {avail} MiB < {need} MiB required {detail}", headroom)

    def swap() -> Condition:
        used, token = parse_swap_used_mib(stdout_of(get_capture(mem, "swapusage", "sysctl vm.swapusage"), "sysctl vm.swapusage"))
        limit = cfg["max_swap_gib"] * 1024
        if used <= limit:
            return Condition("swap", "pass", f"swap used {used} MiB <= {limit} MiB allowed (used = {token})")
        return Condition("swap", "fail", f"swap used {used} MiB > {limit} MiB allowed (used = {token})", headroom)

    def docker() -> Condition:
        entries = mem.get("docker")
        if not isinstance(entries, list) or not entries:
            raise DataError("the probe recorded no Docker Desktop process check")
        running = []
        for entry in entries:
            cap = entry.get("pgrep") if isinstance(entry, dict) else None
            out = stdout_of(cap if isinstance(cap, dict) else None, f"pgrep -x {entry.get('name') if isinstance(entry, dict) else '?'}", (0, 1))
            if cap.get("rc") == 0:
                running.append(f"{entry.get('name')} (pid {' '.join(out.split())})")
        if running:
            return Condition("docker", "fail", f"Docker Desktop is running: {', '.join(running)}", "quit Docker Desktop before node mode (decision D7)")
        return Condition("docker", "pass", "Docker Desktop is not running")

    return [evaluate("memory", memory), evaluate("swap", swap), evaluate("docker", docker)]


GATE_FUNCTIONS: dict[str, Callable[[Context], list[Condition]]] = {
    "G-ALIAS": gate_alias,
    "G-SIGN": gate_sign,
    "G-SEC": gate_sec,
    "G-TOOLS": gate_tools,
    "G-ENV": gate_env,
    "G-NET": gate_net,
    "G-MEM": gate_mem,
}


# ---------------------------------------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------------------------------------
def check_identity(probe: dict[str, Any], expected: dict[str, Any], source: str) -> str:
    hw = probe["hardware"]
    want = expected["identity"]
    measured: dict[str, Any] = {}
    try:
        measured["arch"] = first_line(stdout_of(get_capture(hw, "arch", "uname -m"), "uname -m"))
        for key, cap_key in (("memsize_bytes", "memsize"), ("physicalcpu", "physicalcpu"), ("ncpu", "ncpu")):
            text = first_line(stdout_of(get_capture(hw, cap_key, f"sysctl hw.{cap_key}"), f"sysctl -n hw.{cap_key}"))
            if not text.isdigit():
                raise DataError(f"sysctl -n hw.{cap_key} printed {text!r}")
            measured[key] = int(text)
    except DataError as exc:
        raise IdentityError(f"cannot establish this host's identity from {source}: {exc}") from None
    wrong = [f"{key} {measured[key]!r}, expected {want[key]!r}" for key in ("arch", "memsize_bytes", "physicalcpu", "ncpu") if measured[key] != want[key]]
    if wrong:
        raise IdentityError(f"{source} describes another machine than {expected['host']}'s expected.yaml: {'; '.join(wrong)}")
    return f"{measured['arch']}, {measured['physicalcpu']} cores / {measured['ncpu']} threads, hw.memsize {measured['memsize_bytes']} ({_gib(measured['memsize_bytes'])} GiB)"


# ---------------------------------------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------------------------------------
def normalise_gate(value: str) -> str:
    name = value.strip().upper()
    if not name.startswith("G-"):
        name = "G-" + name
    if name in GATES:
        return name
    for gid, where in NOT_EVALUATED:
        if name == gid:
            raise UsageError(f"{gid} is not evaluated here: {where}")
    raise UsageError(f"unknown gate {value!r}; known: {', '.join(GATES)}")


def build_parser() -> _Parser:
    parser = _Parser(
        prog="host_state_check.py",
        description="Evaluate this host against conf/hosts/<host>/expected.yaml: the host gates of plan §9.3 (turing bring-up task G1).",
        epilog="Exit codes: 0 the report was produced (--check: every gate passed), 1 --check and a gate failed, 2 a gate could not be evaluated (--check) or a usage or environment error.",
    )
    parser.add_argument("--host", metavar="NAME", help="the host to evaluate (default: this machine's short hostname)")
    parser.add_argument("--expected", metavar="FILE", help="the expected-state file (default: conf/hosts/<host>/expected.yaml)")
    parser.add_argument("--probe-json", metavar="FILE", help="evaluate this saved probe output instead of running the probe")
    parser.add_argument("--root", metavar="DIR", help="the Juniper root passed to the probe (default: $JUNIPER_ROOT, else ~/Development/python/Juniper)")
    parser.add_argument("--section", action="append", metavar="GATE", help="evaluate only this gate (G-MEM, g-mem or mem); repeatable")
    parser.add_argument("--check", action="store_true", help="gate mode: exit 1 while a gate fails, 2 when one cannot be evaluated")
    parser.add_argument("--json", action="store_true", help="print one JSON object instead of the report")
    return parser


def startup_error(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def exit_code(gates: list[GateResult], check: bool) -> int:
    """Under --check, 2 when any condition could not be evaluated (even in a failed gate), else 1 on a failure."""
    if not check:
        return 0
    statuses = {c.status for g in gates for c in g.conditions}
    if "error" in statuses:
        return 2
    if "fail" in statuses:
        return 1
    return 0


def summary_line(gates: list[GateResult]) -> str:
    passed = [g.id for g in gates if g.status == "pass"]
    failed = [g.id for g in gates if g.status == "fail"]
    errors = [g.id for g in gates if g.status == "error"]
    text = f"readiness: {len(passed)} of {len(gates)} gates pass"
    if passed and (failed or errors):
        text += f" ({', '.join(passed)})"
    if failed:
        text += f"; {len(failed)} fail: {', '.join(failed)}"
    if errors:
        text += f"; {len(errors)} could not be evaluated: {', '.join(errors)}"
    return text


def emit(result: dict[str, Any], gates: list[GateResult], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return
    probe = result["probe"]
    print(f"host:      {result['host']}, against {display(result['expected'])}")
    print(f"probe:     {display(probe['path'])} ({'saved' if probe['source'] == 'file' else 'run now'}), collected {probe['collected_at']} on {probe['node']}")
    print(f"identity:  {result['identity']}")
    for gate in gates:
        print()
        print(f"{STATUS_LABEL[gate.status]:<5} {gate.id}  {gate.summary()}")
        for cond in gate.conditions:
            line = f"  {STATUS_LABEL[cond.status]:<5} {cond.id:<18} {cond.message}"
            if cond.status != "pass" and cond.remediation:
                line += f" -- fix: {cond.remediation}"
            print(line)
    if result["not_evaluated"]:
        print()
        print("not evaluated here:")
        for item in result["not_evaluated"]:
            print(f"  {item['id']:<8} {item['where']}")
    print()
    print(result["summary"])


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        selected = list(GATES)
        if args.section:
            wanted = {normalise_gate(v) for v in args.section}
            selected = [g for g in GATES if g in wanted]
        if args.host is not None and _NAME_RE.fullmatch(args.host) is None:
            raise UsageError(f"not a host name: {args.host!r} (lower-case letters, digits and '-')")
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Run with --help for usage.", file=sys.stderr)
        return 2

    host = args.host or socket.gethostname().split(".")[0].lower()
    expected_path = Path(args.expected) if args.expected else REPO_ROOT / "conf" / "hosts" / host / "expected.yaml"
    try:
        if not args.expected and _NAME_RE.fullmatch(host) is None:
            raise ExpectedError(f"this machine's short hostname {host!r} is not a host name; pass --host")
        expected = load_expected(expected_path)
        if (args.expected is None or args.host is not None) and expected["host"] != host:
            raise ExpectedError(f"{display(expected_path)} describes host {expected['host']!r}, not {host!r}")
    except ExpectedError as exc:
        return startup_error(str(exc))
    host = expected["host"]

    sections = ["hardware"] + [s for s in PROBE_SECTIONS if any(s in GATE_SECTIONS[g] for g in selected)]
    root = os.path.abspath(os.path.expanduser(args.root or os.environ.get("JUNIPER_ROOT") or os.path.join("~", "Development", "python", "Juniper")))
    try:
        if args.probe_json:
            source = display(args.probe_json)
            try:
                raw = Path(args.probe_json).read_bytes()
            except OSError as exc:
                raise ProbeError(f"cannot read {args.probe_json}: {exc.strerror or exc}") from None
            probe = parse_probe(raw, source)
            probe_path = str(Path(args.probe_json).resolve())
        else:
            tools = expected["gates"]["G-TOOLS"]["local_bin"] if "G-TOOLS" in selected else []
            probe, probe_path = run_probe(sections, tools, expected["vm"]["name"], root)
            source = "the probe's output"
        require_sections(probe, sections, source)
        identity = check_identity(probe, expected, source)
    except (ProbeError, IdentityError) as exc:
        return startup_error(str(exc))

    ctx = Context(host=host, expected=expected, record_base=record_base(expected_path), probe=probe)
    gates = [GateResult(gid, GATE_FUNCTIONS[gid](ctx)) for gid in selected]
    code = exit_code(gates, args.check)
    result = {
        "schema": SCHEMA_VERSION,
        "mode": "check" if args.check else "report",
        "host": host,
        "expected": str(expected_path.resolve()),
        "probe": {"source": "file" if args.probe_json else "run", "path": probe_path, "collected_at": str(probe.get("collected_at")), "node": str(probe.get("node"))},
        "identity": identity,
        "gates": [g.as_json() for g in gates],
        "not_evaluated": [] if args.section else [{"id": gid, "where": where} for gid, where in NOT_EVALUATED],
        "readiness": {"passed": sum(g.status == "pass" for g in gates), "evaluated": len(gates)},
        "ok": code == 0,
        "exit_code": code,
        "summary": summary_line(gates),
    }
    emit(result, gates, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
