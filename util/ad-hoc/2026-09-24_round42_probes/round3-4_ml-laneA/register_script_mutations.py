"""Lane A: mutation-check register_open_set.py and register_status_crosscheck.py on a scratch copy
of the register (origin/main == b8b24b41's blob). Each mutation edits ONE row; both scripts are run
from a scratch tree laid out like the repo (the crosscheck resolves the register via __file__)."""

import shutil
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
ML = S / "ml-main"
T = S / "regmut"
REG_REL = Path("notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")
if T.exists():
    shutil.rmtree(T)
(T / "notes").mkdir(parents=True)
(T / "util/ad-hoc").mkdir(parents=True)
for name in ("register_open_set.py", "register_status_crosscheck.py"):
    shutil.copy2(ML / "util/ad-hoc" / name, T / "util/ad-hoc" / name)
original = (ML / REG_REL).read_text(encoding="utf-8")
lines = original.split("\n")


def row_index(prefix):
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    return hits


def run(text):
    (T / REG_REL).write_text(text, encoding="utf-8")
    a = subprocess.run([sys.executable, "util/ad-hoc/register_open_set.py"], cwd=T, capture_output=True, text=True).stdout.splitlines()[0]
    b = subprocess.run([sys.executable, "util/ad-hoc/register_status_crosscheck.py"], cwd=T, capture_output=True, text=True)
    verdict = b.stdout.strip().splitlines()[-1] if b.stdout.strip() else b.stderr.strip()[-120:]
    return a, verdict, b.returncode


print("control                              :", run(original))

# M1: un-FIX a fixed id's section-4 row (APD-CASCOR-005, first row = section 4).
i = row_index("| APD-CASCOR-005 ")[0]
m1 = lines.copy(); assert "**FIXED" in m1[i]; m1[i] = m1[i].replace("**FIXED", "**PENDING", 1)
print("M1 un-FIX CASCOR-005 section-4 row   :", run("\n".join(m1)))

# M2: mark an open id FIXED in its status cell (APD-ECO-008 section-4 row) without the other touches.
i = row_index("| APD-ECO-008 ")[0]
m2 = lines.copy(); assert "**FIXED" not in m2[i]
cells = m2[i].split("|"); cells[2] = " **FIXED (mutation)** —" + cells[2]; m2[i] = "|".join(cells)
print("M2 FIX ECO-008 status cell only      :", run("\n".join(m2)))

# M3: put the token in a NON-status cell of an open row (the anchors cell).
m3 = lines.copy(); cells = m3[i].split("|"); cells[4] = cells[4] + " **FIXED-looking text "; m3[i] = "|".join(cells)
print("M3 token in ECO-008 anchors cell     :", run("\n".join(m3)))

# M4: add a phantom open row to a section-4 table.
m4 = lines.copy(); m4.insert(i + 1, "| APD-ECO-099 | phantom open row | L | x | — | Low |")
print("M4 phantom open row                  :", run("\n".join(m4)))
