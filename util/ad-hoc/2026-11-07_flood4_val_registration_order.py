"""
Flood-4 validation: compare the ORDER of ci.yml's regression-step suite invocations with REFERENCE.md's
`### Running every suite` block, and locate each new suite in ci.yml, the run list and the Test Suite
Reference (by line number), for both origin/main and this worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
NEW = ["tests/test_claude_agent_guard_brace_cap.py", "tests/test_per_run_timeout_boundary.py", "tests/test_host_state_gate_boundaries.py", "tests/test_release_train_exact_caps.py"]
INV = re.compile(r"python3 -m unittest -v (tests/test_[A-Za-z0-9_]+\.py)")


def ci_sequence(text: str) -> list[str]:
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "- name: Run Python regression tests")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("- name: "))
    return [m.group(1) for l in lines[start:end] if not l.strip().startswith("#") for m in [INV.search(l)] if m]


def ref_sequence(text: str) -> tuple[list[str], int, int]:
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "### Running every suite")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## ") or lines[i].startswith("### "))
    return [m.group(1) for l in lines[start:end] for m in [INV.search(l)] if m], start + 1, end


def tsr_entries(text: str) -> dict[str, int]:
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "## Test Suite Reference")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    out: dict[str, int] = {}
    for i in range(start, end):
        m = re.match(r"- `(tests/test_[A-Za-z0-9_]+\.py)` -- ", lines[i])
        if m:
            out.setdefault(m.group(1), i + 1)
    return out


def main() -> int:
    for label, ci, ref in (
        ("origin/main", subprocess.run(["git", "show", f"{BASE}:.github/workflows/ci.yml"], cwd=HERE, capture_output=True, text=True, check=True).stdout, subprocess.run(["git", "show", f"{BASE}:docs/REFERENCE.md"], cwd=HERE, capture_output=True, text=True, check=True).stdout),
        ("carrier", (HERE / ".github/workflows/ci.yml").read_text(), (HERE / "docs/REFERENCE.md").read_text()),
    ):
        cs = ci_sequence(ci)
        rs, rstart, rend = ref_sequence(ref)
        ts = tsr_entries(ref)
        print(f"== {label}: ci {len(cs)} (unique {len(set(cs))}), run-list {len(rs)} (unique {len(set(rs))}) lines {rstart}-{rend}, TSR entries {len(ts)}")
        print("   sequences identical:", cs == rs)
        if cs != rs:
            for i, (a, b) in enumerate(zip(cs, rs)):
                if a != b:
                    print(f"   first divergence at index {i}: ci={a} ref={b}")
                    break
        dup_ci = sorted({s for s in cs if cs.count(s) > 1})
        print("   duplicated in ci:", dup_ci)
        missing_tsr = sorted(set(cs) - set(ts))
        print(f"   run by ci but NO Test Suite Reference entry ({len(missing_tsr)}):", missing_tsr[:60])
        for n in NEW:
            ci_idx = cs.index(n) if n in cs else None
            prev = cs[ci_idx - 1] if ci_idx else None
            ref_idx = rs.index(n) if n in rs else None
            rprev = rs[ref_idx - 1] if ref_idx else None
            print(f"   {n}: ci#{ci_idx} after {prev}; ref#{ref_idx} after {rprev}; TSR line {ts.get(n)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
