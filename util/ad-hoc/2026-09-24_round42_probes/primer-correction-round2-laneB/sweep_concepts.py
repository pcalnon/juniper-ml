#!/usr/bin/env python3
"""Concept-derived sweep of the primer at the PR head for passages that still rely on the refuted premises.

Scratch instrument for round-2 Lane B (primer correction). Read-only: prints hits.

Concepts (not just the author's search terms):
  C1 immutability / never-changes / cache-forever
  C2 content-addressing / hash-of-inputs identity
  C3 checksum / digest as validator
  C4 validator strength / ETag / entity tag
  C5 conditional requests (If-*, 304/412/428, Range)
  C6 caching directives (max-age, immutable, no-cache, public/private, CDN, shared cache)
  C7 concurrency (lost update, RMW, race, atomic, lock, last-writer, optimistic, CAS)
  C8 idempotent / dedupe / nonce / seed determinism
  C9 juniper-data read counters / Content-Location / latest
A hit is REPORTED when the line (or a line within +-WINDOW) names juniper-data / the Juniper codebase,
or when the line is inside a fenced code block (examples), or inside Appendix A.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PRIMER = Path(sys.argv[1])
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 9866
WINDOW = 3
MARK = re.compile(r"\*\*\[Corrected: E\.[12]\]\(#e[12]-[a-z-]+\)\*\*")

CONCEPTS = {
    "C1": r"immutab|cannot change|can't change|never chang|never go stale|go stale|stale|forever|for a year|31536000|cannot have changed|can never serve|pure function",
    "C2": r"content[- ]address|content hash|content[- ]derived|hash(es)? of the (inputs|request)|hash of inputs|hashes canonical|derived from inputs|request[- ]derived|same (id|URI|URL)",
    "C3": r"checksum|digest|sha-?256|compute_checksum|arrays_to_bytes|\bhash\b",
    "C4": r"\bETag|entity[- ]tag|validator|\bW/|\bweak\b|\bstrong\b",
    "C5": r"If-Match|If-None-Match|If-Range|If-Modified-Since|If-Unmodified-Since|Last-Modified|conditional|precondition|\b304\b|\b412\b|\b428\b|Not Modified|\bRange\b|\b206\b|resum",
    "C6": r"max-age|no-cache|no-store|must-revalidate|Cache-Control|\bprivate\b|\bpublic\b|\bCDN\b|shared cache|\bVary\b|cach(e|ing|ed)|revalidat|freshness",
    "C7": r"lost[- ]update|read-modify-write|last[- ]writer|optimistic|concurren|\brace\b|atomic|\block\b|_version_lock|version check|compare-and-swap|\bCAS\b|serialis|serializ",
    "C8": r"idempot|dedup|nonce|\bseed\b|non-deterministic|deterministic|re-POST|collid",
    "C9": r"record_access|access_count|last_accessed|Content-Location|/latest|\blatest\b|update_dataset_tags|update_tags|\btags\b",
}
JUNIPER = re.compile(r"juniper[-_]data|juniper_data|DatasetMeta|generate_dataset_id|dataset_id\.py|artifacts\.py|routes/datasets|local_fs|Juniper'?s|the real service|the service", re.I)


def main() -> int:
    lines = PRIMER.read_text(encoding="utf-8").split("\n")[:LIMIT]
    in_fence = [False] * len(lines)
    fence = False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            in_fence[i] = True
            fence = not fence
            continue
        in_fence[i] = fence
    appendix_a = None
    for i, ln in enumerate(lines):
        if ln.startswith("## Appendix A"):
            appendix_a = i
            break
    jmask = [bool(JUNIPER.search(ln)) for ln in lines]
    near = [any(jmask[max(0, i - WINDOW): i + WINDOW + 1]) for i in range(len(lines))]
    compiled = {k: re.compile(v, re.I) for k, v in CONCEPTS.items()}
    n = 0
    for i, ln in enumerate(lines):
        tags = [k for k, rx in compiled.items() if rx.search(ln)]
        if not tags:
            continue
        where = []
        if jmask[i]:
            where.append("J")
        elif near[i]:
            where.append("j~")
        if in_fence[i]:
            where.append("CODE")
        if appendix_a is not None and i >= appendix_a:
            where.append("APPX")
        if not where:
            continue
        marked = "M" if MARK.search(ln) else "-"
        n += 1
        print(f"{i + 1:5d} {marked} {','.join(tags):20s} {'/'.join(where):10s} {ln[:220]}")
    print(f"# {n} hits", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
