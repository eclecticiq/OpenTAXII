import structlog
from opentaxii.local import context
from opentaxii.signals import (
    CONTENT_BLOCK_CREATED, INBOX_MESSAGE_CREATED,
    SUBSCRIPTION_CREATED)

log = structlog.getLogger(__name__)


class PersistenceManager(object):
    '''Manager responsible for persisting and retrieving data.

    Manager uses API instance ``api`` for basic data CRUD operations and
    provides additional logic on top.

    :param `opentaxii.persistence.api.OpenTAXIIPersistenceAPI` api:
        instance of persistence API class
    '''

    def __init__(self, server, api):
        self.server = server
        self.api = api

    def create_service(self, service_entity):
        '''Create service.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity object

        :return: created collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.ServiceEntity`
        '''
        return self.api.create_service(service_entity)

    def update_service(self, service_entity):
        '''Update service.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity object

        :return: created collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.ServiceEntity`
        '''
        return self.api.update_service(service_entity)

    def delete_service(self, service_id):
        '''Delete service.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity object
        '''
        return self.api.delete_service(service_id)

    def delete_collection(self, collection_name):
        '''Delete cllection.

        :param str collection_name: name of a collection to delete
        '''
        return self.api.delete_collection(collection_name)

    def set_collection_services(self, collection_id, service_ids):
        '''Set collection's services.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        return self.api.set_collection_services(
            collection_id, service_ids)

    def create_collection(self, entity):
        '''Create a collection.

        :param `opentaxii.taxii.entities.CollectionEntity` collection_entity:
            collection entity object

        :return: created collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        collection = self.api.create_collection(entity)
        return collection

    def get_services(self):
        '''Get configured services.

        Methods loads services entities via persistence API.

        :return: list of service entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.ServiceEntity`
        '''
        return self.api.get_services()

    def get_services_for_collection(self, collection):
        '''Get the services associated with a collection.

        :param `opentaxii.taxii.entities.CollectionEntity` collection:
            collection entity in question

        :return: list of service entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.ServiceEntity`
        '''
        if context.account.can_read(collection.name):
            return self.api.get_services(collection_id=collection.id)

    def get_collections(self, service_id=None):
        '''Get the collections. If `service_id` is provided, return collection
        attached to a service.

        :param str service_id: ID of the service in question

        :return: list of collection entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        collections = [
            collection
            for collection in self.api.get_collections(service_id=service_id)
            if context.account.can_read(collection.name)]
        return collections

    def get_collection(self, name, service_id=None):
        '''Get a collection by name and service ID.

        Collection name is unique globally, so can be used as a key.
        Method retrieves collection entity using collection name
        ``name`` and service ID ``service_id`` as a composite key.

        :param str name: a collection name
        :param str service_id: ID of a service

        :return: collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        collection = self.api.get_collection(name, service_id=service_id)
        if collection and context.account.can_read(collection.name):
            return collection

    def update_collection(self, collection):
        '''Update a collection

        :param `opentaxii.taxii.entities.CollectionEntity` collection_entity:
            collection entity object

        :return: updated collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        return self.api.update_collection(collection)

    def create_inbox_message(self, entity):
        '''Create an inbox message.

        Methods emits :py:const:`opentaxii.signals.INBOX_MESSAGE_CREATED`
        signal.

        :param `opentaxii.taxii.entities.InboxMessageEntity` entity:
            inbox message entity in question
        :return: updated inbox message entity
        :rtype: :py:class:`opentaxii.taxii.entities.InboxMessageEntity`
        '''

        if self.server.config['save_raw_inbox_messages']:
            entity = self.api.create_inbox_message(entity)
            INBOX_MESSAGE_CREATED.send(self, inbox_message=entity)

        return entity

    def create_content(self, content, service_id=None, inbox_message_id=None,
                       collections=None):
        '''Create a content block.

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
        '''
        if inbox_message_id:
            content.inbox_message_id = inbox_message_id

        collections = collections or []
        collection_ids = [
            collection.id
            for collection in collections
            if context.account.can_modify(collection.name)]

        if collection_ids:
            content = self.api.create_content_block(
                content, collection_ids=collection_ids, service_id=service_id)
            CONTENT_BLOCK_CREATED.send(
                self, content_block=content,
                collection_ids=collection_ids, service_id=service_id)
        else:
            log.warning(
                "create_content.unknown_collections",
                collections=[c.name for c in collections],
                user=context.account)

        return content

    def get_content_blocks_count(self, collection_id, start_time=None,
                                 end_time=None, bindings=None):
        '''Get a count of the content blocks associated with a collection.

        :param str collection_id: ID fo a collection in question
        :param datetime start_time: start of a time frame
        :param datetime end_time: end of a time frame
        :param list bindings: list of
            :py:class:`opentaxii.taxii.entities.ContentBindingEntity`

        :return: content block count
        :rtype: int
        '''
        return self.api.get_content_blocks_count(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings or [])

    def get_content_blocks(self, collection_id, start_time=None, end_time=None,
                           bindings=None, offset=0, limit=None):
        '''Get the content blocks associated with a collection.

        :param str collection_id: ID fo a collection in question
        :param datetime start_time: start of a time frame
        :param datetime end_time: end of a time frame
        :param list bindings: list of
            :py:class:`opentaxii.taxii.entities.ContentBindingEntity`
        :param int offset: result set offset
        :param int limit: result set max size

        :return: content blocks list
        :rtype: list of :py:class:`opentaxii.taxii.entities.ContentBlockEntity`
        '''

        return self.api.get_content_blocks(
            collection_id=collection_id,
            start_time=start_time,
            end_time=end_time,
            bindings=bindings or [],
            offset=offset,
            limit=limit)

    def create_result_set(self, entity):
        '''Create a result set.

        :param `opentaxii.taxii.entities.ResultSetEntity` entity:
            result set entity in question

        :return: updated result set entity
        :rtype: :py:class:`opentaxii.taxii.entities.ResultSetEntity`
        '''
        return self.api.create_result_set(entity)

    def get_result_set(self, result_set_id):
        '''Get a result set entity by ID.

        :param str result_set_id: ID of a result set.

        :return: result set entity
        :rtype: :py:class:`opentaxii.taxii.entities.ResultSetEntity`
        '''
        return self.api.get_result_set(result_set_id)

    def create_subscription(self, entity):
        '''Create a subscription.

        Methods emits :py:const:`opentaxii.signals.SUBSCRIPTION_CREATED`
        signal.

        :param `opentaxii.taxii.entities.SubscriptionEntity` entity:
            subscription entity in question.

        :return: updated subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''

        created = self.api.create_subscription(entity)

        SUBSCRIPTION_CREATED.send(self, subscription=created)

        return created

    def get_subscription(self, subscription_id):
        '''Get a subscription entity by ID.

        :param str subscription_id: ID of a subscription

        :return: subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        return self.api.get_subscription(subscription_id)

    def get_subscriptions(self, service_id):
        '''Get the subscriptions attached to/created via a service.

        :param str service_id: ID of a service

        :return: list of subscription entities
        :rtype: list of :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        return self.api.get_subscriptions(service_id=service_id)

    def update_subscription(self, subscription):
        '''Update a subscription status.

        :param `opentaxii.taxii.entities.SubscriptionEntity` subscription:
            subscription entity in question

        :return: updated subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        return self.api.update_subscription(subscription)

    def get_domain(self, service_id):
        '''Get configured domain name needed to create absolute URLs.

        :param str service_id: ID of a service
        '''
        return self.api.get_domain(service_id)

    def delete_content_blocks(
            self, collection_name, start_time, end_time=None,
            with_messages=False):
        '''Delete content blocks in a specified collection with
        timestamp label in a specified time frame.

        :param str collection_name: collection name
        :param datetime start_time: exclusive beginning of a timeframe
        :param datetime end_time: inclusive end of a timeframe
        :param bool with_messages: delete related inbox messages

        :return: the count of rows deleted
        :rtype: int
        '''
        count = self.api.delete_content_blocks(
            collection_name, start_time, end_time=end_time,
            with_messages=with_messages)
        log.info(
            "collection.content_blocks.deleted",
            with_messages=with_messages,
            collection=collection_name,
            count=count)
        return count
