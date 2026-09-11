#!/usr/bin/env python3
"""2026-09-11_seqsafety_comment_fanout.py -- correct "ADVISORY / never blocks a merge" in 8 siblings.

Project: juniper-ml
Sub-Project: CI documentation integrity (cross-repo fan-out)
Application: ad-hoc repair
Author: Paul Calnon
License: MIT License

WHAT IS WRONG

Every sibling's `.github/workflows/sequence-safety.yml` states that the job is "ADVISORY,
NOT a required check", that it "never blocks a merge", and that "Promotion to a required
context, if ever desired, is an owner-only branch-ruleset decision". The promotion HAS
happened: `util/ad-hoc/2026-09-11_fleet_required_context_probe.py` reads each repo's live
ruleset and finds `Sequence Safety` among the required contexts in all nine repos --
juniper-ml (17 contexts), cascor (24), canopy (21), data (22), data-client (20),
cascor-client (20), cascor-worker (22), deploy (12), recurrence (10).

A reader who trusts the comment takes a red `Sequence Safety` for non-blocking and waits for
a merge that cannot happen. That is how the juniper-ml instance was found, on ml#1837, and
juniper-ml was corrected alone (ml#1849 / ml#1856).

THE PREMISE WAS CHECKED, NOT ASSUMED

The 2026-09-09 handoff asserted the required half from juniper-ml's ruleset and generalised
to eight repos whose rulesets nobody had read. If `Sequence Safety` were genuinely advisory
in a sibling, that sibling's comment would be CORRECT and editing it would introduce the
defect. So the ruleset is read per repo, first, and the fan-out covers only repos where the
claim is actually false. A comment and a ruleset are different authorities.

WHY IT IS NOT ONE PATCH

The eight files have eight different md5s -- per-repo headers, and different line wrapping
of the same sentences. So the paragraph is located by its FIRST and LAST sentence and
replaced as a block at the file's own comment indent, rather than by line number or by an
exact multi-line string that only matches one repo.

WHAT IT PRESERVES

"Never wired into the CI Quality Gate" stays, because it is still TRUE and is a different
claim from "not required" -- conflating the two is what produced the drift. juniper-ml's
corrected header makes exactly that distinction and this mirrors it.

SOURCE OF TRUTH IS THE API, NOT THE LOCAL CHECKOUT

Content is fetched from `repos/<owner>/<repo>/contents/...?ref=<default branch>`. Sibling
checkouts on this machine go stale silently, and `util/open_signed_pr.py` uploads WHOLE
FILES -- editing a stale copy would revert whatever landed meanwhile.

EXIT CODES

  * 0 -- every targeted repo patched (or, in dry-run, would be);
  * 1 -- at least one repo could not be patched (named, with the reason). A repo whose
    anchors did not match is NOT silently skipped: the whole point is that the text varies.
  * 2 -- could not run (gh missing, ruleset unreadable).

Usage:
    python3 util/ad-hoc/2026-09-11_seqsafety_comment_fanout.py            # dry run + diffs
    python3 util/ad-hoc/2026-09-11_seqsafety_comment_fanout.py --out DIR  # write patched files
"""

from __future__ import annotations

import argparse
import base64
import difflib
import json
import re
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
from pathlib import Path

OWNER = "pcalnon"
WORKFLOW = ".github/workflows/sequence-safety.yml"
CONTEXT = "Sequence Safety"

SIBLINGS = [
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]


def _gh_json(path: str):
    p = subprocess.run(  # nosec B603 B607 -- fixed argv, no shell
        ["gh", "api", path], capture_output=True, text=True, timeout=180
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[:200] or f"gh api {path} failed")
    return json.loads(p.stdout)


def ruleset_requires(repo: str, context: str) -> tuple:
    """(is_required, ruleset_id). Reads every ACTIVE ruleset on the repo."""
    for rs in _gh_json(f"repos/{OWNER}/{repo}/rulesets"):
        detail = _gh_json(f"repos/{OWNER}/{repo}/rulesets/{rs['id']}")
        if detail.get("enforcement") != "active":
            continue
        for rule in detail.get("rules", []):
            if rule.get("type") != "required_status_checks":
                continue
            names = [
                c["context"]
                for c in rule.get("parameters", {}).get("required_status_checks", [])
            ]
            if context in names:
                return True, rs["id"]
    return False, None


def fetch(repo: str) -> str:
    blob = _gh_json(f"repos/{OWNER}/{repo}/contents/{WORKFLOW}")
    return base64.b64decode(blob["content"]).decode("utf-8")


# --- the three drift sites ---------------------------------------------------------------
#
# Each is located by a pattern that tolerates the per-repo line wrapping. Every one asserts
# EXACTLY ONE match; zero means the text moved and a blind sweep would have written nothing
# while reporting success.

_PARA_START = re.compile(r"^(?P<pre>#\s+)ADVISORY, NOT a required check", re.M)
# The paragraph END is found STRUCTURALLY -- the bare `#` line that closes the block -- not
# by its last sentence. The sentence varies more than it looks: cascor ends "this PR makes
# NO ruleset change.", deploy WRAPS the same words across two lines ("NO ruleset" / "change."),
# and recurrence says "this workflow makes NO protection change." A text anchor matched six
# of eight and the two misses were reported rather than silently skipped, which is the only
# reason this was caught.
_PARA_BLANK = re.compile(r"^#\s*$", re.M)
_DESC = re.compile(r"Per-PR sequence-safety net \(ADVISORY, standalone\)")
_JOB = re.compile(r"^(?P<pre>\s*#\s*)sequence-safety \(ADVISORY\):", re.M)
# NOT anchored at the comment marker, and NOT single-line. The sentence begins mid-line
# (after "base..HEAD.") and in two of eight repos it WRAPS across a `#` continuation --
# canopy breaks after "advisory --", data-client breaks inside "never a required / context".
# A single-line pattern matched six and reported the two misses, which is how the wrap was
# found. Matched lazily between two fixed anchors and re-emitted as one correctly indented
# line, so the wrapping of the original does not have to be modelled.
_JOB_NEVER = re.compile(
    r"Standalone \+ advisory --.*?never wired into\s*(?:\n\s*#\s*)?(?P<gate>[^.]+?)\.",
    re.S,
)
# Guard against the lazy match running away if the anchors ever drift apart.
_JOB_NEVER_MAX = 220


def _paragraph(pre: str, repo: str, ruleset_id) -> str:
    """The corrected header paragraph, wrapped at the file's own comment indent."""
    lines = [
        "REQUIRED in the branch ruleset, and deliberately ABSENT from the CI Quality Gate",
        "`needs:`. Those are two different things and this comment used to conflate them: it",
        'opened "ADVISORY, NOT a required check" and promised that promotion "if ever desired"',
        "would be a future owner-only decision. The promotion HAPPENED; nobody edited the",
        "header. A reader who trusts it takes a red Sequence Safety for non-blocking; it",
        "blocks. Verified against the live ruleset, which this command prints:",
        "",
        # Deliberately unwrapped: a `gh api` command broken across a comment continuation
        # cannot be copied and run, which is the only thing this line is for.
        f"    gh api repos/{OWNER}/{repo}/rulesets/{ruleset_id}",
        "",
        f"It lists `{CONTEXT}` among its required contexts. Read the ruleset, never this",
        "comment -- a comment and a ruleset are different authorities, and this header is",
        "the standing proof that they drift.",
        "",
        "It remains a STANDALONE workflow, deliberately separate from ci.yml and never wired",
        "into the CI Quality Gate `needs:` -- which is a SEPARATE fact from whether it is",
        "required, and the one this header previously used to justify the wrong claim. Being",
        "required is a branch-ruleset property; the Quality Gate is a workflow property.",
        "Enforcement after merge is still the post-merge net (main-verify.yml).",
    ]
    return "\n".join((pre + ln).rstrip() for ln in lines)


def patch(text: str, repo: str, ruleset_id) -> tuple:
    """Return (new_text, notes). Raises AssertionError naming any anchor that did not match."""
    notes = []

    m = _PARA_START.search(text)
    if not m:
        raise AssertionError("header paragraph start not found")
    blank = _PARA_BLANK.search(text, m.start())
    if not blank:
        raise AssertionError("header paragraph end (bare '#' line) not found")
    pre = m.group("pre")
    block = text[m.start() : blank.start()]
    # Sanity: we are replacing the paragraph that makes the FALSE claims, not its neighbour.
    for needle in ("never blocks a merge", "Promotion to a required context"):
        if needle not in block:
            raise AssertionError(f"paragraph does not contain {needle!r} -- wrong block")
    new = text[: m.start()] + _paragraph(pre, repo, ruleset_id) + "\n" + text[blank.start() :]
    notes.append(f"header paragraph replaced ({len(block)} chars, {block.count(chr(10))} lines)")

    n = len(_DESC.findall(new))
    if n != 1:
        raise AssertionError(f"description tag matched {n} times, expected 1")
    new = _DESC.sub("Per-PR sequence-safety net (REQUIRED, standalone)", new)
    notes.append("description tag ADVISORY -> REQUIRED")

    n = len(_JOB.findall(new))
    if n != 1:
        raise AssertionError(f"job comment tag matched {n} times, expected 1")
    new = _JOB.sub(lambda mm: f"{mm.group('pre')}sequence-safety (REQUIRED):", new)
    notes.append("job comment tag ADVISORY -> REQUIRED")

    hits = list(_JOB_NEVER.finditer(new))
    if len(hits) != 1:
        raise AssertionError(
            f"job 'never a required context' sentence matched {len(hits)} times, expected 1"
        )
    hit = hits[0]
    if len(hit.group(0)) > _JOB_NEVER_MAX:
        raise AssertionError(
            f"job sentence match ran {len(hit.group(0))} chars (> {_JOB_NEVER_MAX}) -- "
            "anchors drifted, refusing to rewrite a span that large"
        )
    gate = " ".join(hit.group("gate").split())
    # Re-emit at the indent of the line the match STARTS on, so a wrapped original collapses
    # rather than being patched in place at two different indents. Wrapped to the width of
    # the block it sits in rather than left as one long line.
    line_start = new.rfind("\n", 0, hit.start()) + 1
    indent = re.match(r"\s*#\s*", new[line_start:]).group(0)
    head_len = hit.start() - line_start
    sentence = (
        f"Standalone, and REQUIRED in the branch ruleset -- not wired into {gate}, "
        "which is a SEPARATE fact."
    )
    width = 100
    out, cur = [], ""
    budget_first = max(20, width - head_len)
    for word in sentence.split():
        budget = budget_first if not out else width - len(indent)
        if cur and len(cur) + 1 + len(word) > budget:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    out.append(cur)
    replacement = ("\n" + indent).join(out)
    new = new[: hit.start()] + replacement + new[hit.end() :]
    notes.append(f"job 'never a required context' corrected (gate: {gate!r})")

    return new, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", help="directory to write patched files into (default: dry run)")
    ap.add_argument("--repos", nargs="*", default=SIBLINGS)
    args = ap.parse_args(argv)

    failures = []
    patched = 0
    for repo in args.repos:
        print(f"\n=== {repo} ===")
        try:
            required, rid = ruleset_requires(repo, CONTEXT)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{repo}: ruleset unreadable: {exc}")
            print("    RULESET UNREADABLE -- skipped")
            continue
        if not required:
            print(f"    {CONTEXT} is NOT required here -- comment is CORRECT, nothing to do")
            continue
        print(f"    {CONTEXT} REQUIRED (ruleset {rid})")

        try:
            before = fetch(repo)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{repo}: fetch failed: {exc}")
            print("    FETCH FAILED")
            continue
        try:
            after, notes = patch(before, repo, rid)
        except AssertionError as exc:
            failures.append(f"{repo}: {exc}")
            print(f"    ANCHOR MISS: {exc}")
            continue

        for n in notes:
            print(f"    - {n}")
        diff = list(
            difflib.unified_diff(
                before.splitlines(), after.splitlines(),
                fromfile=f"{repo}/{WORKFLOW} (main)", tofile=f"{repo}/{WORKFLOW} (patched)",
                lineterm="", n=1,
            )
        )
        print(f"    diff: {sum(1 for d in diff if d.startswith('-') and not d.startswith('---'))} "
              f"removed / {sum(1 for d in diff if d.startswith('+') and not d.startswith('+++'))} added")
        if args.out:
            outdir = Path(args.out)
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / f"{repo}.yml").write_text(after, encoding="utf-8")
            (outdir / f"{repo}.diff").write_text("\n".join(diff) + "\n", encoding="utf-8")
            print(f"    wrote {outdir / (repo + '.yml')}")
        patched += 1

    print(f"\n{patched} repo(s) {'patched' if args.out else 'would be patched'}; "
          f"{len(failures)} failure(s)")
    if failures:
        print("failures:", file=sys.stderr)
        for f in failures:
            print(f"    {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
