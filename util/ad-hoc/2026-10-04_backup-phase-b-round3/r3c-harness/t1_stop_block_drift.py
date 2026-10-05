#!/usr/bin/env python3
"""Lane C round 3: the STOP block is replaced whole, between its first line and STOP_END, without checking
what lies between. An item added to the block upstream is discarded silently."""
import importlib.util

spec = importlib.util.spec_from_file_location("atk", "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/bin/t1_gate_attacks.py")
atk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atk)
atk.OUT.mkdir(parents=True, exist_ok=True)
start = "> **STOP — §8 is not executable as written (rounds 4–8, 2026-09-24).**"
i = atk.STAGED.index(start)
j = atk.STAGED.index("\n", i) + 1
marker = "> 6. **UPSTREAM-ADDED STOP ITEM (scratch marker).** A defect recorded on main after the frozen set.\n"
d = atk.STAGED[:j] + marker + atk.STAGED[j:]
r, wrote = atk.run_case("g1_stop_block_item_added_upstream", d, atk.SCRIPT, expect_write=True)
out = (atk.OUT / "g1_stop_block_item_added_upstream" / atk.D_REL).read_text(encoding="utf-8")
print("upstream-added STOP item survives in the written design:", "UPSTREAM-ADDED STOP ITEM" in out)
