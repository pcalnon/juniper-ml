#!/usr/bin/env python3
"""Run the ruling-26 fix's bash-specific lines under Bash 3.2.57 (macOS legs) and local bash, and compare (V26 CODE lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (validation of the ruling-26 lockfile-print ports; tmp/flood4/session11/r26/val_code/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session11/briefs/V26_ports_validator.txt (CODE lens); juniper-canopy#814 (its Bash 3.2 check of the
    same lines, under the same local `bash:3.2.57` image)

The bash:3.2.57 image has no git or jq, so, as canopy#814 did, only the lines whose meaning could differ across bash
versions are run: `GH_STATUS=0`, the capture line, `redact()`, the stderr print, and the `(HTTP 401)` match. They are
taken VERBATIM from each frozen workflow (no retyping), the runner temp prefix (--runner-tmp) rewritten into the
mounted work directory. A stub `gh` on PATH prints a body, then a message on stderr, then exits with a given status.
Each scenario runs under the local bash and under `docker run --rm --network none -v WORK:/work bash:3.2.57`; the two
outputs must be byte-identical and must never contain the token.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_code_bash32.py --runner-tmp PREFIX --out DIR NAME=WORKFLOW [...]
Exit 0 when every scenario matches across the two bashes and no output holds the token; 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 -- runs bash and docker with fixed argv
import sys
from pathlib import Path

import yaml

IMAGE = "bash:3.2.57"
GH_STUB = '#!/bin/sh\nprintf \'%s\' "$GH_STDOUT"\nif [ -n "$GH_ERR" ]; then printf \'%s\\n\' "$GH_ERR" >&2; fi\nexit "$GH_RC"\n'
# name: (token, gh stdout, gh stderr, gh exit status)
SCENARIOS = {
    "401-token-twice": ("tok-plain-123", "{}", "gh: tok-plain-123 Bad credentials (tok-plain-123) (HTTP 401)", 1),
    "glob-token": ("a*b?c[d]e", "{}", "gh: a*b?c[d]e and aXbYcde must differ (HTTP 502)", 1),
    "empty-token": ("", "{}", "gh: message with *** and (HTTP 401)", 1),
    "exit-4": ("tok", "", "gh: set the GH_TOKEN environment variable", 4),
    "success": ("tok", '{"data":{}}', "", 0),
}


def _lines(workflow: Path) -> dict[str, str]:
    data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    run = next(step["run"] for job in data["jobs"].values() for step in job["steps"] if str(step.get("name", "")).startswith("Commit updated lockfile"))
    lines = run.splitlines()

    def one(needle: str) -> int:
        hits = [i for i, line in enumerate(lines) if needle in line]
        if len(hits) != 1:
            raise SystemExit(f"{workflow}: expected one line with {needle!r}, found {len(hits)}")
        return hits[0]

    init = one("GH_STATUS=0")
    capture = one("|| GH_STATUS=$?")
    redact_start = one("redact() {")
    stderr_if = one('if [ -n "${GH_STDERR}" ]; then')
    hint_if = one('*"(HTTP 401)"*')
    pick = lambda a, b: "\n".join(line.strip() for line in lines[a : b + 1])  # noqa: E731
    return {
        "init": pick(init, init),
        "capture": pick(capture, capture),
        "redact": pick(redact_start, redact_start + 2),
        "stderr": pick(stderr_if, stderr_if + 2),
        "hint": pick(hint_if, hint_if + 2),
    }


def _script(parts: dict[str, str], runner_tmp: str, work_in_shell: str) -> str:
    body = "\n".join([parts["init"], parts["capture"], parts["redact"], parts["stderr"]])
    body = body.replace(runner_tmp, f"{work_in_shell}/")
    return "\n".join(
        [
            "set -euo pipefail",
            body,
            'echo "status=${GH_STATUS}"',
            'echo "result-file=$(cat ' + f"{work_in_shell}/lockfile-commit-result.json" + ')"',
            'redact "twice: ${GH_TOKEN:-}|${GH_TOKEN:-}|end"',
            parts["hint"],
            'echo "bash=${BASH_VERSION}" >&2',
            "",
        ]
    )


def _run(cmd: list[str], env: dict[str, str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False, timeout=120)  # nosec B603
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runner-tmp", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("pairs", nargs="+", help="NAME=WORKFLOW")
    args = parser.parse_args()
    out = args.out.resolve()
    ok = True
    report = []
    for pair in args.pairs:
        name, workflow = pair.split("=", 1)
        parts = _lines(Path(workflow))
        for scenario, (token, stdout, stderr, rc) in SCENARIOS.items():
            work = out / name / scenario
            if work.exists():
                shutil.rmtree(work)
            (work / "bin").mkdir(parents=True)
            (work / "bin" / "gh").write_text(GH_STUB, encoding="utf-8")
            (work / "bin" / "gh").chmod(0o700)
            results = {}
            for label in ("local", "bash32"):
                shell_work = str(work) if label == "local" else "/work"
                script = work / f"step_{label}.sh"
                script.write_text(_script(parts, args.runner_tmp, shell_work), encoding="utf-8")
                (work / "lockfile-commit-result.json").unlink(missing_ok=True)
                env_vars = {"GH_TOKEN": token, "GH_STDOUT": stdout, "GH_ERR": stderr, "GH_RC": str(rc)}
                if label == "local":
                    env = {"PATH": f"{work / 'bin'}:/usr/bin:/bin", "LANG": "C", "HOME": str(work), "TMPDIR": str(work), **env_vars}
                    results[label] = _run(["bash", str(script)], env)
                else:
                    # --user: files the container writes into the bind mount stay owned by this user, not root.
                    cmd = ["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{work}:/work", "-w", "/work", "-e", "PATH=/work/bin:/usr/local/bin:/usr/bin:/bin", "-e", "TMPDIR=/work"]
                    for key, value in env_vars.items():
                        cmd += ["-e", f"{key}={value}"]
                    cmd += [IMAGE, "bash", "/work/step_bash32.sh"]
                    results[label] = _run(cmd, dict(os.environ))
            lc, lo, le = results["local"]
            bc, bo, be = results["bash32"]
            strip_ver = lambda s: "\n".join(line for line in s.splitlines() if not line.startswith("bash="))  # noqa: E731
            same = (lc, lo.replace(str(work), "/work"), strip_ver(le)) == (bc, bo, strip_ver(be))
            leaked = bool(token) and (token in lo + le + bo + be)
            versions = [line for line in (le + be).splitlines() if line.startswith("bash=")]
            report.append(f"[{name} / {scenario}] local exit {lc} | bash3.2 exit {bc} | {'IDENTICAL' if same else 'DIFFERENT'}{' TOKEN-LEAK' if leaked else ''} {versions}")
            report.append(f"    stdout={bo!r}")
            report.append(f"    stderr={strip_ver(be)!r}")
            if not same:
                report.append(f"    local stdout={lo!r} stderr={strip_ver(le)!r}")
            ok &= same and not leaked
    text = "\n".join(report) + f"\nRESULT: {'OK' if ok else 'CHECK'}\n"
    (out / "bash32_report.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
