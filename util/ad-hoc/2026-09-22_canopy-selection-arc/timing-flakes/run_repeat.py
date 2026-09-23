"""Scratch driver (agent-s): run canopy pytest from <worktree>/src with ws_repeat_plugin loaded.

Usage: <canopy-env-python> run_repeat.py <pytest args...>
"""

import os
import sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRATCH)

import pytest  # noqa: E402

import ws_repeat_plugin  # noqa: E402

WORKTREE = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--test-timing-flakes--20260922-2022--26e0546f"

if __name__ == "__main__":
    os.chdir(os.path.join(WORKTREE, "src"))
    sys.exit(pytest.main(sys.argv[1:], plugins=[ws_repeat_plugin]))
