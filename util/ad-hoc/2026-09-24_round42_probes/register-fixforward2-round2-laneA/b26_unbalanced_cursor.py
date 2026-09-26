#!/usr/bin/env python3
"""Lane A round 2: an UNBALANCED 10,000-deep cursor through the toy's decode_cursor, main vs head.
Run with the pinned venv's python."""
import base64
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
for label, p in (("main", S / "main/notes/primer_df21367d.md"), ("head", S / "head/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")):
    src = re.search(r"<!-- example-file: conditional_datasets\.py -->\n```python\n(.*?)\n```", p.read_text(encoding="utf-8"), re.S).group(1) + "\n"
    d = tempfile.mkdtemp()
    (Path(d) / "cd.py").write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"cd_{label}", Path(d) / "cd.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    shutil.rmtree(d)
    for name, raw in (("unbalanced [ x10000", b"[" * 10000), ("balanced 10000", b"[" * 10000 + b"]" * 10000)):
        cur = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        try:
            m.decode_cursor(cur)
            out = "decoded?!"
        except m.ProblemException as e:
            out = f"ProblemException {e.status}"
        except RecursionError:
            out = "RecursionError (escapes -> 500)"
        except Exception as e:
            out = f"{type(e).__name__}"
        print(f"{label}: {name:22} -> {out}")
