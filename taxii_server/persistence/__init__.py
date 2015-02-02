
from ..signals import POST_SAVE_CONTENT_BLOCK

from blinker import signal


class DataStorage(object):

    def __init__(self, api):
        self.api = api

    def get_collections(self, inbox_id=None):
        return self.api.get_collections(inbox_id=inbox_id)


    def save_collection(self, collection_entity):
        return self.api.save_entity(collection_entity)


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
