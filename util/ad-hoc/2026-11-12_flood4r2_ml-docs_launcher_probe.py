#!/usr/bin/env python3
"""
Probe the three local Claude Code launchers with a stub ``claude``: the facts the carried launcher section states.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- investigation (claim evidence for the Cursor flood-4 round-2 docs carrier, draft juniper-ml#2479)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2);
         tests/test_claude_interactive.py (``ClaudeInteractiveEndToEndTests._launch``, whose fixture this copies)

Each case copies ``scripts/claude_interactive.bash``, ``scripts/wake_the_claude.bash``,
``scripts/default_interactive_session_claude_code.bash`` and ``util/juniper_repo_tmp.bash`` into a fresh fixture
checkout of its own (a ``git init`` directory under the session's temp root), links ``claudey`` to the first, and
puts a stub ``claude`` first on a PATH of system directories only. The stub prints a version for ``--version``
and otherwise records its argv, NUL-separated. No real Claude Code starts, and nothing outside the fixture is
written. A case records the exit status, stdout, the ``Error:`` lines of stderr, and the argv the stub received,
then evaluates its named expectations. The report is one JSON file; the exit status is 1 when any expectation
is false, so a sentence the probe contradicts cannot be carried by accident.

Usage: 2026-11-12_flood4r2_ml-docs_launcher_probe.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYSTEM_PATH = "/usr/bin:/bin"
DEFAULT_PROMPT = "Hello World, Claude!"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
SCRUBBED = ("CLAUDE_SKIP_PERMISSIONS", "CLAUDE_REMOTE_CONTROL", "CLAUDE_MODEL", "CLAUDE_EFFORT", "CLAUDE_ID", "CLAUDE_WORKTREE", "CLAUDE_PROMPT", "CLAUDE_PROMPT_FILE", "CLAUDE_PROMPT_PATH", "WTC_DEBUG", "BASH_ENV", "ENV", "SCRIPT_VERSION")
STUB = '#!/usr/bin/env bash\nif [[ "$1" == "--version" ]]; then\n  if [[ "${STUB_EMPTY_VERSION:-}" == "1" ]]; then exit 0; fi\n  echo "claude-test-version"; exit 0\nfi\nprintf \'%s\\0\' "$@" >> "$CLAUDE_ARGV_NUL_LOG"\n'
REFUSED = 'Error: refused "%s": its value is missing or invalid (WTC_DEBUG=0 logs why)'
EXCLUSIVE = "A prompt and a prompt file are exclusive: give --prompt (or CLAUDE_PROMPT), or --file / --path (or CLAUDE_PROMPT_FILE / CLAUDE_PROMPT_PATH), not both"


def build_fixture(root: Path) -> None:
    (root / "scripts").mkdir()
    for name in ("claude_interactive.bash", "wake_the_claude.bash", "default_interactive_session_claude_code.bash"):
        target = root / "scripts" / name
        target.write_text((REPO / "scripts" / name).read_text(encoding="utf-8"), encoding="utf-8")
        target.chmod(0o755)
    (root / "util").mkdir()
    (root / "util" / "juniper_repo_tmp.bash").write_text((REPO / "util" / "juniper_repo_tmp.bash").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "claudey").symlink_to("scripts/claude_interactive.bash")
    (root / "bin").mkdir()
    stub = root / "bin" / "claude"
    stub.write_text(STUB, encoding="utf-8")
    stub.chmod(0o755)
    (root / "prompts").mkdir()
    (root / "prompts" / "handoff.md").write_text("---\nname: handoff\n---\nfile prompt body\n\n\n", encoding="utf-8")
    (root / "prompts" / "other.md").write_text("other prompt\n", encoding="utf-8")
    (root / "prompts" / "blank.md").write_text("  \n\t\n", encoding="utf-8")
    (root / "emptydir").mkdir()


def run_case(case: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="flood4r2-launcher-") as temp_dir:
        root = Path(temp_dir).resolve()
        build_fixture(root)
        argv_log = root / "claude_argv.nul"
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_") and key not in SCRUBBED}
        env.update({name: "" for name in SENTRY_DSN_NAMES})  # set to empty, not unset: nothing here may report to Sentry
        env["PATH"] = SYSTEM_PATH if case.get("no_claude") else f"{root / 'bin'}:{SYSTEM_PATH}"
        env["CLAUDE_ARGV_NUL_LOG"] = str(argv_log)
        env["WTC_SESSIONS_DIR"] = str(root / "sessions")
        env["WTC_LOGS_DIR"] = str(root / "logs")
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        env["GIT_CEILING_DIRECTORIES"] = str(root.parent)
        subprocess.run(["git", "init", "-q", str(root)], env=env, check=True, capture_output=True)
        env.update(case.get("env", {}))
        entry = {"claudey": root / "claudey", "wake": root / "scripts" / "wake_the_claude.bash", "default": root / "scripts" / "default_interactive_session_claude_code.bash"}[case["entry"]]
        args = [arg.replace("{root}", str(root)) for arg in case["args"]]
        proc = subprocess.run(["bash", str(entry), *args], cwd=str(root), env=env, text=True, capture_output=True, check=False, timeout=120)
        argv = argv_log.read_bytes().decode("utf-8").split("\0")[:-1] if argv_log.exists() else None
        stub_path = str(root / "bin" / "claude")
        result = {
            "id": case["id"],
            "entry": case["entry"],
            "args": case["args"],
            "env": sorted(case.get("env", {})),
            "no_claude": bool(case.get("no_claude")),
            "rc": proc.returncode,
            "stdout": proc.stdout.replace(str(root), "{root}"),
            "stderr_errors": [line.replace(str(root), "{root}") for line in proc.stderr.splitlines() if line.startswith("Error:")],
            "stderr_lines": len(proc.stderr.splitlines()),
            "argv": argv,
            "stub": stub_path.replace(str(root), "{root}"),
        }
        result["checks"] = [{"label": label, "ok": bool(check(result))} for label, check in case["expect"]]
        result["stdout"] = result["stdout"][-1500:]
        return result


def launched(result: dict) -> bool:
    return result["argv"] is not None


def prompt_of(result: dict):
    argv = result["argv"] or []
    return argv[argv.index("--") + 1] if "--" in argv else None


def options_of(result: dict) -> list:
    argv = result["argv"] or []
    return argv[: argv.index("--")] if "--" in argv else argv


def says(text: str):
    return lambda r: text in r["stdout"]


def err(text: str):
    return lambda r: text in r["stderr_errors"]


def rc(code: int):
    return lambda r: r["rc"] == code


def quiet(r: dict) -> bool:
    return r["stderr_lines"] == 0


CASES = [
    # ---- entry points: what Claude Code is handed ----------------------------------------------------
    {"id": "E1 claudey, no arguments", "entry": "claudey", "args": [], "expect": [
        ("exit 0", rc(0)),
        ("claude gets a bare --worktree and --remote-control, --effort max, --model opus, --dangerously-skip-permissions, then -- and the default prompt", lambda r: r["argv"] == ["--worktree", "--remote-control", "--effort", "max", "--model", "opus", "--dangerously-skip-permissions", "--", DEFAULT_PROMPT]),
        ("wake is handed --model opus --effort max --worktree 0 -- --remote-control --dangerously-skip-permissions --prompt <default>", says("wake_the_claude.bash --model opus --effort max --worktree 0 -- --remote-control --dangerously-skip-permissions --prompt " + DEFAULT_PROMPT)),
        ("prints Launching ... and Closed ...", lambda r: "Launching Default Interactive session with Claude Code" in r["stdout"] and "Closed Default Interactive session with Claude Code" in r["stdout"]),
    ]},
    {"id": "E2 claudey --file <file>", "entry": "claudey", "args": ["--file", "prompts/handoff.md"], "expect": [
        ("exit 0", rc(0)),
        ("the file's text is the prompt, trailing newlines stripped, the leading --- kept", lambda r: prompt_of(r) == "---\nname: handoff\n---\nfile prompt body"),
        ("the default prompt is not sent", lambda r: DEFAULT_PROMPT not in (r["argv"] or [])),
        ("no --prompt flag reaches claude", lambda r: "--prompt" not in (r["argv"] or [])),
        ("the other defaults are unchanged", lambda r: options_of(r) == ["--worktree", "--remote-control", "--effort", "max", "--model", "opus", "--dangerously-skip-permissions"]),
    ]},
    {"id": "E3 claudey --path <dir> --file <name>", "entry": "claudey", "args": ["--path", "prompts", "--file", "other.md"], "expect": [("exit 0", rc(0)), ("the prompt is the file's text", lambda r: prompt_of(r) == "other prompt")]},
    {"id": "E3b claudey --path <file>", "entry": "claudey", "args": ["--path", "prompts/other.md"], "expect": [("exit 0", rc(0)), ("the prompt is the file's text", lambda r: prompt_of(r) == "other prompt")]},
    {"id": "E4 default session script", "entry": "default", "args": [], "expect": [
        ("exit 0", rc(0)),
        ("--session-id plus a UUID", lambda r: len(r["argv"] or []) > 1 and r["argv"][0] == "--session-id" and len(r["argv"][1]) == 36),
        ("then a bare --worktree, a bare --remote-control, --effort high, -- and the default prompt", lambda r: (r["argv"] or [])[2:] == ["--worktree", "--remote-control", "--effort", "high", "--", DEFAULT_PROMPT]),
        ("no --model and no --dangerously-skip-permissions", lambda r: "--model" not in (r["argv"] or []) and "--dangerously-skip-permissions" not in (r["argv"] or [])),
    ]},
    {"id": "E4b default session script, CLAUDE_SKIP_PERMISSIONS=1", "entry": "default", "args": [], "env": {"CLAUDE_SKIP_PERMISSIONS": "1"}, "expect": [("exit 0", rc(0)), ("--dangerously-skip-permissions is sent", lambda r: "--dangerously-skip-permissions" in options_of(r))]},
    {"id": "E4c default session script returns wake's status", "entry": "default", "args": ["--effort", "bogus"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("Closed line still printed", says("Closed Default Interactive session with Claude Code")), ("nothing launched", lambda r: not launched(r))]},
    {"id": "E5 wake, no arguments", "entry": "wake", "args": [], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("usage printed", says("usage: wake_the_claude.bash")), ("nothing launched", lambda r: not launched(r))]},
    {"id": "E6 wake -u", "entry": "wake", "args": ["-u"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("usage printed", says("usage: wake_the_claude.bash"))]},
    {"id": "E6b wake --usage", "entry": "wake", "args": ["--usage"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("usage printed", says("usage: wake_the_claude.bash"))]},
    {"id": "E7 wake -h", "entry": "wake", "args": ["-h"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("usage printed", says("usage: wake_the_claude.bash"))]},
    {"id": "E7b wake --help", "entry": "wake", "args": ["--help"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("usage printed", says("usage: wake_the_claude.bash"))]},
    {"id": "E8 claudey --no-worktree --no-remote-control", "entry": "claudey", "args": ["--no-worktree", "--no-remote-control", "--prompt", "two words"], "expect": [
        ("exit 0", rc(0)), ("neither flag is sent", lambda r: "--worktree" not in options_of(r) and "--remote-control" not in options_of(r)), ("the prompt is one argument", lambda r: prompt_of(r) == "two words")]},
    {"id": "E9 claudey, CLAUDE_WORKTREE=1 CLAUDE_REMOTE_CONTROL=1", "entry": "claudey", "args": [], "env": {"CLAUDE_WORKTREE": "1", "CLAUDE_REMOTE_CONTROL": "1"}, "expect": [("exit 0", rc(0)), ("neither flag is sent", lambda r: "--worktree" not in options_of(r) and "--remote-control" not in options_of(r))]},
    {"id": "E10 claudey -s with no value", "entry": "claudey", "args": ["-s"], "expect": [("exit 1", rc(1)), ("Missing value for -s", says("Missing value for -s")), ("nothing launched", lambda r: not launched(r))]},
    {"id": "E10b wake -s is --dangerously-skip-permissions", "entry": "wake", "args": ["-s", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("argv is --dangerously-skip-permissions -- hi", lambda r: r["argv"] == ["--dangerously-skip-permissions", "--", "hi"])]},
    {"id": "E11 claudey returns wake's status", "entry": "claudey", "args": ["--file", "missing.md"], "expect": [
        ("exit 1", rc(1)), ("Closed line printed before the failing status", says("Closed Default Interactive session with Claude Code")), ("nothing launched", lambda r: not launched(r)),
        ("the unresolved-file error is on stderr", err('Error: no prompt file found for --file "missing.md" and --path ""'))]},
    # ---- version flags ----------------------------------------------------------------------------------
    *[{"id": f"V1 wake {flag}", "entry": "wake", "args": [flag], "env": {"WTC_DEBUG": "1"}, "expect": [
        ("exit 0", rc(0)), ("prints <path-to-claude> <claude --version output>", lambda r: r["stdout"] == "\n{root}/bin/claude claude-test-version\n\n"), ("no session starts", lambda r: not launched(r)), ("nothing on stderr", quiet)]} for flag in ("-v", "-V", "--version", "--claude-version")],
    *[{"id": f"V2 claudey {flag}", "entry": "claudey", "args": [flag], "expect": [
        ("exit 0", rc(0)), ("same line as wake prints, alone on stdout", lambda r: r["stdout"] == "\n{root}/bin/claude claude-test-version\n\n"), ("wake's debug log is off", quiet), ("no session starts", lambda r: not launched(r))]} for flag in ("-v", "-V", "--version", "--claude-version")],
    {"id": "V2b claudey -v drops later arguments", "entry": "claudey", "args": ["-v", "--model", "no-such-model", "--bogus"], "expect": [("exit 0", rc(0)), ("version line only", lambda r: r["stdout"] == "\n{root}/bin/claude claude-test-version\n\n")]},
    {"id": "V2c claudey -v after another flag", "entry": "claudey", "args": ["--no-worktree", "-v"], "expect": [("exit 0", rc(0)), ("version line only", lambda r: r["stdout"] == "\n{root}/bin/claude claude-test-version\n\n"), ("no session starts", lambda r: not launched(r))]},
    {"id": "V2d claudey -v with WTC_DEBUG=0 keeps the debug log", "entry": "claudey", "args": ["-v"], "env": {"WTC_DEBUG": "0"}, "expect": [("exit 0", rc(0)), ("debug log on stderr", lambda r: r["stderr_lines"] > 0), ("version line still printed", says("{root}/bin/claude claude-test-version"))]},
    {"id": "V3 wake --script-version", "entry": "wake", "args": ["--script-version"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("prints wake_the_claude.bash 1.1.0", lambda r: r["stdout"] == "\nwake_the_claude.bash 1.1.0\n\n")]},
    {"id": "V3b wake --script-version ignores an exported SCRIPT_VERSION", "entry": "wake", "args": ["--script-version"], "env": {"WTC_DEBUG": "1", "SCRIPT_VERSION": "0.2.0"}, "expect": [("exit 0", rc(0)), ("still 1.1.0", lambda r: r["stdout"] == "\nwake_the_claude.bash 1.1.0\n\n")]},
    {"id": "V3c claudey --script-version", "entry": "claudey", "args": ["--script-version"], "no_claude": True, "expect": [("exit 0", rc(0)), ("prints 0.2.0 alone", lambda r: r["stdout"] == "0.2.0\n"), ("wake is not called (no claude needed, nothing on stderr)", quiet)]},
    {"id": "V4 wake -v, no claude on PATH", "entry": "wake", "args": ["-v"], "env": {"WTC_DEBUG": "1"}, "no_claude": True, "expect": [("exit 1", rc(1)), ("Error: claude command not found in PATH", err("Error: claude command not found in PATH")), ("the refused line is not added", lambda r: len(r["stderr_errors"]) == 1)]},
    {"id": "V4b claudey -v, no claude on PATH", "entry": "claudey", "args": ["-v"], "no_claude": True, "expect": [("exit 1", rc(1)), ("Error: claude command not found in PATH", err("Error: claude command not found in PATH")), ("that line is all of stderr", lambda r: r["stderr_lines"] == 1)]},
    {"id": "V5 wake -v, claude --version prints nothing", "entry": "wake", "args": ["-v"], "env": {"WTC_DEBUG": "1", "STUB_EMPTY_VERSION": "1"}, "expect": [("exit 1", rc(1)), ("Error: \"<path> --version\" printed no version", err('Error: "{root}/bin/claude --version" printed no version')), ("the refused line is not added", lambda r: len(r["stderr_errors"]) == 1)]},
    # ---- stderr with the debug log off ------------------------------------------------------------------
    {"id": "S1 wake --file missing.md", "entry": "wake", "args": ["--file", "missing.md"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("unresolved-file error", err('Error: no prompt file found for --file "missing.md" and --path ""')), ("then usage", says("usage: wake_the_claude.bash")), ("nothing launched", lambda r: not launched(r)), ("one stderr line", lambda r: r["stderr_lines"] == 1)]},
    {"id": "S2 wake --path no-such-dir", "entry": "wake", "args": ["--path", "no-such-dir"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused --path", err(REFUSED % "--path")), ("then usage", says("usage: wake_the_claude.bash")), ("nothing launched", lambda r: not launched(r))]},
    {"id": "S3 wake --file -x", "entry": "wake", "args": ["--file", "-x"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused --file", err(REFUSED % "--file")), ("then usage", says("usage: wake_the_claude.bash"))]},
    {"id": "S3b wake -f -x names the flag as typed", "entry": "wake", "args": ["-f", "-x"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused -f", err(REFUSED % "-f"))]},
    {"id": "S4 wake --path <dir>, no file name", "entry": "wake", "args": ["--path", "prompts"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("unresolved-file error", err('Error: no prompt file found for --file "" and --path "prompts"')), ("then usage", says("usage: wake_the_claude.bash"))]},
    {"id": "S5 wake --path <dir> --file <not there>", "entry": "wake", "args": ["--path", "prompts", "--file", "nope.md"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused --file", err(REFUSED % "--file"))]},
    {"id": "S5b wake --file <not there> --path <dir>", "entry": "wake", "args": ["--file", "nope.md", "--path", "prompts"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused --path", err(REFUSED % "--path"))]},
    {"id": "S6 wake launch, no claude on PATH", "entry": "wake", "args": ["-p", "hi"], "env": {"WTC_DEBUG": "1"}, "no_claude": True, "expect": [("exit 1", rc(1)), ("Error: claude command not found in PATH", err("Error: claude command not found in PATH"))]},
    {"id": "S7 wake unknown flag, debug log off", "entry": "wake", "args": ["--bogus"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("usage only", says("usage: wake_the_claude.bash")), ("nothing on stderr", quiet), ("nothing launched", lambda r: not launched(r))]},
    {"id": "S7b wake unknown flag, debug log on", "entry": "wake", "args": ["--bogus"], "expect": [("exit 1", rc(1)), ("stderr carries the debug log", lambda r: r["stderr_lines"] > 0), ("but no Error: line of its own", lambda r: r["stderr_errors"] == [])]},
    {"id": "S8 wake --file <whitespace only>", "entry": "wake", "args": ["--file", "prompts/blank.md"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("could not be read, or holds no prompt", err('Error: the prompt file "prompts/blank.md" could not be read, or holds no prompt')), ("no usage text", lambda r: "usage:" not in r["stdout"]), ("nothing launched", lambda r: not launched(r))]},
    {"id": "S9 wake --remote-control laptop", "entry": "wake", "args": ["--remote-control", "laptop"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused --remote-control", err(REFUSED % "--remote-control")), ("then usage", says("usage: wake_the_claude.bash")), ("nothing launched", lambda r: not launched(r))]},
    {"id": "S9b wake -c laptop names the flag as typed", "entry": "wake", "args": ["-c", "laptop"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused -c", err(REFUSED % "-c"))]},
    {"id": "S9c wake --remote-control 0", "entry": "wake", "args": ["--remote-control", "0", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("bare --remote-control", lambda r: r["argv"] == ["--remote-control", "--", "hi"])]},
    {"id": "S9d wake --remote-control 1", "entry": "wake", "args": ["--remote-control", "1", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("omitted", lambda r: r["argv"] == ["--", "hi"])]},
    {"id": "S9e wake --remote-control before a flag", "entry": "wake", "args": ["--remote-control", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("bare --remote-control", lambda r: r["argv"] == ["--remote-control", "--", "hi"])]},
    *[{"id": f"S9f wake {flag} is remote control", "entry": "wake", "args": [flag, "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("bare --remote-control", lambda r: r["argv"] == ["--remote-control", "--", "hi"])]} for flag in ("-c", "--remote", "--control")],
    # ---- prompt and prompt file ---------------------------------------------------------------------------
    {"id": "P1 claudey --file with --prompt", "entry": "claudey", "args": ["--file", "prompts/handoff.md", "--prompt", "hi"], "expect": [("exit 1", rc(1)), ("the exclusive message", says(EXCLUSIVE)), ("wake is not called", lambda r: "Launching" not in r["stdout"] and not launched(r))]},
    {"id": "P2 claudey --file, CLAUDE_PROMPT=1", "entry": "claudey", "args": ["--file", "prompts/other.md"], "env": {"CLAUDE_PROMPT": "1"}, "expect": [("exit 0", rc(0)), ("the file is the prompt", lambda r: prompt_of(r) == "other prompt")]},
    *[{"id": f"P3 claudey {flag} ''", "entry": "claudey", "args": [flag, ""], "expect": [("exit 1", rc(1)), (f"Missing value for {flag}", says(f"Missing value for {flag}")), ("wake is not called", lambda r: "Launching" not in r["stdout"] and not launched(r))]} for flag in ("--file", "--path", "-f", "-l", "--file-name", "--file-path")],
    {"id": "P4 claudey, exported empty CLAUDE_PROMPT_FILE", "entry": "claudey", "args": [], "env": {"CLAUDE_PROMPT_FILE": ""}, "expect": [("exit 1", rc(1)), ("Missing value for --file", says("Missing value for --file")), ("wake is not called", lambda r: "Launching" not in r["stdout"] and not launched(r))]},
    {"id": "P4b claudey, exported empty CLAUDE_PROMPT_PATH", "entry": "claudey", "args": [], "env": {"CLAUDE_PROMPT_PATH": ""}, "expect": [("exit 1", rc(1)), ("Missing value for --path", says("Missing value for --path")), ("wake is not called", lambda r: "Launching" not in r["stdout"] and not launched(r))]},
    {"id": "P4c claudey --prompt hi, exported empty CLAUDE_PROMPT_FILE", "entry": "claudey", "args": ["--prompt", "hi"], "env": {"CLAUDE_PROMPT_FILE": ""}, "expect": [("exit 1", rc(1)), ("Missing value for --file", says("Missing value for --file")), ("wake is not called", lambda r: not launched(r))]},
    {"id": "P5 claudey, CLAUDE_PROMPT_FILE names a file", "entry": "claudey", "args": [], "env": {"CLAUDE_PROMPT_FILE": "prompts/other.md"}, "expect": [("exit 0", rc(0)), ("the file is the prompt", lambda r: prompt_of(r) == "other prompt")]},
    {"id": "P5b claudey --file overrides CLAUDE_PROMPT_FILE", "entry": "claudey", "args": ["--file", "prompts/other.md"], "env": {"CLAUDE_PROMPT_FILE": "prompts/handoff.md"}, "expect": [("exit 0", rc(0)), ("the flag's file is the prompt", lambda r: prompt_of(r) == "other prompt")]},
    {"id": "P5c claudey, CLAUDE_PROMPT_PATH names a file", "entry": "claudey", "args": [], "env": {"CLAUDE_PROMPT_PATH": "prompts/other.md"}, "expect": [("exit 0", rc(0)), ("the file is the prompt", lambda r: prompt_of(r) == "other prompt")]},
    {"id": "P6 claudey '' --file", "entry": "claudey", "args": ["", "--file", "prompts/other.md"], "expect": [("exit 1", rc(1)), ("Unknown argument: (an empty word)", says("Unknown argument: (an empty word)")), ("wake is not called", lambda r: not launched(r))]},
    {"id": "P6b wake stops parsing at an empty word", "entry": "wake", "args": ["-p", "hi", "", "--bogus"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("the words after the empty one are dropped", lambda r: r["argv"] == ["--", "hi"])]},
    {"id": "P7 claudey -w '' --file", "entry": "claudey", "args": ["-w", "", "--file", "prompts/other.md"], "expect": [("exit 0", rc(0)), ("a bare --worktree", lambda r: options_of(r)[:1] == ["--worktree"] and options_of(r)[1] == "--remote-control"), ("the file is the prompt", lambda r: prompt_of(r) == "other prompt")]},
    {"id": "P8 claudey --prompt with no word", "entry": "claudey", "args": ["--prompt"], "expect": [("exit 1", rc(1)), ("Missing value for --prompt", says("Missing value for --prompt")), ("wake is not called", lambda r: not launched(r))]},
    {"id": "P9 wake -p <a word starting with ->", "entry": "wake", "args": ["-p", "--dangerously-skip-permissions"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("the word is the prompt, not a flag", lambda r: r["argv"] == ["--", "--dangerously-skip-permissions"])]},
    *[{"id": f"P9b wake {flag} is a prompt flag", "entry": "wake", "args": [flag, "hi there"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("prompt sent after --", lambda r: r["argv"] == ["--", "hi there"])]} for flag in ("-p", "--prompt", "--prompt-string")],
    {"id": "P9c wake -p 0", "entry": "wake", "args": ["-p", "0"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("default prompt", lambda r: r["argv"] == ["--", DEFAULT_PROMPT])]},
    {"id": "P9d wake -p ''", "entry": "wake", "args": ["-p", ""], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("default prompt", lambda r: r["argv"] == ["--", DEFAULT_PROMPT])]},
    {"id": "P9e wake -p 1", "entry": "wake", "args": ["-p", "1", "--remote-control"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("no prompt and no --", lambda r: r["argv"] == ["--remote-control"])]},
    {"id": "P9f wake -p at the end of the input", "entry": "wake", "args": ["--remote-control", "-p"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("default prompt", lambda r: r["argv"] == ["--remote-control", "--", DEFAULT_PROMPT])]},
    {"id": "P11 wake --file good --file missing", "entry": "wake", "args": ["--file", "prompts/other.md", "--file", "missing.md"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("unresolved-file error names the later file", err('Error: no prompt file found for --file "missing.md" and --path ""')), ("the earlier file is not sent", lambda r: not launched(r))]},
    {"id": "P11b wake --path good --path <dir with no file name>", "entry": "wake", "args": ["--path", "prompts/other.md", "--path", "emptydir"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("unresolved-file error", err('Error: no prompt file found for --file "" and --path "emptydir"')), ("the earlier file is not sent", lambda r: not launched(r))]},
    {"id": "P12 claudey -h", "entry": "claudey", "args": ["-h"], "expect": [
        ("exit 0", rc(0)), ("usage is prefixed Usage: claude_interactive.bash", lambda r: r["stdout"].startswith("Usage: claude_interactive.bash ")), ("lists -h", says("[--help|-h|-?]")),
        ("the prompt and the prompt file are one alternative joined by |", says("[--initial-prompt|--prompt|-p <YOUR_INITIAL_PROMPT_HERE> | [--file-name|--file|-f <PROMPT_FILE>] [--file-path|--path|-l <PROMPT_FILE, or with --file its DIRECTORY>]]"))]},
    {"id": "P13 claudey --remote-control laptop", "entry": "claudey", "args": ["--remote-control", "laptop"], "expect": [("exit 1", rc(1)), ("Unknown argument: laptop", says("Unknown argument: laptop")), ("wake is not called", lambda r: not launched(r))]},
    {"id": "P13b claudey --no-remote-control --prompt --remote-control", "entry": "claudey", "args": ["--no-remote-control", "--prompt", "--remote-control"], "expect": [("exit 0", rc(0)), ("remote control stays off", lambda r: "--remote-control" not in options_of(r)), ("the prompt text is --remote-control", lambda r: prompt_of(r) == "--remote-control")]},
    {"id": "P13c claudey -rc is remote control", "entry": "claudey", "args": ["--no-remote-control", "-rc"], "expect": [("exit 0", rc(0)), ("--remote-control is sent", lambda r: "--remote-control" in options_of(r))]},
    {"id": "P14 wake prefers --prompt to a prompt file", "entry": "wake", "args": ["--prompt", "typed", "--file", "prompts/other.md"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("the typed prompt is sent, the file dropped", lambda r: r["argv"] == ["--", "typed"])]},
    # ---- effort (Overtoad ruling, 2026-11-08) ----------------------------------------------------------------
    {"id": "F1 wake --effort 0", "entry": "wake", "args": ["--effort", "0", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("--effort max", lambda r: r["argv"] == ["--effort", "max", "--", "hi"])]},
    *[{"id": f"F2 wake {flag} {value}", "entry": "wake", "args": [flag, value, "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("no --effort flag", lambda r: r["argv"] == ["--", "hi"])]} for flag, value in (("--effort", "auto"), ("-e", "AUTO"), ("--effort-type", "Auto"), ("--effort-level", "auto"))],
    {"id": "F3 wake --effort 1", "entry": "wake", "args": ["--effort", "1", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("no --effort flag", lambda r: r["argv"] == ["--", "hi"])]},
    {"id": "F4 wake --effort bogus", "entry": "wake", "args": ["--effort", "bogus", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 1", rc(1)), ("refused --effort", err(REFUSED % "--effort")), ("nothing launched", lambda r: not launched(r))]},
    {"id": "F5 claudey -e auto", "entry": "claudey", "args": ["-e", "auto"], "expect": [("exit 0", rc(0)), ("no --effort flag reaches claude", lambda r: "--effort" not in options_of(r)), ("the other defaults are unchanged", lambda r: options_of(r) == ["--worktree", "--remote-control", "--model", "opus", "--dangerously-skip-permissions"])]},
    {"id": "F6 wake --effort high", "entry": "wake", "args": ["--effort", "high", "-p", "hi"], "env": {"WTC_DEBUG": "1"}, "expect": [("exit 0", rc(0)), ("--effort high", lambda r: r["argv"] == ["--effort", "high", "--", "hi"])]},
]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe the local Claude Code launchers with a stub claude.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    for directory in SYSTEM_PATH.split(":"):
        if (Path(directory) / "claude").exists():
            print(f"refused: a real claude sits in {directory}, which every case keeps on PATH")
            return 2
    if shutil.which("bash", path=SYSTEM_PATH) is None or shutil.which("git", path=SYSTEM_PATH) is None:
        print("refused: bash and git are needed in " + SYSTEM_PATH)
        return 2
    results = [run_case(case) for case in CASES]
    failed = [(r["id"], c["label"]) for r in results for c in r["checks"] if not c["ok"]]
    total = sum(len(r["checks"]) for r in results)
    report = {"repo": str(REPO), "cases": len(results), "checks": total, "failed": [list(pair) for pair in failed], "results": results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{len(results)} cases, {total} expectations, {len(failed)} false")
    for case_id, label in failed:
        print(f"FALSE  {case_id}: {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
