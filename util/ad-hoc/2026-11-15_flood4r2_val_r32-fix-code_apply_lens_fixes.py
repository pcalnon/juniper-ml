#!/usr/bin/env python3
"""
Apply the code lens's proposed fixes (F1, F2, F3) to a scratch copy of the r32 pause carrier's manager.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (Cursor flood-4 round 2, validator LN1, code lens on the r32 pause fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor carrier r32-pause-fix; the lens's findings.json F1-F3

Only ``--copy`` is edited: a scratch directory holding a copy of the validator's tree (``src/``,
``conf/``, ``pyproject.toml``), never the carrier and never a worktree's tracked files. Each edit is
an exact replacement whose target must occur exactly once; ``--fixes`` picks which of F1, F2, F3 to
apply. Prints the sha256 of the file before and after.

Usage:
  2026-11-15_flood4r2_val_r32-fix-code_apply_lens_fixes.py --copy <scratch tree> --fixes F1 F2 F3
Exit: 0 when every requested edit applied; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

MANAGER = Path("src/api/lifecycle/manager.py")
NOT_ACTIVE = 'raise RuntimeError("Training is not active")'

EDITS = {
    "F1": (
        ("        self._pause_lock = threading.Lock()\n", "        self._pause_lock = threading.Lock()\n        # The stop signal of the run that owns the lifecycle (see ``_run_training``).\n        self._lifecycle_stop_event = self._stop_event\n"),
        ("        stop_event = self._stop_event if stop_event is None else stop_event\n", "        stop_event = self._stop_event if stop_event is None else stop_event\n        self._lifecycle_stop_event = stop_event\n"),
        (f"        with self._pause_lock:\n            if not self.state_machine.is_started():\n                {NOT_ACTIVE}\n", f"        with self._pause_lock:\n            if not self.state_machine.is_started() or self._lifecycle_stop_event.is_set():\n                {NOT_ACTIVE}\n"),
    ),
    "F2": (
        ("none can straddle the submit.\n            with self._pause_lock:\n                self._pause_event.set()\n", "none can straddle the submit.\n            with self._pause_lock:\n                if not self.state_machine.is_paused():\n                    self._pause_event.set()\n"),
        ("no pause straddles this submit.\n                with self._pause_lock:\n                    self._pause_event.set()\n", "no pause straddles this submit.\n                with self._pause_lock:\n                    if not self.state_machine.is_paused():\n                        self._pause_event.set()\n"),
    ),
    "F3": (
        ("            self.state_machine.handle_command(Command.RESUME)\n            self.training_state.update_state(status=\"Started\")\n", "            if not self.state_machine.handle_command(Command.RESUME):\n                raise RuntimeError(\"Training is not paused\")\n            self.training_state.update_state(status=\"Started\")\n"),
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--fixes", nargs="+", choices=sorted(EDITS), required=True)
    args = parser.parse_args()
    target = args.copy.resolve() / MANAGER
    text = target.read_text(encoding="utf-8")
    print("before", hashlib.sha256(text.encode("utf-8")).hexdigest())
    ok = True
    for fix in args.fixes:
        for old, new in EDITS[fix]:
            count = text.count(old)
            if count != 1:
                print(f"{fix}: target occurs {count} times, not applied: {old[:60]!r}")
                ok = False
                continue
            text = text.replace(old, new, 1)
            print(f"{fix}: applied {old.strip().splitlines()[0][:70]!r}")
    target.write_text(text, encoding="utf-8")
    print("after", hashlib.sha256(text.encode("utf-8")).hexdigest())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
