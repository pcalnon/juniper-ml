#!/usr/bin/env python3
"""Lane C round 3: the snapshot lane's claim (D section 7.7 as regenerated): under ProtectHome=read-only the
`mode=ro` open of the WAL-mode server database works only while -wal/-shm already exist; after a clean
close that removed them a fire FAILS CLOSED with an SQLite error. Simulated as non-root (user namespaces
are not permitted here): the source directory 0555 and the -wal/-shm 0444, so nothing can be created or
opened for write. A scratch database with no real content; the frozen snapshot script (1.1.0) via --src.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
SNAP = S / "frozen/util/ad-hoc/yamaguchi_server_db_snapshot.py"
OUT = S / "snapshot_wal"
ME = subprocess.run(["id", "-un"], capture_output=True, text=True, check=True).stdout.strip()


def fresh(case: str) -> tuple[Path, Path, Path]:
    d = OUT / case
    if d.exists():
        for p in d.rglob("*"):
            p.chmod(0o700 if p.is_dir() else 0o600)
        d.chmod(0o700)
        subprocess.run(["rm", "-rf", str(d)], check=True)
    src_dir = d / "src"
    src_dir.mkdir(parents=True)
    db = src_dir / "Duplicati-server.sqlite"
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE t (x TEXT)")
    con.execute("INSERT INTO t VALUES ('fake')")
    con.commit()
    con.close()
    return d, src_dir, db


def snap(d: Path, db: Path):
    r = subprocess.run([sys.executable, str(SNAP), "--src", str(db), "--dest-dir", str(d / "dest"), "--owner", ME], capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    err = [ln for ln in r.stderr.splitlines() if "Error" in ln or "error" in ln][-1:]
    made = sorted(p.name for p in (d / "dest").glob("*")) if (d / "dest").exists() else []
    return r.returncode, err, made


def lockdown(src_dir: Path):
    for p in src_dir.iterdir():
        p.chmod(0o444)
    src_dir.chmod(0o555)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # (a) clean close: -wal/-shm removed by the last close; directory read-only
    d, src_dir, db = fresh("a_clean_close")
    print(f"(a) siblings after clean close: {sorted(p.name for p in src_dir.iterdir())}")
    lockdown(src_dir)
    rc, err, made = snap(d, db)
    print(f"(a) clean close, read-only dir: snapshot exit={rc} {err} dest={made}")
    # (b) a writer holds the database open (the running server): -wal/-shm exist, then read-only
    d, src_dir, db = fresh("b_writer_running")
    writer = subprocess.Popen([sys.executable, "-c", "import sqlite3,time,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"PRAGMA journal_mode=WAL\"); c.execute(\"INSERT INTO t VALUES ('w')\"); c.commit(); print('ready', flush=True); time.sleep(20)", str(db)], stdout=subprocess.PIPE, text=True)
    writer.stdout.readline()
    print(f"(b) siblings while the writer runs: {sorted(p.name for p in src_dir.iterdir())}")
    lockdown(src_dir)
    rc, err, made = snap(d, db)
    print(f"(b) writer running, read-only dir and siblings: snapshot exit={rc} {err} dest={made}")
    writer.kill(); writer.wait()
    # (c) the writer died uncleanly: stale -wal/-shm left, nobody holds them, read-only
    d, src_dir, db = fresh("c_writer_killed")
    writer = subprocess.Popen([sys.executable, "-c", "import sqlite3,time,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"PRAGMA journal_mode=WAL\"); c.execute(\"INSERT INTO t VALUES ('w')\"); c.commit(); print('ready', flush=True); time.sleep(20)", str(db)], stdout=subprocess.PIPE, text=True)
    writer.stdout.readline()
    writer.kill(); writer.wait()
    print(f"(c) siblings after a kill -9 of the writer: {sorted(p.name for p in src_dir.iterdir())}")
    lockdown(src_dir)
    rc, err, made = snap(d, db)
    print(f"(c) stale siblings, read-only: snapshot exit={rc} {err} dest={made}")
    # restore permissions so the scratch tree can be removed later
    for case in ("a_clean_close", "b_writer_running", "c_writer_killed"):
        sd = OUT / case / "src"
        sd.chmod(0o700)
        for p in sd.iterdir():
            p.chmod(0o600)
    return 0


if __name__ == "__main__":
    sys.exit(main())
