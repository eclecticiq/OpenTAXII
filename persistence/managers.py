
from taxii.entities import *
from .sql.storage import save_entity, get_all_collections, add_content_block

import hooks

class DataCollectionManager(object):

    @staticmethod
    def add_content_block(collection_entity, content_block_entity):
        add_content_block(content_block_entity.id, [collection_entity.id])

    @staticmethod
    def get_all_collections():
        return get_all_collections()


    @staticmethod
    def save_data_collection(collection_entity):
        return save_entity(collection_entity)


class ContentBlockManager(object):

    @staticmethod
    def save_content_block(content_block, inbox_message_entity=None, collections=[], version=10):

        content_block_entity = ContentBlockEntity.to_entity(content_block, inbox_message_entity=inbox_message_entity, version=version)
        content_block_entity = save_entity(content_block_entity)

        if version == 11:
            for collection in collections:
                DataCollectionManager.add_content_block(collection, content_block_entity)

        hooks.post_content_block_save(content_block_entity, inbox_message_entity, collections)




class InboxMessageManager(object):

    @staticmethod
    def save_inbox_message(inbox_message, received_via=None, version=10):

        return save_entity(InboxMessageEntity.to_entity(inbox_message, received_via=received_via, version=version))
