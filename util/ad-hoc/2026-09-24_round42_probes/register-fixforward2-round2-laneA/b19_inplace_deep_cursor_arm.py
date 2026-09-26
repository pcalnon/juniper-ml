#!/usr/bin/env python3
"""Lane A round 2: can the primer's own suite pin the RecursionError catch WITHOUT moving a line?

The stated omission (and the probe's docstring) say the suite has "no line to test without moving one". Build a
same-line deep-cursor arm into test_a_garbage_cursor_is_a_problem_not_a_500 (lines 6084, 6086, 6087), the way
the correction itself added bad_str on 6117/6120, then run the Appendix D harness:
  (1) head + arm                              -> must PASS (arm is valid, line count unchanged)
  (2) head + arm + RecursionError catch reverted -> must be CAUGHT (arm discriminates)
"""
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
HEAD = S / "head"
VENV = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv"
PRI = HEAD / "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
HARNESS = HEAD / "util/ad-hoc/2026-08-13_run_primer_examples.py"
ENV = {"TMPDIR": str(S / "tmp"), "PATH": "/usr/bin:/bin"}

EXPECT = {
    6084: '        response = await client.get("/v1/datasets?cursor=not-a-real-cursor")',
    6086: "    assert response.status_code == 400",
    6087: '    assert response.headers["content-type"].startswith("application/problem+json")',
    5600: "    except (ValueError, KeyError, TypeError, RecursionError, binascii.Error) as exc:  # RecursionError: a cursor nested past the limit",
}
ARM = {
    6084: '        response, deep = await client.get("/v1/datasets?cursor=not-a-real-cursor"), await client.get("/v1/datasets?cursor=" + __import__("base64").urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode())  # nested past the recursion limit',
    6086: "    assert response.status_code == deep.status_code == 400",
    6087: '    assert all(r.headers["content-type"].startswith("application/problem+json") for r in (response, deep))',
}
REVERT = {5600: "    except (ValueError, KeyError, TypeError, binascii.Error) as exc:"}

base = PRI.read_text(encoding="utf-8").split("\n")
for n, t in EXPECT.items():
    assert base[n - 1] == t, (n, base[n - 1])


def run(edits, name):
    lines = list(base)
    for n, t in edits.items():
        lines[n - 1] = t
    assert len(lines) == len(base)
    doc = S / "mut" / f"{name}.md"
    doc.parent.mkdir(exist_ok=True)
    doc.write_text("\n".join(lines), encoding="utf-8")
    p = subprocess.run(["python3", str(HARNESS), "--doc", str(doc), "--venv", VENV], capture_output=True, text=True, env=ENV)
    tail = [ln for ln in p.stdout.split("\n") if " passed" in ln or " failed" in ln]
    doc.unlink()
    print(f"{name}: rc={p.returncode} -- {tail[-1].strip() if tail else p.stdout[-300:]}")


run(ARM, "head_plus_inplace_arm")
run({**ARM, **REVERT}, "head_plus_arm_and_recursion_revert")
