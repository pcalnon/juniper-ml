#!/usr/bin/env python3
"""
Run publish.yml's `Verify TestPyPI install` step under each command GitHub uses for a named or unnamed shell.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier, round-2 validation)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#516 (test_testpypi_install_verify.py:125); round-1 finding T-F1

The carried test asserts the step names no `shell:` with the message "a named shell drops GitHub's
bash -e, and a failing pip would not fail the step". GitHub's workflow-syntax shell table gives:
unspecified -> `bash -e {0}`; `shell: bash` -> `bash --noprofile --norc -eo pipefail {0}`;
`shell: sh` -> `sh -e {0}`; a custom template such as `shell: bash {0}` runs exactly what it names.
This probe runs the step's own `run:` block (read from the carrier, never modified) under each of
those with a stub `pip` that exits 1, and reports whether the step fails before `python` runs.

    python3 2026-11-07_flood4_val_data_named_shell_probe.py <juniper-data tree> <scratch dir>

Writes only under <scratch dir>. Exit 0 always; the report is the result.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - runs a workflow step's shell with fixed argv
import sys
from pathlib import Path

import yaml

SHELLS = {
    "unspecified (bash -e {0})": ["bash", "-e"],
    "shell: bash (bash --noprofile --norc -eo pipefail {0})": ["bash", "--noprofile", "--norc", "-eo", "pipefail"],
    "shell: sh (sh -e {0})": ["sh", "-e"],
    "custom shell: bash {0} (no -e)": ["bash"],
}


def main() -> int:
    tree = Path(sys.argv[1]).resolve()
    scratch = Path(sys.argv[2]).resolve()
    doc = yaml.safe_load((tree / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8"))
    step = next(s for s in doc["jobs"]["testpypi"]["steps"] if s.get("name") == "Verify TestPyPI install")
    script = str(step["run"]).replace("${{ github.event.release.tag_name }}", "v0.17.1")
    results = {}
    for label, argv in SHELLS.items():
        work = scratch / "named_shell_probe" / label.split(" ")[0].replace(":", "")
        if label.startswith("shell: sh"):
            work = scratch / "named_shell_probe" / "sh"
        elif label.startswith("custom"):
            work = scratch / "named_shell_probe" / "custom"
        elif label.startswith("shell: bash"):
            work = scratch / "named_shell_probe" / "bash"
        bindir = work / "bin"
        bindir.mkdir(parents=True, exist_ok=True)
        trace = work / "trace.txt"
        if trace.exists():
            trace.unlink()
        (bindir / "sleep").write_text('#!/bin/sh\nprintf "sleep %s\\n" "$*" >> "$TRACE"\nexit 0\n', encoding="utf-8")
        (bindir / "pip").write_text('#!/bin/sh\nprintf "pip\\n" >> "$TRACE"\nexit 1\n', encoding="utf-8")
        (bindir / "python").write_text('#!/bin/sh\nprintf "python\\n" >> "$TRACE"\nexit 0\n', encoding="utf-8")
        for name in ("sleep", "pip", "python"):
            (bindir / name).chmod(0o755)
        script_file = work / "step.sh"
        script_file.write_text(script, encoding="utf-8")
        env = {"PATH": f"{bindir}{os.pathsep}/usr/bin:/bin", "HOME": str(work), "LANG": "C", "TRACE": str(trace)}
        proc = subprocess.run(argv + [str(script_file)], env=env, capture_output=True, text=True, check=False, timeout=30)  # nosec B603
        steps = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
        results[label] = {"argv": argv + ["<step file>"], "exit": proc.returncode, "trace": steps, "failing_pip_fails_step": proc.returncode != 0 and "python" not in steps}
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
