
import sqlalchemy
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from taxii.bindings import *
from taxii.entities import *

from settings import DB_CONNECTION_STRING

engine = create_engine(DB_CONNECTION_STRING, convert_unicode=True)
Session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))

from .models import *

Base.query = Session.query_property()
Base.metadata.create_all(bind=engine)


def __data_collection_to_model(entity):
    return DataCollection(**entity._asdict())


def __content_block_to_model(entity):
    params = entity._asdict()
    return ContentBlock(**params)


def __content_block_to_entity(model):
    params = dict()
    for k in ContentBlockEntity._fields:
        params[k] = getattr(model, k, None)
    return ContentBlockEntity(**params)


def __inbox_message_to_entity(model):
    params = dict()
    for k in InboxMessageEntity._fields:
        params[k] = getattr(model, k, None)
    return InboxMessageEntity(**params)


def __data_collection_to_entity(model):
    params = dict()
    for k in DataCollectionEntity._fields:
        params[k] = getattr(model, k, None)
    return DataCollectionEntity(**params)


def __inbox_message_to_model(entity):
    return InboxMessage(**entity._asdict())

Converter = namedtuple('Converter', 'to_model to_entity')


_converters = {
    DataCollectionEntity : Converter(to_model=__data_collection_to_model, to_entity=__data_collection_to_entity),
    ContentBlockEntity : Converter(to_model=__content_block_to_model, to_entity=__content_block_to_entity),
    InboxMessageEntity : Converter(to_model=__inbox_message_to_model, to_entity=__inbox_message_to_entity)
}


def get_all_collections(inbox_id=1):
    return map(_converters[DataCollectionEntity].to_entity, DataCollection.query.all())

def save_entity(entity):
    model = _to_model(entity)

    s = Session()
    s.add(model)
    s.commit()

    return _to_entity(entity.__class__, model)


def _to_model(entity):
    return _converters[entity.__class__].to_model(entity)


def _to_entity(entity_class, model):
    return _converters[entity_class].to_entity(model)


def add_content_block(content_block_id, collection_ids):
    if not collection_ids:
        return
    s = Session()
    content_block = ContentBlock.query.get(content_block_id)
    for collection in DataCollection.query.filter(DataCollection.id.in_(collection_ids)):
        collection.content_blocks.append(content_block)
        s.add(collection)
    s.commit()




