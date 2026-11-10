"""
Line-level fidelity of juniper-data's flood-4 docs carrier against its drafts' own hunks (flood-4 docs validator).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-data docs carrier validation (juniper-data #509, #510, #511, #515)

Usage: python3 2026-11-07_flood4_val_data_docs_fidelity.py <juniper-data repo> <base sha> <validator worktree> <out dir>

<validator worktree> is a checkout of <base sha> with the carrier's changed files copied in (uncommitted).
Each draft's own hunks are <from>..<head>: #509 from e7182b2's parent (only the Cursor commit is carried), the
others from merge-base(<base>, head). Reports, per file:
  carrier-added lines no draft adds, draft-added lines the carrier lacks,
  carrier-removed lines no draft removes (main content the carrier drops), and the 512-char line census.
Read-only.
"""

import json
import os
import subprocess
import sys

DRAFTS = {
    509: ("refs/flood4/pr/509", "e7182b23d088595a115130b001f9bdbf65186190^"),
    510: ("refs/flood4/pr/510", None),
    511: ("refs/flood4/pr/511", None),
    515: ("refs/flood4/pr/515", None),
}


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def parse_u0(diff_text):
    """{path: {"add": [lines], "del": [lines]}} from a -U0 diff."""
    out = {}
    path = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            if path is not None:
                out.setdefault(path, {"add": [], "del": []})
        elif line.startswith("--- "):
            continue
        elif path and line.startswith("+"):
            out[path]["add"].append(line[1:])
        elif path and line.startswith("-"):
            out[path]["del"].append(line[1:])
    return out


def main():
    repo, base, wt, out_dir = sys.argv[1:5]
    report = {"drafts": {}, "carrier_extra_add": {}, "draft_add_missing": {}, "carrier_del_unexplained": {}, "long_lines": []}
    draft_diffs = {}
    for n, (ref, frm) in DRAFTS.items():
        head = git(repo, "rev-parse", ref).strip()
        if frm is None:
            frm = git(repo, "merge-base", base, head).strip()
        else:
            frm = git(repo, "rev-parse", frm).strip()
        d = parse_u0(git(repo, "diff", "-U0", frm, head, "--", "docs", "CHANGELOG.md"))
        draft_diffs[n] = d
        report["drafts"][n] = {"head": head, "from": frm, "files": {p: {"add": len(v["add"]), "del": len(v["del"])} for p, v in d.items()}}
    carrier = parse_u0(git(wt, "diff", "-U0", base, "--", "docs", "CHANGELOG.md"))
    for path, v in carrier.items():
        d_add = set()
        d_del = set()
        for d in draft_diffs.values():
            if path in d:
                d_add.update(d[path]["add"])
                d_del.update(d[path]["del"])
        extra = [ln for ln in v["add"] if ln not in d_add]
        if extra:
            report["carrier_extra_add"][path] = extra
        unexplained = [ln for ln in v["del"] if ln not in d_del]
        if unexplained:
            report["carrier_del_unexplained"][path] = unexplained
        for ln in v["add"]:
            if len(ln) > 512:
                report["long_lines"].append({"path": path, "len": len(ln), "start": ln[:80]})
    for n, d in draft_diffs.items():
        for path, v in d.items():
            c_add = set(carrier.get(path, {}).get("add", []))
            missing = [ln for ln in v["add"] if ln not in c_add]
            if missing:
                report["draft_add_missing"].setdefault(path, []).append({"pr": n, "lines": missing})
            c_del = set(carrier.get(path, {}).get("del", []))
            not_deleted = [ln for ln in v["del"] if ln not in c_del]
            if not_deleted:
                report.setdefault("draft_del_not_in_carrier", {}).setdefault(path, []).append({"pr": n, "lines": not_deleted})
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "fidelity.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print("drafts:", json.dumps(report["drafts"], indent=1))
    for key in ("carrier_extra_add", "draft_add_missing", "carrier_del_unexplained", "draft_del_not_in_carrier"):
        section = report.get(key, {})
        print(f"\n=== {key}: {sum(len(v) for v in section.values())} entries")
        for path, items in section.items():
            for it in items:
                if isinstance(it, dict):
                    for ln in it["lines"]:
                        print(f"  [{path}] #{it['pr']}: {ln[:230]}")
                else:
                    print(f"  [{path}]: {it[:230]}")
    print(f"\n=== long_lines (>512): {len(report['long_lines'])}")
    for it in report["long_lines"]:
        print(f"  {it['path']} len={it['len']} {it['start']}")


if __name__ == "__main__":
    main()
