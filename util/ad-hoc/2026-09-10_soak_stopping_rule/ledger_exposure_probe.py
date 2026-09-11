#!/usr/bin/env python3
"""Measure the soak ledger's CONTENT exposure, separately from filename sightings.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-10

Why this exists
---------------
Item F' of
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md``
states: "8 of the 43 runs touched ``reports/soak/pointer_follow_soak.jsonl``; exactly ONE
read its contents", the one being P18-health-interval-non-positive on 2026-08-22.

That number decides item F''s exposure, and through owner decision 8 it decides whether the
leak invalidates its runs -- which changes the DENOMINATOR of every rate in the arc. It is
worth re-deriving rather than inheriting, because the instrument that produced it cannot
quite make the distinction it is being quoted for:

``util/ad-hoc/2026-09-08_soak_label_to_transcript.py`` classifies an occurrence as the
ledger's own note when a window around it contains any of ``LEDGER_MARKERS`` --

    LEDGER_FILE    = "pointer_follow_soak"
    LEDGER_MARKERS = ('"obs_id"', "'obs_id'", LEDGER_FILE)

-- and the third of those is the FILENAME STEM. A ``git status`` line, an ``ls -t
reports/soak/``, or a ``grep -l`` naming the file puts ``pointer_follow_soak`` in the window
with no record content anywhere near it. So the ``ledger=N`` column conflates the two
categories the handoff's sentence turns on, and reading "two rows carry ledger=" as "two
rows read content" is an over-read of the instrument in exactly the direction the re-audit
warns about.

This separates them on the only marker that cannot appear without a record body: ``obs_id``,
a key that exists in the ledger's JSON and nowhere in a directory listing.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/ledger_exposure_probe.py

Read-only. Touches no ledger, runs no probe.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
BINDER = REPO_ROOT / "util" / "ad-hoc" / "2026-09-08_soak_label_to_transcript.py"
LEDGER = REPO_ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"

# Content markers: keys that only ever occur inside a ledger RECORD.
CONTENT_KEYS = ("obs_id", "scored_by", "discriminator_ok", "miss_class")
# Filename markers: the path, with no claim about what came back.
FILENAME_RE = re.compile(r"pointer_follow_soak(?:\.jsonl)?")


def _load_binder():
    spec = importlib.util.spec_from_file_location("soak_binder", BINDER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {BINDER}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["soak_binder"] = mod  # @dataclass needs this before exec_module
    spec.loader.exec_module(mod)
    return mod


def classify(path: pathlib.Path) -> dict:
    """Per transcript: ledger CONTENT occurrences vs FILENAME-only sightings."""
    content = Counter()
    filename = 0
    content_samples: list[str] = []

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except Exception:  # nosec B112 - a malformed transcript line is not fatal
            continue
        stack = [rec]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                kind = node.get("type")
                if kind in ("tool_use", "tool_result"):
                    raw = json.dumps(node.get("input") if kind == "tool_use" else node.get("content"))
                    blob = raw.replace("\\", "")
                    hit_content = False
                    for key in CONTENT_KEYS:
                        n = blob.count(f'"{key}"')
                        if n:
                            content[key] += n
                            hit_content = True
                    if hit_content and len(content_samples) < 3:
                        idx = blob.find('"obs_id"')
                        if idx >= 0:
                            content_samples.append(blob[max(0, idx - 80):idx + 160])
                    filename += len(FILENAME_RE.findall(blob))
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    return {
        "content_hits": sum(content.values()),
        "content_by_key": dict(content),
        "filename_hits": filename,
        "samples": content_samples,
    }


def main() -> int:
    binder = _load_binder()
    rows = binder.load_ledger(LEDGER)

    print("=" * 78)
    print("soak ledger CONTENT exposure -- re-derived 2026-09-10")
    print("=" * 78)
    print(f"ledger           : {LEDGER}")
    print(f"rows             : {len(rows)} valid observations")
    print()
    print("CONTENT marker = an `obs_id` / `scored_by` / `discriminator_ok` / `miss_class`")
    print("key in a tool payload. Those exist in a ledger RECORD and in no directory")
    print("listing, so they cannot be produced by seeing the filename.")
    print()

    # Reuse the binder's own row->transcript binding rather than re-deriving it.
    # Its `bind()` is the function the 09-08 re-audit ran and consensus re-derived
    # independently (subject-text Jaccard, 0 ambiguous); re-implementing it here
    # would put a second, unvalidated binding under a number that decides a
    # denominator.
    bound = binder.bind(rows, binder.discover_transcripts())

    n_content = n_filename = 0
    for entry in bound:
        tpath = entry.get("transcript")
        if not tpath:
            continue
        res = classify(pathlib.Path(tpath))
        if res["content_hits"] == 0 and res["filename_hits"] == 0:
            continue
        verdict = "CONTENT READ" if res["content_hits"] else "filename only"
        if res["content_hits"]:
            n_content += 1
        else:
            n_filename += 1
        print(f"{entry.get('ts', '?'):<21} {entry.get('probe_id', '?'):<34} "
              f"outcome={entry.get('outcome', '?'):<17} "
              f"content={res['content_hits']:<4} filename={res['filename_hits']:<4} {verdict}")
        if res["content_by_key"]:
            print(f"    keys: {res['content_by_key']}")
        for s in res["samples"]:
            print(f"    ...{s[:150]}...")

    print()
    print(f"runs that READ ledger CONTENT : {n_content}")
    print(f"runs that saw the FILENAME only: {n_filename}")
    print(f"runs that touched it at all    : {n_content + n_filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
