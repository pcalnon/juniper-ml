#!/usr/bin/env python3
"""Two gitleaks probes for B9: is the repository config's ruleset non-empty, and what does a scope-exact scan find?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc -- investigation (backup recovery B9 / design P0.5a item 6)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md section 6.2 row B9;
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md P0.5a item 6 and AC-8a;
         util/ad-hoc/2026-10-10_gitleaks_finding_inspect.py (classifies what `scan` reports)

WHY THIS EXISTS

`vacuity` answers "does the ruleset this config loads catch ANYTHING?". In gitleaks v8 a config file without
`[extend] useDefault = true` loads only its own `[[rules]]`; `.gitleaks.toml` had none from 2026-08-13 to B9, so
CI's Security Scan ran with zero rules and passed every time. A scan that cannot fire is not a clean scan. The probe
writes a FABRICATED GitHub-token-shaped value (deterministic, never printed) into three temporary directories and
scans each with `gitleaks dir`:

  * one holding a copy of the config as `.gitleaks.toml` (CI's auto-discovery path: gitleaks-action passes no --config);
  * one scanned with an explicit `--config`;
  * one holding nothing (gitleaks' built-in default, the control).

The control must fire, or the probe itself is broken.

`scan` runs `gitleaks detect --redact` over a named scope and writes a JSON report for the inspector:

  * `main`        -- `--full-history origin/main`: the published default branch;
  * `ci-dispatch` -- every branch head and tag on the remote, exactly: what gitleaks-action scans on a
                     `workflow_dispatch` (or `schedule`) run, where it passes no --log-opts and a fetch-depth-0
                     checkout holds every remote branch. Every SHA must already be present locally (no fetch);
                     the probe refuses otherwise rather than scanning a smaller set than it names;
  * `worktree`    -- `gitleaks dir` over the working tree.

It never prints a value: gitleaks runs with --redact, and the report is summarised by the inspector.

Usage:
    python3 util/ad-hoc/2026-10-10_gitleaks_probe.py vacuity --gitleaks BIN [--config .gitleaks.toml]
    python3 util/ad-hoc/2026-10-10_gitleaks_probe.py scan --gitleaks BIN --scope ci-dispatch --report R.json [--config C]

Exit codes: vacuity -- 0 the config's ruleset fired, 1 it did not (vacuous), 2 the control did not fire (probe broken);
scan -- gitleaks' own exit code (0 clean, 2 findings), or 3 when the scope could not be resolved exactly.
"""

from __future__ import annotations

import argparse
import shutil
import string
import subprocess  # nosec B404 -- fixed argv lists, never a shell
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def fabricated_sample() -> str:
    """A GitHub-PAT-SHAPED value: a fixed-step walk over the alphabet, so it is high-variety but deterministic.

    It is not a credential. It is assembled here so that no file carries one, and it needs no randomness.
    """
    alphabet = string.ascii_letters + string.digits
    return "gh" + "p_" + "".join(alphabet[(11 + i * 29) % len(alphabet)] for i in range(36))


def run_dir_scan(gitleaks: str, target: Path, config: Path | None) -> int:
    argv = [gitleaks, "dir", "--redact", "--no-banner", "--no-color", "--exit-code=2", str(target)]
    if config is not None:
        argv[2:2] = ["--config", str(config)]
    return subprocess.run(argv, capture_output=True, text=True, check=False).returncode  # nosec B603


def vacuity(args: argparse.Namespace) -> int:
    config = Path(args.config).resolve()
    with tempfile.TemporaryDirectory(prefix="gitleaks-vacuity-") as tmp:
        root = Path(tmp)
        line = "GITHUB_TOKEN=" + fabricated_sample() + "\n"
        for name in ("auto", "explicit", "control"):
            (root / name).mkdir()
            (root / name / "sample.txt").write_text(line, encoding="utf-8")
        shutil.copyfile(config, root / "auto" / ".gitleaks.toml")
        auto = run_dir_scan(args.gitleaks, root / "auto", None)
        explicit = run_dir_scan(args.gitleaks, root / "explicit" / "sample.txt", config)
        control = run_dir_scan(args.gitleaks, root / "control", None)
    verdict = {0: "no finding", 2: "finding"}
    print(f"config: {config}")
    print(f"  auto-discovered .gitleaks.toml (CI's path): exit {auto} -- {verdict.get(auto, 'ERROR')}")
    print(f"  explicit --config:                          exit {explicit} -- {verdict.get(explicit, 'ERROR')}")
    print(f"  control, built-in default config:           exit {control} -- {verdict.get(control, 'ERROR')}")
    if control != 2:
        print("PROBE BROKEN: the built-in default did not fire on the fabricated token")
        return 2
    if auto == 2 and explicit == 2:
        print("ACTIVE: the config's ruleset includes the default rules")
        return 0
    print("VACUOUS: the config loads a ruleset that does not include the default rules")
    return 1


def remote_shas(kind: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-remote", kind, "origin"], capture_output=True, text=True, check=True)  # nosec B603 B607
    return sorted({line.split("\t", 1)[0] for line in out.stdout.splitlines() if line.strip()})


def present(shas: list[str]) -> list[str]:
    res = subprocess.run(["git", "-C", str(REPO), "cat-file", "--batch-check"], input="\n".join(shas) + "\n", capture_output=True, text=True, check=True)  # nosec B603 B607
    return [line.split()[0] for line in res.stdout.splitlines() if line.endswith(" missing")]


def scan(args: argparse.Namespace) -> int:
    base = [args.gitleaks]
    tail = ["--redact", "--no-banner", "--no-color", "--exit-code=2", "--report-format=json", f"--report-path={args.report}"]
    source = REPO
    if args.no_ignore:
        # gitleaks reads .gitleaksignore from --source and from --gitleaks-ignore-path. Pointing --source at a
        # subdirectory keeps `git -C <source> log` on this repository's whole history while finding no ignore file
        # there, and the ignore path is an empty directory. The config is then not auto-discovered, so it is passed.
        if args.scope == "worktree":
            print("--no-ignore applies to history scopes only (a dir scan has no commit-scoped fingerprints)", file=sys.stderr)
            return 3
        source = REPO / ".github"
        args.config = args.config or str(REPO / ".gitleaks.toml")
    if args.config:
        tail += ["--config", args.config]
    for rule in args.enable_rule:
        tail += ["--enable-rule", rule]
    with tempfile.TemporaryDirectory(prefix="gitleaks-noignore-") as empty:
        if args.no_ignore:
            tail += ["--gitleaks-ignore-path", empty]
        if args.scope == "worktree":
            argv = base + ["dir"] + tail + [str(REPO)]
        else:
            if args.scope == "main":
                log_opts = "--full-history origin/main"
            else:
                shas = sorted(set(remote_shas("--heads") + remote_shas("--tags")))
                missing = present(shas)
                if missing:
                    print(f"refusing: {len(missing)} remote SHA(s) are not present locally; fetch first", file=sys.stderr)
                    return 3
                print(f"ci-dispatch scope: {len(shas)} remote head/tag SHA(s), all present locally")
                log_opts = "--full-history " + " ".join(shas)
            argv = base + ["detect", "--source", str(source), f"--log-opts={log_opts}"] + tail
        res = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603
    for line in res.stderr.splitlines() + res.stdout.splitlines():
        if " INF " in line or " WRN " in line or " ERR " in line or " FTL " in line:
            print(line)
    return res.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("vacuity", help="does the config's ruleset fire on a fabricated default-rule token?")
    v.add_argument("--gitleaks", required=True)
    v.add_argument("--config", default=str(REPO / ".gitleaks.toml"))
    s = sub.add_parser("scan", help="scope-exact redacted scan to a JSON report")
    s.add_argument("--gitleaks", required=True)
    s.add_argument("--scope", choices=("main", "ci-dispatch", "worktree"), required=True)
    s.add_argument("--report", required=True)
    s.add_argument("--config", help="config path (default: auto-discovered .gitleaks.toml at the repo root, as CI does)")
    s.add_argument("--enable-rule", action="append", default=[], help="restrict to this rule id (repeatable)")
    s.add_argument("--no-ignore", action="store_true", help="report what .gitleaksignore would hide (raw counts); history scopes only")
    args = ap.parse_args()
    return vacuity(args) if args.cmd == "vacuity" else scan(args)


if __name__ == "__main__":
    sys.exit(main())
