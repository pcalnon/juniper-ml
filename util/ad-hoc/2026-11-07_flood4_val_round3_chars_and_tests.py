"""
Round-3 validation of the juniper-ml flood-4 docs carrier: characters and named tests.

1. For every line the carrier adds (diff against bbdeb758), list HTML entities and any
   non-ASCII character that the file's bbdeb758 text does not already use, or uses
   rarely.
2. For every test file path and test function name the added lines cite, check that it
   exists on the tree (a test file under tests/ or a sub-package tests/ directory; a
   function defined as `def test_...` somewhere under a tests/ directory).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier, round-3 validation (session 7ceca543)
"""

import collections
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = "bbdeb75823c011e780058f20d4df902a79f436ba"
FILES = [
    "CHANGELOG.md",
    "docs/REFERENCE.md",
    "docs/QUICK_START.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "juniper-config-tools/README.md",
    "juniper-service-core/README.md",
]
ENTITY = re.compile(r"&(?:[A-Za-z]+|#\d+|#x[0-9A-Fa-f]+);")
TEST_FILE = re.compile(r"(?:[\w./-]*/)?(test_[A-Za-z0-9_]+\.py)")
TEST_FUNC = re.compile(r"`(test_[A-Za-z0-9_]+)`")


def run(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout


def main():
    scratch = Path(sys.argv[1])
    out = {"chars": {}, "entities": [], "test_files": {}, "test_funcs": {}}
    test_defs = collections.defaultdict(list)
    test_paths = {}
    for p in REPO.rglob("test_*.py"):
        rel = p.relative_to(REPO).as_posix()
        if "/.claude/" in "/" + rel or rel.startswith("tmp/") or "/node_modules/" in rel:
            continue
        test_paths.setdefault(p.name, []).append(rel)
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in re.finditer(r"^\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)", text, re.M):
            test_defs[m.group(1)].append(rel)
    for path in FILES:
        base_text = run("show", f"{BASE}:{path}")
        base_counts = collections.Counter(ch for ch in base_text if ord(ch) > 127)
        diff = run("diff", "-U0", BASE, "--", path)
        added = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
        for ln in added:
            for m in ENTITY.finditer(ln):
                out["entities"].append({"file": path, "entity": m.group(0), "line": ln[:200]})
            for ch in set(ch for ch in ln if ord(ch) > 127):
                key = f"{path} U+{ord(ch):04X} {ch}"
                rec = out["chars"].setdefault(key, {"base_uses": base_counts[ch], "added_lines": 0, "example": ln[:240]})
                rec["added_lines"] += 1
            for m in TEST_FILE.finditer(ln):
                name = m.group(1)
                out["test_files"].setdefault(name, test_paths.get(name, []))
            for m in TEST_FUNC.finditer(ln):
                name = m.group(1)
                out["test_funcs"].setdefault(name, test_defs.get(name, []))
    with open(scratch / "chars_and_tests.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("== non-ASCII in added lines (file, char, base uses, added lines) ==")
    for key, rec in sorted(out["chars"].items()):
        flag = "  <-- NEW/RARE" if rec["base_uses"] < 3 else ""
        print(f"{key}: base {rec['base_uses']}, added {rec['added_lines']}{flag}")
        if flag:
            print("     e.g.", rec["example"][:200])
    print("== HTML entities in added lines ==", len(out["entities"]))
    for e in out["entities"]:
        print("  ", e)
    missing_files = [n for n, v in out["test_files"].items() if not v]
    missing_funcs = [n for n, v in out["test_funcs"].items() if not v]
    print(f"== test files cited: {len(out['test_files'])}, missing: {missing_files}")
    print(f"== test functions cited: {len(out['test_funcs'])}, missing: {missing_funcs}")


if __name__ == "__main__":
    main()
