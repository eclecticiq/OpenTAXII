
from blinker import signal

from ..signals import POST_SAVE_CONTENT_BLOCK


class DataManager(object):

    def __init__(self, api):
        self.api = api

    ### These methods only used in the scripts provided with OpenTAXII

    def create_service(self, entity):
        return self.api.create_service(entity)

    def attach_collection_to_services(self, collection_id, services_ids):
        return self.api.attach_collection_to_services(collection_id, services_ids)

    ####

    def get_services(self):
        return self.api.get_services()

    def get_services_for_collection(self, collection, service_type):
        return self.api.get_services(collection_id=collection.id,
                service_type=service_type)

    def get_collections(self, service_id=None):
        return self.api.get_collections(service_id=service_id)

    def get_collection(self, name, service_id):
        return self.api.get_collection(name, service_id)

    def create_collection(self, entity):
        return self.api.create_collection(entity)

    def create_inbox_message(self, entity):
        return self.api.create_inbox_message(entity)

    def create_content(self, content, service_id=None, inbox_message=None,
            collections=[]):

        if inbox_message:
            if not inbox_message.id:
                inbox_message = self.api.create_inbox_message(inbox_message)
            content.inbox_message_id = inbox_message.id

        content = self.api.create_content_block(content)

        collection_ids = [c.id for c in collections]

        if collection_ids:
            self.api.attach_content_to_collections(content, collection_ids)

        signal(POST_SAVE_CONTENT_BLOCK).send(self, content_block=content,
                collection_ids=collection_ids)

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
        return self.api.create_subscription(subscription, service_id=service_id)

    def get_subscription(self, subscription_id):
        return self.api.get_subscription(subscription_id)

    def get_subscriptions(self, service_id):
        return self.api.get_subscriptions(service_id=service_id)

    def update_subscription(self, subscription, new_status):
        subscription.status = new_status
        return self.api.update_subscription(subscription)

