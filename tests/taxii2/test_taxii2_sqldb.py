import datetime
from uuid import uuid4

import pytest
from opentaxii.persistence.sqldb.taxii2models import Job, JobDetail, STIXObject
from opentaxii.taxii2 import entities
from opentaxii.taxii2.utils import DATETIMEFORMAT
from tests.taxii2.utils import (
    API_ROOTS,
    API_ROOTS_WITH_DEFAULT,
    API_ROOTS_WITHOUT_DEFAULT,
    COLLECTIONS,
    GET_API_ROOT_MOCK,
    GET_COLLECTION_MOCK,
    GET_COLLECTIONS_MOCK,
    GET_JOB_AND_DETAILS_MOCK,
    GET_MANIFEST_MOCK,
    GET_OBJECT_MOCK,
    GET_OBJECTS_MOCK,
    GET_VERSIONS_MOCK,
    JOBS,
    NOW,
    STIX_OBJECTS,
)


@pytest.mark.parametrize(
    ["db_api_roots"],
    [
        pytest.param(
            API_ROOTS_WITHOUT_DEFAULT,  # db_api_roots
            id="without default",
        ),
        pytest.param(
            API_ROOTS_WITH_DEFAULT,  # db_api_roots
            id="with default",
        ),
    ],
    indirect=["db_api_roots"],
)
def test_get_api_roots(taxii2_sqldb_api, db_api_roots):
    response = taxii2_sqldb_api.get_api_roots()
    assert response == [api_root for api_root in db_api_roots]


@pytest.mark.parametrize(
    ["api_root_id"],
    [
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            id="first",
        ),
        pytest.param(
            API_ROOTS[1].id,  # api_root_id
            id="second",
        ),
        pytest.param(
            str(uuid4()),  # api_root_id
            id="unknown",
        ),
    ],
)
def test_get_api_root(taxii2_sqldb_api, db_api_roots, api_root_id):
    response = taxii2_sqldb_api.get_api_root(api_root_id)
    assert response == GET_API_ROOT_MOCK(api_root_id)


@pytest.mark.parametrize(
    ["api_root_id", "job_id"],
    [
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            JOBS[0].id,  # job_id
            id="first",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            JOBS[1].id,  # job_id
            id="second",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            JOBS[2].id,  # job_id
            id="wrong api root",
        ),
        pytest.param(
            str(uuid4()),  # api_root_id
            JOBS[0].id,  # job_id
            id="unknown api root",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            str(uuid4()),  # job_id
            id="unknown job id",
        ),
    ],
)
def test_get_job_and_details(taxii2_sqldb_api, db_jobs, api_root_id, job_id):
    response = taxii2_sqldb_api.get_job_and_details(api_root_id, job_id)
    assert response == GET_JOB_AND_DETAILS_MOCK(api_root_id, job_id)


@pytest.mark.parametrize(
    ["api_root_id"],
    [
        pytest.param(
            API_ROOTS[0].id,
            id="first",
        ),
        pytest.param(
            API_ROOTS[1].id,
            id="second",
        ),
        pytest.param(
            str(uuid4()),
            id="unknown",
        ),
    ],
)
def test_get_collections(taxii2_sqldb_api, db_collections, api_root_id):
    response = taxii2_sqldb_api.get_collections(api_root_id)
    assert response == GET_COLLECTIONS_MOCK(api_root_id)


@pytest.mark.parametrize(
    ["api_root_id", "collection_id_or_alias"],
    [
        pytest.param(
            API_ROOTS[0].id,
            COLLECTIONS[0].id,
            id="first",
        ),
        pytest.param(
            API_ROOTS[0].id,
            COLLECTIONS[1].id,
            id="second",
        ),
        pytest.param(
            API_ROOTS[0].id,
            COLLECTIONS[5].alias,
            id="alias",
        ),
        pytest.param(
            API_ROOTS[1].id,
            COLLECTIONS[0].id,
            id="wrong api root",
        ),
        pytest.param(
            str(uuid4()),
            COLLECTIONS[0].id,
            id="unknown api root",
        ),
        pytest.param(
            API_ROOTS[0].id,
            str(uuid4()),
            id="unknown collection id",
        ),
    ],
)
def test_get_collection(
    taxii2_sqldb_api, db_collections, api_root_id, collection_id_or_alias
):
    response = taxii2_sqldb_api.get_collection(api_root_id, collection_id_or_alias)
    assert response == GET_COLLECTION_MOCK(api_root_id, collection_id_or_alias)


@pytest.mark.parametrize(
    [
        "collection_id",
        "limit",
        "added_after",
        "next_kwargs",
        "match_id",
        "match_type",
        "match_version",
        "match_spec_version",
    ],
    [
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="default",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            1,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="limit low",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            2,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="limit exact",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            999,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="limit high",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            NOW,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="added_after",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            {
                "id": STIX_OBJECTS[0].id,
                "date_added": STIX_OBJECTS[0].date_added,
            },  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="next_kwargs",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[0].id],  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_id",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [obj.id for obj in STIX_OBJECTS[:3]],  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_id multiple",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            [STIX_OBJECTS[0].type],  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_type",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            [obj.type for obj in STIX_OBJECTS[:3]],  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_type multiple",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[0].version],  # match_version
            None,  # match_spec_version
            id="version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[1].version],  # match_version
            None,  # match_spec_version
            id="version [1]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[2].version],  # match_version
            None,  # match_spec_version
            id="version [2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[0].version, STIX_OBJECTS[2].version],  # match_version
            None,  # match_spec_version
            id="version [0, 2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["first"],  # match_version
            None,  # match_spec_version
            id="version first",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["last"],  # match_version
            None,  # match_spec_version
            id="version last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["all"],  # match_version
            None,  # match_spec_version
            id="version all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["first", "last"],  # match_version
            None,  # match_spec_version
            id="version first, last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[2].version, "last"],  # match_version
            None,  # match_spec_version
            id="version [2], last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            [STIX_OBJECTS[0].spec_version],  # match_spec_version
            id="spec_version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            [STIX_OBJECTS[1].spec_version],  # match_spec_version
            id="spec_version [1]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            [
                STIX_OBJECTS[0].spec_version,
                STIX_OBJECTS[1].spec_version,
            ],  # match_spec_version
            id="spec_version [0, 1]",
        ),
    ],
)
def test_get_manifest(
    taxii2_sqldb_api,
    db_stix_objects,
    collection_id,
    limit,
    added_after,
    next_kwargs,
    match_id,
    match_type,
    match_version,
    match_spec_version,
):
    response = taxii2_sqldb_api.get_manifest(
        collection_id=collection_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_id=match_id,
        match_type=match_type,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )
    assert response == GET_MANIFEST_MOCK(
        collection_id=collection_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_id=match_id,
        match_type=match_type,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )


@pytest.mark.parametrize(
    [
        "collection_id",
        "limit",
        "added_after",
        "next_kwargs",
        "match_id",
        "match_type",
        "match_version",
        "match_spec_version",
    ],
    [
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="default",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            1,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="limit low",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            2,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="limit exact",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            999,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="limit high",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            NOW,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="added_after",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            {
                "id": STIX_OBJECTS[0].id,
                "date_added": STIX_OBJECTS[0].date_added,
            },  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="next_kwargs",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[0].id],  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_id",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [obj.id for obj in STIX_OBJECTS[:3]],  # match_id
            None,  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_id multiple",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            [STIX_OBJECTS[0].type],  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_type",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            [obj.type for obj in STIX_OBJECTS[:3]],  # match_type
            None,  # match_version
            None,  # match_spec_version
            id="match_type multiple",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[0].version],  # match_version
            None,  # match_spec_version
            id="version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[1].version],  # match_version
            None,  # match_spec_version
            id="version [1]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[2].version],  # match_version
            None,  # match_spec_version
            id="version [2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[0].version, STIX_OBJECTS[2].version],  # match_version
            None,  # match_spec_version
            id="version [0, 2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["first"],  # match_version
            None,  # match_spec_version
            id="version first",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["last"],  # match_version
            None,  # match_spec_version
            id="version last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["all"],  # match_version
            None,  # match_spec_version
            id="version all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            ["first", "last"],  # match_version
            None,  # match_spec_version
            id="version first, last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            [STIX_OBJECTS[2].version, "last"],  # match_version
            None,  # match_spec_version
            id="version [2], last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            [STIX_OBJECTS[0].spec_version],  # match_spec_version
            id="spec_version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            [STIX_OBJECTS[1].spec_version],  # match_spec_version
            id="spec_version [1]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_id
            None,  # match_type
            None,  # match_version
            [
                STIX_OBJECTS[0].spec_version,
                STIX_OBJECTS[1].spec_version,
            ],  # match_spec_version
            id="spec_version [0, 1]",
        ),
    ],
)
def test_get_objects(
    taxii2_sqldb_api,
    db_stix_objects,
    collection_id,
    limit,
    added_after,
    next_kwargs,
    match_id,
    match_type,
    match_version,
    match_spec_version,
):
    response = taxii2_sqldb_api.get_objects(
        collection_id=collection_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_id=match_id,
        match_type=match_type,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )
    assert response == GET_OBJECTS_MOCK(
        collection_id=collection_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_id=match_id,
        match_type=match_type,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )


@pytest.mark.parametrize(
    [
        "api_root_id",
        "collection_id",
        "objects",
    ],
    [
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            COLLECTIONS[5].id,  # collection_id
            [
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
            ],  # objects
            id="single object",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            COLLECTIONS[5].id,  # collection_id
            [
                {
                    "type": "relationship",
                    "spec_version": "2.1",
                    "id": "relationship--44298a74-ba52-4f0c-87a3-1824e67d7fad",
                    "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                    "created": "2016-04-06T20:06:37.000Z",
                    "modified": "2016-04-06T20:06:37.000Z",
                    "relationship_type": "indicates",
                    "source_ref": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                    "target_ref": "malware--31b940d4-6f7f-459a-80ea-9c1f17b5891b",
                },
                {
                    "type": "malware",
                    "spec_version": "2.1",
                    "id": "malware--31b940d4-6f7f-459a-80ea-9c1f17b5891b",
                    "is_family": True,
                    "created": "2016-04-06T20:07:09.000Z",
                    "modified": "2016-04-06T20:07:09.000Z",
                    "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                    "name": "Poison Ivy",
                    "malware_types": ["trojan"],
                },
            ],  # objects
            id="multiple objects",
        ),
        pytest.param(
            API_ROOTS[0].id,  # api_root_id
            COLLECTIONS[5].id,  # collection_id
            [
                {
                    "id": STIX_OBJECTS[0].id,
                    "type": STIX_OBJECTS[0].type,
                    "spec_version": STIX_OBJECTS[0].spec_version,
                    **STIX_OBJECTS[0].serialized_data,
                }
            ],  # objects
            id="existing object",
        ),
    ],
)
def test_add_objects(
    taxii2_sqldb_api,
    db_stix_objects,
    api_root_id,
    collection_id,
    objects,
):
    job = taxii2_sqldb_api.add_objects(
        api_root_id=api_root_id,
        collection_id=collection_id,
        objects=objects,
    )
    # Check response entities
    assert job == entities.Job(
        id=job.id,
        api_root_id=api_root_id,
        status="complete",
        request_timestamp=job.request_timestamp,
        completed_timestamp=job.completed_timestamp,
        total_count=len(objects),
        success_count=len(objects),
        failure_count=0,
        pending_count=0,
        details=entities.JobDetails(
            [
                entities.JobDetail(
                    id=job_detail.id,
                    job_id=job.id,
                    stix_id=obj["id"],
                    version=datetime.datetime.strptime(
                        obj["modified"], DATETIMEFORMAT
                    ).replace(tzinfo=datetime.timezone.utc),
                    message="",
                    status="success",
                )
                for (job_detail, obj) in zip(job.details.success, objects)
            ],
            [],
            [],
        ),
    )
    assert isinstance(job.request_timestamp, datetime.datetime)
    assert isinstance(job.completed_timestamp, datetime.datetime)
    # Check database state
    db_job = taxii2_sqldb_api.db.session.query(Job).one()
    assert str(db_job.api_root_id) == api_root_id
    assert db_job.status == "complete"
    assert isinstance(db_job.request_timestamp, datetime.datetime)
    assert isinstance(db_job.completed_timestamp, datetime.datetime)
    for obj in objects:
        db_obj = (
            taxii2_sqldb_api.db.session.query(STIXObject)
            .filter(
                STIXObject.id == obj["id"],
                STIXObject.version
                == datetime.datetime.strptime(obj["modified"], DATETIMEFORMAT).replace(
                    tzinfo=datetime.timezone.utc
                ),
            )
            .one()
        )
        assert db_obj.id == obj["id"]
        assert str(db_obj.collection_id) == collection_id
        assert db_obj.type == obj["type"]
        assert db_obj.spec_version == obj["spec_version"]
        assert isinstance(db_obj.date_added, datetime.datetime)
        assert db_obj.version == datetime.datetime.strptime(
            obj["modified"], DATETIMEFORMAT
        ).replace(tzinfo=datetime.timezone.utc)
        assert db_obj.serialized_data == {
            key: value
            for (key, value) in obj.items()
            if key not in ["id", "type", "spec_version"]
        }
        db_job_detail = (
            taxii2_sqldb_api.db.session.query(JobDetail)
            .filter(JobDetail.stix_id == obj["id"])
            .one()
        )
        assert db_job_detail.job_id == db_job.id
        assert db_job_detail.stix_id == obj["id"]
        assert db_job_detail.version == datetime.datetime.strptime(
            obj["modified"], DATETIMEFORMAT
        ).replace(tzinfo=datetime.timezone.utc)
        assert db_job_detail.message == ""
        assert db_job_detail.status == "success"


@pytest.mark.parametrize(
    [
        "collection_id",
        "object_id",
        "limit",
        "added_after",
        "next_kwargs",
        "match_version",
        "match_spec_version",
    ],
    [
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="default",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            str(uuid4()),  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="unknown object",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            NOW,  # added_after
            None,  # next_kwargs
            ["all"],  # match_version
            None,  # match_spec_version
            id="added_after, all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            NOW,  # added_after
            None,  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="added_after",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            NOW + datetime.timedelta(seconds=3),  # added_after
            None,  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="added_after, no results",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            1,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="limit",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            1,  # limit
            None,  # added_after
            None,  # next_kwargs
            ["all"],  # match_version
            None,  # match_spec_version
            id="limit, all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            2,  # limit
            None,  # added_after
            None,  # next_kwargs
            ["all"],  # match_version
            None,  # match_spec_version
            id="limit exact, all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            999,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="limit high",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            {
                "id": STIX_OBJECTS[0].id,
                "date_added": STIX_OBJECTS[0].date_added,
            },  # next_kwargs
            None,  # match_version
            None,  # match_spec_version
            id="next",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            {
                "id": STIX_OBJECTS[0].id,
                "date_added": STIX_OBJECTS[0].date_added,
            },  # next_kwargs
            ["all"],  # match_version
            None,  # match_spec_version
            id="next, all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[0].version],  # match_version
            None,  # match_spec_version
            id="version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[1].version],  # match_version
            None,  # match_spec_version
            id="version [1]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[2].version],  # match_version
            None,  # match_spec_version
            id="version [2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[0].version, STIX_OBJECTS[2].version],  # match_version
            None,  # match_spec_version
            id="version [0, 2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            ["first"],  # match_version
            None,  # match_spec_version
            id="version first",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            ["last"],  # match_version
            None,  # match_spec_version
            id="version last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            ["all"],  # match_version
            None,  # match_spec_version
            id="version all",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            ["first", "last"],  # match_version
            None,  # match_spec_version
            id="version first, last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[2].version, "last"],  # match_version
            None,  # match_spec_version
            id="version [2], last",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            [STIX_OBJECTS[0].spec_version],  # match_spec_version
            id="spec_version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            [STIX_OBJECTS[2].spec_version],  # match_spec_version
            id="spec_version [2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_version
            [
                STIX_OBJECTS[0].spec_version,
                STIX_OBJECTS[2].spec_version,
            ],  # match_spec_version
            id="spec_version [0, 2]",
        ),
    ],
)
def test_get_object(
    taxii2_sqldb_api,
    db_stix_objects,
    collection_id,
    object_id,
    limit,
    added_after,
    next_kwargs,
    match_version,
    match_spec_version,
):
    response = taxii2_sqldb_api.get_object(
        collection_id=collection_id,
        object_id=object_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )
    assert response == GET_OBJECT_MOCK(
        collection_id=collection_id,
        object_id=object_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )


@pytest.mark.parametrize(
    [
        "collection_id",
        "object_id",
        "match_version",
        "match_spec_version",
        "expected_objects",
    ],
    [
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # match_version
            None,  # match_spec_version
            [STIX_OBJECTS[1], STIX_OBJECTS[3], STIX_OBJECTS[4]],  # expected_objects
            id="default",
        ),
        pytest.param(
            COLLECTIONS[4].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # match_version
            None,  # match_spec_version
            STIX_OBJECTS,  # expected_objects
            id="wrong collection",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            [STIX_OBJECTS[0].version],  # match_version
            None,  # match_spec_version
            STIX_OBJECTS[1:],  # expected_objects
            id="version",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # match_version
            [STIX_OBJECTS[0].spec_version],  # match_spec_version
            STIX_OBJECTS[1:],  # expected_objects
            id="version",
        ),
    ],
)
def test_delete_object(
    taxii2_sqldb_api,
    db_stix_objects,
    collection_id,
    object_id,
    match_version,
    match_spec_version,
    expected_objects,
):
    taxii2_sqldb_api.delete_object(
        collection_id=collection_id,
        object_id=object_id,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )
    assert set(
        (str(db_obj.collection_id), db_obj.id, db_obj.version)
        for db_obj in taxii2_sqldb_api.db.session.query(STIXObject).all()
    ) == set((obj.collection_id, obj.id, obj.version) for obj in expected_objects)


@pytest.mark.parametrize(
    [
        "collection_id",
        "object_id",
        "limit",
        "added_after",
        "next_kwargs",
        "match_spec_version",
    ],
    [
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_spec_version
            id="default",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            str(uuid4()),  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_spec_version
            id="unknown object",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            NOW,  # added_after
            None,  # next_kwargs
            None,  # match_spec_version
            id="added_after",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            NOW + datetime.timedelta(seconds=3),  # added_after
            None,  # next_kwargs
            None,  # match_spec_version
            id="added_after, no results",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            1,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_spec_version
            id="limit",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            999,  # limit
            None,  # added_after
            None,  # next_kwargs
            None,  # match_spec_version
            id="limit high",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            {
                "id": STIX_OBJECTS[0].id,
                "date_added": STIX_OBJECTS[0].date_added,
            },  # next_kwargs
            None,  # match_spec_version
            id="next",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[0].spec_version],  # match_spec_version
            id="spec_version [0]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [STIX_OBJECTS[2].spec_version],  # match_spec_version
            id="spec_version [2]",
        ),
        pytest.param(
            COLLECTIONS[5].id,  # collection_id
            STIX_OBJECTS[0].id,  # object_id
            None,  # limit
            None,  # added_after
            None,  # next_kwargs
            [
                STIX_OBJECTS[0].spec_version,
                STIX_OBJECTS[2].spec_version,
            ],  # match_spec_version
            id="spec_version [0, 2]",
        ),
    ],
)
def test_get_versions(
    taxii2_sqldb_api,
    db_stix_objects,
    collection_id,
    object_id,
    limit,
    added_after,
    next_kwargs,
    match_spec_version,
):
    response = taxii2_sqldb_api.get_versions(
        collection_id=collection_id,
        object_id=object_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_spec_version=match_spec_version,
    )
    assert response == GET_VERSIONS_MOCK(
        collection_id=collection_id,
        object_id=object_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_spec_version=match_spec_version,
    )


@pytest.mark.parametrize(
    "stix_id, date_added, next_param",
    [
        pytest.param(
            "indicator--fa641b92-94d7-42dd-aa0e-63cfe1ee148a",
            datetime.datetime(
                2022, 2, 4, 18, 40, 6, 297204, tzinfo=datetime.timezone.utc
            ),
            (
                "MjAyMi0wMi0wNFQxODo0MDowNi4yOTcyMDQrMDA6MDB8aW5kaWNhdG9yLS1mYTY0M"
                "WI5Mi05NGQ3LTQyZGQtYWEwZS02M2NmZTFlZTE0OGE="
            ),
            id="simple",
        ),
    ],
)
def test_next_param(taxii2_sqldb_api, stix_id, date_added, next_param):
    assert (
        taxii2_sqldb_api.get_next_param({"id": stix_id, "date_added": date_added})
        == next_param
    )
    assert taxii2_sqldb_api.parse_next_param(next_param) == {
        "id": stix_id,
        "date_added": date_added,
    }
