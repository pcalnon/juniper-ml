#!/usr/bin/env python3
"""
Time brace_expand and the whole hook on brace-heavy and long words, for several copies of the agent guard.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: the linear brace scan and its budget)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: validator finding ml-code-port-lens F1 (9.5 s for the hook on a 25.8 KB ``python3 -c`` word; the hook is
         installed with "timeout": 10 and "onFailure": "block"); the validator's own timing helper, whose six
         shapes and child-process design this keeps (2026-11-09_flood4r2_val_ml-code-port_timing.py).

Usage:
    python3 -I util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_timing.py <out.json> <label>=<guard.py> [<label>=<guard.py> ...]
        [--shapes=<shape>[,<shape>...]]

Three measurements per shape and guard, each in a child process with a 20 s timeout, a 2 GB address-space limit
and no bytecode written:
- ``expand``: one ``brace_expand(word)`` call, the shape grown (n = 250 ... 8000) until a guard passes 5 s;
- ``hook-echo`` and ``hook-quoted`` at n = 2000: ``run_hook`` on ``echo <word>`` and on ``python3 -c "<word>"``
  (the validator's measurement: its 25.8 KB word is ``fstring-like`` at n = 2000);
- ``process``: the hook as Claude Code runs it, ``python3 -I <guard.py>`` with the payload on stdin, wall time
  including interpreter start, for ``python3 -c "<word>"`` at n = 2000.
The home and project directories given to the guard do not exist; no real home is consulted. Prints one line per
measurement and writes them all to <out.json>.
"""
import json
import subprocess  # nosec B404 -- runs the guard copies in child processes with timeouts
import sys
import time

SHAPES = {
    "unclosed-open": lambda n: "{" * n,
    "closed-no-separator": lambda n: "{a}" * n,
    "fstring-like": lambda n: "".join("v%d={x%d};" % (k, k) for k in range(n)),
    "fstring-like-with-commas": lambda n: "".join("print(f'{x%d}', y%d);" % (k, k) for k in range(n)),
    "one-term-sequences": lambda n: "{1..1}" * n,
    "nested-unclosed": lambda n: "{a" * n + "," + "b",
    "json-like": lambda n: "{" + ",".join('"k%d":{"a":%d}' % (k, k) for k in range(n)) + "}",
    "nested-lists-60-deep-long-tail": lambda n: "{a," * 60 + "x" * (12 * n) + "}" * 60,
    "64-words-long-tail": lambda n: "{a,b}" * 6 + "x" * (12 * n),
    "64-words-then-one-term-sequences": lambda n: "{a,b}" * 6 + "{1..1}" * n,
    "plain-long-word-no-brace": lambda n: "abc.def,ghi " * n,
}

CHILD = r"""
import importlib.util, json, resource, sys, time
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
spec = importlib.util.spec_from_file_location("guard_under_test", sys.argv[1])
g = importlib.util.module_from_spec(spec)
sys.modules["guard_under_test"] = g
spec.loader.exec_module(g)
word = sys.stdin.read()
mode = sys.argv[2]
started = time.perf_counter()
if mode == "expand":
    try:
        out = "ok, %d words" % len(g.brace_expand(word))
    except g.MalformedInput as exc:
        out = "refused: " + str(exc)[:60]
else:
    command = ('python3 -c "%s"' % word) if mode == "hook-quoted" else ("echo " + word)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/"}).encode()
    code, so, se = g.run_hook(payload, homes=["/nonexistent-home"], project_dir="/nonexistent-project")
    out = "exit %d%s%s" % (code, " deny" if so else "", (" " + se.split(": ", 2)[-1][:60]) if se else "")
print(json.dumps({"seconds": round(time.perf_counter() - started, 4), "outcome": out}))
"""


def child(guard: str, word: str, mode: str) -> dict:
    started = time.time()
    try:
        proc = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, guard, mode], input=word, capture_output=True, text=True, timeout=20, check=False)  # nosec B603
    except subprocess.TimeoutExpired:
        return {"seconds": round(time.time() - started, 2), "outcome": "TIMEOUT (20 s)"}
    lines = proc.stdout.strip().splitlines()
    return json.loads(lines[-1]) if lines else {"seconds": None, "outcome": "error: " + proc.stderr[-160:]}


def process(guard: str, word: str) -> dict:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": 'python3 -c "%s"' % word}, "cwd": "/"})
    started = time.time()
    try:
        proc = subprocess.run([sys.executable, "-I", "-B", guard], input=payload, capture_output=True, text=True, timeout=20, check=False, env={"JUNIPER_GUARD_HOME": "/nonexistent-home", "PATH": "/usr/bin:/bin"})  # nosec B603
    except subprocess.TimeoutExpired:
        return {"seconds": round(time.time() - started, 2), "outcome": "TIMEOUT (20 s)"}
    return {"seconds": round(time.time() - started, 4), "outcome": "exit %d%s%s" % (proc.returncode, " deny" if proc.stdout else "", (" " + proc.stderr.split(": ", 2)[-1][:60].strip()) if proc.stderr else "")}


def show(shape: str, n: int, chars: int, mode: str, results: dict) -> None:
    cells = "  ".join("%s %7s %s" % (label, "-" if r["seconds"] is None else "%.3f" % r["seconds"], r["outcome"]) for label, r in results.items())
    print("%-34s %-11s n=%-5d chars=%-7d %s" % (shape, mode, n, chars, cells), flush=True)


def main() -> int:
    out = sys.argv[1]
    only = [arg.split("=", 1)[1].split(",") for arg in sys.argv[2:] if arg.startswith("--shapes=")]
    guards = dict(arg.split("=", 1) for arg in sys.argv[2:] if not arg.startswith("--shapes="))
    rows = []
    for shape, build in SHAPES.items():
        if only and shape not in only[-1]:
            continue
        for n in (250, 500, 1000, 2000, 4000, 8000):
            word = build(n)
            results = {label: child(path, word, "expand") for label, path in guards.items()}
            rows.append({"shape": shape, "n": n, "chars": len(word), "mode": "expand", "results": results})
            show(shape, n, len(word), "expand", results)
            if max(r["seconds"] or 99 for r in results.values()) > 5:
                break
        word = build(2000)
        for mode in ("hook-echo", "hook-quoted"):
            results = {label: child(path, word, mode) for label, path in guards.items()}
            rows.append({"shape": shape, "n": 2000, "chars": len(word), "mode": mode, "results": results})
            show(shape, 2000, len(word), mode, results)
        results = {label: process(path, word) for label, path in guards.items()}
        rows.append({"shape": shape, "n": 2000, "chars": len(word), "mode": "process", "results": results})
        show(shape, 2000, len(word), "process", results)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"guards": guards, "python": sys.version.split()[0], "rows": rows}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
