"""Proposed test (validator): the entity-tag list check must run in linear time."""

import time

import pytest

from juniper_data.api.http_cache import if_match_fails, if_none_match_hits, strong_etag


@pytest.mark.unit
@pytest.mark.parametrize("field", [", " * 40 + "x", ",   " * 40 + "x", " " * 8000 + "x", '"a", ' * 2000 + "x"])
def test_a_pathological_field_is_refused_in_linear_time(field: str) -> None:
    started = time.perf_counter()
    assert not if_none_match_hits(field, strong_etag("abc"))
    assert if_match_fails(field, strong_etag("abc"))
    assert time.perf_counter() - started < 0.5
