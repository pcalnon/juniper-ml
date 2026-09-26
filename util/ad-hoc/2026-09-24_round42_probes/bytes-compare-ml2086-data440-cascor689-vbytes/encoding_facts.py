"""Facts behind the encoding choice, checked rather than asserted.

Every non-ASCII string is built with chr() -- the authoring tool JSON-decodes backslash-u escapes,
which silently JOINS a surrogate-pair escape into one astral character.
"""
import sys

HI, LO = 0xD83D, 0xDD11
astral = chr(0x1F511)
pair = chr(HI) + chr(LO)  # two lone surrogates, NOT joined
assert len(pair) == 2 and len(astral) == 1
print(sys.version.split()[0])
for codec in ("utf-8", "utf-16-le", "utf-16", "utf-32-le"):
    try:
        a = astral.encode(codec, "surrogatepass")
        b = pair.encode(codec, "surrogatepass")
        print(f"  {codec:10} surrogatepass: astral={a!r} pair={b!r} COLLIDE={a == b}")
    except UnicodeEncodeError as exc:
        print(f"  {codec:10} surrogatepass: raises {exc!r}")
try:
    chr(0xD800).encode("utf-8", "surrogateescape")
    print("  surrogateescape on U+D800: no raise")
except UnicodeEncodeError as exc:
    print("  surrogateescape on U+D800 raises:", type(exc).__name__)
e_acute = chr(0xE9)
twin = chr(0xDCC3) + chr(0xDCA9)
print("  surrogateescape collides U+00E9 vs U+DCC3 U+DCA9:", e_acute.encode("utf-8", "surrogateescape") == twin.encode("utf-8", "surrogateescape"))
seen = set()
for cp in range(0x110000):
    b = chr(cp).encode("utf-8", "surrogatepass")
    assert b not in seen
    seen.add(b)
print("  utf-8+surrogatepass: 0x110000 distinct per-code-point encodings:", len(seen) == 0x110000)
# prefix-freeness: lead byte fixes the length for every surrogatepass output (ED is 3-byte like any E0-EF lead)
lens = {}
for b in seen:
    lead = b[0]
    lens.setdefault(lead, set()).add(len(b))
print("  lead byte determines length (prefix-free code => sequences injective):", all(len(v) == 1 for v in lens.values()))
