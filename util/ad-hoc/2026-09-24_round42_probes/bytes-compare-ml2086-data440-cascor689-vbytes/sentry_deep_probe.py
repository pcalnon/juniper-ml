"""Where can a secret still reach the Sentry wire under configure_sentry? (capturing transport, no network)

python sentry_deep_probe.py   (with the observability package under test first on sys.path)
"""

import asyncio
import logging
import sys
import threading

import sentry_sdk
from sentry_sdk.transport import Transport

import juniper_observability
from juniper_observability import configure_sentry
from juniper_observability import sentry as obs_sentry

SECRET = "-".join(("deep", "probe", "secret", "LEAKMARK", "e41a"))
DSN = "http://public@127.0.0.1:9/1"
print("sentry-sdk", sentry_sdk.VERSION, "| observability", juniper_observability.__file__)


class Capturing(Transport):
    def __init__(self):
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)


_real_init = sentry_sdk.init
_state = {}


def _init(*a, **kw):
    kw["transport"] = _state["transport"]
    kw.update(_state.get("overrides", {}))
    return _real_init(*a, **kw)


sentry_sdk.init = _init


def start(overrides=None, send_pii=False):
    _state["transport"] = Capturing()
    _state["overrides"] = overrides or {}
    configure_sentry(DSN, "deep-probe", "0", send_pii=send_pii)
    return _state["transport"]


def stop():
    sentry_sdk.flush(timeout=5)
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)


def wire(transport):
    return b"\n".join(e.serialize() for e in transport.envelopes)


def verdict(name, transport, expect_leak=False):
    w = wire(transport)
    kinds = {}
    for e in transport.envelopes:
        for it in e.items:
            kinds[it.type] = kinds.get(it.type, 0) + 1
    leak = SECRET.encode() in w
    vars_frames = w.count(b'"vars":')
    flag = "LEAK" if leak else "clean"
    note = "" if leak == expect_leak else "   <-- UNEXPECTED"
    print(f"  {name:62} {flag:5}  items={kinds} frames-with-vars={vars_frames}{note}")
    if leak:
        i = w.find(SECRET.encode())
        print("      context:", w[max(0, i - 140): i + 10].decode("utf-8", "replace").replace("\n", " "))
    return leak


def holder_chain():
    candidate = SECRET  # noqa: F841 -- the secret local under a name no denylist carries
    try:
        inner_holder()
    except KeyError as exc:
        raise RuntimeError("outer") from exc


def inner_holder():
    candidate = SECRET  # noqa: F841
    raise KeyError("inner")


def holder_group():
    candidate = SECRET  # noqa: F841
    errs = []
    for i in range(2):
        try:
            candidate_inner = SECRET  # noqa: F841
            raise ValueError(f"member {i}")
        except ValueError as e:
            errs.append(e)
    raise ExceptionGroup("grp", errs)


def run_suite(label, overrides):
    print(f"--- {label} (init overrides: {overrides or 'none'})")
    log = logging.getLogger("deep.probe")

    t = start(overrides)
    try:
        holder_chain()
    except RuntimeError:
        sentry_sdk.capture_exception()
    stop()
    verdict("chained exception (raise from), capture_exception", t)

    t = start(overrides)
    try:
        holder_group()
    except ExceptionGroup:
        sentry_sdk.capture_exception()
    stop()
    verdict("ExceptionGroup, capture_exception", t)

    t = start(overrides)
    try:
        holder_chain()
    except RuntimeError:
        log.exception("Exception in ASGI application")
    stop()
    verdict("logging.exception (uvicorn shape)", t)

    t = start(overrides)

    def with_stack():
        candidate = SECRET  # noqa: F841
        log.error("stack info please", stack_info=True)

    with_stack()
    stop()
    verdict("logging.error(stack_info=True) -> threads interface", t)

    t = start(overrides)

    def thread_target():
        candidate = SECRET  # noqa: F841
        raise RuntimeError("in thread")

    th = threading.Thread(target=thread_target)
    th.start()
    th.join()
    stop()
    verdict("uncaught exception in a threading.Thread", t)

    t = start(overrides)

    async def task_body():
        candidate = SECRET  # noqa: F841
        raise RuntimeError("in task")

    async def main():
        task = asyncio.get_running_loop().create_task(task_body())
        try:
            await task
        except RuntimeError:
            sentry_sdk.capture_exception()

    asyncio.run(main())
    stop()
    verdict("asyncio task exception, capture_exception", t)

    # A pure_eval-like event processor that WRITES frame vars after the SDK built the event.
    t = start(overrides)

    def writes_vars(event, hint):
        for value in (event.get("exception") or {}).get("values", []):
            for frame in (value.get("stacktrace") or {}).get("frames", []):
                frame["vars"] = {"candidate": SECRET}
        return event

    sentry_sdk.get_global_scope().add_event_processor(writes_vars)
    try:
        holder_chain()
    except RuntimeError:
        sentry_sdk.capture_exception()
    stop()
    sentry_sdk.get_global_scope()._event_processors.clear()
    verdict("event processor writes frame vars (pure_eval shape)", t)


run_suite("head configure_sentry as shipped", None)
run_suite("backstop alone (include_local_variables forced True)", {"include_local_variables": True})

print("--- channels the fix does not claim to cover (expected LEAK = pre-existing, by design)")
log = logging.getLogger("deep.probe")
t = start()
log.error("boom", extra={"candidate": SECRET})
stop()
verdict("logging extra={'candidate': SECRET}", t, expect_leak=True)

t = start()
log.info("configured %s", SECRET)
try:
    raise RuntimeError("x")
except RuntimeError:
    sentry_sdk.capture_exception()
stop()
verdict("INFO log line with the secret (breadcrumb + enable_logs Log item)", t, expect_leak=True)
