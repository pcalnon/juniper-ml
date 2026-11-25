#!/usr/bin/env python3
"""Re-prove one fixed ruling-26 port with BOTH session-11 harnesses, in a fresh clone (flood-4 session 12).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the fix pass before ruling 26's six PRs land; tmp/flood4/session12/r26/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_flood4_s11_v26_code_proof.py (the code lens's harness: fixed, main, mutants V01-V15,
    CI collection) and util/ad-hoc/2026-11-24_flood4_s11_r26_proof.py (the builder's: fixed, main, canopy#814's M1-M5);
    util/ad-hoc/2026-11-24_flood4_s12_r26_fixpass.py (builds the sets)

For --repo, in order:
  1. the expected-new set: the test names that failed on main in the code lens's session-11 run
     (--s11/val_code/<repo>/proof/summary.json), which the fix pass did not rename;
  2. the code lens's harness, in full, on --clones/<repo> (a fresh clone of main at the set's base): it installs the
     set (sha256-checked), saves main's copies first, runs fixed, main, V01-V15 and the CI collection; after the fix
     pass only V13 (cosmetic) may survive, so V14/V15 (C1's) must now be killed;
  3. the builder's harness on the same clone (the set stays installed), with main's workflow from step 2's saved copy.
pytest runs with SENTRY_SDK_DSN and JUNIPER_CASCOR_LOG_DIR removed from the environment, as both lenses ran it.
Writes <out>/{code,builder}/ and <out>/REPROVE.txt. Exit 0 when both harnesses exit 0.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r26_reprove.py --repo NAME --s11 DIR --sets DIR --clones DIR --out DIR \
        --python PY --not-committed WORDS --ci-args "ARGS" --pytest-args "ARGS" [--builder-only]
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess  # nosec B404 -- runs the two session-11 harnesses with fixed argv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_PROOF = HERE / "2026-11-24_flood4_s11_v26_code_proof.py"
BUILDER_PROOF = HERE / "2026-11-24_flood4_s11_r26_proof.py"
WORKFLOW = ".github/workflows/lockfile-update.yml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--repo", "--python", "--not-committed", "--ci-args", "--pytest-args"):
        parser.add_argument(name, required=True)
    for name in ("--s11", "--sets", "--clones", "--out"):
        parser.add_argument(name, type=Path, required=True)
    parser.add_argument("--builder-only", action="store_true", help="skip the code lens's harness (its passed run in --out/code is kept)")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    s11_summary = json.loads((args.s11 / "val_code" / args.repo / "proof" / "summary.json").read_text(encoding="utf-8"))
    main_run = next(run for run in s11_summary["runs"] if run["label"] == "main")
    expect_new = sorted(node.rsplit("::", 1)[-1] for node in main_run["failed"])
    pytest_args = shlex.split(args.pytest_args)
    env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR")}
    clone = (args.clones / args.repo).resolve()
    sets = (args.sets / args.repo).resolve()

    code_argv = [sys.executable, str(CODE_PROOF), "--clone", str(clone), "--final", str(sets / "final"), "--paths", str(sets / "paths.txt"),
                 "--sha256", str(sets / "final.sha256"), "--workflow", WORKFLOW, "--out", str(out / "code"), "--python", args.python,
                 "--not-committed", args.not_committed, "--expect-new", *expect_new, "--ci-args", args.ci_args, "--", *pytest_args]
    if args.builder_only:
        # The code lens's run already passed in this --out (its summary is kept); only the builder's harness runs again.
        code = subprocess.CompletedProcess(code_argv, 0, (out / "code" / "summary.txt").read_text(encoding="utf-8"), "")
    else:
        code = subprocess.run(code_argv, env=env, capture_output=True, text=True, check=False)  # nosec B603
        (out / "code_stdout.txt").write_text(f"$ {shlex.join(code_argv)}\nexit {code.returncode}\n\n{code.stdout}\n--- stderr ---\n{code.stderr}", encoding="utf-8")

    builder_rc = None
    builder = None
    main_copy = out / "code" / "main_copy" / WORKFLOW
    if main_copy.is_file():
        # The builder's harness takes --expect-new once per name (action="append"), unlike the code lens's (nargs="+").
        builder_argv = [sys.executable, str(BUILDER_PROOF), "--clone", str(clone), "--workflow", WORKFLOW, "--main-copy", str(main_copy),
                        "--out", str(out / "builder"), "--python", args.python, *[f"--expect-new={name}" for name in expect_new], "--", *pytest_args]
        builder = subprocess.run(builder_argv, env=env, capture_output=True, text=True, check=False)  # nosec B603
        builder_rc = builder.returncode
        (out / "builder_stdout.txt").write_text(f"$ {shlex.join(builder_argv)}\nexit {builder_rc}\n\n{builder.stdout}\n--- stderr ---\n{builder.stderr}", encoding="utf-8")

    lines = [f"repo {args.repo}; expected-new ({len(expect_new)}): {expect_new}",
             f"code lens harness exit {code.returncode}", code.stdout.strip()[-6000:],
             f"builder harness exit {builder_rc}", (builder.stdout.strip()[-4000:] if builder else "(not run: no main copy)")]
    (out / "REPROVE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if code.returncode == 0 and builder_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
