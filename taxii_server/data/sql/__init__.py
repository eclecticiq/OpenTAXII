import json
import pytz
from sqlalchemy import orm, engine
from sqlalchemy import and_

from sqlalchemy.orm import exc

from taxii_server.taxii.entities import *

from . import models

import structlog

log = structlog.getLogger(__name__)


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


    def _merge(self, object):
        s = self.Session()
        updated = s.merge(object)
        s.commit()
        return updated



    def add_content(self, content_block, collection_ids):

        if not collection_ids:
            return

        s = self.Session()
        content_block_obj = self.ContentBlock.query.get(content_block.id)

        criteria = self.DataCollection.id.in_(collection_ids)
        collections = self.DataCollection.query.filter(criteria).all()

        if not collections:
            raise ValueError("No collection were found with ids: %s" % collection_ids)

        for collection in collections:
            collection.content_blocks.append(content_block_obj)
            s.add(collection)

            log.debug("Content block added to collection", content_block_id=content_block.id, collection_id=collection.id, collection_name=collection.name)

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


    def get_collection(self, name, service_id):

        service = self.Service.query.get(service_id)

        for c in service.collections:
            if c.name == name:
                return to_collection_entity(c)


    def _get_content_query(self, collection_id=None, start_time=None,
            end_time=None, bindings=[]):

        query = self.ContentBlock.query

        if collection_id:
            query = query.filter(self.ContentBlock.collections.any(id=collection_id))

        if start_time:
            query = query.filter(self.ContentBlock.date_created > start_time)

        if end_time:
            query = query.filter(self.ContentBlock.date_created <= end_time)

        if bindings:
            #FIXME: not implemented
            pass

        return query


    def get_content_count(self, collection_id=None, start_time=None,
            end_time=None, bindings=[]):

        return self._get_content_query(collection_id=collection_id, start_time=start_time,
                end_time=end_time, bindings=bindings).count()


    def get_content(self, collection_id=None, count_only=False, start_time=None,
            end_time=None, bindings=[], offset=0, limit=10):

        query = self._get_content_query(collection_id=collection_id, start_time=start_time,
                end_time=end_time, bindings=bindings)
        
        blocks = query[offset : offset + limit]

        return map(to_block_entity, blocks)


    def save_collection(self, entity):

        collection = self.DataCollection(
            id = entity.id,
            name = entity.name,
            type = entity.type,
            description = entity.description,
            available = entity.available,
            accept_all_content = entity.accept_all_content,
            bindings = serialize_content_bindings(entity.supported_content)
        )

        updated = self._merge(collection)

        log.debug("Collection saved", collection_id=updated.id, collection_name=updated.name)

        return to_collection_entity(updated)


    def assign_collection(self, collection_id, services_ids):
        
        if not collection_id:
            raise Exception('Collection does not exists!')

        collection = self.DataCollection.query.get(collection_id)

        s = self.Session()

        for sid in services_ids:
            service = self.Service.query.get(sid)
            collection.services.append(service)

        s.add(collection)
        s.commit()

        log.debug("Collection attached to services", collection_id=collection.id, collection_name=collection.name, service_ids=services_ids)



    def get_service(self, id):
        s = self.Service.get(id)
        if s:
            return (s.type, s.id, s.properties)


    def save_service(self, type, properties, id=None):
        service = self.Service(id=id, type=type, properties=properties)
        self._merge(service)


    def save_inbox_message(self, entity, service_id=None):

        if entity.destination_collections:
            names = json.dumps(entity.destination_collections) 
        else:
            names = None

        message = self.InboxMessage(
            id = entity.id,
            message_id = entity.message_id,
            original_message = entity.original_message,
            content_block_count = entity.content_block_count,
            destination_collections = names,

            result_id = entity.result_id,
            record_count = entity.record_count,
            partial_count = entity.partial_count,

            subscription_collection_name = entity.subscription_collection_name,
            subscription_id = entity.subscription_id,

            exclusive_begin_timestamp_label = entity.exclusive_begin_timestamp_label,
            inclusive_end_timestamp_label = entity.inclusive_end_timestamp_label,
        )

        updated = self._merge(message)

        return to_inbox_message_entity(updated)



    def save_content(self, entity):

        if entity.content_binding:
            binding = entity.content_binding.binding
            subtype = entity.content_binding.subtypes[0] \
                    if entity.content_binding.subtypes else None
        else:
            binding = None
            subtype = None

        content = self.ContentBlock(
            id = entity.id,
            timestamp_label = entity.timestamp_label,
            inbox_message_id = entity.inbox_message_id,
            content = entity.content,
            binding_id = binding,
            binding_subtype = subtype
        )

        updated = self._merge(content)

        return to_block_entity(updated)


    def save_result_set(self, entity):

        result_set = self.ResultSet(
            id = entity.result_id,
            collection_id = entity.collection_id,
            bindings = serialize_content_bindings(entity.content_bindings),
            begin_time = entity.timeframe[0],
            end_time = entity.timeframe[1]
        )

        updated = self._merge(result_set)

        return to_result_set_entity(updated)


    def get_result_set(self, result_set_id):
        result_set = self.ResultSet.query.get(result_set_id)
        if result_set:
            return to_result_set_entity(result_set)


    def get_subscription(self, subscription_id):
        s = self.Subscription.query.get(subscription_id)
        if s:
            return to_subscription_entity(s)


    def save_subscription(self, entity):

        if entity.params:
            params = entity.params.as_dict()
            if params['content_bindings']:
                params['content_bindings'] = serialize_content_bindings(params['content_bindings'])

        subscription = self.Subscription(
            id = entity.subscription_id,
            collection_id = entity.collection_id,
            params = json.dumps(params),
            status = entity.status
        )


        updated = self._merge(subscription)

        log.debug("Subscription saved", subscription_id=updated.id, collection_id=updated.collection_id, status=updated.status)

        return to_subscription_entity(updated)


def include_all(obj, module):
    for key in module.__all__:
        if not hasattr(obj, key):
            setattr(obj, key, getattr(module, key))
    return obj


def to_collection_entity(model):
    return CollectionEntity(
        id = model.id,
        name = model.name,
        available = model.available,
        type = model.type,
        description = model.description,
        accept_all_content = model.accept_all_content,
        supported_content = deserialize_content_bindings(model.bindings)
    )


def to_block_entity(model):

    subtypes = [model.binding_subtype] if model.binding_subtype else None

    return ContentBlockEntity(
        id = model.id,
        content = model.content,

        timestamp_label = enforce_timezone(model.timestamp_label),
        content_binding = ContentBindingEntity(model.binding_id, subtypes=subtypes),
        message = model.message,
        inbox_message_id = model.inbox_message_id,
    )

def to_inbox_message_entity(model):

    if model.destination_collections:
        names = json.loads(model.destination_collections) 
    else:
        names = []

    return InboxMessageEntity(
        id = model.id,
        message_id = model.message_id,
        original_message = model.original_message,
        content_block_count = model.content_block_count,
        destination_collections = names,

        result_id = model.result_id,
        record_count = model.record_count,
        partial_count = model.partial_count,

        subscription_collection_name = model.subscription_collection_name,
        subscription_id = model.subscription_id,

        exclusive_begin_timestamp_label = enforce_timezone(model.exclusive_begin_timestamp_label),
        inclusive_end_timestamp_label = enforce_timezone(model.inclusive_end_timestamp_label),
    )

def to_result_set_entity(model):
    return ResultSetEntity(
        result_id = model.id,
        collection_id = model.collection_id,
        content_bindings = deserialize_content_bindings(model.bindings),
        timeframe = map(enforce_timezone, (model.begin_time, model.end_time))
    )


def to_subscription_entity(model):

    if model.params:
        parsed = dict(json.loads(model.params))
        if parsed['content_bindings']:
            parsed['content_bindings'] = deserialize_content_bindings(parsed['content_bindings'])
        params = PollRequestParamsEntity(**parsed)
    else:
        params = None

    return SubscriptionEntity(
        subscription_id = model.id,
        collection_id = model.collection_id,
        poll_request_params = params,
        status = model.status
    )


def serialize_content_bindings(content_bindings):
    return json.dumps([(c.binding, c.subtypes) for c in content_bindings])


def deserialize_content_bindings(content_bindings):
    raw_bindings = json.loads(content_bindings)

    bindings = []
    for (binding, subtypes) in raw_bindings:
        entity = ContentBindingEntity(binding, subtypes=subtypes)
        bindings.append(entity)

    return bindings


# SQLite does not preserve TZ information
def enforce_timezone(date):

    if not date:
        return

    if date.tzinfo:
        return date

    return date.replace(tzinfo=pytz.UTC)

