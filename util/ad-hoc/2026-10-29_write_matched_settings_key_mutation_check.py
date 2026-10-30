#!/usr/bin/env python3
"""
Mutation check for util/ad-hoc/2026-10-29_write_matched_settings_key.py: each mutant must be killed by
tests/test_write_matched_settings_key.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — investigation (Phase D round-1 fold-in: the mutants lane B found surviving)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tests/test_write_matched_settings_key.py; Phase D's design, round 1 (lane B, B-3 and its mutation table),
         and rounds 2 to 4 (lanes R2-A, R3 and R4), which added mutants

Each mutant is applied to a COPY of the tool inside a private copy of the files the suite reads, never to the
checkout, and the copied suite runs from the copy's root with bytecode writing off (a stale .pyc would run the
unmutated tool). The exit code is read directly, never through a pipe. Exit 0 when every mutant is killed and the
unmutated copy passes; 1 otherwise.

Usage: python3 util/ad-hoc/2026-10-29_write_matched_settings_key_mutation_check.py <scratch-directory>
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = "util/ad-hoc/2026-10-29_write_matched_settings_key.py"
COPY = (
    TOOL,
    "util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py",
    "util/ad-hoc/2026-10-03_rekey_gate.py",
    "scripts/duplicati-wrapper.bash",
    "util/systemd/duplicati-env.contract",
    "tests/redacted_env.py",
    "tests/test_write_matched_settings_key.py",
)
# (name, old text -- must occur exactly once in the tool, new text)
MUTANTS = (
    ("drop O_EXCL", "os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW", "os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW"),
    ("drop the parent-owner check", "if st.st_uid != os.geteuid():", "if False:"),
    ("drop the gate read-back comparison", "if key is None or sha(key) != target:", "if key is None:"),
    ("drop the bash read-back comparison", "    if got != target:\n", "    if False:\n"),
    ("keep a partial file on a write failure", "        os.unlink(name, dir_fd=dfd)\n", "        pass\n"),
    ("skip the --out checks on a dry run", "dfd = open_out_dir(args.out)", "dfd = None if args.dry_run else open_out_dir(args.out)"),
    ("decode the .env leniently", 'read_regular_file(env_path).decode("utf-8")', 'read_regular_file(env_path).decode("utf-8", errors="replace")'),
    ("split the .env with splitlines", 'for line in text.split("\\n"):', "for line in text.splitlines():"),
    ("write bytecode", "    sys.dont_write_bytecode = True", "    pass"),
    ("ignore blobs under another key in the gate's columns", "        if other:\n", "        if False:\n"),
    ("quote the decode error", "({type(exc).__name__}; text not shown): a server", "({exc}): a server"),
    ("drop the NUL refusal", 'if "\\0" in v:', "if False:"),
    ("drop the CR refusal", 'if "\\r" in v:', "if False:"),
    ("drop the newline refusal", 'if "\\n" in v:', "if False:"),
    ("drop the empty-value refusal", "    if not value:\n", "    if False:\n"),
    ("take the first active line", "            value = m.group(2)\n", "            value = value if value is not None else m.group(2)\n"),
    ("skip the CR strip", 's = line.rstrip("\\r")', "s = line"),
    ("write a trailing newline", 'write_exclusive(dfd, args.out.name, value.encode("utf-8"))', 'write_exclusive(dfd, args.out.name, (value + "\\n").encode("utf-8"))'),
    ("always write the noquote form", "value = forms[matched[0]]", 'value = forms["noquote"]'),
    ("drop the single-key-hash refusal", "    if len(keyhashes) != 1:\n", "    if False:\n"),
    ("keep the file after a failed read-back", "                remove_created(dfd, args.out)\n                raise\n", "                raise\n"),
    # Round 2 (lane R2-A): the deferral, the dry run's refusals, and the five-column scan.
    ("do not defer the signals", "old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, DEFERRED)", "old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, ())"),
    ("refuse another key only outside a dry run", "        if other:\n", "        if other and not args.dry_run:\n"),
    ("refuse an undeliverable form only outside a dry run", "        if why:\n", "        if why and not args.dry_run:\n"),
    ("scan only three of the five columns", "for sql, name in gate.COLUMNS:", "for sql, name in gate.COLUMNS[:3]:"),
    ("treat every OperationalError as absent", 'if isinstance(exc, sqlite3.OperationalError) and str(exc).startswith("no such table"):', "if isinstance(exc, sqlite3.OperationalError):"),
    ("leave double-quoted string literals on", "    con.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML, False)\n", "    pass\n"),
    # Round 3 (lane R3): every one of the four deferred signals, and the core limit.
    ("defer SIGTERM only", "DEFERRED = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)", "DEFERRED = (signal.SIGTERM,)"),
    ("defer all but SIGHUP", "DEFERRED = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)", "DEFERRED = (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT)"),
    ("leave core dumps on", "    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))\n", "    pass\n"),
    # Round 4 (lane R4, R4-3): the block before the create, the core limit before the key is read, the flush before
    # the unblock. The first two survived round 3's suite.
    ("block only after the create",
     "        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, DEFERRED)\n        try:\n            write_exclusive(dfd, args.out.name, value.encode(\"utf-8\"))\n",
     "        write_exclusive(dfd, args.out.name, value.encode(\"utf-8\"))\n        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, DEFERRED)\n        try:\n"),
    ("set the core limit after the key is read",
     "    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))\n    dfd = None\n    try:\n        dfd = open_out_dir(args.out)\n        key = active_key(args.env)\n",
     "    dfd = None\n    try:\n        dfd = open_out_dir(args.out)\n        key = active_key(args.env)\n        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))\n"),
    ("do not flush before the unblock",
     "            sys.stdout.flush()\n            sys.stderr.flush()\n            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)\n",
     "            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)\n"),
)


def build(root: Path) -> None:
    for rel in COPY:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dst)


def run_suite(root: Path) -> int:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPYCACHEPREFIX", None)
    r = subprocess.run([sys.executable, "-m", "unittest", "tests/test_write_matched_settings_key.py"], cwd=root, env=env, capture_output=True, text=True, check=False)
    return r.returncode


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    scratch = Path(argv[1]).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    base = scratch / "unmutated"
    shutil.rmtree(base, ignore_errors=True)
    build(base)
    rc = run_suite(base)
    print(f"unmutated: suite exit {rc} ({'passes' if rc == 0 else 'FAILS -- no mutant result below means anything'})")
    failed = rc != 0
    for n, (name, old, new) in enumerate(MUTANTS):
        root = scratch / f"mutant-{n:02d}"
        shutil.rmtree(root, ignore_errors=True)
        build(root)
        tool = root / TOOL
        text = tool.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            print(f"mutant {n:02d} {name}: NOT APPLIED (the old text occurs {count} times)")
            failed = True
            continue
        tool.write_text(text.replace(old, new), encoding="utf-8")
        rc = run_suite(root)
        verdict = "killed" if rc != 0 else "SURVIVED"
        failed |= rc == 0
        print(f"mutant {n:02d} {name}: {verdict} (suite exit {rc})")
        shutil.rmtree(root, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
