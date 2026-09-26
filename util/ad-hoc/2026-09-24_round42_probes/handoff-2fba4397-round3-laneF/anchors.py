"""Appendix E anchors: where the pair's literals and the bare word sit in each fork site."""
from pathlib import Path

D = Path(__file__).resolve().parent
SITES = {
    "service-core juniper_service_core/security.py @ml main": D / "sc_security.py",
    "canopy src/security.py @canopy main": D / "canopy_security.py",
    "data#440 juniper_data/api/security.py @0bee089e": D / "data440_security.py",
    "cascor#689 src/api/security.py @97341680": D / "cascor689_security.py",
}
NEEDLES = ('encode("utf-8", "surrogatepass")', "surrogatepass", "compare_digest(presented,", ".encode(")
for label, p in SITES.items():
    lines = p.read_text(encoding="utf-8").split("\n")
    print("==", label, f"({len(lines)} lines)")
    for n in NEEDLES:
        hits = [i + 1 for i, line in enumerate(lines) if n in line]
        print(f"   {n!r:40} lines {hits}")
    for i, line in enumerate(lines):
        if "surrogatepass" in line or "compare_digest(" in line:
            print(f"   {i + 1:4}: {line.rstrip()[:130]}")
