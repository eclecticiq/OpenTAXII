import datetime
from typing import Dict, List, NamedTuple, Optional, Tuple

import structlog
from opentaxii.local import context
from opentaxii.persistence.exceptions import (DoesNotExistError,
                                              NoReadNoWritePermission,
                                              NoReadPermission,
                                              NoWritePermission)
from opentaxii.signals import (CONTENT_BLOCK_CREATED, INBOX_MESSAGE_CREATED,
                               SUBSCRIPTION_CREATED)
from opentaxii.taxii2.entities import (ApiRoot, Collection, Job, JobDetail,
                                       ManifestRecord, STIXObject,
                                       VersionRecord)

log = structlog.getLogger(__name__)


class BasePersistenceManager:
    pass


class Taxii1PersistenceManager(BasePersistenceManager):
    """Manager responsible for persisting and retrieving data.

    Manager uses API instance ``api`` for basic data CRUD operations and
    provides additional logic on top.

    :param `opentaxii.persistence.api.OpenTAXIIPersistenceAPI` api:
        instance of persistence API class
    """

    def __init__(self, server, api):
        self.server = server
        self.api = api

    def create_service(self, service_entity):
        """Create service.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity object

        :return: created collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.ServiceEntity`
        """
        return self.api.create_service(service_entity)

    def update_service(self, service_entity):
        """Update service.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity object

        :return: created collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.ServiceEntity`
        """
        return self.api.update_service(service_entity)

    def delete_service(self, service_id):
        """Delete service.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity object
        """
        return self.api.delete_service(service_id)

    def delete_collection(self, collection_name):
        """Delete cllection.

        :param str collection_name: name of a collection to delete
        """
        return self.api.delete_collection(collection_name)

    def set_collection_services(self, collection_id, service_ids):
        """Set collection's services.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        """
        return self.api.set_collection_services(collection_id, service_ids)

    def create_collection(self, entity):
        """Create a collection.

        :param `opentaxii.taxii.entities.CollectionEntity` collection_entity:
            collection entity object

        :return: created collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        """
        collection = self.api.create_collection(entity)
        return collection

    def get_services(self):
        """Get configured services.

        Methods loads services entities via persistence API.

        :return: list of service entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.ServiceEntity`
        """
        return self.api.get_services()

    def get_services_for_collection(self, collection):
        """Get the services associated with a collection.

        :param `opentaxii.taxii.entities.CollectionEntity` collection:
            collection entity in question

        :return: list of service entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.ServiceEntity`
        """
        if context.account.can_read(collection.name):
            services = self.api.get_services(collection_id=collection.id)
            if context.account.can_modify(collection.name):
                return services
            else:
                return list(filter(lambda s: s.type != "inbox", services))

    def get_collections(self, service_id=None):
        """Get the collections. If `service_id` is provided, return collection
        attached to a service.

        :param str service_id: ID of the service in question

        :return: list of collection entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.CollectionEntity`
        """
        collections = [
            collection
            for collection in self.api.get_collections(service_id=service_id)
            if context.account.can_read(collection.name)
        ]
        return collections

    def get_collection(self, name, service_id=None):
        """Get a collection by name and service ID.

        Collection name is unique globally, so can be used as a key.
        Method retrieves collection entity using collection name
        ``name`` and service ID ``service_id`` as a composite key.

        :param str name: a collection name
        :param str service_id: ID of a service

        :return: collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        """
        collection = self.api.get_collection(name, service_id=service_id)
        if collection and context.account.can_read(collection.name):
            return collection

    def update_collection(self, collection):
        """Update a collection

        :param `opentaxii.taxii.entities.CollectionEntity` collection_entity:
            collection entity object

        :return: updated collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        """
        return self.api.update_collection(collection)

    def create_inbox_message(self, entity):
        """Create an inbox message.

        Methods emits :py:const:`opentaxii.signals.INBOX_MESSAGE_CREATED`
        signal.

        :param `opentaxii.taxii.entities.InboxMessageEntity` entity:
            inbox message entity in question
        :return: updated inbox message entity
        :rtype: :py:class:`opentaxii.taxii.entities.InboxMessageEntity`
        """

        if self.server.config["save_raw_inbox_messages"]:
            entity = self.api.create_inbox_message(entity)
            INBOX_MESSAGE_CREATED.send(self, inbox_message=entity)

        return entity

    def create_content(
        self, content, service_id=None, inbox_message_id=None, collections=None
    ):
        """Create a content block.

        Methods emits :py:const:`opentaxii.signals.CONTENT_BLOCK_CREATED`
        signal.

        :param `opentaxii.taxii.entities.ContentBlockEntity` entity:
                content block in question
        :param str service_id: ID of an inbox service via which content
                block was created
        :param `opentaxii.taxii.entities.InboxMessageEntity` inbox_message:
                inbox message that delivered the content block
        :param list collections: a list of destination collections as
                :py:class:`opentaxii.taxii.entities.CollectionEntity`
        :return: updated content block entity
        :rtype: :py:class:`opentaxii.taxii.entities.ContentBlockEntity`
        """
        if inbox_message_id:
            content.inbox_message_id = inbox_message_id

        collections = collections or []
        collection_ids = [
            collection.id
            for collection in collections
            if context.account.can_modify(collection.name)
        ]

        if collection_ids:
            content = self.api.create_content_block(
                content, collection_ids=collection_ids, service_id=service_id
            )
            CONTENT_BLOCK_CREATED.send(
                self,
                content_block=content,
                collection_ids=collection_ids,
                service_id=service_id,
            )
        else:
            log.warning(
                "create_content.unknown_collections",
                collections=[c.name for c in collections],
                user=context.account,
            )

        return content

    def get_content_blocks_count(
        self, collection_id, start_time=None, end_time=None, bindings=None
    ):
        """Get a count of the content blocks associated with a collection.

        :param str collection_id: ID fo a collection in question
        :param datetime start_time: start of a time frame
        :param datetime end_time: end of a time frame
        :param list bindings: list of
            :py:class:`opentaxii.taxii.entities.ContentBindingEntity`

        :return: content block count
        :rtype: int
        """
        return self.api.get_content_blocks_count(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings or [],
        )

    def get_content_blocks(
        self,
        collection_id,
        start_time=None,
        end_time=None,
        bindings=None,
        offset=0,
        limit=None,
    ):
        """Get the content blocks associated with a collection.

        :param str collection_id: ID fo a collection in question
        :param datetime start_time: start of a time frame
        :param datetime end_time: end of a time frame
        :param list bindings: list of
            :py:class:`opentaxii.taxii.entities.ContentBindingEntity`
        :param int offset: result set offset
        :param int limit: result set max size

        :return: content blocks list
        :rtype: list of :py:class:`opentaxii.taxii.entities.ContentBlockEntity`
        """

        return self.api.get_content_blocks(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings or [],
            offset=offset,
            limit=limit,
        )

    def create_result_set(self, entity):
        """Create a result set.

        :param `opentaxii.taxii.entities.ResultSetEntity` entity:
            result set entity in question

        :return: updated result set entity
        :rtype: :py:class:`opentaxii.taxii.entities.ResultSetEntity`
        """
        return self.api.create_result_set(entity)

    def get_result_set(self, result_set_id):
        """Get a result set entity by ID.

        :param str result_set_id: ID of a result set.

        :return: result set entity
        :rtype: :py:class:`opentaxii.taxii.entities.ResultSetEntity`
        """
        return self.api.get_result_set(result_set_id)

    def create_subscription(self, entity):
        """Create a subscription.

        Methods emits :py:const:`opentaxii.signals.SUBSCRIPTION_CREATED`
        signal.

        :param `opentaxii.taxii.entities.SubscriptionEntity` entity:
            subscription entity in question.

        :return: updated subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        """

        created = self.api.create_subscription(entity)

        SUBSCRIPTION_CREATED.send(self, subscription=created)

        return created

    def get_subscription(self, subscription_id):
        """Get a subscription entity by ID.

        :param str subscription_id: ID of a subscription

        :return: subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        """
        return self.api.get_subscription(subscription_id)

    def get_subscriptions(self, service_id):
        """Get the subscriptions attached to/created via a service.

        :param str service_id: ID of a service

        :return: list of subscription entities
        :rtype: list of :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        """
        return self.api.get_subscriptions(service_id=service_id)

    def update_subscription(self, subscription):
        """Update a subscription status.

        :param `opentaxii.taxii.entities.SubscriptionEntity` subscription:
            subscription entity in question

        :return: updated subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        """
        return self.api.update_subscription(subscription)

    def get_domain(self, service_id):
        """Get configured domain name needed to create absolute URLs.

        :param str service_id: ID of a service
        """
        return self.api.get_domain(service_id)

    def delete_content_blocks(
        self, collection_name, start_time, end_time=None, with_messages=False
    ):
        """Delete content blocks in a specified collection with
        timestamp label in a specified time frame.

        :param str collection_name: collection name
        :param datetime start_time: exclusive beginning of a timeframe
        :param datetime end_time: inclusive end of a timeframe
        :param bool with_messages: delete related inbox messages

        :return: the count of rows deleted
        :rtype: int
        """
        count = self.api.delete_content_blocks(
            collection_name, start_time, end_time=end_time, with_messages=with_messages
        )
        log.info(
            "collection.content_blocks.deleted",
            with_messages=with_messages,
            collection=collection_name,
            count=count,
        )
        return count


class JobDetailsResponse(NamedTuple):
    total_count: int
    success: List[JobDetail]
    failure: List[JobDetail]
    pending: List[JobDetail]


class Taxii2PersistenceManager(BasePersistenceManager):
    """Manager responsible for persisting and retrieving data.

    Manager uses API instance ``api`` for basic data CRUD operations and
    provides additional logic on top.

    :param `opentaxii.persistence.api.OpenTAXII2PersistenceAPI` api:
        instance of persistence API class
    """

    def __init__(self, server, api):
        self.server = server
        self.api = api

    def get_api_roots(self) -> Tuple[Optional[ApiRoot], List[ApiRoot]]:
        """
        Get (optional) default api root and list of all api roots.

        :return: Tuple of (default_api_root, all_api_roots)
        """
        api_roots = self.api.get_api_roots()
        if not api_roots:
            return None, []
        default_api_root = None
        for api_root in api_roots:
            if api_root.default:
                default_api_root = api_root
                break
        return (default_api_root, api_roots)

    def get_api_root(self, api_root_id: str) -> ApiRoot:
        api_root = self.api.get_api_root(api_root_id=api_root_id)
        if api_root is None:
            raise DoesNotExistError()
        return api_root

    def _get_job_details_response(
        self, job_details: List[JobDetail]
    ) -> JobDetailsResponse:
        job_details_response = JobDetailsResponse(
            total_count=len(job_details), success=[], failure=[], pending=[]
        )
        for job_detail in job_details:
            getattr(job_details_response, job_detail.status).append(job_detail)
        return job_details_response

    def get_job_and_details(
        self, api_root_id: str, job_id: str
    ) -> Tuple[Job, JobDetailsResponse]:
        job, job_details = self.api.get_job_and_details(
            api_root_id=api_root_id, job_id=job_id
        )
        if job is None:
            raise DoesNotExistError()
        job_details_response = self._get_job_details_response(job_details)
        return (job, job_details_response)

    def get_collections(self, api_root_id: str) -> List[Collection]:
        return self.api.get_collections(api_root_id=api_root_id)

    def get_collection(
        self, api_root_id: str, collection_id_or_alias: str
    ) -> Collection:
        collection = self.api.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if collection is None:
            raise DoesNotExistError()
        return collection

    def get_manifest(
        self,
        api_root_id: str,
        collection_id_or_alias: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_id: Optional[List[str]] = None,
        match_type: Optional[List[str]] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[ManifestRecord], bool]:
        collection = self.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if not collection.can_read(context.account):
            raise NoReadPermission()
        return self.api.get_manifest(
            collection_id=collection.id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_id=match_id,
            match_type=match_type,
            match_version=match_version,
            match_spec_version=match_spec_version,
        )

    def get_objects(
        self,
        api_root_id: str,
        collection_id_or_alias: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_id: Optional[List[str]] = None,
        match_type: Optional[List[str]] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[STIXObject], bool, Optional[str]]:
        collection = self.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if not collection.can_read(context.account):
            raise NoReadPermission()
        return self.api.get_objects(
            collection_id=collection.id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_id=match_id,
            match_type=match_type,
            match_version=match_version,
            match_spec_version=match_spec_version,
        )

    def add_objects(
        self,
        api_root_id: str,
        collection_id_or_alias: str,
        data: Dict,
    ) -> Tuple[Job, JobDetailsResponse]:
        collection = self.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if not collection.can_write(context.account):
            raise NoWritePermission()
        job, job_details = self.api.add_objects(
            api_root_id=api_root_id,
            collection_id=collection.id,
            objects=data["objects"],
        )
        job_details_response = self._get_job_details_response(job_details)
        return (job, job_details_response)

    def get_object(
        self,
        api_root_id: str,
        collection_id_or_alias: str,
        object_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[STIXObject], bool, Optional[str]]:
        collection = self.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if not collection.can_read(context.account):
            raise NoReadPermission()
        versions, more, next_param = self.api.get_object(
            collection_id=collection.id,
            object_id=object_id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_version=match_version,
            match_spec_version=match_spec_version,
        )
        if versions is None:
            raise DoesNotExistError()
        return (versions, more, next_param)

    def delete_object(
        self,
        api_root_id: str,
        collection_id_or_alias: str,
        object_id: str,
        match_version: Optional[List[str]] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> None:
        collection = self.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if not collection:
            raise DoesNotExistError()
        if not collection.can_read(context.account) and not collection.can_write(
            context.account
        ):
            raise NoReadNoWritePermission
        if not collection.can_read(context.account):
            raise NoReadPermission
        if not collection.can_write(context.account):
            raise NoWritePermission
        return self.api.delete_object(
            collection_id=collection.id,
            object_id=object_id,
            match_version=match_version,
            match_spec_version=match_spec_version,
        )

    def get_versions(
        self,
        api_root_id: str,
        collection_id_or_alias: str,
        object_id: str,
        limit: Optional[int] = None,
        added_after: Optional[datetime.datetime] = None,
        next_kwargs: Optional[Dict] = None,
        match_spec_version: Optional[List[str]] = None,
    ) -> Tuple[List[VersionRecord], bool]:
        collection = self.get_collection(
            api_root_id=api_root_id, collection_id_or_alias=collection_id_or_alias
        )
        if not collection:
            raise DoesNotExistError()
        if not collection.can_read(context.account):
            raise NoReadPermission
        versions, more = self.api.get_versions(
            collection_id=collection.id,
            object_id=object_id,
            limit=limit,
            added_after=added_after,
            next_kwargs=next_kwargs,
            match_spec_version=match_spec_version,
        )
        if versions is None:
            raise DoesNotExistError()
        return (versions, more)
