#!/usr/bin/env python3
"""Lane A: replay the committed editor on the BASE inputs and compare with the head, byte for byte.

Builds a minimal tree (the three files at df21367d + the editor from e2f87aae at util/ad-hoc/, where its
REPO = parents[2] resolves to the tree root), runs it, compares sha256 of each output with the head's file,
runs it a second time (must refuse, and write nothing), then a negative control: a copy of the base register
with ONE expected substring perturbed must make the editor refuse and leave all three files untouched.
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
FILES = {
    "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md": "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md",
    "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md": "JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md",
    "docs/REFERENCE.md": "REFERENCE.md",
}
EDITOR = "2026-09-24_register_round42_second_fixforward.py"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(root, perturb=None):
    if root.exists():
        shutil.rmtree(root)
    for rel, name in FILES.items():
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(S / "base" / name, dst)
    if perturb:
        p = root / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
        t = p.read_text(encoding="utf-8")
        assert t.count(perturb[0]) == 1
        p.write_text(t.replace(perturb[0], perturb[1]), encoding="utf-8")
    ed = root / "util/ad-hoc" / EDITOR
    ed.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(S / "head" / EDITOR, ed)
    return ed


def run(ed):
    r = subprocess.run([sys.executable, str(ed)], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip().split("\n")


root = S / "replay"
ed = build(root)
rc, out = run(ed)
print(f"run 1: rc={rc}; last lines: {out[-4:]}")
print(f"  'ok' substitution lines: {sum(1 for x in out if x.strip().startswith('ok '))}")
for rel, name in FILES.items():
    print(f"  {name}: replay==head {sha(root / rel) == sha(S / 'head' / name)}")
before = {rel: sha(root / rel) for rel in FILES}
rc2, out2 = run(ed)
print(f"run 2: rc={rc2}; message: {out2[-1]}")
print(f"  run 2 wrote nothing: {all(sha(root / rel) == before[rel] for rel in FILES)}")

# negative control: perturb one REG_SUBS 'old' string; the editor must refuse and write nothing
nc = S / "replay_nc"
ed = build(nc, perturb=('so **pick one per package**" (7944)', 'so **pick one per package**" (79444)'))
pre = {rel: sha(nc / rel) for rel in FILES}
rc3, out3 = run(ed)
print(f"negative control: rc={rc3}; message: {out3[-1]}")
print(f"  wrote nothing: {all(sha(nc / rel) == pre[rel] for rel in FILES)}")
shutil.rmtree(root)
shutil.rmtree(nc)
