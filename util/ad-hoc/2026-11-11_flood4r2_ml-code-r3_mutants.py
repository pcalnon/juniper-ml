#!/usr/bin/env python3
"""
Run every one-line mutant of the ml-code carrier in a COPY of the tree: round 2's, the validator's, and the scan's own.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: are the tests non-vacuous on the new scan?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-08_flood4r2_ml_code_swap_check.py (round 2's 36 mutants, read from that file);
         validator finding ml-code-port-lens F2 (its 22 mutants, six of which survived round 2's tests; re-anchored
         here on round 3's code); util/claude_agent_guard.py (_brace_closes, _brace_words, _brace_spend).

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_mutants.py <out dir> [--shard I/N] [MUTANT_ID ...]

Nothing in the worktree is edited. A scratch tree that mirrors the repo layout (the guard and its installer,
util/juniper_repo_tmp.bash, util/fleet_triage/, scripts/ and the modules of tests/, without its fixtures) is made
under the temporary directory, turned into an empty git repository of its own (the launcher finds its tmp/ through
git since juniper-ml#2360) and removed at the end; each test file finds its script relative to itself. Per mutant, one exact
string of one file is replaced in the mirror (the string must occur once in the worktree's copy), every
__pycache__ in the mirror is deleted, the mutant's targets run there as separate ``python3 -m unittest``
processes with PYTHONDONTWRITEBYTECODE=1, and the mirror's file is restored. A guard mutant of the V or B
family that the brace suite leaves alive is run against the guard's self-test before it counts as a survivor
(the guard's whole suite takes minutes and pins no brace rule the brace suite does not: run it by hand on an
unexpected survivor). The unmutated mirror must pass every target first (the control), or the run is void.

Families: "main's file" (the four base-* ids of round 2's script: HEAD's whole copy of a code file replaces the
carrier's, every target is run, and the carrier's tests must fail there, which shows each fix fixes); round 2's
list (g, s, c, w, p ids); V1-V22, the validator's; B1-B14, on the one-pass scan and its budget. Two of the validator's are equivalent mutants, as it found (V9: equal ends give one term in either
direction; V15: a rejected sequence group holds no ``{`` to rescan), and are expected to survive.
--shard I/N takes every N-th mutant, so N processes can share the list. Writes <out dir>/mutants[_shardI].json.
Exit 0 when the control passed, every anchor matched and only the expected mutants survived.
"""
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 -- runs unittest on a scratch copy of the tree
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GUARD = "util/claude_agent_guard.py"
BRACE = "tests/test_claude_agent_guard_brace_cap.py"
MIRROR_FILES = [GUARD, "util/install_claude_agent_guard.bash", "util/juniper_repo_tmp.bash", ".gitignore"]  # plus every tests/*.py: the suites import their neighbours
MIRROR_TREES = ["scripts", "util/fleet_triage"]
EXPECTED_SURVIVORS = {"V9": "equivalent: equal ends make one term whichever way the direction is read", "V15": "equivalent: a rejected sequence group holds no { that could open a group"}

# (id, intent, old text, new text): the validator's 22, on round 3's code. V1-V3, V4, V12, V15 and V16 are re-anchored.
VALIDATOR = [
    ("V1", "a comma no longer wins over an earlier '..'", 'found = (shut, "," if comma else "..") if shut != -1 else None', 'found = (shut, "..") if shut != -1 else None'),
    ("V2", "a single '.' counts as the '..' separator", 'elif ch == "." and text[j + 1 : j + 2] == "." and text[j + 2 : j + 3] != "}":', 'elif ch == "." and text[j + 2 : j + 3] != "}":'),
    ("V3", "'..' directly before '}' counts as a separator", 'elif ch == "." and text[j + 1 : j + 2] == "." and text[j + 2 : j + 3] != "}":', 'elif ch == "." and text[j + 1 : j + 2] == ".":'),
    ("V4", "a '{' right after '$' opens a group", 'found = None if i > pos and text[i - 1] == "$" else closes[i]', "found = closes[i]"),
    ("V5", "intmax_t bound off by one", "if any(v < -_INTMAX - 1 or v > _INTMAX for v in numbers):", "if any(v < -_INTMAX - 1 or v >= _INTMAX for v in numbers):"),
    ("V6", "operand limit raised to 2**62", "if any(abs(v) > BRACE_SEQ_OPERAND_LIMIT for v in numbers):", "if any(abs(v) > BRACE_SEQ_OPERAND_LIMIT * 2 for v in numbers):"),
    ("V7", "'-0' pads at length 2", '(len(side) > 2 and side[:2] == "-0")', '(len(side) > 1 and side[:2] == "-0")'),
    ("V8", "padding width from hi only", "width = max(len(lo), len(hi)) if padded else 0", "width = len(hi) if padded else 0"),
    ("V9", "direction from b > a (equal ends)", "direction = 1 if b >= a else -1", "direction = 1 if b > a else -1"),
    ("V10", "the step's sign is not ignored", "size = abs(int(step)) if step else 1", "size = int(step) if step else 1"),
    ("V11", "a generated backtick is not refused", 'if "\\\\" in terms or "`" in terms:', 'if "\\\\" in terms:'),
    ("V12", "the cap ignores the product of groups", "if count * len(tack) > limit:", "if len(tack) > limit:"),
    ("V13", "the depth guard is lifted", "if depth > limit:", "if depth > limit * 1000:"),
    ("V14", "a stray '}' lowers the list depth below 0", 'elif ch == "}" and depth:\n            depth -= 1\n        elif ch == "," and depth == 0:\n            parts.append', 'elif ch == "}":\n            depth -= 1\n        elif ch == "," and depth == 0:\n            parts.append'),
    ("V15", "after a rejected sequence, rescan from the next character", 'i = text.find("{", end + 1)  # not a sequence bash accepts', 'i = text.find("{", i + 1)  # not a sequence bash accepts'),
    ("V16", "a top-level '}' before any separator ends the group", "shut, comma = j, False  # found stands", "shut, comma, found = j, False, None  # found stands"),
    ("V17", "a signed step is not a sequence", r"(?:\.\.([+-]?[0-9]+))?", r"(?:\.\.([0-9]+))?"),
    ("V18", "a '+' endpoint is not a sequence", r"([+-]?[0-9]+)\.\.([+-]?[0-9]+)", r"(-?[0-9]+)\.\.(-?[0-9]+)"),
    ("V19", "the range cap is off by one", "if count > MAX_BRACE_ALTERNATIVES:", "if count > MAX_BRACE_ALTERNATIVES + 1:"),
    ("V20", "the nested-brace refusal ignores '${'", 'if "{" in amble.replace("${", ""):', 'if "{" in amble:'),
    ("V21", "a nested '{' in a sequence group is kept, not refused", 'if "{" in amble.replace("${", ""):\n            raise', 'if "{{{{" in amble.replace("${", ""):\n            raise'),
    ("V22", "letter ranges are case-folded to lower", "a, b = (int(lo), int(hi)) if numeric else (ord(lo), ord(hi))", "a, b = (int(lo), int(hi)) if numeric else (ord(lo.lower()), ord(hi.lower()))"),
]
# The one-pass scan and its budget (round 3).
SCAN = [
    ("B1", "the budget never refuses", "    if budget[0] < 0:", "    if budget[0] < -(10**12):"),
    ("B2", "the budget refuses one character early", "    if budget[0] < 0:", "    if budget[0] <= 0:"),
    ("B3", "a scan is not charged", "    _brace_spend(budget, len(text), source)", "    _brace_spend(budget, 0, source)"),
    ("B4", "each list part gets a budget of its own", "_brace_words(part, limit, source, depth + 1, budget)", "_brace_words(part, limit, source, depth + 1, [BRACE_SCAN_BUDGET])"),
    ("B5", "a long word with no brace is scanned and charged", '    if "{" not in text:\n        return [text]', '    if "{" not in text and len(text) < 100:\n        return [text]'),
    ("B6", "one budget is shared by every call", "_brace_words(text, limit, text, 0, [BRACE_SCAN_BUDGET])", '_brace_words(text, limit, text, 0, _brace_spend.__dict__.setdefault("shared", [BRACE_SCAN_BUDGET]))'),
    ("B7", "a nested {...} is not stepped over", "shut, comma, found = resume[match[j]] if j in match else (-1, False, None)", "shut, comma, found = (-1, False, None)"),
    ("B8", "a comma after the group's } still counts", "shut, comma = j, False  # found stands", "shut = j  # found stands"),
    ("B9", "a comma is lost across a nested {...}", "resume[j] = (shut, comma, found)", "resume[j] = (shut, False, found)"),
    ("B10", "a list is split at nested commas too", '_BRACE_LIST_RE = re.compile(r"[{},]")', '_BRACE_LIST_RE = re.compile(r"[,]")'),
    ("B11", "the scan does not see '.'", '_BRACE_SCAN_RE = re.compile(r"[{},.]")', '_BRACE_SCAN_RE = re.compile(r"[{},]")'),
    ("B12", "the text after a group starts at its }", "        pos = end + 1\n", "        pos = end\n"),
    ("B13", "the word count ignores earlier groups", "        count *= len(tack)\n", "        count *= 1\n"),
    ("B14", "a comma makes a sequence, not a list", 'found = (shut, ",") if shut != -1 else None', 'found = (shut, "..") if shut != -1 else None'),
]


def round2_mutants() -> list:
    path = REPO / "util" / "ad-hoc" / "2026-11-08_flood4r2_ml_code_swap_check.py"
    spec = importlib.util.spec_from_file_location("round2_swap_check", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["round2_swap_check"] = module
    spec.loader.exec_module(module)
    rows = [{"id": ident, "family": "main's file", "intent": "the carrier's tests against HEAD's copy of the file: they must fail", "file": rel, "old": None, "new": None, "targets": list(targets), "deep": False} for ident, rel, targets in module.BASELINES]
    return rows + [{"id": ident, "family": "round 2", "intent": ident.split("-", 1)[1], "file": rel, "old": old, "new": new, "targets": list(targets), "deep": False} for ident, rel, old, new, targets in module.MUTANTS]


def all_mutants() -> list:
    rows = round2_mutants()
    for family, table in (("validator", VALIDATOR), ("scan", SCAN)):
        rows += [{"id": ident, "family": family, "intent": intent, "file": GUARD, "old": old, "new": new, "targets": [BRACE], "deep": True} for ident, intent, old, new in table]
    return rows


def build_mirror(mirror: Path) -> None:
    for rel in MIRROR_FILES + sorted("tests/" + path.name for path in (REPO / "tests").glob("*.py")):
        (mirror / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, mirror / rel)
    for rel in MIRROR_TREES:
        shutil.copytree(REPO / rel, mirror / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "sessions", "pyproject.toml"))
    # Since juniper-ml#2360 the launcher asks git for its checkout's tmp/ and refuses to launch outside one, so the
    # mirror is made an (empty) repository of its own: nothing is added or committed in it.
    subprocess.run(["git", "init", "-q", str(mirror)], capture_output=True, check=True)  # nosec B603 B607 -- fixed argv


def clear_pycache(mirror: Path) -> None:
    for cache in list(mirror.rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)


def run_target(mirror: Path, target: str) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if target == "--self-test":
        argv = [sys.executable, "-I", "-B", str(mirror / GUARD), "--self-test"]
    else:
        argv = [sys.executable, "-B", "-m", "unittest", target]
    proc = subprocess.run(argv, cwd=str(mirror), env=env, capture_output=True, text=True, timeout=1500, check=False)  # nosec B603 -- fixed argv
    text = proc.stdout + proc.stderr
    summary = [line for line in text.splitlines() if line.startswith(("FAILED", "OK", "Ran ")) or "self-test:" in line]
    return {"target": target, "exit": proc.returncode, "summary": " | ".join(summary[-2:]), "first_failures": [line for line in text.splitlines() if line.startswith(("FAIL:", "ERROR:"))][:4]}


def main(argv: list) -> int:
    out = Path(argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    shard = [arg for arg in argv[2:] if arg.startswith("--shard")]
    args = [arg for arg in argv[2:] if not arg.startswith("--shard") and "/" not in arg]
    index, shards = (0, 1)
    if shard:
        index, shards = (int(part) for part in argv[argv.index("--shard") + 1].split("/"))
    mutants = [m for number, m in enumerate(all_mutants()) if number % shards == index and (not args or m["id"] in args)]
    report = {"repo": str(REPO), "shard": "%d/%d" % (index, shards), "control": [], "mutants": []}
    mirror = Path(tempfile.mkdtemp(prefix="ml-code-r3-mutants-"))
    problems = []
    try:
        build_mirror(mirror)
        targets = []
        for m in mutants:
            targets += [t for t in m["targets"] + (["--self-test"] if m["deep"] else []) if t not in targets]
        for target in targets:
            clear_pycache(mirror)
            row = run_target(mirror, target)
            report["control"].append(row)
            print("control  %-90s exit %d  %s" % (target, row["exit"], row["summary"]), flush=True)
            if row["exit"] != 0:
                problems.append("control failed: %s" % target)
        if problems:
            print("the unmutated mirror fails a target: the run is void")
        for m in mutants if not problems else []:
            original = (REPO / m["file"]).read_bytes()
            text = original.decode("utf-8")
            started = time.time()
            row = {key: m[key] for key in ("id", "family", "intent", "file", "old", "new")}
            whole = m["old"] is None  # HEAD's whole file instead of one changed string; every target is then run
            if not whole and text.count(m["old"]) != 1:
                row["verdict"] = "ANCHOR occurs %d times" % text.count(m["old"])
                problems.append("%s: anchor occurs %d times" % (m["id"], text.count(m["old"])))
            else:
                try:
                    if whole:
                        swapped = subprocess.run(["git", "show", "HEAD:" + m["file"]], cwd=str(REPO), capture_output=True, check=True).stdout  # nosec B603 B607 -- fixed argv
                    else:
                        swapped = text.replace(m["old"], m["new"]).encode("utf-8")
                    (mirror / m["file"]).write_bytes(swapped)
                    runs = []
                    for target in m["targets"] + (["--self-test"] if m["deep"] else []):
                        clear_pycache(mirror)
                        runs.append(run_target(mirror, target))
                        if runs[-1]["exit"] != 0 and not whole:
                            break  # killed: the later, slower targets are not needed
                    if whole:
                        runs.sort(key=lambda run: run["exit"] != 0)  # a failing target last, as for a killed mutant
                finally:
                    (mirror / m["file"]).write_bytes(original)
                    clear_pycache(mirror)
                killed = runs[-1]["exit"] != 0
                row.update({"runs": runs, "verdict": "killed" if killed else "survived", "killed_by": runs[-1]["target"] if killed else None})
                if not killed and m["id"] not in EXPECTED_SURVIVORS:
                    problems.append("%s survived" % m["id"])
                if killed and m["id"] in EXPECTED_SURVIVORS:
                    problems.append("%s was expected to survive (equivalent) and was killed: re-read it" % m["id"])
            row["seconds"] = round(time.time() - started, 1)
            report["mutants"].append(row)
            note = " (expected: %s)" % EXPECTED_SURVIVORS[m["id"]] if row["verdict"] == "survived" and m["id"] in EXPECTED_SURVIVORS else ""
            print("%-34s %-9s %s%s" % (m["id"], row["verdict"], ("by %s: %s" % (row["killed_by"], row["runs"][-1]["summary"])) if row.get("killed_by") else "", note), flush=True)
            if m["old"] is None:
                for run in row.get("runs", []):
                    print("    HEAD's %s under %s: exit %d  %s" % (m["file"], run["target"], run["exit"], run["summary"]), flush=True)
            with open(out / ("mutants%s.json" % ("_shard%d" % index if shards > 1 else "")), "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=1)
    finally:
        shutil.rmtree(mirror, ignore_errors=True)
    report["problems"] = problems
    with open(out / ("mutants%s.json" % ("_shard%d" % index if shards > 1 else "")), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    ran = [m for m in report["mutants"] if "runs" in m]
    print("mutants run: %d; killed: %d; survived: %s; problems: %s" % (len(ran), sum(1 for m in ran if m["verdict"] == "killed"), [m["id"] for m in ran if m["verdict"] == "survived"] or "none", problems or "none"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
