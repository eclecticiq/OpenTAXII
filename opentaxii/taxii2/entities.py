"""Taxii2 entities."""
from datetime import datetime
from typing import List, NamedTuple, Optional

from opentaxii.common.entities import Entity
from opentaxii.entities import Account
from opentaxii.taxii2.utils import taxii2_datetimeformat


class ApiRoot(Entity):
    """
    TAXII2 API Root entity.

    :param str id: id of this API root
    :param bool default: indicator of default api root, should only be True once
    :param str title: human readable plain text name used to identify this API Root
    :param str description: human readable plain text description for this API Root
    :param bool is_public: whether this is a publicly readable API root
    """

    def __init__(
        self, id: str, default: bool, title: str, description: str, is_public: bool
    ):
        """Initialize ApiRoot."""
        self.id = id
        self.default = default
        self.title = title
        self.description = description
        self.is_public = is_public


class Collection(Entity):
    """
    TAXII2 Collection entity.

    :param str id: id of this collection
    :param str api_root_id: id of the :class:`ApiRoot` this collection belongs to
    :param str title: human readable plain text name used to identify this collection
    :param str description: human readable plain text description for this collection
    :param str alias: human readable collection name that can be used on systems to alias a collection id
    :param bool is_public: whether this is a publicly readable collection
    :param bool is_public_write: whether this is a publicly writable collection
    """

    def __init__(
        self,
        id: str,
        api_root_id: str,
        title: str,
        description: str,
        alias: str,
        is_public: bool,
        is_public_write: bool,
    ):
        """Initialize Collection."""
        self.id = id
        self.api_root_id = api_root_id
        self.title = title
        self.description = description
        self.alias = alias
        self.is_public = is_public
        self.is_public_write = is_public_write

    def can_read(self, account: Optional[Account]):
        """Determine if `account` is allowed to read from this collection."""
        return self.is_public or (
            account
            and (
                account.is_admin or
                "read" in account.permissions.get(str(self.id), "") or
                "modify" in account.permissions.get(str(self.id), "")
            )
        )

    def can_write(self, account: Optional[Account]):
        """Determine if `account` is allowed to write to this collection."""
        return self.is_public_write or (
            account
            and (
                account.is_admin or "modify" in account.permissions.get(self.id, "")
            )
        )


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
        """Initialize STIXObject."""
        self.id = id
        self.collection_id = collection_id
        self.type = type
        self.spec_version = spec_version
        self.date_added = date_added
        self.version = version
        self.serialized_data = serialized_data


class ManifestRecord(Entity):
    """
    TAXII2 ManifestRecord entity.

    This is a cut-down version of :class:`STIXObject`, for efficiency.

    :param str id: id of this stix object
    :param datetime date_added: the date and time this object was added
    :param datetime version: the version of this object
    :param str spec_version: stix version this object matches
    """

    def __init__(
        self,
        id: str,
        date_added: datetime,
        version: datetime,
        spec_version: str,
    ):
        """Initialize ManifestRecord."""
        self.id = id
        self.date_added = date_added
        self.version = version
        self.spec_version = spec_version


class VersionRecord(Entity):
    """
    TAXII2 VersionRecord entity.

    This is a cut-down version of :class:`STIXObject`, for efficiency.

    :param datetime date_added: the date and time this object was added
    :param datetime version: the version of this object
    """

    def __init__(
        self,
        date_added: datetime,
        version: datetime,
    ):
        """Initialize VersionRecord."""
        self.date_added = date_added
        self.version = version


class JobDetail(Entity):
    """
    TAXII2 JobDetail entity, part of "status resource" in taxii2 docs.

    :param str id: id of this job detail
    :param str job_id: id of the job this detail belongs to
    :param str stix_id: id of the :class:`STIXObject` this detail tracks
    :param datetime version: the version of this object
    :param str message: message indicating more information about the object being created,
        its pending state, or why the object failed to be created.
    :param str status: status of this job
    """

    def __init__(
        self,
        id: str,
        job_id: str,
        stix_id: str,
        version: datetime,
        message: str,
        status: str,
    ):
        """Initialize JobDetail."""
        self.id = id
        self.job_id = job_id
        self.stix_id = stix_id
        self.version = version
        self.message = message
        self.status = status

    def as_taxii2_dict(self):
        """Turn this object into a taxii2 dict."""
        response = {"id": self.stix_id, "version": taxii2_datetimeformat(self.version)}
        if self.message:
            response["message"] = self.message
        return response


class JobDetails(NamedTuple):
    success: List[JobDetail]
    failure: List[JobDetail]
    pending: List[JobDetail]


class Job(Entity):
    """
    TAXII2 Job entity, called a "status resource" in taxii2 docs.

    :param str id: id of this job
    :param str api_root_id: id of the :class:`ApiRoot` this collection belongs to
    :param str status: status of this job
    :param datetime request_timestamp: the datetime of the request that this status resource is monitoring
    :param datetime completed_timestamp: the datetime of the completion of this job (used for cleanup)
    :param int total_count: the total number of stix objects in this job
    :param int success_count: the number of successful stix objects in this job
    :param int failure_count: the number of failed stix objects in this job
    :param int pending_count: the number of pending stix objects in this job
    :param dict details: the details per status of this job
    """

    def __init__(
        self,
        id: str,
        api_root_id: str,
        status: str,
        request_timestamp: datetime,
        completed_timestamp: Optional[datetime] = None,
        total_count: int = 0,
        success_count: int = 0,
        failure_count: int = 0,
        pending_count: int = 0,
        details: Optional[JobDetails] = None,
    ):
        """Initialize Job."""
        self.id = id
        self.api_root_id = api_root_id
        self.status = status
        self.request_timestamp = request_timestamp
        self.completed_timestamp = completed_timestamp
        self.total_count = total_count
        self.success_count = success_count
        self.failure_count = failure_count
        self.pending_count = pending_count
        if details is None:
            details = JobDetails([], [], [])
        self.details = details

    def as_taxii2_dict(self):
        """Turn this object into a taxii2 dict."""
        response = {
            "id": self.id,
            "status": self.status,
            "request_timestamp": taxii2_datetimeformat(self.request_timestamp),
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "pending_count": self.pending_count,
        }
        if self.details.success:
            response["successes"] = [
                job_detail.as_taxii2_dict() for job_detail in self.details.success
            ]
        if self.details.failure:
            response["failures"] = [
                job_detail.as_taxii2_dict() for job_detail in self.details.failure
            ]
        if self.details.pending:
            response["pendings"] = [
                job_detail.as_taxii2_dict() for job_detail in self.details.pending
            ]
        return response
