#!/usr/bin/env python3
"""Lane A: for each round-4 harness arm (M51-M67), WHY does each must-fail test fail?

Loads the harness's MUTATIONS from the head tree, copies that tree once into scratch, and per arm:
applies the edits, runs the arm's must-fail tests in one pytest call with -rf (one-line reasons),
records each test's outcome and reason, and restores. A reason that is an ImportError, a
collection error or a fixture error would make the arm's CAUGHT a vacuous one.
"""

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneA/head")
HARNESS = HEAD / "util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py"
spec = importlib.util.spec_from_file_location("harness_for_classify", HARNESS)
harness = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness
spec.loader.exec_module(harness)

work_root = Path(tempfile.mkdtemp(prefix="classify-arms-"))
work = work_root / "repo"
shutil.copytree(HEAD, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "data", "logs"))
env = {"PATH": "/opt/miniforge3/envs/JuniperData/bin:/usr/bin:/bin", "HOME": str(Path.home()), "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(work_root)}
arms = [m for m in harness.MUTATIONS if int(re.match(r"M(\d+)", m.name).group(1)) >= 51]
print(f"{len(arms)} round-4 arms")
for m in arms:
    originals = {}
    for repo_path, find, replace in m.edits:
        path = work / repo_path.relative_to(harness.REPO)
        text = originals.setdefault(path, path.read_text(encoding="utf-8"))
        current = path.read_text(encoding="utf-8")
        assert current.count(find) == 1, (m.name, repo_path)
        path.write_text(current.replace(find, replace), encoding="utf-8")
    junit = work_root / "junit.xml"
    try:
        proc = subprocess.run(["/opt/miniforge3/envs/JuniperData/bin/python", "-m", "pytest", *m.must_fail, "-q", "--no-header", "-p", "no:cacheprovider", "--tb=short", f"--junitxml={junit}"], cwd=work, capture_output=True, text=True, env=env, timeout=900)
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
    import xml.etree.ElementTree as ET

    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "(no output)"
    print(f"\n{m.name}\n  must-fail: {len(m.must_fail)}; pytest: {tail}")
    for case in ET.parse(junit).getroot().iter("testcase"):
        bad = case.find("failure") if case.find("failure") is not None else case.find("error")
        kind = "PASSED" if bad is None else bad.tag.upper()
        message = "" if bad is None else (bad.get("message") or "").replace("\n", " | ")
        print(f"  {kind:7} {case.get('name')[:100]}\n          -> {message[:230]}")
shutil.rmtree(work_root, ignore_errors=True)
