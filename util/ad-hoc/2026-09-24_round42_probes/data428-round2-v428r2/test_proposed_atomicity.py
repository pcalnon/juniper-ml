"""Proposed tests (validator): pin that the PATCH precondition is evaluated INSIDE the store lock."""

import pytest

from juniper_data.tests.unit.test_conditional_requests import _arrays, _create, _stored_meta, client, store  # noqa: F401  (fixtures)


@pytest.mark.unit
def test_the_store_evaluates_the_precondition_under_its_version_lock(store) -> None:  # noqa: F811
    store.save("guarded", _stored_meta("guarded"), _arrays())
    held: list[bool] = []

    def check(_current) -> bool:
        held.append(store._version_lock.locked())
        return True

    store.update_tags("guarded", ["b"], [], check)
    assert held == [True], "the precondition must run while update_tags holds its lock"


@pytest.mark.unit
def test_a_write_that_lands_between_the_read_and_the_patch_is_412(client, store, monkeypatch) -> None:  # noqa: F811
    dataset_id = _create(client)
    etag = client.get(f"/v1/datasets/{dataset_id}").headers["etag"]
    real = store.update_tags

    def racing(dsid, add, remove, precondition=None):
        real(dsid, ["concurrent"], [])  # another writer wins the race, after any route-level check
        return real(dsid, add, remove, precondition)

    monkeypatch.setattr(store, "update_tags", racing)
    response = client.patch(f"/v1/datasets/{dataset_id}/tags", json={"add_tags": ["mine"]}, headers={"If-Match": etag})
    assert response.status_code == 412
    assert "mine" not in store.get_meta(dataset_id).tags
