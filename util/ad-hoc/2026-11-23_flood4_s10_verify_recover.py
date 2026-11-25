#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_verify_recover.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-11-23
# Last Modified: 2026-11-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     Flood-4 session 10. Recover a carrier's files after the 2026-11-20..22 blind "owner -> Overtoad" pass, PROVABLY:
#     a file is accepted only when its bytes, or an inverse of the substitution, reproduce the sha256 the carrier's agent
#     recorded before the pass (a hashes_final_*.json written by the flood-4 D-14 builder). Inverses tried, in order:
#       verbatim; plain ("Overtoad" -> "owner"); two-step ("The Overtoad" -> "Owner", then "Overtoad" -> "owner");
#       per-occurrence ("The Overtoad" -> "Owner" or "The owner", every combination up to 2**12, then the plain step).
#     Accepted bytes are copied to --out at the same relative path. Nothing in --root is modified.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_verify_recover.py --hashes H.json --root CARRIER --out DIR [--report R.json]
#     Exit 0 = every recorded file recovered; 1 = at least one FAILED or missing.
#####################################################################################################################################################################################################
"""Verify-and-recover carrier files against a recorded sha256 manifest."""

import argparse
import hashlib
import itertools
import json
import os
import sys

TOKEN = b"Overtoad"
CAP_TOKEN = b"The Overtoad"
MAX_COMBO_OCCURRENCES = 12


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _candidates(data):
    yield "verbatim", data
    yield "plain", data.replace(TOKEN, b"owner")
    yield "two-step", data.replace(CAP_TOKEN, b"Owner").replace(TOKEN, b"owner")
    parts = data.split(CAP_TOKEN)
    count = len(parts) - 1
    if 0 < count <= MAX_COMBO_OCCURRENCES:
        for choice in itertools.product((b"Owner", b"The owner"), repeat=count):
            out = parts[0]
            for repl, part in zip(choice, parts[1:]):
                out += repl + part
            yield "per-occurrence", out.replace(TOKEN, b"owner")


def _recorded(entry):
    return entry.get("recorded") or entry.get("sha256")


def _forward(data):
    """The juniper-ml pass: "Owner" -> "The Overtoad", "owner" -> "Overtoad" (case-sensitive, within lines)."""
    return data.replace(b"Owner", CAP_TOKEN).replace(b"owner", TOKEN)


def _git_show(repo, ref, rel):
    import subprocess  # pylint: disable=import-outside-toplevel

    proc = subprocess.run(["git", "-C", repo, "show", f"{ref}:{rel}"], capture_output=True, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _anchored(base, data, want):
    """Equal regions of F(base) vs the damaged bytes come from base verbatim; only the changed blocks are inverted."""
    import difflib  # pylint: disable=import-outside-toplevel

    base_lines = base.splitlines(keepends=True)
    fbase_lines = [_forward(line) for line in base_lines]
    cur_lines = data.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(a=fbase_lines, b=cur_lines, autojunk=False)
    pieces = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            pieces.append(("fixed", b"".join(base_lines[i1:i2])))
        else:
            pieces.append(("changed", b"".join(cur_lines[j1:j2])))
    changed = b"".join(text for kind, text in pieces if kind == "changed")
    count = changed.count(CAP_TOKEN)
    if count > MAX_COMBO_OCCURRENCES:
        return None, f"anchored: {count} capitalised occurrences in changed blocks"
    for choice in itertools.product((b"Owner", b"The owner"), repeat=count):
        it = iter(choice)
        out = []
        for kind, text in pieces:
            if kind == "fixed":
                out.append(text)
                continue
            parts = text.split(CAP_TOKEN)
            rebuilt = parts[0]
            for part in parts[1:]:
                rebuilt += next(it) + part
            out.append(rebuilt.replace(TOKEN, b"owner"))
        candidate = b"".join(out)
        if _sha(candidate) == want:
            return candidate, "anchored"
    return None, f"anchored: no combination of {count} matched"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hashes", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report")
    parser.add_argument("--base-ref", help="commit the carrier was built on; enables the anchored inverse for files the simple inverses miss")
    parser.add_argument("--base-repo", help="repository to read --base-ref from (default --root)")
    args = parser.parse_args(argv)
    with open(args.hashes, encoding="utf-8") as handle:
        manifest = json.load(handle)
    results, failed = [], 0
    for entry in manifest["files"]:
        rel, want = entry["path"], _recorded(entry)
        src = os.path.join(args.root, rel)
        if not entry.get("exists", True):
            results.append({"path": rel, "method": "recorded-absent", "ok": not os.path.exists(src)})
            continue
        if not os.path.isfile(src):
            results.append({"path": rel, "method": "MISSING", "ok": False})
            failed += 1
            continue
        with open(src, "rb") as handle:
            data = handle.read()
        method, good = "FAILED", None
        for name, candidate in _candidates(data):
            if _sha(candidate) == want:
                method, good = name, candidate
                break
        if good is None and args.base_ref:
            base = _git_show(args.base_repo or args.root, args.base_ref, rel)
            if base is not None:
                good, note = _anchored(base, data, want)
                method = "anchored" if good is not None else "FAILED"
                if good is None:
                    print(f"    {rel}: {note}")
        if good is None:
            failed += 1
        else:
            dst = os.path.join(args.out, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as handle:
                handle.write(good)
            os.chmod(dst, os.stat(src).st_mode & 0o777)
        results.append({"path": rel, "method": method, "ok": good is not None, "tokens_on_disk": data.count(TOKEN), "sha256": want})
        print(f"{method:>15}  Overtoad-on-disk={data.count(TOKEN):>3}  {rel}")
    summary = {}
    for item in results:
        summary[item["method"]] = summary.get(item["method"], 0) + 1
    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(summary.items())) + f"; failed={failed}")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            json.dump({"hashes": args.hashes, "root": args.root, "out": args.out, "summary": summary, "failed": failed, "files": results}, handle, indent=2)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
