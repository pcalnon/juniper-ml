"""
Bypass probes for carrier r27 (juniper-canopy's unit-lane juniper-data fake + 8100 guard): every other way a guarded
unit test could reach juniper-data's :8100. Copied into a PROBE TREE as src/tests/unit/test_r27v2_bypass_probe.py and
run there under the carrier's conftest; never added to canopy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2

Safety: nothing listens on :8100 (ss -ltnp before every run); the lens's census fence also refuses every :8100 connect
in this process and in every child interpreter. Each probe records (to $R27V2_PROBE_OUT) what the caller saw, what the
guard refused (claimed with take(), so the guard does not fail the probe) and what the fake answered, then asserts the
SAFE outcome: a failing probe is a hole. The two probes of documented blind spots (a child process, a raw _socket
connect) assert nothing about the guard and only record.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess  # nosec B404 - a probe of the guard's documented child-process blind spot
import sys
import urllib.request

import httpx
import pytest
import requests

pytestmark = pytest.mark.unit
OUT = os.environ.get("R27V2_PROBE_OUT")
URL = "http://127.0.0.1:8100/v1/health/live"


def _record(name: str, **data) -> None:
    if OUT:
        with open(OUT, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"probe": name, **data}, default=str) + "\n")


def _attempt(fn) -> str:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - the probe records whatever the caller saw (every recorded raise is an Exception)
        return f"{type(exc).__name__}: {exc}"[:200]
    return "no exception"


def _check(name, fn, guard, fake):
    outcome = _attempt(fn)
    refused, answered = guard.take(), list(fake.answered)
    _record(name, outcome=outcome, guard_refused=refused, fake_answered=answered)
    return outcome, refused, answered


# P13 first: the module-scoped ``client`` is built by the first test that asks for it.
@pytest.mark.allow_service_ports
def test_p13a_an_opted_out_test_builds_the_shared_app(client, service_port_guard, juniper_data_fake):
    """allow_service_ports disarms the guard AND the fake, so the shared app's startup probe goes to the real network."""
    import main

    _record("p13a allow_service_ports test is the module's first client user", guard_armed_for=service_port_guard.armed_for, fake_answered=list(juniper_data_fake.answered), juniper_data_available=main.juniper_data_available)
    assert juniper_data_fake.answered == []  # the startup probe was NOT answered by the fake: it went to a socket


def test_p13b_a_later_guarded_test_inherits_that_startup_verdict(client, juniper_data_fake):
    body = client.get("/v1/health").json()
    _record("p13b guarded test sharing that app", juniper_data_available=body["juniper_data_available"], fake_answered=list(juniper_data_fake.answered))


def test_p1_sync_httpx_client(service_port_guard, juniper_data_fake):
    _o, refused, answered = _check("p1 sync httpx 127.0.0.1:8100", lambda: httpx.get(URL, timeout=2.0), service_port_guard, juniper_data_fake)
    assert answered == [] and refused, "a sync httpx request must reach the guard (the fake patches only the async transport)"


def test_p2_requests_localhost(service_port_guard, juniper_data_fake):
    _o, refused, _a = _check("p2 requests localhost:8100", lambda: requests.get("http://localhost:8100/v1/health/live", timeout=2.0), service_port_guard, juniper_data_fake)
    assert refused


def test_p3_urllib(service_port_guard, juniper_data_fake):
    _o, refused, _a = _check("p3 urllib 127.0.0.1:8100", lambda: urllib.request.urlopen(URL, timeout=2.0), service_port_guard, juniper_data_fake)  # nosec B310 - a fixed http URL
    assert refused


async def test_p4_websockets(service_port_guard, juniper_data_fake):
    import websockets

    async def go():
        async with websockets.connect("ws://127.0.0.1:8100/ws", open_timeout=2):
            pass

    try:
        await go()
        outcome = "no exception"
    except Exception as exc:  # noqa: BLE001
        outcome = f"{type(exc).__name__}: {exc}"[:200]
    refused = service_port_guard.take()
    _record("p4 websockets ws://127.0.0.1:8100", outcome=outcome, guard_refused=refused, fake_answered=list(juniper_data_fake.answered))
    assert refused


@pytest.mark.parametrize("host", ["::1", "0.0.0.0", "localhost"])  # nosec B104 - connect destinations, never bound
def test_p5_raw_socket_hosts(host, service_port_guard, juniper_data_fake):
    _o, refused, _a = _check(f"p5 socket.create_connection {host}:8100", lambda: socket.create_connection((host, 8100), timeout=2).close(), service_port_guard, juniper_data_fake)
    assert refused


def test_p6_connect_ex(service_port_guard, juniper_data_fake):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = sock.connect_ex(("127.0.0.1", 8100))
    refused = service_port_guard.take()
    _record("p6 connect_ex 127.0.0.1:8100", outcome=result, guard_refused=refused)
    assert refused


async def test_p7_asyncio_open_connection(service_port_guard, juniper_data_fake):
    try:
        await asyncio.wait_for(asyncio.open_connection("127.0.0.1", 8100), 2)
        outcome = "no exception"
    except Exception as exc:  # noqa: BLE001
        outcome = f"{type(exc).__name__}: {exc}"[:200]
    refused = service_port_guard.take()
    _record("p7 asyncio.open_connection 127.0.0.1:8100", outcome=outcome, guard_refused=refused, fake_answered=list(juniper_data_fake.answered))
    assert refused


def test_p8_raw_underscore_socket_is_a_documented_blind_spot(service_port_guard):
    import _socket

    def go():
        raw = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        try:
            raw.connect(("127.0.0.1", 8100))
        finally:
            raw.close()

    outcome = _attempt(go)
    _record("p8 _socket.socket.connect 127.0.0.1:8100 (documented blind spot)", outcome=outcome, guard_refused=service_port_guard.take())


def test_p9_child_process_is_a_documented_blind_spot(service_port_guard):
    code = "import socket; s = socket.socket(); print(s.connect_ex(('127.0.0.1', 8100)))"
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False)  # nosec B603
    _record("p9 child interpreter connect_ex 127.0.0.1:8100 (documented blind spot)", child_stdout=proc.stdout.strip(), child_exit=proc.returncode, guard_refused=service_port_guard.take())
