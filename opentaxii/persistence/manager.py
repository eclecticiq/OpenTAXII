
from ..signals import (
    CONTENT_BLOCK_CREATED, INBOX_MESSAGE_CREATED,
    SUBSCRIPTION_CREATED
)
from ..taxii.converters import blob_to_service_entity


class PersistenceManager(object):

    def __init__(self, api):
        self.api = api

    # These methods only used in the CLI scripts provided with OpenTAXII

    def create_service(self, entity):
        return self.api.create_service(entity)

    def attach_collection_to_services(self, collection_id, services_ids):
        return self.api.attach_collection_to_services(collection_id, services_ids)

    # ====

    def get_services(self):
        return self.api.get_services()

    def get_services_for_collection(self, collection):
        return self.api.get_services(collection_id=collection.id)

    def get_collections(self, service_id):
        return self.api.get_collections(service_id)

    def get_collection(self, name, service_id):
        return self.api.get_collection(name, service_id)

    def create_collection(self, entity):
        return self.api.create_collection(entity)

    def create_inbox_message(self, entity):
        created = self.api.create_inbox_message(entity)

        INBOX_MESSAGE_CREATED.send(self, inbox_message=created)

        return created

    def create_content(self, content, service_id=None, inbox_message=None,
            collections=[]):

        if inbox_message:
            if not inbox_message.id:
                inbox_message = self.api.create_inbox_message(inbox_message)
            content.inbox_message_id = inbox_message.id

        collection_ids = [c.id for c in collections]
        content = self.api.create_content_block(content, collection_ids=collection_ids)

        CONTENT_BLOCK_CREATED.send(self, content_block=content,
                collection_ids=collection_ids, service_id=service_id)

        return content

    def get_content_blocks_count(self, collection_id, start_time=None, end_time=None,
            bindings=[]):

        return self.api.get_content_blocks_count(
            collection_id = collection_id,
            start_time = start_time,
            end_time = end_time,
            bindings = bindings,
        )

    def get_content_blocks(self, collection_id, start_time=None, end_time=None,
            bindings=[], offset=0, limit=10):

        return self.api.get_content_blocks(
            collection_id = collection_id,
            start_time = start_time,
            end_time = end_time,
            bindings = bindings,
            offset = offset,
            limit = limit,
        )


    def create_result_set(self, result_set_entity):
        return self.api.create_result_set(result_set_entity)

    def get_result_set(self, result_set_id):
        return self.api.get_result_set(result_set_id)

    def create_subscription(self, subscription, service_id=None):
        created = self.api.create_subscription(subscription,
                service_id=service_id)

        SUBSCRIPTION_CREATED.send(self, subscription=created, service_id=service_id)
        return created


    def get_subscription(self, subscription_id):
        return self.api.get_subscription(subscription_id)

    def get_subscriptions(self, service_id):
        return self.api.get_subscriptions(service_id=service_id)

    def update_subscription(self, subscription, new_status):
        subscription.status = new_status
        return self.api.update_subscription(subscription)

    def create_services_from_object(self, services_config):

        for blob in services_config:
            self.create_service(blob_to_service_entity(blob))

