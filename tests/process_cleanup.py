"""force_kill -- tear down a process a launcher test started, and everything it has running.

The launcher suites (``tests/test_isolated_stack_script.py``,
``tests/test_experiment_stack_script.py``) drive scripts that ``nohup`` their services, then
clean up in a ``finally`` that runs INSIDE a ``TemporaryDirectory`` block. Anything the cleanup
leaves running races ``rmtree``: a stub that writes a marker after the directory was listed is
exactly ``OSError: [Errno 39] Directory not empty: '…/markers'``, which turned ``main`` red and
HALTed the juniper-ml 0.10.0 release ceremony (juniper-ml#2046).

Ten hand-copied ``_force_kill`` helpers preceded this one, across four suites. They sent
``os.killpg(pid)`` first and read its ``ProcessLookupError`` as "already dead" -- but ``killpg``
raises that for a pid that is alive and merely leads no process group, which is every service a
script launches with a bare ``nohup … &``. Handed such a pid, a copy killed nothing: the stub
outlived its test in 300 of 300 runs (``util/ad-hoc/2026-09-23_force_kill_orphan_writer_race.py``).
A census of every call site (``util/ad-hoc/2026-09-23_force_kill_survivor_census.py``) found two
copies handed a live one in passing runs -- ``TestDataUpLive``'s and the module-level copy in
``tests/test_experiment_stack_script.py`` -- with 8 stubs outliving their tests per run of the
two suites; and two more, ``TestDoUpPartialFailureTeardown``'s and ``TestDoUpFailClosedTeardown``'s,
that back up a teardown under test: handed a nohup'd pid the script normally kills first, they
fail exactly when their test does. #2046 named ``TestDataUpLive``'s and ``TestStopPort``'s, and
``TestStopPort`` is only ever handed ``setsid`` leaders. The five copies still in the tree
(``TestTeardownBehaviour``, ``TestTwoRunConcurrency``, two in ``tests/test_juniper_chop_all.py``,
one in ``tests/test_juniper_plant_all.py``) are handed nothing but ``setsid`` leaders, which
``killpg`` does reach, and were left alone.

Enforced by ``tests/test_isolated_stack_script.py`` ``TestForceKill``, which launches each shape
a real call site hands over; ``util/ad-hoc/2026-09-23_force_kill_mutation_check.py`` kills 5/5
mutants against it.
"""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path


def proc_stat(pid: int) -> "tuple[str, int, int] | None":
    """``(state, ppid, pgrp)`` from ``/proc/<pid>/stat``, or ``None`` once the pid is gone."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    # comm (field 2) may hold spaces and parentheses; nothing after its LAST ")" can.
    state, ppid, pgrp = stat.rsplit(")", 1)[1].split()[:3]
    return state, int(ppid), int(pgrp)


def is_running(pid: int) -> bool:
    """True while ``pid`` exists and is not a zombie -- a zombie has closed its files and runs nothing."""
    info = proc_stat(pid)
    return info is not None and info[0] not in ("Z", "X")


def reachable_from(pid: int) -> "list[int]":
    """``pid``'s descendants, plus the members of the process group ``pid`` leads (if it leads one)."""
    table = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            info = proc_stat(int(entry.name))
            if info is not None:
                table[int(entry.name)] = info
    # pgrp == pid only for a group pid LEADS, so this can never reach the runner's own group.
    found = {other for other, (_state, _ppid, pgrp) in table.items() if pgrp == pid and other != pid}
    descendants: "set[int]" = set()
    frontier = [pid]
    while frontier:
        parent = frontier.pop()
        for child, (_state, ppid, _pgrp) in table.items():
            if ppid == parent and child not in descendants:
                descendants.add(child)
                frontier.append(child)
    return sorted(found | descendants)


def force_kill(pid: int) -> None:
    """SIGKILL ``pid`` and everything it has running, then wait (bounded) for all of it to go.

    Three rules, each one learned:

    - **A** ``killpg`` **miss is not a death.** Only ``os.kill`` settles whether ``pid`` lives,
      so the kill below always reaches ``pid`` itself, whatever ``killpg`` said.
    - **What the process has in flight dies with it.** Stubs publish markers through ``mv``
      CHILDREN, and killing only the stub orphans one mid-rename. So ``pid`` is stopped first
      (it can fork no further writer), its descendants are read while it is still their
      parent, and every one of them is killed and waited for.
    - **Never widen the group kill to** ``os.killpg(os.getpgid(pid), …)``. A nohup'd stub shares
      the TEST RUNNER's process group, so that call kills the runner. ``os.killpg(pid)`` reaches
      only a group ``pid`` itself leads -- a ``setsid`` child's -- whose members need not be
      ``pid``'s descendants.

    A pid that is already gone is a no-op: at most call sites the script under test has
    killed the listener before the ``finally`` runs.
    """
    try:
        os.kill(pid, signal.SIGSTOP)
    except (ProcessLookupError, PermissionError):
        return
    for _ in range(20):
        info = proc_stat(pid)
        if info is None or info[0] in ("T", "t", "Z", "X"):
            break
        time.sleep(0.05)
    victims = [pid, *reachable_from(pid)]
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # The usual answer for a nohup'd pid, which leads no group. It carries no verdict: the
        # per-victim kill below still reaches pid, and the wait after it decides.
        pass
    for victim in victims:
        try:
            os.kill(victim, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            # Already gone -- the group kill or its own exit got there first. The wait decides.
            pass
    for _ in range(40):
        if not any(is_running(victim) for victim in victims):
            return
        time.sleep(0.05)
