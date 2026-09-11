#!/usr/bin/env python3
"""Find the first published juniper-cascor-client that enforces the base_url host guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc floor-setting evidence
Author:      Paul Calnon
Created:     2026-09-11
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-ml [clients] floor decision)

Why this exists
---------------
``juniper-ml``'s ``[clients]`` extra pins ``juniper-cascor-client>=0.5.0``. The base-URL host
guard (``JuniperCascorConfigurationError`` on a hostless URL, plus case-insensitive scheme
normalisation so ``HTTPS://host`` does not become a plaintext request) landed in
cascor-client#129, but WHICH PUBLISHED VERSION first carries it is the thing the floor has to
be set from -- and ``docs/REFERENCE.md`` asserted a boundary ("past cascor-client 0.7.0")
without a probe behind it.

Rather than trust that, this installs each published version into a throwaway venv and
exercises the constructor. The floor should be the LOWEST version that passes both checks,
not simply the newest release.

Usage
-----
    python3 util/ad-hoc/2026-09-11_cascor_client_guard_boundary.py --versions 0.5.0 0.6.0 0.7.0 0.8.0
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - creates throwaway venvs and pip-installs pinned versions
import sys
import tempfile
from pathlib import Path

# Executed inside each throwaway venv; prints one JSON line.
_PROBE = r"""
import json
out = {"import": False, "has_error_type": False, "hostless_refused": None, "scheme_normalised": None}
try:
    import juniper_cascor_client as m
    out["import"] = True
    out["version"] = getattr(m, "__version__", "?")
    E = getattr(m, "JuniperCascorConfigurationError", None)
    out["has_error_type"] = E is not None
    C = getattr(m, "JuniperCascorClient", None)
    if C is not None:
        try:
            C(base_url="https://")
            out["hostless_refused"] = False
        except Exception as exc:
            out["hostless_refused"] = (E is not None and isinstance(exc, E))
        try:
            cl = C(base_url="HTTPS://example.com")
            stored = getattr(cl, "base_url", None) or getattr(cl, "_base_url", None)
            out["scheme_normalised"] = str(stored).startswith("https://")
            out["stored"] = str(stored)
        except Exception as exc:
            out["scheme_normalised"] = "raised:" + type(exc).__name__
except Exception as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
print(json.dumps(out))
"""


def probe(version: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        venv = Path(td) / "v"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True)  # nosec B603
        pip = venv / "bin" / "pip"
        py = venv / "bin" / "python"
        r = subprocess.run(  # nosec B603
            [str(pip), "install", "--quiet", f"juniper-cascor-client=={version}"],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            return {"version": version, "install_failed": r.stderr.strip()[-200:]}
        r = subprocess.run([str(py), "-c", _PROBE], capture_output=True, text=True)  # nosec B603
        try:
            d = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            return {"version": version, "probe_failed": (r.stdout + r.stderr)[-200:]}
        d["version"] = version
        return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versions", nargs="+", required=True)
    args = ap.parse_args()

    rows = []
    for v in args.versions:
        d = probe(v)
        rows.append(d)
        guarded = d.get("hostless_refused") is True and d.get("scheme_normalised") is True
        print(
            f"  {v:8} hostless_refused={str(d.get('hostless_refused')):16} "
            f"scheme_normalised={str(d.get('scheme_normalised')):16} "
            f"{'GUARDED' if guarded else 'unguarded'}"
            + (f"  [{d['install_failed']}]" if "install_failed" in d else "")
        )

    guarded = [r["version"] for r in rows if r.get("hostless_refused") is True and r.get("scheme_normalised") is True]
    print()
    if guarded:
        print(f"lowest probed version with BOTH halves of the guard: {guarded[0]}")
    else:
        print("no probed version carries both halves of the guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
