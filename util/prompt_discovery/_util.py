"""Shared helpers for the prompt-discovery probes.

``util/`` is not a package (no ``__init__.py``; tests use the ``sys.path.insert`` idiom),
so the probes import this module by its bare name once the package directory is on the
path (the script's own directory is on ``sys.path`` when ``cli.py`` is run by path).

Part of the custom-agent suite (PR 4). Design-of-record:
``notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md`` (S5.6).
"""

from __future__ import annotations

import subprocess
from typing import Optional, Sequence, Tuple


def run(cmd: Sequence[str], cwd: Optional[str] = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Run a command without ever raising.

    Returns ``(returncode, stdout, stderr)``. A missing binary yields rc ``127`` and a
    timeout yields rc ``124`` -- callers treat any nonzero rc as "probe unavailable" and
    degrade gracefully rather than aborting the whole bundle.
    """
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            list(cmd),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", f"binary not found: {cmd[0] if cmd else '?'}"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
