#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Run gitleaks the way gitleaks-action e0c47f4f does, on three variants of a
.gitleaks.toml, with the config AUTO-DISCOVERED at the source root (no
--config, GITLEAKS_CONFIG / GITLEAKS_CONFIG_TOML removed from the env).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#802 docs carrier, validation round 2, correction D-F1 (findings: tmp/flood4/canopy/val-round2/)

Variants: as-is; [extend] table removed; [extend] AND the [[rules]] entry
removed. Each runs in git mode (a scratch repo with one commit, as CI's
`detect` scans history) and in --no-git mode. The scanned file holds a
GitHub-PAT-shaped value fabricated at runtime; it is deleted afterwards.

Usage: python3 <this> <gitleaks binary> <.gitleaks.toml> <scratch dir>
"""
import json
import os
import pathlib
import re
import secrets
import shutil
import string
import subprocess
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def variants(text: str) -> dict:
    no_extend = re.sub(r"^\[extend\]\nuseDefault = true\n", "", text, flags=re.M)
    assert no_extend != text, "[extend] block not found"
    m = re.search(r"^\[\[rules\]\]$", no_extend, flags=re.M)
    assert m, "[[rules]] table header not found"
    # drop the [[rules]] entry and everything after it (its allowlist is the file's tail)
    no_rules = no_extend[: m.start()]
    assert not re.search(r"^\[\[rules\]\]$|^\[extend\]$", no_rules, flags=re.M)
    return {"as_is": text, "no_extend": no_extend, "no_extend_no_rules": no_rules}


def run(binary: str, src: pathlib.Path, report: pathlib.Path, git_mode: bool, env: dict) -> dict:
    args = [binary, "detect", "--redact", "-v", "--exit-code=2", "--report-format=sarif", f"--report-path={report}", "--log-level=debug"]
    if not git_mode:
        args.append("--no-git")
    p = subprocess.run(args, cwd=src, capture_output=True, text=True, env=env)
    out = ANSI.sub("", p.stdout + p.stderr)
    keep = [ln for ln in out.splitlines() if re.search(r"config|FTL|leaks found|no leaks|RuleID|rule|ERR|WRN", ln, re.I)]
    rules = []
    if report.exists():
        try:
            sarif = json.loads(report.read_text())
            rules = sorted({r.get("ruleId") for run_ in sarif.get("runs", []) for r in run_.get("results", [])})
            n_driver_rules = len(sarif["runs"][0]["tool"]["driver"].get("rules", []))
        except Exception as exc:  # noqa: BLE001
            n_driver_rules = f"unreadable: {exc}"
    else:
        n_driver_rules = "no report written"
    return {"exit": p.returncode, "fired": rules, "sarif_driver_rule_count": n_driver_rules, "log": keep[:12]}


def main() -> int:
    binary, cfg_path, scratch = sys.argv[1:4]
    base = pathlib.Path(scratch) / "gitleaks_variants"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITLEAKS_")}
    env["TMPDIR"] = str(base)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CEILING_DIRECTORIES"] = str(base)
    alnum = string.ascii_letters + string.digits
    fake = "ghp_" + "".join(secrets.choice(alnum) for _ in range(36))
    results = {"binary_version": subprocess.run([binary, "version"], capture_output=True, text=True).stdout.strip()}
    text = pathlib.Path(cfg_path).read_text()
    for name, body in variants(text).items():
        src = base / name
        src.mkdir()
        (src / ".gitleaks.toml").write_text(body)
        (src / "settings.py").write_text(f'GITHUB_TOKEN = "{fake}"\n')
        g = lambda *a: subprocess.run(["git", *a], cwd=src, capture_output=True, text=True, env=env, check=True)  # noqa: E731
        g("init", "-q", "-b", "main")
        g("-c", "user.name=v", "-c", "user.email=v@example.invalid", "-c", "commit.gpgsign=false", "add", "-A")
        g("-c", "user.name=v", "-c", "user.email=v@example.invalid", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "probe")
        results[name] = {
            "git_mode": run(binary, src, base / f"{name}_git.sarif", True, env),
            "no_git_mode": run(binary, src, base / f"{name}_nogit.sarif", False, env),
        }
        (src / "settings.py").unlink()  # do not leave the fabricated value on disk
        shutil.rmtree(src / ".git")
    out = pathlib.Path(scratch) / "gitleaks_variants.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
