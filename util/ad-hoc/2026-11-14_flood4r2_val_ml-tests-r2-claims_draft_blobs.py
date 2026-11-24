"""
Write each draft's own copy of its new test file into a scratch worktree of main, so the repository's pinned hooks
and suites can be run on the drafts AS SUBMITTED (claims lens, session 8: re-deriving the carried table's "fixes").
Reads refs/flood4r2v/pr/<N> from --repo; writes only into --dest (a validator-owned worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import subprocess  # nosec B404 - fixed argv: git show of fetched refs in the validator's own worktree
import sys
from pathlib import Path

PAIRS = (
    (2469, "tests/test_claude_agent_guard_nest_depth.py"),
    (2472, "tests/test_launcher_prompt_and_version_edges.py"),
    (2478, "tests/test_launcher_empty_version_output.py"),
    (2481, "tests/test_predict_merge_scratch_edges.py"),
    (2484, "tests/test_predict_merge_shallow_worktree.py"),
    (2491, "tests/test_claude_agent_guard_ansi_escapes.py"),
    (2495, "tests/test_prompt_file_boolean_tokens.py"),
    (2496, "tests/test_predict_merge_guard_edges.py"),
    (2499, "tests/test_cascor_eval_zero_and_enabled.py"),
    (2503, "tests/test_prompt_file_kind.py"),
    (2509, "tests/test_wake_spacer_flags.py"),
    (2515, "tests/test_claude_agent_guard_sign_edges.py"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the drafts' test files into a scratch worktree.")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args()
    for number, path in PAIRS:
        done = subprocess.run(["git", "show", f"refs/flood4r2v/pr/{number}:{path}"], cwd=str(args.repo), capture_output=True, check=True)  # nosec B603 B607
        target = args.dest / path
        target.write_bytes(done.stdout)
        print(f"#{number} {path} {len(done.stdout)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
