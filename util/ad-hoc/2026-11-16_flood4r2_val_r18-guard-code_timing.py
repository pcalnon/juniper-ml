"""
Time agent guard copies AS THE HOOK (python3 -I <copy>, payload on stdin) on adversarial command shapes, to compare
main 1.3.0, 1.4.0 and mutants against the installed entry's 10 s timeout (validator JL1, code lens, item 4).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_probe.py

Usage: python3 <this file> <scratch dir> <out.json> [--shapes a,b] [--guard NAME=PATH ...] [--interpreter PATH]
The guard only reads a payload; nothing is executed by bash here. The shapes are text.
"""

import argparse
import json
import subprocess  # nosec B404 -- runs guard copies on payloads
import sys
import time
from pathlib import Path

PER_RUN = 60  # seconds per guard run; the installed entry times out at 10


def nest_diverge(depth: int) -> str:
    """Nested $( ) whose body holds a ) inside a comment: bash's parser and a parenthesis count end it differently,
    so the two readings of each level nest different texts, each with its own cd targets."""
    inner = ": leaf"
    for d in range(depth, 0, -1):
        inner = "cd a%d; : $(%s) # )\ncd b%d" % (d, inner, d)
    return "echo $(%s)" % inner


def nest_case(depth: int) -> str:
    """The same with a case pattern's ) as the divergence."""
    inner = ": leaf"
    for d in range(depth, 0, -1):
        inner = "cd a%d; case x in a) : $(%s) ;; esac; cd b%d" % (d, inner, d)
    return "echo $(%s)" % inner


def nest_plain(depth: int) -> str:
    inner = ": leaf"
    for _ in range(depth):
        inner = "echo $(%s)" % inner
    return inner


SHAPES = {
    "nest-diverge-2": lambda: nest_diverge(2),
    "nest-diverge-3": lambda: nest_diverge(3),
    "nest-diverge-4": lambda: nest_diverge(4),
    "nest-diverge-5": lambda: nest_diverge(5),
    "nest-diverge-4-cred": lambda: nest_diverge(4) + "; cat ~/.ssh/config",
    "cd-chain-12": lambda: "; ".join("cd d%d" % i for i in range(12)) + "; ls x",
    "cd-chain-16": lambda: "; ".join("cd d%d" % i for i in range(16)) + "; ls x",
    "nest-diverge-6": lambda: nest_diverge(6),
    "nest-diverge-7": lambda: nest_diverge(7),
    "nest-diverge-8": lambda: nest_diverge(8),
    "nest-case-6": lambda: nest_case(6),
    "nest-case-8": lambda: nest_case(8),
    "nest-diverge-10": lambda: nest_diverge(10),
    "nest-diverge-12": lambda: nest_diverge(12),
    "nest-case-12": lambda: nest_case(12),
    "nest-plain-12": lambda: nest_plain(12),
    "cd200-rel200": lambda: "; ".join("cd d%d" % i for i in range(200)) + "; cat " + " ".join("f%d/x" % i for i in range(200)),
    "cd200-tplus200": lambda: "; ".join("cd d%d" % i for i in range(200)) + "; cat " + " ".join("~+/f%d/x" % i for i in range(200)),
    "cd200-tminus200": lambda: "; ".join("cd d%d" % i for i in range(200)) + "; cat " + " ".join("~-/f%d/x" % i for i in range(200)),
    "brace64x24k": lambda: "echo {%s}%s" % (",".join("a%d" % i for i in range(64)), "y" * 24000),
    "brace64x30k": lambda: "echo {%s}%s" % (",".join("a%d" % i for i in range(64)), "y" * 30000),
    "brace64-words-500": lambda: "echo " + " ".join("{%s}w%d" % (",".join("a%d" % i for i in range(64)), k) for k in range(500)),
    "brace64-words-2000": lambda: "echo " + " ".join("{%s}w%d" % (",".join("a%d" % i for i in range(64)), k) for k in range(2000)),
    "quoted-brace-2000": lambda: "echo " + " ".join("'{%s}'" % ",".join("a%d" % i for i in range(70)) for _ in range(2000)),
    "comsub-unclosed-3000": lambda: "echo " + "$(" * 3000,
    "comsub-deep-closed-400": lambda: "echo " + "$(" * 400 + ":" + ")" * 400,
    "param-unclosed-3000": lambda: "echo " + "${x:-" * 3000,
    "dq-comsub-3000": lambda: "echo " + '"$(' * 3000,
    "heredoc-in-comsub-500": lambda: "echo $(" + "".join(": <<E%d\n)\nE%d\n" % (i, i) for i in range(500)) + ")",
    "case-in-comsub-2000": lambda: "echo $(" + " ".join("case x in a) : ;; esac;" for _ in range(2000)) + ")",
    "extglob-5000": lambda: "cat " + " ".join("~/.s@(s)h%d/config" % i for i in range(5000)),
    "splice-words-5000": lambda: "cat " + " ".join("~/X/../.ss$(:)h%d/c" % i for i in range(5000)),
    "long-word-200k": lambda: "echo " + "a" * 200000,
}


def run(guard: str, command: str, home: str, interpreter: str) -> tuple:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": home}).encode()
    env = {"PATH": "/usr/bin:/bin", "HOME": home, "JUNIPER_GUARD_HOME": home, "LANG": "C.UTF-8"}
    t0 = time.perf_counter()
    try:
        proc = subprocess.run([interpreter, "-I", guard], input=payload, env=env, capture_output=True, timeout=PER_RUN, check=False)  # nosec B603 -- a guard copy on a payload
    except subprocess.TimeoutExpired:
        return float(PER_RUN), "TIMEOUT>%ds" % PER_RUN
    took = time.perf_counter() - t0
    if proc.returncode == 2:
        verdict = "REFUSE: " + proc.stderr.decode("utf-8", "replace").strip()[-90:]
    elif proc.returncode != 0:
        verdict = "ERROR rc=%d" % proc.returncode
    else:
        verdict = "DENY" if proc.stdout.strip() else "PASS"
    return took, verdict


def main(argv: list) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scratch")
    parser.add_argument("out")
    parser.add_argument("--shapes", default="")
    parser.add_argument("--guard", action="append", default=[])
    parser.add_argument("--interpreter", default=sys.executable)
    args = parser.parse_args(argv)
    scratch = Path(args.scratch).resolve()
    home = str(scratch / "scratch_home")
    guards = dict(g.split("=", 1) for g in args.guard) or {"main": str(scratch / "work" / "guard_main.py"), "new": str(scratch / "work" / "guard_new.py")}
    names = [s for s in args.shapes.split(",") if s] or list(SHAPES)
    rows = []
    for name in names:
        command = SHAPES[name]()
        row = {"shape": name, "bytes": len(command)}
        for gname, path in guards.items():
            took, verdict = run(path, command, home, args.interpreter)
            row[gname] = {"seconds": round(took, 3), "verdict": verdict}
        rows.append(row)
        print("%-24s %7d B  %s" % (name, len(command), "  ".join("%s=%.2fs %s" % (g, row[g]["seconds"], row[g]["verdict"][:60]) for g in guards)), flush=True)
        Path(args.out).write_text(json.dumps({"interpreter": args.interpreter, "per_run_timeout": PER_RUN, "rows": rows}, indent=1))
    Path(args.out).write_text(json.dumps({"interpreter": args.interpreter, "rows": rows}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
