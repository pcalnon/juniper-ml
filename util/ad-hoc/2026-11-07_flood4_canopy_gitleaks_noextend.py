#!/usr/bin/env python3
"""
Show what gitleaks does with canopy's .gitleaks.toml as-is, without its [extend] table, and with neither [extend] nor [[rules]].

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy#790 (validator finding D-F1: "an omitted [extend] leaves nothing to fire")

Usage: 2026-11-07_flood4_canopy_gitleaks_noextend.py <gitleaks binary> <.gitleaks.toml>

The config is passed in GITLEAKS_CONFIG_TOML (no config file is written). The scan target is a
TemporaryDirectory under TMPDIR holding one file with a PAT-shaped string assembled at run time
(not a credential), so "rules fire" is observable. Prints the exit code and the log's first
config/leak lines for each variant.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def variants(text: str) -> dict:
    no_extend = re.sub(r"(?m)^\[extend\]\n(?:useDefault = true\n)?", "", text)
    code = re.sub(r"(?m)^\s*#.*$", "", no_extend)
    assert "[extend]" not in code and "useDefault" not in code
    head, sep, _tail = no_extend.partition("[[rules]]")
    assert sep, "no [[rules]] entry"
    return {"as-is": text, "no-extend": no_extend, "no-extend-no-rules": head}


def main(argv: list[str]) -> int:
    binary, cfg = argv[1], Path(argv[2])
    version = subprocess.run([binary, "version"], capture_output=True, text=True, check=False).stdout.strip()
    print(f"gitleaks {version}")
    with tempfile.TemporaryDirectory(prefix="flood4-gitleaks-") as tdir:
        target = Path(tdir) / "scan"
        target.mkdir()
        token = "ghp_" + "Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7bC0eF3hJ6"  # assembled at run time; not a credential
        (target / "sample.txt").write_text(f"token = {token}\n", encoding="utf-8")
        for name, body in variants(cfg.read_text(encoding="utf-8")).items():
            env = dict(os.environ)
            env["GITLEAKS_CONFIG_TOML"] = body
            proc = subprocess.run([binary, "dir", "--no-banner", "--redact", "--exit-code", "2", str(target)], env=env, capture_output=True, text=True, check=False)
            lines = [ln for ln in (proc.stdout + proc.stderr).splitlines() if re.search(r"Failed|error|leaks found|no leaks|RuleID|rules", ln, re.I)]
            print(f"--- {name}: exit={proc.returncode}")
            for ln in lines[:6]:
                print("    " + ln[:220])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
