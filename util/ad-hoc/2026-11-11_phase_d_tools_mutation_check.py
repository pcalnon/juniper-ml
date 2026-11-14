#!/usr/bin/env python3
"""
Mutation check: the Phase D probe's and finish tool's suites must FAIL on every seeded defect.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (test-efficacy evidence)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/yamaguchi_acceptance_probe.py, util/ad-hoc/2026-11-11_phase_d_finish.{py,bash},
         util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash,
         tests/test_yamaguchi_acceptance_probe.py, tests/test_phase_d_finish.py,
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md

Both tools exist because hand-written checks passed while the thing they checked was wrong. A suite that would also
pass a broken tool repeats that fault one level up, so each mutant below re-creates one plausible defect -- an edge
made exclusive, a refusal dropped, a class decided by text, an empty input read as a pass -- and the tool's suite is
run against it. A mutant the suite does not kill is reported as SURVIVED and the script exits 1.

The repository is not touched: the files the suites need are copied to a fresh directory under the repo's tmp/
(TMPDIR when set), each mutant is written into that copy, and the suite runs there with PYTHONDONTWRITEBYTECODE=1 so
no stale .pyc can stand in for a mutant. The suite's exit status is read directly, never through a pipe, and a
suite that does not end within five minutes counts as killed, by the clock.

Usage: python3 util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py [--only SUBSTRING] [--file SUBSTRING] [--shard K/N] [--anchors-only]
Exit: 0 every mutant killed; 1 a mutant survived or an edit did not apply.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBE = "util/ad-hoc/yamaguchi_acceptance_probe.py"
FINISH = "util/ad-hoc/2026-11-11_phase_d_finish.py"
WRAPPER = "util/ad-hoc/2026-11-11_phase_d_finish.bash"
DEPLOY = "util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash"
PROBE_SUITE = "tests/test_yamaguchi_acceptance_probe.py"
FINISH_SUITE = "tests/test_phase_d_finish.py"
COPIED = [
    PROBE, FINISH, WRAPPER, DEPLOY, PROBE_SUITE, FINISH_SUITE, "tests/duplicati_api_stub.py", "tests/redacted_env.py", "util/ad-hoc/yamaguchi_server_api.py", "util/ad-hoc/yamaguchi_watchdog.py", "util/ad-hoc/yamaguchi_server_db_snapshot.py",
    "util/ad-hoc/2026-11-09_ac4_restore_drill.py",
    "util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py", "util/systemd/yamaguchi-acceptance-probe.service", "util/systemd/yamaguchi-acceptance-probe.timer",
    "notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md",
]

# A backslash, built: an escape typed into this file can reach it as the character it names (the BOM did, 2026-11-11).
BS = chr(92)

# (file, name, old, new): `old` must occur exactly once in the file.
MUTANTS = [
    # --- the probe -------------------------------------------------------------------------------------------------
    (PROBE, "AC-1: exactly 24 h is not yet 24 h", "        if hours < min_hours:  # exactly 24 h", "        if hours <= min_hours:  # exactly 24 h"),
    (PROBE, "AC-1: NRestarts is not judged", '"NeedDaemonReload": "no", "NRestarts": "0"}', '"NeedDaemonReload": "no"}'),
    (PROBE, "AC-2: a trailing slash on TargetURL fails", 'target.rstrip("/") == EXPECTED_TARGET', "target == EXPECTED_TARGET"),
    (PROBE, "AC-2: the schedule's time of day is not judged", "    if time_of_day != EXPECTED_TIME_OF_DAY:\n", "    if False:\n"),
    (PROBE, "AC-2: the filter count is not judged", "    if n_filters != EXPECTED_FILTERS:\n", "    if False:\n"),
    (PROBE, "AC-13: a second run-script option passes", "    if others:\n        fails.append(f\"other run-script options", "    if False:\n        fails.append(f\"other run-script options"),
    (PROBE, "OPTIONS: keep-time and keep-versions pass", "        if name in names:\n            fails.append(f\"{shown(name, options[name])} is set", "        if False:\n            fails.append(f\"{shown(name, options[name])} is set"),
    (PROBE, "OPTIONS: any retention-policy value passes", '    if state == "restored" and options["retention-policy"] != [RULED_RETENTION]:\n', "    if False:\n"),
    (PROBE, "OPTIONS: --expect-retention is ignored", '    if expect_retention in ("suspended", "restored") and state != expect_retention:\n', "    if False:\n"),
    (PROBE, "OPTIONS: an unrecorded option name passes", "    if unexpected:\n", "    if False:\n"),
    (PROBE, "OPTIONS: a recorded option gone missing passes", "    if missing:\n        fails.append(f\"recorded option names now absent", "    if False:\n        fails.append(f\"recorded option names now absent"),
    (PROBE, "OPTIONS: step 11's values are not judged", "        if not good:\n", "        if False:\n"),
    (PROBE, "values: every option value is printable", "    if name in PRINTABLE_VALUES:\n        return f\"{name}=", "    if True:\n        return f\"{name}="),
    (PROBE, "AC-5: other jobs' records count", "    mine = [r for r in records if r[3] == str(backup_id)]\n", "    mine = list(records)\n"),
    (PROBE, "AC-5: one OK record makes the day OK", 'all(verdict == "OK" for verdict, _code in by_day[day])', 'any(verdict == "OK" for verdict, _code in by_day[day])'),
    (PROBE, "AC-5: a 999 record from before the recovery counts", ' and backup == str(probe_id) and when.date() >= recovered_on)', " and backup == str(probe_id))"),
    (PROBE, "AC-5: any ALERT for 999 counts, whatever its code", 'if verdict == "ALERT" and code == "JOB_MISSING" and backup == str(probe_id)', 'if verdict == "ALERT" and backup == str(probe_id)'),
    (PROBE, "AC-5: 36 h is already stale", "    if age_h > max_gap_hours:\n", "    if age_h >= max_gap_hours:\n"),
    (PROBE, "AC-5: the three-day requirement is two", "need_days=3, probe_id=JOB_MISSING_PROBE_ID", "need_days=2, probe_id=JOB_MISSING_PROBE_ID"),
    (PROBE, "AC-5: a BOM hides the log's first record", "    records, unparsed = [], 0\n    for line in text.lstrip(\"\\ufeff\").splitlines():\n        if not line.strip():\n            continue\n        m = WATCHDOG_LINE.match(line)",
     "    records, unparsed = [], 0\n    for line in text.splitlines():\n        if not line.strip():\n            continue\n        m = WATCHDOG_LINE.match(line)"),
    (PROBE, "AC-6a: a run at the enable instant is outside", "    records = [r for r in records if r[0] >= enabled]", "    records = [r for r in records if r[0] > enabled]"),
    (PROBE, "AC-6a: another source passes", "    if wrong:\n", "    if False:\n"),
    (PROBE, "AC-6a: no source line is not an error", "    if not sources:\n", "    if False:\n"),
    (PROBE, "AC-6a: the grace is exclusive", "    return today if now >= today + grace else", "    return today if now > today + grace else"),
    (PROBE, "AC-6a: the mtime slack is exclusive", "> mtime_slack:  # exactly the slack still matches", ">= mtime_slack:  # exactly the slack still matches"),
    (PROBE, "AC-6a: one day is already daily", "min_days=2, mtime_slack=180.0", "min_days=1, mtime_slack=180.0"),
    (PROBE, "AC-6a: a stub snapshot passes", '        if snapshot["size"] <= 4096:\n', "        if False:\n"),
    (PROBE, "AC-6a: a failed newest start passes", "    if failed and (not done or failed[-1] > done[-1]):\n", "    if False:\n"),
    (PROBE, "AC-7: unsyncable volumes pass", "    if unsyncable:\n", "    if False:\n"),
    (PROBE, "AC-7: exactly 24 h is already late", "        elif age_h <= grace_hours:", "        elif age_h < grace_hours:"),
    (PROBE, "AC-7: a supplementary group does not count", 'if service_gid not in d["gids"] | d["groups"]]', 'if service_gid not in d["gids"]]'),
    (PROBE, "AC-7: the keys directory is judged by string prefix", "os.path.commonpath([keys_dir_real, root]) == root", "keys_dir_real.startswith(root)"),
    (PROBE, "AC-7: a line is split at its first colon", '        head, sep, tail = line.rpartition(":")\n', '        head, sep, tail = line.partition(":")\n'),
    (PROBE, "AC-7: the newest dlist is the last one touched", "    return max(dlists, key=lambda pair: pair[0])[1] if dlists else None", '    return max(dlists, key=lambda pair: pair[1]["mtime"])[1] if dlists else None'),
    (PROBE, "AC-7: missing statuses are not an error", "    elif unread:\n", "    elif False:\n"),
    (PROBE, "AC-12: exactly the gate fails", "    if exposure > gate:", "    if exposure >= gate:"),
    (PROBE, "AC-12: a row outside the accepted set passes", "    if outside:\n", "    if False:\n"),
    (PROBE, "AC-12: any number of rows is enough", "len(rows) < MIN_SECURITY_ROWS:", "len(rows) < 0:"),
    (PROBE, "RUN: a warning in scope is allowed whatever its tag", "        if key in ALLOWED_WARNING_TAGS and in_scope:\n", "        if in_scope:\n"),
    (PROBE, "RUN: an allowed tag is allowed whatever its path", "        if key in ALLOWED_WARNING_TAGS and in_scope:\n", "        if key in ALLOWED_WARNING_TAGS:\n"),
    (PROBE, "RUN: a bracket in a path can be the tag", 'WARNING_TAG = re.compile(r"^[^\\[/]*\\[Warning-([^\\]\\s]+)\\]:")', 'WARNING_TAG = re.compile(r"^.*?\\[Warning-([^\\]\\s]+)\\]:?")'),
    (PROBE, "RUN: the scope matches inside a longer path", '"(?<![\\w./-])" + re.escape(scope)', "re.escape(scope)"),
    (PROBE, "RUN: warnings the result did not list are ignored", "    if total > len(listed):\n", "    if False:\n"),
    (PROBE, "RUN: a Success with warnings passes", '        if w["total"]:\n            fails.append(f"ParsedResult=Success but', '        if False:\n            fails.append(f"ParsedResult=Success but'),
    (PROBE, "RUN: an absent NotProcessedFiles passes", "        elif newest[key] is None:\n", "        elif False:\n"),
    (PROBE, "RUN: deletions under suspended retention pass", '    if newest["deleted_sets"] and retention != "restored":\n', "    if False:\n"),
    (PROBE, "RUN: a compact passes", '    if newest["compact"]:\n', "    if False:\n"),
    (PROBE, "RUN: exactly the count tolerance is outside it", "abs(drift) > count_tolerance:", "abs(drift) >= count_tolerance:"),
    (PROBE, "RUN: drift is a failure", '    return Finding("RUN", settle(fails, errors, attn=attn),', '    return Finding("RUN", settle(fails + attn, errors),'),
    (PROBE, "RUN: an exception on the backup's log entry passes", '    if newest.get("exception"):\n', "    if False:\n"),
    (PROBE, "RUN: unreadable entries ahead of the backup pass", "    if unreadable_newer:\n", "    if False:\n"),
    (PROBE, "RUN: unreadable entries are counted past the newest backup", '        if entry.get("operation") == "Backup":\n            break\n', '        if False:\n            break\n'),
    (PROBE, "RUN: a summary keeps the warnings' text", '        "compact": bool(message.get("CompactResults"))', '        "raw_warnings": message.get("Warnings"), "compact": bool(message.get("CompactResults"))'),
    (PROBE, "OFFSCHED: exactly the slack is off schedule", "<= slack.total_seconds():  # exactly the slack is on schedule", "< slack.total_seconds():  # exactly the slack is on schedule"),
    (PROBE, "OFFSCHED: the 15-minute window is exclusive", 'run["begin"] - window <= e["begin"] <= run["begin"]', 'run["begin"] - window < e["begin"] <= run["begin"]'),
    (PROBE, "OFFSCHED: operations after the start are listed", 'run["begin"] - window <= e["begin"] <= run["begin"]', 'run["begin"] - window <= e["begin"]'),
    (PROBE, "CENSUS: an active task does not excuse a difference", "    if active_task:\n        return Finding(\"CENSUS\", \"PENDING\"", "    if False:\n        return Finding(\"CENSUS\", \"PENDING\""),
    (PROBE, "CENSUS: a divergence passes", '    agree = str(metadata["TargetFilesCount"]) == str(n_files) and str(metadata["TargetFilesSize"]) == str(n_bytes)', "    agree = True"),
    (PROBE, "result: an ERROR exits 0", '        return "UNDETERMINED", EXIT_ERROR', '        return "UNDETERMINED", 0'),
    (PROBE, "result: a PENDING is a PASS", '    if verdicts & {"PENDING", "ATTN", "SKIP"}:', '    if verdicts & {"ATTN", "SKIP"}:'),
    (PROBE, "main: --no-server still contacts the server", '    server = {"error": "--no-server"} if args.no_server else collect_server(', "    server = collect_server("),
    (PROBE, "main: --no-write still writes", "    if not args.no_write:\n", "    if True:\n"),
    (PROBE, "server: the export asks for passwords", '{"export-passwords": "false", "token": op}', '{"export-passwords": "true", "token": op}'),
    (PROBE, "server: a failed export is not an error", "        if export is None:\n", "        if False:\n"),
    (PROBE, "output: acceptance.json is group- and world-readable", 'fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)', 'fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)'),
    (PROBE, "AC-6b: a line that is never judged holds RESULT at INCOMPLETE", '    findings.append(Finding("AC-6b", "INFO", ', '    findings.append(Finding("AC-6b", "SKIP", '),
    (PROBE, "RUN: exactly the age limit is already stale", "        if age_hours > limit:  # exactly the limit is inside it\n", "        if age_hours >= limit:  # exactly the limit is inside it\n"),
    (PROBE, "RUN: an active task earns no extra day", "        limit = max_age_hours + (24.0 if active_task else 0.0)\n", "        limit = max_age_hours\n"),
    (PROBE, "RUN: an active task earns two extra days", "        limit = max_age_hours + (24.0 if active_task else 0.0)\n", "        limit = max_age_hours + (48.0 if active_task else 0.0)\n"),
    (PROBE, "RUN: the age limit is not the watchdog's", "MAX_RUN_AGE_HOURS = 26.0  #", "MAX_RUN_AGE_HOURS = 36.0  #"),
    (PROBE, "RUN: main() gives the judge no clock", 'unreadable_before_first_backup(server["entries"]), now=now))', 'unreadable_before_first_backup(server["entries"])))'),
    (PROBE, "RUN: a backup with no readable BeginTime is not an error", '    if now is not None and newest["begin"] is None:\n        errors.append(', '    if now is not None and newest["begin"] is None:\n        notes.append('),
    (PROBE, "server: a refused login prints the server's answer", '        return f"the server refused the login (status {m.group(1)}); its answer is not printed"\n', '        return f"login refused: {text[:200]}"\n'),
    (PROBE, "server: an unknown stop prints its message", '    return "the API client stopped; its message is not printed"\n', '    return f"the API client stopped: {text}"\n'),
    (PROBE, "server: a credential refusal is not cut to 200 characters", '        return f"credential refused: {text[:200]}"\n', '        return f"credential refused: {text}"\n'),
    (DEPLOY, "deploy: the user is read from $USER", 'ME="$(id -un)"\n', 'ME="$USER"\n'),
    # --- the finish tool: the drill's output, read strictly --------------------------------------------------------
    (FINISH, "drill: a FATAL beside a RESULT is ignored", '    if "fatal" in parsed:\n        also', '    if "fatal" in parsed and "result" not in parsed:\n        also'),
    (FINISH, "drill: a stopped driver is not an error", '    if "fatal" in parsed:\n        also', "    if False:\n        also"),
    (FINISH, "drill: a line printed twice is accepted", '    if parsed["repeated"]:\n', "    if False:\n"),
    (FINISH, "drill: the last occurrence of a line wins", "            if key in parsed:\n                repeated.append(key)\n", "            if False:\n                repeated.append(key)\n"),
    (FINISH, "drill: lines out of the driver's order are accepted", '    if parsed["order"] != list(DRIVER_ORDER):\n', "    if False:\n"),
    (FINISH, "drill: lines after RESULT are accepted", '    if parsed["trailing"]:\n', "    if False:\n"),
    (FINISH, "drill: blank lines after RESULT count as content", '        if "result" in parsed and line.strip():\n', '        if "result" in parsed:\n'),
    (FINISH, "drill: a form feed in a path ends a line", '    for raw in text.lstrip(BOM).split("' + BS + 'n"):\n', "    for raw in text.lstrip(BOM).splitlines():\n"),
    (FINISH, "drill: a BOM hides the output's first line", '    for raw in text.lstrip(BOM).split("' + BS + 'n"):\n', '    for raw in text.split("' + BS + 'n"):\n'),
    (FINISH, "drill: a missing line is not an error", '    if missing:\n        return "ERROR", [f"the output is incomplete', '    if False:\n        return "ERROR", [f"the output is incomplete'),
    # --- the drill's numbers ---------------------------------------------------------------------------------------
    (FINISH, "drill: a lowered floor is not noticed", '    if n["floor"] < AC4_MIN_VERIFIED:\n', "    if False:\n"),
    (FINISH, "drill: fewer than fifteen verified files pass", '    if n["verified"] < AC4_MIN_VERIFIED:\n', "    if False:\n"),
    (FINISH, "drill: rc=3 is not an error", '    if n["rc"] < 0 or n["rc"] >= 3:\n', '    if n["rc"] < 0 or n["rc"] > 3:\n'),
    (FINISH, "drill: a restore killed by a signal passes", '    if n["rc"] < 0 or n["rc"] >= 3:\n', '    if n["rc"] >= 3:\n'),
    (FINISH, "drill: rc=-1 passes", '    if n["rc"] < 0 or n["rc"] >= 3:\n', '    if n["rc"] < -1 or n["rc"] >= 3:\n'),
    (FINISH, "drill: an unverified candidate passes", '    if n["verified"] != n["picked"]:\n', "    if False:\n"),
    (FINISH, "drill: a live contradiction passes", '    if n["contradiction"]:\n', "    if False:\n"),
    (FINISH, "drill: the live-oracle floor is not judged", '    if n["live_match"] < AC4_LIVE_FLOOR:\n', "    if False:\n"),
    (FINISH, "drill: negative control (a) is not judged", '    if not n["negative_absent"]:\n', "    if False:\n"),
    (FINISH, "drill: negative control (b) is not judged", '    if not n["negative_rejected"]:\n', "    if False:\n"),
    (FINISH, "drill: the driver's RESULT is taken on trust", '    if recomputed != n["driver_result"]:\n', "    if False:\n"),
    (FINISH, "drill: the exit code is not compared", '    if exit_code is not None and (exit_code == 0) != (n["driver_result"] == "PASS"):\n', "    if False:\n"),
    (FINISH, "drill: another fileset's output is accepted", '    if n["dlist"] != expect_dlist:\n', "    if False:\n"),
    (FINISH, "drill: a restore from another directory is accepted", '    if os.path.normpath(n["dest"]) != os.path.normpath(expect_dest):\n', "    if False:\n"),
    (FINISH, "drill: a trailing slash makes it another directory", '    if os.path.normpath(n["dest"]) != os.path.normpath(expect_dest):\n', '    if n["dest"] != expect_dest:\n'),
    (FINISH, "drill: the two lines that name the fileset may disagree", '    if parsed["destination"]["dlist"] != n["dlist"] or parsed["destination"]["version"] != parsed["drilled"]["version"]:\n', "    if False:\n"),
    (FINISH, "drill: the sampled-file count is not compared", '    if n["candidates"] != n["picked"]:\n', "    if False:\n"),
    # --- the drill verb --------------------------------------------------------------------------------------------
    (FINISH, "drill: an existing output is not adopted", "    exit_code, adopted = None, os.path.lexists(out_path) and not args.rerun\n", "    exit_code, adopted = None, False\n"),
    (FINISH, "drill: --rerun adopts the earlier output", "    exit_code, adopted = None, os.path.lexists(out_path) and not args.rerun\n", "    exit_code, adopted = None, os.path.lexists(out_path)\n"),
    (FINISH, "drill: an active backup does not refuse", '        if state == "active" and not args.allow_active_task:\n', "        if False:\n"),
    (FINISH, "drill: a dlist that is not in the destination is drilled", "        if dlist not in list_dlists(dest):\n", "        if False:\n"),
    (FINISH, "drill: a recorded PASS is drilled again", '    if previous and previous.get("verdict") == "PASS" and not args.rerun:\n', "    if False:\n"),
    (FINISH, "drill: a passed run directory is kept", '    if verdict == "PASS" and run_dir and os.path.lexists(run_dir):\n', "    if False:\n"),
    (FINISH, "drill: a failed run directory is shredded", '    if verdict == "PASS" and run_dir and os.path.lexists(run_dir):\n', "    if run_dir and os.path.lexists(run_dir):\n"),
    (FINISH, "drill: --rerun overwrites the earlier output", "            os.replace(out_path, kept)\n", "            os.unlink(out_path)\n"),
    (FINISH, "drill: the summary does not name the bytes that ran", '    for line in provenance(("driver", DRIVER)):\n        print(line)\n', "    for line in ():\n        print(line)\n"),
    (FINISH, "drill: an adopted output is recorded as run here", '"driver_ran_here": not adopted', '"driver_ran_here": True'),
    (FINISH, "drill: the run root is not checked", "    run_root = check_run_root(args.run_root, owner_uid)\n    out_path = ", "    run_root = os.path.realpath(args.run_root)\n    out_path = "),
    (FINISH, "drill: the driver is given the path as typed", "    dest = os.path.realpath(args.dest)\n", "    dest = args.dest\n"),
    # --- the run root and the verdict records ----------------------------------------------------------------------
    (FINISH, "run root: its owner is not checked", "    if st.st_uid != owner_uid or st.st_mode & 0o077:\n", "    if st.st_mode & 0o077:\n"),
    (FINISH, "run root: its mode is not checked", "    if st.st_uid != owner_uid or st.st_mode & 0o077:\n", "    if st.st_uid != owner_uid:\n"),
    (FINISH, "run root: access for the group is accepted", "    if st.st_uid != owner_uid or st.st_mode & 0o077:\n", "    if st.st_uid != owner_uid or st.st_mode & 0o007:\n"),
    (FINISH, "run root: access for others is accepted", "    if st.st_uid != owner_uid or st.st_mode & 0o077:\n", "    if st.st_uid != owner_uid or st.st_mode & 0o070:\n"),
    (FINISH, "run root: a file is read as a run root", '    if not stat.S_ISDIR(st.st_mode):\n        raise Refused(f"the run root', '    if False:\n        raise Refused(f"the run root'),
    (FINISH, "run root: a symlink is followed", "        st = os.lstat(run_root)\n", "        st = os.stat(run_root)\n"),
    (FINISH, "verdict: written through a planted symlink", 'fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)', 'fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)'),
    (FINISH, "aside: the run root is not checked", "    run_root = check_run_root(args.run_root, owner_uid)\n    drill = read_verdict(", "    run_root = os.path.realpath(args.run_root)\n    drill = read_verdict("),
    (FINISH, "ac6: the run root is not checked", "    run_root = check_run_root(args.run_root, owner_uid)\n    home = source_home()", "    run_root = os.path.realpath(args.run_root)\n    home = source_home()"),
    (FINISH, "status: the run root is not checked", "    run_root = check_run_root(args.run_root, owner_uid)\n    leftovers = ", "    run_root = os.path.realpath(args.run_root)\n    leftovers = "),
    (FINISH, "shred verb: the run root is not checked", "    run_root = check_run_root(args.run_root, owner_uid)\n    files, failures = shred_tree(", "    run_root = os.path.realpath(args.run_root)\n    files, failures = shred_tree("),
    # --- shredding -------------------------------------------------------------------------------------------------
    (FINISH, "shred: a nested path is accepted", "    if os.path.dirname(real) != root:\n", "    if os.path.commonpath([real, root]) != root:\n"),
    (FINISH, "shred: any directory name is accepted", "    if not RUN_DIR_NAME.fullmatch(os.path.basename(real)):\n", "    if False:\n"),
    (FINISH, "shred: the owner is not checked", "    if os.lstat(real).st_uid != owner_uid:\n", "    if False:\n"),
    (FINISH, "shred: a symlinked run directory is accepted", '    if os.path.islink(path):\n        raise Refused(f"{path} is a symlink")\n    real, root', '    if False:\n        raise Refused(f"{path} is a symlink")\n    real, root'),
    (FINISH, "shred: a symlink inside the tree is followed", "            if os.path.islink(target) or not os.path.isfile(target):\n", "            if False:\n"),
    (FINISH, "shred: a directory it may not touch is not a failure", '        return 0, [f"{run_dir}: {exc}"]\n', "        return 0, []\n"),
    (FINISH, "shred verb: a file that stays on disk is a PASS", "    return EXIT_PASS if not failures else EXIT_ERROR\n", "    return EXIT_PASS\n"),
    # --- the aside copy --------------------------------------------------------------------------------------------
    (FINISH, "aside: a failed drill 1 is enough", '    if not drill or drill.get("verdict") != "PASS" or drill.get("dlist") != DRILLS["1"]:\n', "    if not drill:\n"),
    (FINISH, "aside: only some of the dlists are copied", "        rows = copy_aside(args.dest, aside_fd, dlists)\n", "        rows = copy_aside(args.dest, aside_fd, dlists[:8])\n"),
    (FINISH, "aside: an active backup does not refuse", '    if state == "active" and not args.allow_active_task:\n        raise Refused("a server task is active: a dlist it is writing', '    if False:\n        raise Refused("a server task is active: a dlist it is writing'),
    (FINISH, "aside: a prediction that cannot be made stops the copy", '    except ToolError as exc:\n        return f"predicted   : not available', '    except ZeroDivisionError as exc:\n        return f"predicted   : not available'),
    (FINISH, "aside: an existing copy with other content reads current", "                if have != want:\n", "                if False:\n"),
    (FINISH, "aside: a copy that differs from its source is kept", "                if have != want or os.stat(partial, dir_fd=aside_fd, follow_symlinks=False).st_size != src_st.st_size:\n", "                if False:\n"),
    (FINISH, "aside: a symlink is followed, at the source and at an existing copy", "        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)\n", "        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK, dir_fd=dir_fd)\n"),
    (FINISH, "aside: what is not a regular file is read", "    if not stat.S_ISREG(os.fstat(fd).st_mode):\n", "    if False:\n"),
    (FINISH, "aside: an existing copy is trusted before it is opened", "                os.close(open_regular(name, dir_fd=aside_fd))\n", "                pass\n"),
    (FINISH, "aside: a leftover partial file stops the copy", "        os.unlink(partial, dir_fd=aside_fd)  # an interrupted run's leftover\n", "        pass  # an interrupted run's leftover\n"),
    (FINISH, "aside: the copy's timestamps are the copy's own", "            os.utime(out_fd, ns=(src_st.st_atime_ns, src_st.st_mtime_ns))\n", ""),
    (FINISH, "aside: the copy's mode is 0600", "            os.fchmod(out_fd, stat.S_IMODE(src_st.st_mode))\n", ""),
    (FINISH, "aside: the copy is not synced", "            os.fsync(out_fd)\n", ""),
    (FINISH, "aside: the directory is not synced after the copies", "    os.fsync(aside_fd)\n    return rows\n", "    return rows\n"),
    (FINISH, "aside: the manifest is not synced", "        os.fsync(fh.fileno())\n", ""),
    (FINISH, "aside: the directory is not synced after the manifest", "    os.fsync(aside_fd)\n    return len(entries)\n", "    return len(entries)\n"),
    (FINISH, "aside: a directory inside Dropbox is accepted", '        if os.path.commonpath([real, root]) == root:\n            raise Refused(f"the aside directory', '        if False:\n            raise Refused(f"the aside directory'),
    (FINISH, "aside: inside Dropbox is judged by string prefix", '        if os.path.commonpath([real, root]) == root:\n            raise Refused(f"the aside directory', '        if real.startswith(root):\n            raise Refused(f"the aside directory'),
    (FINISH, "aside: the directory's mode is not checked", "    if st.st_uid != owner_uid or stat.S_IMODE(st.st_mode) != 0o700:\n", "    if st.st_uid != owner_uid:\n"),
    (FINISH, "aside: the directory's owner is not checked", "    if st.st_uid != owner_uid or stat.S_IMODE(st.st_mode) != 0o700:\n", "    if stat.S_IMODE(st.st_mode) != 0o700:\n"),
    (FINISH, "aside: a symlink at the directory's name is followed", "        fd = os.open(aside, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)\n", "        fd = os.open(aside, os.O_RDONLY | os.O_DIRECTORY)\n"),
    (FINISH, "aside: a directory this run made and lost is only refused", '        raise (ToolError(problem + " -- and this run created it, so something replaced it") if created else Refused(problem))\n', "        raise Refused(problem)\n"),
    (FINISH, "aside: no Dropbox root is not a refusal", '    if not roots:\n        raise Refused(f"{path} names no Dropbox root")\n', '    if False:\n        raise Refused(f"{path} names no Dropbox root")\n'),
    (FINISH, "aside: the manifest lists only this run's rows", '        if DLIST_NAME.fullmatch(name) and not name.endswith(".partial") and name not in entries:', "        if False:"),
    (FINISH, "aside: a crashed run's half copy is listed as a dlist", '        if DLIST_NAME.fullmatch(name) and not name.endswith(".partial") and name not in entries:', "        if DLIST_NAME.fullmatch(name) and name not in entries:"),
    (FINISH, "aside: the need alone is room enough", "    if free < need * 2:\n", "    if free < need:\n"),
    (FINISH, "aside: exactly twice the need is too little", "    if free < need * 2:\n", "    if free <= need * 2:\n"),
    # --- the prediction --------------------------------------------------------------------------------------------
    (FINISH, "plan: the prediction is the intersection", '    return {"delete": sorted(union),', '    return {"delete": sorted(always),'),
    (FINISH, "plan: the pass's own fileset is left out", "gone = retention.to_delete(list(by_stamp) + [run], max(at, run), policy)", "gone = retention.to_delete(list(by_stamp), max(at, run), policy)"),
    (FINISH, "plan: two dlists with one stamp are accepted", "    if len(by_stamp) != len(dlists):\n", "    if False:\n"),
    (FINISH, "plan: a directory without dlists is an empty plan", '    if not dlists:\n        raise ToolError(f"{dest} holds no dlist', '    if False:\n        raise ToolError(f"{dest} holds no dlist'),
    (FINISH, "plan: the second after an edge is not evaluated", "            for at in (stamp + frame, stamp + frame + dt.timedelta(seconds=1)):\n", "            for at in (stamp + frame,):\n"),
    (FINISH, "plan: only the first frame of the policy has edges", "        for frame, _interval in policy:\n", "        for frame, _interval in policy[:1]:\n"),
    (FINISH, "plan: an edge outside the window is evaluated", "                if now <= at <= end:\n", "                if True:\n"),
    (FINISH, "plan: a policy that cannot be parsed is a traceback", "    except (KeyError, ValueError, IndexError):\n", "    except KeyError:\n"),
    # --- AC-6b -----------------------------------------------------------------------------------------------------
    (FINISH, "ac6b: a live file written at the fileset's start is not the one it read", '    if live["mtime"] <= fileset_start or (', '    if live["mtime"] < fileset_start or ('),
    (FINISH, "ac6b: a snapshot rewritten during the backup is never the same generation", '    if live["mtime"] <= fileset_start or (when is not None and when == live["mtime"].replace(microsecond=0)):\n', '    if live["mtime"] <= fileset_start:\n'),
    (FINISH, "ac6b: the live file's sub-second part breaks the match", 'when == live["mtime"].replace(microsecond=0)', 'when == live["mtime"]'),
    (FINISH, "ac6b: a differing copy passes", '        if size != live["size"] or digest != live["sha256_b64"]:\n', "        if False:\n"),
    (FINISH, "ac6b: the stale pre-recovery snapshot passes", "    stale = when is not None and when < enabled\n", "    stale = False\n"),
    (FINISH, "ac6b: an entry dated exactly at the re-enable is stale", "    stale = when is not None and when < enabled\n", "    stale = when is not None and when <= enabled\n"),
    (FINISH, "ac6b: a stale live file passes when the entry has no time", '        if live["mtime"] < enabled and not stale:\n', "        if False:\n"),
    (FINISH, "ac6b: a live file written exactly at the re-enable is stale", '        if live["mtime"] < enabled and not stale:\n', '        if live["mtime"] <= enabled and not stale:\n'),
    (FINISH, "ac6b: one stale snapshot gives two reasons", '        if live["mtime"] < enabled and not stale:\n', '        if live["mtime"] < enabled:\n'),
    (FINISH, "ac6b: an entry dated after the fileset was complete passes", "    if when is not None and fileset_end is not None and when > fileset_end:\n", "    if False:\n"),
    (FINISH, "ac6b: an entry dated exactly at the end is after it", "    if when is not None and fileset_end is not None and when > fileset_end:\n", "    if when is not None and fileset_end is not None and when >= fileset_end:\n"),
    (FINISH, "ac6b: no entries is a FAIL, not an ERROR", "    if total == 0:\n", "    if False:\n"),
    (FINISH, "ac6b: a folder at the path counts", 'isinstance(entry, dict) and entry.get("type") == "File" and entry.get("path") == path', 'isinstance(entry, dict) and entry.get("path") == path'),
    (FINISH, "ac6b: a stub copy passes", "    if not isinstance(size, int) or isinstance(size, bool) or size <= 4096:\n", "    if False:\n"),
    (FINISH, "ac6b: a copy of exactly 4096 bytes is a database", "    if not isinstance(size, int) or isinstance(size, bool) or size <= 4096:\n", "    if not isinstance(size, int) or isinstance(size, bool) or size < 4096:\n"),
    (FINISH, "ac6: the fileset's end is not given to the judge", "judge_ac6b(entry, total, fileset_start, live, fileset_end)", "judge_ac6b(entry, total, fileset_start, live)"),
    (FINISH, "ac6: the passphrase's hash prefix is printed", "        with contextlib.redirect_stdout(io.StringIO()):  # the loader prints", "        if True:  # the loader prints"),
    (FINISH, "ac6: a dlist that is not a zip is a traceback", "    except (OSError, zipfile.BadZipFile, KeyError, IndexError, ValueError, EOFError) as exc:", "    except OSError as exc:"),
    (FINISH, "ac6: a PASS that leaves the decrypted dlist behind stays a PASS", '    if failures and verdict == "PASS":\n        verdict = "ERROR"\n    record = {"schema": "phase-d-ac6b/2"', '    if False:\n        verdict = "ERROR"\n    record = {"schema": "phase-d-ac6b/2"'),
    (FINISH, "ac6: a dlist that is not in the destination is opened", '    if dlist not in dlists:\n        raise Refused(f"{dlist} is not in {args.dest}")\n', '    if False:\n        raise Refused(f"{dlist} is not in {args.dest}")\n'),
    (FINISH, "ac6: the driver's stop is a traceback", "    except SystemExit as exc:  # the driver's fail()", "    except KeyboardInterrupt as exc:  # the driver's fail()"),
    # --- the server question, the hop to the Source's user, the command line ---------------------------------------
    (FINISH, "server: a failed serverstate reads as idle", "    if returncode not in (0, 2):\n", "    if False:\n"),
    (FINISH, "server: an active task reads as idle", '    if state["ActiveTask"]:\n', "    if False:\n"),
    (FINISH, "server: the hop inherits root's working directory", 'capture_output=True, text=True, timeout=60, check=False, cwd="/")', "capture_output=True, text=True, timeout=60, check=False)"),
    (FINISH, "status: the probe inherits root's working directory", '    code = subprocess.run(argv, check=False, cwd="/").returncode', "    code = subprocess.run(argv, check=False).returncode"),
    (FINISH, "status: the probe keeps root's environment", '"--", "/usr/bin/env", "-i", f"HOME={home}"', '"--", "/usr/bin/env", f"HOME={home}"'),
    (FINISH, "status: dlists the aside copy lacks are not counted", "        beyond = [name for name in list_dlists(dest) if name not in listed]\n", "        beyond = []\n"),
    (FINISH, "status: copies missing from the directory are not counted", "    missing = [name for name in listed if not os.path.isfile(os.path.join(aside, name))]\n", "    missing = []\n"),
    (FINISH, "main: the root gate is gone", "        if os.geteuid() != 0:\n", "        if False:\n"),
    (FINISH, "main: an abbreviated option is accepted", '        kwargs.setdefault("allow_abbrev", False)\n', '        kwargs.setdefault("allow_abbrev", True)\n'),
    (FINISH, "main: a file that cannot be read is a traceback", "    except OSError as exc:  # a file this verb needs", "    except PermissionError as exc:  # a file this verb needs"),
    (FINISH, "load: a script that cannot be imported is a traceback", "    except ImportError as exc:  # the driver imports", "    except ZeroDivisionError as exc:  # the driver imports"),
    (FINISH, "run_driver: the output file is world-readable", "    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)", "    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)"),
    (FINISH, "run_driver: an existing output is overwritten", "    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)", "    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)"),
    (FINISH, "run_driver: the passphrase's hash prefix is kept", "                line = withhold_fingerprint(line)\n", ""),
    (FINISH, "run_driver: the driver's stdout is buffered", 'argv = ["/usr/bin/python3", "-I", "-u", DRIVER,', 'argv = ["/usr/bin/python3", "-I", DRIVER,'),
    (FINISH, "run_driver: the pattern misses the driver's credential line", "=[0-9a-f]{16}", "=[0-9a-f]{15}"),
    # --- the wrapper -----------------------------------------------------------------------------------------------
    (WRAPPER, "wrapper: the caller's environment is not emptied", 'exec "$ENV" -i "${keep[@]}" "$PY" -I "$TOOL" "$@"', 'exec "$ENV" "${keep[@]}" "$PY" -I "$TOOL" "$@"'),
    (WRAPPER, "wrapper: one more variable is let through", "for name in HOME USER LOGNAME TERM; do", "for name in HOME USER LOGNAME TERM COLUMNS; do"),
    (WRAPPER, "wrapper: the interpreter runs without isolated mode", '"$PY" -I "$TOOL" "$@"', '"$PY" "$TOOL" "$@"'),
]
SUITE_OF = {PROBE: PROBE_SUITE, DEPLOY: PROBE_SUITE, FINISH: FINISH_SUITE, WRAPPER: FINISH_SUITE}
SUITE_TIMEOUT = 300  # seconds: a mutant that makes a test wait for ever is killed by the clock, and reported as such


def run_suite(tree: Path, suite: str) -> tuple[int | None, str]:
    """(exit status, or None after SUITE_TIMEOUT; the suite's stderr). `-f`: one failing test is enough to kill a mutant."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([sys.executable, "-m", "unittest", "-f", suite], cwd=tree, env=env, capture_output=True, text=True, check=False, timeout=SUITE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, ""
    return proc.returncode, proc.stderr


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--only", default="", help="run only the mutants whose name contains this text")
    ap.add_argument("--file", default="", help="run only the mutants of files whose path contains this text (e.g. phase_d_finish)")
    ap.add_argument("--shard", default="", help="K/N: of the selected mutants run every N-th, from the K-th (0-based); N copies side by side cover them all")
    ap.add_argument("--anchors-only", action="store_true", help="check that every mutant's anchor occurs exactly once in its file, and run no suite")
    args = ap.parse_args()
    tmp_root = Path(os.environ.get("TMPDIR") or (REPO / "tmp"))
    tmp_root.mkdir(parents=True, exist_ok=True)
    selected = [m for m in MUTANTS if args.only in m[1] and args.file in m[0]]
    if args.shard:
        try:
            shard, shards = (int(part) for part in args.shard.split("/"))
        except ValueError:
            ap.error(f"--shard is K/N, got {args.shard!r}")
        if not 0 <= shard < shards:
            ap.error(f"--shard K/N needs 0 <= K < N, got {args.shard!r}")
        selected = [m for i, m in enumerate(selected) if i % shards == shard]
    names = [m[1] for m in MUTANTS]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        print(f"two mutants share a name: {duplicates}")
        return 1
    failures = 0
    with tempfile.TemporaryDirectory(dir=tmp_root, prefix="phase_d_tools_mutants_") as work:
        tree = Path(work) / "tree"
        for relative in COPIED:
            target = tree / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, target)
        if args.anchors_only:
            for file, name, old, new in selected:
                count = (tree / file).read_text(encoding="utf-8").count(old)
                if count != 1 or old == new:
                    print(f"[EDIT-FAILED] {name}: anchor occurs {count} times in {file}" + (" and the replacement equals it" if old == new else ""))
                    failures += 1
            print(f"{len(selected) - failures} of {len(selected)} anchors occur exactly once")
            return 0 if failures == 0 else 1
        for suite in sorted(set(SUITE_OF.values())):
            code, stderr = run_suite(tree, suite)
            print(f"baseline {suite}: exit={code}")
            if code != 0:
                print(stderr[-5000:])
                return 1
        for file, name, old, new in selected:
            # The copy taken above, not the repository: an edit made there while this runs must not reach a mutant.
            source = (tree / file).read_text(encoding="utf-8")
            if source.count(old) != 1:
                print(f"[EDIT-FAILED] {name}: anchor occurs {source.count(old)} times in {file}")
                failures += 1
                continue
            (tree / file).write_text(source.replace(old, new), encoding="utf-8")
            code, stderr = run_suite(tree, SUITE_OF[file])
            (tree / file).write_text(source, encoding="utf-8")
            verdict = "KILLED" if code != 0 else "SURVIVED"
            failures += verdict == "SURVIVED"
            tail = [line for line in stderr.splitlines() if line.startswith(("FAILED", "OK"))]
            print(f"[{verdict}] {name}  ({'timed out' if code is None else tail[-1] if tail else 'no summary'})", flush=True)
    print(f"{len(selected) - failures} of {len(selected)} mutants killed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
