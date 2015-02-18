
from ..signals import POST_SAVE_CONTENT_BLOCK

from blinker import signal


class DataManager(object):

    def __init__(self, config, api):
        self.config = config
        self.api = api

        for _type, id, props in config.services:
            self.create_service(_type, props, id=id)

    def create_service(self, type, properties, id=None):
        self.api.save_service(id=id, type=type, properties=properties)
    

    def get_services(self):
        return self.api.get_services()


    def get_service_ids_for_collection(self, collection, service_type):
        services = self.api.get_services(collection_id=collection.id,
                service_type=service_type)

        return map(lambda (type, id, opts): id, services)


    def get_collections(self, service_id=None):
        return self.api.get_collections(service_id=service_id)


    def save_collection(self, entity):
        return self.api.save_collection(entity)


    def assign_collection(self, entity, services_ids):
        return self.api.assign_collection(entity, services_ids)


    def save_content_block(self, content_block_entity, inbox_message_entity, collections=[]):

        content_block_entity = self.api.save_entity(content_block_entity)

        self.api.add_content_block(content_block_entity, collections)

        signal(POST_SAVE_CONTENT_BLOCK).send(self, content_block=content_block_entity,
                inbox_message=inbox_message_entity, collections=collections)


    def get_content_blocks(self, collection=None):
        cid = collection.id if collection else None
        return self.api.get_content_blocks(collection_id=cid)


    def save_inbox_message(self, inbox_message):
        return self.api.save_entity(inbox_message)
