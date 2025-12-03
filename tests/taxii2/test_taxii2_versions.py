import datetime
import json
from unittest.mock import patch
from urllib.parse import urlencode
from uuid import uuid4

import pytest
from opentaxii.taxii2.utils import taxii2_datetimeformat
from tests.taxii2.utils import (
    API_ROOTS,
    COLLECTIONS,
    GET_COLLECTION_MOCK,
    GET_NEXT_PARAM,
    GET_VERSIONS_MOCK,
    NOW,
    STIX_OBJECTS,
)


@pytest.mark.parametrize(
    [
        "method",
        "headers",
        "api_root_id",
        "collection_id",
        "object_id",
        "filter_kwargs",
        "expected_status",
        "expected_headers",
        "expected_content",
    ],
    [
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
            },
            {
                "more": False,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[0].version),
                    taxii2_datetimeformat(STIX_OBJECTS[2].version),
                ],
            },
            id="good",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"added_after": taxii2_datetimeformat(NOW)},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
            },
            {
                "more": False,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[2].version),
                ],
            },
            id="good, added_after",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"added_after": taxii2_datetimeformat(NOW).replace("Z", "+00:00")},
            400,
            {
                "Content-Type": "application/taxii+json;version=2.1",
            },
            {
                "code": 400,
                "description": {"added_after": ["Not a valid datetime."]},
                "name": "validation error",
            },
            id="broken added_after",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"limit": 1},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": True,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[0].version),
                ],
            },
            id="good, limit",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"limit": 2},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
            },
            {
                "more": False,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[0].version),
                    taxii2_datetimeformat(STIX_OBJECTS[2].version),
                ],
            },
            id="good, limit exact",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"limit": 999},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
            },
            {
                "more": False,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[0].version),
                    taxii2_datetimeformat(STIX_OBJECTS[2].version),
                ],
            },
            id="good, limit high",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"limit": "a"},
            400,
            {
                "Content-Type": "application/taxii+json;version=2.1",
            },
            {
                "code": 400,
                "description": {"limit": ["Not a valid integer."]},
                "name": "validation error",
            },
            id="broken limit",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {
                "next": GET_NEXT_PARAM(
                    {"id": STIX_OBJECTS[0].id, "date_added": STIX_OBJECTS[0].date_added}
                )
            },
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
            },
            {
                "more": False,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[2].version),
                ],
            },
            id="good, next",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"next": "a"},
            400,
            {
                "Content-Type": "application/taxii+json;version=2.1",
            },
            {
                "code": 400,
                "description": {"next": ["Not a valid value."]},
                "name": "validation error",
            },
            id="broken next",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {"match[spec_version]": STIX_OBJECTS[0].spec_version},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": False,
                "versions": [
                    taxii2_datetimeformat(STIX_OBJECTS[0].version),
                ],
            },
            id="good, spec_version",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[1].id,
            STIX_OBJECTS[2].id,
            {},
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="write-only collection",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[1].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {},
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
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {},
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
            STIX_OBJECTS[0].id,
            {},
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
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            str(uuid4()),
            {},
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="unknown object",
        ),
        pytest.param(
            "get",
            {"Accept": "xml"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {},
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
            COLLECTIONS[5].id,
            STIX_OBJECTS[0].id,
            {},
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
def test_versions(
    authenticated_client,
    method,
    api_root_id,
    collection_id,
    object_id,
    filter_kwargs,
    headers,
    expected_status,
    expected_headers,
    expected_content,
):
    with (
        patch.object(
            authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
            "get_versions",
            side_effect=GET_VERSIONS_MOCK,
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
                COLLECTIONS[5].id: ["write", "read"],
            },
        ),
    ):
        func = getattr(authenticated_client, method)
        if filter_kwargs:
            querystring = f"?{urlencode(filter_kwargs)}"
        else:
            querystring = ""
        kwargs = {"headers": headers}
        response = func(
            f"/taxii2/{api_root_id}/collections/{collection_id}/objects/{object_id}/versions/{querystring}",
            **kwargs,
        )
    assert response.status_code == expected_status
    assert {
        key: response.headers.get(key) for key in expected_headers
    } == expected_headers
    if (
        response.headers.get("Content-Type", "application/taxii+json;version=2.1")
        == "application/taxii+json;version=2.1"
    ) and response.data != b"":
        content = json.loads(response.data)
    else:
        content = response.data
    assert content == expected_content


@pytest.mark.parametrize("is_public", [True, False])
@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_versions_unauthenticated(
    client,
    method,
    is_public,
):
    if is_public:
        collection_id = COLLECTIONS[6].id
        stix_id = STIX_OBJECTS[4].id
        if method == "get":
            expected_status_code = 200
        else:
            expected_status_code = 405
    else:
        collection_id = COLLECTIONS[0].id
        stix_id = STIX_OBJECTS[0].id
        if method == "get":
            expected_status_code = 401
        else:
            expected_status_code = 405
    with (
        patch.object(
            client.application.taxii_server.servers.taxii2.persistence.api,
            "get_versions",
            side_effect=GET_VERSIONS_MOCK,
        ),
        patch.object(
            client.application.taxii_server.servers.taxii2.persistence.api,
            "get_collection",
            side_effect=GET_COLLECTION_MOCK,
        ),
    ):
        func = getattr(client, method)
        response = func(
            f"/taxii2/{API_ROOTS[0].id}/collections/{collection_id}/objects/{stix_id}/versions/",
            headers={"Accept": "application/taxii+json;version=2.1"},
        )
    assert response.status_code == expected_status_code
