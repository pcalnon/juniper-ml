#!/usr/bin/env python3
"""2026-09-09_required_check_comment_drift.py -- comments that call a REQUIRED check advisory.

Project: juniper-ml
Sub-Project: CI documentation integrity
Application: ad-hoc analysis
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`.github/workflows/ci.yml` described `Sequence Safety` as "ADVISORY, NOT required" while the
branch ruleset listed it among the required contexts. A reader who trusts that comment takes
a red check for non-blocking and waits for a merge that cannot happen -- which is how it was
found, on juniper-ml#1837.

It is not a one-off. Both instances share a shape: a check is wired as advisory, the comment
describes the promotion as a FUTURE step ("so the Overtoad can later mark it REQUIRED"), the
promotion then happens in the ruleset, and nobody edits the comment. The plan and the
outcome are the same sentence, so the text stays plausible while becoming false. The
Release-Train Archive Guard block even contradicts itself two lines apart -- "can later mark
it REQUIRED" above, "now that the check is REQUIRED" below.

So this asks the question directly, for every required context: does the workflow that
defines it describe it as advisory or not-yet-required?

The ruleset is the authority. A comment is never evidence about enforcement.

KNOWN FALSE POSITIVE -- THIS IS A CANDIDATE FINDER, NOT A GATE

A comment that CORRECTS the drift necessarily QUOTES the wrong phrasing, so it matches too.
Both hits on the first run were this shape -- the two fixes themselves. There is no reliable
way to tell "this check is advisory" from "this comment used to say the check was advisory"
by pattern, so every hit needs a human read.

That is why it prints CANDIDATE and exits 0 on hits: a gate that cries wolf on its own fix
would be turned off within a week, and the drift it looks for is rare enough that a periodic
sweep is the right cadence. Exit 2 -- the ruleset unreadable -- is the only failure, because
a sweep that could not enumerate the required contexts has measured nothing.

Usage:
    python3 util/ad-hoc/2026-09-09_required_check_comment_drift.py [--ruleset ID]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
from pathlib import Path

WORKFLOWS = Path(".github/workflows")
DEFAULT_RULESET = "13805432"

#: Phrases that assert a check does not block a merge.
ADVISORY_RE = re.compile(
    r"(NOT\s+required|not\s+yet\s+required|advisory,\s*not\s+required"
    r"|can\s+later\s+mark\s+it\s+REQUIRED|later\s+be\s+marked\s+REQUIRED"
    r"|ADVISORY,\s*NOT)",
    re.IGNORECASE,
)


def required_contexts(ruleset: str) -> list:
    res = subprocess.run(  # nosec B603 -- fixed argv
        ["gh", "api", f"repos/pcalnon/juniper-ml/rulesets/{ruleset}"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"could not read ruleset {ruleset}: {res.stderr.strip()[:200]}", file=sys.stderr)
        raise SystemExit(2)
    doc = json.loads(res.stdout)
    for rule in doc.get("rules", []):
        if rule.get("type") == "required_status_checks":
            return [c["context"] for c in rule["parameters"]["required_status_checks"]]
    return []


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ruleset", default=DEFAULT_RULESET)
    args = ap.parse_args(argv)

    contexts = required_contexts(args.ruleset)
    if not contexts:
        print("ruleset lists NO required contexts -- refusing to report clean", file=sys.stderr)
        return 2
    print(f"{len(contexts)} required context(s) in ruleset {args.ruleset}\n")

    findings = []
    for wf in sorted(WORKFLOWS.glob("*.yml")):
        lines = wf.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            if not line.lstrip().startswith("#"):
                continue
            if not ADVISORY_RE.search(line):
                continue
            # Which required context does this comment block belong to? Look for a
            # `name:` of a required context within the following 60 lines.
            window = "\n".join(lines[i:i + 60])
            for ctx in contexts:
                if re.search(rf"name:\s*{re.escape(ctx)}\s*$", window, re.MULTILINE):
                    # Does the surrounding block read as a CORRECTION rather than a claim?
                    block = "\n".join(lines[max(0, i - 12):i + 12])
                    corrective = bool(re.search(
                        r"used to say|stopped being true|has since|promotion happened"
                        r"|which the escape-hatch|Read the ruleset, not",
                        block, re.IGNORECASE))
                    findings.append((str(wf), i + 1, ctx, line.strip()[:100], corrective))
                    break

    for wf, lineno, ctx, text, corrective in findings:
        label = "LIKELY-CORRECTION" if corrective else "CANDIDATE"
        print(f"{label} {wf}:{lineno}")
        print(f"   required context : {ctx}")
        print(f"   comment says     : {text}")
        print()

    likely = sum(1 for f in findings if f[4])
    if findings:
        print(f"{len(findings)} hit(s): {likely} read as corrections, "
              f"{len(findings) - likely} need adjudication.")
        print("Adjudicate by hand -- a correction quotes the wrong phrasing and matches too.")
    else:
        print("no comment describes a required check as advisory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
