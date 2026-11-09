"""
Attack the carried tests' docstring CONCLUSIONS: several new juniper-service-core test files claim the
pre-existing suites stay green under a named mutant (so the new file is the only guard). For each such
mutant, apply it, run the REST of the suite (the carrying file --ignore'd), restore byte-for-byte,
and report whether the rest stayed green (claim holds) or caught it (claim false). Also evaluates the
four new fenced_lines assertions of test_docs_additions_check in memory under the {0,4} fence mutant,
since unittest stops at the earlier pre-existing assertion.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier validation, sub-package slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (BRIEF_VALIDATE.txt)

Usage: python3 <this> <worktree> <venv root> <scratch dir>
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import types
import xml.etree.ElementTree as ET

SC = "juniper-service-core/juniper_service_core/"
T = "juniper-service-core/tests/"

PROBES = [
    ("P1", T + "test_attachment_budget_exact.py", SC + "websocket/worker_stream.py", "if len(attachment_names) > _MAX_ATTACHMENTS:", "if len(attachment_names) >= _MAX_ATTACHMENTS:"),
    ("P2", T + "test_attachment_budget_exact.py", SC + "websocket/worker_stream.py", "if total_bytes > _MAX_TOTAL_BINARY_SIZE:", "if total_bytes >= _MAX_TOTAL_BINARY_SIZE:"),
    ("P3", T + "test_request_body_limit_boundary.py", SC + "middleware.py", "if size > self._max_bytes:", "if size >= self._max_bytes:"),
    ("P4", T + "test_request_body_limit_boundary.py", SC + "middleware.py", "if declared_length > self._max_bytes:", "if declared_length >= self._max_bytes:"),
    ("P5", T + "test_ws_frame_exact_cap.py", SC + "websocket/worker_stream.py", "\n    if len(raw) > _MAX_JSON_SIZE:", "\n    if len(raw) >= _MAX_JSON_SIZE:"),
    ("P6", T + "test_ws_frame_exact_cap.py", SC + "websocket/control_stream.py", "if len(raw) > _MAX_MESSAGE_SIZE:", "if len(raw) >= _MAX_MESSAGE_SIZE:"),
    ("P7", T + "test_middleware.py", SC + "security.py", "if len(self._failures) > self._MAX_ENTRIES:", "if False:"),
    ("P8", T + "test_websocket_replay_continuity.py", SC + "websocket/manager.py", "if last_seq < oldest_seq - 1:", "if last_seq < oldest_seq - 2:"),
    ("P9", T + "test_websocket_replay_continuity.py", SC + "websocket/manager.py", "if last_seq < oldest_seq - 1:", "if last_seq <= oldest_seq - 1:"),
]

NEW_FENCE_ASSERTIONS = [
    ("   ```bash\n   # install the extras\n   ```", {1, 2, 3}, "1-3 spaces of indent are a fence"),
    ("```\n# inside\n   ```\n# a real heading\n", {1, 2, 3}, "a closer indented 3 spaces still closes"),
    ("```\n# still fenced\n    ```\n# still fenced too\n```\n", {1, 2, 3, 4, 5}, "a closer indented 4 spaces does not close"),
    ("~~~ has `tick\n# inside\n~~~\n", {1, 2, 3}, "a tilde fence's info string may contain a backtick"),
]


def clear_pycache(root):
    for dirpath, dirnames, _ in os.walk(root):
        if "__pycache__" in dirnames:
            shutil.rmtree(os.path.join(dirpath, "__pycache__"), ignore_errors=True)


def failed_tests(junit):
    out = []
    for case in ET.parse(junit).iter("testcase"):
        if any(c.tag in ("failure", "error") for c in case):
            out.append(f"{case.get('classname')}::{case.get('name')}")
    return out


def fence_probe(wt):
    path = os.path.join(wt, "juniper-ci-tools/juniper_ci_tools/docs_additions_check.py")
    with open(path) as fh:
        src = fh.read()
    old = '_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")'
    assert src.count(old) == 1
    rows = {}
    for label, text in (("original", src), ("{0,4}", src.replace(old, old.replace("{0,3}", "{0,4}"))), ("{0,2}", src.replace(old, old.replace("{0,3}", "{0,2}")))):
        mod = types.ModuleType(f"dac_probe_{len(rows)}")
        mod.__dict__["__name__"] = mod.__name__
        sys.modules[mod.__name__] = mod  # @dataclass resolves the module via sys.modules
        exec(compile(text, path, "exec"), mod.__dict__)
        rows[label] = [{"assertion": msg, "expected": sorted(exp), "got": sorted(mod.fenced_lines(doc)), "holds": mod.fenced_lines(doc) == exp} for doc, exp, msg in NEW_FENCE_ASSERTIONS]
    return rows


def main(argv):
    wt, venv_root, scratch = argv[1:4]
    py = os.path.join(venv_root, "sc-3.12", "bin", "python")
    junit_dir = os.path.join(wt, "tmp", "val-junit")
    log_dir = os.path.join(scratch, "claims")
    os.makedirs(log_dir, exist_ok=True)
    results = {"probes": [], "fence_new_assertions": fence_probe(wt)}
    for pid, carrier_file, target, old, new in PROBES:
        tpath = os.path.join(wt, target)
        with open(tpath, "rb") as fh:
            original = fh.read()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode()
        row = {"id": pid, "carrier_file": carrier_file, "target": target, "old": old, "new": new, "anchor_count": text.count(old)}
        if row["anchor_count"] != 1:
            row["result"] = "inapplicable"
            results["probes"].append(row)
            continue
        junit = os.path.join(junit_dir, f"claim-{pid}.xml")
        rest = [py, "-m", "pytest", "juniper-service-core/tests/", f"--ignore={carrier_file}", "-p", "no:cacheprovider", "-q", f"--junitxml={junit}"]
        try:
            clear_pycache(os.path.join(wt, SC))
            with open(tpath, "w") as fh:
                fh.write(text.replace(old, new, 1))
            with open(os.path.join(log_dir, f"{pid}-rest.log"), "w") as log:
                row["rest_exit"] = subprocess.run(rest, cwd=wt, stdout=log, stderr=subprocess.STDOUT).returncode
            row["rest_failed"] = failed_tests(junit)
            carried = [py, "-m", "pytest", carrier_file, "-p", "no:cacheprovider", "-q"]
            with open(os.path.join(log_dir, f"{pid}-carried.log"), "w") as log:
                row["carried_exit"] = subprocess.run(carried, cwd=wt, stdout=log, stderr=subprocess.STDOUT).returncode
        finally:
            with open(tpath, "wb") as fh:
                fh.write(original)
            clear_pycache(os.path.join(wt, SC))
        with open(tpath, "rb") as fh:
            row["restored"] = hashlib.sha256(fh.read()).hexdigest() == before
        row["claim_holds"] = row["rest_exit"] == 0 and row["carried_exit"] != 0
        results["probes"].append(row)
        print(f"{pid} {os.path.basename(carrier_file)}: rest_exit={row['rest_exit']} carried_exit={row['carried_exit']} restored={row['restored']} rest_failed={row['rest_failed'][:4]}")
    for label, rows in results["fence_new_assertions"].items():
        print(f"fence {label}: " + ", ".join(f"{r['assertion']}={'ok' if r['holds'] else 'FAILS'}" for r in rows))
    with open(os.path.join(scratch, "docstring_claims.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
