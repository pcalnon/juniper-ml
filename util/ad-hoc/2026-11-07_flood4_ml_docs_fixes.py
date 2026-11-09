#!/usr/bin/env python3
"""
The recorded corrections the Cursor flood-4 juniper-ml docs carrier applies on top of the drafts' own hunks.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_apply.py (consumes the JSON this writes via --fixes)

Each entry replaces text that a draft added (or, for pr 0, adds the carrier's own Version History row).
`old` must occur exactly once in the assembled file; the applier refuses otherwise. `why` is the evidence
that made the draft's sentence false or stale, so every carried-with-fix line traces to a reason.

Usage: 2026-11-07_flood4_ml_docs_fixes.py <out.json>
"""

from __future__ import annotations

import json
import sys

REF = "docs/REFERENCE.md"
CHEAT = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
OVER = "docs/DOCUMENTATION_OVERVIEW.md"
QS = "docs/QUICK_START.md"

FIXES: list[dict] = [
    # ---- #2409 config-tools ----
    {
        "pr": 2409,
        "path": REF,
        "old": "Since `juniper-ml` 0.5.0 it is aggregated under `[tools]` and `[all]`",
        "new": "Since `juniper-ml` 0.6.0, the first release whose PyPI metadata declares it, it is aggregated under `[tools]` and `[all]`",
        "why": "PyPI juniper-ml 0.5.0 requires_dist has no juniper-config-tools; 0.6.0 (2026-05-23) is the first with it",
    },
    {
        "pr": 2409,
        "path": REF,
        "old": "The file alone does not reach a wheel. These packages have no `MANIFEST.in`, and setuptools omits package data that is not declared. ",
        "new": "The declaration is not what ships the file today: setuptools' `build_py` adds `py.typed` and `*.pyi` implicitly (`_IMPLICIT_DATA_FILES`), so a build with the `package-data` entry removed still puts the marker in the wheel (setuptools 81.0.0 on the Linux host). The `0.1.0` wheel lacks it because the file did not exist yet: tag `juniper-config-tools-v0.1.0` has no `py.typed`. ",
        "why": "#2410's negative control failed for all six sub-packages; setuptools build_py.py:25 _IMPLICIT_DATA_FILES = ('*.pyi', 'py.typed')",
    },
    {
        "pr": 2409,
        "path": "juniper-config-tools/README.md",
        "old": "`Typing :: Typed`. The marker file has to be package data. There is\nno `MANIFEST.in`, so an undeclared `py.typed` never reaches a wheel\n(`tests/test_subpackage_py_typed.py`).",
        "new": "`Typing :: Typed`. Current setuptools also adds a package's `py.typed`\nimplicitly (`build_py`'s `_IMPLICIT_DATA_FILES`), so the wheel carries\nthe marker even without the declaration;\n`tests/test_subpackage_py_typed.py` pins the file, the declaration and\nthe classifier.",
        "why": "same as above: an undeclared py.typed does reach the wheel",
    },
    # ---- #2457 recurrence crossval 500: remedy rewritten, 0.8.1 is on PyPI ----
    {
        "pr": 2457,
        "path": REF,
        "old": (
            "juniper-recurrence#229 (merged 2026-11-04, squash `2a467adb`, tag `juniper-recurrence-v0.8.1`) raises the floor to `juniper-model-core[crossval]>=0.3.0,<0.4.0` on recurrence `main`.\n"
            "On 2026-11-04 PyPI's latest `juniper-recurrence` was **0.8.0** (`/pypi/juniper-recurrence/0.8.1/json` returned 404).\n"
            "`pip install -U juniper-recurrence` therefore stays on 0.8.0 until that wheel is published.\n"
            "`juniper-ml`'s `[recurrence]` extra is `juniper-recurrence>=0.8.0,<0.9.0`, which accepts 0.8.0, so installing the meta-package does not force the bump either.\n"
            "\n"
            "The repair that fits the published 0.8.0 range is model-core 0.3.x. PyPI's latest `juniper-model-core` on that date was 0.3.2, which has `groups`. An env already on 0.3.0, 0.3.1, or 0.3.2 never takes this path.\n"
            "\n"
            "```bash\n"
            'python -m pip install -U "juniper-model-core[crossval]>=0.3.0,<0.4.0"\n'
            "python -m pip check\n"
            "```\n"
            "\n"
            "After 0.8.1 is on PyPI, an env left on model-core 0.2.0 fails scoped `pip check` and the preflight refuses before `serve`. The pin probe still will not name model-core. The release-notes archive is juniper-ml#2454; the wheel publish is a separate step, and this page was checked against PyPI on 2026-11-04."
        ),
        "new": (
            "**Fixed in 0.8.1.** juniper-recurrence#229 (merged 2026-11-04, squash `2a467adb`, tag `juniper-recurrence-v0.8.1`) raises the floor to `juniper-model-core[crossval]>=0.3.0,<0.4.0`.\n"
            "PyPI has served `juniper-recurrence` 0.8.1 since 2026-11-06 09:35Z, with that floor in its metadata; juniper-ml#2454 archived its release notes.\n"
            "`juniper-ml`'s `[recurrence]` extra floors `juniper-recurrence>=0.8.1,<0.9.0` since juniper-ml#2473, first released in `juniper-ml` 0.11.4 (PyPI 2026-11-07), so a fresh install of the extra cannot resolve 0.8.0.\n"
            "\n"
            "Repair an env that still serves 0.8.0 by upgrading the app, which brings model-core 0.3.x with it:\n"
            "\n"
            "```bash\n"
            'python -m pip install -U "juniper-recurrence>=0.8.1,<0.9.0"\n'
            "python -m pip check\n"
            "```\n"
            "\n"
            "An env that must stay on 0.8.0 can take model-core 0.3.x alone. Every 0.3 release (0.3.0, 0.3.1, 0.3.2) has `groups`, and 0.8.0's own range (`<0.4.0`) accepts it:\n"
            "\n"
            "```bash\n"
            'python -m pip install -U "juniper-model-core[crossval]>=0.3.0,<0.4.0"\n'
            "python -m pip check\n"
            "```\n"
            "\n"
            "With 0.8.1 installed beside model-core 0.2.0, scoped `pip check` reports the violated floor, so the preflight refuses before `serve`. The pin probe still does not name model-core. Checked against PyPI on 2026-11-07."
        ),
        "why": "PyPI juniper-recurrence 0.8.1 uploaded 2026-11-06T09:35:42Z, requires juniper-model-core[crossval]<0.4.0,>=0.3.0; pyproject.toml:110 floors >=0.8.1 (ml#2473); PyPI juniper-ml 0.11.4 uploaded 2026-11-07T22:59Z",
    },
    {
        "pr": 2457,
        "path": CHEAT,
        "old": 'Until 0.8.1 is on PyPI, `python -m pip install -U "juniper-model-core[crossval]>=0.3.0,<0.4.0"`.',
        "new": 'Fixed in 0.8.1 (PyPI 2026-11-06): `python -m pip install -U "juniper-recurrence>=0.8.1,<0.9.0"`, or model-core `>=0.3.0,<0.4.0` alone to stay on 0.8.0.',
        "why": "0.8.1 on PyPI since 2026-11-06T09:35:42Z",
    },
    {
        "pr": 2457,
        "path": CHEAT,
        "old": "install model-core `>=0.3.0,<0.4.0` until 0.8.1 is on PyPI",
        "new": "fixed in 0.8.1 (PyPI 2026-11-06); model-core `>=0.3.0,<0.4.0` alone repairs a 0.8.0 env",
        "why": "0.8.1 on PyPI since 2026-11-06T09:35:42Z",
    },
    {
        "pr": 2457,
        "path": OVER,
        "old": "install `juniper-model-core[crossval]>=0.3.0,<0.4.0` until 0.8.1 is on PyPI)",
        "new": "fixed in 0.8.1, on PyPI since 2026-11-06; model-core `>=0.3.0,<0.4.0` alone repairs a 0.8.0 env)",
        "why": "0.8.1 on PyPI since 2026-11-06T09:35:42Z",
    },
    {
        "pr": 2457,
        "path": QS,
        "old": 'Until 0.8.1 is on PyPI: `python -m pip install -U "juniper-model-core[crossval]>=0.3.0,<0.4.0"`',
        "new": "Fixed in 0.8.1 (PyPI 2026-11-06): upgrade `juniper-recurrence`, or install `juniper-model-core[crossval]>=0.3.0,<0.4.0` to stay on 0.8.0",
        "why": "0.8.1 on PyPI since 2026-11-06T09:35:42Z",
    },
    # ---- #2465 idle compaction: #2271 closed; worktree nuance ----
    {
        "pr": 2465,
        "path": REF,
        "old": '(`feat/disable-idle-compress-setting-for-claude-code`) adds `"idleCompaction": false` beside them. That key is not loaded. A session\'s idle compaction does not change.',
        "new": '(`feat/disable-idle-compress-setting-for-claude-code`, closed unmerged on 2026-11-06) would have added `"idleCompaction": false` beside them, where it would not have loaded or changed a session\'s idle compaction.',
        "why": "gh: #2271 CLOSED 2026-11-06T13:04:21Z",
    },
    {
        "pr": 2465,
        "path": REF,
        "old": "| `.claude/settings.local.json` | This checkout only; gitignored here |",
        "new": "| `.claude/settings.local.json` | You, in this project only (a session in a git worktree reads the main checkout's copy); gitignored here |",
        "why": "code.claude.com/docs/en/settings: 'In a worktree, it uses the file at the main checkout's root'",
    },
    {
        "pr": 2465,
        "path": REF,
        "old": "Sources, fetched 2026-11-06:",
        "new": "Sources, fetched 2026-11-06 and re-checked 2026-11-07:",
        "why": "re-fetched settings and settings-reference pages 2026-11-07; every quoted fact matched",
    },
]


def _fx(pr: int, path: str, old: str, new: str, why: str) -> dict:
    return {"pr": pr, "path": path, "old": old, "new": new, "why": why}


# Verifier findings (independent read-only agents, probe-backed, file:line evidence on main 303ccc0b).
FIXES += [
    # ---- #2412 host-check wording ----
    _fx(2412, REF, "`1.36` is turing's cluster value with `.x` appended.", "`1.36.x` is turing's cluster value with `.x` appended.", "host_state_check.py:835 appends .x to 1.36"),
    _fx(2412, REF, 'Treating the check\'s figure as "free + inactive, plus speculative again" drops those pages a second time.', 'Treating the check\'s figure as "free + inactive" and adding speculative pages to it counts those pages a second time.', "host_state_check.py:1069 already includes speculative"),
    _fx(2412, REF, "`macvm_ctl status` exits 0 on a failing gate.", "`macvm_ctl status` exits 0 on a failing gate, and 2 when VBoxManage is missing, the VM is not registered, or an input cannot be measured.", "macvm_ctl.bash:39-48,496-508"),
    _fx(2412, REF, "Two of those sentences were wrong until", "Two of its sentences, the kubectl fix and the G-MEM memory message, were worded wrong until", "only the kubectl fix names a task (f1f5938a^:util/host_state_check.py)"),
    _fx(2412, REF, "Upgrading kubectl beside that install leaves the gate on Docker Desktop's binary.", "Docker Desktop's symlink collides with Homebrew `kubernetes-cli` under the shared Intel prefix (decision D7).", "unsupported claim replaced by the plan's D7 text (TURING-HOST-BRINGUP plan :311)"),
    # ---- #2418 Phase D trial drop-in and key write ----
    _fx(2418, REF, "The drop-in resets four lists with an empty assignment, then sets them again: `ExecStart=`, `EnvironmentFile=`, `LoadCredential=`, and `SystemCallErrorNumber=`.", "The drop-in resets four lists with an empty assignment: `ExecStart=`, `EnvironmentFile=`, `LoadCredential=`, and `SystemCallErrorNumber=`. It sets the first three again and leaves `SystemCallErrorNumber=` empty.", "override.conf:67 leaves SystemCallErrorNumber= empty; #2421 TrialDropInMerge asserts []"),
    _fx(2418, REF, "Without the `LoadCredential=` reset, systemd v259 replaces the path for the same credential id instead of starting from the unit file's list.", "An empty `LoadCredential=` resets the list (systemd v259 `load-fragment.c`). Without the reset, v259 would replace the path for the same credential id.", "the draft had the reset's effect backwards (override.conf:27-30)"),
    _fx(2418, REF, "The wrapper reads that file with `$(<file)`, which drops every trailing newline, refuses a NUL, a carriage return, or edge whitespace, and keeps quotes.", "The wrapper reads that file with `$(<file)`, which drops every trailing newline. The wrapper refuses a NUL, a carriage return, or edge whitespace, and keeps quotes.", "$(<file) drops a NUL silently; the wrapper's own checks refuse (duplicati-wrapper.bash:197-206)"),
    _fx(2418, CHEAT, "`NONE` after an `ENV_ACTIVE_KEY` probe match means the paths disagree — stop and keep the `.env`.", "`NONE` after an `ENV_ACTIVE_KEY` probe match means the probe and the tool disagree (are `--env` and `--db` the probe's own paths?) — stop and keep the `.env`.", "write_matched_settings_key.py:379-381"),
    _fx(2418, REF, "A symlinked directory is refused as well (`O_NOFOLLOW`).", "A symlinked directory is refused earlier, as `REFUSED: cannot open … as a directory without following a symlink` (`O_NOFOLLOW`).", "write_matched_settings_key.py:298-300"),
    # ---- #2426 G-SEC getblockall (carried once; #2424 not carried) ----
    _fx(2426, REF, "When `--getblockall` produced stdout, its first line is included. A capture that failed before stdout (missing binary, non-zero exit) leaves only the global-state line.", "When the `--getblockall` capture ran and exited 0, its first line is included, even a sentence the gate does not classify. A missing key, a missing binary, a timeout or a non-zero exit adds no block-all line, even when the command printed one. A successful stealth capture's line follows either way.", "host_state_check.py:522-533,721-732 (probe: State 0 + failed blockall + stealth)"),
    _fx(2426, REF, "State 1 is `Firewall is enabled. (State = 1)`.", "State 1's sentence, as the suite's fixture spells it, is `Firewall is enabled. (State = 1)`.", "only tests/test_host_state_check.py:196 shows it; the code reads only State = N (:719)"),
    # ---- #2428 safe_merge MERGED line ----
    _fx(2428, REF, "Passing `pcalnon/juniper-ml` as `--repo` asks GitHub for a repository that does not exist under that owner.", "Passing `pcalnon/juniper-ml` as `--repo` hands gh `pcalnon/pcalnon/juniper-ml`, which gh reads as HOST/OWNER/REPO: the first `gh pr view` fails (`error connecting to pcalnon`) and the run exits 3.", "measured; safe_merge.py:453,463,1217-1219"),
    _fx(2428, REF, "Exit 3. `PR #<pr> is MERGED at <other8>, but this run verified and tried to merge <head8>`", "Exit 3, on stderr: `ERROR: PR #<pr> is MERGED at <other8>, but this run verified and tried to merge <head8>`", "safe_merge.py:1129-1133,1218 print it to stderr"),
    _fx(2428, CHEAT, "Expected. The line prints the verified `headRefOid`.", "Expected for a squash (the default). The line prints the verified `headRefOid`.", "with --merge-method merge the head is in main's history"),
    _fx(2428, REF, "| The armed net merged before that call |", "| This run armed a net, and the PR was already merged before that call (the net is the likely merger) |", "the wording depends on _ARMED, not on who merged (safe_merge.py:804-817)"),
    # ---- #2442 anomaly detector ----
    _fx(2442, CHEAT, "Three scores that print the same to six decimals are `duplicate_scores`.", "When every retained score (window 10, at least three) prints the same to six decimals, the result is `duplicate_scores`.", "security.py:242-247; probe: 0.1, 0.5, 0.5, 0.5 does not flag"),
    {
        "pr": 2442,
        "path": REF,
        "move": {
            "from": "## Worker Result Anomaly Detector",
            "to_excl": ["**Maintainer:** Paul Calnon"],
            "strip_tail": ["", "---", ""],
            "before": ["---", "", "**Last Updated:** 2026-10-08", "**Version:** 0.6.62", "**Maintainer:** Paul Calnon"],
        },
        "why": "the draft placed its section inside the footer (between **Version:** and **Maintainer:**); moved above the footer rule",
    },
    # ---- verifier 2: #2417, #2432, #2437, #2422, #2433 ----
    _fx(2417, REF, "the column is kept, including a `test_*` column when `split` is `test`", "the `test_*` column is kept when the final block's `split` is `test` (a `validation` final block and the in-loop block fill no column)", "run_suite.py:174-181,931-940: only test_* columns, only for split test"),
    _fx(2417, CHEAT, "a bar of height 0, column kept)", "a bar of height 0, `test_*` column kept when `split` is `test`)", "as above"),
    _fx(2417, REF, "and the suite column is kept.", "and the `test_accuracy` column is kept when `split` is `test`.", "as above"),
    _fx(2417, CHEAT, "and the suite column;", "and the `test_accuracy` column (test split);", "as above"),
    _fx(2417, QS, "and the suite column;", "and the `test_accuracy` column (test split);", "as above"),
    _fx(2417, REF, "| `nan` or `inf` |", "| `nan`, `inf` or `-inf` |", "stats_summary.py:458-461 prints -inf (probe)"),
    _fx(2417, REF, "(`summary.md` prints `theta: 0 (explicit)`)", "(`summary.md` prints `theta: 0 (explicit)`, or `theta: 0.0 (explicit)` for `0.0`: the theta line does not go through `_fmt`)", "stats_summary.py:564 uses str() (probe)"),
    _fx(2417, REF, "every metric undefined", "every metric `null` (only `accuracy` carries an `undefined` reason)", "tests/test_stats_summary_eval_blocks.py:251-256; cascor_eval_fixtures.py:136-143"),
    {
        "pr": 2417,
        "path": REF,
        "move": {"from": "### A zero is a measured value", "to_excl": ["**The boundary.** `cascor.eval_scalars` changed meaning"], "strip_tail": [""], "before": ["### Step-duration honesty (cascor)"]},
        "why": "the inserted heading took over **The boundary.**, the jq block and the Gate: line of the Eval scalars section; moved after that Gate: line",
    },
    _fx(2432, OVER, "(a JSON object, including `{}`, keeps an empty headline;", "(a JSON object with no headline, including `{}`, keeps an empty headline;", "run_suite.py:996-998: an object with headline values prints them"),
    _fx(2432, REF, "No headline keys means empty cells.", "No headline keys means empty cells, except that a `cascor` block with no labelled `eval_scalars` (a `/1` file) still gets `test_*` re-derived from the run's `metrics_final.json`.", "run_suite.py:907-940 (probe: four test_* columns)"),
    {
        "pr": 2432,
        "path": REF,
        "move": {"from": "#### An empty stats.json is not a missing file", "to_excl": ["```bash", "jq '{train_accuracy: .cascor.final.train_accuracy"], "strip_tail": [""], "before": ["#### Held-out `test_*` columns (juniper-ml#2064)"]},
        "why": "the inserted heading took over the existing jq '{train_accuracy...}' block; moved after it",
    },
    _fx(2437, CHEAT, "| `save_model` is `degraded` and `model.npz` is missing or was just deleted |", "| `outcome` is `degraded`, `phases.save_model` is `failed`, and `model.npz` is missing or was just deleted |", "run_experiment.py:2621-2626: degraded is the outcome, the phase is failed"),
    _fx(2437, OVER, "(scored model by `operation_id`, or a pre-W1.5 CLI re-fit). A failed snapshot does not re-fit: [A failed snapshot save does not re-fit](REFERENCE.md#a-failed-snapshot-save-does-not-re-fit).", "(the scored model saved by `operation_id`, or, for a pre-W1.5 service, the launcher-recorded CLI re-fit under interpreter + model-version parity; a 409 or a mismatch is `degraded`; a failed snapshot save does not re-fit: [A failed snapshot save does not re-fit](REFERENCE.md#a-failed-snapshot-save-does-not-re-fit))", "the draft's replacement dropped still-true text of main's row"),
    {
        "pr": 2437,
        "path": CHEAT,
        "move": {"from": "Tip: a snapshot save that gets any status but 201", "take_blank_before": True, "to_excl": ["`recurrence_up` exports `JUNIPER_RECURRENCE_SNAPSHOTS_DIR"], "strip_tail": [], "before": ["Tip: `compare_baseline.py` is a **split** gate"]},
        "why": "the new Tip split main's save_model Tip from its `recurrence_up` continuation line; moved after it",
    },
    _fx(2422, REF, "records `_CLEANUP_INTERVAL + 10` failures into 255 addresses.", "records `_CLEANUP_INTERVAL + 10` (110) failures into 110 distinct addresses (`10.0.0.{i % 255}` never wraps).", "juniper-service-core/tests/test_middleware.py:478-483"),
    _fx(2422, "juniper-service-core/README.md", "The failure map is also hard-capped at 10,000 source IPs.", "The failure map is also trimmed to 10,000 source IPs at each prune (every 100 recorded failures, so it can briefly hold 10,100).", "security.py:481-491"),
    _fx(2422, REF, "The map itself keeps 10,000 source IPs and drops the oldest `window_start` rows.", "The map itself is pruned to 10,000 source IPs every 100 failures (it can reach 10,100) and drops the oldest `window_start` rows.", "security.py:481-491"),
    _fx(2422, CHEAT, "The expiry test (`window_seconds=0`) does not pin this.", "The expiry test (`window_seconds=0`) does not pin this; `test_failed_auth_throttle_caps_live_entries_by_dropping_the_oldest` does.", "the tests carrier (landing first) adds #2419's test (refs/flood4/pr/2419 test_middleware.py:486)"),
    _fx(2422, REF, "The on-tree expiry test does not pin the cap.", "The expiry test does not pin the cap; `test_failed_auth_throttle_caps_live_entries_by_dropping_the_oldest` in `juniper-service-core/tests/test_middleware.py` does.", "as above"),
    _fx(2433, REF, "Reason `Too many rejected handshakes` is `HandshakeCooldown`. Both live in process memory.", "It is the only 4029 on `/ws/workers` (`HandshakeCooldown`'s `Too many rejected handshakes` is a `/ws/control` close). It lives in process memory.", "HandshakeCooldown is wired only into control_stream.py:84-138; worker_stream.py has none"),
    _fx(2433, CHEAT, "`Too many rejected handshakes` is `HandshakeCooldown`, the other 4029.", "`Too many rejected handshakes` is `HandshakeCooldown`, a `/ws/control` 4029; `/ws/workers` has no cooldown.", "as above"),
    _fx(2433, REF, "`HandshakeCooldown` also closes **4029**, with reason `Too many rejected handshakes`.", "`HandshakeCooldown` closes **4029** `Too many rejected handshakes` only on `/ws/control`; `/ws/workers` has no cooldown.", "as above"),
    _fx(2433, REF, "| rejected handshakes, per client IP |", "| rejected `/ws/control` handshakes, per client IP |", "as above"),
    _fx(2433, REF, "A source that stays quiet for longer than the interval is removed, and its next attempt is a full burst.", "A source that stays quiet for longer than the interval is removed by the next cleanup pass, which runs only once `cleanup_interval` has passed since the last one; its next attempt after that is a full burst. At the defaults the refill alone restores the burst sooner (3 tokens in 18 s).", "workers/security.py:145-150,171-173 (probe: quiet 400 s, last pass 150 s earlier, still mapped)"),
    _fx(2433, REF, "Waiting quietly for longer than `cleanup_interval` replaces the bucket with a full one.", "Waiting quietly for longer than `cleanup_interval` lets the next cleanup pass replace the bucket with a full one.", "as above"),
    _fx(2433, QS, "a quiet source past the cleanup interval gets a new full burst", "a source quiet past the cleanup interval is dropped at the next cleanup pass and returns with a full burst", "as above"),
    _fx(2433, REF, "and every later attempt is refused.", "and every later attempt is refused until a cleanup pass drops the bucket after more than `cleanup_interval` of quiet.", "as above"),
    _fx(2433, REF, "`tests/test_t2_workers.py` (`test_rate_limiter_allows_burst_then_blocks`)", "`juniper-service-core/tests/test_t2_workers.py` (`test_rate_limiter_allows_burst_then_blocks`)", "the root-relative path does not exist"),
    {
        "pr": 2433,
        "path": REF,
        "move": {"from": "#### The worker connection bucket refills only up to its burst", "to_excl": ["Control receives rejects malformed/non-object JSON"], "strip_tail": [""], "before": ["#### A measured zero heartbeat overwrites"]},
        "why": "the inserted heading took over the 'Control receives rejects' line and the service-core symptom table; moved after the table",
    },
    {
        "pr": 2444,
        "path": REF,
        "move": {"from": "#### Training-stream resume and the connection cap", "to_excl": ["| Symptom | Check / Fix |"], "strip_tail": [""], "before": ["#### A measured zero heartbeat overwrites"]},
        "why": "same defect: the inserted heading took over the service-core symptom table; moved after the table",
    },
    # ---- #2444 training-stream resume ----
    _fx(2444, REF, "One seq older than the retained window is `resume_failed` `out_of_range`, and the socket stays up as a fresh snapshot.", "A `last_seq` below `oldest_seq - 1` is `resume_failed` `out_of_range`, and the socket stays up as a fresh snapshot.", "manager.py:379; the draft contradicted its own heading"),
    _fx(2444, CHEAT, "A JSON frame whose length equals 60000 bytes is still one frame.", "A broadcast whose `json.dumps` length equals 60000 is still one frame.", "manager.py:409-413 measures json.dumps before seq is added; the wire frame differs"),
    _fx(2444, CHEAT, "| Training WS closes 1013 while few training sockets show |", "| Training WS handshake refused (HTTP 403 on uvicorn; ASGI close 1013) while few training sockets show |", "pre-accept close; uvicorn websockets_impl.py:278-286 answers 403"),
    _fx(2444, REF, "| Training WS closes 1013 while endpoint gauges look low |", "| Training WS handshake refused (HTTP 403 on uvicorn; ASGI close 1013) while endpoint gauges look low |", "pre-accept close; uvicorn answers 403"),
    _fx(2444, REF, "Close reason is `Per-IP connection limit reached`.", "The ASGI close reason is `Per-IP connection limit reached`; uvicorn answers HTTP 403 without it, so look for the WARNING `per-IP limit of 5 reached for unknown`.", "manager.py:302-310"),
    # ---- #2446 /ws/control edges ----
    _fx(2446, REF, "acks `rate_limited` with `data.retry_after` from `LeakyBucket.retry_after`", "acks `rate_limited` with `data.result.retry_after` from `LeakyBucket.retry_after`", "messages.py:184-190 puts it under payload result"),
    _fx(2446, CHEAT, "Pre-accept close. The log has 1013 (disabled), 4029 (cooldown), 4001 (auth), or 4003 (origin).", "Pre-accept close; no log carries the code. uvicorn logs `\"WebSocket /ws/control\" 403`; the handler logs WARNING `blocked (cooldown)` for 4029 and INFO `not in allowlist` / `no Origin header` for 4003 (visible only with an INFO handler); the kill switch (1013) and a failed key (4001) log nothing.", "uvicorn logs only the 403 line (0.46-0.54); control_stream.py:130-143"),
    _fx(2446, REF, "Pre-accept close. The log has 1013 (disabled), 4029 (cooldown), 4001 (auth), or 4003 (origin).", "Pre-accept close; no log carries the code. uvicorn logs `\"WebSocket /ws/control\" 403`; the handler logs WARNING `blocked (cooldown)` for 4029 and INFO `not in allowlist` / `no Origin header` for 4003 (visible only with an INFO handler); the kill switch (1013) and a failed key (4001) log nothing.", "uvicorn logs only the 403 line (0.46-0.54); control_stream.py:130-143"),
    _fx(2446, REF, "The code remains the ASGI reason in the server log.", "The code is not logged either: uvicorn's line is `\"WebSocket /ws/control\" 403`, and only the cooldown (WARNING `blocked (cooldown)`) and Origin (INFO `not in allowlist` / `no Origin header`) refusals leave a handler log line.", "uvicorn drops the close code; control_stream.py:123-124's docstring is wrong too"),
    _fx(2446, REF, "Pre-accept close. Read the server log for 1013, 4029, 4001, or 4003.", "Pre-accept close; the code is not logged. WARNING `blocked (cooldown)` is 4029, INFO `not in allowlist` / `no Origin header` is 4003; no handler line points at the kill switch (1013) or a failed key (4001).", "as above"),
    # ---- #2449 heartbeat zero ----
    _fx(2449, REF, "Idle count still includes a worker aged exactly one timeout", "Registry still lists a worker aged exactly one timeout (the idle count already omits it)", "registry.py:177,279 exclude it at equality"),
    _fx(2449, CHEAT, "Idle pool still lists a worker aged exactly 30 s", "Registry still lists a worker aged exactly 30 s, but the idle pool does not", "registry.py:177,279"),
    _fx(2449, REF, "| Heartbeat age is 0 while the worker clock is ahead | The collector clamps `now - last_heartbeat` at 0. |", "| Heartbeat age reads 0 after a clock step | `last_heartbeat` is the server's own `time.time()` at receipt, never the worker's clock. The collector clamps `now - last_heartbeat` at 0 when the scrape clock reads earlier than that stamp. |", "registry.py:60,107; metrics.py:107"),
    _fx(2449, REF, "`statistics.quantiles` raises `StatisticsError` below two points; that exception is what the per-snapshot handler logs as a malformed snapshot, which is why the length check comes first.", "On Python 3.12 `statistics.quantiles` raises `StatisticsError` below two points, which the per-snapshot handler would log as a malformed snapshot; 3.13 and later return the single value. The length check comes first, so a one-sample window is omitted on every version.", "3.12.8 raises; 3.13.13 and 3.14.7 return the value (probe); metrics.py:121"),
    _fx(2449, REF, "A `0` means it reported idle.", "A `0` means it reported zero.", "metrics.py:110-116 emits the raw number"),
    _fx(2449, REF, "Absent means no `pending_tasks_source`.", "Absent means no `pending_tasks_source`, or the source raised (logged).", "metrics.py:139-143"),
    _fx(2449, OVER, "**See why a quiet worker still looks busy or stays idle at the timeout**", "**See why a quiet worker still looks busy, or leaves the idle pool at the timeout**", "registry.py:177,279"),
    # ---- #2460 replay clamps / paused fit ----
    _fx(2460, REF, "`create_app` mounts this router from `juniper_service_core.routes.snapshots`.", "`build_routers()` (`juniper_service_core.routes`) includes this router as `snapshots_router` for `create_app(routers=...)`; `create_app` itself mounts only the health router.", "app.py:64-66; routes/__init__.py:51-60"),
    _fx(2460, REF, "The clamp at `±10`, the `0.1` floor, the collapsed range, and the paused-completion rows above were run against this checkout's `ReplaySession`, `LifecycleStateMachine`, and `ServiceLifecycleManager`.", "The `±10` clamp, the `0.1` floor and the collapsed range are pinned by `test_replay_speed_range_edges.py`, and the paused `mark_completed` / `mark_failed` arms by `test_lifecycle_paused_terminal.py` (both from the tests carrier, #2445). No test pins the manager-level rows (monitor `completed`, thread exited, resume starts no `fit`).", "'this checkout' has no meaning in REFERENCE.md; the pins arrive with the tests carrier"),
    # ---- #2462 64 KiB frame ----
    _fx(2462, REF, "On a stock uvicorn the 100 MiB constants do not run: the server has already refused the frame at 16 MiB.", "On a stock uvicorn the per-frame 100 MiB check never fires: the server has already refused any frame over 16 MiB. The 100 MiB total still can: a result may declare 32 attachments, and seven of 16 MiB exceed it.", "worker_stream.py:80,89,344,368-372"),
    _fx(2462, REF, "`len` counts Unicode code points of the string `receive_text()` already built.", "`len` counts Unicode code points of the string the server already decoded (`receive_text()`; `receive()[\"text\"]` in the worker message loop).", "worker_stream.py:224,286-290"),
    _fx(2462, REF, "They leave the equality arm to the `>` comparison above.", "They do not pin the equality arm; `juniper-service-core/tests/test_ws_frame_exact_cap.py` does: a 65536-character control command, pong, registration and heartbeat are each handled, and one character more closes the control channel or the registration, or is refused on an open worker connection, which stays up.", "the tests carrier (landing first) adds #2458's test_ws_frame_exact_cap.py; test names at refs/flood4/pr/2458 :99-194"),
    _fx(2456, REF, "A comparison that rejects equality stays green against those tests and starts failing clients that fill the cap.", "A comparison that rejects equality stays green against those tests and starts failing clients that fill the cap. `juniper-service-core/tests/test_request_body_limit_boundary.py` pins the equality arm: a body, a `Content-Length` and chunks that reach the cap exactly are delivered, and one byte over is a 413 before the route runs.", "the tests carrier (landing first) adds #2451's test_request_body_limit_boundary.py; test names at refs/flood4/pr/2451 :77-130"),
    _fx(2462, REF, "A heartbeat (and any other in-cap JSON) is handled.", "A heartbeat (and any other in-cap JSON object) is handled.", "worker_stream.py:299 has no object guard"),
    # ---- #2464 reassignment timeout ----
    _fx(2464, REF, "A result that arrives after the sweep is rejected (`Result for unassigned task`) and does not enter `collect_results`.", "A result that arrives after the sweep is rejected while the task is still queued (`Result for unassigned task`), or once another worker holds it (`assigned to <id>`). If the same worker was handed it again, the coordinator cannot tell the copies apart: the first result to arrive is accepted and the other is rejected as a `Duplicate result`.", "coordinator.py:409,422,425-432 (probe: the late first-copy result is accepted)"),
    _fx(2464, REF, "The next idle heartbeat dispatches, and a late result for the first copy is rejected as unassigned.", "The next idle heartbeat dispatches. If that is the same task, whichever copy's result arrives first is accepted and the other is a `Duplicate result`.", "as above"),
    _fx(2464, REF, "Another idle worker can take it off the tail first.", "Another idle worker can be handed it first. Dispatch pops the head of `_unassigned_tasks`, so tasks queued ahead of it go out before it.", "coordinator.py:383 pops the head; :617 appends at the tail"),
    _fx(2464, REF, "With the defaults a task can stay assigned until just under 130 seconds.", "With the defaults a task can stay assigned for about 130 seconds: a sweep that sees exactly 120 s leaves it, and the next pass reads the clock at least one interval later.", "coordinator.py:563-565,597-600"),
]

CARRIED = [2409, 2412, 2417, 2418, 2422, 2426, 2428, 2432, 2433, 2437, 2442, 2444, 2446, 2449, 2452, 2456, 2457, 2460, 2462, 2464, 2465]

HISTORY_ROW = (
    f"| 0.6.64  | 2026-11-07 | Cursor flood-4 docs consolidation ({len(CARRIED)} drafts, each claim re-derived): config-tools pitfalls and `py.typed`, "
    "host-check wording, G-SEC `getblockall`, Phase D trial drop-in, `safe_merge` SHA, a measured zero, empty `stats.json`, "
    "snapshot save, service-core limits and edges, recurrence crossval 500 (fixed in 0.8.1), idle compaction. "
    "Header 0.6.63 and footer 0.6.62 reconciled. |"
)

CHANGELOG_ENTRY = (
    "### Added\n"
    "\n"
    "- **Operator documentation consolidated from the Cursor flood-4 docs drafts** (ml#2409, #2412, #2417, #2418,\n"
    "  #2422, #2426, #2428, #2432, #2433, #2437, #2442, #2444, #2446, #2449, #2456, #2457, #2460, #2462, #2464 and\n"
    "  #2465), every claim re-derived from `main`, the sub-package code, PyPI and the Claude Code settings docs:\n"
    "  `docs/REFERENCE.md` 0.6.64, the developer cheatsheet, the documentation overview, the quick start, and the\n"
    "  `juniper-config-tools` and `juniper-service-core` READMEs. #2424 makes #2426's claim and is carried once, in\n"
    "  #2426's wording. Corrected where a draft had gone stale or was wrong: recurrence 0.8.1 has been on PyPI since\n"
    "  2026-11-06, so the crossval-500 page gives the fix instead of a wait; an undeclared `py.typed` still reaches a\n"
    "  wheel (setuptools adds it implicitly), and the 0.1.0 wheel is untyped because the file did not exist yet;\n"
    "  `juniper-config-tools` joined `[tools]` in juniper-ml 0.6.0, not 0.5.0; juniper-ml#2271 closed unmerged; a fit\n"
    "  that returns while paused is documented as the defect it is (after resume a start with data is a 409 until stop\n"
    "  or reset); seven sections that sat in the footer, split a paragraph or had swallowed existing text were moved.\n"
    "  From #2452 only the cheatsheet's `--fork-session` example is carried: its forwarded argv now shows the `--` that\n"
    "  `wake_the_claude.bash` puts before the prompt. Not carried: #2440, the same launcher claim; the rest of #2452's\n"
    "  launcher page predates #2468, whose own cheatsheet text is current.\n"
    "\n"
)
assert len(CARRIED) == 21 and all(f"#{n}" in CHANGELOG_ENTRY for n in CARRIED)

FIXES += [
    {
        "pr": 0,
        "path": REF,
        "old": "Fleet PR Lint is still the one truly advisory job. |\n",
        "new": "Fleet PR Lint is still the one truly advisory job. |\n" + HISTORY_ROW + "\n",
        "why": "the carrier's one Version History row; every draft's own row is dropped",
    },
    {
        "pr": 0,
        "path": "CHANGELOG.md",
        "old": "## [Unreleased]\n\n### Changed\n",
        "new": "## [Unreleased]\n\n" + CHANGELOG_ENTRY + "### Changed\n",
        "why": "the carrier's CHANGELOG entry, under the current top [Unreleased]",
    },
]


# Round 2: the orchestrator's three validators (val-claims-A, val-claims-B, val-fidelity). Each finding was
# re-derived against the code before it was applied; ids are the validators' own.
FIXES += [
    # -- claims-B C1 / C6 / C5: /ws/control logging and block remainder (control_security.py:171-175, :183-185) --
    _fx(2446, REF, "The code is not logged either: uvicorn's line is `\"WebSocket /ws/control\" 403`, and only the cooldown (WARNING `blocked (cooldown)`) and Origin (INFO `not in allowlist` / `no Origin header`) refusals leave a handler log line.", "The code is not logged either: uvicorn's line is `\"WebSocket /ws/control\" 403`. The handler logs WARNING `blocked (cooldown)` for a 4029 and INFO `not in allowlist` / `no Origin header` for a 4003; the INFO lines appear only when the service logs `juniper_service_core` at INFO, because neither service-core nor uvicorn's default logging config gives it a handler. The kill switch (1013) and a failed key (4001) log nothing, except the rejection that reaches `ws_control_cooldown_rejections` (default the 10th): it logs WARNING `blocked for 300s (cooldown triggered)` and still closes 4001 or 4003; the next attempt is the 4029.", "claims-B C1+C6: control_security.py:171-175 warns inside record_rejection; control_stream.py:141-143; no basicConfig/dictConfig in service-core"),
    _fx(2446, REF, "| The client sees HTTP 403, not close 4029 or 4003 | Pre-accept close; the code is not logged. WARNING `blocked (cooldown)` is 4029, INFO `not in allowlist` / `no Origin header` is 4003; no handler line points at the kill switch (1013) or a failed key (4001). |", "| The client sees HTTP 403, not close 4029 or 4003 | Pre-accept close; the code is not logged. WARNING `blocked (cooldown)` is 4029; INFO `not in allowlist` / `no Origin header` (logged at INFO) is 4003. WARNING `blocked for 300s (cooldown triggered)` belongs to the 4001 or 4003 attempt that started the block, not to a 4029. No other handler line points at the kill switch (1013) or a failed key (4001). |", "claims-B C1"),
    _fx(2446, REF, "the kill switch (1013) and a failed key (4001) log nothing. |", "the kill switch (1013) logs nothing, and a failed key (4001) logs nothing except on the rejection that starts the cooldown (WARNING `blocked for 300s (cooldown triggered)`, still a 4001). |", "claims-B C1"),
    _fx(2446, CHEAT, "the kill switch (1013) and a failed key (4001) log nothing. |", "the kill switch (1013) logs nothing, and a failed key (4001) logs nothing except on the rejection that starts the cooldown (WARNING `blocked for 300s (cooldown triggered)`, still a 4001). |", "claims-B C1"),
    _fx(2446, REF, "Slightly earlier it returns the remainder rounded to one decimal: 0.06 s remaining reports **0.1**.", "Slightly earlier it returns the remainder rounded to one decimal: 0.06 s remaining reports **0.1**. Under 0.05 s it reports **0.0** while the IP is still blocked, so the 4029 WARNING can print `remaining=0.0s`; from the exact end on it returns `None`.", "claims-B C5: control_security.py:183-185 round(remaining, 1)"),
    _fx(2446, REF, "Equality clears the entry and `get_block_remaining` is `None`. |", "Equality clears the entry and `get_block_remaining` is `None`. Under 0.05 s before the end it already reports `0.0`, while the IP is still blocked. |", "claims-B C5"),
    # -- claims-B W1 / W7 / W8 / R6 / W6: late results, round boundary, dispatch paths (coordinator.py:352, :378-391, :404-432; worker_stream.py:325-326) --
    _fx(2464, REF, "or once another worker holds it (`assigned to <id>`). If the same worker was handed it again, the coordinator cannot tell the copies apart: the first result to arrive is accepted and the other is rejected as a `Duplicate result`.", "or once another worker holds it (`assigned to <id>`; `Duplicate result` once that worker's result is in). If the same worker was handed it again, the coordinator cannot tell the copies apart: the first result to arrive is accepted and, while the round lasts, the other is a `Duplicate result`. `submit_tasks` clears the duplicate set but keeps finished tasks in `_pending_tasks`, so a copy that arrives after the next round starts is accepted and counts toward that round, unless `cancel_round()` ran in between (it clears `_pending_tasks`, and the copy is then `Result for unknown task`).", "claims-B W1+W7; round-2 F10: coordinator.py:540-546: coordinator.py:352 clears _completed_task_ids only; :409 duplicate check precedes :422-432 ownership"),
    _fx(2464, REF, "The next idle heartbeat dispatches. If that is the same task, whichever copy's result arrives first is accepted and the other is a `Duplicate result`. |", "The next idle heartbeat can hand it the same task, and so can the dispatch that follows its late result; that late result was rejected as `Result for unassigned task`, so the new copy is then the only one. On the heartbeat path, whichever copy's result arrives first is accepted and, within the round, the other is a `Duplicate result`; a copy that arrives after the next round starts is accepted as that round's result, unless `cancel_round()` ran in between. |", "claims-B W1+W8: worker_stream.py:325-326 dispatches after every task_result"),
    _fx(2449, REF, "so a worker aged exactly one timeout can take one more task until that sweep removes it.", "so a worker aged exactly one timeout can still be handed tasks, one after each result it submits (only a heartbeat refreshes `last_heartbeat`), until that sweep removes it.", "claims-B R6: coordinator.py:378-379 checks registration only; worker_stream.py:325-326"),
    _fx(2464, REF, "| `active_task_id` is a different task | Stays registered. `tasks_failed` is not incremented, and the other task stays active. | Same requeue. |", "| `active_task_id` is a different task, or `None` | Stays registered. `tasks_failed` is not incremented, and any other active task stays. (`get_next_assignment` ignores `assign_task`'s `False`, so a busy worker can be handed a second task and later read idle while it is still that task's assignee.) | Same requeue. |", "claims-B W6: coordinator.py:389-391 ignores registry.py:254-261's False"),
    # -- claims-B W2 / W10 / W4 / W5 / W9 / W3: anomaly detector --
    _fx(2442, REF, "Both loggers are `WARNING`.", "Both lines log at WARNING.", "claims-B W10: security.py:250 and coordinator.py:460 are logger.warning calls; no setLevel"),
    _fx(2442, REF, "fail the task, or call `AuditLogger.on_anomaly`.", "fail the task, call `WorkerMetrics.on_anomaly`, or emit an `AuditLogger` `ANOMALY_DETECTED` event.", "claims-B W2: audit.py:46 AuditLogger has log/get_counts/reset_counts; :87/:123 WorkerMetrics.on_anomaly; nothing emits ANOMALY_DETECTED"),
    _fx(2442, REF, "A service opts in by assigning `coordinator.anomaly_detector`.", "A service opts in with `WorkerCoordinator(..., anomaly_detector=AnomalyDetector())` or by assigning `coordinator.anomaly_detector`.", "claims-B W4: coordinator.py:220 constructor keyword"),
    _fx(2442, CHEAT, "A scored worker result with no `duration` logs `suspiciously_fast: 0.000s` and is still accepted.", "With an `AnomalyDetector` wired (the coordinator default is `None`), a scored worker result with no `duration` logs `suspiciously_fast: 0.000s` and is still accepted.", "claims-B W5: coordinator.py:220 default None"),
    _fx(2442, REF, "History is per `worker_id`, in memory, and trimmed to the last `duplicate_window` records after each append.", "History is per `worker_id`, in memory, and trimmed to the last `duplicate_window` records after each append. The flag needs a window of 3 or more: with 1 or 2 it never fires, and 0 disables trimming (`history[-0:]` is the whole list), so every result the worker has sent is compared and `total_results` is then a lifetime count.", "claims-B W9 (reworded: window 0 can still flag): security.py:239-247"),
    _fx(2442, REF, "(3 through `duplicate_window`)", "(3 through `duplicate_window`, for a window of 3 or more)", "claims-B W9"),
    _fx(2442, REF, "`test_t2_worker_coordinator.py` (`test_anomaly_detector_skipped_when_score_is_none`).", "`test_t2_worker_coordinator.py` (`test_anomaly_detector_skipped_when_score_is_none`); `test_anomaly_detector_edges.py` (the strict bounds and the six-decimal duplicate window); `test_submit_result_anomaly_accepts.py` (the missing-duration and zero-score submit paths).", "claims-B W3: both files are in the tests carrier, which merges first"),
    _fx(2464, REF, "It does not pin equality.", "It does not pin equality; `juniper-service-core/tests/test_task_reassignment_timeout_boundary.py` pins equality, a zero timeout, one second over, and a completed task.", "claims-B W3: tests carrier test_task_reassignment_timeout_boundary.py:56,82,106,141"),
    # -- claims-B S1 / S4 / S2 / S6 / S5: WebSocket frames and resume --
    _fx(2462, REF, "| A huge worker binary never returns `Binary frame too large` | Stock uvicorn drops the frame at `ws_max_size` (default 16 MiB) before the 100 MiB check. |", "| A huge worker binary never returns `Binary frame too large` | Stock uvicorn closes the connection with **1009** at `ws_max_size` (default 16 MiB) before the handler sees the frame; the reason depends on the WebSocket implementation (empty under the legacy `websockets` one) and is never `Message too large`. The server then deregisters the worker and requeues its task. |", "claims-B S1: worker_stream.py:193-208 finally releases tasks and deregisters"),
    _fx(2462, REF, "A frame of exactly that many bytes is submitted. Stock uvicorn refuses the frame earlier, at `ws_max_size` (default 16 MiB).", "A frame of exactly that many bytes passes the per-frame check; the result is submitted only if all its attachments together stay within 100 MiB. Stock uvicorn closes the connection with **1009** earlier, at `ws_max_size` (default 16 MiB).", "claims-B S1+S4: worker_stream.py:89 _MAX_TOTAL_BINARY_SIZE = _MAX_BINARY_SIZE; :368-372"),
    _fx(2462, REF, "the server has already refused any frame over 16 MiB.", "the server has already closed the connection (**1009**) on any frame over 16 MiB.", "claims-B S1"),
    _fx(2462, CHEAT, "A binary frame of exactly 100 MiB is submitted; stock uvicorn stops a frame at `ws_max_size` (16 MiB) first.", "A binary frame of exactly 100 MiB passes the per-frame check (a result's attachments must total at most 100 MiB); stock uvicorn closes the connection with 1009 at `ws_max_size` (16 MiB) first.", "claims-B S1+S4"),
    _fx(2444, REF, "The default buffer keeps the last **1024** broadcasts. Continuity holds when `last_seq >= oldest_seq - 1`. The raise is `last_seq < oldest_seq - 1`.", "The default buffer keeps the last **1024** sequenced frames (each chunk of a split broadcast takes one). Continuity holds when `last_seq >= oldest_seq - 1`. The raise is `last_seq < oldest_seq - 1`. A `resume_ok` does not prove that nothing was missed (current behaviour, a defect candidate). A broadcast made while no socket is active, including during a sole client's pending resume, is never sequenced or buffered (`broadcast` returns first). One that lands while the replay is being sent is buffered but reaches only active sockets, and the resuming socket is promoted only after the replay, so the client can see a seq gap: `_handle_resume` sends the `replay_since` snapshot one awaited frame at a time while the socket is still pending.", "claims-B S2+S6; round-2 F1: training_stream.py:205-206 promotes after :259-274's awaited replay sends; manager.py:456 sends to active sockets only: manager.py:451-452 returns with no active socket; :312-314 pending is not active; :453-454 one seq per chunk"),
    _fx(2444, REF, "| at or past the newest seq | the client is caught up, or ahead |", "| at or past the newest seq | the client claims every buffered message, or is ahead (it can still have missed one; see above) |", "claims-B S2; round-2 F1"),
    _fx(2444, REF, "Pending handshakes count toward the global cap (close **1013**), and address-less sockets share `\"unknown\"`.", "A `resume_ok` can still miss a broadcast made while no socket was active (never sequenced) or one that lands during the replay send (buffered, but sent only to active sockets); that is current behaviour, not a guarantee. Pending handshakes count toward the global cap (ASGI close **1013**; HTTP 403 on uvicorn), and address-less sockets share `\"unknown\"`.", "claims-B S2; the 403 matches the round-1 #2444 fix"),
    _fx(2444, CHEAT, "Pending handshakes count toward the **1013** cap.", "A `resume_ok` can still miss a broadcast made while no socket was active, or one that lands while the replay is being sent. Pending handshakes count toward the **1013** cap.", "claims-B S2; round-2 F1"),
    _fx(2462, OVER, "**See whether a 64 KB WebSocket text frame is delivered**", "**See whether a 65536-character WebSocket text frame is delivered**", "claims-B S5: the cap counts code points (control_stream.py:230)"),
    # -- claims-B R1-R5, B-own-4: replay and the paused-completion edge --
    _fx(2460, REF, ", a magnitude below `0.1` leaves the index where it is, and a `fit` that returns while the lifecycle is `PAUSED` leaves that status while the monitor says `completed`.", ", and a magnitude below `0.1` leaves the index where it is. A `fit` that returns while the lifecycle is `PAUSED` leaves that status while the monitor says `completed`; that is a known defect, not a contract to keep: after resume the machine is `STARTED` with no thread, and a start with data is refused (409) until stop or reset.", "claims-B R1: lifecycle/manager.py:164-165, :210-217, :283-290"),
    _fx(2460, REF, "Resume does not start another `fit`.", "Resume does not start another `fit`. The machine then stays `STARTED` with no thread (`monitor.status` `running`), and a `POST /v1/training/start` with `inline_data` is refused (409, `Training cannot be started: Training already in progress`; without data it is a 400 first) until `POST /v1/training/stop` or `POST /v1/training/reset`.", "claims-B R1: routes/training.py:58-61; state_machine.py:87 RESET always valid"),
    _fx(2460, REF, "Resume reports `STARTED` and does not start a thread. |", "Resume reports `STARTED` and does not start a thread; a start with data is then a 409 until `POST /v1/training/stop` or `/reset`. |", "claims-B R1"),
    _fx(2460, CHEAT, "Resume then reports STARTED with the thread already gone.", "Resume then reports STARTED with the thread already gone, and a start with data is refused (409) until `POST /v1/training/stop` or `/reset`.", "claims-B R1"),
    _fx(2460, REF, "An unknown action is HTTP 422. No active session is HTTP 409. Snapshots disabled is HTTP 501.", "Snapshots disabled is HTTP 501. Otherwise, with no active session every action is HTTP 409; with a session, an unknown action is HTTP 422.", "claims-B R2: lifecycle/manager.py:520-522 checks the session before replay.py:75-76 validates the action"),
    _fx(2460, REF, "`replay.speed` in the response is `10.0`.", "`data.replay.speed` in the response is `10.0`.", "claims-B R3: routes/snapshots.py:133 success_response envelope"),
    _fx(2460, REF, "`replay.range` is `{\"start\": 5, \"end\": 5}`", "`data.replay.range` is `{\"start\": 5, \"end\": 5}`", "claims-B R3"),
    _fx(2460, REF, "| training thread | already exited |", "| training thread (observed; not a `get_status()` field) | already exited |", "claims-B R3: _status_dict (lifecycle/manager.py:600-610) has no thread field"),
    _fx(2460, REF, "The shared `ReplaySession` in this repo (the speed clamp, the half-second tick cap, and a fit that returns while paused) is [Replay speed, range, and a paused completion](#replay-speed-range-and-a-paused-completion).", "The shared `ReplaySession` (the speed clamp, the half-second tick cap) and the lifecycle's paused-completion edge are in [Replay speed, range, and a paused completion](#replay-speed-range-and-a-paused-completion).", "claims-B R4: replay.py has no fit/lifecycle code"),
    _fx(2460, REF, "so an inverted pair collapses to a point.", "so an inverted pair collapses to an empty range at `start`.", "claims-B R5: replay.py:89-91 end = max(start, ...)"),
    _fx(2460, REF, " (both from the tests carrier, #2445)", "", "claims-B B-own-4: a permanent page must not name a transient process"),
    # -- claims-A F2 / F3 / F4 / F5 / F6 / F8 / F9 / F10 --
    _fx(2437, REF, "The connection, timeout, missing-`size_bytes`, and `OSError` rows are the same function's other returns.", "The HTTP 500, dropped-connection, missing-`size_bytes` and copy-`OSError` cases are pinned by `test_a_snapshot_store_error_fails_the_phase_and_does_not_refit`, `test_a_dropped_snapshot_save_stays_a_failed_phase`, `test_a_snapshot_without_size_bytes_is_not_vouched_for` and `test_a_failed_copy_removes_the_partial_model_and_does_not_refit` in the same file; a socket timeout, which the `POST ` row also covers, is the only case no test pins.", "claims-A F2: tests carrier tests/test_recurrence_operation_identity_and_dataset_budget.py:649,667,691,706"),
    _fx(2433, REF, "That test stays at the exhausted instant, so a refill that ignored the cap would still pass it.", "That test stays at the exhausted instant, so a refill that ignored the cap would still pass it. `test_rate_limiter_refills_only_up_to_burst_and_a_denial_spends_nothing` and `test_rate_limiter_cleanup_keeps_a_bucket_aged_exactly_one_interval` (`juniper-service-core/tests/test_workers_coverage.py`) pin the cap, the no-spend refusal and the keep at an age of exactly one interval.", "claims-A F2: tests carrier test_workers_coverage.py:517,547"),
    _fx(2417, REF, "A reported `0` stays on all three surfaces — [A zero is a measured value](#a-zero-is-a-measured-value)", "A reported `0` stays in `summary.md` and the plot, and in its `test_*` column when the final block's `split` is `test` — [A zero is a measured value](#a-zero-is-a-measured-value)", "claims-A F3: run_suite.py:170-174, :931-941"),
    _fx(2417, REF, "`summary.md`, `eval_metrics.png`, and the suite columns keep a score of `0` or `0.0`.", "`summary.md`, `eval_metrics.png`, and the `test_*` columns (a test-split final block only) keep a score of `0` or `0.0`.", "claims-A F3"),
    _fx(2428, REF, "A net that merges first prints no SHA.", "A net that merged before this run's merge call prints no SHA; one that wins during the call prints the verified head.", "claims-A F4: safe_merge.py:1134-1136"),
    _fx(2409, CHEAT, "and must not be chained with `or`.", "and must not be chained with `or` when `\"\"` is a real value (chain on `is not None`).", "claims-A F5: _env_aliases.py:20-22 recommends the or chain"),
    _fx(2422, REF, "`RateLimiter`'s `test_maybe_cleanup_enforces_hard_cap` does pin oldest-drop", "`RateLimiter`'s `test_maybe_cleanup_enforces_hard_cap` (in `juniper-service-core/tests/test_toplevel_coverage.py`) does pin oldest-drop", "claims-A F6: test_toplevel_coverage.py:262"),
    _fx(2418, REF, "| `1` | `REFUSED:` on stderr. Nothing left written |", "| `1` | `REFUSED:` on stderr. Nothing left written, unless a WARNING says the created file could not be removed |", "claims-A F8: write_matched_settings_key.py:401-408, :429-436"),
    _fx(2412, REF, "and 2 when VBoxManage is missing, the VM is not registered, or an input cannot be measured.", "and 2 on an environment error (VBoxManage missing or failing, the VM not registered) or an input that cannot be measured.", "claims-A F9: macvm_ctl.bash:233, :496-508"),
    _fx(2432, REF, "(missing file, `{`, gone directory), and `test_no_run_dir_and_a_non_mapping_record_are_empty`.", "(missing file, `{`, gone directory), `test_no_run_dir_and_a_non_mapping_record_are_empty`, `test_an_empty_object_is_a_readable_file_with_no_headline` (`{}`), and `test_a_json_value_that_is_not_an_object_falls_back_to_the_recorded_metrics`.", "claims-A F10: tests carrier tests/test_run_suite.py:1296,1303"),
    _fx(2417, REF, "Headline `0.0` is the `_is_metric` contract in", "The zero cases are pinned by `test_a_zero_accuracy_is_reported_not_omitted` and `test_a_zero_score_is_a_bar_and_false_is_not` in the same file and by `test_a_zero_theta_is_a_value` in `tests/test_stats_summary_render.py`. Headline `0.0` is the `_is_metric` contract in", "claims-A F10: tests carrier test_stats_summary_eval_blocks.py:196,252; test_stats_summary_render.py:206"),
    # -- claims-A F7 / fidelity F2: TOC order, labels, and the h2-only convention --
    _fx(2426, REF, "- [The firewall gate reads getblockall](#the-firewall-gate-reads-getblockall)\n- [Host-Check Wording (E-H3)](#host-check-wording-e-h3)\n", "- [Host-Check Wording (E-H3)](#host-check-wording-e-h3)\n- [The firewall gate reads getblockall](#the-firewall-gate-reads-getblockall)\n", "claims-A F7 / fidelity F2: the body has Host-Check first"),
    _fx(2428, REF, "- [The MERGED Line's SHA Is the Verified Head](#the-merged-lines-sha-is-the-verified-head)", "- [The MERGED line's SHA is the verified head](#the-merged-lines-sha-is-the-verified-head)", "claims-A F7 / fidelity F2: the heading's own text"),
    _fx(2437, REF, "- [Experiment Stack Utilities](#experiment-stack-utilities)\n- [A failed snapshot save does not re-fit](#a-failed-snapshot-save-does-not-re-fit)\n", "- [Experiment Stack Utilities](#experiment-stack-utilities)\n", "claims-A F7: main's TOC lists only ## sections; this target is #####"),
    _fx(2464, REF, "- [A task assigned for exactly the reassignment timeout stays assigned](#a-task-assigned-for-exactly-the-reassignment-timeout-stays-assigned)\n", "", "claims-A F7: main's TOC lists only ## sections; this target is ####"),
    _fx(2462, REF, "- [A WebSocket text frame that fills 65536 characters is delivered](#a-websocket-text-frame-that-fills-65536-characters-is-delivered)\n", "", "claims-A F7: main's TOC lists only ## sections; this target is ####"),
    _fx(2444, REF, "- [Training-stream resume and the connection cap](#training-stream-resume-and-the-connection-cap)\n", "", "claims-A F7: main's TOC lists only ## sections; this target is ####"),
    _fx(2433, REF, "- [The Worker Connection Bucket Refills Only up to Its Burst](#the-worker-connection-bucket-refills-only-up-to-its-burst)\n", "", "claims-A F7: main's TOC lists only ## sections; this target is ####"),
    # -- claims-B B-own-1 / B-own-2 / C3 / C4 --
    _fx(2465, REF, "| `.claude/settings.json` | Everyone who clones this repo |", "| `.claude/settings.json` | Everyone who clones this repo, once it is committed. This repo's `.gitignore` (`.claude/*`) ignores it today, so committing it needs a `!.claude/settings.json` re-include or a forced add. A CLI session reads it from its primary working directory; a worktree session started from the desktop app reads the main checkout's copy |", "claims-B B-own-1: git check-ignore -> .gitignore:179 .claude/*; settings docs: read from the primary working directory"),
    _fx(2457, REF, "`juniper-recurrence` 0.8.0 passes `groups=` on every `POST /v1/crossval`, including a series whose `ticker_code` is missing.", "`juniper-recurrence` 0.8.0 passes `groups=` on every `POST /v1/crossval` that reaches the fold cut, including a series whose `ticker_code` is missing (a busy `409`, a dataset-fetch error, and `embargo_days` on an artifact with no `window_end_date` return earlier).", "claims-B B-own-2: v0.8.0 routers/crossval.py lock/map_data_error/build_folds; _folds.py embargo_days ValueError precedes walk_forward_folds"),
    _fx(2456, REF, "The shipped body-limit tests send a payload strictly inside the cap", "This table is the middleware at the ASGI layer (`TestClient`, direct ASGI). Under uvicorn the HTTP parser answers a non-integer `Content-Length` itself (400 `Invalid HTTP request received.` under httptools) and delivers only the declared length of an under-declared body, before this middleware runs.\n\nThe body-limit tests in `test_middleware.py` and `test_toplevel_coverage.py` send a payload strictly inside the cap", "claims-B C3+C4: uvicorn httptools_impl.py:174-175; HTTP/1.1 Content-Length framing"),
    _fx(2456, REF, "(`test_body_limit_allows_within_limit`, `test_body_limit_rejects_oversized_post`,", "(`test_body_limit_allows_within_limit`, `test_body_limit_allows_put_within_limit`, `test_body_limit_rejects_oversized_post`,", "claims-B C3: test_middleware.py:132 on main"),
    _fx(2456, REF, "`test_body_limit_rejects_oversized_chunked_stream`).", "`test_body_limit_rejects_oversized_chunked_stream`) and `juniper-service-core/tests/test_request_body_limit_boundary.py` (the equality arm).", "claims-B C3"),
    # -- fidelity F1 / F3 / F4 / F6 --
    _fx(2442, REF, "See [PF Scenario Suites](#pf-scenario-suites).\n\n## Worker Result Anomaly Detector", "See [PF Scenario Suites](#pf-scenario-suites).\n\n---\n\n## Worker Result Anomaly Detector", "fidelity F1: every other ## section is preceded by a rule; the draft had one"),
    _fx(2457, CHEAT, "Full contract: [REFERENCE — Crossval 500 with model-core 0.2.0](REFERENCE.md#crossval-500-with-model-core-020).", "Full contract: [REFERENCE — Recurrence Env Preflight](REFERENCE.md#recurrence-env-preflight); the 0.8.0 + model-core 0.2.0 case: [REFERENCE — Crossval 500 with model-core 0.2.0](REFERENCE.md#crossval-500-with-model-core-020).", "fidelity F3: the draft replaced main's still-true contract pointer"),
    _fx(2452, CHEAT, "# Forwards args to claude as: --resume <uuid> --fork-session \"hello\"", "# Forwards args to claude as: --resume <uuid> --fork-session -- hello", "fidelity F4: wake_the_claude.bash:342 CLAUDE_END_OF_OPTIONS_FLAG=\"--\"; tests/test_wake_the_claude.py:1331 asserts [..., '--fork-session', '--', 'hello']"),
    # -- round 3 (val-round2): new entries; the other round-2 findings changed the NEW texts above in place --
    _fx(2456, REF, "so an under-declared header or a chunked body with none still 413s.", "so an under-declared header (at the ASGI layer; under uvicorn the parser truncates the body to the declared length first) or a chunked body with none still 413s.", "round-2 F2, a fix to main's CR-024 wording: true only at the ASGI layer (uvicorn httptools_impl.py:169-177 owns Content-Length framing; test_middleware.py:143-152 drives ASGI directly)"),
    _fx(2417, CHEAT, "; a bool does not;", "; a bool is text in `summary.md` only;", "round-2 F3: summary.md prints the words False / True (REFERENCE's zero table)"),
    _fx(2417, QS, "; a bool does not;", "; a bool is text in `summary.md` only;", "round-2 F3"),
    _fx(2417, OVER, "**Read a zero score or a zero θ**", "**Read a zero score or a zero theta**", "round-2 F14: the overview is ASCII apart from the em dash"),
    _fx(2462, REF, "Attachments over `_MAX_BINARY_SIZE` (100 MB)", "Attachments over `_MAX_BINARY_SIZE` (100 MiB)", "round-2 F15, a fix to main's wording: worker_stream.py:72 _MAX_BINARY_SIZE = 100 * 1024 * 1024"),
    _fx(2456, OVER, "a non-ASCII `X-API-Key` is a 401 on `main` (published 0.7.0 still 500s)", "a non-ASCII `X-API-Key` is a 401 from 0.7.1 (0.7.0 still 500s)", "round-2 F16, a fix to main's wording: PyPI juniper-service-core 0.7.1 uploaded 2026-10-10T10:04Z"),
    {
        "pr": 2465,
        "path": CHEAT,
        "move": {"from": "The tracked root `settings.local.json` is not a Claude Code settings file.", "to_excl": ["`wake_the_claude.bash` sends the prompt (from `--prompt`"], "strip_tail": [""], "before": ["### Session ID and Resume"]},
        "why": "fidelity F6: the note split #2468's launcher contract; moved after the Interactive/Headless paragraph",
    },
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], "w", encoding="utf-8") as fh:
        json.dump(FIXES, fh, indent=2)
    print(f"{len(FIXES)} fixes written to {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
