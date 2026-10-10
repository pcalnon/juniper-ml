#!/usr/bin/env python3
"""
Classify, in-process, every token the line read's ``--all`` pass counts as random-looking, without printing any of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_masked_finding_shape.py (the read whose random-looking test this reuses);
         util/ad-hoc/2026-10-08_pr_printed_line_screen.py (the sibling screen for ``--names`` output);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (the PRs this screens)

Why this exists
---------------
The read's ``--all`` mode prints every line masked, with a count of random-looking tokens, so a credential-shaped
value can be found without printing it. A count is not a classification: round 12's reconciliation classified 1,085
tokens (paths, sha256 values, dated names, identifiers) partly by hand. This does the same in-process, for the files
of a push snapshot that are new or changed against an earlier snapshot, using the read's own token test:

  * ``path``: the token, stripped of punctuation and of an ``EX/``, ``HO/``, ``S/`` or ``./`` prefix, is part of a
    path in the snapshot, the earlier snapshot or the repository's tracked list (the read's token class has no ``.``,
    so ``…/name.md`` arrives as ``…/name``);
  * ``session``: the Claude session id of a ``claude.ai/code/session_…`` URL, which the attribution trailer carries;
  * ``hash``: a hex run that prefixes a sha256 of a file under either snapshot or a ``--hash-file``, or names a git
    object (``git cat-file -e``, run in the current repository);
  * ``public``: the token occurs in the text of a tracked file on disk, so it is published already;
  * ``dated``: a name holding a ``YYYY-MM-DD`` date whose other parts are dictionary words, two joined, or short;
  * ``words``: an identifier whose parts (split on punctuation, digits and camel case) are dictionary words, two
    dictionary words joined, or short;
  * ``other``: anything else, printed as ``file:line``, the token's masked shape and how many snapshot files hold it,
    to be read by hand, masked.

A token on a line with ``://`` and an ``@`` before a host is always ``other``: a URL can carry credentials.

Usage
-----
    git ls-files > tracked.txt   # in the repository first
    python3 -B util/ad-hoc/2026-10-10_all_pass_token_classes.py --root <snapshot> [--old <earlier snapshot>] \\
        --tracked tracked.txt [--hash-file FILE ...] [--words /usr/share/dict/words]

Exit 0 when nothing is ``other``, 1 otherwise, 2 on a usage error.
"""
import argparse
import hashlib
import importlib.util
import re
import subprocess  # nosec B404 -- fixed argv, never a shell
import sys
from collections import Counter
from pathlib import Path

READ = Path(__file__).resolve().parent / "2026-10-05_masked_finding_shape.py"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
HEXRUN_RE = re.compile(r"[0-9a-fA-F]{7,}")
SESSION_RE = re.compile(r"session_[0-9A-Za-z]{20,32}$")
STRIP = "`'\"()[]{}<>,;:.!?*|"


def load_read():
    spec = importlib.util.spec_from_file_location("masked_finding_shape", READ)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["masked_finding_shape"] = mod
    spec.loader.exec_module(mod)
    return mod


def files_under(root: Path) -> dict:
    return dict((p.relative_to(root).as_posix(), p) for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink())


def changed(new: dict, old: dict) -> list:
    out = []
    for rel, path in new.items():
        if rel not in old or old[rel].read_bytes() != path.read_bytes():
            out.append(rel)
    return out


def hit_tokens(rd, text: str) -> list:
    """The tokens the read's random_looking() counts, one per hit, in its own order and by its own tests."""
    hits = []
    for tok in rd.LONG_RUN_RE.findall(text):
        mixed = any(ch.isupper() for ch in tok) and any(ch.islower() for ch in tok) and any(ch.isdigit() for ch in tok)
        if mixed and rd.entropy(tok) >= 4.0:
            hits.append(tok)
            continue
        if rd.HEX_RE.search(tok) or rd.UUID_RE.search(tok):
            hits.append(tok)
            continue
        if any((run.islower() or run.isupper()) and rd.entropy(run) >= (3.3 if len(run) >= 20 else 3.6) for run in re.findall(r"[A-Za-z]{16,}", tok)):
            hits.append(tok)
    return hits


def parts_of(tok: str) -> list:
    out = []
    for piece in re.split(r"[^A-Za-z]+", tok):
        out.extend(p for p in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+", piece) if p)
    return out


def is_word(part: str, words: set) -> bool:
    low = part.lower()
    if len(low) <= 3 or low in words:
        return True
    return any(low[:i] in words and low[i:] in words for i in range(3, len(low) - 2))


def all_words(tok: str, words: set) -> bool:
    parts = parts_of(tok)
    return bool(parts) and all(is_word(p, words) for p in parts)


def is_git_object(hexrun: str) -> bool:
    if not 7 <= len(hexrun) <= 40:
        return False
    res = subprocess.run(["git", "cat-file", "-e", hexrun], capture_output=True, check=False)  # nosec B603 B607
    return res.returncode == 0


def classify(tok: str, line: str, pathtext: str, public: str, hashes: list, words: set, cache: dict) -> str:
    if "://" in line and re.search(r"://[^/\s@]*@", line):
        return "other"
    core = tok.strip(STRIP)
    for prefix in ("./", "EX/", "HO/", "S/"):
        if core.startswith(prefix):
            core = core[len(prefix):]
    if core and core in pathtext:
        return "path"
    sess = SESSION_RE.search(core)
    if sess and "claude.ai/code/" + sess.group(0) in line and core.endswith(sess.group(0)):
        return "session"
    runs = HEXRUN_RE.findall(core)
    if runs and all(re.fullmatch(r"[0-9a-fA-F]+", r) for r in runs) and len("".join(runs)) >= len(core) - 1:
        for run in runs:
            if run not in cache:
                low = run.lower()
                cache[run] = any(h.startswith(low) for h in hashes) or is_git_object(low)
        if all(cache[r] for r in runs):
            return "hash"
        return "other"
    if core in public:
        return "public"
    if DATE_RE.search(core):
        rest = DATE_RE.sub(" ", core)
        if all_words(rest, words) or not parts_of(rest):
            return "dated"
    if all_words(core, words):
        return "words"
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--old")
    ap.add_argument("--tracked", required=True)
    ap.add_argument("--hash-file", action="append", default=[])
    ap.add_argument("--words", default="/usr/share/dict/words")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"refused: --root {root} is not a directory", file=sys.stderr)
        return 2
    rd = load_read()
    new = files_under(root)
    old = files_under(Path(args.old)) if args.old else {}
    targets = changed(new, old) if args.old else list(new)

    tracked = Path(args.tracked).read_text(encoding="utf-8").split()
    pathtext = "\n".join(sorted(set(tracked) | set(new) | set(old)))
    texts = []
    for rel in tracked:
        p = Path(rel)
        if p.is_file() and not p.is_symlink():
            texts.append(p.read_bytes().decode("utf-8", errors="replace"))
    public = "\n".join(texts)
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in list(new.values()) + list(old.values())]
    hashes += [hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in args.hash_file]
    words = set(w.strip().lower() for w in Path(args.words).read_text(encoding="utf-8", errors="replace").split())
    snap = dict((rel, new[rel].read_bytes().decode("utf-8", errors="replace")) for rel in new)

    counts, others, cache, total = Counter(), [], {}, 0
    for rel in targets:
        for n, line in enumerate(snap[rel].split("\n"), 1):
            for tok in hit_tokens(rd, line):
                total += 1
                cls = classify(tok, line, pathtext, public, hashes, words, cache)
                counts[cls] += 1
                if cls == "other":
                    held = sum(1 for t in snap.values() if tok in t)
                    others.append(f"  {rel}:{n} other: {rd.mask(tok)} (in {held} snapshot file(s))")
    print(f"{len(targets)} new or changed file(s); {total} random-looking token(s): " + ", ".join(f"{k} {counts[k]}" for k in ("path", "session", "hash", "public", "dated", "words", "other")))
    for row in others:
        print(row)
    return 1 if counts["other"] else 0


if __name__ == "__main__":
    sys.exit(main())
