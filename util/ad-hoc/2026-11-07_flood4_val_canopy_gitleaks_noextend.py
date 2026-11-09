#!/usr/bin/env python3
"""
Measure what gitleaks 8.24.3 does with juniper-canopy's .gitleaks.toml when the `[extend]` table is removed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy DOCS carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#790 (docs claim: "an omitted [extend] table leaves the step with nothing to fire ... exits 0")

The carrier's CI/CD docs claim that removing `[extend] useDefault = true` from the CURRENT .gitleaks.toml
leaves the Gitleaks step with nothing to fire, so it exits 0. gitleaks 8.24.3 validates every rule after
extension (config/config.go Translate, extendDepth == 0 -> Rule.Validate), and the file's only [[rules]]
entry has neither `regex` nor `path`. This script runs the real 8.24.3 binary on a fabricated GitHub-PAT-shaped
value (assembled at runtime, never a credential) under two configs, passed through GITLEAKS_CONFIG_TOML so no
.toml file is written anywhere:
  as-is      -- the file exactly as on main
  no-extend  -- the same text with the `[extend]` table's two lines removed
It records each run's exit code and the tail of stderr. --exit-code=2 mirrors gitleaks-action (leaks -> 2).

    python3 2026-11-07_flood4_val_canopy_gitleaks_noextend.py <gitleaks binary> <canopy .gitleaks.toml> <out dir>
"""

from __future__ import annotations

import json
import os
import string
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

_ALPHABET = string.ascii_letters + string.digits


def _fabricated_github_pat() -> str:
    """Same deterministic walk the canopy regression test uses; GitHub-PAT-shaped, never a credential."""
    return "gh" + "p_" + "".join(_ALPHABET[(11 + i * 29) % len(_ALPHABET)] for i in range(36))


def main() -> int:
    binary, config_path, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    text = config_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    no_extend = "".join(line for line in lines if line.strip() not in ("[extend]", "useDefault = true"))
    live = [line.strip() for line in no_extend.splitlines() if line.strip() and not line.strip().startswith("#")]
    assert "[extend]" not in live and not any(line.startswith("useDefault") for line in live), live
    assert len(lines) - len(no_extend.splitlines(keepends=True)) == 2, "expected to remove exactly the two [extend] lines"
    scan = out_dir / "gitleaks_noextend_scan"
    scan.mkdir(parents=True, exist_ok=True)
    sample = scan / "sample.txt"
    sample.write_text("GITHUB_TOKEN=" + _fabricated_github_pat() + "\n", encoding="utf-8")
    results = {}
    try:
        for name, body in (("as-is", text), ("no-extend", no_extend)):
            report = out_dir / f"gitleaks_noextend_report_{name}.json"
            env = {k: v for k, v in os.environ.items() if k not in ("GITLEAKS_CONFIG",)}
            env["GITLEAKS_CONFIG_TOML"] = body
            argv = [binary, "dir", "--redact", "--no-banner", "--no-color", "--exit-code=2", "--report-format=json", f"--report-path={report}", str(scan)]
            res = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False, env=env)  # nosec B603
            findings = None
            if report.exists():
                try:
                    findings = sorted({f["RuleID"] for f in json.loads(report.read_text(encoding="utf-8"))})
                except (ValueError, KeyError):
                    findings = "unparseable"
            results[name] = {"exit": res.returncode, "rules_fired": findings, "stderr_tail": res.stderr[-600:]}
    finally:
        sample.unlink(missing_ok=True)
        scan.rmdir()
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
