import json
from unittest.mock import patch

import pytest
from tests.taxii2.utils import (API_ROOTS_WITH_DEFAULT,
                                API_ROOTS_WITHOUT_DEFAULT, config_noop,
                                config_remove_fields)


@pytest.mark.parametrize(
    [
        "method",
        "headers",
        "config_override_func",
        "api_roots",
        "expected_status",
        "expected_headers",
        "expected_content",
    ],
    [
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            config_noop,
            API_ROOTS_WITH_DEFAULT,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "title": "Some TAXII Server",
                "description": "This TAXII Server contains a listing of...",
                "contact": "string containing contact information",
                "default": f"/taxii2/{API_ROOTS_WITH_DEFAULT[0].id}/",
                "api_roots": [f"/taxii2/{item.id}/" for item in API_ROOTS_WITH_DEFAULT],
            },
            id="good, with default api root",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            config_noop,
            API_ROOTS_WITHOUT_DEFAULT,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "title": "Some TAXII Server",
                "description": "This TAXII Server contains a listing of...",
                "contact": "string containing contact information",
                "api_roots": [f"/taxii2/{item.id}/" for item in API_ROOTS_WITHOUT_DEFAULT],
            },
            id="good, without default api root",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            config_noop,
            [],
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "title": "Some TAXII Server",
                "description": "This TAXII Server contains a listing of...",
                "contact": "string containing contact information",
                "api_roots": [],
            },
            id="good, no api roots configured",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            config_remove_fields("description", "contact"),
            [],
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "title": "Some TAXII Server",
                "api_roots": [],
            },
            id="good, no api roots and no description or contact",
        ),
        pytest.param(
            "get",
            {"Accept": "xml"},
            config_noop,
            [],
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
            config_noop,
            [],
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
def test_discovery(
    authenticated_client,
    method,
    headers,
    config_override_func,
    api_roots,
    expected_status,
    expected_headers,
    expected_content,
):
    config_defaults = {
        "title": "Some TAXII Server",
        "description": "This TAXII Server contains a listing of...",
        "contact": "string containing contact information",
    }
    with patch.object(
        authenticated_client.application.taxii_server.servers.taxii2,
        "config",
        config_override_func(
            {
                **authenticated_client.application.taxii_server.servers.taxii2.config,
                **config_defaults,
            }
        ),
    ), patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "get_api_roots",
        return_value=api_roots,
    ):
        func = getattr(authenticated_client, method)
        response = func("/taxii2/", headers=headers)
    assert response.status_code == expected_status
    assert {
        key: response.headers.get(key) for key in expected_headers
    } == expected_headers
    assert json.loads(response.data) == expected_content


@pytest.mark.parametrize("public_discovery", [True, False])
@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_discovery_unauthenticated(
    client,
    method,
    public_discovery,
):
    if public_discovery:
        if method == "get":
            expected_status_code = 200
        else:
            expected_status_code = 405
    else:
        if method == "get":
            expected_status_code = 401
        else:
            expected_status_code = 405
    with patch.object(
        client.application.taxii_server.servers.taxii2,
        "config",
        {
            **client.application.taxii_server.servers.taxii2.config,
            "title": "Some TAXII Server",
            "public_discovery": public_discovery,
        },
    ):
        func = getattr(client, method)
        response = func(
            "/taxii2/",
            headers={"Accept": "application/taxii+json;version=2.1"},
        )
    assert response.status_code == expected_status_code
