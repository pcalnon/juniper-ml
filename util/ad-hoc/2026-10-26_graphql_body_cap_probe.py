#!/usr/bin/env python3
"""Probe GitHub's GraphQL endpoint for the request-body sizes it accepts (follow-up to juniper-ml#2227).

Project:      juniper-ml
Sub-Project:  release train
Application:  GraphQL request-body cap probe
Author:       Paul Calnon
Created:      2026-10-26
License:      MIT License
Status:       ad-hoc — investigation (a single-use measurement)
Retire when:  RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      juniper-ml#2227; reports/2026-10-26_graphql-body-cap-probe/ (runner run 40410086979)

Why this exists
---------------
``util/release_train/ceremony.py`` HALTs ``archive-too-large`` when a release-notes archive's base64
exceeds ``ARCHIVE_B64_MAX_DEFAULT`` (125,000 B), because the archive travels inside ONE
``createCommitOnBranch`` request. That default is the figure measured from turing on 2026-10-17
(130,000 B accepted, 131,000 B refused with HTTP 499), later re-diagnosed as turing's link: GitHub's
GraphQL frontend drops a request that runs past about 7-10 s. The owner ruled on 2026-10-18 to keep the
conservative figure as the default, and to let ``JUNIPER_RELEASE_TRAIN_ARCHIVE_B64_MAX`` override it
"once a runner-side measurement settles the real cap". This is that measurement's instrument. It runs
the same way on a workstation and on a GitHub-hosted runner, so the two can be compared.

What it sends
-------------
Read-only requests, one per size and mode. Each is a no-op query, and the request's transport is what
gets measured:

* ``comment``: ``query { rateLimit { remaining } }`` followed by a ``#`` comment, padded so the JSON body
  is exactly N bytes. This was turing's 2026-10-17 method, so the two runs can be compared.
* ``variable``: the same query, with the padding in a declared String variable. This is how
  ``createCommitOnBranch`` carries its base64 ``contents``. The variable is never used, so GitHub may
  answer with a validation error. An HTTP 200 carrying GraphQL JSON still proves the whole body was
  received and parsed, which is the property under test.

For each request the probe records the HTTP status (or the exception), the elapsed seconds, and whether
the reply was GraphQL JSON. With ``--bisect`` it then narrows each boundary it found, where one size was
accepted and the next refused, to within 1%.

Usage
-----
    python3 util/ad-hoc/2026-10-26_graphql_body_cap_probe.py [--sizes 131072,262144,...]
        [--mode comment|variable|both] [--bisect] [--timeout 60] [--json OUT]

The token comes from ``GITHUB_TOKEN`` or ``GH_TOKEN``, else from ``gh auth token``. It is never printed.
Exit 0 when every request completed (accepted or refused alike), 2 on misuse or a missing token.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

GRAPHQL_URL = "https://api.github.com/graphql"
DEFAULT_SIZES = (100_000, 125_000, 130_000, 131_000, 140_000, 262_144, 524_288, 1_048_576, 2_097_152, 4_194_304, 8_388_608)
COMMENT_QUERY = "query { rateLimit { remaining } }"
VARIABLE_QUERY = "query($pad: String) { rateLimit { remaining } }"
PAD_CHAR = "A"  # in the base64 alphabet, like the archive the ceremony sends


def _token() -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    try:
        out = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip()


def build_body(mode: str, size: int) -> bytes:
    """A JSON request body of exactly ``size`` bytes (or the smallest possible, when ``size`` is below it)."""

    def render(pad: int) -> bytes:
        if mode == "comment":
            payload = {"query": COMMENT_QUERY + "\n#" + PAD_CHAR * pad}
        else:
            payload = {"query": VARIABLE_QUERY, "variables": {"pad": PAD_CHAR * pad}}
        return json.dumps(payload, separators=(",", ":")).encode("ascii")

    base = len(render(0))
    return render(max(0, size - base))


def send(token: str, body: bytes, timeout: float) -> dict:
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "juniper-ml-graphql-body-cap-probe",
        },
    )
    started = time.monotonic()
    result = {"bytes": len(body), "status": None, "graphql_json": False, "error": None}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result["status"] = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        result["status"] = exc.code
        raw = exc.read() if exc.fp else b""
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as exc:
        result["error"] = f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}"
        raw = b""
    result["seconds"] = round(time.monotonic() - started, 2)
    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = None
    if isinstance(parsed, dict) and ("data" in parsed or "errors" in parsed):
        result["graphql_json"] = True
        errors = parsed.get("errors") or []
        if errors:
            result["graphql_error"] = str(errors[0].get("message", ""))[:160]
    elif raw:
        result["body_head"] = raw[:160].decode("utf-8", "replace")
    result["accepted"] = result["status"] == 200 and result["graphql_json"]
    return result


def bisect(token: str, mode: str, ok_size: int, bad_size: int, timeout: float) -> list:
    """Narrow [ok_size, bad_size] to within 1%, probing the midpoint each round."""
    trail = []
    while bad_size - ok_size > max(1024, ok_size // 100):
        mid = (ok_size + bad_size) // 2
        row = send(token, build_body(mode, mid), timeout)
        row["mode"] = mode
        trail.append(row)
        _print_row(row)
        if row["accepted"]:
            ok_size = mid
        else:
            bad_size = mid
    return trail


def _print_row(row: dict) -> None:
    outcome = "ACCEPTED" if row["accepted"] else "REFUSED"
    detail = row.get("error") or row.get("graphql_error") or row.get("body_head") or ""
    print(f"  {row['mode']:<8} {row['bytes']:>10,} B  HTTP {row['status']!s:<4} {row['seconds']:>7.2f}s  {outcome:<8} {detail}", flush=True)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--sizes", default=",".join(str(s) for s in DEFAULT_SIZES), help="comma-separated body sizes in bytes")
    parser.add_argument("--mode", choices=("comment", "variable", "both"), default="both")
    parser.add_argument("--bisect", action="store_true", help="narrow every accepted->refused boundary to within 1%%")
    parser.add_argument("--timeout", type=float, default=60.0, help="per-request timeout in seconds")
    parser.add_argument("--json", dest="json_out", help="also write every result to this file")
    args = parser.parse_args(argv)
    try:
        sizes = sorted({int(s) for s in args.sizes.split(",") if s.strip()})
    except ValueError:
        print(f"--sizes must be comma-separated integers, got {args.sizes!r}", file=sys.stderr)
        return 2
    token = _token()
    if not token:
        print("no token: set GITHUB_TOKEN or GH_TOKEN, or log in with `gh auth login`", file=sys.stderr)
        return 2
    modes = ("comment", "variable") if args.mode == "both" else (args.mode,)
    where = "GitHub-hosted runner" if os.environ.get("GITHUB_ACTIONS") == "true" else "workstation"
    print(f"GraphQL body-cap probe ({where}; {GRAPHQL_URL}; timeout {args.timeout:g}s)")
    results = []
    for mode in modes:
        rows = []
        for size in sizes:
            row = send(token, build_body(mode, size), args.timeout)
            row["mode"] = mode
            rows.append(row)
            _print_row(row)
        if args.bisect:
            for before, after in zip(rows, rows[1:]):
                if before["accepted"] and not after["accepted"]:
                    rows.extend(bisect(token, mode, before["bytes"], after["bytes"], args.timeout))
        accepted = [r["bytes"] for r in rows if r["accepted"]]
        refused = [r["bytes"] for r in rows if not r["accepted"]]
        print(f"  {mode}: largest accepted {max(accepted):,} B" if accepted else f"  {mode}: nothing accepted", end="")
        print(f"; smallest refused {min(refused):,} B" if refused else "; nothing refused", flush=True)
        results.extend(rows)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump({"where": where, "url": GRAPHQL_URL, "results": results}, handle, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
