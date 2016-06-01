import structlog
from opentaxii.signals import (
    CONTENT_BLOCK_CREATED, INBOX_MESSAGE_CREATED,
    SUBSCRIPTION_CREATED
)
from opentaxii.taxii.converters import blob_to_service_entity

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

    # Methods only used in the CLI scripts provided with OpenTAXII.

    def create_service(self, entity):
        '''Create a service.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        return self.api.create_service(entity)

    def attach_collection_to_services(self, collection_id, service_ids):
        '''Attach collection to the services.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        return self.api.attach_collection_to_services(
            collection_id, service_ids)

    def create_collection(self, entity):
        '''Create a collection.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''
        collection = self.api.create_collection(entity)
        log.info("collection.created", collection=collection.name)
        return collection

    def create_services_from_object(self, services_config):
        '''Create services from configuration object and persis them.

        NOTE: Additional method that is only used in the helper scripts
        shipped with OpenTAXII.
        '''

        for blob in services_config:
            service = blob_to_service_entity(blob)
            self.create_service(service)

            log.info("service.created", id=service.id, type=service.type)

    # =================================================================

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

        return self.api.get_services(collection_id=collection.id)

    def get_collections(self, service_id):
        '''Get the collections associated with a service.

        :param str service_id: ID of the service in question

        :return: list of collection entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''

        return self.api.get_collections(service_id)

    def get_collection(self, name, service_id):
        '''Get a collection by name and service ID.

        According to TAXII spec collection name is unique per service instance.
        Method retrieves collection entity using collection name
        ``name`` and service ID ``service_id`` as a composite key.

        :param str name: a collection name
        :param str service_id: ID of a service

        :return: collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        return self.api.get_collection(name, service_id)

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
        collection_ids = [c.id for c in collections]
        content = self.api.create_content_block(
            content, collection_ids=collection_ids, service_id=service_id)

        CONTENT_BLOCK_CREATED.send(
            self, content_block=content,
            collection_ids=collection_ids, service_id=service_id)

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
            bindings=bindings or [],
        )

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
            limit=limit,
        )

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

    def delete_content_blocks(self, collection_name, start_time,
                              end_time=None):
        '''Delete content blocks in a specified collection with
        timestamp label in a specified time frame.

        :param str collection_name: collection name
        :param datetime start_time: exclusive beginning of a timeframe
        :param datetime end_time: inclusive end of a timeframe

        :return: the count of rows deleted
        :rtype: int
        '''
        count = self.api.delete_content_blocks(
            collection_name, start_time, end_time=end_time)

        log.info(
            "collection.content_blocks.deleted",
            collection=collection_name,
            count=count)

        return count
