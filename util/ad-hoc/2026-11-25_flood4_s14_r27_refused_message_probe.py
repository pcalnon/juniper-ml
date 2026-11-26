"""
Print what httpx raises, and what canopy's probe_dependency reports, when a connect is refused (no listener).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects

Usage (run with the interpreter of the venv under test):
    python -I <this file> <canopy src dir>

No connect leaves this process for a real listener: the script binds an ephemeral port on 127.0.0.1 and ::1 WITHOUT
listening, so a connect to it is refused by the kernel the way an empty host refuses :8100 (no Juniper port is
touched). It prints, as JSON, the exception type and message httpx raises for http://localhost:<port>/ and
http://127.0.0.1:<port>/, and the DependencyStatus canopy's health.probe_dependency returns for each.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys


def _bound_not_listening() -> tuple[int, list[socket.socket]]:
    held = []
    v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    v4.bind(("127.0.0.1", 0))
    held.append(v4)
    port = v4.getsockname()[1]
    v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        v6.bind(("::1", port))
        held.append(v6)
    except OSError as exc:  # no IPv6 loopback, or the port is taken there: the IPv4 socket is enough
        print(f"IPv6 loopback not bound ({exc.strerror}); probing IPv4 only", file=sys.stderr)
        v6.close()
    return port, held


async def _probe(src: str, port: int) -> dict:
    sys.path.insert(0, src)
    import httpx
    from health import probe_dependency

    result = {"httpx": httpx.__version__}
    for host in ("localhost", "127.0.0.1"):
        url = f"http://{host}:{port}/v1/health/live"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(url)
            result[f"raw_{host}"] = "no exception"
        except Exception as exc:  # noqa: BLE001 - the point is to print it
            result[f"raw_{host}"] = {"type": type(exc).__name__, "message": str(exc)}
        status = await probe_dependency("JuniperData", url)
        result[f"probe_{host}"] = {"status": status.status, "message": status.message.replace(str(port), "<port>")}
    return result


def main() -> int:
    port, held = _bound_not_listening()
    try:
        print(json.dumps(asyncio.run(_probe(sys.argv[1], port)), indent=1))
    finally:
        for sock in held:
            sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
