#!/usr/bin/env python3
"""Reproduce: LogConfig binds the custom-level closures so the LOGGER becomes the message.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cascor#573 logging arc; found while building roadmap step P0.4)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: cascor src/log_config/log_config.py (the setattr/__get__ loop in LogConfig.__init__),
         src/log_config/logger/logger.py (_init_log_method's log_for_level closure)

WHAT IT SHOWS

``Logger._init_log_method`` builds each custom level method as a CLOSURE,
``log_for_level(message, *args, **kwargs)`` -- no ``self``; the Logger instance is captured from
the enclosing scope. ``LogConfig.__init__`` then copies each one onto the stdlib ``juniper``
logger with ``getattr(custom_logger, name).__get__(self.logger, type(self.logger))``. ``__get__``
on a plain function BINDS it, so the ``juniper`` logger becomes the first positional argument --
``message`` -- and the real message slides into ``*args``. Then:

  * the closure's ``self.isEnabledFor(level_number)`` is the CLASS-level ``Logger.isEnabledFor``,
    reading ``Logger._log_level`` -- so the defect is latent at the default INFO (VERBOSE=5 and
    TRACE=1 are filtered) and LIVE whenever the class level is VERBOSE or TRACE;
  * when live, ``self._log(level, <Logger juniper>, ("the message",))`` formats
    ``str(logger) % ("the message",)`` -> ``TypeError: not all arguments converted``, which
    logging's ``handleError`` prints as ``--- Logging error ---`` on stderr. The record is lost.

Found because the P0.4 envelope emitter (cascor ``src/tests/helpers/log_envelope_emitter.py``)
first set TRACE before constructing LogConfig, and ten such tracebacks came out of LogConfig's
own ``self.logger.verbose(...)`` / ``.trace(...)`` calls.

USAGE

    python3 util/ad-hoc/2026-09-23_logconfig_custom_level_binding_repro.py [--cascor-src <cascor>/src]

Runs two child interpreters (TRACE, then the default INFO) and prints what each saw. Exit 0 when
the defect reproduces exactly as described (errors at TRACE, none at INFO); 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"

CHILD = r'''
import inspect, logging, logging.config, sys
sys.path.insert(0, sys.argv[1])
from log_config.logger.logger import Logger
from log_config.log_config import LogConfig
level = sys.argv[2]
if level != "DEFAULT":
    Logger.set_level(level.replace("+UNBOUND", ""))
lc = LogConfig(_LogConfig__log_config=logging.config)
log = lc.get_logger()
if level.endswith("+UNBOUND"):
    # The binding "corrected": the closure copied onto ``juniper`` WITHOUT ``__get__``, so it is
    # called as ``log_for_level(message, *args)``. Shows where a well-formed record then goes.
    log.verbose = getattr(lc.custom_logger, "verbose")
bound = log.verbose
print("BOUND_TO", type(bound).__name__, getattr(getattr(bound, "__self__", None), "name", None))
print("PARAMS", list(inspect.signature(bound.__func__ if hasattr(bound, "__func__") else bound).parameters))
log.verbose("repro verbose record %s", "ARG")
print("CLASS_LEVEL", Logger.get_level())
'''


def run(src: Path, level: str) -> tuple[str, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        env = {k: v for k, v in os.environ.items() if k not in {"CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL"}}
        env["JUNIPER_CASCOR_LOG_DIR"] = tmp
        proc = subprocess.run([PY, "-c", CHILD, str(src), level], capture_output=True, text=True, env=env, cwd=src, timeout=120)
        log_file = Path(tmp) / "juniper_cascor.log"
        file_text = log_file.read_text(encoding="utf-8") if log_file.is_file() else ""
    return proc.stdout, proc.stderr, file_text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cascor-src", default="/home/pcalnon/Development/python/Juniper/juniper-cascor/src")
    args = ap.parse_args(argv)
    src = Path(args.cascor_src).resolve()
    results = {}
    for level in ("TRACE", "DEFAULT", "TRACE+UNBOUND"):
        out, err, file_text = run(src, level)
        errors = err.count("--- Logging error ---")
        as_message = err.count("Message: <Logger juniper")
        landed = file_text.count("repro verbose record")
        on_stderr = sum(1 for ln in err.splitlines() if "repro verbose record ARG" in ln)
        results[level] = errors
        print(f"== class level {level}: {errors} '--- Logging error ---' block(s); {as_message} naming the LOGGER as the message; the verbose record reached the file sink {landed} time(s), stderr {on_stderr} time(s)")
        for line in out.splitlines():
            if line.startswith(("BOUND_TO", "PARAMS", "CLASS_LEVEL")):  # the child's own probes, not its Path-A chatter
                print(f"   {line}")
    reproduced = results["TRACE"] > 0 and results["DEFAULT"] == 0
    print(f"\nrepro: {'REPRODUCED -- live at TRACE, latent at the default level' if reproduced else 'NOT reproduced as described'}")
    return 0 if reproduced else 1


if __name__ == "__main__":
    sys.exit(main())
