#!/usr/bin/env python3
"""Resolve soak ledger rows to their subagent transcripts, and re-audit retrieval.

Project:     Juniper
Sub-Project: juniper-ml
Application: pointer-follow soak -- item E evidence recovery
Author:      Paul Calnon
Version:     0.1.0
License:     MIT

WHY THIS EXISTS
---------------
`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` Sec 4.8
records that two retrieval standards are live in one corpus: 8 follows were
scored on tool OUTPUT and 18 on tool INPUT, so the headline rate is 60.5% as
scored and 41.9% if only the input-scored follows count. Nobody has ratified a
standard, and the 8 output-scored rows -- all dated 2026-08-22 -- were never
re-audited (ml#1644's re-audit covered only the automated 2026-09-03/04 runs).

Two things blocked the re-audit. Both are solved here:

1. `util/ad-hoc/2026-08-21_soak_probe_evidence.py` SUBAGENT_DIRS points at a
   WORKTREE-suffixed project directory that no longer exists. Only that one
   path component is stale; the session UUID under it is correct, and the
   transcripts live under the PRIMARY project directory.

2. 41 of the 49 ledger rows carry hand-written session labels (`soak-A-P02`)
   rather than session UUIDs, and the label->file mapping was recorded nowhere.
   It is nonetheless recoverable: each transcript's sidecar
   `agent-<id>.meta.json` carries a `description` that BEGINS WITH THE PROBE ID
   ("P02 assert release tag"), and the transcript's mtime orders repeat runs of
   the same probe. Probe id + mtime ordering is a 1:1 key.

WHAT IT DOES NOT DO
-------------------
It does not ratify a retrieval standard -- that is a judgement the owner makes
on this evidence. It reports, per row, what the tool layer actually shows:
whether the destination appeared in a tool INPUT, in a tool RESULT, or in
neither. It does not modify the ledger.

MATCHING IS REPORTED, NOT ASSUMED. Where a probe's transcript count and its
observation count disagree, every candidate is printed and the row is marked
AMBIGUOUS rather than silently bound to the nearest file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# The transcripts. The stale entry is kept, last, so a host that still has the
# old worktree-suffixed directory keeps working.
PROJECT_DIRS = [
    Path.home() / ".claude/projects" / "-home-pcalnon-Development-python-Juniper-juniper-ml",
    Path.home() / ".claude/projects"
    / "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-giggly-marinating-backus",
]
SESSION_UUID = "bf50124e-6fde-4314-bdca-0ca7876b8efb"

DEST = "docs/REFERENCE.md"
ANSWER_KEY = "conf/soak_probes.json"
PROTOCOL_DOC = "POINTER-FOLLOW-SOAK-LEDGER"

# THE LEDGER ITSELF IS AN ANSWER SHEET, and neither marker above covers it.
# `reports/soak/pointer_follow_soak.jsonl` carries, per record, the probe's
# `pointer`, its scored `outcome`, and a `note` restating the correct answer in
# prose. A subject running an unscoped `grep -rn <term> .` from the repo root
# matches it, and is then shown the previous run's answer AND its scoring.
LEDGER_FILE = "pointer_follow_soak"
LEDGER_MARKERS = ('"obs_id"', "'obs_id'", LEDGER_FILE)

# A grep -rn emits `path:LINE:text`; a grep -rl emits `path` alone. Only the
# first is the document's CONTENT coming back.
CONTENT_RE = re.compile(re.escape(DEST) + r":\d+:")

# Every checkout of juniper-ml, including its worktrees, is the same document.
# A same-named file in a SIBLING repo is a different one -- and 7 of the 8
# siblings ship their own `docs/REFERENCE.md` (every one but juniper-recurrence,
# measured 2026-09-08), so the instrument's `hit = doc in blob` substring test
# cannot tell them apart.
# Both entries end at a segment boundary. A bare "/juniper-ml" is a PREFIX and
# matched `/juniper-mlx/` and `/juniper-ml-scratch/` -- a third repo's file
# claimed as ours.
ML_ROOTS = ("juniper-ml/", "juniper-ml--")
CD_RE = re.compile(r"cd\s+(/[\w./-]+)")
PATH_CHARS = re.compile(r"[\w./~-]")
SIBLING_REPOS = (
    "juniper-cascor-client/", "juniper-cascor-worker/", "juniper-data-client/",
    "juniper-recurrence-client/", "juniper-recurrence-model/",
    "juniper-cascor/", "juniper-canopy/", "juniper-data/", "juniper-deploy/",
    "juniper-recurrence/", "juniper-legacy/",
)

# Mechanism classes for a destination hit.
M_CONTENT = "content"     # the document's text came back, or it was opened by name
M_FILENAME = "filename"   # only its NAME came back (grep -l, ls) -- not read
M_FOREIGN = "foreign"     # a same-named file in another repo
M_LEDGER = "ledger"       # the match is inside the soak ledger's own JSON

# Sec 4 of the ledger defines FOLLOW as "opened the destination, grepped it, or
# otherwise read it". Both of these are tool-layer evidence. Model prose that
# merely NAMES the file is neither, and is never counted here -- that conflation
# is the defect ml#1644 fixed.
STANDARD_INPUT = "input"      # destination path appeared in a tool_use input
STANDARD_RESULT = "result"    # destination content came back in a tool_result


def subagent_dirs() -> list[Path]:
    return [d / SESSION_UUID / "subagents" for d in PROJECT_DIRS]


def load_ledger(path: Path) -> list[dict]:
    """Return EVERY observation, rescores applied, flagged valid/invalidated.

    Invalidated rows are kept because they still consumed a transcript. Dropping
    them first is what made the ordinal binding mis-align: a probe with 3
    transcripts and 2 surviving observations looks like a count mismatch when in
    fact the third transcript belongs to the invalidated row.
    """
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    obs = [r for r in rows if r.get("kind") == "observation"]
    invalidated = {r["invalidates"] for r in rows if r.get("kind") == "invalidate"}
    rescores = {r["rescores"]: r for r in rows if r.get("kind") == "rescore"}

    out = []
    for r in obs:
        row = dict(r)
        row["valid"] = r["obs_id"] not in invalidated
        rs = rescores.get(r["obs_id"])
        if rs:
            row["outcome"] = rs["to_outcome"]
            row["rescored_from"] = rs["from_outcome"]
        out.append(row)
    out.sort(key=lambda r: r["ts"])
    return out


UUID_LEN = 36


def is_uuid(session: str) -> bool:
    return len(session) == UUID_LEN and session.count("-") == 4


def find_uuid_transcript(session: str) -> Path | None:
    """A UUID-session row's transcript is a top-level `<uuid>.jsonl`.

    The automated 2026-09-03/04 runs were dispatched from a worktree session, so
    their transcripts sit under that worktree's own project directory -- not
    under the pilot's `subagents/` dir. Search every project directory.
    """
    root = Path.home() / ".claude/projects"
    if not root.exists():
        return None
    for proj in root.iterdir():
        cand = proj / f"{session}.jsonl"
        if cand.exists():
            return cand
    return None


def probe_num(probe_id: str) -> str:
    """`P02-assert-release-tag-ref` -> `P02`."""
    return probe_id.split("-", 1)[0]


def discover_transcripts() -> dict[str, list[dict]]:
    """Map probe number -> [{path, mtime, description}], oldest first."""
    found: dict[str, list[dict]] = {}
    for d in subagent_dirs():
        if not d.exists():
            continue
        for meta in d.glob("*.meta.json"):
            try:
                info = json.loads(meta.read_text())
            except json.JSONDecodeError:
                continue
            desc = (info.get("description") or "").strip()
            head = desc.split(" ", 1)[0]
            # Only descriptions that BEGIN with a probe id are probe runs; the
            # threshold-analysis and handoff-validation agents share the dir.
            if not (len(head) == 3 and head[0] == "P" and head[1:].isdigit()):
                continue
            jsonl = meta.with_name(meta.name.replace(".meta.json", ".jsonl"))
            if not jsonl.exists():
                continue
            found.setdefault(head, []).append(
                {
                    "path": jsonl,
                    "mtime": datetime.fromtimestamp(jsonl.stat().st_mtime, timezone.utc),
                    "description": desc,
                }
            )
    for runs in found.values():
        runs.sort(key=lambda r: r["mtime"])
    return found


def classify_occurrences(where: str, blob: str, cmd: str) -> list[str]:
    """Say what EACH destination occurrence actually is.

    Counting hits answers an adjacent question. Some of the output-scored
    follows rest on a hit that is not the destination document: a `grep -rl`
    filename list, a sibling repo's same-named file, and the soak ledger's own
    note. Each is measured, and each was counted as retrieval by the existing
    screen.

    PER OCCURRENCE, not per result. One `grep -rn` result can carry six
    occurrences of the path in different roles -- a genuine content line, and
    the ledger's note quoting the same path. Classifying a result by its FIRST
    occurrence reports whichever happened to sort first.
    """
    cd = CD_RE.search(cmd or "")
    foreign_cwd = bool(cd) and not any(r in cd.group(1) + "/" for r in ML_ROOTS)

    out = []
    start = 0
    while True:
        idx = blob.find(DEST, start)
        if idx < 0:
            break
        start = idx + len(DEST)
        if where == "result":
            # The transcript's content is itself JSON, so json.dumps() escapes
            # its inner quotes: the ledger's `"obs_id"` reaches here as
            # `\"obs_id\"` and a literal-quote marker never matches. Dropping
            # backslashes before the test costs nothing and catches both forms.
            window = blob[max(0, idx - 400):idx + 200].replace("\\", "")
            if any(m in window for m in LEDGER_MARKERS):
                out.append(M_LEDGER)
                continue
        # A sibling repo reaches the transcript two ways: the subject `cd`s into
        # it, or names it in the path argument. Read the path segment BEFORE the
        # occurrence FIRST -- an explicitly qualified path outranks the cwd in
        # both directions.
        #
        # ORDER IS LOAD-BEARING. Testing `foreign_cwd` first discards the whole
        # input, so a subject that ran `cd <ECOSYSTEM PARENT> && sed -n … \
        # juniper-ml/docs/REFERENCE.md` had a genuine read of OUR file thrown
        # away: the parent directory matches no `juniper-ml` root segment. That
        # is a false-negative generator, and it is what produced the original
        # 51.2% headline. Found by Lane A review 2026-09-09.
        # Walk back to the start of the PATH TOKEN, not a fixed-width text
        # window: a window is not a path, so a grep PATTERN that merely mentions
        # our path scored as a read of it. Proximity decides, not list order.
        head = idx
        while head > 0 and PATH_CHARS.match(blob[head - 1]):
            head -= 1
        token = blob[head:idx]
        if any(s in token for s in SIBLING_REPOS):
            out.append(M_FOREIGN)
            continue
        if not any(r in token for r in ML_ROOTS) and foreign_cwd:
            out.append(M_FOREIGN)
            continue
        if where == "input":
            out.append(M_CONTENT)
            continue
        # `grep -rn` emits `path:LINE:text` at the occurrence; `grep -rl` emits
        # the bare path. Anchor the test AT the occurrence -- searching the whole
        # blob lets one content line launder every filename-only hit beside it.
        out.append(M_CONTENT if CONTENT_RE.match(blob, idx) else M_FILENAME)
    return out


def scan(path: Path) -> dict:
    """Classify every destination hit in a transcript by mechanism.

    Deliberately a re-implementation rather than an import: the screen in
    `util/ad-hoc/2026-08-21_soak_probe_evidence.py` is dated and unwired, and an
    independent read is the point of a re-audit.
    """
    counts = {M_CONTENT: 0, M_FILENAME: 0, M_FOREIGN: 0, M_LEDGER: 0}
    in_input = in_result = 0
    contaminated = 0
    ledger_read = 0
    tool_calls = 0
    pending: dict[str, str] = {}

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue

        stack = [rec]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if node.get("type") == "tool_use":
                    tool_calls += 1
                    blob = json.dumps(node.get("input") or {})
                    pending[node.get("id") or ""] = blob
                    if DEST in blob:
                        in_input += 1
                        for cls in classify_occurrences("input", blob, blob):
                            counts[cls] += 1
                    if ANSWER_KEY in blob or PROTOCOL_DOC in blob:
                        contaminated += 1
                    if LEDGER_FILE in blob:
                        ledger_read += 1
                elif node.get("type") == "tool_result":
                    blob = json.dumps(node.get("content") or "")
                    cmd = pending.get(node.get("tool_use_id") or "", "")
                    if DEST in blob:
                        in_result += 1
                        for cls in classify_occurrences("result", blob, cmd):
                            counts[cls] += 1
                    if ANSWER_KEY in blob:
                        contaminated += 1
                    if LEDGER_FILE in blob or '"obs_id"' in blob.replace("\\", ""):
                        ledger_read += 1
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    return {
        "tool_calls": tool_calls,
        "in_input": in_input,
        "in_result": in_result,
        "mech": counts,
        # Retrieval that survives a mechanism check: the document's own text.
        "retrieved": counts[M_CONTENT] > 0,
        "contaminated": contaminated > 0,
        "contamination_hits": contaminated,
        # Reading the ledger is contamination the existing screen cannot see.
        "ledger_leak": ledger_read > 0,
        "ledger_hits": ledger_read,
    }


def dump_evidence(path: Path, width: int = 220) -> list[dict]:
    """Return each destination hit with the tool that produced it.

    The count alone cannot settle item E. `docs/REFERENCE.md` inside a
    tool_result may be the document's CONTENT coming back from a grep -- a
    follow under Sec 4 -- or merely its FILENAME in a directory listing or a
    `grep -l`, which is not reading it at all. Only the surrounding text
    separates the two, so a re-audit that reports counts and stops has answered
    an adjacent question.
    """
    hits = []
    pending: dict[str, str] = {}

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        stack = [rec]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if node.get("type") == "tool_use":
                    tid = node.get("id") or ""
                    name = node.get("name") or "?"
                    blob = json.dumps(node.get("input") or {})
                    pending[tid] = f"{name} {blob[:width]}"
                    if DEST in blob:
                        hits.append({"where": "input", "tool": name, "text": blob[:width]})
                elif node.get("type") == "tool_result":
                    blob = json.dumps(node.get("content") or "")
                    if DEST in blob:
                        idx = blob.find(DEST)
                        start = max(0, idx - width // 2)
                        tid = node.get("tool_use_id") or ""
                        hits.append({
                            "where": "result",
                            "tool": pending.get(tid, "(unmatched call)"),
                            "text": blob[start:start + width],
                        })
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return hits


def bind(all_obs: list[dict], transcripts: dict[str, list[dict]]) -> list[dict]:
    """Bind each observation to a transcript.

    Two disjoint mechanisms, because the corpus has two eras:

    * A row whose `session` is a real UUID (the automated 2026-09-03/04 runs) is
      bound DIRECTLY by filename. That binding is exact by construction.
    * A row whose `session` is a hand-written label (`soak-A-P02`) is bound by
      probe id + run order. Both sequences are in time order, so the k-th
      observation of a probe is the k-th transcript of that probe.

    Where a probe's transcript count and its observation count disagree the
    binding is reported `ordinal` rather than `exact` and must not be relied on:
    pilot runs were discarded for registry leakage (`conf/soak_probes.json`
    `_README`), so a surplus of transcripts is expected.

    THE COUNT IS 10, NOT 8. This docstring said 8 until 2026-09-10, when the set
    was enumerated for the first time: 57 probe-id transcripts, 40 bound, 17
    unbound, of which 7 carry a recorded retirement reason in the registry's
    `retired` block and **10** do not. All 10 screen as contaminated, so the
    discard was principled -- what was missing is a per-run record of the reason,
    and a correct count. Enumerated by
    `util/ad-hoc/2026-09-10_soak_stopping_rule/discarded_run_census.py`; analysed
    in `notes/JUNIPER_2026-09-10_JUNIPER-ML_SOAK-DISCARDED-RUN-SELECTION-ANALYSIS.md`.
    """
    labelled: dict[str, list[dict]] = {}
    bound = []
    for row in all_obs:
        if is_uuid(row["session"]):
            entry = dict(row)
            entry["probe_num"] = probe_num(row["probe_id"])
            path = find_uuid_transcript(row["session"])
            entry["transcript"] = path
            entry["binding"] = "uuid" if path else "missing"
            bound.append(entry)
        else:
            labelled.setdefault(probe_num(row["probe_id"]), []).append(row)

    for pnum, rows in sorted(labelled.items()):
        runs = transcripts.get(pnum, [])
        used: dict[Path, int] = {}
        for row in rows:
            entry = dict(row)
            entry["probe_num"] = pnum
            entry["n_obs"] = len(rows)
            entry["n_transcripts"] = len(runs)
            ts = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
            # A row is scored AFTER its run finishes, so the transcript that
            # produced it is the latest one for that probe at or before the
            # ledger timestamp. Ordinal position fails here: P02 carries two
            # observation rows for ONE run (an 08-21 miss, later invalidated,
            # and its 08-22 re-score), so counting rows against files leaves the
            # last run of that probe with nothing to bind to.
            prior = [r for r in runs if r["mtime"] <= ts]
            if prior:
                pick = max(prior, key=lambda r: r["mtime"])
                entry["transcript"] = pick["path"]
                entry["transcript_mtime"] = pick["mtime"]
                used[pick["path"]] = used.get(pick["path"], 0) + 1
                entry["binding"] = "nearest"
            else:
                entry["transcript"] = None
                entry["binding"] = "missing"
            bound.append(entry)
        # A transcript claimed by two rows means the run was scored twice; the
        # binding is still right, but the pair is not two independent runs.
        for entry in bound:
            t = entry.get("transcript")
            if t is not None and used.get(t, 0) > 1:
                entry["binding"] = "shared"
    bound.sort(key=lambda r: r["ts"])
    return bound


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ledger", type=Path, help="path to pointer_follow_soak.jsonl")
    ap.add_argument("--only-output-scored", action="store_true",
                    help="restrict to the 8 rows scored on tool output")
    ap.add_argument("--evidence", action="store_true",
                    help="dump each destination hit with the tool that produced it")
    args = ap.parse_args()

    dirs = [d for d in subagent_dirs() if d.exists()]
    if not dirs:
        print("no transcript directory found; checked:", file=sys.stderr)
        for d in subagent_dirs():
            print(f"  {d}", file=sys.stderr)
        return 3
    print(f"transcript dirs : {', '.join(str(d) for d in dirs)}")

    all_obs = load_ledger(args.ledger)
    n_valid = sum(1 for r in all_obs if r["valid"])
    transcripts = discover_transcripts()
    n_files = sum(len(v) for v in transcripts.values())
    print(f"ledger          : {len(all_obs)} observations ({n_valid} valid)")
    print(f"transcripts     : {n_files} pilot probe runs over {len(transcripts)} probes")

    bound = bind(all_obs, transcripts)

    markers = ("via-search-output", "RETRIEVED via search output")
    rows = []
    for entry in bound:
        note = entry.get("note") or ""
        # MATCH THE CONSENSUS SCRIPT'S UNIT EXACTLY. Sec 4.8 of the 09-04 review
        # counts output-scored FOLLOWS -- 8 of them. Counting every row whose
        # note carries the marker gives 9, because one `miss` row mentions it
        # too, and a 9-row set silently re-answers a question asked about 8.
        entry["scored_via_output"] = (
            any(m in note for m in markers) and entry["outcome"] == "follow"
        )
        entry["marker_in_note"] = any(m in note for m in markers)
        if not entry["valid"]:
            continue
        if args.only_output_scored and not entry["scored_via_output"]:
            continue
        rows.append(entry)

    print("\n== per-row re-audit (valid rows only) ==")
    print(f"{'ts':20s} {'probe':6s} {'outcome':16s} {'bind':8s} "
          f"{'in':>3s} {'res':>4s}  {'mechanism':26s} {'verdict':8s} {'scored':7s} flags")
    agree = disagree = unbound = 0
    for e in rows:
        via = "OUTPUT" if e["scored_via_output"] else "-"
        if e["transcript"] is None:
            print(f"{e['ts'][:19]:20s} {e['probe_num']:6s} {e['outcome']:16s} "
                  f"{'MISSING':8s} {'-':>3s} {'-':>4s}  {'-':26s} {'-':8s} {via:7s} -")
            unbound += 1
            continue
        s = scan(e["transcript"])
        mech = s["mech"]
        # RETRIEVED means the document's own text came back. A filename-only
        # hit, a sibling repo's file, and the ledger's own note are all counted
        # as retrieval by the existing screen; none of them is reading it.
        verdict = "RETRIEVED" if mech[M_CONTENT] else "NO"
        e["verdict"] = verdict
        e["mech"] = mech
        e["ledger_leak"] = s["ledger_leak"]
        parts = [f"{k}={v}" for k, v in mech.items() if v]
        flags = []
        if s["contaminated"]:
            flags.append("CONTAM")
        if s["ledger_leak"]:
            flags.append("LEDGER-LEAK")
        recorded_follow = e["outcome"] == "follow"
        evidence_follow = verdict == "RETRIEVED"
        mark = "" if recorded_follow == evidence_follow else "  <-- DIFFERS"
        if recorded_follow == evidence_follow:
            agree += 1
        else:
            disagree += 1
        print(f"{e['ts'][:19]:20s} {e['probe_num']:6s} {e['outcome']:16s} "
              f"{e['binding']:8s} {s['in_input']:3d} {s['in_result']:4d}  "
              f"{','.join(parts) or '-':26s} {verdict:8s} {via:7s} "
              f"{','.join(flags) or '-'}{mark}")

    print(f"\n  agree {agree} / differ {disagree} / unbound {unbound}")

    scored_out = [e for e in rows if e["scored_via_output"] and e.get("mech")]
    if scored_out:
        print("\n== the output-scored follows, re-audited by MECHANISM ==")
        print(f"  {len(scored_out)} output-scored follows "
              f"(Sec 4.8 of the 09-04 review counts 8)")
        survives = [e for e in scored_out if e["mech"][M_CONTENT]]
        print(f"    hit is the document's own text          : {len(survives)}")
        for cls, why in ((M_FILENAME, "filename only (grep -l) -- never read"),
                         (M_FOREIGN, "a SIBLING REPO's docs/REFERENCE.md"),
                         (M_LEDGER, "the soak ledger's own note")):
            bad = [e for e in scored_out
                   if not e["mech"][M_CONTENT] and e["mech"][cls]]
            if bad:
                print(f"    {why:40s}: {len(bad)}")
                for e in bad:
                    print(f"        {e['ts'][:19]}  {e['probe_id']}")
        print("\n  Sec 4 defines FOLLOW as 'opened the destination, grepped it, or")
        print("  otherwise read it'. Only the first line above meets that. The")
        print("  09-04 review's expectation -- that the rate holds at 60.5% under")
        print("  the protocol's own standard -- is NOT supported by the transcripts.")

    scored = [e for e in rows if e.get("mech") is not None]
    if scored:
        n = len(scored)
        as_scored = sum(1 for e in scored if e["outcome"] == "follow")
        survives = sum(1 for e in scored
                       if e["outcome"] == "follow" and e["mech"][M_CONTENT])
        input_only = sum(1 for e in scored
                         if e["outcome"] == "follow" and not e["scored_via_output"])
        print("\n== what the rate becomes ==")
        print(f"  as recorded                          : {as_scored}/{n} = "
              f"{100.0 * as_scored / n:.1f}%")
        print(f"  input-scored only (the 41.9% floor)  : {input_only}/{n} = "
              f"{100.0 * input_only / n:.1f}%")
        print(f"  survives a MECHANISM check           : {survives}/{n} = "
              f"{100.0 * survives / n:.1f}%")
        print("\n  The third line is the new one. It is not a third standard: it")
        print("  applies the protocol's OWN Sec 4 definition (inputs union results)")
        print("  and then discards hits that are not the destination document at")
        print("  all. It is BELOW the as-recorded rate, so recovering this evidence")
        print("  does not rescue the bet -- it moves the estimate further from the")
        print("  0.75 boundary, in the direction the verdict already points.")

    leaks = [e for e in rows if e.get("ledger_leak")]
    if leaks:
        print("\n== NEW: contamination the existing screen cannot see ==")
        print(f"  {len(leaks)} of {len(rows)} runs touched the soak ledger itself.")
        print("  `reports/soak/pointer_follow_soak.jsonl` records, per observation,")
        print("  the probe's `pointer`, its scored `outcome`, and a `note` restating")
        print("  the answer in prose -- so a run that reads it has seen the answer")
        print("  sheet AND the previous run's scoring. The screen in")
        print("  util/ad-hoc/2026-08-21_soak_probe_evidence.py checks only")
        print(f"  ANSWER_KEY={ANSWER_KEY!r} and PROTOCOL_DOC={PROTOCOL_DOC!r};")
        print("  the ledger's own path matches NEITHER.")
        for e in leaks:
            print(f"    {e['ts'][:19]}  {e['probe_id']:34s} outcome={e['outcome']}")

    if args.evidence:
        print("\n== destination hits, with the tool that produced each ==")
        for e in rows:
            if e["transcript"] is None:
                continue
            hits = dump_evidence(e["transcript"])
            if not hits:
                continue
            tag = "OUTPUT-SCORED" if e["scored_via_output"] else e["outcome"]
            print(f"\n-- {e['ts'][:19]}  {e['probe_id']}  [{tag}]")
            print(f"   {e['transcript'].name}")
            for h in hits[:4]:
                print(f"   [{h['where']:6s}] via {h['tool'][:100]}")
                print(f"            ...{h['text']}...")

    odd = [e for e in rows if e.get("marker_in_note") and not e["scored_via_output"]]
    if odd:
        print("\n== marker present but the row is NOT a follow ==")
        for e in odd:
            print(f"  {e['ts'][:19]}  {e['probe_id']:34s} outcome={e['outcome']}  "
                  f"evidence={e.get('verdict', '-')}")

    # A disagreement is a row scored `follow` with no surviving content hit, or
    # a row scored otherwise that HAS one. Comparing against the string
    # "NEITHER" here was a stale predicate left by the mechanism refactor: the
    # verdict vocabulary became RETRIEVED/NO, so `verdict != "NEITHER"` was
    # always true and every source-recovered row was reported as a conflict.
    weak = [e for e in rows
            if e.get("verdict")
            and (e["outcome"] == "follow") != (e["verdict"] == "RETRIEVED")]
    if weak:
        print("\n== rows whose transcript disagrees with the recorded outcome ==")
        for e in weak:
            parts = ",".join(f"{k}={v}" for k, v in e["mech"].items() if v) or "no hit"
            print(f"  {e['ts'][:19]}  {e['probe_id']:34s} recorded={e['outcome']:16s} "
                  f"evidence={parts}  ({e['binding']})")
        print("  Candidates for re-scoring, NOT re-scorings: whether a filename-only")
        print("  or sibling-repo hit counts is exactly the standard question item E")
        print("  puts to the owner. The ledger is not modified by this tool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
