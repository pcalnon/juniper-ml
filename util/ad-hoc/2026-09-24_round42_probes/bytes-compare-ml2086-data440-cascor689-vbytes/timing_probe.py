"""compare_digest(presented, candidate) on bytes of different lengths: what does the time track?"""
import hmac
import sys
import timeit


def t(a, b, n=200):
    return min(timeit.repeat(lambda: hmac.compare_digest(a, b), number=n, repeat=7)) / n * 1e6


print(sys.version.split()[0])
cand = b"c" * 1_000_000
for plen in (1, 1_000, 1_000_000, 2_000_000):
    pres = b"p" * plen
    print(f"  presented len {plen:>9} vs candidate len 1e6 : {t(pres, cand):8.1f} us")
pres = b"p" * 16
for clen in (16, 1_000, 1_000_000, 2_000_000):
    print(f"  presented len        16 vs candidate len {clen:>9}: {t(pres, b'c' * clen):8.1f} us")
# equal length: first-byte mismatch vs last-byte mismatch vs match
base = b"k" * 1_000_000
first = b"x" + base[1:]
last = base[:-1] + b"x"
print(f"  equal-length, mismatch at byte 0 : {t(first, base):8.1f} us")
print(f"  equal-length, mismatch at last   : {t(last, base):8.1f} us")
print(f"  equal-length, match              : {t(base, base):8.1f} us")
