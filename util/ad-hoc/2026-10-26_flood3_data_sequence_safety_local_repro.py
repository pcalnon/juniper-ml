"""
Reproduce juniper-data's two Sequence Safety screens on an uncommitted change, without a commit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — investigation (one-off pre-upload check for the juniper-data flood-3 backlog PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §4 (juniper-data rows)

Local commits cannot be signed headless, so the screens' git-range drivers (``run``) cannot be
pointed at the change. This drives the same library functions on the same inputs instead:

* symbol screen: ``py_symbols`` on each BASE / HEAD text, ``classify_file``, ``apply_relocation``,
  then ``apply_waivers`` for any ``Allow-Symbol-Loss:`` text passed with ``--trailers``;
* docs screen: ``parse_hunks`` over a saved ``--unified=0`` diff (what CI's ``file_diff`` runs),
  ``fenced_lines`` of each BASE / HEAD text, ``classify_file`` with ``DEFAULT_MIN_RUN``.

Usage:
    python 2026-10-26_flood3_data_sequence_safety_local_repro.py \
        --ci-tools <juniper-ci-tools source dir> --head-root <juniper-data worktree> \
        --py REL=BASEFILE [--py ...] --docs-diff <unified0 diff> --docs REL=BASEFILE [--docs ...] \
        [--trailers <file holding commit-message text>]

Exit status: 0 when no unwaived FAIL finding remains, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _pairs(values: list[str]) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for item in values:
        rel, _, base = item.partition("=")
        if not rel or not base:
            raise SystemExit(f"expected REL=BASEFILE, got {item!r}")
        out[rel] = Path(base)
    return out


def _split_diff(text: str) -> dict[str, str]:
    """Split a multi-file unified diff into per-file chunks keyed by the post-image path."""
    per_file: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            current = line[len("+++ b/") :]
            per_file[current] = []
            continue
        if current is not None:
            per_file[current].append(line)
    return {path: "\n".join(lines) for path, lines in per_file.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--ci-tools", required=True, type=Path)
    parser.add_argument("--head-root", required=True, type=Path)
    parser.add_argument("--py", action="append", default=[])
    parser.add_argument("--docs-diff", type=Path)
    parser.add_argument("--docs", action="append", default=[])
    parser.add_argument("--trailers", type=Path)
    args = parser.parse_args()

    sys.path.insert(0, str(args.ci_tools))
    from juniper_ci_tools import docs_additions_check as docs_screen
    from juniper_ci_tools import symbol_loss_check as symbol_screen

    trailer_text = args.trailers.read_text(encoding="utf-8") if args.trailers else ""
    failing = 0

    base_invs: dict = {}
    head_invs: dict = {}
    findings: list = []
    for rel, base_path in _pairs(args.py).items():
        base_inv = symbol_screen.py_symbols(base_path.read_text(encoding="utf-8"))
        head_inv = symbol_screen.py_symbols((args.head_root / rel).read_text(encoding="utf-8"))
        if base_inv is None or head_inv is None:
            print(f"UNPARSEABLE {rel}")
            failing += 1
            continue
        base_invs[rel], head_invs[rel] = base_inv, head_inv
        findings += symbol_screen.classify_file(rel, base_inv, head_inv, False)
    symbol_screen.apply_relocation(findings, base_invs, head_invs)
    allowed, wildcard = symbol_screen.parse_allow_trailers(trailer_text)
    symbol_screen.apply_waivers(findings, allowed)
    print(f"symbol screen: {len(base_invs)} file(s); trailer tokens {sorted(allowed)}; wildcard {wildcard}")
    for finding in findings:
        print(f"  {finding.severity:6} {finding.verdict:10} {finding.path} {finding.symbol} {finding.detail}")
        failing += finding.severity == "FAIL"
    if not findings:
        print("  clean")

    if args.docs_diff:
        chunks = _split_diff(args.docs_diff.read_text(encoding="utf-8"))
        bases = _pairs(args.docs)
        doc_findings: list = []
        for path, chunk in chunks.items():
            hunks = docs_screen.parse_hunks(chunk)
            base_fenced = docs_screen.fenced_lines(bases[path].read_text(encoding="utf-8")) if path in bases else None
            head_fenced = docs_screen.fenced_lines((args.head_root / path).read_text(encoding="utf-8"))
            doc_findings += docs_screen.classify_file(path, hunks, docs_screen.DEFAULT_MIN_RUN, base_fenced, head_fenced)
            print(f"docs screen: {path}: {len(hunks)} hunk(s)")
        for finding in doc_findings:
            print(f"  {finding.severity:6} {finding.reason:16} {finding.path} {finding.detail}")
            failing += finding.severity == "FAIL"

    print(f"unwaived FAIL findings: {failing}")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
