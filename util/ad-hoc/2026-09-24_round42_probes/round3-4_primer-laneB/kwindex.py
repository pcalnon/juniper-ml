#!/usr/bin/env python3
"""Broad keyword index over the primer (worktree copy). Prints line, section, matched terms.

Lane B scratch tool. Read-only on the primer copy.
"""
import re
import sys
from pathlib import Path

P = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-laneB/primer_WT.md")

TERMS = {
    "artifact": r"artifact",
    "npz": r"\bnpz\b|savez",
    "etag": r"etag|entity[- ]tag",
    "304": r"\b304\b|not modified",
    "if-none-match": r"if-none-match",
    "if-match": r"if-match\b",
    "if-range": r"if-range",
    "range/206": r"\brange\b|\b206\b|partial content|resum",
    "validator": r"validator",
    "digest": r"digest",
    "sha": r"sha-?256|sha256|hashlib",
    "checksum": r"checksum",
    "DatasetMeta": r"datasetmeta",
    "cache": r"cach",
    "cache-control": r"cache-control|max-age|s-maxage|no-cache|no-store|31536000",
    "cdn": r"\bcdn\b|shared cache|intermediar",
    "conditional": r"conditional|precondition|\b412\b|\b428\b",
    "strong/weak": r"\bstrong\b|\bweak\b|\bW/",
    "immutable": r"immutab|cannot change|never change|can't change|does not change|unchanging|stable",
    "content-address": r"content[- ]address|content[- ]derived|content hash|hash(es|ed)? (over|of) (the )?(content|bytes)",
    "dataset_id": r"dataset_id|generate_dataset_id|dataset id",
    "last-modified": r"last-modified",
    "lost-update": r"lost update|lost-update|optimistic",
    "juniper-data": r"juniper-data\b|juniper_data",
    "deterministic": r"determinis|reproducib|idempot",
    "access": r"access_count|last_accessed|record_access|/access",
    "download": r"download",
    "fingerprint": r"fingerprint",
}
COMPILED = {k: re.compile(v, re.I) for k, v in TERMS.items()}


def main() -> int:
    only = set(sys.argv[1:])
    lines = P.read_text(encoding="utf-8").split("\n")
    section = "?"
    in_code = False
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{2,3} ", ln):
            section = ln.lstrip("#").strip()[:60]
        hits = [k for k, rx in COMPILED.items() if rx.search(ln)]
        if only:
            hits = [h for h in hits if h in only]
        if hits:
            print(f"{i}\t{'C' if in_code else 'P'}\t{section}\t{','.join(hits)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
