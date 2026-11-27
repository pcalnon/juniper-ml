#!/usr/bin/env python3
"""Round-4 adversarial review probes for juniper-cascor's one-artifact sweep (round 3, the second fix pass): run, don't read.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (round-4 review of the sweep's round 3, diff sha256 e02b4da8...)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: tmp/sweep/ROUND4_BRIEF.md (the brief); util/ad-hoc/2026-11-23_publish_port_template_identity.py (the checker
         under review); util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py (round 2's probes: its suite() is
         reused by ``edits`` with other edits); tmp/sweep/REVIEW_DISPOSITIONS.md (what rounds 2 and 3 were to fix)

Why
---
Each subcommand executes a claim instead of reading it. Nothing here writes under a frozen tree, and the only network
use is ``gh api`` GETs.

- ``mutants``: builds bypass mutants of passing workflows (cascor's template, two port simulations), runs the checker
  on each, and runs each mutant's install script under the runner's default shell (``bash -e``) with stand-in
  ``pip``/``python``/``sleep``, so a verdict of PASS can be set beside what the script then does.
- ``edits``: round 2's ``suite`` with this review's edits: the keys F7 admits on every job, cancelling and invalid
  forms that must still fail, and docs edits for F6.
- ``ml-skip``: runs juniper-ml's own publish tests against a scratch tree holding ported workflows, and against main's,
  and reports what runs, fails and skips.
- ``fetch`` / ``tree``: read files, or list paths, of a repository at a ref (GET only).

    python3 -I util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py mutants --template T --port P --ml ML --checker C --out DIR
    python3 -I util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py edits --base DIR --work DIR --python PY
    python3 -I util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py ml-skip --ml-root DIR --port-dir DIR --out DIR --python PY

Exit status: 0 always for probes (each prints what it measured); 2 on a usage error.
"""

from __future__ import annotations

import argparse
import base64
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

INSTALL_JOB = "Verify the TestPyPI install"
R2_PROBES = Path(__file__).resolve().parent / "2026-11-23_publish_sweep_r2_review_probes.py"
DOTGITHUB = "." + "github"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))
    return data


def dump(wf: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(wf, sort_keys=False, width=100000, allow_unicode=True), encoding="utf-8")


def install_job(wf: dict) -> dict:
    return [job for job in wf["jobs"].values() if job.get("name") == INSTALL_JOB][0]


def install_step(wf: dict) -> dict:
    steps = [s for s in install_job(wf)["steps"] if "run" in s]
    assert len(steps) == 1, [s.get("name") for s in steps]
    return steps[0]


def edit_run(wf: dict, old: str, new: str, count: int = 1) -> dict:
    """WF with OLD replaced by NEW in the install step's script; OLD must occur exactly COUNT times."""
    out = copy.deepcopy(wf)
    step = install_step(out)
    run = str(step["run"])
    assert run.count(old) == count, (old, run.count(old))
    step["run"] = run.replace(old, new)
    return out


def last_line(wf: dict) -> str:
    lines = [ln for ln in str(install_step(wf)["run"]).splitlines() if ln.strip()]
    return lines[-1]


def before_last(wf: dict, insert: str) -> dict:
    """WF with INSERT added as a command just before the install script's last line (the python -c check)."""
    line = last_line(wf)
    indent = line[: len(line) - len(line.lstrip())]
    return edit_run(wf, line, f"{indent}{insert}\n{line}")


def checker_verdict(checker: Path, template: Path, path: Path) -> "tuple[str, list[str]]":
    proc = subprocess.run([sys.executable, "-I", str(checker), "--template", str(template), str(path)], capture_output=True, text=True, check=False)
    reasons = [line.strip()[2:] for line in proc.stdout.splitlines() if line.strip().startswith("- ")]
    return ("PASS" if proc.returncode == 0 else "FAIL"), reasons


#: Stand-ins: pip logs and succeeds (pip download writes the wheel into --dest); python logs, prints a version when the
#: command reads one, and otherwise exits with PYEXIT (1 = the TestPyPI wheel is broken: its import fails); sleep logs.
PIP_STUB = r"""#!/bin/bash
echo "PIP $*" >> "$SIMLOG"
if [ "$1" = download ]; then
  dest=""; prev=""
  for a in "$@"; do if [ "$prev" = "--dest" ]; then dest="$a"; fi; prev="$a"; done
  [ -n "$dest" ] && : > "$dest/juniper_ml-${SIMVERSION}-py3-none-any.whl"
fi
exit 0
"""
PY_STUB = r"""#!/bin/bash
echo "PY $*" >> "$SIMLOG"
case "$*" in
  *tomllib*) echo "$SIMVERSION"; exit 0 ;;
  -mpip*|"-m pip"*) exit 0 ;;
esac
exit "${PYEXIT:-0}"
"""
SLEEP_STUB = '#!/bin/bash\necho "SLEEP $*" >> "$SIMLOG"\n'


def run_install(wf: dict, out: Path, pyexit: int) -> "tuple[int, list[str]]":
    """Run WF's install script under ``bash -e`` (the runner's default) with the stand-ins; return (rc, log)."""
    out.mkdir(parents=True, exist_ok=True)
    bindir = out / "bin"
    bindir.mkdir(exist_ok=True)
    for name, body in (("pip", PIP_STUB), ("python", PY_STUB), ("sleep", SLEEP_STUB)):
        (bindir / name).write_text(body, encoding="utf-8")
        (bindir / name).chmod(0o755)
    ws = out / "ws"
    for rel in ("pyproject.toml", "juniper-recurrence-model/juniper_recurrence_model/_version.py"):
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text('version = "0.15.0"\n__version__ = "0.15.0"\n', encoding="utf-8")
    for d in ("runner_temp", "tmpdir"):
        (out / d).mkdir(exist_ok=True)
    log = out / "log"
    log.write_text("", encoding="utf-8")
    script = out / "install.sh"
    script.write_text(str(install_step(wf)["run"]), encoding="utf-8")
    env = {
        "PATH": f"{bindir}:/usr/bin:/bin",
        "SIMLOG": str(log),
        "SIMVERSION": "0.15.0",
        "PYEXIT": str(pyexit),
        "RUNNER_TEMP": str(out / "runner_temp"),
        "GITHUB_WORKSPACE": str(ws),
        "HOME": str(out),
        "TMPDIR": str(out / "tmpdir"),
        "RELEASE_TAG": "v0.15.0",
    }
    proc = subprocess.run(["bash", "-e", str(script)], env=env, capture_output=True, text=True, cwd=str(ws), check=False, timeout=60)
    return proc.returncode, log.read_text(encoding="utf-8").splitlines()


def mutants(template: Path, port: Path, ml: Path, checker: Path, out: Path) -> int:
    t, p, m = load(template), load(port), load(ml)
    fetch_t = '"juniper-cascor==${VERSION}"'
    rows: list[tuple[str, str, str, dict]] = [
        ("T0", "control: cascor template, unchanged", "-", t),
        ("M1", "import piped: `python -c ... | tee $RUNNER_TEMP/import.log`", "import fails the step (I8)", edit_run(t, last_line(t).strip(), last_line(t).strip() + ' | tee "${RUNNER_TEMP}/import.log"')),
        ("M2", "import backgrounded: `python -c ... &`", "import fails the step (I8)", edit_run(t, last_line(t).strip(), last_line(t).strip() + " &")),
        ("M3", "`python() ( true )`: a function with a subshell body", "r3: no alias or function", before_last(t, "python() ( true )")),
        ("M4", "`hash -p /usr/bin/true python`", "r3: no PATH, alias or function", before_last(t, "hash -p /usr/bin/true python")),
        ("M5", "`python -mpip install --force-reinstall ... juniper-cascor==0.14.0` from PyPI", "F4: pip in any form", before_last(t, 'python -mpip install --no-deps --force-reinstall --index-url https://pypi.org/simple/ "juniper-cascor==0.14.0"')),
        ("M6", '`"${p:-pip}" install --force-reinstall ... juniper-cascor==0.14.0` from PyPI', "F4: pip in any form", before_last(t, '"${p:-pip}" install --no-deps --force-reinstall --index-url https://pypi.org/simple/ "juniper-cascor==0.14.0"')),
        ("M7", "`pip${u} config set global.extra-index-url https://pypi.org/simple/` before the fetch", "F4: pip config", edit_run(t, 'VERSION="${RELEASE_TAG#v}"', 'VERSION="${RELEASE_TAG#v}"\npip${u} config set global.extra-index-url https://pypi.org/simple/')),
        ("M8", "fetch target unquoted; VERSION carries `--extra-index-url=https://pypi.org/simple/`", "F2: TestPyPI alone", edit_run(edit_run(t, fetch_t, "juniper-cascor==${VERSION}"), 'VERSION="${RELEASE_TAG#v}"', 'VERSION="${RELEASE_TAG#v} --extra-index-url=https://pypi.org/simple/"')),
        ("P0", "control: recurrence-model port (set -euo pipefail)", "-", p),
        ("M9", "import piped, in a script with `set -o pipefail`", "import fails the step (I8)", edit_run(p, last_line(p).strip(), last_line(p).strip() + ' | tee "${RUNNER_TEMP}/import.log"')),
        ("M10", "import backgrounded, in a script with `set -o pipefail`", "import fails the step (I8)", edit_run(p, last_line(p).strip(), last_line(p).strip() + " &")),
        ("ML0", "control: juniper-ml publish.yml with the F2 edits", "-", m),
        ("M11", 'a file copied into the fresh --dest before the fetch: `cp "${RUNNER_TEMP}/old.whl" "${DOWNLOAD_DIR}/juniper_ml-${VERSION}-py3-none-any.whl"`', "F2: --dest an empty mktemp -d", edit_run(m, 'FETCHED=0', 'cp "${RUNNER_TEMP}/old.whl" "${DOWNLOAD_DIR}/juniper_ml-${VERSION}-py3-none-any.whl"\nFETCHED=0')),
    ]
    # Workflow-level mutants, outside the install script.
    b = copy.deepcopy(t)
    b["jobs"]["build"]["defaults"] = {"run": {"shell": "bash -c 'cp \"$GITHUB_WORKSPACE\"/stash/*.whl \"$GITHUB_WORKSPACE\"/dist/ 2>/dev/null; exec bash -e \"$0\"' {0}"}}
    rows.append(("M12", "build job `defaults.run.shell` that copies a file into dist/ before every default-shell step", "F1: nothing may write into the dist before the record", b))
    a = copy.deepcopy(t)
    steps = a["jobs"]["build"]["steps"]
    at = [i for i, s in enumerate(steps) if s.get("name") == "Record SHA256SUMS"][0]
    steps.insert(at, {"name": "Assert release tag matches built version", "if": "steps.reuse.outputs.reuse != 'true'", "run": 'util/assert_release_tag.bash --ref "${{ github.ref }}" --dist-dir dist --expect-prefix v'})
    rows.append(("M13", "juniper-ml's tag-assert step in cascor (a non-ml repo): a repo script runs between build and record", "F1: the window allow-list", a))
    c = copy.deepcopy(t)
    c["jobs"]["pypi"]["concurrency"] = "publish-pypi-${{ github.ref_name }}"
    rows.append(("M14", "a job-level concurrency group (no cancel-in-progress) on the PyPI job", "r3: no cancelling concurrency", c))
    r = copy.deepcopy(t)
    r["jobs"]["republish"]["timeout-minutes"] = 30
    rows.append(("M15", "timeout-minutes on the republish job (a key F7 admits on every job)", "F7 on the checker side; republish identity", r))
    out.mkdir(parents=True, exist_ok=True)
    print(f"{'id':5s} {'checker':7s} {'rc(py ok)':9s} {'rc(import fails)':16s} target / mutant")
    for ident, label, target, wf in rows:
        path = out / f"{ident}.yml"
        dump(wf, path)
        verdict, reasons = checker_verdict(checker, template, path)
        try:
            rc_ok, log_ok = run_install(wf, out / f"{ident}.run_ok", 0)
            rc_bad, _ = run_install(wf, out / f"{ident}.run_bad", 1)
        except (subprocess.TimeoutExpired, AssertionError) as exc:
            rc_ok, rc_bad, log_ok = "-", "-", [f"not run: {exc}"]
        print(f"{ident:5s} {verdict:7s} {rc_ok!s:9s} {rc_bad!s:16s} [{target}] {label}")
        for reason in reasons[:3]:
            print(f"        checker: {reason[:220]}")
        shown = [ln for ln in log_ok if not ln.startswith("SLEEP")]
        for line in shown[:6]:
            print(f"        ran: {line[:220]}")
    return 0


def _my_edits(wf_prefix: str) -> "list[tuple[str, str, list[tuple[str, object]]]]":
    """This review's edits, in round 2's suite() shape: (id, kind, [(file, (old, new) | callable)])."""
    pub, prot = wf_prefix + "publish.yml", wf_prefix + "publish-protocol.yml"
    pypi_job = "  pypi:\n    name: Publish to PyPI\n    needs: [testpypi, verify-testpypi-install]\n"
    ref = "docs/ci_cd/REFERENCE.md"
    poll = "The JSON checks poll up to 20 times, 15 s apart"
    return [
        ("E1 timeout-minutes on every job of publish.yml", "harmless", [(pub, ("    runs-on: ubuntu-latest\n", "    runs-on: ubuntu-latest\n    timeout-minutes: 30\n"))]),
        ("E2 job concurrency on the PyPI job, cancel-in-progress false", "admitted", [(pub, (pypi_job, pypi_job + "    concurrency:\n      group: pypi-${{ github.ref_name }}\n      cancel-in-progress: false\n"))]),
        ("E3 job concurrency on the PyPI job, a group name alone", "admitted", [(pub, (pypi_job, pypi_job + "    concurrency: pypi-${{ github.ref_name }}\n"))]),
        ("E4 job concurrency on the PyPI job, cancel-in-progress true", "must fail", [(pub, (pypi_job, pypi_job + "    concurrency:\n      group: pypi-${{ github.ref_name }}\n      cancel-in-progress: true\n"))]),
        ("E5 workflow concurrency, cancel-in-progress true (publish.yml)", "must fail", [(pub, ("permissions: {}\n\nenv:\n", "permissions: {}\n\nconcurrency:\n  group: publish-${{ github.ref_name }}\n  cancel-in-progress: true\n\nenv:\n"))]),
        ("E6 workflow concurrency, cancel-in-progress an expression (publish.yml)", "must fail", [(pub, ("permissions: {}\n\nenv:\n", "permissions: {}\n\nconcurrency:\n  group: publish-${{ github.ref_name }}\n  cancel-in-progress: ${{ github.event_name == 'workflow_dispatch' }}\n\nenv:\n"))]),
        ("E7 run-name on publish-protocol.yml", "harmless", [(prot, ("name: Publish juniper-cascor-protocol to PyPI\n", "name: Publish juniper-cascor-protocol to PyPI\nrun-name: Publish ${{ github.ref_name }}\n"))]),
        ("E8 timeout-minutes at the workflow level (not a workflow key)", "must fail", [(pub, ("permissions: {}\n\nenv:\n", "permissions: {}\n\ntimeout-minutes: 30\n\nenv:\n"))]),
        ("E9 run-name on a job (not a job key)", "must fail", [(pub, (pypi_job, pypi_job + "    run-name: x\n"))]),
        ("E10 sub-package workflow concurrency made cancelling", "must fail", [(prot, ("  cancel-in-progress: false\n", "  cancel-in-progress: true\n"))]),
        ("E11 REFERENCE poll interval changed 15 -> 16 s", "must fail", [(ref, (poll, poll.replace("15 s apart", "16 s apart")))]),
        ("E12 REFERENCE poll sentence broken over two lines", "harmless", [(ref, (poll, poll.replace("20 times,", "20\ntimes,")))]),
    ]


def edits(base: Path, work: Path, python: str) -> int:
    spec = importlib.util.spec_from_file_location("r2_probes", R2_PROBES)
    module = importlib.util.module_from_spec(spec)
    sys.modules["r2_probes"] = module
    spec.loader.exec_module(module)
    module._edits = lambda: _my_edits(module.WF)
    return module.suite(base, work, python, None)


ML_TESTS = ("test_publish_testpypi_verify.py", "test_publish_subpackage_workflows.py", "redacted_env.py")
SUBPACKAGES = ("ci-tools", "config-tools", "doc-tools", "model-core", "observability", "service-core")


def _unittest(tree: Path, python: str) -> "tuple[str, list[str]]":
    env = {k: v for k, v in os.environ.items()}
    env["TMPDIR"] = str(tree / "tmpdir")
    (tree / "tmpdir").mkdir(exist_ok=True)
    proc = subprocess.run([python, "-m", "unittest", "-v", "tests.test_publish_testpypi_verify", "tests.test_publish_subpackage_workflows"], cwd=str(tree), capture_output=True, text=True, env=env, check=False)
    text = proc.stdout + proc.stderr
    summary = [ln for ln in text.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    skipped = [ln for ln in text.splitlines() if "skipped" in ln and ("..." in ln or ln.startswith(("setUpClass", "test")))]
    return " | ".join(summary), skipped


def ml_skip(ml_root: Path, port_dir: Path, out: Path, python: str) -> int:
    """Run juniper-ml's two publish test modules against main's workflows and against the ported ones."""
    variants = {"main": {}, "port": {}}
    wf_main = ml_root / DOTGITHUB / "workflows"
    variants["main"]["publish.yml"] = wf_main / "publish.yml"
    variants["port"]["publish.yml"] = port_dir / "faithful+ml-F2" / "juniper-ml" / "workflows" / "publish.yml"
    for suffix in SUBPACKAGES:
        name = f"publish-{suffix}.yml"
        variants["main"][name] = wf_main / name
        variant = "reorder" if suffix in ("config-tools", "doc-tools") else "faithful"
        variants["port"][name] = port_dir / variant / "juniper-ml" / "workflows" / name
    for label, files in variants.items():
        tree = out / label
        if tree.exists():
            shutil.rmtree(tree)
        (tree / DOTGITHUB / "workflows").mkdir(parents=True)
        (tree / "tests").mkdir()
        for name, src in files.items():
            shutil.copyfile(src, tree / DOTGITHUB / "workflows" / name)
        for name in ML_TESTS:
            shutil.copyfile(ml_root / "tests" / name, tree / "tests" / name)
        summary, skipped = _unittest(tree, python)
        print(f"== {label}: {summary}")
        for line in skipped:
            print(f"   {line[:200]}")
    return 0


def gh_get(path: str) -> "dict | list":
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"gh api {path}: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout)


def fetch(repo: str, ref: str, out: Path, paths: "list[str]") -> int:
    for rel in paths:
        data = gh_get(f"repos/pcalnon/{repo}/contents/{rel}?ref={ref}")
        dest = out / repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(base64.b64decode(data["content"]))
        print(f"{repo}/{rel} @ {ref}: blob {data['sha'][:12]} -> {dest}")
    return 0


def tree(repo: str, ref: str, pattern: str) -> int:
    data = gh_get(f"repos/pcalnon/{repo}/{'g' + 'it'}/trees/{ref}?recursive=1")
    for item in data.get("tree") or []:
        if item.get("type") == "blob" and re.search(pattern, item["path"]):
            print(item["path"])
    if data.get("truncated"):
        print("(listing truncated)")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mutants")
    for name in ("--template", "--port", "--ml", "--checker", "--out"):
        p.add_argument(name, required=True, type=Path)
    p = sub.add_parser("edits")
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--python", required=True)
    p = sub.add_parser("ml-skip")
    p.add_argument("--ml-root", required=True, type=Path)
    p.add_argument("--port-dir", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--python", required=True)
    p = sub.add_parser("fetch")
    p.add_argument("--repo", required=True)
    p.add_argument("--ref", default="main")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("paths", nargs="+")
    p = sub.add_parser("tree")
    p.add_argument("--repo", required=True)
    p.add_argument("--ref", default="main")
    p.add_argument("--pattern", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "mutants":
        return mutants(args.template.resolve(), args.port.resolve(), args.ml.resolve(), args.checker.resolve(), args.out.resolve())
    if args.cmd == "edits":
        return edits(args.base.resolve(), args.work.resolve(), args.python)
    if args.cmd == "ml-skip":
        return ml_skip(args.ml_root.resolve(), args.port_dir.resolve(), args.out.resolve(), args.python)
    if args.cmd == "fetch":
        return fetch(args.repo, args.ref, args.out.resolve(), args.paths)
    if args.cmd == "tree":
        return tree(args.repo, args.ref, args.pattern)
    return 2


if __name__ == "__main__":
    sys.exit(main())
