#!/usr/bin/env python3
"""
Verify the PUBLISHED juniper-ci-tools wheel is the release the run_tests rollout was proven against.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-28
Status: ad-hoc -- one-off (the run_tests rollout, step 4 of § 4.3 of
        notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-10-17_verify_data_client_0_6_0_published_wheel.py and
         util/ad-hoc/2026-09-10_verify_published_wheels.py (the pattern this follows);
         .github/workflows/publish-ci-tools.yml (what builds and uploads it)

Why this exists
---------------
juniper-recurrence and juniper-data-client convert their util/run_tests.py to thin specs over
``juniper_ci_tools.run_tests``, pinned ``juniper-ci-tools>=0.10.0,<0.11.0``. Both conversions were proven against
0.10.0 built from this repo's tree. A checkout is not a deployment, so before their PRs open, this checks what
``pip install`` actually serves:

1. the PyPI wheel downloads, and so does TestPyPI's, and they are one artifact (sha256);
2. its METADATA names the version, ``Requires-Python >=3.11`` and the PyYAML requirement;
3. every ``juniper_ci_tools/*.py`` in it equals ``git show REF:juniper-ci-tools/juniper_ci_tools/<name>`` byte for
   byte, with no module missing or extra (REF: the Release's target, the proposal's merge commit);
4. installed into a fresh venv, with ``python -I`` (no PYTHONPATH, no user site), it imports from that venv's
   site-packages, ``__version__`` and ``run_tests.ENGINE_VERSION`` are the version, and ``run_tests.__all__`` is the
   public API REF's source declares.

Every download lands in its own new directory under ``--work`` (a directory under a repo's gitignored ``tmp/``,
never the system temp directory), and nothing is executed from inside one. Exit 0 when every check passes, 1
otherwise; the PyPI CDN can lag a few minutes after a publish, so a 404 right after one is worth one retry.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess  # nosec B404 - pip, git and a venv's interpreter, fixed argv
import sys
import zipfile
from email.parser import Parser
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
PACKAGE = "juniper-ci-tools"
MODULE_DIR = "juniper_ci_tools"
TREE = "juniper-ci-tools/juniper_ci_tools"
INDEXES = {"pypi": "https://pypi.org/simple/", "testpypi": "https://test.pypi.org/simple/"}

PROBE = r"""
import json, sys, sysconfig
import juniper_ci_tools, juniper_ci_tools.run_tests as rt
print(json.dumps({"version": juniper_ci_tools.__version__, "engine": rt.ENGINE_VERSION, "all": sorted(rt.__all__),
                  "file": rt.__file__, "purelib": sysconfig.get_paths()["purelib"], "isolated": sys.flags.isolated}))
"""

results: list[tuple[bool, str]] = []


def check(ok: bool, what: str) -> bool:
    results.append((ok, what))
    print(f"{'PASS' if ok else 'FAIL'}  {what}", flush=True)
    return ok


def run(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=False, **kwargs)  # nosec B603


def download(index: str, url: str, version: str, work: Path) -> Path | None:
    dest = work / f"download-{index}"
    dest.mkdir(parents=True, exist_ok=False)
    proc = run([sys.executable, "-m", "pip", "download", f"{PACKAGE}=={version}", "--no-deps", "--only-binary=:all:", "--no-cache-dir", "--index-url", url, "-d", str(dest)])
    wheels = sorted(dest.glob("*.whl"))
    if not check(proc.returncode == 0 and len(wheels) == 1, f"{index}: pip download {PACKAGE}=={version} -> {', '.join(w.name for w in wheels) or (proc.stderr.strip().splitlines() or ['nothing'])[-1]}"):
        return None
    return wheels[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_modules(ref: str) -> dict[str, bytes]:
    names = run(["git", "-C", str(HERE), "ls-tree", "--name-only", f"{ref}:{TREE}"]).stdout.split()
    out = {}
    for name in names:
        if name.endswith(".py"):
            proc = subprocess.run(["git", "-C", str(HERE), "show", f"{ref}:{TREE}/{name}"], capture_output=True, check=True)  # nosec B603 B607
            out[name] = proc.stdout
    return out


def declared_all(source: bytes) -> list[str]:
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            return sorted(ast.literal_eval(node.value))
    raise SystemExit("REF's run_tests.py declares no __all__")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--work", required=True, type=Path, help="a NEW directory under a repo's tmp/")
    parser.add_argument("--version", default="0.10.0")
    parser.add_argument("--ref", default="7e485e9ab990662436dc9d1126ca94d64b995836", help="the Release's target commit")
    parser.add_argument("--python", default=sys.executable, help="the interpreter the probe venv is made from")
    args = parser.parse_args()
    work = args.work.absolute()
    work.mkdir(parents=True, exist_ok=False)

    wheels = {index: download(index, url, args.version, work) for index, url in INDEXES.items()}
    wheel = wheels["pypi"]
    if wheel is None:
        return 1
    digests = {index: sha256(path) for index, path in wheels.items() if path is not None}
    check(len(set(digests.values())) == 1 and len(digests) == 2, f"one artifact on both indexes: {digests}")

    with zipfile.ZipFile(wheel) as archive:
        members = {Path(name).name: archive.read(name) for name in archive.namelist() if name.startswith(f"{MODULE_DIR}/") and name.endswith(".py") and name.count("/") == 1}
        meta_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        meta = Parser().parsestr(archive.read(meta_name).decode("utf-8"))
    check(meta["Name"] == PACKAGE and meta["Version"] == args.version, f"METADATA: {meta['Name']} {meta['Version']}")
    check(meta["Requires-Python"] == ">=3.11", f"METADATA: Requires-Python {meta['Requires-Python']}")
    requires = meta.get_all("Requires-Dist") or []
    check(any(req.replace(" ", "").lower().startswith("pyyaml>=") for req in requires), f"METADATA: Requires-Dist {requires}")

    tree = tree_modules(args.ref)
    check(sorted(members) == sorted(tree), f"the wheel's modules are REF's: {len(members)} in the wheel, {len(tree)} at {args.ref[:10]}")
    differing = sorted(name for name in set(members) & set(tree) if members[name] != tree[name])
    check(not differing and "run_tests.py" in members, f"every module equals REF's byte for byte (differing: {differing or 'none'}; run_tests.py sha256 {hashlib.sha256(members.get('run_tests.py', b'')).hexdigest()[:16]})")

    venv = work / "venv"
    proc = run([args.python, "-m", "venv", str(venv)])
    if not check(proc.returncode == 0, f"fresh venv from {args.python}"):
        return 1
    py = venv / "bin" / "python"
    proc = run([str(py), "-m", "pip", "install", "--no-cache-dir", "--quiet", str(wheel)])
    if not check(proc.returncode == 0, f"pip install {wheel.name} (and PyYAML from PyPI) into it"):
        print(proc.stderr)
        return 1
    proc = run([str(py), "-I", "-c", PROBE], cwd=work)
    if not check(proc.returncode == 0, "the probe imports juniper_ci_tools.run_tests under python -I"):
        print(proc.stderr)
        return 1
    got = json.loads(proc.stdout)
    check(got["version"] == args.version and got["engine"] == args.version, f"__version__ {got['version']}, run_tests.ENGINE_VERSION {got['engine']}")
    check(got["all"] == declared_all(tree["run_tests.py"]), f"run_tests.__all__ is REF's public API ({len(got['all'])} names)")
    check(Path(got["file"]).is_relative_to(Path(got["purelib"])) and got["isolated"] == 1, f"imported from the venv's site-packages: {got['file']}")

    failed = [what for ok, what in results if not ok]
    print(f"{len(results) - len(failed)} of {len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
