#!/usr/bin/env python3
"""
Verify the 2026-10-26 flood-3 backlog fixes: a lockfile base64 behavioural probe and a comment-only YAML diff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §4 (the base64 row, the
         claude.yml header row, the recurrence memory-budget row and the main-verify catch-up-base row)

Two subcommands:

``lockfile-b64 --workflow PATH --expect fixed|defect``
    Extracts the REAL shell of the ``Commit updated lockfile ...`` step from a ``lockfile-update.yml`` and runs
    it under ``bash --noprofile --norc -eo pipefail`` (what Actions runs for ``shell: bash``) against stub
    ``git`` / ``gh`` (and, per case, a stub ``base64``), with the real ``jq``. Every system-temp-directory path in the
    step is relocated into this probe's own work directory before anything runs, so nothing is written under
    the system temp directory. Cases:

    * ``fail``  -- ``base64`` exits 1 with no output (the failure the §4 row describes);
    * ``empty`` -- ``base64`` exits 0 with no output;
    * ``real``  -- the real ``base64``.

    ``--expect fixed``: ``fail`` and ``empty`` must exit non-zero WITHOUT calling ``gh`` (no commit), and
    ``real`` must exit 0 with the payload's ``contents`` equal to the lockfile's base64.
    ``--expect defect``: ``fail`` must exit 0 AND send ``gh`` a payload whose ``contents`` is empty -- proof that
    the probe can see the defect at all (non-vacuity), run against the pre-fix workflow.

``comment-only --old PATH --new PATH``
    Parses both workflows and compares them after dropping every line that is a shell comment (first
    non-blank character ``#``) inside any string value. YAML comments are dropped by the parser itself. Exit 0
    iff equal, i.e. the change touched comments only; it also says whether the parsed YAML is byte-identical.

Exit: 0 = every expectation held, 1 = an expectation failed, 2 = usage / extraction error.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess  # nosec B404 - runs the workflow's own extracted shell against stubs (fixed argv)
import sys
import tempfile
from pathlib import Path

import yaml

STEP_PREFIX = "Commit updated lockfile"

GIT_STUB = """#!/usr/bin/env bash
case "$1" in
  diff) exit 1 ;;
  rev-parse) echo 0123456789abcdef0123456789abcdef01234567 ;;
  *) echo "unexpected git $*" >&2; exit 97 ;;
esac
"""

GH_STUB = """#!/usr/bin/env bash
if [ "$1" = "api" ] && [ "$2" = "graphql" ] && [ "$3" = "--input" ]; then
  cp "$4" "$CAPTURE"
  echo '{"data":{"createCommitOnBranch":{"commit":{"oid":"abc","url":"https://example.invalid/commit/abc"}}}}'
  exit 0
fi
echo "unexpected gh $*" >&2
exit 98
"""

BASE64_STUBS = {
    "fail": '#!/usr/bin/env bash\necho "base64: simulated failure" >&2\nexit 1\n',
    "empty": "#!/usr/bin/env bash\nexit 0\n",
}


def _extract_step(workflow: Path) -> str:
    doc = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    for job in (doc.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if str(step.get("name", "")).startswith(STEP_PREFIX) and "run" in step:
                return str(step["run"])
    raise SystemExit(f"error: no step named {STEP_PREFIX!r}... with a run: block in {workflow}")


def _write_exe(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _run_case(script: str, case: str, scratch: Path) -> dict:
    work = scratch / case
    bindir = work / "bin"
    bindir.mkdir(parents=True)
    relocated = script.replace("/tmp/", f"{work}/")  # tmp-path-literal: allow
    # The work dir itself may sit under a repo's tmp/ (".../juniper-ml/tmp/..."), so judge what is left
    # once its own path is removed: any other "/tmp" is a literal the relocation missed.  # tmp-path-literal: allow
    if "/tmp" in relocated.replace(str(work), ""):  # tmp-path-literal: allow
        raise SystemExit("error: a /tmp reference survived relocation; refusing to run the step")  # tmp-path-literal: allow
    lock = work / "requirements.lock"
    lock_bytes = b"# probe lockfile\nexample-package==1.0.0\n"
    lock.write_bytes(lock_bytes)
    step_file = work / "step.bash"
    step_file.write_text(relocated, encoding="utf-8")
    _write_exe(bindir / "git", GIT_STUB)
    _write_exe(bindir / "gh", GH_STUB)
    if case in BASE64_STUBS:
        _write_exe(bindir / "base64", BASE64_STUBS[case])
    capture = work / "capture.json"
    env = {
        "PATH": f"{bindir}:{os.environ.get('PATH', '/usr/bin:/bin')}",
        "HOME": str(work),
        "LANG": "C",
        "TMPDIR": str(work),
        "BRANCH": "probe-branch",
        "EVENT_NAME": "pull_request",
        "GITHUB_REPOSITORY": "pcalnon/probe",
        "GH_TOKEN": "probe-placeholder",
        "CAPTURE": str(capture),
    }
    bash = shutil.which("bash") or "/usr/bin/bash"
    proc = subprocess.run([bash, "--noprofile", "--norc", "-eo", "pipefail", str(step_file)], cwd=work, env=env, capture_output=True, text=True, timeout=60, check=False)  # nosec B603 - fixed argv
    contents = None
    if capture.exists():
        payload = json.loads(capture.read_text(encoding="utf-8"))
        contents = payload["variables"]["input"]["fileChanges"]["additions"][0]["contents"]
    return {
        "case": case,
        "rc": proc.returncode,
        "gh_called": capture.exists(),
        "contents": contents,
        "expected_contents": base64.b64encode(lock_bytes).decode("ascii"),
        "stdout_tail": proc.stdout.strip().splitlines()[-2:],
        "stderr_tail": proc.stderr.strip().splitlines()[-2:],
    }


def cmd_lockfile_b64(args: argparse.Namespace) -> int:
    script = _extract_step(Path(args.workflow))
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="flood3-b64-probe-") as tmp:
        scratch = Path(tmp)
        results = {case: _run_case(script, case, scratch) for case in ("fail", "empty", "real")}
    for res in results.values():
        shown = dict(res)
        shown["contents"] = None if res["contents"] is None else f"<{len(res['contents'])} chars>"
        shown.pop("expected_contents")
        print(json.dumps(shown))
    if args.expect == "fixed":
        for case in ("fail", "empty"):
            res = results[case]
            if res["rc"] == 0 or res["gh_called"]:
                failures.append(f"{case}: expected a non-zero exit and no gh call, got rc={res['rc']} gh_called={res['gh_called']}")
        if not any("::error::base64 produced an empty payload" in line for line in results["empty"]["stdout_tail"]):
            failures.append("empty: the ::error:: annotation was not printed")
        real = results["real"]
        if real["rc"] != 0 or real["contents"] != real["expected_contents"]:
            failures.append(f"real: expected rc=0 and the lockfile's base64, got rc={real['rc']} contents_match={real['contents'] == real['expected_contents']}")
    else:
        res = results["fail"]
        if not (res["rc"] == 0 and res["gh_called"] and res["contents"] == ""):
            failures.append(f"fail: expected the DEFECT (rc=0, gh called, empty contents), got rc={res['rc']} gh_called={res['gh_called']} contents={res['contents']!r}")
    for line in failures:
        print(f"EXPECTATION FAILED: {line}")
    print(f"lockfile-b64 --expect {args.expect}: {'PASS' if not failures else 'FAIL'} ({args.workflow})")
    return 0 if not failures else 1


def _strip_comment_lines(node: object) -> object:
    if isinstance(node, dict):
        return {k: _strip_comment_lines(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_strip_comment_lines(v) for v in node]
    if isinstance(node, str):
        return "\n".join(line for line in node.splitlines() if not line.lstrip().startswith("#"))
    return node


def cmd_comment_only(args: argparse.Namespace) -> int:
    old = yaml.safe_load(Path(args.old).read_text(encoding="utf-8"))
    new = yaml.safe_load(Path(args.new).read_text(encoding="utf-8"))
    identical = old == new
    equal_modulo_comments = _strip_comment_lines(old) == _strip_comment_lines(new)
    verdict = "PASS" if equal_modulo_comments else "FAIL"
    print(f"comment-only: {verdict} parsed_identical={identical} equal_modulo_comment_lines={equal_modulo_comments} ({args.new})")
    return 0 if equal_modulo_comments else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("lockfile-b64")
    p1.add_argument("--workflow", required=True)
    p1.add_argument("--expect", choices=("fixed", "defect"), required=True)
    p1.set_defaults(func=cmd_lockfile_b64)
    p2 = sub.add_parser("comment-only")
    p2.add_argument("--old", required=True)
    p2.add_argument("--new", required=True)
    p2.set_defaults(func=cmd_comment_only)
    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
