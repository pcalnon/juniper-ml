"""Lane A mutation harness for the #2059 fork-drift gate.

Copies eco/ to eco-mut/ once, then for each mutation: rewrites ONE site file in
eco-mut/, runs probe_run.py (cross-repo forced, and for service-core mutations
also the default always-on mode), records the failing subtests, and restores the
file from eco/. A mutation's `old` text must occur EXACTLY once, or the harness
refuses (so a mutation can never silently no-op).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
ECO = S / "eco"
MUT = S / "eco-mut"

if not MUT.exists():
    shutil.copytree(ECO, MUT, symlinks=True)

CANOPY = "juniper-canopy/src/security.py"
SVC = "juniper-ml/juniper-service-core/juniper_service_core/security.py"

CANOPY_FILTER = "self._api_keys: set[str] = {k for k in (api_keys or []) if isinstance(k, str) and k.strip()}"
SVC_FILTER = CANOPY_FILTER  # identical text in both copies

LOOP = "        matched = False\n        for candidate in self._api_keys:\n            if hmac.compare_digest(api_key, candidate):\n                matched = True\n        return matched\n"
LOOP_ANY = "        return any(hmac.compare_digest(api_key, k) for k in self._api_keys)\n"
LOOP_BREAK = "        matched = False\n        for candidate in self._api_keys:\n            if hmac.compare_digest(api_key, candidate):\n                matched = True\n                break\n        return matched\n"
LOOP_ANY_KEEP_MARKERS = "        matched = False\n        matched = any(hmac.compare_digest(api_key, k) for k in self._api_keys)\n        return matched\n"

MUTATIONS = [
    # (id, file, old, new, expectation)
    ("C1-canopy-filter-removed", CANOPY, CANOPY_FILTER, "self._api_keys: set[str] = set(api_keys) if api_keys else set()", "FAIL blank-api-key-filter@canopy"),
    ("C2-canopy-strip-dropped", CANOPY, "if isinstance(k, str) and k.strip()}", "if isinstance(k, str) and k}", "FAIL blank-api-key-filter@canopy"),
    ("C3-canopy-compare-any", CANOPY, LOOP, LOOP_ANY, "FAIL nonshortcircuit-key-compare@canopy"),
    ("C4-canopy-compare-break(markers kept)", CANOPY, LOOP, LOOP_BREAK, "instrument limit: short-circuit restored, markers intact"),
    ("C5-canopy-any-assigned(markers kept)", CANOPY, LOOP, LOOP_ANY_KEEP_MARKERS, "instrument limit: any() restored, markers intact"),
    ("C6-canopy-enabled-from-raw(markers kept)", CANOPY, "self._enabled = len(self._api_keys) > 0", "self._enabled = bool(api_keys)", "instrument limit: blank key enables auth again, markers intact"),
    ("S1-svc-filter-removed", SVC, SVC_FILTER, "self._api_keys: set[str] = set(api_keys) if api_keys else set()", "FAIL blank-api-key-filter@juniper-ml (both tests)"),
    ("S2-svc-strip-dropped", SVC, "if isinstance(k, str) and k.strip()}", "if isinstance(k, str) and k}", "FAIL blank-api-key-filter@juniper-ml (both tests)"),
    ("S3-svc-compare-any", SVC, LOOP, LOOP_ANY, "FAIL nonshortcircuit-key-compare@juniper-ml (both tests)"),
    ("S4-svc-compare-break(markers kept)", SVC, LOOP, LOOP_BREAK, "instrument limit"),
    ("S5-svc-enabled-from-raw(markers kept)", SVC, "self._enabled = len(self._api_keys) > 0", "self._enabled = bool(api_keys)", "instrument limit"),
]


def run_probe(force_local: bool) -> list[str]:
    args = [sys.executable, str(S / "probe_run.py"), str(MUT / "juniper-ml")]
    if force_local:
        args.append("--force-local")
    out = subprocess.run(args, capture_output=True, text=True, check=False).stdout
    keep = [ln for ln in out.splitlines() if " | FAIL | " in ln or " | ERROR | " in ln or "SKIP" in ln or ln.startswith("testsRun=") or ln.startswith("ecosystem_root")]
    return keep


only = sys.argv[1:] or None
print("baseline (force-local):")
for ln in run_probe(True):
    print("   ", ln)
for mid, rel, old, new, expect in MUTATIONS:
    if only and not any(o in mid for o in only):
        continue
    target = MUT / rel
    original = (ECO / rel).read_text(encoding="utf-8")
    count = original.count(old)
    if count != 1:
        print(f"\n### {mid}: REFUSED -- `old` occurs {count} times in {rel}")
        continue
    target.write_text(original.replace(old, new), encoding="utf-8")
    try:
        mutated = target.read_text(encoding="utf-8")
        assert mutated != original
        print(f"\n### {mid}  [{rel}]  expectation: {expect}")
        print("  force-local run:")
        for ln in run_probe(True):
            print("     ", ln[:260])
        if rel == SVC:
            print("  default run (no opt-in; always-on test only):")
            for ln in run_probe(False):
                print("     ", ln[:260])
    finally:
        target.write_text(original, encoding="utf-8")
        assert target.read_text(encoding="utf-8") == original
print("\nrestored; eco-mut site files equal eco:", all((MUT / r).read_text() == (ECO / r).read_text() for r in (CANOPY, SVC)))
