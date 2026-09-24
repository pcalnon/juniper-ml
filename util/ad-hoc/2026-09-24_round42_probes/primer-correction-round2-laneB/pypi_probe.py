#!/usr/bin/env python3
"""Public PyPI reads for round-2 Lane B: pinned-toolchain availability and juniper-data's latest release.

Read-only: GETs https://pypi.org/pypi/<name>/json and prints versions and upload times.
"""
from __future__ import annotations

import json
import urllib.request

PINS = {"fastapi": "0.141.1", "starlette": "1.6.0", "pydantic": "2.13.4", "httpx": "0.28.1"}


def get(name: str) -> dict:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=30) as r:  # noqa: S310 - fixed https host
        return json.load(r)


def main() -> int:
    for name, want in PINS.items():
        d = get(name)
        print(f"{name:10s} latest={d['info']['version']:10s} pinned={want:8s} {'present' if want in d['releases'] else 'ABSENT'}")
    d = get("juniper-data")
    print(f"juniper-data latest={d['info']['version']}")
    for v in ("0.15.0", "0.16.0"):
        files = d["releases"].get(v, [])
        stamps = sorted({f.get("upload_time_iso_8601", "?") for f in files})
        print(f"  {v}: {'present' if files else 'ABSENT'} uploads={stamps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
