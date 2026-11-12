#!/usr/bin/env python3
"""AC-4 restore drill for the Yamaguchi set: one NAMED fileset, destination-only, secret-free sample.

Project:     juniper-ml
Sub-Project: backup infrastructure (Phase D step 14, AC-4)
Author:      Paul Calnon
Created:     2026-11-09
Version:     1.0.0
Status:      ad-hoc -- recovery (Phase D sitting)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md (AC-4, note AC-4a)
             notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.4 step 14)
             util/ad-hoc/duplicati_drill_fresh.py (the 2026-08 drill this replaces for AC-4)

Why a new driver and not util/ad-hoc/duplicati_drill_fresh.py (found 2026-11-08):
  * it decrypts with `duplicati-aescrypt d <passphrase> ...` -- the archive passphrase on argv, readable
    by every user in /proc/*/cmdline. Here AES Crypt is decrypted IN-PROCESS (python3-cryptography);
  * it drills only the NEWEST dlist; AC-4's first drill must restore 20260918T140000Z by name;
  * it passes `--no-local-blocks`, deprecated in 2.4.0.0 (whose default is local blocks OFF; the design
    says never pass `--restore-with-local-blocks`). Neither option is passed here;
  * it has no negative control (AC-4 requires one that FAILS) and no secret-path exclusion: a sample from
    ~/.ssh or ~/.gnupg would put cleartext keys on disk.

What it does (run as ROOT -- post-recovery volumes are 0640 duplicati:duplicati):
  1. Decrypts the named dlist into a root-only run dir and STREAMS filelist.json (a 1.9M-entry fileset
     does not fit comfortably in memory as one json.loads).
  2. Samples files by size stratum (small <= 1 MiB, multi 1-64 MiB, one large 256 MiB-2 GiB, one empty)
     from an ALLOW-LIST of benign extensions, minus a DENY-LIST of secret-bearing prefixes and names,
     preferring files whose live copy is unchanged since the fileset (so the live oracle engages).
  3. One `duplicati-cli restore` of all candidates plus one path that is NOT in the fileset, against a
     NONEXISTENT --dbpath (a temporary database built from the destination alone), pinned with
     --version computed from the destination's own dlist list, which must not change during the restore.
  4. Judges each restored file by SHA-256 AND length against the dlist manifest, and against the live
     file where it predates the fileset; then the negative controls:
       (a) the not-in-fileset path must NOT be restored;
       (b) a one-byte-flipped copy of a verified file must FAIL the oracle.
  Exit 0 = PASS (>= --min-verified files verified, every candidate verified, no live contradiction,
  both negative controls fail as they must); 1 = FAIL; 2 = operational error.

Secrets: the passphrase is read from --cred-file (key PASSPHRASE; one pair of matching outer quotes is
stripped) and reaches duplicati-cli only through its environment (PASSPHRASE), never argv. Only its
sha256[:16] is printed. Nothing is deleted by this tool; the run dir is shredded by the operator after.
"""

import argparse
import base64
import calendar
import codecs
import hashlib
import hmac
import json
import os
import pwd
import random
import re
import subprocess
import sys
import time
import zipfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ALLOW_EXT = (".py", ".md", ".rst", ".txt", ".rs", ".c", ".h", ".cpp", ".hpp", ".js", ".ts", ".css", ".html", ".tex", ".csv", ".ipynb", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".mp3", ".mp4", ".ogg", ".wav", ".iso", ".pt", ".pth", ".onnx", ".npz", ".npy", ".parquet", ".whl", ".so", ".o", ".a", ".rlib", ".jar", ".ttf", ".otf", ".woff", ".woff2")
SOURCE_USER = "pcalnon"  # the backup Source is this user's home; resolved, never ~ (the drill runs as root)
SOURCE_HOME = pwd.getpwnam(SOURCE_USER).pw_dir.rstrip("/") + "/"
DENY_PREFIX = tuple(SOURCE_HOME + p for p in (".ssh/", ".gnupg/", ".config/duplicati-backup/", ".local/share/keyrings/", ".password-store/", ".mozilla/", ".config/google-chrome/", ".config/chromium/", ".config/Slack/", ".config/Code/", ".config/Cursor/", ".config/gh/", ".aws/", ".docker/", ".kube/", ".claude/", ".amp/", ".local/state/", ".cache/"))
DENY_NAME = re.compile(r"(^|/)\.env|secret|token|credential|passw|passphrase|private|id_(rsa|ed25519|ecdsa)" r"|\.(key|pem|p12|pfx|kdbx|keystore|asc|gpg)$|cookie|session", re.IGNORECASE)
NEGATIVE_NAME = ".phase-d-ac4-negative-control-"
VOLATILE_FS = {"tmpfs", "ramfs", "devtmpfs", "squashfs", "overlay"}


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(2)


def load_passphrase(path, key):
    value = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(rf"^\s*(?:export\s+)?{re.escape(key)}=(.*)$", line.rstrip("\n"))
            if m:
                value = m.group(1).strip()
    if not value:
        fail(f"no {key}= assignment in {path}")
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1]
    print(f"credential  : {path} key={key} (sha256[:16]={hashlib.sha256(value.encode()).hexdigest()[:16]})")
    return value


def aescrypt_decrypt(src, dst, password):
    """Decrypt an AES Crypt v2 or v3 file in-process, both HMACs verified (fails closed)."""
    with open(src, "rb") as f:
        size = os.fstat(f.fileno()).st_size
        head = f.read(5)
        if head[:3] != b"AES" or head[3] not in (2, 3):
            fail(f"{os.path.basename(src)}: not an AES Crypt v2/v3 file")
        ver = head[3]
        while True:
            n = int.from_bytes(f.read(2), "big")
            if n == 0:
                break
            f.read(n)
        iters = int.from_bytes(f.read(4), "big") if ver == 3 else 0
        iv1, c_ivkey, mac1 = f.read(16), f.read(48), f.read(32)
        if ver == 2:
            key, pw = iv1 + b"\0" * 16, password.encode("utf-16-le")
            for _ in range(8192):
                key = hashlib.sha256(key + pw).digest()
            ok = hmac.compare_digest(hmac.new(key, c_ivkey, hashlib.sha256).digest(), mac1)
        else:
            key = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), iv1, iters, 32)
            ok = any(hmac.compare_digest(hmac.new(key, c_ivkey + extra, hashlib.sha256).digest(), mac1) for extra in (b"\x03", b""))
        if not ok:
            fail(f"{os.path.basename(src)}: header HMAC mismatch (AES Crypt v{ver}) -- wrong passphrase, or a damaged volume")
        d1 = Cipher(algorithms.AES(key), modes.CBC(iv1)).decryptor()
        ivkey = d1.update(c_ivkey) + d1.finalize()
        iv2, k2 = ivkey[:16], ivkey[16:48]
        start = f.tell()
        ct_len = size - start - (33 if ver == 2 else 32)
        if ct_len <= 0 or ct_len % 16:
            fail(f"{os.path.basename(src)}: ciphertext length {ct_len} is not a positive multiple of 16")
        mac2 = hmac.new(k2, digestmod=hashlib.sha256)
        d2 = Cipher(algorithms.AES(k2), modes.CBC(iv2)).decryptor()
        held = b""
        with open(dst, "wb") as out:
            left = ct_len
            while left:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    fail(f"{os.path.basename(src)}: truncated")
                left -= len(chunk)
                mac2.update(chunk)
                buf = held + d2.update(chunk)
                out.write(buf[:-16])
                held = buf[-16:]
            held += d2.finalize()
            mod = f.read(1)[0] if ver == 2 else None
            if not hmac.compare_digest(mac2.digest(), f.read(32)):  # authenticate before unpadding
                fail(f"{os.path.basename(src)}: content HMAC mismatch")
            if ver == 2:
                tail = held if mod == 0 else held[:mod]
            else:
                pad = held[-1]
                if not 1 <= pad <= 16 or held[-pad:] != bytes([pad]) * pad:
                    fail(f"{os.path.basename(src)}: bad PKCS#7 padding")
                tail = held[:-pad]
            out.write(tail)


def iter_json_array(stream, chunk=1 << 22):
    """Yield the objects of a top-level JSON array from a binary stream, one at a time."""
    dec = json.JSONDecoder()
    utf8 = codecs.getincrementaldecoder("utf-8")()  # a chunk may end inside a multibyte character
    buf, pos, started = "", 0, False
    while True:
        data = stream.read(chunk)
        buf = buf[pos:] + utf8.decode(data or b"", final=not data)
        pos = 0
        while True:
            while pos < len(buf) and buf[pos] in " \t\r\n,﻿":  # .NET writes a UTF-8 BOM
                pos += 1
            if not started:
                if pos < len(buf) and buf[pos] == "[":
                    started, pos = True, pos + 1
                    continue
                if pos < len(buf):
                    fail(f"filelist.json does not start with a JSON array (first character {buf[pos]!r})")
                break
            if pos < len(buf) and buf[pos] == "]":
                return
            try:
                obj, end = dec.raw_decode(buf, pos)
            except json.JSONDecodeError:
                if not data:
                    fail("filelist.json ended inside an entry")
                break
            yield obj
            pos = end
        if not data:
            return


def stratum_of(size):
    if size == 0:
        return "empty"
    if size <= 1 << 20:
        return "small"
    if size <= 64 << 20:
        return "multi"
    if 256 << 20 <= size <= 2 << 30:
        return "large"
    return None


def eligible(path):
    return path.startswith(SOURCE_HOME) and not path.startswith(DENY_PREFIX) and not DENY_NAME.search(path) and NEGATIVE_NAME not in path and not any(ch in path for ch in "*?[]{}") and path.lower().endswith(ALLOW_EXT)


def sha256_b64(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return base64.b64encode(h.digest()).decode()


def judge(c, found, epoch):
    """(verdict, live) for a restored file against the manifest and the live copy."""
    if found is None:
        return "MISSING", None
    if os.path.getsize(found) != c["size"]:
        return f"LENGTH_MISMATCH {os.path.getsize(found)} != {c['size']}", None
    if c["size"] and sha256_b64(found) != c["hash"]:
        return "HASH_MISMATCH", None
    try:
        st = os.lstat(c["path"])
    except OSError:
        return "VERIFIED", None  # the live file is gone: the live oracle cannot engage
    live = None
    if st.st_mtime < epoch and os.path.isfile(c["path"]):
        live = "match" if (st.st_size == c["size"] and (not c["size"] or sha256_b64(c["path"]) == c["hash"])) else "contradiction"
    return "VERIFIED", live


def main():
    ap = argparse.ArgumentParser(description="AC-4 restore drill of one named Yamaguchi fileset")
    ap.add_argument("--dest", required=True, help="destination directory (no default, deliberately)")
    ap.add_argument("--dlist", required=True, help="dlist file name to drill, e.g. duplicati-20260918T140000Z.dlist.zip.aes")
    ap.add_argument("--run-root", default="/root/phase-d-tmp")
    ap.add_argument("--cred-file", default=SOURCE_HOME + ".config/duplicati-backup/env")
    ap.add_argument("--cred-key", default="PASSPHRASE")
    ap.add_argument("--per-stratum", type=int, default=8, help="small and multi each; large and empty take one")
    ap.add_argument("--min-verified", type=int, default=15)
    ap.add_argument("--live-floor", type=int, default=5)
    ap.add_argument("--seed", type=int, default=None, help="default: derived from the dlist name")
    ap.add_argument("--select-only", action="store_true")
    args = ap.parse_args()

    if os.geteuid() != 0:
        fail("run as root: post-recovery volumes are 0640 duplicati:duplicati")
    dest = os.path.realpath(args.dest)
    dlists = sorted(n for n in os.listdir(dest) if ".dlist." in n)
    if args.dlist not in dlists:
        fail(f"{args.dlist} is not in {dest}")
    m = re.search(r"-(\d{8}T\d{6})Z\.dlist\.", args.dlist)
    if not m:
        fail(f"cannot parse the UTC stamp in {args.dlist}")
    epoch = calendar.timegm(time.strptime(m.group(1), "%Y%m%dT%H%M%S"))
    version = len(dlists) - 1 - dlists.index(args.dlist)
    run_root = os.path.realpath(args.run_root)
    if run_root.startswith(("/home/", "/tmp", "/var/tmp", dest)):
        fail(f"run root {run_root} must be outside /home, /tmp and the destination")
    os.makedirs(run_root, mode=0o700, exist_ok=True)
    mp = run_root
    while not os.path.ismount(mp):
        mp = os.path.dirname(mp)
    with open("/proc/mounts") as fh:
        fstype = next((ln.split()[2] for ln in fh if ln.split()[1] == mp), None)
    if fstype in VOLATILE_FS:
        fail(f"run root is on {fstype}")
    st = os.statvfs(run_root)
    print(f"run root    : {run_root} on {mp} ({fstype}), {st.f_bavail * st.f_frsize / 2**30:.0f} GiB free")
    run_dir = os.path.join(run_root, f"ac4-{m.group(1)}-{time.strftime('%Y%m%d-%H%M%S')}")
    work, restored, tmpdir = (os.path.join(run_dir, d) for d in ("work", "restored", "tmp"))
    for d in (run_dir, work, restored, tmpdir):
        os.makedirs(d, mode=0o700, exist_ok=True)
    print(f"run dir     : {run_dir}")
    print(f"destination : {dest} ({len(dlists)} dlists); drilling {args.dlist} = --version={version}")
    print(f"oracle epoch: {epoch} ({time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch))})")

    passphrase = load_passphrase(args.cred_file, args.cred_key)
    plain = os.path.join(work, "dlist.zip")
    aescrypt_decrypt(os.path.join(dest, args.dlist), plain, passphrase)
    rng = random.Random(args.seed if args.seed is not None else int(hashlib.sha256(args.dlist.encode()).hexdigest()[:8], 16))
    pools = {"small": [], "multi": [], "large": [], "empty": []}
    seen = {k: 0 for k in pools}
    total = 0
    with zipfile.ZipFile(plain) as zf, zf.open("filelist.json") as fl:
        for e in iter_json_array(fl):
            total += 1
            if e.get("type") != "File":
                continue
            s = stratum_of(e.get("size", -1))
            if s is None or not eligible(e.get("path", "")):
                continue
            seen[s] += 1  # reservoir sample, 400 per stratum
            item = {"path": e["path"], "size": e["size"], "hash": e.get("hash")}
            if len(pools[s]) < 400:
                pools[s].append(item)
            else:
                j = rng.randrange(seen[s])
                if j < 400:
                    pools[s][j] = item
    if total == 0:
        fail("filelist.json yielded no entries -- a parser fault, not an empty fileset")
    print(f"fileset     : {total} entries; eligible small={seen['small']} multi={seen['multi']} large={seen['large']} empty={seen['empty']}")

    def static(c):
        try:
            st = os.lstat(c["path"])
            return st.st_mtime < epoch and st.st_size == c["size"]
        except OSError:
            return False

    picked, bases, dirs = [], set(), {}
    for s, want in (("small", args.per_stratum), ("multi", args.per_stratum), ("large", 1), ("empty", 1)):
        pool = sorted(pools[s], key=lambda c: (not static(c), rng.random()))
        got = 0
        for c in pool:
            base, top = os.path.basename(c["path"]), "/".join(c["path"].split("/")[:6])
            if got >= want or base in bases or dirs.get(top, 0) >= 2:
                continue
            picked.append({**c, "stratum": s})
            bases.add(base)
            dirs[top] = dirs.get(top, 0) + 1
            got += 1
    negative = f"{SOURCE_HOME}{NEGATIVE_NAME}{rng.randrange(10**9):09d}.txt"
    with open(os.path.join(run_dir, "candidates.json"), "w") as fh:
        json.dump({"dlist": args.dlist, "version": version, "candidates": picked, "negative": negative}, fh, indent=1)
    for c in picked:
        print(f"  [{c['stratum']:>5}] {c['size']:>11} B  static={static(c)!s:5}  {c['path']}")
    print(f"  [  neg] (not in fileset)  {negative}")
    if len(picked) < args.min_verified:
        fail(f"only {len(picked)} candidates; AC-4 needs >= {args.min_verified}")
    if args.select_only:
        return 0

    dbpath = os.path.join(run_dir, "tempdb.sqlite")  # must stay absent: destination-only restore
    argv = ["duplicati-cli", "restore", f"file://{dest}"] + [c["path"] for c in picked] + [negative] + [f"--dbpath={dbpath}", f"--restore-path={restored}", f"--tempdir={tmpdir}", f"--version={version}", "--overwrite=true", "--console-log-level=Warning"]
    env = dict(os.environ, PASSPHRASE=passphrase)
    t0 = time.monotonic()
    proc = subprocess.run(argv, env=env, capture_output=True, text=True, check=False)
    took = time.monotonic() - t0
    with open(os.path.join(run_dir, "restore.log"), "w") as fh:
        fh.write(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
    now = sorted(n for n in os.listdir(dest) if ".dlist." in n)
    if now != dlists:
        fail("the destination's dlist list changed during the restore; --version no longer names the drilled fileset -- rerun")
    if os.path.exists(dbpath):
        fail(f"{dbpath} materialized; the restore was not destination-only")
    print(f"restore     : duplicati-cli rc={proc.returncode} in {took:.0f}s (0 ok, 1 nothing changed, 2 warnings, >=3 errors; log restore.log)")

    found = {}
    for root, _d, files in os.walk(restored):
        for n in files:
            found.setdefault(n, os.path.join(root, n))
    results, verified, live_ok, contra = [], 0, 0, 0
    for c in picked:
        verdict, live = judge(c, found.get(os.path.basename(c["path"])), epoch)
        if proc.returncode >= 3 and verdict == "VERIFIED":
            verdict = f"VERIFIED (but rc={proc.returncode})"
        verified += verdict == "VERIFIED"
        live_ok += live == "match"
        contra += live == "contradiction"
        results.append({**c, "verdict": verdict, "live": live})
        print(f"  [{c['stratum']:>5}] {verdict:<16} live={live}  {c['path']}")
    neg_a = os.path.basename(negative) not in found
    neg_b = False
    probe = next((r for r in results if r["verdict"] == "VERIFIED" and r["size"] > 0), None)
    if probe:
        flipped = os.path.join(work, "negative-flip.bin")
        with open(found[os.path.basename(probe["path"])], "rb") as src, open(flipped, "wb") as dst:
            data = bytearray(src.read(1 << 20))
            data[0] ^= 0xFF
            dst.write(data)
            dst.write(src.read())
        neg_b = judge(probe, flipped, 0)[0] != "VERIFIED"
    with open(os.path.join(run_dir, "results.json"), "w") as fh:
        json.dump({"results": results, "neg_not_in_fileset_absent": neg_a, "neg_flip_rejected": neg_b}, fh, indent=1)
    print()
    print(f"drilled     : {args.dlist} (--version={version})")
    print(f"VERIFIED    : {verified}/{len(picked)} (SHA-256 + length vs the dlist manifest; AC-4 floor {args.min_verified})")
    print(f"live oracle : {live_ok} match, {contra} contradiction (floor {args.live_floor})")
    print(f"negative    : not-in-fileset path absent={neg_a}; flipped-byte copy rejected={neg_b}")
    passed = proc.returncode < 3 and verified == len(picked) and verified >= args.min_verified and contra == 0 and live_ok >= args.live_floor and neg_a and neg_b
    print("RESULT: PASS" if passed else "RESULT: FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
