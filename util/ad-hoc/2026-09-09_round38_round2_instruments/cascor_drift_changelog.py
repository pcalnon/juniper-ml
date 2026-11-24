#!/usr/bin/env python3
"""Append the drift-repair entry at the END of cascor's [Unreleased] ### Fixed block.

Placed last on purpose: another session is writing to the same section concurrently, and an
insertion at the section TOP conflicts with theirs in the 3-way merge while one at the end does
not (the round-38 handoff's §5.2 trap).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — investigation (round-2 validation of the round-38 defect-register handoff)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: reports/2026-09-09_round-38-consensus/; see README.md in this directory for what each
         script settled and what it needs on disk to run.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--mirror-shortfall-constants-all--20260909-1600--3de89b11")
CHANGELOG = W / "CHANGELOG.md"

ENTRY = """- **`CI — juniper-cascor-model` was RED on `main`, and the fix that broke it did not work
  either.** The four `_PROJECT_API_SHORTFALL_*` constants added on 2026-09-09 were never listed in
  `cascor_constants/constants_api/constants_api_defaults.py`'s `__all__`, so CodeQL reported them as
  unused globals; the remedy added a **second** `__all__` in the middle of the file, and only to the
  `juniper-cascor-model/` mirror. That is wrong twice. It broke `tests/test_drift.py`, which requires
  the extracted tree to be byte-identical to `src/` — red on `main` from `44dafe0` onward. And it had
  no effect on the finding it was meant to silence, because the module already ends with its own
  complete `__all__`, so the mid-file binding is simply replaced at import time by the one at the
  end, which still did not name the four constants. The stray block is gone and the four names are
  in the real `__all__`, in its existing alphabetical order, in **both** copies. Nothing star-imports
  this module (`constants_api/__init__.py` names every symbol explicitly), so `__all__` here is
  documentation and a CodeQL signal, never behaviour: no import changes. Verified by the drift suite
  (3 passed, previously 1 failed / 2 passed) and by `test_allow_truncated_datasets.py` (28 passed).

"""

ANCHOR = "\n### Changed\n"

text = CHANGELOG.read_text()
head, sep, tail = text.partition("### Fixed\n")
if not sep:
    sys.exit("FAIL: no '### Fixed' block in CHANGELOG.md")
# End of the Fixed block = the next '### ' heading after it, or the next '## [' release heading.
rest = tail
cut = len(rest)
for marker in ("\n### ", "\n## ["):
    at = rest.find(marker)
    if at != -1:
        cut = min(cut, at + 1)
block, remainder = rest[:cut], rest[cut:]
if not block.endswith("\n\n"):
    sys.exit(f"FAIL: unexpected end of the Fixed block: {block[-40:]!r}")
CHANGELOG.write_text(head + sep + block + ENTRY + remainder)
print("entry appended at the END of [Unreleased] > ### Fixed")

diff = subprocess.run(["git", "-C", str(W), "diff", "--stat", "--", "CHANGELOG.md"], capture_output=True, text=True, check=True)
print(diff.stdout.strip())
