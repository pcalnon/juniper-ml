#!/usr/bin/env python3
"""
The second session-8 fix-up of the flood-4 "ml-tests" carrier (round 2): the small steps no carrier tool covers.

Two validators of session 8 reported findings on the carrier: the tests lens (two test assertions that do not pin
what their tests claim, mutants S1 and R7) and the claims lens (wrong attributions and process jargon in the texts
and in the manifest's carried table). The fixes go in with `patch`, the orchestrator's edits helper and the
carrier's own tools; this file holds what is left, one subcommand each:

  progress FILE MSG          append a line stamped from the clock to a PROGRESS.txt
  snapshot                   copy files into a snapshot directory and write its SHA256SUMS (sha256sum format)
  suite                      run one unittest suite alone, as CI does, and report `Ran N` and the verdict
  copytree                   copy every path of the carrier's manifest into a scratch worktree, sha256-checked
  mutants                    in a COPY of the carrier (never the carrier), apply the tests lens's mutants S1 and
                             R7 one at a time, run the whole suite, restore in `finally:` and sha256-check
  spec-names                 the carrier's mutant spec with chosen rows' test selections pinned to their last run's
  text-edits                 the claims lens's text fixes as an edits file for the orchestrator's edits helper
  f13                        the claims lens's F13 rule on carried_input.json (exact counts), plus fix notes
  precommit                  the pinned pre-commit on explicit paths, every file hashed before and after
  gates                      CodeQL prescreen and the seven shapes on the Python files; G-PATH and G-TMP on helpers
  freeze                     a freeze directory (snapshot/, paths.txt, plan.json) for the sequence-safety probe
  json-append                append the entries of a JSON list file to a JSON list file (indent 2, as written)
  json-set                   set one key of a JSON object file from a JSON file (indent 2, as written)
  verify-fixes               show each applied text fix in the rendered texts, the landed CHANGELOG.md, the
                             regenerated manifest and the deliverables: its new text there, its old text gone
  zero                       count "session 8" and "session-7 spec" in the rendered texts and the manifest's carried table

Every run that executes tests sets the six Sentry DSN variables to "" and PYTHONDONTWRITEBYTECODE=1, and uses the
interpreter it is started with (the env's python3.14, through the orchestrator's runenv.bash).

Usage:
    python3 util/ad-hoc/2026-11-14_flood4r2_fix_ml-tests-r2s8b.py <subcommand> --help

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 round 2: the ml-tests carrier's second session-8 fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-08_flood4r2_fix_apply_edits.py; tmp/flood4r2-val/ml-tests-r2-tests-lens-s7/findings.json; tmp/flood4r2-val/ml-tests-r2-claims-lens-s8/findings.json
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")

# The tests lens's mutants, as its scratch defines them (util/ad-hoc/2026-11-12_flood4r2_val_ml-tests-r2-tests_mutants.py, ids S1 and R7).
MUTANTS = (
    {
        "id": "S1",
        "pr": 2499,
        "finding": "the tests lens's F1",
        "test_file": "tests/test_cascor_eval_zero_and_enabled.py",
        "target": "util/experiments/stats_summary.py",
        "old": '    elif live is not None and live.get("enabled") is False:\n',
        "new": '    elif live is not None and not live.get("enabled", True):\n',
        "claim": "only enabled is False turns the in-loop scalars off (an enabled of 0 does not)",
    },
    {
        "id": "R7",
        "pr": 2507,
        "finding": "the tests lens's F2",
        "test_file": "tests/test_pyproject_extras.py",
        "target": "tests/test_pyproject_extras.py",
        "old": '        if not line.startswith("|"):\n            break\n',
        "new": '        if not line.startswith("|"):\n            continue\n',
        "claim": "parsing stops at the first line that is not part of the table, so a later table is not a row",
    },
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "absent"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _progress(path: Path, message: str) -> None:
    line = f"{_stamp()} {message}"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)


def _env() -> dict:
    return {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "PYTHONDONTWRITEBYTECODE": "1"}


def _clear_pycache(root: Path, *paths: str) -> None:
    for rel in paths:
        cache = (root / rel).parent / "__pycache__"
        if cache.is_dir():
            shutil.rmtree(cache)


def _run_suite(root: Path, suite: str, log: Path, label: str) -> dict:
    argv = [sys.executable, "-B", "-m", "unittest", "-v", suite]
    done = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, env=_env(), check=False, timeout=900)
    text = done.stdout + done.stderr
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"===== {label} (cwd {root}; {_stamp()}): {' '.join(argv)}\nrc={done.returncode}\n{text}\n")
    ran = re.search(r"^Ran (\d+) tests? in ", text, re.M)
    verdict = re.search(r"^(OK.*|FAILED.*)$", text, re.M)
    failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", text, re.M)))
    return {"rc": done.returncode, "ran": int(ran.group(1)) if ran else None, "verdict": verdict.group(1) if verdict else None, "failed": failed, "interpreter": sys.executable, "version": sys.version.split()[0]}


def cmd_progress(args) -> int:
    _progress(Path(args.file), " ".join(args.msg))
    return 0


def cmd_snapshot(args) -> int:
    root, dest = Path(args.root).resolve(), Path(args.dest).resolve()
    lines = []
    for rel in args.paths:
        src = root / rel
        if not src.is_file():
            raise SystemExit(f"missing: {src}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        if _sha(target) != _sha(src):
            raise SystemExit(f"copy differs: {rel}")
        lines.append(f"{_sha(src)}  {rel}")
    sums = dest / "SHA256SUMS"
    with open(sums, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"{len(lines)} files -> {dest} ({sums})")
    return 0


def cmd_suite(args) -> int:
    root = Path(args.root).resolve()
    log = Path(args.log)
    rows = {}
    for suite in args.suites:
        got = _run_suite(root, suite, log, args.label)
        rows[suite] = got
        print(f"{suite}: rc {got['rc']}, Ran {got['ran']}, {got['verdict']}" + (f", failed {got['failed']}" if got["failed"] else "") + f" [{got['version']} {got['interpreter']}]")
    if args.json:
        Path(args.json).write_text(json.dumps({"root": str(root), "label": args.label, "at": _stamp(), "suites": rows}, indent=2) + "\n", encoding="utf-8")
    return 0 if all(row["rc"] == 0 for row in rows.values()) else 1


def cmd_copytree(args) -> int:
    src, dest = Path(args.src).resolve(), Path(args.dest).resolve()
    if dest == src or src in dest.parents:
        raise SystemExit("refusing: --dest is the carrier or inside it")
    paths = [row["path"] for row in json.loads(Path(args.manifest).read_text(encoding="utf-8"))["files"]]
    bad = []
    for rel in paths:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / rel, target)
        if _sha(target) != _sha(src / rel):
            bad.append(rel)
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=str(dest), capture_output=True, text=True, check=True).stdout
    changed = sorted(line[3:] for line in status.splitlines())
    record = {"src": str(src), "dest": str(dest), "files": len(paths), "differing_after_copy": bad, "change_list_equals_manifest": changed == sorted(paths), "only_in_change_list": sorted(set(changed) - set(paths)), "missing_from_change_list": sorted(set(paths) - set(changed)), "sha256": {rel: _sha(dest / rel) for rel in paths}}
    Path(args.out).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"{len(paths)} files copied; differing: {bad or 'none'}; change list == manifest paths: {record['change_list_equals_manifest']}")
    return 0 if not bad and record["change_list_equals_manifest"] else 1


def cmd_mutants(args) -> int:
    copy, carrier, out = Path(args.copy).resolve(), Path(args.carrier).resolve(), Path(args.out).resolve()
    if copy == carrier or carrier in copy.parents:
        raise SystemExit("refusing: mutants run in a copy, never in the carrier")
    out.mkdir(parents=True, exist_ok=True)
    touched = sorted({m["target"] for m in MUTANTS} | {m["test_file"] for m in MUTANTS})
    before = {rel: {"copy": _sha(copy / rel), "carrier": _sha(carrier / rel)} for rel in touched}
    unequal = [rel for rel, pair in before.items() if pair["copy"] != pair["carrier"]]
    if unequal:
        raise SystemExit(f"refusing: the copy differs from the carrier on {unequal}")
    _progress(Path(args.progress), f"S8B MUTANTS S1 R7 about to start in the COPY {copy} (never in the carrier). sha256 BEFORE, copy == carrier: " + "; ".join(f"{rel} {pair['copy']}" for rel, pair in before.items()))
    rows, ok = [], True
    for m in MUTANTS:
        log = out / f"mut_{m['id']}.log"
        log.write_text("", encoding="utf-8")
        target = copy / m["target"]
        _clear_pycache(copy, m["target"], m["test_file"])
        baseline = _run_suite(copy, m["test_file"], log, "baseline (no mutant)")
        original = target.read_bytes()
        sha_before = _sha(target)
        count = original.count(m["old"].encode())
        row = {"id": m["id"], "pr": m["pr"], "finding": m["finding"], "test_file": m["test_file"], "target": m["target"], "mutant": f"{m['target']}: {m['old']!r} -> {m['new']!r}", "claim": m["claim"], "origin": "session 8, the tests lens (its scratch's mutant " + m["id"] + ")", "baseline": baseline, "log": str(log)}
        if baseline["rc"] != 0 or count != 1:
            row["result"] = f"error: baseline rc {baseline['rc']}, old occurs {count} times"
            rows.append(row)
            ok = False
            continue
        try:
            target.write_bytes(original.replace(m["old"].encode(), m["new"].encode(), 1))
            _clear_pycache(copy, m["target"], m["test_file"])
            mutant = _run_suite(copy, m["test_file"], log, f"mutant {m['id']}")
        finally:
            target.write_bytes(original)
            _clear_pycache(copy, m["target"], m["test_file"])
        sha_after = _sha(target)
        row.update({"mutant_run": mutant, "target_sha256_before": sha_before, "target_sha256_after": sha_after, "restored_byte_for_byte": sha_before == sha_after})
        row["result"] = "killed" if mutant["rc"] == 1 and mutant["ran"] == baseline["ran"] else ("survived" if mutant["rc"] == 0 else f"error: mutant rc {mutant['rc']}")
        row["test_file_sha256"], row["target_sha256"] = _sha(copy / m["test_file"]), sha_after
        ok = ok and row["result"] == "killed" and row["restored_byte_for_byte"]
        rows.append(row)
        print(f"{m['id']} {m['test_file']} [{m['target']}]: baseline Ran {baseline['ran']} {baseline['verdict']}; mutant Ran {mutant['ran']} {mutant['verdict']} failed {mutant['failed']}; {row['result']}; restored {row['restored_byte_for_byte']}")
    after = {rel: {"copy": _sha(copy / rel), "carrier": _sha(carrier / rel)} for rel in touched}
    moved = [rel for rel in touched if after[rel] != before[rel]]
    (out / "new_mutants.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (out / "new_mutants_hashes.json").write_text(json.dumps({"copy": str(copy), "carrier": str(carrier), "before": before, "after": after, "moved": moved}, indent=2) + "\n", encoding="utf-8")
    _progress(Path(args.progress), f"S8B MUTANTS done: " + ", ".join(f"{row['id']} {row['result']}" for row in rows) + f"; every target restored: {all(row.get('restored_byte_for_byte') for row in rows)}; files whose sha256 moved (copy or carrier): {moved or 'none'}. Evidence: {out}/new_mutants.json, mut_S1.log, mut_R7.log")
    return 0 if ok and not moved else 1


def _dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _load_roundtrip(path: Path):
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if json.dumps(data, indent=2) + "\n" != raw:
        raise SystemExit(f"{path}: does not round-trip at indent 2; refusing to rewrite it")
    return data


def cmd_f13(args) -> int:
    path = Path(args.file)
    before = _sha(path)
    carried = _load_roundtrip(path)
    prefix, typed = "session 8: ", ", at the place the session-7 spec typed:"
    stripped, replaced, notes = [], [], []
    for entry in carried:
        taken = entry["taken"]
        for index, item in enumerate(taken):
            if item.startswith(prefix):
                item = item[len(prefix) :]
                stripped.append(entry["pr"])
            if item.count(typed) == 1:
                item = item.replace(typed, ":")
                replaced.append(entry["pr"])
            elif item.count(typed) > 1:
                raise SystemExit(f"#{entry['pr']}: {typed!r} occurs more than once in one item")
            taken[index] = item
    if len(stripped) != args.expect_stripped or len(replaced) != args.expect_replaced:
        raise SystemExit(f"refusing: stripped {len(stripped)} (expected {args.expect_stripped}), replaced {len(replaced)} (expected {args.expect_replaced}); nothing written")
    for pr_text in args.add_fix or []:
        number, text = pr_text.split("=", 1)
        entry = next((e for e in carried if e["pr"] == int(number)), None)
        if entry is None:
            raise SystemExit(f"#{number}: not in {path}")
        if text not in entry["fixes"]:
            entry["fixes"].append(text)
            notes.append(int(number))
    left = [e["pr"] for e in carried if any("session 8" in item or "session-7 spec" in item for item in e["taken"])]
    _dump(path, carried)
    record = {"file": str(path), "sha256_before": before, "sha256_after": _sha(path), "stripped_prefix": stripped, "typed_place_replaced": replaced, "fix_notes_added": notes, "taken_items_still_naming_a_session": left}
    if args.log:
        _dump(Path(args.log), record)
    print(json.dumps(record, indent=1))
    return 0 if not left else 1


def cmd_spec_names(args) -> int:
    """The carrier's mutant spec with each chosen row's test selection pinned to the one its earlier run recorded.

    The carrier's runner selects the tests a row runs from `git diff origin/main` when the row names none, which in
    a copy reads today's main, and finds nothing for a test file the copy holds as a new, untracked file. Pinning a
    row to the selection its earlier run recorded makes the re-run select exactly what that run did.
    """
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    runs = json.loads(Path(args.runs).read_text(encoding="utf-8"))
    pinned = {}
    for index in args.rows:
        if not spec[index].get("names"):
            spec[index]["names"] = runs[index]["selection"]
            pinned[index] = len(spec[index]["names"])
    _dump(Path(args.out), spec)
    print(f"{args.out}: {len(spec)} rows; selection pinned from {args.runs} on rows {pinned} (row: number of tests); rows already naming theirs left as they were")
    return 0


def cmd_text_edits(args) -> int:
    """The claims lens's text fixes as an edits file for the orchestrator's edits helper (every old exactly once).

    TEMPLATE/<name> is the carrier's template, DELIVERABLES/<name> the carrier's scratch file of that name, and
    MANIFEST/carried/<pr>/<field> the carried input the manifest tool reads (carried_input.json), never the
    manifest itself. --also ID=PATH applies fix ID to one more carrier file too (the carrier's own CHANGELOG.md).
    """
    fixes = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    skip = set(args.skip.split(",")) if args.skip else set()
    also = dict(item.split("=", 1) for item in args.also or [])
    edits = []
    for fix in fixes:
        if fix["id"] in skip:
            continue
        kind, name = fix["file"].split("/", 1)
        target = {"TEMPLATE": f"{args.scratch_rel}/templates/{name}", "DELIVERABLES": f"{args.scratch_rel}/{name}", "MANIFEST": f"{args.scratch_rel}/carried_input.json"}[kind]
        edits.append({"id": fix["id"], "file": target, "old": fix["old"], "new": fix["new"]})
        if fix["id"] in also:
            edits.append({"id": f"{fix['id']}-also", "file": also[fix["id"]], "old": fix["old"], "new": fix["new"]})
    _dump(Path(args.out), {"worktree": str(Path(args.worktree).resolve()), "edits": edits})
    print(f"{args.out}: {len(edits)} edits ({', '.join(edit['id'] for edit in edits)}); skipped {sorted(skip)}")
    return 0


def _paths(args) -> list:
    if args.manifest:
        return [row["path"] for row in json.loads(Path(args.manifest).read_text(encoding="utf-8"))["files"]]
    return list(args.paths)


def cmd_precommit(args) -> int:
    """The repository's pinned pre-commit on explicit paths, run from --root; every file hashed before and after."""
    root = Path(args.root).resolve()
    paths = _paths(args)
    before = {rel: _sha(root / rel) for rel in paths}
    done = subprocess.run([args.pre_commit, "run", "--files", *paths], cwd=str(root), capture_output=True, text=True, env=_env(), check=False, timeout=1800)
    after = {rel: _sha(root / rel) for rel in paths}
    rewritten = [rel for rel in paths if before[rel] != after[rel]]
    text = done.stdout + done.stderr
    Path(args.log).write_text(f"cwd {root}\n{args.pre_commit} run --files <{len(paths)} paths>\nrc={done.returncode}\nrewritten: {rewritten or 'none'}\n{text}", encoding="utf-8")
    counts = {word: len(re.findall(rf"[.)]{word}\s*$", text, re.M)) for word in ("Passed", "Skipped", "Failed")}
    print(f"pre-commit rc {done.returncode} on {len(paths)} files in {root}: {counts}; rewritten: {rewritten or 'none'}; log {args.log}")
    return 0 if done.returncode == 0 and not rewritten else 1


def cmd_gates(args) -> int:
    """CodeQL prescreen and the seven shapes on the changed Python files; G-PATH and G-TMP on the helpers."""
    root = Path(args.root).resolve()
    paths = _paths(args)
    python = [rel for rel in paths if rel.endswith(".py")]
    helpers = [rel for rel in paths if rel.startswith("util/ad-hoc/")]
    tool_root = Path(args.tool_root).resolve() if args.tool_root else root
    runs = {
        "codeql_prescreen": [sys.executable, "-B", str(tool_root / "util/ad-hoc/2026-10-05_codeql_python_prescreen.py"), *python],
        "codeql_shapes": [sys.executable, "-B", str(tool_root / "util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_codeql_shapes.py"), *python],
        "g_path": [sys.executable, "-B", str(tool_root / "util/home_path_literal_check.py"), *helpers],
        "g_tmp": [sys.executable, "-B", str(tool_root / "util/tmp_path_literal_check.py"), *helpers],
    }
    record = {"root": str(root), "python_files": len(python), "helpers": len(helpers)}
    for name, argv in runs.items():
        done = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, env=_env(), check=False, timeout=900)
        out = (done.stdout + done.stderr).strip()
        record[name] = {"rc": done.returncode, "tail": out.splitlines()[-6:] if out else []}
        print(f"{name}: rc {done.returncode}: " + " | ".join(record[name]["tail"][-3:]))
    Path(args.out).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return 0


def cmd_freeze(args) -> int:
    """A freeze directory for the orchestrator's sequence-safety probe: snapshot/, paths.txt (add) and plan.json."""
    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    paths = _paths(args)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(tree), capture_output=True, text=True, check=True).stdout.strip()
    for rel in paths:
        target = out / "snapshot" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tree / rel, target)
    (out / "paths.txt").write_text("".join(f"add {rel}\n" for rel in paths), encoding="utf-8")
    _dump(out / "plan.json", {"main_sha": head[:8], "source": str(tree), "files": {rel: _sha(out / "snapshot" / rel) for rel in paths}})
    print(f"{len(paths)} paths frozen from {tree} (HEAD {head[:8]}) into {out}")
    return 0


def cmd_json_append(args) -> int:
    path = Path(args.file)
    data = _load_roundtrip(path)
    if not isinstance(data, list):
        raise SystemExit(f"{path}: not a JSON list")
    entries = json.loads(Path(args.entries).read_text(encoding="utf-8"))
    data.extend(entries)
    _dump(path, data)
    print(f"{path}: {len(entries)} entries appended, {len(data)} now")
    return 0


def cmd_json_set(args) -> int:
    path = Path(args.file)
    data = _load_roundtrip(path)
    data[args.key] = json.loads(Path(args.value).read_text(encoding="utf-8"))
    _dump(path, data)
    print(f"{path}: key {args.key!r} set")
    return 0


def _manifest_field(manifest: dict, spec: str) -> str:
    _, _, number, field = spec.split("/", 3)
    entry = next(e for e in manifest["carried"] if e["pr"] == int(number))
    value = entry[field]
    return "\n".join(value) if isinstance(value, list) else value


def cmd_verify_fixes(args) -> int:
    fixes = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    skip = set(args.skip.split(",")) if args.skip else set()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    changelog = Path(args.changelog).read_text(encoding="utf-8")
    rows, ok = [], True
    for fix in fixes:
        if fix["id"] in skip:
            rows.append({"id": fix["id"], "status": "skipped"})
            continue
        kind, name = fix["file"].split("/", 1)
        places = []
        if kind == "TEMPLATE":
            places.append((f"rendered {name}", (Path(args.texts) / name).read_text(encoding="utf-8")))
            if name == "changelog_entry.txt":
                places.append(("landed CHANGELOG.md", changelog))
        elif kind == "DELIVERABLES":
            places.append((name, (Path(args.scratch) / name).read_text(encoding="utf-8")))
        elif kind == "MANIFEST":
            places.append((f"manifest {fix['file']}", _manifest_field(manifest, fix["file"])))
        for label, text in places:
            new_count = text.count(fix["new"]) if fix["new"] else None
            old_count = text.count(fix["old"])
            good = old_count == 0 and (new_count is None or new_count >= 1)
            ok = ok and good
            line = None
            if fix["new"] and new_count:
                line = text[: text.index(fix["new"])].count("\n") + 1
            rows.append({"id": fix["id"], "where": label, "new_occurs": new_count, "old_occurs": old_count, "line": line, "ok": good})
    Path(args.out).write_text(json.dumps({"rows": rows, "all_ok": ok}, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(row)
    print(f"all_ok={ok}")
    return 0 if ok else 1


def cmd_zero(args) -> int:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    carried = json.dumps(manifest["carried"], ensure_ascii=False)
    counts = {"manifest carried table": {needle: carried.count(needle) for needle in ("session 8", "session-7 spec")}}
    for name in sorted(os.listdir(args.texts)):
        text = (Path(args.texts) / name).read_text(encoding="utf-8")
        counts[f"texts/{name}"] = {needle: text.count(needle) for needle in ("session 8", "session-7 spec")}
    total = sum(sum(row.values()) for row in counts.values())
    print(json.dumps(counts, indent=1))
    print(f"total={total}")
    return 0 if total == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("progress")
    p.add_argument("file")
    p.add_argument("msg", nargs="+")
    p.set_defaults(func=cmd_progress)
    p = sub.add_parser("snapshot")
    p.add_argument("--root", required=True)
    p.add_argument("--dest", required=True)
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_snapshot)
    p = sub.add_parser("suite")
    p.add_argument("--root", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--label", default="suite")
    p.add_argument("--json")
    p.add_argument("suites", nargs="+")
    p.set_defaults(func=cmd_suite)
    p = sub.add_parser("copytree")
    p.add_argument("--src", required=True)
    p.add_argument("--dest", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_copytree)
    p = sub.add_parser("mutants")
    p.add_argument("--copy", required=True)
    p.add_argument("--carrier", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--progress", required=True)
    p.set_defaults(func=cmd_mutants)
    p = sub.add_parser("f13")
    p.add_argument("--file", required=True)
    p.add_argument("--log")
    p.add_argument("--expect-stripped", type=int, default=15)
    p.add_argument("--expect-replaced", type=int, default=4)
    p.add_argument("--add-fix", action="append", help="PR=TEXT: a fix note appended to that draft's fixes")
    p.set_defaults(func=cmd_f13)
    p = sub.add_parser("spec-names")
    p.add_argument("--spec", required=True)
    p.add_argument("--runs", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--rows", nargs="+", type=int, required=True)
    p.set_defaults(func=cmd_spec_names)
    p = sub.add_parser("text-edits")
    p.add_argument("--fixes", required=True)
    p.add_argument("--skip", default="")
    p.add_argument("--worktree", required=True)
    p.add_argument("--scratch-rel", default="tmp/flood4r2/ml-tests/r2")
    p.add_argument("--also", action="append", help="ID=PATH: apply that fix to one more file of the carrier")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_text_edits)
    for name, func in (("precommit", cmd_precommit), ("gates", cmd_gates), ("freeze", cmd_freeze)):
        p = sub.add_parser(name)
        p.add_argument("--manifest", help="take the paths from this manifest's files")
        p.add_argument("paths", nargs="*")
        if name == "freeze":
            p.add_argument("--tree", required=True)
            p.add_argument("--out", required=True)
        else:
            p.add_argument("--root", required=True)
        if name == "precommit":
            p.add_argument("--log", required=True)
            p.add_argument("--pre-commit", default="/opt/miniforge3/bin/pre-commit")
        if name == "gates":
            p.add_argument("--out", required=True)
            p.add_argument("--tool-root", help="where the gate tools live (default: --root)")
        p.set_defaults(func=func)
    p = sub.add_parser("json-append")
    p.add_argument("--file", required=True)
    p.add_argument("--entries", required=True)
    p.set_defaults(func=cmd_json_append)
    p = sub.add_parser("json-set")
    p.add_argument("--file", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    p.set_defaults(func=cmd_json_set)
    p = sub.add_parser("verify-fixes")
    p.add_argument("--fixes", required=True)
    p.add_argument("--skip", default="")
    p.add_argument("--texts", required=True)
    p.add_argument("--changelog", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--scratch", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_verify_fixes)
    p = sub.add_parser("zero")
    p.add_argument("--texts", required=True)
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=cmd_zero)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
