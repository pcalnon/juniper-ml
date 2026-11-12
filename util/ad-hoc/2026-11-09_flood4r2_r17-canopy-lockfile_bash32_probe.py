"""
Run the ruling-17 fix's new shell constructs, extracted verbatim from the step, under bash 3.2.57 and the local bash.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4, owner ruling 17 ("canopy: dead error path"); juniper-canopy lockfile-update.yml

juniper-canopy's regression test runs the commit step's own ``run:`` block with ``bash``
on CI's required macOS leg, whose image (macos-26-arm64 20261102.0473.1) ships Bash
3.2.57. This takes, verbatim from the step, the ``redact`` function (its printf format
bracketed so an empty result is visible; the substitution itself untouched), the gh capture
line (with ``gh`` replaced by a fixed stand-in command) and the 401-hint test, and runs them in
the official ``bash:3.2.57`` image (``--network none``, the probe mounted read-only) and
under the local bash, comparing each output with the expected text.

Usage::

    python3 util/ad-hoc/2026-11-09_flood4r2_r17-canopy-lockfile_bash32_probe.py \
        --workflow <canopy worktree>/.github/workflows/lockfile-update.yml --out <dir under a repository's tmp/>

Writes ``<out>/probe.sh`` and ``<out>/bash32_probe.json``. Exit 0 when both shells print the expected text.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - runs bash locally and in a pinned container
import sys
from pathlib import Path

import yaml

STEP_NAME = "Commit updated lockfile (GitHub-signed, via API)"
IMAGE = "bash:3.2.57"
STAND_IN = "sh -c 'echo body; echo \"gh: Bad credentials (HTTP 401)\" >&2; exit 1'"

EXPECTED = "\n".join(
    [
        "[gh: token *** lacks access]",
        "[a *** b tok]",
        "[a b]",
        "[c d]",
        "[1][gh: Bad credentials (HTTP 401)]",
        "401-hint: yes",
        "401-hint: no",
        "[0][]",
        "",
    ]
)


def extract(workflow: Path) -> tuple[str, str, str]:
    with workflow.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    step = [s for s in doc["jobs"]["update-lockfile"]["steps"] if s.get("name") == STEP_NAME][0]
    lines = step["run"].splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "redact() {")
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == "}")
    function = "\n".join(line.strip() for line in lines[start : end + 1])
    capture = next(line.strip() for line in lines if line.strip().startswith("GH_STDERR=$({ gh api graphql"))
    hint = next(line.strip() for line in lines if "(HTTP 401)" in line and line.strip().startswith("if [["))
    return function, capture, hint


def build(function: str, capture: str, hint: str) -> str:
    gh_part = capture[capture.index("gh api graphql") : capture.index(";")]
    failing_capture = capture.replace(gh_part, STAND_IN + " > /dev/null")
    passing_capture = capture.replace(gh_part, "true")
    return "\n".join(
        [
            "set -euo pipefail",
            function.replace("printf '%s\\n' ", "printf '[%s]\\n' "),
            "GH_TOKEN='lockfile-regen-token-not-real'",
            'redact "gh: token lockfile-regen-token-not-real lacks access"',
            "GH_TOKEN='t*k?[x]'",
            'redact "a t*k?[x] b tok"',
            "GH_TOKEN=''",
            'redact "a b"',
            "unset GH_TOKEN",
            'redact "c d"',
            "GH_STATUS=0",
            failing_capture,
            'printf \'[%s][%s]\\n\' "${GH_STATUS}" "${GH_STDERR}"',
            hint,
            '  echo "401-hint: yes"',
            "else",
            '  echo "401-hint: no"',
            "fi",
            "GH_STDERR='gh: HTTP 502'",
            hint,
            '  echo "401-hint: yes"',
            "else",
            '  echo "401-hint: no"',
            "fi",
            "GH_STATUS=0",
            passing_capture,
            'printf \'[%s][%s]\\n\' "${GH_STATUS}" "${GH_STDERR}"',
            "",
        ]
    )


def run(command: list[str]) -> dict:
    proc = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)  # nosec B603 - fixed argv
    return {"command": command, "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "as_expected": proc.returncode == 0 and proc.stdout == EXPECTED}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    function, capture, hint = extract(args.workflow)
    probe = out / "probe.sh"
    probe.write_text(build(function, capture, hint), encoding="utf-8")
    digest = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{index .RepoDigests 0}}"], capture_output=True, text=True, check=False).stdout.strip()  # nosec B603 B607
    results = {
        "image": IMAGE,
        "image_digest": digest,
        "extracted": {"function": function, "capture": capture, "hint": hint},
        "bash_3_2_57": run(["docker", "run", "--rm", "--network", "none", "-v", f"{out}:/probe:ro", IMAGE, "bash", "/probe/probe.sh"]),
        "bash_3_2_57_version": run(["docker", "run", "--rm", "--network", "none", IMAGE, "bash", "--version"])["stdout"].splitlines()[:1],
        "local_bash": run(["bash", str(probe)]),
        "local_bash_version": run(["bash", "--version"])["stdout"].splitlines()[:1],
        "expected_stdout": EXPECTED,
    }
    (out / "bash32_probe.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for key in ("bash_3_2_57", "local_bash"):
        print(f"{key}: exit={results[key]['exit']} as_expected={results[key]['as_expected']}")
        print(results[key]["stdout"], end="")
        if results[key]["stderr"]:
            print(f"stderr: {results[key]['stderr']!r}")
    print(f"versions: {results['bash_3_2_57_version']} / {results['local_bash_version']}; image {digest}")
    return 0 if results["bash_3_2_57"]["as_expected"] and results["local_bash"]["as_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
