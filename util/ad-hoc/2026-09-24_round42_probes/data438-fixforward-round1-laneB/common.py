"""Lane B (r42d): shared helpers -- start/stop a scratch juniper-data server on a free port."""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB")
TREES = {"head": S / "head", "main": S / "main"}


def port_is_free(port: int) -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def free_port(start: int) -> int:
    for port in range(start, start + 200):
        if port != 8100 and port_is_free(port):
            return port
    raise RuntimeError("no free port")


@contextlib.contextmanager
def server(tree: str, port_start: int, storage: Path, log: Path):
    """Start serve.py for ``tree`` on a free port over ``storage``; yield (base_url, proc)."""
    port = free_port(port_start)
    storage.mkdir(parents=True, exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(S), "LANG": "C.UTF-8"}
    logf = open(log, "w")
    proc = subprocess.Popen(
        ["bash", str(S / "scripts" / "run_in_tree.bash"), str(TREES[tree]), str(S / "scripts" / "serve.py"), str(TREES[tree]), str(port), str(storage)],
        stdout=logf,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 60
        while True:
            try:
                if httpx.get(base + "/v1/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if proc.poll() is not None:
                raise RuntimeError(f"server exited rc={proc.returncode}; see {log}")
            if time.monotonic() > deadline:
                raise RuntimeError("server never became healthy")
            time.sleep(0.1)
        yield base, proc
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=10)
        logf.close()


def fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path
