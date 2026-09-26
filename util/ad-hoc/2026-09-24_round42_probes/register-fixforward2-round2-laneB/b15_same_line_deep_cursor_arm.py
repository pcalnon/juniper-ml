#!/usr/bin/env python3
"""Lane B r2: can the primer's OWN suite pin the RecursionError catch without moving a line?

Rewrites two existing lines of test_a_garbage_cursor_is_a_problem_not_a_500 in place (6084 fetches a second,
10,000-deep cursor on the same line; 6086 asserts both are 400), keeps the line count, and runs the Appendix D
harness on (a) that primer and (b) that primer with line 5600's RecursionError catch reverted.

Usage: python3 b15_same_line_deep_cursor_arm.py <laneB dir> <venv>
"""
import subprocess
import sys
from pathlib import Path

S = Path(sys.argv[1])
VENV = sys.argv[2]
REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
lines = (S / "after" / REL).read_text(encoding="utf-8").split("\n")
n_before = len(lines)

OLD_6084 = '        response = await client.get("/v1/datasets?cursor=not-a-real-cursor")'
OLD_6086 = "    assert response.status_code == 400"
assert lines[6083] == OLD_6084 and lines[6085] == OLD_6086, (lines[6083], lines[6085])
lines[6083] = '        response, deep = await client.get("/v1/datasets?cursor=not-a-real-cursor"), await client.get("/v1/datasets", params={"cursor": __import__("base64").urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode()})  # nested past the recursion limit'
lines[6085] = "    assert response.status_code == 400 == deep.status_code"
assert len(lines) == n_before

armed = S / "primer_armed.md"
armed.write_text("\n".join(lines), encoding="utf-8")
reverted = list(lines)
assert "RecursionError" in reverted[5599]
reverted[5599] = "    except (ValueError, KeyError, TypeError, binascii.Error) as exc:"
rev = S / "primer_armed_5600_reverted.md"
rev.write_text("\n".join(reverted), encoding="utf-8")

for label, doc in (("armed, head code", armed), ("armed, 5600 reverted", rev)):
    p = subprocess.run([sys.executable, str(S / "after/util/ad-hoc/2026-08-13_run_primer_examples.py"), "--doc", str(doc), "--venv", VENV], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "TMPDIR": str(S / "tmp"), "HOME": str(Path.home())})
    tail = [l for l in p.stdout.split("\n") if " passed" in l or " failed" in l]
    print(f"{label:24} rc={p.returncode} {tail[-1].strip() if tail else ''} (lines {len(doc.read_text(encoding='utf-8').splitlines())})")
armed.unlink()
rev.unlink()
