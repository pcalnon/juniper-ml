#!/usr/bin/env python3
"""One-shot: retire util/ad-hoc/2026-09-11_seqsafety_fanout_arm_merge.py, premise inverted.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

Moves the script into `util/ad-hoc/retired/` (existing convention, `_RETIRED-<date>` suffix)
and prepends a header recording WHY, so the next reader meets the refutation at the file
rather than having to find a PR body.

Idempotent.
"""

from __future__ import annotations

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "util" / "ad-hoc" / "2026-09-11_seqsafety_fanout_arm_merge.py"
DST = ROOT / "util" / "ad-hoc" / "retired" / "2026-09-11_seqsafety_fanout_arm_merge_RETIRED-2026-09-11.py"

HEADER = '''"""
RETIRED 2026-09-11 — ITS CENTRAL PREMISE IS INVERTED. DO NOT RUN.

Status: retired 2026-09-11 (kept for provenance; it was executed against eight repos)

This script's docstring states:

    "GitHub's auto-merge net stores its own commit subject/body, and when armed WITHOUT
     them both fields are `null`. A squash that fires on a null body ships the SUBJECT
     ONLY -- dropping the [body]"

That is backwards, and independent consensus over 1877 PRs established the opposite:

* A `null` body is the SAFE state. The field was omitted at arm time, so the repository's
  `squash_merge_commit_message` (COMMIT_MESSAGES on all nine repos) resolves at MERGE
  time and the full body lands. Measured: 60 single-parent commits pushed AFTER arming,
  across 48 PRs, ZERO lost, at lags up to 40.7 hours. juniper-ml#1797 landed a
  26,052-character message from a null-body arm.
* A NON-NULL body is an ARM-TIME SNAPSHOT and is the hazard this script was meant to
  avoid. It binds when the net fires, so every commit pushed after the arm is dropped.
  Of the 29 PRs with a post-arm single-parent commit, 23 lost that commit's body.
  juniper-ml#1228 lost an `Allow-Symbol-Loss:` waiver that way and `Post-Merge Main
  Verification` failed on the landed SHA three seconds later; juniper-ml#1877 silently
  lost nine commit messages.

So this script installs the defect it was written to prevent. Two further problems:

* It arms from `commits[0]["messageBody"]` -- the FIRST commit only -- so on any
  multi-commit PR every later commit's message is dropped BY CONSTRUCTION, with no
  post-arm push required at all.
* It accepts `commitBody | length > 0` as "the only proof the arm took". `length` is 0
  for BOTH `null` and `""`, which is precisely the indistinguishability that produced the
  superseded diagnosis. The correct discriminator is the value, not its length.

It also performs `--disable-auto` then re-arms, a sequence that MERGES a mergeable PR on
the spot -- observed here on three sibling repos on 2026-09-11.

Replacement, none of which mutates auto-merge state:

* `util/safe_merge.py` `stale_snapshot_refusal` -- refuses at entry on a stored empty body.
* `util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py` -- measures
  whether an open PR's stored snapshot is already missing a commit.
* `util/ad-hoc/2026-09-10_soak_stopping_rule/trailer_loss_check.py` -- measures, after the
  fact, whether a merged PR's squash body lost a trailer its source commits carried.

The eight sibling PRs it armed have all merged; five landed from a snapshot body. Nothing
here needs re-running -- the correct action for a future fan-out is to arm with NO body
flags and let the default resolve at merge time.

ORIGINAL DOCSTRING FOLLOWS.
"""

'''


def main() -> int:
    if DST.exists():
        print("already retired")
        return 0
    if not SRC.exists():
        print(f"nothing to retire: {SRC} not present", file=sys.stderr)
        return 1
    DST.parent.mkdir(parents=True, exist_ok=True)
    body = SRC.read_text(encoding="utf-8")
    # Keep the shebang first so the file still reads as a script.
    if body.startswith("#!"):
        shebang, _, rest = body.partition("\n")
        body = f"{shebang}\n{HEADER}{rest}"
    else:
        body = HEADER + body
    DST.write_text(body, encoding="utf-8")
    SRC.unlink()
    print(f"retired -> {DST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
