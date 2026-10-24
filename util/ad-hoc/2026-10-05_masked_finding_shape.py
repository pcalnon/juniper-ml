#!/usr/bin/env python3
"""
Print a masked shape of the text around each finding the pre-push gate reports, so a finding can be classified
without printing the value it matched.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-05
Status: ad-hoc — classification aid for the consolidated development plan's validation rounds
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py (the gate whose KEYs this reads);
         util/ad-hoc/2026-10-08_line_read_mutation_run.py (the mutation run that checks the contract below is pinned);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (XC-PRESERVE);
         reports/2026-10-04_consolidated-development-plan/round7-reconciliation.md .. round12-reconciliation.md,
         round13-laneA-reprobe.md and round13-laneB1-safety.md (round 13's findings, R13A- and R13B1-),
         round14-laneB-attack.md (round 14's, R14B-)

What it does
------------
Each KEY is ``PATH:LINES:COLUMN:RULE:HASH`` exactly as the gate prints it (LINES is ``N`` or ``START-END``). For each
one it reads PATH under ``--root``, numbers lines as the gate does (CRLF read as LF, lines split at LF, a file with no
LF split at its CRs), and prints every line of the KEY's range WHOLE, masked, with the finding's character offset on
its first line (the gate's column counts BYTES, one more after line 1, and is converted first: round 10, R10A-02;
whole lines since round 12, R12B1-10, because a window could miss the value of the finding it read).

Masking: every run of letters and digits, Unicode included, is replaced by its class and length -- ``<U8>`` upper
case, ``<l8>`` lower case, ``<M8>`` mixed, ``<D8>`` digits, ``<N8>`` a run with non-ASCII letters -- every run of
other non-blank characters (punctuation, symbols, underscores) by its length, ``<P3>`` (round 11: R11B1-02), and,
since round 13 (R13B1-14), every run of blanks other than the ASCII space and tab -- CR, VT, FF, the separators
0x1C-0x1F, NEL, NBSP, the Unicode spaces -- by its length, ``<S1>``: printed as they were, a value's own blanks showed
in place, and a CR returned a terminal's cursor so that later text overprinted the line. Since round 12 there is no
exception: a credential name is masked like everything else (R12A-02, R12B1-06), because a name's words kept in clear
printed a value that is, or contains, a credential word. Since round 13 a listed line's entry says nothing of why it
is listed (R13B1-09): its counts of names and markers told a value holding a credential word (``blue-TOKEN-river``)
from one holding another word of the same shape (``blue-SPOON-river``). A line is listed or it is not. Only spaces
and tabs print as they are.

It also counts the tokens on each printed line that look random: round 6's Lane A1 test (mixed-case alphanumeric,
``+/=_-`` allowed, 16 or more characters, 4.0 bits per character or more); a run of letters in one case, of 20 or
more at 3.3 bits or of 16 to 19 at 3.6; and, since round 12 (R12B1-11), a run of 32 or more hex digits holding both a
digit and a letter, or a UUID. Only the count is printed, never the token. The count is a selector, not a proof: a
value whose randomness lies in its symbols scores 0, and so does a short random value (under about 20 characters the
4.0-bit test needs nearly every character to differ); the masked shape is what shows them.

Shape is not content: a masked line can say a finding is a placeholder, a name or an option list, and it cannot
prove that a value is not a credential.

``--names`` (round 8's reconciliation; widened in rounds 9 to 13) needs no KEY. It walks ``--root`` and lists every
line that names a credential or carries a marker, then prints, each once, the nearest non-blank line above it, the
line itself WHOLE, and the next five non-blank lines below it, all masked.

THE READ'S CONTRACT, which the regression's ``contract`` and ``names`` checks test and the mutation run checks they pin
(each clause as the checks now test it; round 13 found an unpinned part in each, R13A-01..04, R13B1-03..11):

1. It lists every line that names a credential: B9's names in any case with up to three separator characters of any
   kind between their parts, or none (``pass phrase``, ``pass.phrase``, ``settings_encryption_key``,
   ``web service password``, ``settingsEncryptionKey``); the env-style names as the gate reads them (``*_API_KEY(S)``,
   ``*_TOKEN``, ``*_PASSWORD``, ``*_SECRET``: upper case with a prefix or without one, bare ``TOKEN``, ``PASSWORD``
   and ``SECRET`` included; after leading underscores, as in ``__API_KEY__`` and ``_TOKEN`` (round 13: R13B1-08); or
   any case after a prefix such as ``db_``); and the API-key headers (``X-API-Key``, ``Authorization``, also after
   ``_`` as in ``HTTP_AUTHORIZATION``). And every line that carries a marker: ``aescrypt``; ``openssl``'s ``-pass``,
   ``-passin``, ``-passout`` or ``-password`` before ``pass:``, after blanks or a quote, or as an argv-list item (a
   quote, a comma and a quote between them; ``-passin`` and ``-passout`` since round 13's pins, R13A-01, R13B1-06);
   its ``-k``/``-kfile`` on a line that names openssl, alone or as a list item; a PEM private-key line of any kind;
   the three refusal texts.
2. It prints each listed line whole, the nearest NON-BLANK line above it and the five NON-BLANK lines below it, and
   each line once in its file's output: a line that is itself listed prints as its own entry, never as another
   entry's line above or below, and a line inside two entries' windows prints once (round 13: R13A-03, R13B1-05).
3. On every line it prints, in every mode, every run of letters and digits is masked by class and length, every run
   of other non-blank characters by its length, and every run of blanks but spaces and tabs by its length, names and
   markers included: nothing prints in clear but spaces and tabs. Every line has exactly its mode's form, so no field
   carries a character of the text: ``PATH:N len=L random-looking=R: `` for an entry, ``    above LN random-looking=R: ``
   and ``    below LN random-looking=R: `` for the lines around it, ``PATH:N random-looking=R: `` under ``--all``, and
   in KEY mode the header ``PATH:LINES:COLUMN RULE`` and ``    LN len=L offset=O random-looking=R: `` (``offset=O``
   on the range's first line only); an entry gives no count of what it matched (round 13: R13B1-04, R13B1-09).
   stderr prints no line's characters either (R13B1-03): only the files it refuses with their reasons, its summary,
   and, for a malformed KEY, ``BAD KEY`` with the KEY's place (``argument N`` or ``--keys-file line N``) and its
   masked shape (R13B1-10).
4. It numbers lines as the gate does, and refuses (exit 3) a symlink, a special file, an unreadable file or directory,
   text with a NUL character or not UTF-8, a root that holds no regular file or is itself a symlink, and, in KEY mode,
   a KEY whose path is a symlink (at any step below ``--root``), not a regular file, outside ``--root`` (``..`` or an
   absolute path), or under a ``--root`` that is itself a symlink; whose lines the file does not have (line 0, past
   its end, or a START after its END, which the refusal names); whose column is not on its first line; or whose
   numbers are too long to read; and a ``--keys-file`` that is a symlink, a special file, not UTF-8 or holds a NUL
   (round 13: R13A-02, R13B1-07, R13B1-11, R13B1-17). It checks by ``lstat`` before it opens anything, so a FIFO is
   refused, not read. A refusal names the file (or the KEY's path) and the reason, never the file's bytes, and a
   refused KEY prints nothing on stdout (R13A-04).

Outside it, so listed limits of the read, whose control is the every-line read (``--all``) where the plan requires it:
a value two or more non-blank lines above its name or six or more below it; a name split across lines, or with four
or more characters between its parts; a credential with neither a name nor a marker among the printed lines, which
includes these layouts (rounds 11 to 13: R11B1-11, R12A-14, R12B1-12, R13B1-13): ``openssl``'s ``-k`` or ``-pass``
with the value on a continuation line; ``openssl``'s ``-pass=pass:`` and ``--pass=pass:`` (its option parser takes
``-flag=value``); an argv item with a string prefix (``f"pass:``, ``b"pass:``); a ``.netrc`` line; a lower-case
bare key (``password:``, ``token:``, ``api_key =``), whatever its value; a credential in a URL's query string (a
Duplicati ``TargetURL``'s ``authid``); ``http.client``'s refusal text (``Invalid header value``); an env-style name with a digit
right after its credential word (``*_PASSWORD2``), with a plural word (``GITHUB_TOKENS``), with its word joined to a
prefix (``PGPASSWORD``), or with a word the env-style names do not hold (``DB_PASS``, ``SSH_PRIVATE_KEY``); a
kebab-case key (``db-password``); a camel-case key (``apiKey``, ``authorizationHeader``); and a capitalised one-word
label (``Password``). The gate reads the ``PGPASSWORD``, ``GITHUB_TOKENS``, ``apiKey``, ``SSH_PRIVATE_KEY`` and
``Password`` assignments (round 13 measured them), and the lower-case bare keys and the ``authid`` query when their
values look random (round 14 measured them: R14B-11), so KEY mode reads them when the gate reports them; ``--names``
does not list them. Nor are these refused: a ``--root`` below a symlinked directory (only a root that is itself a
symlink is), and a KEY path with a trailing slash (``a.env/`` reads ``a.env``) (round 13: R13B1-17). The PATH field
prints a file's name as it is, unmasked, so a name holding a control character (a CR, an escape sequence) can
overprint or erase a terminal's lines; the control is the PR's own changed-file list (round 14: R14B-10).

Limits of the checks, not of the read (round 14: R14B-01..07; listed limits by the owner's rulings of 2026-10-10 and
2026-10-24). The read does what clauses 1 to 4 say, but the checks hold these parts of them by form only, so an edit
that broke one would still pass: the numeric fields (``random-looking=``, ``offset=``, the summary's counts) are held
to digits, not to their values; a refusal is held by its reason's first words, and the planted-value test looks for
whole values, not their parts; the one malformed KEY planted holds no colon; and these layouts are planted once, in
one spelling or one length: lower-case prefixed ``TOKEN``, ``SECRET`` and ``API_KEY`` names, ``openssl``'s four
spellings after a double quote or as argv-list items, a run of two or more blanks that print as a tag, and a KEY
whose END is past the file's end. The 12 mutants that show it are
``reports/2026-10-04_consolidated-development-plan/round14-mutants-laneB.json``, all of which survive. An edit to the
read runs the mutation run over that file as well, and an edit to one of those parts adds its case first.

That is the plan's read of every added line that names a credential, done without printing a value's characters. Run
it on scratch copies of the files a PR adds, made AFTER the last edit; for files a PR changes, copy each changed hunk
with ten context lines (``git diff -U10``), so that a name above a changed value comes too.

``--all`` prints every line of every file, masked, for the read of every added line that backup-arc or
transcript-derived text needs.

Never paste the output of any mode into public text: it gives the shape of every value it prints.

Usage
-----
    python3 util/ad-hoc/2026-10-05_masked_finding_shape.py --root <scan-dir> KEY [KEY ...]
    python3 util/ad-hoc/2026-10-05_masked_finding_shape.py --root <scan-dir> --keys-file <file of KEYs>
    python3 util/ad-hoc/2026-10-05_masked_finding_shape.py --root <scratch copies> --names
    python3 util/ad-hoc/2026-10-05_masked_finding_shape.py --root <scratch copies> --all
"""
import argparse
import math
import os
import re
import stat
import sys
from collections import Counter
from pathlib import Path

KEY_RE = re.compile(r"^(?P<path>.+):(?P<line>\d+)(?:-(?P<end>\d+))?:(?P<col>\d+):(?P<rule>[a-z0-9-]+):(?P<hash>[0-9a-f]+)$")
LONG_RUN_RE = re.compile(r"[A-Za-z0-9+/=_-]{16,}")
# a hex key of 32+ digits holding a digit and a letter, or a UUID (round 12: R12B1-11, where both scored 0)
HEX_RE = re.compile(r"(?<![0-9A-Fa-f])(?=[0-9A-Fa-f]*[0-9])(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{32,}(?![0-9A-Fa-f])")
UUID_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])")
RUN_RE = re.compile(r"[^\W_]+")  # a run of letters and digits, Unicode included
MASK_RE = re.compile(r"[^\W_]+|(?:[^\w\s]|_)+")  # that, or a run of other non-blank characters (round 11: R11B1-02)
BLANK_RE = re.compile(r"[^\S \t]+")  # a run of blanks other than the ASCII space and tab: CR, VT, NBSP, ... (round 13: R13B1-14)
# --names: the gate's B9 names in any case, with up to three separator characters of any kind between their parts
# (blanks from round 10's reconciliation, R10B1-03; any kind from round 11's), env-style names (upper case, prefix optional), any-case env names after a prefix (`db_password`), and the
# API-key headers. Markers: credentials that carry no name. All are assembled from parts, so that this file passes the
# gate without an --accept. Since round 13 (R13B1-08), upper-case env names after leading underscores too, as the
# gate's wrapper reads them.
_SEP = "[^A-Za-z0-9\\n]{0,3}"  # up to three of any separator: `-`, `_`, blanks, dots, slashes, ... (round 11: R11A-02, R11B1-04)
_B9 = "pass" + _SEP + "phrase|settings" + _SEP + "encryption" + _SEP + "key|duplicati" + _SEP + "web" + _SEP + "credential|web" + _SEP + "service" + _SEP + "pass" + "word"
_ENV_WORDS = "API_KEYS?|TOK" + "EN|PASS" + "WORD|SEC" + "RET"
NAME_RE = re.compile(
    "(?i:" + _B9 + ")"
    + "|(?<![A-Za-z0-9_])(?:[A-Z][A-Z0-9_]*_)?(?:" + _ENV_WORDS + ")(?:_[A-Z0-9]+)*(?![A-Za-z0-9_])"
    + "|(?<![A-Za-z0-9])_+(?:[A-Z][A-Z0-9_]*_)?(?:" + _ENV_WORDS + ")(?:_[A-Z0-9]+)*(?![A-Za-z0-9])"  # `__API_KEY__`, `_TOKEN`
    + "|(?i:[a-z0-9]_(?:" + _ENV_WORDS + ")(?:_[a-z0-9]+)*(?![a-z0-9]))"
    + "|(?i:x-api-" + "key|(?<![A-Za-z0-9])authori" + "zation(?![A-Za-z0-9]))"  # after `_` too (round 12: R12B1-05)
)
# `openssl`'s `-pass pass:` argument (and -passin, -passout, -password), after blanks or a quote, or as an argv-list
# item, and its `-k`/`-kfile`, alone or as a list item (R10B1-03; round 12: R12B1-05; `-k` counts only on a line that
# names openssl, see _markers)
MARKER_RE = re.compile(
    "(?i)aes" + "crypt|-pass(?:in|out|w" + "ord)?(?:[ \\t]+[\"']?|[\"'][ \\t]*,[ \\t]*[\"'])pass:|private " + "key|in header " + "value|illegal header " + "value|invalid x-api-key " + "header"
    + "|(?<![\\w-])-k(?:file)?(?=[ \\t=]|[\"'][ \\t]*,)"
)
BELOW = 5  # non-blank lines printed under every listed line (round 10's reconciliation: R10A-01, R10B1-02)
ABOVE = 1  # and above it: a Kubernetes entry may give its value before its name (round 11: R11B1-11)


class Refused(Exception):
    """Input this tool cannot read reliably; the caller exits 3."""


def _cls(tok: str) -> str:
    if not tok.isascii():
        return f"<N{len(tok)}>"
    if tok.isdigit():
        return f"<D{len(tok)}>"
    if tok.isupper():
        return f"<U{len(tok)}>"
    if tok.islower():
        return f"<l{len(tok)}>"
    return f"<M{len(tok)}>"


def _mask_runs(text: str) -> str:
    """Mask every run of letters and digits by class and length, and every run of other non-blank characters by its
    length (``<P3>``), names included (round 12: R12A-02, R12B1-06). Blanks are left to mask()."""
    return MASK_RE.sub(lambda m: _cls(m.group(0)) if RUN_RE.fullmatch(m.group(0)) else f"<P{len(m.group(0))}>", text)


def mask(text: str) -> str:
    """A line masked: its runs as _mask_runs masks them, then every run of blanks but spaces and tabs by its length
    (``<S1>``; round 13: R13B1-14), so that only spaces and tabs print as they are."""
    return BLANK_RE.sub(lambda m: f"<S{len(m.group(0))}>", _mask_runs(text))


def _why(exc: Exception) -> str:
    """A refusal's reason, without the input's bytes: a decode error names the byte it failed on (round 11)."""
    if isinstance(exc, UnicodeDecodeError):
        return f"not UTF-8 (at byte {exc.start})"
    return str(exc)


def entropy(tok: str) -> float:
    counts = Counter(tok)
    return -sum(c / len(tok) * math.log2(c / len(tok)) for c in counts.values())


def random_looking(text: str) -> int:
    """Round 6's test (mixed case and digits, 16+ characters, 4.0 bits or more); since round 10's reconciliation, a
    run of 20+ letters in one case at 3.3 bits or more (R10B1-05); since round 12's, a hex key or a UUID (R12B1-11)."""
    hits = 0
    for tok in LONG_RUN_RE.findall(text):
        mixed = any(ch.isupper() for ch in tok) and any(ch.islower() for ch in tok) and any(ch.isdigit() for ch in tok)
        if mixed and entropy(tok) >= 4.0:
            hits += 1
            continue
        if HEX_RE.search(tok) or UUID_RE.search(tok):
            hits += 1
            continue
        # a token can join a name to its value (`NAME=value`), so test its letter runs one by one
        # 20+ letters at 3.3 bits; 16-19 at 3.6, where English words of that length fall well below (round 11: R11A-08)
        if any((run.islower() or run.isupper()) and entropy(run) >= (3.3 if len(run) >= 20 else 3.6) for run in re.findall(r"[A-Za-z]{16,}", tok)):
            hits += 1
    return hits


def _markers(text: str) -> list[tuple[int, int]]:
    """Marker spans; `-k` and `-kfile` count only on a line that names openssl (curl's `-k` is not a credential)."""
    spans = []
    for m in MARKER_RE.finditer(text):
        if m.group(0).lower().startswith("-k") and "openssl" not in text.lower():
            continue
        spans.append(m.span())
    return spans


def char_col(text: str, col: int, first_line: bool) -> int:
    """The 0-based character offset of a gate KEY's column. Gitleaks 8.30.1 reports a 1-based BYTE column on a file's
    first line and one more on later lines (round 10, R10A-02), so after a multibyte character a character slice at
    `col - 1` lands inside the value."""
    off = col - 1 if first_line else col - 2
    return len(text.encode("utf-8")[: max(0, off)].decode("utf-8", errors="ignore"))


def col_on_line(text: str, col: int, first_line: bool) -> bool:
    """Whether a gate KEY's column falls on its line, counted as char_col counts it. A column past the line's end was
    clamped to the end, and one before its start to 0 (round 13: R13B1-17): either way the KEY numbers the line unlike
    this read, so it is refused."""
    off = col - 1 if first_line else col - 2
    return 0 <= off < len(text.encode("utf-8"))


def _files(root: Path) -> tuple[list[Path], list[str]]:
    """Every regular file under root, sorted, and every reason to refuse: a symlink, a special file, a walk error."""
    if root.is_symlink() or not root.is_dir():
        return [], [f"{root}: not a directory, or a symlink"]
    found, refused = [], []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: refused.append(f"{e.filename}: {e.strerror}"), followlinks=False):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                refused.append(f"{p}: a symlink; copy the file itself")
            elif name in filenames and not p.is_file():
                refused.append(f"{p}: not a regular file")
            elif name in filenames:
                found.append(p)
    return sorted(found), refused


def _key_path(root: Path, rel: str) -> Path:
    """A KEY's file, checked as _files checks a walked one, by lstat before anything opens it: KEY mode read through
    a symlink and hung on a FIFO (round 12: R12B1-04)."""
    if root.is_symlink() or not root.is_dir():
        raise Refused("--root is not a directory, or is a symlink")
    parts = Path(rel).parts
    if not parts or Path(rel).is_absolute() or ".." in parts:
        raise Refused("the KEY's path is not inside --root")
    p, st = root, None
    for part in parts:
        p = p / part
        st = os.lstat(p)
        if stat.S_ISLNK(st.st_mode):
            raise Refused("a symlink; copy the file itself")
    if not stat.S_ISREG(st.st_mode):
        raise Refused("not a regular file")
    return p


def _keys_file(name: str) -> list[tuple[str, str]]:
    """--keys-file's KEYs, each with its place in the file, the file checked as a KEY's file is, by lstat before it is
    opened: a FIFO hung the read, and text that is not UTF-8 crashed it naming the byte (round 13: R13B1-11). Its lines
    are read and split by _read, which refuses a NUL and text that is not UTF-8."""
    mode = os.lstat(name).st_mode
    if not stat.S_ISREG(mode):
        raise Refused("a symlink; copy the file itself" if stat.S_ISLNK(mode) else "not a regular file")
    return [(f"--keys-file line {i}", ln.strip()) for i, ln in enumerate(_read(Path(name)), 1) if ln.strip()]


def _read(path: Path) -> list[str]:
    """Lines numbered as the gate numbers them: CRLF read as LF, lines split at LF, and a file with no LF at all split
    at its CRs (round 11: R11A-10, R11B1-03). Refuses text with NUL, and text that is not UTF-8 (the decode raises)."""
    data = path.read_bytes()
    if b"\x00" in data:
        raise Refused("a NUL character (UTF-16 without a byte-order mark?); convert it to UTF-8 and read it apart")
    text = data.decode("utf-8").replace("\r\n", "\n")
    if "\n" not in text:
        text = text.replace("\r", "\n")
    return text.split("\n")


def names(root: Path, every: bool) -> int:
    """List (masked) every line under root that names a credential or carries a marker, or every line; 3 if refused."""
    files, refused = _files(root)
    if not files and not refused:
        refused.append(f"{root}: holds no regular file (round 11: R11B1-08)")
    listed = read = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        try:
            lines = _read(path)
        except (Refused, OSError, UnicodeDecodeError) as exc:
            refused.append(f"{rel}: {_why(exc)}")
            continue
        read += len(lines)
        if every:
            for n, text in enumerate(lines, 1):
                listed += 1
                print(f"{rel}:{n} random-looking={random_looking(text)}: {mask(text)}")
            continue
        found = {n for n, text in enumerate(lines, 1) if NAME_RE.search(text) or _markers(text)}
        shown = set()
        for n in sorted(found):
            text = lines[n - 1]
            listed += 1
            # the nearest non-blank line above, then the listed line WHOLE, then the next BELOW non-blank lines, each
            # once: windows let a value past their ends go unshown (round 11: R11B1-01); a trailing comment or
            # qualifier hid the value below (round 10: R10A-01, R10B1-02); a line that is itself listed prints as its
            # own entry
            above = [(k, a) for k, a in enumerate(lines[: n - 1], 1) if a.strip()][-ABOVE:]
            for k, a in above:
                if k not in shown and k not in found:
                    shown.add(k)
                    print(f"    above L{k} random-looking={random_looking(a)}: {mask(a)}")
            shown.add(n)
            # no count of the names or markers a line matched: a count told a credential word in a value from another
            # word of its shape (round 13: R13B1-09)
            print(f"{rel}:{n} len={len(text)} random-looking={random_looking(text)}: {mask(text)}")
            below = [(k, b) for k, b in enumerate(lines[n:], n + 1) if b.strip()][:BELOW]
            for k, b in below:
                if k not in shown and k not in found:
                    shown.add(k)
                    print(f"    below L{k} random-looking={random_looking(b)}: {mask(b)}")
    for reason in refused:
        print(f"REFUSED {reason}", file=sys.stderr)
    print(f"{listed} line(s) listed from {len(files)} file(s) and {read} line(s) read; {len(refused)} refused", file=sys.stderr)
    return 3 if refused else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", required=True, help="the --scan-dir the gate ran on")
    ap.add_argument("--keys-file", help="a file holding one KEY per line")
    ap.add_argument("--names", action="store_true", help="list, masked, every line under --root that names a credential")
    ap.add_argument("--all", dest="every", action="store_true", help="print every line under --root, masked")
    ap.add_argument("keys", nargs="*")
    args = ap.parse_args()
    if args.names or args.every:
        if args.keys or args.keys_file:
            ap.error("--names and --all take no KEY")
        return names(Path(args.root), args.every)
    keys = [(f"argument {i}", key) for i, key in enumerate(args.keys, 1)]
    if args.keys_file:
        try:
            keys += _keys_file(args.keys_file)
        except (Refused, OSError, ValueError) as exc:  # a decode error is a ValueError
            print(f"REFUSED --keys-file {args.keys_file}: {_why(exc)}", file=sys.stderr)
            return 3
    if not keys:
        ap.error("no KEY given")
    status = 0
    for where, key in keys:
        m = KEY_RE.match(key)
        if not m:
            # its place and its masked shape, never its text: a wrong --keys-file printed every line in clear (R13B1-10)
            print(f"BAD KEY {where}: {mask(key)}", file=sys.stderr)
            status = 3
            continue
        try:
            first = int(m["line"])
            last = int(m["end"] or first)
            col = int(m["col"])
            lines = _read(_key_path(Path(args.root), m["path"]))  # numbered as the gate numbers them (round 11: R11B1-03)
        except (Refused, OSError, ValueError) as exc:  # ValueError: a NUL in a path, a number too long to read (R13B1-11)
            print(f"REFUSED {m['path']}: {_why(exc)}", file=sys.stderr)
            status = 3
            continue
        if first > last:
            print(f"REFUSED {m['path']}: lines {first}-{last} start after they end (START > END)", file=sys.stderr)
            status = 3
            continue
        if not 1 <= first <= last <= len(lines):
            print(f"REFUSED {m['path']}: line {m['line']}{'-' + m['end'] if m['end'] else ''} is not in its {len(lines)} lines, so this read numbers it unlike the gate", file=sys.stderr)
            status = 3
            continue
        if not col_on_line(lines[first - 1], col, first == 1):
            print(f"REFUSED {m['path']}: column {col} is not on line {first}, so this read numbers it unlike the gate", file=sys.stderr)
            status = 3
            continue
        print(f"{m['path']}:{m['line']}{'-' + m['end'] if m['end'] else ''}:{col} {m['rule']}")
        for n in range(first, last + 1):
            text = lines[n - 1]
            offset = f" offset={char_col(text, col, n == 1)}" if n == first else ""
            print(f"    L{n} len={len(text)}{offset} random-looking={random_looking(text)}: {mask(text)}")
    return status


if __name__ == "__main__":
    sys.exit(main())
