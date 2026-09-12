#!/usr/bin/env python3
"""One-shot: correct reference_sequence_safety_local_repro.md with the 2026-09-11 consensus.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-11

The note's 2026-09-10 section already corrects the 2026-09-09 mechanism. Two things were
still wrong or missing, and one of them propagated into shipped tooling:

1. The 2026-09-09 section is not marked SUPERSEDED at its head, so a reader who lands there
   first gets the refuted account.
2. The 2026-09-10 section's remedy line -- `"string" -> re-arm with --body-file before it
   fires` -- is over-broad and, as a general instruction, dangerous. A stored string is an
   ARM-TIME SNAPSHOT, and re-arming a mergeable PR MERGES IT on the spot.

Idempotent; refuses on a drifted anchor.
"""

from __future__ import annotations

import pathlib
import sys

NOTE = pathlib.Path.home() / (
    ".claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/"
    "reference_sequence_safety_local_repro.md"
)

OLD_HEAD = ("## 2026-09-09 — WHY the trailer gets dropped: the auto-merge net arms with an "
            "EMPTY commitBody")
NEW_HEAD = """## 2026-09-09 — SUPERSEDED — "the net arms with an EMPTY commitBody"

> **SUPERSEDED 2026-09-10, and REFUTED AS A MECHANISM 2026-09-11.** Read the 2026-09-11
> section at the end of this file before acting on anything below. In short: the net does
> **not** arm empty. `gh pr merge --auto` with no body flags OMITS `commitBody`, GitHub
> stores `null`, and `null` is the SAFE state — the repo's `COMMIT_MESSAGES` default is
> resolved at MERGE time and trailers survive. `util/safe_merge.py` has never passed a
> body in any version, so it cannot cause this. The measurement below (ml#1831 landing
> bodyless) is REAL and reproduces; the mechanism inferred from it was over-generalised.
> This section is kept because it is where the claim came from, not as guidance."""

OLD_REMEDY = '''# "null"   -> safe, leave it alone
# "string" -> re-arm with --body-file before it fires'''
NEW_REMEDY = '''# "null"   -> SAFE. Resolved at merge time. Leave it alone.
# ""       -> DESTRUCTIVE, immediately: the squash lands with no body at all.
# "string" -> an ARM-TIME SNAPSHOT. See the 2026-09-11 section: do NOT reflexively
#             re-arm; a re-arm on a mergeable PR MERGES IT ON THE SPOT.'''

APPENDIX = '''

## 2026-09-11 — CONSENSUS: three states, and the hazard is a body stored BEFORE later commits

Validated by independent agent consensus (3 Lane A entry points — the `gh` source, the repo's
merge history, GitHub's schema/docs — plus 2 Lane B adversarial rounds), over 1877 PRs.
Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**`commitBody` has THREE states, not two.**

| state | how it arises | effect |
|---|---|---|
| `null` | field OMITTED at arm time — `gh pr merge --auto` with no body flags | **SAFE.** `COMMIT_MESSAGES` resolves at MERGE time. 60 post-arm commits over 48 PRs, **zero** lost, lags to 40.7h |
| `""` | an explicit empty string | **DESTRUCTIVE at once.** Overrides the default; squash lands bodyless. 8 PRs here (ml#1831 landed one line) — but all 8 had bodyless sources, so none actually lost anything |
| non-empty | a body supplied at arm time | **ARM-TIME SNAPSHOT.** Binds when the net fires. Of 29 PRs with a post-arm single-parent commit, **23 lost that commit's body** |

**`util/safe_merge.py` is NOT the cause and never was.** It passes no body on either path, in
any version. ml#1228 — the one real waiver loss — was armed by something else **5m42s after
safe_merge's own disarm**. A note that keeps safe_merge as its subject is wrong a third time.

**Two tiers of harm, routinely fused:**

* **provenance loss** — common, silent, reddens nothing. 36 PRs. ml#1877 lost **nine** commit
  messages (all six consensus rounds and the CodeQL fix) and nobody noticed.
* **waiver loss** — n=1, loud. ml#1228 lost
  `Allow-Symbol-Loss: method:NetGuaranteeDocTest.test_docstring_states_the_net_is_not_head_pinned`
  from a commit pushed 17 min after arming; `Post-Merge Main Verification` failed on the landed
  SHA 3s later, four follow-on reds, cleared by ml#1243.

**The rule is about TIMING, not about supplying a body.** A body supplied AFTER the last
commit is correct, and is the only way to guarantee a trailer's exact text — 12 PRs here carry
a deliberately curated message, and the alternative on a large PR is ml#1797's 26,052-char
auto-concatenation. **Never supply a body at arm time if more commits may follow; if you do,
re-supply it after the last one.**

**DO NOT "disarm and re-arm" as a reflex.** `--auto` on a mergeable PR merges ON THE SPOT —
that sequence merged three sibling PRs on 2026-09-11 — and if the disarm succeeds while the
re-arm's `--match-head-commit` fails (which happens precisely when the head has moved), the PR
is left with no net at all.

**Tools, none of which mutate auto-merge state:**

```bash
# is an OPEN PR's stored snapshot already missing a commit?
python3 util/ad-hoc/2026-09-10_soak_stopping_rule/armed_snapshot_staleness.py --open
# did a MERGED PR's squash body lose a trailer its source commits carried?
python3 util/ad-hoc/2026-09-10_soak_stopping_rule/trailer_loss_check.py --recent 40
```

`util/safe_merge.py` now refuses at entry on a stored `""` and reads the net back after arming
rather than inferring "armed" from exit 0.

**Two other accounts of ml#1228 are on `main` and are both WRONG.** Commit `f65a31016b2a`'s
message says squash "composes from the PR's FIRST commit" — refuted by ml#1797 (`null`, 49
commits, 26,052-char message). `util/ad-hoc/2026-09-11_seqsafety_fanout_arm_merge.py` said a
null body "ships the SUBJECT ONLY" and armed eight sibling repos on that premise; **retired
2026-09-11** to `util/ad-hoc/retired/`.

**How this reached shipped tooling: the INDEX HOOK, not the note.** This file was corrected on
2026-09-10, but `MEMORY.md`'s one-line hook still read *"The net arms with an empty
`commitBody` and DROPS it"* — the superseded claim. An agent reading the always-loaded index
and acting without opening the on-demand note gets the refuted account with full confidence.
**When a note is corrected, its index hook is part of the correction.** Hook fixed 2026-09-11.
'''


def main() -> int:
    src = NOTE.read_text(encoding="utf-8")
    if "2026-09-11 — CONSENSUS: three states" in src:
        print("already applied")
        return 0
    for name, old in (("09-09 head", OLD_HEAD), ("remedy block", OLD_REMEDY)):
        if src.count(old) != 1:
            print(f"REFUSING: anchor {name!r} found {src.count(old)} times", file=sys.stderr)
            return 1
    src = src.replace(OLD_HEAD, NEW_HEAD).replace(OLD_REMEDY, NEW_REMEDY)
    NOTE.write_text(src.rstrip("\n") + APPENDIX, encoding="utf-8")
    print(f"applied to {NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
