import sqlalchemy
from sqlalchemy import orm, engine

from taxii_server.taxii.entities import *

from . import models


class SQLDB(object):

    def __init__(self, db_connection_string, create_tables=False):

        self.engine = engine.create_engine(db_connection_string, convert_unicode=True)

        self.Session = orm.scoped_session(orm.sessionmaker(autocommit=False,
            autoflush=True, bind=self.engine))

        include_all(self, models)

        self.Base.query = self.Session.query_property()

        if create_tables:
            self.create_all_tables()


    def create_all_tables(self):
        self.Base.metadata.create_all(bind=self.engine)


    def add_content_block(self, content_block, collections):

        if not collections:
            return

        s = self.Session()
        content_block_obj = self.ContentBlock.query.get(content_block.id)

        criteria = self.DataCollection.id.in_([c.id for c in collections])

        for collection in self.DataCollection.query.filter(criteria):
            collection.content_blocks.append(content_block_obj)
            s.add(collection)

        s.commit()


    def get_collections(self, inbox_id=None):

        query = self.DataCollection.query
        if inbox_id:
            query = query.filter_by(inbox_id=inbox_id)

        return collections_to_entities(query.all())


    def get_collection(self, name):

        collections = self.DataCollection.filter_by(name=name).all()

        return collections_to_entities(collections)


    def get_content_blocks(self, collection_id=None):

        if collection_id:
            collection = self.DataCollection.query.get(collection_id)
            content_blocks = collection.content_blocks

        content_blocks = self.ContentBlock.query.all()

        return blocks_to_entities(content_blocks)


    def save_entity(self, entity):
        if isinstance(entity, DataCollectionEntity):
            model_cls = self.DataCollection
        elif isinstance(entity, ContentBlockEntity):
            model_cls = self.ContentBlock
        elif isinstance(entity, InboxMessageEntity):
            model_cls = self.InboxMessage

        model = entity_to_model(entity, model_cls)

        s = self.Session()
        s.add(model)
        s.commit()

        return model_to_entity(model, entity.__class__)



def include_all(obj, module):
    for key in module.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(module, key))
    return obj


def entity_to_model(entity, model_cls):
    return model_cls(**entity._asdict())


def model_to_entity(model, entity_cls):
    params = dict()
    for k in entity_cls._fields:
        params[k] = getattr(model, k, None)
    return entity_cls(**params)


def collections_to_entities(collections):
    return map(lambda o: model_to_entity(o, DataCollectionEntity), collections)

def blocks_to_entities(blocks):
    return map(lambda o: model_to_entity(o, ContentBlockEntity), blocks)

