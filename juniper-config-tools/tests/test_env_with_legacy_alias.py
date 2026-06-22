"""Regression tests for :func:`juniper_config_tools.env_with_legacy_alias`.

Behaviour matrix exercised:

| env state                | returns                | warning?    |
|--------------------------|------------------------|-------------|
| canonical set            | canonical value        | none        |
| only legacy set          | legacy value           | exactly one |
| both set                 | canonical value        | none        |
| neither set              | default                | none        |
| legacy_name=None, no env | default                | none        |

Additional pins:

- The warning is a :class:`DeprecationWarning`.
- The warning message names BOTH the legacy and canonical names so
  operators can mechanically fix configuration.
- The warning is emitted with ``stacklevel=2`` so the reported
  filename is the caller's, not ``_env_aliases.py``.
"""

from __future__ import annotations

import warnings

import pytest

from juniper_config_tools import env_with_legacy_alias


class TestCanonicalEnvSet:
    """Behaviour when the canonical env var is set."""

    def test_returns_canonical_value(self, clean_env: pytest.MonkeyPatch) -> None:
        clean_env.setenv("JCT_TEST_NEW", "canonical-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        assert result == "canonical-value"
        assert caught == []

    def test_canonical_wins_when_both_set(self, clean_env: pytest.MonkeyPatch) -> None:
        clean_env.setenv("JCT_TEST_NEW", "canonical-value")
        clean_env.setenv("JCT_TEST_LEGACY", "legacy-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        assert result == "canonical-value"
        assert caught == []

    def test_canonical_empty_string_is_returned(self, clean_env: pytest.MonkeyPatch) -> None:
        """An empty string is a real value, not 'unset'. Must not fall through
        to the legacy alias."""
        clean_env.setenv("JCT_TEST_NEW", "")
        clean_env.setenv("JCT_TEST_LEGACY", "legacy-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        assert result == ""
        assert caught == []


class TestLegacyEnvSet:
    """Behaviour when only the legacy env var is set."""

    def test_returns_legacy_value(self, clean_env: pytest.MonkeyPatch) -> None:
        clean_env.setenv("JCT_TEST_LEGACY", "legacy-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        assert result == "legacy-value"
        deprecation = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation) == 1

    def test_warning_names_both_envvars(self, clean_env: pytest.MonkeyPatch) -> None:
        clean_env.setenv("JCT_TEST_LEGACY", "legacy-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        deprecation = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation) == 1
        message = str(deprecation[0].message)
        assert "JCT_TEST_LEGACY" in message, f"legacy name missing from warning: {message!r}"
        assert "JCT_TEST_NEW" in message, f"canonical name missing from warning: {message!r}"

    def test_warning_stacklevel_reports_caller_filename(self, clean_env: pytest.MonkeyPatch) -> None:
        """``stacklevel=2`` makes the warning report this test file's
        filename, not ``_env_aliases.py``."""
        clean_env.setenv("JCT_TEST_LEGACY", "legacy-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        deprecation = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation) == 1
        # The warning's filename must be THIS test file, not the helper's
        # implementation file. (Path may be absolute or relative; check
        # the basename.)
        filename = deprecation[0].filename
        assert filename.endswith("test_env_with_legacy_alias.py"), f"expected warning to be attributed to the test caller (stacklevel=2), got filename={filename!r}"

    def test_legacy_empty_string_is_returned(self, clean_env: pytest.MonkeyPatch) -> None:
        """An empty-string legacy value is still a real value; warn and return."""
        clean_env.setenv("JCT_TEST_LEGACY", "")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        assert result == ""
        deprecation = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation) == 1


class TestNeitherEnvSet:
    """Behaviour when neither env var is set — covers the default path."""

    def test_returns_none_when_no_default(self, clean_env: pytest.MonkeyPatch) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY")
        assert result is None
        assert caught == []

    def test_returns_explicit_default(self, clean_env: pytest.MonkeyPatch) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", "JCT_TEST_LEGACY", default="fallback")
        assert result == "fallback"
        assert caught == []


class TestLegacyNameNone:
    """Behaviour when ``legacy_name=None`` (canonical-only mode)."""

    def test_canonical_set_returns_value(self, clean_env: pytest.MonkeyPatch) -> None:
        clean_env.setenv("JCT_TEST_NEW", "canonical-value")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", None)
        assert result == "canonical-value"
        assert caught == []

    def test_canonical_unset_returns_default(self, clean_env: pytest.MonkeyPatch) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", None, default="d")
        assert result == "d"
        assert caught == []

    def test_legacy_in_env_ignored_when_legacy_name_is_none(self, clean_env: pytest.MonkeyPatch) -> None:
        """When ``legacy_name=None`` we explicitly disable the fallback;
        even if some env var with the same name happens to be set, the
        helper must not read it (the helper does not know what 'legacy'
        means without an explicit name)."""
        # JCT_TEST_LEGACY may be set but it's irrelevant because we
        # passed legacy_name=None.
        clean_env.setenv("JCT_TEST_LEGACY", "should-not-be-read")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = env_with_legacy_alias("JCT_TEST_NEW", None, default="d")
        assert result == "d"
        assert caught == []


class TestPublicSurface:
    """Sanity pins on what the package exports — the surface the
    cascor-worker CFG-06 PR consumes."""

    def test_env_with_legacy_alias_is_importable_from_top(self) -> None:
        from juniper_config_tools import env_with_legacy_alias as imported

        assert callable(imported)

    def test_version_string_is_importable(self) -> None:
        from juniper_config_tools import __version__

        assert isinstance(__version__, str)
        # Semver-ish — X.Y.Z, at minimum 3 numeric components.
        parts = __version__.split(".")
        assert len(parts) >= 3, f"__version__={__version__!r} is not X.Y.Z"
        for part in parts[:3]:
            head = part.split("-", 1)[0].split("+", 1)[0]
            assert head.isdigit(), f"version component {part!r} (from {__version__!r}) not numeric"


class TestModuleFormEntryPoint:
    """``python -m juniper_config_tools --version`` is the only CLI
    surface in 0.1.0 — keep it covered."""

    def test_version_flag_prints_version(self) -> None:
        from juniper_config_tools.__main__ import main

        # argparse exits with code 0 after printing --version; capture
        # via SystemExit so we can pin the exit code.
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_main_with_no_args_returns_zero(self) -> None:
        from juniper_config_tools.__main__ import main

        # No args = parse OK, no action, exit 0.
        result = main([])
        assert result == 0

    def test_module_form_via_subprocess(self) -> None:
        """End-to-end: ``python -m juniper_config_tools --version`` from
        a subprocess prints the version on stdout and exits 0."""
        import subprocess  # nosec B404 — hardcoded args, no untrusted input
        import sys

        proc = subprocess.run(  # nosec B603 — sys.executable + hardcoded args
            [sys.executable, "-m", "juniper_config_tools", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"

        from juniper_config_tools._version import __version__

        # argparse may write --version to stdout (3.10+) or stderr (older).
        combined = proc.stdout + proc.stderr
        assert __version__ in combined, f"version {__version__!r} not in output: {combined!r}"
