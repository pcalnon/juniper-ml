#!/usr/bin/env python3
"""Lane B r2: was an n_samples bound available without moving a line? (tests omission 1's premise)

Puts a one-line bound on the formerly blank line 5658 (directly above the n_samples read), keeps the count,
runs the Appendix D harness, and drives 1.5 / 1e8 / 1e19 / 64 through it.
"""
import asyncio
import importlib.util
import re
import resource
import subprocess
import sys
from pathlib import Path

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
S = Path(sys.argv[1])
VENV = sys.argv[2]
REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
lines = (S / "after" / REL).read_text(encoding="utf-8").split("\n")
assert lines[5657] == "" and lines[5658].strip().startswith("n_samples = int(")
lines[5657] = '        if not (type(body.params.get("n_samples", 512)) is int and 1 <= body.params.get("n_samples", 512) <= 1_000_000): raise ProblemException(status=422, title="Request validation failed", detail="n_samples must be an integer from 1 to 1,000,000.", type_="https://errors.example.com/validation-failed")'
doc = S / "primer_bounded.md"
doc.write_text("\n".join(lines), encoding="utf-8")
p = subprocess.run([sys.executable, str(S / "after/util/ad-hoc/2026-08-13_run_primer_examples.py"), "--doc", str(doc), "--venv", VENV], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "TMPDIR": str(S / "tmp"), "HOME": str(Path.home())})
print("harness:", [l for l in p.stdout.split("\n") if " passed" in l or " failed" in l][-1:], "lines:", len(doc.read_text(encoding="utf-8").splitlines()))

src = re.search(r"<!-- example-file: conditional_datasets\.py -->\n```python\n(.*?)\n```", doc.read_text(encoding="utf-8"), re.S).group(1) + "\n"
mp = S / "tmp" / "cd_bounded.py"
mp.write_text(src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("cd_bounded", mp)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
doc.unlink()


async def drive():
    sys.path.insert(0, f"{VENV}/lib/python3.13/site-packages")
    import httpx

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mod.create_app(), raise_app_exceptions=False), base_url="http://t") as c:
        for v in ("64", "1.5", "100000000", "1e19"):
            r = await c.post("/v1/datasets", content=('{"generator": "spiral", "params": {"n_samples": ' + v + "}}").encode(), headers={"Content-Type": "application/json"})
            print(f"  n_samples {v:>10}: {r.status_code} {r.headers.get('content-type')}")


asyncio.run(drive())
mp.unlink()
