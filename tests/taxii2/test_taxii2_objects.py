import datetime
import json
from unittest.mock import patch
from urllib.parse import urlencode
from uuid import uuid4

import pytest
from opentaxii.taxii2.utils import taxii2_datetimeformat
from tests.taxii2.utils import (ADD_OBJECTS_MOCK, API_ROOTS, COLLECTIONS,
                                GET_COLLECTION_MOCK, GET_JOB_AND_DETAILS_MOCK,
                                GET_NEXT_PARAM, GET_OBJECTS_MOCK, JOBS, NOW,
                                STIX_OBJECTS)


@pytest.mark.parametrize(
    [
        "method",
        "headers",
        "api_root_id",
        "collection_id",
        "filter_kwargs",
        "post_data",
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
            {},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].alias,
            {},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, by alias",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"added_after": taxii2_datetimeformat(NOW)},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[1:2]
                ],
            },
            id="good, added_after",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"added_after": taxii2_datetimeformat(NOW + datetime.timedelta(seconds=3))},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
            },
            {},
            id="good, no results",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"added_after": taxii2_datetimeformat(NOW).replace("Z", "+00:00")},
            {},
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
            {"limit": 1},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": True,
                "next": GET_NEXT_PARAM(
                    {"id": STIX_OBJECTS[0].id, "date_added": STIX_OBJECTS[0].date_added}
                ),
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:1]
                ],
            },
            id="good, limit",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"limit": 2},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, limit exact",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"limit": 999},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, limit high",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"limit": "a"},
            {},
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
            {
                "next": GET_NEXT_PARAM(
                    {"id": STIX_OBJECTS[0].id, "date_added": STIX_OBJECTS[0].date_added}
                )
            },
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[1:2]
                ],
            },
            id="good, next",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"next": "a"},
            {},
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
            {"match[id]": STIX_OBJECTS[0].id},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in [STIX_OBJECTS[0]]
                ],
            },
            id="good, id",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[id]": ",".join([obj.id for obj in STIX_OBJECTS[:3]])},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, ids",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[type]": STIX_OBJECTS[0].type},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in [STIX_OBJECTS[0]]
                ],
            },
            id="good, type",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[type]": ",".join([obj.type for obj in STIX_OBJECTS[:3]])},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, types",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[version]": taxii2_datetimeformat(STIX_OBJECTS[0].version)},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:1]
                ],
            },
            id="good, version",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[version]": "last"},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, version last",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[version]": "first"},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=3)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[1:3]
                ],
            },
            id="good, version first",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[version]": "all"},
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
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:3]
                ],
            },
            id="good, version all",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {
                "match[version]": ",".join(
                    [taxii2_datetimeformat(obj.version) for obj in STIX_OBJECTS[:3]]
                )
            },
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
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:3]
                ],
            },
            id="good, versions",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {"match[spec_version]": STIX_OBJECTS[0].spec_version},
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(NOW),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:1]
                ],
            },
            id="good, spec_version",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {
                "match[spec_version]": ",".join(
                    [obj.spec_version for obj in STIX_OBJECTS[:3]]
                )
            },
            {},
            200,
            {
                "Content-Type": "application/taxii+json;version=2.1",
                "X-TAXII-Date-Added-First": taxii2_datetimeformat(NOW),
                "X-TAXII-Date-Added-Last": taxii2_datetimeformat(
                    NOW + datetime.timedelta(seconds=2)
                ),
            },
            {
                "more": False,
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.type,
                        "spec_version": obj.type,
                        **obj.serialized_data,
                    }
                    for obj in STIX_OBJECTS[:2]
                ],
            },
            id="good, spec_versions",
        ),
        pytest.param(
            "get",
            {"Accept": "application/taxii+json;version=2.1"},
            API_ROOTS[0].id,
            COLLECTIONS[1].id,
            {},
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
            {},
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
            {},
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
            {},
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
            {"Accept": "xml"},
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
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
            {
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "application/taxii+json;version=2.1",
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
            {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy",
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            },
            202,
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
            id="post, good",
        ),
        pytest.param(
            "post",
            {
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "application/taxii+json;version=2.1",
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
            {},
            400,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 400,
                "description": ["No objects"],
                "name": "validation error",
            },
            id="post, missing data",
        ),
        pytest.param(
            "post",
            {
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "application/taxii+json;version=2.1",
            },
            API_ROOTS[0].id,
            COLLECTIONS[0].id,
            {},
            {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy",
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            },
            404,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 404,
                "description": "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again.",
                "name": "Not Found",
            },
            id="post, read-only collection",
        ),
        pytest.param(
            "post",
            {
                "Accept": "xml",
                "Content-Type": "application/taxii+json;version=2.1",
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
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
            id="post, wrong accept header",
        ),
        pytest.param(
            "post",
            {
                "Accept": "application/taxii+json;version=2.1",
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
            {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy",
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            },
            415,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 415,
                "description": (
                    "The server does not support the media type transmitted in the "
                    "request."
                ),
                "name": "Unsupported Media Type",
            },
            id="post, missing content-type header",
        ),
        pytest.param(
            "post",
            {
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "xml",
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
            {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy",
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            },
            415,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 415,
                "description": (
                    "The server does not support the media type transmitted in the "
                    "request."
                ),
                "name": "Unsupported Media Type",
            },
            id="post, wrong content-type header",
        ),
        pytest.param(
            "post",
            {
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "application/taxii+json;version=2.1",
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
            {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy" * 33,
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            },
            413,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 413,
                "description": "The data value transmitted exceeds the capacity limit.",
                "name": "Request Entity Too Large",
            },
            id="post, too big",
        ),
        pytest.param(
            "post",
            {
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "application/taxii+json;version=2.1",
                "Content-Length": 1,
            },
            API_ROOTS[0].id,
            COLLECTIONS[5].id,
            {},
            {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy" * 33,
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            },
            413,
            {"Content-Type": "application/taxii+json;version=2.1"},
            {
                "code": 413,
                "description": "The data value transmitted exceeds the capacity limit.",
                "name": "Request Entity Too Large",
            },
            id="post, too big, fake content-length",
        ),
    ],
)
def test_objects(
    authenticated_client,
    method,
    api_root_id,
    collection_id,
    filter_kwargs,
    post_data,
    headers,
    expected_status,
    expected_headers,
    expected_content,
):
    with patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "get_objects",
        side_effect=GET_OBJECTS_MOCK,
    ), patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "get_collection",
        side_effect=GET_COLLECTION_MOCK,
    ), patch.object(
        authenticated_client.account,
        "permissions",
        {
            COLLECTIONS[0].id: ["read"],
            COLLECTIONS[1].id: ["write"],
            COLLECTIONS[2].id: ["read", "write"],
            COLLECTIONS[4].id: ["read", "write"],
            COLLECTIONS[5].id: ["write", "read"],
        },
    ), patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "add_objects",
        side_effect=ADD_OBJECTS_MOCK,
    ) as add_objects_mock, patch.object(
        authenticated_client.application.taxii_server.servers.taxii2.persistence.api,
        "get_job_and_details",
        side_effect=GET_JOB_AND_DETAILS_MOCK,
    ):
        func = getattr(authenticated_client, method)
        if filter_kwargs:
            querystring = f"?{urlencode(filter_kwargs)}"
        else:
            querystring = ""
        kwargs = {"headers": headers}
        if method == "post":
            kwargs["json"] = post_data
        response = func(
            f"/{api_root_id}/collections/{collection_id}/objects/{querystring}",
            **kwargs,
        )
    assert response.status_code == expected_status
    if method == "post" and expected_status == 202:
        add_objects_mock.assert_called_once_with(
            api_root_id=API_ROOTS[0].id,
            collection_id=COLLECTIONS[5].id,
            objects=post_data["objects"],
        )
    else:
        add_objects_mock.assert_not_called()
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
def test_objects_unauthenticated(
    client,
    method,
    is_public,
):
    if is_public:
        collection_id = COLLECTIONS[6].id
        if method == "get":
            expected_status_code = 200
        elif method == "post":
            expected_status_code = 401
        else:
            expected_status_code = 405
    else:
        collection_id = COLLECTIONS[0].id
        if method == "get":
            expected_status_code = 401
        elif method == "post":
            expected_status_code = 401
        else:
            expected_status_code = 405
    with patch.object(
        client.application.taxii_server.servers.taxii2.persistence.api,
        "get_objects",
        side_effect=GET_OBJECTS_MOCK,
    ), patch.object(
        client.application.taxii_server.servers.taxii2.persistence.api,
        "get_collection",
        side_effect=GET_COLLECTION_MOCK,
    ):
        kwargs = {
            'headers':{
                "Accept": "application/taxii+json;version=2.1",
                "Content-Type": "application/taxii+json;version=2.1",
            }
        }
        if method == "post":
            kwargs["json"] = {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                        "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                        "created": "2016-04-06T20:03:48.000Z",
                        "modified": "2016-04-06T20:03:48.000Z",
                        "indicator_types": ["malicious-activity"],
                        "name": "Poison Ivy Malware",
                        "description": "This file is part of Poison Ivy",
                        "pattern": "[ file:hashes.'SHA-256' = "
                        "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                        "pattern_type": "stix",
                        "valid_from": "2016-01-01T00:00:00Z",
                    }
                ]
            }
        func = getattr(client, method)
        response = func(
            f"/{API_ROOTS[0].id}/collections/{collection_id}/objects/",
            **kwargs,
        )
    assert response.status_code == expected_status_code
