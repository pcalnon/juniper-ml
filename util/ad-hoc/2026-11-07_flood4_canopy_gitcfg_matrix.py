#!/usr/bin/env python3
"""
Run canopy's AGENTS.md date-check test under several hostile global git configs, to show its fixture is hermetic.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy#794 (validator finding T-F2: color.ui=always and a refusing core.hooksPath)

Usage: 2026-11-07_flood4_canopy_gitcfg_matrix.py <tests worktree> <out dir> <label>

Each config is written to a TemporaryDirectory under TMPDIR (with a hooks dir whose hooks exit 1)
and passed as GIT_CONFIG_GLOBAL to `conda run -n JuniperCanopy1 python -m pytest` from src/.
Writes <out>/gitcfg_<label>_<config>.log and prints a summary; nothing touches a signing key
(gpg.program=false).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CONDA = "/opt/miniforge3/bin/conda"
TEST = "tests/unit/test_agents_md_date_check.py"


def counts(text: str) -> dict:
    out = {}
    for key in ("passed", "failed", "error"):
        found = re.findall(r"(\d+) " + key + r"\b", text)
        if found:
            out[key] = int(found[-1])
    return out


def main(argv: list[str]) -> int:
    wt, out, label = Path(argv[1]).resolve(), Path(argv[2]).resolve(), argv[3]
    summary = {}
    with tempfile.TemporaryDirectory(prefix="flood4-gitcfg-") as tdir:
        hooks = Path(tdir) / "hooks"
        hooks.mkdir()
        for name in ("pre-commit", "commit-msg"):
            hook = hooks / name
            hook.write_text("#!/bin/sh\necho 'refusing hook (flood-4 matrix)' >&2\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
        configs = {
            "devnull": None,
            "signing_cannot_sign": "[user]\n\tname = t\n\temail = t@t\n\tsigningkey = 0000000000000000\n[commit]\n\tgpgsign = true\n[tag]\n\tgpgsign = true\n[gpg]\n\tprogram = false\n",
            "color_ui_always": "[color]\n\tui = always\n",
            "hookspath_refusing": f"[core]\n\thooksPath = {hooks}\n",
        }
        for name, body in configs.items():
            env = dict(os.environ)
            if body is None:
                env["GIT_CONFIG_GLOBAL"] = os.devnull
            else:
                cfg = Path(tdir) / f"{name}.gitconfig"
                cfg.write_text(body, encoding="utf-8")
                env["GIT_CONFIG_GLOBAL"] = str(cfg)
            proc = subprocess.run([CONDA, "run", "-n", "JuniperCanopy1", "python", "-m", "pytest", "-p", "no:cacheprovider", TEST], cwd=wt / "src", env=env, capture_output=True, text=True, check=False)
            text = proc.stdout + proc.stderr
            log = out / f"gitcfg_{label}_{name}.log"
            log.write_text(f"# config {name}:\n{body}\n# exit={proc.returncode}\n{text}", encoding="utf-8")
            summary[name] = {"exit": proc.returncode, **counts(text), "failed_ids": re.findall(r"^FAILED (\S+)", text, re.M), "log": str(log)}
    (out / f"gitcfg_{label}_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for name, res in summary.items():
        print(f"{label} {name}: exit={res['exit']} passed={res.get('passed', 0)} failed={res.get('failed', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
