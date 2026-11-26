"""
Which NumPy scalar types Starlette's send_json serialisation (json.dumps, separators, ensure_ascii=False) accepts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Usage:
  python <this file>
"""

from __future__ import annotations

import json
import sys

import numpy as np


def main() -> int:
    print("numpy", np.__version__, "python", sys.version.split()[0])
    for name in ("float64", "float32", "float16", "int64", "int32", "bool_", "complex128", "str_"):
        value = getattr(np, name)(1)
        try:
            out = json.dumps({"v": value}, separators=(",", ":"), ensure_ascii=False)
            verdict = f"serialises -> {out} (isinstance float: {isinstance(value, float)}, str: {isinstance(value, str)})"
        except TypeError as exc:
            verdict = f"TypeError: {exc}"
        print(f"np.{name}: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
