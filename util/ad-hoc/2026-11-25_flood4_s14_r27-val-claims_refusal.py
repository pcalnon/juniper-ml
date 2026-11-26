"""
Measure what httpx raises, and what canopy's probe_dependency reports, for a connect the kernel refuses.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r27 (juniper-canopy unit-lane :8100 connects)

Usage (run with the interpreter of the venv under test):
    python -I <this file> <canopy src dir> <output json path>

No connect can reach a live listener. The script binds one ephemeral port on 127.0.0.1 and, when it can, the same
port on ::1, WITHOUT listening on either, so the kernel refuses a connect to it the way an empty host refuses :8100. No
Juniper port is touched. For http://127.0.0.1:<port>/ and http://localhost:<port>/ it records the exception type,
str() and the chained cause httpx raises, and the DependencyStatus canopy's health.probe_dependency returns, and it
checks how this host resolves localhost.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys
from pathlib import Path


def _bind_unlistened() -> tuple[int, list[socket.socket], list[str]]:
    held: list[socket.socket] = []
    notes: list[str] = []
    v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    v4.bind(("127.0.0.1", 0))
    port = v4.getsockname()[1]
    held.append(v4)
    try:
        v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        v6.bind(("::1", port))
        held.append(v6)
    except OSError as exc:
        notes.append(f"::1 bind of port {port} failed: {type(exc).__name__}: {exc}")
    return port, held, notes


async def _attempt(url: str) -> dict:
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
        return {"url": url, "raised": None, "status_code": response.status_code}
    except Exception as exc:  # noqa: BLE001 - the point is to record whatever is raised
        cause = exc.__cause__
        return {
            "url": url,
            "raised": type(exc).__module__ + "." + type(exc).__qualname__,
            "str": str(exc),
            "cause": None if cause is None else type(cause).__module__ + "." + type(cause).__qualname__ + ": " + str(cause),
        }


async def _probe(url: str) -> dict:
    from health import probe_dependency

    status = await probe_dependency("JuniperData", url)
    return {"url": url, "status": status.status, "message": status.message}


def main() -> int:
    src_dir, out_path = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    sys.path.insert(0, str(src_dir))
    port, held, notes = _bind_unlistened()
    try:
        resolved = sorted({(info[0].name, info[4][0]) for info in socket.getaddrinfo("localhost", port, type=socket.SOCK_STREAM)})
        urls = [f"http://127.0.0.1:{port}/v1/health/live", f"http://localhost:{port}/v1/health/live"]
        attempts = [asyncio.run(_attempt(url)) for url in urls]
        probes = [asyncio.run(_probe(url)) for url in urls]
    finally:
        for sock in held:
            sock.close()
    result = {"port": port, "bound_families": len(held), "notes": notes, "localhost_resolves_to": resolved, "attempts": attempts, "probes": probes}
    out_path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
