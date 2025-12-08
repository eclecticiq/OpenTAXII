import json
import uuid
from unittest.mock import patch
from uuid import uuid4

import pytest

from opentaxii.entities import Account
from opentaxii.persistence.sqldb import taxii2models
from opentaxii.taxii2.entities import Collection
from tests.taxii2.utils import (
    API_ROOTS,
    COLLECTIONS,
    GET_API_ROOT_MOCK,
    GET_COLLECTION_MOCK,
)


@pytest.mark.parametrize(
    "method,headers,api_root_id,collection_id,expected_status,expected_headers,expected_content",
    [
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[0].id,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "id": str(COLLECTIONS[0].id),
                "title": "0Read only",
                "description": "Read only description",
                "can_read": True,
                "can_write": False,
                "media_types": ["application/stix+json;version=2.1"],
            },
            id="good",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[4].id,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "id": str(COLLECTIONS[4].id),
                "title": "4No description",
                "can_read": True,
                "can_write": True,
                "media_types": ["application/stix+json;version=2.1"],
            },
            id="good, no description",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "id": str(COLLECTIONS[5].id),
                "title": "5With alias",
                "description": "With alias description",
                "alias": "this-is-an-alias",
                "can_read": False,
                "can_write": True,
                "media_types": ["application/stix+json;version=2.1"],
            },
            id="good, with description",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].alias,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "id": str(COLLECTIONS[5].id),
                "title": "5With alias",
                "description": "With alias description",
                "alias": "this-is-an-alias",
                "can_read": False,
                "can_write": True,
                "media_types": ["application/stix+json;version=2.1"],
            },
            id="good, by alias",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[1].id,
            COLLECTIONS[0].id,
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="wrong api root",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            str(uuid4()),
            COLLECTIONS[0].id,
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="unknown api root",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            str(uuid4()),
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="unknown collection",
        ),
        pytest.param(
            "get",
            {"Accept": "xml"},
            API_ROOTS[0].id,
            COLLECTIONS[0].id,
            406,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 406,
                "name": "Not Acceptable",
                "description": (
                    "The resource identified by the request is only capable of generating response entities which"
                    " have content characteristics not acceptable according to the accept headers sent in the"
                    " request."
                ),
            },
            id="wrong accept header",
        ),
        pytest.param(
            "post",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[0].id,
            405,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 405,
                "description": "The method is not allowed for the requested URL.",
                "name": "Method Not Allowed",
            },
            id="wrong method",
        ),
    ],
)
def test_collection(
    authenticated_client,
    method,
    api_root_id,
    collection_id,
    headers,
    expected_status,
    expected_headers,
    expected_content,
):
    with (
        patch.object(
            authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
            "get_api_root",
            side_effect=GET_API_ROOT_MOCK,
        ),
        patch.object(
            authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
            "get_collection",
            side_effect=GET_COLLECTION_MOCK,
        ),
        patch.object(
            authenticated_client.account,
            "permissions",
            {
                COLLECTIONS[0].id: ["read"],
                COLLECTIONS[1].id: ["write"],
                COLLECTIONS[2].id: ["read", "write"],
                COLLECTIONS[4].id: ["read", "write"],
                COLLECTIONS[5].id: ["write"],
            },
        ),
    ):
        func = getattr(authenticated_client, method)
        response = func(
            f"/taxii2/{api_root_id}/collections/{collection_id}/", headers=headers
        )
    assert response.status_code == expected_status
    assert {
        key: response.headers.get(key) for key in expected_headers
    } == expected_headers
    if (
        response.headers.get("Content-Type", "application/taxii+json;version=2.1")
        == "application/taxii+json;version=2.1"
    ):
        content = json.loads(response.data)
    else:
        content = response.data
    assert content == expected_content


@pytest.mark.parametrize("is_public", [True, False])
@pytest.mark.parametrize("is_public_write", [True, False])
@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_collection_unauthenticated(
    client,
    method,
    is_public,
    is_public_write,
):
    if is_public:
        collection_id = COLLECTIONS[6].id
        if method == "get":
            expected_status_code = 200
        else:
            expected_status_code = 405
    elif is_public_write:
        collection_id = COLLECTIONS[7].id
        if method == "get":
            expected_status_code = 200
        else:
            expected_status_code = 405
    else:
        collection_id = COLLECTIONS[0].id
        if method == "get":
            expected_status_code = 401
        else:
            expected_status_code = 405
    with (
        patch.object(
            client.application.taxii_server.servers.taxii2.persistence.api,
            "get_api_root",
            side_effect=GET_API_ROOT_MOCK,
        ),
        patch.object(
            client.application.taxii_server.servers.taxii2.persistence.api,
            "get_collection",
            side_effect=GET_COLLECTION_MOCK,
        ),
    ):
        func = getattr(client, method)
        response = func(
            f"/taxii2/{API_ROOTS[0].id}/collections/{collection_id}/",
            headers={"Accept": "application/taxii+json;version=2.1"},
        )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    ["api_root_id", "title", "description", "alias", "is_public", "is_public_write"],
    [
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            "my new collection",  # title
            None,  # description
            None,  # alias
            False,  # is_public
            False,  # is_public_write
            id="api_root_id, title",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            "my new collection",  # title
            "my description",  # description
            None,  # alias
            True,  # is_public
            False,  # is_public_write
            id="api_root_id, title, description",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            "my new collection",  # title
            "my description",  # description
            "my-alias",  # alias
            False,  # is_public
            True,  # is_public_write
            id="api_root_id, title, description, alias",
        ),
    ],
)
def test_add_collection(
    app,
    api_root_id,
    title,
    description,
    alias,
    is_public,
    is_public_write,
    db_api_roots,
    db_collections,
):
    collection = app.taxii_server.servers.taxii2.persistence.api.add_collection(
        api_root_id=api_root_id,
        title=title,
        description=description,
        alias=alias,
        is_public=is_public,
        is_public_write=is_public_write,
    )
    assert collection.id is not None
    assert collection.api_root_id == api_root_id
    assert collection.title == title
    assert collection.description == description
    assert collection.alias == alias
    assert collection.is_public == is_public
    assert collection.is_public_write == is_public_write
    db_collection = (
        app.taxii_server.servers.taxii2.persistence.api.db.session.query(
            taxii2models.Collection
        )
        .filter(taxii2models.Collection.id == collection.id)
        .one()
    )
    assert db_collection.api_root_id == api_root_id
    assert db_collection.title == title
    assert db_collection.description == description
    assert db_collection.alias == alias
    assert db_collection.is_public == is_public
    assert db_collection.is_public_write == is_public_write


def test_collection_can_read():
    collection = Collection(
        id=uuid.UUID("f74bf902-0b63-4c76-9bed-aecb120b084d"),
        api_root_id=uuid.UUID("fe6489a0-26eb-4810-8efc-ad5a46d85a35"),
        title="test",
        description="test",
        alias=None,
        is_public=False,
        is_public_write=False,
    )

    # Without account
    assert collection.can_read(None) is False
    # With account
    assert collection.can_read(Account("admin", "admin", {}, is_admin=True)) is True
    assert (
        collection.can_read(Account("inaccessible", "inaccessible", {}, is_admin=False))
        is False
    )
    assert (
        collection.can_read(
            Account("read_only", "read_only", {collection.id: "read"}, is_admin=False)
        )
        is True
    )
    assert (
        collection.can_read(
            Account(
                "write_access",
                "write_access",
                {collection.id: "modify"},
                is_admin=False,
            )
        )
        is True
    )

    # Public
    collection.is_public_write = True
    assert collection.can_read(None) is False
    collection.is_public = True
    assert collection.can_read(None) is True


def test_collection_can_write():
    collection = Collection(
        id=uuid.UUID("f74bf902-0b63-4c76-9bed-aecb120b084d"),
        api_root_id=uuid.UUID("fe6489a0-26eb-4810-8efc-ad5a46d85a35"),
        title="test",
        description="test",
        alias=None,
        is_public=False,
        is_public_write=False,
    )

    # Without account
    assert collection.can_write(None) is False
    # With account
    assert collection.can_write(Account("admin", "admin", {}, is_admin=True)) is True
    assert (
        collection.can_write(
            Account("inaccessible", "inaccessible", {}, is_admin=False)
        )
        is False
    )
    assert (
        collection.can_write(
            Account("read_only", "read_only", {collection.id: "read"}, is_admin=False)
        )
        is False
    )
    assert (
        collection.can_write(
            Account(
                "write_access",
                "write_access",
                {collection.id: "modify"},
                is_admin=False,
            )
        )
        is True
    )

    # Public
    collection.is_public = True
    assert collection.can_write(None) is False
    collection.is_public_write = True
    assert collection.can_write(None) is True
