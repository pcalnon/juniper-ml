#!/usr/bin/env python3
"""
A delaying TCP relay in front of juniper-data, for W1.5's live "40 s data server" check.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W1.5 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         tests/test_recurrence_operation_identity_and_dataset_budget.py (the scaled, hermetic version)

Relays every connection, byte for byte, to one fixed upstream ``--upstream-host:--upstream-port``. When the
connection's first request line matches ``--slow`` (a regex; by default the artifact download, which is the
only juniper-data call a recurrence service makes for a ``dataset_id`` ref) it sleeps ``--delay`` seconds
before connecting upstream. It is a relay rather than an HTTP proxy on purpose: no URL is ever built from what
a client sent, and the upstream is only ever the address given on the command line.

Run it in front of a real juniper-data, bring a recurrence service up with
``util/experiment_stack.bash --up --recurrence --shared-data http://127.0.0.1:<port>``, and drive a run: the
service's inner client then waits ``--delay`` seconds for the artifact, under whatever
``JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS`` that launch gave it. A timed-out client opens a new
connection for its retry, so every attempt is delayed. Each connection is logged to stderr with its first
request line, whether it was delayed, and how long it lasted.

Usage:
    python3 util/ad-hoc/2026-10-08_w15_slow_data_proxy.py --upstream-port 8110 --port 8297 --delay 40
"""

from __future__ import annotations

import argparse
import re
import socket
import socketserver
import sys
import threading
import time

#: The most a request head may take before the relay gives up on finding its end.
MAX_HEAD_BYTES = 65536


def _pump(source: socket.socket, sink: socket.socket) -> None:
    """Copy bytes from ``source`` to ``sink`` until ``source`` closes, then half-close ``sink``."""
    try:
        while True:
            chunk = source.recv(65536)
            if not chunk:
                break
            sink.sendall(chunk)
    except OSError as exc:  # either side went away mid-copy: the relay is done with this direction
        print(f"  relay direction ended: {exc}", file=sys.stderr, flush=True)
    try:
        sink.shutdown(socket.SHUT_WR)
    except OSError as exc:  # the peer is already gone
        print(f"  relay half-close skipped: {exc}", file=sys.stderr, flush=True)


class _Relay(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port: int, upstream_host: str, upstream_port: int, slow: "re.Pattern[str]", delay: float) -> None:
        super().__init__(("127.0.0.1", port), _Handler)
        self.upstream = (upstream_host, upstream_port)
        self.slow = slow
        self.delay = delay


class _Handler(socketserver.BaseRequestHandler):
    server: _Relay

    def handle(self) -> None:
        started = time.monotonic()
        client: socket.socket = self.request
        head = b""
        while b"\r\n\r\n" not in head and len(head) < MAX_HEAD_BYTES:
            chunk = client.recv(4096)
            if not chunk:
                return
            head += chunk
        request_line = head.split(b"\r\n", 1)[0].decode("latin-1")
        delayed = bool(self.server.slow.search(request_line))
        if delayed:
            time.sleep(self.server.delay)
        with socket.create_connection(self.server.upstream, timeout=600) as upstream:
            upstream.sendall(head)
            outbound = threading.Thread(target=_pump, args=(client, upstream), daemon=True)
            outbound.start()
            _pump(upstream, client)
            outbound.join(timeout=5)
        print(f"{request_line} -> relayed in {time.monotonic() - started:.1f}s{' (delayed)' if delayed else ''}", file=sys.stderr, flush=True)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--upstream-host", default="127.0.0.1", help="the real juniper-data host (default 127.0.0.1)")
    parser.add_argument("--upstream-port", type=int, required=True, help="the real juniper-data port")
    parser.add_argument("--port", type=int, required=True, help="loopback port to listen on")
    parser.add_argument("--delay", type=float, default=40.0, help="seconds to sleep before relaying a matching connection (default 40)")
    parser.add_argument("--slow", default=r"^GET /v1/datasets/[^/ ]+/artifact ", help="regex over the first request line selecting the delayed connections")
    args = parser.parse_args(argv)
    relay = _Relay(args.port, args.upstream_host, args.upstream_port, re.compile(args.slow), args.delay)
    print(f"relay 127.0.0.1:{args.port} -> {args.upstream_host}:{args.upstream_port}; delaying {args.slow!r} by {args.delay:g}s", file=sys.stderr, flush=True)
    try:
        relay.serve_forever()
    except KeyboardInterrupt:
        print("relay stopped", file=sys.stderr)
    finally:
        relay.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
