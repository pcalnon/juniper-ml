"""Pytest fixtures for tests that touch ``prometheus_client.REGISTRY``.

Most consumer test suites in the Juniper fleet need to scrub the
default Prometheus ``REGISTRY`` between tests to avoid the
"Duplicated timeseries" failure described in
``juniper_observability.prometheus_helpers``. Until 2026-05-05 each
consumer wrote its own file-scoped autouse fixture, which had two
predictable failure modes:

1. The fixture only sees collectors registered *during its own tests*
   — pollution from earlier tests in other files slips through. Caused
   the juniper-data ``TestSEC16MetricsAppIntegration`` regression on
   2026-05-04.
2. Each consumer's implementation drifts independently from the
   others; bugs fixed in one don't propagate.

This module provides one shared implementation. Consumers wire it
in their ``conftest.py``::

    # tests/conftest.py
    import pytest

    from juniper_observability.testing import reset_prometheus_registry  # noqa: F401


    @pytest.fixture(autouse=True)
    def _autouse_reset(reset_prometheus_registry):
        # ``reset_prometheus_registry`` is a function-scoped fixture
        # that scrubs REGISTRY after each test. The autouse wrapper
        # is a one-liner so consumers can opt in / opt out per test
        # session.
        pass

The fixture itself is intentionally not autouse so consumers can
choose whether they want it on every test or only the metrics-
adjacent ones.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def reset_prometheus_registry():
    """Function-scoped fixture that scrubs Prometheus state after each test.

    Records the set of collectors registered with the default
    ``prometheus_client.REGISTRY`` *before* the test runs; after the
    test, unregisters anything that was added during it. Pre-existing
    collectors (e.g. session-scoped ones from earlier tests in the
    same session that still need to live) are left in place — the
    scrub is incremental, not absolute.

    Also clears the
    :func:`juniper_observability.prometheus_helpers.lazy_register_or_reuse`
    cache so the next test re-runs the lazy-init path cleanly.

    No-op when ``prometheus_client`` is not importable — the fixture
    yields silently so a consumer without the optional ``[prometheus]``
    extra installed can still use this module.

    Yields:
        ``None``. Use as a regular pytest fixture; the cleanup runs
        when the test returns.
    """
    try:
        from prometheus_client import REGISTRY
    except ImportError:
        # Graceful no-op when the optional dependency is absent. The
        # ``yield`` keyword is required for pytest to recognise this
        # as a setup/teardown fixture rather than a fixture that
        # returns a value.
        yield
        return

    from juniper_observability.prometheus_helpers import _clear_lazy_cache

    # ``_collector_to_names`` is the inverse of ``_names_to_collectors``;
    # iterating its keys gives every distinct registered collector
    # (each appears exactly once). We snapshot before yielding so we
    # can compute the diff afterwards.
    before = set(REGISTRY._collector_to_names.keys())
    yield
    after = set(REGISTRY._collector_to_names.keys())
    for collector in after - before:
        try:
            REGISTRY.unregister(collector)
        except Exception:  # nosec B110 — best-effort cleanup, never raise from teardown
            pass

    # Clear the lazy cache last so a subsequent test that re-uses the
    # same metric name doesn't get a stale collector pointing at a
    # now-unregistered REGISTRY entry.
    _clear_lazy_cache()
