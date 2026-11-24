#!/usr/bin/env python3
"""
Put "owner" back wherever juniper-ml#2606 renamed a TECHNICAL owner to "Overtoad", from a reviewed list, on current main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — migration (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2606; util/ad-hoc/2026-11-24_technical_owner_restore_list.tsv (written by
    2026-11-24_technical_owner_decisions.py); util/ad-hoc/2026-11-23_pr2606_rebuild.py (the protected sets)

What it does
------------
For each row of the list (path, line, occurrence, base token, head token) it:

1. refuses a protected path: a record, a pinned file, the requirements domain, a ``KEEP_MAIN`` file (all as
   ``2026-11-23_pr2606_rebuild.py`` defines them), a symlink, or a path named by ``--avoid`` (main's files
   that hold open high or error CodeQL alerts);
2. checks, from ``--base`` (main before #2606) and ``--head`` (#2606's merge), that the token at that
   occurrence is one #2606 renamed, from the base token to the head token. A file #2606 ADDED has no base: its
   base text is the head text with the two-step inverse applied ("The Overtoad" -> "Owner", then "Overtoad" ->
   "owner"), which is how #2606's rebuild reconstructed it;
3. finds the head line in the checkout (current main): at the same line number if that line is still the
   head line, else the one line in the file equal to it. A line main has changed since is REFUSED, because the
   token can no longer be placed by text alone;
4. writes the base token back in place of the head token, at that token's column, and nothing else.

Every written line is then checked: it must equal the head line with exactly the listed tokens put back, and
every other line of the file must be untouched.

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_restore.py --repo . --list LIST.tsv --base 515e16a0 --head 5a049144
        [--avoid PATH ...] [--apply] [--report out.tsv]
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location("pr2606_rebuild", os.path.join(HERE, "2026-11-23_pr2606_rebuild.py"))
rb = importlib.util.module_from_spec(_SPEC)
sys.modules["pr2606_rebuild"] = rb
_SPEC.loader.exec_module(rb)

SEP = re.compile(r"(Owner|owner)")


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args[:3])} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def head_columns(base_line: str, head_line: str) -> dict[int, tuple[str, str, int]] | None:
    """occurrence -> (base token, head token, head column) for every owner token of BASE_LINE."""
    pieces = SEP.split(base_line)
    pattern = "".join(re.escape(p) if k % 2 == 0 else "(Owner|owner|The Overtoad|Overtoad)" for k, p in enumerate(pieces))
    match = re.fullmatch(pattern, head_line)
    if not match:
        return None
    out, head_pos = {}, len(pieces[0])
    for k in range(1, len(pieces), 2):
        got = match.group((k + 1) // 2)
        out[(k + 1) // 2] = (pieces[k], got, head_pos)
        head_pos += len(got) + len(pieces[k + 1])
    return out


def protected(path: str, mode: str | None, avoid: set[str]) -> str | None:
    if mode is None:
        return "not on main"
    if mode == "120000":
        return "a symlink"
    if mode not in ("100644", "100755"):
        return f"mode {mode}"
    if rb.is_record(path):
        return "a record"
    if rb.is_pinned(path):
        return "a pinned file"
    if path.startswith(rb.TECHNICAL_DOMAINS):
        return "the requirements domain"
    if path in rb.KEEP_MAIN:
        return "kept at main's bytes (KEEP_MAIN)"
    if path in avoid:
        return "holds an open high or error CodeQL alert on main"
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--list", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--avoid", nargs="*", default=[])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    if git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        raise SystemExit("REFUSED: the checkout has tracked changes; it must be a clean checkout of main")
    modes = {}
    for row in git(repo, "ls-tree", "-r", "HEAD").splitlines():
        meta, path = row.split("\t", 1)
        modes[path] = meta.split()[0]
    wanted: dict[str, dict[int, list[tuple[int, str, str]]]] = {}
    with open(args.list, encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        if header[:5] != ["path", "line", "occurrence", "base", "head"]:
            raise SystemExit(f"REFUSED: unexpected list header {header[:5]}")
        for raw in handle:
            path, line, occurrence, base_token, head_token = raw.rstrip("\n").split("\t")[:5]
            wanted.setdefault(path, {}).setdefault(int(line), []).append((int(occurrence), base_token, head_token))
    report, refused, applied, writes = [], 0, 0, {}
    for path in sorted(wanted):
        why = protected(path, modes.get(path), set(args.avoid))
        if why:
            for line, items in wanted[path].items():
                refused += len(items)
                report.append(f"REFUSED\t{path}:{line}\t{why}")
            continue
        head_text = git(repo, "show", f"{args.head}:{path}")
        head_lines = head_text.split("\n")
        if subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{args.base}:{path}"], capture_output=True).returncode == 0:
            base_lines = git(repo, "show", f"{args.base}:{path}").split("\n")
        else:
            # #2606 ADDED this file: its pre-rename text is the two-step inverse, as #2606's rebuild reconstructed it
            base_lines = rb.invert(head_text).split("\n")
            report.append(f"NOTE\t{path}\tadded by #2606: base reconstructed by the two-step inverse")
        with open(os.path.join(repo, path), encoding="utf-8", newline="") as handle:
            current = handle.read().split("\n")
        new = list(current)
        changed_lines = set()
        for line, items in sorted(wanted[path].items()):
            base_line, head_line = base_lines[line - 1], head_lines[line - 1]
            columns = head_columns(base_line, head_line)
            if columns is None:
                refused += len(items)
                report.append(f"REFUSED\t{path}:{line}\tthe base and head lines differ beyond the rename")
                continue
            bad = [o for o, b, h in items if o not in columns or columns[o][0] != b or columns[o][1] != h or b == h]
            if bad:
                refused += len(items)
                report.append(f"REFUSED\t{path}:{line}\toccurrence(s) {bad} are not tokens #2606 renamed as listed")
                continue
            if line <= len(current) and current[line - 1] == head_line:
                at = line
            else:
                hits = [n for n, text in enumerate(current, 1) if text == head_line]
                if len(hits) != 1:
                    refused += len(items)
                    report.append(f"REFUSED\t{path}:{line}\tmain changed the line since #2606 ({len(hits)} exact match(es) of the head line)")
                    continue
                at = hits[0]
            text = head_line
            for occurrence, base_token, head_token in sorted(items, key=lambda item: -columns[item[0]][2]):
                col = columns[occurrence][2]
                if text[col : col + len(head_token)] != head_token:
                    raise SystemExit(f"INTERNAL: {path}:{line} occurrence {occurrence} is not {head_token!r} at column {col}")
                text = text[:col] + base_token + text[col + len(head_token) :]
            new[at - 1] = text
            changed_lines.add(at)
            applied += len(items)
            report.append(f"APPLIED\t{path}:{at}\t{len(items)} token(s){'' if at == line else f' (head line {line})'}")
        # nothing but the listed lines may change, and each changed line must be the head line with tokens put back
        for n, (old_text, new_text) in enumerate(zip(current, new), 1):
            if old_text != new_text and n not in changed_lines:
                raise SystemExit(f"VERIFY FAILED: {path}:{n} changed without a listed token")
        if changed_lines:
            writes[path] = "\n".join(new)
    if args.apply:
        for path, text in writes.items():
            with open(os.path.join(repo, path), "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write("\n".join(report) + "\n")
    print(f"main {git(repo, 'rev-parse', '--short=8', 'HEAD').strip()}: {applied} token(s) restored in {len(writes)} file(s), {refused} refused" + ("  APPLIED" if args.apply else "  (dry run)"))
    for row in report:
        if row.startswith("REFUSED"):
            print(row)
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
