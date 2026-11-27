#!/usr/bin/env python3
"""Round-2 adversarial review probes for juniper-cascor's one-artifact sweep (the fix pass): run, don't read.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (round-2 review of the sweep's fix pass, diff sha256 0056f312...)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: tmp/sweep/cascor-r2/juniper-cascor (the frozen round-2 tree: never edited, only copied);
         util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker whose rules the ports must
         satisfy); tmp/sweep/REVIEW_DISPOSITIONS.md (the fix list)

Why
---
A fix pass is the least trustworthy part of a change. Each subcommand executes one claim instead of reading it:

- ``loop-sim``: runs each publisher's real install script (parsed from its YAML) under the runner's default shell
  (``bash -e {0}``) against stub ``pip``/``python``/``sleep`` that fail a chosen number of times, and reports whether
  a failure can pass, whether ``exit 1`` is reached on the fifth failure, and whether the import runs last.
- ``findspec``: runs the protocol publisher's real ``python -c`` line against fake installs (metadata only, a regular
  package, a namespace directory, a module file), with and without ``PYTHONOPTIMIZE``.
- ``fetch-ports``: reads (GET only, ``gh api``) the 15 port targets' publish workflows from each repo's ``main`` into
  ``--out/<repo>/workflows/``, and prints each file's blob sha.

    python3 -I util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py loop-sim --wf-dir DIR --out DIR
    python3 -I util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py fetch-ports --out DIR

Exit status: 0 always for probes (each prints what it measured); 2 on a usage error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

INSTALL_JOB = "Verify the TestPyPI install"
PIP_STUB = '#!/bin/bash\nc=$(cat "$SIMSTATE/count" 2>/dev/null || echo 0); c=$((c+1)); echo $c > "$SIMSTATE/count"\necho "PIP[$c] cwd=$PWD args=$*" >> "$SIMSTATE/log"\nif [ "$c" -le "${FAILS:-0}" ]; then exit 1; fi\nexit 0\n'
PY_STUB = '#!/bin/bash\necho "PY cwd=$PWD args=$*" >> "$SIMSTATE/log"\nexit ${PYEXIT:-0}\n'
SLEEP_STUB = '#!/bin/bash\necho "SLEEP $*" >> "$SIMSTATE/log"\n'


def install_script(path: Path) -> "tuple[str, dict]":
    wf = yaml.safe_load(path.read_text(encoding="utf-8"))
    job = [j for j in wf["jobs"].values() if j.get("name") == INSTALL_JOB][0]
    step = [s for s in job["steps"] if "run" in s][0]
    return step["run"], step.get("env") or {}


def loop_sim(wf_dir: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    bindir = out / "bin"
    bindir.mkdir(exist_ok=True)
    for name, body in (("pip", PIP_STUB), ("python", PY_STUB), ("sleep", SLEEP_STUB)):
        (bindir / name).write_text(body, encoding="utf-8")
        (bindir / name).chmod(0o755)
    ws = out / "ws"
    for pkg, ver in (("juniper-cascor-protocol", "0.3.0"), ("juniper-cascor-model", "0.2.1")):
        (ws / pkg).mkdir(parents=True, exist_ok=True)
        (ws / pkg / "pyproject.toml").write_text(f'[project]\nname = "{pkg}"\nversion = "{ver}"\n', encoding="utf-8")
    runner_temp = out / "runner_temp"
    runner_temp.mkdir(exist_ok=True)
    for path in sorted(wf_dir.glob("publish*.yml")):
        run, step_env = install_script(path)
        script = out / f"{path.name}.sh"
        script.write_text(run, encoding="utf-8")
        for fails, pyexit in ((0, 0), (1, 0), (4, 0), (5, 0), (9, 0), (0, 1)):
            state = out / f"state_{path.name}_{fails}_{pyexit}"
            state.mkdir(exist_ok=True)
            for p in state.iterdir():
                p.unlink()
            env = {
                "PATH": f"{bindir}:/usr/bin:/bin",
                "SIMSTATE": str(state),
                "FAILS": str(fails),
                "PYEXIT": str(pyexit),
                "RUNNER_TEMP": str(runner_temp),
                "GITHUB_WORKSPACE": str(ws),
                "HOME": str(out),
                "RELEASE_TAG": "v0.14.1",
            }
            # The runner's default for a `run` step with no `shell:` on Linux is `bash -e {0}`.
            r = subprocess.run(["bash", "-e", str(script)], env=env, capture_output=True, text=True, cwd=str(ws), check=False)
            log = (state / "log").read_text(encoding="utf-8").splitlines() if (state / "log").exists() else []
            pips = [line for line in log if line.startswith("PIP")]
            pys = [line for line in log if line.startswith("PY")]
            errors = [line for line in r.stdout.splitlines() if line.startswith("::error::")]
            last = log[-1].split(" ", 1)[0] if log else "-"
            print(f"{path.name:26s} pip-fails={fails} py-exit={pyexit} -> rc={r.returncode} pip-calls={len(pips)} python-ran={bool(pys)} last-call={last} errors={len(errors)}")
            if errors:
                print(f"    {errors[0]}")
            if fails == 0 and pyexit == 0:
                print(f"    pip: {pips[0] if pips else '-'}")
                print(f"    py : {pys[0] if pys else '-'}")
                print(f"    step env: {sorted(step_env)}")
    return 0


def findspec(wf_dir: Path, out: Path) -> int:
    """Run the protocol publisher's real ``python -c`` line against fake installs: metadata only, a regular package, a
    namespace directory, and each of those under PYTHONOPTIMIZE (which strips ``assert``)."""
    run, _ = install_script(wf_dir / "publish-protocol.yml")
    line = [c for c in run.splitlines() if c.strip().startswith("python -c ")][-1].strip()
    code = line[len("python -c ") :].strip()
    assert code[0] == code[-1] == '"', code
    code = code[1:-1]
    out.mkdir(parents=True, exist_ok=True)
    cwd = out / "cwd"
    cwd.mkdir(exist_ok=True)
    cases = {}
    for case in ("metadata-only", "regular-package", "namespace-dir", "module-file"):
        site = out / case
        site.mkdir(exist_ok=True)
        di = site / "juniper_cascor_protocol-0.3.0.dist-info"
        di.mkdir(exist_ok=True)
        (di / "METADATA").write_text("Metadata-Version: 2.1\nName: juniper-cascor-protocol\nVersion: 0.3.0\n", encoding="utf-8")
        if case == "regular-package":
            (site / "juniper_cascor_protocol").mkdir(exist_ok=True)
            (site / "juniper_cascor_protocol" / "__init__.py").write_text("raise SystemExit('the package ran')\n", encoding="utf-8")
        if case == "namespace-dir":
            (site / "juniper_cascor_protocol").mkdir(exist_ok=True)
        if case == "module-file":
            (site / "juniper_cascor_protocol.py").write_text("", encoding="utf-8")
        cases[case] = site
    for case, site in cases.items():
        for optimize in ("", "1"):
            env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(site), "HOME": str(out)}
            if optimize:
                env["PYTHONOPTIMIZE"] = optimize
            r = subprocess.run([os.environ.get("PROBE_PYTHON", sys.executable), "-s", "-c", code], env=env, capture_output=True, text=True, cwd=str(cwd), check=False)
            tail = (r.stdout.strip() or r.stderr.strip().splitlines()[-1] if (r.stdout.strip() or r.stderr.strip()) else "")
            print(f"{case:16s} PYTHONOPTIMIZE={optimize or '-':2s} rc={r.returncode} {tail[:150]}")
    return 0


#: The 15 port targets of the sweep: repo -> its publish workflows.
PORTS = {
    "juniper-canopy": ["publish.yml"],
    "juniper-data": ["publish.yml"],
    "juniper-data-client": ["publish.yml"],
    "juniper-cascor-client": ["publish.yml"],
    "juniper-cascor-worker": ["publish.yml"],
    "juniper-recurrence": ["publish-recurrence-app.yml", "publish-recurrence-client.yml", "publish-recurrence-model.yml"],
    "juniper-ml": ["publish.yml", "publish-ci-tools.yml", "publish-config-tools.yml", "publish-doc-tools.yml", "publish-model-core.yml", "publish-observability.yml", "publish-service-core.yml"],
}


def fetch_ports(out: Path) -> int:
    import base64
    import hashlib
    import json

    for repo, files in PORTS.items():
        dest = out / repo / "workflows"
        dest.mkdir(parents=True, exist_ok=True)
        for name in files:
            # GET only: the contents API at main.
            r = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/contents/%2Egithub/workflows/{name}?ref=main"], capture_output=True, text=True, check=False)
            if r.returncode != 0:
                print(f"FAILED {repo}/{name}: {r.stderr.strip()[:200]}")
                continue
            data = json.loads(r.stdout)
            body = base64.b64decode(data["content"])
            (dest / name).write_bytes(body)
            print(f"{repo}/{name}: blob {data['sha'][:12]}, {body.count(b'\n')} lines, sha256 {hashlib.sha256(body).hexdigest()[:12]}")
    return 0


TEMPLATE_STEPS = {"Download dist artifacts", "Verify the dist against SHA256SUMS", "Verify TestPyPI serves exactly these files"}


def show_install(root: Path) -> int:
    """For each port target under ROOT: the TestPyPI job's keys and steps, and every step that is not a template step
    or the upload (the install check and what it needs), in full."""
    for repo, files in PORTS.items():
        for name in files:
            path = root / repo / "workflows" / name
            wf = yaml.safe_load(path.read_text(encoding="utf-8"))
            jobs = wf["jobs"]
            test = [(j, job) for j, job in jobs.items() if job.get("name") == "Publish to TestPyPI"]
            print("=" * 120)
            print(f"{repo}/{name}: workflow env {wf.get('env')}; top permissions {wf.get('permissions')}; jobs {[(j, job.get('name')) for j, job in jobs.items()]}")
            if len(test) != 1:
                print(f"   !! {len(test)} jobs named 'Publish to TestPyPI'")
                continue
            job_id, job = test[0]
            print(f"   job {job_id}: keys {sorted(job)}; permissions {job.get('permissions')}; defaults {job.get('defaults')}; env {job.get('env')}; runs-on {job.get('runs-on')}")
            for i, s in enumerate(job.get("steps") or []):
                label = s.get("name") or s.get("uses")
                if label in TEMPLATE_STEPS or str(s.get("uses") or "").startswith("pypa/gh-action-pypi-publish@"):
                    print(f"   [{i}] (template) {label}")
                    continue
                print(f"   [{i}] {label}")
                for key, value in s.items():
                    if key == "run":
                        print("        run: |")
                        for line in str(value).splitlines():
                            print(f"          {line}")
                    elif key != "name":
                        print(f"        {key}: {value}")
    return 0


#: The template's install loop (cascor round 2), filled with a package and the shell variable holding its version.
TEMPLATE_LOOP = (
    "for attempt in 1 2 3 4 5; do\n"
    "  if pip install \\\n"
    "    --no-deps \\\n"
    "    --index-url https://test.pypi.org/simple/ \\\n"
    '    "{pkg}==${{{var}}}"; then\n'
    "    break\n"
    "  fi\n"
    '  if [ "${{attempt}}" -eq 5 ]; then\n'
    '    echo "::error::{pkg} ${{{var}}} is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"\n'
    "    exit 1\n"
    "  fi\n"
    '  echo "TestPyPI index lag — retrying in 10s (attempt ${{attempt}}/5)"\n'
    "  sleep 10\n"
    "done"
)
TAG_EXPR = "${{ github.event.release.tag_name }}"
CHECKER_NAME = "2026-11-23_publish_port_template_identity.py"


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))
    return data


def _step_named(job: dict, name: str) -> dict:
    found = [s for s in job.get("steps") or [] if s.get("name") == name]
    assert len(found) == 1, (name, [s.get("name") for s in job.get("steps") or []])
    return found[0]


def _port_install_script(orig: str, pkg: str, sparse: "str | None", variant: str) -> "tuple[str, dict, list[str]]":
    """The repo's own install commands moved into the new job with the template's mechanical changes only: ``cd`` to
    $RUNNER_TEMP first, a file the version is read from addressed under $GITHUB_WORKSPACE, the tag through env, and the
    target install inside the template's loop. Everything else keeps its order. Returns (script, step env, notes)."""
    lines = [ln.rstrip() for ln in orig.splitlines()]
    body = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    notes: list[str] = []
    env: dict = {}
    head: list[str] = []
    if body and body[0].startswith("set -"):
        head.append(body.pop(0))
    head.append('cd "${RUNNER_TEMP}"')
    # The target install: a `for attempt ... done` block holding `pip install ... <pkg>==`, or one such line.
    start = end = None
    var = None
    for i, c in enumerate(body):
        if c.startswith("for attempt in") and start is None:
            j = body.index("done", i)
            block = " ".join(body[i : j + 1])
            if "pip install" in block and f"{pkg}==" in block:
                start, end = i, j
                break
        if c.startswith("pip install") and f"{pkg}==" in c and "--index-url https://test.pypi.org/simple/" in c:
            start = end = i
            break
    if start is None:
        notes.append("no TestPyPI install of the target package found: kept the script's own fetch unchanged")
        pre, post, loop = body, [], []
    else:
        block = " ".join(body[start : end + 1])
        var = re.search(re.escape(pkg) + r"==\$\{(\w+)\}", block).group(1)
        pre, post = body[:start], body[end + 1 :]
        loop = TEMPLATE_LOOP.format(pkg=pkg, var=var).splitlines()
    out_pre: list[str] = []
    for c in pre:
        if c == 'cd "${RUNNER_TEMP}"':
            continue
        if TAG_EXPR in c:
            env["RELEASE_TAG"] = TAG_EXPR
            notes.append("tag through env RELEASE_TAG")
            c = c.replace(f'"{TAG_EXPR}"', '"${RELEASE_TAG}"').replace(TAG_EXPR, "${RELEASE_TAG}")
        if "open('pyproject.toml','rb')" in c:
            c = c.replace("open('pyproject.toml','rb')", "open('${GITHUB_WORKSPACE}/pyproject.toml','rb')")
            notes.append("pyproject.toml read under $GITHUB_WORKSPACE")
        if sparse and sparse in c and f'"${{GITHUB_WORKSPACE}}/{sparse}"' not in c:
            c = c.replace(f" {sparse}", f' "${{GITHUB_WORKSPACE}}/{sparse}"')
            notes.append(f"{sparse} read under $GITHUB_WORKSPACE")
        out_pre.append(c)
    # Collapse VERSION="${RELEASE_TAG}" + VERSION="${VERSION#v}" into the template's one line.
    if 'VERSION="${RELEASE_TAG}"' in out_pre and 'VERSION="${VERSION#v}"' in out_pre:
        i = out_pre.index('VERSION="${RELEASE_TAG}"')
        out_pre[i] = 'VERSION="${RELEASE_TAG#v}"'
        out_pre.remove('VERSION="${VERSION#v}"')
    post = [c for c in post if c != 'cd "${RUNNER_TEMP}"']
    if variant == "reorder":
        # Move the python -c checks after every other post-install command (both still run, under bash -e).
        checks = [c for c in post if re.match(r"python3? -c ", c)]
        post = [c for c in post if c not in checks] + checks
        notes.append("python -c moved last")
    script = "\n".join(head + out_pre + loop + post) + "\n"
    return script, env, notes


def port_sim(template_dir: Path, root: Path, out: Path, checker: Path) -> int:
    """Build a faithful port of each target, and variants, then run the checker on every one."""
    single = _load(template_dir / "publish.yml")
    tjobs = single["jobs"]
    tmpl = {
        "build": {n: _step_named(tjobs["build"], n) for n in ("Reuse an earlier attempt's artifact", "Record SHA256SUMS", "Upload dist artifacts")},
        "test": {n: _step_named(tjobs["testpypi"], n) for n in ("Download dist artifacts", "Verify the dist against SHA256SUMS", "Verify TestPyPI serves exactly these files")},
        "prod": {n: _step_named(tjobs["pypi"], n) for n in ("Download dist artifacts", "Verify the dist against SHA256SUMS", "Verify TestPyPI still serves exactly these files", "Verify PyPI serves exactly these files")},
    }
    republish = tjobs["republish"]
    dispatch = single["on"]["workflow_dispatch"]
    out.mkdir(parents=True, exist_ok=True)
    built: list[tuple[str, str, Path, list[str]]] = []
    for repo, files in PORTS.items():
        for name in files:
            src = _load(root / repo / "workflows" / name)
            pkg = src["env"]["PUBLISH_PACKAGE"]
            dist = src["env"]["PUBLISH_DIST_DIR"]
            prefix = "v" if dist == "dist" else f"{pkg}-v"
            jobs = src["jobs"]
            test_id = [j for j, job in jobs.items() if job.get("name") == "Publish to TestPyPI"][0]
            prod_id = [j for j, job in jobs.items() if job.get("name") == "Publish to PyPI"][0]
            test, prod, build = jobs[test_id], jobs[prod_id], jobs["build"]
            install_steps = [s for s in test["steps"] if (s.get("name") or s.get("uses")) not in tmpl["test"] and not str(s.get("uses") or "").startswith("pypa/")]
            setup = [s for s in install_steps if str(s.get("uses") or "").startswith("actions/setup-python@")]
            checkout = [s for s in install_steps if str(s.get("uses") or "").startswith("actions/checkout@")]
            runs = [s for s in install_steps if "run" in s]
            assert len(runs) == 1, (repo, name, [s.get("name") for s in runs])
            sparse = None
            if checkout and (checkout[0].get("with") or {}).get("sparse-checkout"):
                sparse = str(checkout[0]["with"]["sparse-checkout"]).strip()
            guard_dispatch = "workflow_dispatch" in str(build.get("if") or "")
            for variant in ("faithful", "reorder", "faithful+drop-build-extra"):
                script, step_env, notes = _port_install_script(runs[0]["run"], pkg, sparse, "reorder" if variant == "reorder" else "faithful")
                if variant == "reorder" and "python -c moved last" in notes and script == _port_install_script(runs[0]["run"], pkg, sparse, "faithful")[0]:
                    continue  # the reorder changes nothing for this script
                wf = dict(src)
                wf["env"] = {"PUBLISH_PACKAGE": pkg, "PUBLISH_DIST_DIR": dist, "PUBLISH_TAG_PREFIX": prefix}
                wf["on"] = {"release": {"types": ["published"]}, "workflow_dispatch": dispatch}
                new_build = dict(build)
                new_build["if"] = (
                    f"(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))"
                    if guard_dispatch
                    else f"startsWith(github.event.release.tag_name, '{prefix}')"
                )
                steps = [tmpl["build"].get(s.get("name"), s) for s in build["steps"]]
                if variant == "faithful+drop-build-extra":
                    # Drop any step between the build command and Record SHA256SUMS that is not `twine check`.
                    bi = [i for i, s in enumerate(steps) if re.search(r"\bpython3?\s+-m\s+build\b", str(s.get("run") or ""))][0]
                    ri = [i for i, s in enumerate(steps) if s.get("name") == "Record SHA256SUMS"][0]
                    dropped = [s.get("name") for s in steps[bi + 1 : ri] if not str(s.get("run") or "").strip().startswith("twine check ")]
                    steps = steps[: bi + 1] + [s for s in steps[bi + 1 : ri] if str(s.get("run") or "").strip().startswith("twine check ")] + steps[ri:]
                    if not dropped:
                        continue
                    notes = notes + [f"dropped build step(s) {dropped}"]
                new_build["steps"] = steps
                upload_t = [s for s in test["steps"] if str(s.get("uses") or "").startswith("pypa/")][0]
                upload_p = [s for s in prod["steps"] if str(s.get("uses") or "").startswith("pypa/")][0]
                new_test = {k: v for k, v in test.items() if k != "steps"}
                new_test["permissions"] = {"id-token": "write"}
                new_test["steps"] = [tmpl["test"]["Download dist artifacts"], tmpl["test"]["Verify the dist against SHA256SUMS"], upload_t, tmpl["test"]["Verify TestPyPI serves exactly these files"]]
                install_job_steps = [dict(s) for s in setup]
                if checkout or "pyproject.toml read under $GITHUB_WORKSPACE" in notes:
                    path = sparse or "pyproject.toml"
                    install_job_steps.append({"uses": (checkout[0] if checkout else {"uses": "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"})["uses"], "with": {"sparse-checkout": f"{path}\n", "persist-credentials": False}})
                istep = {"name": runs[0]["name"]}
                if step_env:
                    istep["env"] = step_env
                istep["run"] = script
                install_job_steps.append(istep)
                install = {"name": "Verify the TestPyPI install", "needs": test_id, "runs-on": "ubuntu-latest", "permissions": {"contents": "read"}, "steps": install_job_steps}
                new_prod = {k: v for k, v in prod.items() if k != "steps"}
                new_prod["needs"] = [test_id, "verify-testpypi-install"]
                new_prod["permissions"] = {"id-token": "write"}
                new_prod["steps"] = [tmpl["prod"]["Download dist artifacts"], tmpl["prod"]["Verify the dist against SHA256SUMS"], tmpl["prod"]["Verify TestPyPI still serves exactly these files"], upload_p, tmpl["prod"]["Verify PyPI serves exactly these files"]]
                new_jobs = {"build": new_build, test_id: new_test, "verify-testpypi-install": install, prod_id: new_prod}
                for j, job in jobs.items():
                    if j not in ("build", test_id, prod_id, "republish"):
                        new_jobs[j] = job
                new_jobs["republish"] = republish
                wf["jobs"] = new_jobs
                dest = out / variant / repo / "workflows" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(yaml.safe_dump(wf, sort_keys=False, width=100000, allow_unicode=True), encoding="utf-8")
                built.append((f"{repo}/{name}", variant, dest, notes))
    for label, variant, dest, notes in built:
        r = subprocess.run([sys.executable, "-I", str(checker), "--template", str(template_dir / "publish.yml"), str(dest)], capture_output=True, text=True, check=False)
        lines = [ln for ln in r.stdout.splitlines() if ln.startswith("    - ")]
        print(f"{'PASS' if r.returncode == 0 else 'FAIL'}  {label:50s} [{variant}]  {'; '.join(dict.fromkeys(notes))}")
        for ln in lines:
            print(f"        {ln.strip()[:400]}")
    return 0


def show_job(paths: "list[Path]", job_id: str) -> int:
    """Print one job of each workflow: its wiring, and each step's action or script."""
    for path in paths:
        job = _load(path)["jobs"][job_id]
        print("=" * 100)
        print(path, {k: job.get(k) for k in ("name", "needs", "runs-on", "permissions")})
        for s in job.get("steps") or []:
            if "run" in s:
                print(f"  step {s.get('name')!r} env={s.get('env')}")
                print("\n".join("    " + line for line in str(s["run"]).splitlines()))
            else:
                print(f"  uses {str(s.get('uses')).split('@')[0]} with={s.get('with')}")
    return 0


WF = ".github/workflows/"
ALL3 = [WF + "publish.yml", WF + "publish-protocol.yml", WF + "publish-cascor-model.yml"]
SUMMARY_JOB = '\n  summary:\n    name: Summarize the release\n    needs: [pypi]\n    runs-on: ubuntu-latest\n    permissions: {}\n    steps:\n      - run: echo "published"\n'


def _rewrap(text: str, starts: str, width: int) -> str:
    import textwrap

    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ln.startswith(starts)]
    assert len(hits) == 1, (starts, len(hits))
    lines[hits[0]] = "\n".join(textwrap.wrap(lines[hits[0]], width=width, break_long_words=False, break_on_hyphens=False))
    return "\n".join(lines)


def _edits() -> "list[tuple[str, str, list[tuple[str, object]]]]":
    """(id, kind, [(file, transformation)]): a transformation is (old, new) replacing every occurrence (at least one),
    or a callable on the file's text. kind is 'harmless' (should pass) or 'mutation' (should fail)."""
    ins_after_version = 'VERSION="${RELEASE_TAG#v}"\n'
    return [
        ("H1a dependabot download-artifact all 3", "harmless", [(f, ("actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2", "actions/download-artifact@1111111111111111111111111111111111111111  # v8.0.3")) for f in ALL3]),
        ("H1b dependabot gh-action-pypi-publish all 3", "harmless", [(f, ("pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3", "pypa/gh-action-pypi-publish@2222222222222222222222222222222222222222  # v1.14.4")) for f in ALL3]),
        ("H1c dependabot setup-python all 3", "harmless", [(f, ("actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0", "actions/setup-python@3333333333333333333333333333333333333333  # v7.2.0")) for f in ALL3]),
        ("H1d dependabot checkout all 3", "harmless", [(f, ("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1", "actions/checkout@4444444444444444444444444444444444444444  # v7.0.2")) for f in ALL3]),
        ("H2a reword a YAML comment (publish.yml)", "harmless", [(WF + "publish.yml", ("  # Ruling 2 of 2026-11-16: the install check runs in a job of its own, after the TestPyPI job.", "  # Ruling 2 of 2026-11-16 puts the install check in a job of its own, after the TestPyPI job."))]),
        ("H2b reword a # comment inside the install script (publish.yml)", "harmless", [(WF + "publish.yml", ("# TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so.", "# TestPyPI's simple index may trail its JSON, so: five tries, 10 s apart, then an error naming the lag."))]),
        ("H2c reword a template-step Python comment, ALL copies", "harmless", [(f, ("# publish step uploads every file in it, so an extra file would be published too.", "# publish step uploads every file in it, so an extra file would be published as well.")) for f in ALL3]),
        ("H2d reword a template-step Python comment, ONE copy", "template-drift", [(WF + "publish-protocol.yml", ("# publish step uploads every file in it, so an extra file would be published too.", "# publish step uploads every file in it, so an extra file would be published as well."))]),
        ("H2e reword the install loop's retry echo, all 3", "harmless?", [(f, ("TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)", "TestPyPI has not served it yet; retrying in 10s (attempt ${attempt}/5)")) for f in ALL3]),
        ("H3a rewrap MANUAL install-job paragraph at 120", "harmless", [("docs/ci_cd/MANUAL.md", lambda t: _rewrap(t, "**The install check runs in a job of its own**", 120))]),
        ("H3b rewrap MANUAL install-job paragraph at 100", "harmless", [("docs/ci_cd/MANUAL.md", lambda t: _rewrap(t, "**The install check runs in a job of its own**", 100))]),
        ("H3c rewrap REFERENCE poll paragraph at 120", "harmless", [("docs/ci_cd/REFERENCE.md", lambda t: _rewrap(t, "The JSON checks poll up to", 120))]),
        ("H3d rewrap REFERENCE install-contract paragraph at 120", "harmless", [("docs/ci_cd/REFERENCE.md", lambda t: _rewrap(t, "Each runs in the job `Verify the TestPyPI install`", 120))]),
        ("H4 new unrelated job in publish.yml", "harmless", [(WF + "publish.yml", lambda t: t.rstrip("\n") + "\n" + SUMMARY_JOB)]),
        ("H5 CHANGELOG edit", "harmless", [("CHANGELOG.md", ("## [Unreleased]\n", "## [Unreleased]\n\n- A harmless line a maintainer adds.\n"))]),
        ("H6 timeout-minutes on the install job (publish.yml)", "harmless", [(WF + "publish.yml", ("    name: Verify the TestPyPI install\n    needs: testpypi\n    runs-on: ubuntu-latest\n", "    name: Verify the TestPyPI install\n    needs: testpypi\n    runs-on: ubuntu-latest\n    timeout-minutes: 15\n"))]),
        ("H7 run-name on publish.yml", "harmless", [(WF + "publish.yml", ("name: Publish to PyPI\n\non:\n", "name: Publish to PyPI\nrun-name: Publish ${{ github.ref_name }} to PyPI\n\non:\n"))]),
        ("H8 a concurrency block on publish.yml", "harmless", [(WF + "publish.yml", ("permissions: {}\n", "permissions: {}\n\nconcurrency:\n  group: publish-${{ github.ref_name }}\n  cancel-in-progress: false\n"))]),
        ("H9 install job's setup-python 3.12 -> 3.13 (publish.yml)", "harmless", [(WF + "publish.yml", ('      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n        with:\n          python-version: "3.12"\n\n      - name: Verify TestPyPI install\n', '      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n        with:\n          python-version: "3.13"\n\n      - name: Verify TestPyPI install\n'))]),
        ("H10 rename the install STEP (publish.yml)", "harmless?", [(WF + "publish.yml", ("      - name: Verify TestPyPI install\n", "      - name: Install from TestPyPI and import\n"))]),
        ("Ma export PIP_EXTRA_INDEX_URL in the script", "mutation", [(WF + "publish.yml", (ins_after_version, ins_after_version + "          export PIP_EXTRA_INDEX_URL=https://pypi.org/simple/\n"))]),
        ("Mb pip config set global.extra-index-url", "mutation", [(WF + "publish.yml", (ins_after_version, ins_after_version + "          pip config set global.extra-index-url https://pypi.org/simple/\n"))]),
        ("Mc pip -q install pre-install", "mutation", [(WF + "publish.yml", (ins_after_version, ins_after_version + '          pip -q install "juniper-cascor==${VERSION}"\n'))]),
        ("Md inline PIP_EXTRA_INDEX_URL on the target install", "mutation", [(WF + "publish.yml", ("            if pip install \\\n", "            if PIP_EXTRA_INDEX_URL=https://pypi.org/simple/ pip install \\\n"))]),
        ("Me twine-check step also writes into dist", "mutation", [(WF + "publish.yml", ("        run: twine check dist/*\n", "        run: |\n          twine check dist/*\n          cp dist/*.whl dist/juniper_cascor-0.0.0-py3-none-any.whl\n"))]),
    ]


def suite(base: Path, work: Path, python: str, only: "list[str] | None" = None) -> int:
    import shutil
    import xml.etree.ElementTree as ET

    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(base, work, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    junit = work.parent / f"{work.name}.junit.xml"
    cmd = [python, "-m", "pytest", "src/tests/unit/test_publish_one_artifact.py", "src/tests/unit/test_publish_docs_bounds.py", "-p", "no:cacheprovider", "-q", f"--junitxml={junit}"]

    def run() -> "tuple[int, list[str]]":
        subprocess.run(cmd, cwd=str(work), env=env, capture_output=True, text=True, check=False)
        root = ET.parse(junit).getroot()
        cases = root.iter("testcase")
        failed = [f"{c.get('classname', '').rsplit('.', 1)[-1]}::{c.get('name')}" for c in cases if c.find("failure") is not None or c.find("error") is not None]
        total = sum(1 for _ in root.iter("testcase"))
        return total, failed

    total, failed = run()
    print(f"baseline: {total} cases, {len(failed)} failing {failed}")
    for label, kind, changes in _edits():
        if only and not any(label.startswith(prefix) for prefix in only):
            continue
        saved = {}
        ok = True
        for rel, how in changes:
            path = work / rel
            text = saved.setdefault(rel, path.read_text(encoding="utf-8"))
            current = path.read_text(encoding="utf-8")
            if callable(how):
                new = how(current)
            else:
                old, rep = how
                if current.count(old) < 1:
                    print(f"!! {label}: anchor missing in {rel}: {old[:60]!r}")
                    ok = False
                    break
                new = current.replace(old, rep)
            if new == current:
                print(f"!! {label}: no change in {rel}")
                ok = False
            path.write_text(new, encoding="utf-8")
        if ok:
            total, failed = run()
            verdict = "PASS" if not failed else f"FAIL {len(failed)}"
            print(f"{verdict:8s} [{kind}] {label}")
            for f in failed:
                print(f"           - {f}")
        for rel, text in saved.items():
            (work / rel).write_text(text, encoding="utf-8")
    total, failed = run()
    print(f"after restore: {total} cases, {len(failed)} failing")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("suite")
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--python", required=True)
    p.add_argument("--only", nargs="*", help="run only the edits whose id starts with one of these")
    p = sub.add_parser("show-job")
    p.add_argument("--job", required=True)
    p.add_argument("paths", nargs="+", type=Path)
    p = sub.add_parser("port-sim")
    p.add_argument("--template-dir", required=True, type=Path)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--checker", required=True, type=Path)
    p = sub.add_parser("show-install")
    p.add_argument("--root", required=True, type=Path)
    for name in ("loop-sim", "findspec"):
        p = sub.add_parser(name)
        p.add_argument("--wf-dir", required=True, type=Path)
        p.add_argument("--out", required=True, type=Path)
    p = sub.add_parser("fetch-ports")
    p.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "fetch-ports":
        return fetch_ports(args.out)
    if args.cmd == "show-install":
        return show_install(args.root)
    if args.cmd == "port-sim":
        return port_sim(args.template_dir, args.root, args.out, args.checker)
    if args.cmd == "show-job":
        return show_job(args.paths, args.job)
    if args.cmd == "suite":
        return suite(args.base, args.work, args.python, args.only)
    if args.cmd == "loop-sim":
        return loop_sim(args.wf_dir, args.out)
    if args.cmd == "findspec":
        return findspec(args.wf_dir, args.out)
    return 2


if __name__ == "__main__":
    sys.exit(main())
