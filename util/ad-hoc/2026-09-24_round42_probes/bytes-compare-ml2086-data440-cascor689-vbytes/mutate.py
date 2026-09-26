"""New mutations (not in the implementer's harness) against the three PR heads.

Each mutation: copy the tree, apply exact-text edits (count must match), run the PR's own new
tests in the owning repo's CI lane, report which tests fail. For the loop-shape mutation the
fork-drift gate is also run against the synthetic ecosystem root with the mutated file.

python mutate.py <suite> <mutation-id|all>
"""

import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

V = Path(__file__).resolve().parent
CASCOR_PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
DATA_PY = "/opt/miniforge3/envs/JuniperData/bin/python"

BYTES_LINE = 'if hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")):'
PRESENTED_LINE = 'presented = api_key.encode("utf-8", "surrogatepass")'

LOOP_BLOCK = """        presented = api_key.encode("utf-8", "surrogatepass")
        matched = False
        for candidate in self._api_keys:
            if hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")):
                matched = True
        return matched"""
SWALLOW_BLOCK = """        matched = False
        for candidate in self._api_keys:
            try:
                if hmac.compare_digest(api_key, candidate):
                    matched = True
            except TypeError:
                pass
        return matched"""


def svc_mutations(path):
    return {
        "UTF16": ("utf-16-le + surrogatepass on both sides: total, but NOT injective (a surrogate pair and its astral char share bytes)", path, [('"utf-8", "surrogatepass"', '"utf-16-le", "surrogatepass"', 2)]),
        "BREAK": ("short-circuit on first match (break) -- the drift markers stay present", path, [("                matched = True\n", "                matched = True\n                break\n", 1)]),
        "SWALLOW": ("the tempting non-fix: keep the str compare, swallow TypeError (non-ASCII never raises, never matches)", path, [(LOOP_BLOCK, SWALLOW_BLOCK, 1)]),
        "EQ": ("bytes == in place of compare_digest (never raises, correct results, early-exit timing)", path, [(BYTES_LINE, 'if presented == candidate.encode("utf-8", "surrogatepass"):', 1)]),
    }


SUITES = {
    "sc": {
        "src": V / "ml-head",
        "copy": ["juniper-service-core", "juniper-model-core", "juniper-observability"],
        "cwd": ".",
        "python": CASCOR_PY,
        "pythonpath": ["juniper-service-core", "juniper-model-core", "juniper-observability"],
        "tests": ["juniper-service-core/tests/test_security.py", "juniper-service-core/tests/test_middleware.py", "juniper-service-core/tests/test_t2_websocket.py"],
        "marker": None,
        "mutations": svc_mutations("juniper-service-core/juniper_service_core/security.py"),
        "drift_site": ("juniper-ml", "juniper-service-core/juniper_service_core/security.py"),
    },
    "data": {
        "src": V / "data-head",
        "copy": ["juniper_data", "pyproject.toml"],
        "cwd": ".",
        "python": DATA_PY,
        "pythonpath": [],
        "tests": ["juniper_data/tests/unit/test_security.py"],
        "marker": "unit and not slow",
        "mutations": svc_mutations("juniper_data/api/security.py"),
        "drift_site": ("juniper-data", "juniper_data/api/security.py"),
    },
    "cascor": {
        "src": V / "cascor-head",
        "copy": ["src", "conf", "pyproject.toml"],
        "cwd": ".",
        "python": CASCOR_PY,
        "pythonpath": [],
        "tests": ["src/tests/unit/api/test_api_security.py", "src/tests/unit/test_main_sentry_no_local_variables.py"],
        "marker": "unit and not slow",
        "mutations": {
            **svc_mutations("src/api/security.py"),
            "ALIAS-INIT": (
                "a second bootstrap init through an alias, locals left ON (the AST guard matches only `sentry_sdk.init`)",
                "src/main.py",
                [("            before_send=_sentry_strip_sensitive_headers,\n        )\n", "            before_send=_sentry_strip_sensitive_headers,\n        )\n        from sentry_sdk import init as _sentry_init_again\n\n        _sentry_init_again(dsn=_sentry_dsn, before_send=_sentry_strip_sensitive_headers)\n", 1)],
            ),
        },
        "drift_site": ("juniper-cascor", "src/api/security.py"),
    },
    "obs": {
        "src": V / "ml-head",
        "copy": ["juniper-observability"],
        "cwd": "juniper-observability",
        "python": CASCOR_PY,
        "pythonpath": ["juniper-observability"],
        "tests": ["tests/test_sentry.py"],
        "marker": None,
        "mutations": {
            "FIRST-EXC-ONLY": ("backstop walks only the FIRST exception of a chain", "juniper-observability/juniper_observability/sentry.py", [("for value in values if isinstance(value, dict))", "for value in values[:1] if isinstance(value, dict))", 1)]),
            "LOCALS-FOLLOW-PII": ("include_local_variables=send_pii (locals come back whenever PII is opted in)", "juniper-observability/juniper_observability/sentry.py", [("        include_local_variables=False,\n", "        include_local_variables=send_pii,\n", 1)]),
            "IN-APP-ONLY": (
                "backstop drops vars only from in_app frames (a pip-installed service-core frame is in_app: false)",
                "juniper-observability/juniper_observability/sentry.py",
                [('                if isinstance(frame, dict):\n                    frame.pop("vars", None)\n', '                if isinstance(frame, dict) and frame.get("in_app", True):\n                    frame.pop("vars", None)\n', 1)],
            ),
        },
        "drift_site": None,
    },
}


def results(junit):
    out = {}
    for case in ET.parse(junit).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        failed = case.find("failure") is not None or case.find("error") is not None
        out[node] = "failed" if failed else ("skipped" if case.find("skipped") is not None else "passed")
    return out


def run(suite_id, mutation_id):
    s = SUITES[suite_id]
    with tempfile.TemporaryDirectory(dir=V / "out", prefix=f"mut-{suite_id}-") as tmp:
        tree = Path(tmp)
        for rel in s["copy"]:
            src = s["src"] / rel
            if src.is_dir():
                shutil.copytree(src, tree / rel, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(src, tree / rel)
        if mutation_id != "NONE":
            summary, path, edits = s["mutations"][mutation_id]
            target = tree / path
            text = target.read_text(encoding="utf-8")
            for old, new, count in edits:
                found = text.count(old)
                if found != count:
                    return f"[{suite_id}] {mutation_id}: REFUSED -- expected {count} of {old[:50]!r}, found {found}"
                text = text.replace(old, new)
            target.write_text(text, encoding="utf-8")
        else:
            summary = "unmutated"
        env = {k: v for k, v in os.environ.items() if "DSN" not in k and k != "JUNIPER_CASCOR_LOG_DIR"}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if s["pythonpath"]:
            env["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in s["pythonpath"])
        else:
            env.pop("PYTHONPATH", None)
        junit = tree / "junit.xml"
        marker = ["-m", s["marker"]] if s["marker"] else []
        subprocess.run([s["python"], "-m", "pytest", "-p", "no:cacheprovider", "-q", f"--junitxml={junit}", *marker, *s["tests"]], cwd=tree / s["cwd"], env=env, capture_output=True, text=True)
        res = results(junit)
        failed = sorted(n for n, o in res.items() if o == "failed")
        line = f"[{suite_id}] {mutation_id:24} {summary[:95]}\n      -> {len(failed)} of {len(res)} tests FAIL"
        if failed:
            groups = {}
            for n in failed:
                name = n.split("::")[-1].split("[")[0]
                groups[name] = groups.get(name, 0) + 1
            line += ": " + ", ".join(f"{k} x{v}" for k, v in groups.items())
        if s["drift_site"] and mutation_id != "NONE":
            repo, rel = s["drift_site"]
            synth_file = V / "synth" / repo / rel
            keep = synth_file.read_bytes()
            try:
                synth_file.write_bytes((tree / s["mutations"][mutation_id][1]).read_bytes() if s["mutations"][mutation_id][1].endswith("security.py") else keep)
                env2 = dict(env, JUNIPER_DRIFT_TEST_FORCE_LOCAL="1")
                env2.pop("PYTHONPATH", None)
                proc = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "tests/test_service_fork_drift.py"], cwd=V / "synth" / "juniper-ml", env=env2, capture_output=True, text=True)
                tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "?"
                line += f"\n      -> fork-drift gate on the mutated file: {'FAILS' if proc.returncode else 'PASSES'} ({tail[:70]})"
            finally:
                synth_file.write_bytes(keep)
        return line


SUITES["sc-full"] = dict(SUITES["sc"], tests=["juniper-service-core/tests"])
SUITES["data-nomarker"] = dict(SUITES["data"], marker=None)

suite = sys.argv[1]
which = sys.argv[2]
ids = ["NONE", *SUITES[suite]["mutations"]] if which == "all" else [which]
for mid in ids:
    print(run(suite, mid), flush=True)
