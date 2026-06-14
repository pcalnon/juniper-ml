#!/usr/bin/env python3
# Ad-hoc verifier for finding P6-CEIL-04: check K&R 2312.09048v2 theorem quotes.
# Single-use; safe to delete. Author: adversarial-verifier session 2026-06-12.
import subprocess

PDF = "/home/pcalnon/Development/python/Juniper/juniper-ml/papers/On The Expressivity of Recurrent Neural Cascades-2312.09048v2.pdf"

# Raw stream (no -layout) so character offsets are meaningful.
txt = subprocess.check_output(["pdftotext", PDF, "-"], text=True)
print("LEN", len(txt))

needles = [
    "negative weight that implements",
    "not group-free",
    "second-order neuron",
    "the case where",
    "cyclic group of order two",
    "group of order two",
    "RNC consisting of a single",
]
for n in needles:
    idx = txt.find(n)
    print("\n=== NEEDLE", repr(n), "idx", idx, "===")
    if idx >= 0:
        print(txt[max(0, idx - 350):idx + 350])
