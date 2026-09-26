"""Lane B (r42d): apply MX10 (the create's re-check outside the file lock) to a copied tree."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from my_mutants import BASE, MUTANTS  # noqa: E402

tree = Path(sys.argv[1])
_why, edits = MUTANTS["MX10"]
for rel, old, new in edits:
    assert rel == BASE
    p = tree / rel
    t = p.read_text()
    assert t.count(old) == 1
    p.write_text(t.replace(old, new))
print("MX10 applied to", tree)
