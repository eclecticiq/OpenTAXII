import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from opentaxii.persistence.sqldb import taxii2models
from opentaxii.taxii2.utils import taxii2_datetimeformat
from tests.taxii2.utils import (API_ROOTS, GET_JOB_AND_DETAILS_MOCK, JOBS,
                                config_noop, server_mapping_noop,
                                server_mapping_remove_fields)


@pytest.mark.parametrize(
    [
        "method",
        "headers",
        "api_root_id",
        "job_id",
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
            JOBS[0].id,
            config_noop,
            server_mapping_noop,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "id": JOBS[0].id,
                "status": JOBS[0].status,
                "request_timestamp": taxii2_datetimeformat(JOBS[0].request_timestamp),
                "total_count": 4,
                "success_count": 1,
                "successes": [
                    {
                        "id": "indicator--c410e480-e42b-47d1-9476-85307c12bcbf",
                        "version": "2018-05-27T12:02:41.312000Z",
                    }
                ],
                "failure_count": 1,
                "failures": [
                    {
                        "id": "malware--664fa29d-bf65-4f28-a667-bdb76f29ec98",
                        "version": "2018-05-28T14:03:42.543000Z",
                        "message": "Unable to process object",
                    }
                ],
                "pending_count": 2,
                "pendings": [
                    {
                        "id": "indicator--252c7c11-daf2-42bd-843b-be65edca9f61",
                        "version": "2018-05-18T20:16:21.148000Z",
                    },
                    {
                        "id": "relationship--045585ad-a22f-4333-af33-bfd503a683b5",
                        "version": "2018-05-15T10:13:32.579000Z",
                    },
                ],
            },
            id="good, first, first",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[1].id,
            JOBS[3].id,
            config_noop,
            server_mapping_noop,
            200,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "id": JOBS[3].id,
                "status": JOBS[3].status,
                "request_timestamp": taxii2_datetimeformat(JOBS[3].request_timestamp),
                "total_count": 0,
                "success_count": 0,
                "successes": [],
                "failure_count": 0,
                "failures": [],
                "pending_count": 0,
                "pendings": [],
            },
            id="good, second, second",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            JOBS[3].id,
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
            id="wrong api id",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
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
            id="unknown job id, taxii2 only config",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
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
            id="unknown job id, taxii1/2 config",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            str(uuid4()),
            JOBS[0].id,
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
            JOBS[0].id,
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
            JOBS[0].id,
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
            JOBS[0].id,
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
def test_status(
    authenticated_client,
    method,
    api_root_id,
    job_id,
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
        "get_api_roots",
        return_value=API_ROOTS,
    ), patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "get_job_and_details",
        side_effect=GET_JOB_AND_DETAILS_MOCK,
    ), patch.object(
        authenticated_client.application.taxii_server,
        "servers",
        server_mapping_override_func(
            authenticated_client.application.taxii_server.servers
        ),
    ):
        func = getattr(authenticated_client, method)
        response = func(f"/{api_root_id}/status/{job_id}/", headers=headers)
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


@pytest.mark.parametrize("method", ["get", "post", "delete"])
def test_status_unauthenticated(
    client,
    method,
):
    func = getattr(client, method)
    response = func(f"/{API_ROOTS[0].id}/status/{JOBS[0].id}/")
    assert response.status_code == 401


def test_job_cleanup(app, db_jobs):
    number_removed = app.taxii_server.servers.taxii2.persistence.api.job_cleanup()
    assert number_removed == 3
    assert (
        app.taxii_server.servers.taxii2.persistence.api.db.session.query(
            taxii2models.Job
        ).count()
        == 3
    )
