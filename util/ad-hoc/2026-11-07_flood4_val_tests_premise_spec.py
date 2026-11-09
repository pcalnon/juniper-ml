"""
Write the premise-probe spec: each new boundary suite's docstring says its EXISTING sibling suite survives a boundary mutant.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 tests carrier, slice B)
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 carrier validation (BRIEF_VALIDATE.txt); consumed by 2026-11-07_flood4_val_tests_mutants.py

Usage: python3 <this> <out spec.json>

Every entry is kind "probe": the claim holds when the sibling suite PASSES under the mutant (rc 0). A sibling that
fails would make the new suite's stated reason for existing false (its tests would still be valid).
"""

import json
import sys


def p(pid, target, old, new, test_file, claim):
    return {"id": pid, "target": target, "old": old, "new": new, "test_file": test_file, "expect": [], "kind": "probe", "claim": claim}


SPEC = [
    p("PG1", "util/host_state_check.py", "    if abs(gap) <= skew:", "    if abs(gap) < skew:", "tests/test_host_state_check.py", "test_host_state_gate_boundaries.py: replacing <= with < still passes that suite"),
    p("PG2", "util/host_state_check.py", '    if rec["mbps"] < floor:', '    if rec["mbps"] <= floor:', "tests/test_host_state_check.py", "test_host_state_gate_boundaries.py: a measurement equal to the floor is untested"),
    p("PT1", "util/release_train/ceremony.py", "        if encoded_len > cap:", "        if encoded_len >= cap:", "tests/test_release_train_ceremony.py", "test_release_train_exact_caps.py: none of the sibling cases fail if > becomes >="),
    p("PT2", "util/release_train/propose.py", "    return body if _body_size(body) <= PR_BODY_MAX else _pr_body(prop, date, inline_notes=False)", "    return body if _body_size(body) < PR_BODY_MAX else _pr_body(prop, date, inline_notes=False)", "tests/test_release_train_propose.py", "test_release_train_exact_caps.py: none fail if <= becomes <"),
    p("PT3", "util/release_train/propose.py", "    if _body_size(prop.pr_body) > PR_BODY_MAX:  # refuse BEFORE", "    if _body_size(prop.pr_body) >= PR_BODY_MAX:  # refuse BEFORE", "tests/test_release_train_propose.py", "test_release_train_exact_caps.py: none fail if > becomes >="),
    p("PP1", "util/experiments/run_suite.py", "if not timeout > sum(terms.values())}", "if not timeout >= sum(terms.values())}", "tests/test_run_suite.py", "test_per_run_timeout_boundary.py: both test_run_suite results survive > -> >="),
    p("PB1", "util/claude_agent_guard.py", "    return _unique([text] + done + pending)[: limit + 1]", "    return _unique([text] + done + pending)[: limit]", "tests/test_claude_agent_guard.py", "test_claude_agent_guard_brace_cap.py: test_claude_agent_guard.py never reaches the cap"),
    # The other direction of the two PR-body comparisons (MT1/MT2 in the main spec moved them down): real mutants, must be killed.
    {"id": "MT4", "target": "util/release_train/propose.py", "old": "    return body if _body_size(body) <= PR_BODY_MAX else _pr_body(prop, date, inline_notes=False)", "new": "    return body if _body_size(body) <= PR_BODY_MAX + 1 else _pr_body(prop, date, inline_notes=False)", "test_file": "tests/test_release_train_exact_caps.py", "expect": ["test_one_byte_over_the_limit_drops_the_notes"], "kind": "mutant"},
    {"id": "MT5", "target": "util/release_train/propose.py", "old": "    if _body_size(prop.pr_body) > PR_BODY_MAX:  # refuse BEFORE", "new": "    if _body_size(prop.pr_body) > PR_BODY_MAX + 1:  # refuse BEFORE", "test_file": "tests/test_release_train_exact_caps.py", "expect": ["test_execute_refuses_one_byte_over_before_any_write"], "kind": "mutant"},
]


def main() -> int:
    with open(sys.argv[1], "w", encoding="utf-8") as fh:
        json.dump(SPEC, fh, indent=1)
    print(f"{len(SPEC)} entries -> {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
