import json
import uuid
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import literal

from opentaxii.persistence.sqldb import taxii2models
from tests.taxii2.utils import (
    API_ROOTS,
    API_ROOTS_WITH_DEFAULT,
    GET_API_ROOT_MOCK,
    config_noop,
    config_override,
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
                "title": API_ROOTS[0].title,
                "description": API_ROOTS[0].description,
                "versions": ["application/taxii+json;version=2.1"],
                "max_content_length": 1024,
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
            {
                "title": API_ROOTS[1].title,
                "description": API_ROOTS[1].description,
                "versions": ["application/taxii+json;version=2.1"],
                "max_content_length": 1024,
            },
            id="good, second",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[2].id,
            config_noop,
            server_mapping_noop,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "title": API_ROOTS[2].title,
                "versions": ["application/taxii+json;version=2.1"],
                "max_content_length": 1024,
            },
            id="good, no description",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            config_override({"max_content_length": 1024000}),
            server_mapping_noop,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "title": API_ROOTS[0].title,
                "description": API_ROOTS[0].description,
                "versions": ["application/taxii+json;version=2.1"],
                "max_content_length": 1024000,
            },
            id="good, first, max_content_length override",
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
def test_api_root(
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
    with patch.object(
        authenticated_client.application.taxii_server.servers.taxii2,
        "config",
        config_override_func(
            authenticated_client.application.taxii_server.servers.taxii2.config
        ),
    ), patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "get_api_root",
        side_effect=GET_API_ROOT_MOCK,
    ), patch.object(
        authenticated_client.application.taxii_server,
        "servers",
        server_mapping_override_func(
            authenticated_client.application.taxii_server.servers
        ),
    ):
        func = getattr(authenticated_client, method)
        response = func(f"/taxii2/{api_root_id}/", headers=headers)
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
def test_api_root_unauthenticated(
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
    with patch.object(
        client.application.taxii_server.servers.taxii2.persistence.api,
        "get_api_root",
        side_effect=GET_API_ROOT_MOCK,
    ):
        func = getattr(client, method)
        response = func(
            f"/taxii2/{api_root_id}/",
            headers={"Accept": "application/taxii+json;version=2.1"},
        )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    ["title", "description", "default", "is_public", "api_root_id", "db_api_roots"],
    [
        pytest.param(
            "my new api root",  # title
            None,  # description
            False,  # default
            False,  # is_public
            None,  # api_root_id
            [],  # db_api_roots
            id="title only",
        ),
        pytest.param(
            "my new api root",  # title
            "my description",  # description
            False,  # default
            True,  # is_public
            None,  # api_root_id
            [],  # db_api_roots
            id="title, description",
        ),
        pytest.param(
            "my new api root",  # title
            None,  # description
            True,  # default
            False,  # is_public
            None,  # api_root_id
            [],  # db_api_roots
            id="title, default",
        ),
        pytest.param(
            "my new api root",  # title
            None,  # description
            False,  # default
            False,  # is_public
            "7468eafb-585d-402e-b6b9-49fe76492f9e",  # api_root_id
            [],  # db_api_roots
            id="title, id (str)",
        ),
        pytest.param(
            "my new api root",  # title
            None,  # description
            False,  # default
            False,  # is_public
            uuid.UUID("7468eafb-585d-402e-b6b9-49fe76492f9e"),  # api_root_id
            [],  # db_api_roots
            id="title, id (uuid)",
        ),
        pytest.param(
            "my new api root",  # title
            "my description",  # description
            True,  # default
            True,  # is_public
            None,  # api_root_id
            API_ROOTS_WITH_DEFAULT,  # db_api_roots
            id="title, description, default, existing",
        ),
    ],
    indirect=["db_api_roots"],
)
def test_add_api_root(
    app, title, description, default, is_public, api_root_id, db_api_roots
):
    api_root = app.taxii_server.servers.taxii2.persistence.api.add_api_root(
        title, description, default, is_public, api_root_id
    )
    if api_root_id:
        assert str(api_root.id) == str(api_root_id)
    else:
        assert api_root.id is not None
    assert api_root.title == title
    assert api_root.description == description
    assert api_root.default == default
    assert api_root.is_public == is_public
    db_api_root = (
        app.taxii_server.servers.taxii2.persistence.api.db.session.query(
            taxii2models.ApiRoot
        )
        .filter(taxii2models.ApiRoot.id == api_root.id)
        .one()
    )
    assert db_api_root.title == title
    assert db_api_root.description == description
    assert db_api_root.default == default
    assert db_api_root.is_public == is_public
    if default:
        assert (
            app.taxii_server.servers.taxii2.persistence.api.db.session.query(
                taxii2models.ApiRoot
            )
            .filter(taxii2models.ApiRoot.default == literal(True))
            .count()
        ) == 1
