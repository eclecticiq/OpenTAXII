
class OpenTAXIIPersistenceAPI(object):
    '''Abstract class that represents OpenTAXII Persistence API.

    This class defines required methods that need to exist in
    a specific Persistence API implementation.
    '''

    def init_app(self, app):
        pass

    def create_service(self, service_entity):
        '''Create a service.

        NOTE: Additional data management method that is not used
        in TAXII server logic but only in helper scripts.

        :param `opentaxii.taxii.entities.ServiceEntity` service_entity:
            service entity in question
        :return: updated service entity, with ID field not None
        :rtype: :py:class:`opentaxii.taxii.entities.ServiceEntity`
        '''
        raise NotImplementedError()

    def create_collection(self, collection_entity):
        '''Create a collection.

        NOTE: Additional data management method that is not used
        in TAXII server logic but only in helper scripts.

        :param `opentaxii.taxii.entities.CollectionEntity` collection_entity:
            collection entity in question
        :return: updated collection entity, with ID field not None
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        raise NotImplementedError()

    def attach_collection_to_services(self, collection_id, service_ids):
        '''Attach collection to the services.

        NOTE: Additional data management method that is not used
        in TAXII server logic but only in helper scripts.

        :param str collection_id: collection entity in question
        :param list service_ids: collection entity in question
        :return: updated collection entity, with ID field not None
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        raise NotImplementedError()

    def get_services(self, collection_id=None):
        '''Get the configured services.

        :param str collection_id: get only services assigned to
                                  collection with provided ID

        :return: list of service entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.ServiceEntity`
        '''
        raise NotImplementedError()

    def get_collections(self, service_id):
        '''Get the collections attached to a service.

        :param str service_id: ID of a service in question

        :return: list of collection entities.
        :rtype: list of :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        raise NotImplementedError()

    def get_collection(self, collection_name, service_id):
        '''Get a collection by name and service ID.

        According to TAXII spec collection name is unique per service instance.
        Method retrieves collection entity using collection name
        ``collection_name`` and service ID ``service_id`` as a composite key.

        :param str collection_name: a collection name
        :param str service_id: ID of a service

        :return: collection entity
        :rtype: :py:class:`opentaxii.taxii.entities.CollectionEntity`
        '''
        raise NotImplementedError()

    def create_inbox_message(self, inbox_message_entity):
        '''Create an inbox message.

        :param `opentaxii.taxii.entities.InboxMessageEntity` \
            inbox_message_entity: inbox message entity in question
        :return: updated inbox message entity
        :rtype: :py:class:`opentaxii.taxii.entities.InboxMessageEntity`
        '''
        raise NotImplementedError()

    def create_content_block(self, content_block_entity, collection_ids=None,
                             service_id=None):
        '''Create a content block.

        :param `opentaxii.taxii.entities.ContentBlockEntity` \
            content_block_entity: content block in question
        :param list collection_ids: a list of collection IDs as strings
        :param str service_id: ID of an inbox service via which content
            block was created

        :return: updated content block entity
        :rtype: :py:class:`opentaxii.taxii.entities.ContentBlockEntity`
        '''
        raise NotImplementedError()

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
        raise NotImplementedError()

    def get_content_blocks(self, collection_id, start_time=None, end_time=None,
                           bindings=None, offset=0, limit=10):
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
        raise NotImplementedError()

    def create_result_set(self, result_set_entity):
        '''Create a result set.

        :param `opentaxii.taxii.entities.ResultSetEntity` result_set_entity:
            result set entity in question

        :return: updated result set entity
        :rtype: :py:class:`opentaxii.taxii.entities.ResultSetEntity`
        '''
        raise NotImplementedError()

    def get_result_set(self, result_set_id):
        '''Get a result set entity by ID.

        :param str result_set_id: ID of a result set.

        :return: result set entity
        :rtype: :py:class:`opentaxii.taxii.entities.ResultSetEntity`
        '''
        raise NotImplementedError()

    def create_subscription(self, subscription_entity):
        '''Create a subscription.

        :param `opentaxii.taxii.entities.SubscriptionEntity` \
            subscription_entity: subscription entity in question.

        :return: updated subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        raise NotImplementedError()

    def get_subscription(self, subscription_id):
        '''Get a subscription entity by ID.

        :param str subscription_id: ID of a subscription

        :return: subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        raise NotImplementedError()

    def get_subscriptions(self, service_id):
        '''Get the subscriptions attached to/created via a service.

        :param str service_id: ID of a service

        :return: list of subscription entities
        :rtype: list of :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        raise NotImplementedError()

    def update_subscription(self, subscription_entity):
        '''Update a subscription status.

        :param `opentaxii.taxii.entities.SubscriptionEntity` \
            subscription_entity: subscription entity in question

        :return: updated subscription entity
        :rtype: :py:class:`opentaxii.taxii.entities.SubscriptionEntity`
        '''
        raise NotImplementedError()

    def get_domain(self, service_id):
        '''Get configured domain needed to create absolute URLs.

        Returns `None` by default.

        :param str service_id: ID of a service
        '''
        return None

    def delete_content_blocks(self, collection_name, start_time,
                              end_time=None):
        '''Delete content blocks in a specified collection with
        timestamp label in a specified time frame.

        :param str collection_name: collection name
        :param datetime start_time: exclusive beginning of a timeframe
        :param datetime end_time: inclusive end of a timeframe
        '''
        pass
