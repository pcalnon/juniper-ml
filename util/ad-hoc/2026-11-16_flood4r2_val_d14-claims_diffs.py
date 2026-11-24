"""
Write a unified diff of every changed text file of the two D-14 carriers against its base blob, and against today's origin/main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator MN2, claims lens, flood-4 session 9)
Created: 2026-11-16
Status: ad-hoc - investigation
Retire when: RETAINED - ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Cursor flood-4 disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)

Usage: python3 <this file>
Reads blobs with `git show` in the validator's OWN juniper-ml worktree and in the juniper-cascor primary's object store
(read-only), writes base/main/carrier copies and diffs under <scratch>/diffs/. Read-only on both carriers.
"""

import difflib
import json
import subprocess
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
O = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
ML = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d"
CC = JUNIPER / "worktrees" / "juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d"
CASCOR_PRIMARY = JUNIPER / "juniper-cascor"
SCRATCH = O / "tmp" / "flood4r2-val" / "d14-claims-lens" / "diffs"

REPOS = {
    "ml": {"carrier": ML, "git": O, "base": "f181856f4d0ab797b281e99d3547ab379b257dc8"},
    "cascor": {"carrier": CC, "git": CASCOR_PRIMARY, "base": "1de9c6f76523bd0887a0a72835b173469ad102d7"},
}


def blob(git_dir, rev, path):
    res = subprocess.run(["git", "-C", str(git_dir), "show", f"{rev}:{path}"], capture_output=True, check=False)
    if res.returncode != 0:
        return None
    return res.stdout.decode("utf-8")


def rev_parse(git_dir, rev):
    res = subprocess.run(["git", "-C", str(git_dir), "rev-parse", rev], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def udiff(old, new, a, b):
    return "".join(difflib.unified_diff((old or "").splitlines(keepends=True), (new or "").splitlines(keepends=True), fromfile=a, tofile=b, n=3))


def main():
    summary = {}
    for key, spec in REPOS.items():
        manifest = json.loads((spec["carrier"] / "tmp" / "flood4-fix" / "d14-resume" / "manifest.json").read_text(encoding="utf-8"))
        main_sha = rev_parse(spec["git"], "origin/main")
        rows = []
        for entry in manifest["files"]:
            path = entry["path"]
            carrier_text = (spec["carrier"] / path).read_text(encoding="utf-8")
            base_text = blob(spec["git"], spec["base"], path)
            main_text = blob(spec["git"], main_sha, path)
            safe = path.replace("/", "__")
            out = SCRATCH / key
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{safe}.carrier_vs_base.diff").write_text(udiff(base_text, carrier_text, f"base/{path}", f"carrier/{path}"), encoding="utf-8")
            if base_text is not None:
                (out / f"{safe}.base").write_text(base_text, encoding="utf-8")
            if main_text is not None:
                (out / f"{safe}.main").write_text(main_text, encoding="utf-8")
                (out / f"{safe}.base_vs_main.diff").write_text(udiff(base_text, main_text, f"base/{path}", f"main/{path}"), encoding="utf-8")
            rows.append({"path": path, "base_exists": base_text is not None, "main_exists": main_text is not None, "main_changed_since_base": (base_text != main_text)})
        summary[key] = {"base": spec["base"], "main": main_sha, "files": rows}
    (SCRATCH / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for key, res in summary.items():
        moved = [r["path"] for r in res["files"] if r["main_changed_since_base"] and r["base_exists"]]
        print(f"{key}: base {res['base'][:8]} main {res['main'][:8]}; files changed on main since base: {moved}")


if __name__ == "__main__":
    main()
