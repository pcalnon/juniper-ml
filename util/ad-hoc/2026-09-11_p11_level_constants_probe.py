#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.1)
Application: ad-hoc probe
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: establish, empirically, whether the TWO constants the emit path chooses between
can actually disagree -- because P1.1 collapses three level states into one and must not
silently change which threshold wins.

The emit path today is:

    _get_log_level_check(config_lvl=_level_logger_config, norm_lvl=_level_logger_name)(is_configured())
    # -> lambda c: norm_lvl if c else config_lvl

so BEFORE configuration it uses ``_LOGGER_LOG_LEVEL_LOGGING_CONFIG`` (a NUMBER) and AFTER
it uses ``_LOGGER_LOG_LEVEL_NAME`` (a NAME). If those two always resolve to the same
number, the branch is decorative and collapsing it is behaviour-preserving. If they can
diverge, the collapse must keep whichever the arc decides is canonical -- and say so.

Run under several environments to see which inputs move which constant.
Read-only.
"""
import os
import subprocess
import sys

CASCOR_SRC = "/home/pcalnon/Development/python/Juniper/juniper-cascor/src"

# NOTE: built with str.replace, NOT str.format -- the body is full of f-string braces
# that format() would try to substitute (it raised KeyError: 'n' on `{n}`).
CHILD = r"""
import sys
sys.path.insert(0, "@@SRC@@")
from cascor_constants import constants as C
names = (
    "_LOGGER_LOG_LEVEL_NAME",
    "_LOGGER_LOG_LEVEL_NAME_LOGGING_CONFIG",
    "_LOGGER_LOG_LEVEL_LOGGING_CONFIG",
    "_LOGGER_LOG_LEVEL",
)
for n in names:
    print(f"{n}={getattr(C, n, '<missing>')!r}")
num = C._LOGGER_LOG_LEVEL_NUMBERS_DICT
resolved_name = num.get(C._LOGGER_LOG_LEVEL_NAME)
print(f"RESOLVED_name_as_number={resolved_name!r}")
print(f"RESOLVED_config_number={C._LOGGER_LOG_LEVEL_LOGGING_CONFIG!r}")
print(f"AGREE={resolved_name == C._LOGGER_LOG_LEVEL_LOGGING_CONFIG}")
"""


def run(label, env_overrides):
    env = {k: v for k, v in os.environ.items() if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    env.update(env_overrides)
    out = subprocess.run(
        [sys.executable, "-c", CHILD.replace("@@SRC@@", CASCOR_SRC)],
        capture_output=True, text=True, env=env, check=False,
    )
    if out.returncode != 0:
        print(f"--- {label}: FAILED\n{out.stderr[-800:]}")
        return None
    vals = dict(line.split("=", 1) for line in out.stdout.strip().splitlines() if "=" in line)
    print(f"--- {label}")
    for k in ("_LOGGER_LOG_LEVEL_NAME", "_LOGGER_LOG_LEVEL_NAME_LOGGING_CONFIG",
              "_LOGGER_LOG_LEVEL_LOGGING_CONFIG"):
        print(f"      {k:<40} {vals.get(k)}")
    print(f"      {'name-as-number vs config-number AGREE?':<40} {vals.get('AGREE')}")
    return vals


def main():
    print("Do the emit path's two level sources agree, and what moves them?\n")
    rows = {
        "no level env set": {},
        "JUNIPER_CASCOR_LOG_LEVEL=TRACE": {"JUNIPER_CASCOR_LOG_LEVEL": "TRACE"},
        "CASCOR_LOG_LEVEL=DEBUG (deprecated name)": {"CASCOR_LOG_LEVEL": "DEBUG"},
        "JUNIPER_CASCOR_LOG_LEVEL=WARNING": {"JUNIPER_CASCOR_LOG_LEVEL": "WARNING"},
    }
    got = {}
    for label, env in rows.items():
        got[label] = run(label, env)
        print()

    print("=" * 78)
    base = got.get("no level env set")
    if not base:
        return 2
    diverged = [lbl for lbl, v in got.items() if v and v.get("AGREE") == "False"]
    moved_name = [lbl for lbl, v in got.items()
                  if v and v.get("_LOGGER_LOG_LEVEL_NAME") != base.get("_LOGGER_LOG_LEVEL_NAME")]
    moved_cfg = [lbl for lbl, v in got.items()
                 if v and v.get("_LOGGER_LOG_LEVEL_LOGGING_CONFIG") != base.get("_LOGGER_LOG_LEVEL_LOGGING_CONFIG")]

    print(f"environments where the two DISAGREE : {diverged or 'none'}")
    print(f"environments that move the NAME     : {moved_name or 'none'}")
    print(f"environments that move the CONFIG   : {moved_cfg or 'none'}")
    print()
    if diverged:
        print("=> The is_configured() branch is LOAD-BEARING: the two sources can differ, so")
        print("   collapsing them changes which threshold wins. P1.1 must state which is canonical.")
    else:
        print("=> The two sources agree in every environment probed, so the is_configured()")
        print("   branch selects between EQUAL values and collapsing it is behaviour-preserving")
        print("   for these inputs. That is evidence, not proof: a logging_config.yaml edit could")
        print("   still move the config side independently.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
