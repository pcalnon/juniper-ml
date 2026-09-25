#!/usr/bin/env python3
"""Does Appendix E's marker pair survive a revert to the str compare? (read-only; git show only)

Mutant: drop every `.encode("utf-8", "surrogatepass")` call (the natural "simplification" back to the
str compare that raised TypeError), keep comments and the variable name. Check the pair the snapshot
proposes (bare `surrogatepass` + `compare_digest(presented,`) and the r1 literal alternative.
"""
import subprocess

SITES = [
    ("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream", "origin/main", "juniper-service-core/juniper_service_core/security.py"),
    ("/home/pcalnon/Development/python/Juniper/juniper-data", "0bee089e758d0a77b0031555ea865c7417b3013c", "juniper_data/api/security.py"),
    ("/home/pcalnon/Development/python/Juniper/juniper-cascor", "97341680fc7d794f9e2a00a22615126c12cb0358", "src/api/security.py"),
    ("/home/pcalnon/Development/python/Juniper/juniper-canopy", "origin/main", "src/security.py"),
]
PAIR = ("surrogatepass", "compare_digest(presented,")
STRICT = ('encode("utf-8", "surrogatepass")', "compare_digest(presented,")

for repo, ref, path in SITES:
    src = subprocess.run(["git", "-C", repo, "show", f"{ref}:{path}"], capture_output=True, text=True, check=True).stdout
    mutant = src.replace('.encode("utf-8", "surrogatepass")', "")
    # canopy routes through _compare_bytes; its natural revert is dropping the helper at the compare sites
    mutant = mutant.replace("_compare_bytes(api_key)", "api_key").replace("_compare_bytes(candidate)", "candidate")
    print(f"{path} @ {ref[:8]}")
    print(f"   base   pair={all(m in src for m in PAIR)} strict={all(m in src for m in STRICT)}")
    print(f"   mutant pair={all(m in mutant for m in PAIR)} strict={all(m in mutant for m in STRICT)}  (encode calls left: {mutant.count('.encode(')})")
