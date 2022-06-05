import base64
import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from opentaxii.server import ServerMapping
from opentaxii.taxii2.entities import (ApiRoot, Collection, Job, JobDetail,
                                       ManifestRecord, STIXObject,
                                       VersionRecord)
from opentaxii.taxii2.utils import DATETIMEFORMAT, taxii2_datetimeformat

API_ROOTS_WITH_DEFAULT = (
    ApiRoot(str(uuid4()), True, "first title", "first description", False),
    ApiRoot(str(uuid4()), False, "second title", "second description", True),
)
API_ROOTS_WITHOUT_DEFAULT = (
    ApiRoot(str(uuid4()), False, "first title", "first description", False),
    ApiRoot(str(uuid4()), False, "second title", "second description", True),
    ApiRoot(str(uuid4()), False, "third title", None, False),
)
API_ROOTS = API_ROOTS_WITHOUT_DEFAULT
NOW = datetime.datetime.now(datetime.timezone.utc)
JOBS = tuple()
for api_root in API_ROOTS:
    JOBS = JOBS + (
        Job(
            str(uuid4()),
            api_root.id,
            "complete",
            NOW,
            NOW - datetime.timedelta(hours=24, minutes=1),
        ),
        Job(
            str(uuid4()),
            api_root.id,
            "pending",
            NOW,
            None,
        ),
    )
JOBS = JOBS + (
    Job(
        str(uuid4()),
        API_ROOTS[0].id,
        "pending",
        NOW,
        None,
        6,
        1,
        2,
        3,
    ),
)

JOBS[0].details.success.extend(
    [
        JobDetail(
            id=str(uuid4()),
            job_id=JOBS[0].id,
            stix_id="indicator--c410e480-e42b-47d1-9476-85307c12bcbf",
            version=datetime.datetime.strptime(
                "2018-05-27T12:02:41.312Z", DATETIMEFORMAT
            ).replace(tzinfo=datetime.timezone.utc),
            message="",
            status="success",
        )
    ]
)
JOBS[0].success_count = 1
JOBS[0].details.failure.extend(
    [
        JobDetail(
            id=str(uuid4()),
            job_id=JOBS[0].id,
            stix_id="malware--664fa29d-bf65-4f28-a667-bdb76f29ec98",
            version=datetime.datetime.strptime(
                "2018-05-28T14:03:42.543Z", DATETIMEFORMAT
            ).replace(tzinfo=datetime.timezone.utc),
            message="Unable to process object",
            status="failure",
        )
    ]
)
JOBS[0].failure_count = 1
JOBS[0].details.pending.extend(
    [
        JobDetail(
            id=str(uuid4()),
            job_id=JOBS[0].id,
            stix_id="indicator--252c7c11-daf2-42bd-843b-be65edca9f61",
            version=datetime.datetime.strptime(
                "2018-05-18T20:16:21.148Z", DATETIMEFORMAT
            ).replace(tzinfo=datetime.timezone.utc),
            message="",
            status="pending",
        ),
        JobDetail(
            id=str(uuid4()),
            job_id=JOBS[0].id,
            stix_id="relationship--045585ad-a22f-4333-af33-bfd503a683b5",
            version=datetime.datetime.strptime(
                "2018-05-15T10:13:32.579Z", DATETIMEFORMAT
            ).replace(tzinfo=datetime.timezone.utc),
            message="",
            status="pending",
        ),
    ]
)
JOBS[0].pending_count = 2
JOBS[0].total_count = 4

COLLECTIONS = (
    Collection(
        str(uuid4()),
        API_ROOTS[0].id,
        "0Read only",
        "Read only description",
        None,
        False,
    ),
    Collection(
        str(uuid4()),
        API_ROOTS[0].id,
        "1Write only",
        "Write only description",
        None,
        False,
    ),
    Collection(
        str(uuid4()),
        API_ROOTS[0].id,
        "2Read/Write",
        "Read/Write description",
        None,
        False,
    ),
    Collection(
        str(uuid4()),
        API_ROOTS[0].id,
        "3No permissions",
        "No permissions description",
        None,
        False,
    ),
    Collection(str(uuid4()), API_ROOTS[0].id, "4No description", "", None, False),
    Collection(
        str(uuid4()),
        API_ROOTS[0].id,
        "5With alias",
        "With alias description",
        "this-is-an-alias",
        False,
    ),
    Collection(
        str(uuid4()),
        API_ROOTS[0].id,
        "6Public",
        "public description",
        "",
        True,
    ),
)
STIX_OBJECTS = (
    STIXObject(
        f"indicator--{str(uuid4())}",
        COLLECTIONS[5].id,
        "indicator",
        "2.0",
        NOW,
        NOW + datetime.timedelta(seconds=1),
        {
            "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
            "created": "2016-04-06T20:03:48.000Z",
            "modified": taxii2_datetimeformat(NOW + datetime.timedelta(seconds=1)),
            "indicator_types": ["malicious-activity"],
            "name": "Poison Ivy Malware",
            "description": "This file is part of Poison Ivy",
            "pattern": "[ file:hashes.'SHA-256' = "
            "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
            "pattern_type": "stix",
            "valid_from": "2016-01-01T00:00:00Z",
        },
    ),
    STIXObject(
        f"relationship--{str(uuid4())}",
        COLLECTIONS[5].id,
        "relationship",
        "2.1",
        NOW + datetime.timedelta(seconds=2),
        NOW + datetime.timedelta(seconds=3),
        {
            "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
            "created": "2016-04-06T20:06:37.000Z",
            "modified": taxii2_datetimeformat(NOW + datetime.timedelta(seconds=3)),
            "relationship_type": "indicates",
            "source_ref": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
            "target_ref": "malware--31b940d4-6f7f-459a-80ea-9c1f17b5891b",
        },
    ),
)
STIX_OBJECTS = STIX_OBJECTS + (
    STIXObject(
        STIX_OBJECTS[0].id,
        COLLECTIONS[5].id,
        "indicator",
        "2.1",
        NOW + datetime.timedelta(seconds=3),
        NOW + datetime.timedelta(seconds=-1),
        {
            "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
            "created": "2016-04-06T20:03:48.000Z",
            "modified": taxii2_datetimeformat(NOW + datetime.timedelta(seconds=-1)),
            "indicator_types": ["malicious-activity"],
            "name": "Poison Ivy Malware",
            "description": "This file is part of Poison Ivy",
            "pattern": "[ file:hashes.'SHA-256' = "
            "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
            "pattern_type": "stix",
            "valid_from": "2016-01-01T00:00:00Z",
        },
    ),
    STIXObject(
        f"indicator--{str(uuid4())}",
        COLLECTIONS[1].id,
        "indicator",
        "2.1",
        NOW,
        NOW + datetime.timedelta(seconds=1),
        {
            "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
            "created": "2016-04-06T20:03:48.000Z",
            "modified": taxii2_datetimeformat(NOW + datetime.timedelta(seconds=1)),
            "indicator_types": ["malicious-activity"],
            "name": "Poison Ivy Malware",
            "description": "This file is part of Poison Ivy",
            "pattern": "[ file:hashes.'SHA-256' = "
            "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
            "pattern_type": "stix",
            "valid_from": "2016-01-01T00:00:00Z",
        },
    ),
    STIXObject(
        f"indicator--{str(uuid4())}",
        COLLECTIONS[6].id,
        "indicator",
        "2.0",
        NOW,
        NOW + datetime.timedelta(seconds=1),
        {
            "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
            "created": "2016-04-06T20:03:48.000Z",
            "modified": taxii2_datetimeformat(NOW + datetime.timedelta(seconds=1)),
            "indicator_types": ["malicious-activity"],
            "name": "Poison Ivy Malware",
            "description": "This file is part of Poison Ivy",
            "pattern": "[ file:hashes.'SHA-256' = "
            "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
            "pattern_type": "stix",
            "valid_from": "2016-01-01T00:00:00Z",
        },
    ),
)


def process_match_version(match_version):
    if match_version is None:
        match_version = ["last"]
    versions_per_id = {}
    for stix_obj in STIX_OBJECTS:
        if stix_obj.id not in versions_per_id:
            versions_per_id[stix_obj.id] = []
        versions_per_id[stix_obj.id].append(stix_obj.version)
    id_version_combos = []
    for value in match_version:
        if value == "last":
            for obj_id, versions in versions_per_id.items():
                id_version_combos.append((obj_id, max(versions)))
        elif value == "first":
            for obj_id, versions in versions_per_id.items():
                id_version_combos.append((obj_id, min(versions)))
        elif value == "all":
            for obj_id, versions in versions_per_id.items():
                for version in versions:
                    id_version_combos.append((obj_id, version))
        else:
            for obj_id in versions_per_id:
                id_version_combos.append((obj_id, value))
    return id_version_combos


def GET_API_ROOT_MOCK(api_root_id):
    for api_root in API_ROOTS:
        if api_root.id == api_root_id:
            return api_root
    return None


def GET_JOB_AND_DETAILS_MOCK(api_root_id, job_id):
    job_response = None
    for job in JOBS:
        if job.api_root_id == api_root_id and job.id == job_id:
            job_response = job
            break
    return job_response


def GET_COLLECTIONS_MOCK(api_root_id):
    response = []
    for collection in COLLECTIONS:
        if collection.api_root_id == api_root_id:
            response.append(collection)
    return response


def GET_COLLECTION_MOCK(api_root_id, collection_id_or_alias):
    for collection in COLLECTIONS:
        if collection.api_root_id == api_root_id and (
            collection.id == collection_id_or_alias
            or collection.alias == collection_id_or_alias
        ):
            return collection
    return None


def STIX_OBJECT_FROM_MANIFEST(stix_id):
    for obj in STIX_OBJECTS:
        if obj.id == stix_id:
            return obj


def GET_MANIFEST_MOCK(
    collection_id: str,
    limit: Optional[int] = None,
    added_after: Optional[datetime.datetime] = None,
    next_kwargs: Optional[Dict] = None,
    match_id: Optional[List[str]] = None,
    match_type: Optional[List[str]] = None,
    match_version: Optional[List[str]] = None,
    match_spec_version: Optional[List[str]] = None,
):
    stix_objects, more, _ = GET_OBJECTS_MOCK(
        collection_id=collection_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_id=match_id,
        match_type=match_type,
        match_version=match_version,
        match_spec_version=match_spec_version,
    )
    response = [
        ManifestRecord(obj.id, obj.date_added, obj.version, obj.spec_version)
        for obj in stix_objects
    ]
    return response, more


def GET_NEXT_PARAM(kwargs: Dict) -> str:
    return base64.b64encode(
        f"{kwargs['date_added'].isoformat()}|{kwargs['id']}".encode("utf-8")
    ).decode()


def GET_OBJECTS_MOCK(
    collection_id: str,
    limit: Optional[int] = None,
    added_after: Optional[datetime.datetime] = None,
    next_kwargs: Optional[Dict] = None,
    match_id: Optional[List[str]] = None,
    match_type: Optional[List[str]] = None,
    match_version: Optional[List[str]] = None,
    match_spec_version: Optional[List[str]] = None,
):
    id_version_combos = process_match_version(match_version)
    response = []
    more = False
    for stix_object in STIX_OBJECTS:
        if (
            stix_object.collection_id == collection_id
            and (stix_object.id, stix_object.version) in id_version_combos
        ):
            if limit is not None and limit == len(response):
                more = True
                break
            if added_after is not None:
                if stix_object.date_added <= added_after:
                    continue
            if next_kwargs is not None:
                if stix_object.date_added < next_kwargs["date_added"] or (
                    stix_object.date_added == next_kwargs["date_added"]
                    and stix_object.id == next_kwargs["id"]
                ):
                    continue
            if match_id is not None and stix_object.id not in match_id:
                continue
            if match_type is not None and stix_object.type not in match_type:
                continue
            if (
                match_spec_version is not None
                and stix_object.spec_version not in match_spec_version
            ):
                continue
            response.append(stix_object)
    if more:
        next_param = GET_NEXT_PARAM(
            {"id": response[-1].id, "date_added": response[-1].date_added}
        )
    else:
        next_param = None
    return response, more, next_param


def GET_OBJECT_MOCK(
    collection_id: str,
    object_id: str,
    limit: Optional[int] = None,
    added_after: Optional[datetime.datetime] = None,
    next_kwargs: Optional[Dict] = None,
    match_version: Optional[List[str]] = None,
    match_spec_version: Optional[List[str]] = None,
):
    id_version_combos = process_match_version(match_version)
    response = []
    more = False
    at_least_one = False
    for stix_object in STIX_OBJECTS:
        if stix_object.collection_id == collection_id and stix_object.id == object_id:
            at_least_one = True
            if (
                stix_object.id,
                stix_object.version,
            ) not in id_version_combos:
                continue
            if limit is not None and limit == len(response):
                more = True
                break
            if added_after is not None:
                if stix_object.date_added <= added_after:
                    continue
            if next_kwargs is not None:
                if stix_object.date_added < next_kwargs["date_added"] or (
                    stix_object.date_added == next_kwargs["date_added"]
                    and stix_object.id == next_kwargs["id"]
                ):
                    continue
            if (
                match_spec_version is not None
                and stix_object.spec_version not in match_spec_version
            ):
                continue
            response.append(stix_object)
    if more:
        next_param = GET_NEXT_PARAM(
            {"id": response[-1].id, "date_added": response[-1].date_added}
        )
    else:
        next_param = None
    if not at_least_one:
        response = None
    return response, more, next_param


def ADD_OBJECTS_MOCK(api_root_id: str, collection_id: str, objects: List[Dict]):
    return JOBS[0]


def DELETE_OBJECT_MOCK(
    collection_id: str,
    object_id: str,
    match_version: Optional[List[str]] = None,
    match_spec_version: Optional[List[str]] = None,
):
    return


def GET_VERSIONS_MOCK(
    collection_id: str,
    object_id: str,
    limit: Optional[int] = None,
    added_after: Optional[datetime.datetime] = None,
    next_kwargs: Optional[Dict] = None,
    match_spec_version: Optional[List[str]] = None,
):
    versions, more, _ = GET_OBJECT_MOCK(
        collection_id=collection_id,
        object_id=object_id,
        limit=limit,
        added_after=added_after,
        next_kwargs=next_kwargs,
        match_spec_version=match_spec_version,
        match_version=["all"],
    )
    return (
        [VersionRecord(obj.date_added, obj.version) for obj in versions]
        if versions is not None
        else None,
        more,
    )


def config_noop(config):
    return config


def config_remove_fields(*fields):
    def inner(config):
        for field in fields:
            del config[field]
        return config

    return inner


def config_override(override):
    def inner(config):
        return {**config, **override}

    return inner


def server_mapping_remove_fields(*fields):
    def inner(original):
        override = {field: None for field in fields}
        kwargs = {**dict(original._asdict()), **override}
        return ServerMapping(**kwargs)

    return inner


def server_mapping_noop(original):
    return original
