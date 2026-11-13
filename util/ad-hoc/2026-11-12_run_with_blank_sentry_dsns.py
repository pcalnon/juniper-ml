#!/usr/bin/env python3
"""
Run one command with the six Sentry DSN variables set to "" (the consolidated plan's H-14), in a named directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- runner used by this arc's local suite and mutation runs
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (XC-SENTRY; H-14);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md

Why
---
H-14: for every service launch and suite run, ``SENTRY_SDK_DSN``, ``SENTRY_DSN``, ``JUNIPER_CASCOR_SENTRY_DSN``,
``JUNIPER_DATA_SENTRY_DSN``, ``CANOPY_SENTRY_DSN`` and ``JUNIPER_CANOPY_SENTRY_DSN`` are set to ``""`` and never unset,
because ``load_dotenv`` re-injects an unset name while it leaves an empty one alone. This host's shell exports
``SENTRY_SDK_DSN`` non-empty, and juniper-cascor's ``src/main.py`` initialises Sentry from it at import. A suite run
that forgets the rule can therefore send test events to the live project.

Typing six assignments before every command is how the rule gets forgotten, and a worktree-isolated session's
command guard refuses several compound shapes. This runner takes the directory, the environment changes and the
command as arguments, so each run is one plain call.

What it does
------------
1. Sets the six names to ``""`` in the child's environment (any other name containing both ``SENTRY`` and ``DSN``
   is blanked too, and reported).
2. Applies every ``--unset NAME``, then every ``--set NAME=VALUE``, whatever their order on the command line. It
   refuses to unset any name that reads as a Sentry DSN, and to set one to a non-empty value, whether or not the
   name is in the environment already.
3. Prepends ``--prepend-pythonpath`` entries to ``PYTHONPATH``.
4. Runs the command in ``--cwd``. With ``--log FILE`` the child's output goes to that file and the last ``--tail``
   lines are printed; without it the output passes through.
5. Prints the names it blanked (never a value) and ``exit=<code>``, and exits with the command's code.

What it cannot do
-----------------
It sets the CHILD's environment and nothing later. A child that re-reads a shell start-up file gets whatever that file
exports: on this host ``~/.bashrc`` exports ``SENTRY_SDK_DSN``, so ``-- bash -ic '...'`` (an INTERACTIVE shell) hands
its command a live DSN again, while ``-- bash -c '...'`` does not. Run the program itself, not an interactive shell.

Usage
-----
    python3 util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py --cwd DIR [--set N=V] [--unset N]
        [--prepend-pythonpath P] [--log FILE] [--tail 25] -- CMD [ARG ...]

    python3 util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py --self-test
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404 -- runs the caller's own command, argv form, no shell
import sys
from pathlib import Path

SIX = (
    "SENTRY_SDK_DSN",
    "SENTRY_DSN",
    "JUNIPER_CASCOR_SENTRY_DSN",
    "JUNIPER_DATA_SENTRY_DSN",
    "CANOPY_SENTRY_DSN",
    "JUNIPER_CANOPY_SENTRY_DSN",
)


def is_sentry_dsn_name(name: str) -> bool:
    """One of the six, or any other name that reads as a Sentry DSN. Judged by the NAME, whether or not it is set."""
    return name in SIX or ("SENTRY" in name.upper() and "DSN" in name.upper())


def blanked_environment(base: dict[str, str], sets: list[str], unsets: list[str], prepend: list[str]) -> tuple[dict[str, str], list[str]]:
    """The child's environment, and the names blanked beyond the six."""
    env = dict(base)
    extra = sorted(name for name in env if is_sentry_dsn_name(name) and name not in SIX)
    for name in (*SIX, *extra):
        env[name] = ""
    for name in unsets:
        if is_sentry_dsn_name(name):
            raise SystemExit(f"refused: --unset {name} (H-14: a Sentry DSN name is blanked, never unset)")
        env.pop(name, None)
    for item in sets:
        name, sep, value = item.partition("=")
        if not sep or not name:
            raise SystemExit(f"--set wants NAME=VALUE, got {item!r}")
        # By the name's shape, not by membership in the current environment: a DSN-like name this shell does not
        # hold yet must be refused too, or ``--set NEW_SENTRY_DSN=<dsn>`` would hand the child a live DSN.
        if is_sentry_dsn_name(name) and value != "":
            raise SystemExit(f"refused: --set {name}=<non-empty> (H-14)")
        env[name] = value
    if prepend:
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join([*prepend, existing]) if existing else os.pathsep.join(prepend)
    return env, extra


def tail_lines(path: Path, count: int) -> list[str]:
    """The last ``count`` lines of ``path``."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        lines = handle.read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines[-count:] if count > 0 else []


def self_test() -> int:
    """Check the blanking rules on constructed environments. Exit 0 when every case holds."""
    failures: list[str] = []
    base = {"SENTRY_SDK_DSN": "https://example.invalid/1", "PATH": "/bin", "MY_SENTRY_DSN_COPY": "x", "KEEP": "1", "PYTHONPATH": "/old"}
    env, extra = blanked_environment(base, ["A=b", "EMPTY="], ["KEEP"], ["/new"])
    for name in SIX:
        if env.get(name, "missing") != "":
            failures.append(f"{name} is not set-and-empty")
    if env.get("MY_SENTRY_DSN_COPY") != "" or extra != ["MY_SENTRY_DSN_COPY"]:
        failures.append("a seventh SENTRY..DSN name was not blanked and reported")
    if "KEEP" in env or env.get("A") != "b" or env.get("EMPTY") != "":
        failures.append("--set / --unset were not applied")
    if env.get("PYTHONPATH") != os.pathsep.join(["/new", "/old"]):
        failures.append("PYTHONPATH was not prepended")
    if base["SENTRY_SDK_DSN"] == "":
        failures.append("the caller's mapping was modified")
    refused = (
        ((["SENTRY_DSN=https://example.invalid/2"], []), "--set of a DSN to a value"),
        (([], ["SENTRY_SDK_DSN"]), "--unset of a DSN"),
        # A DSN-like name the environment does NOT hold: refused by its shape, not by membership.
        ((["NOT_YET_SET_SENTRY_DSN=https://example.invalid/3"], []), "--set of an unseen DSN-like name to a value"),
        (([], ["NOT_YET_SET_SENTRY_DSN"]), "--unset of an unseen DSN-like name"),
    )
    for bad_args, label in refused:
        try:
            blanked_environment(base, bad_args[0], bad_args[1], [])
        except SystemExit:
            continue
        failures.append(f"{label} was accepted")
    # The child really sees them empty, and the exit code is the child's.
    probe = "import os, sys; sys.exit(0 if all(os.environ.get(n) == '' for n in sys.argv[1:]) else 3)"
    done = subprocess.run([sys.executable, "-c", probe, *SIX], env=blanked_environment(base, [], [], [])[0], check=False)  # nosec B603
    if done.returncode != 0:
        failures.append(f"a child did not see the six names empty (exit {done.returncode})")
    control = subprocess.run([sys.executable, "-c", probe, *SIX], env=base, check=False)  # nosec B603
    if control.returncode != 3:
        failures.append(f"the control (no blanking) did not fail as it must (exit {control.returncode})")
    for line in failures:
        print(f"FAIL  {line}")
    print(f"self-test: {'OK' if not failures else 'FAILED'} ({len(failures)} failure(s))")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cwd", help="directory to run the command in")
    parser.add_argument("--set", dest="sets", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--unset", dest="unsets", action="append", default=[], metavar="NAME")
    parser.add_argument("--prepend-pythonpath", dest="prepend", action="append", default=[], metavar="PATH")
    parser.add_argument("--log", help="write the command's output here and print only its tail")
    parser.add_argument("--tail", type=int, default=25, help="lines of --log to print (default 25)")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- CMD [ARG ...]")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not args.cwd:
        parser.error("--cwd and a command after -- are required")
    cwd = Path(args.cwd)
    if not cwd.is_dir():
        raise SystemExit(f"--cwd {cwd} is not a directory")

    env, extra = blanked_environment(dict(os.environ), args.sets, args.unsets, args.prepend)
    print(f"blanked: {', '.join(SIX)}" + (f"; also {', '.join(extra)}" if extra else ""), flush=True)

    if args.log:
        log = Path(args.log)
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w", encoding="utf-8") as handle:
            done = subprocess.run(command, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)  # nosec B603
        for line in tail_lines(log, args.tail):
            print(line)
        print(f"log: {log}")
    else:
        done = subprocess.run(command, cwd=cwd, env=env, check=False)  # nosec B603
    print(f"exit={done.returncode}", flush=True)
    return done.returncode


if __name__ == "__main__":
    raise SystemExit(main())
