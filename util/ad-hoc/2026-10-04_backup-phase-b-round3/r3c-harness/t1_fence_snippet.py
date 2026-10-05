#!/usr/bin/env python3
"""Lane C round 3: run the ONE fenced block the clearing script changes (P0 step 10's guard dry-run),
extracted verbatim from the frozen D, against stubs: an API client stub (per-case output) in a scratch
cwd and a PATH-shadowed `sudo` that maps the guard's installed path to a stub guard. Nothing real runs.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
D = S / "frozen/notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md"
W = S / "fence_snippet"


def extract() -> str:
    text = D.read_text(encoding="utf-8")
    start = text.index("   ```text\n   url=\"$(python3 util/ad-hoc/yamaguchi_server_api.py export <id>")
    body_start = text.index("\n", start) + 1
    end = text.index("\n   ```\n", body_start)
    body = text[body_start:end + 1]
    lines = [ln[3:] if ln.startswith("   ") else ln for ln in body.split("\n")]
    return "\n".join(lines)


def mk(path: Path, content: str, mode: int = 0o755) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)


def main() -> int:
    W.mkdir(parents=True, exist_ok=True)
    snippet = extract()
    print("---- extracted snippet (verbatim, dedented) ----")
    print(snippet, end="")
    print("------------------------------------------------")
    runnable = snippet.replace("<id>", "2")
    mk(W / "snippet.bash", runnable, 0o644)
    mk(W / "util/ad-hoc/yamaguchi_server_api.py",
       "import json, os, sys\n"
       "m = os.environ['STUB_MODE']\n"
       "open(os.environ['STUB_LOG'], 'a').write('API ' + ' '.join(sys.argv[1:]) + '\\n')\n"
       "if m == 'ok': print(json.dumps({'Backup': {'TargetURL': 'file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi'}}))\n"
       "elif m == 'fail': sys.exit(1)\n"
       "elif m == 'null': print(json.dumps({'Backup': {'TargetURL': None}}))\n"
       "elif m == 'nobackup': print(json.dumps({'Other': {}}))\n"
       "elif m == 'empty': print(json.dumps({'Backup': {'TargetURL': ''}}))\n"
       "elif m == 'other': print(json.dumps({'Backup': {'TargetURL': 'file:///somewhere/else'}}))\n", 0o644)
    mk(W / "stubbin/sudo",
       "#!/usr/bin/env bash\n"
       "printf 'SUDO-STUB %s\\n' \"$*\" >> \"$STUB_LOG\"\n"
       "[[ \"$1\" == -u ]] && shift 2\n"
       "args=()\n"
       "for a in \"$@\"; do [[ \"$a\" == /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash ]] && a=\"$STUB_GUARD\"; args+=(\"$a\"); done\n"
       "exec \"${args[@]}\"\n")
    mk(W / "stubbin/guard",
       "#!/usr/bin/env bash\n"
       "u=\"${DUPLICATI__REMOTEURL:-}\"\n"
       "printf 'GUARD-STUB called: url length=%s value=%q\\n' \"${#u}\" \"$u\" >> \"$STUB_LOG\"\n"
       "if [[ -n \"$u\" ]]; then [[ \"${u%/}\" == file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi ]] || exit 5; fi\n"
       "exit 0\n")
    for mode in ("ok", "fail", "null", "nobackup", "empty", "other"):
        log = W / f"log-{mode}.txt"
        if log.exists():
            log.unlink()
        env = dict(os.environ, PATH=f"{W / 'stubbin'}:{os.environ['PATH']}", STUB_MODE=mode, STUB_LOG=str(log), STUB_GUARD=str(W / "stubbin/guard"), PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run(["bash", str(W / "snippet.bash")], cwd=W, env=env, capture_output=True, text=True)
        calls = log.read_text().strip().splitlines() if log.exists() else []
        guard_ran = any(c.startswith("GUARD-STUB") for c in calls)
        refuse = "REFUSE" in r.stderr
        print(f"== mode={mode:9s} exit={r.returncode} stdout={r.stdout.strip()!r} REFUSE={refuse} guard_ran={guard_ran}")
        for c in calls:
            print(f"   log: {c}")
        tb = [ln for ln in r.stderr.splitlines() if ln.startswith(("REFUSE", "json", "KeyError", "TypeError"))]
        for ln in tb:
            print(f"   stderr: {ln}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
