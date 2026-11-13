#!/usr/bin/env python3
"""
Run every recent real Bash command through several copies of the agent guard: refusals, outcome changes and time.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: the cost of the scan budget on real commands)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-08_flood4r2_ml_code_r2_refusal_census.py (round 2's census, whose transcript reader
         and outcome classes this keeps); validator findings ml-code-port-lens F1 and ml-code-claims-lens F11.

Usage:
    python3 -I util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_census.py <transcripts dir> <max files> <out.json>
        <label>=<guard.py> [<label>=<guard.py> ...] [--slowest N] [--no-gc]

Reads the newest <max files> *.jsonl transcripts under <transcripts dir> once, then runs each guard's
``BashAnalyzer`` over every Bash tool_use command against a throwaway home, timing each call. AGGREGATES ONLY
are printed and written: no command text, no evidence text (only its shape, below) and no transcript content. Per guard: commands
refused, by the guard's own reason (its message up to the first ": "), and by the first word with everything
but [A-Za-z0-9_.-] removed; total and largest analysis time; the longest text given to ``brace_expand`` and, for
a guard that has a brace scan budget, the most any one call spent of it. For every pair of guards: the commands
whose outcome differs (passes, the rule ids denied, or refused), counted by the pair of outcomes; and, for the
same commands, by what explains the change without quoting it: the command's first word, whether the word the
later guard refuses is quoted (bash never brace-expands quoted text, so that refusal is a false one), and for a
rule the later guard adds, the SHAPE of the word that tripped it (every letter as ``a``, every digit as ``9``,
24 characters at most: ``--aa`` is a two-letter long option, ``aaa9`` a name with a digit). Last, the
--slowest N commands of each guard (default 5) are run through every guard AS THE HOOK RUNS (``python3 -I
<guard.py>``, payload on stdin, a throwaway home): wall seconds, with the command's length and first word only.
"""
import collections
import gc
import importlib.util
import itertools
import json
import os
import re
import subprocess  # nosec B404 -- runs the guard copies as the hook does, on commands read from transcripts
import sys
import tempfile
import time
from pathlib import Path


def load(path: str, label: str):
    name = "guard_under_census_" + re.sub(r"[^A-Za-z0-9_]", "_", label)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def commands(path: Path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            message = row.get("message") if isinstance(row, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Bash":
                    command = (part.get("input") or {}).get("command")
                    if isinstance(command, str):
                        yield command


def first_word(command: str) -> str:
    head = command.strip().split(None, 1)[0] if command.strip() else ""
    return re.sub(r"[^A-Za-z0-9_.-]", "", head)[:20] or "?"


def shape(evidence) -> str:
    return re.sub(r"[0-9]", "9", re.sub(r"[A-Za-z]", "a", str(evidence)))[:24]


def failing_word_kind(guard, command: str) -> str:
    """Whether the top-level word that brace_expand refuses is quoted; nested text when no top-level word fails."""
    try:
        lexer = guard.Lexer(command).run()
    except Exception:  # an unlexable command is its own class
        return "unlexable"
    for seg in lexer.segments:
        for word in seg.words:
            try:
                guard.brace_expand(word.text)
            except guard.MalformedInput:
                return "a quoted top-level word" if word.quoted else "an UNQUOTED top-level word"
            except Exception:  # counted, never raised: the census must finish
                return "a top-level word that crashes brace_expand"
    return "nested text (bash -c, $( ), eval or an interpreter's string literal)"


def census(guard, every: list) -> dict:
    reasons = collections.Counter()
    heads = collections.Counter()
    outcomes = []  # per command: "ok", or the sorted rule ids it denies, or "refused: <reason>"
    details = []  # per command: {rule id: shape of its first evidence}, or the kind of word that is refused
    seconds = []
    stats = {"longest_brace_text": 0, "brace_calls": 0, "most_budget_spent": None}
    plain_expand = guard.brace_expand

    def counting_expand(text, *args, **kwargs):
        stats["brace_calls"] += 1
        stats["longest_brace_text"] = max(stats["longest_brace_text"], len(text))
        return plain_expand(text, *args, **kwargs)

    guard.brace_expand = counting_expand
    budget_total = getattr(guard, "BRACE_SCAN_BUDGET", None)
    if budget_total is not None:
        plain_spend = guard._brace_spend
        stats["most_budget_spent"] = 0

        def counting_spend(budget, amount, source):
            stats["most_budget_spent"] = max(stats["most_budget_spent"], budget_total - budget[0] + amount)
            return plain_spend(budget, amount, source)

        guard._brace_spend = counting_spend
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        for name in (".ssh", ".gnupg", ".claude"):
            (home / name).mkdir(parents=True)
        ctx = guard.Context([str(home)], tmp)
        for command in every:
            started = time.perf_counter()
            try:
                hits = guard.BashAnalyzer(ctx).analyze(command)
                outcome = " ".join(sorted({hit.rule_id for hit in hits})) or "ok"
                detail = {}
                for hit in hits:
                    detail.setdefault(hit.rule_id, shape(hit.evidence))
            except guard.MalformedInput as exc:
                outcome = "refused: " + str(exc).split(": ", 1)[0][:110]
                detail = None
            except Exception as exc:  # a guard bug must not stop the census; counted by class only
                outcome = "refused: NOT a MalformedInput: " + exc.__class__.__name__
                detail = None
            seconds.append(time.perf_counter() - started)
            outcomes.append(outcome)
            details.append(failing_word_kind(guard, command) if detail is None else detail)
            if outcome.startswith("refused: "):
                reasons[outcome[9:]] += 1
                heads[first_word(command)] += 1
    return {"refused": sum(reasons.values()), "by_reason": dict(reasons.most_common()), "refused_by_first_word": dict(heads.most_common(15)), "outcomes": outcomes, "details": details, "seconds": seconds, "stats": stats}


def as_hook(guard_path: str, command: str, home: str) -> dict:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": home})
    started = time.time()
    try:
        proc = subprocess.run([sys.executable, "-I", "-B", guard_path], input=payload, capture_output=True, text=True, timeout=30, check=False, cwd=home, env={"JUNIPER_GUARD_HOME": home, "PATH": "/usr/bin:/bin"})  # nosec B603
    except subprocess.TimeoutExpired:
        return {"seconds": round(time.time() - started, 2), "outcome": "TIMEOUT (30 s)"}
    return {"seconds": round(time.time() - started, 3), "outcome": "exit %d%s" % (proc.returncode, " deny" if proc.stdout else "")}


def main(argv: list) -> int:
    slowest = 5
    if "--no-gc" in argv:  # a collection of this process's own growing heap can land inside one command's timing
        gc.disable()
        argv = [arg for arg in argv if arg != "--no-gc"]
    if "--slowest" in argv:
        at = argv.index("--slowest")
        slowest = int(argv[at + 1])
        argv = argv[:at] + argv[at + 2 :]
    root = Path(argv[1]).expanduser()
    limit = int(argv[2])
    out = Path(argv[3])
    guards = {label: str(Path(path).resolve()) for label, path in (arg.split("=", 1) for arg in argv[4:])}  # absolute: the hook runs elsewhere
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    every = [command for path in files for command in commands(path)]
    report = {"transcripts": len(files), "commands": len(every), "longest_command": max(map(len, every), default=0), "guards": {}, "changes": {}, "slowest_as_hook": []}
    print("transcripts read: %d (newest first); Bash commands: %d; longest command: %d characters" % (len(files), len(every), report["longest_command"]), flush=True)
    results = {}
    for label, path in guards.items():
        guard = load(path, label)
        result = results[label] = census(guard, every)
        timing = {"total_seconds": round(sum(result["seconds"]), 2), "largest_seconds": round(max(result["seconds"], default=0.0), 4), "over_100ms": sum(1 for s in result["seconds"] if s > 0.1), "over_1s": sum(1 for s in result["seconds"] if s > 1.0)}
        report["guards"][label] = {"path": path, "version": getattr(guard, "__version__", "?"), "refused": result["refused"], "by_reason": result["by_reason"], "refused_by_first_word": result["refused_by_first_word"], "analysis_time": timing, "brace": result["stats"]}
        print("guard %s (%s): refused %d; by reason %s" % (label, report["guards"][label]["version"], result["refused"], json.dumps(result["by_reason"])), flush=True)
        print("  refused, by first word: %s" % json.dumps(result["refused_by_first_word"]))
        print("  analysis time: %s; brace: %s" % (json.dumps(timing), json.dumps(result["stats"])), flush=True)
    for a, b in itertools.combinations(guards, 2):
        changes = collections.Counter("%s -> %s" % pair for pair in zip(results[a]["outcomes"], results[b]["outcomes"]) if pair[0] != pair[1])
        why = collections.Counter()
        for k, (before, after) in enumerate(zip(results[a]["outcomes"], results[b]["outcomes"])):
            if before == after:
                continue
            detail = results[b]["details"][k]
            if isinstance(detail, str):
                reason = "the refused word is %s" % detail
            else:
                gained = [rule for rule in after.split() if rule not in before.split()]
                reason = "; ".join("%s on a word shaped %s" % (rule, detail.get(rule, "?")) for rule in gained) or "rules lost: %s" % " ".join(r for r in before.split() if r not in after.split())
            why["%s -> %s | first word %s | %s" % (before[:60], after[:60], first_word(every[k]), reason)] += 1
        report["changes"]["%s -> %s" % (a, b)] = {"commands": sum(changes.values()), "by_pair": dict(changes.most_common()), "explained": dict(why.most_common())}
        print("outcome changes %s -> %s: %d commands; %s" % (a, b, sum(changes.values()), json.dumps(dict(changes.most_common()))), flush=True)
        for line, count in why.most_common():
            print("    %3d  %s" % (count, line), flush=True)
    picked = []
    for label in guards:
        order = sorted(range(len(every)), key=lambda k: results[label]["seconds"][k], reverse=True)
        picked += [k for k in order[:slowest] if k not in picked]
    with tempfile.TemporaryDirectory() as tmp:
        home = os.path.join(tmp, "home")
        os.makedirs(os.path.join(home, ".ssh"))
        for k in picked:
            row = {"command_characters": len(every[k]), "first_word": first_word(every[k]), "in_process_seconds": {label: round(results[label]["seconds"][k], 4) for label in guards}, "as_hook": {label: as_hook(path, every[k], home) for label, path in guards.items()}}
            report["slowest_as_hook"].append(row)
            print("slow command (%d characters, first word %s): in process %s; as the hook %s" % (row["command_characters"], row["first_word"], json.dumps(row["in_process_seconds"]), json.dumps(row["as_hook"])), flush=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
