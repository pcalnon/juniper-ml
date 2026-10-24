#!/usr/bin/env python3
"""
Run CI's two sequence-safety screens over a PR's path list before the PR exists: each path's text at a base ref
against its text in the working tree, with no commit made.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-24
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: .github/workflows/ci.yml (the ``sequence-safety`` job this reproduces);
         juniper-ci-tools/juniper_ci_tools/symbol_loss_check.py and docs_additions_check.py (the screens it calls);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (the PR it was written for)

Why this exists
---------------
The required ``Sequence Safety`` job screens a PR's ``base..HEAD`` range: an AST symbol-loss screen over
``tests/*.py``, ``util/**/*.py`` and ``util/**/*.bash``, and a deletion-magnitude screen over the docs cluster
(``AGENTS.md``, ``docs/**/*.md``, ``notes/**/*.md``). Both CLIs need two commits. A plan PR here is pushed as
signed GraphQL commits from untracked files, so there is no local head commit to give them, and a waiver trailer
must be in the commit message before the first push. This runs the screens' own library functions on the same
inputs: the base text from ``git show <base>:<path>``, the head text from the working tree, and the intended
commit message for the waiver trailers.

What it does
------------
Symbol screen: for each listed ``.py``/``.bash`` path in the CI scope, the base and head inventories
(``symbols_for``), ``classify_file``, ``apply_relocation`` across the listed files, and the message's
``Allow-Symbol-Loss`` waivers. Docs screen: for each listed path in the docs scope, a ``--unified=0`` diff of the
two texts by ``git diff --no-index`` with the myers algorithm (CI's default), ``parse_hunks``, the fence maps,
``classify_file`` at ``--min-run`` (the module's default unless given), and the message's ``Allow-Docs-Rewrite``
waivers. It prints each finding's path, symbol or reason, verdict and severity, never a file's text.

Limits: the merge result CI screens is ``main`` plus the PR, and this is the base ref plus the listed paths, so a
path changed on ``main`` after ``--base`` and not listed is not screened; give ``--base`` as the PR's base.

Usage
-----
    python3 -B util/ad-hoc/2026-10-24_sequence_safety_on_paths.py --list <paths.txt> --ci-tools <dir holding
        juniper_ci_tools/> [--base origin/main] [--message <commit message file>] [--min-run N]
Exit 0 when neither screen has an unwaived FAIL; 1 when one has; 2 on a bad path list or an unresolvable base.
"""
import argparse
import subprocess  # nosec B404 -- fixed argv, never a shell
import sys
import tempfile
from pathlib import Path

SYMBOL_SCOPE = ["tests/*.py", "util/**/*.py", "util/**/*.bash"]  # ci.yml's sequence-safety job, verbatim


def git_text(base: str, path: str):
    """The path's text at ``base``, or None when it does not exist there."""
    cp = subprocess.run(["git", "show", f"{base}:{path}"], capture_output=True, text=True, check=False)  # nosec B603 B607
    return cp.stdout if cp.returncode == 0 else None


def no_index_diff(base_text: str, head_text: str) -> str:
    """A unified=0 diff of two texts, by git's myers algorithm, as CI's ``git diff --unified=0`` makes it."""
    with tempfile.TemporaryDirectory(prefix="seqsafe-") as tmp:
        a, b = Path(tmp) / "a", Path(tmp) / "b"
        a.write_text(base_text, encoding="utf-8")
        b.write_text(head_text, encoding="utf-8")
        argv = ["git", "diff", "--no-index", "--diff-algorithm=myers", "--unified=0", "--no-color", str(a), str(b)]
        return subprocess.run(argv, capture_output=True, text=True, check=False).stdout  # nosec B603 B607


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--list", required=True, help="the PR's paths, one per line")
    ap.add_argument("--ci-tools", required=True, help="a directory holding the juniper_ci_tools package")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--message", help="the intended commit message, for its waiver trailers")
    ap.add_argument("--min-run", type=int)
    ap.add_argument("--verbose", action="store_true", help="print WARN findings too, not only their count")
    args = ap.parse_args()
    sys.path.insert(0, str(Path(args.ci_tools).resolve()))
    from juniper_ci_tools import docs_additions_check as docs  # noqa: E402
    from juniper_ci_tools import symbol_loss_check as sym  # noqa: E402

    paths = [ln.strip() for ln in Path(args.list).read_text(encoding="utf-8").splitlines() if ln.strip()]
    bad = [p for p in paths if not Path(p).is_file() or Path(p).is_symlink()]
    if not paths or bad:
        print(f"refused: {len(bad)} missing or irregular path(s) of {len(paths)}: {bad[:5]}", file=sys.stderr)
        return 2
    if subprocess.run(["git", "rev-parse", "--verify", "-q", f"{args.base}^{{commit}}"], capture_output=True, check=False).returncode:  # nosec B603 B607
        print(f"refused: the base {args.base!r} does not resolve", file=sys.stderr)
        return 2
    message = Path(args.message).read_text(encoding="utf-8") if args.message else ""
    min_run = args.min_run if args.min_run is not None else docs.DEFAULT_MIN_RUN

    # The symbol-loss screen.
    scoped = [p for p in paths if (p.endswith(".py") or p.endswith(".bash")) and sym._match_scope(p, SYMBOL_SCOPE)]
    base_invs, head_invs, findings, unparseable = {}, {}, [], []
    for path in sorted(set(scoped)):
        is_bash = path.endswith(".bash")
        base_text = git_text(args.base, path)
        b_inv, ok = sym.symbols_for(path, base_text) if base_text is not None else (None, True)
        if not ok:
            unparseable.append(f"base:{path}")
        h_inv, ok = sym.symbols_for(path, Path(path).read_text(encoding="utf-8"))
        if not ok:
            unparseable.append(f"head:{path}")
        base_invs[path], head_invs[path] = b_inv or {}, h_inv or {}
        findings.extend(sym.classify_file(path, base_invs[path], head_invs[path], is_bash))
    sym.apply_relocation(findings, base_invs, head_invs)
    allowed, _ = sym.parse_allow_trailers(message)
    sym.apply_waivers(findings, allowed)
    sym_fails = [f for f in findings if f.severity == "FAIL"]
    print(f"symbol screen: {len(scoped)} file(s) in scope of {len(paths)}; {len(findings)} finding(s), {len(sym_fails)} FAIL; unparseable: {unparseable or 'none'}")
    for f in sorted(findings, key=lambda x: (x.path, x.symbol)):
        if args.verbose or f.severity == "FAIL":
            print(f"  {f.severity:5} {f.verdict:10} {f.path} :: {f.symbol}")

    # The docs deletion-magnitude screen.
    dscoped = [p for p in paths if docs.in_docs_scope(p)]
    dfindings = []
    for path in sorted(set(dscoped)):
        base_text = git_text(args.base, path)
        head_text = Path(path).read_text(encoding="utf-8")
        hunks = docs.parse_hunks(no_index_diff(base_text or "", head_text)) if base_text is not None else []
        base_fenced = docs.fenced_lines(base_text) if base_text is not None else None
        dfindings.extend(docs.classify_file(path, hunks, min_run, base_fenced, docs.fenced_lines(head_text)))
    dallowed, wildcard = docs.parse_allow_trailers(message)
    docs.apply_waivers(dfindings, dallowed, wildcard)
    docs_fails = [f for f in dfindings if f.severity == "FAIL"]
    warns = sum(1 for f in dfindings if f.severity == "WARN")
    print(f"docs screen: {len(dscoped)} file(s) in scope; min_run {min_run}; {len(dfindings)} finding(s), {len(docs_fails)} FAIL, {warns} WARN")
    for f in sorted(dfindings, key=lambda x: (x.path, x.reason)):
        if args.verbose or f.severity == "FAIL":
            print(f"  {f.severity:5} {f.reason} {f.path} {f.detail}")
    return 1 if sym_fails or docs_fails else 0


if __name__ == "__main__":
    sys.exit(main())
