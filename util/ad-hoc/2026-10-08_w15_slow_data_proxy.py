#!/usr/bin/env python3
"""
A delaying reverse proxy in front of juniper-data, for W1.5's live "40 s data server" check.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W1.5 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         tests/test_recurrence_operation_identity_and_dataset_budget.py (the scaled, hermetic version)

Forwards every request to ``--upstream`` unchanged, after sleeping ``--delay`` seconds when the path matches
``--slow`` (a regex; by default the artifact download, which is the only juniper-data call a recurrence service
makes for a ``dataset_id`` ref). Run it in front of a real juniper-data, bring a recurrence service up with
``util/experiment_stack.bash --up --recurrence --shared-data http://127.0.0.1:<port>``, and drive a run: the
service's inner client then waits ``--delay`` seconds for the artifact, under whatever
``JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS`` that launch gave it. Each request is logged to stderr with
its path, status and seconds.

Usage:
    python3 util/ad-hoc/2026-10-08_w15_slow_data_proxy.py --upstream http://127.0.0.1:8110 --port 8139 --delay 40
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

#: Request headers passed upstream; everything else (Host, Connection, ...) is the proxy's own.
FORWARDED_REQUEST_HEADERS = ("Accept", "Content-Type", "X-API-Key", "X-Request-ID")
#: Response headers passed back to the caller.
FORWARDED_RESPONSE_HEADERS = ("Content-Type", "Content-Disposition", "ETag", "Last-Modified")


class _Proxy(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, upstream: str, slow: "re.Pattern[str]", delay: float) -> None:
        super().__init__(("127.0.0.1", port), _Handler)
        self.upstream = upstream.rstrip("/")
        self.slow = slow
        self.delay = delay


class _Handler(BaseHTTPRequestHandler):
    server: _Proxy

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - http.server API; this script logs its own lines
        return

    def _forward(self) -> None:
        started = time.monotonic()
        path = self.path
        delayed = bool(self.server.slow.search(path.split("?", 1)[0]))
        if delayed:
            time.sleep(self.server.delay)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {name: self.headers[name] for name in FORWARDED_REQUEST_HEADERS if self.headers.get(name) is not None}
        request = urllib.request.Request(f"{self.server.upstream}{path}", data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(request, timeout=600) as resp:  # nosec B310 - loopback upstream named on the command line
                status, reply_headers, payload = resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as exc:
            status, reply_headers, payload = exc.code, exc.headers, exc.read()
        try:
            self.send_response(status)
            for name in FORWARDED_RESPONSE_HEADERS:
                if reply_headers.get(name) is not None:
                    self.send_header(name, reply_headers[name])
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            outcome = str(status)
        except (BrokenPipeError, ConnectionResetError):
            outcome = f"{status}, but the caller had already gone"
        print(f"{self.command} {path} -> {outcome} in {time.monotonic() - started:.1f}s{' (delayed)' if delayed else ''}", file=sys.stderr, flush=True)

    do_GET = _forward  # noqa: N815 - http.server dispatches on these names
    do_POST = _forward  # noqa: N815
    do_DELETE = _forward  # noqa: N815


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--upstream", required=True, help="the real juniper-data base URL")
    parser.add_argument("--port", type=int, required=True, help="loopback port to listen on")
    parser.add_argument("--delay", type=float, default=40.0, help="seconds to sleep before forwarding a matching request (default 40)")
    parser.add_argument("--slow", default=r"^/v1/datasets/[^/]+/artifact$", help="regex over the request path selecting the delayed requests")
    args = parser.parse_args(argv)
    proxy = _Proxy(args.port, args.upstream, re.compile(args.slow), args.delay)
    print(f"proxy 127.0.0.1:{args.port} -> {proxy.upstream}; delaying {args.slow!r} by {args.delay:g}s", file=sys.stderr, flush=True)
    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        print("proxy stopped", file=sys.stderr)
    finally:
        proxy.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
