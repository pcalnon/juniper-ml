"""
Flood-4 validation (fidelity lens): trace every carrier hunk to a draft's own merge-base..head hunk.

For each draft: verify the local ref against GitHub's headRefOid (gh, read-only), compute its merge-base
with origin/main and its own per-file diff. For the carrier (BASE..TREE): every added line is looked up
among the drafts' added lines for the same file; every deleted main line is listed with the drafts that
also delete it and whether main added it after some draft's merge-base (a reverted main change). A
whole-file-copy screen compares each touched file's carrier blob with each draft's head blob. Finally the
drafts' own diffs are re-applied (--3way, into a throwaway index only) onto BASE and the result diffed
against TREE: that residual must be exactly the manifest's recorded fixes and drops.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"
DRAFTS = [2466, 2419, 2427, 2430, 2436, 2439, 2441, 2443, 2445, 2447, 2451, 2458, 2461, 2463, 2425, 2413, 2414, 2416, 2429, 2431, 2434, 2421, 2448, 2459, 2410, 2455, 2403, 2407]
DOCS_DRAFTS = [2424, 2432]
NO_REAPPLY = {2403, 2407}  # conflicted; the builder rebuilt them from main's blob


def git(*args: str, env: dict[str, str] | None = None, check: bool = True, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=HERE, check=check, capture_output=True, text=True, env=env, input=stdin)


def parse_diff(text: str) -> dict[str, dict[str, list[str]]]:
    files: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"+": [], "-": []})
    cur = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            cur = None
        elif line.startswith("+++ "):
            p = line[4:]
            cur = p[2:] if p.startswith("b/") else None
        elif line.startswith("--- "):
            p = line[4:]
            if p != "/dev/null":
                cur = p[2:]
        elif cur and line.startswith("+") and not line.startswith("+++"):
            files[cur]["+"].append(line[1:])
        elif cur and line.startswith("-") and not line.startswith("---"):
            files[cur]["-"].append(line[1:])
    return files


def word_delta(old: str, new: str) -> list[str]:
    a, b = old.split(" "), new.split(" ")
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op != "equal":
            out.append(f"{op}: [{' '.join(a[i1:i2])}] -> [{' '.join(b[j1:j2])}]")
    return out


def main() -> int:
    out = Path(sys.argv[1])
    report: dict[str, object] = {}
    heads: dict[int, str] = {}
    mbs: dict[int, str] = {}
    draft_diff: dict[int, dict[str, dict[str, list[str]]]] = {}
    draft_status: dict[int, list[str]] = {}
    gh_check = {}
    for n in DRAFTS + DOCS_DRAFTS:
        heads[n] = git("rev-parse", f"refs/flood4/pr/{n}").stdout.strip()
        r = subprocess.run(["gh", "pr", "view", str(n), "--repo", "pcalnon/juniper-ml", "--json", "headRefOid,state,isDraft,baseRefName"], capture_output=True, text=True)
        info = json.loads(r.stdout) if r.returncode == 0 else {"error": r.stderr.strip()}
        gh_check[n] = {"local": heads[n], "github": info.get("headRefOid"), "match": info.get("headRefOid") == heads[n], "state": info.get("state"), "isDraft": info.get("isDraft"), "base": info.get("baseRefName")}
        mbs[n] = git("merge-base", BASE, heads[n]).stdout.strip()
        draft_diff[n] = parse_diff(git("diff", "--no-renames", mbs[n], heads[n]).stdout)
        draft_status[n] = git("diff", "--no-renames", "--name-status", mbs[n], heads[n]).stdout.splitlines()
    report["gh_heads"] = gh_check
    report["merge_bases"] = mbs
    report["draft_files"] = draft_status

    carrier = parse_diff(git("diff", "--no-renames", BASE, TREE).stdout)
    untraced: dict[str, list[str]] = {}
    traced_by: dict[str, Counter[int]] = {}
    minus_report: dict[str, list[dict[str, object]]] = {}
    for path, pm in sorted(carrier.items()):
        if path.startswith("util/ad-hoc/"):
            continue
        pool: dict[int, Counter[str]] = {n: Counter(draft_diff[n].get(path, {"+": []})["+"]) for n in DRAFTS + DOCS_DRAFTS}
        miss = []
        tb: Counter[int] = Counter()
        for line in pm["+"]:
            who = [n for n in pool if pool[n][line] > 0]
            if who:
                tb[who[0]] += 1
            elif line.strip():
                miss.append(line)
        untraced[path] = miss
        traced_by[path] = tb
        rows = []
        for line in pm["-"]:
            removers = [n for n in DRAFTS + DOCS_DRAFTS if line in draft_diff[n].get(path, {"-": []})["-"]]
            main_added_after = []
            for n in DRAFTS + DOCS_DRAFTS:
                if path in draft_diff[n]:
                    md = parse_diff(git("diff", "--no-renames", mbs[n], BASE, "--", path).stdout).get(path, {"+": []})["+"]
                    if line in md:
                        main_added_after.append(n)
            best = None
            for cand in pm["+"]:
                ratio = difflib.SequenceMatcher(a=line, b=cand, autojunk=False).ratio()
                if best is None or ratio > best[0]:
                    best = (ratio, cand)
            rows.append({"line": line[:300], "drafts_deleting_it": removers, "main_added_after_mb_of": main_added_after, "closest_added": (best[1][:300] if best else None), "ratio": round(best[0], 3) if best else None, "word_delta": word_delta(line, best[1]) if best and best[0] > 0.5 else []})
        minus_report[path] = rows
    report["untraced_added_lines"] = {k: v for k, v in untraced.items() if v}
    report["traced_added_line_counts"] = {k: dict(v) for k, v in traced_by.items()}
    report["deleted_or_altered_main_lines"] = {k: v for k, v in minus_report.items() if v}

    # whole-file-copy screen: carrier blob == a draft's head blob for a file main moved since that draft's mb
    stale = []
    for n in DRAFTS + DOCS_DRAFTS:
        for row in draft_status[n]:
            status, path = row.split("\t", 1)
            if status == "D":
                continue
            cb = git("rev-parse", f"{TREE}:{path}", check=False).stdout.strip()
            hb = git("rev-parse", f"{heads[n]}:{path}", check=False).stdout.strip()
            mbb = git("rev-parse", f"{mbs[n]}:{path}", check=False).stdout.strip()
            bb = git("rev-parse", f"{BASE}:{path}", check=False).stdout.strip()
            moved = (mbb != bb)
            stale.append({"pr": n, "path": path, "status": status, "carrier_eq_draft_head": cb == hb, "main_moved_since_mb": moved, "in_carrier": path in carrier, "suspect": bool(cb == hb and moved)})
    report["whole_file_screen"] = stale

    # re-apply each draft's own diff into a throwaway index, diff against TREE
    idx = HERE / "tmp" / "flood4_val_fidelity_index"
    idx.parent.mkdir(parents=True, exist_ok=True)
    if idx.exists():
        idx.unlink()
    env = dict(os.environ, GIT_INDEX_FILE=str(idx))
    git("read-tree", BASE, env=env)
    apply_log = {}
    for n in DRAFTS:
        if n in NO_REAPPLY:
            continue
        patch = git("diff", "--no-renames", "--binary", mbs[n], heads[n]).stdout
        r = git("apply", "--cached", "--3way", "-", env=env, check=False, stdin=patch)
        apply_log[n] = {"rc": r.returncode, "stderr": r.stderr.strip()[-600:]}
    reapplied = git("write-tree", env=env).stdout.strip()
    report["reapply"] = {"tree": reapplied, "apply": apply_log}
    resid = git("diff", "--no-renames", "--stat=200", reapplied, TREE).stdout
    report["reapply_vs_carrier_stat"] = resid
    (out.parent / "reapply_vs_carrier.patch").write_text(git("diff", "--no-renames", reapplied, TREE).stdout)
    idx.unlink()
    out.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print("gh mismatches:", [n for n, v in gh_check.items() if not v["match"]])
    print("untraced added lines:", {k: len(v) for k, v in untraced.items() if v})
    print("deleted/altered main lines:", {k: len(v) for k, v in minus_report.items() if v})
    print("whole-file suspects:", [(s["pr"], s["path"]) for s in stale if s["suspect"]])
    print("reapply:", {n: v["rc"] for n, v in apply_log.items() if v["rc"] != 0})
    print(resid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
