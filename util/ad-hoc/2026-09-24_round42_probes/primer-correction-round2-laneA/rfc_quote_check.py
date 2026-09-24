#!/usr/bin/env python3
"""Lane A r2: verify RFC 9110 quotations and paraphrase anchors in the primer's Appendix E and rewrites.

rfc9110.txt was fetched from https://www.rfc-editor.org/rfc/rfc9110.txt. Page footers/headers and
form feeds are removed, whitespace is collapsed, and every match is mapped to the numbered section
that contains it, so a quote attributed to the wrong section is reported as such.
Negative control: a one-word mutation of each quote must NOT be found.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = (HERE / "rfc9110.txt").read_text(encoding="utf-8-sig")
lines = []
for ln in raw.replace("\f", "\n").splitlines():
    if re.match(r"^Fielding, et al\.\s+Standards Track\s+\[Page \d+\]$", ln.strip()):
        continue
    if re.match(r"^RFC 9110\s+HTTP Semantics\s+June 2022$", ln.strip()):
        continue
    lines.append(ln)
# section map: heading lines like "8.8.1.  Weak versus Strong" at column 0, after the ToC
body_start = [i for i, l in enumerate(lines) if re.match(r"^1\.  Introduction$", l)][0]  # column-0 heading = body (ToC entries are indented)
text_parts, offsets, sec_marks = [], 0, []
for l in lines[body_start:]:
    m = re.match(r"^(\d+(?:\.\d+)*)\.\s{2}\S", l)
    if m:
        sec_marks.append((offsets, m.group(1), l.strip()))
    s = " ".join(l.split())
    if s:
        text_parts.append(s)
        offsets += len(s) + 1
norm = " ".join(text_parts)


def section_at(pos: int) -> str:
    cur = "?"
    for off, num, _ in sec_marks:
        if off <= pos:
            cur = num
        else:
            break
    return cur


def check(label: str, quote: str, cited: str) -> bool:
    q = " ".join(quote.split())
    hits = [m.start() for m in re.finditer(re.escape(q), norm)]
    secs = sorted({section_at(h) for h in hits})
    ok = bool(hits) and any(s == cited or s.startswith(cited + ".") for s in secs)
    # negative control: mutate one word
    words = q.split()
    mut = " ".join(words[:-1] + [words[-1] + "X"])
    neg = re.search(re.escape(mut), norm) is None
    print(f"[{'VERBATIM' if hits else 'NOT FOUND'}{' in ' + ','.join(secs) if hits else ''}] cited §{cited} -> {'OK' if ok else 'MISMATCH'} | neg-control {'ok' if neg else 'FAILED'} | {label}")
    return ok and neg


results = []
# --- Appendix E (primer b6129bf8 L9897-9899): the only RFC quotation in E.1/E.2
results.append(check("E.1 L9897-9899", "a validator is weak if it is shared by two or more representations of a given resource at the same time, unless those representations have identical representation data", "8.8.1"))
# --- Rewritten L4222 continues a quotation on L4223-4224 (bold markup stripped)
results.append(check("L4222-4224 quote (bold stripped)", "if the data is available prior to the response header fields being sent and the digest does not need to be recalculated every time a validation request is received.", "8.8.1"))
# --- Rewritten L4222's unquoted paraphrase: source sentence it paraphrases
results.append(check("L4222 paraphrase source", "A collision-resistant hash function applied to the representation data is also sufficient", "8.8.1"))
# --- E.1 paraphrase anchors (not quoted in the primer; the sentences they rest on)
results.append(check("E.1 If-Range strong-only (13.1.5)", "A client MUST NOT generate an If-Range header field containing an entity tag that is marked as weak.", "13.1.5"))
results.append(check("E.1 If-Match strong comparison (13.1.1)", "An origin server MUST use the strong comparison function when comparing entity tags for If-Match", "13.1.1"))
results.append(check("E.1 If-None-Match weak comparison (13.1.2)", "A recipient MUST use the weak comparison function when comparing entity tags for If-None-Match", "13.1.2"))
# --- pre-existing quotes adjacent to markers (out of the PR's diff; checked for completeness)
results.append(check("L4244-4245 (pre-existing, cited §13.2.1)", "to forgo forwarding conditional requests when they hold a fresh response", "13.2.1"))
results.append(check("L4195 (pre-existing, cited §13.1.1)", "appears to have already been applied", "13.1.1"))
results.append(check("L4196-4197 (pre-existing, cited §13.1.1)", "an origin server is better off being stringent in sending 412 for every failed precondition on an unsafe method", "13.1.1"))
results.append(check("L4255-4256 (pre-existing, cited §8.8.1)", "if the origin server sends the same validator for a representation with a gzip content coding applied as it does for a representation with no content coding, then that validator is weak.", "8.8.1"))
# http_cache.py (juniper-data) calls this phrase the §8.8.1 definition, in quotes
results.append(check("juniper-data http_cache.py:17-19 quoted phrase", "Same content, possibly different bytes", "8.8.1"))
print(f"{sum(results)}/{len(results)} OK (the last is expected NOT FOUND)")
sys.exit(0)
