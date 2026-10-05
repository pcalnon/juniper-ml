#!/usr/bin/env python3
"""Lane C round 3, task 3c: the password-init hand start's --dry-run and refusal cases, non-root,
as the current user (DUPLICATI_RUN_AS=$(id -un)), against a scratch 0700 folder, dummy secret files
and a STUB server (DUPLICATI_SERVER) -- the real binary is never named. `sudo` is PATH-shadowed too.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
SCRIPT = S / "frozen/util/ad-hoc/2026-10-03_password_init_hand_start.bash"
OUT = S / "pwinit"
ME = subprocess.run(["id", "-un"], capture_output=True, text=True, check=True).stdout.strip()


def setup(case: str):
    d = OUT / case
    if d.exists():
        shutil.rmtree(d)
    (d / "data").mkdir(parents=True, mode=0o700)
    (d / "data").chmod(0o700)
    for name in ("key", "pw"):
        (d / name).write_text("dummy-not-a-secret\n")
        (d / name).chmod(0o600)
    stub = d / "server-stub"
    stub.write_text("#!/usr/bin/env bash\n"
                    f"printf 'SERVER-STUB %s\\n' \"$*\" >> {d}/server.log\n"
                    "for a in \"$@\"; do case \"$a\" in --parameters-file=*) f=\"${a#--parameters-file=}\";; esac; done\n"
                    f"[[ -n \"$f\" ]] && {{ stat -c '%a' \"$f\" > {d}/seen-mode; python3 -c 'import sys; t=open(sys.argv[1]).read(); print(len(t.splitlines()), [l.split(\"=\",1)[0] for l in t.splitlines()], all(l == l.strip() for l in t.splitlines()))' \"$f\" > {d}/seen-shape; }}\n"
                    "exit \"${STUB_SERVER_EXIT:-102}\"\n")
    stub.chmod(0o700)
    return d, stub


def run(d: Path, stub: Path, *extra: str, dry: bool = True, port: str = "1", env_extra: dict | None = None, path: str | None = None):
    env = dict(os.environ, DUPLICATI_RUN_AS=ME, DUPLICATI_SERVER=str(stub), STUB_LOG=str(d / "stub.log"),
               PATH=path or f"{S / 'stubs/bin'}:{os.environ['PATH']}", PYTHONDONTWRITEBYTECODE="1")
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT), "--data-folder", str(d / "data"), "--settings-key-file", str(d / "key"), "--ui-password-file", str(d / "pw"), "--port", port, *extra]
    if dry:
        cmd.append("--dry-run")
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    return r


def show(case: str, r, d: Path):
    called = (d / "server.log").exists()
    left = list((d / "data").glob(".password-init-*"))
    print(f"== {case}: exit={r.returncode} server_invoked={called} params_left={len(left)}")
    for ln in r.stderr.splitlines():
        if "FATAL" in ln or "dry run" in ln or "exit 102" in ln or "expecting" in ln:
            print(f"   | {ln.split(': ', 1)[-1][:220]}")
    if (d / "seen-shape").exists():
        print(f"   | params file as the server saw it: mode={(d / 'seen-mode').read_text().strip()} lines/names/trimmed={(d / 'seen-shape').read_text().strip()}")
    if "dummy-not-a-secret" in r.stdout + r.stderr:
        print("   !! a secret value reached the output")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    d, stub = setup("a_dry_ok"); show("a_dry_ok", run(d, stub), d)
    d, stub = setup("b_group_readable_pw"); (d / "pw").chmod(0o640); show("b_group_readable_pw", run(d, stub), d)
    d, stub = setup("b2_group_readable_key_0400"); (d / "key").chmod(0o400); show("b2_key_0400_stricter_than_0600", run(d, stub), d)
    d, stub = setup("c_folder_0750"); (d / "data").chmod(0o750); show("c_folder_0750", run(d, stub), d)
    d, stub = setup("d_port_in_use")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); s.listen(); port = s.getsockname()[1]
        r = run(d, stub, port=str(port))
    show(f"d_port_in_use({port})", r, d)
    with socket.socket(socket.AF_INET6) as s6:
        try:
            s6.bind(("::1", 0)); s6.listen(); p6 = s6.getsockname()[1]
            d, stub = setup("d2_port_in_use_v6"); show(f"d2_port_in_use_ipv6({p6})", run(d, stub, port=str(p6)), d)
        except OSError as exc:
            print(f"== d2: ipv6 loopback unavailable ({exc})")
    d, stub = setup("e_edge_ws_pw_DRY"); (d / "pw").write_text(" dummy-not-a-secret \n"); show("e_edge_whitespace_pw_DRY_RUN", run(d, stub), d)
    d, stub = setup("e2_edge_ws_pw_REAL"); (d / "pw").write_text(" dummy-not-a-secret \n"); show("e2_edge_whitespace_pw_REAL(stub)", run(d, stub, dry=False), d)
    d, stub = setup("e3_crlf_key_REAL"); (d / "key").write_text("dummy-not-a-secret\r\n"); show("e3_crlf_key_REAL(stub)", run(d, stub, dry=False), d)
    d, stub = setup("e4_trailing_tab_key_DRY"); (d / "key").write_text("dummy-not-a-secret\t\n"); show("e4_trailing_tab_key_DRY_RUN", run(d, stub), d)
    d, stub = setup("f_two_lines_REAL"); (d / "pw").write_text("a-line\nanother\n"); show("f_two_lines_pw_REAL(stub)", run(d, stub, dry=False), d)
    d, stub = setup("g_ok_REAL_102"); show("g_ok_REAL_102(stub)", run(d, stub, dry=False), d)
    d, stub = setup("h_REAL_exit1"); show("h_REAL_server_exit_1(stub)", run(d, stub, dry=False, env_extra={"STUB_SERVER_EXIT": "1"}), d)
    # no `ss` on PATH: a PATH of symlinks to everything the script needs except ss
    nos = OUT / "path_no_ss"
    if nos.exists():
        shutil.rmtree(nos)
    nos.mkdir()
    for tool in ("bash", "stat", "id", "grep", "mktemp", "shred", "rm", "python3", "chmod", "chown", "cat", "env"):
        src = shutil.which(tool)
        if src:
            (nos / tool).symlink_to(src)
    d, stub = setup("i_no_ss"); show("i_no_ss_on_PATH", run(d, stub, path=str(nos)), d)
    print("--- the real duplicati-server was never named: DUPLICATI_SERVER was a stub in every case")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
