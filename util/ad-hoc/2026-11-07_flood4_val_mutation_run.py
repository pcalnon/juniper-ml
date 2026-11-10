"""
Validator-chosen one-line mutants for the flood-4 tests carrier's sub-package slice (15 test files).
For each mutant: require the anchor text to occur exactly once, sha256 the target, clear the
package's __pycache__, apply, run ONLY the carried test file under the CI-parity venv, restore the
original bytes, verify sha256, clear __pycache__ again. Failing tests are classified NEW vs
PRE-EXISTING by comparing test names with the file's version on origin/main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier validation, sub-package slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (BRIEF_VALIDATE.txt)

Usage: python3 <this> <worktree> <venv root> <scratch dir> [mutant ids...]
"""

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

SC = "juniper-service-core/juniper_service_core/"
CT = "juniper-ci-tools/juniper_ci_tools/"
T_SC = "juniper-service-core/tests/"
T_CT = "juniper-ci-tools/tests/"

SPEC = [
    ("A1", T_SC + "test_anomaly_detector_edges.py", SC + "workers/security.py", "if abs(score) < self._stale_threshold:", "if score < self._stale_threshold:"),
    ("A2", T_SC + "test_anomaly_detector_edges.py", SC + "workers/security.py", 'unique = len({f"{s:.6f}" for s in recent_scores})', 'unique = len({f"{s:.5f}" for s in recent_scores})'),
    ("B1", T_SC + "test_attachment_budget_exact.py", SC + "websocket/worker_stream.py", "if total_bytes > _MAX_TOTAL_BINARY_SIZE:", "if total_bytes >= _MAX_TOTAL_BINARY_SIZE:"),
    ("B2", T_SC + "test_attachment_budget_exact.py", SC + "websocket/worker_stream.py", "if total_bytes > _MAX_TOTAL_BINARY_SIZE:", "if total_bytes > _MAX_TOTAL_BINARY_SIZE + 1:"),
    ("B3", T_SC + "test_attachment_budget_exact.py", SC + "websocket/worker_stream.py", "if len(raw_bytes) > _MAX_BINARY_SIZE:", "if len(raw_bytes) > _MAX_BINARY_SIZE + 1:"),
    ("C1", T_SC + "test_lifecycle_paused_terminal.py", SC + "lifecycle/state_machine.py", "if self._status in (LifecycleStatus.STARTED, LifecycleStatus.PAUSED):\n            prev = self._status.name\n            self._status = LifecycleStatus.FAILED", "if self._status is LifecycleStatus.STARTED:\n            prev = self._status.name\n            self._status = LifecycleStatus.FAILED"),
    ("C2", T_SC + "test_lifecycle_paused_terminal.py", SC + "lifecycle/state_machine.py", "if self._status is LifecycleStatus.STARTED:\n            self._status = LifecycleStatus.PAUSED", "if self._status is not LifecycleStatus.PAUSED:\n            self._status = LifecycleStatus.PAUSED"),
    ("D1", T_SC + "test_middleware.py", SC + "security.py", "if len(self._failures) > self._MAX_ENTRIES:", "if len(self._failures) > self._MAX_ENTRIES + 1:"),
    ("D1b", T_SC + "test_middleware.py", SC + "security.py", "if len(self._failures) > self._MAX_ENTRIES:", "if len(self._failures) >= self._MAX_ENTRIES:"),
    ("D2", T_SC + "test_middleware.py", SC + "security.py", "for ip in oldest[: len(self._failures) - self._MAX_ENTRIES]:", "for ip in oldest[: len(self._failures) - self._MAX_ENTRIES - 1]:"),
    ("E1", T_SC + "test_registry_measured_zero.py", SC + "workers/registry.py", "return (time.time() - self.last_heartbeat) < timeout", "return (time.time() - self.last_heartbeat) <= timeout"),
    ("E2", T_SC + "test_registry_measured_zero.py", SC + "workers/metrics.py", "if gpu_util is not None:", "if gpu_util:"),
    ("E3", T_SC + "test_registry_measured_zero.py", SC + "workers/registry.py", "if recent_task_durations_seconds is not None:", "if recent_task_durations_seconds:"),
    ("F1", T_SC + "test_replay_speed_range_edges.py", SC + "lifecycle/replay.py", "if self._paused or abs(self._speed) < 0.1:", "if self._paused or abs(self._speed) <= 0.1:"),
    ("F2", T_SC + "test_replay_speed_range_edges.py", SC + "lifecycle/replay.py", "if nxt < self._range_start or nxt >= self._range_end:", "if nxt < self._range_start - 1 or nxt >= self._range_end:"),
    ("F3", T_SC + "test_replay_speed_range_edges.py", SC + "lifecycle/replay.py", 'end = max(start, min(int(params.get("end", self._range_end)), self._length))', 'end = min(int(params.get("end", self._range_end)), self._length)'),
    ("G1", T_SC + "test_request_body_limit_boundary.py", SC + "middleware.py", "if size > self._max_bytes:", "if size >= self._max_bytes:"),
    ("G2", T_SC + "test_request_body_limit_boundary.py", SC + "middleware.py", "if size > self._max_bytes:", "if size > self._max_bytes + 1:"),
    ("G3", T_SC + "test_request_body_limit_boundary.py", SC + "middleware.py", "if declared_length > self._max_bytes:", "if declared_length > self._max_bytes + 1:"),
    ("H1", T_SC + "test_security.py", SC + "security.py", "self._counters[key] = (1, now)\n                return (True, self._limit - 1, self._window)", "self._counters[key] = (1, now)\n                pass"),
    ("H2", T_SC + "test_security.py", SC + "security.py", "if now - window_start >= self._window:\n                self._counters[key] = (1, now)", "if now - window_start >= self._window + 1:\n                self._counters[key] = (1, now)"),
    ("I1", T_SC + "test_submit_result_anomaly_accepts.py", SC + "workers/coordinator.py", "if self._anomaly_detector is not None and parsed.score is not None:", "if self._anomaly_detector is not None and parsed.score:"),
    ("I2", T_SC + "test_submit_result_anomaly_accepts.py", SC + "workers/coordinator.py", "training_duration=parsed.duration or 0.0,", "training_duration=parsed.duration or 1.0,"),
    ("J1", T_SC + "test_task_reassignment_timeout_boundary.py", SC + "workers/coordinator.py", "(now - task.dispatched_at) > self._task_reassignment_timeout:", "(now - task.dispatched_at) > self._task_reassignment_timeout + 1.0:"),
    ("J2", T_SC + "test_task_reassignment_timeout_boundary.py", SC + "workers/coordinator.py", "if task.assigned_worker_id is not None and not task.completed and (now - task.dispatched_at)", "if task.assigned_worker_id is not None and (now - task.dispatched_at)"),
    ("K1", T_SC + "test_websocket_control_security.py", SC + "websocket/control_security.py", "[t for t in timestamps if t > cutoff]", "[t for t in timestamps if t >= cutoff]"),
    ("K2", T_SC + "test_websocket_control_security.py", SC + "websocket/control_security.py", "if time.monotonic() < blocked_until:", "if time.monotonic() <= blocked_until:"),
    ("K3", T_SC + "test_websocket_control_security.py", SC + "websocket/control_security.py", "all(t < cutoff for t in timestamps)", "all(t <= cutoff for t in timestamps)"),
    ("K4", T_SC + "test_websocket_control_security.py", SC + "websocket/control_security.py", "    if not origin:", "    if origin is None:"),
    ("K5", T_SC + "test_websocket_control_security.py", SC + "websocket/control_security.py", "if self._tokens >= 1.0:\n                self._tokens -= 1.0", "if self._tokens > 1.0:\n                self._tokens -= 1.0"),
    ("L1", T_SC + "test_websocket_replay_continuity.py", SC + "websocket/manager.py", "if last_seq < oldest_seq - 1:", "if last_seq < oldest_seq - 2:"),
    ("L2", T_SC + "test_websocket_replay_continuity.py", SC + "websocket/manager.py", "if last_seq > 0:", "if last_seq > 1:"),
    ("L3", T_SC + "test_websocket_replay_continuity.py", SC + "websocket/manager.py", "if len(serialized) <= self._max_message_size_bytes:", "if len(serialized) < self._max_message_size_bytes:"),
    ("M1", T_SC + "test_workers_coverage.py", SC + "workers/security.py", "if now - b.last_access > self._cleanup_interval]", "if now - b.last_access >= self._cleanup_interval]"),
    ("M2", T_SC + "test_workers_coverage.py", SC + "workers/security.py", "if now - self._last_cleanup < self._cleanup_interval:", "if now - self._last_cleanup <= self._cleanup_interval:"),
    ("M3", T_SC + "test_workers_coverage.py", SC + "workers/security.py", "elapsed = now - self.last_refill", "elapsed = 0.0"),
    ("N1", T_SC + "test_ws_frame_exact_cap.py", SC + "websocket/worker_stream.py", "\n    if len(raw) > _MAX_JSON_SIZE:", "\n    if len(raw) >= _MAX_JSON_SIZE:"),
    ("N2", T_SC + "test_ws_frame_exact_cap.py", SC + "websocket/worker_stream.py", "\n            if len(raw) > _MAX_JSON_SIZE:", "\n            if len(raw) >= _MAX_JSON_SIZE:"),
    ("N3", T_SC + "test_ws_frame_exact_cap.py", SC + "websocket/control_stream.py", "if len(raw) > _MAX_MESSAGE_SIZE:", "if len(raw) > _MAX_MESSAGE_SIZE + 1:"),
    ("O1", T_CT + "test_docs_additions_check.py", CT + "docs_additions_check.py", '_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")', '_FENCE_RE = re.compile(r"^ {0,4}(`{3,}|~{3,})(.*)$")'),
    ("O2", T_CT + "test_docs_additions_check.py", CT + "docs_additions_check.py", 'if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):', 'if match and not ("`" in match.group(2)):'),
]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def clear_pycache(root):
    for dirpath, dirnames, _ in os.walk(root):
        for d in list(dirnames):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)


def test_names(source):
    names = set()
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test_"):
                    names.add(f"{node.name}.{sub.name}")
    return names


def main_names(wt, rel):
    proc = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=wt, capture_output=True, text=True)
    if proc.returncode != 0:
        return set()
    return test_names(proc.stdout)


def parse_junit(path):
    out = []
    for case in ET.parse(path).iter("testcase"):
        cls = case.get("classname", "").split(".")
        name = case.get("name", "").split("[", 1)[0]
        last = cls[-1] if cls else ""
        key = f"{last}.{name}" if last and not last.startswith("test_") else name
        for child in case:
            if child.tag in ("failure", "error"):
                msg = (child.get("message") or "").strip().splitlines()
                out.append({"test": key, "full": f"{case.get('classname')}::{case.get('name')}", "message": msg[0][:300] if msg else ""})
    return out


def main(argv):
    wt, venv_root, scratch = argv[1:4]
    only = set(argv[4:])
    junit_dir = os.path.join(wt, "tmp", "val-junit")
    os.makedirs(junit_dir, exist_ok=True)
    log_dir = os.path.join(scratch, "mutants")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(scratch, "mutants_spec.json"), "w") as fh:
        json.dump([dict(zip(("id", "test_file", "target", "old", "new"), row)) for row in SPEC], fh, indent=1)
    results = []
    for mid, test_file, target, old, new in SPEC:
        if only and mid not in only:
            continue
        is_ct = test_file.startswith("juniper-ci-tools/")
        py = os.path.join(venv_root, "ct-3.12" if is_ct else "sc-3.12", "bin", "python")
        pkg_root = os.path.join(wt, CT if is_ct else SC)
        tpath = os.path.join(wt, target)
        with open(tpath, "rb") as fh:
            original = fh.read()
        before = sha256_bytes(original)
        text = original.decode()
        count = text.count(old)
        row = {"id": mid, "test_file": test_file, "target": target, "old": old, "new": new, "anchor_count": count, "sha_before": before}
        if count != 1:
            row["result"] = "inapplicable"
            results.append(row)
            print(f"{mid}: anchor count {count} -- skipped")
            continue
        with open(os.path.join(wt, test_file)) as fh:
            new_names = test_names(fh.read()) - main_names(wt, test_file)
        junit = os.path.join(junit_dir, f"mut-{mid}.xml")
        if os.path.exists(junit):
            os.remove(junit)
        if is_ct:
            cwd, rel = os.path.join(wt, "juniper-ci-tools"), test_file[len("juniper-ci-tools/"):]
        else:
            cwd, rel = wt, test_file
        try:
            clear_pycache(pkg_root)
            with open(tpath, "w") as fh:
                fh.write(text.replace(old, new, 1))
            log_path = os.path.join(log_dir, f"{mid}.log")
            with open(log_path, "w") as log:
                proc = subprocess.run([py, "-m", "pytest", rel, "-p", "no:cacheprovider", "-q", f"--junitxml={junit}"], cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
            row["pytest_exit"] = proc.returncode
        finally:
            with open(tpath, "wb") as fh:
                fh.write(original)
            clear_pycache(pkg_root)
        with open(tpath, "rb") as fh:
            row["sha_after"] = sha256_bytes(fh.read())
        row["restored"] = row["sha_after"] == before
        fails = parse_junit(junit) if os.path.exists(junit) else []
        row["failed"] = fails
        row["new_tests_failed"] = sorted({f["test"] for f in fails if f["test"] in new_names})
        row["preexisting_tests_failed"] = sorted({f["test"] for f in fails if f["test"] not in new_names})
        row["result"] = "killed-by-new" if row["new_tests_failed"] else ("killed-by-preexisting-only" if fails else "survived")
        results.append(row)
        print(f"{mid}: exit={row['pytest_exit']} restored={row['restored']} result={row['result']} new={row['new_tests_failed']} pre={row['preexisting_tests_failed']}")
    out = os.path.join(scratch, "mutants_results.json" if not only else f"mutants_results_{'_'.join(sorted(only))}.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
