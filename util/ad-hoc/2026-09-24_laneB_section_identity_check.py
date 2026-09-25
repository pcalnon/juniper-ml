"""Lane B probe: is main's [0.16.0] CHANGELOG section identical to the v0.16.0 tag's?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (written by validation lane B, container-registry session, 2026-09-24)
Created: 2026-09-24
Status: ad-hoc — investigation (provenance copy of a validation-lane probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#438/#439. An independent re-derivation of what
         util/ad-hoc/2026-09-24_changelog_section_identity.py reports (it does not use that script).

Paths are relative to the lane's scratch directory, which was NOT retained. To re-run, save the four
CHANGELOG.md versions beside this file: data0160/CHANGELOG.md (tag v0.16.0), cl_theirs.md
(0f0f7e0e), cl_merge.md (322135bd) and cl_base.md (1afc3484).

Independent re-derivation (does not use the untracked juniper-ml ad-hoc script).
Section = from the '## [0.16.0]' heading up to (not including) the next '## [' heading.
Prints line counts and sha256 prefixes for a few newline conventions. Ephemeral scratch probe.
"""

import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def section(path: str, version: str) -> list[str]:
    lines = open(path, encoding="utf-8").read().split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith(f"## [{version}]"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## ["))
    return lines[start:end]


for label, path in (("tag v0.16.0", "data0160/CHANGELOG.md"), ("main 0f0f7e0e", "cl_theirs.md"), ("pr439 head 322135bd", "cl_merge.md"), ("base 1afc3484", "cl_base.md")):
    sec = section(os.path.join(HERE, path), "0.16.0")
    variants = {
        "joined": "\n".join(sec),
        "joined+nl": "\n".join(sec) + "\n",
        "stripped": "\n".join(sec).rstrip("\n"),
        "stripped+nl": "\n".join(sec).rstrip("\n") + "\n",
    }
    shas = {k: hashlib.sha256(v.encode("utf-8")).hexdigest()[:12] for k, v in variants.items()}
    print(f"{label:22s} lines={len(sec):4d} nonblank-trailing-trimmed={len('\n'.join(sec).rstrip(chr(10)).split(chr(10))):4d} {shas}")
