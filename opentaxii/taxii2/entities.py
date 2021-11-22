from datetime import datetime

from opentaxii.common.entities import Entity


class ApiRoot(Entity):
    """
    TAXII2 API Root entity.

    :param id int: id of this API root
    :param bool default: indicator of default api root, should only be True once
    :param str title: human readable plain text name used to identify this API Root
    :param str description: human readable plain text description for this API Root
    """

    def __init__(self, id: int, default: bool, title: str, description: str):
        self.id = id
        self.default = default
        self.title = title
        self.description = description


class Collection(Entity):
    """
    TAXII2 Collection entity.

    :param str id: id of this collection
    :param int api_root_id: id of the :class:`ApiRoot` this collection belongs to
    :param str title: human readable plain text name used to identify this collection
    :param str description: human readable plain text description for this collection
    :param str alias: human readable collection name that can be used on systems to alias a collection id
    """

    def __init__(
        self, id: str, api_root_id: int, title: str, description: str, alias: str
    ):
        self.id = id
        self.api_root_id = api_root_id
        self.title = title
        self.description = description
        self.alias = alias


class STIXObject(Entity):
    """
    TAXII2 STIXObject entity.

    :param str id: id of this stix object
    :param str collection_id: id of the :class:`Collection` this stix object belongs to
    :param str type: type of this stix object
    :param str spec_version: stix version this object matches
    :param datetime date_added: the date and time this object was added
    :param datetime version: the version of this object
    :param dict serialized_data: the payload of this object
    """

    def __init__(
        self,
        id: str,
        collection_id: str,
        type: str,
        spec_version: str,
        date_added: datetime,
        version: datetime,
        serialized_data: dict,
    ):
        self.id = id
        self.collection_id = collection_id
        self.type = type
        self.spec_version = spec_version
        self.date_added = date_added
        self.version = version
        self.serialized_data = serialized_data


class Job(Entity):
    """
    TAXII2 Job entity, called a "status resource" in taxii2 docs.

    :param str id: id of this job
    :param str status: status of this job
    :param datetime request_timestamp: the datetime of the request that this status resource is monitoring
    :param datetime completed_timestamp: the datetime of the completion of this job (used for cleanup)
    """

    def __init__(
        self,
        id: str,
        status: str,
        request_timestamp: datetime,
        completed_timestamp: datetime,
    ):
        self.id = id
        self.status = status
        self.request_timestamp = request_timestamp
        self.completed_timestamp = completed_timestamp


class JobDetail(Entity):
    """
    TAXII2 JobDetail entity, part of "status resource" in taxii2 docs.

    :param str id: id of this job detail
    :param str job_id: id of the job this detail belongs to
    :param str stix_id: id of the :class:`STIXObject` this detail tracks
    :param str version: the version of this object
    :param str message: message indicating more information about the object being created,
        its pending state, or why the object failed to be created.
    """

    def __init__(self, id: str, job_id: str, stix_id: str, version: str, message: str):
        self.id = id
        self.job_id = job_id
        self.stix_id = stix_id
        self.version = version
        self.message = message
