import json
from unittest.mock import patch
from uuid import uuid4

import pytest

from tests.taxii2.utils import (
    API_ROOTS,
    COLLECTIONS,
    GET_API_ROOT_MOCK,
    GET_COLLECTIONS_MOCK,
    config_noop,
    server_mapping_noop,
    server_mapping_remove_fields,
)


@pytest.mark.parametrize(
    [
        "method",
        "headers",
        "api_root_id",
        "config_override_func",
        "server_mapping_override_func",
        "expected_status",
        "expected_headers",
        "expected_content",
    ],
    [
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            config_noop,
            server_mapping_noop,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "collections": [
                    {
                        "id": str(COLLECTIONS[0].id),
                        "title": "0Read only",
                        "description": "Read only description",
                        "can_read": True,
                        "can_write": False,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[1].id),
                        "title": "1Write only",
                        "description": "Write only description",
                        "can_read": False,
                        "can_write": True,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[2].id),
                        "title": "2Read/Write",
                        "description": "Read/Write description",
                        "can_read": True,
                        "can_write": True,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[3].id),
                        "title": "3No permissions",
                        "description": "No permissions description",
                        "can_read": False,
                        "can_write": False,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[4].id),
                        "title": "4No description",
                        "can_read": True,
                        "can_write": True,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[5].id),
                        "title": "5With alias",
                        "description": "With alias description",
                        "alias": "this-is-an-alias",
                        "can_read": False,
                        "can_write": True,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[6].id),
                        "title": "6Public",
                        "description": "public description",
                        "can_read": True,
                        "can_write": False,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                    {
                        "id": str(COLLECTIONS[7].id),
                        "title": "7Publicwrite",
                        "description": "public write description",
                        "can_read": False,
                        "can_write": True,
                        "media_types": ["application/stix+json;version=2.1"],
                    },
                ]
            },
            id="good, first",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[1].id,
            config_noop,
            server_mapping_noop,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {},
            id="good, second (no collections)",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            str(uuid4()),
            config_noop,
            server_mapping_remove_fields("taxii1"),
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="unknown api root, taxii2 only config",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            str(uuid4()),
            config_noop,
            server_mapping_noop,
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="unknown api root, taxii1/2 config",
        ),
        pytest.param(
            "get",
            {"Accept": "xml"},
            API_ROOTS[0].id,
            config_noop,
            server_mapping_noop,
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
            config_noop,
            server_mapping_noop,
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
def test_collections(
    authenticated_client,
    method,
    api_root_id,
    headers,
    config_override_func,
    server_mapping_override_func,
    expected_status,
    expected_headers,
    expected_content,
):
    with (
        patch.object(
            authenticated_client.application.taxii_server.servers.taxii2,
            "config",
            config_override_func(
                authenticated_client.application.taxii_server.servers.taxii2.config
            ),
        ),
        patch.object(
            authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
            "get_api_root",
            side_effect=GET_API_ROOT_MOCK,
        ),
        patch.object(
            authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
            "get_collections",
            side_effect=GET_COLLECTIONS_MOCK,
        ),
        patch.object(
            authenticated_client.application.taxii_server,
            "servers",
            server_mapping_override_func(
                authenticated_client.application.taxii_server.servers
            ),
        ),
        patch.object(
            authenticated_client.account,
            "permissions",
            {
                str(COLLECTIONS[0].id): ["read"],
                str(COLLECTIONS[1].id): ["write"],
                str(COLLECTIONS[2].id): ["read", "write"],
                str(COLLECTIONS[4].id): ["read", "write"],
                str(COLLECTIONS[5].id): ["write"],
            },
        ),
    ):
        func = getattr(authenticated_client, method)
        response = func(f"/taxii2/{api_root_id}/collections/", headers=headers)
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
@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_collections_unauthenticated(
    client,
    method,
    is_public,
):
    if is_public:
        api_root_id = API_ROOTS[1].id
        if method == "get":
            expected_status_code = 200
        else:
            expected_status_code = 405
    else:
        api_root_id = API_ROOTS[0].id
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
            "get_collections",
            side_effect=GET_COLLECTIONS_MOCK,
        ),
    ):
        func = getattr(client, method)
        response = func(
            f"/taxii2/{api_root_id}/collections/",
            headers={"Accept": "application/taxii+json;version=2.1"},
        )
    assert response.status_code == expected_status_code
