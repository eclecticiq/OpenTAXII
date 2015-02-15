import sqlalchemy
from sqlalchemy import orm, engine

from taxii_server.taxii.entities import *

from . import models


class SQLDB(object):

    def __init__(self, db_connection, create_tables=False):

        self.engine = engine.create_engine(db_connection, convert_unicode=True)

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


    def get_services(self, collection_id=None, service_type=None):

        query = self.Service.query

        if collection_id:
            query = query.filter(self.Service.collections.any(id=collection_id))

        if service_type:
            query = query.filter_by(type=service_type)

        return [(s.type, s.id, s.properties) for s in query.all()]
 

    def get_collections(self, service_id=None):

        if service_id:
            service = self.Service.query.get(service_id)
            collections = service.collections
        else:
            collections = self.DataCollection.query.all()

        return map(to_collection_entity, collections)


    def get_collection(self, name):

        collections = self.DataCollection.filter_by(name=name).all()
        return map(to_collection_entity, collections)


    def get_content_blocks(self, collection_id=None):

        if collection_id:
            collection = self.DataCollection.query.get(collection_id)
            content_blocks = collection.content_blocks

        content_blocks = self.ContentBlock.query.all()

        return blocks_to_entities(content_blocks)


    def save_collection(self, entity):

        coll = entity_to_model(entity, self.DataCollection)

        s = self.Session()
        coll = s.merge(coll)
        s.commit()

        return to_collection_entity(coll)


    def assign_collection(self, entity, services_ids):

        coll = self.DataCollection.query.get(entity.id)

        s = self.Session()

        for sid in services_ids:
            service = self.Service.query.get(sid)
            service.collections.append(coll)
            s.add(service)

        s.commit()


    def get_service(self, id):
        s = self.Service.get(id)
        if s:
            return (s.type, s.id, s.properties)

    def save_service(self, type, properties, id=None):

        service = self.Service(id=id, type=type, properties=properties)
        s = self.Session()
        s.merge(service)
        s.commit()

        return service



    def save_entity(self, entity):
        if isinstance(entity, CollectionEntity):
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
    if hasattr(entity, '_asdict'):
        return model_cls(**entity._asdict())
    return model_cls(**entity.as_dict())


def model_to_entity(model, entity_cls):
    params = dict()
    for k in entity_cls._fields:
        params[k] = getattr(model, k, None)
    return entity_cls(**params)


def to_collection_entity(model):
    return CollectionEntity(
        id = model.id,
        name = model.name,
        available = model.available,
        type = model.type,
        description = model.description,
        accept_all_content = model.accept_all_content,
        supported_content = model.supported_content
    )


def blocks_to_entities(blocks):
    return map(lambda o: model_to_entity(o, ContentBlockEntity), blocks)

