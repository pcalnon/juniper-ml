"""
Behavioural probes behind the flood-4 juniper-ml docs carrier's claims (claims lens, slice A).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-ml docs carrier validation, claims lens slice A
         (#2417 zero / NaN / inf rendering, #2422 failed-auth table sizes, #2409 DeprecationWarning attribution,
         #2433 worker connection bucket timing)

Usage: <python with matplotlib + fastapi> -I 2026-11-07_flood4_val_ml_docs_claims_a_probe.py <repo_root> <out_dir>

Imports util/experiments and juniper-service-core / juniper-config-tools from <repo_root> (read-only; no
file under <repo_root> is written). Renders probe PNGs into <out_dir>/png/ and writes <out_dir>/probe.json.
"""

import json
import os
import subprocess
import sys
import textwrap


def probe_eval_render(repo: str, out_dir: str) -> dict:
    sys.path.insert(0, os.path.join(repo, "util"))
    sys.path.insert(0, os.path.join(repo, "tests"))
    import matplotlib

    matplotlib.use("Agg")
    from pathlib import Path

    from experiments import plots_cascor as plots
    from experiments import stats_summary as ss
    from cascor_eval_fixtures import METRICS_FINAL_TEST_SPLIT, with_final_accuracy

    png_dir = os.path.join(out_dir, "png")
    os.makedirs(png_dir, exist_ok=True)
    out: dict = {}
    for label, value in (("zero", 0.0), ("nan", float("nan")), ("inf", float("inf")), ("neginf", float("-inf")), ("true", True)):
        row: dict = {}
        blocks = ss.cascor_eval_blocks(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, None if label == "true" else value))
        if label == "true":
            blocks["eval_scalars"]["accuracy"] = True
        _names, series, _subtitle = plots.eval_metrics_series(blocks)
        final = next((v for r, _, v in series if r == "final evaluation"), {})
        row["series_has_accuracy"] = "accuracy" in final
        row["series_accuracy"] = repr(final.get("accuracy"))
        lines = ss._eval_lines(blocks["eval_scalars"], ["accuracy"])
        row["summary_line"] = lines[0]
        try:
            path = plots.render_eval_metrics(blocks, f"probe {label}", Path(png_dir) / f"eval_{label}.png")
            row["render"] = f"ok {os.path.getsize(path)} bytes"
        except Exception as exc:  # noqa: BLE001 -- the probe records whatever the renderer raises
            row["render"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        out[label] = row
    return out


def probe_failed_auth(repo: str) -> dict:
    sys.path.insert(0, os.path.join(repo, "juniper-service-core"))
    import juniper_service_core.security as sec

    clock = {"t": 1_700_000_000.0}

    def fake_time() -> float:
        clock["t"] += 0.01
        return clock["t"]

    sec.time.time = fake_time  # type: ignore[assignment]
    thr = sec.FailedAuthThrottle(max_failures=10, window_seconds=3600)
    sizes = []
    pre_prune = []
    real = thr._maybe_cleanup

    def spy() -> None:
        pre_prune.append(len(thr._failures))
        real()

    thr._maybe_cleanup = spy  # type: ignore[method-assign]
    for i in range(10_500):
        thr.record_failure(f"ip{i}")
        sizes.append(len(thr._failures))
    crossing = [n for n in pre_prune if n > 10_000]
    return {"max_size": max(sizes), "first_pre_prune_over_cap": crossing[0] if crossing else None, "later_pre_prune_over_cap": sorted(set(crossing[1:])), "size_after_call_10100": sizes[10_099], "size_after_call_10199": sizes[10_198], "size_after_call_10200": sizes[10_199]}


def probe_warning_attribution(repo: str, out_dir: str) -> dict:
    pkg = os.path.join(repo, "juniper-config-tools")
    lib_dir = os.path.join(out_dir, "warnprobe")
    os.makedirs(lib_dir, exist_ok=True)
    with open(os.path.join(lib_dir, "svc_lib.py"), "w", encoding="utf-8") as fh:
        fh.write("from juniper_config_tools import env_with_legacy_alias\n\ndef read():\n    return env_with_legacy_alias('NEW_X', 'OLD_X')\n")
    with open(os.path.join(lib_dir, "main_call.py"), "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent(
            """
            import sys
            sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
            from juniper_config_tools import env_with_legacy_alias
            import svc_lib
            print("lib:", svc_lib.read(), flush=True)
            for _ in range(3):
                print("main:", env_with_legacy_alias('NEW_X', 'OLD_X'), flush=True)
            """
        ))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONWARNINGS", "NEW_X")}
    env["OLD_X"] = "legacy"
    res = {}
    for label, flags in (("default", []), ("W_default", ["-W", "default"])):
        proc = subprocess.run([sys.executable, *flags, os.path.join(lib_dir, "main_call.py"), pkg, lib_dir], capture_output=True, text=True, env=env, timeout=60)
        res[label] = {"stdout": proc.stdout.strip().splitlines(), "stderr_warning_lines": [ln for ln in proc.stderr.splitlines() if "DeprecationWarning" in ln]}
    return res


def probe_worker_bucket(repo: str) -> dict:
    sys.path.insert(0, os.path.join(repo, "juniper-service-core"))
    import juniper_service_core.workers.security as ws

    clock = {"t": 1_800_000_000.0}
    ws.time.time = lambda: clock["t"]  # type: ignore[assignment]
    lim = ws.ConnectionRateLimiter()
    first = [lim.allow("h") for _ in range(4)]
    waits = {}
    for dt in (5.9, 6.0):
        clock["t"] = 1_800_000_000.0 + dt
        b = lim._buckets["h"]
        waits[dt] = round(b.tokens + (clock["t"] - b.last_refill) * b.rate, 6)
    zero = ws.ConnectionRateLimiter(max_connections_per_minute=0)
    z = [zero.allow("z") for _ in range(5)]
    return {"defaults_first_four": first, "tokens_would_be_at": waits, "rate0_first_five": z}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    repo, out_dir = argv[1], argv[2]
    os.makedirs(out_dir, exist_ok=True)
    report = {"python": sys.version.split()[0]}
    for name, fn in (("eval_render", lambda: probe_eval_render(repo, out_dir)), ("failed_auth", lambda: probe_failed_auth(repo)), ("warning_attribution", lambda: probe_warning_attribution(repo, out_dir)), ("worker_bucket", lambda: probe_worker_bucket(repo))):
        try:
            report[name] = fn()
        except Exception as exc:  # noqa: BLE001 -- a failed probe is recorded, not hidden
            report[name] = f"PROBE FAILED: {type(exc).__name__}: {exc}"
    with open(os.path.join(out_dir, "probe.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, default=str)
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
