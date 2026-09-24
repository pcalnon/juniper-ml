#!/usr/bin/env python3
"""Lane A: APD-ML-008 -- marker-preserving regressions of the two key-handling guards.

For each mutation of juniper-service-core's security.py (PR-head copy) and canopy's
src/security.py (origin/main copy):
  * GATE: does the PR head's own ``guard_is_present`` still report the guard present?
  * BEHAVIOUR: a three-key compare_digest call count + blank-key enable checks.
And for service-core: does the package's own tests/test_security.py catch it (pytest on a copy)?
Nothing is written outside the scratch dir."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA")
HEAD = S / "head"
PY = sys.executable

spec = importlib.util.spec_from_file_location("gate_head", HEAD / "tests/test_service_fork_drift.py")
gate = importlib.util.module_from_spec(spec)
sys.modules["gate_head"] = gate
spec.loader.exec_module(gate)
SITES = {(g.guard_id, s.repo): s for g in gate.GUARDS for s in g.sites}

SC_SRC = (HEAD / "juniper-service-core/juniper_service_core/security.py").read_text()
CAN_SRC = (S / "src/juniper-canopy/src/security.py").read_text()

LOOP_SC = """        matched = False
        for candidate in self._api_keys:
            if hmac.compare_digest(api_key, candidate):
                matched = True
        return matched"""
assert LOOP_SC in SC_SRC, "service-core loop text not found"
FILTER = "{k for k in (api_keys or []) if isinstance(k, str) and k.strip()}"
assert FILTER in SC_SRC and FILTER in CAN_SRC

MUTS = {
    "M1 break after match": lambda s: s.replace("                matched = True\n", "                matched = True\n                break\n", 1),
    "M2 return True inside loop": lambda s: s.replace("                matched = True\n", "                return True\n", 1),
    "M3 early any(), loop left as dead code": lambda s: s.replace("        matched = False\n        for candidate", "        return any(hmac.compare_digest(api_key, k) for k in self._api_keys)\n        matched = False\n        for candidate", 1),
    "M4 loop over first key only": lambda s: s.replace("for candidate in self._api_keys:", "for candidate in list(self._api_keys)[:1]:", 1),
    "M5 filter predicate negated": lambda s: s.replace(FILTER, "{k for k in (api_keys or []) if not (isinstance(k, str) and k.strip())} | set(api_keys or [])", 1),
    "M6 pre-fix constructor, markers in a docstring": lambda s: s.replace(FILTER, "set(api_keys) if api_keys else set()  # was: isinstance(k, str) and k.strip()", 1),
    "M7 filter short-circuited by an or-True": lambda s: s.replace(FILTER, "{k for k in (api_keys or []) if isinstance(k, str) and (k.strip() or True)}", 1),
}


def load_security(src: str, name: str, extra_path: list[str]) -> types.ModuleType | None:
    d = S / "mut_mod" / name
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "security_mut.py").write_text(src)
    code = (
        "import sys, types, importlib.util\n"
        f"sys.path[:0] = {extra_path!r}\n"
        f"spec = importlib.util.spec_from_file_location('security_mut', {str(d / 'security_mut.py')!r})\n"
        "m = importlib.util.module_from_spec(spec); sys.modules['security_mut'] = m\n"
        "spec.loader.exec_module(m)\n"
        "A = m.APIKeyAuth\n"
        "calls = []\n"
        "real = m.hmac.compare_digest\n"
        "m.hmac = types.SimpleNamespace(compare_digest=lambda a, b: (calls.append(b), real(a, b))[1])\n"
        "a = A(['key1', 'key2', 'key3'])\n"
        "first = next(iter(a._api_keys))\n"
        "ok = a.validate(first)\n"
        "n = len(calls)\n"
        "blank_enabled = A(['   ']).enabled or A(['']).enabled\n"
        "real_ok = A(['k']).validate('k') and not A(['k']).validate('x')\n"
        "print(f'{ok} {n} {blank_enabled} {real_ok}')\n"
    )
    r = subprocess.run([PY, "-c", code], capture_output=True, text=True, cwd=str(d))
    return r.stdout.strip() or ("ERR " + r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "ERR")


def sc_suite(src: str, name: str) -> str:
    d = S / "mut_sc" / name
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(HEAD / "juniper-service-core", d)
    (d / "juniper_service_core/security.py").write_text(src)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(d)
    env.pop("PYTEST_ADDOPTS", None)
    probe = subprocess.run([PY, "-c", "import juniper_service_core,sys;print(juniper_service_core.__file__)"], capture_output=True, text=True, env=env, cwd=str(d))
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_security.py"], capture_output=True, text=True, env=env, cwd=str(d))
    last = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1:] or ["?"]
    return f"{last[0]} (imported {probe.stdout.strip().replace(str(S), '$S')})"


def gate_says(src: str, guard: str, repo: str) -> bool:
    return gate.guard_is_present(src, SITES[(guard, repo)])


print("baseline service-core:", gate_says(SC_SRC, "nonshortcircuit-key-compare", "juniper-ml"), gate_says(SC_SRC, "blank-api-key-filter", "juniper-ml"), load_security(SC_SRC, "sc_base", [str(HEAD / "juniper-service-core")]), sc_suite(SC_SRC, "sc_base"))
print("baseline canopy       :", gate_says(CAN_SRC, "nonshortcircuit-key-compare", "juniper-canopy"), gate_says(CAN_SRC, "blank-api-key-filter", "juniper-canopy"), load_security(CAN_SRC, "can_base", [str(S / "src/juniper-canopy/src")]))
print("columns: gate(compare) gate(filter) | behaviour: validate(first) compare_calls blank_enables_auth real_key_ok | service-core own test_security.py")
for label, fn in MUTS.items():
    sc = fn(SC_SRC)
    can = fn(CAN_SRC)
    assert sc != SC_SRC, f"{label}: no-op on service-core"
    tag = label.split()[0]
    print(f"{label}")
    print(f"   service-core: gate={gate_says(sc, 'nonshortcircuit-key-compare', 'juniper-ml')},{gate_says(sc, 'blank-api-key-filter', 'juniper-ml')} | behaviour={load_security(sc, 'sc_' + tag, [str(HEAD / 'juniper-service-core')])} | own suite: {sc_suite(sc, 'sc_' + tag)}")
    if can != CAN_SRC:
        print(f"   canopy      : gate={gate_says(can, 'nonshortcircuit-key-compare', 'juniper-canopy')},{gate_says(can, 'blank-api-key-filter', 'juniper-canopy')} | behaviour={load_security(can, 'can_' + tag, [str(S / 'src/juniper-canopy/src')])}")
    else:
        print("   canopy      : mutation did not apply (text differs)")
