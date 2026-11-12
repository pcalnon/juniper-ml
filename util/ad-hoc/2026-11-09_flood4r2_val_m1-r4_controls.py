#!/usr/bin/env python3
"""
Controls for two round-4 real-engine shapes: a token on a remerge-looking line, and a quoted path holding a newline.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round-4 validation of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
2026-11-09_flood4r2_val_m1-r4_real_engine.py's s07 used a value built with step 31, which is not coprime with the
62-character alphabet, so it alternated two characters and no rule could fire: a harness defect, not a result. This
re-runs s07 with a coprime step. s11b showed a finding losing its commit through round 4's filter when a conflicted
path holds a newline and the word "commit"; c1 asks whether the same happens in an ORDINARY commit (no merge, no
--remerge-diff, no filter involved), i.e. whether it is gitleaks' own quoted-path handling rather than the carrier's.

Usage:
    python3 <this> --real-engine-module <that script> --r2-ci <ci.yml> --r4-ci <ci.yml> --engine <gitleaks> --repo-config <dir> --out <dir>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load(path: Path):
    spec = importlib.util.spec_from_file_location("val_m1_r4_real_engine", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["val_m1_r4_real_engine"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real-engine-module", required=True, type=Path)
    ap.add_argument("--r2-ci", required=True, type=Path)
    ap.add_argument("--r4-ci", required=True, type=Path)
    ap.add_argument("--engine", required=True, type=Path)
    ap.add_argument("--repo-config", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    m = load(args.real_engine_module)
    out = args.out / "engine-shapes"
    engine_bin = out / "engine-bin"
    rows = {}

    def both(name: str, repo, base: str, head: str, n: str) -> None:
        row = {}
        for label, ci in (("r4", args.r4_ci), ("r2", args.r2_ci)):
            r = m.run_step(ci, repo, base, head, n, str(engine_bin))
            (out / f"{name}.{label}.log").write_text(r.pop("_log"), encoding="utf-8")
            row[label] = {k: r[k] for k in ("rc", "found", "notes")}
        rows[name] = row
        print(json.dumps({name: row}))

    # s07 again, coprime step: an added line that starts "remerge CONFLICT" and holds a token.
    r = m.Repo(out / "s07fix" / "repo", args.repo_config)
    base = r.head()
    c1 = r.commit("pr/looks.txt", "remerge CONFLICT (content): Merge conflict in x GITHUB_TOKEN=" + m.pat(13, 5) + "\n")
    both("s07fix_remerge_looking_line_in_commit", r, base, c1, "1")
    # c1: an ordinary commit adding the newline path (first) and a token file (later) - no merge at all.
    r = m.Repo(out / "c1" / "repo", args.repo_config)
    base = r.head()
    r.write("conf/odd\nthe commit name.txt", "a\n")
    r.write("zz/tok.txt", "GITHUB_TOKEN=" + m.pat(53) + "\n")
    r.git("add", "-A")
    r.git("commit", "-q", "--no-verify", "-m", "ordinary commit")
    c = r.head()
    both("c1_ordinary_commit_newline_commit_path_then_token", r, base, c, "1")
    # c2: the same without the word "commit" in the newline path.
    r = m.Repo(out / "c2" / "repo", args.repo_config)
    base = r.head()
    r.write("conf/odd\nthe other name.txt", "a\n")
    r.write("zz/tok.txt", "GITHUB_TOKEN=" + m.pat(53) + "\n")
    r.git("add", "-A")
    r.git("commit", "-q", "--no-verify", "-m", "ordinary commit")
    c = r.head()
    both("c2_ordinary_commit_newline_path_then_token", r, base, c, "1")
    # c3: an ordinary MODIFY of the newline path holding "commit" (quoted --- and +++ lines), then a token file.
    r = m.Repo(out / "c3" / "repo", args.repo_config)
    r.commit("conf/odd\nthe commit name.txt", "a\nb\n", "add it")
    base = r.head()
    r.write("conf/odd\nthe commit name.txt", "a\nB2\n")
    r.write("zz/tok.txt", "GITHUB_TOKEN=" + m.pat(53) + "\n")
    r.git("add", "-A")
    r.git("commit", "-q", "--no-verify", "-m", "ordinary modify")
    c = r.head()
    both("c3_ordinary_modify_newline_commit_path_then_token", r, base, c, "1")
    # s11c/s11d: the token is IN the newline path's conflict resolution (no other token), with and without "commit".
    for tag, nl in (("c", "conf/odd\nthe commit name.txt"), ("d", "conf/odd\nthe other name.txt")):
        r = m.Repo(out / f"s11{tag}" / "repo", args.repo_config)
        base, merge, head = m.conflict_merge(r, nl, "a\nb\nc\n", "a\nPR\nc\n", "a\nBASE\nc\n", "a\nGITHUB_TOKEN=" + m.pat(47) + "\nc\n")
        (out / f"s11{tag}.plain-remerge.txt").write_text(r.git("log", "-p", "-U0", "--remerge-diff", "-1", merge), encoding="utf-8")
        both(f"s11{tag}_token_in_newline_path_resolution_merge_{merge[:8]}", r, base, head, "3")
    (out / "controls.json").write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
