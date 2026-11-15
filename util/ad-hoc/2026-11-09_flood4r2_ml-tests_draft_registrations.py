"""
Extract each flood-4 round-2 ml-tests draft's own registration text into a draft wiring spec.

Reads <scratch>/own/own-<N>.diff.txt (2026-11-09_flood4r2_ml-tests_survey.py) and collects, per new
suite: the comment lines the draft added above its ci.yml invocation, the comment it added above its
main-verify.yml invocation (and whether it added one at all), and its docs/REFERENCE.md Test Suite
Reference entry. Writes <scratch>/spec_draft.json. The spec is then reviewed and corrected by hand
(each description re-derived) before 2026-11-09_flood4r2_ml-tests_wire.py consumes it; this script
never touches the registration files.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_draft_registrations.py --scratch <dir> N:suite [N:suite ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_wire_ml_tests.py (the spec format it feeds)
"""

import argparse
import json
import re
import sys
from pathlib import Path

_FILE_RE = re.compile(r"(?m)^(?=diff --git )")


def _sections(diff: str) -> dict:
    out = {}
    for part in _FILE_RE.split(diff):
        m = re.match(r"diff --git a/(\S+) b/", part)
        if m:
            out[m.group(1)] = part
    return out


def _added_block(section: str, suite: str) -> tuple:
    """Comment lines added directly above ``python3 -m unittest -v <suite>``, and whether the invocation was added."""
    added = [ln[1:] for ln in section.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    for i, ln in enumerate(added):
        if ln.strip() == f"python3 -m unittest -v {suite}":
            comments = []
            j = i - 1
            while j >= 0 and added[j].strip().startswith("#"):
                comments.insert(0, added[j].strip()[1:].strip())
                j -= 1
            return True, comments
    return False, []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("items", nargs="+")
    args = ap.parse_args()
    spec = []
    for item in args.items:
        n, suite = item.split(":", 1)
        diff = (Path(args.scratch) / "own" / f"own-{int(n)}.diff.txt").read_text(encoding="utf-8")
        secs = _sections(diff)
        ci_added, ci_comments = _added_block(secs.get(".github/workflows/ci.yml", ""), suite)
        mv_added, mv_comments = _added_block(secs.get(".github/workflows/main-verify.yml", ""), suite)
        desc = ""
        ref = secs.get("docs/REFERENCE.md", "")
        head = f"- `{suite}`"
        for ln in ref.splitlines():
            body = ln[1:].lstrip() if ln.startswith("+") and not ln.startswith("+++") else ""
            if body.startswith(head):
                rest = body[len(head) :]
                desc = rest.split(" -- ", 1)[1] if " -- " in rest else rest.strip()
        spec.append({"pr": int(n), "test": suite, "ci_added": ci_added, "ci_comment": "\n".join(ci_comments), "mv_added": mv_added, "mv_comment": "\n".join(mv_comments), "desc": desc})
        print(f"#{n} {suite}: ci={ci_added} ({len(ci_comments)} comment lines) mv={mv_added} desc={'yes' if desc else 'NO'}")
    with open(Path(args.scratch) / "spec_draft.json", "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
