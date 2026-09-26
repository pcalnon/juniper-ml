"""Rebuild compare_probe.py's adversarial pair list with chr() (ASCII-only source)."""
p = "compare_probe.py"
s = open(p, encoding="utf-8").read()
start = s.index("pairs = [")
end = s.index("]\nfor a, b in pairs:")
new_pairs = """pairs = [
    (chr(0x1F600), chr(0xD83D) + chr(0xDE00)),  # astral vs its surrogate pair as two code units
    (chr(0x1F511), chr(0xD83D) + chr(0xDD11)),
    (chr(0x10000), chr(0xD800) + chr(0xDC00)),  # a pair that UTF-16 would join
    (chr(0x10FFFF), chr(0xDBFF) + chr(0xDFFF)),
    (chr(0xE9), chr(0xDCC3) + chr(0xDCA9)),  # surrogateescape twins
    (chr(0xFF), chr(0xDCFF)),  # latin-1 vs escaped byte
    ("e" + chr(0x301), chr(0xE9)),  # combining vs precomposed
    ("key" + chr(0), "key"),
    (chr(0), chr(0) * 2),
    ("k", "k "),
    (" k", "k"),
    (chr(0xA0) + "k", " k"),
    (chr(0x85) + "k", chr(10) + "k"),
    ("ab", "ab" + chr(0xD800)),
    ("a" * 100_000, "a" * 99_999 + "b"),
    (chr(0x10FFFF) * 10_000, chr(0x10FFFF) * 10_000),
    (chr(0xD800) * 10_000, chr(0xD800) * 9_999 + chr(0xDC00)),
"""
s = s[:start] + new_pairs + s[end:]
i = s.index("for presented in [")
j = s.index("]:", i)
s = s[:i] + 'for presented in ["", " ", "\\t", chr(0xA0), chr(0x2028), chr(0x3000)' + s[j:]
open(p, "w", encoding="utf-8").write(s)
non_ascii = [ln for ln in s.splitlines() if any(ord(c) > 127 for c in ln)]
print("non-ASCII lines left:", len(non_ascii))
for ln in non_ascii:
    print("  ", ln[:100])
