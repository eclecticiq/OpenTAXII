import sqlalchemy
from sqlalchemy import orm, engine


from taxii_server.taxii.entities import *


class SQLDB(object):

    def __init__(self, db_connection_string):

        self.engine = engine.create_engine(db_connection_string, convert_unicode=True)
        self.Session = orm.scoped_session(orm.sessionmaker(autocommit=False, autoflush=True, bind=self.engine))

        import models
        include_all(self, models)

        self.Base.query = self.Session.query_property()


    def create_all_tables(self):
        self.Base.metadata.create_all(bind=self.engine)


    def add_content_block(content_block_id, collection_ids):
        if not collection_ids:
            return
        s = Session()
        content_block = self.ContentBlock.query.get(content_block_id)
        for collection in self.DataCollection.query.filter(DataCollection.id.in_(collection_ids)):
            collection.content_blocks.append(content_block)
            s.add(collection)
        s.commit()


    def get_all_collections(self):
        return map(lambda o: model_to_entity(o, DataCollectionEntity), self.DataCollection.query.all())


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


