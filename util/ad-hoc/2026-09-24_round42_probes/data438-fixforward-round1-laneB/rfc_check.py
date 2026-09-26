"""Lane B (r42d): is the quoted sentence verbatim in RFC 9110, and inside §8.8.1?"""

import re
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB")
raw = (S / "out" / "rfc9110.txt").read_text()
lines = raw.splitlines()
QUOTE = "a validator is weak if it is shared by two or more representations of a given resource at the same time, unless those representations have identical representation data"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


# page breaks: drop form feeds and the running header/footer lines
body_lines = [ln for ln in lines if not re.match(r"^(RFC 9110\s+HTTP Semantics|Fielding, et al\.\s+Standards Track)", ln) and "\f" not in ln]
flat = norm("\n".join(body_lines))
print("quote verbatim in RFC (whitespace-normalised):", QUOTE in flat)
# locate section boundaries by their headings (the TOC also lists them; take the LAST occurrence)
h881 = max(i for i, ln in enumerate(lines) if re.match(r"^8\.8\.1\.\s+Weak versus Strong", ln))
h882 = max(i for i, ln in enumerate(lines) if re.match(r"^8\.8\.2\.\s", ln))
print(f"section 8.8.1 heading at line {h881 + 1}, 8.8.2 at line {h882 + 1}")
sect = norm("\n".join(ln for ln in lines[h881:h882] if "\f" not in ln and not re.match(r"^(RFC 9110\s+HTTP Semantics|Fielding, et al\.)", ln)))
print("quote inside 8.8.1:", QUOTE in sect)
for i in range(h881, h882):
    if "validator is weak if it is shared" in lines[i] or "a validator is weak if" in lines[i]:
        print(f"line {i + 1}: {lines[i].strip()}")
for phrase in ("possibly different", "same content"):
    print(f"'{phrase}' occurs in RFC:", phrase in flat)
# what follows the quoted clause in the RFC (the head of the next clause), to check the quote is not truncated mid-sentence
idx = sect.index(QUOTE)
print("RFC continues after the quote:", repr(sect[idx + len(QUOTE): idx + len(QUOTE) + 60]))
print("RFC text before the quote:", repr(sect[max(0, idx - 80): idx]))
