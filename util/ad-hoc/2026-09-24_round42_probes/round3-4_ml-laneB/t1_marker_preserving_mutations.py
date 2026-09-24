"""Lane B, T1: marker-PRESERVING mutations of the two key-handling guards.

juniper-ml#2059's non-vacuity script (util/ad-hoc/2026-09-23_verify_shared_package_guard_sites_are_not_vacuous.py)
mutates by DELETING a marker string, so it can only show the markers are necessary. This asks the
other question: does the gate stay GREEN when the guarded PROPERTY breaks but the marker substrings
survive? For every mutation it runs

  (1) the gate itself -- SharedPackageGuardTest for the service-core copy, and
      ServiceForkDriftTest (JUNIPER_DRIFT_TEST_FORCE_LOCAL=1) for canopy's copy in the scratch
      ecosystem -- and
  (2) a behavioural oracle on the mutated module: the blank filter (a blank-plus-real key list must
      not accept an empty key; a blank-only list must leave auth disabled) and a compare-count spy
      (three keys, the first-iterated one presented, all three must be compared) -- the same spy
      canopy#660 ships as test_validate_compares_every_key_even_when_the_first_matches.

Scratch only: every tree lives under this lane's scratch dir; no checkout is written.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

LANE = Path(__file__).resolve().parent
ECO = LANE / "eco"
WORK = LANE / "t1_mut"
SC_REL = Path("juniper-service-core/juniper_service_core/security.py")
TEST_REL = Path("tests/test_service_fork_drift.py")
CANOPY_REL = Path("src/security.py")

FILTER_LINE = "{k for k in (api_keys or []) if isinstance(k, str) and k.strip()}"
LOOP = """        matched = False
        for candidate in self._api_keys:
            if hmac.compare_digest(api_key, candidate):
                matched = True
        return matched
"""

MUTATIONS = {
    "M1 break-after-match (short-circuit restored)": [(LOOP, LOOP.replace("matched = True\n", "matched = True\n                break\n"))],
    "M2 return-True-inside-loop": [(LOOP, LOOP.replace("                matched = True\n", "                return True\n"))],
    "M3 strip-normalises-instead-of-filtering": [(FILTER_LINE, "{k.strip() for k in (api_keys or []) if isinstance(k, str)}")],
    "M4 filter-gates-enabled-only": [
        ("self._api_keys: set[str] = " + FILTER_LINE, "self._api_keys: set[str] = {k for k in (api_keys or []) if isinstance(k, str)}"),
        ("self._enabled = len(self._api_keys) > 0", "self._enabled = any(isinstance(k, str) and k.strip() for k in self._api_keys)"),
    ],
    "M5 loop-commented-out-any-returned": [
        (
            LOOP,
            "".join("        # " + line.lstrip() + "\n" for line in LOOP.splitlines()) + "        return any(hmac.compare_digest(api_key, c) for c in self._api_keys)\n",
        )
    ],
    "M6 filter-removed-marker-left-in-docstring": [
        ("self._api_keys: set[str] = " + FILTER_LINE, "self._api_keys: set[str] = set(api_keys) if api_keys else set()"),
        ('"""Initialize with optional list of valid API keys.', '"""Initialize with optional list of valid API keys (formerly filtered with ``isinstance(k, str) and k.strip()``).'),
    ],
    "M7 any-returned-first-loop-left-as-dead-code": [(LOOP, "        return any(hmac.compare_digest(api_key, c) for c in self._api_keys)\n" + LOOP)],
}


def mutate(src: str, edits) -> str:
    for old, new in edits:
        if src.count(old) != 1:
            raise SystemExit(f"anchor count {src.count(old)} != 1 for {old[:60]!r}")
        src = src.replace(old, new)
    return src


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def oracle(path: Path, name: str) -> list[str]:
    """Behavioural checks. Returns the list of violated properties."""
    bad = []
    mod = load(path, name)
    A = mod.APIKeyAuth
    if A(["", "   "]).enabled:
        bad.append("blank-only keys ENABLE auth")
    if A(["   ", "real"]).validate("") or A(["", "real"]).validate(""):
        bad.append("blank+real keys ACCEPT an empty X-API-Key")
    auth = A(["key1", "key2", "key3"])
    seen = []
    real = auth.validate.__globals__["hmac"].compare_digest

    def counting(a, b):
        seen.append(b)
        return real(a, b)

    saved = auth.validate.__globals__["hmac"]
    auth.validate.__globals__["hmac"] = SimpleNamespace(compare_digest=counting)
    try:
        first = next(iter(auth._api_keys))
        ok = auth.validate(first)
    finally:
        auth.validate.__globals__["hmac"] = saved
    if not ok:
        bad.append("a valid key is REFUSED")
    if sorted(seen) != ["key1", "key2", "key3"]:
        bad.append(f"compare SHORT-CIRCUITS (compared {len(seen)} of 3 keys)")
    return bad


def run_gate(cwd: Path, test_id: str, force_local: bool) -> tuple[int, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL")}
    if force_local:
        env["JUNIPER_DRIFT_TEST_FORCE_LOCAL"] = "1"
    r = subprocess.run([sys.executable, "-m", "unittest", test_id], cwd=cwd, env=env, capture_output=True, text=True, check=False)
    tail = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""
    return r.returncode, tail


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    rows = []
    # --- service-core copy, SharedPackageGuardTest ---
    sc_src = (ECO / "juniper-ml" / SC_REL).read_text(encoding="utf-8")
    for label, edits in [("control", [])] + list(MUTATIONS.items()):
        tree = WORK / ("sc_" + label.split()[0])
        for rel in (TEST_REL, SC_REL):
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ECO / "juniper-ml" / rel, tree / rel)
        (tree / "tests" / "__init__.py").touch()
        (tree / SC_REL).write_text(mutate(sc_src, edits), encoding="utf-8")
        rc, tail = run_gate(tree, "tests.test_service_fork_drift.SharedPackageGuardTest", False)
        bad = oracle(tree / SC_REL, "sc_" + label.split()[0].replace("-", "_"))
        rows.append(("service-core", label, "GREEN" if rc == 0 else "RED", tail, bad))
    # --- canopy copy, ServiceForkDriftTest in a scratch ecosystem ---
    cn_src = (ECO / "juniper-canopy" / CANOPY_REL).read_text(encoding="utf-8")
    for label, edits in [("control", [])] + list(MUTATIONS.items()):
        eco = WORK / ("eco_" + label.split()[0])
        for repo in ("juniper-data", "juniper-cascor"):
            (eco / repo).mkdir(parents=True)
            # the anchors only need to exist; copy the two fork files the gate reads
            for rel in ("juniper_data/api/security.py", "juniper_data/api/middleware.py", "juniper_data/api/app.py") if repo == "juniper-data" else ("src/api/security.py", "src/api/middleware.py", "src/api/app.py"):
                (eco / repo / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ECO / repo / rel, eco / repo / rel)
        (eco / "juniper-canopy" / CANOPY_REL).parent.mkdir(parents=True, exist_ok=True)
        (eco / "juniper-canopy" / CANOPY_REL).write_text(mutate(cn_src, edits), encoding="utf-8")
        for rel in (TEST_REL, SC_REL):
            (eco / "juniper-ml" / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ECO / "juniper-ml" / rel, eco / "juniper-ml" / rel)
        (eco / "juniper-ml" / "tests" / "__init__.py").touch()
        rc, tail = run_gate(eco / "juniper-ml", "tests.test_service_fork_drift.ServiceForkDriftTest", True)
        rows.append(("canopy", label, "GREEN" if rc == 0 else "RED", tail, None))
    print(f"{'copy':13} {'mutation':48} {'gate':6} {'gate tail':28} oracle")
    for copy, label, gate, tail, bad in rows:
        orc = "-" if bad is None else ("OK" if not bad else "; ".join(bad))
        print(f"{copy:13} {label:48} {gate:6} {tail[:28]:28} {orc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
