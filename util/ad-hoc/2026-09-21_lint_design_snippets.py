#!/usr/bin/env python3
"""
Extract the tagged fenced code blocks of a design document and lint each with the real tool.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
         (the consensus procedure requires code snippets to be validated, not merely read)

A fenced block is linted when its FIRST line is a marker of the form
    # file: <relative/name.ext>        (bash, ini, conf, env, python)
    ; file: <relative/name.ext>        (also accepted for ini)
The block is written to <workdir>/<relative/name.ext> and checked by extension:
    .bash .sh      bash -n, then shellcheck (if a binary can be found)
    .service .timer .path .mount .automount .conf(under *.d/)   systemd-analyze verify
                   (system units) -- unresolvable dependencies are reported, not hidden
    .py            python3 -m py_compile
    .env .conf(other) .rules .txt   syntax only: KEY=VALUE lines / non-empty
Exit 0 when every linted block passed, 1 otherwise. Nothing outside <workdir> is written.

Usage:
    2026-09-21_lint_design_snippets.py --doc notes/<design>.md --workdir <scratch>/snippets
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

FENCE_RE = re.compile(r"^```([A-Za-z0-9_+-]*)\s*$")
MARKER_RE = re.compile(r"^\s*[#;]\s*file:\s*(\S+)\s*$")


def find_shellcheck() -> str | None:
    for cand in (shutil.which("shellcheck"), "/opt/miniforge3/bin/shellcheck"):
        if cand and os.path.exists(cand):
            return cand
    home = os.path.expanduser("~/.cache/pre-commit")
    if os.path.isdir(home):
        for root, _dirs, files in os.walk(home):
            if "shellcheck" in files:
                p = os.path.join(root, "shellcheck")
                if os.access(p, os.X_OK):
                    return p
    return None


def extract(doc: str):
    blocks = []
    with open(doc, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        lang = m.group(1)
        start = i + 1
        j = start
        while j < len(lines) and not lines[j].startswith("```"):
            j += 1
        body = lines[start:j]
        if body:
            mk = MARKER_RE.match(body[0])
            if mk:
                blocks.append((mk.group(1), lang, start + 1, "\n".join(body[1:]) + "\n"))
        i = j + 1
    return blocks


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def lint(path: str, workdir: str, shellcheck: str | None):
    ext = os.path.splitext(path)[1]
    name = os.path.basename(path)
    rel = os.path.relpath(path, workdir)
    # A dot-file (".env") and a file under etc/default/ have NO extension for splitext,
    # so key the environment-file grammar on the name and location as well. Without this
    # both blocks were reported "no linter" -- a vacuous pass (caught by validation 2026-09-21).
    is_env_file = name == ".env" or ext in (".env", ".default") or rel.startswith("etc/default/")
    results = []
    if ext in (".bash", ".sh"):
        results.append(("bash -n",) + run(["bash", "-n", path]))
        if shellcheck:
            results.append(("shellcheck",) + run([shellcheck, "-x", "-S", "style", path]))
        else:
            results.append(("shellcheck", 2, "shellcheck binary not found"))
    elif ext in (".service", ".timer", ".path", ".mount", ".automount", ".socket") or \
            (ext == ".conf" and ".d/" in path.replace(workdir, "")):
        # systemd-analyze verify checks that every Exec*= target exists on THIS host. The
        # design's scripts are not installed here, so verify a copy whose Exec*= paths are
        # rewritten to the extracted copies of the same scripts (by installed path, then by
        # basename anywhere in the extracted tree). Anything not found stays as written and
        # fails honestly. User units (under .config/systemd/user/) are verified with --user.
        verify_dir = os.path.join(workdir, "_verify")
        os.makedirs(verify_dir, exist_ok=True)
        vpath = os.path.join(verify_dir, name)
        rewrites = []
        with open(path, encoding="utf-8") as fh, open(vpath, "w", encoding="utf-8") as out:
            for line in fh:
                m = re.match(r"^(Exec\w+=)([-+@:!]*)(\S+)(.*)$", line.rstrip("\n"))
                if m:
                    target = m.group(3)
                    cand = target.replace("%h", "home/pcalnon").lstrip("/")
                    found = os.path.join(workdir, cand) if os.path.isfile(os.path.join(workdir, cand)) else None
                    if not found:
                        base = os.path.basename(target)
                        for root, _d, files in os.walk(workdir):
                            if "_verify" in root:
                                continue
                            if base in files:
                                found = os.path.join(root, base)
                                break
                    if found:
                        rewrites.append(f"{target} -> {found}")
                        line = f"{m.group(1)}{m.group(2)}{found}{m.group(4)}\n"
                out.write(line)
        cmd = ["systemd-analyze", "verify", "--no-pager"]
        if "/systemd/user/" in path:
            cmd.append("--user")
        rc, text = run(cmd + [vpath])
        note = ("\n".join("rewrote for verify: " + r for r in rewrites) + ("\n" if rewrites else "")) + text
        results.append(("systemd-analyze verify", rc, note.strip()))
    elif ext == ".py":
        results.append(("py_compile",) + run([sys.executable, "-m", "py_compile", path]))
    elif is_env_file or ext in (".conf", ".rules", ".txt"):
        bad = []
        n = 0
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                s = line.rstrip("\n")
                if not s.strip() or s.lstrip().startswith("#"):
                    continue
                if is_env_file and not (
                        re.match(r"^(export\s+)?[A-Za-z_][A-Za-z0-9_]*=", s)
                        or re.match(r"^--[A-Za-z0-9][A-Za-z0-9-]*(=.*)?$", s)):
                    bad.append(f"line {n}: not KEY=VALUE or --option[=value]")
        label = "KEY=VALUE / --option grammar" if is_env_file else "non-empty"
        results.append((label, 1 if bad else 0, "\n".join(bad) or f"ok ({n} lines checked)"))
    else:
        results.append(("no linter", 0, f"no linter for {name}; extracted only"))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc", required=True)
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()
    os.makedirs(args.workdir, exist_ok=True)
    shellcheck = find_shellcheck()
    print(f"shellcheck: {shellcheck or 'NOT FOUND'}")
    blocks = extract(args.doc)
    print(f"tagged blocks found: {len(blocks)}")
    failures = 0
    # Phase 1: extract EVERY block before linting any. A unit's ExecStart= may name a
    # script that appears later in the document; linting as-we-go made the first run
    # fail and the second pass (on a populated workdir) succeed -- an order-dependent
    # verdict (caught by validation 2026-09-21).
    written = []
    for rel, lang, line, body in blocks:
        out = os.path.join(args.workdir, rel)
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
        if out.endswith((".bash", ".sh", ".py")):
            os.chmod(out, 0o700)  # owner-only: systemd-analyze verify wants Exec targets executable; the scratch tree is private
        written.append((rel, lang, line, body, out))
    # Phase 2: lint.
    for rel, lang, line, body, out in written:
        print("=" * 90)
        print(f"{rel}  (lang={lang or '-'}, doc line {line}, {len(body.splitlines())} lines)")
        for tool, rc, text in lint(out, args.workdir, shellcheck):
            status = "PASS" if rc == 0 else ("SKIP" if rc == 2 and "not found" in text else "FAIL")
            if status == "FAIL":
                failures += 1
            print(f"  [{status}] {tool}")
            if text and (status != "PASS" or tool == "systemd-analyze verify"):
                for t in text.splitlines()[:40]:
                    print(f"        {t}")
    print("=" * 90)
    print(f"blocks: {len(blocks)}  failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
