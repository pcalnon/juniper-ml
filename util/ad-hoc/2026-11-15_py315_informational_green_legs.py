#!/usr/bin/env python3
"""Make a workflow job's informational Python 3.15 leg conclude GREEN and report its failures as a warning instead.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- migration (phase 1 of the Python 3.15 migration, follow-up to juniper-ml#2567)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (added the legs); the Overtoad's report of 2026-11-15:
         "tests run using python3.15 are supposed to produce an informational message without affecting the ability
         of code to commit, push, PR, or merge"

Why this exists
---------------
Phase 1 gave each 3.15 leg a job-level ``continue-on-error: ${{ matrix.experimental == true }}``. That keeps every
gate's ``needs.<job>.result`` at ``success`` (measured, juniper-data#538), but the leg's own check still concludes
``failure``: every PR shows a red X and "Some checks were not successful", ``mergeStateStatus`` reads UNSTABLE, and
``gh pr checks`` and any tool reading all checks treat the PR as failing. An informational check must not look like
a failure. This script gives EVERY step of the job an ``id`` and the same ``continue-on-error`` expression, so on the
3.15 leg a failing step no longer fails the job, and appends one step that reports each failed step as a warning
annotation and a job-summary table. The blocking legs are untouched: the expression is false there.

The edit is textual (a yaml round-trip would drop the files' comments) and is checked by parsing the result: same
steps in the same order, plus the report step; every step carries the expression; ids unique.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_informational_green_legs.py <workflow.yml> <job-id> [<job-id> ...] [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

COE = "continue-on-error: ${{ matrix.experimental == true }}"
REPORT_NAME = "Report the informational Python 3.15 result"
REPORT_STEP = """\
      - name: Report the informational Python 3.15 result
        # Python 3.15 is INFORMATIONAL (phase 1 of the 3.15 migration). On the 3.15 leg every step above
        # carries `continue-on-error: ${{ matrix.experimental == true }}`, so a failing step neither stops
        # this job nor turns its check red, and no merge, push or deployment waits on it. This step says
        # what failed instead: a warning annotation, and a table in the job summary.
        if: always() && matrix.experimental == true
        env:
          STEPS_JSON: ${{ toJSON(steps) }}
          PY_LEG: ${{ matrix.python-version }}
        run: |
          python3 - <<'PY'
          import json, os
          steps = json.loads(os.environ["STEPS_JSON"])
          leg = os.environ["PY_LEG"]
          failed = [k for k, v in steps.items() if v.get("outcome") not in ("success", "skipped")]
          rows = "\\n".join(f"| `{k}` | {v.get('outcome')} |" for k, v in steps.items())
          with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
              fh.write(f"### Python {leg}: informational, blocks nothing\\n\\n| Step | Outcome |\\n|---|---|\\n{rows}\\n")
          if failed:
              print(f"::warning title=Python {leg} (informational)::{len(failed)} step(s) failed on Python {leg}: {', '.join(failed)}. Nothing is blocked; see this job's summary.")
          else:
              print(f"::notice title=Python {leg} (informational)::every step passed on Python {leg}")
          PY
"""


def slug(step_first_line: str, taken: set[str]) -> str:
    text = step_first_line.split(":", 1)[1].strip().strip("'\"")
    if text.startswith(("actions/", "./")) or "@" in text:  # a `uses:` step: name it after the action
        text = text.split("@")[0].rsplit("/", 1)[-1]
    base = re.sub(r"\$\{\{[^}]*\}\}", "", text).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:40].strip("-") or "step"
    if not base[0].isalpha():
        base = "s-" + base
    out, n = base, 2
    while out in taken:
        out, n = f"{base}-{n}", n + 1
    taken.add(out)
    return out


def transform_job(lines: list[str], job: str) -> list[str]:
    try:
        start = lines.index(f"  {job}:\n")
    except ValueError:
        raise SystemExit(f"job {job!r} not found as a two-space key") from None
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^  [A-Za-z0-9_-]+:\s*$", lines[i])), len(lines))
    try:
        steps_at = next(i for i in range(start, end) if lines[i] == "    steps:\n")
    except StopIteration:
        raise SystemExit(f"job {job!r}: no '    steps:' line") from None
    item_starts = [i for i in range(steps_at + 1, end) if lines[i].startswith("      - ")]
    taken: set[str] = set()
    for i in item_starts:  # collect existing ids first so new ones never collide
        j_end = next((k for k in item_starts if k > i), end)
        for k in range(i, j_end):
            m = re.match(r"^(      - |        )id:\s*(\S+)", lines[k])
            if m:
                taken.add(m.group(2))
    out = lines[:steps_at + 1]
    for n, i in enumerate(item_starts):
        j_end = item_starts[n + 1] if n + 1 < len(item_starts) else end
        block = lines[i:j_end]
        if n == 0:
            out.extend(lines[steps_at + 1:i])
        keys = "".join(block)
        insert = []
        if not re.search(r"^(      - |        )id:", keys, re.M):
            insert.append(f"        id: {slug(block[0][8:], taken)}\n")
        if re.search(r"^(      - |        )continue-on-error:", keys, re.M):
            raise SystemExit(f"job {job!r}: step {block[0].strip()!r} already sets continue-on-error; combine by hand")
        insert.append(f"        {COE}\n")
        out.extend([block[0], *insert, *block[1:]])
    # Blank lines and two-space comments (the next job's banner) at the end of the block belong to the next job:
    # they stay after the appended report step.
    body, trail = out, []
    while body and (body[-1].strip() == "" or body[-1].startswith("  #")):
        trail.insert(0, body.pop())
    return body + ["\n", *REPORT_STEP.splitlines(keepends=True), *trail] + lines[end:]


def check(doc: dict, job: str, before: list[str]) -> None:
    steps = doc["jobs"][job]["steps"]
    names = [s.get("name") or s.get("uses") for s in steps]
    if names[:-1] != before or names[-1] != REPORT_NAME:
        raise SystemExit(f"job {job!r}: step list changed beyond the appended report step: {names}")
    ids = [s.get("id") for s in steps[:-1]]
    if len(set(ids)) != len(ids) or None in ids:
        raise SystemExit(f"job {job!r}: ids missing or duplicated: {ids}")
    if any(s.get("continue-on-error") != "${{ matrix.experimental == true }}" for s in steps[:-1]):
        raise SystemExit(f"job {job!r}: a step lacks the continue-on-error expression")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workflow", type=Path)
    ap.add_argument("jobs", nargs="+")
    ap.add_argument("--check", action="store_true", help="transform in memory and validate; write nothing")
    args = ap.parse_args()
    text = args.workflow.read_text(encoding="utf-8")
    before_doc = yaml.safe_load(text)
    lines = text.splitlines(keepends=True)
    for job in args.jobs:
        if before_doc["jobs"][job].get("continue-on-error") != "${{ matrix.experimental == true }}":
            raise SystemExit(f"job {job!r}: no job-level informational expression; is it a 3.15 matrix job?")
        lines = transform_job(lines, job)
    new = "".join(lines)
    doc = yaml.safe_load(new)
    for job in args.jobs:
        check(doc, job, [s.get("name") or s.get("uses") for s in before_doc["jobs"][job]["steps"]])
    if set(doc["jobs"]) != set(before_doc["jobs"]):
        raise SystemExit("job set changed")
    for jid in set(doc["jobs"]) - set(args.jobs):
        if doc["jobs"][jid] != before_doc["jobs"][jid]:
            raise SystemExit(f"job {jid!r} changed but was not named")
    if not args.check:
        args.workflow.write_text(new, encoding="utf-8")
    print(f"{'checked' if args.check else 'wrote'} {args.workflow}: {', '.join(args.jobs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
