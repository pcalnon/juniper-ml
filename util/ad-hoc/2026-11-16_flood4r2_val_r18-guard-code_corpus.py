"""
No-denial-lost corpus check for agent guard 1.4.0 (validator JL1, code lens, item 3): run main 1.3.0 and 1.4.0
in-process on (a) the 378 credential-reaching candidates of the earlier final check (bypass.json rows' "command") and
(b) every Bash command string literal in the agent-guard test suites of main (edea2eb1), and count the decision
transitions. Aggregates are printed; for (b) the transitions that lose a block are listed (they are test strings).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_differential.py (loader, decide)

Usage: python3 <this file> <scratch dir> <bypass.json> <out.json> <suite file> [<suite file> ...]
The guards only judge payloads (run_hook); nothing is executed.
"""

import ast
import importlib.util
import json
import os
import sys
from pathlib import Path


def load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def suite_strings(path: Path) -> list:
    """Every string constant in a suite that could be a Bash command (has a space or a shell metacharacter)."""
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if 2 <= len(s) <= 20000 and (" " in s or any(c in s for c in "~$`{}|;&<>")) and "\n\n" not in s:
                out.append(s)
    return out


def main(argv: list) -> int:
    scratch = Path(argv[0]).resolve()
    rows = json.loads(Path(argv[1]).read_text())["rows"]
    out = Path(argv[2])
    suites = []
    for arg in argv[3:]:
        path = Path(arg)
        suites.extend(sorted(path.glob("test_claude_agent_guard*.py")) if path.is_dir() else [path])
    print("suites:", len(suites))
    diff = load_helper(Path(__file__).with_name("2026-11-16_flood4r2_val_r18-guard-code_differential.py"), "jl1_diff_c")
    os.environ.pop("CLAUDE_PROJECT_DIR", None)
    home = str(scratch / "scratch_home")
    cwd = os.path.join(home, "Development", "repo")
    guards = {"main": diff.load(scratch / "work" / "guard_main.py", "jl1_cm"), "new": diff.load(scratch / "work" / "guard_new.py", "jl1_cn")}
    report = {}
    # (a) the 378 candidates
    trans = {}
    for row in rows:
        verdicts = tuple(diff.decide(g, row["command"], home, cwd)[0] for g in guards.values())
        key = "%s->%s" % verdicts
        trans[key] = trans.get(key, 0) + 1
    report["candidates_378"] = {"n": len(rows), "transitions": trans}
    print("candidates:", len(rows), trans)
    # (b) suite strings, judged as Bash commands with cwd = the scratch repo and with cwd = the scratch home
    strings = []
    for suite in suites:
        strings.extend(suite_strings(suite))
    strings = sorted(set(strings))
    trans = {}
    lost = []
    for s in strings:
        for where in (cwd, home):
            s2 = s.replace("@HOME@", home).replace("@ROOT@", str(scratch / "root")).replace("@REPO@", cwd)
            verdicts = tuple(diff.decide(g, s2, home, where)[0] for g in guards.values())
            key = "%s->%s" % verdicts
            trans[key] = trans.get(key, 0) + 1
            if verdicts[0] in ("DENY", "REFUSE") and verdicts[1] == "PASS":
                lost.append({"cwd": "HOME" if where == home else "REPO", "string": s[:300], "main": verdicts[0]})
    report["suite_strings"] = {"n_strings": len(strings), "n_judgements": 2 * len(strings), "transitions": trans, "block_to_pass": lost}
    print("suite strings:", len(strings), trans)
    for item in lost:
        print("  BLOCK->PASS", item["cwd"], item["main"], repr(item["string"][:160]))
    out.write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
