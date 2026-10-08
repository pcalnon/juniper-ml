#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_disposition_render.py -- render flood-3's per-PR record from data + live GitHub state.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: `2026-10-08_fleet_flood3_disposition.json` (the verdicts), `2026-10-08_fleet_flood3_pr_actions.py close`

WHY THIS EXISTS

A 116-row disposition written by hand drifts from the PRs it describes the moment anything merges.
The verdicts (quality, priority, route, notes) are judgement and live in the JSON; the OUTCOME
(merged / closed / still open, and the carrier's state) is a fact and is read live, per PR, at
render time. A row whose live state contradicts its route is printed as a MISMATCH, never smoothed.

Modes:
    --markdown <out.md>      per-repo tables for the notes record / the final report
    --closes <dir>           one comment file per PR to close + closes.json for `pr_actions close`;
                             a carried/superseded PR whose carrier is not MERGED is SKIPPED (reported)

Usage:
    2026-10-08_fleet_flood3_disposition_render.py --data <json> [--markdown OUT] [--closes DIR]

Exit: 0 rendered with no mismatch; 1 at least one MISMATCH or skipped close; 2 bad input / read failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys
from pathlib import Path

OWNER = "pcalnon"
REPO_ORDER = ["juniper-ml", "juniper-data", "juniper-canopy", "juniper-cascor", "juniper-data-client", "juniper-deploy", "juniper-cascor-client", "juniper-cascor-worker"]
NOTES = "notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md"


def pr_state(repo: str, n: int, cache: dict) -> dict:
    key = (repo, n)
    if key not in cache:
        res = subprocess.run(["gh", "api", f"repos/{OWNER}/{repo}/pulls/{n}", "--jq", "{state, merged, merge_commit_sha, title, merged_at, closed_at}"], capture_output=True, text=True, timeout=120, check=False)  # nosec B603 B607
        if res.returncode != 0:
            raise RuntimeError(f"{repo}#{n}: {res.stderr.strip()[:200]}")
        cache[key] = json.loads(res.stdout)
    return cache[key]


def carrier_of(entry: dict, carriers: dict) -> int | None:
    c = entry.get("carrier")
    if c is None or isinstance(c, int):
        return c
    return (carriers.get(entry["repo"]) or {}).get(c)


def outcome(entry: dict, live: dict, carrier: int | None, carrier_live: dict | None) -> tuple[str, bool]:
    """(text, consistent) for one PR."""
    route = entry["route"]
    if live["merged"]:
        return (f"**merged** `{(live['merge_commit_sha'] or '')[:8]}`", route == "merged")
    if route == "merged":
        return (f"open -- merge pending ({live['state']})", live["state"] == "open")
    target = f"#{carrier}" if carrier else "--"
    c_merged = bool(carrier_live and carrier_live.get("merged"))
    if route == "carried":
        text = f"carried in {target}" + ("" if c_merged else " (carrier not merged yet)")
    elif route == "superseded":
        text = f"superseded; unique content in {target}" if carrier else "superseded"
    elif route == "wrong":
        text = "closed -- incorrect on main"
    else:
        text = f"{route}"
    text += "; **closed**" if live["state"] == "closed" else "; open"
    return text, True


def render_markdown(data: dict, cache: dict) -> tuple[str, int]:
    carriers = data["carriers"]
    mismatches = 0
    out: list[str] = []
    for repo in REPO_ORDER:
        rows = [e for e in data["prs"] if e["repo"] == repo]
        if not rows:
            continue
        out.append(f"### {repo} ({len(rows)})\n")
        out.append("| PR | title | kind | quality | prio | outcome | evaluation |")
        out.append("|---|---|---|---|---|---|---|")
        for e in sorted(rows, key=lambda r: r["pr"]):
            live = pr_state(repo, e["pr"], cache)
            carrier = carrier_of(e, carriers)
            carrier_live = pr_state(repo, carrier, cache) if carrier else None
            text, ok = outcome(e, live, carrier, carrier_live)
            if not ok:
                mismatches += 1
                text = f"MISMATCH (route={e['route']}): {text}"
            title = live["title"].replace("|", "\\|")
            note = (e.get("note") or "").replace("|", "\\|")
            out.append(f"| #{e['pr']} | {title} | {e['kind']} | {e.get('quality') or '-'} | {e.get('priority') or '-'} | {text} | {note} |")
        out.append("")
    return "\n".join(out), mismatches


def comment_for(e: dict, carrier: int | None, carrier_live: dict | None, repo_title: str) -> str:
    q = f"quality **{e.get('quality')}**, priority **{e.get('priority')}**"
    sha = ((carrier_live or {}).get("merge_commit_sha") or "")[:8]
    record = f"Full per-PR record: juniper-ml `{NOTES}`."
    if e["route"] == "carried":
        head = f"**Carried, not rejected.** This PR's content landed in #{carrier} (**merged** `{sha}`), which consolidates this repo's Cursor flood-3 PRs that edit the same files and therefore conflict with each other by construction."
    elif e["route"] == "superseded":
        if carrier:
            head = f"**Superseded.** A sibling covers the same ground better; this PR's unique content landed in #{carrier} (**merged** `{sha}`)."
        else:
            head = "**Superseded.** The change this PR makes is already on `main`."
    else:
        head = "**Closed: incorrect on `main`.**"
    return "\n\n".join([head, f"Evaluation (2026-10-08 flood-3 disposition): {q}. {e.get('note', '')}", record])


def render_closes(data: dict, cache: dict, out_dir: Path) -> int:
    carriers = data["carriers"]
    out_dir.mkdir(parents=True, exist_ok=True)
    spec, skipped = [], 0
    for e in data["prs"]:
        if e["route"] not in ("carried", "superseded", "wrong"):
            continue
        live = pr_state(e["repo"], e["pr"], cache)
        if live["state"] != "open":
            continue
        carrier = carrier_of(e, carriers)
        # A NAMED carrier slot ("docs", "tests", "consolidation") that resolves to nothing means the
        # consolidation PR does not exist yet -- that is "not merged", never "no carrier needed".
        # Only a literal null carrier (e.g. a PR superseded by work already on main) closes ungated.
        if isinstance(e.get("carrier"), str) and carrier is None:
            print(f"SKIP {e['repo']}#{e['pr']}: carrier slot {e['carrier']!r} not opened yet")
            skipped += 1
            continue
        carrier_live = pr_state(e["repo"], carrier, cache) if carrier else None
        if carrier and not (carrier_live or {}).get("merged"):
            print(f"SKIP {e['repo']}#{e['pr']}: carrier #{carrier} not merged")
            skipped += 1
            continue
        path = out_dir / f"{e['repo']}-{e['pr']}.md"
        path.write_text(comment_for(e, carrier, carrier_live, live["title"]) + "\n", encoding="utf-8")
        spec.append({"repo": e["repo"], "pr": e["pr"], "carrier": carrier, "comment_file": str(path)})
    (out_dir / "closes.json").write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8")
    print(f"{len(spec)} close(s) ready -> {out_dir / 'closes.json'}; {skipped} skipped")
    return 1 if skipped else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--markdown")
    ap.add_argument("--closes")
    args = ap.parse_args(argv)
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    cache: dict = {}
    rc = 0
    try:
        if args.markdown:
            md, mismatches = render_markdown(data, cache)
            Path(args.markdown).write_text(md + "\n", encoding="utf-8")
            print(f"markdown -> {args.markdown} ({mismatches} mismatch(es))")
            rc = max(rc, 1 if mismatches else 0)
        if args.closes:
            rc = max(rc, render_closes(data, cache, Path(args.closes)))
    except RuntimeError as exc:
        print(f"READ-FAILED {exc}", file=sys.stderr)
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
