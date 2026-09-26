#!/usr/bin/env python3
"""Lane A round 2: replay the corrections editor on e2f87aae's register + primer.

1. Stage e2f87aae's two notes plus 990ef3f9's editor in a scratch repo layout.
2. Run the editor. Compare its output to 990ef3f9's two files byte for byte.
3. Run it again: it must refuse and write nothing.
4. Controls: (a) a perturbed primer line -> must refuse, write nothing;
   (b) a register lacking the PREREQ -> must refuse; (c) a register sub that matches twice -> must refuse.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRI = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
ED = "util/ad-hoc/2026-09-24_register_round42_second_fixforward_corrections.py"


def show(rev: str, rel: str) -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def stage(root: Path, reg: bytes, pri: bytes) -> None:
    if root.exists():
        shutil.rmtree(root)
    (root / "notes").mkdir(parents=True)
    (root / "util/ad-hoc").mkdir(parents=True)
    (root / REG).write_bytes(reg)
    (root / PRI).write_bytes(pri)
    (root / ED).write_bytes(show("990ef3f9", ED))


def run(root: Path, *extra: str) -> "tuple[int, str]":
    p = subprocess.run([sys.executable, str(root / ED), *extra], capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


base_reg, base_pri = show("e2f87aae", REG), show("e2f87aae", PRI)
head_reg, head_pri = show("990ef3f9", REG), show("990ef3f9", PRI)
print("base reg", sha(base_reg), "base primer", sha(base_pri))
print("head reg", sha(head_reg), "head primer", sha(head_pri))

root = S / "replay"
stage(root, base_reg, base_pri)
rc, out = run(root)
print("--- run 1 rc", rc)
print(out)
r1_reg, r1_pri = (root / REG).read_bytes(), (root / PRI).read_bytes()
print("run1 reg == head:", r1_reg == head_reg, sha(r1_reg))
print("run1 primer == head:", r1_pri == head_pri, sha(r1_pri))

rc, out = run(root)
print("--- run 2 rc", rc)
print(out)
print("run2 wrote nothing:", (root / REG).read_bytes() == r1_reg and (root / PRI).read_bytes() == r1_pri)

# Control (a): perturb one primer line the editor names (9943)
lines = base_pri.decode("utf-8").split("\n")
lines[9943 - 1] = lines[9943 - 1] + " "
stage(root, base_reg, "\n".join(lines).encode("utf-8"))
before = ((root / REG).read_bytes(), (root / PRI).read_bytes())
rc, out = run(root)
print("--- control (a) perturbed primer 9943: rc", rc, "|", out.splitlines()[-1] if out else "")
print("control (a) wrote nothing:", ((root / REG).read_bytes(), (root / PRI).read_bytes()) == before)

# Control (b): register without PREREQ
reg_b = base_reg.decode("utf-8").replace("a second fix-forward the last 5", "a second fix-forward the last five")
stage(root, reg_b.encode("utf-8"), base_pri)
before = ((root / REG).read_bytes(), (root / PRI).read_bytes())
rc, out = run(root)
print("--- control (b) no PREREQ: rc", rc, "|", out.splitlines()[-1] if out else "")
print("control (b) wrote nothing:", ((root / REG).read_bytes(), (root / PRI).read_bytes()) == before)

# Control (c): duplicate a sub's old text -> count 2
old = "since four juniper-ml notes link into cascor."
reg_c = base_reg.decode("utf-8") + "\n" + old + "\n"
stage(root, reg_c.encode("utf-8"), base_pri)
before = ((root / REG).read_bytes(), (root / PRI).read_bytes())
rc, out = run(root)
print("--- control (c) duplicated sub text: rc", rc, "|", out.splitlines()[-1] if out else "")
print("control (c) wrote nothing:", ((root / REG).read_bytes(), (root / PRI).read_bytes()) == before)

# Control (d): a --dry-run on base writes nothing
stage(root, base_reg, base_pri)
rc, out = run(root, "--dry-run")
print("--- control (d) dry run: rc", rc, "|", out.splitlines()[-1] if out else "")
print("control (d) wrote nothing:", (root / REG).read_bytes() == base_reg and (root / PRI).read_bytes() == base_pri)
shutil.rmtree(root)
