"""Prove whether TestEntityTagListRunsInLinearTime's CHILD interpreter sees a mutated scratch copy.

Three copies of the tree, each run exactly as the harness runs a node (cwd = copy,
``python -m pytest <node> -q --no-header -p no:cacheprovider``, PYTHONDONTWRITEBYTECODE=1):

  control  -- unmutated: must pass.
  fastmut  -- ``if_match_fails`` returns False for everything. The child's printed triple
              becomes [False, False, False] instead of [False, True, False], so the test
              fails FAST on its equality assertion -- iff the child loaded the mutated file.
  M20      -- the harness's own M20 edit (backtracking grammar): must fail on the 30 s bound.

A fourth run executes the child command by hand with the copy's path, printing the module
file the child loaded.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

L = Path(__file__).resolve().parent
SRC = L / "trees" / "3a76a4c"
PY = "/opt/miniforge3/envs/JuniperData/bin/python"
NODE = "juniper_data/tests/unit/test_conditional_requests.py::TestEntityTagListRunsInLinearTime::test_hostile_fields_are_refused_well_inside_a_generous_bound"
CACHE_REL = Path("juniper_data/api/http_cache.py")

LINEAR = r"""_ENTITY_TAG_LIST = re.compile(r'[ \t]*(?:(?:W/)?"[^"]*"[ \t]*)?(?:,[ \t]*(?:(?:W/)?"[^"]*"[ \t]*)?)*')"""
BACKTRACKING = r"""_ENTITY_TAG_LIST = re.compile(r'[ \t]*(?:(?:W/)?"[^"]*")?[ \t]*(?:,[ \t]*(?:(?:W/)?"[^"]*")?[ \t]*)*')"""
IFMATCH = "    return if_match is not None and not _list_names(if_match, etag, strong=True)\n"

env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(L / "tmp" / "childproof")}
Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)


def make_copy(name: str, find: str | None = None, replace: str | None = None) -> Path:
    dest = L / "tmp" / "childproof" / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    if find is not None:
        target = dest / CACHE_REL
        text = target.read_text()
        assert text.count(find) == 1, (name, text.count(find))
        target.write_text(text.replace(find, replace))
    return dest


def run(copy: Path) -> tuple[int, float, str]:
    t0 = time.monotonic()
    proc = subprocess.run([PY, "-m", "pytest", NODE, "-q", "--no-header", "-p", "no:cacheprovider"], cwd=copy, capture_output=True, text=True, env=env)
    out = proc.stdout + proc.stderr
    keep = [ln for ln in out.splitlines() if ("assert" in ln.lower() or "passed" in ln or "failed" in ln or "did not finish" in ln or ln.startswith("E "))]
    return proc.returncode, time.monotonic() - t0, "\n      ".join(keep[:8])


for name, find, replace in (("control", None, None), ("fastmut", IFMATCH, "    return False\n"), ("M20", LINEAR, BACKTRACKING)):
    copy = make_copy(name, find, replace)
    rc, secs, excerpt = run(copy)
    print(f"[{name}] exit={rc} ({'PASS' if rc == 0 else 'FAIL'}) in {secs:.1f}s\n      {excerpt}")

# By hand: the child command with the fastmut copy's path, printing what it loaded and returned.
copy = L / "tmp" / "childproof" / "fastmut"
probe = (
    "import importlib.util, json, sys\n"
    "spec = importlib.util.spec_from_file_location('http_cache_under_test', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
    "print('child loaded', m.__file__)\n"
    "print('if_match_fails(\"x, zz\", tag) ->', m.if_match_fails('x, zz', m.strong_etag('abc')))\n"
)
print(subprocess.run([PY, "-c", probe, str(copy / CACHE_REL)], capture_output=True, text=True, env=env).stdout)
