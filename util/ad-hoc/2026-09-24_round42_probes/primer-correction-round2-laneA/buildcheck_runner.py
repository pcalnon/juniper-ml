#!/usr/bin/env python3
"""Lane A r2: re-run the PR's build script `--check` on PR-head content in a scratch copy.

Layout (so the script's REPO = parents[2] resolves to the scratch tree):
  buildcheck/util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py   (PR head copy, byte-identical)
  buildcheck/notes/<PRIMER>                                               (primer at b6129bf8)
The script's only git call, `git show HEAD:<primer>`, is replaced by the primer at dcfc024f (the
PR's base, extracted with `git show dcfc024f:<primer>`) -- i.e. exactly the pre-commit state the
PR body describes (HEAD = base, working tree = corrected file). Then mutation controls:
  M1 one character changed inside Appendix E           -> expect DIFFERS, rc 1
  M2 one character changed on an untouched line (L100) -> expect DIFFERS, rc 1
  M3 HEAD already carries the correction (post-merge) -> expect REFUSED (SystemExit)
  M4 base with one inserted line near the top          -> expect REFUSED (primer moved)
"""
import contextlib
import importlib.util
import io
import shutil
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
PRIMER = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
TREE = S / "buildcheck"
shutil.rmtree(TREE, ignore_errors=True)
(TREE / "util" / "ad-hoc").mkdir(parents=True)
(TREE / "notes").mkdir(parents=True)
SCRIPT = TREE / "util" / "ad-hoc" / "2026-09-24_primer_correct_artifact_validator.py"
shutil.copyfile(S / "pr_build_script.py", SCRIPT)
BASE = (S / "primer_base.md").read_text(encoding="utf-8")
HEAD = (S / "primer_head.md").read_text(encoding="utf-8")


def load():
    spec = importlib.util.spec_from_file_location("buildscript", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.REPO == TREE, mod.REPO
    return mod


def run(label, wt_text, head_text):
    (TREE / PRIMER).write_text(wt_text, encoding="utf-8")
    mod = load()
    mod.head_primer = lambda: head_text
    sys.argv = [str(SCRIPT), "--check"]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    except SystemExit as exc:
        rc = f"SystemExit({str(exc.code)[:110]!r})"
    after = (TREE / PRIMER).read_text(encoding="utf-8")
    print(f"[{label}] rc={rc} | stdout: {' / '.join(buf.getvalue().strip().splitlines())} | wrote_nothing={after == wt_text}")


run("REAL: wt=head, HEAD=base", HEAD, BASE)
ap = HEAD.index("### E.1 Artifact validator")
run("M1: 1 char in Appendix E", HEAD[:ap + 10] + ("X" if HEAD[ap + 10] != "X" else "Y") + HEAD[ap + 11:], BASE)
lines = HEAD.split("\n")
lines[99] = lines[99] + "."
run("M2: 1 char on untouched L100", "\n".join(lines), BASE)
run("M3: HEAD already corrected", HEAD, HEAD)
bl = BASE.split("\n")
run("M4: base with inserted line", HEAD, "\n".join(bl[:10] + ["inserted"] + bl[10:]))
shutil.rmtree(TREE, ignore_errors=True)
