"""Lane B: materialise ONE named mutant from mutants.py as a persistent tree (mut-keep/<name>)."""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mutants  # noqa: E402

name = sys.argv[1]
work = mutants.LANE / "mut-keep" / name
if work.exists():
    shutil.rmtree(work)
shutil.copytree(mutants.SRC, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".hypothesis", ".benchmarks", "data"))
for rel, find, repl in mutants.MUTATIONS[name]:
    p = work / rel
    t = p.read_text(encoding="utf-8")
    assert t.count(find) == 1, (rel, t.count(find))
    p.write_text(t.replace(find, repl), encoding="utf-8")
print(work)
