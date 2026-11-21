#!/usr/bin/env python3
"""
Re-derive on this host's bash every brace word the guard's tests pin, and show which known bypasses still pass.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: validator pins and the open-bypass list)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tests/test_claude_agent_guard_brace_cap.py (SEQUENCE_CASES, REFUSED_SEQUENCES, SEQUENCE_DENIES); validator
         findings ml-code-port-lens F2 (five pin rows), F3 and F4 (two bypasses already on main) and F5; owner
         ruling 18 (the escape gap); the validator's bypass probe, whose bash harness this keeps.

Usage:
    python3 -I util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_pins_vs_bash.py <out.json> <label>=<guard.py> [...]

bash never runs a pinned command: for a word it runs ``printf '<%s>\\n' WORD`` and for a command the same printf
on the command's arguments, with ``set -f`` (no pathname expansion), ``ulimit -v 409600; ulimit -t 5``, an empty
scratch directory as cwd, ``HOME`` a scratch home, ``PATH=/usr/bin:/bin`` and a 10 s timeout. A command
substitution that a candidate spells (``$(:{)``) does run; each one here is a no-op or a missing command.
Each guard runs as the hook does (``python3 -I <guard.py>``, payload on stdin) with ``JUNIPER_GUARD_HOME`` set to
the scratch home, so the real home is not consulted.

Part 1, the pins. Every SEQUENCE_CASES row must equal bash's words, in order. Every SEQUENCE_DENIES command must
make a guarded word in bash (a ``.ssh`` / ``.gnupg`` component, or ``sudo`` / ``gpg2`` as the command word) and be
denied by the LAST guard given. REFUSED_SEQUENCES rows are listed with bash's words, for reading.
Part 2, the candidates below: bash's words, whether one reaches a credential directory once ``x/..`` pairs are
collapsed, and each guard's verdict. ``open`` marks the bypasses that are known and not fixed here; the exit
status is 1 when a pin fails, when an ``open`` candidate is no longer allowed by the last guard (the texts
would then be stale), or when a candidate that must be denied is allowed.
"""
import importlib.util
import json
import posixpath
import subprocess  # nosec B404 -- bash runs printf on fixed words; the guard copies run as hooks
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TESTS = REPO_ROOT / "tests" / "test_claude_agent_guard_brace_cap.py"
CRED = (".ssh", ".gnupg")
# (command, what the last guard must say, note)
CANDIDATES = [
    ("cat ~/.ssh/config", "deny", "control"),
    ("cat ~/.{r..t..1}sh/config", "deny", "ruling 15: the stepped sequence"),
    ("{s..s..1}udo true", "deny", "ruling 15: a stepped sequence that spells sudo (bash's words below are the arguments only)"),
    ("gpg{2..2..1} --card-status", "deny", "ruling 15: a stepped sequence that spells gpg2"),
    ("cat ~/.ss{x..y,h}/config", "deny", "port lens F2, mutant V1: a comma wins over an earlier .."),
    ("cat ~/Development/../.ss{h,x}/config", "deny", "control: a list below the home head"),
    ("cat ~/.ss{h,b\\}c}/config", "open", "ruling 18, the escape gap: an escaped } ends the group here"),
    ("cat ~/Development/../.ss{h,$(:{)}/config", "open", "port lens F3: an unbalanced { inside $(...)"),
    ("cat ~/Development/../.ss{h,`:{`}/config", "open", "port lens F3: the backtick form"),
    ("cat ~/Development/../.gnu{pg,$(:{)}/pubring.kbx", "open", "port lens F3: .gnupg"),
    ("cat ~/.ss{h,$(:{)}/config", "deny", "port lens F3 at the home head: the computed head is denied"),
    ("cat ~/Development/../.ss$(:)h/config", "open", "port lens F4: an empty $(...) splices the name below the head"),
    ("cat ~/Development/../.ss`:`h/config", "open", "port lens F4: the backtick form"),
    ("cat ~/Development/../.ss${x}h/config", "open", "port lens F4: an empty parameter"),
    ("cat ~/.ss$(:)h/config", "deny", "port lens F4 at the home head: the computed head is denied"),
    ("cat @HOME@/.ss{h,$(:{)}/config", "any", "port lens F3 through the home's absolute path (@HOME@ is the scratch home)"),
    ("cat @HOME@/.ss$(:)h/config", "any", "port lens F4 through the home's absolute path"),
    ("cat home/.ss{h,$(:{)}/config", "any", "port lens F3 in a relative path (cwd is the scratch home's parent)"),
    ("cat home/.ss$(:)h/config", "any", "port lens F4 in a relative path"),
    ("echo '$'{a,b}", "any", "claims lens F2: a quoted $ hides a group that bash expands"),
    ("echo {}{},01,,-}", "any", "port lens F5: bash's {} rule at the start of a word"),
    ("echo .ss{Y..a..3}h", "any", "claims lens F6: bash makes .ssYh .ssh .ss_h"),
]


def bash_words(args_text: str, scratch: Path) -> dict:
    home = scratch / "home"
    home.mkdir(exist_ok=True)
    script = "ulimit -v 409600; ulimit -t 5; set -f; x=; printf '<%%s>\\n' %s" % args_text
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin", "LC_ALL": "C"}
    try:
        proc = subprocess.run(["/usr/bin/bash", "-c", script], cwd=str(scratch), env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=10, check=False)  # nosec B603
    except subprocess.TimeoutExpired:
        return {"rc": None, "words": [], "stderr": "TIMEOUT"}
    out = proc.stdout.decode("utf-8", "surrogateescape")
    words = [line[1:-1].replace(str(home), "~") for line in out.splitlines() if line.startswith("<") and line.endswith(">")]
    return {"rc": proc.returncode, "words": words, "stderr": proc.stderr.decode("utf-8", "replace")[-200:].replace(str(home), "~")}


def reaches_cred(word: str) -> bool:
    parts = []
    for comp in word.split("/"):
        if comp == ".." and parts and parts[-1] not in ("..", "~", ""):
            parts.pop()
            continue
        parts.append(comp)
    return any(p in CRED for p in parts) or any(c in CRED for c in posixpath.normpath(word).split("/"))


def guard_verdict(guard: str, command: str, scratch: Path) -> str:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(scratch)})
    env = {"JUNIPER_GUARD_HOME": str(scratch / "home"), "PATH": "/usr/bin:/bin"}
    try:
        proc = subprocess.run([sys.executable, "-I", "-B", guard], input=payload.encode("utf-8"), cwd=str(scratch), env=env, capture_output=True, timeout=30, check=False)  # nosec B603
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    if proc.returncode == 2:
        return "refuse"
    if proc.returncode == 0:
        return "deny" if proc.stdout.strip() else "allow"
    return "error %d" % proc.returncode


def load_pins():
    spec = importlib.util.spec_from_file_location("brace_cap_pins", TESTS)
    module = importlib.util.module_from_spec(spec)
    sys.modules["brace_cap_pins"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    out = sys.argv[1]
    guards = {label: str(Path(path).resolve()) for label, path in (arg.split("=", 1) for arg in sys.argv[2:])}  # absolute: the hook runs elsewhere
    last = list(guards)[-1]
    pins = load_pins()
    report = {"bash": subprocess.run(["/usr/bin/bash", "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0], "guards": guards, "sequence_cases": [], "refused_sequences": [], "sequence_denies": [], "candidates": []}  # nosec B603
    failures = []
    with tempfile.TemporaryDirectory(prefix="pins-vs-bash-") as tmp:
        scratch = Path(tmp)
        for word, expected in pins.SEQUENCE_CASES:
            bash = bash_words(word, scratch)
            ok = bash["words"] == expected
            report["sequence_cases"].append({"word": word, "pinned": expected, "bash": bash["words"], "equal": ok})
            if not ok:
                failures.append("SEQUENCE_CASES %s: pinned %s, bash %s" % (word, expected, bash["words"]))
        for word, reason in pins.REFUSED_SEQUENCES:
            bash = bash_words(word, scratch)
            report["refused_sequences"].append({"word": word, "reason": reason, "bash": bash["words"][:8], "bash_rc": bash["rc"], "bash_stderr": bash["stderr"]})
        for command, rule in pins.SEQUENCE_DENIES:
            head, _, args_text = command.partition(" ")
            head_words = bash_words(head, scratch)["words"]
            words = bash_words(args_text, scratch)["words"]
            guarded = any(reaches_cred(w) for w in words) or any(w in ("sudo", "gpg2") for w in head_words)
            verdict = guard_verdict(guards[last], command, scratch)
            report["sequence_denies"].append({"command": command, "rule": rule, "bash_command_word": head_words, "bash_arguments": words, "bash_makes_a_guarded_word": guarded, last: verdict})
            if not guarded or verdict != "deny":
                failures.append("SEQUENCE_DENIES %s: bash guarded word %s, %s says %s" % (command, guarded, last, verdict))
        print("pins: %d SEQUENCE_CASES, %d REFUSED_SEQUENCES, %d SEQUENCE_DENIES checked against %s" % (len(pins.SEQUENCE_CASES), len(pins.REFUSED_SEQUENCES), len(pins.SEQUENCE_DENIES), report["bash"]))
        for command, expect, note in CANDIDATES:
            spelled = command.replace("@HOME@", str(scratch / "home"))
            bash = bash_words(spelled.partition(" ")[2], scratch)
            cred = [w for w in bash["words"] if reaches_cred(w)]
            verdicts = {label: guard_verdict(path, spelled, scratch) for label, path in guards.items()}
            report["candidates"].append({"command": command, "note": note, "expect": expect, "bash_words": bash["words"], "bash_reaches_cred": cred, "verdicts": verdicts})
            print("%-5s %-46s bash: %-58s %s" % (expect, command, " ".join(bash["words"])[:58], " ".join("%s=%s" % kv for kv in verdicts.items())))
            if expect == "open" and (verdicts[last] != "allow" or not cred):
                failures.append("candidate %s is listed as an open bypass but %s says %s (bash reaches a credential path: %s)" % (command, last, verdicts[last], bool(cred)))
            if expect == "deny" and verdicts[last] != "deny":
                failures.append("candidate %s must be denied; %s says %s" % (command, last, verdicts[last]))
    report["failures"] = failures
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    for line in failures:
        print("FAIL " + line)
    print("failures: %d" % len(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
