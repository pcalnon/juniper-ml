#!/usr/bin/env python3
"""Archive the independent reviews of R-OBS-SC-2's follow-ups and of plan v1.15.16, verbatim, with one fix-pass record.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consolidated plan record)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- single-use archiver, with a re-check mode
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md v1.15.16 (which decides this archive);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md
         (its item 6, "Archive the reviews"); util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the same transcript lookup)

Why
---
Four reviews, each an Opus sub-agent that returned its report as its final message, shaped what R-OBS-SC-2's follow-ups
shipped: two of the ``retry-after-rounds-up`` guard and its register filing (juniper-ml#2576), and two of the juniper-cascor
0.14.0 and juniper-canopy 0.10.0 release bodies. On 2026-11-15 one report sat in a worktree's gitignored ``tmp/`` and
three existed only in session transcripts. Claude Code moves a transcript between project directories (session
1b4fec84's moved at about 03:20Z, while this archive was being prepared), and ``git worktree remove`` deletes a
worktree's ``tmp/``. So each brief and each report is copied here, verbatim, into ``reports/``. Two more reviews read
plan v1.15.16's own draft (session b9dfa450), and they are archived the same way. One file is copied as it is from a
worktree's ``tmp/``: the five PRs' validation fix pass of 2026-11-12, the only copy of findings plan v1.15.16 records.

Each transcript is found by session-id prefix under ``~/.claude/projects/*/``, never by a fixed path. A round's brief
is the agent's n-th prompt (the spawn prompt, or a message sent to the running agent); its report is the text of the
last assistant message before the next prompt. A message spread over several transcript rows is joined by message id.

Every report's sha256 is pinned below. A run refuses to write when a transcript's text no longer hashes to its pin,
and the round-1 guard report must also equal the copy its session saved (after that copy's one-line HTML comment).

Usage
-----
    python3 util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py [--check]

``--check`` writes nothing. It exits 1 when an archived file is missing or differs from what the sources give now. When
a transcript has gone, it checks the archived report against its pin instead and says so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
OUT = "reports/2026-11-15_r-obs-sc-2-follow-ups-reviews"
PROJECTS = Path.home() / ".claude" / "projects"

#: slug -> (title, session prefix, agent id, round (1-based prompt index), the report's sha256)
REVIEWS = {
    "guard-round-1": (
        "The retry-after-rounds-up guard, round 1",
        "7d425759",
        "agent-a5ec31fdeec16fafe",
        1,
        "ab6629d70f0ebb11838dbdaf0be839173519ed3a03e039b9caa3012e1e58af46",
    ),
    "guard-round-2": (
        "The APD-ECO-016 change set (guard + register), round 2",
        "1b4fec84",
        "agent-a55b11b832d780f60",
        1,
        "6c4a08a59b9acde5aa54d4d836c4d0a6bed5a90511b0d8becec36be690a6d9d1",
    ),
    "notes-round-1": (
        "The juniper-cascor v0.14.0 and juniper-canopy v0.10.0 release bodies, round 1",
        "1b4fec84",
        "agent-a1bd2c68c56b33137",
        1,
        "89c6315846421b4f5b73941db855a1ace8a9622d4739ab69e81bc472240dcc2b",
    ),
    "notes-round-2": (
        "The release-body corrections, round 2",
        "1b4fec84",
        "agent-a1bd2c68c56b33137",
        2,
        "cb5a499bd5fed541adadcf757bf24a3f32b128934328c6f8e5dfbfb8b0486ac4",
    ),
    "plan-v1-15-16-review-a": (
        "Plan v1.15.16's draft: the fact-check",
        "b9dfa450",
        "agent-a26341d463f77d37d",
        1,
        "35ce751d184fe98e0fc5ce9da4bc9ab08744b04d86a59ac0f992991ea52fcbe7",
    ),
    "plan-v1-15-16-review-b": (
        "Plan v1.15.16's draft: the adversarial read",
        "b9dfa450",
        "agent-a1665ffe2f43192ea",
        1,
        "7508c19f061843d2fa58f45a7e8da234c4ae8b8b311d31a4e3db4047390a8d0b",
    ),
}

#: The one report its session saved to disk, relative to the juniper-ml primary checkout.
SAVED_ROUND_1 = ".claude/worktrees/toasty-prancing-karp/tmp/s1/guard_review_round1.md"
SAVED_ROUND_1_SHA = "37508e487e0eda0068a749aea2528cdfe55066737311a4a20f7a7358aa8e9dc8"

#: Files copied verbatim: archived name -> (source, relative to the juniper-ml primary checkout; its sha256; what it is).
#: The five PRs' fix pass of 2026-11-12 (session 6e3bdef0) is the only copy of the findings plan v1.15.16 records from
#: that validation; the rest of its evidence (461 MB of probes, logs and copies in the same tmp/) is not archived.
FILES = {
    "five-prs-validation-fixpass-round-1.md": (
        ".claude/worktrees/logical-percolating-sparkle/tmp/lps/fixpass_r1.md",
        "ad8d90912ec864c96ac99a1134deee64890149d74c7ec626c3dfbcfea063a77d",
        "The five PRs' validation, round 1: the fix pass and its list 'For the handoff and plan v1.15.16' (session 6e3bdef0, 2026-11-12)",
    ),
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def primary_checkout() -> Path:
    out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=_REPO, capture_output=True, text=True, check=True)
    return Path(out.stdout.strip()).parent


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
    return ""


def _is_prompt(row: dict) -> bool:
    content = (row.get("message") or {}).get("content")
    if row.get("type") != "user" or not _text(content):
        return False
    return not (isinstance(content, list) and any(isinstance(x, dict) and x.get("type") == "tool_result" for x in content))


def transcript(session: str, agent: str) -> Path | None:
    hits = sorted(PROJECTS.glob(f"*/{session}*/subagents/{agent}.jsonl"))
    if len(hits) > 1:
        raise SystemExit(f"refusing: {len(hits)} transcripts match {session}*/{agent}: {hits}")
    return hits[0] if hits else None


def model_of(path: Path) -> str:
    meta = path.with_suffix(".meta.json")
    if not meta.is_file():
        return "unknown"
    data = json.loads(meta.read_text(encoding="utf-8"))
    return f"{data.get('model')} ({data.get('pickedEffortModel')})"


def extract(path: Path, round_no: int) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    prompts = [i for i, r in enumerate(rows) if _is_prompt(r)]
    start = prompts[round_no - 1]
    end = prompts[round_no] if round_no < len(prompts) else len(rows)
    finals = [i for i in range(start + 1, end) if rows[i].get("type") == "assistant" and _text(rows[i]["message"].get("content"))]
    if not finals:
        raise SystemExit(f"refusing: no report between rows {start} and {end} of {path}")
    last = rows[finals[-1]]
    mid = last["message"].get("id")
    parts = [i for i in range(start + 1, end) if rows[i].get("type") == "assistant" and rows[i]["message"].get("id") == mid]
    report = "".join(_text(rows[i]["message"].get("content")) for i in parts)
    return {
        "brief": _text(rows[start]["message"].get("content")),
        "brief_ts": rows[start].get("timestamp"),
        "report": report,
        "report_ts": last.get("timestamp"),
        "rows": f"{start} / {parts[0]}-{parts[-1]}" if len(parts) > 1 else f"{start} / {parts[0]}",
    }


def render_readme(found: dict) -> str:
    lines = [
        "# R-OBS-SC-2 follow-ups: the independent reviews, and one fix pass",
        "",
        "Archived on 2026-11-15 by `util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`, as plan v1.15.16 records",
        "(`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Each review ran as an independent",
        "sub-agent and returned its report as its final message. Four reviewed what R-OBS-SC-2's follow-ups shipped (the",
        "guard and register change, and the two release bodies); the last two reviewed plan v1.15.16's own draft. Before this",
        "archive one report sat in a worktree's gitignored `tmp/`, and the rest existed only in session transcripts, which",
        "Claude Code moves between project directories.",
        "",
        "Each `*_brief.md` is the prompt the reviewer was given, and each `*_report.md` is the report it returned: both",
        "verbatim, plus one final newline. Neither was edited, so a report's findings are as the reviewer wrote them,",
        "before any were checked. What was applied, and where, is recorded in plan v1.15.16 and in the PRs named there.",
        "",
        "| Review | Session, agent and model | Brief sent (UTC) | Report returned (UTC) | Report sha256 (text) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for slug, (title, session, agent, round_no, pin) in REVIEWS.items():
        got = found[slug]
        lines.append(f"| [{title}]({slug}_report.md) ([brief]({slug}_brief.md)) | `{session}`, `{agent}` (prompt {round_no}; rows {got['rows']}), {got['model']} | {got['brief_ts']} | {got['report_ts']} | `{pin[:16]}…` |")
    lines += [
        "",
        f"The round-1 guard report also equals the copy its session saved, `{SAVED_ROUND_1}` in the juniper-ml primary",
        f"(sha256 `{SAVED_ROUND_1_SHA[:16]}…`), once that copy's one-line HTML comment is removed. The two notes rounds are one",
        "agent: round 2 was a message sent to it while it ran.",
        "",
        "Copied verbatim from a worktree's gitignored `tmp/`, which `git worktree remove` deletes:",
        "",
        "| File | What it is | Source (in the juniper-ml primary) | sha256 |",
        "| --- | --- | --- | --- |",
    ]
    for name, (src, pin, what) in FILES.items():
        lines.append(f"| [{name}]({name}) | {what} | `{src}` | `{pin[:16]}…` |")
    lines += [
        "",
        "Re-check (it writes nothing; when a source has gone, it checks the archived copy against its pinned sha256):",
        "",
        "```bash",
        "python3 util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py --check",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if the archive is missing or differs")
    args = parser.parse_args()
    out_dir = _REPO / OUT
    found: dict = {}
    failures: list[str] = []
    for slug, (_title, session, agent, round_no, pin) in REVIEWS.items():
        path = transcript(session, agent)
        if path is None:
            archived = out_dir / f"{slug}_report.md"
            if not args.check:
                raise SystemExit(f"refusing: transcript {session}*/{agent} is gone; only --check can run")
            ok = archived.is_file() and sha(archived.read_text(encoding="utf-8")[:-1]) == pin
            print(f"{'PASS' if ok else 'FAIL'} {slug}: transcript gone; archived report {'matches' if ok else 'does not match'} its pin")
            if not ok:
                failures.append(slug)
            continue
        got = extract(path, round_no)
        got["model"] = model_of(path)
        if sha(got["report"]) != pin:
            failures.append(slug)
            print(f"FAIL {slug}: the transcript's report hashes to {sha(got['report'])}, not its pin {pin}")
            continue
        found[slug] = got
    saved = primary_checkout() / SAVED_ROUND_1
    if saved.is_file() and "guard-round-1" in found:
        body = saved.read_text(encoding="utf-8")
        head, _, rest = body.partition("\n\n")
        report = found["guard-round-1"]["report"]
        ok = sha(body) == SAVED_ROUND_1_SHA and head.startswith("<!--") and "\n" not in head and rest in (report, report + "\n")
        verdict = "equals" if ok else "does NOT equal"
        print(f"{'PASS' if ok else 'FAIL'} guard-round-1: the saved copy (sha256 {sha(body)[:16]}…) {verdict} the transcript's report after its comment line")
        if not ok:
            failures.append("guard-round-1 saved copy")
    elif not saved.is_file():
        print(f"NOTE guard-round-1: the saved copy {SAVED_ROUND_1} is gone; the transcript and the pin stand in for it")
    copies: dict[str, str] = {}
    for name, (src, pin, _what) in FILES.items():
        source = primary_checkout() / src
        archived = out_dir / name
        if not source.is_file():
            ok = archived.is_file() and sha(archived.read_text(encoding="utf-8")) == pin
            print(f"{'PASS' if ok else 'FAIL'} {name}: source gone; archived copy {'matches' if ok else 'does not match'} its pin")
            if not ok or not args.check:
                failures.append(name)
            continue
        text = source.read_text(encoding="utf-8")
        if sha(text) != pin:
            failures.append(name)
            print(f"FAIL {name}: the source hashes to {sha(text)}, not its pin {pin}")
            continue
        copies[name] = text
    if failures:
        print(f"refusing: {len(failures)} failure(s): {failures}")
        return 1
    if len(found) < len(REVIEWS) or len(copies) < len(FILES):
        return 0
    files = {"README.md": render_readme(found), **copies}
    for slug, got in found.items():
        files[f"{slug}_brief.md"] = got["brief"] + "\n"
        files[f"{slug}_report.md"] = got["report"] + "\n"
    pending = [name for name, text in files.items() if not (out_dir / name).is_file() or (out_dir / name).read_text(encoding="utf-8") != text]
    if args.check:
        for name in sorted(files):
            print(f"{'FAIL' if name in pending else 'PASS'} {OUT}/{name}")
        return 1 if pending else 0
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in pending:
        (out_dir / name).write_text(files[name], encoding="utf-8")
        print(f"wrote {OUT}/{name} (sha256 {sha(files[name])[:16]}…)")
    if not pending:
        print("nothing to write: the archive is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
