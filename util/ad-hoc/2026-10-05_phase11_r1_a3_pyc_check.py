# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/pyc_check.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Read-only: parse a .pyc header and compare its SHIM constant with a source file's SHIM."""
import ast
import datetime
import hashlib
import marshal
import os
import struct
import sys

pyc, src = sys.argv[1], sys.argv[2]
with open(pyc, "rb") as fh:
    b = fh.read()
flags = struct.unpack("<I", b[4:8])[0]
mtime = struct.unpack("<I", b[8:12])[0]
size = struct.unpack("<I", b[12:16])[0]
print("pyc", pyc.split("/")[-1], "flags", flags, "recorded src mtime", datetime.datetime.fromtimestamp(mtime).isoformat(), "recorded src size", size)
code = marshal.loads(b[16:])
consts = [c for c in code.co_consts if isinstance(c, str) and "window.__f058v2" in c]
with open(src, encoding="utf-8") as fh:
    s = fh.read()
tree = ast.parse(s)
shim_src = next(n.value.value for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SHIM")
print("SHIM consts in pyc:", len(consts), "sha", [hashlib.sha256(c.encode()).hexdigest()[:16] for c in consts])
print("SHIM in source sha", hashlib.sha256(shim_src.encode()).hexdigest()[:16], "equal:", bool(consts) and consts[0] == shim_src)
# Also compare the full code object to a fresh compile of the source.
fresh = compile(s, src, "exec")
print("co_code equal to fresh compile of frozen source:", fresh.co_code == code.co_code, "; consts equal (strings):", [c for c in fresh.co_consts if isinstance(c, str)] == [c for c in code.co_consts if isinstance(c, str)])
st = os.stat(src)
print("frozen source size", st.st_size)
