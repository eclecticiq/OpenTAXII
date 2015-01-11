from ..taxii.entities import *
from ..signals import POST_SAVE_CONTENT_BLOCK

from blinker import signal


class DataStorage(object):

    def __init__(self, db):
        self.db = db

    def get_all_collections(self):
        return self.db.get_all_collections()

    def save_data_collection(self, collection_entity):
        return self.db.save_entity(collection_entity)

    def save_content_block(self, content_block, inbox_message_entity=None, collections=[], version=10):

        content_block_entity = ContentBlockEntity.to_entity(content_block, inbox_message_entity=inbox_message_entity, version=version)
        content_block_entity = self.db.save_entity(content_block_entity)

        if version == 11:
            for collection in collections:
                self.db.add_content_block(content_block_entity.id, [collection_entity.id])

        post_save = signal(POST_SAVE_CONTENT_BLOCK)

        post_save.send(self, content_block=content_block_entity, inbox_message=inbox_message_entity,
                collections=collections)



    def save_inbox_message(self, inbox_message, received_via=None, version=10):
        return self.db.save_entity(InboxMessageEntity.to_entity(inbox_message, received_via=received_via, version=version))
