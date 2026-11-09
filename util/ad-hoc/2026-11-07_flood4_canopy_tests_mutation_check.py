#!/usr/bin/env python3
"""
Mutation-check the canopy flood-4 tests carrier; prove #794's fixture is keyless and #792's stand-in is not vacuous.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation (canopy #789 #792 #794 #795); BRIEF_COMMON rule 11; flood-3 record §6

Usage: 2026-11-07_flood4_canopy_tests_mutation_check.py <tests worktree> <out dir>

1. One one-line mutant per carried test file, applied to the workflow it pins; the file is restored
   byte-for-byte (sha256 before == after) and stale __pycache__ under src/tests is deleted first.
2. #794 under a SIGNING global config that cannot sign (commit.gpgsign=true, gpg.program=false):
   the carried fixture passes; the draft's fixture (its head blob, swapped in and restored) fails.
3. #792 with a BSD-like base64 first on PATH (refuses a FILE operand, as macOS's does): forced
   non-Linux with the stand-in -> passes; forced non-Linux without it -> CI's macOS failures;
   the real Linux path -> fails too (Linux is never silently emulated). Plus the probe, both ways.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
CONDA = "/opt/miniforge3/bin/conda"
CANOPY_PRIMARY = os.path.expanduser("~/Development/python/Juniper/juniper-canopy")

MUTANTS = [
    {
        "name": "789_bare_bandit",
        "test": "tests/regression/test_bandit_sarif_upload.py",
        "target": ".github/workflows/ci.yml",
        "old": '          pip install "bandit[sarif]" pip-audit\n',
        "new": "          pip install bandit pip-audit\n",
    },
    {
        "name": "795_drop_codecov_token",
        "test": "tests/regression/test_codecov_token_upload.py",
        "target": ".github/workflows/ci.yml",
        "old": "          token: ${{ secrets.CODECOV_TOKEN }}\n",
        "new": "          token: ${{ secrets.GITHUB_TOKEN }}\n",
    },
    {
        "name": "792_guard_never_fires",
        "test": "tests/regression/test_lockfile_regen_empty_payload.py",
        "target": ".github/workflows/lockfile-update.yml",
        "old": '          if [ -z "${LOCK_B64}" ]; then\n',
        "new": "          if false; then\n",
    },
    {
        "name": "794_drop_future_date_check",
        "test": "tests/unit/test_agents_md_date_check.py",
        "target": ".github/workflows/agents-md-touch-up.yml",
        "old": '          if [[ "$current" > "$today" ]]; then\n',
        "new": "          if false; then\n",
    },
]

SIGNING_GITCONFIG = "[user]\n\tname = t\n\temail = t@t\n\tsigningkey = 0000000000000000\n[commit]\n\tgpgsign = true\n[tag]\n\tgpgsign = true\n[gpg]\n\tprogram = false\n"

BSD_LIKE_BASE64 = """#!/usr/bin/env python3
# BSD-like base64 (as on CI's macOS runner): a FILE operand is refused; stdin is encoded.
import base64
import sys

operands = [a for a in sys.argv[1:] if not a.startswith("-")]
if operands:
    sys.stderr.write("base64: invalid argument " + operands[0] + "\\n")
    sys.exit(64)
sys.stdout.write(base64.b64encode(sys.stdin.buffer.read()).decode("ascii"))
"""

PROBE_SNIPPET = (
    "import importlib.util, sys, tempfile\n"
    "from pathlib import Path\n"
    "spec = importlib.util.spec_from_file_location('m', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
    "with tempfile.TemporaryDirectory() as d:\n"
    "    print('PROBE', m._base64_runs_the_steps_form(Path(d)))\n"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_pycache(root: Path) -> int:
    n = 0
    for p in sorted(root.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)
        n += 1
    return n


def counts(text: str) -> dict:
    out = {}
    for key in ("passed", "failed", "error", "errors", "skipped"):
        found = re.findall(r"(\d+) " + key + r"\b", text)
        if found:
            out[key] = int(found[-1])
    return out


def run_pytest(src: Path, test: str, log: Path, *, git_global: str, extra_env: dict | None = None, plugins: tuple = ()) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ADHOC)
    env["GIT_CONFIG_GLOBAL"] = git_global
    env.update(extra_env or {})
    cmd = [CONDA, "run", "-n", "JuniperCanopy1", "python", "-m", "pytest", "-p", "no:cacheprovider"]
    for plugin in plugins:
        cmd += ["-p", plugin]
    cmd.append(test)
    proc = subprocess.run(cmd, cwd=src, env=env, capture_output=True, text=True, check=False)
    text = proc.stdout + proc.stderr
    log.write_text(f"# cwd={src}\n# GIT_CONFIG_GLOBAL={git_global}\n# PATH[0]={env['PATH'].split(os.pathsep)[0]}\n# extra_env={extra_env}\n# cmd={' '.join(cmd)}\n{text}\n# exit={proc.returncode}\n", encoding="utf-8")
    return {"exit": proc.returncode, "counts": counts(text), "log": str(log)}


def main(argv: list[str]) -> int:
    wt = Path(argv[1]).resolve()
    out = Path(argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    src = wt / "src"
    results = {"worktree": wt.as_posix(), "mutations": [], "signing": [], "bsd_sim": [], "probe": []}
    ok = True
    # Read-only leak probe (validator finding T-F1): the absolute paths the lockfile step writes,
    # taken from the workflow text itself, must not exist on the host before or after any run.
    step_text = (wt / ".github/workflows/lockfile-update.yml").read_text(encoding="utf-8")
    leak_paths = sorted(set(re.findall(r"(/\S*lockfile-commit(?:-result)?\.json)", step_text)))
    results["host_leak_paths"] = leak_paths
    results["host_leak_before"] = {p: os.path.exists(p) for p in leak_paths}

    for mut in MUTANTS:
        target = wt / mut["target"]
        before = sha(target)
        cleared = clear_pycache(src / "tests")
        text = target.read_text(encoding="utf-8")
        assert text.count(mut["old"]) == 1, (mut["name"], text.count(mut["old"]))
        target.write_text(text.replace(mut["old"], mut["new"]), encoding="utf-8")
        try:
            res = run_pytest(src, mut["test"], out / f"mut_{mut['name']}.log", git_global=os.devnull)
        finally:
            target.write_bytes(text.encode("utf-8"))
        after = sha(target)
        killed = res["counts"].get("failed", 0) > 0 and res["exit"] != 0
        ok &= killed and before == after
        results["mutations"].append({**{k: mut[k] for k in ("name", "test", "target")}, "mutant": f"{mut['target']}: {mut['old'].strip()!r} -> {mut['new'].strip()!r}", "pycache_dirs_cleared": cleared, "result": "killed" if killed else "survived", "sha256_before": before, "sha256_after": after, "restored": before == after, **res})

    # 2. #794 keyless fixture under a signing config that cannot sign.
    cfg = out / "signing_emulation_gitconfig.txt"
    cfg.write_text(SIGNING_GITCONFIG, encoding="utf-8")
    test794 = wt / "src/tests/unit/test_agents_md_date_check.py"
    carried = run_pytest(src, "tests/unit/test_agents_md_date_check.py", out / "signing_carried.log", git_global=str(cfg))
    before = sha(test794)
    original = test794.read_bytes()
    draft = subprocess.run(["git", "-C", CANOPY_PRIMARY, "show", "refs/flood4/pr/794:src/tests/unit/test_agents_md_date_check.py"], check=True, capture_output=True).stdout
    clear_pycache(src / "tests")
    test794.write_bytes(draft)
    try:
        drafted = run_pytest(src, "tests/unit/test_agents_md_date_check.py", out / "signing_draft.log", git_global=str(cfg))
    finally:
        test794.write_bytes(original)
    clear_pycache(src / "tests")
    after = sha(test794)
    results["signing"] = [
        {"variant": "carried (fixture passes -c commit.gpgsign=false -c tag.gpgsign=false)", "expect": "pass", **carried},
        {"variant": "draft head blob 572e252b (inherits the global signing config)", "expect": "fail", **drafted, "sha256_before": before, "sha256_after": after, "restored": before == after},
    ]
    ok &= carried["exit"] == 0 and drafted["exit"] != 0 and before == after

    # 3. #792 on a simulated macOS base64.
    with tempfile.TemporaryDirectory(prefix="flood4-bsd-base64-") as tdir:
        fake_dir = Path(tdir) / "bin"
        fake_dir.mkdir()
        fake = fake_dir / "base64"
        fake.write_text(BSD_LIKE_BASE64, encoding="utf-8")
        fake.chmod(0o755)
        bsd_path = f"{fake_dir}{os.pathsep}{os.environ['PATH']}"
        test792 = "tests/regression/test_lockfile_regen_empty_payload.py"
        sims = [
            ("forced-not-linux, stand-in", {"PATH": bsd_path, "FLOOD4_SIM_MODE": "stand-in"}, ("2026-11-07_flood4_canopy_force_not_linux",), "pass"),
            ("forced-not-linux, stand-in disabled (the draft's behaviour)", {"PATH": bsd_path, "FLOOD4_SIM_MODE": "no-stand-in"}, ("2026-11-07_flood4_canopy_force_not_linux",), "fail"),
            ("real Linux path, BSD-like base64 (never silently emulated)", {"PATH": bsd_path}, (), "fail"),
            ("forced-not-linux, real GNU base64 (probe passes, no stand-in)", {"FLOOD4_SIM_MODE": "stand-in"}, ("2026-11-07_flood4_canopy_force_not_linux",), "pass"),
        ]
        for idx, (label, env, plugins, expect) in enumerate(sims):
            res = run_pytest(src, test792, out / f"bsd_sim_{idx}.log", git_global=os.devnull, extra_env=env, plugins=plugins)
            good = (res["exit"] == 0) if expect == "pass" else (res["exit"] != 0 and res["counts"].get("failed", 0) > 0)
            ok &= good
            results["bsd_sim"].append({"variant": label, "expect": expect, "as_expected": good, **res})
        for label, path_value, expect in (("real GNU base64", os.environ["PATH"], "True"), ("BSD-like base64", bsd_path, "False")):
            env = dict(os.environ)
            env["PATH"] = path_value
            proc = subprocess.run([CONDA, "run", "-n", "JuniperCanopy1", "python", "-c", PROBE_SNIPPET, str(wt / "src" / test792)], env=env, capture_output=True, text=True, check=False)
            got = "True" if "PROBE True" in proc.stdout else ("False" if "PROBE False" in proc.stdout else proc.stdout + proc.stderr)
            ok &= got == expect
            results["probe"].append({"base64": label, "expect": expect, "got": got})

    results["host_leak_after"] = {p: os.path.exists(p) for p in leak_paths}
    ok &= not any(results["host_leak_before"].values()) and not any(results["host_leak_after"].values())
    results["all_as_expected"] = bool(ok)
    (out / "mutation_summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mutations": [(m["name"], m["result"], m["counts"], m["restored"]) for m in results["mutations"]], "signing": [(s["variant"][:30], s["exit"], s["counts"]) for s in results["signing"]], "bsd_sim": [(s["variant"][:40], s["as_expected"], s["counts"]) for s in results["bsd_sim"]], "probe": results["probe"], "host_leak_before": results["host_leak_before"], "host_leak_after": results["host_leak_after"], "all_as_expected": results["all_as_expected"]}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
