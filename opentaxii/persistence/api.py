
class OpenTAXIIPersistenceAPI(object):

    def create_service(self, service_entity):
        raise NotImplementedError()

    def get_services(self, collection_id=None, service_type=None):
        raise NotImplementedError()

    def get_collections(self, service_id):
        raise NotImplementedError()

    def get_collection(self, collection_name, service_id):
        raise NotImplementedError()

    def create_collection(self, collection_entity):
        raise NotImplementedError()

    def attach_collection_to_services(self, collection_id, services_ids):
        raise NotImplementedError()

    def create_inbox_message(self, inbox_message_entity): 
        raise NotImplementedError()

    def create_content_block(self, content_block_entity, collection_ids=None): 
        raise NotImplementedError()

    def get_content_blocks_count(self, collection_id, start_time=None,
            end_time=None, bindings=[]):
        raise NotImplementedError()

    def get_content_blocks(self, collection_id, start_time=None, end_time=None,
            bindings=[], offset=0, limit=10):
        raise NotImplementedError()

    def create_result_set(self, result_set_entity):
        raise NotImplementedError()

    def get_result_set(self, result_set_id):
        raise NotImplementedError()

    def create_subscription(self, subscription_entity, service_id=None):
        raise NotImplementedError()

    def get_subscription(self, subscription_id):
        raise NotImplementedError()

    def get_subscriptions(self, service_id):
        raise NotImplementedError()

    def update_subscription(self, subscription_entity, service_id=None):
        raise NotImplementedError()

