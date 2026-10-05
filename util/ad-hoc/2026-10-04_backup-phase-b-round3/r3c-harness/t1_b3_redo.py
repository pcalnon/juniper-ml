#!/usr/bin/env python3
"""Lane C round 3: redo of attack b3 (a prose edit that ADDS a fence), with old not a substring of new."""
import importlib.util

spec = importlib.util.spec_from_file_location("atk", "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/bin/t1_gate_attacks.py")
atk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atk)
atk.OUT.mkdir(parents=True, exist_ok=True)
b3 = atk.append_edits(atk.SCRIPT, "edit('prose edit that adds a fence', 'Require exit 0: it is', '```text\\nnew fence\\n```\\n\\nRequire exit zero: it is')")
atk.run_case("b3b_prose_edit_adds_a_fence", atk.STAGED, b3)
# an indented fence added inside a list item (the declared fence's own indentation)
b5 = atk.append_edits(atk.SCRIPT, "edit('prose edit that adds an indented fence', '   Require exit 0: it is', '   ```text\\n   new fence\\n   ```\\n\\n   Require exit zero: it is')")
atk.run_case("b5_prose_edit_adds_an_indented_fence", atk.STAGED, b5)
