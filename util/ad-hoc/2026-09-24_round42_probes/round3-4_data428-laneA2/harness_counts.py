"""Static counts from the shipped non-vacuity harness: mutations, CAUGHT arms, controls, baseline set.

Also checks each edit's find-string occurs exactly once in the tree (the harness's own precondition)
and that every named node id exists in the test file.
"""

import importlib.util
import re
import sys
from pathlib import Path

tree = Path(sys.argv[1])
path = tree / "util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py"
spec = importlib.util.spec_from_file_location("harness_under_count", path)
mod = importlib.util.module_from_spec(spec)
sys.modules["harness_under_count"] = mod  # @dataclass needs the module registered
spec.loader.exec_module(mod)

muts = mod.MUTATIONS
must_fail = sum(len(m.must_fail) for m in muts)
controls = sum(len(m.must_still_pass) for m in muts)
every = sorted({n for m in muts for n in m.must_fail + m.must_still_pass})
print(f"mutations={len(muts)} must_fail(CAUGHT arms)={must_fail} controls={controls} unique_named_tests(baseline)={len(every)}")
print("names:", [m.name.split(":")[0] for m in muts])

# Every named node must exist in the test file as class::method.
test_src = (tree / mod.T).read_text()
classes = {}
current = None
for line in test_src.splitlines():
    m = re.match(r"class (\w+)", line)
    if m:
        current = m.group(1)
        classes[current] = set()
        continue
    m = re.match(r"    def (test_\w+)", line)
    if m and current:
        classes[current].add(m.group(1))
missing = [n for n in every if n.split("::")[2] not in classes.get(n.split("::")[1], set())]
print("named node ids missing from the test file:", missing)

# Each edit must match exactly once in the tree's CURRENT source (the harness refuses otherwise).
bad = []
for m in muts:
    for repo_path, find, _replace in m.edits:
        rel = repo_path.relative_to(mod.REPO)
        text = (tree / rel).read_text()
        c = text.count(find)
        if c != 1:
            bad.append((m.name, str(rel), c))
print("edits not matching exactly once:", bad)

# Which tests in the file are named by no mutation at all?
all_tests = {f"{c}::{t}" for c, ts in classes.items() for t in ts}
named = {"::".join(n.split("::")[1:]) for n in every}
print(f"tests in file={len(all_tests)}; named by the harness={len(named & all_tests)}; unnamed={len(all_tests - named)}")
for t in sorted(all_tests - named):
    print("  unnamed:", t)
