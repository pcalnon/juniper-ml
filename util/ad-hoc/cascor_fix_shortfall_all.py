#!/usr/bin/env python3
"""
Repair the juniper-cascor constants drift that cascor#633 left on `main`: export the four
SHORTFALL constants from the module's REAL ``__all__``, and delete the stray second one.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off (applied once to the cascor worktree named below)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#633 (which introduced the drift); the round-38 handoff
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md;
         memory reference_codeql_unused_global_cascor (declaring __all__ is the sanctioned fix)

The defect, found by round-2 lane A on 2026-09-09
------------------------------------------------
`CI — juniper-cascor-model` has been RED on cascor `main` since `44dafe0` (cascor#633). Its
`tests/test_drift.py` requires `juniper-cascor-model/cascor_constants/` to be byte-identical to
`src/cascor_constants/`, and the two diverged by a seven-line block:

    __all__ = [ ...the four _PROJECT_API_SHORTFALL_* names... ]

present mid-file in the model copy only. That block was a CodeQL `py/unused-global-variable`
remedy, and it is wrong twice over. It broke the mirror; and it does not even work, because the
module already ends with its own full `__all__`, so the mid-file binding is REPLACED at import
time by the one at the end -- which never listed the four new names.

The repair, applied to BOTH copies identically:
  * delete the stray mid-file ``__all__``;
  * add the four names to the real ``__all__`` at the end of the file, in its existing
    alphabetical order (between ``_PROJECT_API_SERVICE_TERMINATION_TIMEOUT`` and
    ``_PROJECT_API_TLS_MIN_VERSION_DEFAULT``).

Nothing does ``from ... import *`` on this module (`constants_api/__init__.py` lists every name
explicitly), so ``__all__`` is documentation and a CodeQL signal here, never behaviour.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--mirror-shortfall-constants-all--20260909-1600--3de89b11")
SRC = W / "src/cascor_constants/constants_api/constants_api_defaults.py"
MODEL = W / "juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py"

STRAY = (
    "\n__all__ = [\n"
    '    "_PROJECT_API_SHORTFALL_REFUSAL_TOKEN",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER",\n'
    "]\n"
)
ANCHOR = '    "_PROJECT_API_SERVICE_TERMINATION_TIMEOUT",\n    "_PROJECT_API_TLS_MIN_VERSION_DEFAULT",\n'
ADDITION = (
    '    "_PROJECT_API_SERVICE_TERMINATION_TIMEOUT",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST",\n'
    '    "_PROJECT_API_SHORTFALL_REFUSAL_TOKEN",\n'
    '    "_PROJECT_API_TLS_MIN_VERSION_DEFAULT",\n'
)


def fix(path: Path) -> None:
    text = path.read_text()
    if STRAY in text:
        text = text.replace(STRAY, "", 1)
        print(f"  {path.name}: removed the stray mid-file __all__")
    if text.count(ANCHOR) != 1:
        sys.exit(f"FAIL: __all__ anchor found {text.count(ANCHOR)} times in {path}")
    text = text.replace(ANCHOR, ADDITION, 1)
    path.write_text(text)
    print(f"  {path.name}: four SHORTFALL names added to the real __all__")


for target in (SRC, MODEL):
    print(target.parts[-4])
    fix(target)

if SRC.read_bytes() != MODEL.read_bytes():
    sys.exit("FAIL: the two copies are still not byte-identical")
print("both copies byte-identical")

names = [line.strip().strip('",') for line in SRC.read_text().splitlines() if line.startswith('    "_PROJECT_API_')]
if names != sorted(names):
    first = next(i for i, (a, b) in enumerate(zip(names, sorted(names))) if a != b)
    sys.exit(f"FAIL: __all__ is no longer sorted, first divergence at {names[first]!r}")
print(f"__all__ sorted, {len(names)} names")

out = subprocess.run(
    ["/opt/miniforge3/envs/JuniperCascor1/bin/python", "-c", "import ast,sys;m=ast.parse(open(sys.argv[1]).read());print(sum(1 for n in m.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='__all__' for t in n.targets)))", str(SRC)],
    capture_output=True, text=True, check=True,
)
print(f"__all__ bindings in the file: {out.stdout.strip()} (must be 1)")
