"""Tests for ``juniper_observability.testing.reset_prometheus_registry``.

The fixture is exercised through pytester so the assertions can
inspect what runs during *another* test session — necessary because
the fixture runs its scrub during teardown of the test that requested
it, and the only place we can verify "the scrub happened correctly"
is from the next test in the same session.

``pytester.runpytest`` calls below pass ``-p no:playwright -p no:dash``
explicitly. The parent ``pyproject.toml`` blocks autoload for the outer
pytest invocation, but pytester spawns a fresh inner pytest from a
temp dir and does not inherit the outer ``addopts``. In envs that have
``pytest-playwright``/``dash.testing`` installed without their runtime
deps (e.g. the legacy ``JuniperCascor-DEPRECATED`` env that has
``pytest-playwright`` but no ``playwright``), autoload would crash the
inner pytest before any test ran.
"""

from __future__ import annotations

import pytest

pytest_plugins = ["pytester"]


def test_fixture_scrubs_added_collectors_after_test(pytester):
    """A test that registers a metric leaves nothing behind for the next test."""
    pytester.makepyfile(
        """
        import pytest

        from prometheus_client import REGISTRY, Counter

        from juniper_observability.testing import reset_prometheus_registry  # noqa: F401


        def test_register_a_metric(reset_prometheus_registry):
            # Registers a brand-new collector. The fixture must
            # unregister it on teardown.
            Counter("test_fixture_scrub_target", "doc")
            assert "test_fixture_scrub_target" in REGISTRY._names_to_collectors


        def test_metric_was_scrubbed(reset_prometheus_registry):
            # Runs after the previous test in the same pytest session.
            # If the fixture worked, REGISTRY no longer has the metric.
            assert "test_fixture_scrub_target" not in REGISTRY._names_to_collectors
        """
    )
    result = pytester.runpytest("-q", "-p", "no:playwright", "-p", "no:dash")
    result.assert_outcomes(passed=2)


def test_fixture_clears_lazy_cache_after_test(pytester):
    """A test that fills the lazy cache leaves it empty for the next test."""
    pytester.makepyfile(
        """
        from prometheus_client import Counter

        from juniper_observability.prometheus_helpers import _lazy_cache, lazy_register_or_reuse
        from juniper_observability.testing import reset_prometheus_registry  # noqa: F401


        def test_populate_cache(reset_prometheus_registry):
            lazy_register_or_reuse(Counter, "test_fixture_cache_target", "doc")
            assert "test_fixture_cache_target" in _lazy_cache


        def test_cache_was_cleared(reset_prometheus_registry):
            assert "test_fixture_cache_target" not in _lazy_cache
        """
    )
    result = pytester.runpytest("-q", "-p", "no:playwright", "-p", "no:dash")
    result.assert_outcomes(passed=2)


def test_fixture_preserves_collectors_registered_before_yield(pytester):
    """The fixture is *incremental* — pre-existing collectors are not touched."""
    pytester.makepyfile(
        """
        from prometheus_client import REGISTRY, Counter

        from juniper_observability.testing import reset_prometheus_registry  # noqa: F401

        # Module-level (i.e. registered BEFORE any test runs).
        _SESSION_METRIC = Counter("test_fixture_preserves_session_metric", "doc")


        def test_session_metric_visible(reset_prometheus_registry):
            assert "test_fixture_preserves_session_metric" in REGISTRY._names_to_collectors


        def test_session_metric_still_visible(reset_prometheus_registry):
            # Even after the fixture's teardown, the pre-existing
            # collector is still there — only NEW additions are
            # scrubbed.
            assert "test_fixture_preserves_session_metric" in REGISTRY._names_to_collectors
        """
    )
    result = pytester.runpytest("-q", "-p", "no:playwright", "-p", "no:dash")
    result.assert_outcomes(passed=2)


def test_fixture_is_no_op_when_prometheus_client_missing(pytester, monkeypatch):
    """The fixture yields silently when ``prometheus_client`` cannot be imported."""
    # Monkeypatch the import inside the inner pytester to fail.
    pytester.makepyfile(
        """
        import builtins

        _real_import = builtins.__import__


        def _no_prometheus(name, *args, **kwargs):
            if name == "prometheus_client" or name.startswith("prometheus_client."):
                raise ImportError("simulated absence")
            return _real_import(name, *args, **kwargs)


        builtins.__import__ = _no_prometheus

        from juniper_observability.testing import reset_prometheus_registry  # noqa: F401


        def test_fixture_no_ops(reset_prometheus_registry):
            # If the fixture didn't no-op, the import inside it would
            # raise and pytest would error. Reaching this assertion is
            # the test.
            assert True
        """
    )
    result = pytester.runpytest("-q", "-p", "no:playwright", "-p", "no:dash")
    result.assert_outcomes(passed=1)
